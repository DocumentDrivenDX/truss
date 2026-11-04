# SPDX-License-Identifier: MIT OR Apache-2.0
"""TN12 real public54 negative installation control. Other TN06–08 cases follow
under the frozen explicit CRUD route; this file claims no migration success.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import psycopg
from truss import LocalPostgres, Ok
from truss.lifecycle import InstallRefused
from truss.catalog_runtime import _release
from runtime_migration_fixture import assembly
import test_temporal_canonical_text_native as scalar_fixture
ROOT = scalar_fixture.ROOT

PUBLIC054_WHEEL_SHA256 = '4aebc56e92fdbde6714d9b811860707d2ffc9b0edbc63cc91e9dc3488c042b52'


class TemporalCatalogTransportTests(unittest.TestCase):
    cleanup_owned_runtime = classmethod(scalar_fixture.TemporalCanonicalTextNativeTests.cleanup_owned_runtime.__func__)

    @classmethod
    def setUpClass(cls):
        cls.old_python = Path(os.environ['TRUSS_PUBLIC054_PYTHON'])
        cls.old_wheel = Path(os.environ['TRUSS_PUBLIC054_WHEEL'])
        if sha256(cls.old_wheel.read_bytes()).hexdigest() != PUBLIC054_WHEEL_SHA256:
            raise RuntimeError('Exact verified real public54 wheel required')
        # Validate installed archive payload, not a caller-supplied version label.
        check = '''import hashlib,importlib.metadata,json,pathlib,sys,zipfile,truss
assert importlib.metadata.version('umf-truss')=='0.0.54'
root=pathlib.Path(truss.__file__).parent
with zipfile.ZipFile(sys.argv[1]) as archive:
 for name in archive.namelist():
  if name.startswith('truss/') and not name.endswith('/'):
   assert (root/name.removeprefix('truss/')).read_bytes()==archive.read(name),name
print(json.dumps({'distribution':'umf-truss','version':'0.0.54','moduleRoot':str(root),'manifestSha256':hashlib.sha256((root/'_catalog_runtime/manifest.json').read_bytes()).hexdigest()}))
'''
        cls.old_environment = {**os.environ, 'PYTHONPATH': str(ROOT / 'packages/python/tests'), 'PYTHONDONTWRITEBYTECODE': '1'}
        observed = subprocess.run([str(cls.old_python), '-c', check, str(cls.old_wheel)],
            env=cls.old_environment, check=True, capture_output=True, text=True, timeout=30)
        cls.old_identity = json.loads(observed.stdout)
        cls.root = Path(tempfile.mkdtemp(prefix='truss-temporal-public054-refusal-'))
        cls.runtime = LocalPostgres(cls.root / 'data')
        cls.addClassCleanup(cls.cleanup_owned_runtime)
        cls.runtime.__enter__()
        cls.original_pid = int((cls.runtime.directory / 'postmaster.pid').read_text().splitlines()[0])
        cls.uri = cls.runtime.info.connection_uri

    def snapshot(self, connection):
        from truss._migration_verify import structure, acl
        tables = connection.execute("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relkind IN ('r','p') ORDER BY c.relname").fetchall()
        rows = {}
        for (name,) in tables:
            statement = psycopg.sql.SQL('SELECT coalesce(jsonb_agg(v ORDER BY v::text),\'[]\'::jsonb)::text FROM (SELECT to_jsonb(t) v FROM ONLY truss.{} t) q').format(psycopg.sql.Identifier(name))
            rows[name] = connection.execute(statement).fetchone()[0]
        with connection.cursor() as cursor:
            inventory, grants = structure(cursor), acl(cursor)
        roles = connection.execute('SELECT oid,rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,rolcanlogin,rolreplication,rolbypassrls,rolconfig FROM pg_roles ORDER BY oid').fetchall()
        memberships = connection.execute('SELECT roleid,member,grantor,admin_option,inherit_option,set_option FROM pg_auth_members ORDER BY roleid,member,grantor').fetchall()
        sequences = {}
        for (name,) in connection.execute("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relkind='S' ORDER BY c.relname"):
            sequences[name] = connection.execute(psycopg.sql.SQL('SELECT last_value,is_called FROM truss.{}').format(psycopg.sql.Identifier(name))).fetchone()
        return {'tables': rows, 'sequences': sequences, 'inventory': inventory, 'acl': grants, 'roles': roles, 'memberships': memberships}

    def test_public54_populated_installation_refuses_candidate_without_effects(self):
        from test_catalog_relational_support import relational_document
        model = relational_document()
        model['id'] = 'adoc'
        model['extensions'] = {'x-original-unknown': {'future': [3, 1, 4], 'retained': None}}
        model['vocabularies'] = {'x-original-unknown': {'version': '1.0.0'}}
        model_path, seed_path = self.root / 'model.json', self.root / 'original-seed.json'
        model_path.write_text(json.dumps(model, ensure_ascii=True))
        # Existing seed helper performs public acceptance, create, import,
        # update, edge, retained request/history/feed/ACK. No migration runs.
        result = subprocess.run([str(self.old_python), str(ROOT / 'packages/python/tests/runtime_migration_fixture.py'),
                                 self.uri, str(model_path), str(seed_path)],
                                env=self.old_environment, capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise AssertionError('Genuine public54 seed failed: ' + result.stdout + result.stderr)
        with psycopg.connect(self.uri, autocommit=True, options='-c statement_timeout=10000') as admin:
            self.assertEqual(admin.execute('SELECT release_id FROM truss.catalog_runtime_installation').fetchone(),
                             ('truss-catalog-runtime/0.75-candidate',))
            for table in ('prop_def', 'object', 'schema_doc', 'journal', 'catalog_registration_request', 'request_receipt'):
                self.assertGreater(admin.execute(psycopg.sql.SQL('SELECT count(*) FROM truss.{}').format(psycopg.sql.Identifier(table))).fetchone()[0], 0, table)
            before = self.snapshot(admin)
            admin.execute('BEGIN')
            host, candidate, transaction = assembly(admin)
            try:
                answer = candidate.install_in_transaction(transaction)
                self.assertIsInstance(answer, Ok)
                self.assertIsInstance(answer.value, InstallRefused)
                self.assertEqual(answer.value.code, 'incompatible')
            finally:
                host.detach()
            admin.commit()
            after = self.snapshot(admin)
            self.assertEqual(after, before)
            manifest, digest, _ = _release()
            self.assertEqual(manifest['releaseId'], 'truss-catalog-runtime/0.76-temporal-candidate')
            print('temporal-public054-no-effects ' + json.dumps({
                'oldWheelSha256': PUBLIC054_WHEEL_SHA256, 'oldManifestSha256': self.old_identity['manifestSha256'],
                'candidateManifestSha256': digest, 'refusal': 'InstallRefused/incompatible',
                'beforeAfterEqual': True, 'populatedTables': sorted(before['tables']),
                'tableByteDigests': {name: sha256(raw.encode()).hexdigest() for name, raw in before['tables'].items()}}, sort_keys=True))
