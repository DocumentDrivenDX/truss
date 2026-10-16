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

parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--model-request',type=Path,required=True);parser.add_argument('--generated',type=Path,required=True);parser.add_argument('--pg-bin',type=Path,default=Path('/opt/homebrew/opt/postgresql@18/bin'));args=parser.parse_args()
root=Path(__file__).resolve().parents[1];out=args.output.absolute();out.mkdir(parents=True,exist_ok=False);pg=out/'postgres';sock=out/'socket';sock.mkdir();started=False;checks=[]
def run(*command):
 result=subprocess.run(list(map(str,command)),text=True,capture_output=True,check=True)
 with (out/'native-lifecycle.log').open('a')as log:log.write(result.stdout+result.stderr)
try:
 run(args.pg_bin/'initdb','-D',pg,'-A','trust','-U','sdk_test','--no-sync')
 run(args.pg_bin/'pg_ctl','-D',pg,'-l',out/'postgres.log','-o',f"-F -k {sock} -c listen_addresses='' -p 55495",'-w','start');started=True
 dsn=f'host={sock} port=55495 dbname=postgres user=sdk_test'
 packet=json.loads(args.model_request.read_bytes());original=packet['binding']['modelJson'].encode();digest=hashlib.sha256(original).hexdigest();doc=json.loads(original)
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
    prepared=a.prepare_catalog(documents,source_version='0.8.0',bun_executable='/opt/homebrew/bin/bun')
    accepted=success(a.accept_in_transaction(t,prepared,request_key='typed-sdk-original',bun_executable='/opt/homebrew/bin/bun'))
    assert hasattr(accepted,'registration_id')
   with transaction(admin)as(a,t):success(a.configure_module_access_in_transaction(t,(ModuleAccessGrant(doc['id'],'sales','sdk_reader','sdk_writer'),)))
   admin.execute('GRANT sdk_reader,sdk_writer TO sdk_person WITH SET FALSE')
   admin.execute(sql.SQL('REVOKE {} FROM sdk_person').format(sql.Identifier(installed.registrar_role)))
   checks.append('original core08 schema accepted through public API')
   with transaction(person)as(a,t):
    ref=success(a.get_type_reference_in_transaction(t,document_id=doc['id'],module_id='sales',record_id='order'))
    context=success(a.group_context_in_transaction(t))
    operation=CreateObject(type_definition_pin=ref.definition_pin,values=(AuthoredValue(name='id',value=TextValue(kind='string',text='bar')),AuthoredValue(name='status',value=TextValue(kind='string',text='draft'))),ownership=RootlessOwnership())
    applied=expect(success(a.apply_in_transaction(t,context.input((operation,),MapValue(entries=())),context.request('typed-sdk-seed'),documents=documents,bun_executable='/opt/homebrew/bin/bun')),GroupSuccess)
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
   (args.generated/'truss_declarations.py').write_text('from umf_access import query,Param\nfrom native_sales.models import Order\n@query\ndef selected(status:Param[str]):return Order.objects.filter(Order.c.status==status).limit(10).all()\n')
   config={'package':'native_sales','modules':['truss_declarations'],'targets':[{'id':'owned','kind':'truss','backendId':'truss.postgresql.runtime','backendVersion':'0.4.39','targetProfile':'truss-runtime-pg18.6/0.5','binding':packet['binding'],'engineCompiler':'truss-runtime','engineRequests':{'selected:0':request},'platform':[{'name':'postgresql','versions':['18.6']}]}]}
   (args.generated/'truss-config.json').write_text(json.dumps(config))
   for extra in ([],['--check']):
    command=[sys.executable,'-B','-m','umf_access.build.catalog','catalog','--root',str(args.generated),'--config',str(args.generated/'truss-config.json'),*extra]
    compiled=subprocess.run(command,capture_output=True,text=True)
    assert compiled.returncode==0,compiled.stdout+compiled.stderr
   from native_sales import queries
   assert queries.selected(target,status='draft')==[Order(id='bar',status='draft')]
   checks.append('real CLI catalog/check and generated typed query through original Truss path')
   admin.execute('REVOKE sdk_reader,sdk_writer FROM sdk_person')
   try:target.read(entry,Parameters(status='draft'))
   except TrussReadRefused:checks.append('native authorization revocation refuses SDK read')
   else:raise AssertionError('native unauthorized read escaped')
finally:
 if started:run(args.pg_bin/'pg_ctl','-D',pg,'-m','fast','-w','stop')
 (out/'verification.json').write_text(json.dumps({'checks':checks,'ownedServerStopped':not(pg/'postmaster.pid').exists(),'temporal':'HELD','scope':'Truss RC module ACL schema, instance and typed read; no protected current-policy/action qualification'},indent=2)+'\n')
print(json.dumps({'status':'pass','checks':len(checks),'output':str(out)}))
