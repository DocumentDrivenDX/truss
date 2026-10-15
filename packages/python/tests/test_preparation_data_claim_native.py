"""Actual engine D custody and excluded E invocation of the pinned owner ABI."""
import contextlib
from importlib.resources import files
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from hashlib import sha256
import psycopg
from psycopg import sql
from truss import Error
from truss._engine_preparation import _EnginePreparationSession
from truss._preparation_data_claim import capture_preparation_claim_data, issue_preparation_data_claim_in_transaction
import test_preparation_program_native as original

_ROOT = Path(__file__).resolve().parents[3]
_OWNER = 'a8f73415aef8052e2dedeb3bc644426824675d14'
_OWNER_SQL_SHA = 'b91e5df98c96edb3643da58a28b76b876d1ef53142529cd773e55d0b14f07c96'


@unittest.skipIf(original.MutationCompiler is None, 'Requires original Weft mutation bridge')
class PreparationDataClaimNativeTests(unittest.TestCase):
    def exercise(self, admin, unused_data, params, enrolled):
        from adopter_workflow import transaction, success
        owner = admin.execute('SELECT r.rolname FROM truss.catalog_runtime_installation i JOIN pg_catalog.pg_roles r ON r.oid=i.owner_oid WHERE i.singleton').fetchone()[0]
        admin.execute(sql.SQL('GRANT pg_read_all_stats TO {} WITH INHERIT TRUE').format(sql.Identifier(owner)))
        for name in ('preparation-attempt-anchor-storage.sql', 'preparation-peer-xid.sql', 'preparation-attempt-anchor.sql'):
            admin.execute(files('truss').joinpath('_security_bootstrap', name).read_text())
        for kind, name in (('TABLE', 'preparation_attempt_anchor'), ('SEQUENCE', 'preparation_attempt_anchor_seq')):
            admin.execute(sql.SQL('ALTER '+kind+' truss.{} OWNER TO {}').format(sql.Identifier(name), sql.Identifier(owner)))
        for signature in ('require_preparation_peer_xid(int4,xid8)', 'create_preparation_attempt_anchor(bytea,int4,int4,xid8,bytea)',
                          'check_preparation_attempt_coordinator(int4,uuid)', 'check_preparation_attempt_data(int4,uuid)'):
            admin.execute(sql.SQL('ALTER FUNCTION truss.'+signature+' OWNER TO {}').format(sql.Identifier(owner)))
        # Read the exact committed owner spike for this fixture; no production
        # installer or generated-storage support is implied by loading it here.
        raw = subprocess.check_output(['git', 'show', _OWNER+':tests/security/native/pg18-preparation-data-claim.sql'], cwd='/Users/erik/Projects/umf')
        self.assertEqual(sha256(raw).hexdigest(), _OWNER_SQL_SHA)
        admin.execute(raw.decode())
        admin.execute(sql.SQL('ALTER SCHEMA umf_security OWNER TO {}').format(sql.Identifier(owner)))
        admin.execute(sql.SQL('ALTER TABLE umf_security.preparation_data_claim OWNER TO {}').format(sql.Identifier(owner)))
        for signature in ('claim_preparation_data(int4,uuid,xid8)', 'require_preparation_data_claim(int4,uuid)'):
            admin.execute(sql.SQL('ALTER FUNCTION umf_security.'+signature+' OWNER TO {}').format(sql.Identifier(owner)))
        # Assessor only: the production coordinator guard must call the private
        # consumer internally. No ordinary SDK wrapper/direct grant is added.
        admin.execute('CREATE FUNCTION truss.engine_claim_probe(a int4,n uuid) RETURNS TABLE(claim_id uuid,data_pid int4,data_xid xid8,program_id int8) LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ SELECT * FROM umf_security.require_preparation_data_claim(a,n) $$')
        admin.execute(sql.SQL('ALTER FUNCTION truss.engine_claim_probe(int4,uuid) OWNER TO {}').format(sql.Identifier(owner)))
        admin.execute('REVOKE ALL ON FUNCTION truss.engine_claim_probe(int4,uuid) FROM PUBLIC')
        admin.execute('GRANT EXECUTE ON FUNCTION truss.engine_claim_probe(int4,uuid) TO products_person')
        conninfo = psycopg.conninfo.make_conninfo(**dict(params, user='products_person', options='-c statement_timeout=10000'))
        # Generic local native login is an engine lifecycle fixture, not a new
        # SCRAM authentication qualification; that provider has separate evidence.
        session = _EnginePreparationSession(conninfo, 10000, 10000)
        try:
            cap = session.prepare_connection()
            def capture_pid(cursor):
                cursor.execute('SELECT pg_catalog.pg_backend_pid()::text', prepare=False)
                return int(cursor.fetchone()[0])
            data_pid = session.capture_before_snapshot(cap, capture_pid)
            with psycopg.connect(conninfo, autocommit=True) as coordinator:
                coordinator.execute('BEGIN')
                try:
                    cxid = coordinator.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
                    anchor, nonce = admin.execute('SELECT * FROM truss.create_preparation_attempt_anchor(%s,%s,%s,%s::xid8,%s)',
                        (b'original-products-store', data_pid, coordinator.info.backend_pid, cxid, enrolled.program_identity)).fetchone()
                    session.begin()
                    data = success(capture_preparation_claim_data(session))
                    self.assertEqual(data.data_pid, data_pid)
                    with transaction(admin) as (assembly, tx):
                        pending = success(issue_preparation_data_claim_in_transaction(assembly._host, tx, anchor_id=anchor, anchor_nonce=str(nonce), data=data))
                        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                            with coordinator.transaction():
                                coordinator.execute('SELECT * FROM truss.engine_claim_probe(%s,%s)', (anchor, nonce))
                    row = coordinator.execute('SELECT * FROM truss.engine_claim_probe(%s,%s)', (anchor, nonce)).fetchone()
                    self.assertEqual((str(row[0]), row[1], row[2]), (pending.claim_id, data.data_pid, data.data_xid))
                    program_id = admin.execute('SELECT program_id FROM truss.preparation_program_registration WHERE program_identity=%s::uuid',
                                               (json.loads(enrolled.program_identity),)).fetchone()[0]
                    self.assertEqual(row[3], program_id)
                    self.assertFalse(pending.authority)
                    with transaction(admin) as (assembly, tx):
                        retry = success(issue_preparation_data_claim_in_transaction(assembly._host, tx, anchor_id=anchor, anchor_nonce=str(nonce), data=data))
                        self.assertEqual(retry, pending)
                    acknowledged, error = session.complete(commit=False, committed=object(), rolled_back=object())
                    self.assertIsNone(error)
                    self.assertIsNotNone(acknowledged)
                    with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                        with coordinator.transaction():
                            coordinator.execute('SELECT * FROM truss.engine_claim_probe(%s,%s)', (anchor, nonce))
                    with transaction(admin) as (assembly, tx):
                        self.assertIsInstance(issue_preparation_data_claim_in_transaction(assembly._host, tx, anchor_id=anchor, anchor_nonce=str(nonce), data=data), Error)
                    self.assertEqual(admin.execute('SELECT count(*) FROM umf_security.preparation_data_claim WHERE anchor_id=%s', (anchor,)).fetchone(), (1,))
                finally:
                    coordinator.execute('ROLLBACK')
        finally:
            session.close()

    def test_engine_capture_and_independently_committed_native_claim(self):
        source = _ROOT / 'scripts/export-products-native-binding.py'
        lines = source.read_text().splitlines(keepends=True)
        indices = [i for i, line in enumerate(lines) if line.startswith("                    (output/'program-registration.json')")]
        self.assertEqual(len(indices), 1)
        lines.insert(indices[0]+1, '                    claim_probe(admin,person,params,enrolled)\n')
        namespace = {'__name__': 'engine_claim_assessor', '__file__': str(source), 'claim_probe': self.exercise}
        exec(compile(''.join(lines), str(source), 'exec'), namespace)
        model = _ROOT / 'docs/helix/04-build/evidence/preparation-program-20261015/original-demo-model.json'
        with tempfile.TemporaryDirectory(prefix='truss-engine-data-claim-') as directory:
            with contextlib.redirect_stdout(io.StringIO()):
                namespace['run'](model, Path(directory)/'products', shutil.which('bun') or 'bun',
                                 bootstrap_source_epoch=True, register_action_store=True, register_preparation_program=True)
