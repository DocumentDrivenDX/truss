"""Synthetic original-port controls; no native authority qualification."""
import copy
import unittest
from truss._operation_admission import AdmissionCustody, AdmissionRefusal


class AdmissionCustodyTests(unittest.TestCase):
    def test_one_use_and_original_input_correspondence(self):
        producer, original, payload = object(), object(), object()
        events = []
        custody = AdmissionCustody(producer, 1,
            lambda confirmation, value: events.append(('verify',confirmation,value)),
            lambda confirmation, value: events.append(('admit',confirmation,value)) or 'native result')
        ticket = custody.register_confirmed(producer, original)
        self.assertEqual(custody.admit_once(ticket,payload), 'native result')
        self.assertEqual(events,[('verify',original,payload),('admit',original,payload)])
        for rejected in [ticket,copy.copy(ticket),object()]:
            with self.assertRaises(AdmissionRefusal): custody.admit_once(rejected,payload)
        self.assertEqual(len(events),2)
        with self.assertRaises(AdmissionRefusal): custody.register_confirmed(producer,original)
        with self.assertRaises(AdmissionRefusal): custody.register_confirmed(producer,object())

    def test_failure_never_restores_permission(self):
        for phase in ['verify','admit']:
            producer, original = object(), object()
            events=[]
            def verify(*args):
                events.append('verify')
                if phase=='verify': raise OSError('original lifetime unavailable')
            def admit(*args):
                events.append('admit')
                raise OSError('native result unavailable')
            custody=AdmissionCustody(producer,2,verify,admit)
            later=custody.register_confirmed(producer,object())
            ticket=custody.register_confirmed(producer,original)
            with self.assertRaises(OSError): custody.admit_once(ticket,b'original')
            with self.assertRaises(AdmissionRefusal): custody.admit_once(ticket,b'original')
            with self.assertRaises(AdmissionRefusal): custody.admit_once(later,b'new attempt')
            self.assertEqual(events,['verify'] if phase=='verify' else ['verify','admit'])

    def test_close_and_reentrant_verification_prevent_dispatch(self):
        producer=object();events=[]
        def verify(*args):
            with self.assertRaises(AdmissionRefusal): custody.admit_once(ticket,b'copy')
            with self.assertRaises(AdmissionRefusal): custody.register_confirmed(producer,object())
            custody.close(producer)
        custody=AdmissionCustody(producer,2,verify,lambda *args:events.append('admit'))
        ticket=custody.register_confirmed(producer,object())
        with self.assertRaises(AdmissionRefusal):custody.admit_once(ticket,b'original')
        self.assertEqual(events,[])
        with self.assertRaises(AdmissionRefusal):custody.register_confirmed(producer,object())

    def test_foreign_custody_and_invalid_capacity_refuse(self):
        producer=object();custody=AdmissionCustody(producer,1,lambda *args:None,lambda *args:None)
        for value in [0,-1,True,1.0]:
            with self.assertRaises(AdmissionRefusal):AdmissionCustody(producer,value,lambda:None,lambda:None)
        with self.assertRaises(AdmissionRefusal):custody.register_confirmed(object(),object())
        with self.assertRaises(AdmissionRefusal):custody.close(object())
        other=AdmissionCustody(producer,1,lambda *args:None,lambda *args:None)
        ticket=other.register_confirmed(producer,object())
        with self.assertRaises(AdmissionRefusal):custody.admit_once(ticket,b'original')

    def test_async_or_nonvoid_verification_cannot_dispatch(self):
        producer=object();events=[];pending=[]
        async def asynchronous(*args):events.append('async body')
        with self.assertRaises(AdmissionRefusal):AdmissionCustody(producer,1,asynchronous,lambda:None)
        def wrapped(*args):
            coroutine=asynchronous();pending.append(coroutine);return coroutine
        for verify in [wrapped,lambda *args:True]:
            custody=AdmissionCustody(producer,1,verify,lambda *args:events.append('admit'))
            ticket=custody.register_confirmed(producer,object())
            with self.assertRaises(AdmissionRefusal):custody.admit_once(ticket,b'original')
            with self.assertRaises(AdmissionRefusal):custody.admit_once(ticket,b'original')
        self.assertIsNone(pending[0].cr_frame)
        self.assertEqual(events,[])


if __name__=='__main__':unittest.main()
