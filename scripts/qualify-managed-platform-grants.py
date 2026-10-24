#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Installed managed-grants release regression with owned native worker custody.

The explicit module set supplements the other mandatory release workflow gates;
it is not an all-component discovery campaign or actual Lakebase acceptance.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import zipfile

import pgserver
import truss
from native_fixture import WorkerCluster

ROOT = Path(__file__).resolve().parents[1]
UMF_OWNER_REVISION = '5ba77cff91a121a44c82f6bce32a78d8842161b5'
MODULES = (
    'test_installation_sql_batch', 'test_installation_set_facts',
    'test_installation_batching_native', 'test_installation_batching_observer',
    'test_measure_installer_submissions',
    'test_managed_platform_grants_native', 'test_managed_grants_migration_native',
    'test_preparation_runtime_recipe', 'test_installation_privileges_native',
    'test_managed_installation_native', 'test_install_preflight_native',
    'test_lifecycle_native', 'test_module_access_batch_native',
    'test_host_execution', 'test_host_control_custody', 'test_lifecycle_wire',
    'test_action_role_installation_native', 'test_action_store_native',
    'test_preparation_source_inventory_native', 'test_catalog_codes_native',
    'test_catalog_evolution_native', 'test_catalog_runtime_native',
    'test_cli_install_refusal', 'test_local_install_cli_native',
    'test_catalog_key_backfill_native',
    'test_audit_accumulation_native',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files_under(root):
    return [p for p in root.rglob('*') if p.is_file()
            and '__pycache__' not in p.parts and p.suffix != '.pyc']


def payload_under(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in files_under(root)}


def input_basis():
    inputs = []
    for directory in ('packages/python/tests', 'packages/python/examples',
                      'packages/browser/fixtures', 'tests/fixtures', 'scripts'):
        inputs.extend(files_under(ROOT / directory))
    inputs += [ROOT / name for name in (
        'tests/fixtures/layout-migration-planning.json',
        'tests/fixtures/operation-ordinal-issuer.json',
        'docs/helix/03-test/acceptance-outer-json-expected.proposal.json',
        'docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json',
        'docs/helix/02-design/contracts/bindings/bootstrap-permit-arithmetic-v0.1.proposal.json',
        'docs/helix/03-test/python-exact-value-vectors.proposal.json',
        'docs/helix/04-build/evidence/receipt-position-locator-vectors.json',
        'docs/helix/02-design/contracts/row-operation-registry-observation-v0.1.proposal.sql',
    )]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(inputs)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    owner = Path(os.environ.get('UMF_OWNER_ROOT', ''))
    if not os.environ.get('UMF_OWNER_ROOT') or not (owner / 'src/index.ts').is_file():
        raise ValueError('UMF_OWNER_ROOT must select the pinned independent test oracle source')
    owner_revision = subprocess.check_output(['git', '-C', str(owner), 'rev-parse', 'HEAD'], text=True).strip()
    owner_status = subprocess.check_output(['git', '-C', str(owner), 'status', '--porcelain',
        '--', 'src', 'package.json', 'bun.lock'], text=True)
    if owner_revision != UMF_OWNER_REVISION or owner_status:
        raise ValueError('Exact unmodified independent UMF owner source/lock required')
    bun = os.environ.get('TRUSS_BUN_EXECUTABLE') or shutil.which('bun') or 'bun'
    bun_version = subprocess.check_output([bun, '--version'], text=True).strip()
    if bun_version != '1.4.3':
        raise ValueError('Bun 1.4.3 required for the independent test oracle')
    loaded = Path(truss.__file__).resolve().parent
    if loaded.is_relative_to(ROOT) or not loaded.is_relative_to(Path(sys.prefix).resolve()):
        raise ValueError('Exact installed package outside the checkout required')
    source = ROOT / 'packages/python/src/truss'
    expected = payload_under(source)
    with zipfile.ZipFile(args.wheel) as archive:
        payload = {n.removeprefix('truss/'): archive.read(n)
                   for n in archive.namelist() if n.startswith('truss/') and not n.endswith('/')}
    if payload != expected or payload_under(loaded) != expected:
        raise ValueError('Installed/wheel/source payload correspondence failed')
    basis = input_basis()
    wheel_digest = digest(args.wheel)
    record = {'scope': __doc__, 'sourceCommit': os.environ.get('GITHUB_SHA') or subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'platform': platform.platform(), 'python': sys.version,
        'wheelSha256': wheel_digest, 'loadedPackage': str(loaded),
        'nativeManifestSha256': digest(source / '_catalog_runtime/manifest.json'),
        'packageFilesVerified': len(payload), 'inputBasis': basis,
        'ownerOracle': {'sourceCommit': owner_revision, 'sourceClean': not owner_status,
            'packageJsonSha256': digest(owner / 'package.json'), 'lockSha256': digest(owner / 'bun.lock'),
            'Bun': bun_version, 'scope': 'Independent strict protected regression test oracle; not a deployment sidecar'},
        'inputPinScope': 'All test/helper, Python example, browser fixture, root fixture and script files plus eight explicit fixture paths; not a hermetic host or external-owner-input claim',
        'outcomes': [],
        'passed': False, 'workerStopped': False, 'lakebaseAcceptance': 'not_run'}
    receipt = destination / 'qualification.json'

    def save():
        receipt.write_text(json.dumps(record, indent=2) + '\n')

    save()
    try:
        worker = WorkerCluster()
        with worker:
            environment = {**os.environ, **worker.environment(),
                'PYTHONPATH': str(ROOT / 'scripts'),
                'TRUSS_CENSUS_POSTGRES_BIN': str(Path(pgserver.__file__).resolve().parent / 'pginstall/bin')}
            environment.pop('TRUSS_NATIVE_TEST_SOCKET', None)
            for module in MODULES:
                command = [sys.executable, '-W', 'error', str(ROOT / 'scripts/run-python-test-module.py'),
                    'discover', '-s', str(ROOT / 'packages/python/tests'), '-p', module + '.py', '-v']
                started = time.monotonic()
                timed_out = False
                try:
                    run = subprocess.run(command, cwd=Path(sys.prefix), env=environment,
                                         capture_output=True, timeout=600)
                    output, returncode = run.stdout + run.stderr, run.returncode
                except subprocess.TimeoutExpired as error:
                    output = (error.stdout or b'') + (error.stderr or b'')
                    returncode, timed_out = None, True
                restored = False
                try:
                    worker.verify_clean()
                    restored = True
                except Exception as error:
                    output += ('\nWorker inventory verification failed: ' + repr(error)).encode()
                count = re.search(rb'Ran (\d+) tests? in ', output)
                path = destination / (module + '.log.gz')
                path.write_bytes(gzip.compress(output, mtime=0))
                row = {'module': module, 'command': command, 'returncode': returncode, 'timedOut': timed_out,
                    'tests': int(count.group(1)) if count else 0, 'baselineRestored': restored,
                    'seconds': time.monotonic() - started, 'log': path.name, 'logSha256': digest(path),
                    'passed': returncode == 0 and restored and count is not None
                    and int(count.group(1)) > 0 and re.search(rb'\nOK\s*$', output) is not None}
                record['outcomes'].append(row)
                save()
                print(json.dumps(row), flush=True)
                if not row['passed']:
                    break
            worker.verify_clean()
            record['workerBaselineRestored'] = True
        record['workerStopped'] = True
    except Exception as error:
        record['error'] = repr(error)
    record['inputsUnchanged'] = input_basis() == basis
    record['payloadUnchanged'] = (payload_under(source) == expected
        and payload_under(loaded) == expected and digest(args.wheel) == wheel_digest)
    record['ownerOracle']['inputsUnchanged'] = (
        subprocess.check_output(['git', '-C', str(owner), 'rev-parse', 'HEAD'], text=True).strip() == owner_revision
        and not subprocess.check_output(['git', '-C', str(owner), 'status', '--porcelain',
            '--', 'src', 'package.json', 'bun.lock'], text=True)
        and digest(owner / 'package.json') == record['ownerOracle']['packageJsonSha256']
        and digest(owner / 'bun.lock') == record['ownerOracle']['lockSha256'])
    record['tests'] = sum(row['tests'] for row in record['outcomes'])
    record['skipped'] = 0 if all(row['passed'] for row in record['outcomes']) else None
    record['passed'] = (len(record['outcomes']) == len(MODULES) and all(row['passed'] for row in record['outcomes'])
        and record['workerStopped'] and record['inputsUnchanged'] and record['payloadUnchanged']
        and record['ownerOracle']['inputsUnchanged'] and 'error' not in record)
    save()
    return 0 if record['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
