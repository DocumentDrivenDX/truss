"""Public refusal, repair and acceptance of existing scalar requiredness."""
import json,os
from truss import CatalogDocument,CatalogAcceptanceRefused,CatalogRegistration,ObjectFound,Ok,QueryRows
from truss.contracts import TextValue
from truss.groups import AuthoredValue,CreateObject,RootlessOwnership,UpdateObject,StoredObjectReference,GroupSuccess,CommittedReceiptReplay
import test_group_create_native as base

class RequiredEvolutionTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    source_version='0.7.0'
    def fields(self,source):
        source['umf']=self.source_version
        module=source['modules'][0];record=next(e for e in module['elements'] if e['id']=='A');record['name']='A'
        module['elements'].append({'id':'optional','name':'optional','kind':'field','scalarType':'string','nullability':'absent-allowed','cardinality':'one','extensions':{}})
        record['members'].append({'module':'m','element':'optional'})
    def test_refuse_missing_repair_accept_and_retry(self):
        c,h,a,t=self.ready(self.fields)
        original_documents=self.documents
        semantic,request=self.input(a,t,(self.create('one'),));created=self.apply(a,t,semantic,request);self.assertIsInstance(created,GroupSuccess);identity=created.response.semantic.results[0].identity
        h.detach();c.commit();self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE');c,h,a,t=self.consumer()
        original_report=a.report_in_transaction(t).value.original_bytes
        doc=json.loads(next(d.content for d in self.documents if d.document_id=='adoc'))
        next(e for e in doc['modules'][0]['elements'] if e['id']=='optional')['nullability']='required'
        prepared=a.prepare_catalog((CatalogDocument('adoc','r2',json.dumps(doc).encode()),),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        refused=a.accept_in_transaction(t,prepared,request_key='required-missing');self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,CatalogAcceptanceRefused,repr(refused));self.assertEqual({(v.field_id,v.rule,v.affected_object_count) for v in refused.value.violations},{('optional','property.required',1)})
        fix=UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='optional',value=TextValue(kind='string',text='present')),),unset=(),expected_version='1')
        update,req=self.input(a,t,(fix,));req=a.group_context_in_transaction(t).value.request('repair-required');self.assertIsInstance(self.apply(a,t,update,req),GroupSuccess);h.detach();c.commit();c,h,a,t=self.consumer()
        before=self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall()
        accepted=a.accept_in_transaction(t,prepared,request_key='required-compatible');self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted));h.detach();c.commit();c,h,a,t=self.consumer()
        self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall(),before)
        self.assertTrue(a.accept_in_transaction(t,prepared,request_key='required-compatible').value.replayed)
        found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value;self.assertIsInstance(found,ObjectFound);self.assertEqual(found.object.version,2);self.assertEqual(dict(found.object.values)['optional'],'present')
        rows=a.query_in_transaction(t,sql='SELECT a.optional FROM "A" a',document_ids=('adoc',));self.assertIsInstance(rows.value,QueryRows,repr(rows));self.assertEqual(rows.value.rows,(('present',),))
        replay=a.apply_in_transaction(t,semantic,request,documents=original_documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'));self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
        self.assertEqual(a.report_in_transaction(t,revision=1).value.original_bytes,original_report);h.detach();c.commit()

class RequiredEvolution08Tests(RequiredEvolutionTests):
    source_version='0.8.0'
