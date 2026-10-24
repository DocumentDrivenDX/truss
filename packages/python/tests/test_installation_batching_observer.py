# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure controls for bounded installer execution-failure observation."""

from __future__ import annotations

import json
import os
import re
import sys
import unittest
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter_ns
from types import TracebackType
from typing import Any, ClassVar, Self

_MAX_EVENTS = 16_384
_MAX_FRAME_DEPTH = 32
_SQLSTATE = re.compile(r"^[0-9A-Z]{5}$")
_ORIGIN_FILES = frozenset(
    {
        "_installation_privileges.py",
        "_installation_sql_batch.py",
        "test_installation_batching_native.py",
    }
)
_WRAPPER_FUNCTIONS = frozenset({"_rows", "_rows_from_cursor", "submit", "execute"})


def _callsite() -> dict[str, Any]:
    frame = sys._getframe(2)
    for _ in range(_MAX_FRAME_DEPTH):
        if frame is None:
            break
        source = frame.f_code.co_filename.rsplit("/", 1)[-1]
        function = frame.f_code.co_name
        if source in _ORIGIN_FILES and function not in _WRAPPER_FUNCTIONS:
            if source == "_installation_sql_batch.py":
                subphase = "ddl_batch"
            elif source == "test_installation_batching_native.py":
                subphase = (
                    "unbatched_reference"
                    if function == "_unbatched_reference"
                    else "native_test_call"
                )
            elif function == "_verify_final_acl_rows":
                subphase = "final_verification"
            elif function == "_verify":
                subphase = "privilege_verification"
            elif function in {
                "finalize_installation_grants",
                "protect_installation_with_cursor",
            }:
                subphase = "grant_protection"
            elif function in {
                "installation_grant_policy_with_cursor",
                "require_empty_managed_grants_with_cursor",
            }:
                subphase = "policy_read"
            else:
                subphase = "installation_privileges"
            return {
                "source": source,
                "function": function,
                "line": frame.f_lineno,
                "subphase": subphase,
            }
        frame = frame.f_back
    return {
        "source": "unresolved",
        "function": "unresolved",
        "line": 0,
        "subphase": "unresolved",
    }


class PublicExecuteObserver:
    """Observe public cursor calls on exactly one connection without query data."""

    def __init__(
        self, cursor_type: type, connection: object, *, limit: int = _MAX_EVENTS
    ):
        if type(limit) is not int or limit < 1 or limit > _MAX_EVENTS:
            raise ValueError("Invalid execution-observation limit")
        self.cursor_type = cursor_type
        self.connection = connection
        self.limit = limit
        self.phase_name = "unclassified"
        self.ordinal = 0
        self._phase_ordinals: dict[str, int] = {}
        self.events: list[dict[str, Any]] = []
        self.dropped_events = 0
        self._original_execute: Any = None
        self._wrapper: Any = None

    def __enter__(self) -> Self:
        original = self.cursor_type.execute
        self._original_execute = original
        observer = self

        def observed(cursor: Any, *args: Any, **kwargs: Any) -> Any:
            if cursor.connection is not observer.connection:
                return original(cursor, *args, **kwargs)

            observer.ordinal += 1
            phase_ordinal = observer._phase_ordinals.get(observer.phase_name, 0) + 1
            observer._phase_ordinals[observer.phase_name] = phase_ordinal
            event: dict[str, Any] = {
                "phase": observer.phase_name,
                "ordinal": observer.ordinal,
                "phaseOrdinal": phase_ordinal,
            }
            event.update(_callsite())
            started = perf_counter_ns()
            try:
                return original(cursor, *args, **kwargs)
            except BaseException as error:
                event["exceptionType"] = type(error).__name__
                sqlstate = getattr(error, "sqlstate", None)
                if type(sqlstate) is str and _SQLSTATE.fullmatch(sqlstate):
                    event["sqlState"] = sqlstate
                raise
            finally:
                event["elapsedNs"] = max(0, perf_counter_ns() - started)
                if len(observer.events) < observer.limit:
                    observer.events.append(event)
                else:
                    observer.dropped_events += 1

        self._wrapper = observed
        self.cursor_type.execute = observed
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        # Restore the exact descriptor captured on entry, including on cancellation.
        self.cursor_type.execute = self._original_execute

    @contextmanager
    def phase(self, name: str) -> Iterator[None]:
        if type(name) is not str or not name or len(name) > 32:
            raise ValueError("Invalid observation phase")
        previous = self.phase_name
        self.phase_name = name
        try:
            yield
        finally:
            self.phase_name = previous

    def snapshot(self) -> dict[str, Any]:
        return {
            "events": [dict(event) for event in self.events],
            "eventLimit": self.limit,
            "droppedEvents": self.dropped_events,
            "totalObservedCalls": self.ordinal,
        }


def _write_exclusive(path: Path, value: dict[str, Any]) -> None:
    """Write a safe JSON receipt once, without replacing earlier evidence."""
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        payload = (
            json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def observe_baseline(
    observer: PublicExecuteObserver,
    operation: Callable[[], Any],
    *,
    evidence_path: Path | None,
    source_hashes: dict[str, str],
    statement_timeout_ms: int,
    operation_timeout_ms: int,
    succeeded: Callable[[Any], bool],
) -> Any:
    """Run baseline and persist failed evidence before caller assertions execute."""
    result: Any = None
    primary: BaseException | None = None
    try:
        with observer.phase("baseline"):
            result = operation()
        return result
    except BaseException as error:
        primary = error
        raise
    finally:
        if evidence_path is not None and (primary is not None or not succeeded(result)):
            report = {
                "schemaVersion": 1,
                "status": "failed",
                "phase": "baseline",
                "candidate": "not_run",
                "failureType": type(primary).__name__
                if primary is not None
                else "BaselineRefused",
                "timeoutsMs": {
                    "statement": statement_timeout_ms,
                    "operation": operation_timeout_ms,
                },
                "sourceHashes": dict(source_hashes),
                "observation": observer.snapshot(),
            }
            try:
                _write_exclusive(evidence_path, report)
            except BaseException as write_error:
                if primary is None:
                    raise
                primary.add_note(
                    "Writing failed-baseline evidence also failed: "
                    + type(write_error).__name__
                )


class _FakeCursor:
    execute_calls: ClassVar[
        list[tuple[object, tuple[object, ...], dict[str, object]]]
    ] = []
    failure: BaseException | None = None

    def __init__(self, connection: object):
        self.connection = connection

    def execute(self, query: object, *args: object, **kwargs: object) -> str:
        self.execute_calls.append((query, args, kwargs))
        if self.failure is not None:
            raise self.failure
        return "executed"


class _QueryThatMustNotBeRendered:
    def __str__(self) -> str:
        raise AssertionError("query was stringified")

    def __repr__(self) -> str:
        raise AssertionError("query was represented")


class _SqlStateFailure(RuntimeError):
    sqlstate = "57014"


class InstallationBatchingObserverTests(unittest.TestCase):
    def setUp(self) -> None:
        _FakeCursor.execute_calls = []
        _FakeCursor.failure = None

    def test_non_ddl_driver_failure_is_recorded_without_query_data(self) -> None:
        connection = object()
        failure = _SqlStateFailure("private driver message")
        _FakeCursor.failure = failure
        observer = PublicExecuteObserver(_FakeCursor, connection)
        with (
            observer,
            observer.phase("baseline"),
            self.assertRaises(RuntimeError) as raised,
        ):
            _FakeCursor(connection).execute("SELECT confidential")
        self.assertIs(raised.exception, failure)
        self.assertEqual(observer.ordinal, 1)
        event = observer.events[0]
        self.assertEqual(event["phase"], "baseline")
        self.assertEqual(event["exceptionType"], "_SqlStateFailure")
        self.assertEqual(event["sqlState"], "57014")
        self.assertNotIn("private driver message", json.dumps(observer.snapshot()))
        self.assertNotIn("confidential", json.dumps(observer.snapshot()))

    def test_original_exception_identity_and_query_are_never_rendered(self) -> None:
        connection = object()
        failure = RuntimeError("opaque failure")
        _FakeCursor.failure = failure
        observer = PublicExecuteObserver(_FakeCursor, connection)
        query = _QueryThatMustNotBeRendered()
        with observer, self.assertRaises(RuntimeError) as raised:
            _FakeCursor(connection).execute(query)
        self.assertIs(raised.exception, failure)
        self.assertIs(_FakeCursor.execute_calls[0][0], query)
        self.assertNotIn("sql", observer.events[0])
        self.assertNotIn("query", observer.events[0])

    def test_failed_baseline_evidence_exists_before_result_assertion(self) -> None:
        connection = object()
        observer = PublicExecuteObserver(_FakeCursor, connection)
        with (
            observer,
            self.subTest("evidence is emitted before assertion"),
            TemporaryDirectory() as directory,
        ):
            path = Path(directory) / "failure.json"
            outcome = observe_baseline(
                observer,
                lambda: {"status": "failed"},
                evidence_path=path,
                source_hashes={"module": "a" * 64},
                statement_timeout_ms=1000,
                operation_timeout_ms=5000,
                succeeded=lambda value: value.get("status") == "success",
            )
            with self.assertRaises(AssertionError):
                self.assertEqual(outcome["status"], "success")
            receipt = json.loads(path.read_text())
            self.assertEqual(receipt["candidate"], "not_run")
            self.assertEqual(
                receipt["timeoutsMs"], {"statement": 1000, "operation": 5000}
            )

    def test_unowned_cursor_passes_through_and_hook_is_restored_exactly(self) -> None:
        owner = object()
        other = object()
        original = _FakeCursor.execute
        observer = PublicExecuteObserver(_FakeCursor, owner)
        with observer:
            self.assertEqual(_FakeCursor(other).execute("SELECT 1"), "executed")
            self.assertEqual(observer.events, [])
        self.assertIs(_FakeCursor.execute, original)
        self.assertEqual(len(_FakeCursor.execute_calls), 1)

    def test_callsite_skips_proxy_frames_and_selects_installer_source(self) -> None:
        connection = object()
        observer = PublicExecuteObserver(_FakeCursor, connection)

        def proxy(cursor: _FakeCursor) -> str:
            return cursor.execute("opaque")

        def installer_site(cursor: _FakeCursor) -> str:
            return proxy(cursor)

        installer_site.__code__ = installer_site.__code__.replace(
            co_filename="/approved/truss/_installation_privileges.py"
        )
        with observer:
            installer_site(_FakeCursor(connection))
        event = observer.events[0]
        self.assertEqual(event["source"], "_installation_privileges.py")
        self.assertEqual(event["function"], "installer_site")
        self.assertEqual(event["subphase"], "installation_privileges")


if __name__ == "__main__":
    unittest.main()
