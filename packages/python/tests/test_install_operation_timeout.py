# SPDX-License-Identifier: MIT OR Apache-2.0
"""Focused public controls for the bounded install-only operation timeout."""

import unittest
from threading import RLock
from types import SimpleNamespace
from unittest.mock import Mock

from truss.catalog_runtime import (
    CatalogReferenceAssembly,
    PendingCatalogInstallation,
)
from truss.execution import Error, ExecutionFailure, Ok, TransactionHandle
from truss.psycopg_host import PsycopgHost


class InstallOperationTimeoutTests(unittest.TestCase):
    def assembly(self):
        host = object.__new__(PsycopgHost)
        host._deadline_ms = 60000
        host._run_operation_with_attempt = Mock(return_value=(
            Ok(PendingCatalogInstallation("install-id", "owner", "registrar", "release")),
            None,
        ))
        assembly = object.__new__(CatalogReferenceAssembly)
        assembly._host = host
        assembly._disposed = False
        assembly._lock = RLock()
        return assembly, host

    def test_default_install_uses_existing_host_deadline(self):
        assembly, host = self.assembly()

        result = assembly.install_in_transaction(object())

        self.assertIsInstance(result, Ok)
        self.assertIsNone(host._run_operation_with_attempt.call_args.kwargs["operation_timeout_ms"])
        self.assertEqual(host._deadline_ms, 60000)

    def test_explicit_install_override_is_bounded_and_does_not_change_host_default(self):
        assembly, host = self.assembly()

        result = assembly.install_in_transaction(object(), operation_timeout_ms=180000)

        self.assertIsInstance(result, Ok)
        self.assertEqual(host._run_operation_with_attempt.call_args.kwargs["operation_timeout_ms"], 180000)
        self.assertEqual(host._deadline_ms, 60000)

    def test_invalid_override_refuses_before_host_operation(self):
        for value in (True, 0, -1, 180001, 1.0, "180000"):
            with self.subTest(value=value):
                assembly, host = self.assembly()

                result = assembly.install_in_transaction(object(), operation_timeout_ms=value)

                self.assertIsInstance(result, Error)
                self.assertEqual(result.error, ExecutionFailure(
                    "execution_obligation", "Install operation timeout must be 1..180000 milliseconds"))
                host._run_operation_with_attempt.assert_not_called()

    def test_private_host_path_passes_one_per_operation_override(self):
        host = object.__new__(PsycopgHost)
        issuer = object()
        transaction = TransactionHandle(issuer, "transaction-key", "read_committed", "read_write")
        custody = SimpleNamespace(
            handle=transaction,
            identity=("pid", "xid", "read_committed", "read_write"),
        )
        host._issuer = issuer
        host._transactions = {transaction._key: custody}
        host._attempt = Mock(return_value="completed")

        result, attempt = PsycopgHost._run_operation_with_attempt(
            host, transaction, lambda *_: None, operation_timeout_ms=180000)

        self.assertEqual(result, "completed")
        self.assertIsNone(attempt)
        self.assertIs(host._attempt.call_args.args[1], custody)
        self.assertEqual(host._attempt.call_args.kwargs["operation_timeout_ms"], 180000)
        self.assertTrue(callable(host._attempt.call_args.kwargs["attempt_capture"]))


if __name__ == "__main__":
    unittest.main()
