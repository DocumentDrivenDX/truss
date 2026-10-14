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
    observe_preparation_owners_with_cursor,
    bootstrap_preparation_data_authority_lock_in_transaction,
    verify_preparation_mint_exclusion_with_cursor,
)


class PreparationAuthorityNativeTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_reserved_two_integer_permit_namespace_requires_native_issuer(self):
        """Dedicated disposable DB privilege witness, not permit admission."""
        data, host, assembly, tx = self.ready(document_ids=('adoc',))
        host.detach(); data.commit()
        self.admin.execute('CREATE ROLE preparation_mint_owner NOLOGIN')
        self.addCleanup(self.admin.execute, 'DROP ROLE preparation_mint_owner')
        self.addCleanup(self.admin.execute, 'DROP OWNED BY preparation_mint_owner')
        names = ('pg_advisory_lock', 'pg_advisory_lock_shared',
                 'pg_try_advisory_lock', 'pg_try_advisory_lock_shared',
                 'pg_advisory_xact_lock', 'pg_advisory_xact_lock_shared',
                 'pg_try_advisory_xact_lock', 'pg_try_advisory_xact_lock_shared')
        for name in names:
            self.admin.execute(f'REVOKE ALL ON FUNCTION pg_catalog.{name}(int4,int4) FROM PUBLIC')
        self.admin.execute('GRANT EXECUTE ON FUNCTION pg_catalog.pg_advisory_xact_lock(int4,int4) TO preparation_mint_owner')
        self.admin.execute('CREATE FUNCTION public.preparation_mint_probe() RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ SELECT pg_catalog.pg_advisory_xact_lock(19001,19002) $$')
        self.admin.execute('ALTER FUNCTION public.preparation_mint_probe() OWNER TO preparation_mint_owner')
        self.admin.execute('REVOKE ALL ON FUNCTION public.preparation_mint_probe() FROM PUBLIC')
        self.admin.execute('GRANT EXECUTE ON FUNCTION public.preparation_mint_probe() TO consumer')
        caller_oid = self.admin.execute("SELECT oid FROM pg_catalog.pg_roles WHERE rolname='consumer'").fetchone()[0]
        owner_oid = self.admin.execute("SELECT oid FROM pg_catalog.pg_roles WHERE rolname='preparation_mint_owner'").fetchone()[0]
        with self.admin.cursor() as cursor:
            verify_preparation_mint_exclusion_with_cursor(cursor, caller_oid, owner_oid)
        self.admin.execute('CREATE ROLE preparation_mint_escape NOLOGIN')
        self.addCleanup(self.admin.execute, 'DROP ROLE preparation_mint_escape')
        self.addCleanup(self.admin.execute, 'DROP OWNED BY preparation_mint_escape')
        self.admin.execute('GRANT EXECUTE ON FUNCTION pg_catalog.pg_advisory_xact_lock(int4,int4) TO preparation_mint_escape')
        self.admin.execute('GRANT preparation_mint_escape TO consumer WITH INHERIT TRUE')
        with self.admin.cursor() as cursor:
            with self.assertRaises(ValueError):
                verify_preparation_mint_exclusion_with_cursor(cursor, caller_oid, owner_oid)
        data.execute('BEGIN')
        data.execute('SELECT pg_catalog.pg_advisory_xact_lock(19001,19002)')
        data.execute('ROLLBACK')
        self.admin.execute('REVOKE preparation_mint_escape FROM consumer')
        with self.admin.cursor() as cursor:
            verify_preparation_mint_exclusion_with_cursor(cursor, caller_oid, owner_oid)
        self.admin.execute('GRANT preparation_mint_owner TO consumer WITH INHERIT FALSE, SET TRUE')
        with self.admin.cursor() as cursor:
            with self.assertRaises(ValueError):
                verify_preparation_mint_exclusion_with_cursor(cursor, caller_oid, owner_oid)
        self.admin.execute('REVOKE preparation_mint_owner FROM consumer')
        for name in names:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                data.execute(f'SELECT pg_catalog.{name}(19001,19002)')
        data.execute('BEGIN')
        data.execute('SELECT public.preparation_mint_probe()')
        rows = self.admin.execute("SELECT classid::text,objid::text,objsubid,mode FROM pg_catalog.pg_locks WHERE pid=%s AND locktype='advisory'", (data.info.backend_pid,)).fetchall()
        self.assertIn(('19001', '19002', 2, 'ExclusiveLock'), rows)
        # Existing bigint group namespace remains callable and distinct.
        data.execute('SELECT pg_catalog.pg_advisory_xact_lock(81608673413698::int8)')
        spaces = self.admin.execute("SELECT DISTINCT objsubid FROM pg_catalog.pg_locks WHERE pid=%s AND locktype='advisory' ORDER BY objsubid", (data.info.backend_pid,)).fetchall()
        self.assertEqual(spaces, [(1,), (2,)])
        self.assertEqual(data.execute('COMMIT').statusmessage, 'COMMIT')
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=%s AND locktype='advisory'", (data.info.backend_pid,)).fetchone(), (0,))
        self.admin.execute('DROP FUNCTION public.preparation_mint_probe()')

    def test_data_owned_authority_exclusion_survives_coordinator_disconnect(self):
        data, old_host, assembly, old_tx = self.ready(document_ids=('adoc',))
        old_host.detach(); data.commit()
        self.admin.execute('CREATE ROLE preparation_executor LOGIN NOINHERIT')
        self.addCleanup(self.admin.execute, 'DROP ROLE preparation_executor')
        self.addCleanup(self.admin.execute, 'DROP OWNED BY preparation_executor')
        self.admin.execute('GRANT pg_read_all_stats TO preparation_executor WITH INHERIT TRUE')
        self.admin.execute('GRANT SELECT ON truss.catalog_runtime_installation,truss.schema_head,truss.schema_doc,truss.module_access TO preparation_executor')
        self.admin.execute('BEGIN')
        installer = adopt_psycopg_host(self.admin)
        install_tx = installer.adopt_transaction().value
        authority = bootstrap_preparation_authority_lock_in_transaction(installer, install_tx, executor_role='preparation_executor')
        data_lock = bootstrap_preparation_data_authority_lock_in_transaction(installer, install_tx, executor_role='consumer')
        self.assertIsInstance(authority, Ok, str(installer._custody.last_attempt.error))
        self.assertIsInstance(data_lock, Ok, str(installer._custody.last_attempt.error))
        installer.detach(); self.admin.commit()
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        data_host = adopt_psycopg_host(data)
        self.consumer_connections.append((data, data_host))
        data_tx = data_host.adopt_transaction(isolation='repeatable_read').value
        def hold(cursor, observed):
            acquire_preparation_authority_lock_with_cursor(cursor, data_lock.value)
            return capture_preparation_data_with_cursor(cursor)
        captured = data_host._run_operation(data_tx, hold)
        self.assertIsInstance(captured, Ok, str(data_host._custody.last_attempt.error))
        params = psycopg.conninfo.conninfo_to_dict(self.info.connection_uri); params['user'] = 'preparation_executor'
        coordinator = psycopg.connect(**params, autocommit=True, options='-c statement_timeout=10000')
        self.addCleanup(coordinator.close)
        coordinator.execute('BEGIN')
        host = adopt_psycopg_host(coordinator, statement_timeout_ms=10000, operation_timeout_ms=30000)
        self.consumer_connections.append((coordinator, host))
        adopted = host.adopt_transaction()
        self.assertIsInstance(adopted, Ok, str(host._custody.last_attempt.error))
        tx = adopted.value
        observed = host._run_operation(tx, lambda cursor, identity: observe_preparation_owners_with_cursor(cursor, authority.value, captured.value))
        self.assertIsInstance(observed, Ok, str(host._custody.last_attempt.error))
        self.assertEqual(observed.value.owners, (('adoc', 'm', 'group_reader', 'group_writer', 'true'),))
        self.admin.execute("SET lock_timeout='150ms'")
        with self.assertRaises(psycopg.errors.LockNotAvailable):
            self.admin.execute('REVOKE group_writer FROM consumer')
        coordinator_pid = coordinator.info.backend_pid
        coordinator.close()
        self.admin.execute('SELECT pg_catalog.pg_stat_clear_snapshot()')
        self.assertEqual(self.admin.execute('SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_stat_activity WHERE pid=%s)', (coordinator_pid,)).fetchone(), (False,))
        with self.assertRaises(psycopg.errors.LockNotAvailable):
            self.admin.execute('REVOKE group_writer FROM consumer')
        live_data = data_host._run_operation(data_tx, lambda cursor, identity: verify_preparation_data_with_cursor(cursor, captured.value))
        self.assertIsInstance(live_data, Ok)
        data_host.detach()
        # Actual original native completion of this diagnostic transaction;
        # no selection/manifest/seal is written or qualified by the test.
        self.assertEqual(data.execute('COMMIT').statusmessage, 'COMMIT')
        self.admin.execute('REVOKE group_writer FROM consumer')
        self.admin.execute("SET lock_timeout='0'")

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
        data.execute('SET LOCAL search_path=public,pg_catalog')
        with data.cursor() as cursor:
            with self.assertRaises(ValueError):
                verify_preparation_data_with_cursor(cursor, captured)
        data.execute('SET LOCAL search_path=pg_catalog,pg_temp')
        self.assertFalse(captured.security_ready)
        self.admin.execute('REVOKE group_writer FROM consumer')
        self.assertEqual(data.execute(membership).fetchone(), (True,))
        self.admin.execute('CREATE ROLE preparation_executor LOGIN NOINHERIT')
        self.admin.execute('GRANT pg_read_all_stats TO preparation_executor WITH INHERIT TRUE')
        self.admin.execute('GRANT SELECT ON truss.catalog_runtime_installation,truss.schema_head,truss.schema_doc,truss.module_access TO preparation_executor')
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
            owners = observe_preparation_owners_with_cursor(cursor, issuer, captured)
            self.assertEqual(owners.owners, (('adoc', 'm', 'group_reader', 'group_writer', 'false'),))
            self.assertFalse(owners.security_ready)
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
        coordinator.execute('BEGIN')
        with coordinator.cursor() as cursor:
            owners = observe_preparation_owners_with_cursor(cursor, issuer, captured)
            self.assertEqual(owners.owners, (('adoc', 'm', 'group_reader', 'group_writer', 'true'),))
        coordinator.rollback()
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
