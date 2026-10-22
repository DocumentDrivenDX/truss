import unittest,time,json,os,cProfile,pstats,io,threading,subprocess
from collections import Counter
from unittest.mock import patch
import psycopg,psutil
from truss.psycopg_host import _GuardedCursor
from test_batched_import_native import BatchedImportTests

class Cost(BatchedImportTests):
    for name in tuple(n for n in dir(BatchedImportTests) if n.startswith('test_')):locals()[name]=None
    def test_cost(self):
        from psycopg import sql
        c,h,a,t=self.ready(document_ids=('adoc',))
        self.admin.execute('CREATE TABLE public.import_cost_counts(home text,rows_written bigint)')
        self.addCleanup(self.admin.execute,'DROP TABLE IF EXISTS public.import_cost_counts')
        self.admin.execute('''CREATE FUNCTION public.import_cost_insert() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN INSERT INTO public.import_cost_counts SELECT TG_TABLE_NAME,count(*) FROM new_rows;RETURN NULL; END;$$''')
        self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.import_cost_insert() CASCADE')
        for home in ('object','journal','runtime_owned_operation'):
            self.admin.execute(sql.SQL('CREATE TRIGGER import_cost_insert AFTER INSERT ON truss.{} REFERENCING NEW TABLE AS new_rows FOR EACH STATEMENT EXECUTE FUNCTION public.import_cost_insert()').format(sql.Identifier(home)))
        receipts=[]
        for size in (128,256,512,1024):
            # Separate transaction per workload, current ordinary person and exact build/import APIs.
            waits=Counter();stopped=threading.Event();monitor=psycopg.connect(self.info.connection_uri,autocommit=True)
            def sample():
                while not stopped.wait(.02):
                    row=monitor.execute('SELECT state,wait_event_type,wait_event FROM pg_stat_activity WHERE pid=%s',(c.info.backend_pid,)).fetchone()
                    if row:waits[str(row)]+=1
            sampler=threading.Thread(target=sample,daemon=True);sampler.start()
            calls=Counter();original=_GuardedCursor.execute
            def observe(cursor,query,*args,**kwargs):
                text=str(query);calls['clientStatements']+=1
                for needle in ('person_build_import_records','person_process_import_chunk','person_validate_batched_import_report'):
                    if needle in text:calls[needle]+=1
                return original(cursor,query,*args,**kwargs)
            native_process=psutil.Process(c.info.backend_pid);native_start=native_process.cpu_times()
            profiler=cProfile.Profile();start=time.monotonic();cpu=time.process_time()
            with patch.object(_GuardedCursor,'execute',observe):
                profiler.enable();built=self.build(a,t,size,prefix=f'cost-{size}-');build=time.monotonic()-start
                result=self.run_batch(a,t,built);profiler.disable()
            elapsed=time.monotonic()-start;python_cpu=time.process_time()-cpu;stopped.set();sampler.join();monitor.close()
            self.assertEqual(result.result.report.counts.created_pending,str(size));describe_start=time.monotonic();catalog=a.reader_catalog_in_transaction(t);describe_seconds=time.monotonic()-describe_start
            self.assertEqual(catalog.status,'ok')
            commit_start=time.monotonic();h.detach();c.commit();commit_seconds=time.monotonic()-commit_start;native_end=native_process.cpu_times()
            counts=self.admin.execute('SELECT home,count(*),sum(rows_written)::bigint FROM public.import_cost_counts GROUP BY home').fetchall()
            groups=self.admin.execute('SELECT count(DISTINCT group_attempt_id),count(*) FROM truss.runtime_import_source').fetchone()
            stream=io.StringIO();pstats.Stats(profiler,stream=stream).sort_stats('cumulative').print_stats(18)
            receipt=dict(records=size,buildSeconds=build,totalSeconds=elapsed,pythonCpuSeconds=python_cpu,describeSeconds=describe_seconds,commitSeconds=commit_seconds,nativeCpuSeconds=(native_end.user-native_start.user)+(native_end.system-native_start.system),endToEndThroughCommitSeconds=time.monotonic()-start,clientCalls=dict(calls),nativeStatements=counts,cumulativeNativeGroups=groups,waitSamples=dict(waits),pythonProfile=stream.getvalue())
            receipts.append(receipt);print(json.dumps(receipt),flush=True)
            self.admin.execute('TRUNCATE public.import_cost_counts')
            c,h,a,t=self.consumer()
        from pathlib import Path
        Path(os.environ['TRUSS_COST_RECEIPT']).write_text(json.dumps({'scope':'Synthetic macOS ARM64 native public import, fixed read-only samples and fixture statement triggers; no general latency or native CPU claim','runs':receipts},indent=2)+'\n')
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cost));raise SystemExit(not r.wasSuccessful())
