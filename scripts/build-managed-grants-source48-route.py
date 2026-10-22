#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Append the published 0.0.48 → current managed-grants migration route.

Capture both approved initializer timezones from the exact public 0.0.48 wheel.
The source profile already exists as the retained c433 candidate; this producer
adds its exact native ACL census and the final managed-grants-only edge while
preserving all published migration inputs and the original 0.0.48 manifest.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'packages/python/src/truss'
MIGRATIONS = PACKAGE / '_migrations'
SOURCE48 = 'c4339ac7f09ab5a004c272ab00962107a970938004c1765ec4163e4d5ca9b6f0'
TARGET = '35fd797b5cf48dd888c68e53b9e599df20cffe00f8f3d33e1563820ea808d59f'
SOURCE_LABEL = 'source48'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def _builder():
    path = ROOT / 'scripts/build-managed-grants-migration.py'
    spec = importlib.util.spec_from_file_location('managed_grants_migration_builder', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _wheel_package(wheel, expected_wheel_sha256, destination):
    raw = wheel.read_bytes()
    if digest(raw) != expected_wheel_sha256:
        raise ValueError('Public v0.0.48 wheel SHA-256 does not match the supplied pin')
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if any(Path(name).is_absolute() or '..' in Path(name).parts for name in names):
            raise ValueError('Unsafe path in source48 wheel')
        metadata = [name for name in names if name.endswith('.dist-info/METADATA')]
        if len(metadata) != 1:
            raise ValueError('Expected exactly one wheel METADATA file')
        version_lines = [line for line in archive.read(metadata[0]).decode().splitlines()
                         if line.startswith('Version: ')]
        if version_lines != ['Version: 0.0.48']:
            raise ValueError('Source wheel is not the public v0.0.48 release')
        archive.extractall(destination)
    manifest_path = destination / 'truss/_catalog_runtime/manifest.json'
    manifest_raw = manifest_path.read_bytes()
    if digest(manifest_raw) != SOURCE48:
        raise ValueError('Public v0.0.48 wheel does not contain the retained c433 runtime profile')
    return manifest_raw


def _capture_pair(wheel, wheel_sha256, timezone, output_dir):
    sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'packages/python/src'),
                    str(ROOT / 'packages/python/tests')]
    builder = _builder()
    from native_fixture import DatabaseFixture, WorkerCluster
    from test_catalog_relational_support import relational_document

    output_dir.mkdir(parents=True, exist_ok=True)
    os.environ['TZ'] = timezone
    if hasattr(__import__('time'), 'tzset'):
        __import__('time').tzset()
    with tempfile.TemporaryDirectory(prefix='truss-managed-grants-source48-') as temporary:
        run_dir = Path(temporary)
        source_root = run_dir / 'source48'
        source_root.mkdir()
        _wheel_package(wheel, wheel_sha256, source_root)
        model = relational_document()
        model['id'] = 'adoc'
        model_path = run_dir / 'model.json'
        model_path.write_text(json.dumps(model, sort_keys=True) + '\n')
        with WorkerCluster() as worker:
            fixture = None
            try:
                fixture = DatabaseFixture(worker.root)
                source = builder._capture('source48', source_root, fixture.get_uri(), model_path, run_dir)
                fixture.cleanup()
                fixture = None
                worker.verify_clean()
                fixture = DatabaseFixture(worker.root)
                target = builder._capture('target', ROOT / 'packages/python/src', fixture.get_uri(), model_path, run_dir)
                fixture.cleanup()
                fixture = None
                worker.verify_clean()
            finally:
                if fixture is not None:
                    fixture.cleanup()
    capture = {
        'interfaceVersion': 'truss-managed-grants-source48-capture/0.1',
        'initializationTimeZone': timezone,
        'sourceWheelSha256': wheel_sha256,
        'source': source,
        'target': target,
    }
    name = timezone.replace('/', '_') + '.json'
    (output_dir / name).write_bytes(canonical(capture) + b'\n')
    return capture


def _legacy_acl_projection(profile):
    """Project the original profile's old routine labels to PostgreSQL name width."""
    def name_limit(value):
        return value.encode('utf-8')[:63].decode('utf-8')
    return {role: sorted({(kind, name_limit(name), privilege, grantable)
                          for kind, name, privilege, grantable in rows})
            for role, rows in profile.items()}


def _validate_capture(ny, utc, pinned, target_digest, wheel_sha256):
    from truss._migration_verify import matches_inventory

    if ny['initializationTimeZone'] != 'America/New_York' or utc['initializationTimeZone'] != 'UTC':
        raise ValueError('Source48 captures must cover New York and UTC initialization')
    for capture in (ny, utc):
        if capture['sourceWheelSha256'] != wheel_sha256:
            raise ValueError('Capture was not produced from the exact pinned source48 wheel')
        source, target = capture['source'], capture['target']
        if source['sha256'] != SOURCE48 or target['sha256'] != target_digest:
            raise ValueError('Capture source/target runtime manifest differs from its frozen pin')
        old_source = read_json(MIGRATIONS / f'{SOURCE48}.json')
        if not matches_inventory(source['inventory'], old_source):
            raise ValueError('Public source48 native inventory differs from retained c433 profile')
        if _legacy_acl_projection(old_source['acl']) != {
                role: sorted(set(map(tuple, rows))) for role, rows in source['acl'].items()}:
            raise ValueError('Public source48 ACL differs from retained c433 ACL after legacy-name projection')
        if source['configuration'] != old_source['configuration']:
            raise ValueError('Public source48 preparation configuration differs from retained profile')
        current_target = read_json(MIGRATIONS / f'{target_digest}.json')
        if not matches_inventory(target['inventory'], current_target):
            raise ValueError('Captured target native inventory differs from the packaged target profile')
        expected_exact = read_json(MIGRATIONS / f'{target_digest}.acl.json')['acl']
        if target['exactAcl'] != expected_exact:
            raise ValueError('Captured target exact ACL differs from its immutable target ACL profile')
        if source['exactAcl'] != target['exactAcl']:
            raise ValueError('The managed-grants route must preserve the exact source ACL')
    if ny['source']['inventory']['columns'] != utc['source']['inventory']['columns']:
        raise ValueError('Source48 column fingerprints differ across initializer captures')
    if ny['target']['inventory']['columns'] != utc['target']['inventory']['columns']:
        raise ValueError('Current target column fingerprints differ across initializer captures')
    if ny['source']['exactAcl'] != utc['source']['exactAcl']:
        raise ValueError('Source48 exact ACL census differs across initializer captures')
    if ny['target']['exactAcl'] != utc['target']['exactAcl']:
        raise ValueError('Target exact ACL census differs across initializer captures')
    return ny['source'], ny['target']


def _verify_pinned_artifact_bytes(pinned):
    files = pinned.get('files')
    immutable = pinned.get('immutableFiles')
    if not isinstance(files, dict) or not isinstance(immutable, list):
        raise ValueError('Current migration manifest has no valid files/immutableFiles inventory')
    if len(immutable) != len(set(immutable)):
        raise ValueError('Current immutable migration inventory contains duplicate paths')
    for name, expected in files.items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or path.name != name:
            raise ValueError('Unsafe migration artifact path in manifest: ' + name)
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError('Invalid SHA-256 pin for migration artifact: ' + name)
        artifact = MIGRATIONS / name
        try:
            actual = digest(artifact.read_bytes())
        except FileNotFoundError as exc:
            raise ValueError('Pinned migration artifact is missing: ' + name) from exc
        if actual != expected:
            raise ValueError('Pinned migration artifact bytes changed: ' + name)
    missing = [name for name in immutable if name not in files]
    if missing:
        raise ValueError('Immutable migration artifact has no current file pin: ' + missing[0])


def _package(source, target, wheel, wheel_sha256, target_digest):
    pinned = read_json(MIGRATIONS / 'manifest.json')
    _verify_pinned_artifact_bytes(pinned)
    if pinned['target'] != target_digest or target_digest != TARGET:
        raise ValueError('The current target changed; re-freeze before extending source48')
    if SOURCE48 in pinned.get('sources', []):
        raise ValueError('Source48 is already admitted; refusing to rewrite its publication record')
    if f'{SOURCE48}.json' not in pinned['files']:
        raise ValueError('Retained c433 source profile is missing from the current package')
    if pinned['files'][f'{SOURCE48}.json'] != digest((MIGRATIONS / f'{SOURCE48}.json').read_bytes()):
        raise ValueError('Retained c433 source profile bytes no longer match their package pin')

    with zipfile.ZipFile(wheel) as archive:
        previous_manifest_raw = archive.read('truss/_migrations/manifest.json')
        previous_artifact_names = set(archive.namelist())
    previous_manifest = json.loads(previous_manifest_raw)
    if previous_manifest.get('target') != SOURCE48:
        raise ValueError('The public source48 wheel does not retain c433 as its published target')
    for name in previous_manifest['immutableFiles']:
        if name not in previous_manifest.get('files', {}):
            raise ValueError('Published 0.0.48 immutable artifact has no file pin: ' + name)
        if name not in pinned.get('immutableFiles', []):
            raise ValueError('Published 0.0.48 immutable artifact lost immutable membership: ' + name)
        if name not in pinned['files'] or pinned['files'][name] != previous_manifest['files'][name]:
            raise ValueError('Published 0.0.48 immutable migration artifact changed: ' + name)
        wheel_path = 'truss/_migrations/' + name
        if wheel_path not in previous_artifact_names:
            raise ValueError('Published 0.0.48 wheel is missing immutable artifact bytes: ' + name)
        with zipfile.ZipFile(wheel) as archive:
            wheel_bytes = archive.read(wheel_path)
        if digest(wheel_bytes) != previous_manifest['files'][name]:
            raise ValueError('Published 0.0.48 immutable artifact bytes do not match its pin: ' + name)
        if (MIGRATIONS / name).read_bytes() != wheel_bytes:
            raise ValueError('Current immutable artifact bytes differ from published 0.0.48 wheel: ' + name)
    previous_manifest_digest = digest(previous_manifest_raw)
    previous_manifest_name = previous_manifest_digest + '.manifest.json'

    previous_target = read_json(MIGRATIONS / f'{SOURCE48}.json')
    builder = _builder()
    builder._validate_managed_delta(previous_target, target)
    managed_sql = (PACKAGE / '_catalog_runtime/managed-grants.sql').read_text().strip()
    if 'ADD COLUMN managed_grants jsonb' not in managed_sql or 'CREATE OR REPLACE FUNCTION truss.runtime_current_installation()' not in managed_sql:
        raise ValueError('The current managed-grants SQL fragment changed unexpectedly')
    existing_edge = read_json(MIGRATIONS / f"edge-{builder.SOURCE47}-{target_digest}.json")
    if existing_edge['target'] != target_digest:
        raise ValueError('Current source47 edge does not describe the frozen target')

    acl_name = f'{SOURCE48}.acl.json'
    edge_name = f'edge-{SOURCE48}-{target_digest}.json'
    exact_acl = {'acl': source['exactAcl'],
                 'aclNameProfile': 'truss-native-acl-names/0.2',
                 'runtimeManifestSha256': SOURCE48}
    recipe = {'source': SOURCE48, 'target': target_digest, 'steps': [managed_sql],
              'ownership': [], 'moduleGrants': []}
    generated = {acl_name: canonical(exact_acl) + b'\n',
                 edge_name: canonical(recipe) + b'\n',
                 previous_manifest_name: previous_manifest_raw}

    manifest = dict(pinned)
    manifest['sources'] = list(pinned['sources']) + [SOURCE48]
    manifest['sourceWheels'] = dict(pinned['sourceWheels'])
    manifest['sourceWheels'][SOURCE_LABEL] = {
        'filename': wheel.name,
        'runtimeManifestSha256': SOURCE48,
        'sha256': wheel_sha256,
        'tag': 'v0.0.48',
    }
    manifest['edges'] = list(pinned['edges']) + [
        {'source': SOURCE48, 'target': target_digest, 'direction': 'forward', 'artifact': edge_name}
    ]
    manifest['exactAclProfiles'] = dict(pinned.get('exactAclProfiles', {}))
    manifest['exactAclProfiles'][SOURCE48] = acl_name
    immutable = list(pinned['immutableFiles'])
    for name in (f'{SOURCE48}.json', acl_name, edge_name, previous_manifest_name):
        if name not in immutable:
            immutable.append(name)
    manifest['immutableFiles'] = immutable

    all_bytes = {name: (MIGRATIONS / name).read_bytes() for name in pinned['files']}
    for name, raw in generated.items():
        if name in all_bytes and all_bytes[name] != raw:
            raise ValueError('Generated source48 artifact collides with existing bytes: ' + name)
        all_bytes[name] = raw
    manifest['files'] = {name: digest(raw) for name, raw in sorted(all_bytes.items())}
    return manifest, generated


def main():
    sys.path.insert(0, str(ROOT / 'packages/python/src'))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source48-wheel', type=Path, required=True)
    parser.add_argument('--expected-source48-wheel-sha256', required=True)
    parser.add_argument('--expected-target-manifest-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True,
                        help='Capture/preview directory; use the same directory in both timezone runs')
    parser.add_argument('--initialization-time-zone', choices=('America/New_York', 'UTC'))
    parser.add_argument('--peer', type=Path,
                        help='The other timezone capture directory; required for final --package')
    parser.add_argument('--finalize-captures', action='store_true',
                        help='Validate two saved captures without starting another native worker')
    parser.add_argument('--check-only', action='store_true', help='Validate inputs without writing package artifacts')
    parser.add_argument('--package', action='store_true', help='Append source48 profile, exact ACL, and edge to the current manifest')
    args = parser.parse_args()

    if len(args.expected_source48_wheel_sha256) != 64 or len(args.expected_target_manifest_sha256) != 64:
        parser.error('Both exact public-wheel and frozen target SHA-256 values are required')
    target_raw = (PACKAGE / '_catalog_runtime/manifest.json').read_bytes()
    target_digest = digest(target_raw)
    if target_digest != args.expected_target_manifest_sha256 or target_digest != TARGET:
        raise ValueError('Current target runtime manifest differs from the frozen 35fd target')
    if args.finalize_captures == (args.initialization_time_zone is not None):
        parser.error('Use exactly one of --finalize-captures or --initialization-time-zone')
    if args.finalize_captures and not args.peer:
        parser.error('--finalize-captures requires the independent timezone --peer directory')
    if args.package and (not args.finalize_captures or not args.peer):
        parser.error('--package requires both saved initializer captures')

    pinned = read_json(MIGRATIONS / 'manifest.json')
    if f'{SOURCE48}.json' not in pinned['files'] or f'{TARGET}.json' not in pinned['files']:
        raise ValueError('Retained c433 source or current target profile is missing')
    if digest(args.source48_wheel.read_bytes()) != args.expected_source48_wheel_sha256:
        raise ValueError('Source48 wheel bytes do not match the explicit checksum pin')

    if args.finalize_captures:
        ny = read_json(args.output / 'America_New_York.json')
        utc = read_json(args.peer / 'UTC.json')
    else:
        os.environ['TZ'] = args.initialization_time_zone
        capture = _capture_pair(args.source48_wheel, args.expected_source48_wheel_sha256,
                                args.initialization_time_zone, args.output)
        print(json.dumps({'capture': str(args.output / (args.initialization_time_zone.replace('/', '_') + '.json')),
                          'sourceManifestSha256': capture['source']['sha256'],
                          'targetManifestSha256': capture['target']['sha256'],
                          'timezone': args.initialization_time_zone}, indent=2))
        return

    source, target = _validate_capture(ny, utc, pinned, target_digest,
                                       args.expected_source48_wheel_sha256)
    if args.check_only:
        _package(source, target, args.source48_wheel,
                 args.expected_source48_wheel_sha256, target_digest)
        print('Public source48 profile, pinned artifact bytes, immutable 0.0.48 artifacts, and c433→35fd route inputs are consistent; no package artifacts written.')
        return
    manifest, generated = _package(source, target, args.source48_wheel,
                                   args.expected_source48_wheel_sha256, target_digest)
    if args.package:
        for name, raw in generated.items():
            (MIGRATIONS / name).write_bytes(raw)
        (MIGRATIONS / 'manifest.json').write_bytes(canonical(manifest) + b'\n')
        destination = MIGRATIONS
    else:
        destination = args.output / 'package'
        destination.mkdir(exist_ok=True)
        for name, raw in generated.items():
            (destination / name).write_bytes(raw)
        (destination / 'manifest.json').write_bytes(canonical(manifest) + b'\n')
    print(json.dumps({'source': SOURCE48, 'target': target_digest,
                      'edge': f'edge-{SOURCE48}-{target_digest}.json',
                      'source48WheelSha256': args.expected_source48_wheel_sha256,
                      'files': sorted(generated), 'writtenTo': str(destination)}, indent=2))


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT / 'scripts'))
    main()
