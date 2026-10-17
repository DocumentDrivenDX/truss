"""One genuine public SDK RelatedKeys read/page/stream workflow on fresh PG18."""
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
import argparse, hashlib, json, math, subprocess, sys
import psycopg
from psycopg import sql
import weft
from truss import CatalogDocument, ModuleAccessGrant, adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration
from truss.access import TrussTarget
from truss.contracts import MapValue, TextValue
from truss.groups import AuthoredValue, CreateObject, RootlessOwnership, GroupSuccess, CreateEdge, StoredObjectReference, NullOrderKey
from truss.query import QueryCatalogSources, QueryRefused
from truss.query_stream import owned_stream_operation
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'packages/python/examples'))
from adopter_workflow import transaction, success, expect

parser=argparse.ArgumentParser()
for name in ('generated','model','output','pg-bin','bun-executable'):parser.add_argument('--'+name,type=Path,required=True)
args=parser.parse_args();out=args.output.absolute();out.mkdir(parents=True,exist_ok=False)
original=args.model.read_bytes();digest=hashlib.sha256(original).hexdigest();doc=json.loads(original)
sys.path.insert(0,str(args.generated.absolute()))
from native_sales.models import Order
from native_sales.keys import CustomerKey
assert Order.UMF_SOURCE.document_sha256==digest
assert weft.__version__=='0.4.42-dev.0'
assert subprocess.check_output([str(args.bun_executable),'--version'],text=True).strip()=='1.4.2'
documents=(CatalogDocument(doc['id'],digest,original,digest),);checks=[];started=False
pg=out/'postgres';sock=out/'socket';sock.mkdir()
def run(*command):
    result=subprocess.run(list(map(str,command)),text=True,capture_output=True,check=True)
    with (out/'lifecycle.log').open('a')as log:log.write(result.stdout+result.stderr)
try:
    run(args.pg_bin/'initdb','-D',pg,'-A','trust','-U','sdk_test','--no-sync')
    run(args.pg_bin/'pg_ctl','-D',pg,'-l',out/'postgres.log','-o',f"-F -k {sock} -c listen_addresses='' -p 55495",'-w','start');started=True
    with psycopg.connect(host=str(sock),port=55495,dbname='postgres',user='sdk_test',autocommit=True,options='-c statement_timeout=10000')as admin:
        assert admin.info.server_version==180006
        with transaction(admin)as(a,t):installed=success(a.install_in_transaction(t))
        admin.execute('CREATE ROLE sdk_person LOGIN');admin.execute('CREATE ROLE sdk_reader NOLOGIN');admin.execute('CREATE ROLE sdk_writer NOLOGIN')
        admin.execute(sql.SQL('GRANT {} TO sdk_person WITH SET FALSE').format(sql.Identifier(installed.registrar_role)))
        with psycopg.connect(host=str(sock),port=55495,dbname='postgres',user='sdk_person',autocommit=True,options='-c statement_timeout=10000')as person:
            with transaction(person)as(a,t):
                prepared=a.prepare_catalog(documents,source_version='0.8.0',bun_executable=str(args.bun_executable))
                success(a.accept_in_transaction(t,prepared,request_key='sdk-related-model'))
            with transaction(admin)as(a,t):success(a.configure_module_access_in_transaction(t,(ModuleAccessGrant(doc['id'],'sales','sdk_reader','sdk_writer'),)))
            admin.execute('GRANT sdk_reader,sdk_writer TO sdk_person WITH SET FALSE')
            admin.execute(sql.SQL('REVOKE {} FROM sdk_person').format(sql.Identifier(installed.registrar_role)))
            with transaction(person)as(a,t):
                refs={name:success(a.get_type_reference_in_transaction(t,document_id=doc['id'],module_id='sales',record_id=name))for name in ('order','customer')}
                context=success(a.group_context_in_transaction(t))
                def create(record,values):return CreateObject(type_definition_pin=refs[record].definition_pin,values=tuple(AuthoredValue(name=k,value=TextValue(kind='string',text=v))for k,v in values.items()),ownership=RootlessOwnership())
                operations=(create('order',{'id':'bar','status':'draft'}),create('order',{'id':'baz','status':'draft'}),create('customer',{'customerId':'c0','customerName':'First'}),create('customer',{'customerId':'c1','customerName':'Second'}))
                seeded=expect(success(a.apply_in_transaction(t,context.input(operations,MapValue(entries=())),context.request('sdk-related-seed'),documents=documents,bun_executable=str(args.bun_executable))),GroupSuccess)
                identities=[r.identity for r in seeded.response.semantic.results]
            with transaction(person)as(a,t):
                relation=success(a.get_relationship_reference_in_transaction(t,document_id=doc['id'],module_id='sales',relationship_id='customers'))
                links=tuple(CreateEdge(relationship_definition_pin=relation.definition_pin,source=StoredObjectReference(identity=identities[0]),target=StoredObjectReference(identity=identities[index]),values=(),order_key=NullOrderKey())for index in (2,2,3))
                context=success(a.group_context_in_transaction(t));expect(success(a.apply_in_transaction(t,context.input(links,MapValue(entries=())),context.request('sdk-related-links'),documents=documents,bun_executable=str(args.bun_executable))),GroupSuccess)
            checks.append('exact original schema, objects and parallel edges through public APIs and caller commits')
            declaration='from umf_access import query,Param\nfrom native_sales.models import Order,OrderIdentity\nfrom native_sales.keys import OrderKey\n@query\ndef related_rows():return Order.objects.into(OrderIdentity).include_keys(Order.c.customers,limit=2).order_by(Order.c.id.asc()).limit(10).all()\n@query\ndef related_pages(after:Param[OrderKey|None]):return Order.objects.into(OrderIdentity).include_keys(Order.c.customers,limit=2).order_by(Order.c.id.asc()).page(size=1,after=after)\n'
            (args.generated/'truss_related_declarations.py').write_text(declaration)
            from importlib import import_module
            from dataclasses import replace
            from umf_access.capture import capture,render_logical,ExpressionNode
            declarations=import_module('truss_related_declarations');requests={}
            binding={'modelJson':original.decode(),'modelSha256':digest}
            for name in ('related_rows','related_pages'):
                variant=capture(getattr(declarations,name)).variants[0]
                if name=='related_pages':variant=replace(variant,node=ExpressionNode('all',variant.node.args[:2]))
                query=render_logical(variant,binding=binding,owner_bound=name=='related_pages')
                with transaction(person,read_only=True)as(a,t):captured=expect(success(a.query_catalog_sources_in_transaction(t,sql=query,document_ids=(doc['id'],))),QueryCatalogSources)
                requests[name+':0']=json.loads(captured.request_json)
                assert requests[name+':0']['modules'][0]['documentJson'].encode()==original
            (out/'requests.json').write_text(json.dumps(requests,indent=2)+'\n')
            request=requests['related_rows:0'];config={'package':'native_sales','modules':['truss_related_declarations'],'targets':[{'id':'owned','kind':'truss','backendId':'truss.postgresql.runtime','backendVersion':'0.4.41','targetProfile':'truss-runtime-pg18.6/0.5','binding':binding,'engineCompiler':'truss-runtime','engineRequests':requests,'platform':[{'name':'postgresql','versions':['18.6']}]}]}
            (args.generated/'related-config.json').write_text(json.dumps(config))
            for extra in ([],['--check']):
                built=subprocess.run([sys.executable,'-B','-m','umf_access.build.catalog','catalog','--root',str(args.generated),'--config',str(args.generated/'related-config.json'),*extra],capture_output=True,text=True)
                assert built.returncode==0,built.stdout+built.stderr
            from native_sales import queries
            entries=tuple(plan.variants[0].entry for plan in (queries._Q0,queries._Q1))
            @contextmanager
            def operation(budget):
                person.execute('BEGIN READ ONLY');host=adopt_psycopg_host(person,statement_timeout_ms=max(1,math.floor(budget.total_seconds()*1000)),operation_timeout_ms=max(1,math.floor(budget.total_seconds()*1000)))
                try:
                    tx=success(host.adopt_transaction(access_mode='read_only'))
                    yield success(create_reference_assembly(CatalogRuntimeConfiguration(),host)),tx
                except BaseException:host.detach();person.rollback();raise
                else:assert host.detach();person.commit()
            @contextmanager
            def lease():yield person
            target=TrussTarget(operation,binding_sha256=request['target']['bindingSha256'],platform=(('postgresql','18.6'),),default_timeout=timedelta(seconds=10),catalog_entries=entries,stream_operation=owned_stream_operation(lease))
            rows=queries.related_rows(target)
            assert [r.row.id for r in rows]==['bar','baz']
            assert rows[0].keys.items==(CustomerKey(customer_id='c0'),)*2 and rows[0].keys.truncated
            assert type(rows[0].keys.items[0])is CustomerKey
            assert rows[1].keys.items==()and not rows[1].keys.truncated
            first=queries.related_pages(target,after=None);second=queries.related_pages(target,after=first.next_after)
            assert list(first.items)+list(second.items)==rows and second.next_after is None
            assert list(queries.related_pages_stream(target,after=None,max_rows=3))==rows
            assert person.info.transaction_status==psycopg.pq.TransactionStatus.IDLE
            assert person.execute('SELECT count(*) FROM pg_catalog.pg_cursors').fetchone()==(0,)
            checks.append('genuine CLI-generated read/page/stream preserve Key identity, parallel occurrences, truncation and empty bags')
            with transaction(person,read_only=True)as(a,t):
                ordinary=success(a.query_in_transaction(t,sql='SELECT "r"."id" AS "id" FROM "sales"."order" AS "r" ORDER BY "r"."id" ASC',document_ids=(doc['id'],)))
                assert ordinary.rows==(('bar',),('baz',))
                foreign=json.loads(json.dumps(request));foreign['sql']=foreign['sql'].replace(' ORDER BY',' WHERE "r"."id" = \'foreign\' ORDER BY')
                program=weft.compile_engine_read_json(json.dumps({'version':'weft.engine-read/0.1','compiler':'truss-runtime','request':foreign}))
                assert json.loads(program)['status']=='compiled'
                refused=success(a.query_in_transaction(t,sql=request['sql'],document_ids=(doc['id'],),engine_program=program))
                assert isinstance(refused,QueryRefused)and refused.code=='stale_context'
            checks.append('ordinary SQL remains usable and a different valid original program refuses')
finally:
    if started:run(args.pg_bin/'pg_ctl','-D',pg,'-m','immediate','-w','stop')
(out/'verification.json').write_text(json.dumps({'checks':checks,'schemaSha256':digest,'weftVersion':weft.__version__,'serverStopped':True,'scope':'ordinary module ACL RelatedKeys; no navigation IR, Graph, temporal or protected actions'},indent=2)+'\n')
print(json.dumps({'checks':checks,'serverStopped':True},indent=2))
