"""Actual authority-exclusion component; no bulk seal or fixed-cut bridge claim."""
import psycopg
from dataclasses import replace
from truss import Ok, Error, adopt_psycopg_host
import test_group_create_native as base
from truss._security_preparation_authority import (
    bootstrap_preparation_authority_lock_in_transaction,
    acquire_preparation_authority_lock_with_cursor,
    capture_preparation_data_with_cursor, verify_preparation_data_with_cursor,
    verify_preparation_peer_with_cursor,
)


class PreparationAuthorityNativeTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_current_authority_exclusion_does_not_refresh_or_admit_rr(self):
        data, data_host, assembly, data_tx = self.ready(document_ids=('adoc',))
        data_host.detach(); data.commit()
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        membership = """SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_auth_members m
            JOIN pg_catalog.pg_roles r ON r.oid=m.roleid
            JOIN pg_catalog.pg_roles p ON p.oid=m.member
            WHERE r.rolname='group_writer' AND p.rolname=SESSION_USER)"""
        self.assertEqual(data.execute(membership).fetchone(), (True,))
        original_snapshot = data.execute('SELECT pg_current_snapshot()::text').fetchone()
        with data.cursor() as cursor:
            captured = capture_preparation_data_with_cursor(cursor)
            verify_preparation_data_with_cursor(cursor, captured)
        self.assertFalse(captured.security_ready)
        self.admin.execute('REVOKE group_writer FROM consumer')
        self.assertEqual(data.execute(membership).fetchone(), (True,))
        self.admin.execute('CREATE ROLE preparation_executor LOGIN NOINHERIT')
        self.admin.execute('GRANT pg_read_all_stats TO preparation_executor WITH INHERIT TRUE')
        def drop_executor():
            self.admin.execute('DROP OWNED BY preparation_executor')
            self.admin.execute('DROP ROLE preparation_executor')
        self.addCleanup(drop_executor)
        self.admin.execute('BEGIN')
        installer = adopt_psycopg_host(self.admin)
        installed = bootstrap_preparation_authority_lock_in_transaction(
            installer, installer.adopt_transaction().value,
            executor_role='preparation_executor')
        self.assertIsInstance(installed, Ok, str(installer._custody.last_attempt.error))
        issuer = installed.value
        self.assertFalse(issuer.security_ready)
        installer.detach(); self.admin.commit()
        params = psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        params['user'] = 'preparation_executor'
        coordinator = psycopg.connect(**params, autocommit=True,
            options='-c statement_timeout=10000')
        self.addCleanup(coordinator.close)
        coordinator.execute('BEGIN')
        host = adopt_psycopg_host(coordinator, statement_timeout_ms=10000)
        self.addCleanup(host.detach)
        self.consumer_connections.append((coordinator, host))
        tx = host.adopt_transaction().value
        def acquire(cursor, observed):
            acquire_preparation_authority_lock_with_cursor(cursor, issuer)
            verify_preparation_peer_with_cursor(cursor, captured)
            with self.assertRaises(ValueError):
                verify_preparation_peer_with_cursor(cursor, replace(captured, challenge='foreign'))
            cursor.execute(membership.replace('p.rolname=SESSION_USER', "p.rolname='consumer'"))
            return cursor.fetchone()
        fresh = host._run_operation(tx, acquire)
        self.assertIsInstance(fresh, Ok, str(host._custody.last_attempt.error))
        self.assertEqual(fresh.value, (False,))
        self.admin.execute("SET lock_timeout='150ms'")
        for statement in ('GRANT group_writer TO consumer WITH SET FALSE',
                          'ALTER ROLE consumer NOLOGIN',
                          "UPDATE truss.module_access SET reader_role=reader_role"):
            with self.assertRaises(psycopg.errors.LockNotAvailable):
                self.admin.execute(statement)
        self.assertEqual(data.execute('SELECT pg_current_snapshot()::text').fetchone(), original_snapshot)
        self.assertEqual(data.execute(membership).fetchone(), (True,))
        with data.cursor() as cursor:
            verify_preparation_data_with_cursor(cursor, captured)
        data.execute("SELECT set_config('application_name','changed',true)")
        changed = host._run_operation(tx, lambda cursor, observed: verify_preparation_peer_with_cursor(cursor, captured))
        self.assertIsInstance(changed, Error)
        data.execute('SELECT set_config(\'application_name\',%s,true)', (captured.challenge,))
        with data.cursor() as cursor:
            verify_preparation_data_with_cursor(cursor, captured)
        self.assertEqual(data.execute("SELECT current_setting('transaction_isolation'),current_setting('transaction_read_only')").fetchone(), ('repeatable read', 'off'))
        # Original RC-only facade remains closed on the stale RR connection.
        data.execute('SAVEPOINT original_rc_boundary')
        with self.assertRaises((psycopg.errors.FeatureNotSupported, psycopg.errors.InsufficientPrivilege)):
            data.execute('SELECT truss.reader_catalog(256,1048576,%s,%s)',
                self.admin.execute('SELECT release_id,release_sha256 FROM truss.catalog_runtime_installation').fetchone())
        data.execute('ROLLBACK TO SAVEPOINT original_rc_boundary')
        host.detach(); coordinator.rollback()
        self.admin.execute("SET lock_timeout='0'")
        # Released native role cut admits the waiting class of change.
        self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
        coordinator.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        with self.assertRaises(psycopg.errors.FeatureNotSupported):
            coordinator.execute('SELECT truss.acquire_preparation_authority_lock()')
        coordinator.rollback()
        # Ordinary unrelated data person has no issuer EXECUTE privilege.
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            data.execute('SELECT truss.acquire_preparation_authority_lock()')
        data.rollback()
        coordinator.execute('BEGIN')
        with coordinator.cursor() as cursor:
            with self.assertRaises(ValueError):
                verify_preparation_peer_with_cursor(cursor, captured)
        data.close()
        with coordinator.cursor() as cursor:
            with self.assertRaises(ValueError):
                verify_preparation_peer_with_cursor(cursor, captured)
        coordinator.rollback()
