"""Independent coordinator ordering/fault controls; synthetic host only."""
from contextlib import contextmanager
import json
from types import SimpleNamespace
import unittest
from truss._query_execution import QueryCoordinator, QueryPlan
from truss.weft import CompilerBoundary, CompileRefusal
from test_weft import fixture


def coordinator(host=None, obligations=()):
    request,response=fixture()
    response['obligations']=list(obligations)
    engine=QueryCoordinator(CompilerBoundary(lambda _:json.dumps(response)),host)
    return engine,engine.compile_request(json.dumps(request).encode())


class QueryExecutionTests(unittest.TestCase):
    def host(self, events, *, rows=None, decode=None, drift=False, cleanup_failure=False):
        verifies=0
        def verify(_):
            nonlocal verifies
            verifies+=1;events.append('verify')
            if drift and verifies==2:raise RuntimeError('current context changed')
        def query(sql,parameters):
            events.append(('query',sql,parameters))
            return [['9007199254740993']] if rows is None else rows
        @contextmanager
        def context():
            events.append('enter')
            try:yield SimpleNamespace(verify_context=verify,query=query)
            finally:
                events.append('cleanup')
                if cleanup_failure:raise RuntimeError('cleanup unavailable')
        def decoder(_,actual):
            events.append('decode')
            return decode if decode is not None else [{'integerToken':actual[0][0]}]
        return SimpleNamespace(read_context=context,decode=decoder,handlers={})

    def test_missing_host_foreign_plan_and_unknown_obligation_never_acquire(self):
        engine,plan=coordinator()
        with self.assertRaises(CompileRefusal) as error:engine.execute(plan)
        self.assertEqual(error.exception.code,'runtime_unavailable')
        events=[];other,other_plan=coordinator(self.host(events))
        for foreign in [plan,QueryPlan(other_plan.compiled)]:
            with self.assertRaises(CompileRefusal) as error:other.execute(foreign)
            self.assertEqual(error.exception.code,'plan')
        unknown,unknown_plan=coordinator(self.host(events),[{'owner':'host','id':'unknown'}])
        with self.assertRaises(CompileRefusal) as error:unknown.execute(unknown_plan)
        self.assertEqual(error.exception.code,'obligation');self.assertEqual(events,[])

    def test_obligations_and_publication_recheck_have_original_order(self):
        events=[];host=self.host(events)
        host.handlers={'fixture':SimpleNamespace(accepts=lambda *_:True,
          check=lambda *_:events.append('check'))}
        engine,plan=coordinator(host,[{'owner':'host','id':'fixture'}])
        result=engine.execute(plan)
        self.assertEqual(events,['enter','verify','check',
          ('query','SELECT fixture',('9007199254740993',)),'decode','verify','cleanup'])
        self.assertEqual(result[0]['integerToken'],'9007199254740993')
        with self.assertRaises(TypeError):result[0]['integerToken']='different'

    def test_drift_cleanup_and_numeric_transport_withhold_results(self):
        for options,exception in [({'drift':True},RuntimeError),
                                   ({'cleanup_failure':True},RuntimeError),
                                   ({'rows':[[9007199254740993]]},CompileRefusal),
                                   ({'decode':[{'integerToken':9007199254740993}]},CompileRefusal),
                                   ({'decode':[{'text':'\ud800'}]},CompileRefusal),
                                   ({'rows':[['a','b']]},CompileRefusal)]:
            events=[];engine,plan=coordinator(self.host(events,**options))
            with self.subTest(options=options),self.assertRaises(exception):engine.execute(plan)
            self.assertEqual(events.count('enter'),1)
            self.assertEqual(events.count('cleanup'),1)
            self.assertLessEqual(sum(isinstance(e,tuple) and e[0]=='query' for e in events),1)

    def test_disposal_and_reentrancy_do_not_repeat_native_work(self):
        events=[];host=self.host(events)
        def check(*_):
            with self.assertRaises(CompileRefusal) as error:engine.execute(plan)
            self.assertEqual(error.exception.code,'busy')
            engine.dispose()
        host.handlers={'fixture':SimpleNamespace(accepts=lambda *_:True,check=check)}
        engine,plan=coordinator(host,[{'owner':'host','id':'fixture'}])
        with self.assertRaises(CompileRefusal) as error:engine.execute(plan)
        self.assertEqual(error.exception.code,'disposed')
        self.assertEqual(events,['enter','verify','cleanup'])
        with self.assertRaises(CompileRefusal):engine.execute(plan)
        self.assertEqual(events,['enter','verify','cleanup'])

    def test_suppressed_host_failure_cannot_become_empty_success(self):
        @contextmanager
        def suppress():
            try:
                yield SimpleNamespace(
                    verify_context=lambda _: (_ for _ in ()).throw(RuntimeError('failed')),
                    query=lambda *_: (_ for _ in ()).throw(AssertionError('unexpected query')))
            except RuntimeError:pass
        host=SimpleNamespace(read_context=suppress,decode=lambda *_:[],handlers={})
        engine,plan=coordinator(host)
        with self.assertRaises(CompileRefusal) as error:engine.execute(plan)
        self.assertEqual(error.exception.code,'context')

    def test_disposal_during_context_exit_withholds_buffered_result(self):
        events=[];host=self.host(events);original=host.read_context
        @contextmanager
        def dispose_on_exit():
            with original() as scope:yield scope
            engine.dispose()
        host.read_context=dispose_on_exit
        engine,plan=coordinator(host)
        with self.assertRaises(CompileRefusal) as error:engine.execute(plan)
        self.assertEqual(error.exception.code,'disposed')
        self.assertEqual(events[-1],'cleanup')

    def test_original_host_functions_are_captured_at_construction(self):
        events=[];host=self.host(events)
        engine,plan=coordinator(host)
        host.read_context=lambda: (_ for _ in ()).throw(RuntimeError('replaced context'))
        host.decode=lambda *_: (_ for _ in ()).throw(RuntimeError('replaced decoder'))
        self.assertEqual(engine.execute(plan)[0]['integerToken'],'9007199254740993')

    def test_async_and_nonvoid_checks_cannot_permit_sql(self):
        async def pending(*_):return None
        events=[];host=self.host(events)
        host.handlers={'fixture':SimpleNamespace(accepts=lambda *_:True,check=pending)}
        with self.assertRaises(CompileRefusal):coordinator(host)
        self.assertEqual(events,[])
        for check in [lambda *_:pending(),lambda *_:False,lambda *_:True]:
            events=[];host=self.host(events)
            host.handlers={'fixture':SimpleNamespace(accepts=lambda *_:True,check=check)}
            engine,plan=coordinator(host,[{'owner':'host','id':'fixture'}])
            with self.assertRaises(CompileRefusal) as error:engine.execute(plan)
            self.assertEqual(error.exception.code,'execution_obligation')
            self.assertEqual(events,['enter','verify','cleanup'])

        deferred = []
        def body():
            events.append('deferred body ran')
            yield None
        def deferred_check(*_):
            value = body()
            deferred.append(value)
            return value
        events=[];host=self.host(events)
        host.handlers={'fixture':SimpleNamespace(accepts=lambda *_:True,check=deferred_check)}
        engine,plan=coordinator(host,[{'owner':'host','id':'fixture'}])
        with self.assertRaises(CompileRefusal):engine.execute(plan)
        self.assertEqual(events,['enter','verify','cleanup'])
        self.assertIsNone(deferred[0].gi_frame)
        with self.assertRaises(StopIteration):next(deferred[0])
        self.assertEqual(events,['enter','verify','cleanup'])

    def test_async_context_verification_cannot_permit_sql(self):
        events=[]
        async def verify(*_):events.append('should never run')
        @contextmanager
        def context():
            events.append('enter')
            try:
                yield SimpleNamespace(verify_context=verify,
                  query=lambda *_:events.append('unexpected sql'))
            finally:events.append('cleanup')
        engine,plan=coordinator(SimpleNamespace(read_context=context,decode=lambda *_:[],handlers={}))
        with self.assertRaises(CompileRefusal) as error:engine.execute(plan)
        self.assertEqual(error.exception.code,'execution_obligation')
        self.assertEqual(events,['enter','cleanup'])

    def test_async_context_exit_cannot_publish_or_enter(self):
        events=[]
        class Manager:
            def __enter__(self):events.append('unexpected entry')
            async def __exit__(self,*_):events.append('unexpected async cleanup')
        host=SimpleNamespace(read_context=Manager,decode=lambda *_:[],handlers={})
        engine,plan=coordinator(host)
        with self.assertRaises(CompileRefusal) as error:engine.execute(plan)
        self.assertEqual(error.exception.code,'execution_obligation');self.assertEqual(events,[])

    def test_wrapped_async_cleanup_withholds_buffered_result(self):
        events=[];host=self.host(events);original=host.read_context
        async def pending_cleanup():events.append('should never run')
        class Manager:
            def __init__(self):self.original=original()
            def __enter__(self):return self.original.__enter__()
            def __exit__(self,*args):
                self.original.__exit__(*args)
                return pending_cleanup()
        host.read_context=Manager
        engine,plan=coordinator(host)
        with self.assertRaises(CompileRefusal) as error:engine.execute(plan)
        self.assertEqual(error.exception.code,'execution_obligation')
        self.assertEqual(events[-1],'cleanup');self.assertNotIn('should never run',events)


if __name__=='__main__':unittest.main()
