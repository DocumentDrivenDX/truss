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


class OwnedCatalogKeyBackfillTests(CatalogKeyBackfillTests):
    """Existing owned children gain keys without changing their data or roots."""
    for _name in tuple(n for n in dir(CatalogKeyBackfillTests) if n.startswith('test_')):
        locals()[_name]=None
    source_version='0.8.0'

    def fields(self,source):
        super().fields(source)
        module=source['modules'][0]
        roots=[e for e in module['elements'] if e['id']=='B' or e['id'].startswith('B-')]
        module['elements']=[e for e in module['elements'] if e not in roots]
        record=next(e for e in roots if e['kind']=='record')
        for reference in record['members']+[f for k in record['keys'] for f in k['fields']]:
            reference['module']='roots'
        module['relationships'][0]['target'][0]['module']='roots'
        module['relationships'].append({'id':'children','name':'children',
            'source':[{'module':'roots','element':'B'}],
            'target':[{'module':'m','element':'A','key':'a-primary'}],
            'sourceMultiplicity':{'min':0,'max':1},'targetMultiplicity':{'min':0,'max':4},
            'targetLifecycle':'owned','directed':True})
        source['modules'].append({'id':'roots','namespace':'roots','elements':roots,'relationships':[],'extensions':{}})

    def seed_owned(self,values=('first','second')):
        import psycopg
        from truss import ModuleAccessGrant,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
        from truss.groups import OwnedOwnership,AliasObjectReference,CreateEdge,NullOrderKey
        c,h,a,t=self.ready(self.fields,document_ids=('adoc',));h.detach();c.rollback()
        for role in ('roots_reader','roots_writer'):
            self.admin.execute('CREATE ROLE '+role+' NOLOGIN')
            self.addCleanup(self.admin.execute,'DROP ROLE '+role)
        self.admin.execute('BEGIN');host=adopt_psycopg_host(self.admin);tx=host.adopt_transaction().value
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        self.assertIsInstance(assembly.configure_module_access_in_transaction(tx,
            (ModuleAccessGrant('adoc','roots','roots_reader','roots_writer'),)),Ok)
        host.detach();self.admin.commit()
        self.admin.execute('GRANT roots_reader,roots_writer TO consumer WITH SET FALSE')
        c,h,a,t=self.consumer();relation=a.get_relationship_reference_in_transaction(t,
            document_id='adoc',module_id='m',relationship_id='children').value
        operations=[self.create('root','root',alias='root',record='B')]
        for index,value in enumerate(values):
            alias='child'+str(index)
            operations.extend((replace(self.create(str(index),value,alias=alias),
                ownership=OwnedOwnership(root=AliasObjectReference(alias='root'))),
                CreateEdge(relationship_definition_pin=relation.definition_pin,
                    source=AliasObjectReference(alias='root'),target=AliasObjectReference(alias=alias),
                    values=(),order_key=NullOrderKey())))
        context=a.group_context_in_transaction(t).value
        created=a.apply_in_transaction(t,context.input(tuple(operations),MapValue(entries=())),context.request('owned-before-key'),documents=self.documents)
        self.assertIsInstance(created,Ok,repr(created)+' '+str(h._custody.last_attempt.error))
        self.assertIsInstance(created.value,GroupSuccess,repr(created))
        identities=tuple(r.identity for r in created.value.response.semantic.results)
        h.detach();c.commit()
        self.admin.execute('REVOKE roots_writer FROM consumer')
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        self.original_images=self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall()
        self.original_keys=self.admin.execute('SELECT to_jsonb(k) FROM truss.object_key_bucket k ORDER BY storage_row_id').fetchall()
        self.original_journal=self.admin.execute('SELECT count(*) FROM truss.journal').fetchone()
        return identities[0],identities[1]

    def assert_preserved(self,*,keys=False):
        self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall(),self.original_images)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(),self.original_journal)
        if keys:self.assertEqual(self.admin.execute('SELECT to_jsonb(k) FROM truss.object_key_bucket k ORDER BY storage_row_id').fetchall(),self.original_keys)

    def test_owned_backfill_commit_reopen_and_reader_scoped_retry(self):
        from truss import Error
        from truss.groups import OwnedOwnership,StoredObjectReference
        root,child=self.seed_owned();c,h,a,t=self.consumer();accepted=self.register(a,t)
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(h._custody.last_attempt.error))
        self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted))
        original=accepted.value.report_bytes;revision=accepted.value.revision
        self.assertEqual(len(json.loads(original)['keyBackfills']),2)
        h.detach();c.commit();self.assert_preserved()
        c,h,a,t=self.consumer()
        found=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-backfill',values=('first',))
        self.assertIsInstance(found,Ok,repr(found));self.assertIsInstance(found.value,ObjectFound,repr(found))
        self.assertEqual(found.value.object.id,int(child.id));self.assertEqual(found.value.object.version,1)
        self.assertEqual(found.value.object.ownership,OwnedOwnership(root=StoredObjectReference(identity=root)))
        retry=self.register(a,t);self.assertIsInstance(retry,Ok,repr(retry))
        self.assertTrue(retry.value.replayed);self.assertEqual(retry.value.report_bytes,original)
        h.detach();c.commit();self.admin.execute('REVOKE roots_reader FROM consumer')
        c,h,a,t=self.consumer();report=a.report_in_transaction(t,revision)
        self.assertIsInstance(report,Error,repr(report));self.assertEqual(report.error.sql_state,'42501')
        h.detach();c.rollback();c,h,a,t=self.consumer();retry=self.register(a,t)
        self.assertIsInstance(retry,Error,repr(retry));self.assertEqual(retry.error.sql_state,'42501')
        h.detach();c.rollback()

    def test_missing_root_reader_refuses_before_acceptance(self):
        from truss import Error
        self.seed_owned();self.admin.execute('REVOKE roots_reader FROM consumer')
        c,h,a,t=self.consumer();accepted=self.register(a,t)
        self.assertIsInstance(accepted,Error,repr(accepted));self.assertEqual(accepted.error.sql_state,'42501')
        h.detach();c.rollback();self.assert_preserved(keys=True)

    def test_root_reader_revoked_before_commit_aborts_backfill(self):
        import psycopg
        self.seed_owned();c,h,a,t=self.consumer();accepted=self.register(a,t)
        self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogRegistration)
        self.admin.execute('REVOKE roots_reader FROM consumer');h.detach()
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.commit()
        c.rollback();self.assert_preserved(keys=True)

    def test_duplicate_owned_candidates_preserve_images_and_keys(self):
        self.seed_owned(('same','same'));c,h,a,t=self.consumer();accepted=self.register(a,t)
        self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogAcceptanceRefused,repr(accepted))
        self.assertEqual([(v.rule,v.affected_object_count) for v in accepted.value.violations],[('key.duplicate',2)])
        h.detach();c.commit();self.assert_preserved(keys=True)
