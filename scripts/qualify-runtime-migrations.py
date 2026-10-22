#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Release gate: every admitted lineage source migrates using the installed latest tool."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def validate_previous_manifest(manifest, original):
    previous=json.loads(original)
    original_hash=hashlib.sha256(original).hexdigest()
    archived=original_hash+'.manifest.json'
    if manifest['files'].get(archived)!=original_hash or archived not in manifest['immutableFiles']:
        raise AssertionError('Archive the original published manifest for historical receipt reconciliation')
    if not set(previous['sources']+[previous['target']])<=set(manifest['sources']+[manifest['target']]):
        raise AssertionError('Release strands an admitted installation')
    for name in previous['immutableFiles']:
        if name not in manifest['immutableFiles'] or manifest['files'].get(name)!=previous['files'][name]:
            raise AssertionError('Published migration artifact changed or lost immutable custody: '+name)
    return previous


def check_history(manifest):
    tags=subprocess.check_output(['git','tag','--list','v*'],cwd=ROOT,text=True).splitlines()
    tags=[t for t in tags if all(p.isdecimal() for p in t[1:].split('.'))]
    current=tuple(int(p) for p in importlib.metadata.version('truss-toolkit').split('.'))
    for tag in sorted(tags,key=lambda t:tuple(map(int,t[1:].split('.'))),reverse=True):
        if tuple(map(int,tag[1:].split('.')))>=current:continue
        old=subprocess.run(['git','show',tag+':packages/python/src/truss/_migrations/manifest.json'],cwd=ROOT,capture_output=True)
        if old.returncode:continue
        previous=validate_previous_manifest(manifest,old.stdout)
        return tag,previous['target']
    return None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheelhouse',required=True,type=Path)
    parser.add_argument('--download',action='store_true',help='Fetch exact declared public fixture wheels if absent')
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--installed-package',action='store_true')
    args=parser.parse_args()
    import truss
    from truss._migration_recipe import load_recipe,plan_route
    manifest,artifacts,recipe_digest=load_recipe()
    if args.installed_package and Path(truss.__file__).resolve().is_relative_to(ROOT/'packages/python/src'):
        raise AssertionError('Release gate must import the installed wheel')
    previous=check_history(manifest)
    args.wheelhouse.mkdir(parents=True,exist_ok=True)
    # No source can be dropped from the fixture matrix while it remains admitted.
    required=set(manifest['sources']);fixtures=set()
    wheels={}
    for label,entry in manifest['sourceWheels'].items():
        path=args.wheelhouse/entry['filename']
        if not path.exists() and args.download:
            url='https://github.com/DocumentDrivenDX/truss/releases/download/'+entry['tag']+'/'+entry['filename']
            with urllib.request.urlopen(url,timeout=60) as response:path.write_bytes(response.read())
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise AssertionError('Source wheel integrity failure: '+path.name)
        with zipfile.ZipFile(path) as wheel:
            original=wheel.read('truss/_catalog_runtime/manifest.json')
        digest=hashlib.sha256(original).hexdigest()
        if digest!=entry['runtimeManifestSha256'] or digest not in required|{manifest['target']}:raise AssertionError('Fixture/source tuple mismatch')
        fixtures.add(digest);wheels[label]=path
        plan_route(manifest,digest)
    if fixtures-{manifest['target']}!=required:raise AssertionError('Every lineage source needs a real published-wheel fixture')
    if previous and previous[1] not in fixtures:raise AssertionError('Previous target needs a real migration or unchanged-tuple fixture')
    sys.path.insert(0,str(ROOT/'packages/python/tests'))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    os.environ['TRUSS_MIGRATION_EVIDENCE_DIRECTORY']=str(args.output.parent.resolve())
    import test_runtime_migrations
    from test_runtime_migrations_native import RuntimeMigrationNativeTests
    class UnchangedTupleTests(RuntimeMigrationNativeTests):
        for _name in tuple(n for n in dir(RuntimeMigrationNativeTests) if n.startswith('test_')):locals()[_name]=None
        def test_previous_tuple_is_current_without_fake_migration(self):
            """@covers US-045-AC8"""
            before=self.state()
            self.assertEqual(self.tool.status()['state'],'current')
            with self.assertRaisesRegex(ValueError,'Already at latest'):self.tool.prepare()
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_migration_receipt').fetchone(),(0,))
            self.assertEqual(self.state(),before)
    suite=unittest.defaultTestLoader.loadTestsFromModule(test_runtime_migrations)
    for label,path in wheels.items():
        key='TRUSS_MIGRATION_GATE_'+label.upper();os.environ[key]=str(path.resolve())
        digest=manifest['sourceWheels'][label]['runtimeManifestSha256']
        base=UnchangedTupleTests if digest==manifest['target'] else RuntimeMigrationNativeTests
        case=type(label+'MigrationTests',(base,),{'source_label':label,'wheel_environment':key})
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    from test_runtime_migrations_subsequent_native import SubsequentRuntimeMigrationTests
    os.environ['TRUSS_MIGRATION_WHEELHOUSE']=str(args.wheelhouse.resolve())
    subsequent=type('PriorPublishedReceiptTests',(SubsequentRuntimeMigrationTests,),{'wheel_environment':'TRUSS_MIGRATION_GATE_SOURCE44'})
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(subsequent))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    receipt={'scope':'Installed latest-only runtime migration gate; PostgreSQL18.6, unprotected UMF0.10 lineage',
        'sourceCommit':os.environ.get('GITHUB_SHA'),'workflowRunId':os.environ.get('GITHUB_RUN_ID'),
        'package':importlib.metadata.version('truss-toolkit'),'loadedPackage':str(Path(truss.__file__).resolve()),
        'platform':sys.platform,'python':sys.version,'recipeSha256':recipe_digest,
        'targetManifestSha256':manifest['target'],'sources':sorted(fixtures),
        'originalWheels':{label:{'filename':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for label,path in wheels.items()},
        'previousMigrationRelease':previous[0] if previous else None,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skipped':len(result.skipped),'passed':result.wasSuccessful() and not result.skipped,
        'limitations':['No pre-0.10 or protected-profile migration','Qualification applies only to the recorded platform and exact tuple','One final publication per complete route; actual multi-edge and prior published receipt controls are included']}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    raise SystemExit(0 if receipt['passed'] else 1)


if __name__=='__main__':main()
