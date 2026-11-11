# SPDX-License-Identifier: MIT OR Apache-2.0
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

if __name__=='__main__':unittest.main()
