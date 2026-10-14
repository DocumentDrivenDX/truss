"""Basic public registration-owned retained scalar/container rebinding."""
import json, os
from dataclasses import replace
from truss import Ok, Error, CatalogDocument, CatalogRegistration, CatalogAcceptanceRefused, ObjectFound, HistoryEntity, HistoricalRecord, QueryRows, FeedPage, ModuleAccessGrant, adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration
from truss.contracts import BooleanValue, NullValue, SequenceValue, TextValue, MapValue
from truss.groups import AuthoredValue, GroupSuccess
import test_group_create_native as base

class CatalogRebindTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')): locals()[_name]=None
    source_version='0.7.0'
    def fields(self, source):
        source['umf']=self.source_version
        for element in source['modules'][0]['elements']:
            if element['kind']=='record':element['name']=element['id']
    def revised(self, original):
        source=json.loads(original.content);module=source['modules'][0]
        fields=[{'id':name,'name':name,'kind':'field','cardinality':'one','nullability':'absent-allowed','scalarType':family,'extensions':{}}
                for name,family in [('giftWrap','boolean'),('giftNote','string')]]
        fields.append({'id':'giftFlags','name':'giftFlags','kind':'field','cardinality':'array','nullability':'absent-allowed','itemType':{'module':'m','element':'flagItem'},'extensions':{}})
        module['elements']+=fields+[{'id':'flagItem','name':'flagItem','kind':'field','cardinality':'one','nullability':'required','scalarType':'boolean','extensions':{}}]
        next(e for e in module['elements'] if e['id']=='A')['members'] += [{'module':'m','element':f['id']} for f in fields]
        return CatalogDocument('adoc','r2',json.dumps(source).encode())
    def test_register_rebind_read_report_history_and_retry(self):
        c,h,a,t=self.ready(self.fields);originals=self.documents
        flags=SequenceValue(items=(BooleanValue(value=True),BooleanValue(value=False)))
        operation=replace(self.create(),values=self.create().values+(
            AuthoredValue(name='giftWrap',value=BooleanValue(value=True)),AuthoredValue(name='giftNote',value=NullValue()),
            AuthoredValue(name='giftFlags',value=flags),AuthoredValue(name='unmatched',value=TextValue(kind='string',text='keep'))))
        context=a.group_context_in_transaction(t).value
        created=self.apply(a,t,context.input((operation,),MapValue(entries=())),context.request('retain-before-registration'))
        self.assertIsInstance(created,GroupSuccess);identity=created.response.semantic.results[0].identity
        h.detach();c.commit()
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        document=self.revised(next(d for d in originals if d.document_id=='adoc'))
        c,h,a,t=self.consumer();prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        accepted=a.accept_in_transaction(t,prepared,request_key='bind-gifts')
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(h._custody.last_attempt.error))
        self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted))
        report=json.loads(accepted.value.report_bytes)
        self.assertEqual(report['interfaceVersion'],'truss-catalog-registration-report/0.3')
        self.assertEqual(len(report['rebinds']),1);self.assertEqual(len(report['rebinds'][0]['effects']),3);self.assertEqual(len(report['rebinds'][0]['events']),4)
        self.assertTrue(all(e['component']=='event' and type(e['bytesBase64']) is str for e in report['rebinds'][0]['events']))
        self.assertEqual(report['rebinds'][0]['beforeVersion'],'1');self.assertEqual(report['rebinds'][0]['afterVersion'],'2')
        read=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(read.value,ObjectFound,repr(read));self.assertEqual(read.value.object.version,2)
        values=dict(read.value.object.values);self.assertTrue(values['giftWrap']);self.assertIsNone(values['giftNote']);self.assertEqual(values['giftFlags'],flags)
        self.assertEqual(dict(read.value.object.retained),{'unmatched':'keep'})
        h.detach();c.commit()
        c,h,a,t=self.consumer()
        for version in (1,2):
            history=a.reconstruct_in_transaction(t,entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(identity.id)),version=version)
            self.assertIsInstance(history.value,HistoricalRecord,repr(history)+' '+str(h._custody.last_attempt.error))
            image=json.loads(history.value.record);self.assertEqual(image['recordVersion'],str(version))
            self.assertEqual({e['name'] for e in image['retained']},{'giftWrap','giftFlags','giftNote','unmatched'} if version==1 else {'unmatched'})
        projection=a.query_in_transaction(t,sql='SELECT a."giftWrap", a."giftNote", a."giftFlags" FROM "A" a',document_ids=('adoc',))
        self.assertIsInstance(projection.value,QueryRows,repr(projection)+' '+str(h._custody.last_attempt.error));self.assertEqual(projection.value.rows,((True,None,(True,False)),))
        complete=a.query_in_transaction(t,sql='SELECT a.* FROM "A" a',document_ids=('adoc',),read_profile='complete-entity')
        self.assertIsInstance(complete.value,QueryRows,repr(complete)+' '+str(h._custody.last_attempt.error))
        projected=dict(zip(complete.value.columns,complete.value.rows[0],strict=True));self.assertEqual(projected['_version'],2);self.assertEqual(projected['_created_by'],'consumer');self.assertEqual(projected['_updated_by'],'consumer')
        retry=a.accept_in_transaction(t,prepared,request_key='bind-gifts')
        self.assertIsInstance(retry,Ok,repr(retry));self.assertTrue(retry.value.replayed)
        self.assertEqual(retry.value.report_bytes,accepted.value.report_bytes)
        self.assertEqual(a.report_in_transaction(t,accepted.value.revision).value.original_bytes,accepted.value.report_bytes)
        # Historical reports retain their original bytes/format.
        self.assertNotEqual(json.loads(a.report_in_transaction(t,1).value.original_bytes)['interfaceVersion'],'truss-catalog-registration-report/0.3')
        h.detach();c.commit()
        self.assertEqual(self.admin.execute('SELECT ver FROM truss.object WHERE id=%s',(int(identity.id),)).fetchone(),(2,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_catalog_rebind_transition').fetchone(),(1,))
        # Rebinding is one committed feed transaction with its catalog revision.
        self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin)
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value;admin_tx=admin_host.adopt_transaction().value
        self.assertIsInstance(admin_assembly.configure_module_access_in_transaction(admin_tx,(ModuleAccessGrant('zdoc','m','group_reader','group_writer'),)),Ok)
        self.assertIsInstance(admin_assembly.register_feed_consumer_in_transaction(admin_tx,consumer_id='rebind-feed',reader_role='group_reader'),Ok)
        admin_host.detach();self.admin.commit();self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        found_rebind=False
        for _ in range(5):
            c,h,a,t=self.consumer();page=a.read_feed_in_transaction(t,consumer_id='rebind-feed')
            self.assertIsInstance(page.value,FeedPage,repr(page)+' '+str(h._custody.last_attempt.error));payload=json.loads(page.value.content)
            operations=[e['op'] for e in payload['changes']]
            if 'rebind' in operations:
                self.assertEqual(operations.count('rebind'),3);self.assertEqual(operations.count('metadata'),1)
                self.assertEqual(len(payload['revisions']),1);found_rebind=True
            self.assertIsInstance(a.acknowledge_feed_in_transaction(t,page.value),Ok)
            h.detach();c.commit()
            if found_rebind:break
        self.assertTrue(found_rebind)
        # Metadata can still be read by a registrar; data-bearing reports cannot.
        self.admin.execute('REVOKE group_writer,group_reader FROM consumer')
        c,h,a,t=self.consumer()
        denied=a.report_in_transaction(t,accepted.value.revision)
        self.assertIsInstance(denied,Error,repr(denied));self.assertEqual(denied.error.sql_state,'42501')
        self.assertIsInstance(a.catalog_view_in_transaction(t,a.catalog_view_request()),Ok)
        h.detach();c.rollback()


    def test_invalid_candidate_refuses_without_changing_data(self):
        c,h,a,t=self.ready(self.fields)
        operation=replace(self.create(),values=self.create().values+(AuthoredValue(name='giftWrap',value=TextValue(kind='string',text='invalid-boolean')),))
        context=a.group_context_in_transaction(t).value
        self.assertIsInstance(self.apply(a,t,context.input((operation,),MapValue(entries=())),context.request('invalid-retained')),GroupSuccess)
        h.detach();c.commit()
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        document=self.revised(next(d for d in self.documents if d.document_id=='adoc'))
        c,h,a,t=self.consumer();prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        refused=a.accept_in_transaction(t,prepared,request_key='invalid-rebind')
        self.assertIsInstance(refused,Ok,repr(refused));self.assertIsInstance(refused.value,CatalogAcceptanceRefused,repr(refused))
        self.assertEqual([(v.field_id,v.rule,v.affected_object_count) for v in refused.value.violations],[('giftWrap','property.rebind_value',1)])
        h.detach();c.commit()
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(1,))
        self.assertEqual(self.admin.execute('SELECT ver,retained FROM truss.object').fetchone(),(1,{'giftWrap':{'kind':'string','text':'invalid-boolean'}}))

    def test_create_and_register_in_one_host_transaction(self):
        c,h,a,t=self.ready(self.fields)
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        operation=replace(self.create(),values=self.create().values+(AuthoredValue(name='giftWrap',value=BooleanValue(value=True)),))
        context=a.group_context_in_transaction(t).value
        created=self.apply(a,t,context.input((operation,),MapValue(entries=())),context.request('same-transaction-create'))
        self.assertIsInstance(created,GroupSuccess);identity=created.response.semantic.results[0].identity
        document=self.revised(next(d for d in self.documents if d.document_id=='adoc'))
        prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        accepted=a.accept_in_transaction(t,prepared,request_key='same-transaction-rebind')
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(h._custody.last_attempt.error))
        self.assertIsInstance(accepted.value,CatalogRegistration)
        h.detach();c.commit()
        self.assertEqual(self.admin.execute('SELECT ver FROM truss.object WHERE id=%s',(int(identity.id),)).fetchone(),(2,))

class CatalogRebind08Tests(CatalogRebindTests):
    source_version='0.8.0'
