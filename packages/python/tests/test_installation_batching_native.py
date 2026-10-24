# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native regression and paired client-submission measurement for install DDL."""

import hashlib
import json
import os
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import truss._installation_privileges as privileges
from psycopg import pq, sql
from test_psycopg_host_native import PsycopgHostNativeTests
from truss import Error, Ok, PsycopgProfile, psycopg_host
from truss._installation_privileges import (
    InstallationRoles,
    protect_installation_in_transaction,
)
from truss._installation_sql_batch import execute_ordered_ddl

ROOT = Path(__file__).resolve().parents[3]
_SEPARATOR = "\n;\n"


class _CountingCursor:
    def __init__(self, cursor, record):
        self._cursor = cursor
        self._record = record

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def execute(self, query, *args, **kwargs):
        rendered = query if isinstance(query, str) else query.as_string(self.connection)
        self._record["submissions"].append(
            {
                "utf8Bytes": len(rendered.encode("utf-8")),
                "sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
            }
        )
        if args or kwargs != {"prepare": False, "binary": False}:
            raise AssertionError(
                "Installer DDL must use prepare=False, binary=False, without parameters"
            )
        return self._cursor.execute(query, *args, **kwargs)


class InstallationBatchingNativeTests(unittest.TestCase):
    """Run only under the existing owned PostgreSQL 18.6 fixture runner."""

    run_pg = classmethod(PsycopgHostNativeTests.run_pg.__func__)
    setUpClass = classmethod(PsycopgHostNativeTests.setUpClass.__func__)
    tearDownClass = classmethod(PsycopgHostNativeTests.tearDownClass.__func__)
    tearDown = PsycopgHostNativeTests.tearDown
    selected_profile = PsycopgProfile(server=180006)

    def setUp(self):
        PsycopgHostNativeTests.setUp(self)
        self.tx = PsycopgHostNativeTests.begin(self)
        self.suffix = uuid4().hex[:10]
        self.owner = f"batch_owner_{self.suffix}"
        self.client = f"batch_client_{self.suffix}"
        self._last_measurement = {"submissions": []}
        self.connection.execute(
            (
                ROOT
                / "docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql"
            ).read_text(),
            prepare=False,
        )
        self.connection.execute(
            "CREATE TYPE truss.choice AS ENUM ('a','b'); "
            "CREATE DOMAIN truss.positive AS integer CHECK (VALUE > 0); "
            "CREATE FUNCTION truss.private_probe() RETURNS integer LANGUAGE sql AS 'SELECT 1'; "
            "CREATE FUNCTION truss.private_probe(value integer) RETURNS integer LANGUAGE sql AS 'SELECT value'; "
            "CREATE TEMP TABLE caller_sentinel(value text); "
            "INSERT INTO caller_sentinel VALUES ('before-install')",
            prepare=False,
        )

    def _roles(self, *, tolerated=()):
        return InstallationRoles(self.owner, self.client, tuple(tolerated))

    def _run_install(self, *, roles=None, after_ddl=None):
        self._last_measurement = {"submissions": []}
        self._last_after_ddl_ran = False

        def observed(cursor, units):
            source_units = tuple(units)
            result = execute_ordered_ddl(
                _CountingCursor(cursor, self._last_measurement), source_units
            )
            if after_ddl is not None:
                self._last_after_ddl_ran = True
                after_ddl(cursor)
            return result

        with patch.object(privileges, "execute_ordered_ddl", side_effect=observed):
            return protect_installation_in_transaction(
                self.host, self.tx, roles or self._roles()
            )

    def _source_fingerprint(self):
        namespace = self.connection.execute(
            "SELECT oid FROM pg_catalog.pg_namespace WHERE nspname=%s",
            ("truss",),
        ).fetchone()[0]
        facts = {
            "namespace": self.connection.execute(
                "SELECT oid,nspowner,nspacl::text FROM pg_catalog.pg_namespace WHERE oid=%s",
                (namespace,),
            ).fetchone(),
            "relations": self.connection.execute(
                """SELECT oid,relname,relkind,relowner,relacl::text FROM pg_catalog.pg_class
                   WHERE relnamespace=%s ORDER BY oid""",
                (namespace,),
            ).fetchall(),
            "columns": self.connection.execute(
                """SELECT attrelid,attnum,attname,attacl::text FROM pg_catalog.pg_attribute
                   WHERE attrelid IN (SELECT oid FROM pg_catalog.pg_class WHERE relnamespace=%s)
                     AND attnum>0 AND NOT attisdropped ORDER BY attrelid,attnum""",
                (namespace,),
            ).fetchall(),
            "routines": self.connection.execute(
                """SELECT oid,proname,prokind,proowner,proacl::text,
                          pg_catalog.pg_get_function_identity_arguments(oid)
                   FROM pg_catalog.pg_proc WHERE pronamespace=%s ORDER BY oid""",
                (namespace,),
            ).fetchall(),
            "types": self.connection.execute(
                """SELECT oid,typname,typtype,typowner,typacl::text,typrelid,typelem
                   FROM pg_catalog.pg_type WHERE typnamespace=%s ORDER BY oid""",
                (namespace,),
            ).fetchall(),
        }
        return json.dumps(facts, sort_keys=True, default=str, separators=(",", ":"))

    def _assert_caller_state(self, expected_snapshot):
        self.assertEqual(self._source_fingerprint(), expected_snapshot)
        self.assertEqual(
            self.connection.execute("SELECT value FROM caller_sentinel").fetchall(),
            [("before-install",)],
        )
        self.assertEqual(
            self.connection.info.transaction_status, pq.TransactionStatus.INTRANS
        )
        self.assertEqual(self.connection.execute("SELECT 42").fetchone(), (42,))

    def _measure_install(self, label, submitter, *, roles=None):
        measurement = {"label": label, "submissions": []}
        self._last_measurement = measurement

        def observed(cursor, units):
            rendered = tuple(
                unit if isinstance(unit, str) else unit.as_string(cursor.connection)
                for unit in units
            )
            source_hash = hashlib.sha256()
            for unit in rendered:
                encoded = unit.encode("utf-8")
                source_hash.update(len(encoded).to_bytes(8, "big"))
                source_hash.update(encoded)
            measurement["sourceUnitCount"] = len(rendered)
            measurement["sourceUtf8BytesIncludingJoinSeparators"] = sum(
                len(unit.encode("utf-8")) for unit in rendered
            ) + max(0, len(rendered) - 1) * len(_SEPARATOR.encode("utf-8"))
            measurement["sourceUnitsSha256"] = source_hash.hexdigest()
            counted = _CountingCursor(cursor, measurement)
            started = time.perf_counter()
            try:
                return submitter(counted, rendered)
            finally:
                measurement["ddlSubmitterElapsedSeconds"] = (
                    time.perf_counter() - started
                )

        self._last_measurement = measurement
        started = time.perf_counter()
        with patch.object(privileges, "execute_ordered_ddl", side_effect=observed):
            result = protect_installation_in_transaction(
                self.host, self.tx, roles or self._roles()
            )
        measurement["completeProtectionOperationElapsedSeconds"] = (
            time.perf_counter() - started
        )
        measurement["clientExecuteSubmissionCount"] = len(measurement["submissions"])
        measurement["clientSubmissionUtf8Bytes"] = sum(
            item["utf8Bytes"] for item in measurement["submissions"]
        )
        measurement["serverStatementCount"] = None
        measurement["serverWaits"] = None
        return result, measurement

    def _unbatched_reference(self, cursor, units):
        """Reference the prior per-source-unit execute shape; not a server count."""
        for unit in units:
            cursor.execute(unit, prepare=False, binary=False)
            saw_rows = cursor.description is not None
            while cursor.nextset():
                saw_rows = saw_rows or cursor.description is not None
            if saw_rows:
                raise ValueError("Installation DDL returned rows")

    def test_batched_and_unbatched_install_match_and_outer_savepoint_restores_exact_state(
        self,
    ):
        before = self._source_fingerprint()
        self.connection.execute("SAVEPOINT caller_install_boundary")

        baseline, baseline_measure = self._measure_install(
            "unbatched-reference", self._unbatched_reference
        )
        self.assertIsInstance(
            baseline, Ok, str(getattr(self.host._custody.last_attempt, "error", None))
        )
        self.assertEqual(
            baseline_measure["clientExecuteSubmissionCount"],
            baseline_measure["sourceUnitCount"],
        )
        self.assertGreater(baseline_measure["sourceUnitCount"], 32)
        self.assertEqual(
            baseline.value.relations, len(baseline.value.original_objects[0])
        )
        self.connection.execute("ROLLBACK TO SAVEPOINT caller_install_boundary")
        self._assert_caller_state(before)

        candidate, candidate_measure = self._measure_install(
            "bounded-batches", execute_ordered_ddl
        )
        self.assertIsInstance(
            candidate, Ok, str(getattr(self.host._custody.last_attempt, "error", None))
        )
        self.assertEqual(
            candidate_measure["sourceUnitCount"], baseline_measure["sourceUnitCount"]
        )
        self.assertEqual(
            candidate_measure["sourceUnitsSha256"],
            baseline_measure["sourceUnitsSha256"],
        )
        self.assertLess(
            candidate_measure["clientExecuteSubmissionCount"],
            baseline_measure["clientExecuteSubmissionCount"],
        )
        self.assertEqual(candidate.value.relations, baseline.value.relations)
        self.assertEqual(candidate.value.routines, baseline.value.routines)
        self.assertEqual(candidate.value.types, baseline.value.types)
        self.connection.execute("ROLLBACK TO SAVEPOINT caller_install_boundary")
        self._assert_caller_state(before)

        report = {
            "interfaceVersion": "truss-installer-ddl-batching-measurement/0.1",
            "scope": "client-side DDL execute submissions and elapsed time only; server statement counts and waits were not measured",
            "sourceHashes": {
                name: hashlib.sha256(
                    (ROOT / "packages/python/src/truss" / name).read_bytes()
                ).hexdigest()
                for name in (
                    "_installation_privileges.py",
                    "_installation_sql_batch.py",
                )
            },
            "baseline": baseline_measure,
            "candidate": candidate_measure,
        }
        evidence_path = os.environ.get("TRUSS_INSTALLATION_BATCHING_EVIDENCE")
        if evidence_path:
            Path(evidence_path).write_text(
                json.dumps(report, sort_keys=True, indent=2) + "\n"
            )

    def test_preexisting_extra_column_inherited_and_extension_state_still_refuse(self):
        owner_role = "batch_external_owner_" + self.suffix
        member_role = "batch_external_member_" + self.suffix
        self.connection.execute(
            sql.SQL("CREATE ROLE {} NOLOGIN; CREATE ROLE {} NOLOGIN").format(
                sql.Identifier(owner_role), sql.Identifier(member_role)
            ),
            prepare=False,
        )
        cases = (
            (
                "extra-view",
                "CREATE VIEW truss.batch_extra_view AS SELECT 1 AS value",
                None,
            ),
            (
                "column-grant",
                sql.SQL("GRANT SELECT(id) ON truss.schema_head TO {}").format(
                    sql.Identifier(owner_role)
                ),
                None,
            ),
            (
                "inherited-grant",
                sql.SQL(
                    "GRANT SELECT ON truss.schema_head TO {}; GRANT {} TO {}"
                ).format(
                    sql.Identifier(owner_role),
                    sql.Identifier(owner_role),
                    sql.Identifier(member_role),
                ),
                "inherited",
            ),
            (
                "extension-dependency",
                "ALTER EXTENSION plpgsql ADD TABLE truss.schema_head",
                None,
            ),
        )
        for index, (label, mutation, expected) in enumerate(cases):
            with self.subTest(control=label):
                before = self._source_fingerprint()
                savepoint = f"caller_control_{index}"
                self.connection.execute(
                    sql.SQL("SAVEPOINT {}").format(sql.Identifier(savepoint))
                )
                self.connection.execute(mutation, prepare=False)
                if expected == "inherited":
                    self.assertTrue(
                        self.connection.execute(
                            "SELECT pg_catalog.has_table_privilege(%s,%s,%s)",
                            (member_role, "truss.schema_head", "SELECT"),
                        ).fetchone()[0]
                    )
                result = protect_installation_in_transaction(
                    self.host, self.tx, self._roles()
                )
                self.assertIsInstance(result, Error)
                self.assertEqual(result.error.code, "invalid_transaction")
                cause = self.host._custody.last_attempt.error
                if label == "extra-view":
                    self.assertEqual(
                        str(cause), "Unsupported installation relation or owner"
                    )
                elif label == "extension-dependency":
                    self.assertEqual(
                        str(cause), "Extension-owned installation object refused"
                    )
                else:
                    self.assertEqual(
                        getattr(cause, "object_class", None),
                        "column" if label == "column-grant" else "relation",
                    )
                self.assertEqual(
                    self.connection.execute(
                        "SELECT value FROM caller_sentinel"
                    ).fetchall(),
                    [("before-install",)],
                )
                self.assertEqual(
                    self.connection.execute(
                        "SELECT count(*) FROM pg_catalog.pg_roles WHERE rolname IN (%s,%s)",
                        (self.owner, self.client),
                    ).fetchone()[0],
                    0,
                )
                self.connection.execute(
                    sql.SQL("ROLLBACK TO SAVEPOINT {}").format(
                        sql.Identifier(savepoint)
                    )
                )
                self.connection.execute(
                    sql.SQL("RELEASE SAVEPOINT {}").format(sql.Identifier(savepoint))
                )
                self._assert_caller_state(before)
                if label == "extra-view":
                    self.assertIsNone(
                        self.connection.execute(
                            "SELECT pg_catalog.to_regclass('truss.batch_extra_view')"
                        ).fetchone()[0]
                    )
                elif label == "column-grant":
                    self.assertFalse(
                        self.connection.execute(
                            "SELECT pg_catalog.has_column_privilege(%s,%s,%s,%s)",
                            (owner_role, "truss.schema_head", "id", "SELECT"),
                        ).fetchone()[0]
                    )
                elif label == "inherited-grant":
                    self.assertFalse(
                        self.connection.execute(
                            "SELECT pg_catalog.has_table_privilege(%s,%s,%s)",
                            (member_role, "truss.schema_head", "SELECT"),
                        ).fetchone()[0]
                    )
                    self.assertFalse(
                        self.connection.execute(
                            "SELECT pg_catalog.pg_has_role(%s,%s,'MEMBER')",
                            (member_role, owner_role),
                        ).fetchone()[0]
                    )
                else:
                    self.assertFalse(
                        self.connection.execute(
                            """SELECT EXISTS (
                                SELECT 1 FROM pg_catalog.pg_depend d
                                JOIN pg_catalog.pg_extension e
                                  ON d.refclassid='pg_catalog.pg_extension'::pg_catalog.regclass
                                 AND d.refobjid=e.oid
                                WHERE e.extname='plpgsql'
                                  AND d.classid='pg_catalog.pg_class'::pg_catalog.regclass
                                  AND d.objid='truss.schema_head'::pg_catalog.regclass
                                  AND d.deptype='e')"""
                        ).fetchone()[0]
                    )

    def test_mid_batch_statement_timeout_and_post_batch_drift_roll_back_to_caller_savepoint(
        self,
    ):
        before = self._source_fingerprint()
        self.connection.execute("SAVEPOINT caller_failure_boundary")
        timeout_batches = []

        def timeout_submitter(cursor, units):
            units = list(units)
            self.assertGreater(len(units), 32)
            injected = [
                *units[:32],
                (
                    "DO $truss_batch_deadline$ BEGIN "
                    "PERFORM pg_catalog.pg_sleep(3); "
                    "END $truss_batch_deadline$"
                ),
                *units[32:],
            ]
            return execute_ordered_ddl(cursor, injected)

        def timeout_intercept(cursor, units):
            class RecordCursor(_CountingCursor):
                def execute(inner_self, query, *args, **kwargs):
                    timeout_batches.append(len(query.encode("utf-8")))
                    return super().execute(query, *args, **kwargs)

            return timeout_submitter(RecordCursor(cursor, {"submissions": []}), units)

        with patch.object(
            privileges, "execute_ordered_ddl", side_effect=timeout_intercept
        ):
            timed_out = protect_installation_in_transaction(
                self.host, self.tx, self._roles()
            )
        self.assertIsInstance(timed_out, Error)
        self.assertEqual(getattr(timed_out.error, "sql_state", None), "57014")
        self.assertGreaterEqual(len(timeout_batches), 2)
        self._assert_caller_state(before)

        drift_cases = (
            (
                "missing-overload",
                lambda cursor: cursor.execute(
                    "DROP FUNCTION truss.private_probe(integer)", prepare=False
                ),
            ),
            (
                "replacement-overload-identity",
                lambda cursor: cursor.execute(
                    "DROP FUNCTION truss.private_probe(integer); "
                    "CREATE FUNCTION truss.private_probe(value integer) RETURNS integer "
                    "LANGUAGE sql AS 'SELECT value + 1'",
                    prepare=False,
                ),
            ),
            (
                "object-owner",
                lambda cursor: cursor.execute(
                    sql.SQL("ALTER TABLE truss.schema_head OWNER TO {}").format(
                        sql.Identifier("batch_external_owner_" + self.suffix)
                    ),
                    prepare=False,
                ),
            ),
        )
        self.connection.execute(
            sql.SQL("CREATE ROLE {} NOLOGIN").format(
                sql.Identifier("batch_external_owner_" + self.suffix)
            ),
            prepare=False,
        )
        for index, (label, mutate) in enumerate(drift_cases):
            with self.subTest(drift=label):
                savepoint = f"caller_drift_{index}"
                self.connection.execute(
                    sql.SQL("SAVEPOINT {}").format(sql.Identifier(savepoint))
                )
                result = self._run_install(after_ddl=mutate)
                self.assertIsInstance(result, Error)
                self.assertEqual(result.error.code, "invalid_transaction")
                self.assertTrue(self._last_after_ddl_ran)
                expected_message = (
                    "Installation ownership mismatch"
                    if label == "object-owner"
                    else "Installation object identities changed"
                )
                self.assertEqual(
                    str(self.host._custody.last_attempt.error), expected_message
                )
                self.connection.execute(
                    sql.SQL("ROLLBACK TO SAVEPOINT {}").format(
                        sql.Identifier(savepoint)
                    )
                )
                self.connection.execute(
                    sql.SQL("RELEASE SAVEPOINT {}").format(sql.Identifier(savepoint))
                )
                self._assert_caller_state(before)

    def test_operation_deadline_cancels_multi_statement_batch_before_later_batch(self):
        statement_timeout_ms = 1000
        operation_timeout_ms = 1200
        sleep_per_statement_ms = 400
        sleep_count = 4
        self.assertLess(operation_timeout_ms, sleep_per_statement_ms * sleep_count)
        self.assertLess(sleep_per_statement_ms, statement_timeout_ms)

        self.connection.execute(
            "CREATE TEMP TABLE batch_deadline_sentinel(value text NOT NULL)"
        )
        before = self._source_fingerprint()
        self.connection.execute("SAVEPOINT caller_operation_deadline_boundary")

        self.assertTrue(self.host.detach())
        self.host = psycopg_host.adopt_psycopg_host(
            self.connection,
            profile=self.selected_profile,
            statement_timeout_ms=statement_timeout_ms,
            operation_timeout_ms=operation_timeout_ms,
        )
        self.addCleanup(self.host.detach)
        adopted = self.host.adopt_transaction()
        self.assertIsInstance(adopted, Ok)
        self.tx = adopted.value

        sleep_unit = " ".join(
            f"DO $truss_deadline_{index}$ BEGIN "
            f"PERFORM pg_catalog.pg_sleep({sleep_per_statement_ms / 1000}); "
            f"END $truss_deadline_{index}$;"
            for index in range(sleep_count)
        )
        later_batch = (
            "INSERT INTO pg_temp.batch_deadline_sentinel(value) "
            "VALUES ('later-batch-ran')"
        )
        submitted: list[str] = []
        original_deadline = psycopg_host._Deadline
        deadlines = []

        def track_deadline(connection, milliseconds):
            deadline = original_deadline(connection, milliseconds)
            deadlines.append(deadline)
            return deadline

        class CapturingCursor:
            def __init__(self, cursor):
                self._cursor = cursor

            def __getattr__(self, name):
                return getattr(self._cursor, name)

            def execute(self, query, *args, **kwargs):
                rendered = (
                    query
                    if isinstance(query, str)
                    else query.as_string(self.connection)
                )
                submitted.append(rendered)
                return self._cursor.execute(query, *args, **kwargs)

        def submit_with_deadline(cursor, units):
            captured = tuple(units)
            self.assertGreater(len(captured), 32)
            injected = [sleep_unit, *captured[:31], later_batch, *captured[31:]]
            return execute_ordered_ddl(CapturingCursor(cursor), injected)

        started = time.monotonic()
        with (
            patch.object(
                privileges, "execute_ordered_ddl", side_effect=submit_with_deadline
            ),
            patch.object(psycopg_host, "_Deadline", side_effect=track_deadline),
        ):
            result = protect_installation_in_transaction(
                self.host, self.tx, self._roles()
            )
        elapsed = time.monotonic() - started

        self.assertIsInstance(result, Error)
        self.assertEqual(result.error.code, "cancelled")
        self.assertEqual(result.error.sql_state, "57014")
        self.assertTrue(deadlines)
        self.assertTrue(deadlines[0].expired.is_set())
        self.assertLess(elapsed, operation_timeout_ms / 1000 + 1.0)
        self.assertEqual(len(submitted), 1)
        self.assertIn("pg_sleep(0.4)", submitted[0])
        self.assertNotIn(later_batch, submitted[0])
        self.assertEqual(
            self.connection.execute(
                "SELECT value FROM pg_temp.batch_deadline_sentinel"
            ).fetchall(),
            [],
        )
        self._assert_caller_state(before)
        self.assertEqual(
            self.connection.execute("SHOW statement_timeout").fetchone(), ("3s",)
        )
        self.assertTrue(self.host.detach())
        self.assertEqual(self.connection.execute("SELECT 43").fetchone(), (43,))
        self.assertEqual(
            self.connection.info.transaction_status, pq.TransactionStatus.INTRANS
        )

    def test_tolerated_role_acl_drift_is_not_hidden_by_batching(self):
        tolerated = "batch_tolerated_" + self.suffix
        self.connection.execute(
            sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(tolerated)),
            prepare=False,
        )
        before = self._source_fingerprint()
        self.connection.execute("SAVEPOINT caller_tolerated_boundary")

        def add_grant(cursor):
            cursor.execute(
                sql.SQL("GRANT SELECT ON truss.schema_head TO {}").format(
                    sql.Identifier(tolerated)
                ),
                prepare=False,
            )

        result = self._run_install(
            roles=self._roles(tolerated=(tolerated,)), after_ddl=add_grant
        )

        self.assertIsInstance(result, Error)
        self.assertEqual(result.error.code, "invalid_transaction")
        self.assertTrue(self._last_after_ddl_ran)
        self.assertEqual(
            str(self.host._custody.last_attempt.error),
            "Tolerated native grants changed during installation",
        )
        self.connection.execute("ROLLBACK TO SAVEPOINT caller_tolerated_boundary")
        self._assert_caller_state(before)


def load_tests(loader, tests, pattern):
    names = (
        "test_batched_and_unbatched_install_match_and_outer_savepoint_restores_exact_state",
        "test_preexisting_extra_column_inherited_and_extension_state_still_refuse",
        "test_mid_batch_statement_timeout_and_post_batch_drift_roll_back_to_caller_savepoint",
        "test_operation_deadline_cancels_multi_statement_batch_before_later_batch",
        "test_tolerated_role_acl_drift_is_not_hidden_by_batching",
    )
    return unittest.TestSuite(InstallationBatchingNativeTests(name) for name in names)


if __name__ == "__main__":
    unittest.main()
