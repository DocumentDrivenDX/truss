"""Actual multi-attempt imports do linear graph validation at finish and commit."""
import json,time
from truss import Ok
import test_import_runtime_native as base
class ImportChunkClosureTests(base.ImportRuntimeTests):
    for name in tuple(n for n in dir(base.ImportRuntimeTests) if n.startswith('test_')):locals()[name]=None
    def test_thirty_two_imports_do_not_rescan_other_attempts(self):
        c,h,a,t=self.ready();h.detach();c.rollback()
        self.admin.execute("ALTER ROLE consumer SET track_functions='all'")
        c,h,a,t=self.consumer();context=a.import_context_in_transaction(t).value
        records=tuple(self.record(a,t,label='chunk-'+str(i)) for i in range(32))
        started=time.perf_counter();report=self.execute(a,t,context,records,'chunk-32')
        applied=time.perf_counter();self.assertEqual(report.counts.created_pending,'32')
        h.detach();c.commit();committed=time.perf_counter()
        c.execute('SELECT pg_stat_force_next_flush()');self.admin.execute('SELECT pg_stat_clear_snapshot()')
        calls=self.admin.execute("SELECT calls FROM pg_stat_user_functions WHERE funcid='truss.runtime_graph_validate_object_qualified(bigint,integer,boolean,oid)'::regprocedure").fetchone()[0]
        self.assertGreaterEqual(calls,32)
        self.assertLessEqual(calls,32*5,'Each attempt must validate its own affected graph, not every other import attempt')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(32,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.record_source').fetchone(),(32,))
        print(json.dumps({'records':32,'applySeconds':applied-started,'commitSeconds':committed-applied,'graphValidationCalls':calls}),flush=True)
