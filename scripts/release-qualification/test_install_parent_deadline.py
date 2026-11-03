#!/usr/bin/env python3
"""Pure .55 install-timeout regression; no connection or SQL is used."""
import hashlib
import importlib.metadata
import json
import os
import pathlib
import unittest
from threading import RLock, get_ident
from types import SimpleNamespace
from unittest.mock import patch
from weakref import ref

from psycopg import pq
import truss.psycopg_host as psycopg_host
from truss.psycopg_host import PsycopgHost


class DeadlineCaptured(Exception):
    pass


class Connection:
    pass


class InstallParentDeadlineTests(unittest.TestCase):
    def test_install_override_is_clamped_before_sql_to_active_parent(self):
        host = object.__new__(PsycopgHost)
        connection = Connection()
        custody = psycopg_host._ConnectionCustody(RLock())
        custody.attached = ref(host)
        host._connection = connection
        host._custody = custody
        host._closed = False
        host._transactions = {}
        host._deadline_ms = 60000
        host._status = lambda: pq.TransactionStatus.INTRANS
        reservation = object.__new__(psycopg_host._HostOperationReservation)
        reservation.hosts = (host,)
        reservation.active = True
        reservation.thread = get_ident()
        reservation.deadline = SimpleNamespace(end=105.0, check=lambda: None)
        custody.reservation = reservation
        observed = []

        def capture_deadline(_connection, milliseconds):
            observed.append(milliseconds)
            raise DeadlineCaptured()

        with psycopg_host._registry_lock:
            psycopg_host._registry[connection] = custody
        try:
            with patch.object(psycopg_host, "monotonic", return_value=100.0), \
                    patch.object(psycopg_host, "_Deadline", side_effect=capture_deadline):
                host._attempt(lambda *_: self.fail("callback must not run"),
                              operation_timeout_ms=180000)
        finally:
            with psycopg_host._registry_lock:
                psycopg_host._registry.pop(connection, None)
        self.assertEqual(observed, [5000])


def verify_installed_candidate():
    expected_root = pathlib.Path(os.environ["TRUSS_QUALIFIED_SITE_PACKAGES"]).resolve()
    expected_wheel_sha = os.environ["TRUSS_QUALIFIED_WHEEL_SHA256"]
    imported = pathlib.Path(psycopg_host.__file__).resolve()
    if not imported.is_relative_to(expected_root):
        raise SystemExit(f"Truss imported outside selected venv: {imported}")
    distribution = importlib.metadata.distribution("umf-truss")
    if distribution.version != "0.0.55":
        raise SystemExit(f"Unexpected installed Truss version: {distribution.version}")
    direct_url = json.loads(distribution.read_text("direct_url.json") or "{}")
    actual = direct_url.get("archive_info", {}).get("hashes", {}).get("sha256")
    if actual != expected_wheel_sha:
        raise SystemExit(f"Installed wheel digest mismatch: {actual}")


if __name__ == "__main__":
    verify_installed_candidate()
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(InstallParentDeadlineTests))
    raise SystemExit(0 if result.wasSuccessful() else 1)
