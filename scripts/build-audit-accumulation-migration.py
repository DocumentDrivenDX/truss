#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Append a native-qualified audit-reader-only edge to the latest runtime.

The prior 0.49 wheel is used only as a native source fixture. Its target is not
added to the published source-wheel matrix: existing public source wheels keep
their direct latest-only routes through the retained intermediate edge.
Capture source and target in both approved initializer timezones, then run
--finalize-captures --check-only before an explicitly authorized --package.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'packages/python/src/truss'
MIGRATIONS = PACKAGE / '_migrations'
SOURCE = '35fd797b5cf48dd888c68e53b9e599df20cffe00f8f3d33e1563820ea808d59f'
SQL_FRAGMENT = '_catalog_runtime/audit-reader-accumulation.sql'
ROUTINE = ('runtime_read_mutation_group_audit',
           'selected_attempt uuid, maximum_events integer, expected_release text, expected_digest text, include_data boolean')


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
        try:
            actual = digest((MIGRATIONS / name).read_bytes())
        except FileNotFoundError as exc:
            raise ValueError('Pinned migration artifact is missing: ' + name) from exc
        if actual != expected:
            raise ValueError('Pinned migration artifact bytes changed: ' + name)
    for name in immutable:
        if name not in files:
            raise ValueError('Immutable migration artifact has no current file pin: ' + name)


def _verify_source49_wheel(wheel, expected_wheel_sha256, previous_manifest_raw):
    raw = wheel.read_bytes()
    if digest(raw) != expected_wheel_sha256:
        raise ValueError('Exact 0.0.49 source wheel SHA-256 mismatch')
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if any(Path(name).is_absolute() or '..' in Path(name).parts for name in names):
            raise ValueError('Unsafe path in 0.0.49 source wheel')
        metadata = [name for name in names if name.endswith('.dist-info/METADATA')]
        if len(metadata) != 1:
            raise ValueError('Expected exactly one wheel METADATA file')
        version = [line for line in archive.read(metadata[0]).decode().splitlines()
                   if line.startswith('Version: ')]
        if version != ['Version: 0.0.49']:
            raise ValueError('Expected the exact 0.0.49 predecessor source wheel')
        if archive.read('truss/_migrations/manifest.json') != previous_manifest_raw:
            raise ValueError('The predecessor wheel does not carry the exact current migration manifest')
        runtime_manifest = archive.read('truss/_catalog_runtime/manifest.json')
        if digest(runtime_manifest) != SOURCE:
            raise ValueError('The predecessor wheel runtime manifest is not the retained 35fd source')
    return runtime_manifest


def _source_package(wheel, expected_wheel_sha256, previous_manifest_raw, destination):
    runtime_manifest = _verify_source49_wheel(wheel, expected_wheel_sha256, previous_manifest_raw)
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(destination)
    return runtime_manifest


def _verify_public48_wheel(wheel, pinned):
    entry = pinned.get('sourceWheels', {}).get('source48')
    if not entry or digest(wheel.read_bytes()) != entry['sha256']:
        raise ValueError('Exact previously published 0.0.48 source wheel required')
    with zipfile.ZipFile(wheel) as archive:
        previous_manifest_raw = archive.read('truss/_migrations/manifest.json')
        previous_digest = digest(previous_manifest_raw)
        previous_manifest_name = previous_digest + '.manifest.json'
        if previous_manifest_name not in pinned['files']:
            raise ValueError('Current package does not retain the exact published 0.0.48 manifest')
        if digest((MIGRATIONS / previous_manifest_name).read_bytes()) != previous_digest:
            raise ValueError('Retained 0.0.48 migration manifest bytes changed')
        if (MIGRATIONS / previous_manifest_name).read_bytes() != previous_manifest_raw:
            raise ValueError('Current archive differs from the public 0.0.48 migration manifest')
        previous = json.loads(previous_manifest_raw)
        if previous.get('target') != entry.get('runtimeManifestSha256'):
            raise ValueError('Published 0.0.48 migration manifest target differs from its source-wheel pin')
        wheel_names = set(archive.namelist())
        for name in previous['immutableFiles']:
            if name not in previous['files'] or name not in pinned['files']:
                raise ValueError('Published 0.0.48 immutable artifact lost its pin: ' + name)
            expected = previous['files'][name]
            if pinned['files'][name] != expected or name not in pinned['immutableFiles']:
                raise ValueError('Published 0.0.48 immutable artifact pin or custody changed: ' + name)
            archive_name = 'truss/_migrations/' + name
            if archive_name not in wheel_names:
                raise ValueError('Published 0.0.48 wheel is missing immutable artifact: ' + name)
            original = archive.read(archive_name)
            if digest(original) != expected or (MIGRATIONS / name).read_bytes() != original:
                raise ValueError('Published 0.0.48 immutable artifact bytes changed: ' + name)
    return previous_manifest_raw, previous_digest


def _capture_pair(source_wheel, source_wheel_sha256, public48_wheel,
                  target_digest, timezone, output_dir):
    sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'packages/python/src'),
                    str(ROOT / 'packages/python/tests')]
    builder = _builder()
    from native_fixture import DatabaseFixture, WorkerCluster
    from test_catalog_relational_support import relational_document

    output_dir.mkdir(parents=True, exist_ok=True)
    os.environ['TZ'] = timezone
    if hasattr(__import__('time'), 'tzset'):
        __import__('time').tzset()
    pinned = read_json(MIGRATIONS / 'manifest.json')
    previous_manifest_raw = (MIGRATIONS / 'manifest.json').read_bytes()
    _verify_pinned_artifact_bytes(pinned)
    _verify_public48_wheel(public48_wheel, pinned)
    actual_target_digest = digest((PACKAGE / '_catalog_runtime/manifest.json').read_bytes())
    if actual_target_digest != target_digest:
        raise ValueError('Current runtime target differs from the explicit target SHA-256 pin')
    with tempfile.TemporaryDirectory(prefix='truss-audit-accumulation-') as temporary:
        run_dir = Path(temporary)
        source_root = run_dir / 'source49'
        source_root.mkdir()
        _source_package(source_wheel, source_wheel_sha256, previous_manifest_raw, source_root)
        model = relational_document()
        model['id'] = 'adoc'
        model_path = run_dir / 'model.json'
        model_path.write_text(json.dumps(model, sort_keys=True) + '\n')
        with WorkerCluster() as worker:
            fixture = None
            try:
                fixture = DatabaseFixture(worker.root)
                source = builder._capture('source35', source_root, fixture.get_uri(), model_path, run_dir)
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
        'interfaceVersion': 'truss-audit-accumulation-capture/0.1',
        'initializationTimeZone': timezone,
        'sourceWheelSha256': source_wheel_sha256,
        'public48WheelSha256': pinned['sourceWheels']['source48']['sha256'],
        'targetManifestSha256': target_digest,
        'source': source,
        'target': target,
    }
    name = timezone.replace('/', '_') + '.json'
    (output_dir / name).write_bytes(canonical(capture) + b'\n')
    return capture


def _routine_map(artifact):
    return {(row[0], row[1]): row[2] for row in artifact['inventory']['routines']}


def _validate_pair(ny, utc, target_digest, source_wheel_sha256, public48_wheel_sha256):
    from truss._migration_verify import matches_inventory

    if ny['initializationTimeZone'] != 'America/New_York' or utc['initializationTimeZone'] != 'UTC':
        raise ValueError('Audit-accumulation captures must cover New York and UTC initialization')
    old = read_json(MIGRATIONS / f'{SOURCE}.json')
    pinned = read_json(MIGRATIONS / 'manifest.json')
    exact_acl_name = pinned.get('exactAclProfiles', {}).get(SOURCE)
    if not exact_acl_name:
        raise ValueError('Retained 35fd exact ACL profile is missing from the migration manifest')
    exact_acl_profile = read_json(MIGRATIONS / exact_acl_name)
    if (exact_acl_profile.get('runtimeManifestSha256') != SOURCE
            or exact_acl_profile.get('aclNameProfile') != 'truss-native-acl-names/0.2'):
        raise ValueError('Retained 35fd exact ACL evidence has an invalid identity')
    target_profile = None
    for capture in (ny, utc):
        if capture['sourceWheelSha256'] != source_wheel_sha256:
            raise ValueError('Capture was not produced from the exact predecessor wheel')
        if capture['public48WheelSha256'] != public48_wheel_sha256:
            raise ValueError('Capture did not bind the exact public 0.0.48 wheel')
        if capture.get('targetManifestSha256') != target_digest:
            raise ValueError('Capture target differs from the explicit target manifest pin')
        source, target = capture['source'], capture['target']
        if source['sha256'] != SOURCE or target['sha256'] != target_digest:
            raise ValueError('Capture source/target runtime manifest differs from its frozen pin')
        if not matches_inventory(source['inventory'], old):
            raise ValueError('Predecessor native inventory differs from the retained 35fd profile')
        if source['exactAcl'] != exact_acl_profile['acl'] or source['acl'] != old['acl']:
            raise ValueError('Predecessor ACL differs from the retained 35fd profile')
        if source['configuration'] != old['configuration']:
            raise ValueError('Predecessor preparation configuration differs from retained profile')
        if source.get('managedGrants') != old.get('managedGrants'):
            raise ValueError('Predecessor managed-grants carrier differs from retained profile')
        if target['exactAcl'] != source['exactAcl'] or target['acl'] != source['acl']:
            raise ValueError('Audit-reader SQL must preserve all exact native ACLs')
        if target['configuration'] != source['configuration']:
            raise ValueError('Audit-reader SQL must preserve preparation configuration')
        if target.get('managedGrants') != source.get('managedGrants'):
            raise ValueError('Audit-reader SQL must preserve managed-grants carrier evidence')
        before, after = source['inventory'], target['inventory']
        stable = set(before) - {'routines'}
        if not matches_inventory({key: after[key] for key in stable},
                                 {'inventory': {key: before[key] for key in stable},
                                  'initializationAlternatives': source.get('initializationAlternatives', [])}):
            raise ValueError('Audit-reader target changes native structure outside the selected routine')
        old_routines, new_routines = _routine_map(source), _routine_map(target)
        if set(old_routines) != set(new_routines):
            raise ValueError('Audit-reader target changes routine identities')
        changed = {identity for identity in old_routines
                   if old_routines[identity] != new_routines[identity]}
        if changed != {ROUTINE}:
            raise ValueError('Only runtime_read_mutation_group_audit may change in the audit accumulation edge')
        source_manifest = source['manifest']
        target_manifest = target['manifest']
        relative = SQL_FRAGMENT.removeprefix('_catalog_runtime/')
        if relative not in target_manifest['files']:
            raise ValueError('Target runtime manifest does not bind the audit accumulation SQL fragment')
        if relative in source_manifest['files']:
            raise ValueError('Audit accumulation must be a newly appended runtime source file')
        expected_files = dict(source_manifest['files'])
        expected_files[relative] = digest((PACKAGE / SQL_FRAGMENT).read_bytes())
        if target_manifest['files'] != expected_files:
            raise ValueError('Target runtime source must append only the audit accumulation SQL fragment')
        target_profile = target
    if _routine_map(ny['target']) != _routine_map(utc['target']):
        raise ValueError('Changed audit routine differs across initialization timezones')
    if ny['source']['exactAcl'] != utc['source']['exactAcl'] or ny['target']['exactAcl'] != utc['target']['exactAcl']:
        raise ValueError('Native ACL census differs across initialization timezones')
    return ny['source'], target_profile


def _package(source, target, source_wheel, source_wheel_sha256,
             public48_wheel, target_digest):
    pinned = read_json(MIGRATIONS / 'manifest.json')
    previous_manifest_raw = (MIGRATIONS / 'manifest.json').read_bytes()
    _verify_pinned_artifact_bytes(pinned)
    if pinned['target'] != SOURCE or source['sha256'] != SOURCE:
        raise ValueError('The additive edge must start at the current 35fd target')
    if target['sha256'] != target_digest or target_digest == SOURCE:
        raise ValueError('The candidate target manifest pin is inconsistent')
    if digest((PACKAGE / '_catalog_runtime/manifest.json').read_bytes()) != target_digest:
        raise ValueError('Current runtime source does not match the captured target digest')
    _verify_public48_wheel(public48_wheel, pinned)
    _verify_source49_wheel(source_wheel, source_wheel_sha256, previous_manifest_raw)
    archive_name = digest(previous_manifest_raw) + '.manifest.json'
    sql_path = PACKAGE / SQL_FRAGMENT
    if not sql_path.is_file():
        raise ValueError('Audit accumulation SQL fragment is missing')
    sql = sql_path.read_text().strip()
    first_statement = None
    for line in sql.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith('--'):
            continue
        first_statement = stripped
        break
    if first_statement is None or not first_statement.startswith(
            'CREATE OR REPLACE FUNCTION truss.runtime_read_mutation_group_audit('):
        raise ValueError('New migration edge must replace only the selected native audit routine')

    previous = read_json(MIGRATIONS / f'{SOURCE}.json')
    old_routines, target_routines = _routine_map(previous), _routine_map(target)
    if old_routines.get(ROUTINE) == target_routines.get(ROUTINE):
        raise ValueError('The selected audit routine did not change in the target')

    edge_name = f'edge-{SOURCE}-{target_digest}.json'
    target_name = f'{target_digest}.json'
    acl_name = f'{target_digest}.acl.json'
    relative = SQL_FRAGMENT.removeprefix('_catalog_runtime/')
    if target['manifest']['files'].get(relative) != digest(sql_path.read_bytes()):
        raise ValueError('Target source manifest does not bind the exact audit accumulation SQL bytes')
    target_profile = dict(target)
    exact_acl = target_profile.pop('exactAcl')
    target_profile.pop('aclNameProfile', None)
    target_profile['definitionAlternatives'] = previous.get('definitionAlternatives', [])
    target_profile['initializationAlternatives'] = previous.get('initializationAlternatives', [])
    exact_acl = {'acl': exact_acl, 'aclNameProfile': 'truss-native-acl-names/0.2',
                 'runtimeManifestSha256': target_digest}
    recipe = {'source': SOURCE, 'target': target_digest, 'steps': [sql],
              'ownership': [], 'moduleGrants': []}
    generated = {target_name: canonical(target_profile) + b'\n',
                 acl_name: canonical(exact_acl) + b'\n',
                 edge_name: canonical(recipe) + b'\n',
                 archive_name: previous_manifest_raw}

    manifest = dict(pinned)
    manifest['target'] = target_digest
    manifest['targetRelease'] = target['manifest']['releaseId']
    manifest['edges'] = list(pinned['edges']) + [
        {'source': SOURCE, 'target': target_digest, 'direction': 'forward', 'artifact': edge_name}
    ]
    manifest['exactAclProfiles'] = dict(pinned.get('exactAclProfiles', {}))
    manifest['exactAclProfiles'][target_digest] = acl_name
    immutable = list(pinned['immutableFiles'])
    for name in (target_name, acl_name, edge_name, archive_name):
        if name not in immutable:
            immutable.append(name)
    manifest['immutableFiles'] = immutable
    all_bytes = {name: (MIGRATIONS / name).read_bytes() for name in pinned['files']}
    for name, raw in generated.items():
        if name in all_bytes and all_bytes[name] != raw:
            raise ValueError('Generated audit accumulation artifact collides with existing bytes: ' + name)
        if name not in all_bytes and (MIGRATIONS / name).exists():
            raise ValueError('Unpinned artifact path already exists: ' + name)
        all_bytes[name] = raw
    manifest['files'] = {name: digest(raw) for name, raw in sorted(all_bytes.items())}
    return manifest, generated


def main():
    sys.path.insert(0, str(ROOT / 'packages/python/src'))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source49-wheel', type=Path, required=True,
                        help='Exact 0.0.49 wheel used as a native source fixture, not admitted as a public source')
    parser.add_argument('--expected-source49-wheel-sha256', required=True)
    parser.add_argument('--expected-target-manifest-sha256', required=True)
    parser.add_argument('--source48-wheel', type=Path, required=True,
                        help='Exact public 0.0.48 wheel used to verify prior immutable evidence')
    parser.add_argument('--output', type=Path, required=True,
                        help='Capture/preview directory; use the same directory in both timezone runs')
    parser.add_argument('--initialization-time-zone', choices=('America/New_York', 'UTC'))
    parser.add_argument('--peer', type=Path, help='Other timezone capture directory')
    parser.add_argument('--finalize-captures', action='store_true')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--package', action='store_true')
    args = parser.parse_args()

    if len(args.expected_source49_wheel_sha256) != 64 or len(args.expected_target_manifest_sha256) != 64:
        parser.error('Exact 0.0.49 source wheel and target manifest SHA-256 values required')
    if args.finalize_captures == (args.initialization_time_zone is not None):
        parser.error('Use exactly one of --finalize-captures or --initialization-time-zone')
    if args.finalize_captures and not args.peer:
        parser.error('--finalize-captures requires the independent timezone --peer directory')
    if args.package and (not args.finalize_captures or not args.peer):
        parser.error('--package requires both saved initializer captures')

    pinned = read_json(MIGRATIONS / 'manifest.json')
    if pinned.get('target') != SOURCE:
        raise ValueError('Current migration manifest does not target retained 35fd runtime')
    if args.finalize_captures:
        ny = read_json(args.output / 'America_New_York.json')
        utc = read_json(args.peer / 'UTC.json')
    else:
        _capture_pair(args.source49_wheel, args.expected_source49_wheel_sha256,
                      args.source48_wheel, args.expected_target_manifest_sha256,
                      args.initialization_time_zone, args.output)
        return

    target_raw = (PACKAGE / '_catalog_runtime/manifest.json').read_bytes()
    target_digest = digest(target_raw)
    if target_digest != args.expected_target_manifest_sha256:
        raise ValueError('Current runtime target differs from the explicit target SHA-256 pin')
    source, target = _validate_pair(
        ny, utc, target_digest, args.expected_source49_wheel_sha256,
        pinned['sourceWheels']['source48']['sha256'])
    if args.check_only:
        _package(source, target, args.source49_wheel, args.expected_source49_wheel_sha256,
                 args.source48_wheel, target_digest)
        print('Audit accumulation captures, all current pins, public 0.0.48 immutable artifacts, and the 35fd→target route are consistent; no package artifacts written.')
        return
    manifest, generated = _package(
        source, target, args.source49_wheel, args.expected_source49_wheel_sha256,
        args.source48_wheel, target_digest)
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
    print(json.dumps({'source': SOURCE, 'target': target_digest,
                      'edge': f'edge-{SOURCE}-{target_digest}.json',
                      'source49WheelSha256': args.expected_source49_wheel_sha256,
                      'public48WheelSha256': pinned['sourceWheels']['source48']['sha256'],
                      'files': sorted(generated), 'writtenTo': str(destination)}, indent=2))


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT / 'scripts'))
    main()
