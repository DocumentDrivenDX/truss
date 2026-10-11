"""Actual lock-lifetime fence, not authenticated installed archive admission."""
import unittest
from pathlib import Path
from test_native_pg8000 import NativeBoundaryFixture
ROOT=Path(__file__).resolve().parents[3]

class ArchiveSelfWriteFenceNativeTests(NativeBoundaryFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin=cls.Connection(**cls.kwargs)
        cls.admin.run('CREATE DATABASE archive_fence_component')
        cls.kwargs={**cls.kwargs,'database':'archive_fence_component'}
        c=cls.Connection(**cls.kwargs)
        try:
            c.run((ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text())
            c.run((ROOT/'packages/postgresql/native/catalog-report/archive-self-write-fence.sql').read_text())
            c.run("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0','fixture','fixture',sha256(decode('01','hex')),'fixture',sha256(decode('02','hex')),'fixture','truss',now(),now()::text)")
        finally:c.close()
    @classmethod
    def tearDownClass(cls):
        cls.admin.run('DROP DATABASE archive_fence_component');cls.admin.close()
        super().tearDownClass()
    def setUp(self):
        self.c=self.Connection(**self.kwargs);self.c.run('BEGIN');self.c.run('SET CONSTRAINTS ALL IMMEDIATE')
        self.c.run("INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('fixture','input','original',decode('01','hex'),sha256(convert_to('original','UTF8')))")
    def tearDown(self):self.c.run('ROLLBACK');self.c.close()
    def lock(self):self.c.run('LOCK TABLE truss.installation_archive IN SHARE MODE NOWAIT')
    def refused(self,sql):
        from pg8000.exceptions import DatabaseError
        self.c.run('SAVEPOINT refusal')
        try:
            with self.assertRaises(DatabaseError) as caught:self.c.run(sql)
            self.assertEqual(caught.exception.args[0]['C'],'55000')
            self.assertEqual(caught.exception.args[0]['M'],'selected archive cut excludes same-backend writes')
        finally:
            self.c.run('ROLLBACK TO refusal');self.c.run('RELEASE refusal')
    def test_all_write_events_and_noop_statements_are_fenced(self):
        self.lock()
        for sql in ["UPDATE truss.installation_archive SET artifact_bytes=decode('02','hex')",
                    "INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('fixture','input','second',decode('02','hex'),sha256(convert_to('second','UTF8')))",
                    'DELETE FROM truss.installation_archive','TRUNCATE truss.installation_archive',
                    "INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) SELECT installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256 FROM truss.installation_archive WHERE false",
                    'UPDATE truss.installation_archive SET artifact_identity=artifact_identity WHERE false']:
            with self.subTest(sql=sql):self.refused(sql)
        self.assertEqual(self.c.run("SELECT encode(artifact_bytes,'hex') FROM truss.installation_archive"),[['01']])
    def test_change_restore_cannot_begin_under_original_cut(self):
        self.lock();self.refused("UPDATE truss.installation_archive SET artifact_bytes=decode('02','hex')")
        self.assertEqual(self.c.run("SELECT encode(artifact_bytes,'hex') FROM truss.installation_archive"),[['01']])
    def test_rollback_across_acquisition_releases_fence_same_xid(self):
        xid=self.c.run('SELECT pg_current_xact_id()::text');self.c.run('SAVEPOINT acquisition');self.lock()
        self.c.run('ROLLBACK TO acquisition');self.c.run('RELEASE acquisition')
        self.assertEqual(self.c.run('SELECT pg_current_xact_id()::text'),xid)
        self.assertEqual(self.c.run("SELECT count(*) FROM pg_locks WHERE locktype='relation' AND relation='truss.installation_archive'::regclass AND pid=pg_backend_pid() AND mode='ShareLock' AND granted"),[[0]])
        self.c.run("UPDATE truss.installation_archive SET artifact_bytes=decode('02','hex')")
        self.assertEqual(self.c.run("SELECT encode(artifact_bytes,'hex') FROM truss.installation_archive"),[['02']])
    def test_release_reparents_fence_and_later_rollback_preserves_it(self):
        self.c.run('SAVEPOINT acquisition');self.lock();self.c.run('RELEASE acquisition')
        self.c.run('SAVEPOINT later');self.c.run('ROLLBACK TO later');self.c.run('RELEASE later')
        self.refused('DELETE FROM truss.installation_archive')
    def test_unselected_writes_and_reads_remain_available(self):
        self.c.run("UPDATE truss.installation_archive SET artifact_bytes=decode('02','hex')")
        self.assertEqual(self.c.run("SELECT encode(artifact_bytes,'hex') FROM truss.installation_archive"),[['02']])
        self.lock();self.assertEqual(self.c.run('SELECT count(*) FROM truss.installation_archive'),[[1]])
    def test_always_enabled_and_public_execution_revoked(self):
        self.assertEqual(self.c.run("SELECT tgenabled FROM pg_trigger WHERE tgrelid='truss.installation_archive'::regclass AND tgname='runtime_selected_archive_write_fence'"),[['A']])
        self.assertEqual(self.c.run("SELECT count(*) FROM pg_proc WHERE oid='truss.runtime_fence_selected_archive_writes()'::regprocedure"),[[1]])
        self.assertEqual(self.c.run("SELECT count(*) FROM pg_proc p CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a WHERE p.oid='truss.runtime_fence_selected_archive_writes()'::regprocedure AND a.grantee=0 AND a.privilege_type='EXECUTE'"),[[0]])
    def test_lock_upgrade_keeps_original_fence_visible(self):
        self.lock();self.c.run('LOCK TABLE truss.installation_archive IN ACCESS EXCLUSIVE MODE NOWAIT')
        self.assertEqual(self.c.run("SELECT count(*) FROM pg_locks WHERE locktype='relation' AND relation='truss.installation_archive'::regclass AND pid=pg_backend_pid() AND mode='ShareLock' AND granted"),[[1]])
        self.refused('DELETE FROM truss.installation_archive')
    def test_replica_mode_does_not_disable_fence(self):
        self.lock();self.c.run('SET LOCAL session_replication_role=replica')
        self.refused('DELETE FROM truss.installation_archive')
