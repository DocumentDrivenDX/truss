#!/usr/bin/env python3
"""Validate already-published release archives before a PyPI OIDC upload."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import re
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from email.parser import BytesParser
from pathlib import Path
from typing import Any

SHA = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
TAG = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")


class ReleaseError(ValueError):
    pass


def _version_tuple(version: str) -> tuple[int, int, int]:
    if not re.fullmatch(
        r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version
    ):
        raise ReleaseError("version must be numeric X.Y.Z")
    major, minor, patch = (int(part) for part in version.split("."))
    return major, minor, patch


def distribution_for_version(version: str) -> str:
    """Keep immutable historical names while selecting the renamed cohort."""
    return "truss-toolkit" if _version_tuple(version) <= (0, 0, 50) else "umf-truss"


def wheel_prefix_for_version(version: str) -> str:
    normalized = re.sub(r"[-_.]+", "_", distribution_for_version(version))
    return f"{normalized}-{version}-"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseError(message)


def _exact_tag_proof(release, tag_ref, tag_object, producer_run, producer_jobs,
                     *, repository, source_sha, tag):
    """Validate the successful tag workflow's fixed package/native/release job graph."""
    _require(type(producer_run) is dict and type(producer_jobs) is dict,
             "temporal publication requires authenticated exact-tag producer run and jobs")
    run_id = str(producer_run.get("id", ""))
    attempt = str(producer_run.get("run_attempt", ""))
    _require(run_id.isdecimal() and int(run_id) > 0 and attempt.isdecimal() and int(attempt) > 0,
             "exact-tag producer run/attempt identity is missing")
    _require(producer_run.get("path") == ".github/workflows/release.yml"
             and producer_run.get("event") == "workflow_dispatch"
             and producer_run.get("head_branch") == tag
             and producer_run.get("head_sha") == source_sha
             and producer_run.get("conclusion") == "success"
             and producer_run.get("repository", {}).get("full_name") == repository,
             "exact-tag producer run is not the successful selected release source")
    referenced_workflows = producer_run.get("referenced_workflows")
    _require(type(referenced_workflows) is list and not referenced_workflows,
             "exact-tag producer has unvalidated nested reusable workflows")
    jobs = producer_jobs.get("jobs")
    _require(type(jobs) is list, "exact-tag producer job receipt is malformed")
    required = {"package", "native (ubuntu-24.04)", "publish"}
    required_steps = {
        "package": {
            "Check active HF release cohort bindings",
            "Verify reproducible embedded owner delivery assets",
            "Verify complete source payload in wheel and sdist",
        },
        "native (ubuntu-24.04)": {
            "Install exact released compiler and verify its checksum",
            "Qualify the installed standalone local carrier and retained refusals",
            "Qualify the installed fresh baseline and refusal controls",
            "Qualify the installed final package with independent HF assertions",
            "Qualify installed managed platform grants and contained refusals",
            "Verify installed embedded owners with every subprocess forbidden",
            "Run the installed public adopter workflow",
            "Run installed current-policy query and activation workflows",
            "Run exact installed compiler cohort and asset-cache unit module",
        },
        "publish": {"Record exact assets and publish"},
    }
    selected = {}
    for job in jobs:
        if type(job) is dict and job.get("name") in required:
            name = job["name"]
            _require(name not in selected, "exact-tag producer has duplicate required jobs")
            selected[name] = job
    _require(set(selected) == required, "exact-tag package/native/release jobs are incomplete")
    for name, job in selected.items():
        _require(job.get("conclusion") == "success"
                 and str(job.get("run_id")) == run_id
                 and str(job.get("run_attempt")) == attempt
                 and job.get("head_sha", source_sha) == source_sha,
                 "exact-tag required job did not succeed on the authenticated run: " + name)
        steps = job.get("steps")
        _require(type(steps) is list, "exact-tag required job has no step evidence: " + name)
        observed = {}
        for step in steps:
            if type(step) is dict and type(step.get("name")) is str:
                step_name = step["name"]
                _require(step_name not in observed, "exact-tag job has duplicate step evidence: " + name)
                observed[step_name] = step.get("conclusion")
        missing_steps = sorted(required_steps[name] - set(observed))
        failed_steps = sorted(step for step in required_steps[name] if observed.get(step) != "success")
        _require(not missing_steps and not failed_steps,
                 "exact-tag owner/platform/SDK/public-dependency step evidence is incomplete for "
                 + name + ": " + ", ".join(missing_steps + failed_steps))
    _require(release.get("tag_name") == tag and release.get("draft") is False
             and release.get("prerelease") is False
             and resolve_tag_commit(tag_ref, tag_object, tag) == source_sha,
             "exact-tag release/ref/object does not resolve to authenticated source")
    return {"runId": run_id, "attempt": attempt, "sourceCommit": source_sha,
            "tag": tag, "jobs": tuple(sorted(("native","package","publish"))),
            "jobStepEvidence": {name: tuple(sorted(required_steps[name])) for name in sorted(required_steps)},
            "nestedReusableWorkflows": (), "releaseId": str(release.get("id", ""))}


def _load_weft_owner_release(directory: Path) -> dict[str, Any]:
    """Load the selected immutable Weft release API record and existing assets."""
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
    api_path = directory / "release-api.json"
    _require(api_path.is_file() and not api_path.is_symlink(),
             "Missing upstream Weft GitHub release API receipt")
    assets = {}
    for name in required:
        path = directory / name
        _require(path.is_file() and not path.is_symlink(),
                 "Missing upstream Weft owner proof asset: " + name)
        assets[name] = path.read_bytes()
    return {"releaseApi": json.loads(api_path.read_bytes()), "assetBytes": assets}


def _temporal_owner_readiness(verified, owner_release, core_owner_proofs):
    from component_prerequisite_validators import (validate_core_selected_owner_proofs,
        validate_weft_published_owner_proofs)
    core = validate_core_selected_owner_proofs(core_owner_proofs, selected=verified['selectedCore'])
    _require(type(owner_release) is dict,
             "Temporal prepublication requires authenticated upstream Weft owner release receipts")
    source = verified['weftOwnerSource']
    weft = validate_weft_published_owner_proofs(owner_release,
        source_commit=source['sourceCommit'], source_tree=source['sourceTree'],
        canonical_umf=source['canonicalCoreSourceCommit'], cargo_lock_sha256=source['cargoLockSha256'])
    return {'core':core, 'weft':weft}


def _load_core_owner_proofs(directory: Path, selected):
    """Read existing retained SDK material; committed cohort alone selects P.

    Inputs are existing registry/controller files, original-provenance-ID.json
    and retained member bytes. No retrieval, qualification or owner code runs.
    Content hashes locate copied files without relabeling their original names.
    """
    _require(type(selected) is dict and type(selected.get('qualification')) is dict,
             "Missing trusted selected Core owner admission")
    blobs = {}; provenance = {}; readiness = []
    _require(directory.is_dir() and not directory.is_symlink(), 'Core original material directory missing')
    for path in directory.rglob('*'):
        _require(not path.is_symlink(), 'Symlink in Core original material directory')
        if not path.is_file():continue
        raw = path.read_bytes(); blobs[_sha(raw)] = raw
        if path.suffix != '.json':continue
        try:value = json.loads(raw)
        except (ValueError, UnicodeDecodeError):continue
        if type(value) is not dict:continue
        if path.name.startswith('original-provenance-') and path.name.endswith('.json'):
            _require(path.name not in provenance, 'Duplicate Core original provenance')
            provenance[path.name] = value
        if value.get('profile') == 'umf.core-successor.material-readiness/1':readiness.append(raw)
    q = selected['qualification']; registry_raw = blobs.get(q['registrySha256'])
    _require(type(registry_raw) is bytes, 'Missing immutable selected P registry bytes')
    registry = json.loads(registry_raw)
    matches = [row for row in registry['admissions'] if row['id'] == q['admissionId']]
    _require(len(matches) == 1, 'Missing trusted selected Core owner admission')
    aggregate = matches[0]; materials = {}; controllers = {}
    for platform, binding in aggregate['components'].items():
        comp = next(row for row in registry['admissions'] if row['id'] == binding['admission_id'])
        ctrl = comp['controller']; controllers[ctrl['commit']] = {
            'script':blobs.get(ctrl['script_sha256']), 'workflow':blobs.get(ctrl['workflow_sha256'])}
        records = {}
        for material in [binding['material'], comp.get('common'), comp.get('continuation')]:
            if material is None:continue
            proofs = ([material['proof'], *[row['provenance'] for row in material['envelopes']]]
                      if material.get('profile') == 'umf.core-successor.multipart-material/1' else [material])
            for proof in proofs:
                original = provenance.get('original-provenance-'+str(proof['artifact'])+'.json')
                _require(type(original) is dict and original.get('binding') == proof,
                         'Missing/misbound original Core run/job/artifact provenance')
                records[str(proof['artifact'])] = {key:original[key] for key in ('run','job','artifact')} | {
                    'memberBytes':{name:blobs.get(digest) for name,digest in proof['members'].items()}}
        materials[platform] = records
    matching = {raw for raw in readiness if json.loads(raw).get('source') == aggregate['source']
                and json.loads(raw).get('version') == aggregate['version']}
    _require(len(matching) == 1, 'Missing/ambiguous original Core material readiness')
    return {'registryBytes':registry_raw, 'controllerBytes':controllers,
            'materials':materials, 'readinessBytes':matching.pop()}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_sums(data: bytes) -> dict[str, str]:
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ReleaseError("SHA256SUMS is not ASCII") from exc
    result: dict[str, str] = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.+-]+)", line)
        _require(match is not None, "SHA256SUMS has a malformed entry")
        assert match is not None
        digest, filename = match.groups()
        _require(filename not in result, "SHA256SUMS has duplicate filenames")
        result[filename] = digest
    _require(bool(result), "SHA256SUMS is empty")
    return result


def _metadata(raw: bytes, distribution: str, version: str) -> None:
    message = BytesParser().parsebytes(raw)
    _require(
        message.get("Name") == distribution,
        "archive metadata distribution name differs",
    )
    _require(message.get("Version") == version, "archive metadata version differs")
    _require(
        not any("@" in item for item in message.get_all("Requires-Dist", [])),
        "archive metadata contains a direct URL dependency",
    )

    if version == "0.0.56":
        requirements = message.get_all("Requires-Dist", [])
        for pin, extra in (("umf-weft==0.4.57", "query"), ("umf-access==0.1.0.dev10", "typed-sdk")):
            matches = [item.partition(';')[0].strip().replace('_', '-') for item in requirements
                       if item.partition(';')[2].strip().replace("'", '"') == f'extra == "{extra}"']
            _require(matches == [pin], "selected release extra missing or changed: " + extra)
        _require(not any(re.match(r"weft[-_.]sql\b", item, re.I) for item in requirements),
                 "legacy weft-sql dependency conflicts with selected compiler")


def validate_archive(path: Path, distribution: str, version: str) -> None:
    if path.name.endswith(".whl"):
        try:
            with zipfile.ZipFile(path) as archive:
                names = [
                    name
                    for name in archive.namelist()
                    if name.endswith(".dist-info/METADATA")
                ]
                _require(
                    len(names) == 1, "wheel must contain exactly one METADATA file"
                )
                _metadata(archive.read(names[0]), distribution, version)
        except (OSError, zipfile.BadZipFile) as exc:
            raise ReleaseError("wheel archive is invalid") from exc
    elif path.name.endswith(".tar.gz"):
        try:
            with tarfile.open(path, "r:gz") as archive:
                members = [
                    item
                    for item in archive.getmembers()
                    if item.isfile() and item.name.endswith("/PKG-INFO")
                ]
                root_metadata = [item for item in members if item.name.count("/") == 1]
                _require(
                    len(root_metadata) == 1,
                    "sdist must contain exactly one root PKG-INFO file",
                )
                for member in members:
                    stream = archive.extractfile(member)
                    _require(stream is not None, "sdist PKG-INFO cannot be read")
                    assert stream is not None
                    _metadata(stream.read(), distribution, version)
        except (OSError, tarfile.TarError) as exc:
            raise ReleaseError("source archive is invalid") from exc
    else:
        raise ReleaseError("unsupported distribution archive")


def resolve_tag_commit(
    ref: dict[str, Any], annotated: dict[str, Any] | None, expected_tag: str
) -> str:
    _require(
        ref.get("ref") == f"refs/tags/{expected_tag}", "tag reference is malformed"
    )
    obj = ref.get("object")
    _require(isinstance(obj, dict), "tag reference object is missing")
    sha = obj.get("sha")
    kind = obj.get("type")
    _require(
        isinstance(sha, str) and COMMIT.fullmatch(sha) is not None,
        "tag object SHA is invalid",
    )
    if kind == "commit":
        _require(
            annotated is None, "lightweight tag unexpectedly has an annotated object"
        )
        return sha
    _require(
        kind == "tag" and isinstance(annotated, dict), "annotated tag object is missing"
    )
    assert isinstance(annotated, dict)
    _require(annotated.get("sha") == sha, "annotated tag object identity differs")
    target = annotated.get("object")
    _require(
        isinstance(target, dict) and target.get("type") == "commit",
        "tag target is not a commit",
    )
    assert isinstance(target, dict)
    target_sha = target.get("sha")
    _require(
        isinstance(target_sha, str) and COMMIT.fullmatch(target_sha) is not None,
        "tag target SHA is invalid",
    )
    return target_sha


def prepare_release(
    *,
    repository: str,
    release: dict[str, Any],
    tag_ref: dict[str, Any],
    tag_object: dict[str, Any] | None,
    assets_dir: Path,
    output_dir: Path,
    tag: str,
    source_sha: str,
    expected_source_tree: str | None = None,
    expected_sums_sha256: str,
    distribution: str,
    wheel_prefix: str,
    wheel_count: int,
    require_sdist: bool,
    producer_run: dict[str, Any] | None = None,
    producer_jobs: dict[str, Any] | None = None,
    owner_release: dict[str, Any] | None = None,
    core_owner_proofs: dict[str, Any] | None = None,
    allowed_workflow_paths: set[str] | None = None,
    allowed_workflow_prefixes: tuple[str, ...] = (),
) -> dict[str, Any]:
    _require(TAG.fullmatch(tag) is not None, "tag must be numeric vX.Y.Z")
    _require(COMMIT.fullmatch(source_sha) is not None, "source SHA is invalid")
    if expected_source_tree is not None:
        _require(COMMIT.fullmatch(expected_source_tree) is not None, "source tree is invalid")
    _require(
        SHA.fullmatch(expected_sums_sha256) is not None, "SHA256SUMS pin is invalid"
    )
    _require(
        release.get("tag_name") == tag
        and release.get("draft") is False
        and release.get("prerelease") is False,
        "release is absent, draft, prerelease or for another tag",
    )
    _require(
        resolve_tag_commit(tag_ref, tag_object, tag) == source_sha,
        "tag does not resolve to the pinned source",
    )
    if producer_run is not None:
        _require(
            producer_run.get("conclusion") == "success",
            "release producer run did not succeed",
        )
        producer_repo = producer_run.get("repository")
        _require(
            isinstance(producer_repo, dict)
            and producer_repo.get("full_name") == repository,
            "release producer repository differs",
        )
        _require(
            producer_run.get("event") in {"push", "workflow_dispatch"}
            and producer_run.get("head_sha") == source_sha,
            "release producer event or source commit differs",
        )
        producer_path = producer_run.get("path")
        prefix_match = isinstance(producer_path, str) and any(
            producer_path.startswith(prefix)
            and re.fullmatch(r"[A-Za-z0-9_.-]+\.yml", producer_path[len(prefix) :])
            is not None
            for prefix in allowed_workflow_prefixes
        )
        _require(
            producer_path in (allowed_workflow_paths or set()) or prefix_match,
            "release producer workflow is not allowed",
        )
        if producer_path in (allowed_workflow_paths or set()):
            _require(
                producer_run.get("head_branch") == tag,
                "release producer did not run on the tagged source",
            )
        if prefix_match:
            _require(
                producer_run.get("event") == "workflow_dispatch",
                "selected release publisher must be manually dispatched",
            )
            basename = producer_path.rsplit("/", 1)[-1]
            match = re.fullmatch(
                r"release-selected-publish-(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.yml",
                basename,
            )
            _require(
                match is not None and "v" + ".".join(match.groups()) == tag,
                "selected release workflow does not identify this tag version",
            )
            try:
                run_start = datetime.fromisoformat(
                    producer_run["created_at"].replace("Z", "+00:00")
                )
                run_end = datetime.fromisoformat(
                    producer_run["updated_at"].replace("Z", "+00:00")
                )
                release_published = datetime.fromisoformat(
                    release["published_at"].replace("Z", "+00:00")
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ReleaseError(
                    "selected release publication window is missing"
                ) from exc
            _require(
                run_start <= release_published <= run_end,
                "selected release publication is outside its successful workflow run",
            )
    version = tag[1:]
    _require(
        distribution == distribution_for_version(version)
        and wheel_prefix == wheel_prefix_for_version(version),
        "distribution or wheel prefix differs from the versioned release cohort",
    )
    if distribution == "umf-truss":
        _require(release.get("immutable") is True, "renamed release must be immutable")
    raw_assets = release.get("assets")
    _require(isinstance(raw_assets, list), "release asset inventory is missing")
    assets: dict[str, dict[str, Any]] = {}
    for item in raw_assets:
        _require(
            isinstance(item, dict) and isinstance(item.get("name"), str),
            "release has an invalid asset",
        )
        name = item["name"]
        _require(name not in assets, "release has duplicate asset names")
        assets[name] = item

    def read_asset(name: str) -> bytes:
        _require(Path(name).name == name, "release asset filename is unsafe")
        item = assets.get(name)
        _require(item is not None, f"release is missing {name}")
        assert item is not None
        path = assets_dir / name
        _require(
            path.is_file() and not path.is_symlink(),
            f"release asset {name} is missing or unsafe",
        )
        digest = item.get("digest")
        _require(
            isinstance(digest, str) and digest == "sha256:" + _sha(path.read_bytes()),
            f"GitHub asset digest differs for {name}",
        )
        return path.read_bytes()

    sums_bytes = read_asset("SHA256SUMS")
    _require(
        _sha(sums_bytes) == expected_sums_sha256,
        "SHA256SUMS differs from its explicit pin",
    )
    sums = parse_sums(sums_bytes)
    pin_bytes = read_asset("release-pins.json")
    try:
        pins = json.loads(pin_bytes)
    except json.JSONDecodeError as exc:
        raise ReleaseError("release-pins.json is invalid") from exc
    _require(
        isinstance(pins, dict)
        and pins.get("tag") == tag
        and pins.get("commit") == source_sha
        and pins.get("version") == version
        and pins.get("distribution") == distribution,
        "release pins do not match the requested tag, source, version and distribution",
    )
    wheel_candidates = sorted(name for name in sums if name.startswith(wheel_prefix) and name.endswith(".whl"))
    temporal_wheel = False
    for name in wheel_candidates:
        try:
            with zipfile.ZipFile(assets_dir / name) as archive:
                manifest = json.loads(archive.read("truss/_catalog_runtime/manifest.json"))
            temporal_wheel = temporal_wheel or manifest.get("releaseId") == "truss-catalog-runtime/0.76-temporal-candidate"
        except (OSError, KeyError, zipfile.BadZipFile, json.JSONDecodeError):
            continue
    temporal_pin = pins.get("temporalQualifiedWheel")
    _require(temporal_wheel == (temporal_pin is not None),
             "temporal candidate wheel and exact qualification pin must be selected together")
    if temporal_wheel:
        _require(expected_source_tree is not None,
                 "selected temporal release requires the independently resolved tag source tree")
        import temporal_qualified_artifact
        verified = temporal_qualified_artifact.verify_release_staging(
            assets_dir, source_commit=source_sha, source_tree=expected_source_tree)
        exact_tag_proof = _exact_tag_proof(release, tag_ref, tag_object, producer_run,
            producer_jobs, repository=repository, source_sha=source_sha, tag=tag)
        exact_tag_proof["ownerReadiness"] = _temporal_owner_readiness(
            verified, owner_release, core_owner_proofs)
        from release_cohort import require_stage_admission
        component=verified['componentResult'];admission=verified['admission']
        admission_result=verified['admissionResult']
        require_stage_admission('prepublication',component=component,records={
            'sourceIdentity':{'commit':source_sha,'tree':expected_source_tree},
            'ownerClosure':admission_result.get('wheels'),
            'resourceClosure':component['coreC1'],
            'weftClosure':component['weftSDK42'],
            'inventories':admission.get('initializationCaptures'),
            'freshBaseline':admission_result.get('captureTransitions'),
            'campaignInputs':admission,
            'campaign130':verified['campaign130'],
            'exactTagProofs':exact_tag_proof, 'selectedCore':verified['selectedCore']})
        intake = json.loads((assets_dir / "temporal-qualification-intake.json").read_bytes())
        expected_pin = {
            "schema": "truss.temporal-qualified-wheel-release-pin/1",
            "sourceCommit": source_sha, "sourceTree": expected_source_tree,
            "runId": str(intake["runId"]), "runAttempt": str(intake["runAttempt"]),
            "artifactId": str(intake["artifactId"]), "artifactSha256": intake["artifactSha256"],
            "candidateWheelSha256": verified["candidateWheelSha256"],
            "qualifiedBundleSha256": _sha((assets_dir / "temporal-qualified-evidence.zip").read_bytes()),
            "bindingSha256": _sha((assets_dir / "temporal-qualification-binding.json").read_bytes()),
            "memberManifestSha256": _sha((assets_dir / "temporal-qualified-member-manifest.json").read_bytes()),
        }
        _require(temporal_pin == expected_pin,
                 "release temporal qualification pin differs from authenticated original bundle")
    if version == "0.0.56":
        from release_cohort import load_cohort
        expected_cohort = load_cohort(require_qualified=True)
        _require(pins.get("dependencyCohort") == expected_cohort,
                 "release dependency cohort differs from actual qualified identities")
    archives = sorted(
        name for name in sums if name.startswith(wheel_prefix) and name.endswith(".whl")
    )
    _require(
        len(archives) == wheel_count,
        "SHA256SUMS wheel inventory differs from the expected cohort",
    )
    sdist_prefix = wheel_prefix.rstrip("-")
    sdists = sorted(
        name
        for name in sums
        if name.startswith(sdist_prefix) and name.endswith(".tar.gz")
    )
    _require(
        len(sdists) == (1 if require_sdist else 0),
        "SHA256SUMS source archive inventory differs",
    )
    selected = archives + sdists
    _require(not output_dir.exists(), "verified distribution output path must be new")
    output_dir.mkdir(parents=True)
    files: dict[str, str] = {}
    for name in selected:
        path = assets_dir / name
        _require(
            path.is_file() and not path.is_symlink(),
            f"release archive {name} is missing or unsafe",
        )
        data = path.read_bytes()
        _require(_sha(data) == sums[name], f"SHA256SUMS digest differs for {name}")
        item = assets[name]
        _require(
            item.get("digest") == "sha256:" + _sha(data),
            f"GitHub digest differs for {name}",
        )
        validate_archive(path, distribution, version)
        (output_dir / name).write_bytes(data)
        files[name] = sums[name]
    receipt = {
        "schema": "pypi-release-source.v1",
        "status": "verified",
        "repository": repository,
        "tag": tag,
        "source_sha": source_sha,
        "distribution": distribution,
        "version": version,
        "sums_sha256": _sha(sums_bytes),
        "release_pins_sha256": _sha(pin_bytes),
        "github_release_immutable": release.get("immutable") is True,
        "files": files,
    }
    if producer_run is not None:
        receipt["producer_run_id"] = producer_run.get("id")
        receipt["producer_workflow_path"] = producer_run.get("path")
    return receipt


def check_pypi(distribution: str, version: str, expected_files: dict[str, str]) -> str:
    url = f"https://pypi.org/pypi/{distribution}/{version}/json"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            value = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return "absent"
        raise ReleaseError(f"PyPI returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ReleaseError("PyPI version lookup failed") from exc
    _require(isinstance(value, dict), "PyPI response is malformed")
    info = value.get("info")
    _require(
        isinstance(info, dict)
        and info.get("name") == distribution
        and info.get("version") == version,
        "PyPI response identifies a different release",
    )
    raw = value.get("urls")
    _require(isinstance(raw, list), "PyPI file inventory is missing")
    actual: dict[str, str] = {}
    for item in raw:
        _require(
            isinstance(item, dict) and isinstance(item.get("filename"), str),
            "PyPI file record is malformed",
        )
        name = item["filename"]
        digest = (
            item.get("digests", {}).get("sha256")
            if isinstance(item.get("digests"), dict)
            else None
        )
        _require(
            name not in actual
            and isinstance(digest, str)
            and SHA.fullmatch(digest) is not None,
            "PyPI file inventory contains a duplicate or invalid digest",
        )
        actual[name] = digest
    _require(
        actual == expected_files,
        "PyPI version collision: published file inventory or digest differs",
    )
    for item in raw:
        file_url = item.get("url")
        _require(
            isinstance(file_url, str)
            and file_url.startswith("https://files.pythonhosted.org/"),
            "PyPI file URL is outside the public file host",
        )
        request = urllib.request.Request(file_url)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                digest = _sha(response.read())
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ReleaseError("PyPI file download failed") from exc
        _require(
            digest == expected_files[item["filename"]],
            "PyPI-served archive bytes differ",
        )
    return "matching"


def wait_for_pypi(
    distribution: str, version: str, files: dict[str, str], timeout: int = 300
) -> str:
    _require(
        type(timeout) is int and 1 <= timeout <= 600,
        "PyPI visibility bound must be 1–600 seconds",
    )
    deadline = time.monotonic() + timeout
    while True:
        state = check_pypi(distribution, version, files)
        if state == "matching":
            return state
        remaining = deadline - time.monotonic()
        _require(
            remaining > 0,
            "PyPI did not expose exact archive bytes before the visibility timeout",
        )
        time.sleep(min(5, remaining))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "check-pypi"))
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--dist-dir", type=Path)
    parser.add_argument("--release-json", type=Path)
    parser.add_argument("--tag-ref-json", type=Path)
    parser.add_argument("--tag-object-json", type=Path)
    parser.add_argument("--producer-run-json", type=Path)
    parser.add_argument("--producer-jobs-json", type=Path)
    parser.add_argument("--owner-release-dir", type=Path)
    parser.add_argument("--core-owner-proof-dir", type=Path)
    parser.add_argument("--assets-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--repository")
    parser.add_argument("--tag")
    parser.add_argument("--source-sha")
    parser.add_argument("--expected-source-tree")
    parser.add_argument("--expected-sums-sha256")
    parser.add_argument("--distribution")
    parser.add_argument("--wheel-prefix")
    parser.add_argument("--wheel-count", type=int)
    parser.add_argument("--require-sdist", action="store_true")
    parser.add_argument("--producer-workflow-path", action="append", default=[])
    parser.add_argument("--producer-workflow-prefix", action="append", default=[])
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if args.command == "prepare":
        required = (
            args.release_json,
            args.tag_ref_json,
            args.assets_dir,
            args.output_dir,
            args.repository,
            args.tag,
            args.source_sha,
            args.expected_sums_sha256,
            args.distribution,
            args.wheel_prefix,
            args.wheel_count,
        )
        _require(
            all(value is not None for value in required),
            "prepare requires complete release inputs",
        )
        _require(
            args.receipt.parent == args.output_dir,
            "receipt must be written beside verified archives",
        )

        def load(path: Path) -> Any:
            return json.loads(path.read_text(encoding="utf-8"))

        producer = load(args.producer_run_json) if args.producer_run_json else None
        producer_jobs = load(args.producer_jobs_json) if args.producer_jobs_json else None
        owner_release = _load_weft_owner_release(args.owner_release_dir) if args.owner_release_dir else None
        core_owner_proofs = None
        if args.core_owner_proof_dir is not None:
            import temporal_qualified_artifact
            verified_owner_context = temporal_qualified_artifact.verify_release_staging(
                args.assets_dir, source_commit=args.source_sha, source_tree=args.expected_source_tree)
            core_owner_proofs = _load_core_owner_proofs(args.core_owner_proof_dir,
                verified_owner_context['selectedCore'])
        receipt = prepare_release(
            repository=args.repository,
            release=load(args.release_json),
            tag_ref=load(args.tag_ref_json),
            tag_object=load(args.tag_object_json) if args.tag_object_json else None,
            assets_dir=args.assets_dir,
            output_dir=args.output_dir,
            tag=args.tag,
            source_sha=args.source_sha,
            expected_source_tree=args.expected_source_tree,
            expected_sums_sha256=args.expected_sums_sha256,
            distribution=args.distribution,
            wheel_prefix=args.wheel_prefix,
            wheel_count=args.wheel_count,
            require_sdist=args.require_sdist,
            producer_run=producer,
            producer_jobs=producer_jobs,
            owner_release=owner_release,
            core_owner_proofs=core_owner_proofs,
            allowed_workflow_paths=set(args.producer_workflow_path),
            allowed_workflow_prefixes=tuple(args.producer_workflow_prefix),
        )
        args.receipt.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {"status": "verified", "version": receipt["version"]}, sort_keys=True
            )
        )
        return 0
    _require(
        args.dist_dir is not None,
        "registry check requires the verified archive directory",
    )
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    _require(
        receipt.get("schema") == "pypi-release-source.v1"
        and receipt.get("status") == "verified",
        "verified source receipt is invalid",
    )
    for name, digest in receipt["files"].items():
        path = args.dist_dir / name
        _require(
            Path(name).name == name and path.is_file() and not path.is_symlink(),
            "verified archive is missing",
        )
        _require(
            _sha(path.read_bytes()) == digest,
            "verified archive changed after release validation",
        )

    def check() -> str:
        return check_pypi(receipt["distribution"], receipt["version"], receipt["files"])

    status = (
        wait_for_pypi(
            receipt["distribution"], receipt["version"], receipt["files"], args.timeout
        )
        if args.wait
        else check()
    )
    print(json.dumps({"status": status}, sort_keys=True))
    import os

    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"status={status}\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ReleaseError, OSError, KeyError, TypeError) as exc:
        print(f"release validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
