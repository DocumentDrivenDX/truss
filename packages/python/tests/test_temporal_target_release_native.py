# SPDX-License-Identifier: MIT OR Apache-2.0
"""TX-5 target authority, deadline, and cleanup gates for temporal reads."""
import time
from threading import Event
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from unittest.mock import patch

import test_temporal_engine_native as engine
from truss.access import TrussTarget


class TemporalTargetReleaseTests(engine.TemporalEngineNativeTests):
    # Keep this module focused while reusing the exact installed-candidate fixture.
    for _name in tuple(n for n in dir(engine.TemporalEngineNativeTests) if n.startswith("test_")):
        locals()[_name] = None

    def _entry_and_target(self):
        connection, host, assembly, tx = self.ready()
        self._store_rows(assembly, tx)
        request = self._capture_request(
            assembly,
            tx,
            'SELECT a."A-on" AS occurred_at FROM "A" a WHERE a."A-on" = :boundary',
        )
        entry = self._entry(
            request,
            kind="date",
            temporal_parameters={"boundary": {"kind": "date", "value": "2024-02-29"}},
            page_size=None,
        )
        host.detach()
        connection.commit()

        opened = []

        @contextmanager
        def operation(timeout):
            connection, host, assembly, tx = self.consumer()
            connection.execute(
                "SELECT pg_catalog.set_config('statement_timeout', %s, true)",
                (str(max(1, int(timeout.total_seconds() * 1000))),),
            )
            opened.append((connection.info.backend_pid, connection))
            try:
                yield assembly, tx
            except BaseException:
                host.detach()
                connection.rollback()
                raise
            else:
                host.detach()
                connection.commit()

        target = TrussTarget(
            operation,
            binding_sha256=entry.artifact()["request"]["target"]["bindingSha256"],
            platform=(("postgresql", "18.6"),),
            default_timeout=timedelta(seconds=20),
            catalog_entries=(entry,),
        )
        return entry, target, opened

    def test_local_timestamp_boundary_reaches_the_installed_native_filter(self):
        connection, host, assembly, tx = self.ready()
        self._store_rows(assembly, tx)
        request = self._capture_request(
            assembly,
            tx,
            'SELECT a."A-local" AS occurred_at FROM "A" a WHERE a."A-local" = :boundary',
        )
        entry = self._entry(
            request,
            kind="local",
            temporal_parameters={"boundary": {"kind": "local", "value": "2024-11-03T01:30:00.000000"}},
        )
        host.detach()
        connection.commit()
        target = self._target(entry)
        parameters = entry.parameters.model_validate(
            {"boundary": datetime(2024, 11, 3, 1, 30)}, strict=True
        )
        rows = target.read_native_temporal(entry, parameters)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row.occurred_at == datetime(2024, 11, 3, 1, 30) for row in rows))

    def _wait_until(self, event, message):
        deadline = time.monotonic() + 10
        while not event.is_set():
            if time.monotonic() > deadline:
                self.fail(message)
            time.sleep(0.01)

    def test_revoked_current_authority_withholds_native_temporal_result_and_cleans_up(self):
        entry, target, opened = self._entry_and_target()
        rows_consumed, continue_query = Event(), Event()
        decoded_results = []
        import truss._query_runtime as query_runtime
        original_decode = query_runtime._decode_rows

        def final_authorization_barrier(*args, **kwargs):
            result = original_decode(*args, **kwargs)
            decoded_results.append(result)
            rows_consumed.set()
            if not continue_query.wait(10):
                raise TimeoutError("final authorization barrier timed out")
            return result

        try:
            with patch("truss._query_runtime._decode_rows", final_authorization_barrier):
                with ThreadPoolExecutor(max_workers=1) as pool:
                    try:
                        future = pool.submit(
                            target.read_native_temporal,
                            entry,
                            entry.parameters.model_validate({"boundary": date(2024, 2, 29)}, strict=True),
                        )
                        self._wait_until(rows_consumed, "Temporal result rows were not decoded")
                        self.assertTrue(opened)
                        # The wrapper calls the original decoder once with the
                        # complete unchanged rows, then pauses before post-query
                        # READ COMMITTED authorization and typed result handoff.
                        self.admin.execute("REVOKE group_writer FROM consumer")
                        continue_query.set()
                        with self.assertRaises(Exception) as raised:
                            future.result(timeout=15)
                        refusal = getattr(raised.exception.original, "value", raised.exception.original)
                        self.assertEqual(getattr(refusal, "code", None), "unauthorized",
                                         repr(raised.exception.original))
                        self.assertEqual(len(decoded_results), 1)
                        self.assertEqual(type(decoded_results[0]).__name__, "QueryRows")
                    finally:
                        continue_query.set()
            self.assertEqual(self.admin.execute("SELECT 42").fetchone(), (42,))
            self.assertEqual(int(opened[0][1].info.transaction_status), 0,
                             "Refused result must leave the owned transaction settled")
        finally:
            self.admin.execute("GRANT group_writer TO consumer WITH SET FALSE")

    def test_expired_native_temporal_deadline_cancels_and_rolls_back_owned_transaction(self):
        entry, target, opened = self._entry_and_target()
        self.admin.execute("BEGIN")
        self.admin.execute("LOCK TABLE truss.object IN ACCESS EXCLUSIVE MODE")
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                try:
                    future = pool.submit(
                        target.read_native_temporal,
                        entry,
                        entry.parameters.model_validate({"boundary": date(2024, 2, 29)}, strict=True),
                        timeout=timedelta(milliseconds=150),
                    )
                    EventWaiter(self.admin, opened, future)
                    with self.assertRaises(Exception) as raised:
                        future.result(timeout=10)
                    original = raised.exception.original
                    execution_error = getattr(original, "error", None)
                    self.assertIn(getattr(execution_error, "code", None),
                                  ("cancelled", "execution_obligation"), repr(original))
                finally:
                    self.admin.rollback()
            self.assertEqual(self.admin.execute("SELECT 42").fetchone(), (42,))
            self.assertEqual(int(opened[0][1].info.transaction_status), 0,
                             "Deadline cancellation must leave the owned transaction settled")
        finally:
            if self.admin.info.transaction_status:
                self.admin.rollback()


def EventWaiter(admin, opened, future):
    """Wait until the native statement is blocked by the test-owned table lock."""
    from threading import Event

    event = Event()
    deadline = time.monotonic() + 10
    deadline = time.monotonic() + 10
    while not opened:
        if future.done():
            raise AssertionError("Temporal target stopped before data-source dispatch")
        if time.monotonic() > deadline:
            raise AssertionError("Temporal target did not open its owned transaction")
        time.sleep(0.01)
    while True:
        if future.done():
            raise AssertionError("Temporal query completed before the expected relation-lock wait")
        admin.execute("SELECT pg_catalog.pg_stat_clear_snapshot()")
        blocked = admin.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=%s AND wait_event_type='Lock')",
            (opened[0][0],),
        ).fetchone()[0]
        if blocked:
            event.set()
            return event
        if time.monotonic() > deadline:
            raise AssertionError("Temporal source did not reach the locked data table")
        time.sleep(0.01)
    raise AssertionError("Temporal target did not open its owned transaction")
