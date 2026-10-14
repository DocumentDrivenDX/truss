"""Registration custody controls; synthetic port does not qualify owner/native semantics."""
import hashlib
import json
import unittest
from pathlib import Path
import subprocess
from truss.bulk_action_gateway import ActionRegistration, GatewayRefusal


def artifact(body):
    return json.dumps({'mediaType':'application/json','utf8':body,'sha256':hashlib.sha256(body.encode()).hexdigest()}).encode()


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.model=artifact('{}')
        self.pin=json.dumps({'documentSha256':hashlib.sha256(b'{}').hexdigest()}).encode()
        self.preparation=artifact('{"owner":"synthetic-test"}')

    def test_retains_immutable_originals_and_grants_no_execution_api(self):
        registration=ActionRegistration(lambda model,pin:self.preparation)
        handle=registration.register(self.model,self.pin,self.preparation)
        self.assertEqual(registration.original(handle).model,self.model)
        self.assertEqual(registration.original(handle).preparation,self.preparation)
        self.assertFalse(hasattr(registration,'invoke'))
        with self.assertRaises(GatewayRefusal):registration.original(True)

    def test_foreign_and_forged_action_tickets_cannot_select_another_registry(self):
        a=ActionRegistration(lambda *args:self.preparation)
        b=ActionRegistration(lambda *args:self.preparation)
        ticket=a.register(self.model,self.pin,self.preparation)
        b.register(self.model,self.pin,self.preparation)
        with self.assertRaises(GatewayRefusal):b.original(ticket)
        with self.assertRaises(GatewayRefusal):a.original(type(ticket)())

    def test_envelope_escape_and_exact_payload_bounds_are_separate(self):
        for length in (600000,1048576):
            body='{"data":"'+('x'*(length-11))+'"}'
            model=artifact(body);pin=json.dumps({'documentSha256':hashlib.sha256(body.encode()).hexdigest()}).encode()
            registration=ActionRegistration(lambda *args:self.preparation)
            registration.register(model,pin,self.preparation)
        body=json.dumps({'data':'"'*300000},separators=(',',':'))
        model=artifact(body);self.assertGreater(len(model),1048576)
        pin=json.dumps({'documentSha256':hashlib.sha256(body.encode()).hexdigest()}).encode()
        ActionRegistration(lambda *args:self.preparation).register(model,pin,self.preparation)
        too_big='{"data":"'+('x'*(1048577-11))+'"}'
        calls=[]
        with self.assertRaises(GatewayRefusal):ActionRegistration(lambda *args:calls.append(args)).register(artifact(too_big),json.dumps({'documentSha256':hashlib.sha256(too_big.encode()).hexdigest()}).encode(),self.preparation)
        self.assertFalse(calls)

    def test_changed_owner_output_refuses_without_publishing_handle(self):
        registration=ActionRegistration(lambda model,pin:artifact('{"changed":true}'))
        with self.assertRaises(GatewayRefusal):registration.register(self.model,self.pin,self.preparation)
        with self.assertRaises(GatewayRefusal):registration.original(0)

    def test_reentrancy_and_capacity_do_not_bypass_registration(self):
        def owner(model,pin):
            with self.assertRaises(GatewayRefusal):registration.register(model,pin,self.preparation)
            return self.preparation
        registration=ActionRegistration(owner,1)
        registration.register(self.model,self.pin,self.preparation)
        with self.assertRaises(GatewayRefusal):registration.register(self.model,self.pin,self.preparation)

    def test_bad_source_and_deferred_owner_refuse_before_publication(self):
        calls=[];registration=ActionRegistration(lambda *args:calls.append(args))
        for source in [bytearray(self.model),b'{"x":1,"x":2}',artifact('{}')[:-1]]:
            with self.assertRaises(GatewayRefusal):registration.register(source,self.pin,self.preparation)
        self.assertFalse(calls)
        async def owner(*args):return self.preparation
        with self.assertRaises(GatewayRefusal):ActionRegistration(owner)

class OriginalOwnerTests(unittest.TestCase):
    def test_original_umf_preparation_and_tamper_refusal(self):
        fixture=json.loads(Path('/Users/erik/Projects/weft/tests/mutation/fixtures/postgres-owner-plan.json').read_text())
        request=fixture['request'];model=json.dumps(request['model']).encode();pin=json.dumps(request['action']).encode()
        supplied=json.dumps(fixture['registry']['actions'][0]['preparation']).encode()
        oracle=Path(__file__).with_name('owner_action_preparation.ts')
        def prepare_owner(original_model,original_action):
            payload={'model':json.loads(original_model),'action':json.loads(original_action),'pin':request['modelPin']}
            run=subprocess.run(['bun',str(oracle)],input=json.dumps(payload),capture_output=True,text=True,timeout=30)
            if run.returncode:raise ValueError('Original owner refused')
            return run.stdout.strip().encode()
        registration=ActionRegistration(prepare_owner)
        handle=registration.register(model,pin,supplied)
        self.assertEqual(registration.original(handle).preparation,supplied)
        policy=registration.family_policy(handle)
        self.assertEqual(policy.family_identity,b'["sales","set-active"]')
        self.assertEqual(policy.action_pin,pin)
        self.assertEqual(policy.roles,('bulk-editor',))
        self.assertTrue(policy.person_required)
        with self.assertRaises(GatewayRefusal):registration.family_policy(type(handle)())
        values=json.dumps({'active-value':{'boolean':False}}).encode()
        self.assertIs(registration.validate_values(handle,values),values)
        for bad in [{'active-value':{'integerToken':'0'}},{},{'active-value':{'boolean':False},'extra':{'boolean':True}}]:
            with self.assertRaises(GatewayRefusal):registration.validate_values(handle,json.dumps(bad).encode())
        # Native source declaration spellings survive the Python wire decoder.
        original_doc=json.loads(request['model']['utf8'])
        action_definition=original_doc['modules'][0]['extensions']['umf.actions']['actions'][0]
        action_definition['parameters'][1]['field']={'module':'sales','element':'customer-id'}
        # Key edits are forbidden by original owner preparation, so use a fresh non-Key Field.
        numeric={'id':'number-value','name':'number_value','kind':'field','scalarType':'integer','cardinality':'one','nullability':'required','extensions':{},'facets':{'integerWidth':{'bits':8,'signed':True}}}
        original_doc['modules'][0]['elements'].append(numeric)
        record=next(e for e in original_doc['modules'][0]['elements'] if e['id']=='customer')
        record['members'].append({'module':'sales','element':'number-value'})
        ref={'module':'sales','element':'number-value'}
        action_definition['parameters'][1]['field']=ref
        action_definition['writes'][0]['fields']=[ref]
        action_definition['binding']['effects'][0]['values'][0]['field']=ref
        for spelling in ['8.0','8e0']:
            body_text=json.dumps(original_doc).replace('"bits": 8,','"bits": '+spelling+',')
            variant_model=artifact(body_text);variant_snapshot=json.loads(variant_model)
            variant_action={**request['action'],'documentSha256':variant_snapshot['sha256']}
            variant_pin={**request['modelPin'],'sha256':variant_snapshot['sha256']}
            def variant_owner(model_bytes,action_bytes):
                payload={'model':json.loads(model_bytes),'action':json.loads(action_bytes),'pin':variant_pin}
                result=subprocess.run(['bun',str(oracle)],input=json.dumps(payload),capture_output=True,text=True,timeout=30)
                if result.returncode:raise ValueError('Original owner refused')
                return result.stdout.strip().encode()
            variant_preparation=variant_owner(variant_model,json.dumps(variant_action).encode())
            variant=ActionRegistration(variant_owner)
            t=variant.register(variant_model,json.dumps(variant_action).encode(),variant_preparation)
            value_bytes=json.dumps({'active-value':{'integerToken':'127'}}).encode()
            self.assertIs(variant.validate_values(t,value_bytes),value_bytes)
        lossy_text=json.dumps(original_doc).replace('"bits": 8,','"bits": 8.0000000000000000000000000001,')
        lossy_model=artifact(lossy_text);lossy_snapshot=json.loads(lossy_model)
        variant_pin={**request['modelPin'],'sha256':lossy_snapshot['sha256']}
        lossy_action={**request['action'],'documentSha256':lossy_snapshot['sha256']}
        with self.assertRaises(ValueError):variant_owner(lossy_model,json.dumps(lossy_action).encode())
        changed=json.loads(supplied);body=json.loads(changed['utf8']);body['frames']=[]
        with self.assertRaises(GatewayRefusal):registration.register(model,pin,artifact(json.dumps(body)))

if __name__=='__main__':unittest.main()
