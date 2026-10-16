"""Basic database originals -> complete facts -> original UMF child workflow.
Private supplied-cut evaluation, not native query permission or public release.
"""
import json
import os
import shutil
import unittest
from truss import Ok, adopt_psycopg_host
from truss.contracts import TextValue, BooleanValue, MapValue
from truss.groups import CreateObject, AuthoredValue, RootlessOwnership, RequestNone, GroupSuccess
from truss._current_query_facts import capture_current_query_facts_with_cursor, _key_batches
from truss._umf_key_tuples import KeyTupleRequest
from truss._current_query_computation import open_current_query_computation
from truss._current_query_pipe import _envelope
from truss._current_query_subjects import observe_current_query_subject_in_transaction
import test_current_query_subjects_native as subject


class KeyBatchTests(unittest.TestCase):
    def test_partition_before_original_encoder_dispatch(self):
        request=KeyTupleRequest('m','Record','pk',('key',))
        pending=[('1','1',request,[],[])]*128
        self.assertEqual([len(b) for b in _key_batches(b' '*40960,pending)],[102,26])
        escaped=b'"'*500000
        long_request=KeyTupleRequest('m','Record','pk',('k'*30000,))
        batches=list(_key_batches(escaped,[('1','1',long_request,[],[])]*2))
        self.assertEqual([len(b) for b in batches],[1,1])


class CurrentQueryFactsNativeTests(subject.CurrentQuerySubjectsNativeTests):
    for name in tuple(n for n in dir(subject.CurrentQuerySubjectsNativeTests) if n.startswith('test_')):
        locals()[name]=None

    def test_complete_public_objects_feed_original_policy_child(self):
        subject.CurrentQuerySubjectsNativeTests.test_ordinary_session_observes_only_enrolled_subject_and_original_key(self)
        bun=os.environ.get('TRUSS_BUN_EXECUTABLE',shutil.which('bun') or 'bun')
        for connection,host in self.consumer_connections:
            host.detach();connection.rollback();connection.close()
        c,h,a,t=self.consumer()
        view=a.catalog_view_in_transaction(t,a.catalog_view_request()).value.view
        types={d.reference.authored_identity:d.reference for d in view.definitions if d.reference.kind=='type'}
        inputs=[('Project',{'projectId':'p1'}),('Resource',{'resourceId':'r1','salary':9007199254740993}),
                ('Resource',{'resourceId':'r2','salary':200}),
                ('Ownership',{'ownerId':'o1','ownerResource':'r1','ownerProject':'p1'}),
                ('Assignment',{'assignmentId':'a1','assignmentStaff':'alice','assignmentProject':'p1','active':True})]
        operations=[]
        for index,(record,fields) in enumerate(inputs):
            values=tuple(AuthoredValue(name=name,value=BooleanValue(value=value) if type(value) is bool else TextValue(kind='integer' if type(value) is int else 'string',text=str(value))) for name,value in fields.items())
            operations.append(CreateObject(type_definition_pin=types[record].definition_pin,values=values,ownership=RootlessOwnership(),alias='fact'+str(index)))
        context=a.group_context_in_transaction(t).value
        result=a.apply_in_transaction(t,context.input(tuple(operations),MapValue(entries=())),RequestNone(),documents=self.current_source_documents,bun_executable=bun)
        self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
        h.detach();c.commit()
        c,h,a,t=self.consumer()
        observed=observe_current_query_subject_in_transaction(h,t,self.current_subject_registration,bun_executable=bun)
        self.assertIsInstance(observed,Ok,str(h._custody.last_attempt.error))
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);self.tx=self.host.adopt_transaction().value
        def compute(cursor, _):
            captured=capture_current_query_facts_with_cursor(cursor,bun_executable=bun)
            facts=json.loads(captured.facts_bytes);coverage=json.loads(captured.coverage_bytes)
            self.assertEqual(len(facts),6);self.assertEqual(len(captured.rows),6);self.assertEqual(len(coverage),5)
            resource=next(f for f in facts if f['type']['elementId']=='Resource' and f['key']==[{'string':'r1'}])
            self.assertEqual(next(f['value'] for f in resource['fields'] if f['field']['elementId']=='salary'),{'integerToken':'9007199254740993'})
            for _,_,_,receipt,namespace,transport in captured.rows:
                self.assertTrue(namespace);self.assertEqual(transport,('umf-key-tuple-v1:hex:'+json.loads(receipt)['bytesHex']).encode())
            source=_envelope(captured.sources.initialize_bytes)['sources'];ontology=source['ontology']
            # Authored diagnostic realization, not a registered native owner.
            owner={'version':'umf.security.logical-owner/0.1','id':'diagnostic-owner','revision':'1',
                   'storage':[{'type':e['type'],'field':f['ref'],'storageEffect':'canonical'} for e in ontology['entities'] for f in e['fields']],
                   'disclosure':{'readAction':'read'}}
            generation=cursor.execute('SELECT pg_catalog.pg_current_xact_id()::pg_catalog.text',prepare=False).fetchone()[0]
            cut={'version':'umf.security.logical-facts/0.1','trusted':True,'generation':generation,'expectedGeneration':generation,
                 'policy':{'id':source['policy']['id'],'revision':source['policy']['revision']},'ontology':source['policy']['ontology'],
                 'protection':None,'domains':source['closure']['pins'],'owner':{'id':owner['id'],'revision':owner['revision']},
                 'subject':{'type':ontology['subject'],'key':[{'string':observed.value.key}]},'facts':facts,'graphs':[],
                 'coverage':coverage,'graphCoverage':[],'context':[],'valueProfiles':[],'maxFacts':10000,'maxSteps':1000000}
            target={'documentId':'domain','moduleId':'m','elementId':'Resource'}
            operations=[{'id':'read','kind':'read-rules','selection':{'type':target}},
                        {'id':'scan','kind':'scan','selection':{'type':target,'fields':[{'documentId':'domain','moduleId':'m','elementId':'salary'}]}}]
            receipt=captured.sources.source_receipt
            with open_current_query_computation(bun_executable=bun,timeout_seconds=10) as child:
                initialized=_envelope(child.exchange(captured.sources.initialize_bytes,source_receipt=receipt))
                self.assertEqual(initialized['kind'],'initialized')
                inspection={'kind':'inspect-routes','requestId':'inspect','sourceReceipt':receipt,'owner':owner,'routes':[]}
                inspected=_envelope(child.exchange(json.dumps(inspection,separators=(',',':')).encode(),source_receipt=receipt))
                self.assertEqual(inspected['kind'],'routes-inspected')
                request={'kind':'evaluate','requestId':'evaluate','sourceReceipt':receipt,'owner':owner,'cut':cut,'operations':operations,'routes':[]}
                evaluated=_envelope(child.exchange(json.dumps(request,separators=(',',':')).encode(),source_receipt=receipt))
            self.assertEqual(evaluated['kind'],'evaluation');self.assertEqual(evaluated['batch']['status'],'completed')
            self.assertFalse(evaluated['batch']['authority']);return evaluated
        evaluated=self.host._run_operation(self.tx,compute)
        self.assertIsInstance(evaluated,Ok,str(self.host._custody.last_attempt.error))
        self.assertEqual(len(evaluated.value['batch']['operations']),2)
        read,scan=evaluated.value['batch']['operations']
        self.assertEqual({row['resource']['key'][0]['string']:row['decision'] for row in read['outcome']['rows']},
                         {'r1':'permit','r2':'deny'})
        self.assertEqual(scan['outcome']['rows'],[[{
            'field':{'documentId':'domain','moduleId':'m','elementId':'salary'},
            'disposition':'original','value':{'integerToken':'9007199254740993'}}]])
