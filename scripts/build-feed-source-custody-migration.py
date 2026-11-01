#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Capture and package the native-qualified 0.74 → 0.75 custody edge.

Capture separately under America/New_York and UTC. Run the source-only
``--finalize-captures --check-only`` path and obtain Sol review before using
``--package``. Native capture/packaging is intentionally not run by this
generator's source tests.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'packages/python/src/truss'
MIGRATIONS = PACKAGE / '_migrations'
SOURCE = '288801f7177338328441b5d3ce9328af31740ebf513f04ea45e30ae316a9f3a4'
TARGET_RELEASE = 'truss-catalog-runtime/0.75-candidate'
NEW_ROUTINES = {
    'runtime_feed_custody_assert_mutable',
    'runtime_feed_custody_prune_stale',
    'runtime_feed_custody_consumer_guard',
    'runtime_feed_custody_truncate_guard',
    'open_feed_source_custody',
    'renew_feed_source_custody',
    'acknowledge_feed_under_source_custody',
    'reconcile_feed_ack_under_source_custody',
    'close_feed_source_custody',
}
CHANGED_ROUTINES = {
    ('acknowledge_feed', 'selected_consumer text, expected_prior bytea, target bytea, payload_sha256 text, expected_release text, expected_digest text'),
    ('acknowledge_feed_with_receipt', 'selected_consumer text, prior bytea, target bytea, feed_sha text, destination text, request_sha text, publication text, receipt bytea, expected_release text, expected_digest text'),
    ('catalog_accept_with_keys', 'input_bytes bytea, documents_bytes bytea, declarations_bytes bytea, source_bytes bytea, origin_bytes bytea, request_key text, key_receipts bytea, preview_mode boolean, expected_revision integer, expected_documents bytea'),
    ('get_object', 'selected_document text, selected_module text, selected_record text, selected_id bigint, maximum_bytes integer, expected_release text, expected_digest text'),
    ('query_scope', 'binding jsonb'),
}
NEW_TRIGGERS = {
    ('runtime_feed_consumer', 'runtime_feed_source_custody_guard'),
    ('runtime_feed_consumer', 'runtime_feed_source_custody_consumer_truncate'),
    ('runtime_feed_ack_receipt', 'runtime_feed_source_custody_receipt_truncate'),
}
NEW_CUSTODY_COLUMNS = {
    'custody_id', 'backend_pid', 'backend_start', 'opened_xid', 'consumer_id',
    'registration_id', 'installation_id', 'source_epoch', 'release_id',
    'release_sha256', 'prior_bytes', 'target_bytes', 'feed_sha256',
    'payload_bytes', 'maximum_facts', 'maximum_bytes', 'request_bytes',
    'destination_registration_bytes', 'ack_scope_bytes', 'destination_id',
    'request_sha256', 'publication_id', 'internal_token',
    'internal_token_sha256', 'phase', 'ack_xid', 'ack_receipt_bytes',
}
NEW_CUSTODY_CONSTRAINTS = {
    'runtime_feed_source_custody_ack_scope_bytes_check',
    'runtime_feed_source_custody_ack_scope_bytes_not_null',
    'runtime_feed_source_custody_backend_pid_not_null',
    'runtime_feed_source_custody_backend_start_not_null',
    'runtime_feed_source_custody_consumer_id_key',
    'runtime_feed_source_custody_consumer_id_not_null',
    'runtime_feed_source_custody_custody_id_not_null',
    'runtime_feed_source_custody_destination_id_not_null',
    'runtime_feed_source_custody_destination_registration_b_not_null',
    'runtime_feed_source_custody_destination_registration_byte_check',
    'runtime_feed_source_custody_feed_sha256_check',
    'runtime_feed_source_custody_feed_sha256_not_null',
    'runtime_feed_source_custody_installation_id_not_null',
    'runtime_feed_source_custody_internal_token_check',
    'runtime_feed_source_custody_internal_token_not_null',
    'runtime_feed_source_custody_internal_token_sha256_check',
    'runtime_feed_source_custody_internal_token_sha256_not_null',
    'runtime_feed_source_custody_maximum_bytes_check',
    'runtime_feed_source_custody_maximum_bytes_not_null',
    'runtime_feed_source_custody_maximum_facts_check',
    'runtime_feed_source_custody_maximum_facts_not_null',
    'runtime_feed_source_custody_opened_xid_not_null',
    'runtime_feed_source_custody_payload_bytes_check',
    'runtime_feed_source_custody_payload_bytes_not_null',
    'runtime_feed_source_custody_phase_check',
    'runtime_feed_source_custody_phase_not_null',
    'runtime_feed_source_custody_pkey',
    'runtime_feed_source_custody_prior_bytes_check',
    'runtime_feed_source_custody_prior_bytes_not_null',
    'runtime_feed_source_custody_publication_id_not_null',
    'runtime_feed_source_custody_registration_id_not_null',
    'runtime_feed_source_custody_release_id_not_null',
    'runtime_feed_source_custody_release_sha256_check',
    'runtime_feed_source_custody_release_sha256_not_null',
    'runtime_feed_source_custody_request_bytes_check',
    'runtime_feed_source_custody_request_bytes_not_null',
    'runtime_feed_source_custody_request_sha256_not_null',
    'runtime_feed_source_custody_source_epoch_not_null',
    'runtime_feed_source_custody_target_bytes_check',
    'runtime_feed_source_custody_target_bytes_not_null',
}
NEW_CUSTODY_INDEXES = {
    'runtime_feed_source_custody_consumer_id_key',
    'runtime_feed_source_custody_pkey',
}
FEED_GRANTS = [
    'open_feed_source_custody(text,bytea,bytea,text,bytea,integer,integer,bytea,bytea,bytea,text,text,text,text,text)',
    'renew_feed_source_custody(uuid,bytea,bytea,bytea,text,text,text)',
    'acknowledge_feed_under_source_custody(uuid,bytea,bytea,bytea,text,bytea,bytea,text,text,text,text,bytea,text,text)',
    'reconcile_feed_ack_under_source_custody(uuid,bytea,bytea,bytea,text,bytea,bytea,text,text,text,text,bytea,text,text)',
    'close_feed_source_custody(uuid,bytea,bytea,bytea,boolean,text,text)',
]
CUSTODY_CHANGED_SOURCES = {
    'feed.sql', 'feed-receipts.sql', 'runtime.sql', 'read.sql', 'query.sql',
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_bytes())


def routine_map(profile):
    return {(row[0], row[1]): row[2] for row in profile['inventory']['routines']}


def _pinned_artifacts(manifest):
    for name, expected in manifest['files'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or path.name != name:
            raise ValueError('Unsafe migration artifact path: ' + name)
        if digest((MIGRATIONS / name).read_bytes()) != expected:
            raise ValueError('Pinned migration artifact changed: ' + name)
    if len(manifest['immutableFiles']) != len(set(manifest['immutableFiles'])):
        raise ValueError('Duplicate immutable migration artifacts')
    if any(name not in manifest['files'] for name in manifest['immutableFiles']):
        raise ValueError('Unpinned immutable migration artifact')


def _validate_inventory(source, target):
    from truss._migration_verify import matches_inventory

    before, after = source['inventory'], target['inventory']
    if before.keys() != after.keys():
        raise ValueError('Native inventory categories changed')
    old_routines, new_routines = routine_map(source), routine_map(target)
    old_by_name = {key[0] for key in old_routines}
    new_by_name = {key[0] for key in new_routines}
    if old_by_name - new_by_name:
        raise ValueError('Custody target removes a predecessor routine')
    additions = set(new_routines) - set(old_routines)
    if {name for name, _arguments in additions} != NEW_ROUTINES or len(additions) != len(NEW_ROUTINES):
        raise ValueError(f'Unexpected custody routine identities: {sorted(additions)}')
    changed = {key for key in old_routines if old_routines[key] != new_routines[key]}
    if changed != CHANGED_ROUTINES:
        raise ValueError(f'Unexpected existing routine changes: {sorted(changed)}')

    old_tables = {row[0] for row in before['relations'] if row[1] in ('r', 'p')}
    new_tables = {row[0] for row in after['relations'] if row[1] in ('r', 'p')}
    if new_tables - old_tables != {'runtime_feed_source_custody'} or old_tables - new_tables:
        raise ValueError('Custody target must add exactly its private table')
    custody_columns = {row[2] for row in after['columns'] if row[0] == 'runtime_feed_source_custody'}
    custody_constraints = {row[1] for row in after['constraints'] if row[0] == 'runtime_feed_source_custody'}
    custody_indexes = {row[0] for row in after['indexes'] if row[0].startswith('runtime_feed_source_custody')}
    custody_relations = {row[0] for row in after['relations'] if row[0].startswith('runtime_feed_source_custody')}
    if custody_columns != NEW_CUSTODY_COLUMNS or custody_constraints != NEW_CUSTODY_CONSTRAINTS \
            or custody_indexes != NEW_CUSTODY_INDEXES \
            or custody_relations != NEW_CUSTODY_INDEXES | {'runtime_feed_source_custody'}:
        raise ValueError('Private custody table native shape differs from the exact reviewed schema')
    old_triggers = {(row[0], row[1]) for row in before['triggers']}
    new_triggers = {(row[0], row[1]) for row in after['triggers']}
    if new_triggers - old_triggers != NEW_TRIGGERS or old_triggers - new_triggers:
        raise ValueError('Custody target trigger delta is not the reviewed guard set')

    filtered = copy.deepcopy(after)
    filtered['columns'] = [row for row in filtered['columns']
                           if row[0] != 'runtime_feed_source_custody'
                           and row[0] not in NEW_CUSTODY_INDEXES]
    filtered['constraints'] = [row for row in filtered['constraints']
                               if row[0] != 'runtime_feed_source_custody']
    filtered['indexes'] = [row for row in filtered['indexes']
                           if row[0] not in NEW_CUSTODY_INDEXES]
    filtered['relations'] = [row for row in filtered['relations']
                             if row[0] not in NEW_CUSTODY_INDEXES | {'runtime_feed_source_custody'}]
    filtered['triggers'] = [row for row in filtered['triggers']
                            if (row[0], row[1]) not in NEW_TRIGGERS]
    filtered['routines'] = [row for row in filtered['routines']
                            if row[0] not in NEW_ROUTINES]
    for row in filtered['routines']:
        key = (row[0], row[1])
        if key in CHANGED_ROUTINES:
            row[2] = old_routines[key]
    old_horizon = next(row for row in before['relations'] if row[0] == 'journal_runtime_horizon')
    filtered['relations'] = [old_horizon if row[0] == 'journal_runtime_horizon' else row
                             for row in filtered['relations']]
    if not matches_inventory(filtered, source):
        raise ValueError('Custody target changes native inventory outside the reviewed delta')


def _validate_runtime_manifest(source, target):
    old, new = source['manifest'], target['manifest']
    if new.get('releaseId') != TARGET_RELEASE:
        raise ValueError('Expected exact 0.75 candidate runtime release identity')
    old_files, new_files = old['files'], new['files']
    expected_names = set(old_files) | {'feed-custody.sql'}
    if set(new_files) != expected_names:
        raise ValueError('0.75 must append only the feed-custody source file')
    for name, old_hash in old_files.items():
        if name not in CUSTODY_CHANGED_SOURCES and new_files[name] != old_hash:
            raise ValueError('Unexpected runtime source change: ' + name)
    if new['version'] != '0.75' or new['layoutProfile'] != old['layoutProfile']:
        raise ValueError('Custody release changes unsupported runtime metadata')


def _target_initialization_rule(source, target_ny, target_utc):
    pinned = read_json(MIGRATIONS / 'manifest.json')
    evidence = read_json(MIGRATIONS / pinned['initializationProfiles'])
    source_rules = source.get('initializationAlternatives', [])
    horizon = [rule for rule in source_rules
               if rule['surface'] == 'relations' and rule['identity'] == ['journal_runtime_horizon']]
    if len(horizon) != 1:
        raise ValueError('One exact source journal horizon initialization rule is required')
    if horizon[0] not in evidence['rules']:
        raise ValueError('Source horizon variants lack pinned initialization evidence')
    def horizon_row(profile):
        rows = [row for row in profile['inventory']['relations'] if row[0] == 'journal_runtime_horizon']
        if len(rows) != 1:
            raise ValueError('One journal runtime horizon relation is required')
        return rows[0]

    ny_row, utc_row = horizon_row(target_ny), horizon_row(target_utc)
    ny_inventory = copy.deepcopy(target_ny['inventory'])
    utc_inventory = copy.deepcopy(target_utc['inventory'])
    ny_inventory['relations'] = [row for row in ny_inventory['relations'] if row[0] != 'journal_runtime_horizon']
    utc_inventory['relations'] = [row for row in utc_inventory['relations'] if row[0] != 'journal_runtime_horizon']
    if ny_inventory != utc_inventory:
        raise ValueError('Timezone captures differ outside the journal horizon relation')
    variants = []
    for row in [*horizon[0]['rows'], ny_row, utc_row]:
        if row not in variants:
            variants.append(row)
    return {'identity': ['journal_runtime_horizon'], 'surface': 'relations', 'rows': variants}


def _extended_initialization_evidence(pinned, target_digest, target_ny, target_utc, rule):
    evidence = copy.deepcopy(read_json(MIGRATIONS / pinned['initializationProfiles']))
    if rule not in evidence['rules']:
        evidence['rules'].append(rule)
    captures = {capture['initializationTimeZone']: capture for capture in evidence['captures']}
    for timezone, target in (('America/New_York', target_ny), ('UTC', target_utc)):
        capture = captures.get(timezone)
        if capture is None:
            raise ValueError('Pinned initialization evidence lacks a required timezone capture')
        capture['inventories'][target_digest] = digest(canonical(target['inventory']))
    raw = canonical(evidence) + b'\n'
    name = f'native-initialization-profiles-{digest(raw)[:16]}.json'
    return name, raw


def _validate_acl(source, target, source_exact_acl):
    old_acl, new_acl = source['acl'], target['acl']
    if old_acl.keys() != new_acl.keys():
        raise ValueError('Native ACL role profile changed')
    for role, entries in old_acl.items():
        if not set(map(canonical, entries)) <= set(map(canonical, new_acl[role])):
            raise ValueError('Custody candidate removes a predecessor privilege')
    old_objects = {(entry[0], entry[1]) for values in old_acl.values() for entry in values}
    new_objects = {(entry[0], entry[1]) for values in new_acl.values() for entry in values}
    allowed_names = NEW_ROUTINES | {
        'runtime_feed_source_custody', '_runtime_feed_source_custody',
    }
    additions = new_objects - old_objects
    if any(name.split('(')[0] not in allowed_names for _kind, name in additions):
        raise ValueError('Custody candidate adds an unreviewed ACL object')
    additions_by_role = {
        role: set(map(canonical, new_acl[role])) - set(map(canonical, old_acl[role]))
        for role in old_acl
    }
    allowed_public = {
        canonical(['type', '_runtime_feed_source_custody', 'USAGE', False]),
    }
    if any(additions_by_role[role] for role in old_acl if role not in ('owner', 'feed', 'public')):
        raise ValueError('Custody target adds privileges outside owner/feed profiles')
    if additions_by_role['public'] - allowed_public:
        raise ValueError('PUBLIC receives an unreviewed custody privilege')
    if any(json.loads(row)[1].split('(')[0] not in allowed_names
           for row in additions_by_role['owner']):
        raise ValueError('Custody target widens owner grants on a predecessor object')
    if any(json.loads(row)[0] != 'routine'
           for row in additions_by_role['feed']):
        raise ValueError('Feed role receives a non-routine custody privilege')
    feed_object_names = {json.loads(row)[1].split('(')[0]
                         for row in additions_by_role['feed']}
    if feed_object_names != {signature.split('(')[0] for signature in FEED_GRANTS} \
            or len(additions_by_role['feed']) != len(FEED_GRANTS):
        raise ValueError('Feed ACL object delta differs from the five custody routines')
    old_exact = {canonical(row) for row in source_exact_acl['feed']}
    new_exact = {canonical(row) for row in target['exactAcl']['feed']}
    added_exact = [json.loads(row.decode()) for row in new_exact - old_exact]
    normalize = lambda signature: (signature.split('(')[0],
                                   ''.join(signature[signature.find('(') + 1:-1].split()))
    actual = {(normalize(row[1]), row[2], row[3]) for row in added_exact}
    expected = {(normalize(signature), 'EXECUTE', False) for signature in FEED_GRANTS}
    if actual != expected:
        raise ValueError('Feed role must receive exactly the five handle routine grants')
    if any(json.loads(row)[0] == 'schema' for row in additions_by_role['public']):
        raise ValueError('Custody target unexpectedly widens public schema privileges')


def _validate_pair(ny, utc, target_digest):
    from truss._migration_verify import matches_inventory

    pinned = read_json(MIGRATIONS / 'manifest.json')
    if pinned['target'] != SOURCE:
        raise ValueError('The additive edge must start at the current 0.74 target')
    source = read_json(MIGRATIONS / f'{SOURCE}.json')
    exact_name = pinned.get('exactAclProfiles', {}).get(SOURCE)
    if not exact_name:
        raise ValueError('Current 0.74 exact ACL profile is required')
    exact = read_json(MIGRATIONS / exact_name)
    if (exact.get('runtimeManifestSha256') != SOURCE
            or exact.get('aclNameProfile') != 'truss-native-acl-names/0.2'):
        raise ValueError('Current source exact ACL identity failed')

    if ny.get('initializationTimeZone') != 'America/New_York' or utc.get('initializationTimeZone') != 'UTC':
        raise ValueError('Independent New York and UTC target captures are required')
    if ny.get('targetManifestSha256') != target_digest or utc.get('targetManifestSha256') != target_digest:
        raise ValueError('Target captures do not bind the current runtime manifest')
    target_ny, target_utc = ny['target'], utc['target']
    if target_ny['sha256'] != target_digest or target_utc['sha256'] != target_digest:
        raise ValueError('Target capture digest mismatch')
    if target_ny['manifest'] != target_utc['manifest']:
        raise ValueError('Timezone captures observed different target manifests')
    if target_ny['configuration'] != source['configuration'] or target_utc['configuration'] != source['configuration']:
        raise ValueError('Target changes metadata-owner preparation configuration')
    _validate_runtime_manifest(source, target_ny)
    _validate_inventory(source, target_ny)
    _validate_acl(source, target_ny, exact['acl'])
    if target_ny['exactAcl'] != target_utc['exactAcl'] or target_ny['acl'] != target_utc['acl']:
        raise ValueError('Exact native ACL capture differs by initialization timezone')
    initialization_rule = _target_initialization_rule(source, target_ny, target_utc)
    target_profile = copy.deepcopy(target_ny)
    target_profile['definitionAlternatives'] = source.get('definitionAlternatives', [])
    target_profile['initializationAlternatives'] = [initialization_rule]
    if not matches_inventory(target_utc['inventory'], target_profile):
        raise ValueError('UTC target inventory is outside qualified initialization alternatives')

    equivalence = read_json(MIGRATIONS / pinned['definitionEquivalence'])
    if any(rule not in equivalence['rules'] for rule in target_ny.get('definitionAlternatives', [])):
        raise ValueError('Target restore deparse differences need independent qualification')
    initialization = read_json(MIGRATIONS / pinned['initializationProfiles'])
    if any(rule not in initialization['rules'] for rule in source.get('initializationAlternatives', [])):
        raise ValueError('Source initialization variant no longer has pinned native evidence')
    return source, target_ny, target_utc, initialization_rule


def _ownership_statements():
    signatures = {
        'runtime_feed_custody_assert_mutable(text)',
        'runtime_feed_custody_prune_stale()',
        'runtime_feed_custody_consumer_guard()',
        'runtime_feed_custody_truncate_guard()',
        FEED_GRANTS[0], FEED_GRANTS[1], FEED_GRANTS[2], FEED_GRANTS[3], FEED_GRANTS[4],
    }
    statements = ['ALTER TABLE truss.runtime_feed_source_custody OWNER TO {}',
                  'REVOKE ALL ON TABLE truss.runtime_feed_source_custody FROM PUBLIC']
    for signature in sorted(signatures):
        statements.extend((f'ALTER FUNCTION truss.{signature} OWNER TO {{}}',
                           f'REVOKE ALL ON FUNCTION truss.{signature} FROM PUBLIC'))
    return statements


def _package(source, target, target_digest, target_utc=None, initialization_rule=None):
    pinned = read_json(MIGRATIONS / 'manifest.json')
    target_utc = target if target_utc is None else target_utc
    initialization_rule = initialization_rule or _target_initialization_rule(source, target, target_utc)
    old_manifest_raw = (MIGRATIONS / 'manifest.json').read_bytes()
    _pinned_artifacts(pinned)
    if pinned['target'] != SOURCE or digest((PACKAGE / '_catalog_runtime/manifest.json').read_bytes()) != target_digest:
        raise ValueError('Source or current target manifest pin changed')
    if target['sha256'] != target_digest:
        raise ValueError('Captured target differs from current candidate digest')
    if routine_map(source).keys() == routine_map(target).keys():
        raise ValueError('Expected newly added custody routine identities')

    source_routines = routine_map(source)
    changed = []
    for key, definition in routine_map(target).items():
        if key in CHANGED_ROUTINES and source_routines.get(key) != definition:
            changed.append(definition)
    changed_keys = {key for key, definition in routine_map(target).items()
                    if key in CHANGED_ROUTINES and source_routines.get(key) != definition}
    if changed_keys != CHANGED_ROUTINES:
        raise ValueError('Exact reviewed existing routine identity delta required')

    sql_path = PACKAGE / '_catalog_runtime/feed-custody.sql'
    if target['manifest']['files'].get('feed-custody.sql') != digest(sql_path.read_bytes()):
        raise ValueError('Target manifest does not pin exact custody SQL source')
    source_sql = sql_path.read_text().strip()
    steps = [source_sql, *changed]
    recipe = {'source': SOURCE, 'target': target_digest, 'steps': steps,
              'ownership': _ownership_statements(), 'moduleGrants': [],
              'feedGrants': FEED_GRANTS}

    target_profile = copy.deepcopy(target)
    exact_acl = target_profile.pop('exactAcl')
    target_profile.pop('aclNameProfile', None)
    target_profile['definitionAlternatives'] = target.get('definitionAlternatives', [])
    target_profile['initializationAlternatives'] = [initialization_rule]
    source_horizon = next(row for row in source['inventory']['relations']
                          if row[0] == 'journal_runtime_horizon')
    target_profile['inventory']['relations'] = [
        source_horizon if row[0] == 'journal_runtime_horizon' else row
        for row in target_profile['inventory']['relations']]
    exact_acl_profile = {'acl': exact_acl, 'aclNameProfile': 'truss-native-acl-names/0.2',
                         'runtimeManifestSha256': target_digest}
    edge_name = f'edge-{SOURCE}-{target_digest}.json'
    target_name = f'{target_digest}.json'
    acl_name = f'{target_digest}.acl.json'
    archive_name = digest(old_manifest_raw) + '.manifest.json'
    initialization_name, initialization_raw = _extended_initialization_evidence(
        pinned, target_digest, target, target_utc, initialization_rule)
    generated = {edge_name: canonical(recipe) + b'\n',
                 target_name: canonical(target_profile) + b'\n',
                 acl_name: canonical(exact_acl_profile) + b'\n',
                 archive_name: old_manifest_raw,
                 initialization_name: initialization_raw}

    manifest = dict(pinned)
    manifest['target'] = target_digest
    manifest['targetRelease'] = target['manifest']['releaseId']
    manifest['initializationProfiles'] = initialization_name
    manifest['sources'] = list(pinned['sources'])
    if SOURCE not in manifest['sources']:
        manifest['sources'].append(SOURCE)
    manifest['edges'] = [*pinned['edges'],
                         {'source': SOURCE, 'target': target_digest,
                          'direction': 'forward', 'artifact': edge_name}]
    manifest['exactAclProfiles'] = dict(pinned.get('exactAclProfiles', {}))
    manifest['exactAclProfiles'][target_digest] = acl_name
    immutable = list(pinned['immutableFiles'])
    for name in generated:
        if name not in immutable:
            immutable.append(name)
    manifest['immutableFiles'] = immutable
    all_bytes = {name: (MIGRATIONS / name).read_bytes() for name in pinned['files']}
    for name, raw in generated.items():
        if name in all_bytes and all_bytes[name] != raw:
            raise ValueError('Generated migration artifact collides with pinned bytes: ' + name)
        all_bytes[name] = raw
    manifest['files'] = {name: digest(raw) for name, raw in sorted(all_bytes.items())}
    return manifest, generated


def main():
    sys.path.insert(0, str(ROOT / 'packages/python/src'))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-target-manifest-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--initialization-time-zone', choices=('America/New_York', 'UTC'))
    parser.add_argument('--peer', type=Path)
    parser.add_argument('--finalize-captures', action='store_true')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--package', action='store_true')
    args = parser.parse_args()
    if len(args.expected_target_manifest_sha256) != 64:
        parser.error('Exact candidate runtime manifest SHA-256 required')
    if args.finalize_captures == (args.initialization_time_zone is not None):
        parser.error('Use exactly one of --finalize-captures or --initialization-time-zone')
    if not args.finalize_captures and args.initialization_time_zone is None:
        parser.error('A native capture requires --initialization-time-zone')
    if args.finalize_captures and not args.peer:
        parser.error('--finalize-captures requires the independent timezone --peer capture directory')
    if args.package and (not args.finalize_captures or not args.peer):
        parser.error('--package requires both saved timezone captures')
    target_raw = (PACKAGE / '_catalog_runtime/manifest.json').read_bytes()
    target_digest = digest(target_raw)
    if target_digest != args.expected_target_manifest_sha256:
        raise ValueError('Current target runtime manifest differs from the explicit digest')
    pinned = read_json(MIGRATIONS / 'manifest.json')
    _pinned_artifacts(pinned)
    if pinned['target'] != SOURCE:
        raise ValueError('Current migration target is not the exact 0.74 source endpoint')
    args.output.mkdir(parents=True, exist_ok=True)

    if not args.finalize_captures:
        sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'packages/python/tests')]
        from native_fixture import DatabaseFixture, WorkerCluster
        from test_catalog_relational_support import relational_document
        builder_spec = importlib.util.spec_from_file_location(
            'managed_grants_migration_builder', ROOT / 'scripts/build-managed-grants-migration.py')
        builder = importlib.util.module_from_spec(builder_spec)
        builder_spec.loader.exec_module(builder)
        import time
        os.environ['TZ'] = args.initialization_time_zone
        if hasattr(time, 'tzset'):
            time.tzset()
        with WorkerCluster() as worker:
            fixture = DatabaseFixture(worker.root)
            try:
                model = relational_document()
                model['id'] = 'adoc'
                model_path = args.output / 'model.json'
                model_path.write_text(json.dumps(model, sort_keys=True) + '\n')
                target = builder._capture('target', ROOT / 'packages/python/src',
                                          fixture.get_uri(), model_path, args.output)
            finally:
                fixture.cleanup()
                worker.verify_clean()
        capture = {'interfaceVersion': 'truss-feed-source-custody-capture/0.1',
                   'initializationTimeZone': args.initialization_time_zone,
                   'targetManifestSha256': target_digest, 'target': target}
        name = args.initialization_time_zone.replace('/', '_') + '.json'
        (args.output / name).write_bytes(canonical(capture) + b'\n')
        return

    ny = read_json(args.output / 'America_New_York.json')
    utc = read_json(args.peer / 'UTC.json')
    source, target, target_utc, initialization_rule = _validate_pair(ny, utc, target_digest)
    if args.check_only:
        _package(source, target, target_digest, target_utc, initialization_rule)
        print('Source/target inventories, ACLs, captured timezone profiles, and edge are internally consistent; no files written.')
        return
    manifest, generated = _package(source, target, target_digest, target_utc, initialization_rule)
    destination = MIGRATIONS if args.package else args.output / 'package'
    destination.mkdir(parents=True, exist_ok=True)
    for name, raw in generated.items():
        (destination / name).write_bytes(raw)
    (destination / 'manifest.json').write_bytes(canonical(manifest) + b'\n')
    print(json.dumps({'source': SOURCE, 'target': target_digest,
                      'edge': f'edge-{SOURCE}-{target_digest}.json',
                      'files': sorted(generated), 'writtenTo': str(destination)}, indent=2))


if __name__ == '__main__':
    main()
