#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Capture and build the explicit v0.0.47 → managed-grants migration edge.

This is intentionally separate from build-runtime-migration-baseline.py: that
script owns only the original receipt-ledger baseline. This command verifies
real source47 and current target installations, then appends the retained HF
source47→c4339 edge statements before the newly authored managed-grants SQL
and current changed routines. It never edits published source44/46/47 bytes.

Capture is deferred until the current runtime source digest is frozen. Run once
per initializer timezone, retaining the first capture directory as --peer for
the other timezone. WorkerCluster/DatabaseFixture own lifecycle and cleanup.
"""
from __future__ import annotations

import argparse
import hashlib
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
OLD_HF_TARGET = 'c4339ac7f09ab5a004c272ab00962107a970938004c1765ec4163e4d5ca9b6f0'
SOURCE47 = '7ac989147f22d437b1ce0d814ebbfaa25aa868ab5495de125aa5e2bda7b963ea'
MANAGED_COLUMN = 'managed_grants'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_bytes())


def _source47_package(wheel: Path, destination: Path, pinned: dict):
    expected = pinned['sourceWheels']['source47']
    if digest(wheel.read_bytes()) != expected['sha256']:
        raise ValueError('Exact published v0.0.47 wheel required')
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if any(Path(name).is_absolute() or '..' in Path(name).parts for name in names):
            raise ValueError('Unsafe path in source47 wheel')
        archive.extractall(destination)
    manifest_path = destination / 'truss/_catalog_runtime/manifest.json'
    raw = manifest_path.read_bytes()
    if digest(raw) != SOURCE47 or digest(raw) != expected['runtimeManifestSha256']:
        raise ValueError('Published v0.0.47 native manifest bytes changed')
    return raw


def _capture(label: str, package_root: Path, uri: str, model_path: Path, run_dir: Path):
    """Install one selected package in its own disposable native database."""
    from truss._migration_verify import acl, context, roles, structure
    import psycopg

    producer = ROOT / 'packages/python/tests/runtime_migration_fixture.py'
    output = run_dir / f'{label}-fixture.json'
    env = dict(os.environ)
    env['PYTHONPATH'] = str(package_root) + os.pathsep + str(ROOT / 'packages/python/tests')
    completed = subprocess.run(
        [sys.executable, str(producer), uri, str(model_path), str(output)],
        env=env, text=True, capture_output=True, timeout=180)
    if completed.returncode:
        raise RuntimeError(f'{label} fixture failed:\n{completed.stdout}\n{completed.stderr}')

    with psycopg.connect(uri, autocommit=True) as connection, connection.cursor() as cursor:
        cursor.execute('SET search_path=pg_catalog,pg_temp')
        observed, owner, registrar, managed_policy = context(cursor)
        if (managed_policy.get('roles') or managed_policy.get('observations')):
            raise ValueError(f'{label} source/target fixture must have the strict empty managed-grants policy')
        native = structure(cursor)
        role_map = roles(cursor, owner, registrar)
        profile = {kind: [] for kind in
                   ('owner', 'registrar', 'administrator', 'reader', 'writer', 'feed', 'audit', 'public')}
        for kind, name, _object_owner, grantee, privilege, grantable, _grantor in acl(cursor):
            meanings = role_map.get(grantee)
            if not meanings or len(meanings) != 1:
                raise ValueError(f'Unclassified installation role in {label} ACL: {grantee!r}/{meanings!r}')
            profile[next(iter(meanings))].append([kind, name, privilege, grantable])
        for rows in profile.values():
            rows.sort()
        exact_acl = {kind: [] for kind in profile}
        exact_role_map = roles(cursor, owner, registrar)
        for kind, name, _object_owner, grantee, privilege, grantable, _grantor in acl(cursor, full_names=True):
            meanings = exact_role_map.get(grantee)
            if not meanings or len(meanings) != 1:
                raise ValueError(f'Unclassified exact ACL role in {label}: {grantee!r}/{meanings!r}')
            exact_acl[next(iter(meanings))].append([kind, name, privilege, grantable])
        for rows in exact_acl.values():
            rows.sort()
        cursor.execute('SELECT preparation_configuration FROM truss.catalog_runtime_installation')
        configuration = cursor.fetchone()[0]
        manifest_raw = (package_root / 'truss/_catalog_runtime/manifest.json').read_bytes()
        artifact = {
            'inventory': native,
            'acl': profile,
            'configuration': configuration,
            'manifest': json.loads(manifest_raw),
            'sha256': digest(manifest_raw),
            'definitionAlternatives': [],
            'initializationAlternatives': [],
            'aclNameProfile': 'truss-native-acl-names/0.2',
            'exactAcl': exact_acl,
        }
        if (package_root / 'truss/_catalog_runtime/managed-grants.sql').exists():
            cursor.execute('SELECT managed_grants FROM truss.catalog_runtime_installation WHERE singleton')
            artifact['managedGrants'] = cursor.fetchone()[0]
    for relative, expected in artifact['manifest']['files'].items():
        packaged = package_root / 'truss/_catalog_runtime' / relative
        if digest(packaged.read_bytes()) != expected:
            raise ValueError(f'{label} runtime file differs from its manifest: {relative}')
    return artifact


def _routine_map(artifact):
    return {(row[0], row[1]): row[2] for row in artifact['inventory']['routines']}


def _validate_managed_delta(previous: dict, target: dict):
    """Admit the authored final column/check/routine on top of the HF target."""
    before, after = previous['inventory'], target['inventory']
    from truss._migration_verify import matches_inventory
    stable_categories = set(before) - {'columns', 'constraints', 'routines'}
    profile = {'inventory': {name: before[name] for name in stable_categories},
               'initializationAlternatives': previous.get('initializationAlternatives', [])}
    observed = {name: after[name] for name in stable_categories}
    if not matches_inventory(observed, profile):
        raise ValueError('Unreviewed managed-target native delta outside qualified initialization alternatives')
    old_columns = before['columns']
    new_columns = after['columns']
    if len(new_columns) != len(old_columns) + 1:
        raise ValueError('Exactly one final source column must be appended in native order')
    old_column_set = {canonical(row) for row in old_columns}
    new_column_set = {canonical(row) for row in new_columns}
    added_columns = new_column_set - old_column_set
    if len(added_columns) != 1 or old_column_set - new_column_set:
        raise ValueError('Target columns must preserve every predecessor column and add one')
    column = json.loads(next(iter(added_columns)))
    if column[0] != 'catalog_runtime_installation' or column[2] != MANAGED_COLUMN:
        raise ValueError('The one new final column must be catalog_runtime_installation.managed_grants')
    if column[3] != 'jsonb' or column[4] is not True or column[7] is not False:
        raise ValueError('Managed grants must be non-null native jsonb and not dropped')
    if not column[14] or 'truss-managed-grants/0.1' not in column[14]:
        raise ValueError('Managed grants must have the exact strict-policy source default')
    old_attnums = [row[1] for row in old_columns if row[0] == 'catalog_runtime_installation' and not row[7]]
    if not old_attnums or column[1] != max(old_attnums) + 1:
        raise ValueError('Managed grants must occupy the next source attribute number')
    old_constraints, new_constraints = before['constraints'], after['constraints']
    old_constraint_set = {canonical(row) for row in old_constraints}
    new_constraint_set = {canonical(row) for row in new_constraints}
    added_constraints = new_constraint_set - old_constraint_set
    if len(new_constraints) != len(old_constraints) + 2 or len(added_constraints) != 2 or old_constraint_set - new_constraint_set:
        raise ValueError('Managed grants must add exactly its CHECK and native NOT NULL constraints')
    constraints = [json.loads(row) for row in added_constraints]
    checks = [row for row in constraints if row[2] == 'c']
    not_null = [row for row in constraints if row[2] == 'n']
    if len(checks) != 1 or len(not_null) != 1:
        raise ValueError('Managed grants must have one strict CHECK and one native NOT NULL constraint')
    constraint = checks[0]
    if (constraint[0] != 'catalog_runtime_installation'
            or MANAGED_COLUMN not in constraint[6] or 'truss-managed-grants/0.1' not in constraint[6]):
        raise ValueError('New managed-grants constraint must be a table CHECK')
    if not_null[0][0] != 'catalog_runtime_installation' or MANAGED_COLUMN not in not_null[0][6]:
        raise ValueError('New native NOT NULL constraint must protect managed_grants')
    old_routines, new_routines = _routine_map(previous), _routine_map(target)
    if set(old_routines) != set(new_routines):
        raise ValueError('Managed target may not add or remove routine identities')
    changed = {identity for identity in new_routines if new_routines[identity] != old_routines[identity]}
    if changed != {('runtime_current_installation', '')}:
        raise ValueError(f'Expected only the managed current-installation routine change: {sorted(changed)}')
    previous_exact_acl = previous['acl'] if previous.get('aclNameProfile') == 'truss-native-acl-names/0.2' else previous.get('exactAcl', previous['acl'])
    current_exact_acl = target.get('exactAcl', target['acl'])
    if previous_exact_acl != current_exact_acl:
        raise ValueError('Managed target unexpectedly changes native ACL profiles')
    if previous['configuration'] != target['configuration']:
        raise ValueError('Managed grants must preserve the metadata-owner configuration')
    policy = target.get('managedGrants')
    if policy != {'interfaceVersion': 'truss-managed-grants/0.1', 'roles': [], 'observations': []}:
        raise ValueError('Fresh target conversion must install the empty strict managed-grants policy')


def _statements_from_target(target: dict, retained_hf_edge: dict, managed_sql: str):
    # The recipe is the already-reviewed HF source47 edge followed by the
    # single source-ordered managed fragment. The final routine body must
    # correspond exactly to the fragment and target native capture.
    hf_steps = retained_hf_edge['steps']
    if not hf_steps or any(not isinstance(step, str) or not step for step in hf_steps):
        raise ValueError('Retained HF recipe statements are required')
    if 'ADD COLUMN managed_grants jsonb' not in managed_sql or 'CREATE OR REPLACE FUNCTION truss.runtime_current_installation()' not in managed_sql:
        raise ValueError('Managed fragment must add the source column and replace the central routine')
    routine = _routine_map(target).get(('runtime_current_installation', ''))
    if not routine or 'managed_grants' not in routine:
        raise ValueError('Captured final routine does not contain managed grants behavior')
    return [*hf_steps, managed_sql.strip()]


def _timezone_rule(left: dict, right: dict):
    """Return the one already-qualified New York/UTC horizon-bound variant."""
    if left['initializationTimeZone'] == right['initializationTimeZone']:
        raise ValueError('Initializer captures must use different timezone profiles')
    rules = []
    for label in ('source', 'target'):
        before, after = left[label]['inventory'], right[label]['inventory']
        if set(before) != set(after):
            raise ValueError(f'Initializer native inventory categories differ for {label}')
        changed = []
        for category in before:
            old_rows, new_rows = before[category], after[category]
            if old_rows == new_rows:
                continue
            if category != 'relations' or len(old_rows) != len(new_rows):
                raise ValueError(f'Unreviewed initializer difference in {label}/{category}')
            left_by_key = {(row[0], row[1]): row for row in old_rows}
            right_by_key = {(row[0], row[1]): row for row in new_rows}
            if left_by_key.keys() != right_by_key.keys():
                raise ValueError(f'Initializer relation membership changed for {label}')
            for identity, first in left_by_key.items():
                second = right_by_key[identity]
                if first == second:
                    continue
                if identity != ('journal_runtime_horizon', 'r') or first[:7] + first[8:] != second[:7] + second[8:]:
                    raise ValueError(f'Unreviewed native partition bound change for {label}/{identity}')
                changed.append({'surface': 'relations', 'identity': ['journal_runtime_horizon'],
                                'rows': sorted([first, second], key=canonical)})
        if len(changed) != 1:
            raise ValueError(f'Expected one journal-horizon initializer variant for {label}')
        rules.append(changed[0])
    if rules[0] != rules[1]:
        raise ValueError('Source and target initializers must retain the same exact horizon variants')
    return rules[0]


def _package_artifacts(source: dict, target: dict, initializer_rule: dict, target_digest: str,
                       source_wheel: Path, retained_edge: dict, managed_sql: str):
    """Update only current migration manifest plus new target/edge artifacts."""
    pinned = read_json(MIGRATIONS / 'manifest.json')
    previous_target = read_json(MIGRATIONS / f'{OLD_HF_TARGET}.json')
    _validate_managed_delta(previous_target, target)
    if source['sha256'] != SOURCE47:
        raise ValueError('Captured source must be the exact published v0.0.47 runtime')
    archived_source = read_json(MIGRATIONS / f'{SOURCE47}.json')
    # Preserve original published profile bytes and require the independent
    # source fixture to observe the same definitions and ordinary ACLs.
    from truss._migration_verify import matches_inventory
    if not matches_inventory(source['inventory'], archived_source) or source['acl'] != archived_source['acl']:
        raise ValueError('Fresh source47 observation differs from immutable published profile')
    exact_source_name = pinned.get('exactAclProfiles', {}).get(SOURCE47)
    if not exact_source_name or source['exactAcl'] != read_json(MIGRATIONS / exact_source_name)['acl']:
        raise ValueError('Fresh source47 exact ACLs differ from immutable published evidence')
    _validate_managed_delta(previous_target, target)
    if target['sha256'] != target_digest:
        raise ValueError('Frozen target digest differs from the native target capture')
    prior_init = read_json(MIGRATIONS / pinned['initializationProfiles'])
    if initializer_rule not in prior_init['rules']:
        raise ValueError('Managed target initializer is outside the previously qualified NY/UTC profile')

    target_profile = dict(target)
    exact_acl = target_profile.pop('exactAcl')
    target_profile.pop('aclNameProfile', None)
    target_profile['definitionAlternatives'] = previous_target.get('definitionAlternatives', [])
    target_profile['initializationAlternatives'] = [initializer_rule]
    exact_name = f'{target_digest}.acl.json'
    exact_profile = {'acl': exact_acl,
                     'aclNameProfile': 'truss-native-acl-names/0.2',
                     'runtimeManifestSha256': target_digest}
    edge_name = f'edge-{SOURCE47}-{target_digest}.json'
    recipe = {
        'source': SOURCE47,
        'target': target_digest,
        'steps': _statements_from_target(target, retained_edge, managed_sql),
        'ownership': retained_edge['ownership'],
        'moduleGrants': retained_edge['moduleGrants'],
    }

    manifest = dict(pinned)
    manifest['target'] = target_digest
    manifest['targetRelease'] = target['manifest']['releaseId']
    manifest['edges'] = [edge for edge in pinned['edges']
                         if not (edge['source'] == SOURCE47 and edge['target'] == OLD_HF_TARGET)]
    manifest['edges'].append({'source': SOURCE47, 'target': target_digest,
                              'direction': 'forward', 'artifact': edge_name})
    exact_profiles = dict(pinned.get('exactAclProfiles', {}))
    exact_profiles[target_digest] = exact_name
    manifest['exactAclProfiles'] = exact_profiles
    immutable = list(pinned['immutableFiles'])
    for name in (f'{target_digest}.json', exact_name, edge_name):
        if name not in immutable:
            immutable.append(name)
    manifest['immutableFiles'] = immutable

    # Keep all old profile/recipe bytes, including the unpublished HF candidate,
    # as historical artifacts. Only the active graph edge and target change.
    generated = {
        f'{target_digest}.json': canonical(target_profile) + b'\n',
        exact_name: canonical(exact_profile) + b'\n',
        edge_name: canonical(recipe) + b'\n',
    }
    all_bytes = {}
    for name in pinned['files']:
        if name in generated:
            raise ValueError('New target filename collides with historical artifact: ' + name)
        all_bytes[name] = (MIGRATIONS / name).read_bytes()
    all_bytes.update(generated)
    manifest['files'] = {name: digest(raw) for name, raw in sorted(all_bytes.items())}
    manifest['sourceWheels']['source47'] = {
        **manifest['sourceWheels']['source47'],
        'sha256': digest(source_wheel.read_bytes()),
        'runtimeManifestSha256': SOURCE47,
        'tag': 'v0.0.47',
    }
    return manifest, generated


def main():
    sys.path.insert(0, str(ROOT / 'packages/python/src'))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source47-wheel', type=Path, required=True)
    parser.add_argument('--expected-target-manifest-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True,
                        help='Capture directory; use the same directory in both timezone runs')
    parser.add_argument('--initialization-time-zone', choices=('America/New_York', 'UTC'))
    parser.add_argument('--peer', type=Path,
                        help='Other timezone capture directory; required for final --package')
    parser.add_argument('--package', action='store_true',
                        help='After both independent captures, generate current target and edge artifacts')
    parser.add_argument('--check-only', action='store_true',
                        help='Validate inputs and captures without writing package artifacts')
    parser.add_argument('--finalize-captures', action='store_true',
                        help='Build from the two saved captures in --output/--peer without starting another worker')
    args = parser.parse_args()

    if len(args.expected_target_manifest_sha256) != 64:
        parser.error('Provide the frozen current target manifest SHA-256')
    if not args.finalize_captures and args.initialization_time_zone is None:
        parser.error('--initialization-time-zone is required when capturing')
    if args.finalize_captures and args.initialization_time_zone is not None:
        parser.error('--initialization-time-zone cannot be combined with --finalize-captures')
    if not args.finalize_captures and os.environ.get('TZ') != args.initialization_time_zone:
        os.environ['TZ'] = args.initialization_time_zone
    pinned = read_json(MIGRATIONS / 'manifest.json')
    if SOURCE47 not in pinned['sources'] or f'{OLD_HF_TARGET}.json' not in pinned['files']:
        raise ValueError('Current migration lineage no longer has the reviewed source47/HF artifacts')
    old_edge_name = f'edge-{SOURCE47}-{OLD_HF_TARGET}.json'
    if old_edge_name not in pinned['files']:
        raise ValueError('Retained source47→HF target edge is missing')
    old_edge = read_json(MIGRATIONS / old_edge_name)
    if old_edge.get('source') != SOURCE47 or old_edge.get('target') != OLD_HF_TARGET:
        raise ValueError('Retained HF edge identity mismatch')
    if digest((PACKAGE / '_catalog_runtime/manifest.json').read_bytes()) != args.expected_target_manifest_sha256:
        raise ValueError('Current target source digest differs from the freeze input')
    if digest((PACKAGE / '_catalog_runtime/manifest.json').read_bytes()) == SOURCE47:
        raise ValueError('Current target still equals the published source47 cohort')
    manifest_raw = (PACKAGE / '_catalog_runtime/manifest.json').read_bytes()
    target_digest = digest(manifest_raw)
    if not args.output.exists():
        args.output.mkdir(parents=True)

    # This is intentionally a local version check. Publication changes are
    # checked again by the release workflow before packaging.
    tags = subprocess.run(['git', 'tag', '--list', 'v0.0.48'], cwd=ROOT,
                          text=True, capture_output=True, check=True).stdout.splitlines()
    if tags:
        raise ValueError('v0.0.48 is published/tagged; revalidate the MG-4 lineage before regeneration')

    if args.package and args.peer is None:
        if not args.finalize_captures:
            parser.error('--package requires the independent other-timezone --peer capture')

    if args.finalize_captures:
        if not args.peer:
            parser.error('--finalize-captures requires --peer pointing to the other capture directory')
        ny = read_json(args.output / 'America_New_York.json')
        utc = read_json(args.peer / 'UTC.json')
        if ny['initializationTimeZone'] != 'America/New_York' or utc['initializationTimeZone'] != 'UTC':
            raise ValueError('Saved capture files do not match the approved initializer timezones')
        if ny['sourceWheelSha256'] != digest(args.source47_wheel.read_bytes()) or utc['sourceWheelSha256'] != digest(args.source47_wheel.read_bytes()):
            raise ValueError('Saved captures were not produced from the exact supplied source47 wheel')
        if ny['targetManifestSha256'] != target_digest or utc['targetManifestSha256'] != target_digest:
            raise ValueError('Saved captures do not match the current frozen runtime manifest')
        source, target = ny['source'], ny['target']
        peer = utc
        capture = ny
    else:
        # Source47 bytes are copied only into a temporary extraction directory.
        with tempfile.TemporaryDirectory(prefix='truss-managed-grants-migration-') as temporary:
            run_dir = Path(temporary)
            source_root = run_dir / 'source47'
            source_root.mkdir()
            _source47_package(args.source47_wheel, source_root, pinned)
            model_path = run_dir / 'model.json'
            sys.path.insert(0, str(ROOT / 'packages/python/tests'))
            from test_catalog_relational_support import relational_document
            document = relational_document()
            document['id'] = 'adoc'
            model_path.write_text(json.dumps(document, sort_keys=True) + '\n')

            from native_fixture import DatabaseFixture, WorkerCluster
            with WorkerCluster() as worker:
                worker_root = worker.root
                fixture = None
                try:
                    fixture = DatabaseFixture(worker_root)
                    source_uri = fixture.get_uri()
                    source = _capture('source47', source_root, source_uri, model_path, run_dir)
                    fixture.cleanup()
                    fixture = None
                    worker.verify_clean()

                    fixture = DatabaseFixture(worker_root)
                    target_uri = fixture.get_uri()
                    target = _capture('target', ROOT / 'packages/python/src', target_uri, model_path, run_dir)
                    fixture.cleanup()
                    fixture = None
                    worker.verify_clean()
                finally:
                    if fixture is not None:
                        fixture.cleanup()

        if target['sha256'] != target_digest:
            raise AssertionError('Target fixture captured another runtime manifest')
        capture = {
            'interfaceVersion': 'truss-managed-grants-capture/0.1',
            'initializationTimeZone': args.initialization_time_zone,
            'source': source,
            'target': target,
            'sourceWheelSha256': digest(args.source47_wheel.read_bytes()),
            'targetManifestSha256': target_digest,
        }
        capture_path = args.output / (args.initialization_time_zone.replace('/', '_') + '.json')
        capture_path.write_bytes(canonical(capture) + b'\n')
        print(json.dumps({'capture': str(capture_path), 'target': target_digest,
                          'timezone': args.initialization_time_zone}, indent=2))

    if not args.finalize_captures and args.peer is None:
        return
    if not args.finalize_captures:
        peer_path = args.peer / ('UTC.json' if args.initialization_time_zone == 'America/New_York'
                                else 'America_New_York.json')
        peer = read_json(peer_path)
    if peer['initializationTimeZone'] == capture['initializationTimeZone']:
        raise ValueError('Peer must be the other approved initializer timezone')
    peer_source, peer_target = peer['source'], peer['target']
    if source['sha256'] != peer_source['sha256'] or target['sha256'] != peer_target['sha256']:
        raise ValueError('Independent initializer captures must use identical source/target manifests')
    if source['inventory']['columns'] != peer_source['inventory']['columns']:
        raise ValueError('Source column fingerprint changed across initializer captures')
    if target['inventory']['columns'] != peer_target['inventory']['columns']:
        raise ValueError('Target column fingerprint changed across initializer captures')

    previous_target = read_json(MIGRATIONS / f'{OLD_HF_TARGET}.json')
    _validate_managed_delta(previous_target, target)
    managed_sql = (PACKAGE / '_catalog_runtime/managed-grants.sql').read_text()
    steps = _statements_from_target(target, old_edge, managed_sql)
    if args.check_only:
        print('Source47→combined target recipe inputs are structurally consistent; no package artifacts written.')
        return
    initializer_rule = _timezone_rule(peer, capture)
    manifest, generated = _package_artifacts(source, target, initializer_rule, target_digest,
                                               args.source47_wheel, old_edge, managed_sql)
    manifest_bytes = canonical(manifest) + b'\n'
    if args.package:
        for name, raw in generated.items():
            (MIGRATIONS / name).write_bytes(raw)
        (MIGRATIONS / 'manifest.json').write_bytes(manifest_bytes)
    else:
        package_dir = args.output / 'package'
        package_dir.mkdir(exist_ok=True)
        for name, raw in generated.items():
            (package_dir / name).write_bytes(raw)
        (package_dir / 'manifest.json').write_bytes(manifest_bytes)
    print(json.dumps({'target': target_digest,
                      'edge': f'edge-{SOURCE47}-{target_digest}.json',
                      'writtenTo': str(MIGRATIONS if args.package else package_dir)}, indent=2))


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT / 'scripts'))
    main()
