#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Observe one authentic installed0.76 initializer; never rewrite0.75 profiles.

Explicit execution only, on the admitted qualification worker. Produces raw
observations requiring source/cohort reconciliation, not a qualified baseline.
"""
import argparse
from hashlib import sha256
from importlib.resources import files
import json
import os
import platform
import subprocess
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-wheel',required=True,type=Path)
    parser.add_argument('--wheel-sha256',required=True)
    parser.add_argument('--initialization-time-zone',required=True,choices=('UTC','America/New_York'))
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--evidence-root',action='append',type=Path,default=[],help='Explicit run-scoped generated evidence roots, including prior serial capture')
    args=parser.parse_args()
    # Authenticate the original hosted input and all component prerequisites
    # before creating output or importing a native/runtime dependency.
    input_root=args.candidate_wheel.resolve().parent.parent
    hosted_path=input_root/'hosted-input.json'
    verified_path=input_root/'verified-input.json'
    if not hosted_path.is_file() or not verified_path.is_file():
        raise ValueError('Missing authenticated inventory-observation hosted input')
    hosted=json.loads(hosted_path.read_bytes());verified=json.loads(verified_path.read_bytes())
    if (verified.get('candidateWheelSha256')!=args.wheel_sha256
            or Path(verified.get('candidateWheel','')).resolve()!=args.candidate_wheel.resolve()):
        raise ValueError('Original inventory candidate wheel/input binding differs')
    from release_cohort import component_source_refs
    cohort_bytes=(ROOT/'scripts/truss-release-cohort.json').read_bytes()
    component_source_refs(cohort_bytes)
    refs=hosted.get('componentPrerequisiteReceipts')
    if type(refs) is not list:
        raise ValueError('Missing original component prerequisite refs for inventory-observation')
    members={}
    for name,digest_expected in hosted.get('files',{}).items():
        path=input_root/name
        if path.is_symlink() or not path.is_file() or sha256(path.read_bytes()).hexdigest()!=digest_expected:
            raise ValueError('Original inventory hosted member path/hash differs: '+name)
        raw=path.read_bytes();members[name]=raw;members['inputs/'+name]=raw
    from temporal_qualified_artifact import require_closed_component_prerequisites
    component_result=require_closed_component_prerequisites(refs,members,cohort_bytes=cohort_bytes,
        owner_identities=hosted.get('ownerIdentities'),admitted_wheels=hosted.get('wheels'))
    from release_cohort import require_stage_admission
    require_stage_admission('inventory-observation',component=component_result,records={
        'sourceIdentity':verified.get('sourceIdentity'),
        'ownerClosure':hosted.get('ownerIdentities'),
        'resourceClosure':hosted.get('ownerIdentities',{}).get('core',{}).get('resources'),
        'weftClosure':component_result['weftSDK42']})
    output=args.output.resolve()
    evidence=ROOT/'docs/helix/04-build/evidence/design-audit'
    if not output.is_relative_to(evidence.resolve()):raise ValueError('Owned native evidence directory required')
    output.mkdir(parents=True,exist_ok=False)
    if os.environ.get('TRUSS_NATIVE_WORKER'):raise ValueError('Initializer capture requires its own serial owned lease')
    from temporal_qualification_support import assert_qualification_checkout,commit_tree,journal_custody_inputs
    source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    source_tree=commit_tree(ROOT,source_commit)
    custody_inputs=journal_custody_inputs(ROOT,source_commit)
    source_identity=assert_qualification_checkout(ROOT,source_commit,source_tree,evidence_roots=(*args.evidence_root,output))
    if os.environ.get('GITHUB_SHA',source_commit)!=source_commit:raise ValueError('Actual checkout/runner source mismatch')
    from typed_sdk_cohort import _installed_wheel
    wheel=_installed_wheel(args.candidate_wheel,args.wheel_sha256,'truss','umf-truss')
    import truss
    if (wheel['version']!='0.0.56' or Path(truss.__file__).resolve().is_relative_to(ROOT/'packages/python/src')
            or not Path(truss.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())):
        raise ValueError('Exact installed candidate wheel outside source checkout required')
    import psycopg
    from truss import LocalPostgres,Ok
    from truss.catalog_runtime import _release
    from truss._migration_verify import structure,acl,roles,context
    from temporal_qualification_support import OwnedNativeCleanup
    sys.path.insert(0,str(ROOT/'packages/python/tests'))
    from runtime_migration_fixture import assembly
    # All actual S/W resources, compiled module enrollments and source seals
    # precede these captures; their later changes require a new source capture.
    from release_cohort import load_cohort,verify_installed
    load_cohort(require_qualified=True);verify_installed()
    from truss._temporal_owner import _inspector
    from truss._temporal_compiler import compiler
    _inspector()
    if compiler() is None:raise ValueError('Actual compiled temporal Weft enrollment required before capture')
    package=Path(truss.__file__).resolve().parent
    nonmigration={str(p.relative_to(package)):sha256(p.read_bytes()).hexdigest() for p in sorted(package.rglob('*'))
        if p.is_file() and '_migrations' not in p.relative_to(package).parts and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    for name,digest_expected in nonmigration.items():
        source=ROOT/'packages/python/src/truss'/name
        if not source.is_file() or sha256(source.read_bytes()).hexdigest()!=digest_expected:
            raise ValueError('Actual capture package differs from original committed source: '+name)
    manifest,digest,_=_release()
    if manifest['releaseId']!='truss-catalog-runtime/0.76-temporal-candidate':raise ValueError('Actual0.76 source required')
    raw_manifest=files('truss').joinpath('_catalog_runtime/manifest.json').read_bytes()
    output.joinpath('original-runtime-manifest.json').write_bytes(raw_manifest)
    os.environ['TZ']=args.initialization_time_zone
    owned=Path(tempfile.mkdtemp(prefix='truss-temporal-init-'))
    monitor=OwnedNativeCleanup([],output/'cleanup.json');observed=None;error=None
    try:
        with monitor:
            with LocalPostgres(owned/'data') as runtime:
                with psycopg.connect(runtime.info.connection_uri,autocommit=True,options='-c statement_timeout=30000') as connection:
                    initialization_zone=connection.execute('SHOW TimeZone').fetchone()[0]
                    if initialization_zone!=args.initialization_time_zone:
                        raise RuntimeError('Native initializer timezone differs; never infer or patch an observation')
                    connection.execute('BEGIN');host,engine,tx=assembly(connection)
                    try:
                        result=engine.install_in_transaction(tx)
                        output.joinpath('raw-installer-output.json').write_text(json.dumps({'outcome':repr(result),
                            'hostLastAttempt':repr(host._custody.last_attempt)},indent=2)+'\n')
                        if not isinstance(result,Ok):raise RuntimeError('Actual candidate initializer refused: '+repr(result))
                    finally:host.detach()
                    connection.commit()
                    connection.execute('SET search_path=pg_catalog,pg_temp')
                    connection.execute("SET TimeZone='UTC'") # Observation only AFTER original initializer.
                    with connection.cursor() as cursor:
                        ctx,owner,registrar,_=context(cursor);inventory=structure(cursor);rolemap=roles(cursor,owner,registrar)
                        from truss._initialization_custody import verify_stored,source_policy
                        from truss._installation_privileges import verify_initialization_custody_privileges
                        verify_initialization_custody_privileges(cursor,owner,(registrar,))
                        horizon=[r for r in inventory['relations'] if r[0]=='journal_runtime_horizon'][0]
                        custody=verify_stored(cursor,{'manifest':manifest,'sha256':digest},horizon)
                        witness=json.loads(custody.raw)
                        original_custody={'policy':source_policy(manifest),'witnessHex':custody.raw.hex(),'sha256':custody.digest,
                            'nativeDerivation':{'beforeUtc':witness['clockBeforeUtc'],'afterUtc':witness['clockAfterUtc'],'timeZone':witness['timeZone'],
                            'pairs':witness['candidateBoundPairs'],'bounds':list(custody.candidate_bounds),'installerSha256':witness['installerSha256']}}
                        output.joinpath('initialization-custody.json').write_bytes(custody.raw)
                        grants={k:[] for k in ('owner','registrar','administrator','reader','writer','feed','audit','public')}
                        raw_acl=acl(cursor,full_names=True)
                        for kind,name,objowner,grantee,priv,grantable,grantor in raw_acl:
                            kinds=rolemap.get(grantee)
                            if not kinds or len(kinds)!=1:raise RuntimeError('Unclassified actual native ACL')
                            grants[next(iter(kinds))].append([kind,name,priv,grantable])
                        for rows in grants.values():rows.sort()
                    configuration,managed=connection.execute('SELECT preparation_configuration,managed_grants FROM truss.catalog_runtime_installation').fetchone()
                    actual=connection.execute('SELECT release_id,release_sha256 FROM truss.catalog_runtime_installation').fetchone()
                    if actual!=(manifest['releaseId'],digest):raise RuntimeError('Actual installation/source identity mismatch')
                    observed={'sha256':digest,'manifest':manifest,'inventory':inventory,'acl':grants,
                        'initializationCustody':original_custody,'rawAcl':raw_acl,'aclNameProfile':'truss-native-acl-names/0.2','configuration':configuration,'managedGrants':managed,
                        'initializationTimeZone':initialization_zone,'observationTimeZone':'UTC'}
                    output.joinpath('native-profile-observation.json').write_text(json.dumps(observed,indent=2)+'\n')
                if (runtime.directory/'log').is_file():shutil.copyfile(runtime.directory/'log',output/'original-postgres.log')
            shutil.rmtree(owned) # Monitor confirms actual pg_ctl3 + original PID absence BEFORE deletion.
        assert_qualification_checkout(ROOT,source_commit,source_tree,evidence_roots=(*args.evidence_root,output))
        if journal_custody_inputs(ROOT,source_commit)!=custody_inputs:raise ValueError('Custody code/schema/governing inputs changed during capture')
    except BaseException as caught:
        error={'class':type(caught).__module__+'.'+type(caught).__qualname__,'message':str(caught)}
        raise
    finally:
        receipt={'scope':'Raw actual installed initializer/profile observation ONLY; no migration, admitted baseline or native composition qualification',
            'wheel':wheel,'runtimeManifestSha256':digest,'runtimeRelease':manifest['releaseId'],
            'initializationTimeZone':args.initialization_time_zone,'observed':observed is not None,
            'cleanupConfirmed':monitor.confirmed,'error':error,
            'passed':observed is not None and monitor.confirmed and error is None,
            'producerSha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'nonMigrationPackageFiles':nonmigration,'journalCustodyInputs':custody_inputs,
            'sourceCommit':source_commit,'sourceTree':source_tree,'sourceIdentity':source_identity,
            'sysPlatform':sys.platform,'machine':platform.machine(),'pythonMajorMinor':list(sys.version_info[:2]),
            'profileSha256':sha256(output.joinpath('native-profile-observation.json').read_bytes()).hexdigest() if observed is not None else None,
            'historicalProfilesModified':False,'issuedBaseline':False}
        output.joinpath('receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return 0 if receipt['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
