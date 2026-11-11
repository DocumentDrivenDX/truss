# SPDX-License-Identifier: MIT OR Apache-2.0
"""Separate public055 populated-state refusal. UNEXECUTED until full campaign."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import psycopg
from truss import LocalPostgres,Ok
from truss.lifecycle import InstallRefused
from truss.catalog_runtime import _release
from truss.migrations import RuntimeMigrations
from truss.recovery_registry import HostRecoveryRegistry
from runtime_migration_fixture import assembly
from test_temporal_catalog_transport_native import TemporalCatalogTransportTests

ROOT=Path(__file__).resolve().parents[3]
PROVENANCE_SHA256='7eb2db195d7ae7e01d56039e13f893356740e9907a447f63e4a93bd72904aa40'
PUBLIC055_WHEEL_SHA256='156df20641d8c4fee6d836c6b29266a0a7eb3b1299c407e430ce0d2c07a79805'
PUBLIC055_NATIVE_SHA256='5ecb599f65d64e6656bf6c83c30cea6e2aefd488cb3fe821b749458d5e9b3522'


def provenance():
    raw=(ROOT/'packages/python/tests/fixtures/temporal/public055-provenance.json').read_bytes()
    if sha256(raw).hexdigest()!=PROVENANCE_SHA256:raise ValueError('Exact original public055 fixture provenance required')
    selected=json.loads(raw)
    if selected['wheelSHA256']!=PUBLIC055_WHEEL_SHA256 or selected['nativeManifestSHA256']!=PUBLIC055_NATIVE_SHA256:raise ValueError('Original public055 identities differ')
    for prefix in ('originalSeedProducer','seedProducer'):
        if sha256((ROOT/selected[prefix]).read_bytes()).hexdigest()!=selected[prefix+'SHA256']:raise ValueError('Original055 seed producer changed')
    if sha256((ROOT/selected['constraints']).read_bytes()).hexdigest()!=selected['constraintsSHA256']:raise ValueError('Original public055 dependency constraints changed')
    return selected


class TemporalPublic055RefusalTests(unittest.TestCase):
    cleanup_owned_runtime=classmethod(TemporalCatalogTransportTests.cleanup_owned_runtime.__func__)
    def snapshot(self,connection):
        state=TemporalCatalogTransportTests.snapshot(self,connection)
        from truss._migration_verify import acl
        with connection.cursor() as cursor:state['acl']=acl(cursor,full_names=True)
        return state

    @classmethod
    def setUpClass(cls):
        cls.provenance=provenance();cls.old_python=Path(os.environ['TRUSS_PUBLIC055_PYTHON']);cls.old_wheel=Path(os.environ['TRUSS_PUBLIC055_WHEEL'])
        if sha256(cls.old_wheel.read_bytes()).hexdigest()!=PUBLIC055_WHEEL_SHA256:raise ValueError('Authentic immutable public055 wheel required')
        check='''import importlib.metadata,pathlib,sys,zipfile,hashlib,json,truss
assert sys.version_info[:2]==(3,11)
assert importlib.metadata.version('umf-truss')=='0.0.55'
root=pathlib.Path(truss.__file__).resolve().parent
assert root.is_relative_to(pathlib.Path(sys.prefix).resolve())
with zipfile.ZipFile(sys.argv[1]) as z:
 names=z.namelist();assert len(names)==len(set(names))
 for name in names:
  if name.startswith('truss/') and not name.endswith('/'):
   assert (root/name.removeprefix('truss/')).read_bytes()==z.read(name),name
 assert hashlib.sha256(z.read('truss/_catalog_runtime/manifest.json')).hexdigest()==sys.argv[2]
expected_files={name.removeprefix('truss/') for name in names if name.startswith('truss/') and not name.endswith('/')}
actual_files={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
assert actual_files==expected_files
selected=json.loads(pathlib.Path(sys.argv[3]).read_bytes())
for name,version in selected['dependencyPins311Linux'].items():
 assert importlib.metadata.version(name)==version,name
for name in selected['forbiddenOwnerDistributions']:
 try:importlib.metadata.distribution(name)
 except importlib.metadata.PackageNotFoundError:continue
 raise ValueError('Foreign owner installed in predecessor environment: '+name)
print(json.dumps({'version':'0.0.55','moduleRoot':str(root),'manifestSha256':sys.argv[2],'dependencyPins':selected['dependencyPins311Linux'],'foreignOwnersAbsent':True}))
'''
        cls.old_environment={**os.environ,'PYTHONPATH':str(ROOT/'packages/python/tests'),'PYTHONDONTWRITEBYTECODE':'1'}
        checked=subprocess.run([str(cls.old_python),'-I','-c',check,str(cls.old_wheel),PUBLIC055_NATIVE_SHA256,str(ROOT/'packages/python/tests/fixtures/temporal/public055-provenance.json')],env=cls.old_environment,text=True,capture_output=True,check=True,timeout=30)
        cls.old_identity=json.loads(checked.stdout)
        cls.evidence=Path(os.environ['TRUSS_NATIVE_EVIDENCE_DIR'])/'public055';cls.evidence.mkdir(parents=True,exist_ok=False)
        (cls.evidence/'original-installed-identity.json').write_text(json.dumps(cls.old_identity,indent=2)+'\n')
        cls.root=Path(tempfile.mkdtemp(prefix='truss-temporal-public055-refusal-'));cls.runtime=LocalPostgres(cls.root/'data');cls.addClassCleanup(cls.cleanup_owned_runtime)
        cls.runtime.__enter__();cls.original_pid=int((cls.runtime.directory/'postmaster.pid').read_text().splitlines()[0]);cls.uri=cls.runtime.info.connection_uri

    def test_public55_populated_installation_refuses_candidate_without_effects(self):
        from test_catalog_relational_support import relational_document
        model=relational_document();model['id']='adoc';model['extensions']={'x-original-unknown':{'future':[3,1,4],'retained':None}};model['vocabularies']={'x-original-unknown':{'version':'1.0.0'}}
        source=self.root/'model.json';source.write_text(json.dumps(model,ensure_ascii=True));seed=self.root/'original-seed.json'
        result=subprocess.run([str(self.old_python),str(ROOT/self.provenance['seedProducer']),self.uri,str(source),str(seed),str(self.old_wheel)],env=self.old_environment,text=True,capture_output=True,timeout=240)
        (self.evidence/'original-seed.stdout').write_text(result.stdout);(self.evidence/'original-seed.stderr').write_text(result.stderr)
        if seed.exists():(self.evidence/'original-seed.json').write_bytes(seed.read_bytes())
        self.assertEqual(result.returncode,0,'Actual installed055 seed failed: '+result.stdout+result.stderr)
        seeded=json.loads(seed.read_bytes());observations={}
        with psycopg.connect(self.uri,autocommit=True,options='-c statement_timeout=10000') as admin:
            original=admin.execute('SELECT installation_id::text,release_id,release_sha256 FROM truss.catalog_runtime_installation').fetchone()
            self.assertEqual(original,(seeded['installation'],'truss-catalog-runtime/0.75-candidate',PUBLIC055_NATIVE_SHA256))
            for table in ('prop_def','object','schema_doc','journal','catalog_registration_request','request_receipt','runtime_feed_consumer'):
                self.assertGreater(admin.execute(psycopg.sql.SQL('SELECT count(*) FROM truss.{}').format(psycopg.sql.Identifier(table))).fetchone()[0],0,table)
            self.assertEqual(admin.execute('SELECT count(*) FROM truss.runtime_feed_consumer WHERE last_prior IS NOT NULL AND last_target IS NOT NULL AND last_payload_sha256 IS NOT NULL').fetchone(),(1,))
            before=self.snapshot(admin)
            (self.evidence/'snapshot-before.json').write_text(json.dumps(before,indent=2)+'\n')
            self.assertIn('x-original-unknown',before['tables']['schema_doc'])
            admin.execute('BEGIN');admin.execute('CREATE TEMP TABLE public055_prior(value int)');admin.execute('INSERT INTO public055_prior VALUES(7)');xid=admin.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
            host,candidate,tx=assembly(admin)
            try:answer=candidate.install_in_transaction(tx,operation_timeout_ms=180000)
            finally:host.detach()
            self.assertEqual(answer,Ok(InstallRefused(code='incompatible')))
            self.assertEqual(admin.info.transaction_status,psycopg.pq.TransactionStatus.INTRANS)
            self.assertEqual(admin.execute('SELECT pg_current_xact_id()::text').fetchone(),(xid,));self.assertEqual(admin.execute('SELECT * FROM public055_prior').fetchall(),[(7,)])
            admin.commit();after=self.snapshot(admin)
            (self.evidence/'snapshot-after-installer.json').write_text(json.dumps(after,indent=2)+'\n')
            self.assertEqual(after,before);observations['installer']='InstallRefused/incompatible'
            tool=RuntimeMigrations(lambda:psycopg.connect(self.uri,autocommit=True),HostRecoveryRegistry(self.root/'candidate-registry.sqlite'))
            for name in ('status','verify','prepare'):
                with self.subTest(operation=name),self.assertRaisesRegex(ValueError,'Installed native definitions drifted or source unsupported') as caught:getattr(tool,name)()
                observations[name]={'errorClass':type(caught.exception).__name__,'message':str(caught.exception)}
                after=self.snapshot(admin)
                (self.evidence/('snapshot-after-'+name+'.json')).write_text(json.dumps(after,indent=2)+'\n')
                self.assertEqual(after,before,name)
            self.assertIsNone(admin.execute("SELECT to_regclass('truss.runtime_initialization_custody')").fetchone()[0])
            self.assertEqual(admin.execute('SELECT count(*) FROM truss.runtime_migration_receipt').fetchone(),(0,))
            self.assertEqual(admin.execute('SELECT installation_id::text,release_id,release_sha256 FROM truss.catalog_runtime_installation').fetchone(),original)
        native,digest,_=_release();self.assertEqual(native['releaseId'],'truss-catalog-runtime/0.76-temporal-candidate')
        report={'scope':'Actual installed public055 populated-state refusal ONLY','oldWheelSHA256':PUBLIC055_WHEEL_SHA256,'oldNativeManifestSHA256':PUBLIC055_NATIVE_SHA256,'candidateNativeManifestSHA256':digest,'fixtureProvenanceSHA256':PROVENANCE_SHA256,'seedProducerSHA256':self.provenance['seedProducerSHA256'],'oldInstalledIdentity':self.old_identity,'refusals':observations,'completeStateEqualAfterEveryAttempt':True,'tableByteDigests':{n:sha256(b.encode()).hexdigest() for n,b in before['tables'].items()},'noMigrationReceipt':True,'noCustodyWitness':True,'cleanup':'Separate owned-monitor pg_ctl3+originalPIDabsence proof REQUIRED before PASS'}
        report['candidateSourceCommit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        report['candidateSourceTree']=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip()
        (self.evidence/'public055-no-effects.json').write_text(json.dumps(report,indent=2)+'\n');print('temporal-public055-no-effects '+json.dumps(report,sort_keys=True))
