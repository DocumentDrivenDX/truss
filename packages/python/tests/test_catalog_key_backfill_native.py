"""Basic public alternate-key backfill and qualified duplicate refusal."""
import json,os
from dataclasses import replace
from truss import CatalogDocument,CatalogRegistration,CatalogAcceptanceRefused,Ok,ObjectFound,QueryRows,HistoricalRecord,HistoryEntity
from truss.contracts import MapValue,TextValue
from truss.groups import GroupSuccess,GroupFailed,UpdateObject,StoredObjectReference,AuthoredValue
import test_catalog_rebind_native as base

class CatalogKeyBackfillTests(base.CatalogRebindTests):
    for _name in tuple(n for n in dir(base.CatalogRebindTests) if n.startswith('test_')):locals()[_name]=None
    def fields(self,source):
        super().fields(source)
        next(e for e in source['modules'][0]['elements'] if e['id']=='A-value')['nullability']='required'
    def with_key(self):
        original=next(d for d in self.documents if d.document_id=='adoc');source=json.loads(original.content)
        next(e for e in source['modules'][0]['elements'] if e['id']=='A')['keys'].append(
            {'id':'a-backfill','name':'backfill','fields':[{'module':'m','element':'A-value'}],'primary':False})
        return CatalogDocument('adoc','r2',json.dumps(source).encode())
    def seed(self,values):
        c,h,a,t=self.ready(self.fields);context=a.group_context_in_transaction(t).value
        operations=tuple(self.create(label=str(i),value=value,alias='item'+str(i)) for i,value in enumerate(values))
        applied=a.apply_in_transaction(t,context.input(operations,MapValue(entries=())),context.request('before-new-key'),documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(applied,Ok,repr(applied));self.assertIsInstance(applied.value,GroupSuccess)
        identities=tuple(r.identity for r in applied.value.response.semantic.results)
        h.detach();c.commit();self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        return identities
    def register(self,a,t):
        document=self.with_key();prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        return a.accept_in_transaction(t,prepared,request_key='new-alternate-key')
    def test_register_existing_objects_lookup_and_query(self):
        identities=self.seed(('first','second'));c,h,a,t=self.consumer();accepted=self.register(a,t)
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(h._custody.last_attempt.error));self.assertIsInstance(accepted.value,CatalogRegistration)
        report=json.loads(accepted.value.report_bytes);self.assertEqual(len(report['keyBackfills']),2)
        found=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-backfill',values=('first',),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(found.value,ObjectFound,repr(found));self.assertEqual(found.value.object.id,int(identities[0].id));self.assertEqual(found.value.object.version,1)
        query=a.query_in_transaction(t,sql='SELECT a."A-value" FROM "A" a ORDER BY a."A-value"',document_ids=('adoc',))
        self.assertIsInstance(query.value,QueryRows,repr(query));self.assertEqual(query.value.rows,(('first',),('second',)))
        history=a.reconstruct_in_transaction(t,entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(identities[0].id)),version=1)
        self.assertIsInstance(history.value,HistoricalRecord,repr(history))
        documents=tuple(self.with_key() if d.document_id=='adoc' else d for d in self.documents)
        context=a.group_context_in_transaction(t).value
        update=UpdateObject(target=StoredObjectReference(identity=found.value.object.identity),set=(AuthoredValue(name='A-value',value=TextValue(kind='string',text='changed')),),unset=(),expected_version='1')
        changed=a.apply_in_transaction(t,context.input((update,),MapValue(entries=())),context.request('after-key-backfill'),documents=documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(changed.value,GroupSuccess,repr(changed)+' '+str(h._custody.last_attempt.error))
        reread=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-backfill',values=('changed',),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(reread.value,ObjectFound,repr(reread));self.assertEqual(reread.value.object.version,2)
        duplicate=replace(self.create(label='unused',value='second'),type_definition_pin=reread.value.object.definition_pin)
        refused=a.apply_in_transaction(t,context.input((duplicate,),MapValue(entries=())),context.request('duplicate-after-backfill'),documents=documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(refused.value,GroupFailed,repr(refused))
        h.detach();c.commit()
    def test_duplicate_candidates_refuse_without_catalog_effects(self):
        self.seed(('same','same'));c,h,a,t=self.consumer();prior=a.status_in_transaction(t).value.revision;accepted=self.register(a,t)
        self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogAcceptanceRefused)
        self.assertEqual([(v.key_id,v.rule,v.affected_object_count) for v in accepted.value.violations],[('a-backfill','key.duplicate',2)])
        self.assertEqual(a.status_in_transaction(t).value.revision,prior);h.detach();c.rollback()

class CatalogKeyBackfill08Tests(CatalogKeyBackfillTests):
    source_version='0.8.0'
