"""Real original engine-stream E2Es, sharing the public schema/instance fixture."""
from contextlib import contextmanager
from datetime import timedelta
import json
import psycopg
from truss.access import TrussTarget
from truss.query_stream import owned_stream_operation


def check_streams(*,admin,person,target,page_entry,Parameters,checks,out):
    leased=False
    @contextmanager
    def lease():
        nonlocal leased
        assert not leased
        leased=True
        try:yield person
        finally:leased=False
    operation=owned_stream_operation(lease)
    source=json.loads(target.native_target_json)
    streamed=TrussTarget(target.operation,binding_sha256=target.binding_sha256,platform=target.platform,
        default_timeout=timedelta(seconds=10),catalog_entries=(page_entry,),stream_operation=operation)
    values=Parameters(status='draft')
    assert [row.id for row in streamed.stream(page_entry,values,max_rows=2)]==['bar','baz']
    assert person.info.transaction_status==psycopg.pq.TransactionStatus.IDLE and not leased
    assert person.execute('SELECT count(*) FROM pg_catalog.pg_cursors').fetchone()==(0,)
    checks.append('owned RC cursor stream bound releases portal and native transaction')
    stream=streamed.stream(page_entry,values,max_rows=10**50)
    assert next(stream).id=='bar' and leased
    # Independent writer adds a matching object by public API in the broader
    # campaign; this basic cursor control checks actual early-close custody.
    stream.close()
    assert not leased and person.info.transaction_status==psycopg.pq.TransactionStatus.IDLE
    assert person.execute('SELECT count(*) FROM pg_catalog.pg_cursors').fetchone()==(0,)
    checks.append('early generator close rolls back owned native cursor; huge max_rows has no API ceiling')
    person.execute('BEGIN')
    person.execute('CREATE TEMP TABLE unrelated_stream_work (id integer)')
    person.execute('INSERT INTO unrelated_stream_work VALUES (7)')
    try:list(streamed.stream(page_entry,values,max_rows=2))
    except ValueError as error:assert 'idle connection' in str(error)
    else:raise AssertionError('foreign transaction borrowed')
    assert person.info.transaction_status==psycopg.pq.TransactionStatus.INTRANS
    person.commit()
    assert person.execute('SELECT id FROM unrelated_stream_work').fetchall()==[(7,)]
    checks.append('active foreign transaction refused before SQL; unrelated work commits unchanged')
    (out/'stream-scope.json').write_text(json.dumps({'clientPageSize':1,'nativeMaximumScanRows':10000,'nativeSourceMaterializes':True,'temporal':'HELD','protectedSecurity':False,'currentTarget':source,'scope':'bounded ordinary module ACL cursor candidate'},indent=2)+'\n')


def check_large_streams(*,admin,person,target,Parameters,checks,out,documents,document_id,generated,bun_executable):
    import importlib, subprocess, sys
    from dataclasses import replace
    from truss import Ok
    from truss.contracts import MapValue,TextValue
    from truss.groups import AuthoredValue,CreateObject,RootlessOwnership,GroupSuccess
    from truss.query_stream import QueryStreamRefused
    from truss.query import QueryRefused
    from umf_access.engine_catalog import EngineRead
    from native_sales.models import Order
    from adopter_workflow import transaction,success,expect
    def seed(connection,keys):
        with transaction(connection) as (assembly,tx):
            ref=success(assembly.get_type_reference_in_transaction(tx,document_id=document_id,module_id='sales',record_id='order'))
            context=success(assembly.group_context_in_transaction(tx))
            creates=tuple(CreateObject(type_definition_pin=ref.definition_pin,values=(AuthoredValue(name='id',value=TextValue(kind='string',text=key)),AuthoredValue(name='status',value=TextValue(kind='string',text='export'))),ownership=RootlessOwnership()) for key in keys)
            result=expect(success(assembly.apply_in_transaction(tx,context.input(creates,MapValue(entries=())),context.request('stream-seed-'+keys[0]),documents=documents,bun_executable=str(bun_executable))),GroupSuccess)
            assert len(result.response.semantic.results)==len(keys)
    for start in range(0,2500,500):seed(person,[f'k{i:04}' for i in range(start,min(2500,start+500))])
    with transaction(person,read_only=True) as (assembly,tx):
        captured=success(assembly.query_catalog_sources_in_transaction(tx,sql='SELECT "r"."id" AS "id", "r"."status" AS "status" FROM "sales"."order" AS "r" WHERE "r"."status" = :status',document_ids=(document_id,),parameters={'status':'export'},maximum_rows=1000,maximum_scan_rows=10000,maximum_bytes=16777216))
    request=json.loads(captured.request_json)
    import weft
    entry=EngineRead.build(weft,request,parameters=Parameters,result=Order,method='truss-runtime',page_size=999)
    (out/'stream-original-request.json').write_text(captured.request_json)
    (out/'stream-original-program.json').write_text(entry.originals())
    with (generated/'truss_declarations.py').open('a') as declarations:
        declarations.write('@query\ndef selected_export(status:Param[str],after:Param[OrderKey|None]):return Order.objects.filter(Order.c.status==status).page(size=999,after=after)\n')
    config=json.loads((generated/'truss-config.json').read_bytes());config['targets'][0]['engineRequests']['selected_export:0']=request
    (generated/'truss-config.json').write_text(json.dumps(config))
    for extra in ([],['--check']):
        result=subprocess.run([sys.executable,'-B','-m','umf_access.build.catalog','catalog','--root',str(generated),'--config',str(generated/'truss-config.json'),*extra],capture_output=True,text=True)
        assert result.returncode==0,result.stdout+result.stderr
    from native_sales import queries
    importlib.invalidate_caches();queries=importlib.reload(queries)
    leased=False;fetches=[];injection=None
    @contextmanager
    def lease():
        nonlocal leased
        assert not leased;leased=True
        try:yield person
        finally:leased=False
    owned=owned_stream_operation(lease)
    @contextmanager
    def operation(budget):
        with owned(budget) as (assembly,tx):
            original=assembly.query_stream_fetch_in_transaction
            def fetch(transaction,handle,*,count,validate,operation_deadline=None,final_bound=False):
                def validator(rows):
                    result=validate(rows)
                    if injection is not None:injection()
                    return result
                batch=original(transaction,handle,count=count,validate=validator,operation_deadline=operation_deadline,final_bound=final_bound)
                fetches.append({'requested':count,'returned':len(batch.items),'exhausted':batch.exhausted})
                return batch
            assembly.query_stream_fetch_in_transaction=fetch
            yield assembly,tx
    streamed=TrussTarget(target.operation,binding_sha256=request['target']['bindingSha256'],platform=target.platform,
        default_timeout=timedelta(seconds=10),catalog_entries=(entry,),stream_operation=operation)
    stream=queries.selected_export_stream(streamed,status='export',after=None,max_rows=2200)
    first=next(stream)
    assert first.id=='k0000' and leased
    with psycopg.connect(person.info.dsn,autocommit=True,options='-c statement_timeout=10000') as writer:
        seed(writer,['k1750z'])
    rows=[first,*stream]
    assert [r.id for r in rows]==[f'k{i:04}' for i in range(2200)]
    assert [f['returned'] for f in fetches]==[999,999,202] and all(f['requested']<=999 for f in fetches)
    assert not leased and person.info.transaction_status==psycopg.pq.TransactionStatus.IDLE
    checks.append('generated stream yields exact2200of2500 in authored Key order; independent public writer after first page excluded')
    all_rows=list(queries.selected_export_stream(streamed,status='export',after=None,max_rows=10**50))
    assert len(all_rows)==2501 and [r.id for r in all_rows]==sorted([f'k{i:04}' for i in range(2500)]+['k1750z'])
    checks.append('new native stream observes committed writer; huge bound does not truncate finite source')
    # Revoke during real typed page processing, after native FETCH but before
    # publication. The final fresh native scope must discard the entire page.
    def revoke():admin.execute('REVOKE sdk_reader,sdk_writer FROM sdk_person')
    injection=revoke
    try:
        try:list(streamed.stream(entry,Parameters(status='export'),max_rows=2200))
        except QueryStreamRefused:pass
        else:raise AssertionError('post-fetch revocation leaked typed rows')
    finally:
        injection=None;admin.execute('GRANT sdk_reader,sdk_writer TO sdk_person WITH SET FALSE')
    assert not leased and person.info.transaction_status==psycopg.pq.TransactionStatus.IDLE
    checks.append('actual native role revocation during typed processing discards complete fetched page and terminates cursor')
    stream=streamed.stream(entry,Parameters(status='export'),max_rows=2200)
    assert next(stream).id=='k0000'
    # A whole first page is already admitted/buffered; consume it before testing
    # the next fresh native page, so no claim of per-row authorization is made.
    for _ in range(998):next(stream)
    admin.execute('REVOKE sdk_reader,sdk_writer FROM sdk_person')
    try:
        try:next(stream)
        except QueryStreamRefused:pass
        else:raise AssertionError('later unauthorized page escaped')
    finally:
        stream.close();admin.execute('GRANT sdk_reader,sdk_writer TO sdk_person WITH SET FALSE')
    assert not leased and person.execute('SELECT count(*) FROM pg_catalog.pg_cursors').fetchone()==(0,)
    checks.append('between-page native revocation raises after complete admitted prefix; terminal portal cleanup confirmed')
    # A result validator is real caller code executed under the native page
    # operation. Its failure cannot publish even one row from that page.
    def invalid_dto():raise ValueError('injected typed DTO failure after native fetch')
    injection=invalid_dto
    try:
        try:list(streamed.stream(entry,Parameters(status='export'),max_rows=2200))
        except QueryStreamRefused:pass
        else:raise AssertionError('invalid typed page published')
    finally:injection=None
    assert not leased and person.info.transaction_status==psycopg.pq.TransactionStatus.IDLE
    checks.append('typed DTO failure after native fetch yields no page and terminal native cleanup succeeds')
    # A genuine independent native table lock makes the data path wait. The
    # first page's capture/declare/FETCH share the absolute per-page deadline.
    from time import monotonic
    from umf_access.postgres_read import TimedOut
    admin.execute('BEGIN');admin.execute('LOCK TABLE truss.object IN ACCESS EXCLUSIVE MODE')
    started=monotonic()
    try:
        try:list(streamed.stream(entry,Parameters(status='export'),max_rows=2200,timeout=timedelta(milliseconds=300)))
        except TimedOut:pass
        else:raise AssertionError('blocked native source escaped page deadline')
    finally:admin.rollback()
    elapsed=monotonic()-started
    assert elapsed<3,elapsed
    assert not leased and person.info.transaction_status==psycopg.pq.TransactionStatus.IDLE
    assert person.execute('SELECT count(*) FROM pg_catalog.pg_cursors').fetchone()==(0,)
    checks.append('real native exclusive lock times out first page; shared startup budget and complete rollback confirmed')
    # Break the physical connection only after real final-page validation. The
    # final page must remain withheld because native CLOSE/rollback is unknown.
    broken=[]
    @contextmanager
    def broken_lease():
        with psycopg.connect(person.info.dsn,autocommit=True,options='-c statement_timeout=10000') as connection:
            broken.append(connection)
            yield connection
    broken_owned=owned_stream_operation(broken_lease)
    @contextmanager
    def broken_operation(budget):
        with broken_owned(budget) as (assembly,tx):
            original=assembly.query_stream_close_in_transaction
            def close(transaction,handle):
                broken[-1].close()
                return original(transaction,handle)
            assembly.query_stream_close_in_transaction=close
            yield assembly,tx
    broken_target=TrussTarget(target.operation,binding_sha256=request['target']['bindingSha256'],platform=target.platform,
        default_timeout=timedelta(seconds=10),catalog_entries=(entry,),stream_operation=broken_operation)
    published=[]
    try:
        for row in broken_target.stream(entry,Parameters(status='export'),max_rows=1):published.append(row)
    except (ValueError,psycopg.Error):pass
    else:raise AssertionError('unknown final cleanup reported successful export')
    assert published==[] and broken[-1].closed
    checks.append('physical disconnect before final cleanup withholds final page and closes quarantined connection')
    # Successful native cleanup still consumes the final page's original
    # budget. It must not publish late merely because CLOSE had a fresh budget.
    from time import sleep
    @contextmanager
    def delayed_operation(budget):
        with owned(budget) as (assembly,tx):
            original=assembly.query_stream_close_in_transaction
            def close(transaction,handle):
                result=original(transaction,handle)
                sleep(2.1)
                return result
            assembly.query_stream_close_in_transaction=close
            yield assembly,tx
    delayed_target=TrussTarget(target.operation,binding_sha256=request['target']['bindingSha256'],platform=target.platform,
        default_timeout=timedelta(seconds=2),catalog_entries=(entry,),stream_operation=delayed_operation)
    published=[]
    try:
        for row in delayed_target.stream(entry,Parameters(status='export'),max_rows=1):published.append(row)
    except TimedOut as error:
        assert str(error)=='stream final page deadline expired during cleanup',str(error)
        (out/'delayed-cleanup.json').write_text(json.dumps({'observedError':str(error),'nativeCloseCompleted':True,'originalPageBudgetSeconds':2,'injectedSuccessfulCleanupDelaySeconds':2.1})+'\n')
    else:raise AssertionError('late successful cleanup published final page')
    assert published==[] and not leased and person.info.transaction_status==psycopg.pq.TransactionStatus.IDLE
    assert person.execute('SELECT count(*) FROM pg_catalog.pg_cursors').fetchone()==(0,)
    checks.append('delayed successful native cleanup preserves original final-page deadline and withholds late final rows')
    (out/'large-stream.json').write_text(json.dumps({'rowsSeededPublicly':2500,'writerAddedPublicly':1,'snapshotExportRows':2200,'batches':fetches,'blockedPageSeconds':elapsed,'nativeMaximumScanRows':10000,'nativeMaximumBytes':16777216,'serverWork':'whole bounded source materialization and sort; not page-bounded','temporal':'HELD'},indent=2)+'\n')
