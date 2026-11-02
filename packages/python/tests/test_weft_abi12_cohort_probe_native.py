# SPDX-License-Identifier: MIT OR Apache-2.0
"""Authentic public54/Weft051 ABI1.2 capture companion for the single cursor test."""
from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import patch

import weft
from truss._query_cache import compile_response as original_compile_response
import truss._query_runtime as query_runtime
import test_query_stream_abi12_native as original_fixture
from test_query_stream_abi12_native import QueryStreamABI12Tests


class WeftABI12CohortProbeNativeTests(QueryStreamABI12Tests):
    # Keep only the requested original three-row cursor regression and capture.
    for _name in tuple(name for name in dir(QueryStreamABI12Tests) if name.startswith("test_")):
        if _name != "test_actual_selected_cursor_decodes_all_batches_and_descriptors":
            locals()[_name] = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

    @staticmethod
    def _payload(text):
        raw = text.encode("utf-8", errors="strict")
        return {"utf8": text, "base64": base64.b64encode(raw).decode("ascii"),
                "sha256": hashlib.sha256(raw).hexdigest(), "byteLength": len(raw)}

    def test_capture_authentic_request_and_old_cohort_response(self):
        destination = os.environ.get("TRUSS_T4A_CAPTURE_PATH")
        self.assertTrue(destination, "TRUSS_T4A_CAPTURE_PATH is required")
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
