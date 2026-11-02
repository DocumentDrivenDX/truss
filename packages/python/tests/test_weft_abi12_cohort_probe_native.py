# SPDX-License-Identifier: MIT OR Apache-2.0
"""Authentic public54/Weft051 ABI1.2 capture companion for the single cursor test."""
from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
import zipfile
from types import SimpleNamespace
from unittest.mock import patch

import weft
from truss._query_cache import compile_response as original_compile_response
import truss._query_runtime as query_runtime
import test_query_stream_abi12_native as original_fixture
from test_query_stream_abi12_native import QueryStreamABI12Tests

PROBE_PATH = Path(__file__).resolve().parents[3] / "scripts/probe-weft-abi12-cohort.py"
_spec = importlib.util.spec_from_file_location("truss_abi12_probe", PROBE_PATH)
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)


class WeftABI12CohortProbeNativeTests(QueryStreamABI12Tests):
    # Keep only the requested original three-row cursor regression and capture.
    for _name in tuple(name for name in dir(QueryStreamABI12Tests) if name.startswith("test_")):
        if _name != "test_actual_selected_cursor_decodes_all_batches_and_descriptors":
            locals()[_name] = None

    @classmethod
    def setUpClass(cls):
        import truss
        from pathlib import Path
        source_root = Path(__file__).resolve().parents[1] / "src"
        if importlib.metadata.version("umf-truss") != "0.0.54":
            raise AssertionError("Installed public Truss 0.0.54 required")
        if Path(truss.__file__).resolve().is_relative_to(source_root.resolve()):
            raise AssertionError("Installed public Truss wheel required; source checkout import refused")
        if importlib.metadata.version("weft-sql") != "0.4.51" or weft.__version__ != "0.4.51":
            raise AssertionError("Original Weft 0.4.51 cohort required")
        if importlib.metadata.version("pgserver-pg18") != "18.6.1":
            raise AssertionError("Checksum-verified pgserver-pg18==18.6.1 required")
        super().setUpClass()
        cls.original_postmaster_pid = int((cls.runtime.directory / "postmaster.pid").read_text().splitlines()[0])
        if cls.original_postmaster_pid <= 0:
            raise AssertionError("Original running postmaster PID required")

    @classmethod
    def cleanup(cls):
        """Override the fixture's deletion to prove stop while data still exists."""
        proof = {"confirmed": False, "runtimeDirectory": str(cls.runtime.directory),
                 "dataDeleted": False}
        try:
            pid = getattr(cls, "original_postmaster_pid", None)
            stop_error = None
            try:
                cls.runtime.__exit__(None, None, None)
            except Exception as error:
                stop_error = f"{type(error).__name__}: {error}"
            if pid is None:
                raise RuntimeError("Original postmaster PID was never observed; retain owned data")
            pg_ctl = cls.runtime.psql_path.with_name("pg_ctl")
            proof.update(probe.confirm_native_stop(pg_ctl, cls.runtime.directory, pid))
            if stop_error is not None:
                proof["stopError"] = stop_error
                proof["confirmed"] = False
            if not proof["confirmed"]:
                raise RuntimeError("Native shutdown uncertain; retain owned data")
            # pg_ctl status==3 and original PID absence were observed above,
            # before deleting the data directory.
            shutil.rmtree(cls.root)
            proof["dataDeleted"] = not cls.root.exists()
        except Exception as error:
            proof["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            cls.cleanup_proof = proof
            output = Path(os.environ["TRUSS_T4A_CAPTURE_PATH"])
            probe._write_json(output.with_name(output.name + ".cleanup.json"), proof)

    @staticmethod
    def _payload(text):
        raw = text.encode("utf-8", errors="strict")
        return {"utf8": text, "base64": base64.b64encode(raw).decode("ascii"),
                "sha256": hashlib.sha256(raw).hexdigest(), "byteLength": len(raw)}

    def test_capture_authentic_request_and_old_cohort_response(self):
        destination = os.environ.get("TRUSS_T4A_CAPTURE_PATH")
        self.assertTrue(destination, "TRUSS_T4A_CAPTURE_PATH is required")
        probe.refuse_existing_output(Path(destination).absolute())
        compiler_calls = []
        page_program_calls = []
        checker_calls = []

        def observe_compile_response(compiler, request, page_size=None, after=None):
            entrypoint = getattr(compiler, "__qualname__", getattr(compiler, "__name__", type(compiler).__name__))
            module = getattr(compiler, "__module__", None)

            def forwarding(*original_args):
                if not original_args or type(original_args[0]) is not str:
                    raise AssertionError("Original owner compiler request string required")
                exact_request = original_args[0]
                response = compiler(*original_args)
                if type(response) is not str:
                    raise AssertionError("Original owner compiler response text required")
                compiler_calls.append({
                    "entrypoint": {"module": module, "qualname": entrypoint},
                    "arguments": [self._payload(value) if type(value) is str else value for value in original_args],
                    "request": self._payload(exact_request),
                    "pageSize": page_size,
                    "after": after,
                    "response": self._payload(response),
                })
                return response

            return original_compile_response(forwarding, request, page_size, after)

        original_engine_page = weft.compile_engine_page_json
        original_engine_page_checker = weft.check_engine_page_json

        def observe_engine_page(engine_input):
            if type(engine_input) is not str:
                raise AssertionError("Original engine-page input string required")
            program = original_engine_page(engine_input)
            if type(program) is not str:
                raise AssertionError("Original engine-page program string required")
            page_program_calls.append({"input": self._payload(engine_input), "program": self._payload(program)})
            return program

        def observe_engine_page_checker(program, current_request, after_json):
            result = original_engine_page_checker(program, current_request, after_json)
            checker_calls.append({
                "program": self._payload(program),
                "currentRequest": self._payload(current_request),
                "afterJson": self._payload(after_json),
                "result": self._payload(result),
            })
            return result

        with patch.object(query_runtime, "compile_response", side_effect=observe_compile_response), \
             patch.object(weft, "compile_engine_page_json", side_effect=observe_engine_page), \
             patch.object(weft, "check_engine_page_json", side_effect=observe_engine_page_checker):
            connection, host, assembly, tx, program = self.original()
            seen = []
            handle = assembly.query_stream_open_in_transaction(
                tx, engine_program=program, parameters={"wanted": "same"})

            def validate(rows):
                seen.append(rows.column_descriptors)
                return rows.rows

            first = assembly.query_stream_fetch_in_transaction(tx, handle, count=2, validate=validate)
            second = assembly.query_stream_fetch_in_transaction(tx, handle, count=2, validate=validate)
            self.assertEqual(first.items + second.items, (("0",), ("1",), ("2",)))
            self.assertFalse(first.exhausted)
            self.assertTrue(second.exhausted)
            self.assertTrue(all(len(columns) == 1 and columns[0].output_name == "A-label" for columns in seen))
            assembly.query_stream_close_in_transaction(tx, handle)
            # The cursor path uses the owner export API. Exercise the ordinary
            # page checker explicitly with the unchanged captured request and
            # its actual continuation argument; no native binding is authored.
            self.assertEqual(len(compiler_calls), 1)
            old_check = weft.check_engine_page_json(
                program, compiler_calls[0]["request"]["utf8"], json.dumps(compiler_calls[0]["after"]))
            self.assertEqual(json.loads(old_check)["status"], "compiled", old_check)

        self.assertEqual(len(compiler_calls), 1)
        self.assertEqual(len(page_program_calls), 1)
        self.assertGreaterEqual(len(checker_calls), 1)
        call = compiler_calls[0]
        self.assertEqual(call["entrypoint"]["qualname"], "compile_truss_runtime_page_json")
        self.assertEqual(call["pageSize"], 2)
        self.assertIsNone(call["after"])
        request_object = json.loads(call["request"]["utf8"])
        binding_json = request_object["target"]["bindingJson"]
        engine_page_input = page_program_calls[0]["input"]["utf8"]
        engine_page_value = json.loads(engine_page_input)
        self.assertEqual(engine_page_value["request"], request_object)
        self.assertEqual(engine_page_value["pageSize"], 2)

        import truss
        from truss._current_query_originals import _CONSUMER_COHORTS
        native_path = Path(weft.weft.__file__).resolve()
        native_sha = hashlib.sha256(native_path.read_bytes()).hexdigest()
        cohort = [row for row in _CONSUMER_COHORTS if row["weftModuleSha256"] == native_sha]
        self.assertEqual(len(cohort), 1, "Installed Weft native module must match one frozen original cohort")
        wheel_inputs = json.loads(os.environ["TRUSS_T4A_PUBLIC_WHEELS"])
        self.assertEqual(wheel_inputs["umfTruss054"]["sha256"],
                         "4aebc56e92fdbde6714d9b811860707d2ffc9b0edbc63cc91e9dc3488c042b52")
        self.assertEqual(wheel_inputs["weftSql051"]["sha256"], cohort[0]["weftWheelSha256"])
        test_source = Path(original_fixture.__file__).resolve()
        root = Path(__file__).resolve().parents[3]
        source_commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"], check=True, text=True,
            stdout=subprocess.PIPE).stdout.strip()
        result = {
            "schema": "truss.weft-abi12-native-capture/0.1",
            "scope": "Authentic installed-public54 request capture plus ordinary ABI1.2 three-row cursor execution; no 0.4.56 claim",
            "sourceCommit": source_commit,
            "python": __import__("sys").version,
            "truss": {"distribution": "umf-truss", "version": importlib.metadata.version("umf-truss"),
                      "module": str(Path(truss.__file__).resolve()),
                      "publicWheelSha256": "4aebc56e92fdbde6714d9b811860707d2ffc9b0edbc63cc91e9dc3488c042b52"},
            "weft": {"distribution": "weft-sql", "version": importlib.metadata.version("weft-sql"),
                     "nativeModule": str(native_path), "nativeModuleSha256": native_sha,
                     "wheelSha256": cohort[0]["weftWheelSha256"]},
            "nativeRuntime": {"distribution": "pgserver-pg18", "version": importlib.metadata.version("pgserver-pg18")},
            "verifiedWheelInputs": wheel_inputs,
            "fixtureSources": [
                {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                for path in (test_source, Path(__file__).resolve(), Path(__file__).resolve().parents[3] / "scripts/probe-weft-abi12-cohort.py",
                             Path(__file__).resolve().parents[1] / "tests/test_compiled_query_native.py",
                             Path(__file__).resolve().parents[1] / "tests/test_group_create_native.py",
                             Path(__file__).resolve().parents[1] / "tests/test_catalog_runtime_native.py",
                             Path(__file__).resolve().parents[1] / "src/truss/local_runtime.py",
                             Path(__file__).resolve().parents[1] / "src/truss/_query_runtime.py")
            ],
            "compilerCall": {**call, "bindingJson": self._payload(binding_json)},
            "enginePage": {**page_program_calls[0],
                           "checkerCall": checker_calls[0]},
            "assertions": {"rows": [["0"], ["1"], ["2"]], "pageSize": 2,
                           "firstPageExhausted": False, "secondPageExhausted": True,
                           "column": "A-label"},
        }
        path = Path(destination).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)


class ProbeControlTests(unittest.TestCase):
    """Pure corruption and custody controls; these never start PostgreSQL."""

    def test_each_payload_representation_must_match(self):
        payload = probe.payload_record("exact λ bytes\n")
        self.assertEqual(probe.validate_payloads({"nested": [payload], "source": {"sha256": "identity"}}), 1)
        for key, value in (("utf8", "changed"), ("base64", "%%%"), ("sha256", "0" * 64),
                           ("byteLength", True), ("byteLength", payload["byteLength"] + 1)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                probe.validate_payloads({**payload, key: value})
        for key in payload:
            with self.subTest(missing=key), self.assertRaises(ValueError):
                probe.validate_payloads({k: v for k, v in payload.items() if k != key})

    def test_existing_outputs_refuse_before_capture_or_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.json"
            for suffix in ("", ".tmp", ".run.json", ".cleanup.json"):
                existing = Path(str(path) + suffix)
                existing.write_text("retained evidence")
                with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                    probe.refuse_existing_output(path)
                for operation in (probe.capture, probe.replay):
                    with self.subTest(operation=operation.__name__, suffix=suffix), self.assertRaises(ValueError):
                        operation(SimpleNamespace(output=path))
                self.assertEqual(existing.read_text(), "retained evidence")
                existing.unlink()
            path.symlink_to(Path(directory) / "absent-target")
            for operation in (probe.capture, probe.replay):
                with self.subTest(operation=operation.__name__, dangling_symlink=True), self.assertRaises(ValueError):
                    operation(SimpleNamespace(output=path))

    def test_replay_rejects_corrupt_bytes_before_candidate_api_import(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "input.json"
            malformed = probe.payload_record("retained original bytes")
            malformed["sha256"] = "0" * 64
            capture_path.write_text(json.dumps({"nested": {"raw": malformed}}))
            with self.assertRaisesRegex(ValueError, "Payload bytes/hash/length differ"):
                probe.replay(SimpleNamespace(capture=capture_path, output=Path(directory) / "result.json"))
            capture_path.write_text('{"same":"first","same":"second"}')
            with self.assertRaisesRegex(ValueError, "Duplicate capture JSON member"):
                probe.replay(SimpleNamespace(capture=capture_path, output=Path(directory) / "result.json"))

    def test_stop_requires_status_three_and_original_pid_absence(self):
        for pid in (0, -12345, True, None):
            with self.subTest(pid=pid), self.assertRaises(ValueError):
                probe.confirm_native_stop(Path("pg_ctl"), Path("owned-data"), pid)
        for status, absent, expected in ((3, True, True), (0, True, False), (1, True, False),
                                         (4, True, False), (3, False, False)):
            completed = subprocess.CompletedProcess([], status, "status output", "status error")
            with self.subTest(status=status, absent=absent), \
                 patch.object(probe.subprocess, "run", return_value=completed), \
                 patch.object(probe.os, "kill", side_effect=ProcessLookupError() if absent else None):
                proof = probe.confirm_native_stop(Path("pg_ctl"), Path("owned-data"), 12345)
                self.assertEqual(proof["confirmed"], expected)

    def test_candidate_wheel_checksums_and_installed_module_must_agree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel, sums, installed = root / "umf_weft-0.4.56-test.whl", root / "SHA256SUMS", root / "weft.so"
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr("weft/weft.abi3.so", b"native wheel module")
            sums.write_text(f"{probe.sha256(wheel.read_bytes())}  {wheel.name}\n")
            installed.write_bytes(b"native wheel module")
            self.assertEqual(probe.verify_wheel_module(wheel, sums, installed)["nativeModuleSha256"],
                             probe.sha256(installed.read_bytes()))
            installed.write_bytes(b"other installed module")
            with self.assertRaises(ValueError):
                probe.verify_wheel_module(wheel, sums, installed)
            sums.write_text(f"{'0' * 64}  {wheel.name}\n")
            with self.assertRaises(ValueError):
                probe.verify_wheel_module(wheel, sums, installed)

    def test_cleanup_retains_data_when_stop_proof_is_uncertain(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "owned-cluster"
            root.mkdir()
            runtime = SimpleNamespace(directory=root / "data", psql_path=Path("psql"),
                                      __exit__=lambda *args: None)
            owner = SimpleNamespace(runtime=runtime, root=root, original_postmaster_pid=12345)
            output = Path(directory) / "capture.json"
            with patch.dict(os.environ, {"TRUSS_T4A_CAPTURE_PATH": str(output)}), \
                 patch.object(probe, "confirm_native_stop", return_value={"confirmed": False, "pgCtlStatus": 1}):
                with self.assertRaises(RuntimeError):
                    WeftABI12CohortProbeNativeTests.cleanup.__func__(owner)
            self.assertTrue(root.exists())
            self.assertFalse(json.loads(Path(str(output) + ".cleanup.json").read_text())["dataDeleted"])

    def test_cleanup_observes_stop_before_deleting_owned_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "owned-cluster"
            root.mkdir()
            runtime = SimpleNamespace(directory=root / "data", psql_path=Path("psql"),
                                      __exit__=lambda *args: None)
            owner = SimpleNamespace(runtime=runtime, root=root, original_postmaster_pid=12345)
            def proof_before_delete(*args):
                self.assertTrue(root.exists())
                return {"confirmed": True, "pgCtlStatus": 3, "originalPostmasterPidAbsent": True}
            output = Path(directory) / "capture.json"
            with patch.dict(os.environ, {"TRUSS_T4A_CAPTURE_PATH": str(output)}), \
                 patch.object(probe, "confirm_native_stop", side_effect=proof_before_delete):
                WeftABI12CohortProbeNativeTests.cleanup.__func__(owner)
            self.assertFalse(root.exists())
            self.assertTrue(owner.cleanup_proof["dataDeleted"])
