#!/usr/bin/env python3
"""Reclaim only unused SDKs on GitHub-hosted runners for the exact large stress case."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path


TARGET_FREE_BYTES = 64 * 1024**3
LINUX_UNUSED_SDKS = (
    Path("/usr/local/lib/android"),
    Path("/usr/share/dotnet"),
    Path("/opt/ghc"),
)
MACOS_COMMAND_LINE_TOOLS = Path("/Library/Developer/CommandLineTools")


def require_github_hosted_runner() -> tuple[str, Path, Path]:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("runner cleanup is restricted to GitHub Actions")
    if os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted":
        raise RuntimeError("runner cleanup is restricted to GitHub-hosted runners")

    runner_os = os.environ.get("RUNNER_OS")
    expected_os = {"Linux": "Linux", "macOS": "Darwin"}.get(runner_os or "")
    if expected_os is None or platform.system() != expected_os:
        raise RuntimeError(f"unsupported or mismatched hosted runner OS: {runner_os!r}")

    workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve(strict=True)
    current = Path.cwd().resolve(strict=True)
    if workspace not in (current, *current.parents):
        raise RuntimeError("current directory is outside GITHUB_WORKSPACE")
    runner_temp = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    return runner_os, workspace, runner_temp


def df_snapshot(path: Path) -> dict[str, object]:
    completed = subprocess.run(
        ["df", "-Pk", str(path)], check=True, capture_output=True, text=True
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        raise RuntimeError(f"could not parse df output for {path}")
    columns = lines[-1].split()
    if len(columns) < 6:
        raise RuntimeError(f"unexpected df output for {path}: {lines[-1]!r}")
    available_bytes = int(columns[3]) * 1024
    return {
        "filesystem": columns[0],
        "totalBytes": int(columns[1]) * 1024,
        "usedBytes": int(columns[2]) * 1024,
        "availableBytes": available_bytes,
        "availableGiB": round(available_bytes / 1024**3, 2),
        "line": lines[-1],
    }


def remove_exact_sdk(path: Path, expected_parent: Path, command=None) -> str:
    if path.parent != expected_parent or path.name in ("", ".", ".."):
        raise RuntimeError(f"refusing unexpected SDK path: {path}")
    if not path.exists() and not path.is_symlink():
        return f"absent: {path}"
    if path.is_symlink():
        raise RuntimeError(f"refusing to remove SDK symlink: {path}")
    if not path.is_dir():
        raise RuntimeError(f"refusing to remove non-directory SDK path: {path}")
    resolved = path.resolve(strict=True)
    resolved_parent = expected_parent.resolve(strict=True)
    if resolved != resolved_parent / path.name:
        raise RuntimeError(f"refusing SDK path that resolves elsewhere: {path} -> {resolved}")
    if command is None:
        command = subprocess.run
    command(["sudo", "rm", "-rf", "--", str(path)], check=True)
    return f"removed: {path}"


def reclaim_linux(command=None) -> list[str]:
    outcomes = []
    for sdk in LINUX_UNUSED_SDKS:
        outcomes.append(remove_exact_sdk(sdk, sdk.parent, command))
    return outcomes


def reclaim_macos(command=None, applications: Path = Path("/Applications"),
                  command_line_tools: Path = MACOS_COMMAND_LINE_TOOLS) -> list[str]:
    outcomes = []
    if command is None:
        command = subprocess.run
    if not command_line_tools.is_dir():
        raise RuntimeError(f"required CommandLineTools directory is missing: {command_line_tools}")
    command(
        ["sudo", "/usr/bin/xcode-select", "--switch", str(command_line_tools)],
        check=True,
    )
    selected = Path(command(
        ["/usr/bin/xcode-select", "--print-path"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()).resolve(strict=True)
    if selected != command_line_tools.resolve(strict=True):
        raise RuntimeError(f"CommandLineTools was not selected: {selected}")
    outcomes.append(f"selected: {selected}")

    for xcode in sorted(applications.glob("Xcode*.app")):
        if xcode.parent != applications or not xcode.name.startswith("Xcode") or not xcode.name.endswith(".app"):
            raise RuntimeError(f"refusing unexpected Xcode path: {xcode}")
        if xcode.is_symlink():
            outcomes.append(f"skipped symlink: {xcode}")
            continue
        outcomes.append(remove_exact_sdk(xcode, applications, command))
    return outcomes


def main() -> int:
    # Check the runner identity before inspecting or changing any SDK path.
    runner_os, workspace, runner_temp = require_github_hosted_runner()
    output_dir = runner_temp / "public-stress"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "runner-capacity.json"
    report: dict[str, object] = {
        "runnerEnvironment": os.environ.get("RUNNER_ENVIRONMENT"),
        "runnerOS": runner_os,
        "targetFreeBytes": TARGET_FREE_BYTES,
        "targetFreeGiB": TARGET_FREE_BYTES / 1024**3,
        "workspace": str(workspace),
    }
    try:
        report["before"] = df_snapshot(workspace)
        if runner_os == "Linux":
            report["reclamation"] = reclaim_linux()
        else:
            report["reclamation"] = reclaim_macos()
        report["after"] = df_snapshot(workspace)
        available = int(report["after"]["availableBytes"])  # type: ignore[index]
        report["reclaimedAvailableBytes"] = available - int(report["before"]["availableBytes"])  # type: ignore[index]
        report["status"] = "ready" if available >= TARGET_FREE_BYTES else "capacity-refusal"
        if available < TARGET_FREE_BYTES:
            report["reason"] = "available filesystem space remains below the 64 GiB large-workload target"
    except Exception as error:
        report["status"] = "capacity-refusal"
        report["error"] = f"{type(error).__name__}: {error}"
        try:
            report["after"] = df_snapshot(workspace)
        except Exception as df_error:
            report["afterDfError"] = f"{type(df_error).__name__}: {df_error}"

    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "ready":
        print("CAPACITY REFUSAL: large stress workload will not run on this runner.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"REFUSING runner cleanup: {error}", file=sys.stderr)
        raise SystemExit(2)
