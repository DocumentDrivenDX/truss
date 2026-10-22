#!/usr/bin/env python3
"""Retain the successful post-publication v0.0.49 proof without rerunning it.

This packager is deliberately separate from verify-public-049.py. It performs no
network, package installation, PostgreSQL, or qualification work. It refuses to
assemble a packet until output2 is complete and passed for the exact public tag.
It copies receipts/logs and small identity files only, never virtualenvs, unpacked
corpora, public wheel payloads, or process inventories.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from typing import Any

BASE = Path('/private/tmp/truss-managed-grants-049')
EXPECTED_TAG = 'v0.0.49'
EXPECTED_COMMIT = 'dd13e95804abc30202d449a756240c6a684ab942'
EXPECTED_NATIVE = '288801f7177338328441b5d3ce9328af31740ebf513f04ea45e30ae316a9f3a4'
EXPECTED_MIGRATIONS = '96addcdb95523f478d8f50b0b47198e47a860680c7400dd359711930e837e535'
EXPECTED_WEFT_SOURCE = '557153731e9f5d0583193a1189a07c6ed485d3d3'
EXPECTED_VERIFIER_SHA256 = '0c800ce47499d4e6b1126d3c7f03032a1099c558dcc8d15f7bed65dd6bb8f1c6'
EXPECTED_OUTPUT2 = BASE / 'published-049-verification-2'
EXPECTED_API = BASE / 'public-049-github-release.json'
EXPECTED_PREFLIGHT = BASE / 'public-049' / 'preflight.json'
EXPECTED_WORKFLOW = BASE / 'tag-049-workflow.json'
EXPECTED_CAPSULE = BASE / 'public-049' / 'all'
EXPECTED_ATTEMPT1 = BASE / 'published-049-verification-1'
EXPECTED_ATTEMPT1_DRIVER_LOG = BASE / 'published-049-verification-1-driver.log'
EXPECTED_BOOTSTRAP = BASE / 'venv-bootstrap-diagnosis'
EXPECTED_TAG_WORKFLOW_LOG = BASE / 'tag-049-workflow.log'
EXPECTED_OUTPUT2_DRIVER_LOG = BASE / 'published-049-verification-2-driver.log'
EXPECTED_VERIFIER_SOURCE = BASE / 'verify-public-049.py'
EXPECTED_SOURCE = Path('/Users/erik/Projects/truss')
OUTPUT = BASE / 'published-0.0.49'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def file_identity(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
            size += len(block)
    return h.hexdigest(), size


def read_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'required regular JSON file is missing: {path}')
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f'expected JSON object in {path}')
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def copy_verified(source: Path, packet: Path, relative: str, expected: str | None = None) -> dict[str, Any]:
    if source.is_symlink() or not source.is_file():
        raise ValueError(f'retention input is not a regular file: {source}')
    before = sha256(source)
    if expected is not None and before != expected:
        raise ValueError(f'input digest differs from its public identity: {source.name}')
    target = packet / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(target)
    shutil.copyfile(source, target)
    after = sha256(source)
    copied = sha256(target)
    if before != after or before != copied:
        raise ValueError(f'input changed during retention: {source}')
    return {'path': relative, 'sha256': copied, 'bytes': target.stat().st_size,
            'sourceName': source.name}


def parse_sums(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for number, line in enumerate(path.read_text().splitlines(), 1):
        fields = line.split('  ', 1)
        if len(fields) != 2 or not re.fullmatch(r'[0-9a-f]{64}', fields[0]):
            raise ValueError(f'malformed public SHA256SUMS line {number}')
        name = fields[1]
        if not name or '/' in name or '\\' in name or name in rows:
            raise ValueError(f'unsafe or repeated public asset name on line {number}')
        rows[name] = fields[0]
    if not rows:
        raise ValueError('public SHA256SUMS is empty')
    return rows


def validate_release(api: dict, preflight: dict, workflow: dict, pins: dict,
                     output2: dict, out_dir: Path, capsule: Path) -> dict[str, Any]:
    if api.get('tag_name') != EXPECTED_TAG or api.get('draft') is not False or not api.get('published_at'):
        raise ValueError('GitHub API response does not prove a published v0.0.49 release')
    if preflight.get('release') != api.get('html_url') or preflight.get('publishedAt') != api.get('published_at'):
        raise ValueError('preflight release URL/time differs from GitHub API')
    if preflight.get('tagCommit') != EXPECTED_COMMIT or workflow.get('headSha') != EXPECTED_COMMIT:
        raise ValueError('tag workflow/preflight do not bind the required dd13 source commit')
    if workflow.get('conclusion') != 'success' or workflow.get('status') != 'completed':
        raise ValueError('tag release workflow is not completed successfully')
    if workflow.get('url') != preflight.get('tagWorkflow'):
        raise ValueError('preflight and supplied tag workflow URLs differ')
    jobs = workflow.get('jobs')
    if not isinstance(jobs, list):
        raise ValueError('tag workflow has no job inventory')
    by_name = {job.get('name'): job for job in jobs if isinstance(job, dict)}
    required_jobs = {'package', 'native (ubuntu-24.04)', 'publish'}
    if not required_jobs <= set(by_name):
        raise ValueError(f'tag workflow is missing required jobs: {sorted(required_jobs-set(by_name))}')
    if any(by_name[name].get('conclusion') != 'success' for name in required_jobs):
        raise ValueError('tag workflow package, Linux native, or publish gate failed')
    if any(job.get('conclusion') not in ('success', 'skipped') for job in by_name.values()):
        raise ValueError('tag workflow contains a failed or cancelled job')

    if not (preflight.get('allApiDigestsAndSizesVerified') is True and
            preflight.get('sha256SumsExactInventory') is True and
            preflight.get('publicTagPackageBytesMatchCIArtifacts') is True):
        raise ValueError('preflight does not prove API digests, exact SHA256SUMS, and CI asset correspondence')
    for name, expected in (('nativeManifestSha256', EXPECTED_NATIVE),
                           ('migrationManifestSha256', EXPECTED_MIGRATIONS),
                           ('weftSourceRevision', EXPECTED_WEFT_SOURCE)):
        if preflight.get(name) != expected:
            raise ValueError(f'preflight {name} differs from the pinned release source')
    if pins.get('tag') != EXPECTED_TAG or pins.get('commit') != EXPECTED_COMMIT:
        raise ValueError('public release pins do not identify the exact tag commit')
    if pins.get('distribution') != 'truss-toolkit' or pins.get('version') != '0.0.49':
        raise ValueError('public release pins do not identify Truss toolkit 0.0.49')
    if pins.get('runtimeManifestSha256') != EXPECTED_NATIVE or pins.get('migrationManifestSha256') != EXPECTED_MIGRATIONS:
        raise ValueError('release pins differ from the public native/migration manifests')
    if pins.get('weftSourceRevision') != EXPECTED_WEFT_SOURCE:
        raise ValueError('release pins differ from the public Weft source revision')
    if (pins.get('managedGrantsInterface') != 'truss-managed-grants/0.1' or
            pins.get('managedGrantsSelection') != 'fresh-install-only' or
            pins.get('managedGrantsProtectedActivation') is not False or
            pins.get('actualLakebaseAcceptance') is not False or
            pins.get('installationUpgradesSupported') is not True or
            pins.get('runtimeSupport') != 'latest-only'):
        raise ValueError('public release pins differ from the qualified managed-grants/release limits')
    if pins.get('hfConformanceTests') != 62 or len(pins.get('migrationSources', [])) != 4:
        raise ValueError('public release pins do not identify four migration sources and HF62')

    assets = api.get('assets')
    if not isinstance(assets, list) or not assets:
        raise ValueError('public GitHub API response has no asset list')
    api_by_name: dict[str, dict] = {}
    for asset in assets:
        if not isinstance(asset, dict) or not isinstance(asset.get('name'), str):
            raise ValueError('public API asset row is malformed')
        name = asset['name']
        digest = asset.get('digest')
        size = asset.get('size')
        if name in api_by_name or not isinstance(size, int) or size <= 0:
            raise ValueError(f'public API has duplicate or invalid asset row: {name}')
        if not isinstance(digest, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
            raise ValueError(f'public API has no valid SHA-256 digest for {name}')
        api_by_name[name] = asset
    preflight_hashes = preflight.get('assetSha256')
    if not isinstance(preflight_hashes, dict) or set(preflight_hashes) != set(api_by_name):
        raise ValueError('preflight asset identity set differs from public API')
    for name, asset in api_by_name.items():
        if asset['digest'].split(':', 1)[1] != preflight_hashes[name]:
            raise ValueError(f'public API and preflight disagree on {name}')
    if preflight.get('assetCount') != len(api_by_name):
        raise ValueError('preflight asset count differs from public API inventory')
    capsule_members = list(capsule.iterdir())
    if any(path.is_symlink() or not path.is_file() for path in capsule_members):
        raise ValueError('public Truss capsule must contain only regular top-level asset files')
    if {path.name for path in capsule_members} != set(api_by_name):
        raise ValueError('downloaded public Truss capsule inventory differs from GitHub API')
    for name, asset in api_by_name.items():
        path = capsule / name
        actual_sha, actual_size = file_identity(path)
        if actual_sha != preflight_hashes[name] or actual_size != asset['size']:
            raise ValueError(f'downloaded public asset bytes/size differ from API and preflight: {name}')

    sums_path = capsule / 'SHA256SUMS'
    sums_rows = parse_sums(sums_path)
    expected_payload_names = set(api_by_name) - {'SHA256SUMS'}
    if set(sums_rows) != expected_payload_names:
        raise ValueError('public SHA256SUMS names differ from the API payload inventory')
    if sha256(sums_path) != preflight_hashes.get('SHA256SUMS'):
        raise ValueError('public SHA256SUMS digest differs from preflight')
    for name, digest_value in sums_rows.items():
        if digest_value != preflight_hashes[name] or digest_value != api_by_name[name]['digest'].split(':', 1)[1]:
            raise ValueError(f'public SHA256SUMS/API/preflight disagree on {name}')

    if output2.get('passed') is not True or output2.get('errors') != []:
        raise ValueError('output2 public verifier did not pass cleanly')
    if output2.get('actualLakebaseAcceptance') != 'not_run':
        raise ValueError('output2 must preserve Lakebase as not run')
    if output2.get('sourceCommit') != EXPECTED_COMMIT or output2.get('inputsUnchanged') is not True:
        raise ValueError('output2 did not pass against unchanged exact dd13 tag inputs')
    if output2.get('localPlatform') != 'macos-arm64' or output2.get('hfTests') != 62:
        raise ValueError('output2 does not contain the expected Mac ARM64 public installed/HF62 proof')
    if output2.get('releasedRuntimeReceiptSha256') is None or output2.get('hfReceiptSha256') is None:
        raise ValueError('output2 is missing retained checker receipt digests')
    steps = output2.get('steps')
    if not isinstance(steps, list) or not steps or any(step.get('returncode') != 0 or step.get('timedOut') is not False for step in steps):
        raise ValueError('output2 contains a failed or incomplete logged step')
    step_logs: set[str] = set()
    for step in steps:
        name = step.get('log')
        if (not isinstance(name, str) or Path(name).name != name or
                not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.log', name) or name in step_logs):
            raise ValueError('output2 has an unsafe or duplicate step-log name')
        log_path = out_dir / name
        if log_path.is_symlink() or not log_path.is_file() or sha256(log_path) != step.get('logSha256'):
            raise ValueError(f'output2 step log is missing or its recorded digest differs: {name}')
        step_logs.add(name)

    truss_inventory = output2.get('publicAssets', {}).get('truss', {})
    if set(truss_inventory.get('assetNames', [])) != set(api_by_name):
        raise ValueError('output2 Truss API inventory differs from the public release')
    payload_hashes = truss_inventory.get('payloadSha256')
    if not isinstance(payload_hashes, dict) or set(payload_hashes) != expected_payload_names:
        raise ValueError('output2 Truss asset hash map is incomplete')
    for name, digest_value in payload_hashes.items():
        if digest_value != preflight_hashes[name]:
            raise ValueError(f'output2 public payload hash differs for {name}')
    if truss_inventory.get('sha256SumsSha256') != preflight_hashes['SHA256SUMS']:
        raise ValueError('output2 checksum manifest differs from public API/preflight')
    helper_api = output2.get('githubReleases', {}).get('truss', {})
    helper_assets = helper_api.get('assets')
    helper_digests = helper_api.get('assetDigests')
    if (helper_api.get('tagName') != EXPECTED_TAG or helper_api.get('isDraft') is not False or
            helper_api.get('publishedAt') != api.get('published_at') or
            not isinstance(helper_assets, list) or set(helper_assets) != set(api_by_name) or
            helper_digests != {name: row['digest'].split(':', 1)[1] for name, row in api_by_name.items()}):
        raise ValueError('output2 verifier release inventory differs from the supplied public GitHub API result')
    output_asset_hashes = output2.get('publicAssetSha256', {}).get('truss')
    if output_asset_hashes != payload_hashes:
        raise ValueError('output2 completed public asset hashes differ from its complete inventory')

    managed_asset = read_json(capsule / 'managed-grants-qualification.json')
    migration_asset = read_json(capsule / 'migration-qualification.json')
    hf_asset = read_json(capsule / 'hf-conformance-qualification.json')
    outcomes = managed_asset.get('outcomes', [])
    if not (managed_asset.get('passed') is True and managed_asset.get('tests') == 130 and
            managed_asset.get('skipped') == 0 and len(managed_asset.get('outcomes', [])) == 21 and
            all(isinstance(row, dict) and row.get('passed') is True and row.get('returncode') == 0 and
                row.get('timedOut') is False for row in outcomes) and
            sum(row.get('tests', 0) for row in outcomes) == 130 and
            managed_asset.get('sourceCommit') == EXPECTED_COMMIT and
            managed_asset.get('nativeManifestSha256') == EXPECTED_NATIVE):
        raise ValueError('public managed-grants asset is not the exact passing 21-module/130-test gate')
    if not (migration_asset.get('passed') is True and migration_asset.get('tests') == 106 and
            migration_asset.get('failures') == 0 and migration_asset.get('errors') == 0 and
            migration_asset.get('skipped') == 0 and len(migration_asset.get('sources', [])) == 4 and
            migration_asset.get('sourceCommit') == EXPECTED_COMMIT and
            migration_asset.get('targetManifestSha256') == EXPECTED_NATIVE):
        raise ValueError('public migration asset is not the exact passing four-source/106-case gate')
    if not (hf_asset.get('passed') is True and hf_asset.get('tests') == 62 and
            hf_asset.get('failures') == 0 and hf_asset.get('errors') == 0 and
            hf_asset.get('skipped') == 0 and hf_asset.get('sourceCommit') == EXPECTED_COMMIT and
            hf_asset.get('nativeManifestSha256') == EXPECTED_NATIVE and
            hf_asset.get('compilerSourceRevision') == EXPECTED_WEFT_SOURCE):
        raise ValueError('public HF archive receipt is not the exact passing HF62/source-557 result')

    managed = preflight.get('managed', {})
    migrations = preflight.get('migrations', {})
    hf = preflight.get('hf', {})
    if managed != {'modules': 21, 'tests': 130, 'skipped': 0}:
        raise ValueError('preflight managed-grants gate does not match 21-module/130-test result')
    if migrations.get('tests') != 106 or migrations.get('failures') != 0 or migrations.get('errors') != 0 or migrations.get('skipped') != 0:
        raise ValueError('preflight does not contain the exact passing 106-case migration gate')
    if hf.get('tests') != 62 or hf.get('failures') != 0 or hf.get('errors') != 0 or hf.get('skipped') != 0:
        raise ValueError('preflight does not contain the exact passing HF62 gate')
    return {
        'tag': EXPECTED_TAG,
        'tagCommit': EXPECTED_COMMIT,
        'publishedAt': api['published_at'],
        'releaseUrl': api['html_url'],
        'workflowUrl': workflow.get('url'),
        'nativeManifestSha256': EXPECTED_NATIVE,
        'migrationManifestSha256': EXPECTED_MIGRATIONS,
        'weftSourceRevision': EXPECTED_WEFT_SOURCE,
        'assetCount': len(api_by_name),
        'assets': {name: {'sha256': preflight_hashes[name], 'bytes': api_by_name[name]['size'],
                          'apiAssetId': api_by_name[name].get('id')} for name in sorted(api_by_name)},
        'managed': managed,
        'migrations': migrations,
        'hf': hf,
        'publicMacNativeVerificationBeforeOutput2': preflight.get('publicMacNativeVerification'),
        'output2': {'path': str(out_dir), 'passed': True, 'sourceCommit': output2['sourceCommit'],
                    'localPlatform': output2['localPlatform'], 'hfTests': output2['hfTests'],
                    'releasedRuntimeReceiptSha256': output2['releasedRuntimeReceiptSha256'],
                    'hfReceiptSha256': output2['hfReceiptSha256'],
                    'installedPayload': output2.get('installedPayload'),
                    'publicAssetSha256': output2.get('publicAssetSha256')},
        'actualLakebaseAcceptance': 'not_run',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output2', type=Path, default=EXPECTED_OUTPUT2)
    parser.add_argument('--api', type=Path, default=EXPECTED_API)
    parser.add_argument('--preflight', type=Path, default=EXPECTED_PREFLIGHT)
    parser.add_argument('--workflow', type=Path, default=EXPECTED_WORKFLOW)
    parser.add_argument('--capsule', type=Path, default=EXPECTED_CAPSULE)
    parser.add_argument('--attempt1', type=Path, default=EXPECTED_ATTEMPT1)
    parser.add_argument('--attempt1-driver-log', type=Path, default=EXPECTED_ATTEMPT1_DRIVER_LOG)
    parser.add_argument('--bootstrap-diagnosis', type=Path, default=EXPECTED_BOOTSTRAP)
    parser.add_argument('--tag-workflow-log', type=Path, default=EXPECTED_TAG_WORKFLOW_LOG)
    parser.add_argument('--output2-driver-log', type=Path, default=EXPECTED_OUTPUT2_DRIVER_LOG)
    parser.add_argument('--verifier-source', type=Path, default=EXPECTED_VERIFIER_SOURCE)
    parser.add_argument('--source-root', type=Path, default=EXPECTED_SOURCE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()

    output2_dir = args.output2.resolve(strict=True)
    output2_path = output2_dir / 'qualification.json'
    output2 = read_json(output2_path)
    api_path = args.api.resolve(strict=True)
    preflight_path = args.preflight.resolve(strict=True)
    workflow_path = args.workflow.resolve(strict=True)
    capsule = args.capsule.resolve(strict=True)
    pins_path = capsule / 'release-pins.json'
    pins = read_json(pins_path)
    api = read_json(api_path)
    preflight = read_json(preflight_path)
    workflow = read_json(workflow_path)
    receipt_core = validate_release(api, preflight, workflow, pins, output2, output2_dir, capsule)
    source_basis = {
        'api': sha256(api_path), 'preflight': sha256(preflight_path),
        'workflow': sha256(workflow_path), 'output2Qualification': sha256(output2_path),
        'publicSums': sha256(capsule / 'SHA256SUMS'), 'releasePins': sha256(pins_path),
    }

    output = args.output.resolve()
    if output.parent != BASE or output.name != 'published-0.0.49':
        raise ValueError('Output must be the fresh private published-0.0.49 packet directory')
    output.mkdir(parents=True, exist_ok=False)
    retained: list[dict[str, Any]] = []

    def retain(source: Path, relative: str, expected: str | None = None):
        row = copy_verified(source, output, relative, expected)
        retained.append(row)
        return row

    # Exact public release identities and a small set of public API assets.
    retain(api_path, 'release/public-release-api.json')
    retain(preflight_path, 'release/preflight.json')
    retain(workflow_path, 'release/tag-workflow.json')
    retain(args.tag_workflow_log.resolve(strict=True), 'release/tag-workflow.log')
    retain(capsule / 'SHA256SUMS', 'release/SHA256SUMS', preflight['assetSha256']['SHA256SUMS'])
    retain(pins_path, 'release/release-pins.json', preflight['assetSha256']['release-pins.json'])
    for name in ('managed-grants-qualification.json', 'migration-qualification.json',
                 'hf-conformance-qualification.json'):
        retain(capsule / name, f'release/{name}', preflight['assetSha256'][name])

    # Preserve all bounded output2 top-level receipts/logs, excluding environments
    # and extracted archives by design. Unknown directories fail closed.
    allowed_dirs = {'public-venv', 'hf-standalone'}
    for child in sorted(output2_dir.iterdir()):
        if child.is_symlink():
            raise ValueError(f'output2 contains a symlink: {child}')
        if child.is_dir():
            if child.name not in allowed_dirs:
                raise ValueError(f'output2 contains an unreviewed directory: {child.name}')
            continue
        if (child.name == 'qualification.json' or child.suffix in ('.json', '.log', '.txt') or
                child.name in {'runtime-SHA256SUMS', 'truss-SHA256SUMS', 'weft-SHA256SUMS'}):
            retain(child, f'verification/output2/{child.name}')
    retain(args.output2_driver_log.resolve(strict=True), 'verification/output2/outer-driver.log')
    checker_path_value = output2.get('releasedRuntimeReceipt')
    if not isinstance(checker_path_value, str):
        raise ValueError('output2 has no checker receipt path')
    checker_path = Path(checker_path_value).resolve(strict=True)
    if checker_path != (args.source_root.resolve() / 'docs/helix/04-build/evidence/design-audit' /
                        f'mg49-public-{output2_dir.name}' / 'receipt.json').resolve():
        raise ValueError('output2 checker receipt path is outside its expected exact source evidence directory')
    top_level_checker = output2_dir / 'released-runtime-receipt.json'
    if (top_level_checker.is_symlink() or not top_level_checker.is_file() or
            sha256(top_level_checker) != output2['releasedRuntimeReceiptSha256'] or
            sha256(checker_path) != output2['releasedRuntimeReceiptSha256']):
        raise ValueError('output2 top-level and source checker receipts do not match its recorded digest')
    if sha256(top_level_checker) != sha256(output / 'verification/output2/released-runtime-receipt.json'):
        raise ValueError('retained top-level checker receipt differs from output2')
    checker_evidence_dir = checker_path.parent
    checker_evidence_bytes = 0
    for child in sorted(checker_evidence_dir.rglob('*')):
        if child == checker_path:
            continue
        relative = child.relative_to(checker_evidence_dir)
        if any(part.casefold() in {'public-venv', 'hf-standalone', 'corpus', 'corpora'}
               for part in relative.parts):
            raise ValueError(f'checker evidence contains excluded environment/corpus material: {relative}')
        if child.is_symlink():
            raise ValueError(f'checker evidence directory contains a symlink: {relative}')
        if child.is_dir():
            continue
        if not child.is_file() or child.stat().st_size > 32 * 1024 * 1024:
            raise ValueError(f'checker evidence directory contains an unbounded non-file: {relative}')
        checker_evidence_bytes += child.stat().st_size
        if checker_evidence_bytes > 128 * 1024 * 1024:
            raise ValueError('checker sidecar evidence exceeds the retention size bound')
        retain(child, f'verification/output2/checker-evidence/{relative.as_posix()}')

    hf_path = output2.get('hfReceipt')
    if not isinstance(hf_path, str):
        raise ValueError('output2 has no HF receipt path')
    if Path(hf_path).resolve() != (output2_dir / 'hf-qualification.json').resolve():
        raise ValueError('output2 HF receipt path is not its own retained result')
    hf_receipt = read_json(Path(hf_path))
    if sha256(Path(hf_path)) != output2['hfReceiptSha256']:
        raise ValueError('output2 HF receipt digest differs from its recorded digest')
    if not (hf_receipt.get('passed') is True and hf_receipt.get('tests') == 62 and
            hf_receipt.get('failures') == 0 and hf_receipt.get('errors') == 0 and
            hf_receipt.get('skipped') == 0 and hf_receipt.get('sourceCommit') == EXPECTED_COMMIT and
            hf_receipt.get('nativeManifestSha256') == EXPECTED_NATIVE):
        raise ValueError('output2 HF receipt is not the exact passing public HF62 result')
    if hf_receipt.get('compilerSourceRevision') != EXPECTED_WEFT_SOURCE:
        raise ValueError('output2 HF receipt does not bind the exact public Weft source revision')
    installed_identities = output2.get('installedPayload', {}).get('identities', {})
    weft_cohort = installed_identities.get('weftCohort', {})
    if (output2.get('weftSourceFreezeRevision') != EXPECTED_WEFT_SOURCE or
            weft_cohort.get('weftRevision') != EXPECTED_WEFT_SOURCE or
            weft_cohort.get('weftModuleSha256') != hf_receipt.get('compilerNativeModuleSha256')):
        raise ValueError('output2 installed payload does not bind the HF Weft source/module cohort')
    mac_weft = output2.get('macWeftVerification', {})
    linux_weft = output2.get('linuxWeftVerification', {})
    if (mac_weft.get('wheelSha256') != weft_cohort.get('weftWheelSha256') or
            mac_weft.get('nativeModuleSha256') != weft_cohort.get('weftModuleSha256') or
            linux_weft.get('wheelSha256') != pins.get('weftWheelSha256') or
            linux_weft.get('nativeModuleSha256') != pins.get('weftNativeModuleSha256')):
        raise ValueError('output2 public Mac/Linux Weft cohort identities are inconsistent')

    # Keep the failed ensurepip invocation and its isolated root-cause proof,
    # clearly classified as bootstrap diagnosis only, never as test evidence.
    attempt1 = args.attempt1.resolve(strict=True)
    first_result = read_json(attempt1 / 'qualification.json')
    if first_result.get('passed') is not False or not any('ensurepip' in err for err in first_result.get('errors', [])):
        raise ValueError('attempt1 is not the retained ensurepip bootstrap failure')
    retain(attempt1 / 'qualification.json', 'diagnostics/public-verifier-attempt1/qualification.json')
    retain(args.attempt1_driver_log.resolve(strict=True), 'diagnostics/public-verifier-attempt1/outer-driver.log')
    for child in sorted(attempt1.iterdir()):
        if child.is_symlink():
            raise ValueError(f'attempt1 contains a symlink: {child.name}')
        if child.is_file() and child.suffix == '.log':
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.log', child.name):
                raise ValueError(f'attempt1 contains an unsafe log basename: {child.name}')
            retain(child, f'diagnostics/public-verifier-attempt1/{child.name}')
        elif child.is_dir() and child.name in {'public-venv', 'hf-standalone'}:
            continue
        elif child.is_dir():
            raise ValueError(f'attempt1 contains an unreviewed directory: {child.name}')
    bootstrap = args.bootstrap_diagnosis.resolve(strict=True)
    bootstrap_receipt = read_json(bootstrap / 'receipt.json')
    if 'Pure fresh-environment bootstrap diagnosis' not in bootstrap_receipt.get('scope', ''):
        raise ValueError('bootstrap diagnosis receipt has an unexpected scope')
    if bootstrap_receipt.get('failedReadonlyProbeExitCode') != 1 or bootstrap_receipt.get('canonicalBootstrapExitCode') != 0:
        raise ValueError('bootstrap diagnosis does not retain both failure and successful canonical control')
    retain(bootstrap / 'receipt.json', 'diagnostics/venv-bootstrap-diagnosis/receipt.json')
    for name in ('failed-launcher-readonly.log', 'canonical-bootstrap.log', 'canonical-env-check.log'):
        retain(bootstrap / name, f'diagnostics/venv-bootstrap-diagnosis/{name}')
    classification_path = output / 'diagnostics/public-verifier-attempt1/classification.json'
    write_json(classification_path, {
        'classification': 'unqualified bootstrap diagnostic',
        'qualificationClaim': False,
        'failure': 'The first public checker attempt stopped while bootstrapping its fresh venv (ensurepip) before PostgreSQL/runtime qualification.',
        'resolutionEvidence': 'The unchanged verifier succeeded when invoked with the canonical Python 3.11 executable; output2 is the separate required post-publication proof.',
        'attempt1QualificationSha256': sha256(attempt1 / 'qualification.json'),
        'bootstrapDiagnosisSha256': sha256(bootstrap / 'receipt.json'),
    })
    retained.append({'path': 'diagnostics/public-verifier-attempt1/classification.json',
                     'sha256': sha256(classification_path), 'bytes': classification_path.stat().st_size,
                     'sourceName': 'generated-retention-classification'})

    # Re-read primary inputs after copying so the receipt binds a stable snapshot.
    for path, expected in ((api_path, source_basis['api']), (preflight_path, source_basis['preflight']),
                           (workflow_path, source_basis['workflow']),
                           (output2_path, source_basis['output2Qualification']),
                           (capsule / 'SHA256SUMS', source_basis['publicSums']),
                           (pins_path, source_basis['releasePins'])):
        if sha256(path) != expected:
            raise ValueError(f'primary input changed during packet retention: {path}')
    verifier_source = args.verifier_source.resolve(strict=True)
    verifier_row = copy_verified(verifier_source, output, 'producers/verify-public-049.py',
                                 EXPECTED_VERIFIER_SHA256)
    producer_path = Path(__file__).resolve()
    producer_row = copy_verified(producer_path, output, 'producers/retain-published-049-proof.py')
    retained.extend((verifier_row, producer_row))
    receipt = {
        'schema': 'truss-published-release-proof/0.1',
        'status': 'verified',
        'scope': 'Exact public Truss v0.0.49 tag/assets plus successful output2 Mac ARM64 public verifier; no Lakebase acceptance claim.',
        **receipt_core,
        'retainedEvidence': sorted(retained, key=lambda row: row['path']),
        'diagnostics': {
            'attempt1Classification': 'retained unqualified bootstrap/setup diagnostic; excluded from passing qualification claims',
            'attempt1Failure': first_result['errors'],
            'bootstrapDiagnosisScope': bootstrap_receipt['scope'],
        },
        'excludedMaterial': [
            'public verifier virtual environments',
            'extracted HF corpus trees',
            'wheel/sdist/archive payload copies (identified by complete public API and SHA256SUMS records)',
            'unrelated process inventories',
        ],
        'producer': {'script': str(Path(__file__).resolve()), 'sha256': sha256(Path(__file__).resolve()),
                     'python': sys.version},
    }
    write_json(output / 'receipt.json', receipt)
    print(json.dumps({'status': 'verified', 'output': str(output / 'receipt.json'),
                      'retainedFiles': len(retained), 'assetCount': receipt['assetCount'],
                      'actualLakebaseAcceptance': 'not_run'}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
