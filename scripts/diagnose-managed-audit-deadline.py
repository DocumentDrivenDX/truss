#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Run one unchanged audit deadline case with bounded PostgreSQL diagnostics."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
import traceback
import zipfile
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
MODULE = "test_audit_disclosure_native.AuditDisclosureNativeTests.test_whole_group_more_than_1024_events_uses_separate_event_budget"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cpu_model() -> Optional[str]:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith(("model name", "hardware")):
                return line.split(":", 1)[-1].strip()[:200]
    except OSError:
        pass
    return None


def exact_wheel_payload(wheel: Path, loaded_package: Path) -> dict:
    with zipfile.ZipFile(wheel) as archive:
        members = {name.removeprefix("truss/"): archive.read(name)
                   for name in archive.namelist()
                   if name.startswith("truss/") and not name.endswith("/")}
    actual = {path.relative_to(loaded_package).as_posix(): path.read_bytes()
              for path in loaded_package.rglob("*") if path.is_file()
              and "__pycache__" not in path.parts and path.suffix != ".pyc"}
    if members != actual:
        missing = sorted(set(members) ^ set(actual))[:20]
        differing = sorted(name for name in members.keys() & actual.keys()
                           if members[name] != actual[name])[:20]
        raise RuntimeError(f"Installed Truss payload differs from selected wheel: paths={missing}, bytes={differing}")
    return {"members": len(members), "exact": True}


def test_source_path() -> Path:
    return ROOT / "packages/python/tests/test_audit_disclosure_native.py"


def write_bootstrap(path: Path) -> None:
    # This code runs only in the child test process. It logs templates and hashes,
    # never bound values or connection strings, and preserves every original call.
    path.write_text(r'''import hashlib,json,os,re,threading,time,unittest
from pathlib import Path
import psycopg

TRACE=Path(os.environ["TRUSS_DIAGNOSTIC_TRACE"])
Path(os.environ["TRUSS_DIAGNOSTIC_BOOTSTRAP_MARKER"]).write_text("loaded\n",encoding="utf-8")
LOCK=threading.Lock()
QUERIES=[]
CANDIDATES=[]
TARGET_ACTIVE=False
TARGET="test_audit_disclosure_native.AuditDisclosureNativeTests.test_whole_group_more_than_1024_events_uses_separate_event_budget"

def _raw(query, connection=None):
    try:
        return query if isinstance(query,str) else query.as_string(connection) if hasattr(query,"as_string") else repr(query)
    except Exception:
        return repr(query)

def _safe(query,connection=None):
    text=_raw(query,connection)
    text=re.sub(r"'(?:''|[^'])*'", "'<literal>'", text)
    text=re.sub(r'\b[0-9]+(?:\.[0-9]+)?\b', '<number>', text)
    return text[:12000]

def _diag(error):
    d=getattr(error,"diag",None)
    names=("severity","sqlstate","message_primary","message_detail","message_hint","context","schema_name","table_name","column_name","constraint_name","statement_position","internal_position","internal_query")
    values={}
    if d is not None:
        for name in names:
            value=getattr(d,name,None)
            values[name]=(_safe(str(value)) if name in ("context","internal_query")
                          else str(value)[:4000]) if value is not None else None
    return {"type":type(error).__name__,"text":str(error)[:4000],"sqlstate":getattr(error,"sqlstate",None),"diag":values}

def _record(query, elapsed, error=None, kind="execute", connection=None):
    raw=_raw(query,connection)
    safe_sql=_safe(query,connection)
    match=re.match(r"\s*([A-Za-z]+)",safe_sql)
    row={"kind":kind,"statementClass":match.group(1).upper() if match else "OTHER","durationSeconds":elapsed,"statementSha256":hashlib.sha256(raw.encode("utf-8","replace")).hexdigest(),"safeSql":safe_sql,"error":_diag(error) if error else None}
    with LOCK:
        QUERIES.append(row)
        if len(QUERIES)>20000: QUERIES.pop(0)
    return row

def _candidate(row,query,args,kwargs):
    if TARGET_ACTIVE and row.get("safeSql","").lstrip().upper().startswith("SELECT"):
        params=args[0] if args else kwargs.get("params")
        CANDIDATES.append((row,query,params))

_execute=psycopg.Cursor.execute
def _timed_execute(self,query,*args,**kwargs):
    started=time.monotonic()
    try:
        result=_execute(self,query,*args,**kwargs)
        row=_record(query,time.monotonic()-started,connection=self.connection)
        _candidate(row,query,args,kwargs)
        return result
    except BaseException as error:
        row=_record(query,time.monotonic()-started,error,connection=self.connection)
        _candidate(row,query,args,kwargs)
        raise
psycopg.Cursor.execute=_timed_execute

_executemany=psycopg.Cursor.executemany
def _timed_executemany(self,query,*args,**kwargs):
    started=time.monotonic()
    try:
        result=_executemany(self,query,*args,**kwargs)
        _record(query,time.monotonic()-started,kind="executemany",connection=self.connection)
        return result
    except BaseException as error:
        _record(query,time.monotonic()-started,error,kind="executemany",connection=self.connection)
        raise

psycopg.Cursor.executemany=_timed_executemany

def _maybe_explain(test):
    failures=[]
    hosts=[]
    for connection,host in getattr(test,"consumer_connections",[]):
        attempt=getattr(getattr(host,"_custody",None),"last_attempt",None)
        error=getattr(attempt,"error",None)
        if error is not None: hosts.append(_diag(error))
    failures.append({"consumerHostAttempts":hosts})
    if CANDIDATES:
        failing=[item for item in CANDIDATES if item[0].get("error")]
        row,query,params=max(failing or CANDIDATES,key=lambda item:item[0]["durationSeconds"])
        result={"statementSha256":row["statementSha256"],"explain":"not attempted","plan":None}
        try:
            connections=getattr(test,"consumer_connections",[])
            if not connections: raise RuntimeError("Original consumer connection is unavailable")
            original_connection=connections[-1][0]
            with psycopg.connect(original_connection.info.dsn,options="-c statement_timeout=10000 -c default_transaction_read_only=on",autocommit=True) as observer:
                with observer.cursor() as cursor:
                    rendered=query if isinstance(query,str) else query.as_string(observer)
                    cursor.execute("EXPLAIN (FORMAT JSON, VERBOSE, COSTS TRUE) "+rendered,params)
                    plan=cursor.fetchone()[0]
                    encoded=json.dumps(plan,sort_keys=True,default=str)
                    if len(encoded.encode("utf-8"))<=2*1024*1024:
                        result["plan"]=plan
                    else:
                        result["plan"]={"truncated":True,"bytes":len(encoded.encode("utf-8")),"sha256":hashlib.sha256(encoded.encode("utf-8")).hexdigest(),"prefix":encoded[:4096]}
            result["explain"]="estimated plan only; ANALYZE was not requested"
        except BaseException as error:
            result["explainError"]=_diag(error)
        failures.append(result)
    with Path(os.environ["TRUSS_DIAGNOSTIC_FAILURES"]).open("w",encoding="utf-8") as out:
        json.dump(failures,out,indent=2,default=str)

def _flush():
    with TRACE.open("w",encoding="utf-8") as out:
        for row in QUERIES: out.write(json.dumps(row,sort_keys=True)+"\n")

import test_audit_disclosure_native as _audit
_target=getattr(_audit.AuditDisclosureNativeTests,"test_whole_group_more_than_1024_events_uses_separate_event_budget")
def _diagnose_target(self,*args,**kwargs):
    global TARGET_ACTIVE
    TARGET_ACTIVE=True
    try: return _target(self,*args,**kwargs)
    except BaseException:
        _maybe_explain(self)
        raise
    finally:
        TARGET_ACTIVE=False
        _flush()
_diagnose_target.__name__=_target.__name__
_diagnose_target.__doc__=_target.__doc__
_diagnose_target.__qualname__=_target.__qualname__
_audit.AuditDisclosureNativeTests.test_whole_group_more_than_1024_events_uses_separate_event_budget=_diagnose_target
''', encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    wheel = args.wheel.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite diagnostic output: {output}")
    output.mkdir(parents=True)

    import pgserver
    import psycopg
    import truss
    from truss._runtime_profile import SERVER_VERSION
    from native_fixture import WorkerCluster

    dist = importlib.metadata.distribution("truss-toolkit")
    version = dist.version
    if version != args.expected_version:
        raise RuntimeError(f"Installed Truss version {version} != expected {args.expected_version}")
    loaded_package = Path(truss.__file__).resolve().parent
    if loaded_package.is_relative_to(ROOT / "packages"):
        raise RuntimeError("Source-checkout Truss import is forbidden")
    payload = exact_wheel_payload(wheel, loaded_package)
    target_source_sha = sha256(test_source_path())
    import weft
    weft_native=importlib.import_module("weft.weft")
    weft_dist = importlib.metadata.distribution("weft-sql")
    pgserver_version=importlib.metadata.version("pgserver-pg18")
    if pgserver_version != "18.6.1":
        raise RuntimeError(f"Expected public pgserver-pg18 18.6.1, got {pgserver_version}")
    if weft_dist.version != "0.4.51":
        raise RuntimeError(f"Expected public weft-sql 0.4.51, got {weft_dist.version}")
    direct_urls = {}
    for name in ("truss-toolkit", "pgserver-pg18", "weft-sql"):
        raw = importlib.metadata.distribution(name).read_text("direct_url.json")
        direct_urls[name] = json.loads(raw) if raw else None

    start = time.monotonic()
    system_before = {"loadAverage": os.getloadavg() if hasattr(os, "getloadavg") else None,
                     "cpuCount": os.cpu_count(), "cpuModel": cpu_model()}
    worker_results = {}
    test_results = {}
    trace = output / "instrumented/cursor-statements.jsonl"
    failure_path = output / "instrumented/failure-diagnostics.json"
    for label, instrumented in (("original", False), ("instrumented", True)):
        case_output = output / label
        case_output.mkdir()
        env = dict(os.environ)
        python_path = [str(ROOT / "scripts"), str(ROOT / "packages/python/tests")]
        bootstrap_marker = case_output / "bootstrap-loaded"
        if instrumented:
            bootstrap = output / "instrumented/bootstrap"
            bootstrap.mkdir(parents=True)
            write_bootstrap(bootstrap / "sitecustomize.py")
            trace.parent.mkdir(exist_ok=True)
            trace.touch()
            python_path.insert(0, str(bootstrap))
            env["TRUSS_DIAGNOSTIC_TRACE"] = str(trace)
            env["TRUSS_DIAGNOSTIC_FAILURES"] = str(failure_path)
            env["TRUSS_DIAGNOSTIC_BOOTSTRAP_MARKER"] = str(bootstrap_marker)
        env["PYTHONPATH"] = os.pathsep.join(python_path)
        env["TRUSS_CENSUS_POSTGRES_BIN"] = str(Path(pgserver.__file__).resolve().parent / "pginstall/bin")
        command = [sys.executable, str(ROOT / "scripts/run-python-test-module.py"), MODULE, "-v"]
        (case_output / "command.json").write_text(json.dumps({"argv": command, "test": MODULE,
            "instrumented": instrumented, "python": sys.version, "trussVersion": version,
            "postgresqlExpected": SERVER_VERSION, "statementTimeoutMs": 10000,
            "operationTimeoutMs": 30000}, indent=2) + "\n")
        metadata = {"inventoryRestored": False, "serverStoppedAndDirectoryRemoved": False}
        result = None
        try:
            with WorkerCluster() as worker:
                if worker.settings.get("server_version") != SERVER_VERSION:
                    raise RuntimeError(f"Worker PostgreSQL {worker.settings.get('server_version')} != {SERVER_VERSION}")
                metadata.update(settings=worker.settings, baselineDigest=hashlib.sha256(
                    json.dumps(worker.baseline, sort_keys=True, default=str).encode()).hexdigest())
                try:
                    result = subprocess.run(command, cwd=sys.prefix, env={**env, **worker.environment()},
                                            capture_output=True, timeout=120)
                    (case_output / "unittest.log").write_bytes(result.stdout + result.stderr)
                except subprocess.TimeoutExpired as error:
                    (case_output / "unittest.log").write_bytes((error.stdout or b"") + (error.stderr or b"") + b"\nDiagnostic outer watchdog expired at 120 seconds.\n")
                    result = subprocess.CompletedProcess(command, 124)
                worker.verify_clean()
                metadata["inventoryRestored"] = True
            metadata["serverStoppedAndDirectoryRemoved"] = True
        except BaseException as error:
            metadata["phaseError"] = f"{type(error).__name__}: {str(error)[:4000]}"
            (case_output / "driver-error.log").write_text(traceback.format_exc()[-16000:])
        worker_results[label] = metadata
        if result is None:
            test_results[label] = {"passed": False, "exitCode": 125, "instrumented": instrumented,
                                   "instrumentationLoaded": bootstrap_marker.exists() if instrumented else None}
        else:
            test_results[label] = {"passed": result.returncode == 0, "exitCode": result.returncode,
                                   "instrumented": instrumented,
                                   "instrumentationLoaded": bootstrap_marker.exists() if instrumented else None}
        if not metadata["inventoryRestored"] or not metadata["serverStoppedAndDirectoryRemoved"]:
            break

    if sha256(test_source_path()) != target_source_sha:
        raise RuntimeError("Audit test source changed during diagnostic execution")

    receipt = {
        "cohort": args.cohort,
        "passed": len(test_results) == 2 and all(item["passed"] for item in test_results.values())
                  and all(item["inventoryRestored"] and item["serverStoppedAndDirectoryRemoved"]
                          for item in worker_results.values())
                  and test_results["instrumented"]["instrumentationLoaded"]
                  and bool(trace.exists() and trace.stat().st_size),
        "test": MODULE,
        "testSource": {"path": "packages/python/tests/test_audit_disclosure_native.py",
                       "sha256": target_source_sha},
        "diagnosticOnly": True,
        "instrumentationCanAffectTiming": True,
        "originalTestResultIsUninstrumented": test_results.get("original"),
        "instrumentedDiagnosticResult": test_results.get("instrumented"),
        "retries": 0,
        "limitsMs": {"statement": 10000, "operation": 30000, "outerWatchdog": 120000},
        "python": sys.version,
        "platform": platform.platform(),
        "cpuCount": os.cpu_count(),
        "cpuModel": cpu_model(),
        "loadAverage": os.getloadavg() if hasattr(os, "getloadavg") else None,
        "systemBefore": system_before,
        "systemAfter": {"loadAverage": os.getloadavg() if hasattr(os, "getloadavg") else None,
                        "cpuCount": os.cpu_count(), "cpuModel": cpu_model()},
        "truss": {"version": version, "wheel": str(wheel), "wheelSha256": sha256(wheel),
                  "loadedFrom": str(loaded_package), "payload": payload,
                  "installationOrigin": direct_urls["truss-toolkit"]},
        "postgresql": {"serverVersion": SERVER_VERSION,
                       "pgserverDistribution": pgserver_version,
                       "pgserverModule": str(Path(pgserver.__file__).resolve()),
                       "installationOrigin": direct_urls["pgserver-pg18"]},
        "psycopg": {"version": psycopg.__version__, "module": str(Path(psycopg.__file__).resolve())},
        "weft": {"version": weft_dist.version, "module": str(Path(weft.__file__).resolve()),
                 "installationOrigin": direct_urls["weft-sql"]},
        "weftNative": {"module": str(Path(weft_native.__file__).resolve()),
                       "sha256": sha256(Path(weft_native.__file__).resolve())},
        "sourceRevision": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         capture_output=True, text=True, check=True).stdout.strip(),
        "driverSha256": sha256(Path(__file__).resolve()),
        "workers": worker_results,
        "elapsedSeconds": time.monotonic() - start,
        "cursorTrace": {"path": str(trace.relative_to(output)), "sha256": sha256(trace) if trace.exists() else None,
                        "statementCount": sum(1 for _ in trace.open()) if trace.exists() else 0},
        "failureDiagnostics": str(failure_path.relative_to(output)) if failure_path.exists() else None,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"passed": receipt["passed"], "cohort": args.cohort,
                      "original": test_results.get("original"),
                      "instrumented": test_results.get("instrumented"),
                      "receipt": str(output / "receipt.json")}))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
