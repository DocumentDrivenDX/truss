# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual provisional metadata effects, never committed installation."""
import json
import unittest
from unittest.mock import patch
from test_native_pg8000 import NativeBoundaryFixture
from truss._catalog_installation import construct_provisional_catalog_layout,CatalogConstructionFailure
from truss._catalog_installation import prepare_provisional_catalog_construction,execute_provisional_catalog_construction
from truss._construction_recovery import ProvisionalConstructionRecovery

class MetadataNativeTests(NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        self.connection=self.Connection(**self.kwargs)
        self.connection.run('SELECT 1')
    def tearDown(self):self.connection.close()
    def test_original_marker_archive_epoch_round_trip_and_rollback(self):
        value=construct_provisional_catalog_layout(self.connection,metadata=True)
        report=json.loads(value.metadata_observation)
        self.assertFalse(report['installationReady'])
        self.assertTrue(value.rollback_confirmed)
        self.assertEqual(report['marker']['installationId'],report['capture']['installationId'])
        self.assertEqual(self.connection.run("SELECT to_regnamespace('truss')::text"),[[None]])
        retained=value.recovery.inspect(value.recovery_reference)
        self.assertTrue(retained.original.metadata_recipe)
        self.assertTrue(retained.original.metadata_input)
        self.assertEqual(retained.original.ordinary_call_limit,160)

    def test_archive_substitution_refuses_and_rolls_back(self):
        connection=self.connection
        class Port:
            @property
            def _transaction_status(self):return connection._transaction_status
            def run(self,sql):
                if sql.startswith('SET CONSTRAINTS ALL IMMEDIATE'):
                    connection.run("UPDATE truss.installation_archive SET artifact_bytes=decode('61','hex') WHERE artifact_role='input'")
                return connection.run(sql)
        with self.assertRaises(CatalogConstructionFailure) as caught:
            construct_provisional_catalog_layout(Port(),metadata=True)
        self.assertTrue(caught.exception.rollback_confirmed)
        self.assertIn('metadata_archive_readback',caught.exception.original_attempt)
        self.assertEqual(connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_missing_duplicate_marker_clock_and_epoch_faults_refuse(self):
        faults=(
            "DELETE FROM truss.installation_archive WHERE artifact_role='input'",
            "INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) SELECT installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256 FROM truss.installation_archive WHERE artifact_role='input'",
            "UPDATE truss.installation_marker SET layout_version='changed'",
            "UPDATE truss.installation_marker SET installed_at=installed_at+interval '1 microsecond'",
            "DELETE FROM truss.source_epoch_current; DELETE FROM truss.source_epoch_registry",
        )
        connection=self.connection
        for fault in faults:
            class Port:
                @property
                def _transaction_status(self):return connection._transaction_status
                def run(self,sql):
                    if sql=='SET CONSTRAINTS ALL IMMEDIATE':connection.run(fault)
                    return connection.run(sql)
            with self.subTest(fault=fault),self.assertRaises(CatalogConstructionFailure) as caught:
                construct_provisional_catalog_layout(Port(),metadata=True)
            self.assertTrue(caught.exception.rollback_confirmed)
            self.assertEqual(connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_lost_original_epoch_reply_is_retained_without_replay(self):
        connection=self.connection;calls=[]
        class Port:
            @property
            def _transaction_status(self):return connection._transaction_status
            def run(self,sql):
                result=connection.run(sql)
                if sql.startswith('SELECT truss.runtime_issue_source_epoch('):
                    calls.append(sql);raise OSError('epoch reply lost')
                return result
        with self.assertRaises(CatalogConstructionFailure) as caught:
            construct_provisional_catalog_layout(Port(),metadata=True)
        self.assertEqual(len(calls),1)
        self.assertTrue(caught.exception.rollback_confirmed)
        self.assertIn('metadata_capture',caught.exception.original_attempt)
        self.assertEqual(connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_lost_rollback_ack_keeps_original_attempt_unresolved(self):
        connection=self.connection;rollbacks=[]
        class Port:
            @property
            def _transaction_status(self):return connection._transaction_status
            def run(self,sql):
                result=connection.run(sql)
                if sql=='ROLLBACK':
                    rollbacks.append(sql);raise OSError('rollback acknowledgment lost')
                return result
        with self.assertRaises(CatalogConstructionFailure) as caught:
            construct_provisional_catalog_layout(Port(),metadata=True)
        failure=caught.exception
        self.assertFalse(failure.rollback_confirmed)
        self.assertEqual(rollbacks,['ROLLBACK'])
        retained=failure.recovery.inspect(failure.recovery_reference)
        self.assertEqual(retained.phase,'unresolved')
        self.assertTrue(retained.original.metadata_recipe)
        self.assertIn('metadata_epoch_readback',failure.original_attempt)
        self.assertEqual(connection.run("SELECT to_regnamespace('truss')::text"),[[None]])

    def test_lost_final_publication_keeps_native_originals(self):
        with patch('truss._catalog_installation.ProvisionalCatalogConstruction',side_effect=OSError('result publication lost')):
            with self.assertRaises(OSError) as caught:
                construct_provisional_catalog_layout(self.connection,metadata=True)
        failure=caught.exception
        observation=failure.recovery.inspect(failure.recovery_reference)
        self.assertTrue(observation.rollback_confirmed)
        captured=[call.original_result[0][0] for call in observation.calls
            if call.original_result and call.sql.startswith('WITH native_original AS MATERIALIZED')]
        self.assertEqual(len(captured),1)
        self.assertTrue(json.loads(captured[0])['clockParity'])
        epochs=[call.original_result for call in observation.calls
            if call.sql.startswith('SELECT truss.runtime_issue_source_epoch(')]
        self.assertEqual(len(epochs),1)
        self.assertTrue(epochs[0][0][0])

    def test_changed_recipe_refuses_before_begin(self):
        recovery=ProvisionalConstructionRecovery()
        reference=prepare_provisional_catalog_construction(self.connection,recovery,metadata=True)
        with patch('truss._installation_metadata.PROFILE_SHA256','0'*64):
            with self.assertRaises(ValueError):execute_provisional_catalog_construction(recovery,reference)
        observation=recovery.inspect(reference)
        self.assertEqual(observation.calls,())
        self.assertEqual(observation.phase,'preflight_terminated')
        self.assertEqual(self.connection._transaction_status,b'I')
