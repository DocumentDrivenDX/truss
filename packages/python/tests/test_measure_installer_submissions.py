# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure PostgreSQL profile controls for the installer measurement runner."""

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/measure-installer-submissions.py"
RUNTIME_PROFILE = (
    ROOT / "packages/python/src/truss/_profiles/local-postgres-runtime.json"
)
SPEC = importlib.util.spec_from_file_location("measure_installer_submissions", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MEASURER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MEASURER)


def numeric_server_version(display_version):
    major, minor = (int(part) for part in display_version.split("."))
    return major * 10000 + minor


def trigger_fixture():
    constraint_rows = []
    raw_trigger_rows = []
    for index in range(130):
        relation = f"child_{index}"
        constraint_name = f"child_{index}_parent_fkey"
        constraint_oid = str(50000 + index)
        constraint_definition = (
            "FOREIGN KEY (parent_id) REFERENCES parent(id) "
            "ON UPDATE NO ACTION ON DELETE NO ACTION"
        )
        constraint_rows.append(
            [relation, constraint_name, "f", constraint_definition, True, False, False]
        )
        for action in ("a", "c"):
            trigger_oid = str(10000 + index * 2 + (action == "c"))
            trigger_name = f"RI_ConstraintTrigger_{action}_{trigger_oid}"
            trigger_definition = (
                f'CREATE CONSTRAINT TRIGGER "{trigger_name}" AFTER UPDATE ON '
                f"truss.parent FROM truss.{relation} DEFERRABLE INITIALLY DEFERRED "
                "FOR EACH ROW EXECUTE FUNCTION pg_catalog.ri_action()"
            )
            raw_trigger_rows.append(
                [
                    trigger_oid,
                    "parent",
                    trigger_name,
                    "O",
                    True,
                    constraint_oid,
                    constraint_oid,
                    relation,
                    constraint_name,
                    "f",
                    "truss",
                    constraint_definition,
                    trigger_definition,
                ]
            )
    for index in range(62):
        trigger_oid = str(20000 + index)
        trigger_name = f"application_trigger_{index}"
        raw_trigger_rows.append(
            [
                trigger_oid,
                "parent",
                trigger_name,
                "O",
                False,
                "0",
                None,
                None,
                None,
                None,
                None,
                None,
                f'CREATE TRIGGER "{trigger_name}" BEFORE INSERT ON truss.parent',
            ]
        )
    normalized, evidence = MEASURER._normalize_internal_trigger_rows(
        raw_trigger_rows, constraint_rows
    )
    return raw_trigger_rows, constraint_rows, normalized, evidence


class InstallerMeasurementRuntimeProfileTests(unittest.TestCase):
    def test_public49_profile_pair_and_candidate_profile_are_accepted(self):
        # The public 0.0.49 wheel and current source use the selected 18.6 tuple.
        public49_display = "18.6"
        MEASURER._require_server_version_profile(
            public49_display, numeric_server_version(public49_display)
        )

        candidate = json.loads(RUNTIME_PROFILE.read_bytes())
        MEASURER._require_server_version_profile(
            candidate["serverVersion"],
            numeric_server_version(candidate["serverVersion"]),
        )

    def test_wrong_display_or_numeric_profile_is_refused(self):
        for display, numeric in (("18.06", 180006), ("18.6", 180007)):
            with (
                self.subTest(display=display, numeric=numeric),
                self.assertRaisesRegex(RuntimeError, "PostgreSQL 18.6 package profile"),
            ):
                MEASURER._require_server_version_profile(display, numeric)


class FakeCursor:
    def __init__(self, *, nextset_result=None, nextset_error=None):
        self.nextset_result = nextset_result
        self.nextset_error = nextset_error
        self.execute_result = object()

    def execute(self, *args, **kwargs):
        return self.execute_result

    def nextset(self, *args, **kwargs):
        if self.nextset_error is not None:
            raise self.nextset_error
        return self.nextset_result


class FakePsycopg:
    Cursor = FakeCursor


def measurement_recorder():
    return {
        "cursorExecuteCount": 0,
        "cursorExecuteElapsedNs": 0,
        "cursorExecuteMaxNs": 0,
        "cursorNextsetCount": 0,
        "cursorNextsetElapsedNs": 0,
        "cursorNextsetMaxNs": 0,
        "cursorNextsetFailureCount": 0,
        "orderedDdlHelperCalls": 0,
        "orderedDdlUnits": 0,
        "orderedDdlExecuteSubmissions": 0,
        "orderedDdlSourceUnitCount": 0,
        "orderedDdlOtherUnitCount": 0,
        "directSourceUnitExecuteSubmissions": 0,
        "sourceUnitHashes": set(),
    }


class InstallerMeasurementObserverTests(unittest.TestCase):
    def setUp(self):
        self.original_execute = FakeCursor.execute
        self.original_nextset = FakeCursor.nextset
        self.recorder = measurement_recorder()
        MEASURER._measure_cursor_execute(FakePsycopg, self.recorder)

    def tearDown(self):
        MEASURER._ACTIVE_MEASUREMENT.set(None)
        MEASURER._restore_instrumentation(FakePsycopg, self.recorder)

    def test_active_execute_and_nextset_are_counted_separately(self):
        cursor = FakeCursor(nextset_result=True)
        token = MEASURER._ACTIVE_MEASUREMENT.set(self.recorder)
        try:
            self.assertIs(cursor.execute("select 1"), cursor.execute_result)
            self.assertIs(cursor.nextset(), True)
        finally:
            MEASURER._ACTIVE_MEASUREMENT.reset(token)
        self.assertEqual(self.recorder["cursorExecuteCount"], 1)
        self.assertEqual(self.recorder["cursorNextsetCount"], 1)
        self.assertEqual(self.recorder["cursorNextsetFailureCount"], 0)
        self.assertGreaterEqual(self.recorder["cursorExecuteElapsedNs"], 0)
        self.assertGreaterEqual(self.recorder["cursorNextsetElapsedNs"], 0)

    def test_nextset_exception_identity_is_preserved_and_counted(self):
        error = RuntimeError("sentinel exception; not report data")
        cursor = FakeCursor(nextset_error=error)
        token = MEASURER._ACTIVE_MEASUREMENT.set(self.recorder)
        try:
            with self.assertRaises(RuntimeError) as raised:
                cursor.nextset()
        finally:
            MEASURER._ACTIVE_MEASUREMENT.reset(token)
        self.assertIs(raised.exception, error)
        self.assertEqual(self.recorder["cursorNextsetCount"], 1)
        self.assertEqual(self.recorder["cursorNextsetFailureCount"], 1)

    def test_inactive_calls_pass_through_and_hooks_restore_exactly(self):
        cursor = FakeCursor(nextset_result="unchanged")
        self.assertIs(cursor.execute("select 1"), cursor.execute_result)
        self.assertEqual(cursor.nextset(), "unchanged")
        self.assertEqual(self.recorder["cursorExecuteCount"], 0)
        self.assertEqual(self.recorder["cursorNextsetCount"], 0)
        MEASURER._restore_instrumentation(FakePsycopg, self.recorder)
        self.assertIs(FakeCursor.execute, self.original_execute)
        self.assertIs(FakeCursor.nextset, self.original_nextset)

    def test_process_cpu_has_explicit_install_window_scope(self):
        summary = MEASURER._measurement_summary(
            self.recorder, install_elapsed_ns=23, process_cpu_ns=9
        )
        self.assertEqual(summary["installElapsedNs"], 23)
        self.assertEqual(summary["installerProcessCpuElapsedNs"], 9)
        self.assertEqual(summary["cursorExecuteSubmissionCount"], 0)
        self.assertEqual(summary["cursorNextsetCallCount"], 0)
        self.assertIn("whole diagnostic child process CPU", summary["processCpuScope"])
        self.assertNotIn("SQL", summary)

    def test_clocks_start_after_hook_setup_and_stop_at_installer_return(self):
        clock_calls = []
        hook_setup_complete = False

        def wall_clock():
            self.assertTrue(hook_setup_complete)
            clock_calls.append("wall")
            return 100 if clock_calls.count("wall") == 1 else 200

        def process_clock():
            self.assertTrue(hook_setup_complete)
            clock_calls.append("cpu")
            return 10 if clock_calls.count("cpu") == 1 else 30

        hook_setup_complete = True
        with (
            patch.object(MEASURER, "perf_counter_ns", wall_clock),
            patch.object(MEASURER.time, "process_time_ns", process_clock),
        ):
            result = MEASURER._call_measured_install(self.recorder, lambda: "installed")
        self.assertEqual(result, "installed")
        self.assertEqual(clock_calls, ["wall", "cpu", "wall", "cpu"])
        self.assertEqual(self.recorder["installElapsedNs"], 100)
        self.assertEqual(self.recorder["installerProcessCpuElapsedNs"], 20)

    def test_summary_failure_does_not_mask_installer_error_or_skip_restore(self):
        self.recorder["installAttempted"] = True
        self.recorder["installElapsedNs"] = 10
        self.recorder["installerProcessCpuElapsedNs"] = 5
        token = MEASURER._ACTIVE_MEASUREMENT.set(self.recorder)
        original = RuntimeError("original installer failure")
        report_error = ValueError("reporting failure")
        result = {}
        try:
            with (
                patch.object(
                    MEASURER, "_measurement_summary", side_effect=report_error
                ),
                self.assertRaises(RuntimeError) as raised,
            ):
                try:
                    raise original
                except BaseException as primary:  # noqa: BLE001 - test BaseException preservation
                    try:
                        raise
                    finally:
                        MEASURER._finish_measurement(
                            FakePsycopg, self.recorder, token, result, primary
                        )
        finally:
            MEASURER._ACTIVE_MEASUREMENT.set(None)
            MEASURER._restore_instrumentation(FakePsycopg, self.recorder)
        self.assertIs(raised.exception, original)
        self.assertEqual(result["measurementSummaryFailureType"], "ValueError")
        self.assertTrue(result["instrumentationHooksRestored"])
        self.assertIs(FakeCursor.execute, self.original_execute)
        self.assertIs(FakeCursor.nextset, self.original_nextset)

    def test_ordered_ddl_hook_covers_batch_module_and_privileges_alias_once(self):
        def execute_ordered_ddl(cursor, units):
            for unit in units:
                cursor.execute(unit)

        batch = SimpleNamespace(execute_ordered_ddl=execute_ordered_ddl)
        privileges = SimpleNamespace(execute_ordered_ddl=execute_ordered_ddl)
        self.recorder["sourceUnitHashes"] = {
            hashlib.sha256(b"catalog-runtime-ddl").hexdigest(),
            hashlib.sha256(b"privileges-ddl").hexdigest(),
        }
        MEASURER._measure_ordered_ddl(batch, (privileges,), self.recorder)
        cursor = FakeCursor()
        token = MEASURER._ACTIVE_MEASUREMENT.set(self.recorder)
        try:
            # catalog_runtime resolves the batch module inside install, while
            # privileges retains its imported alias.
            batch.execute_ordered_ddl(cursor, ["catalog-runtime-ddl"])
            privileges.execute_ordered_ddl(cursor, ["privileges-ddl"])
        finally:
            MEASURER._ACTIVE_MEASUREMENT.reset(token)
            MEASURER._restore_instrumentation(FakePsycopg, self.recorder)
        self.assertEqual(self.recorder["orderedDdlHelperCalls"], 2)
        self.assertEqual(self.recorder["orderedDdlUnits"], 2)
        self.assertEqual(self.recorder["orderedDdlExecuteSubmissions"], 2)
        self.assertEqual(self.recorder["orderedDdlSourceUnitCount"], 2)
        self.assertEqual(self.recorder["orderedDdlOtherUnitCount"], 0)
        self.assertIs(batch.execute_ordered_ddl, execute_ordered_ddl)
        self.assertIs(privileges.execute_ordered_ddl, execute_ordered_ddl)


class InstallerPublicationBindingTests(unittest.TestCase):
    def test_publisher_recomputes_snapshot_package_source_and_budget_bindings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_root = root / "src" / "truss"
            source_root.mkdir(parents=True)
            members = {
                "truss/_installation_privileges.py": b"privileges",
                "truss/_installation_sql_batch.py": b"batch",
                "truss/catalog_runtime.py": b"catalog",
                "truss/psycopg_host.py": b"host",
                "truss/_catalog_runtime/runtime.sql": (
                    ROOT / "packages/python/src/truss/_catalog_runtime/runtime.sql"
                ).read_bytes(),
            }
            for name, content in members.items():
                path = source_root / name.removeprefix("truss/")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            wheel = root / "candidate.whl"
            with zipfile.ZipFile(wheel, "w") as archive:
                for name, content in members.items():
                    archive.writestr(name, content)
            source_tree = MEASURER._tree_digest(source_root)
            module_paths = {
                "truss._installation_privileges": "truss/_installation_privileges.py",
                "truss._installation_sql_batch": "truss/_installation_sql_batch.py",
                "truss.catalog_runtime": "truss/catalog_runtime.py",
                "truss.psycopg_host": "truss/psycopg_host.py",
            }
            module_hashes = {
                module: hashlib.sha256(members[member]).hexdigest()
                for module, member in module_paths.items()
            }
            before = {
                "sourceFreeze": {"gitCommit": "commit", "sourceTree": source_tree},
                "environmentDistributionVersion": "0.0.49",
                "sourceProjectVersion": "0.0.50",
                "releaseSha256": MEASURER.NATIVE_MANIFEST_SHA256,
                "runtimeSqlSha256": MEASURER.RUNTIME_SQL_SHA256,
                "moduleSha256": module_hashes,
            }
            _, constraint_rows, normalized_triggers, trigger_evidence = (
                trigger_fixture()
            )
            snapshot = {
                "relations": [],
                "sequences": [],
                "triggers": normalized_triggers,
                "constraints": constraint_rows,
                "relationRows": {
                    "reader_catalog_validator_secret": [
                        {"secret": "<validated-validator-secret>"}
                    ],
                    "catalog_runtime_installation": [
                        {
                            "singleton": True,
                            "installation_id": "<generated:installation_id>",
                            "source_epoch": "<generated:source_epoch>",
                            "genesis_at": "<generated:genesis_at>",
                            "owner_oid": MEASURER.OWNER_ROLE,
                            "registrar_oid": MEASURER.CLIENT_ROLE,
                        }
                    ],
                    "schema_rev": [{"rev": 0, "accepted_at": "<generated:genesis_at>"}],
                },
            }
            snapshot_sha = hashlib.sha256(
                MEASURER._canonical_bytes(snapshot)
            ).hexdigest()
            baseline_secret_sha = hashlib.sha256(b"baseline-secret").hexdigest()
            candidate_secret_sha = hashlib.sha256(b"candidate-secret").hexdigest()

            def snapshot_evidence(commitment):
                return {
                    "profile": MEASURER._SNAPSHOT_PROFILE,
                    "nativeManifestSha256": MEASURER.NATIVE_MANIFEST_SHA256,
                    "runtimeSqlSha256": MEASURER.RUNTIME_SQL_SHA256,
                    "installationIdentity": {
                        "installationId": "00000000-0000-4000-8000-000000000001",
                        "sourceEpoch": "00000000-0000-4000-8000-000000000002",
                        "genesisAt": "2026-10-23T12:00:00+00:00",
                        "ownerOid": "41",
                        "registrarOid": "73",
                    },
                    "schemaRevision": {
                        "rev": 0,
                        "acceptedAt": "2026-10-23T12:00:00+00:00",
                    },
                    "nativeRoleBindings": {
                        "owner": {"oid": "41", "name": MEASURER.OWNER_ROLE},
                        "registrar": {"oid": "73", "name": MEASURER.CLIENT_ROLE},
                    },
                    "validatorSecret": {
                        "status": "validated",
                        "table": "truss.reader_catalog_validator_secret",
                        "column": "secret",
                        "rowCount": 1,
                        "secretBytes": 32,
                        "secretSha256": commitment,
                        "runtimeSqlSha256": MEASURER.RUNTIME_SQL_SHA256,
                        "nativeManifestSha256": MEASURER.NATIVE_MANIFEST_SHA256,
                    },
                    "internalTriggers": trigger_evidence,
                }

            report = {
                "comparison": {
                    "status": "equal",
                    "snapshotEqual": True,
                    "baselineSnapshotSha256": snapshot_sha,
                    "candidateSnapshotSha256": snapshot_sha,
                    "baselineValidatorSecretSha256": baseline_secret_sha,
                    "candidateValidatorSecretSha256": candidate_secret_sha,
                    "validatorSecretCommitmentsDistinct": True,
                },
                "measurements": {
                    label: {
                        "budgetsMs": {"statement": 60000, "operation": 60000},
                        "baselineWheel": (
                            {
                                "wheelSha256": MEASURER.BASELINE_WHEEL_SHA256,
                                "distributionVersion": MEASURER.BASELINE_VERSION,
                                "payloadMembersEqual": True,
                            }
                            if label == "baseline"
                            else None
                        ),
                        "package": {
                            "before": copy.deepcopy(before),
                            "after": copy.deepcopy(before),
                        },
                        "snapshot": copy.deepcopy(snapshot),
                        "snapshotSha256": snapshot_sha,
                        "snapshotEvidence": snapshot_evidence(
                            baseline_secret_sha
                            if label == "baseline"
                            else candidate_secret_sha
                        ),
                    }
                    for label in ("baseline", "candidate")
                },
            }
            MEASURER._validate_published_comparison(
                report,
                source_root=source_root,
                candidate_wheel=wheel,
                source_commit="commit",
                project_version="0.0.50",
                target_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
            )
            mutations = []
            changed_snapshot = copy.deepcopy(report)
            changed_snapshot["measurements"]["candidate"]["snapshot"][
                "relations"
            ].append("tampered")
            mutations.append(changed_snapshot)
            unequal_snapshot = copy.deepcopy(report)
            unequal_snapshot["measurements"]["candidate"]["snapshot"][
                "sequences"
            ].append(["unexpected_sequence", 1, False])
            candidate_sha = hashlib.sha256(
                MEASURER._canonical_bytes(
                    unequal_snapshot["measurements"]["candidate"]["snapshot"]
                )
            ).hexdigest()
            unequal_snapshot["measurements"]["candidate"]["snapshotSha256"] = (
                candidate_sha
            )
            unequal_snapshot["comparison"]["candidateSnapshotSha256"] = candidate_sha
            mutations.append(unequal_snapshot)
            changed_comparison = copy.deepcopy(report)
            changed_comparison["comparison"]["baselineSnapshotSha256"] = "0" * 64
            mutations.append(changed_comparison)
            changed_source = copy.deepcopy(report)
            for side in ("before", "after"):
                changed_source["measurements"]["candidate"]["package"][side][
                    "sourceFreeze"
                ]["sourceTree"]["sha256"] = "0" * 64
            mutations.append(changed_source)
            changed_module = copy.deepcopy(report)
            for side in ("before", "after"):
                changed_module["measurements"]["candidate"]["package"][side][
                    "moduleSha256"
                ]["truss.catalog_runtime"] = "0" * 64
            mutations.append(changed_module)
            changed_after = copy.deepcopy(report)
            changed_after["measurements"]["candidate"]["package"]["after"][
                "releaseSha256"
            ] = "0" * 64
            mutations.append(changed_after)
            changed_budget = copy.deepcopy(report)
            changed_budget["measurements"]["baseline"]["budgetsMs"]["operation"] = 30000
            mutations.append(changed_budget)
            same_secret = copy.deepcopy(report)
            same_secret["measurements"]["candidate"]["snapshotEvidence"][
                "secretSha256"
            ] = baseline_secret_sha
            same_secret["comparison"]["candidateValidatorSecretSha256"] = (
                baseline_secret_sha
            )
            mutations.append(same_secret)
            false_distinct = copy.deepcopy(report)
            false_distinct["comparison"]["validatorSecretCommitmentsDistinct"] = False
            mutations.append(false_distinct)
            raw_secret = copy.deepcopy(report)
            raw_secret["measurements"]["candidate"]["snapshotEvidence"][
                "validatorSecret"
            ]["secretHex"] = "ab" * 32
            mutations.append(raw_secret)
            changed_original_identity = copy.deepcopy(report)
            changed_original_identity["measurements"]["candidate"]["snapshotEvidence"][
                "installationIdentity"
            ]["installationId"] = "not-a-canonical-uuid"
            mutations.append(changed_original_identity)
            wrong_oid_binding = copy.deepcopy(report)
            wrong_oid_binding["measurements"]["candidate"]["snapshot"]["relationRows"][
                "catalog_runtime_installation"
            ][0]["owner_oid"] = "4294967296"
            wrong_oid_binding["measurements"]["candidate"]["snapshotSha256"] = (
                hashlib.sha256(
                    MEASURER._canonical_bytes(
                        wrong_oid_binding["measurements"]["candidate"]["snapshot"]
                    )
                ).hexdigest()
            )
            wrong_oid_binding["comparison"]["candidateSnapshotSha256"] = (
                wrong_oid_binding["measurements"]["candidate"]["snapshotSha256"]
            )
            mutations.append(wrong_oid_binding)
            for mutated in mutations:
                with (
                    self.subTest(report=mutations.index(mutated)),
                    self.assertRaises(ValueError),
                ):
                    MEASURER._validate_published_comparison(
                        mutated,
                        source_root=source_root,
                        candidate_wheel=wheel,
                        source_commit="commit",
                        project_version="0.0.50",
                        target_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
                    )


class InstallerSnapshotProfileTests(unittest.TestCase):
    def test_canonical_native_oid_text_is_bounded_and_ascii_only(self):
        self.assertEqual(MEASURER._canonical_oid_text("1"), 1)
        self.assertEqual(MEASURER._canonical_oid_text("4294967295"), 4294967295)
        for invalid in (
            None,
            True,
            1,
            "",
            "0",
            "00",
            "01",
            "+1",
            "-1",
            " 1",
            "١",
            "4294967296",
            "1.0",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(RuntimeError):
                MEASURER._canonical_oid_text(invalid)

    def test_native_role_oid_text_binds_only_the_exact_fixed_roles(self):
        role_map = {41: MEASURER.OWNER_ROLE, 73: MEASURER.CLIENT_ROLE}
        self.assertEqual(
            MEASURER._bind_installation_role_oids([("41", "73")], role_map),
            (41, 73),
        )
        for rows, mapping in (
            ([("41", "41")], role_map),
            ([("41", "73"), ("41", "73")], role_map),
            ([("041", "73")], role_map),
            ([("41", "73")], {41: MEASURER.CLIENT_ROLE, 73: MEASURER.OWNER_ROLE}),
        ):
            with (
                self.subTest(rows=rows, mapping=mapping),
                self.assertRaises(RuntimeError),
            ):
                MEASURER._bind_installation_role_oids(rows, mapping)

    def test_native_validator_secret_projects_only_a_source_bound_commitment(self):
        raw = bytes(range(32))
        rows = [(raw.hex(), 32)]
        evidence = MEASURER._native_validator_secret_evidence(
            rows,
            runtime_sql_sha256=MEASURER.RUNTIME_SQL_SHA256,
            native_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
        )
        self.assertEqual(evidence["secretSha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(evidence["secretBytes"], 32)
        self.assertNotIn("secret", evidence)
        self.assertNotIn(raw.hex(), json.dumps(evidence))
        self.assertNotEqual(
            evidence["secretSha256"],
            MEASURER._native_validator_secret_evidence(
                [(bytes(reversed(range(32))).hex(), 32)],
                runtime_sql_sha256=MEASURER.RUNTIME_SQL_SHA256,
                native_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
            )["secretSha256"],
        )
        self.assertEqual(
            MEASURER._normalize_validator_secret_json_row(
                {"secret": "\\x" + raw.hex()}, raw.hex()
            ),
            {"secret": "<validated-validator-secret>"},
        )
        for json_row in (
            {"secret": "\\x" + ("0" * 64)},
            {"secret": "\\x" + raw.hex(), "extra": "field"},
            {"secret": raw.hex()},
            ["\\x" + raw.hex()],
        ):
            with self.subTest(json_row=json_row), self.assertRaises(RuntimeError):
                MEASURER._normalize_validator_secret_json_row(json_row, raw.hex())
        for invalid_rows in (
            [],
            rows + rows,
            [(raw.hex().upper(), 32)],
            [(raw.hex(), 31)],
            [(raw.hex()[:-2], 32)],
        ):
            with self.subTest(rows=invalid_rows), self.assertRaises(RuntimeError):
                MEASURER._native_validator_secret_evidence(
                    invalid_rows,
                    runtime_sql_sha256=MEASURER.RUNTIME_SQL_SHA256,
                    native_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
                )

    def test_snapshot_evidence_is_closed_and_cross_binds_original_identity(self):
        _, constraint_rows, normalized_triggers, trigger_evidence = trigger_fixture()
        evidence = {
            "profile": MEASURER._SNAPSHOT_PROFILE,
            "nativeManifestSha256": MEASURER.NATIVE_MANIFEST_SHA256,
            "runtimeSqlSha256": MEASURER.RUNTIME_SQL_SHA256,
            "installationIdentity": {
                "installationId": "00000000-0000-4000-8000-000000000001",
                "sourceEpoch": "00000000-0000-4000-8000-000000000002",
                "genesisAt": "2026-10-23T12:00:00+00:00",
                "ownerOid": "41",
                "registrarOid": "73",
            },
            "schemaRevision": {
                "rev": 0,
                "acceptedAt": "2026-10-23T12:00:00+00:00",
            },
            "nativeRoleBindings": {
                "owner": {"oid": "41", "name": MEASURER.OWNER_ROLE},
                "registrar": {"oid": "73", "name": MEASURER.CLIENT_ROLE},
            },
            "validatorSecret": {
                "status": "validated",
                "table": "truss.reader_catalog_validator_secret",
                "column": "secret",
                "rowCount": 1,
                "secretBytes": 32,
                "secretSha256": hashlib.sha256(b"s" * 32).hexdigest(),
                "runtimeSqlSha256": MEASURER.RUNTIME_SQL_SHA256,
                "nativeManifestSha256": MEASURER.NATIVE_MANIFEST_SHA256,
            },
            "internalTriggers": trigger_evidence,
        }
        validated = MEASURER._snapshot_evidence(
            evidence,
            runtime_sql_sha256=MEASURER.RUNTIME_SQL_SHA256,
            native_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
        )
        snapshot = {
            "triggers": normalized_triggers,
            "constraints": constraint_rows,
            "relationRows": {
                "catalog_runtime_installation": [
                    {
                        "singleton": True,
                        "installation_id": "<generated:installation_id>",
                        "source_epoch": "<generated:source_epoch>",
                        "genesis_at": "<generated:genesis_at>",
                        "owner_oid": MEASURER.OWNER_ROLE,
                        "registrar_oid": MEASURER.CLIENT_ROLE,
                    }
                ],
                "schema_rev": [{"rev": 0, "accepted_at": "<generated:genesis_at>"}],
                "reader_catalog_validator_secret": [
                    {"secret": "<validated-validator-secret>"}
                ],
            },
        }
        MEASURER._validate_snapshot_normalization(snapshot, validated)
        bad = copy.deepcopy(evidence)
        bad["schemaRevision"]["acceptedAt"] = "2026-10-23T12:00:01+00:00"
        with self.assertRaisesRegex(ValueError, "does not bind genesis"):
            MEASURER._snapshot_evidence(
                bad,
                runtime_sql_sha256=MEASURER.RUNTIME_SQL_SHA256,
                native_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
            )
        bad = copy.deepcopy(evidence)
        bad["nativeRoleBindings"]["owner"]["oid"] = "73"
        with self.assertRaisesRegex(ValueError, "role binding evidence"):
            MEASURER._snapshot_evidence(
                bad,
                runtime_sql_sha256=MEASURER.RUNTIME_SQL_SHA256,
                native_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
            )
        bad_snapshot = copy.deepcopy(snapshot)
        bad_snapshot["relationRows"]["schema_rev"][0]["accepted_at"] = "wrong"
        with self.assertRaisesRegex(ValueError, "revision markers"):
            MEASURER._validate_snapshot_normalization(bad_snapshot, validated)

        bad_snapshot = copy.deepcopy(snapshot)
        bad_snapshot["triggers"][0][4] += " altered-tail"
        with self.assertRaisesRegex(ValueError, "foreign-key evidence mismatch"):
            MEASURER._validate_snapshot_normalization(bad_snapshot, validated)
        bad_evidence = copy.deepcopy(validated)
        bad_evidence["internalTriggers"][0]["originalDefinition"] += " altered-tail"
        with self.assertRaisesRegex(ValueError, "foreign-key evidence mismatch"):
            MEASURER._validate_snapshot_normalization(snapshot, bad_evidence)
        bad_snapshot = copy.deepcopy(snapshot)
        bad_snapshot["constraints"].append(
            copy.deepcopy(bad_snapshot["constraints"][0])
        )
        with self.assertRaisesRegex(ValueError, "foreign-key evidence mismatch"):
            MEASURER._validate_snapshot_normalization(bad_snapshot, validated)

    def test_internal_trigger_normalization_is_fk_bound_and_finite(self):
        raw_rows, constraint_rows, normalized, evidence = trigger_fixture()
        self.assertEqual(len(normalized), 322)
        self.assertEqual(sum(row[3] is True for row in normalized), 260)
        self.assertEqual(sum(row[3] is False for row in normalized), 62)
        self.assertEqual(
            normalized[260:],
            [[row[1], row[2], row[3], False, row[12]] for row in raw_rows[260:]],
        )
        self.assertEqual(
            normalized[0][1].split("<native-oid-for-fk:")[0],
            "RI_ConstraintTrigger_a_",
        )
        self.assertTrue(normalized[1][1].startswith("RI_ConstraintTrigger_c_"))
        self.assertNotEqual(normalized[0][1], normalized[2][1])
        self.assertTrue(normalized[0][4].endswith(raw_rows[0][12].split('" ', 1)[1]))
        self.assertEqual(len(evidence), 260)
        self.assertEqual(evidence[0]["constraintRelation"], "child_0")
        self.assertEqual(evidence[0]["constraintDefinition"], constraint_rows[0][3])

        renumbered = copy.deepcopy(raw_rows)
        for index, row in enumerate(renumbered[:260]):
            new_trigger_oid = str(int(row[0]) + 300000)
            row[0] = new_trigger_oid
            row[2] = f"RI_ConstraintTrigger_{row[2].split('_')[-2]}_{new_trigger_oid}"
            row[5] = str(int(row[5]) + 60000)
            row[6] = str(int(row[6]) + 60000)
            old_quoted = f'"{raw_rows[index][2]}"'
            new_quoted = f'"{row[2]}"'
            row[12] = row[12].replace(old_quoted, new_quoted, 1)
        renumbered_snapshot, renumbered_evidence = (
            MEASURER._normalize_internal_trigger_rows(renumbered, constraint_rows)
        )
        self.assertEqual(renumbered_snapshot, normalized)
        self.assertNotEqual(renumbered_evidence, evidence)

        for mutate in (
            lambda rows: rows.pop(),
            lambda rows: rows.__setitem__(1, rows[0]),
            lambda rows: rows.__setitem__(0, [str(int(rows[0][0]) + 1), *rows[0][1:]]),
            lambda rows: rows[0].__setitem__(2, "RI_ConstraintTrigger_c_1"),
            lambda rows: rows.__setitem__(0, [*rows[0][:5], "999999", *rows[0][6:]]),
            lambda rows: rows.__setitem__(0, [*rows[0][:7], "foreign", *rows[0][8:]]),
            lambda rows: rows.__setitem__(0, [*rows[0][:10], "public", *rows[0][11:]]),
            lambda rows: rows.__setitem__(
                0, [*rows[0][:11], rows[0][11] + " altered-fk", rows[0][12]]
            ),
            lambda rows: rows.__setitem__(
                0, [*rows[0][:12], rows[0][12].replace('"RI_', '"other_')]
            ),
        ):
            changed = copy.deepcopy(raw_rows)
            mutate(changed)
            with self.assertRaises((RuntimeError, ValueError)):
                MEASURER._normalize_internal_trigger_rows(changed, constraint_rows)

        for mutate in (
            lambda rows: rows.pop(),
            lambda rows: rows.append(copy.deepcopy(rows[0])),
            lambda rows: rows[0].__setitem__("position", 322),
        ):
            changed = copy.deepcopy(evidence)
            mutate(changed)
            with self.assertRaises(ValueError):
                MEASURER._validate_internal_trigger_evidence(changed)

        changed_constraints = copy.deepcopy(constraint_rows)
        changed_constraints[0][3] += " changed"
        with self.assertRaisesRegex(RuntimeError, "foreign-key constraint"):
            MEASURER._normalize_internal_trigger_rows(raw_rows, changed_constraints)

        changed_raw = copy.deepcopy(raw_rows)
        changed_raw[-1][2] = "changed_noninternal_name"
        changed_normalized, changed_evidence = (
            MEASURER._normalize_internal_trigger_rows(changed_raw, constraint_rows)
        )
        self.assertEqual(changed_normalized[-1][1], "changed_noninternal_name")
        self.assertEqual(changed_evidence, evidence)

    def test_actual_snapshot_accepts_json_oid_text_and_rejects_numeric_or_mismatch(
        self,
    ):
        from uuid import UUID

        timestamp = "2026-10-23T12:00:00+00:00"
        secret = bytes(range(32))

        class Result:
            def __init__(self, rows):
                self.rows = rows

            def fetchall(self):
                return self.rows

            def fetchone(self):
                return self.rows[0] if self.rows else None

        class Connection:
            def __init__(
                self,
                owner_json_oid: str | int = "41",
                registrar_json_oid: str | int = "73",
                role_rows=None,
            ):
                self.owner_json_oid = owner_json_oid
                self.registrar_json_oid = registrar_json_oid
                self.role_rows = role_rows or [
                    ("41", MEASURER.OWNER_ROLE),
                    ("73", MEASURER.CLIENT_ROLE),
                ]
                (
                    self.raw_trigger_rows,
                    self.constraint_rows,
                    _,
                    _,
                ) = trigger_fixture()

            def execute(self, query, *args, **kwargs):
                text = query if isinstance(query, str) else query.as_string(None)
                if "SELECT c.relname::text" in text and "relkind IN ('r','p')" in text:
                    return Result(
                        [
                            ("catalog_runtime_installation",),
                            ("reader_catalog_validator_secret",),
                            ("schema_rev",),
                        ]
                    )
                if "SELECT oid::text,rolname::text FROM pg_catalog.pg_roles" in text:
                    return Result(self.role_rows)
                if "SELECT owner_oid::text,registrar_oid::text" in text:
                    return Result([("41", "73")])
                if "pg_catalog.encode(secret,'hex')" in text:
                    return Result([(secret.hex(), 32)])
                if (
                    "SELECT COALESCE(c.relname::text,''),con.conname::text,con.contype::text"
                    in text
                ):
                    return Result(self.constraint_rows)
                if "SELECT t.oid::text,c.relname::text,t.tgname::text" in text:
                    self.assert_trigger_join(text)
                    return Result(self.raw_trigger_rows)
                if "to_jsonb(row_value)" in text:
                    if "catalog_runtime_installation" in text:
                        row = {
                            "singleton": True,
                            "installation_id": str(UUID(int=1)),
                            "source_epoch": str(UUID(int=2)),
                            "genesis_at": timestamp,
                            "owner_oid": self.owner_json_oid,
                            "registrar_oid": self.registrar_json_oid,
                        }
                    elif "schema_rev" in text:
                        row = {"rev": 0, "accepted_at": timestamp}
                    else:
                        row = {"secret": "\\x" + secret.hex()}
                    return Result([(json.dumps(row),)])
                if "to_jsonb(accepted_at)" in text:
                    return Result([(json.dumps(timestamp),)])
                if "relkind='S'" in text:
                    return Result([])
                return Result([])

            def assert_trigger_join(self, text):
                if (
                    "con.oid=t.tgconstraint AND con.contype='f'" not in text
                    or "conrel.oid=con.conrelid" not in text
                    or "con_ns.oid=conrel.relnamespace" not in text
                    or "pg_get_constraintdef(con.oid,true)" not in text
                ):
                    raise AssertionError(
                        "Trigger query omitted native FK identity joins"
                    )

        snapshot, evidence = MEASURER._installation_snapshot(
            Connection(),
            runtime_sql_sha256=MEASURER.RUNTIME_SQL_SHA256,
            native_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
        )
        MEASURER._validate_snapshot_normalization(snapshot, evidence)
        self.assertEqual(
            evidence["installationIdentity"]["installationId"], str(UUID(int=1))
        )
        self.assertEqual(evidence["schemaRevision"]["acceptedAt"], timestamp)
        self.assertEqual(evidence["nativeRoleBindings"]["owner"]["oid"], "41")
        self.assertNotIn(secret.hex(), json.dumps(evidence))
        self.assertEqual(len(evidence["internalTriggers"]), 260)
        self.assertEqual(len(snapshot["triggers"]), 322)
        self.assertEqual(sum(row[3] is True for row in snapshot["triggers"]), 260)
        for owner_oid, registrar_oid, roles in (
            (41, "73", None),
            ("073", "41", None),
            ("41", "73", [("41", "not_owner"), ("73", MEASURER.CLIENT_ROLE)]),
        ):
            with (
                self.subTest(owner_oid=owner_oid, registrar_oid=registrar_oid),
                self.assertRaises(RuntimeError),
            ):
                MEASURER._installation_snapshot(
                    Connection(owner_oid, registrar_oid, roles),
                    runtime_sql_sha256=MEASURER.RUNTIME_SQL_SHA256,
                    native_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
                )

    def test_public49_may_lack_batch_helper_only_after_exact_wheel_binding(self):
        missing = ModuleNotFoundError("missing helper")
        missing.name = "truss._installation_sql_batch"
        package = {"moduleSha256": {"truss._installation_sql_batch": None}}
        binding = {
            "wheelSha256": MEASURER.BASELINE_WHEEL_SHA256,
            "distributionVersion": MEASURER.BASELINE_VERSION,
            "payloadMembersEqual": True,
        }
        with patch.object(MEASURER.importlib, "import_module", side_effect=missing):
            self.assertIsNone(
                MEASURER._load_ordered_ddl_module("baseline", package, binding)
            )
            with self.assertRaisesRegex(RuntimeError, "required for this phase"):
                MEASURER._load_ordered_ddl_module("candidate", package, binding)
            with self.assertRaisesRegex(RuntimeError, "required for this phase"):
                MEASURER._load_ordered_ddl_module("baseline", package, None)
        dependency_error = ModuleNotFoundError("missing dependency")
        dependency_error.name = "truss.some_dependency"
        with (
            patch.object(
                MEASURER.importlib, "import_module", side_effect=dependency_error
            ),
            self.assertRaises(ModuleNotFoundError) as raised,
        ):
            MEASURER._load_ordered_ddl_module("baseline", package, binding)
        self.assertIs(raised.exception, dependency_error)
        with (
            patch.object(
                MEASURER.importlib,
                "import_module",
                return_value=SimpleNamespace(),
            ),
            self.assertRaisesRegex(TypeError, "helper API is unavailable"),
        ):
            MEASURER._load_ordered_ddl_module("candidate", package, binding)
        helper_module = SimpleNamespace(execute_ordered_ddl=lambda cursor, units: None)
        with patch.object(
            MEASURER.importlib, "import_module", return_value=helper_module
        ):
            self.assertIs(
                MEASURER._load_ordered_ddl_module("candidate", package, binding),
                helper_module,
            )
            with self.assertRaisesRegex(RuntimeError, "unexpectedly contains"):
                MEASURER._load_ordered_ddl_module("baseline", package, binding)

    def test_validator_secret_evidence_is_closed_and_source_bound(self):
        valid = {
            "status": "validated",
            "table": "truss.reader_catalog_validator_secret",
            "column": "secret",
            "rowCount": 1,
            "secretBytes": 32,
            "secretSha256": "a" * 64,
            "runtimeSqlSha256": MEASURER.RUNTIME_SQL_SHA256,
            "nativeManifestSha256": MEASURER.NATIVE_MANIFEST_SHA256,
        }
        result = MEASURER._validator_secret_evidence(
            valid,
            runtime_sql_sha256=MEASURER.RUNTIME_SQL_SHA256,
            native_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
        )
        self.assertEqual(result, valid)
        for field, value in (
            ("rowCount", True),
            ("secretBytes", 31),
            ("secretSha256", "A" * 64),
            ("runtimeSqlSha256", "0" * 64),
            ("nativeManifestSha256", "0" * 64),
            ("secretHex", "ab" * 32),
        ):
            changed = dict(valid)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                MEASURER._validator_secret_evidence(
                    changed,
                    runtime_sql_sha256=MEASURER.RUNTIME_SQL_SHA256,
                    native_manifest_sha256=MEASURER.NATIVE_MANIFEST_SHA256,
                )

    def test_snapshot_failure_location_exposes_only_safe_frame_coordinates(self):
        try:
            MEASURER._canonical_oid_text("0")
        except RuntimeError as error:
            location = MEASURER._safe_traceback_location(error)
        else:
            self.fail("Expected invalid OID refusal")
        self.assertEqual(set(location), {"basename", "function", "line"})
        self.assertEqual(location["basename"], "measure-installer-submissions.py")
        self.assertEqual(location["function"], "_canonical_oid_text")
        self.assertIs(type(location["line"]), int)


if __name__ == "__main__":
    unittest.main()
