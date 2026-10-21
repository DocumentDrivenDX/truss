# SPDX-License-Identifier: MIT OR Apache-2.0
"""Runtime status carriers keep person disclosure minimal."""
import unittest

from truss import InstallRefused
from truss.lifecycle import (AdminInstallRecovery, LifecycleRefused,
                             PersonRuntimeStatus)


class LifecycleCarrierTests(unittest.TestCase):
    def test_person_status_does_not_expose_install_or_role_identity(self):
        status = PersonRuntimeStatus(installation='compatible', catalog='empty')
        self.assertEqual(status.outcome, 'status')
        self.assertFalse(hasattr(status, 'installation_id'))
        self.assertFalse(hasattr(status, 'owner_role'))
        self.assertFalse(hasattr(status, 'registrar_role'))

    def test_admin_recovery_is_a_separate_explicit_carrier(self):
        recovery = AdminInstallRecovery(owner_role='truss_owner', registrar_role='truss_registrar')
        self.assertEqual((recovery.owner_role, recovery.registrar_role),
                         ('truss_owner', 'truss_registrar'))
        self.assertEqual(LifecycleRefused(reason='unauthorized').outcome, 'refused')

    def test_install_refusals_are_closed_preflight_codes(self):
        codes = ('busy', 'invalid_roles', 'unsupported_postgres', 'already_installed',
                 'incompatible', 'unauthorized', 'role_exists', 'read_only')
        refusals = tuple(InstallRefused(code=code) for code in codes)
        self.assertEqual(tuple(item.code for item in refusals), codes)
        self.assertTrue(all(item.outcome == 'refused' for item in refusals))
        with self.assertRaises(ValueError):
            InstallRefused(code='retry')


if __name__ == '__main__':
    unittest.main()
