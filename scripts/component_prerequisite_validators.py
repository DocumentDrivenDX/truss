"""Pure validators for the current Core C1 component-result roster.

These functions inspect already-produced original result objects and companions.
They do not import owner packages or execute bundled validator code. The
result bundle must be authenticated by the caller against its admitted paths,
source file hashes, run and artifact identity before validation.
"""
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from typing import Any

FACTORY51 = "core.c1.factory-51/1"
EARLY18 = "core.c1.early-controls-18/1"
RUST477 = "core.c1.rust-census-477/1"
PYTHON31 = "core.c1.python-cases-31/1"
SAGA19 = "core.c1.saga-19/1"
RESOURCES9 = "core.c1.resources-nine/1"
REQUIRED = frozenset((FACTORY51, EARLY18, RUST477, PYTHON31, SAGA19, RESOURCES9))
CORE_COST_PROFILE = "umf.private-retained-cost-gate/1"
FACTORY_PROFILE = "umf.private-installed-factory-cost/1"
FACTORY_INPUT = "installed-canonical/1"
COST_MEMBERS = frozenset((
    "measurement.json", "public-controls.xml",
    "identity-cost-before.json", "identity-cost-after.json",
    "installed-record-cost-before.json", "installed-record-cost-after.json",
))
RESOURCE_NAMES = (
    "coreSchema", "referenceSchema", "packageSchema", "constraints", "domainPolicy",
    "tablesPackage", "actionsPackage", "bindingPackage", "stableBindingPackage",
)
# These four literal calls are already made by Weft's pinned installed-wheel
# producer. They are outcomes within its existing SDK42 report, not a new
# report schema or four invented API names.
WEFT_ORIGINAL_CHECK_CALLS = {
    "read-check": "compiled",
    "page-check": "compiled",
    "read-context-drift": "blocked",
    "page-context-drift": "blocked",
}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


class Refusal(ValueError):
    """Missing, failed, unknown, malformed, or misbound original result."""


def _need(ok: bool, message: str) -> None:
    if not ok:
        raise Refusal(message)


def _sha(value: Any, label: str) -> str:
    _need(type(value) is str and SHA256.fullmatch(value) is not None and set(value) != {"0"},
          f"{label}: nonzero SHA-256 required")
    return value


def _commit(value: Any, label: str) -> str:
    _need(type(value) is str and COMMIT.fullmatch(value) is not None and set(value) != {"0"},
          f"{label}: full source commit required")
    return value


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _same(actual: Any, expected: Any, label: str) -> None:
    _need(actual == expected, f"{label}: original result differs")


def _expected(expected: Any) -> dict[str, Any]:
    fields = {
        "source", "controllerSource", "wheelSha256", "nativeSha256", "censusSha256",
        "run", "attempt", "currentInputIdentity", "resourceManifest", "factoryPairs",
        "earlyControls", "rustCases", "pythonGroups", "sagaCorpusSha256", "sagaInputs",
    }
    _need(type(expected) is dict and set(expected) == fields, "Closed current C1 source/result binding required")
    for name in ("source", "controllerSource"):
        _commit(expected[name], "C1 " + name)
    for name in ("wheelSha256", "nativeSha256", "censusSha256", "sagaCorpusSha256"):
        _sha(expected[name], "C1 " + name)
    _need(type(expected["run"]) is str and expected["run"].isdecimal() and int(expected["run"]) > 0,
          "Original positive C1 run ID required")
    _need(type(expected["attempt"]) is str and expected["attempt"].isdecimal() and int(expected["attempt"]) > 0, "Original positive C1 attempt required")
    identity = expected["currentInputIdentity"]
    _need(type(identity) is dict and identity.get("resourceFixtureSHA256") is not None,
          "Authenticated current input identity required")
    _sha(identity["resourceFixtureSHA256"], "Current resource fixture")
    resources = expected["resourceManifest"]
    _need(type(resources) is dict and set(resources) == {"profile", "inputProfile", "resources"}
          and resources["profile"] == "umf.codegen.installed-source-manifest/1"
          and resources["inputProfile"] == FACTORY_INPUT and type(resources["resources"]) is list
          and len(resources["resources"]) == 9, "Exact current nine-resource source manifest required")
    _need([row.get("name") for row in resources["resources"]] == list(RESOURCE_NAMES),
          "Current nine-resource names/order differ")
    for row in resources["resources"]:
        _need(type(row) is dict and set(row) == {"name", "path", "bytes", "sha256"}
              and type(row["path"]) is str and row["path"] and type(row["bytes"]) is int
              and 0 < row["bytes"] <= 2**53 - 1, "Malformed current resource source binding")
        _sha(row["sha256"], "Current resource " + row["name"])
    pairs = expected["factoryPairs"]
    _need(type(pairs) is list and len(pairs) == 51, "Exact source-derived 51 factory oracle pairs required")
    _need(all(type(row) is dict and set(row) == {"case", "carrier", "resultSHA256"}
              and type(row["case"]) is str and row["carrier"] in ("dispatcher", "list", "tuple")
              for row in pairs), "Malformed C1 factory oracle roster")
    _need(len({(r["case"], r["carrier"]) for r in pairs}) == 51, "Duplicate C1 factory oracle pair")
    for row in pairs:
        _sha(row["resultSHA256"], "C1 oracle result")
    _need(type(expected["earlyControls"]) is list and len(expected["earlyControls"]) == 18
          and len(set(expected["earlyControls"])) == 18, "Exact disjoint source-derived early18 roster required")
    rust = expected["rustCases"]
    _need(type(rust) is list and len(rust) == 477, "Exact named C1 Rust477 source census required")
    _need(all(type(r) is dict and set(r) == {"package", "target", "name"}
              and all(type(r[k]) is str and r[k] for k in r) for r in rust), "Malformed Rust case identity")
    _need(len({(r["package"], r["target"], r["name"]) for r in rust}) == 477, "Duplicate Rust case identity")
    groups = expected["pythonGroups"]
    _need(type(groups) is list and groups and all(type(g) is dict and set(g) == {"group", "cases"}
          and type(g["group"]) is str and type(g["cases"]) is list and g["cases"] for g in groups),
          "Exact current named Python groups required")
    cases = [case for group in groups for case in group["cases"]]
    _need(len(cases) == 31 and len(set(cases)) == 31, "Exact later31 named Python cases required")
    _need(type(expected["sagaInputs"]) is dict and expected["sagaInputs"], "Original Saga input hash roster required")
    for name, digest in expected["sagaInputs"].items():
        _need(type(name) is str and name and ".." not in name.split("/"), "Unsafe Saga input path")
        _sha(digest, "Saga input " + name)
    return expected


def _cost_receipt(value: Any, expected: dict[str, Any]) -> dict[str, Any]:
    _need(type(value) is dict, "Original same-job C1 cost receipt required")
    for key, want in (("profile", CORE_COST_PROFILE), ("inputProfile", FACTORY_INPUT),
                      ("artifactSource", expected["source"]), ("controllerSource", expected["controllerSource"]),
                      ("wheelSHA256", expected["wheelSha256"]), ("nativeSHA256", expected["nativeSha256"]),
                      ("run", expected["run"]), ("attempt", expected["attempt"]),
                      ("censusSHA256", expected["censusSha256"]), ("currentInputIdentity", expected["currentInputIdentity"]),
                      ("status", "cost-gate-passed")):
        _same(value.get(key), want, "C1 cost " + key)
    _need(value.get("fullyQualified") is False and value.get("requiredQualificationPassed") is False
          and value.get("publishable") is False and value.get("readyForEnrollment") is False,
          "Cost receipt cannot claim semantic/release qualification")
    _need(all(value.get(k) is True for k in ("identityBeforePassed", "identityAfterPassed", "publicProbePassed",
          "publicControlsPassed", "expensiveTestCompilationAdmitted")), "C1 cost gate did not complete all original checks")
    _need(value.get("publicControlsExecution") == "COMPLETED", "Original early controls did not execute")
    members = value.get("members")
    _need(type(members) is dict and set(members) == COST_MEMBERS, "Closed original cost member roster required")
    for name, row in members.items():
        _need(type(row) is dict and set(row) == {"bytes", "sha256"} and type(row["bytes"]) is int
              and row["bytes"] > 0, "Malformed cost member record: " + name)
        _sha(row["sha256"], "Cost member " + name)
    return value


def _junit(raw: Any, selectors: list[str], label: str) -> None:
    _need(type(raw) is bytes, label + ": original JUnit bytes required")
    try:
        cases = list(ET.fromstring(raw).iter("testcase"))
    except ET.ParseError as error:
        raise Refusal(label + ": malformed original JUnit XML") from error
    expected = []
    for selector in selectors:
        parts = selector.split("::")
        _need(len(parts) in (2, 3), label + ": selector must name a method")
        path, *nodes = parts
        expected.append((".".join([path.removesuffix(".py").replace("/", "."), *nodes[:-1]]), nodes[-1]))
    actual = [(row.get("classname"), row.get("name")) for row in cases]
    _need(len(actual) == len(set(actual)) and set(actual) == set(expected), label + ": exact named case roster differs")
    _need(not any(row.find(tag) is not None for row in cases for tag in ("failure", "error", "skipped")),
          label + ": failure/error/skip present")


def _factory51(report: Any, expected: dict[str, Any]) -> None:
    _need(type(report) is dict, "Original installed-factory measurement required")
    for key, want in (("profile", FACTORY_PROFILE), ("inputProfile", FACTORY_INPUT), ("status", "cost-complete"),
                      ("actualCandidateSource", expected["source"]), ("wheelSHA256", expected["wheelSha256"]),
                      ("nativeSHA256", expected["nativeSha256"]),
                      ("currentInputIdentity", expected["currentInputIdentity"])):
        _same(report.get(key), want, "Factory measurement " + key)
    _sha(report.get("closureSHA256"), "C1 source closure")
    for key, count in (("maximumWork", 1_000_000), ("inspectionCases", 17), ("inspectionCalls", 51), ("freshConstructors", 51)):
        _need(type(report.get(key)) is int and report[key] == count, "C1 factory count/type differs: " + key)
    _need(report.get("requestCustodyPreserved") is True and report.get("installedFilesUnchanged") is True
          and report.get("publishable") is False and report.get("readyForEnrollment") is False,
          "Factory measurement claimed custody or qualification incorrectly")
    pairs = report.get("pairs")
    wanted = expected["factoryPairs"]
    _need(type(pairs) is list and len(pairs) == 51, "C1 factory pair rows missing")
    _same([(row.get("case"), row.get("carrier")) for row in pairs],
          [(row["case"], row["carrier"]) for row in wanted], "C1 factory pair order")
    for row, oracle in zip(pairs, wanted):
        _same(row.get("resultSHA256"), oracle["resultSHA256"], "C1 factory oracle result")
        _need(row.get("completed") is True, "C1 factory pair incomplete")
        _same(row.get("manifestSHA256"), _digest(_canonical(row.get("sourceManifest"))), "Paid manifest result hash")
        manifest = row.get("sourceManifest")
        _same(manifest, expected["resourceManifest"], "Actual nine-resource manifest")
        _need(all(type(resource["bytes"]) is float for resource in manifest["resources"]),
              "Original current-input manifest byte lengths must retain source wire number types")
        for stage_name in ("constructor", "call", "manifest"):
            stage = row.get(stage_name)
            _need(type(stage) is dict and stage.get("completed") is True and stage.get("workCreated") is True
                  and type(stage.get("maximumWork")) is int and stage["maximumWork"] == 1_000_000
                  and type(stage.get("returnedWork")) is int and type(stage.get("attemptedWork")) is int
                  and 0 <= stage["returnedWork"] == stage["attemptedWork"] <= 1_000_000,
                  "C1 factory lifetime incomplete/over-budget: " + stage_name)


def _early18(bundle: Any, expected: dict[str, Any]) -> None:
    _need(type(bundle) is dict and set(bundle) == {"cost", "xml", "memberBytes"}, "C1 early18 original result bundle required")
    cost = _cost_receipt(bundle["cost"], expected)
    raw = bundle["xml"]
    members = bundle["memberBytes"]
    _need(type(members) is dict and set(members) == COST_MEMBERS, "Original cost-gate member bytes required")
    for name, member in members.items():
        binding = cost["members"][name]
        _need(type(member) is bytes and len(member) == binding["bytes"] and _digest(member) == binding["sha256"],
              "Original cost-gate member bytes/hash differ: " + name)
    _same(members["public-controls.xml"], raw, "Original cost-gate controls bytes")
    for when in ("before", "after"):
        identity = json.loads(members[f"identity-cost-{when}.json"])
        installed = json.loads(members[f"installed-record-cost-{when}.json"])
        _same(identity.get("profile"), "umf.private-retained-installed-identity/1", "Installed identity profile")
        for key, want in (("artifactSource", expected["source"]), ("controllerSource", expected["controllerSource"]),
                          ("wheelSHA256", expected["wheelSha256"])):
            _same(identity.get(key), want, "Installed identity " + key)
        _need(identity.get("distributionOwnershipVerified") is True
              and identity.get("completeWheelAndInstalledRecordVerified") is True,
              "Original installed ownership/RECORD verification incomplete")
        modules = identity.get("loadedModules")
        _need(type(modules) is dict and len(modules) == 4
              and modules.get("umf/_rust_core.abi3.so", {}).get("sha256") == expected["nativeSha256"],
              "Original installed module identity incomplete/misbound")
        _same(installed.get("status"), "passed", "Installed RECORD status")
        _same(installed.get("wheel_sha256"), expected["wheelSha256"], "Installed RECORD wheel")
        _same(installed.get("native_sha256"), expected["nativeSha256"], "Installed RECORD native")
    _same(_digest(raw) if type(raw) is bytes else None, cost["members"]["public-controls.xml"]["sha256"],
          "Original early-controls XML digest")
    _same(len(raw), cost["members"]["public-controls.xml"]["bytes"], "Original early-controls XML size")
    _junit(raw, expected["earlyControls"], "Early18 controls")


def _rust477(bundle: Any, expected: dict[str, Any]) -> None:
    _need(type(bundle) is dict and set(bundle) == {"result", "compiled", "compiledBytes", "caseLogs"}, "C1 original Rust result bundle required")
    result, compiled, raw, logs = bundle["result"], bundle["compiled"], bundle["compiledBytes"], bundle["caseLogs"]
    _need(type(result) is dict and type(compiled) is dict and type(raw) is bytes and type(logs) is dict, "Malformed Rust477 original outputs")
    try:
        _same(json.loads(raw), compiled, "Original compiled-census bytes")
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Refusal("Original compiled-census bytes are not the supplied result object") from error
    _same(result.get("source"), expected["source"], "Rust result source")
    _same(result.get("status"), "passed", "Rust result status")
    _need(type(result.get("cases")) is int and result["cases"] == 477 and result.get("passed") == 477,
          "Rust result must report all 477 selected cases")
    _same(result.get("censusSHA256"), expected["censusSha256"], "Rust census hash")
    _same(result.get("compiledCensusSHA256"), _digest(raw), "Rust compiled-census receipt hash")
    rows = result.get("results")
    _need(type(rows) is list and len(rows) == 477, "Original 477 Rust result rows required")
    identities = [(r.get("package"), r.get("target"), r.get("name")) for r in rows]
    wanted = [(r["package"], r["target"], r["name"]) for r in expected["rustCases"]]
    _need(len(set(identities)) == 477 and set(identities) == set(wanted), "Rust result named case roster differs")
    _need(all(r.get("passed") is True and type(r.get("exit")) is int and r["exit"] == 0 for r in rows),
          "Rust case failed/skipped")
    _need(set(logs) == set(identities), "Original named Rust case logs are incomplete/extra")
    for row, identity in zip(rows, identities):
        log = logs[identity]
        _need(type(log) is bytes and _digest(log) == _sha(row.get("logSHA256"), "Rust case log"),
              "Original named Rust case log hash differs")
        try:
            text = log.decode("utf-8")
        except UnicodeDecodeError as error:
            raise Refusal("Original Rust case log is not UTF-8") from error
        _need("1 passed; 0 failed" in text and "1 ignored" not in text,
              "Original Rust case log does not show exactly a passing nonignored outcome")
    _same(compiled.get("source"), expected["controllerSource"], "Compiled census controller source")
    _same(compiled.get("status"), "authenticated-before-test-execution", "Compiled census status")
    _same(compiled.get("selectedCases"), 477, "Compiled selected case count")
    _same(compiled.get("censusSHA256"), expected["censusSha256"], "Compiled census hash")
    targets = compiled.get("targets")
    _need(type(targets) is list, "Compiled Rust target/readback records missing")
    wanted_by_target = {}
    for row in expected["rustCases"]:
        wanted_by_target.setdefault((row["package"], row["target"]), []).append(row["name"])
    target_map = {}
    for target in targets:
        key = (target.get("package"), target.get("target")) if type(target) is dict else None
        _need(type(target) is dict and key in wanted_by_target and key not in target_map, "Unknown/duplicate compiled Rust target")
        for field in ("executable", "sha256", "listingSHA256"):
            _need(type(target.get(field)) is str and target[field], "Compiled Rust target binding missing: " + field)
        _sha(target["sha256"], "Compiled Rust executable")
        _sha(target["listingSHA256"], "Compiled Rust listing")
        target_map[key] = target.get("caseNames")
    _need(set(target_map) == set(wanted_by_target), "Compiled Rust target roster differs")
    for key, names in wanted_by_target.items():
        actual_names = target_map[key]
        _need(type(actual_names) is list and all(type(name) is str for name in actual_names),
              "Compiled Rust full test listing malformed")
        _need(all(actual_names.count(name) == 1 for name in names),
              "Compiled census selected test missing/duplicated")
        if key[1] == "lib":
            prefixes = {name.rsplit("::", 1)[0] + "::" for name in names}
            selected_modules = {name for name in actual_names if any(name.startswith(prefix) for prefix in prefixes)}
            _need(selected_modules == set(names),
                  "Compiled selected Rust lib module has unapproved cases")
        else:
            _need(set(actual_names) == set(names), "Compiled Rust integration target has unapproved cases")


def _python31(bundle: Any, expected: dict[str, Any]) -> None:
    _need(type(bundle) is dict and set(bundle) == {"aggregate", "xml"}, "C1 Python31 original result bundle required")
    aggregate, xmls = bundle["aggregate"], bundle["xml"]
    _need(type(aggregate) is dict and type(xmls) is dict, "Malformed aggregate/Python XML outputs")
    _same(aggregate.get("profile"), "umf.private-installed-factory-semantics/1", "C1 aggregate profile")
    _same(aggregate.get("inputProfile"), FACTORY_INPUT, "C1 aggregate input profile")
    for key, want in (("artifactSource", expected["source"]), ("controllerSource", expected["controllerSource"]),
                      ("wheelSHA256", expected["wheelSha256"]), ("currentInputIdentity", expected["currentInputIdentity"])):
        _same(aggregate.get(key), want, "C1 aggregate " + key)
    _need(aggregate.get("costGateAuthenticated") is True and aggregate.get("rustPassed") is True
          and aggregate.get("sagaPassed") is True and aggregate.get("finalIdentityPassed") is True
          and aggregate.get("requiredQualificationPassed") is True and aggregate.get("publishable") is False
          and aggregate.get("readyForEnrollment") is False, "C1 aggregate gates incomplete or overclaims")
    groups = aggregate.get("pythonGroups")
    wanted = expected["pythonGroups"]
    _need(type(groups) is list and len(groups) == len(wanted), "C1 aggregate Python group roster incomplete")
    _same([(g.get("group"), g.get("cases")) for g in groups],
          [(g["group"], g["cases"]) for g in wanted], "C1 Python source group roster")
    _need(len(xmls) == len(wanted), "Every original Python group XML is required")
    for index, (group, selected) in enumerate(zip(groups, wanted)):
        _need(group.get("passed") is True, "C1 Python group failed")
        raw = xmls.get(str(index))
        _need(type(raw) is bytes and _digest(raw) == group.get("xmlSHA256"), "C1 original Python XML hash differs")
        _junit(raw, selected["cases"], "C1 Python group " + selected["group"])


def _saga19(report: Any, expected: dict[str, Any]) -> None:
    _need(type(report) is dict, "Original installed Saga19 receipt required")
    _same(report.get("profile"), "umf.saga.portable-host-receipt/2", "Saga result schema")
    _same(report.get("hostId"), "python", "Saga selected host")
    _same(report.get("runtime"), {"python": "3.11.17", "platform": "Linux", "arch": "x86_64"}, "Saga runtime")
    _same(report.get("corpusSha256"), expected["sagaCorpusSha256"], "Saga corpus identity")
    _same(report.get("qualificationInputs"), expected["sagaInputs"], "Saga source input roster")
    _need(report.get("cases") == 19 and report.get("passed") == 19, "Saga19 totals incomplete")
    rows = report.get("results")
    _need(type(rows) is list and len(rows) == 19 and len({r.get("id") for r in rows}) == 19
          and all(r.get("passed") is True for r in rows), "Saga19 original result identities incomplete/failed")
    binding = report.get("installedBinding")
    _need(type(binding) is dict and binding.get("status") == "passed"
          and binding.get("wheelSha256") == expected["wheelSha256"]
          and binding.get("beforeNativeSha256") == expected["nativeSha256"]
          and binding.get("afterNativeSha256") == expected["nativeSha256"], "Saga19 installed owner bytes differ")


def validate_weft_existing_sdk_checks(report: Any, *, source_commit: str,
                                      pins_before_after: dict[str, str]) -> dict[str, str]:
    """Validate the four existing wheel-smoke check calls inside its SDK42 report.

    The caller first authenticates this original report by its existing handoff
    path/SHA and joins its run, source, wheel, native module, and shim through
    ``final_weft_component``. This helper adds no receipt or JSON field.
    """
    _need(type(report) is dict, "Original Weft SDK42 report required")
    _same(report.get("sourceCommit"), _commit(source_commit, "Weft source"), "Weft SDK report source")
    _same(report.get("version"), "0.4.57", "Weft SDK report version")
    _same(report.get("controls"), 42, "Weft SDK control count")
    _same(report.get("pinsBeforeAfter"), pins_before_after, "Weft SDK before/after owner pins")
    checks = report.get("checks")
    _need(type(checks) is list, "Original SDK check outcomes missing")
    rows = {}
    for row in checks:
        _need(type(row) is dict and set(row) == {"id", "status"}
              and type(row["id"]) is str and type(row["status"]) is str,
              "Original SDK check outcome row malformed")
        if row["id"] in WEFT_ORIGINAL_CHECK_CALLS:
            _need(row["id"] not in rows, "Duplicate original SDK check outcome")
            rows[row["id"]] = row["status"]
    _need(rows == WEFT_ORIGINAL_CHECK_CALLS,
          "Original installed read/page check calls are missing or have wrong outcomes")
    return rows


def _validate_weft_published_owner_records(records: Any, *, source_commit: str,
                                           source_tree: str, canonical_umf: str,
                                           cargo_lock_sha256: str) -> dict[str, Any]:
    """Validate existing published Weft platform, SDK, WASM/browser and pin records.

    This consumes the owner’s existing release JSON formats. It does not make
    Truss a producer of browser evidence and does not infer qualification from
    a release tag or from caller-supplied readiness flags.
    """
    _need(type(records) is dict and set(records) == {
        "releasePins", "platforms", "wasmManifest", "controllerRegistration",
        "browserParity", "browserReceipts", "releaseAssetDigests",
    }, "Missing Weft published owner proof records")
    source_commit = _commit(source_commit, "Weft owner source")
    _need(type(source_tree) is str and re.fullmatch(r"[0-9a-f]{40}", source_tree) is not None,
          "Weft owner source tree required")
    _need(type(canonical_umf) is str and re.fullmatch(r"[0-9a-f]{40}", canonical_umf) is not None,
          "Canonical UMF source required")
    cargo_lock_sha256 = _sha(cargo_lock_sha256, "Weft Cargo.lock")

    pins = records["releasePins"]
    _need(type(pins) is dict and pins.get("schema") == "weft-hosted-release-pins/1"
          and pins.get("tag") == "v0.4.57" and pins.get("version") == "0.4.57"
          and pins.get("distribution") == "umf-weft"
          and pins.get("sourceCommit") == source_commit and pins.get("commit") == source_commit,
          "Existing Weft hosted release pins differ from selected owner source")
    current = pins.get("currentQualification")
    _need(type(current) is dict and current.get("sourceCommit") == source_commit
          and current.get("sourceTree") == source_tree and current.get("status") == "checked",
          "Weft published current qualification source/tree differs")
    _need(current.get("profile") == "weft-current-three-wheel-sdk-controller-pairs/1"
          and type(current.get("registration")) is dict
          and current["registration"].get("schema") == "weft-0457-controller-pair-registration/1",
          "Registered Weft Q/P controller-pair profile is required")
    wheel_pins = pins.get("wheelSha256")
    _need(type(wheel_pins) is dict and set(wheel_pins) == {
        "umf_weft-0.4.57-cp39-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "umf_weft-0.4.57-cp39-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
        "umf_weft-0.4.57-cp39-abi3-macosx_11_0_arm64.whl",
    }, "Exact published three-platform Weft wheel pins required")
    for name, digest in wheel_pins.items():
        _sha(digest, "Published Weft wheel " + name)
    qualification_wheels = current.get("wheels")
    _need(type(qualification_wheels) is list and len(qualification_wheels) == 3,
          "Weft original three-platform wheel/controller rows are required")
    qualified_by_target = {row.get("target"): row for row in qualification_wheels if type(row) is dict}
    observations = current.get("actualGitHubObservations")
    _need(type(observations) is list and len(observations) >= 3,
          "Weft original GitHub run/job/artifact observations are required")
    observation_by_target = {row.get("target"): row for row in observations if type(row) is dict}

    platforms = records["platforms"]
    _need(type(platforms) is dict and set(platforms) == {"linux-x86_64", "linux-aarch64", "macos-arm64"},
          "All three original Weft platform receipts are required")
    registration = records["controllerRegistration"]
    _need(type(registration) is dict and registration.get("schema") == "weft-0457-controller-pair-registration/1"
          and registration.get("status") == "reviewed" and registration.get("sourceCommit") == source_commit
          and registration.get("sourceTree") == source_tree,
          "Weft original Q/P registration source binding is missing")
    targets = {"linux-x86_64": "x86_64-unknown-linux-gnu",
               "linux-aarch64": "aarch64-unknown-linux-gnu",
               "macos-arm64": "aarch64-apple-darwin"}
    matched_wheels = set()
    for platform, rows in platforms.items():
        _need(type(rows) is dict and set(rows) == {"component", "sdk", "packaging", "reportDigests"},
              "Existing component/SDK/packaging receipt trio required: " + platform)
        component, sdk, packaging = rows["component"], rows["sdk"], rows["packaging"]
        _need(all(type(x) is dict for x in (component, sdk, packaging)),
              "Malformed Weft owner report trio: " + platform)
        target = targets[platform]
        _need(component.get("status") == "passed" and component.get("sourceCommit") == source_commit
              and component.get("sourceTree") == source_tree
              and component.get("target") == target and component.get("canonicalUmf") == canonical_umf
              and component.get("cargoLockSha256") == cargo_lock_sha256,
              "Weft platform component source/target/lock differs: " + platform)
        if platform == "linux-x86_64":
            stage_rows = component.get("stageResults")
            _need(component.get("workflowCommit") == source_commit
                  and type(stage_rows) is list and stage_rows,
                  "Original Linux Weft producer outcome/stages missing")
        else:
            role = "macos" if platform == "macos-arm64" else "arm64"
            registered = registration.get(role)
            _need(type(registered) is dict and component.get("controllerCommit") == registered.get("controllerCommit")
                  and component.get("controllerTree") == registered.get("controllerTree")
                  and component.get("workflowCommit") == registered.get("controllerCommit")
                  and component.get("profile") == registered.get("profile"),
                  "Weft original Q/P controller identity differs: " + platform)
            stage_rows = component.get("sdkStages")
            _need(component.get("producerJobName") == ("macos-pair" if role == "macos" else "arm64-pair")
                  and type(stage_rows) is list and stage_rows,
                  "Original Weft Q/P SDK stages missing: " + platform)
        _need(len({r.get("name") for r in stage_rows}) == len(stage_rows)
              and all(type(r) is dict and type(r.get("exitCode")) is int and r["exitCode"] == 0
                      for r in stage_rows), "Weft platform original stage results incomplete: " + platform)
        _need(component.get("nativeAdmission") is False and component.get("publicationAdmission") is False,
              "Weft owner producer scope was upgraded: " + platform)
        wheel_sha = component.get("wheelSha256")
        _sha(wheel_sha, "Weft component wheel " + platform)
        _need(wheel_sha in wheel_pins.values() and wheel_sha not in matched_wheels,
              "Weft platform wheel does not uniquely join published pins: " + platform)
        matched_wheels.add(wheel_sha)
        qualified_row = qualified_by_target.get(target)
        observation = observation_by_target.get(target)
        _need(type(qualified_row) is dict and qualified_row.get("wheelSha256") == wheel_sha
              and qualified_row.get("nativeModuleSha256") == component.get("nativeModuleSha256")
              and qualified_row.get("shimSha256") == component.get("shimSha256")
              and qualified_row.get("sdkReportSha256") == rows["reportDigests"].get("sdk")
              and qualified_row.get("packagingReportSha256") == rows["reportDigests"].get("packaging")
              and type(observation) is dict
              and str(observation.get("runID")) == str(component.get("producerRunId"))
              and str(observation.get("originalAttempt")) == str(component.get("producerRunAttempt")),
              "Weft owner wheel/report/run identities do not join release pins: " + platform)
        if platform == "linux-x86_64":
            if observation.get("finalRunConclusion") == "cancelled":
                _need(str(observation.get("runID")) == "41686658658"
                      and str(observation.get("actualJob")) == "126094501575"
                      and str(observation.get("originalAttempt")) == "1"
                      and observation.get("originalAttemptConclusion") == "cancelled"
                      and component.get("producerRunConclusion") == "NOT CLAIMED while producer is running",
                      "Only the exact cancelled Weft run with its pinned selected job is permitted")
            else:
                _need(observation.get("finalRunConclusion") == "success"
                      and component.get("producerRunConclusion") == "success",
                      "Weft Linux producer run did not complete successfully")
        else:
            _need(str(observation.get("actualJob", "")).isdecimal()
                  and int(observation["actualJob"]) > 0
                  and str(observation.get("originalAttempt", "")).isdecimal()
                  and int(observation["originalAttempt"]) > 0,
                  "Weft registered Q/P selected job identity is missing")
        if platform != "linux-x86_64":
            role = "macos" if platform == "macos-arm64" else "arm64"
            _need(qualified_row.get("controllerCommit") == component.get("controllerCommit")
                  and qualified_row.get("controllerTree") == component.get("controllerTree")
                  and qualified_row.get("profile") == component.get("profile")
                  and str(observation.get("actualJob", "")).isdecimal(),
                  "Weft Q/P controller/run/job differs from release-pin registration: " + role)
        pins_before_after = sdk.get("pinsBeforeAfter")
        _need(type(pins_before_after) is dict and pins_before_after.get("wheelSha256") == wheel_sha
              and pins_before_after.get("nativeModuleSha256") == component.get("nativeModuleSha256")
              and pins_before_after.get("shimSha256") == component.get("shimSha256")
              and type(rows.get("reportDigests")) is dict
              and component.get("sdkReportSha256") == rows["reportDigests"].get("sdk")
              and component.get("packagingReportSha256") == rows["reportDigests"].get("packaging"),
              "Weft SDK/packaging report hash joins differ: " + platform)
        _need(packaging.get("status") == "passed" and packaging.get("version") == "0.4.57"
              and packaging.get("wheelSha256") == wheel_sha
              and packaging.get("nativeModuleSha256") == component.get("nativeModuleSha256"),
              "Weft packaging report differs from installed wheel/module: " + platform)
        validate_weft_existing_sdk_checks(sdk, source_commit=source_commit,
            pins_before_after={"wheelSha256": wheel_sha,
                               "nativeModuleSha256": component.get("nativeModuleSha256"),
                               "shimSha256": component.get("shimSha256")})
    _need(matched_wheels == set(wheel_pins.values()), "Published Weft wheel pin set differs from platform receipts")

    wasm = records["wasmManifest"]
    _need(type(wasm) is dict and wasm.get("status") == "passed"
          and wasm.get("sourceCommit") == source_commit and wasm.get("sourceTree") == source_tree
          and wasm.get("workflowCommit") == source_commit and wasm.get("canonicalUmf") ==
              "git+https://github.com/DocumentDrivenDX/umf.git?rev=" + canonical_umf + "#" + canonical_umf
          and wasm.get("cargoLockSha256") == cargo_lock_sha256 and wasm.get("target") == "wasm32-unknown-unknown"
          and wasm.get("NodeCases") == 14 and wasm.get("ChromiumCases") == 14
          and wasm.get("nativeDatabaseExecution") is False and wasm.get("publicationAdmission") is False,
          "Weft original Node/Chromium WASM proof is missing or misbound")
    for role in ("macos", "arm64"):
        pair = registration.get(role)
        _need(type(pair) is dict and pair.get("status") == "reviewed"
              and pair.get("sourceCommit") == source_commit and pair.get("sourceTree") == source_tree
              and pair.get("profile") == ("weft-current-macos-controller-pair/1" if role == "macos"
                                            else "weft-current-arm64-controller-pair/1")
              and type(pair.get("controllerCommit")) is str
              and re.fullmatch(r"[0-9a-f]{40}", pair["controllerCommit"]) is not None,
              "Weft registered original Q/P controller pair is incomplete: " + role)
    parity, browser = records["browserParity"], records["browserReceipts"]
    browser_summary = browser.get("summary") if type(browser) is dict else None
    _need(type(parity) is dict and type(browser) is dict
          and parity.get("cases") == 9 and parity.get("byteParity") is True
          and type(browser.get("cases")) is list and len(browser["cases"]) == 9
          and type(browser_summary) is dict and browser_summary.get("cases") == 9
          and browser_summary.get("byteParity") is True
          and browser_summary.get("wasmSha256") == parity.get("wasmSha256")
          and browser_summary.get("browser") == parity.get("browser")
          and browser_summary.get("playwrightVersion") == parity.get("playwrightVersion"),
          "Weft original nine-case browser/compiler parity receipts are missing or differ")
    assets = records["releaseAssetDigests"]
    _need(type(assets) is dict and assets.get("schema") == "weft-release-assets/1"
          and assets.get("sourceCommit") == source_commit and assets.get("status") == "verified-before-publication"
          and assets.get("expectedWheelCount") == 3 and type(assets.get("wheels")) is dict
          and set(assets["wheels"]) == set(wheel_pins)
          and set(assets.get("assetSha256", {})) >= {"SHA256SUMS", "release-pins.json",
              "current-controller-pair-registration.json", "current-wasm-manifest.json",
              "macos-browser-compiler-parity.json", "macos-browser-compiler-receipts.json",
              "current-source-manifest.json"}
          and all(type(v) is str and SHA256.fullmatch(v) for v in assets["assetSha256"].values()),
          "Weft published source/pin/checksum/public-dependency evidence is incomplete")
    return {"profile": "weft-0457-published-owner-proof/1", "sourceCommit": source_commit,
            "sourceTree": source_tree, "platforms": tuple(sorted(platforms)),
            "nodeCases": wasm["NodeCases"], "chromiumCases": wasm["ChromiumCases"],
            "browserCases": parity["cases"], "sourceDependencyClosure": "cargo-package-lists-and-local-dependency-bound"}


def validate_weft_published_owner_proofs(bundle: Any, *, source_commit: str,
                                         source_tree: str, canonical_umf: str,
                                         cargo_lock_sha256: str) -> dict[str, Any]:
    """Authenticate existing Weft release JSON bytes against GitHub and SHA256SUMS.

    ``bundle`` is transport only: the ordinary GitHub release API object and
    the original named release-asset bytes. No caller readiness flag or new
    producer receipt schema is accepted.
    """
    required = {
        "release-pins.json", "release-assets-0.4.57.json", "SHA256SUMS",
        "current-controller-pair-registration.json", "current-source-manifest.json",
        "current-wasm-manifest.json", "macos-browser-compiler-parity.json",
        "macos-browser-compiler-receipts.json",
        "x86_64-unknown-linux-gnu-component.json", "x86_64-unknown-linux-gnu-sdk-smoke.json",
        "x86_64-unknown-linux-gnu-packaging.json",
        "aarch64-unknown-linux-gnu-component.json", "aarch64-unknown-linux-gnu-sdk-smoke.json",
        "aarch64-unknown-linux-gnu-packaging.json",
        "aarch64-apple-darwin-component.json", "aarch64-apple-darwin-sdk-smoke.json",
        "aarch64-apple-darwin-packaging.json",
    }
    _need(type(bundle) is dict and set(bundle) == {"releaseApi", "assetBytes"},
          "Original Weft GitHub release API and named asset bytes are required")
    release, assets = bundle["releaseApi"], bundle["assetBytes"]
    _need(type(release) is dict and release.get("tag_name") == "v0.4.57"
          and release.get("draft") is False and release.get("prerelease") is False
          and release.get("immutable") is True and release.get("target_commitish") == source_commit,
          "Immutable selected Weft GitHub release metadata required")
    _need(type(assets) is dict and set(assets) == required
          and all(type(raw) is bytes for raw in assets.values()),
          "Exact original Weft proof asset byte roster required")
    api_assets = release.get("assets")
    _need(type(api_assets) is list, "Original Weft GitHub release asset inventory is missing")
    api_by_name = {}
    for row in api_assets:
        _need(type(row) is dict and type(row.get("name")) is str
              and row["name"] not in api_by_name, "Duplicate/malformed Weft release API asset")
        api_by_name[row["name"]] = row
    for name, raw in assets.items():
        row = api_by_name.get(name)
        _need(type(row) is dict and row.get("digest") == "sha256:" + _digest(raw)
              and type(row.get("size")) is int and row["size"] == len(raw),
              "Weft original release asset bytes differ from GitHub: " + name)
    try:
        sums = {}
        for line in assets["SHA256SUMS"].decode("ascii").splitlines():
            match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.+-]+)", line)
            _need(match is not None and match[2] not in sums, "Malformed original Weft SHA256SUMS")
            sums[match[2]] = match[1]
    except UnicodeDecodeError as error:
        raise Refusal("Original Weft SHA256SUMS is not ASCII") from error
    try:
        decoded = {name: json.loads(assets[name]) for name in required if name.endswith(".json")}
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Refusal("Malformed original Weft owner JSON asset") from error
    release_assets = decoded["release-assets-0.4.57.json"]
    _need(type(release_assets) is dict and release_assets.get("sourceCommit") == source_commit
          and release_assets.get("status") == "verified-before-publication"
          and type(release_assets.get("assetSha256")) is dict
          and release_assets["assetSha256"].get("SHA256SUMS") == _digest(assets["SHA256SUMS"])
          and release_assets["assetSha256"].get("release-pins.json") == _digest(assets["release-pins.json"]),
          "Weft original release asset inventory is not source-bound")
    for name in required - {"release-assets-0.4.57.json", "SHA256SUMS"}:
        _need(release_assets["assetSha256"].get(name) == _digest(assets[name]),
              "Weft owner release inventory digest differs: " + name)
    release_pins = decoded["release-pins.json"]
    wheel_pins = release_pins.get("wheelSha256") if type(release_pins) is dict else None
    _need(type(wheel_pins) is dict and type(release_assets.get("wheels")) is dict,
          "Original Weft wheel digest map is missing")
    for name, digest in wheel_pins.items():
        _need(sums.get(name) == digest and release_assets["assetSha256"].get(name) == digest
              and release_assets["wheels"].get(name) == digest,
              "Original Weft wheel checksum, release inventory and pins differ: " + name)
    source_manifest = decoded["current-source-manifest.json"]
    _need(source_manifest.get("sourceCommit") == source_commit and source_manifest.get("sourceTree") == source_tree
          and source_manifest.get("cargoLockSha256") == cargo_lock_sha256
          and source_manifest.get("status") == "passed" and source_manifest.get("sourceOnly") is True
          and source_manifest.get("publicationAdmission") is False,
          "Weft original source/public-dependency closure is missing or misbound")
    platforms = {}
    for target, prefix in (("linux-x86_64", "x86_64-unknown-linux-gnu"),
                           ("linux-aarch64", "aarch64-unknown-linux-gnu"),
                           ("macos-arm64", "aarch64-apple-darwin")):
        names = {role: prefix + "-" + suffix + ".json" for role, suffix in
                 (("component", "component"), ("sdk", "sdk-smoke"), ("packaging", "packaging"))}
        platforms[target] = {**{role: decoded[name] for role, name in names.items()},
            "reportDigests": {role: _digest(assets[name]) for role, name in names.items()
                              if role in ("sdk", "packaging")}}
    records = {
        "releasePins": decoded["release-pins.json"], "platforms": platforms,
        "wasmManifest": decoded["current-wasm-manifest.json"],
        "controllerRegistration": decoded["current-controller-pair-registration.json"],
        "browserParity": decoded["macos-browser-compiler-parity.json"],
        "browserReceipts": decoded["macos-browser-compiler-receipts.json"],
        "releaseAssetDigests": release_assets,
    }
    return _validate_weft_published_owner_records(records, source_commit=source_commit,
        source_tree=source_tree, canonical_umf=canonical_umf, cargo_lock_sha256=cargo_lock_sha256)


def validate_one_component_prerequisite(gate_id: str, result: Any, expected: dict[str, Any]) -> dict[str, Any]:
    """Run the fixed in-source validator for one current C1 output identity."""
    _need(gate_id in REQUIRED, "Unknown C1 component validator ID")
    expected = _expected(expected)
    if gate_id == FACTORY51:
        _factory51(result, expected)
    elif gate_id == EARLY18:
        _early18(result, expected)
    elif gate_id == RUST477:
        _rust477(result, expected)
    elif gate_id == PYTHON31:
        _python31(result, expected)
    elif gate_id == SAGA19:
        _saga19(result, expected)
    elif gate_id == RESOURCES9:
        _need(type(result) is dict, "C1 current resource manifest receipt required")
        _same(result, expected["resourceManifest"], "C1 canonical current resource manifest")
    return {"gateId": gate_id, "source": expected["source"], "wheelSha256": expected["wheelSha256"],
            "nativeSha256": expected["nativeSha256"], "validated": True}


def validate_component_prerequisites(receipts: Any, expected: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Require and validate all fixed C1 outputs; no scope/qualified flags accepted."""
    _need(type(receipts) is dict and set(receipts) == REQUIRED, "Unknown, missing, or extra C1 producer result IDs")
    expected = _expected(expected)
    result = {}
    for gate_id in sorted(REQUIRED):
        result[gate_id] = validate_one_component_prerequisite(gate_id, receipts[gate_id], expected)
    early_members = receipts[EARLY18]["memberBytes"]
    try:
        cost_measurement = json.loads(early_members["measurement.json"])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Refusal("Original cost-gate measurement member is malformed") from error
    _same(cost_measurement, receipts[FACTORY51], "Cost member to independent factory result join")
    return result


# T06 consumes the existing Core successor controller's original bytes. These
# private transport/context dictionaries are NOT new owner producer schemas.
CORE_SDK_GATES = ('job-setup', 'source', 'common', 'wheel', 'sdk', 'rebuild',
                  'consumers', 'inspection', 'final-identity')
CORE_SDK_CHECKS = ('build', 'package', 'browser-setup', 'bun-full', 'node-native',
                   'node-browser', 'bun-saga', 'chromium-saga')
CORE_PLATFORMS = ('linux-x86_64', 'macos-arm64')
CORE_CELLS = tuple(kind + '-' + version for kind in ('direct', 'rebuilt')
                   for version in ('3.11.17', '3.13.16'))
CORE_OWNER_WORKFLOW = '.github/workflows/core-successor-qualification.yml'
CORE_OWNER_REGISTRY = 'qualification-inputs/core-successor-admissions.json'
CORE_UPLOAD = 'Retain sanitized failures and original component custody'


def selected_core_owner_context(cohort_bytes, *, owner, wheel):
    """Export ONLY committed cohort selection plus independently admitted bytes.

    The optional owner qualification registration belongs to the source-controlled
    cohort. A proof bundle can never select its own P, registry hash or admission.
    No current registration is fabricated when that source field is absent.
    """
    cohort = _core_json(cohort_bytes, 'committed cohort')
    source = cohort.get('componentPrerequisiteSourceRefs', {}).get('core', {}).get('sourceCommit')
    _commit(source, 'Selected Core source')
    _need(type(owner) is dict and owner.get('sourceCommit') == source
          and type(wheel) is dict and wheel.get('sha256') == owner.get('wheelSha256'),
          'Selected Core owner/wheel differs from authenticated source')
    return {'sourceCommit': source, 'version': cohort['core']['version'],
            'wheelSha256': _sha(wheel['sha256'], 'Selected Core wheel'),
            'nativeSha256': _sha(owner.get('moduleSha256'), 'Selected Core native'),
            'qualification': cohort.get('coreOwnerQualification')}


def _core_json(raw, label):
    _need(type(raw) is bytes, 'Original Core bytes missing: ' + label)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _need(key not in result, 'Duplicate Core JSON field: ' + label)
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Refusal('Malformed original Core JSON: ' + label) from error
    _need(type(value) is dict, 'Original Core object required: ' + label)
    return value


def _core_path(path):
    _need(type(path) is str and path and not path.startswith('/') and '\\' not in path
          and all(part not in ('', '.', '..') for part in path.split('/')), 'Unsafe original Core member')
    return path


def _core_members(proof, record):
    """P pins each original member; raw Actions records join that exact material."""
    from datetime import datetime
    run, job, artifact = record['run'], record['job'], record['artifact']
    _need(all(type(value.get(key)) is int for value,keys in ((run,('id','run_attempt')),(job,('id','run_id','run_attempt')),(artifact,('id',))) for key in keys), 'Core original API identity types differ')
    _need(proof['workflow'] == CORE_OWNER_WORKFLOW and proof['upload_step'].startswith(CORE_UPLOAD),
          'Core owner workflow/upload step differs')
    for name in ('run', 'job', 'attempt', 'artifact'):
        _need(type(proof[name]) is int and proof[name] > 0, 'Core original numeric identity missing')
    _need(run.get('id') == proof['run'] and run.get('run_attempt') == proof['attempt']
          and run.get('head_sha') == proof['workflow_sha'] and run.get('path') == proof['workflow']
          and run.get('event') == 'workflow_dispatch' and run.get('status') == 'completed'
          and run.get('conclusion') in (('success','failure') if proof['kind'] == 'continuation' else ('success',)) and run.get('repository', {}).get('full_name') == 'DocumentDrivenDX/umf'
          and run.get('repository', {}).get('id') == 1382276802
          and run.get('repository', {}).get('owner', {}).get('id') == 273466046,
          'Core original Actions run/source differs')
    _need(job.get('id') == proof['job'] and job.get('run_id') == proof['run']
          and job.get('run_attempt') == proof['attempt'] and job.get('head_sha') == proof['workflow_sha']
          and job.get('name') == proof['job_name'] and job.get('status') == 'completed'
          and job.get('conclusion') in (('success','failure') if proof['kind'] == 'continuation' else ('success',))
          and {'linux-x86_64': 'ubuntu-24.04', 'macos-arm64': 'macos-15'}[proof['platform']] in job.get('labels', []),
          'Core original job/platform differs')
    suffix = '-' + proof['envelope'] if 'envelope' in proof else ''
    artifact_name = 'core-successor-' + ('linux' if proof['platform'] == 'linux-x86_64' else 'macos')
    _need(artifact.get('id') == proof['artifact'] and artifact.get('expired') is False
          and artifact.get('digest') == 'sha256:' + proof['sha256']
          and artifact.get('name') == artifact_name + '-' + str(proof['run']) + '-' + str(proof['attempt']) + suffix
          and artifact.get('workflow_run', {}).get('id') == proof['run']
          and artifact.get('workflow_run', {}).get('head_sha') == proof['workflow_sha'],
          'Core original artifact differs')
    steps = [step for step in job.get('steps', []) if step.get('name') == proof['upload_step']]
    _need(len(steps) == 1 and steps[0].get('status') == 'completed'
          and steps[0].get('conclusion') == 'success', 'Core original upload did not pass')
    def moment(value):
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    _need(moment(job['started_at']) <= moment(steps[0]['started_at']) <= moment(artifact['created_at'])
          <= moment(steps[0]['completed_at']) <= moment(job['completed_at']), 'Core artifact upload time differs')
    members = record['memberBytes']
    _need(type(members) is dict and set(members) == set(proof['members']), 'Core original member roster differs')
    for path, digest in proof['members'].items():
        _core_path(path); _sha(digest, 'Core member')
        _need(type(members[path]) is bytes and _digest(members[path]) == digest,
              'Core original member hash differs: ' + path)
    return members


def _core_material(material, records):
    """Verify regular or existing multipart original custody, without retrieval."""
    if material.get('profile') != 'umf.core-successor.multipart-material/1':
        _need({str(material['artifact'])} <= set(records), 'Core material records differ')
        return _core_members(material, records[str(material['artifact'])])
    proof = material['proof']
    expected = {str(proof['artifact'])} | {str(row['provenance']['artifact']) for row in material['envelopes']}
    _need(expected <= set(records) and len(expected) == len(material['envelopes']) + 1,
          'Core multipart artifact roster differs')
    result = dict(_core_members(proof, records[str(proof['artifact'])]))
    parts = {}
    for row in material['envelopes']:
        p = row['provenance']; raw = _core_members(p, records[str(p['artifact'])])['payload.bin']
        _need((row['object'], row['ordinal']) not in parts, 'Duplicate Core part')
        parts[(row['object'], row['ordinal'])] = raw
    _need(set(parts) == {(name, i) for name, obj in material['objects'].items() for i in range(len(obj['parts']))},
          'Core multipart object coverage differs')
    for name, obj in material['objects'].items():
        _core_path(name); offset = 0; chunks = []
        for ordinal, part in enumerate(obj['parts']):
            raw = parts[(name, ordinal)]
            _need(part['ordinal'] == ordinal and part['offset'] == offset and part['length'] == len(raw)
                  and part['sha256'] == _digest(raw), 'Core multipart gap/length/hash differs')
            chunks.append(raw); offset += len(raw)
        raw = b''.join(chunks)
        _need(name not in result and obj['bytes'] == len(raw) and obj['sha256'] == _digest(raw),
              'Core logical object differs')
        result[name] = raw
    return result


def _core_source_archive(raw, a):
    """Check the actual complete Git archive tree and selected source hashes."""
    import io
    import tarfile
    files = {}; tree = {}; prefix = 'umf-v' + a['version'] + '/'
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:*') as archive:
        for row in archive:
            if row.isdir():
                continue
            _need(row.name.startswith(prefix), 'Core source prefix differs')
            name = _core_path(row.name[len(prefix):])
            _need(name not in files and (row.isfile() or row.issym()), 'Core source duplicate/type differs')
            data = archive.extractfile(row).read() if row.isfile() else row.linkname.encode()
            files[name] = data; node = tree
            segments = name.split('/')
            for segment in segments[:-1]:
                _need(segment not in node or type(node[segment]) is dict, 'Core Git path collision')
                node = node.setdefault(segment, {})
            _need(segments[-1] not in node, 'Core Git path collision')
            mode = '120000' if row.issym() else '100755' if row.mode & 0o111 else '100644'
            blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).digest()
            node[segments[-1]] = (mode, blob)
    def git_tree(node):
        body = b''
        for name, value in sorted(node.items(), key=lambda row: row[0].encode() + (b'/' if type(row[1]) is dict else b'')):
            mode, oid = ('40000', git_tree(value)) if type(value) is dict else value
            body += mode.encode() + b' ' + name.encode() + b'\0' + oid
        return hashlib.sha1(b'tree ' + str(len(body)).encode() + b'\0' + body).digest()
    _same(git_tree(tree).hex(), a['source']['tree'], 'Core complete source tree')
    for path, digest in {**a['inputs'], **a['recipes']}.items():
        _need(path in files and _digest(files[path]) == digest, 'Core source input/recipe differs: ' + path)
    return files


def _core_wheel(raw, version):
    import io
    from email.parser import BytesParser
    from zipfile import ZipFile
    with ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        _need(len(names) == len(set(names)), 'Core wheel duplicate members')
        metadata = [name for name in names if name.endswith('.dist-info/METADATA')]
        native = [name for name in names if name.startswith('umf/_rust_core.') and name.endswith(('.so', '.pyd'))]
        _need(len(metadata) == len(native) == 1 and 'umf/_bin/umf' in names, 'Core wheel payload incomplete')
        meta = BytesParser().parsebytes(archive.read(metadata[0]))
        _need(meta.get('Name', '').replace('_', '-').lower() == 'umf-core' and meta.get('Version') == version,
              'Core wheel selected distribution/version differs')
        payload = {name: _digest(archive.read(name)) for name in names if name.startswith('umf/') and not name.endswith('/')}
        return payload[native[0]], payload['umf/_bin/umf'], payload


def _core_sdk(members, a, roster, platform, sdk_path):
    import io
    import tarfile
    def report(name):return _core_json(members[name], name)
    sdk = report(sdk_path)
    namespace = sdk_path[:-len('sdk.json')]
    _need(sdk_path.endswith('sdk.json'), 'Core original SDK evidence path differs')
    _need(set(sdk) == {'archive_sha256', 'manifest_sha256', 'platform', 'checks'}
          and sdk['platform'] == platform and set(sdk['checks']) == set(CORE_SDK_CHECKS)
          and all(value is True for value in sdk['checks'].values()), 'Core original SDK gates incomplete')
    archive = members[roster[platform + '/sdk']['member']]
    manifest_raw = members[roster[platform + '/sdk-manifest']['member']]
    _same(sdk['archive_sha256'], _digest(archive), 'Core SDK archive')
    _same(sdk['manifest_sha256'], _digest(manifest_raw), 'Core SDK manifest')
    package = report(namespace+'sdk-receipt.json')
    _need(package.get('status') == 'built' and package.get('sha256') == _digest(archive)
          and package.get('manifestSha256') == _digest(manifest_raw), 'Core SDK package custody differs')
    manifest = _core_json(manifest_raw, 'SDK manifest'); archived = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:*') as tar:
        for row in tar:
            if not row.isfile():continue
            _core_path(row.name); _need(row.name not in archived, 'SDK archive duplicate member')
            archived[row.name] = tar.extractfile(row).read()
    _need(archived.get('package/manifest.json') == manifest_raw, 'Installed SDK manifest/archive differs')
    metadata = _core_json(archived['package/package.json'], 'SDK package metadata')
    _need(manifest.get('profile') == 'umf.sdk.distribution.rust-default/1' and metadata.get('name') == '@umf/core' and metadata.get('version') == a['version'], 'Core SDK distribution/version differs')
    for name, digest in manifest['sha256'].items():
        _need('package/' + name in archived and _digest(archived['package/' + name]) == digest,
              'SDK distribution member differs')
    # These are retained ORIGINAL custody objects. No substitute success flag
    # can replace either full139 custody or the separate Saga-only interface.
    decoded = []
    for name, raw in members.items():
        if name.endswith('.json'):
            decoded.append((name, _core_json(raw, name)))
    def one_profile(profile):
        rows = list({_digest(_canonical(value)): value for name, value in decoded if name.startswith(namespace) and value.get('profile') == profile}.values())
        _need(len(rows) == 1, 'Missing/duplicate original SDK custody: ' + profile)
        return rows[0]
    full = one_profile('umf.sdk-installed-archive-custody/2')
    saga = one_profile('umf.sdk-installed-saga-custody/1')
    browser = one_profile('umf.sdk-installed-browser-saga/1')
    required_members = {'package/'+name for name in ('package.json','manifest.json','dist/umf-node.js','dist/umf-browser.js','dist/rust-default-manifest.json','dist/umf_core_node.node','dist/loader-contract.js','dist/runtime/wasm/index.js','dist/runtime/wasm/pkg/umf_core_wasm.js','dist/runtime/wasm/pkg/umf_core_wasm_bg.wasm')}
    for custody, full_phase in [(full, True), (saga, False)]:
        _need(custody['archiveSha256'] == _digest(archive) and custody['sdkManifestSha256'] == _digest(manifest_raw)
              and custody['installerSourceSha256'] == a['recipes']['scripts/test-sdk-install.ts']
              and custody['existing139ConsumerChecks'] == ('passed' if full_phase else 'not-run-in-saga-phase')
              and custody['sagaResult']['cases'] == custody['sagaResult']['passed'] == 19,
              'Original SDK installed full139/Saga custody differs')
        _need(custody['exactArchiveMembers'] == custody['installedMembers'] and set(custody['installedMembers']) == required_members,
              'Original SDK archive-to-installed members differ')
        for name, row in custody['installedMembers'].items():
            _need(name in archived and row == {'size': len(archived[name]), 'sha256': _digest(archived[name])},
                  'Original SDK installed member bytes differ')
    _need(browser['artifactSourceS'] == a['source']['commit'] and browser['controllerQ'] == a['controller']['commit']
          and browser['archiveSha256'] == _digest(archive) and browser['installedMembers'] == saga['installedMembers']
          and browser['qualificationInputs'] == saga['sagaQualificationInputs']
          and browser['result']['cases'] == browser['result']['passed'] == 19
          and browser['hostCalls'] == 0 and type(browser['browser']) is str and browser['browser'],
          'Core installed Chromium Saga differs')
    # Original node consumer prints JSON lines, not a new per-call report.
    outputs = []
    for name, raw in members.items():
        if name.endswith('.log'):
            for line in raw.splitlines():
                try:value = json.loads(line)
                except (ValueError, UnicodeDecodeError):continue
                if type(value) is dict:outputs.append(value)
    nodes = [v for v in outputs if v.get('status') == 'passed' and v.get('runtime') == 'node']
    _need(any('chromium' not in v for v in nodes) and any(type(v.get('chromium')) is dict
          and v['chromium'].get('status') == 'passed' and v['chromium'].get('nodeGlobalsAbsent') is True
          and type(v['chromium'].get('version')) is str and v['chromium']['version'] for v in nodes),
          'Original Node/browser consumer output missing')


def _core_deep(d, a, cell, original):
    _need(d['profile'] == 'umf.core-successor.installed-inspection/3'
          and all(d[key] == a[key] for key in ('source', 'version', 'resources', 'protocols')),
          'Core original installed inspection identity differs')
    for key, count in [('maximumWork', 1000000), ('cases', 17), ('calls', 51), ('coldConstructors', 51), ('paidManifestReports', 51)]:
        _need(type(d[key]) is int and d[key] == count, 'Core installed inspection count differs')
    for key in ('coldPerCall', 'constructorPassed', 'custodyPreserved', 'installedFilesUnchanged',
                'loadedOwnershipVerified', 'recordVerified', 'embeddedCLIVerified', 'normalResolver',
                'resourceSuccess', 'budgetRefusalVerified'):
        _need(d[key] is True, 'Core installed inspection failed: ' + key)
    _need(d['runtime']['cell'] == cell and d['runtime']['python'] == cell.split('-', 1)[1]
          and d['runtime']['implementation'] == 'cpython', 'Core actual interpreter differs')
    compatibility = d['compatibility']
    _need(compatibility['profile'] == 'umf.core-successor.named-compatibility/1'
          and compatibility['source'] == a['source'] and compatibility['original'] == original
          and compatibility['census_sha256'] == a['compatibility']['census_sha256']
          and compatibility['wheel_sha256'] == d['wheel_sha256'] and compatibility['native_sha256'] == d['native_sha256'],
          'Core compatibility source/wheel/original differs')
    for group in ('early', 'later'):
        _need(list(compatibility['groups'][group]['cases']) == a['compatibility'][group]
              and all(value == 'passed' for value in compatibility['groups'][group]['cases'].values()),
              'Core original named compatibility results missing')


def validate_core_selected_owner_proofs(bundle, *, selected):
    """Narrow owner readiness from immutable P-selected SDK original materials.

    No network, producer function, dynamic owner code, native import or upstream
    release promotion. Missing future selected registration ALWAYS refuses.
    """
    try:
        return _validate_core_selected_owner_proofs(bundle, selected)
    except Refusal:
        raise
    except Exception as error:
        raise Refusal('Malformed/missing original selected Core owner proof') from error


def _validate_core_selected_owner_proofs(bundle, selected):
    _need(type(selected) is dict and set(selected) == {'sourceCommit', 'version', 'wheelSha256', 'nativeSha256', 'qualification'},
          'Trusted source-controlled selected Core context required')
    q = selected['qualification']
    _need(type(q) is dict and set(q) == {'authorityCommit', 'authorityTree', 'registrySha256', 'admissionId'},
          'Missing trusted selected Core owner admission')
    _commit(selected['sourceCommit'], 'Core S'); _commit(q['authorityCommit'], 'Core P'); _commit(q['authorityTree'], 'Core P tree')
    _need(type(bundle) is dict and set(bundle) == {'registryBytes', 'controllerBytes', 'materials', 'readinessBytes'},
          'Original Core selected owner transport required')
    _same(_digest(bundle['registryBytes']), _sha(q['registrySha256'], 'Core P registry'), 'Core immutable P registry')
    registry = _core_json(bundle['registryBytes'], 'P registry')
    _need(registry.get('profile') == 'umf.core-successor.registry/2' and type(registry.get('admissions')) is list,
          'Core owner registry profile differs')
    rows = registry['admissions']; _need(len({a['id'] for a in rows}) == len(rows), 'Duplicate Core owner admission')
    matches = [a for a in rows if a['id'] == q['admissionId']]
    _need(len(matches) == 1, 'Missing trusted selected Core owner admission')
    a = matches[0]
    _need(a['purpose'] == 'candidate-aggregate' and a['profile'] in
          ('umf.core-successor.candidate/2', 'umf.core-successor.candidate-multipart/1'), 'Core original aggregate admission required')
    _need(a['source']['commit'] == selected['sourceCommit'] and a['version'] == selected['version'],
          'Core selected source/version differs')
    _need(set(a['components']) == set(CORE_PLATFORMS) and set(bundle['materials']) == set(CORE_PLATFORMS),
          'Core both original platform materials required')
    expected_roles = {'source', 'core-sdist', 'codegen-wheel', 'codegen-sdist'} | {p+'/'+r for p in CORE_PLATFORMS for r in ('core-wheel','standalone-cli','sdk','sdk-manifest')}
    _need(set(a['roster']) == expected_roles, 'Core coupled original role roster differs')
    readiness = _core_json(bundle['readinessBytes'], 'material readiness')
    _need(readiness['profile'] == 'umf.core-successor.material-readiness/1'
          and readiness['status'] == 'material-gates-passed'
          and all(readiness[key] == a[key] for key in ('source','version','controller','resources','inputs','protocols'))
          and readiness['assets'] == a['roster'], 'Core coupled material readiness differs')
    _need(all(readiness[key] is False for key in ('releaseQualified','nativeReleaseQualified','coupledQualified','publicationAuthorized')),
          'Core material readiness improperly promoted upstream qualification')
    for platform in CORE_PLATFORMS:
        binding = a['components'][platform]
        components = [row for row in rows if row['id'] == binding['admission_id']]
        _need(len(components) == 1, 'Missing Core platform admission')
        comp = components[0]; material = binding['material']
        compatibility = comp['compatibility']
        historical = 'python/tests/test_retained_codegen_native.py::PublicRetainedFeasibilityTests::test_cold_constructor_and_each_17_vector_dispatch_list_tuple_call_fit_strict_1m'
        _need(set(compatibility) == {'census_sha256','early','later','historicalExcluded'}
              and compatibility['historicalExcluded'] == [historical], 'Core historical disposition differs')
        names = []
        for group, count in [('early',18),('later',31)]:
            selectors = compatibility[group]
            _need(type(selectors) is list and len(selectors) == count
                  and all(type(name) is str and re.fullmatch(r'python/tests/[A-Za-z0-9_]+\.py::(?:[A-Za-z0-9_]+::)?test_[A-Za-z0-9_]+',name) for name in selectors),
                  'Core exact named compatibility roster differs')
            names.extend(selectors)
        _need(len(names) == len(set(names)) and historical not in names, 'Core compatibility overlap')
        _need(comp['purpose'] == 'candidate-production' and comp['platform'] == platform
              and all(comp[key] == a[key] for key in ('source','version','resources','inputs','recipes','protocols')),
              'Core platform admission source/version/input differs')
        ctrl = comp['controller']; _need(len({q['authorityCommit'], ctrl['commit'], a['source']['commit']}) == 3,
                                       'Core S/P/Q must remain distinct')
        controller_bytes = bundle['controllerBytes'][ctrl['commit']]
        _same(_digest(controller_bytes['script']), ctrl['script_sha256'], 'Core fixed Q script')
        _same(_digest(controller_bytes['workflow']), ctrl['workflow_sha256'], 'Core fixed Q workflow')
        _need(material['source'] == a['source']['commit'] and material['controller'] == ctrl['commit']
              and material['platform'] == platform and material['kind'] == 'qualified'
              and readiness['originals'][platform] == material, 'Core original material source/controller differs')
        records = bundle['materials'][platform]
        members = _core_material(material, records)
        def record_ids(value):
            if value.get('profile') == 'umf.core-successor.multipart-material/1':
                return {str(value['proof']['artifact'])} | {str(x['provenance']['artifact']) for x in value['envelopes']}
            return {str(value['artifact'])}
        used_ids = record_ids(material); prior = None
        for role in ('common','continuation'):
            previous = comp.get(role)
            if previous is None:continue
            _need(previous['source'] == comp['source']['commit'] and previous['controller'] == ctrl['commit']
                  and previous['kind'] == role, 'Core reused original source/controller differs')
            previous_members = _core_material(previous, records); used_ids |= record_ids(previous)
            if role == 'continuation':
                prior = _core_json(previous_members['component.json'], 'original continuation')
                origin = previous.get('proof', previous)
                namespace = 'original/'+str(origin['run'])+'-'+str(origin['attempt'])+'-'+str(origin['artifact'])+'/'
                for name, raw in previous_members.items():
                    _need(members.get(namespace+name) == raw, 'Core continuation original namespace differs')
        _need(set(records) == used_ids, 'Unselected Core original material records')
        r = _core_json(members['component.json'], 'component')
        _need(r['status'] == 'passed' and r['failure'] is None and r['profile'] == comp['profile']
              and all(r[key] == comp[key] for key in ('source','version','platform','controller','inputs','resources','protocols'))
              and all(r[key] is False for key in ('releaseQualified','nativeReleaseQualified','coupledQualified')),
              'Core original component failed/misbound/promoted')
        original = r['original']; p = material.get('proof', material)
        _need(original == {key: str(p[key]) if key in ('run','job','attempt') else p[key]
                           for key in ('run','job','attempt','workflow_sha','platform','job_name','upload_step')} | {'controller_sha': ctrl['commit']},
              'Core component original producer namespace differs')
        _need(set(r['steps']) == set(CORE_SDK_GATES) and set(r['inspection']) == set(CORE_CELLS),
              'Core original gate/runtime roster differs')
        gates = {}
        for name, step in r['steps'].items():
            ref = step['evidence']; path = _core_path(ref['path'])
            _need(step['status'] == 'passed' and set(ref) == {'path','sha256'}
                  and _digest(members[path]) == ref['sha256'], 'Core original gate evidence differs: ' + name)
            gates[name] = _core_json(members[path], name)
        if prior is not None:
            _need(all(prior[key] == comp[key] for key in ('source','version','controller','inputs','resources','protocols','platform')),
                  'Core prior source/admission differs')
            for name, step in r['steps'].items():
                if 'original' in step:
                    _need(name not in ('job-setup','final-identity') and step['original'] == prior['steps'][name].get('original',prior['original'])
                          and step['evidence']['sha256'] == prior['steps'][name]['evidence']['sha256'],
                          'Core reused original gate namespace/custody differs')
        _need(gates['job-setup'].get('acquiredThisJob') is True
              and gates['final-identity'].get('sourceUnchanged') is True
              and gates['final-identity'].get('controllerUnchanged') is True, 'Core final/source acquisition failed')
        for role, row in a['roster'].items():
            if row['platform'] != platform:continue
            raw = members[_core_path(row['member'])]
            _need(len(raw) == row['bytes'] and _digest(raw) == row['sha256'], 'Core selected role bytes differ: ' + role)
        for role in ('core-sdist','codegen-wheel','codegen-sdist'):
            row = a['roster'][role]
            _need(_digest(members['common/'+row['name']]) == row['sha256'], 'Core common artifacts differ across platforms')
        source_row = a['roster']['source']
        source_raw = members[source_row['member']]
        _need(gates['source']['allModesSymlinksAndBlobBytesMatch'] is True
              and gates['source'].get('archive_sha256', gates['source'].get('tar_sha256')) == source_row['sha256'], 'Core complete source archive proof missing')
        source_files = _core_source_archive(source_raw, a)
        census_path = 'tests/qualification/fixtures/inspector-construction-batch.json'
        census = _core_json(source_files[census_path], 'Core source census')['installedFactory']
        _need(compatibility == {'census_sha256':a['inputs'][census_path], 'early':census['publicControls'],
                  'later':[name for group in census['python'] for name in group['cases']],
                  'historicalExcluded':census['legacyDisposition']['historicalOnly']}, 'Core compatibility source census differs')
        _need({'python/hatch_build.py','python/umf_codegen/hatch_build.py','tools/verify_python_artifacts.py',
               'tools/qualify_python_release_wheel.py','scripts/package-sdk-rust-default.ts','scripts/package-sdk.py',
               'scripts/test-sdk-install.ts','scripts/saga-portable/installed-browser.ts','scripts/test-native-sdk-install.mjs',
               'tools/generate_codegen_resource_literals.py'} <= set(a['recipes']), 'Core canonical recipe roster incomplete')
        resource_sources = dict(zip(RESOURCE_NAMES, (
            'spec/core/schema.json','spec/core/semantic-type-reference.schema.json','spec/core/extension-package.schema.json',
            'spec/metamodel/generated/core-constraints.json','spec/metamodel/generated/domain-policy.json',
            'spec/extensions/tables/package.json','spec/extensions/actions/package.json','spec/extensions/binding/package.json',
            'spec/extensions/binding-stable/package.json')))
        _need(set(a['resources']) == {'action_runtime_resources/'+name+'.json' for name in RESOURCE_NAMES},
              'Core exact nine resource roles differ')
        for name, path in resource_sources.items():
            _need(a['resources']['action_runtime_resources/'+name+'.json'] == a['inputs'][path]
                  == _digest(source_files[path]), 'Core canonical resource/source differs')
        _need(gates['common'].get('files') == {a['roster'][role]['name']:a['roster'][role]['sha256']
                  for role in ('core-sdist','codegen-wheel','codegen-sdist')}, 'Core original common gate differs')
        import io
        from email.parser import BytesParser
        from zipfile import ZipFile
        with ZipFile(io.BytesIO(members['common/'+a['roster']['codegen-wheel']['name']])) as archive:
            paths = [name for name in archive.namelist() if name.endswith('.dist-info/METADATA')]
            _need(len(paths) == 1, 'Core companion wheel metadata missing')
            meta = BytesParser().parsebytes(archive.read(paths[0]))
            _need(meta.get('Name','').lower().replace('_','-') == 'umf-codegen' and meta.get('Version') == a['version']
                  and any(re.fullmatch(r'umf[-_]core\s*==\s*'+re.escape(a['version']),value,re.I)
                          for value in meta.get_all('Requires-Dist',[])), 'Core companion dependency/version differs')
        wheel_row = a['roster'][platform+'/core-wheel']; wheel_sha = wheel_row['sha256']
        native_sha, embedded_cli, payload = _core_wheel(members[wheel_row['member']], a['version'])
        _need(gates['wheel']['wheel'] == wheel_sha and gates['wheel']['standaloneCLI'] == a['roster'][platform+'/standalone-cli']['sha256'],
              'Core selected wheel/standalone CLI differs')
        if platform == 'linux-x86_64':
            _need(wheel_sha == selected['wheelSha256'] and native_sha == selected['nativeSha256'],
                  'Core Linux direct wheel/native differs from Truss admitted tuple')
        rebuild = gates['rebuild']; rebuild_receipt = _core_json(members['core-artifact.json'], 'sdist rebuild')
        _need(set(rebuild) == {'raw_sha256','sdist_sha256','rebuilt_sha256','receipt_sha256'}
              and rebuild['sdist_sha256'] == a['roster']['core-sdist']['sha256']
              and rebuild['receipt_sha256'] == _digest(members['core-artifact.json'])
              and rebuild_receipt['schema'] == 'umf.python-artifact-qualification/1'
              and rebuild_receipt['source_payload_verification'] == 'passed'
              and rebuild_receipt['distribution_version'] == a['version']
              and rebuild_receipt['artifacts']['sdist_rebuilt']['sha256'] == rebuild['rebuilt_sha256'], 'Core independent sdist rebuild differs')
        def find_hash(digest):
            found = [raw for raw in members.values() if _digest(raw) == digest]
            _need(found, 'Core original archive bytes missing'); return found[0]
        find_hash(rebuild['raw_sha256']); rebuilt_raw = find_hash(rebuild['rebuilt_sha256'])
        rebuilt_native, _, rebuilt_payload = _core_wheel(rebuilt_raw, a['version'])
        consumers = gates['consumers']
        _need(consumers['normalResolverCells'] == list(CORE_CELLS) and set(consumers['cells']) == set(CORE_CELLS),
              'Core normal resolver cell roster differs')
        for cell in CORE_CELLS:
            evidence = consumers['cells'][cell]
            _need(set(evidence) == {'interpreter','install','freeze','record','postRecord','inspection','native','saga'}, 'Core consumer original evidence roster differs')
            material_files = {}
            for kind, prefix, suffix in [('interpreter','interpreter-','.json'),('install','install-','.json'),('freeze','freeze-','.txt'),('record','record-','.json'),('postRecord','record-post-','.json'),('inspection','inspection-','.json'),('native','native-','.xml'),('saga','saga-','.json')]:
                path = prefix+cell+suffix
                _same(_digest(members[path]), evidence[kind], 'Core original '+kind)
                material_files[kind] = members[path]
            d = _core_json(material_files['inspection'], cell)
            _same(d, r['inspection'][cell], 'Core original inspection/component')
            _core_deep(d, comp, cell, r['steps']['consumers'].get('original', original))
            expected_wheel, expected_native, expected_payload = (wheel_sha,native_sha,payload) if cell.startswith('direct-') else (rebuild['rebuilt_sha256'],rebuilt_native,rebuilt_payload)
            _need(d['wheel_sha256'] == expected_wheel and d['native_sha256'] == expected_native,
                  'Core direct/rebuilt wheel/native identity differs')
            _same(_core_json(material_files['interpreter'], cell), d['runtime'], 'Core actual interpreter')
            for label in ('record','postRecord'):
                record = _core_json(material_files[label], label)
                _need(record['status'] == 'passed' and record['distribution_version'] == a['version']
                      and record['wheel_sha256'] == expected_wheel and record['native_sha256'] == expected_native
                      and record['all_files_inside_platlib'] is True, 'Core original installed RECORD differs')
            install = _core_json(material_files['install'], 'normal resolver'); packages = {}
            from urllib.parse import urlparse
            for item in install['install']:
                name = item['metadata']['name'].lower().replace('_','-')
                _need(name not in packages, 'Core resolver duplicate distribution'); packages[name] = item
            for name, digest in [('umf-core',expected_wheel),('umf-codegen',a['roster']['codegen-wheel']['sha256'])]:
                item = packages[name]; info = item['download_info']
                _need(item['metadata']['version'] == a['version'] and info['archive_info']['hashes']['sha256'] == digest
                      and urlparse(info['url']).scheme == 'file' and not urlparse(info['url']).netloc,
                      'Core normal resolver dependency/origin differs')
            _need(material_files['freeze'].strip(), 'Core original dependency freeze missing')
            root = ET.fromstring(material_files['native'])
            cases = list(root.iter('testcase'))
            _need(cases and all(not list(case.iter('failure')) and not list(case.iter('error')) and not list(case.iter('skipped')) for case in cases), 'Core original native tests incomplete')
            saga = _core_json(material_files['saga'], 'Saga consumer')
            _need(saga['cases'] == saga['passed'] == 19 and saga['installedBinding']['wheelSha256'] == expected_wheel
                  and saga['installedBinding']['beforeNativeSha256'] == saga['installedBinding']['afterNativeSha256'] == expected_native,
                  'Core original installed Saga consumer differs')
            compatibility = d['compatibility']
            for group in ('early','later'):
                raw = find_hash(compatibility['groups'][group]['xml_sha256'])
                _junit(raw, comp['compatibility'][group], 'Core SDK named '+group)
            _same(gates['inspection']['reports'][cell], evidence['inspection'], 'Core inspection gate cell')
        for key, digest in [('embeddedCLI19',embedded_cli),('standaloneCLI19',a['roster'][platform+'/standalone-cli']['sha256'])]:
            ref = consumers[key]; cli_raw = members[_core_path(ref['path'])]
            _same(_digest(cli_raw), ref['sha256'], 'Core original CLI receipt')
            cli = _core_json(cli_raw, key)
            _need(cli['host'] == 'cli' and cli['cases'] == cli['passed'] == 19
                  and cli['artifacts']['cliBinary']['sha256'] == digest, 'Core distinct CLI consumer differs')
        _core_sdk(members, comp, a['roster'], platform, r['steps']['sdk']['evidence']['path'])
    return {'profile':'core-selected-owner-readiness/1', 'sourceCommit':selected['sourceCommit'],
            'sourceTree':a['source']['tree'], 'version':a['version'], 'authorityCommit':q['authorityCommit'],
            'controllerCommits':tuple(sorted({row['controller']['commit'] for row in rows if row['id'] in {x['admission_id'] for x in a['components'].values()}})),
            'wheelSha256':selected['wheelSha256'], 'nativeSha256':selected['nativeSha256'],
            'platforms':CORE_PLATFORMS, 'sdkChecks':CORE_SDK_CHECKS, 'cells':CORE_CELLS,
            'scope':'Original selected Core SDK/platform/browser material readiness; no upstream release promotion'}
