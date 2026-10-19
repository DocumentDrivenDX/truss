# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original public schema acceptance, instance creation and typed engine reads.

Owns a new Homebrew PostgreSQL18 cluster; it never borrows a running service.
This qualifies RC module ACL reads, not protected current-policy or actions.
"""
from pathlib import Path
from contextlib import contextmanager
from datetime import timedelta
from dataclasses import replace
import argparse,hashlib,json,math,subprocess,sys,tempfile
import psycopg
from psycopg import sql
import weft
from typed_sdk_cohort import add_cohort_arguments,verify_cohort
from truss import CatalogDocument,ModuleAccessGrant,Ok,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.contracts import MapValue,TextValue
from truss.groups import AuthoredValue,CreateObject,RootlessOwnership,GroupSuccess
from truss.query import QueryCatalogSources
from truss.access import TrussTarget,TrussReadRefused
from umf_access.engine_catalog import EngineRead
from umf_access.types import StrictModel
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'packages/python/examples'))
from adopter_workflow import transaction,success,expect
class Parameters(StrictModel):status:str

parser=argparse.ArgumentParser();parser.add_argument("--streams",action="store_true");parser.add_argument("--streams-basic",action="store_true");parser.add_argument('--output',type=Path,required=True);parser.add_argument('--model-request',type=Path,required=True);parser.add_argument('--generated',type=Path,required=True);parser.add_argument('--bun-executable',type=Path,default=Path('bun'));parser.add_argument('--pg-bin',type=Path,default=Path('/opt/homebrew/opt/postgresql@18/bin'));add_cohort_arguments(parser);args=parser.parse_args()
basic_only=args.streams_basic and not args.streams
root=Path(__file__).resolve().parents[1];out=args.output.absolute();out.mkdir(parents=True,exist_ok=False);pg=out/'postgres';sock=out/'socket';sock.mkdir();started=False;checks=[]
def run(*command):
 result=subprocess.run(list(map(str,command)),text=True,capture_output=True,check=True)
 with (out/'native-lifecycle.log').open('a')as log:log.write(result.stdout+result.stderr)
cohort=verify_cohort(args)
if cohort is not None:(out/'installed-cohort.json').write_text(json.dumps(cohort,indent=2)+'\n')
try:
 (out/'toolchain.json').write_text(json.dumps({'embeddedRuntime':'mini-racer==0.14.1','externalJavaScriptRuntimeRequired':False,'python':sys.version.split()[0],'psycopg':psycopg.__version__},indent=2)+'\n')
 run(args.pg_bin/'initdb','-D',pg,'-A','trust','-U','sdk_test','--no-sync')
 run(args.pg_bin/'pg_ctl','-D',pg,'-l',out/'postgres.log','-o',f"-F -k {sock} -c listen_addresses='' -p 55495",'-w','start');started=True
 dsn=f'host={sock} port=55495 dbname=postgres user=sdk_test'
 packet=json.loads(args.model_request.read_bytes());original=packet['binding']['modelJson'].encode();digest=hashlib.sha256(original).hexdigest();doc=json.loads(original)
 assert type(doc) is dict and doc.get('umf')=='0.10.0','exact current UMF 0.10.0 model required'
 sys.path.insert(0,str(args.generated.absolute()));from native_sales.models import Order
 documents=(CatalogDocument(doc['id'],digest,original,digest),)
 with psycopg.connect(dsn,autocommit=True,options='-c statement_timeout=10000')as admin:
  assert admin.info.server_version==180006
  with transaction(admin)as(a,t):installed=success(a.install_in_transaction(t))
  admin.execute('CREATE ROLE sdk_person LOGIN');admin.execute('CREATE ROLE sdk_reader NOLOGIN');admin.execute('CREATE ROLE sdk_writer NOLOGIN')
  admin.execute(sql.SQL('GRANT {} TO sdk_person WITH SET FALSE').format(sql.Identifier(installed.registrar_role)))
  params=psycopg.conninfo.conninfo_to_dict(dsn);params['user']='sdk_person'
  with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000')as person:
   with transaction(person)as(a,t):
    prepared=a.prepare_catalog(documents,source_version=doc['umf'],bun_executable=str(args.bun_executable))
    accepted=success(a.accept_in_transaction(t,prepared,request_key='typed-sdk-original',bun_executable=str(args.bun_executable)))
    assert hasattr(accepted,'registration_id')
   with transaction(admin)as(a,t):success(a.configure_module_access_in_transaction(t,(ModuleAccessGrant(doc['id'],'sales','sdk_reader','sdk_writer'),)))
   admin.execute('GRANT sdk_reader,sdk_writer TO sdk_person WITH SET FALSE')
   admin.execute(sql.SQL('REVOKE {} FROM sdk_person').format(sql.Identifier(installed.registrar_role)))
   checks.append('current core 0.10 schema accepted through public API')
   with transaction(person)as(a,t):
    ref=success(a.get_type_reference_in_transaction(t,document_id=doc['id'],module_id='sales',record_id='order'))
    context=success(a.group_context_in_transaction(t))
    operation=CreateObject(type_definition_pin=ref.definition_pin,values=(AuthoredValue(name='id',value=TextValue(kind='string',text='bar')),AuthoredValue(name='status',value=TextValue(kind='string',text='draft'))),ownership=RootlessOwnership())
    applied=expect(success(a.apply_in_transaction(t,context.input((operation,),MapValue(entries=())),context.request('typed-sdk-seed'),documents=documents,bun_executable=str(args.bun_executable))),GroupSuccess)
    assert len(applied.response.semantic.results)==1
   checks.append('instance created through public atomic group API')
   with transaction(person,read_only=True)as(a,t):
    ordinary=success(a.query_in_transaction(t,sql='SELECT "r"."id" AS "id", "r"."status" AS "status" FROM "sales"."order" AS "r" WHERE "r"."status" = :status LIMIT 10',document_ids=(doc['id'],),parameters={'status':'draft'}))
    assert ordinary.outcome=='rows'and ordinary.columns==('id','status')and ordinary.rows==(('bar','draft'),)
   checks.append('original public query remains usable with the explicitly selected SDK compiler cohort')
   with transaction(person,read_only=True)as(a,t):
    captured=expect(success(a.query_catalog_sources_in_transaction(t,sql='SELECT "r"."id" AS "id", "r"."status" AS "status" FROM "sales"."order" AS "r" WHERE "r"."status" = :status LIMIT 10',document_ids=(doc['id'],),parameters={'status':'draft'})),QueryCatalogSources)
   request=json.loads(captured.request_json);entry=EngineRead.build(weft,request,parameters=Parameters,result=Order,method='truss-runtime')
   (out/'original-engine-request.json').write_text(captured.request_json)
   (out/'engine-catalog.json').write_text(entry.artifact_json)
   @contextmanager
   def operation(budget):
    person.execute('BEGIN READ ONLY')
    host=adopt_psycopg_host(person,statement_timeout_ms=max(1,math.floor(budget.total_seconds()*1000)),operation_timeout_ms=max(1,math.floor(budget.total_seconds()*1000)))
    try:
     tx=success(host.adopt_transaction(access_mode='read_only'));a=success(create_reference_assembly(CatalogRuntimeConfiguration(),host))
     yield a,tx
    except BaseException:
     host.detach();person.rollback();raise
    else:
     assert host.detach();person.commit()
   target=TrussTarget(operation,binding_sha256=request['target']['bindingSha256'],platform=(('postgresql','18.6'),),default_timeout=timedelta(seconds=10),catalog_entries=(entry,))
   shared={'binding_sha256':request['target']['bindingSha256'],'platform':(('postgresql','18.6'),),'default_timeout':timedelta(seconds=10)}
   captured_target=TrussTarget(operation,**shared,catalog_sources=captured,catalog_entries=(entry,))
   assert captured_target.identity()==target.identity()
   assert target.identity().backend_version==request['target']['backendVersion']
   assert captured_target.read(entry,Parameters(status='draft'))==[Order(id='bar',status='draft')]
   try:TrussTarget(operation,**shared)
   except ValueError:pass
   else:raise AssertionError('target identity guessed without original sources')
   changed_target=json.loads(captured.request_json);changed_target['target']['backendVersion']='unselected-version'
   try:TrussTarget(operation,**shared,catalog_sources=QueryCatalogSources(json.dumps(changed_target)),catalog_entries=(entry,))
   except ValueError:pass
   else:raise AssertionError('mixed original captured targets accepted')
   checks.append('identity derives from original complete native targets; absent or mixed sources refuse')
   assert target.read(entry,Parameters(status='draft'))==[Order(id='bar',status='draft')]
   assert target.read(entry,Parameters(status="draft' OR true --"))==[]
   target.verify();checks.extend(['original engine catalog roundtrip','typed native read','bound injection remains data','eager verify uses native read path'])
   changed_request=dict(request,sql=request['sql'].replace(' LIMIT 10', ' AND "r"."id" = \'different\' LIMIT 10'))
   changed=json.loads(weft.compile_engine_read_json(json.dumps({'version':'weft.engine-read/0.1','compiler':'truss-runtime','request':changed_request})))
   assert changed['status']=='compiled',changed
   with transaction(person,read_only=True)as(a,t):
    refused=success(a.query_in_transaction(t,sql=request['sql'],document_ids=(doc['id'],),parameters={'status':'draft'},engine_program=json.dumps(changed)))
    assert refused.outcome=='refused' and refused.code=='stale_context'
   checks.append('different valid compiler SQL refuses original correspondence')
   if not basic_only:
    (args.generated/'truss_declarations.py').write_text('from umf_access import query,Param\nfrom native_sales.models import Order\n@query\ndef selected(status:Param[str]):return Order.objects.filter(Order.c.status==status).limit(10).all()\n')
    config={'package':'native_sales','modules':['truss_declarations'],'targets':[{'id':'owned','kind':'truss','backendId':'truss.postgresql.runtime','backendVersion':request['target']['backendVersion'],'targetProfile':'truss-runtime-pg18.6/0.5','binding':packet['binding'],'engineCompiler':'truss-runtime','engineRequests':{'selected:0':request},'platform':[{'name':'postgresql','versions':['18.6']}]}]}
    (args.generated/'truss-config.json').write_text(json.dumps(config))
    for extra in ([],['--check']):
     command=[sys.executable,'-B','-m','umf_access.build.catalog','catalog','--root',str(args.generated),'--config',str(args.generated/'truss-config.json'),*extra]
     compiled=subprocess.run(command,capture_output=True,text=True)
     assert compiled.returncode==0,compiled.stdout+compiled.stderr
    from native_sales import queries
    assert queries.selected(target,status='draft')==[Order(id='bar',status='draft')]
    checks.append('real CLI catalog/check and generated typed query through original Truss path')
   # Seed more instances through the same public group path, not storage SQL.
   with transaction(person)as(a,t):
    ref=success(a.get_type_reference_in_transaction(t,document_id=doc['id'],module_id='sales',record_id='order'))
    context=success(a.group_context_in_transaction(t))
    creates=tuple(CreateObject(type_definition_pin=ref.definition_pin,values=(AuthoredValue(name='id',value=TextValue(kind='string',text=key)),AuthoredValue(name='status',value=TextValue(kind='string',text='draft'))),ownership=RootlessOwnership())for key in ('baz','foo'))
    expect(success(a.apply_in_transaction(t,context.input(creates,MapValue(entries=())),context.request('typed-sdk-page-seed'),documents=documents,bun_executable=str(args.bun_executable))),GroupSuccess)
   with transaction(person,read_only=True)as(a,t):
    page_sources=expect(success(a.query_catalog_sources_in_transaction(t,sql=request['sql'].removesuffix(' LIMIT 10'),document_ids=(doc['id'],),parameters={'status':'draft'})),QueryCatalogSources)
   page_request=json.loads(page_sources.request_json)
   page_entry=EngineRead.build(weft,page_request,parameters=Parameters,result=Order,method='truss-runtime',page_size=1)
   (out/'original-engine-page-request.json').write_text(page_sources.request_json)
   (out/'engine-page-catalog.json').write_text(page_entry.artifact_json)
   first=target.page(page_entry,Parameters(status='draft'));assert [r.id for r in first.items]==['bar'] and first.next_after is not None
   second=target.page(page_entry,Parameters(status='draft'),after=first.next_after);assert [r.id for r in second.items]==['baz'] and second.next_after is not None
   third=target.page(page_entry,Parameters(status='draft'),after=second.next_after);assert [r.id for r in third.items]==['foo'] and third.next_after is None
   from umf_access.pages import StaleContinuation
   try:target.page(page_entry,Parameters(status='other'),after=first.next_after)
   except StaleContinuation:pass
   else:raise AssertionError('foreign parameter continuation accepted')
   try:target.page(page_entry,Parameters(status='draft'),after=replace(first.next_after,values=('foo',)))
   except TrussReadRefused:pass
   else:raise AssertionError('typed Key diverged from original native cursor')
   checks.extend(['native owner pages retain complete authored Key without gaps','page continuation rejects parameter drift and typed/native Key disagreement'])
   if not basic_only:
    with (args.generated/'truss_declarations.py').open('a')as declarations:
     declarations.write('from native_sales.keys import OrderKey\n@query\ndef selected_page(status:Param[str],after:Param[OrderKey|None]):return Order.objects.filter(Order.c.status==status).page(size=1,after=after)\n')
    config['targets'][0]['engineRequests']['selected_page:0']=page_request
    (args.generated/'truss-config.json').write_text(json.dumps(config))
    for extra in ([],['--check']):
     compiled=subprocess.run([sys.executable,'-B','-m','umf_access.build.catalog','catalog','--root',str(args.generated),'--config',str(args.generated/'truss-config.json'),*extra],capture_output=True,text=True)
     assert compiled.returncode==0,compiled.stdout+compiled.stderr
    import importlib
    importlib.invalidate_caches();queries=importlib.reload(queries)
    generated_first=queries.selected_page(target,status='draft',after=None)
    generated_second=queries.selected_page(target,status='draft',after=generated_first.next_after)
    assert [r.id for r in generated_first.items]==['bar'] and [r.id for r in generated_second.items]==['baz']
    checks.append('real CLI page catalog/check and generated typed continuation retain native bytes')
   if args.streams or args.streams_basic:
    from typed_sdk_stream_checks import check_streams,check_large_streams
    check_streams(admin=admin,person=person,target=target,page_entry=page_entry,Parameters=Parameters,checks=checks,out=out)
   if args.streams:
    check_large_streams(admin=admin,person=person,target=target,Parameters=Parameters,checks=checks,out=out,documents=documents,document_id=doc["id"],generated=args.generated,bun_executable=args.bun_executable)
   admin.execute('REVOKE sdk_reader,sdk_writer FROM sdk_person')
   try:target.read(entry,Parameters(status='draft'))
   except TrussReadRefused:checks.append('native authorization revocation refuses SDK read')
   else:raise AssertionError('native unauthorized read escaped')
finally:
 if started:run(args.pg_bin/'pg_ctl','-D',pg,'-m','fast','-w','stop')
 (out/'verification.json').write_text(json.dumps({'generatedCatalogCoverage':not basic_only,'streamCoverage':'full' if args.streams else 'basic' if args.streams_basic else 'none','checks':checks,'ownedServerStopped':not(pg/'postmaster.pid').exists(),'temporal':'HELD','scope':'Truss RC module ACL schema, instance and typed read; no protected current-policy/action qualification'},indent=2)+'\n')
print(json.dumps({'status':'pass','checks':len(checks),'output':str(out)}))
