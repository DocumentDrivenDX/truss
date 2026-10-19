# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual public Graph candidate refuses without a qualified authority protocol.

The local PG18.6 caller fixture is not SCRAM or complete B-008 qualification.
"""
import os,unittest
from contextlib import ExitStack
from unittest.mock import patch
from truss import Ok,Error,CurrentDisclosureExecutor,adopt_psycopg_host
from truss.query import QueryRefused
import truss._current_query_runtime as runtime
import truss._current_query_subjects as subjects
import test_current_disclosure_runtime_native as base


@unittest.skipUnless(os.environ.get('TRUSS_GRAPH_ADMISSION_NATIVE_QUALIFICATION')=='1',
                     'explicit serialized Graph refusal qualification required')
class CurrentGraphAdmissionNativeTests(base.CurrentDisclosureRuntimeNativeTests):
    for name in tuple(n for n in dir(base.CurrentDisclosureRuntimeNativeTests) if n.startswith('test_')):
        locals()[name]=None

    def query(self,*,partial=False,settled=False,legacy=False):
        original=subjects._helper_source
        def old_helper(*args,**kwargs):
            source=original(*args,**kwargs)
            complete='LOCK TABLE ONLY truss.module_access,truss.object,truss.object_key_bucket,truss.edge IN SHARE MODE NOWAIT;'
            self.assertIn(complete,source)
            return source.replace(complete,'LOCK TABLE ONLY truss.object IN SHARE MODE NOWAIT;')
        with patch.object(subjects,'_helper_source',side_effect=old_helper) if partial else ExitStack():
            bun=self.create_query_graph()
        import json
        self.assertEqual(json.loads(self.originals.consumer_bytes)['weftModuleSha256'],runtime._GRAPH_CONSUMER_MODULE)
        if legacy:
            from psycopg import sql
            marker=json.loads(self.admin.execute('SELECT truss.current_query_protection_marker()').fetchone()[0])
            marker['profile']='truss-current-query-protection/0.1-candidate'
            body='SELECT '+sql.Literal(json.dumps(marker,sort_keys=True,separators=(',',':'))).as_string()+'::pg_catalog.text'
            self.admin.execute(sql.SQL('CREATE OR REPLACE FUNCTION truss.current_query_protection_marker() RETURNS text LANGUAGE sql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS {}').format(sql.Literal(body)))
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        executor=CurrentDisclosureExecutor(self.host,self.tx,self.current_subject_registration,bun_executable=bun)
        caller,host,assembly,transaction=self.consumer()
        if settled:host.detach();caller.rollback()
        with ExitStack() as stack:
            collectors=[stack.enter_context(patch(target)) for target in (
                'truss._current_query_runtime.capture_current_query_facts_with_cursor',
                'truss._current_disclosure_context_capture.capture_context_disclosure_with_cursor',
                'truss._current_disclosure_evaluation.evaluate_and_stage_current_disclosure')]
            result=assembly.query_current_disclosure_in_transaction(transaction,executor=executor,
                sql='SELECT r.salary FROM Resource r',document_ids=('domain',))
            for collector in collectors:collector.assert_not_called()
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_catalog.pg_class WHERE relnamespace=pg_catalog.pg_my_temp_schema() AND relname LIKE 'truss_presence_%'").fetchone(),(0,))
        return result,host,caller,transaction

    def test_matching_legacy_graph_activation_refuses_before_collection(self):
        result,host,caller,transaction=self.query(legacy=True)
        self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.assertIsInstance(result.value,QueryRefused)
        self.assertEqual(result.value.code,'execution_obligation')

    def test_matching_partial_helper_registration_refuses_before_collection(self):
        result,host,caller,transaction=self.query(partial=True)
        self.assertIsInstance(result,Error)
        self.assertIn('complete ordinary caller Graph source/data cut',str(host._custody.last_attempt.error))

    def test_settled_caller_refuses_without_collection(self):
        result,host,caller,transaction=self.query(settled=True)
        self.assertIsInstance(result,Ok)
        self.assertIsInstance(result.value,QueryRefused)
        self.assertEqual(result.value.code,'stale_context')
