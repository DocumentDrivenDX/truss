# SPDX-License-Identifier: MIT OR Apache-2.0
"""Typed facade outcomes for contained authorization refusals."""
import threading
import unittest
from unittest.mock import patch

from truss import (CatalogRefused, Error, ObjectReadRefused, Ok,
                   CatalogRuntimeConfiguration,
                   create_reference_assembly, adopt_psycopg_host)
from truss.catalog_runtime import CatalogReferenceAssembly
from truss.execution import ExecutionFailure
from truss.groups import UnauthorizedPerson
import test_group_create_native as group_tests


class _Host:
    def __init__(self, result):
        self.result = result

    def _run_operation(self, transaction, callback, **kwargs):
        return self.result


class CatalogAdmissionOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.release = patch('truss.catalog_runtime._release',
            return_value=({'releaseId': 'test-release'}, 'test-digest', ()))
        self.release.start()
        self.addCleanup(self.release.stop)

    def assembly(self, result):
        assembly = object.__new__(CatalogReferenceAssembly)
        assembly._lock = threading.RLock()
        assembly._disposed = False
        assembly._host = _Host(result)
        assembly._group_documents = ()
        return assembly

    def test_catalog_and_group_admission_refusals_are_typed(self):
        denied = Error(ExecutionFailure('execution_obligation', 'denied', sql_state='P1403'))
        assembly = self.assembly(denied)
        self.assertIsInstance(assembly.group_context_in_transaction(None).value, UnauthorizedPerson)
        self.assertIsInstance(assembly.catalog_revision_in_transaction(None).value, CatalogRefused)
        self.assertIsInstance(assembly.prepare_group_in_transaction(None, records=()).value, CatalogRefused)
        self.assertIsInstance(assembly.get_type_reference_in_transaction(
            None, document_id='d', module_id='m', record_id='r').value, CatalogRefused)
        self.assertIsInstance(assembly.get_relationship_reference_in_transaction(
            None, document_id='d', module_id='m', relationship_id='rel').value, CatalogRefused)

    def test_direct_object_key_and_edge_reads_return_typed_refusal(self):
        denied = Error(ExecutionFailure('execution_obligation', 'denied', sql_state='P1403'))
        assembly = self.assembly(denied)
        key = assembly.lookup_key_in_transaction(None, document_id='d', module_id='m',
            record_id='r', key_id='k', values=('v',))
        edge = assembly.get_edge_in_transaction(None, document_id='d', module_id='m',
            relationship_id='rel', edge_id=1)
        self.assertIsInstance(key, Ok)
        self.assertIsInstance(key.value, ObjectReadRefused)
        self.assertIsInstance(edge, Ok)
        self.assertIsInstance(edge.value, ObjectReadRefused)

    def test_owned_edge_builder_returns_safe_outer_refusal_without_dereference(self):
        from unittest.mock import patch

        assembly = self.assembly(Error(ExecutionFailure('execution_obligation', 'denied', sql_state='42501')))
        with patch.object(assembly, 'owned_import_context_in_transaction', return_value=Ok(object())), \
                patch.object(assembly, 'get_relationship_reference_in_transaction', return_value=Ok(CatalogRefused())):
            result = assembly.owned_edge_import_record_in_transaction(
                None, document_id='d', module_id='m', relationship_id='hidden-relationship-731',
                source_endpoint=object(), target_endpoint=object(), values=(), order_key=object())
        self.assertIsInstance(result, Error)
        self.assertEqual(result.error.code, 'execution_obligation')
        self.assertIsNone(result.error.sql_state)
        self.assertEqual(result.error.catalog_code, 'unauthorized')
        self.assertNotIn('hidden-relationship-731', result.error.message)

        original = Error(ExecutionFailure('transaction_unusable', 'original', sql_state='08006'))
        with patch.object(assembly, 'owned_import_context_in_transaction', return_value=Ok(object())), \
                patch.object(assembly, 'get_relationship_reference_in_transaction', return_value=original):
            propagated = assembly.owned_edge_import_record_in_transaction(
                None, document_id='d', module_id='m', relationship_id='hidden-relationship-731',
                source_endpoint=object(), target_endpoint=object(), values=(), order_key=object())
        self.assertIs(propagated, original)

    def test_only_contained_authorization_refusals_are_translated(self):
        for failure in (
            Error(ExecutionFailure('execution_obligation', 'actual damaged grant', sql_state='42501')),
            Error(ExecutionFailure('execution_obligation', 'transport', sql_state='08006')),
            Error(ExecutionFailure('transaction_unusable', 'failed', sql_state='42501')),
        ):
            assembly = self.assembly(failure)
            result = assembly.lookup_key_in_transaction(None, document_id='d', module_id='m',
                record_id='r', key_id='k', values=('v',))
            self.assertIs(result, failure)
            context = assembly.group_context_in_transaction(None)
            self.assertIs(context, failure)


class NativeCatalogAdmissionTests(group_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(group_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_nonmember_admission_is_typed_for_live_and_missing_selections(self):
        from truss.contracts import MapValue, TextValue
        from truss.groups import (AliasObjectReference, AuthoredValue, CreateEdge,
                                  TextOrderKey, GroupSuccess)
        from truss.traversal import TraversalHop

        connection, host, assembly, tx = self.ready(document_ids=('adoc', 'zdoc'))
        context = assembly.group_context_in_transaction(tx).value
        self.assertEqual(assembly.get_type_reference_in_transaction(
            tx, document_id='adoc', module_id='m', record_id='A').value, self.types[('adoc', 'A')])
        self.assertIsNone(assembly.get_type_reference_in_transaction(
            tx, document_id='zdoc', module_id='m', record_id='A').value)
        relationship = assembly.get_relationship_reference_in_transaction(
            tx, document_id='adoc', module_id='m', relationship_id='A-B').value
        operations = (
            self.create(alias='left'),
            self.create(alias='right', record='B'),
            CreateEdge(relationship_definition_pin=relationship.definition_pin,
                source=AliasObjectReference(alias='left'), target=AliasObjectReference(alias='right'),
                values=(AuthoredValue(name='note', value=TextValue(kind='string', text='edge')),),
                order_key=TextOrderKey(text='one'), alias='edge'),
        )
        created = self.apply(assembly, tx,
            context.input(operations, MapValue(entries=())), context.request('admission-seed'))
        self.assertIsInstance(created, GroupSuccess)
        object_id, target_id, edge_id = (int(item.identity.id) for item in created.response.semantic.results)
        object_identity = created.response.semantic.results[0].identity
        host.detach(); connection.commit()

        # Start a fresh transaction on the same ordinary connection before the
        # administrator removes the role. The later call observes current rights.
        connection.execute('BEGIN')
        host = adopt_psycopg_host(connection, statement_timeout_ms=10000, operation_timeout_ms=30000)
        self.addCleanup(host.detach)
        tx = host.adopt_transaction().value
        assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
        self.admin.execute('REVOKE group_writer FROM consumer')
        self.admin.execute('REVOKE group_reader FROM consumer')

        self.assertEqual(assembly.group_context_in_transaction(tx).value, UnauthorizedPerson())
        for result in (
            assembly.catalog_revision_in_transaction(tx),
            assembly.prepare_group_in_transaction(tx, records=(('adoc', 'm', 'A'),)),
            assembly.get_type_reference_in_transaction(tx, document_id='adoc', module_id='m', record_id='A'),
            assembly.get_type_reference_in_transaction(tx, document_id='adoc', module_id='m', record_id='missing'),
            assembly.get_relationship_reference_in_transaction(tx, document_id='adoc', module_id='m', relationship_id='A-B'),
            assembly.get_relationship_reference_in_transaction(tx, document_id='adoc', module_id='m', relationship_id='missing'),
        ):
            self.assertIsInstance(result, Ok)
            self.assertEqual(result.value, CatalogRefused())

        reads = (
            assembly.get_object_in_transaction(tx, document_id='adoc', module_id='m', record_id='A', object_id=object_id),
            assembly.get_object_in_transaction(tx, document_id='adoc', module_id='m', record_id='A', object_id=9223372036854775807),
            assembly.lookup_key_in_transaction(tx, document_id='adoc', module_id='m', record_id='A', key_id='a-primary', values=('value', 'one')),
            assembly.lookup_key_in_transaction(tx, document_id='adoc', module_id='m', record_id='A', key_id='missing', values=('value', 'one')),
            assembly.page_objects_in_transaction(tx, document_id='adoc', module_id='m', record_id='A'),
            assembly.page_objects_in_transaction(tx, document_id='adoc', module_id='m', record_id='missing'),
            assembly.get_edge_in_transaction(tx, document_id='adoc', module_id='m', relationship_id='A-B', edge_id=edge_id),
            assembly.get_edge_in_transaction(tx, document_id='adoc', module_id='m', relationship_id='missing', edge_id=edge_id),
            assembly.page_edges_in_transaction(tx, document_id='adoc', module_id='m', relationship_id='A-B', anchor=object_identity),
            assembly.page_edges_in_transaction(tx, document_id='adoc', module_id='m', relationship_id='missing', anchor=object_identity),
            assembly.traverse_in_transaction(tx, start=object_identity, hops=(TraversalHop(relationship=relationship),)),
        )
        self.assertTrue(all(isinstance(result, Ok) and result.value == ObjectReadRefused() for result in reads), repr(reads))
        self.assertEqual(connection.execute('SELECT 42').fetchone(), (42,))
        host.detach(); connection.rollback()

        # Re-adopt the ordinary consumer connection in read-only mode after revocation.
        connection, host, assembly, tx = self.consumer()
        host.detach()
        connection.execute('SET TRANSACTION READ ONLY')
        host = adopt_psycopg_host(connection, statement_timeout_ms=10000, operation_timeout_ms=30000)
        self.addCleanup(host.detach)
        adopted = host.adopt_transaction(access_mode='read_only')
        self.assertIsInstance(adopted, Ok)
        tx = adopted.value
        assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
        self.assertEqual(assembly.group_context_in_transaction(tx).value, UnauthorizedPerson())
        denied = assembly.get_object_in_transaction(tx, document_id='adoc', module_id='m', record_id='A', object_id=target_id)
        self.assertEqual(denied.value, ObjectReadRefused())
        self.assertEqual(connection.execute('SELECT 42').fetchone(), (42,))
        host.detach(); connection.rollback()


if __name__ == '__main__':
    unittest.main()
