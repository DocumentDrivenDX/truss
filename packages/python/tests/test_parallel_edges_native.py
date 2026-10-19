# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public parallel independent self-edges retain distinct stored identities."""
import os,base64
from dataclasses import replace
from hashlib import sha256
from truss import Ok,QueryRows,QueryRelatedKeys
from truss.contracts import MapValue,ExactArtifact
from truss.groups import CreateEdge,AliasObjectReference,StoredObjectReference,NullOrderKey,GroupSuccess,GroupFailed,Delete
from truss.imports import ImportReported,ImportRejected,ImportSkipped
import test_group_create_native as create_tests

class ParallelEdgesTests(create_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(create_tests.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    def fields(self,source):
        for e in source['modules'][0]['elements']:
            if e['kind']=='record':e['name']=e['id']
        relationship=source['modules'][0]['relationships'][0]
        relationship['target']=[{'module':'m','element':'A','key':'a-primary'}]
        relationship['sourceMultiplicity']={'min':0,'max':2};relationship['targetMultiplicity']={'min':0,'max':2}
    def test_separate_committed_groups_create_parallel_self_edges(self):
        c,h,a,t=self.ready(self.fields)
        pin=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        context=a.group_context_in_transaction(t).value
        first=self.apply(a,t,context.input((self.create('one',alias='root'),CreateEdge(relationship_definition_pin=pin,source=AliasObjectReference(alias='root'),target=AliasObjectReference(alias='root'),values=(),order_key=NullOrderKey())),MapValue(entries=())),context.request('first-self'))
        self.assertIsInstance(first,GroupSuccess);root=first.response.semantic.results[0].identity;edge1=first.response.semantic.results[1].identity
        h.detach();c.commit();c,h,a,t=self.consumer()
        context=a.group_context_in_transaction(t).value
        second=self.apply(a,t,context.input((CreateEdge(relationship_definition_pin=pin,source=StoredObjectReference(identity=root),target=StoredObjectReference(identity=root),values=(),order_key=NullOrderKey()),),MapValue(entries=())),context.request('second-self'))
        self.assertIsInstance(second,GroupSuccess,repr(second));edge2=second.response.semantic.results[0].identity
        self.assertNotEqual(edge1.id,edge2.id)
        h.detach();c.commit();c,h,a,t=self.consumer()
        query=a.query_in_transaction(t,sql='SELECT RELATED_KEYS(a."A-B",2) AS related FROM "A" a',document_ids=('adoc',))
        self.assertIsInstance(query,Ok);self.assertIsInstance(query.value,QueryRows,repr(query.value))
        self.assertEqual(query.value.rows,((QueryRelatedKeys(items=(('value','one'),('value','one')),truncated=False),),))
        context=a.group_context_in_transaction(t).value
        third=self.apply(a,t,context.input((CreateEdge(relationship_definition_pin=pin,source=StoredObjectReference(identity=root),target=StoredObjectReference(identity=root),values=(),order_key=NullOrderKey()),),MapValue(entries=())),context.request('third-refused'))
        self.assertIsInstance(third,GroupFailed)
        page=a.page_edges_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B',anchor=root)
        self.assertIsInstance(page,Ok);self.assertEqual({e.identity.id for e in page.value.edges},{edge1.id,edge2.id})
        built=a.edge_import_record_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B',source_endpoint=root,target_endpoint=root,values=(),order_key=NullOrderKey())
        self.assertIsInstance(built,Ok)
        invalid=b'invalid payload';digest=sha256(invalid).hexdigest()
        record=replace(built.value,payload=ExactArtifact(identity=digest,sha256=digest,bytes_base64=base64.b64encode(invalid).decode()))
        imports=a.import_context_in_transaction(t).value
        refused=a.import_in_transaction(t,imports.input((record,),load_id='parallel',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(refused,ImportReported);self.assertIsInstance(refused.report.outcomes[0],ImportRejected)
        self.assertEqual(refused.report.outcomes[0].code,'invalid')
        context=a.group_context_in_transaction(t).value
        removed=self.apply(a,t,context.input((Delete(operation='delete_edge',target=StoredObjectReference(identity=edge1)),),MapValue(entries=())),context.request('unlink-first'))
        self.assertIsInstance(removed,GroupSuccess)
        page=a.page_edges_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B',anchor=root)
        self.assertEqual(tuple(e.identity.id for e in page.value.edges),(edge2.id,))
        skipped=a.import_in_transaction(t,imports.input((record,),load_id='one-live',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(skipped,ImportReported);self.assertIsInstance(skipped.report.outcomes[0],ImportSkipped)
        self.assertEqual(skipped.report.outcomes[0].identity.id,edge2.id)
        h.detach();c.rollback()
