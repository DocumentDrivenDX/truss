"""Frozen original release-selection native checks; no authenticated PA admission."""
import hashlib,importlib.metadata,importlib.util,json,os,shutil,subprocess,sys,tempfile,uuid,zipfile
from pathlib import Path
resource_countercontrol=sys.argv[1:]==['--countercontrol-no-resource-digest']
archive_countercontrol=sys.argv[1:]==['--countercontrol-no-archive-lock']
self_write_countercontrol=sys.argv[1:]==['--countercontrol-no-self-write-fence']
self_write_profile=sys.argv[1:]==['--archive-self-write-fence'] or self_write_countercontrol
epoch_issuer_countercontrol=sys.argv[1:]==['--countercontrol-no-epoch-issuer-fence']
epoch_table_countercontrol=sys.argv[1:]==['--countercontrol-no-epoch-table-fence']
epoch_order_countercontrol=sys.argv[1:]==['--countercontrol-no-epoch-write-table-locks']
epoch_fence_profile=sys.argv[1:]==['--epoch-state-fence'] or epoch_issuer_countercontrol or epoch_table_countercontrol or epoch_order_countercontrol
fence_check_countercontrol=sys.argv[1:]==['--countercontrol-no-fence-correspondence']
fence_hash_countercontrol=sys.argv[1:]==['--countercontrol-no-fence-body-hash']
countercontrol=resource_countercontrol or archive_countercontrol or self_write_countercontrol or fence_check_countercontrol or fence_hash_countercontrol or epoch_issuer_countercontrol or epoch_table_countercontrol or epoch_order_countercontrol
routine_ddl_profile=sys.argv[1:]==['--routine-ddl-writer-barrier']
if sys.argv[1:] and not routine_ddl_profile and not countercontrol and not self_write_profile and not epoch_fence_profile and sys.argv[1:]!=['--report-write-candidate']:raise ValueError('Explicit supported native control required')
report_write_profile=sys.argv[1:]==['--report-write-candidate']
root=Path.cwd();run_id=str(uuid.uuid4())
folder=root/'docs/helix/04-build/evidence/python-catalog-report-release'/run_id
folder.mkdir(parents=True);os.umask(0o077)
inputs={}
def retain(path):
    p=root/path;inputs[str(p)]=p.read_bytes()
for p in (root/'packages/python/src/truss').rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:inputs[str(p)]=p.read_bytes()
for name in ('test_routine_ddl_barrier_native.py','test_catalog_report_write_candidate_native.py','test_epoch_state_fence_native.py','test_archive_self_write_fence_native.py','test_catalog_report_release_native.py','test_catalog_configured_release_stage_native.py',
             'test_catalog_staging.py','test_catalog_support.py','test_preparation.py','test_native_pg8000.py',
             'test_catalog_source_candidate.py','test_configured_catalog_stage.py','test_native_catalog_dispatch.py','test_native_operation_ordinals.py','test_native_arbitration.py'):
    retain('packages/python/tests/'+name)
for name in ('source-epoch-lock','source-epoch-issue','source-epoch-immutability','source-epoch-fresh-lock','source-epoch-read-fence','source-epoch-fenced-fresh-lock','issued-operation-admission/operation-configuration-context-admission',
             'catalog-observation-recheck','catalog-epoch-context','operation-configuration-current',
             'source-epoch-routine-ddl-barrier','security-query-source-census-pg16','catalog-admission-configuration','catalog-report/report-write-candidate','catalog-report/archive-self-write-fence','catalog-report/archive-write-fence-current','catalog-report/release-selection',
             'canonical-string-bytes','canonical-tree-bytes','catalog-report/configured-graph','catalog-report/resource-selection','catalog-report/configured-stage','catalog-report/source-candidate','catalog-report/configured-metadata','catalog-stage-configured','catalog-stage-issued'):
    retain('packages/postgresql/native/'+name+'.sql')
for path in ('docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
             'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql',
             'docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql',
             'scripts/check-python-catalog-report-release-native.py','scripts/check-module-boundaries.py'):
    retain(path)
# Freeze the original catalog staging component closure used by the configured call.
import ast
staging=ast.parse((root/'packages/python/tests/test_catalog_staging.py').read_text())
components=next(ast.literal_eval(n.value) for n in staging.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COMPONENTS' for t in n.targets))
for name in components:
    retain('packages/postgresql/native/'+name+'.sql')
for name in ('issued-operation-admission/operation-admission','catalog-report/empty-graph',
             'catalog-report/absent-binding-index-declarations','catalog-report/fresh-lifecycle','edge-limit/verify-current-scope'):
    retain('packages/postgresql/native/'+name+'.sql')
retain('docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json')
policy=json.loads((root/'packages/python/src/truss/_profiles/catalog-report-release.json').read_bytes())
for entry in policy['resources']:retain(entry['path'])
for package in ('pg8000','scramp','asn1crypto','dateutil','six'):
    origin=Path(importlib.util.find_spec(package).origin)
    files=[origin] if package=='six' else origin.parent.rglob('*.py')
    for p in files:inputs[str(p)]=p.read_bytes()
    dist=importlib.metadata.distribution('python-dateutil' if package=='dateutil' else package)
    for f in dist.files:
        if str(f).endswith('.dist-info/METADATA'):
            p=Path(dist.locate_file(f));inputs[str(p)]=p.read_bytes()
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pins={p:sha(raw) for p,raw in inputs.items()}
with zipfile.ZipFile(folder/'sources.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for p,raw in inputs.items():archive.writestr(p.lstrip('/'),raw)
pgbin=Path(os.environ['TRUSS_CENSUS_POSTGRES_BIN']).resolve()
binaries={str(p):sha(p.read_bytes()) for p in pgbin.parent.rglob('*') if p.is_file()}
execution=Path(tempfile.mkdtemp(prefix='truss-release-execution-'))
socket=Path(tempfile.mkdtemp(prefix='rl-',dir='/private/tmp'))
pgdata=execution/'pgdata';attempted=False;receipt=None

def run(argv,**kw):
    return subprocess.run(argv,capture_output=True,text=True,timeout=kw.pop('timeout',30),**kw)
def require(result):
    if result.returncode:raise RuntimeError(result.stderr[-4000:])
    return result
try:
    for name,raw in inputs.items():
        if epoch_order_countercontrol and name==str(root/'packages/postgresql/native/source-epoch-issue.sql'):
            marker=b' LOCK TABLE truss.source_epoch_current, truss.source_epoch_registry IN ROW EXCLUSIVE MODE NOWAIT;'
            if raw.count(marker)!=1:raise RuntimeError('Exact strongest writer mode before row effects required')
            raw=raw.replace(marker,b' -- Deliberate omitted upfront write table locks.')
            (folder/'countercontrol-source-epoch-issue.sql').write_bytes(raw)
        if (epoch_issuer_countercontrol and name==str(root/'packages/postgresql/native/source-epoch-issue.sql')) or (epoch_table_countercontrol and name==str(root/'packages/postgresql/native/source-epoch-read-fence.sql')):
            marker=b' IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l'
            if raw.count(marker)!=1:raise RuntimeError('Exact own-reader epoch fence predicate required')
            raw=raw.replace(marker,b' IF FALSE AND EXISTS(SELECT 1 FROM pg_catalog.pg_locks l')
            (folder/('countercontrol-source-epoch-issue.sql' if epoch_issuer_countercontrol else 'countercontrol-source-epoch-read-fence.sql')).write_bytes(raw)
        p=Path(name)
        if p.is_relative_to(root):target=execution/'checkout'/p.relative_to(root)
        else:
            # Execute exact dependency package bytes, rather than installed aliases.
            selected=next((part for part in ('pg8000','scramp','asn1crypto','dateutil') if part in p.parts),None)
            if p.name=='six.py':selected='six.py'
            if selected is None:continue  # Distribution metadata retained as evidence.
            target=execution/'dependencies'/Path(*p.parts[p.parts.index(selected):])
        if archive_countercontrol and name==str(root/'packages/postgresql/native/catalog-report/release-selection.sql'):
            marker=b' LOCK TABLE truss.installation_archive IN SHARE MODE NOWAIT;'
            if raw.count(marker)!=1:raise RuntimeError('Exact archive-lock control site required')
            raw=raw.replace(marker,b' -- Deliberate negative control: archive table lock omitted.')
            (folder/'countercontrol-release-selection.sql').write_bytes(raw)
        if resource_countercontrol and name==str(root/'packages/postgresql/native/catalog-report/resource-selection.sql'):
            marker=b'  IF NOT EXISTS(SELECT 1 FROM truss.installation_archive a WHERE a.archive_row_id=row.archive_row_id'
            if raw.count(marker)!=1:raise RuntimeError('Exact resource digest control site required')
            raw=raw.replace(marker,b'  IF FALSE AND NOT EXISTS(SELECT 1 FROM truss.installation_archive a WHERE a.archive_row_id=row.archive_row_id')
            (folder/'countercontrol-resource-selection.sql').write_bytes(raw)
        if self_write_countercontrol and name==str(root/'packages/postgresql/native/catalog-report/archive-self-write-fence.sql'):
            marker=b' IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l'
            if raw.count(marker)!=1:raise RuntimeError('Exact self-write fence control site required')
            raw=raw.replace(marker,b' IF FALSE AND EXISTS(SELECT 1 FROM pg_catalog.pg_locks l')
            (folder/'countercontrol-archive-self-write-fence.sql').write_bytes(raw)
        if fence_hash_countercontrol and name==str(root/'packages/postgresql/native/catalog-report/archive-write-fence-current.sql'):
            marker=b'  OR sha256(convert_to(routine.prosrc,'
            if raw.count(marker)!=1:raise RuntimeError('Exact original fence body hash control required')
            raw=raw.replace(marker,b'  OR FALSE AND sha256(convert_to(routine.prosrc,')
            (folder/'countercontrol-archive-write-fence-current.sql').write_bytes(raw)
        if fence_check_countercontrol and name==str(root/'packages/postgresql/native/catalog-report/configured-stage.sql'):
            marker=b' PERFORM truss.runtime_require_selected_archive_write_fence();'
            if raw.count(marker)!=2:raise RuntimeError('Exact two installed-fence comparison sites required')
            raw=raw.replace(marker,b' -- Deliberate paired omission: installed fence correspondence absent.')
            (folder/'countercontrol-configured-stage.sql').write_bytes(raw)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        if target.read_bytes()!=raw:raise RuntimeError('Frozen source readback differs')
    if any(Path(p).read_bytes()!=raw for p,raw in inputs.items()):raise RuntimeError('Source changed before native execution')
    require(run([str(pgbin/'initdb'),'-D',str(pgdata),'-U','postgres','--auth=trust','--encoding=UTF8'],timeout=60))
    attempted=True
    require(run([str(pgbin/'pg_ctl'),'-D',str(pgdata),'-l',str(execution/'server.log'),'-w','-o',f"-h '' -k {socket}",'start'],timeout=60))
    test=run([sys.executable,'-m','unittest','discover','-s',str(execution/'checkout/packages/python/tests'),'-p','test_routine_ddl_barrier_native.py' if routine_ddl_profile else 'test_catalog_report_write_candidate_native.py' if report_write_profile else 'test_epoch_state_fence_native.py' if epoch_fence_profile else 'test_archive_self_write_fence_native.py' if self_write_profile else 'test_catalog_report_release_native.py' if archive_countercontrol else 'test_catalog_*release*native.py','-v'],
        cwd=execution/'checkout',env={**os.environ,'PYTHONPATH':str(execution/'checkout/packages/python/src')+os.pathsep+str(execution/'dependencies'),
        'TRUSS_NATIVE_TEST_SOCKET':str(socket/'.s.PGSQL.5432'),'TRUSS_ROUTINE_DDL_EVIDENCE':str(folder)},timeout=120)
    (folder/'tests.stdout.log').write_text(test.stdout);(folder/'tests.stderr.log').write_text(test.stderr)
    if countercontrol:
        expected_failures=1 if epoch_issuer_countercontrol or epoch_order_countercontrol else 10 if epoch_table_countercontrol else 2 if fence_hash_countercontrol else 22 if fence_check_countercontrol else 10 if self_write_countercontrol else 1 if resource_countercontrol else 4
        missing_errors=0 if epoch_issuer_countercontrol or epoch_order_countercontrol else 9 if epoch_table_countercontrol else expected_failures
        if test.returncode!=1 or test.stderr.count('DatabaseError not raised')!=missing_errors or f'FAILED (failures={expected_failures})' not in test.stderr:
            raise RuntimeError('Expected exact native omission counterexamples required')
        if epoch_issuer_countercontrol and "'55P03' != '55000'" not in test.stderr:raise RuntimeError('Original marker-before-guard counterexample required')
        if epoch_order_countercontrol and "(0, 'success') != (2, '55P03')" not in test.stderr:raise RuntimeError('Original writer modes before marker wait counterexample required')
        if epoch_table_countercontrol and 'original source epoch registry evidence are immutable' not in test.stderr:raise RuntimeError('Independent registry TRUNCATE guard control required')
    else:require(test)
    native_test_count=15 if routine_ddl_profile else 15 if report_write_profile else 10 if epoch_fence_profile else 8 if self_write_profile else 12 if archive_countercontrol else 23
    if f'Ran {native_test_count} tests' not in test.stderr or 'skipped' in test.stderr:raise RuntimeError('Complete selected native population required')
    # Execute each original catalog-dispatch regression method exactly once.
    original=ast.parse(inputs[str(root/'packages/python/tests/test_native_catalog_dispatch.py')])
    suite=next(n for n in original.body if isinstance(n,ast.ClassDef) and n.name=='NativeCatalogDispatchTests')
    methods=[n.name for n in suite.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    if len(methods)!=14:raise RuntimeError('Closed original fourteen-method catalog regression inventory required')
    if self_write_countercontrol:
        methods=[]  # Exact body mutation is intentionally inadmissible to configured regression fixtures.
    else:
        regression=run([sys.executable,'-m','unittest',*[f'test_native_catalog_dispatch.NativeCatalogDispatchTests.{name}' for name in methods],'-v'],
            cwd=execution/'checkout',env={**os.environ,'PYTHONPATH':str(execution/'checkout/packages/python/tests')+os.pathsep+str(execution/'checkout/packages/python/src')+os.pathsep+str(execution/'dependencies'),
            'TRUSS_NATIVE_TEST_SOCKET':str(socket/'.s.PGSQL.5432')},timeout=120)
        (folder/'regression.stdout.log').write_text(regression.stdout);(folder/'regression.stderr.log').write_text(regression.stderr);require(regression)
        if 'Ran 14 tests' not in regression.stderr or 'skipped' in regression.stderr:raise RuntimeError('Complete original catalog regressions required')
    auxiliary_methods=[]
    if not countercontrol:
        for module in ('test_catalog_source_candidate','test_configured_catalog_stage'):
            tree=ast.parse(inputs[str(root/f'packages/python/tests/{module}.py')])
            for cls in (n for n in tree.body if isinstance(n,ast.ClassDef)):
                auxiliary_methods.extend(f'{module}.{cls.name}.{n.name}' for n in cls.body
                    if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'))
        if len(auxiliary_methods)!=15:raise RuntimeError('Closed fifteen incoming metadata/source regression inventory required')
        auxiliary=run([sys.executable,'-m','unittest',*auxiliary_methods,'-v'],cwd=execution/'checkout',
            env={**os.environ,'PYTHONPATH':str(execution/'checkout/packages/python/tests')+os.pathsep+str(execution/'checkout/packages/python/src')+os.pathsep+str(execution/'dependencies'),
                'TRUSS_NATIVE_TEST_SOCKET':str(socket/'.s.PGSQL.5432')},timeout=120)
        (folder/'auxiliary.stdout.log').write_text(auxiliary.stdout);(folder/'auxiliary.stderr.log').write_text(auxiliary.stderr);require(auxiliary)
        if 'Ran 15 tests' not in auxiliary.stderr or 'skipped' in auxiliary.stderr:raise RuntimeError('Complete incoming metadata/source regressions required')
    boundary=run([sys.executable,'scripts/check-module-boundaries.py'])
    (folder/'boundaries.stdout.log').write_text(boundary.stdout);(folder/'boundaries.stderr.log').write_text(boundary.stderr);require(boundary)
    if any(Path(p).read_bytes()!=raw for p,raw in inputs.items()):raise RuntimeError('Source changed during native execution')
    receipt={'status':'countercontrol-reproduced' if countercontrol else 'component-passed','countercontrol':countercontrol,'countercontrolKind':'epoch-writer-order' if epoch_order_countercontrol else 'epoch-issuer-fence' if epoch_issuer_countercontrol else 'epoch-table-fence' if epoch_table_countercontrol else 'fence-body-hash' if fence_hash_countercontrol else 'fence-correspondence' if fence_check_countercontrol else 'self-write-fence' if self_write_countercontrol else 'resource-digest' if resource_countercontrol else 'archive-lock' if archive_countercontrol else None,'runId':run_id,'sourceDigests':pins,'nativeBinaryDigests':binaries,
        'executedFenceSqlSha256':sha((execution/'checkout/packages/postgresql/native/catalog-report/archive-self-write-fence.sql').read_bytes()),'executedFenceComparisonSqlSha256':sha((execution/'checkout/packages/postgresql/native/catalog-report/archive-write-fence-current.sql').read_bytes()),'executedConfiguredStageSqlSha256':sha((execution/'checkout/packages/postgresql/native/catalog-report/configured-stage.sql').read_bytes()),'executedReleaseSqlSha256':sha((execution/'checkout/packages/postgresql/native/catalog-report/release-selection.sql').read_bytes()),'testCommand':test.args,'testExitCode':test.returncode,'nativeTests':native_test_count,'selfWriteFenceProfile':self_write_profile,'routineDdlWriterBarrierProfile':routine_ddl_profile,'reportWriteCandidateProfile':report_write_profile,'originalCatalogRegressions':methods,'incomingCatalogRegressions':auxiliary_methods,'python':sys.version,
        'versions':{p:importlib.metadata.version(p) for p in ('pg8000','scramp','asn1crypto')},
        'epochStateFenceProfile':epoch_fence_profile,
        'scope':('Automatic six-tag routine-DDL transaction-lifetime barrier only; successful DDL intentionally leaves epoch unchanged. Fresh census required; shared-role/grant/cascade/other source and event-trigger administration excluded. No automatic epoch issuance or held business-use admission. ' if routine_ddl_profile else '')+('Administrative rollback-only report construction and INSERT/readback; no public acceptance, commit seal or installed authority. ' if report_write_profile else '')+('Native epoch-state fence and writer-before-row table lock ordering; excludes neither routine source nor shared-role/configuration/authorization-data writers. ' if epoch_fence_profile else '')+('Omitted body hash comparison reproduces two isolated same-size/source-settings drift assertions. ' if fence_hash_countercontrol else '')+('Paired omitted installed-fence comparisons reproduce twenty-two exact correspondence assertions. ' if fence_check_countercontrol else '')+('Native actual-lock same-backend archive write fence and acquisition/savepoint controls; separate from configured release installation. ' if self_write_profile else '')+('Deliberate omitted-resource-digest variant reproduces one pre-cut integrity assertion failure; late mutation is independently fenced. ' if resource_countercontrol else 'Deliberate omitted-archive-lock variant reproduces four exact exclusion assertion failures. ' if archive_countercontrol else '')+'Frozen original private release selector, configured catalog staging/metadata producer, Python candidate source composition and tests over owned installed PostgreSQL16.15 Unix fixture. SHARE table lock excludes concurrent archive writes; transaction/savepoint controls qualify only native archive cut lifetime. Administrative synthetic configuration/archive/capture fixtures do not establish authenticated caller, source issuer, complete installed source/authority cut, host held-use dispatcher, public installer, complete accepted report or final disclosure.'}
except BaseException as error:
    receipt={'status':'failed','runId':run_id,'sourceDigests':pins,'nativeBinaryDigests':binaries,'error':str(error)}
finally:
    cleanup={'attempted':attempted}
    try:
        if attempted:
            stopped=run([str(pgbin/'pg_ctl'),'-D',str(pgdata),'-w','-m','immediate','stop'])
            state=run([str(pgbin/'pg_ctl'),'-D',str(pgdata),'status'])
            cleanup.update(stopExitCode=stopped.returncode,statusExitCode=state.returncode,socketAbsent=not (socket/'.s.PGSQL.5432').exists())
            (folder/'server.log').write_bytes((execution/'server.log').read_bytes())
            if stopped.returncode or state.returncode!=3 or not cleanup['socketAbsent']:receipt['status']='failed'
        if any(sha(Path(p).read_bytes())!=h for p,h in binaries.items()):receipt['status']='failed';receipt['binaryDrift']=True
        if not attempted or cleanup.get('statusExitCode')==3 and cleanup.get('socketAbsent'):
            shutil.rmtree(execution);shutil.rmtree(socket)
        else:cleanup['retainedExecutionDirectory']=str(execution)
    except BaseException as error:receipt['status']='failed';cleanup['error']=str(error)
    receipt['cleanup']=cleanup;(folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'evidence':str(folder)}))
if receipt['status'] not in ('component-passed','countercontrol-reproduced'):raise SystemExit(1)
