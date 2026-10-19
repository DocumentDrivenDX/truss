# SPDX-License-Identifier: MIT OR Apache-2.0
"""Protocol sequencing controls; fake child is not UMF/native evidence."""
import json
import unittest
from dataclasses import dataclass
from truss._current_disclosure_session import evaluate_stage_inspect
from truss._current_disclosure_pipe import VERSION
from truss._current_disclosure_wire import frame_digest
from truss._current_query_evaluation import wire

class Deadline:
    failed=False
    def check(self):
        if self.failed:raise TimeoutError('fixture deadline')

@dataclass
class Staged:
    reconstructed_batch:bytes

class Peer:
    def __init__(self,mutate=None):self.calls=[];self.mutate=mutate;self.evaluation=None
    def exchange(self,raw,source_receipt):
        request=json.loads(raw);self.calls.append(request['kind'])
        response={'version':VERSION,'kind':'initialized','requestId':request['requestId'],'sourceReceipt':source_receipt}
        if request['kind']=='evaluate-disclosure':
            self.evaluation=frame_digest(raw)
            response.update(kind='disclosure-evaluated',result={'version':'umf.security.logical-disclosure-batch/0.1-candidate','status':'rendered','authority':False,'complete':False,'batch':{'rows':[]}})
        elif request['kind']=='inspect-native-disclosure':
            response.update(kind='native-disclosure-inspected',evaluationFrameSha256=self.evaluation,inspectionFrameSha256=frame_digest(raw),status='validated-disclosure',complete=False,authority=False)
        if self.mutate:self.mutate(request,response)
        return wire(response)

class HeldDisclosureSessionTests(unittest.TestCase):
    def setUp(self):
        self.initial=wire({'version':VERSION,'kind':'initialize','requestId':'init','sources':{},'owner':{},'selection':{}})
        self.evaluation=wire({'version':VERSION,'kind':'evaluate-disclosure','requestId':'evaluate','sourceReceipt':frame_digest(self.initial),'cut':{}})
        self.deadline=Deadline();self.staged=Staged(b'{"rows":[],"unknown":1.2300e-999999}')
    def run_session(self,peer,stage=None):
        return evaluate_stage_inspect(peer,self.deadline,self.initial,self.evaluation,stage or (lambda raw:self.staged))
    def test_same_child_producer_stage_then_inspection(self):
        peer=Peer()
        def stage(raw):
            self.assertEqual(peer.calls,['initialize','evaluate-disclosure'])
            self.assertEqual(json.loads(raw)['status'],'rendered')
            return self.staged
        self.assertIs(self.run_session(peer,stage),self.staged)
        self.assertEqual(peer.calls,['initialize','evaluate-disclosure','inspect-native-disclosure'])
    def test_refused_evaluation_never_stages_or_inspects(self):
        for key,value in [('status','refused'),('authority',True),('complete',True),('batch',None)]:
            def mutate(request,response):
                if request['kind']=='evaluate-disclosure':response['result'][key]=value
            peer=Peer(mutate)
            with self.subTest(key=key),self.assertRaises(ValueError):self.run_session(peer,lambda raw:self.fail('must not stage'))
            self.assertEqual(peer.calls,['initialize','evaluate-disclosure'])
    def test_staging_failure_and_deadline_never_inspect(self):
        peer=Peer()
        def stage(raw):raise ValueError('fixture staging failure')
        with self.assertRaises(ValueError):self.run_session(peer,stage)
        self.assertEqual(peer.calls,['initialize','evaluate-disclosure'])
        peer=Peer()
        def expire(raw):self.deadline.failed=True;return self.staged
        with self.assertRaises(TimeoutError):self.run_session(peer,expire)
        self.assertEqual(peer.calls,['initialize','evaluate-disclosure'])
    def test_inspection_correlation_refusals_never_return(self):
        for key,value in [('evaluationFrameSha256','0'*64),('inspectionFrameSha256','0'*64),('sourceReceipt','0'*64),('authority',True),('complete',True),('kind','refused'),('status','invalid'),('extra',True)]:
            def mutate(request,response):
                if request['kind']=='inspect-native-disclosure':response[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.run_session(Peer(mutate))
    def test_initialization_and_evaluation_envelopes_are_closed(self):
        for kind in ('initialize','evaluate-disclosure'):
            def mutate(request,response):
                if request['kind']==kind:response['extra']=True
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.run_session(Peer(mutate))
    def test_wrong_source_receipt_never_starts_child(self):
        value=json.loads(self.evaluation);value['sourceReceipt']='0'*64;self.evaluation=wire(value);peer=Peer()
        with self.assertRaises(ValueError):self.run_session(peer)
        self.assertEqual(peer.calls,[])

if __name__=='__main__':unittest.main()
