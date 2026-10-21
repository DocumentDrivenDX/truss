# SPDX-License-Identifier: MIT OR Apache-2.0
"""Lifecycle status and administrator recovery on a real native installation."""
import psycopg

from truss import (AdminInstallRecovery, LifecycleRefused, Ok, PersonRuntimeStatus,
                   CatalogRuntimeConfiguration, adopt_psycopg_host, create_reference_assembly)
import test_group_create_native as group_tests


class LifecycleNativeTests(group_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(group_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_person_status_reports_absent_installation_without_role_details(self):
        status=self.assembly.person_runtime_status_in_transaction(self.tx)
        self.assertEqual(status,Ok(PersonRuntimeStatus(installation='absent',catalog='unknown')))

    def test_minimal_status_admin_recovery_revocation_and_install_busy(self):
        connection, host, assembly, tx = self.ready()

        self.admin.execute('BEGIN')
        self.admin.execute('SELECT pg_catalog.pg_advisory_xact_lock(1953658227,1735549296)')
        busy = assembly.person_runtime_status_in_transaction(tx)
        self.assertEqual(busy, Ok(LifecycleRefused(reason='observation')))
        self.admin.rollback()

        status = assembly.person_runtime_status_in_transaction(tx)
        self.assertIsInstance(status, Ok, repr(status))
        self.assertEqual(status.value, PersonRuntimeStatus(installation='compatible', catalog='accepted'))

        self.admin.execute('BEGIN')
        admin_host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
        admin_tx=admin_host.adopt_transaction().value
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        recovery = admin_assembly.admin_install_recovery_in_transaction(admin_tx)
        self.assertIsInstance(recovery, Ok, repr(recovery))
        self.assertIsInstance(recovery.value, AdminInstallRecovery)
        self.assertEqual(recovery.value.owner_role, self.installation.owner_role)
        self.assertEqual(recovery.value.registrar_role, self.installation.registrar_role)
        admin_host.detach()
        self.admin.rollback()

        # A role name is never included in the ordinary person's refusal.
        self.admin.execute(psycopg.sql.SQL('REVOKE group_writer FROM consumer'))
        denied = assembly.person_runtime_status_in_transaction(tx)
        self.assertEqual(denied, Ok(LifecycleRefused(reason='unauthorized')))

        host.detach()
        connection.rollback()

    def test_ordinary_person_cannot_recover_installation_role_names(self):
        connection, host, assembly, tx = self.ready()
        denied = assembly.admin_install_recovery_in_transaction(tx)
        self.assertEqual(denied, Ok(LifecycleRefused(reason='unauthorized')))
        host.detach()
        connection.rollback()


if __name__ == '__main__':
    import unittest
    unittest.main()
