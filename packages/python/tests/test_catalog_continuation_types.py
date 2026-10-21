# SPDX-License-Identifier: MIT OR Apache-2.0
"""Typed catalog continuation tokens and source expectations reject bad carriers."""
import unittest

from truss.catalog_results import (CatalogDocumentExpectation, CatalogCASConflict,
    RegistrarStatus, ModuleAccessError, ModuleAccessBatchRefused)
from truss.reader_catalog import ReaderCatalog, ReaderCatalogSnapshot, ReaderCatalogUnchanged
from truss.catalog_runtime import _catalog_failure
from truss.execution import Error, ExecutionFailure
from truss import Ok


class CatalogContinuationTypesTests(unittest.TestCase):
    def test_reader_validator_is_bounded_and_snapshot_is_typed(self):
        catalog=ReaderCatalog(3,{},())
        self.assertEqual(ReaderCatalogSnapshot(catalog,'a'*64).catalog,catalog)
        self.assertEqual(ReaderCatalogUnchanged('b'*64).validator,'b'*64)
        for validator in ('', '\0token', 'x'*4097, 23):
            with self.subTest(validator=validator),self.assertRaises(ValueError):
                ReaderCatalogUnchanged(validator)
        with self.assertRaises(ValueError):
            ReaderCatalogSnapshot(object(),'a'*64)

    def test_document_expectation_uses_nonnegative_native_revision(self):
        self.assertEqual(CatalogDocumentExpectation('sales',0).source_catalog_revision,0)
        self.assertEqual(CatalogDocumentExpectation('sales',2147483647).source_catalog_revision,2147483647)
        for revision in (-1,True,2147483648):
            with self.subTest(revision=revision),self.assertRaises(ValueError):
                CatalogDocumentExpectation('sales',revision)
        for document_id in ('', '\0', 'x'*4097, '\ud800'):
            with self.subTest(document_id=repr(document_id)),self.assertRaises(ValueError):
                CatalogDocumentExpectation(document_id,0)

    def test_probe_and_conflict_carriers_are_advisory_and_typed(self):
        self.assertTrue(RegistrarStatus(True).can_register)
        self.assertFalse(RegistrarStatus(False).can_register)
        with self.assertRaises(ValueError):
            RegistrarStatus(1)
        self.assertEqual(CatalogCASConflict().outcome,'conflict')

    def test_only_private_catalog_cas_sqlstate_becomes_a_typed_conflict(self):
        mismatch=_catalog_failure(Error(ExecutionFailure('execution_obligation','revision moved',sql_state='P1011')))
        self.assertEqual(mismatch,Ok(CatalogCASConflict()))
        serialization=Error(ExecutionFailure('retry','retry whole transaction',sql_state='40001',retry_scope='whole_transaction'))
        self.assertIs(_catalog_failure(serialization),serialization)
        unrelated=Error(ExecutionFailure('execution_obligation','same SQLSTATE, different host code',sql_state='P1011'))
        self.assertEqual(_catalog_failure(unrelated),Ok(CatalogCASConflict()))

    def test_module_access_refusal_contains_only_ordered_indexes_and_codes(self):
        refused=ModuleAccessBatchRefused((ModuleAccessError(0,'unknown_module'),
                                         ModuleAccessError(2,'duplicate_selection')))
        self.assertEqual(tuple(error.index for error in refused.errors),(0,2))
        with self.assertRaises(ValueError):
            ModuleAccessError(512,'unknown_module')
        with self.assertRaises(ValueError):
            ModuleAccessBatchRefused(())


if __name__=='__main__':
    unittest.main()
