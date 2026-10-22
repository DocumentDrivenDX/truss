# SPDX-License-Identifier: MIT OR Apache-2.0
"""CLI keeps install refusals structured and success identity intact."""
import unittest

from truss import InstallRefused, Ok
from truss.cli import _InstallRefusalError, _required


class CliInstallRefusalTests(unittest.TestCase):
    def test_named_managed_grant_refusal_keeps_only_safe_fields(self):
        refusal = InstallRefused(code='third_party_grant', role_name='platform_reader',
                                 object_class='column', phase='post_installation')
        with self.assertRaises(_InstallRefusalError) as caught:
            _required(Ok(refusal), install_result=True)
        self.assertEqual(caught.exception.payload(), {
            'outcome': 'refused', 'code': 'third_party_grant',
            'role_name': 'platform_reader', 'object_class': 'column',
            'phase': 'post_installation',
        })

    def test_invalid_role_refusal_preserves_its_code_without_grant_context(self):
        with self.assertRaises(_InstallRefusalError) as caught:
            _required(Ok(InstallRefused(code='invalid_roles')), install_result=True)
        self.assertEqual(caught.exception.payload(), {
            'outcome': 'refused', 'code': 'invalid_roles',
        })

    def test_success_returns_original_pending_identity_carrier(self):
        pending = object()
        self.assertIs(_required(Ok(pending), install_result=True), pending)


if __name__ == '__main__':
    unittest.main()
