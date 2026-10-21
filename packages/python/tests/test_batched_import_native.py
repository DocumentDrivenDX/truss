# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native fixed-client-call imports retain original per-record outcomes and custody."""
from dataclasses import replace
from truss import (Ok,ModuleAccessGrant,ModuleAuditGrant,LoadAuditInvocationSummary,
                   LoadAuditListingEnd,adopt_psycopg_host,create_reference_assembly,
                   CatalogRuntimeConfiguration)
from truss.batched_import import ObjectImportDraft, BatchedImportExecutionResult
from truss.contracts import MapValue,MapEntry,TextValue
from truss.imports import ImportReported, ImportCreated, ImportSkipped, ImportRejected, ImportConsistencyLimits, check_import_report_consistency
import test_import_runtime_native as legacy

class BatchedImportTests(legacy.ImportRuntimeTests):
    for _name in tuple(n for n in dir(legacy.ImportRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None

    def tearDown(self):
        self.admin.execute('DROP TABLE IF EXISTS public.empty_load_commit_probe')
        self.admin.execute('DROP FUNCTION IF EXISTS public.empty_load_commit_reject()')
        super().tearDown()

    def build(self,assembly,tx,count,prefix='row-'):
        result=assembly.build_import_records_in_transaction(tx,tuple(ObjectImportDraft(document_id='adoc',module_id='m',record_id='A',
            values=self.create(label=prefix+str(i),value=str(i)).values) for i in range(count)))
        self.assertIsInstance(result,Ok,repr(result)+' '+str(assembly._host._custody.last_attempt.error))
        return result.value

    def run_batch(self,assembly,tx,built,records=None,chunk_size=128):
        input=built.context.input(built.records if records is None else records,load_id='batch',asserted_origin=MapValue(entries=()),chunk_size=chunk_size)
        result=assembly.import_batched_in_transaction(tx,input,documents=self.documents)
        self.assertIsInstance(result,BatchedImportExecutionResult,repr(result))
        self.assertIsInstance(result.result,ImportReported,repr(result)+' '+str(assembly._host._custody.last_attempt.error))
        return result

    def test_create_skip_reject_original_indices_and_caller_rollback(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',));built=self.build(assembly,tx,3)
        invalid=replace(built.records[2],payload=built.context.object_payload(()))
        result=self.run_batch(assembly,tx,built,records=(built.records[0],built.records[0],invalid),chunk_size=2)
        report=result.result.report
        self.assertEqual([type(o) for o in report.outcomes],[ImportCreated,ImportSkipped,ImportRejected])
        self.assertEqual((report.counts.created_pending,report.counts.skipped,report.counts.rejected),('1','1','1'))
        self.assertEqual(len(report.batches),2)
        self.assertEqual(check_import_report_consistency(report,expected_input_count='3',limits=ImportConsistencyLimits(maximum_records=1024,maximum_decimal_digits=20,maximum_text_units=1048576)).result,'consistent')
        host.detach();connection.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_import_load_chunk').fetchone(),(0,))

    def test_1024_count_and_zero_record_pending_load(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',));built=self.build(assembly,tx,1024)
        result=self.run_batch(assembly,tx,built)
        self.assertEqual(result.result.report.counts.created_pending,'1024')
        self.assertEqual(len(result.result.report.batches),8)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1024,))
        connection,host,assembly,tx=self.consumer();empty=self.build(assembly,tx,0)
        result=self.run_batch(assembly,tx,empty)
        self.assertEqual(result.empty_load_settlement.disposition,'pending')
        self.assertEqual(result.result.report.batches,())
        host.detach();connection.rollback()

    def engine_input(self,count,chunk_size=2):
        import psycopg
        c,h,a,t=self.ready(document_ids=('adoc',));built=self.build(a,t,count)
        input=built.context.input(built.records,load_id='engine',asserted_origin=MapValue(entries=()),chunk_size=chunk_size)
        params=psycopg.conninfo.conninfo_to_dict(self.runtime.info.connection_uri);params['user']='consumer'
        info=psycopg.conninfo.make_conninfo(**params);h.detach();c.rollback()
        return input,info

    def engine(self,input,info):
        from truss import run_import_batches
        return run_import_batches(input,connection_info=info,documents=self.documents,statement_timeout_ms=10000,operation_timeout_ms=30000)

    def test_engine_chunks_and_empty_load_settlement_are_durable(self):
        input,info=self.engine_input(3)
        result=self.engine(input,info)
        self.assertIsInstance(result.result,ImportReported,repr(result))
        self.assertEqual(result.result.report.counts.created_committed,'3')
        self.assertEqual([b.disposition for b in result.result.report.batches],['committed','committed'])
        self.assertIsNone(result.empty_load_settlement)
        empty=self.engine(replace(input,records=()),info)
        self.assertIsInstance(empty.result,ImportReported,repr(empty))
        self.assertEqual(empty.empty_load_settlement.disposition,'committed')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_import_load_chunk').fetchone(),(3,))

    def test_engine_cleanup_fault_retains_confirmed_empty_load(self):
        from unittest.mock import patch
        from truss.engine_import import _EngineImportSession
        from truss.imports import ImportExecutionFailed
        input,info=self.engine_input(0)
        original=_EngineImportSession.close
        def close(session):
            original(session)
            raise OSError('fixture cleanup failure')
        with patch.object(_EngineImportSession,'close',close):result=self.engine(input,info)
        self.assertIsInstance(result,BatchedImportExecutionResult)
        self.assertIsInstance(result.result,ImportExecutionFailed)
        self.assertEqual(result.empty_load_settlement.disposition,'committed')
        self.assertIsNotNone(result.result.report)

    def test_builder_and_chunk_client_statement_budget_is_fixed(self):
        import json,os,time
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        original=host._cursor;queries=[]
        class Counted:
            def __init__(self,cursor):self.cursor=cursor
            def __getattr__(self,name):return getattr(self.cursor,name)
            def execute(self,query,*args,**kwargs):
                queries.append(str(query));return self.cursor.execute(query,*args,**kwargs)
        host._cursor=lambda:Counted(original())
        measurements=[]
        for count in (32,64,128):
            queries.clear();started=time.perf_counter();built=self.build(assembly,tx,count,prefix=str(count)+'-')
            builder_elapsed=time.perf_counter()-started;builder_statements=len(queries)
            queries.clear();started=time.perf_counter();result=self.run_batch(assembly,tx,built)
            elapsed=time.perf_counter()-started
            self.assertEqual(len(queries),6)
            self.assertEqual(builder_statements,3)
            measurements.append({'records':count,'builderClientStatements':builder_statements,'executeClientStatements':len(queries),
                'builderSeconds':builder_elapsed,'executeSeconds':elapsed,'created':result.result.report.counts.created_pending,'skipped':result.result.report.counts.skipped})
        # Optional receipt destination does not alter the measured path.
        if os.environ.get('TRUSS_BATCH_MEASUREMENT'):
            from pathlib import Path
            Path(os.environ['TRUSS_BATCH_MEASUREMENT']).write_text(json.dumps(measurements,indent=2)+'\n')
        host.detach();connection.rollback()

    def test_many_small_chunks_and_1025_envelope_refusal(self):
        from truss.imports import ImportInvalid
        connection,host,assembly,tx=self.ready(document_ids=('adoc',));built=self.build(assembly,tx,33)
        result=self.run_batch(assembly,tx,built,chunk_size=1)
        self.assertEqual(result.result.report.counts.created_pending,'33')
        self.assertEqual(len(result.result.report.batches),33)
        oversized=built.context.input((built.records[0],)*1025,load_id='too-many',asserted_origin=MapValue(entries=()))
        refused=assembly.import_batched_in_transaction(tx,oversized,documents=self.documents)
        self.assertIsInstance(refused.result,ImportInvalid)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(33,))

    def test_empty_engine_unknown_ack_retains_explicit_unknown_load(self):
        from unittest.mock import patch
        from truss.engine_import import _EngineImportSession
        from truss.imports import ImportExecutionFailed
        from truss.execution import ExecutionFailure
        input,info=self.engine_input(0)
        original=_EngineImportSession.control
        def control(session,command,settlements):
            observed,error=original(session,command,settlements)
            if command=='COMMIT':return None,ExecutionFailure('commit_unknown','fixture lost acknowledgement')
            return observed,error
        with patch.object(_EngineImportSession,'control',control):result=self.engine(input,info)
        self.assertIsInstance(result.result,ImportExecutionFailed)
        self.assertEqual(result.result.error.code,'commit_unknown')
        self.assertEqual(result.empty_load_settlement.disposition,'commit_unknown')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_import_load_chunk').fetchone(),(1,))

    def test_malformed_later_chunk_response_is_contained_and_keeps_prior_work(self):
        import json
        from unittest.mock import patch
        from truss.imports import ImportExecutionFailed
        from truss import _batched_import_runtime as runtime
        connection,host,assembly,tx=self.ready(document_ids=('adoc',));built=self.build(assembly,tx,3)
        original=json.loads;chunks=[]
        def decode(*args,**kwargs):
            value=original(*args,**kwargs)
            if type(value) is dict and set(value)=={'context','outcomes','hostTransactionId'}:
                chunks.append(1)
                if len(chunks)==2:value.pop('hostTransactionId')
            return value
        input=built.context.input(built.records,load_id='response-fault',asserted_origin=MapValue(entries=()),chunk_size=2)
        with patch.object(runtime.json,'loads',decode):result=assembly.import_batched_in_transaction(tx,input,documents=self.documents)
        self.assertIsInstance(result.result,ImportExecutionFailed,repr(result))
        self.assertIsNotNone(result.result.report,repr(result))
        self.assertEqual(result.result.report.counts.created_pending,'2')
        self.assertEqual(result.result.report.unprocessed_indices,('2',))
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(2,))

    def test_malformed_later_engine_response_keeps_prior_confirmed_chunk(self):
        import json
        from unittest.mock import patch
        from truss.imports import ImportExecutionFailed
        from truss import _batched_import_runtime as runtime
        input,info=self.engine_input(3);original=json.loads;chunks=[]
        def decode(*args,**kwargs):
            value=original(*args,**kwargs)
            if type(value) is dict and set(value)=={'context','outcomes','hostTransactionId'}:
                chunks.append(1)
                if len(chunks)==2:value['context']['selectedConfiguration'].pop('generation')
            return value
        with patch.object(runtime.json,'loads',decode):result=self.engine(input,info)
        self.assertIsInstance(result.result,ImportExecutionFailed,repr(result))
        self.assertIsNotNone(result.result.report,repr(result))
        self.assertEqual(result.result.report.counts.created_committed,'2')
        self.assertEqual(result.result.report.unprocessed_indices,('2',))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(2,))

    def test_empty_engine_confirmed_commit_rejection_is_rolled_back(self):
        from unittest.mock import patch
        from truss.engine_import import _EngineImportSession
        from truss.imports import ImportExecutionFailed
        input,info=self.engine_input(0)
        self.admin.execute('CREATE TABLE public.empty_load_commit_probe(n integer)')
        self.admin.execute("CREATE FUNCTION public.empty_load_commit_reject() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN RAISE EXCEPTION 'fixture deferred rejection' USING ERRCODE='23514';END;$$")
        self.admin.execute('CREATE CONSTRAINT TRIGGER empty_load_commit_reject AFTER INSERT ON public.empty_load_commit_probe DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.empty_load_commit_reject()')
        self.admin.execute('GRANT INSERT ON public.empty_load_commit_probe TO consumer')
        original=_EngineImportSession.control
        def control(session,command,settlements):
            if command=='COMMIT':session.connection.execute('INSERT INTO public.empty_load_commit_probe VALUES(1)')
            return original(session,command,settlements)
        with patch.object(_EngineImportSession,'control',control):result=self.engine(input,info)
        self.assertIsInstance(result.result,ImportExecutionFailed,repr(result))
        self.assertEqual(result.empty_load_settlement.disposition,'rolled_back')
        self.assertEqual(result.result.error.sql_state,'23514')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_import_load_chunk').fetchone(),(0,))

    def test_nonempty_lost_commit_ack_and_cleanup_preserve_confirmed_prefix(self):
        from unittest.mock import patch
        from truss.engine_import import _EngineImportSession
        from truss.imports import ImportExecutionFailed
        from truss.execution import ExecutionFailure
        input,info=self.engine_input(3)
        original_control=_EngineImportSession.control
        original_close=_EngineImportSession.close
        commits=[]
        def control(session,command,settlements):
            observed,error=original_control(session,command,settlements)
            if command=='COMMIT':
                commits.append(1)
                if len(commits)==2:
                    return None,ExecutionFailure('commit_unknown','fixture lost second acknowledgement')
            return observed,error
        def close(session):
            original_close(session)
            raise OSError('fixture cleanup failure after uncertain commit')
        with patch.object(_EngineImportSession,'control',control),patch.object(_EngineImportSession,'close',close):
            result=self.engine(input,info)
        self.assertIsInstance(result.result,ImportExecutionFailed,repr(result))
        self.assertEqual(result.result.error.code,'commit_unknown')
        report=result.result.report
        self.assertEqual([b.disposition for b in report.batches],['committed','commit_unknown'])
        self.assertEqual((report.counts.created_committed,report.counts.created_commit_unknown),('2','1'))
        self.assertEqual(report.unprocessed_indices,())
        self.assertIsNone(result.empty_load_settlement)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(3,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_import_load_chunk').fetchone(),(2,))
