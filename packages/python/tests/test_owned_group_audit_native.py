# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native audit pages disclose complete edge endpoint and owned-cascade scopes."""
from copy import deepcopy
from dataclasses import replace

from truss import (Ok, ModuleAccessGrant, ModuleAuditGrant, LoadAuditUnavailable,
                   MutationGroupAuditPage, adopt_psycopg_host,
                   create_reference_assembly, CatalogRuntimeConfiguration)
from truss.groups import (OwnedOwnership, StoredObjectReference, AliasObjectReference,
                          Delete, GroupSuccess)
from truss.contracts import MapValue
import test_edge_mutations_native as edge_tests


class OwnedGroupAuditNativeTests(edge_tests.EdgeMutationTests):
    for _name in tuple(n for n in dir(edge_tests.EdgeMutationTests) if n.startswith('test_')):
        locals()[_name] = None

    @staticmethod
    def split_endpoint_modules(source):
        module=source['modules'][0]
        moved=[]
        retained=[]
        for element in module['elements']:
            if element['id']=='B' or element['id'].startswith('B-'):
                copied=deepcopy(element)
                if copied['kind']=='record':
                    for member in copied['members']:
                        member['module']='n'
                    for key in copied['keys']:
                        for field in key['fields']:
                            field['module']='n'
                moved.append(copied)
            else:
                retained.append(element)
        module['elements']=retained
        module['relationships'][0]['target'][0]['module']='n'
        module['relationships'][0]['targetLifecycle']='owned'
        source['modules'].append({'id':'n','namespace':'n','extensions':{},
                                  'elements':moved,'relationships':[]})

    def test_edge_endpoints_and_owned_cascade_require_complete_audit_scope(self):
        connection,host,assembly,tx=self.ready(self.split_endpoint_modules,
                                                document_ids=('adoc',))
        self.admin.execute('BEGIN')
        admin_host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        admin_tx=admin_host.adopt_transaction().value
        configured=admin_assembly.configure_module_access_in_transaction(admin_tx,(
            ModuleAccessGrant('adoc','n','group_reader','group_writer'),))
        self.assertIsInstance(configured,Ok,repr(configured))
        admin_host.detach();self.admin.commit()

        relation=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',
            module_id='m',relationship_id='A-B')
        self.assertIsInstance(relation,Ok,repr(relation))
        self.assertIsNotNone(relation.value)
        context=assembly.group_context_in_transaction(tx).value
        root=self.create(label='audit-root',value='root',alias='root',record='A')
        child=self.create(label='audit-child',value='child',alias='child',record='B')
        child=replace(child,ownership=OwnedOwnership(root=AliasObjectReference(alias='root')))
        operations=(root,child,self.link(relation.value.definition_pin,
            AliasObjectReference(alias='root'),AliasObjectReference(alias='child'),alias='owned-link'))
        applied=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),
            context.request('owned-audit-create'),documents=self.documents,
            bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(applied,Ok,repr(applied))
        self.assertIsInstance(applied.value,GroupSuccess,repr(applied.value))
        root_id,child_id,edge_id=(item.identity for item in applied.value.response.semantic.results)
        writer_xid=connection.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        host.detach();connection.commit()
        create_attempt=self.admin.execute(
            'SELECT id::text FROM truss.runtime_object_attempt WHERE writer_xid=%s::xid8 AND complete ORDER BY id DESC LIMIT 1',
            (writer_xid,)).fetchone()[0]

        self.admin.execute('CREATE ROLE owned_group_audit_reader NOLOGIN NOINHERIT')
        def cleanup_auditor():
            self.admin.execute('DROP ROLE IF EXISTS owned_group_audit_reader')
        self.addCleanup(cleanup_auditor)
        self.admin.execute('BEGIN')
        admin_host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        admin_tx=admin_host.adopt_transaction().value
        grant_m=admin_assembly.grant_module_audit_access_in_transaction(admin_tx,
            ModuleAuditGrant(document_id='adoc',module_id='m',auditor_role='owned_group_audit_reader'))
        self.assertIsInstance(grant_m,Ok,repr(grant_m))
        admin_host.detach();self.admin.commit()
        self.admin.execute('GRANT owned_group_audit_reader TO consumer WITH INHERIT TRUE, SET FALSE')

        connection,host,assembly,tx=self.consumer()
        filters={'documentId':'adoc','moduleId':'m','attemptId':create_attempt}
        denied=assembly.page_mutation_group_audit_in_transaction(tx,filters=filters)
        self.assertIsInstance(denied,Ok,repr(denied))
        self.assertIsInstance(denied.value,LoadAuditUnavailable)
        self.assertEqual(denied.value.reason,'unauthorized')
        host.detach();connection.rollback()

        self.admin.execute('BEGIN')
        admin_host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        admin_tx=admin_host.adopt_transaction().value
        grant_n=admin_assembly.grant_module_audit_access_in_transaction(admin_tx,
            ModuleAuditGrant(document_id='adoc',module_id='n',auditor_role='owned_group_audit_reader'))
        self.assertIsInstance(grant_n,Ok,repr(grant_n))
        admin_host.detach();self.admin.commit()

        connection,host,assembly,tx=self.consumer()
        created=assembly.page_mutation_group_audit_in_transaction(tx,filters=filters)
        self.assertIsInstance(created,Ok,repr(created)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(created.value,MutationGroupAuditPage,repr(created.value))
        self.assertEqual({(scope['documentId'],scope['moduleId']) for scope in created.value.owner_scopes},
                         {('adoc','m'),('adoc','n')})
        self.assertEqual({entry.entity_kind for entry in created.value.entries},{'object','edge'})

        deletion_context=assembly.group_context_in_transaction(tx).value
        deletion=Delete(operation='delete_object',target=StoredObjectReference(identity=root_id),
                        expected_version='1')
        deleted=assembly.apply_in_transaction(tx,deletion_context.input((deletion,),MapValue(entries=())),
            deletion_context.request('owned-audit-delete'),documents=self.documents,
            bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(deleted,Ok,repr(deleted))
        self.assertIsInstance(deleted.value,GroupSuccess,repr(deleted.value))
        self.assertEqual({entry.identity for entry in deleted.value.response.semantic.results[0].deleted},
                         {root_id,child_id,edge_id})
        delete_writer_xid=connection.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        host.detach();connection.commit()
        delete_attempt=self.admin.execute(
            'SELECT id::text FROM truss.runtime_object_attempt WHERE writer_xid=%s::xid8 AND complete ORDER BY id DESC LIMIT 1',
            (delete_writer_xid,)).fetchone()[0]

        connection,host,assembly,tx=self.consumer()
        cascade=assembly.page_mutation_group_audit_in_transaction(tx,
            filters={'documentId':'adoc','moduleId':'m','attemptId':delete_attempt})
        self.assertIsInstance(cascade,Ok,repr(cascade)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(cascade.value,MutationGroupAuditPage,repr(cascade.value))
        self.assertEqual({(scope['documentId'],scope['moduleId']) for scope in cascade.value.owner_scopes},
                         {('adoc','m'),('adoc','n')})
        self.assertGreaterEqual(sum(entry.entity_kind=='object' and entry.operation=='delete'
                                    for entry in cascade.value.entries),2)
        self.assertGreaterEqual(sum(entry.entity_kind=='edge' and entry.operation=='delete'
                                    for entry in cascade.value.entries),1)
        host.detach();connection.rollback()
        self.admin.execute('REVOKE owned_group_audit_reader FROM consumer')
        self.admin.execute('DELETE FROM truss.runtime_import_audit_access WHERE auditor_oid=(SELECT oid FROM pg_roles WHERE rolname=%s)',
                           ('owned_group_audit_reader',))


if __name__ == '__main__':
    import unittest
    unittest.main()
