"""Diagnostic plans only: public chunked same-XID population, not capacity proof."""
import hashlib,json,re,time,unittest
from pathlib import Path
import psycopg
from truss import Ok
from truss.contracts import MapValue
from truss.groups import GroupSuccess
import test_group_create_native as base
SOURCE=Path('/private/tmp/truss-main-integration-20261010/packages/python/src/truss/_catalog_runtime/operations.sql')
OUTPUT=Path('/private/tmp/truss-row-transition-plans-report-20261016.json')
REPORT={'scope':'Diagnostic-only public100-record groups in one transaction; no1024capacity, commit, actual CI cached-plan, production instrumentation or performance qualification claim. Forced generic plans of exact row-validator SELECTs; native guards and deadlines unchanged.','setup':[]}
def save():OUTPUT.write_text(json.dumps(REPORT,indent=2,default=str)+'\n')
def queries():
    source=SOURCE.read_text();start=source.index('CREATE FUNCTION truss.runtime_owned_row_validate_qualified(');end=source.index('\nEND;\n$$;',start);body=source[start:end]
    legacy=body.split(' FOR creation_transition IN ',1)[1].split(' LOOP\n',1)[0]
    owned=body.split(' FOR owned_transition IN\n',1)[1].split('\n LOOP',1)[0]
    latest=body.split(' SELECT * INTO latest FROM ',1)[1].split(';\n IF NOT FOUND',1)[0];latest='SELECT * FROM '+latest
    journal=body.split(' FOR entry IN SELECT j.value FROM ',1)[1].split(' LOOP\n',1)[0];journal='SELECT j.value FROM '+journal
    result={}
    for name,query in [('legacy_create',legacy),('owned',owned),('latest',latest),('journal',journal)]:
        for old,new in [('selected_id','$1'),('selected_type','$2'),('current_actor','$3')]:query=re.sub(r'\b'+old+r'\b',lambda m,new=new:new,query)
        # All statements use a uniform signature; unused $3 remains an explicit
        # PREPARE parameter rather than altering the original selected query.
        result[name]=query
    REPORT['operationsSourceSha256']=hashlib.sha256(source.encode()).hexdigest();REPORT['queries']=result;return result
class TransitionPlans(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
    def tearDown(self):
        try:super().tearDown();REPORT['fixtureCleanup']='passed'
        finally:save()
    def test_same_writer_exact_transition_queries(self):
        c,h,a,t=self.ready(document_ids=('adoc',));identities=[]
        for batch in range(10):
            context=a.group_context_in_transaction(t).value
            operations=tuple(self.create(label=f'probe-{batch*100+i:04}',alias=f'p{batch*100+i}') for i in range(100))
            started=time.monotonic();outcome=a.apply_in_transaction(t,context.input(operations,MapValue(entries=())),context.request(f'plan-populate-{batch}'),documents=self.documents)
            self.assertIsInstance(outcome,Ok,repr(outcome)+' '+str(h._custody.last_attempt.error));self.assertIsInstance(outcome.value,GroupSuccess,repr(outcome))
            results=outcome.value.response.semantic.results;self.assertEqual(len(results),100);identities.extend(r.identity for r in results)
            REPORT['setup'].append({'batch':batch,'publicOperations':100,'seconds':time.monotonic()-started});save();print('public population batch',batch,'complete',flush=True)
        h.detach()
        self.admin.execute('GRANT SELECT ON truss.runtime_object_transition,truss.runtime_object_attempt,truss.runtime_catalog_rebind_transition,truss.runtime_catalog_key_backfill TO consumer')
        self.admin.execute('GRANT EXECUTE ON FUNCTION truss.runtime_owned_profile() TO consumer')
        REPORT['diagnosticPrivileges']='Fixture-only SELECT on four private transition/attempt tables plus EXECUTE on immutable profile helper; no public API support claim.'
        writer,actor=c.execute("SELECT pg_current_xact_id()::text,(SELECT oid FROM pg_roles WHERE rolname=session_user)").fetchone()
        count=c.execute('SELECT count(*) FROM truss.runtime_object_transition WHERE writer_xid=pg_current_xact_id()').fetchone()[0];self.assertEqual(count,1000)
        REPORT['sameWriter']={'writerXid':writer,'actorOid':actor,'transitions':count,'committed':False}
        REPORT['statistics']=c.execute("SELECT relname,relpages,reltuples,pg_relation_size(oid) FROM pg_class WHERE oid IN ('truss.runtime_object_transition'::regclass,'truss.runtime_object_attempt'::regclass)").fetchall()
        REPORT['indexes']=c.execute("SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='truss' AND tablename='runtime_object_transition' ORDER BY indexname").fetchall()
        c.execute("SET LOCAL search_path=pg_catalog,pg_temp")
        c.execute("SET LOCAL row_security=off")
        c.execute("SET LOCAL TimeZone='UTC'")
        c.execute("SET LOCAL bytea_output=hex")
        c.execute('SET LOCAL plan_cache_mode=force_generic_plan');REPORT['plans']={}
        with psycopg.ClientCursor(c) as cursor:
            for name,query in queries().items():
                c.execute('PREPARE transition_'+name+'(bigint,int,oid) AS '+query,prepare=False);REPORT['plans'][name]=[]
                for index in (0,499,999):
                    identity=identities[index]
                    cursor.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) EXECUTE transition_'+name+'(%s,%s,%s)',(identity.id,identity.type_id,actor))
                    REPORT['plans'][name].append({'recordIndex':index,'plan':cursor.fetchone()[0]});save()
                c.execute('DEALLOCATE transition_'+name,prepare=False)
        c.rollback();REPORT['callerRollback']='completed';REPORT['result']='exact plans captured';save()
if __name__=='__main__':unittest.main(verbosity=2)
