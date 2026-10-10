"""Compiler boundary controls with synthetic responses; no SQL/native oracle."""
import copy
from dataclasses import FrozenInstanceError
from decimal import Decimal
import hashlib
import json
import unittest
from truss.weft import CompilerBoundary, CompileRefusal


def fixture():
    digest = hashlib.sha256(b'{}').hexdigest()
    pin = {'documentId':'d','revision':'1','umfVersion':'0.7.0','sha256':digest}
    target = {'backendId':'truss.postgresql','backendVersion':'fixture',
              'targetProfile':'fixture','bindingJson':'{}','bindingSha256':digest}
    request = {'interfaceVersion':'weft-compile/0.2.0','dialect':'weft-sql/0.2.0',
               'target':target,'modules':[{'documentJson':'{}','pin':pin}]}
    response = {'interfaceVersion':'weft-compile/0.2.0','dialect':'weft-sql/0.2.0',
                'status':'compiled','backend':{**target,'interfaceVersion':'weft-backend/0.2.0'},'bindingSha256':digest,
                'modelPins':[pin],'sql':'SELECT fixture','parameters':[
                    {'position':1,'value':'9007199254740993'}],
                'columns':[{'name':'fixture'}],'obligations':[]}
    return request,response


class CompilerBoundaryTests(unittest.TestCase):
    def test_retains_originals_and_freezes_nested_artifacts(self):
        request,response = fixture()
        original = json.dumps(request).encode()
        raw = json.dumps(response)[:-1]+',"metadata":0.12345678901234567890123456789}'
        result = CompilerBoundary(lambda _:raw).compile_request(original)
        self.assertIs(result.original_request, original)
        self.assertEqual(result.original_response,raw.encode())
        self.assertEqual(result.artifact['metadata'],Decimal('0.12345678901234567890123456789'))
        self.assertEqual(result.artifact['parameters'][0]['value'],'9007199254740993')
        with self.assertRaises(TypeError): result.artifact['columns'][0]['name']='changed'
        with self.assertRaises(FrozenInstanceError): result.original_response=b'{}'

    def test_bad_input_refuses_before_compiler(self):
        request,_ = fixture(); calls=[]
        engine=CompilerBoundary(lambda x:calls.append(x))
        altered=copy.deepcopy(request);altered['target']['bindingJson']='{} '
        changed_model=copy.deepcopy(request);changed_model['modules'][0]['documentJson']='[]'
        missing=copy.deepcopy(request);del missing['target']['backendVersion']
        for value in [bytearray(b'{}'),b'\xff',b'{"a":1,"a":2}',b'['*129+b']'*129,
                      b'{"a":NaN}', b'{"a":'+b'9'*5000+b'}',
                      b'{"a":"\\ud800"}',json.dumps(altered).encode(),
                      json.dumps(changed_model).encode(),json.dumps(missing).encode()]:
            with self.subTest(value=str(value)[:50]),self.assertRaises(CompileRefusal):
                engine.compile_request(value)
        self.assertEqual(calls,[])

    def test_changed_and_new_artifacts_refuse_without_retry(self):
        request,response=fixture();original=json.dumps(request).encode()
        for mutation,code in [('backend','artifact_pin'),('carrier','artifact_version'),
                              ('positioned','artifact_version'),('version','artifact_pin'),
                              ('parameter','parameter'),('bool_position','parameter')]:
            changed=copy.deepcopy(response)
            if mutation=='backend': changed['backend']['targetProfile']='other'
            elif mutation=='carrier': changed['columns'][0]['carrierName']=None
            elif mutation=='positioned': changed['obligations'].append({'id':'weft.output.positioned'})
            elif mutation=='version': changed['interfaceVersion']='weft-compile/0.3.0'
            elif mutation=='parameter': changed['parameters'][0]['value']=9007199254740993
            else: changed['parameters'][0]['position']=True
            calls=[]
            engine=CompilerBoundary(lambda raw:calls.append(raw) or json.dumps(changed))
            with self.subTest(mutation=mutation),self.assertRaises(CompileRefusal) as error:
                engine.compile_request(original)
            self.assertEqual(error.exception.code,code);self.assertEqual(len(calls),1)

    def test_blocked_exception_and_disposal_publish_no_plan(self):
        request,response=fixture();original=json.dumps(request).encode();calls=[]
        def fail(raw):
            calls.append(raw);raise OSError('compiler callback failed')
        with self.assertRaises(OSError):CompilerBoundary(fail).compile_request(original)
        self.assertEqual(len(calls),1)
        blocked=CompilerBoundary(lambda _: '{"status":"blocked","diagnostics":[]}')
        with self.assertRaises(CompileRefusal) as error:blocked.compile_request(original)
        self.assertEqual(error.exception.code,'compiler_blocked')
        def dispose(_):
            engine.dispose();return json.dumps(response)
        engine=CompilerBoundary(dispose)
        with self.assertRaises(CompileRefusal) as error:engine.compile_request(original)
        self.assertEqual(error.exception.code,'disposed')
        with self.assertRaises(CompileRefusal):engine.compile_request(original)

    def test_reentrant_compilation_is_refused(self):
        request,response=fixture();original=json.dumps(request).encode();events=[]
        def compile_json(_):
            try:engine.compile_request(original)
            except CompileRefusal as error:events.append(error.code)
            return json.dumps(response)
        engine=CompilerBoundary(compile_json)
        engine.compile_request(original)
        self.assertEqual(events,['busy'])

    def test_async_compilers_refuse_without_execution_or_coroutine_leak(self):
        request, response = fixture()
        original = json.dumps(request).encode()
        calls = []
        async def asynchronous(_):
            calls.append('executed')
            return json.dumps(response)
        class AsyncCallable:
            async def __call__(self, value):
                return await asynchronous(value)
        async def asynchronous_generator(_):
            yield json.dumps(response)
        for callback in [asynchronous, AsyncCallable(), asynchronous_generator]:
            with self.subTest(callback=callback), self.assertRaises(CompileRefusal):
                CompilerBoundary(callback)
        created = []
        def wrapped(value):
            pending = asynchronous(value)
            created.append(pending)
            return pending
        engine = CompilerBoundary(wrapped)
        with self.assertRaises(CompileRefusal):
            engine.compile_request(original)
        self.assertIsNone(created[0].cr_frame)
        def wrapped_disposal(value):
            pending = wrapped(value)
            engine.dispose()
            return pending
        engine = CompilerBoundary(wrapped_disposal)
        with self.assertRaises(CompileRefusal):
            engine.compile_request(original)
        self.assertIsNone(created[1].cr_frame)
        self.assertEqual(calls, [])


if __name__=='__main__':unittest.main()
