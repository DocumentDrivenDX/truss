# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public relationship multiplicity refusal, repair and compatible acceptance."""
import base64,json,os
from truss import Ok,CatalogDocument,CatalogAcceptanceRefused,CatalogRegistration,CatalogRelationshipCompatibilityViolation
from truss.contracts import MapValue
from truss.groups import CreateEdge,AliasObjectReference,StoredObjectReference,NullOrderKey,Delete,GroupSuccess,GroupFailed
import test_group_create_native as base

class RelationshipEvolutionTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    source_version='0.10.0'
    def fields(self,source):
        source['umf']=self.source_version
        rel=source['modules'][0]['relationships'][0];rel['sourceMultiplicity']={'min':0,'max':'*'};rel['targetMultiplicity']={'min':0,'max':'*'}
    def link(self,pin,source,target):return CreateEdge(relationship_definition_pin=pin,source=source,target=target,values=(),order_key=NullOrderKey())
    def run_group(self,a,t,ops,key):
        context=a.group_context_in_transaction(t).value
        return self.apply(a,t,context.input(tuple(ops),MapValue(entries=())),context.request(key))
    def test_refuse_repair_accept_and_enforce_bounds(self):
        c,h,a,t=self.ready(self.fields);pin=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        result=self.run_group(a,t,(self.create('one',alias='a'),self.create('zero',alias='zero'),self.create('b1',record='B',alias='b1'),self.create('b2',record='B',alias='b2'),self.link(pin,AliasObjectReference(alias='a'),AliasObjectReference(alias='b1')),self.link(pin,AliasObjectReference(alias='a'),AliasObjectReference(alias='b2'))),'initial-graph');self.assertIsInstance(result,GroupSuccess)
        source,zero,b1,b2,e1,e2=(r.identity for r in result.response.semantic.results);h.detach();c.commit();self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE');c,h,a,t=self.consumer()
        relationship_id=self.admin.execute("SELECT rel_type_id FROM truss.rel_def WHERE document_id='adoc' AND rel_id='A-B'").fetchone()[0]
        original_revision=self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1').fetchone()[0]
        self.assertEqual(self.admin.execute('SELECT truss.runtime_relationship_pin(%s,%s)',(relationship_id,original_revision)).fetchone()[0],pin)
        doc=json.loads(next(d.content for d in self.documents if d.document_id=='adoc'));rel=doc['modules'][0]['relationships'][0];rel['targetMultiplicity']={'min':1,'max':1};rel['sourceMultiplicity']={'min':0,'max':1}
        document=CatalogDocument('adoc','r2',json.dumps(doc).encode());prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        refused=a.accept_in_transaction(t,prepared,request_key='bad-bounds');self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,CatalogAcceptanceRefused,repr(refused));self.assertTrue(all(isinstance(v,CatalogRelationshipCompatibilityViolation) for v in refused.value.violations));self.assertEqual({(v.relationship_id,v.side,v.rule,v.affected_object_count) for v in refused.value.violations},{('A-B','source','relationship.min',1),('A-B','source','relationship.max',1)})
        repair=self.run_group(a,t,(Delete(operation='delete_edge',target=StoredObjectReference(identity=e2)),self.link(pin,StoredObjectReference(identity=zero),StoredObjectReference(identity=b2))),'repair-bounds');self.assertIsInstance(repair,GroupSuccess);h.detach();c.commit();c,h,a,t=self.consumer()
        objects=self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall();edges=self.admin.execute('SELECT to_jsonb(e) FROM truss.edge e ORDER BY id').fetchall()
        accepted=a.accept_in_transaction(t,prepared,request_key='good-bounds');self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted));h.detach();c.commit();c,h,a,t=self.consumer()
        self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall(),objects);self.assertEqual(self.admin.execute('SELECT to_jsonb(e) FROM truss.edge e ORDER BY id').fetchall(),edges);self.assertTrue(a.accept_in_transaction(t,prepared,request_key='good-bounds').value.replayed)
        self.documents=tuple(document if d.document_id=='adoc' else d for d in self.documents)
        old_pin=pin
        pin=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        current_revision=self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1').fetchone()[0]
        self.assertNotEqual(pin,old_pin)
        self.assertEqual(self.admin.execute('SELECT truss.runtime_relationship_pin(%s,%s)',(relationship_id,original_revision)).fetchone()[0],old_pin)
        self.assertEqual(self.admin.execute('SELECT truss.runtime_relationship_pin(%s,%s)',(relationship_id,current_revision)).fetchone()[0],pin)
        e1=a.get_edge_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B',edge_id=int(e1.id)).value.edge.identity
        failed=self.run_group(a,t,(Delete(operation='delete_edge',target=StoredObjectReference(identity=e1)),),'violate-min');self.assertIsInstance(failed,GroupFailed);self.assertEqual(json.loads(base64.b64decode(failed.failure.inner_error.bytes_base64))['code'],'dependencies')
        failed=self.run_group(a,t,(self.create('b3',record='B',alias='b3'),self.link(pin,StoredObjectReference(identity=source),AliasObjectReference(alias='b3'))),'violate-max');self.assertIsInstance(failed,GroupFailed);self.assertEqual(json.loads(base64.b64decode(failed.failure.inner_error.bytes_base64))['code'],'dependencies')
        h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge_limit').fetchone(),(4,))
