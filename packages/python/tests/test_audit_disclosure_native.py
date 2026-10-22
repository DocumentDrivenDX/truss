# SPDX-License-Identifier: MIT OR Apache-2.0
"""Independent journal-only authority and complete retained group discovery."""
import psycopg
from truss import (Ok, ModuleAccessGrant, ModuleAuditGrant, LoadAuditUnavailable,
    MutationGroupAuditPage, MutationGroupAuditListingEnd, PersonRuntimeStatus, ObjectReadRefused,
    CatalogRuntimeConfiguration, adopt_psycopg_host, create_reference_assembly)
from truss.contracts import MapValue,MapEntry,TextValue
from truss.groups import Delete,StoredObjectReference
import test_object_mutations_native as base


class AuditDisclosureNativeTests(base.ObjectMutationTests):
    for _name in tuple(n for n in dir(base.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def administer(self,callback):
        self.admin.execute('BEGIN')
        host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
        tx=host.adopt_transaction().value
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        try:
            result=callback(assembly,tx)
            self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error))
            host.detach();self.admin.commit()
            return result.value
        finally:
            host.detach()
            self.admin.rollback()

    def audit_person(self):
        params=psycopg.conninfo.conninfo_to_dict(self.runtime.info.connection_uri);params['user']='journal_person'
        connection=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000')
        connection.execute('BEGIN READ ONLY')
        host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000)
        self.consumer_connections.append((connection,host))
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        return connection,host,assembly,host.adopt_transaction(access_mode='read_only').value

    def setup_scopes(self):
        c,h,a,t=self.ready();h.detach();c.rollback()
        self.administer(lambda assembly,tx:assembly.configure_module_access_in_transaction(tx,
            (ModuleAccessGrant('zdoc','m','group_reader','group_writer'),)))
        for role in ('journal_a','journal_b'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN NOINHERIT').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('CREATE ROLE journal_person LOGIN')
        self.addCleanup(self.admin.execute,'DROP ROLE journal_person')
        for doc,role in (('adoc','journal_a'),('zdoc','journal_b')):
            updated=self.administer(lambda assembly,tx:assembly.grant_module_audit_access_in_transaction(tx,
                ModuleAuditGrant(document_id=doc,module_id='m',auditor_role=role)))
            self.assertEqual(updated.outcome,'updated',repr(updated))
        self.admin.execute('GRANT journal_a TO journal_person WITH INHERIT TRUE, SET FALSE')

    def committed(self,operations,action='audit-action'):
        c,h,a,t=self.consumer()
        context=a.group_context_in_transaction(t).value
        result=a.apply_in_transaction(t,context.input(tuple(operations),MapValue(entries=(
            MapEntry(key='x-action',value=TextValue(kind='string',text=action)),))),context.request(action),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(h._custody.last_attempt.error))
        self.assertEqual(result.value.outcome,'success',repr(result))
        h.detach();c.commit()
        return result.value.response.semantic.results

    def page(self,assembly,tx,filters,cursor=None):
        result=assembly.page_mutation_group_audit_in_transaction(tx,filters=filters,cursor=cursor)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(assembly._host._custody.last_attempt.error))
        return result.value

    def test_audit_only_scope_filters_unrelated_groups_but_refuses_mixed_group(self):
        self.setup_scopes()
        self.committed((self.create(document='adoc',label='a-secret',alias='a'),),'first-a')
        self.committed((self.create(document='zdoc',label='b-secret',alias='b'),),'newer-b')
        c,h,a,t=self.audit_person();scope={'documentId':'adoc','moduleId':'m'}
        status=a.person_runtime_status_in_transaction(t)
        self.assertEqual(status,Ok(PersonRuntimeStatus(installation='compatible',catalog='accepted')))
        page=self.page(a,t,scope)
        self.assertIsInstance(page,MutationGroupAuditPage,repr(page))
        self.assertEqual(page.asserted_action,'first-a')
        self.assertNotIn('a-secret',repr(page));self.assertNotIn('b-secret',repr(page))
        # A journal role grants no ordinary table/record reader authority.
        denied=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=1)
        self.assertIsInstance(denied,Ok,repr(denied))
        self.assertIsInstance(denied.value,ObjectReadRefused,repr(denied.value))
        h.detach();c.rollback()
        self.committed((self.create(document='adoc',label='mixed-a',alias='a'),
            self.create(document='zdoc',label='mixed-b',alias='b')),'mixed')
        c,h,a,t=self.audit_person()
        refused=self.page(a,t,scope)
        self.assertIsInstance(refused,LoadAuditUnavailable,repr(refused))
        self.assertEqual(refused.reason,'unauthorized')
        self.admin.execute('GRANT journal_b TO journal_person WITH INHERIT TRUE, SET FALSE')
        complete=self.page(a,t,scope)
        self.assertIsInstance(complete,MutationGroupAuditPage,repr(complete))
        self.assertEqual(complete.asserted_action,'mixed')
        self.assertEqual({owner['documentId'] for owner in complete.owner_scopes},{'adoc','zdoc'})
        h.detach();c.commit()

    def test_deleted_entity_type_filter_and_descending_python_continuation(self):
        self.setup_scopes()
        results=self.committed((self.create(label='deleted-secret'),),'create-deleted')
        identity=results[0].identity
        self.committed((Delete(operation='delete_object',target=StoredObjectReference(identity=identity)),),'delete-retained')
        c,h,a,t=self.audit_person()
        scope={'documentId':'adoc','moduleId':'m','entityType':identity.type_id}
        newest=self.page(a,t,scope)
        self.assertIsInstance(newest,MutationGroupAuditPage,repr(newest))
        self.assertEqual(newest.asserted_action,'delete-retained')
        self.assertEqual({entry.operation for entry in newest.entries},{'delete'})
        older=self.page(a,t,scope,newest.next_page_cursor)
        self.assertIsInstance(older,MutationGroupAuditPage,repr(older))
        self.assertEqual(older.asserted_action,'create-deleted')
        self.assertEqual({entry.operation for entry in older.entries},{'create'})
        self.assertGreaterEqual(newest.observed_at,older.observed_at)
        end=self.page(a,t,scope,older.next_page_cursor)
        self.assertIsInstance(end,MutationGroupAuditListingEnd,repr(end))
        for value in (newest,older):self.assertNotIn('deleted-secret',repr(value))
        h.detach();c.commit()

    def test_unqualified_discovery_omits_hidden_whole_groups_and_binds_cursor(self):
        self.setup_scopes()
        self.committed((self.create(document='adoc',label='visible-a',alias='a'),),'visible-a')
        self.committed((self.create(document='zdoc',label='hidden-b',alias='b'),),'hidden-b')
        self.committed((self.create(document='adoc',label='mixed-a',alias='a'),self.create(document='zdoc',label='mixed-b',alias='b')),'mixed-hidden')
        c,h,a,t=self.audit_person();page=self.page(a,t,{})
        self.assertIsInstance(page,MutationGroupAuditPage,repr(page));self.assertEqual(page.asserted_action,'visible-a')
        self.assertIsInstance(self.page(a,t,{},page.next_page_cursor),MutationGroupAuditListingEnd)
        self.assertIsInstance(self.page(a,t,{'documentId':'adoc','moduleId':'m'},page.next_page_cursor),LoadAuditUnavailable)
        h.detach();c.rollback();self.admin.execute('GRANT journal_b TO journal_person WITH INHERIT TRUE, SET FALSE')
        c,h,a,t=self.audit_person();both=self.page(a,t,{})
        self.assertIsInstance(both,MutationGroupAuditPage,repr(both));self.assertEqual(both.asserted_action,'mixed-hidden')
        self.assertEqual(len(both.owner_scopes),2)

    def test_whole_group_more_than_1024_events_uses_separate_event_budget(self):
        from truss.groups import UpdateObject,AliasObjectReference,AuthoredValue
        self.setup_scopes();operations=[]
        for i in range(350):
            alias='many'+str(i);operations.append(self.create(label=alias,value='before',alias=alias))
            operations.append(UpdateObject(target=AliasObjectReference(alias=alias),set=(
                AuthoredValue(name='A-label',value=TextValue(kind='string',text=alias+'-changed')),
                AuthoredValue(name='A-value',value=TextValue(kind='string',text='after'))),unset=()))
        self.committed(tuple(operations),'many-events')
        c,h,a,t=self.audit_person()
        default=self.page(a,t,{'documentId':'adoc','moduleId':'m'});self.assertIsInstance(default,LoadAuditUnavailable)
        result=a.page_mutation_group_audit_in_transaction(t,filters={'documentId':'adoc','moduleId':'m'},maximum_events=4096)
        self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,MutationGroupAuditPage,repr(result))
        self.assertGreater(int(result.value.event_count),1024);self.assertEqual(int(result.value.operation_count),700)

    def test_optional_key_version_projection_requires_separate_readers_and_named_key(self):
        self.setup_scopes();created=self.committed((self.create(label='exact-key',value='value',alias='a'),),'projected-create')
        c,h,a,t=self.audit_person();scope={'documentId':'adoc','moduleId':'m'}
        refused=self.page(a,t,dict(scope,includeData=True));self.assertIsInstance(refused,LoadAuditUnavailable,repr(refused))
        plain=self.page(a,t,scope);self.assertIsInstance(plain,MutationGroupAuditPage);self.assertTrue(all(e.data is None for e in plain.entries))
        h.detach();c.rollback();self.admin.execute('GRANT group_reader TO journal_person WITH INHERIT TRUE, SET FALSE')
        c,h,a,t=self.audit_person();projected=self.page(a,t,dict(scope,includeData=True))
        self.assertIsInstance(projected,MutationGroupAuditPage,repr(projected));data=projected.entries[0].data
        self.assertEqual(data['basis'],'retained-operation');self.assertIsNone(data['before']);self.assertEqual(data['after']['version'],'1')
        alternate=next(k for k in data['after']['keys'] if k['keyId']=='z-alt')
        self.assertEqual(alternate['values'],[{'kind':'string','text':'exact-key'}])
        named={'documentId':'adoc','moduleId':'m','recordId':'A','keyId':'z-alt','values':[{'kind':'string','text':'exact-key'}]}
        found=self.page(a,t,dict(scope,entityKey=named));self.assertIsInstance(found,MutationGroupAuditPage,repr(found))
        self.assertEqual(found.attempt_id,projected.attempt_id)
        missing=self.page(a,t,dict(scope,entityKey=dict(named,values=[{'kind':'string','text':'absent'}])))
        self.assertIsInstance(missing,MutationGroupAuditListingEnd,repr(missing))
        h.detach();c.rollback();self.admin.execute('REVOKE group_reader FROM journal_person')
        c,h,a,t=self.audit_person();self.assertIsInstance(self.page(a,t,dict(scope,entityKey=named)),LoadAuditUnavailable)
