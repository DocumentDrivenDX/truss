# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original executable construction custody, not installed runtime qualification."""
import dataclasses
import unittest
from unittest.mock import patch
from test_native_pg8000 import NativeBoundaryFixture
from truss._construction_recovery import ProvisionalConstructionRecovery,ConstructionOriginal
from truss._catalog_installation import (prepare_provisional_catalog_construction,
    execute_provisional_catalog_construction,construct_provisional_catalog_layout,CatalogConstructionFailure)


class ConstructionRecoveryTests(unittest.TestCase):
    def test_capacity_and_foreign_reference_refuse_before_run(self):
        connection=object()
        original=ConstructionOriginal(connection,b'source',b'target',b'baseline')
        registry=ProvisionalConstructionRecovery(retained_attempts=1)
        reference=registry.reserve(original)
        with self.assertRaisesRegex(ValueError,'retention exhausted'):
            registry.reserve(original)
        with self.assertRaisesRegex(ValueError,'Foreign'):
            ProvisionalConstructionRecovery().inspect(reference)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            registry.inspect(reference).phase='changed'

    def test_mutable_original_bytes_refuse_registration(self):
        registry=ProvisionalConstructionRecovery()
        with self.assertRaisesRegex(ValueError,'immutable'):
            registry.reserve(ConstructionOriginal(object(),bytearray(b'source'),b'target',b'baseline'))
        self.assertEqual(registry.references(),())

    def test_unresolved_connection_cannot_start_another_attempt(self):
        original=ConstructionOriginal(object(),b'source',b'target',b'baseline')
        registry=ProvisionalConstructionRecovery()
        reference=registry.reserve(original)
        registry.acquire(reference)
        registry.settle(reference,rollback_confirmed=False,primary=None,cleanup=None)
        with self.assertRaisesRegex(ValueError,'Unresolved'):
            registry.reserve(original)
        with self.assertRaisesRegex(ValueError,'twice'):
            registry.acquire(reference)

    def test_metadata_originals_retained_before_any_submission(self):
        recipe=b'original candidate metadata recipe';input_bytes=b'original candidate input'
        registry=ProvisionalConstructionRecovery()
        original=ConstructionOriginal(object(),b'source',b'target',b'baseline',recipe,input_bytes,160)
        reference=registry.reserve(original)
        observation=registry.inspect(reference)
        self.assertIs(observation.original.metadata_recipe,recipe)
        self.assertIs(observation.original.metadata_input,input_bytes)
        self.assertEqual(observation.calls,())
        insufficient=ProvisionalConstructionRecovery()
        with self.assertRaisesRegex(ValueError,'call reservation'):
            insufficient.reserve(ConstructionOriginal(object(),b'source',b'target',b'baseline',recipe,input_bytes,128))
        self.assertEqual(insufficient.references(),())
        for recipe,input_bytes in ((b'recipe',b''),(b'',b'input'),
                (bytearray(b'recipe'),b'input'),(b'recipe',b'x'*1048577)):
            refused=ProvisionalConstructionRecovery()
            with self.assertRaises(ValueError):
                refused.reserve(ConstructionOriginal(object(),b'source',b'target',b'baseline',recipe,input_bytes))
            self.assertEqual(refused.references(),())

    def test_return_fact_survives_status_property_failure(self):
        failure=OSError('status inaccessible')
        class Port:
            def run(self,sql):return [['original']]
            @property
            def _transaction_status(self):raise failure
        registry=ProvisionalConstructionRecovery()
        reference=registry.reserve(ConstructionOriginal(Port(),b'source',b'target',b'baseline'))
        result=registry.acquire(reference).run('SELECT 1')
        self.assertEqual(result,[['original']])
        observation=registry.inspect(reference)
        self.assertTrue(observation.calls[0].returned)
        self.assertIs(observation.calls[0].observation_failure,failure)
        self.assertIsNone(observation.calls[0].exception)
        self.assertIsNone(observation.calls[0].status)
        self.assertEqual(observation.calls[0].original_result,(('original',),))

    def test_returned_original_survives_status_interrupt(self):
        result=[['retained native original']]
        class Port:
            def run(self,sql):return result
            @property
            def _transaction_status(self):raise KeyboardInterrupt()
        registry=ProvisionalConstructionRecovery()
        reference=registry.reserve(ConstructionOriginal(Port(),b'source',b'target',b'baseline'))
        with self.assertRaises(KeyboardInterrupt):registry.acquire(reference).run('SELECT original')
        result.clear()
        self.assertEqual(registry.inspect(reference).calls[0].original_result,(('retained native original',),))

    def test_cleanup_slots_reserved_after_ordinary_capacity(self):
        class Port:
            _transaction_status=b'I'
            def run(self,sql):return []
        registry=ProvisionalConstructionRecovery()
        reference=registry.reserve(ConstructionOriginal(Port(),b'source',b'target',b'baseline'))
        port=registry.acquire(reference)
        for _ in range(128):port.run('SELECT 1')
        with self.assertRaisesRegex(ValueError,'construction call slots'):
            port.run('SELECT 1')
        port.run('ROLLBACK');port.run('SELECT false::text')
        self.assertEqual(len(registry.inspect(reference).calls),130)


class ConstructionRecoveryNativeTests(NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        self.connection=self.Connection(**self.kwargs)
        self.connection.run('SELECT 1')
        self.recovery=ProvisionalConstructionRecovery()
    def tearDown(self):
        if self.connection is not None:self.connection.close()

    def test_original_handle_real_ddl_and_read_only_inspection(self):
        reference=prepare_provisional_catalog_construction(self.connection,self.recovery)
        prepared=self.recovery.inspect(reference)
        self.assertEqual(prepared.phase,'prepared')
        self.assertEqual(prepared.calls,())
        self.assertIs(prepared.original.connection,self.connection)
        result=execute_provisional_catalog_construction(self.recovery,reference)
        self.assertIs(result.recovery_reference,reference)
        observed=self.recovery.inspect(reference)
        self.assertEqual(observed.phase,'terminated')
        self.assertTrue(observed.rollback_confirmed)
        self.assertEqual(observed.calls[0].sql,'BEGIN')
        self.assertTrue(any(c.sql.startswith('CREATE TABLE') for c in observed.calls))
        self.assertEqual(observed.calls[-2].sql,'ROLLBACK')
        self.assertTrue(all(c.returned for c in observed.calls))
        self.connection.close();self.connection=None
        self.assertEqual(self.recovery.inspect(reference),observed)

    def test_lost_rollback_reply_keeps_exact_attempt_unresolved(self):
        connection=self.connection;loss=OSError('rollback reply lost');commands=[]
        class Port:
            @property
            def _transaction_status(self):return connection._transaction_status
            def run(self,sql):
                commands.append(sql)
                result=connection.run(sql)
                if sql=='ROLLBACK':raise loss
                return result
        port=Port()
        reference=prepare_provisional_catalog_construction(port,self.recovery)
        with self.assertRaises(CatalogConstructionFailure):
            execute_provisional_catalog_construction(self.recovery,reference)
        observed=self.recovery.inspect(reference)
        self.assertEqual(observed.phase,'unresolved')
        self.assertFalse(observed.rollback_confirmed)
        self.assertIs(observed.cleanup_failure,loss)
        rollback=observed.calls[-1]
        self.assertEqual(rollback.sql,'ROLLBACK')
        self.assertFalse(rollback.returned)
        self.assertIs(rollback.exception,loss)
        # Idle status after a lost reply is retained, never upgraded to settlement.
        self.assertEqual(rollback.status,b'I')
        before=len(commands)
        with self.assertRaisesRegex(ValueError,'Unresolved'):
            prepare_provisional_catalog_construction(port,self.recovery)
        self.assertEqual(len(commands),before)

    def test_lost_result_publication_preserves_known_rollback(self):
        reference=prepare_provisional_catalog_construction(self.connection,self.recovery)
        with patch('truss._catalog_installation.ProvisionalCatalogConstruction',side_effect=MemoryError('projection lost')):
            with self.assertRaises(MemoryError):
                execute_provisional_catalog_construction(self.recovery,reference)
        observation=self.recovery.inspect(reference)
        self.assertTrue(observation.rollback_confirmed)
        self.assertEqual(observation.phase,'terminated')
        self.assertEqual(sum(c.sql=='BEGIN' for c in observation.calls),1)
        self.assertEqual(sum(c.sql=='ROLLBACK' for c in observation.calls),1)

    def test_registration_failure_before_begin(self):
        with patch.object(self.recovery,'reserve',side_effect=OSError('registry failed')):
            with self.assertRaises(OSError):
                prepare_provisional_catalog_construction(self.connection,self.recovery)
        self.assertEqual(self.connection._transaction_status,b'I')
        self.assertEqual(self.connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_lost_registration_publication_retains_pre_effect_handle(self):
        reserve=self.recovery.reserve
        def lose(original):
            reserve(original)
            raise MemoryError('registration publication lost')
        with patch.object(self.recovery,'reserve',side_effect=lose):
            with self.assertRaises(MemoryError):
                prepare_provisional_catalog_construction(self.connection,self.recovery)
        reference,=self.recovery.references()
        observation=self.recovery.inspect(reference)
        self.assertEqual(observation.phase,'prepared')
        self.assertEqual(observation.calls,())
        self.assertIs(observation.original.connection,self.connection)
        self.assertEqual(self.connection._transaction_status,b'I')

    def test_failure_after_real_ddl_retains_primary_and_cleanup(self):
        connection=self.connection;failure=OSError('failure after ddl')
        class Port:
            @property
            def _transaction_status(self):return connection._transaction_status
            def run(self,sql):
                result=connection.run(sql)
                if sql.startswith('CREATE TABLE'):raise failure
                return result
        reference=prepare_provisional_catalog_construction(Port(),self.recovery)
        with self.assertRaises(CatalogConstructionFailure):
            execute_provisional_catalog_construction(self.recovery,reference)
        observation=self.recovery.inspect(reference)
        self.assertIs(observation.primary_failure,failure)
        self.assertIsNone(observation.cleanup_failure)
        self.assertTrue(observation.rollback_confirmed)
        self.assertEqual(sum(c.sql=='ROLLBACK' for c in observation.calls),1)
        self.assertEqual(self.connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_preflight_failure_retained_without_caller_rollback(self):
        reference=prepare_provisional_catalog_construction(self.connection,self.recovery)
        self.connection.run('BEGIN')
        try:
            with self.assertRaisesRegex(ValueError,'idle installer') as failure:
                execute_provisional_catalog_construction(self.recovery,reference)
            observation=self.recovery.inspect(reference)
            self.assertEqual(observation.phase,'preflight_terminated')
            self.assertIs(observation.primary_failure,failure.exception)
            self.assertFalse(observation.rollback_confirmed)
            self.assertEqual(observation.calls,())
            self.assertEqual(self.connection._transaction_status,b'T')
        finally:self.connection.run('ROLLBACK')

    def test_changed_baseline_preflight_retains_failure(self):
        reference=prepare_provisional_catalog_construction(self.connection,self.recovery)
        with patch('truss._catalog_installation.DEFINITIONS_SHA256','0'*64):
            with self.assertRaises(ValueError) as failure:
                execute_provisional_catalog_construction(self.recovery,reference)
        observation=self.recovery.inspect(reference)
        self.assertEqual(observation.phase,'preflight_terminated')
        self.assertIs(observation.primary_failure,failure.exception)
        self.assertEqual(observation.calls,())

    def test_capacity_gate_precedes_native_target_query(self):
        connection=self.connection;commands=[]
        class Port:
            @property
            def _transaction_status(self):return connection._transaction_status
            def run(self,sql):
                commands.append(sql)
                return connection.run(sql)
        registry=ProvisionalConstructionRecovery(retained_attempts=1)
        port=Port()
        prepare_provisional_catalog_construction(port,registry)
        before=len(commands)
        with self.assertRaises(ValueError):
            prepare_provisional_catalog_construction(port,registry)
        self.assertEqual(len(commands),before)

    def test_convenience_publication_failure_retains_recovery(self):
        with patch('truss._catalog_installation.ProvisionalCatalogConstruction',side_effect=MemoryError('lost result')):
            with self.assertRaises(MemoryError) as failure:
                construct_provisional_catalog_layout(self.connection)
        observation=failure.exception.recovery.inspect(failure.exception.recovery_reference)
        self.assertTrue(observation.rollback_confirmed)
        self.assertEqual(observation.phase,'terminated')

    def test_status_interrupt_stops_ddl_preserving_return_fact(self):
        connection=self.connection;interrupt=KeyboardInterrupt('status interrupted')
        class Port:
            last=''
            @property
            def _transaction_status(self):
                if self.last.startswith('CREATE TABLE'):raise interrupt
                return connection._transaction_status
            def run(self,sql):
                self.last=sql
                return connection.run(sql)
        reference=prepare_provisional_catalog_construction(Port(),self.recovery)
        with self.assertRaises(CatalogConstructionFailure):
            execute_provisional_catalog_construction(self.recovery,reference)
        observation=self.recovery.inspect(reference)
        ddl=[c for c in observation.calls if c.sql.startswith('CREATE TABLE')]
        self.assertEqual(len(ddl),1)
        self.assertTrue(ddl[0].returned)
        self.assertIs(ddl[0].observation_failure,interrupt)
        self.assertIs(observation.primary_failure,interrupt)
        self.assertTrue(observation.rollback_confirmed)

    def test_pre_begin_allocation_failures_retain_original_cause(self):
        for target in ('truss._construction_recovery._ConstructionPort',
                       'truss._catalog_installation._construction_attempt'):
            registry=ProvisionalConstructionRecovery()
            reference=prepare_provisional_catalog_construction(self.connection,registry)
            failure=MemoryError('preflight allocation failed')
            with patch(target,side_effect=failure):
                with self.assertRaises(MemoryError):
                    execute_provisional_catalog_construction(registry,reference)
            observation=registry.inspect(reference)
            self.assertEqual(observation.phase,'preflight_terminated')
            self.assertIs(observation.primary_failure,failure)
            self.assertEqual(observation.calls,())
            self.assertFalse(observation.rollback_confirmed)

    def test_duplicate_execution_cannot_settle_original_owner(self):
        reference=prepare_provisional_catalog_construction(self.connection,self.recovery)
        original_port=self.recovery.acquire(reference)
        before=self.recovery.inspect(reference)
        with self.assertRaisesRegex(ValueError,'twice'):
            execute_provisional_catalog_construction(self.recovery,reference)
        self.assertEqual(self.recovery.inspect(reference),before)
        self.assertEqual(before.phase,'executing')
        self.assertIsNone(before.primary_failure)
        self.assertEqual(original_port.run('SELECT 1'),[[1]])
        self.assertEqual(len(self.recovery.inspect(reference).calls),1)
