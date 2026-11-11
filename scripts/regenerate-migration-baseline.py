#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Regenerate packages/python/src/truss/_migrations from a fresh install.

Starts a private PostgreSQL (pgserver, Unix socket), installs the Truss runtime in the
source checkout, observes the installed catalog structure and ACLs, and writes the
baseline profile that `truss-migrate status` / `verify` compare an installation against.
Run it whenever `_catalog_runtime/manifest.json` changes:

    python scripts/regenerate-migration-baseline.py
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tempfile

os.environ['TZ'] = 'UTC'
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'packages/python/src'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / 'packages/python/tests'))

import psycopg  # noqa: E402
from truss import LocalPostgres, Ok  # noqa: E402
from truss._initialization_custody import source_policy  # noqa: E402
from truss._migration_verify import acl, context, roles, structure  # noqa: E402
from runtime_migration_fixture import seed  # noqa: E402
from test_catalog_relational_support import relational_document  # noqa: E402

MIGRATIONS = SRC / 'truss/_migrations'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def main():
    raw = (SRC / 'truss/_catalog_runtime/manifest.json').read_bytes()
    digest = sha256(raw).hexdigest()
    manifest = json.loads(raw)
    with tempfile.TemporaryDirectory(prefix='truss-baseline-') as tmp, LocalPostgres(Path(tmp) / 'data') as pg:
        with psycopg.connect(pg.info.connection_uri, autocommit=True) as control:
            control.execute('CREATE DATABASE baseline')
        params = psycopg.conninfo.conninfo_to_dict(pg.info.connection_uri)
        params['dbname'] = 'baseline'
        uri = psycopg.conninfo.make_conninfo(**params)
        # Install, register a model, grant module access and seed every role kind, so the
        # observed ACLs cover reader, writer, feed and audit as well as owner and registrar.
        model = relational_document()
        model['id'] = 'adoc'
        (Path(tmp) / 'model.json').write_text(json.dumps(model))
        seed(uri, str(Path(tmp) / 'model.json'), str(Path(tmp) / 'seed.json'))
        with psycopg.connect(uri, autocommit=True) as admin:
            with admin.cursor() as cursor:
                cursor.execute('SET search_path=pg_catalog,pg_temp')
                _ctx, owner, registrar, _managed = context(cursor)
                inventory = structure(cursor)
                rolemap = roles(cursor, owner, registrar)
                profile = {kind: [] for kind in
                           ['owner', 'registrar', 'administrator', 'reader', 'writer', 'feed', 'audit', 'public']}
                for kind, name, _owner, grantee, privilege, grantable, _grantor in acl(cursor, full_names=True):
                    kinds = rolemap.get(grantee)
                    if not kinds or len(kinds) != 1:
                        raise SystemExit(f'unclassified grantee {grantee}: {kinds}')
                    profile[next(iter(kinds))].append([kind, name, privilege, grantable])
                for rows in profile.values():
                    rows.sort()
                cursor.execute('SELECT preparation_configuration FROM truss.catalog_runtime_installation')
                configuration = cursor.fetchone()[0]
    artifact = {
        'acl': profile, 'aclNameProfile': 'truss-native-acl-names/0.2', 'configuration': configuration,
        'definitionAlternatives': [], 'initializationAlternatives': [],
        'initializationPolicies': [source_policy(manifest)], 'inventory': inventory,
        'managedGrants': {'interfaceVersion': 'truss-managed-grants/0.1', 'observations': [], 'roles': []},
        'manifest': manifest, 'sha256': digest,
    }
    previous = json.loads((MIGRATIONS / 'manifest.json').read_bytes())
    for old in MIGRATIONS.glob('*.json'):
        old.unlink()
    body = canonical(artifact)
    (MIGRATIONS / f'{digest}.json').write_bytes(body)
    migration = {
        'baseline': previous['baseline'], 'edges': [], 'files': {f'{digest}.json': sha256(body).hexdigest()},
        'interfaceVersion': 'truss-runtime-migration/0.1', 'sourceWheels': {}, 'sources': [],
        'target': digest, 'targetRelease': manifest['releaseId'],
    }
    (MIGRATIONS / 'manifest.json').write_bytes(canonical(migration))
    print('target', digest)


if __name__ == '__main__':
    main()
