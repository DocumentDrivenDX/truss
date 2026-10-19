# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic public engine-owned import durability and interrupted progress."""
import os
from dataclasses import replace
from unittest.mock import patch
import psycopg
from truss import run_import_batches
from truss.contracts import MapValue,MapEntry,TextValue
from truss.imports import ImportReported,ImportExecutionFailed,ImportCreated,ImportSkipped,ImportRejected
import test_import_runtime_native as base

class EngineImportTests(base.ImportRuntimeTests):
    for _name in tuple(n for n in dir(base.ImportRuntimeTests) if n.startswith('test_')):locals()[_name]=None
    def tearDown(self):
        self.admin.execute('DROP TABLE IF EXISTS public.engine_commit_probe')
        self.admin.execute('DROP FUNCTION IF EXISTS public.engine_commit_reject()')
        super().tearDown()
    def prepared_input(self,labels):
        c,h,a,t=self.ready();context=a.import_context_in_transaction(t).value
        records=tuple(self.record(a,t,label=label) for label in labels)
        input=context.input(records,load_id='engine-load',asserted_origin=MapValue(entries=(MapEntry(key='x-initiated-by',value=TextValue(kind='string',text='adapter')),)))
        params=psycopg.conninfo.conninfo_to_dict(self.runtime.info.connection_uri);params['user']='consumer';info=psycopg.conninfo.make_conninfo(**params)
        h.detach();c.rollback()
        return input,context,info
    def run_batches(self,input,info):
        return run_import_batches(input,connection_info=info,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'),statement_timeout_ms=10000,operation_timeout_ms=30000)
    def test_create_skip_reject_provenance_and_repeat(self):
        input,context,info=self.prepared_input(('one','bad'))
        first=input.records[0];duplicate=replace(first,payload=self.artifact(b'not a valid replacement'))
        bad=replace(input.records[1],payload=context.object_payload(()));input=replace(input,records=(first,duplicate,bad))
        result=self.run_batches(input,info);self.assertIsInstance(result,ImportReported,repr(result));report=result.report
        self.assertEqual(report.execution,'engine_owned');self.assertEqual([type(v) for v in report.outcomes],[ImportCreated,ImportSkipped,ImportRejected]);self.assertEqual((report.counts.created_committed,report.counts.created_pending,report.counts.skipped,report.counts.rejected),('1','0','1','1'));self.assertEqual([b.disposition for b in report.batches],['committed','committed','rolled_back'])
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,));self.assertEqual(self.admin.execute('SELECT load_id FROM truss.record_source').fetchall(),[('engine-load',)])
        repeated=self.run_batches(input,info);self.assertIsInstance(repeated,ImportReported,repr(repeated));self.assertEqual((repeated.report.counts.created_committed,repeated.report.counts.skipped,repeated.report.counts.rejected),('0','2','1'));self.assertNotEqual(report.attempt_id,repeated.report.attempt_id);self.assertEqual(report.input_sha256,repeated.report.input_sha256)
        empty=self.run_batches(replace(input,records=()),info);self.assertIsInstance(empty,ImportReported);self.assertEqual(empty.report.outcomes,());self.assertEqual(empty.report.batches,())
    def test_later_confirmed_rollback_preserves_earlier_commit(self):
        input,context,info=self.prepared_input(('one','two','three'))
        from truss.engine_import import _EngineImportSession
        self.admin.execute('CREATE TABLE public.engine_commit_probe(n integer)')
        self.admin.execute("CREATE FUNCTION public.engine_commit_reject() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN RAISE EXCEPTION 'fixture deferred rejection' USING ERRCODE='23514';END;$$")
        self.admin.execute('CREATE CONSTRAINT TRIGGER engine_commit_reject AFTER INSERT ON public.engine_commit_probe DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.engine_commit_reject()')
        self.admin.execute('GRANT INSERT ON public.engine_commit_probe TO consumer')
        original=_EngineImportSession.settle;calls=[]
        def settle(session,batch,*,commit):
            if commit:
                calls.append(batch.batch_id)
                if len(calls)==2:
                    # A real server rejection during COMMIT confirms rollback.
                    session.connection.execute('INSERT INTO public.engine_commit_probe VALUES(2)')
            return original(session,batch,commit=commit)
        with patch.object(_EngineImportSession,'settle',settle):result=self.run_batches(input,info)
        self.assertIsInstance(result,ImportExecutionFailed,repr(result));self.assertEqual(result.error.sql_state,'23514');report=result.report;self.assertIsNotNone(report,repr(result));self.assertEqual(report.execution,'engine_owned');self.assertEqual(report.status,'interrupted');self.assertEqual([b.disposition for b in report.batches],['committed','rolled_back']);self.assertEqual((report.counts.created_committed,report.counts.created_rolled_back,report.counts.created_pending),('1','1','0'));self.assertEqual(report.unprocessed_indices,('2',));self.assertEqual(len(calls),2)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))
        repeated=self.run_batches(input,info);self.assertIsInstance(repeated,ImportReported);self.assertEqual((repeated.report.counts.created_committed,repeated.report.counts.skipped),('2','1'));self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(3,))
