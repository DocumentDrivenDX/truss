"""Owner-private native program binding; no authorization or SQL execution."""
import contextlib
from importlib.resources import files
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import uuid
import psycopg
from psycopg import sql

try:
    from weft import MutationCompiler
except ImportError:
    MutationCompiler = None

_ROOT = Path(__file__).resolve().parents[3]


@unittest.skipIf(MutationCompiler is None, 'Requires original Weft mutation bridge')
class PreparationProgramBindingNativeTests(unittest.TestCase):
    def exercise(self, admin, data, params, enrolled):
        owner = admin.execute('SELECT r.rolname FROM truss.catalog_runtime_installation i JOIN pg_catalog.pg_roles r ON r.oid=i.owner_oid WHERE i.singleton').fetchone()[0]
        admin.execute(sql.SQL('GRANT pg_read_all_stats TO {} WITH INHERIT TRUE').format(sql.Identifier(owner)))
        for name in ('preparation-attempt-anchor-storage.sql', 'preparation-peer-xid.sql',
                     'preparation-attempt-anchor.sql', 'preparation-program-binding.sql'):
            admin.execute(files('truss').joinpath('_security_bootstrap', name).read_text())
        for kind, name in (('TABLE', 'preparation_attempt_anchor'), ('SEQUENCE', 'preparation_attempt_anchor_seq')):
            admin.execute(sql.SQL('ALTER '+kind+' truss.{} OWNER TO {}').format(sql.Identifier(name), sql.Identifier(owner)))
        signatures = ('require_preparation_peer_xid(int4,xid8)',
                      'create_preparation_attempt_anchor(bytea,int4,int4,xid8,bytea)',
                      'check_preparation_attempt_coordinator(int4,uuid)',
                      'check_preparation_attempt_data(int4,uuid)',
                      'resolve_preparation_program_binding(int4,uuid,xid8)')
        for signature in signatures:
            admin.execute(sql.SQL('ALTER FUNCTION truss.'+signature+' OWNER TO {}').format(sql.Identifier(owner)))
        # Fixture-only narrow assessor. No production installer grants this path.
        admin.execute('CREATE FUNCTION truss.program_binding_probe(a int4,n uuid,x xid8) RETURNS bigint LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ SELECT truss.resolve_preparation_program_binding(a,n,x) $$')
        admin.execute(sql.SQL('ALTER FUNCTION truss.program_binding_probe(int4,uuid,xid8) OWNER TO {}').format(sql.Identifier(owner)))
        admin.execute('REVOKE ALL ON FUNCTION truss.program_binding_probe(int4,uuid,xid8) FROM PUBLIC')
        admin.execute('GRANT EXECUTE ON FUNCTION truss.program_binding_probe(int4,uuid,xid8) TO products_person')
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            data.execute('SELECT truss.resolve_preparation_program_binding(1,%s,%s::xid8)', (uuid.uuid4(), '1'))
        with psycopg.connect(**dict(params, user='products_person'), autocommit=True,
                             options='-c statement_timeout=10000') as coordinator:
            coordinator.execute('BEGIN')
            try:
                xid = coordinator.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
                def anchor(program):
                    return admin.execute('SELECT * FROM truss.create_preparation_attempt_anchor(%s,%s,%s,%s::xid8,%s)',
                                         (b'original-products-store', data.info.backend_pid,
                                          coordinator.info.backend_pid, xid, program)).fetchone()
                original = anchor(enrolled.program_identity)
                foreign = anchor(b'"unregistered-program"')
                data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ WRITE')
                try:
                    data_xid = data.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
                    expected = admin.execute('SELECT program_id FROM truss.preparation_program_registration WHERE program_identity=%s::uuid',
                                             (json.loads(enrolled.program_identity),)).fetchone()[0]
                    def resolve(selected, claimed=data_xid):
                        return data.execute('SELECT truss.program_binding_probe(%s,%s,%s::xid8)', (*selected, claimed)).fetchone()[0]
                    self.assertEqual(resolve(original), expected)
                    with psycopg.connect(**dict(params, user='products_person'), autocommit=True,
                                         options='-c statement_timeout=10000') as foreign_data:
                        foreign_data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ WRITE')
                        try:
                            foreign_xid = foreign_data.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
                            with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                                foreign_data.execute('SELECT truss.program_binding_probe(%s,%s,%s::xid8)',
                                                     (*original, foreign_xid))
                        finally:
                            foreign_data.execute('ROLLBACK')
                    for selected, claimed in ((foreign, data_xid), ((original[0], uuid.uuid4()), data_xid),
                                              (original, str(int(data_xid)+1))):
                        with self.subTest(selected=selected, xid=claimed):
                            with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                                with data.transaction(): resolve(selected, claimed)
                    self.assertEqual(resolve(original), expected)
                finally:
                    data.execute('ROLLBACK')
            finally:
                coordinator.execute('ROLLBACK')

    def test_native_anchor_resolves_exact_original_enrollment(self):
        source = _ROOT / 'scripts/export-products-native-binding.py'
        raw = source.read_text()
        lines = raw.splitlines(keepends=True)
        indices = [i for i, line in enumerate(lines) if line.startswith("                    (output/'program-registration.json')")]
        self.assertEqual(len(indices), 1)
        lines.insert(indices[0]+1, '                    binding_probe(admin,person,params,enrolled)\n')
        namespace = {'__name__': 'native_program_binding_assessor', '__file__': str(source),
                     'binding_probe': self.exercise}
        exec(compile(''.join(lines), str(source), 'exec'), namespace)
        model = _ROOT / 'docs/helix/04-build/evidence/preparation-program-20261015/original-demo-model.json'
        with tempfile.TemporaryDirectory(prefix='truss-program-binding-') as directory:
            with contextlib.redirect_stdout(io.StringIO()):
                namespace['run'](model, Path(directory)/'products', shutil.which('bun') or 'bun',
                                 bootstrap_source_epoch=True, register_action_store=True,
                                 register_preparation_program=True)
