"""Focused adapter lifecycle controls; real FETCH controls live in stream checks."""
from contextlib import contextmanager
from datetime import timedelta
import unittest
from unittest.mock import patch
from umf_access.types import StrictModel
from truss.access import TrussTarget
from truss.query import QueryRows
from truss.query_stream import QueryStreamBatch,QueryStreamRefused

class Parameters(StrictModel):pass
class Row(StrictModel):value:str
class Entry:
    parameters=Parameters
    result=Row
    def artifact(self):
        return {'version':'weft.engine-page/0.1','compiler':'truss-runtime',
                'request':{'target':{}},'pageSize':2}
    def originals(self):return '{}'

class StreamLimitTests(unittest.TestCase):
    def target(self,batches,*,cleanup_error=False):
        events=[]
        class Assembly:
            def query_stream_open_in_transaction(self,*args,**kwargs):
                events.append('open');return object()
            def query_stream_fetch_in_transaction(self,*args,validate,**kwargs):
                values,exhausted=batches.pop(0)
                return QueryStreamBatch(tuple(validate(QueryRows(columns=('value',),
                    rows=tuple((value,) for value in values),catalog_revision='1'))),exhausted)
            def query_stream_close_in_transaction(self,*args):events.append('close')
        @contextmanager
        def operation(budget):
            events.append('enter')
            try:yield Assembly(),object()
            finally:
                events.append('settle')
                if cleanup_error:raise RuntimeError('cleanup failed')
        target=object.__new__(TrussTarget)
        target.default_timeout=timedelta(seconds=10)
        target.native_target_json='{}';target.stream_operation=operation
        return target,events

    def test_bound_emits_prefix_then_refuses_after_cleanup(self):
        target,events=self.target([(('a','b'),False),(('c',),False)])
        with patch('truss.access.EngineRead',Entry):
            stream=target.stream(Entry(),Parameters(),max_rows=3)
            self.assertEqual(next(stream).value,'a');self.assertNotIn('close',events)
            self.assertEqual(next(stream).value,'b');self.assertNotIn('settle',events)
            self.assertEqual(next(stream).value,'c');self.assertEqual(events[-2:],['close','settle'])
            with self.assertRaises(QueryStreamRefused) as caught:next(stream)
        self.assertEqual(caught.exception.original.code,'limits')
        self.assertEqual(tuple(d.code for d in caught.exception.original.diagnostics),('stream_row_limit',))

    def test_proven_exhaustion_completes_normally(self):
        target,events=self.target([(('a',),True)])
        with patch('truss.access.EngineRead',Entry):
            self.assertEqual([r.value for r in target.stream(Entry(),Parameters(),max_rows=2)],['a'])
        self.assertEqual(events[-2:],['close','settle'])

    def test_cleanup_failure_prevents_final_page_and_limit_refusal(self):
        target,events=self.target([(('a','b'),False)],cleanup_error=True)
        with patch('truss.access.EngineRead',Entry):
            with self.assertRaisesRegex(RuntimeError,'cleanup failed'):
                next(target.stream(Entry(),Parameters(),max_rows=2))
        self.assertEqual(events[-2:],['close','settle'])

    def test_cleanup_deadline_prevents_final_page_and_limit_refusal(self):
        from umf_access.postgres_read import TimedOut
        target,events=self.target([(('a','b'),False)])
        with patch('truss.access.EngineRead',Entry),patch('truss.access.monotonic',side_effect=(0,1,11)):
            with self.assertRaises(TimedOut):
                next(target.stream(Entry(),Parameters(),max_rows=2))
        self.assertEqual(events[-2:],['close','settle'])

    def test_early_close_settles_without_fetching_another_page(self):
        batches=[(('a','b'),False),(('c',),True)]
        target,events=self.target(batches)
        with patch('truss.access.EngineRead',Entry):
            stream=target.stream(Entry(),Parameters(),max_rows=5)
            self.assertEqual(next(stream).value,'a');stream.close()
        self.assertEqual(len(batches),1);self.assertEqual(events[-2:],['close','settle'])

if __name__=='__main__':unittest.main()
