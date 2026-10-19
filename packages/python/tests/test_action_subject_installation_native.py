# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native protected enrollment component; no invocation authentication claim."""
import psycopg
import test_group_create_native as base
from truss import Ok, Error, adopt_psycopg_host
from truss._action_subject_installation import bootstrap_action_subjects_in_transaction
from truss._security_catalog_subject_installation import (bootstrap_owned_action_role_cut_in_transaction,
    bootstrap_role_catalog_cut_issuer_in_transaction,verify_owned_action_role_cut_with_cursor,
    verify_role_catalog_cut_issuer_with_cursor)
from psycopg import sql


class ActionSubjectInstallationNativeTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name] = None

    def test_private_explicit_subject_kind_and_original_commit(self):
        data, old_host, assembly, old_tx = self.ready(document_ids=('adoc',))
        old_host.detach(); data.commit()
        self.admin.execute('CREATE ROLE action_service LOGIN')
        self.addCleanup(self.admin.execute, 'DROP ROLE action_service')
        self.admin.execute('CREATE SCHEMA subject_shadow')
        self.addCleanup(self.admin.execute, 'DROP SCHEMA subject_shadow CASCADE')
        self.admin.execute('CREATE DOMAIN subject_shadow.text AS pg_catalog.text CHECK(false)')
        self.admin.execute('SET search_path=subject_shadow,pg_catalog')
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        result = bootstrap_action_subjects_in_transaction(host, tx,
            bindings=(('consumer', b'original-human-identity', 'human'),
                      ('action_service', b'original-service-identity', 'service')))
        self.assertIsInstance(result, Ok, str(host._custody.last_attempt.error))
        self.assertFalse(result.value.security_ready)
        host.detach(); self.admin.commit()
        self.assertEqual(self.admin.execute('SHOW search_path').fetchone(), ('subject_shadow, pg_catalog',))
        self.admin.execute('SET search_path=pg_catalog,pg_temp')
        params = psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        params['user'] = 'action_service'
        with psycopg.connect(**params,autocommit=True) as service:
            service.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
            service.execute('SELECT truss.acquire_action_subject_cut()')
            service.execute('ROLLBACK')
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                service.execute('SELECT * FROM truss.action_subject_binding')
        self.assertEqual(self.admin.execute('SELECT subject_kind,principal_identity FROM truss.action_subject_binding ORDER BY subject_kind').fetchall(),
            [('human', b'original-human-identity'), ('service', b'original-service-identity')])
        for statement in ('SELECT * FROM truss.action_subject_binding',
                          "UPDATE truss.action_subject_binding SET subject_kind='human'",
                          'DELETE FROM truss.action_subject_binding',
                          "INSERT INTO truss.action_subject_binding SELECT * FROM truss.action_subject_binding"):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                data.execute(statement)
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        duplicate = bootstrap_action_subjects_in_transaction(host, tx,
            bindings=(('consumer', b'rebound-without-migration', 'human'),))
        self.assertIsInstance(duplicate, Error)
        host.detach(); self.admin.rollback()
        self.assertEqual(self.admin.execute("SELECT principal_identity FROM truss.action_subject_binding WHERE subject_kind='human'").fetchone(), (b'original-human-identity',))
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        original_snapshot = data.execute('SELECT pg_catalog.pg_current_snapshot()::text').fetchone()
        data.execute('SELECT truss.acquire_action_subject_cut()')
        self.admin.execute("SET lock_timeout='150ms'")
        with self.assertRaises(psycopg.errors.LockNotAvailable):
            self.admin.execute("UPDATE truss.action_subject_binding SET principal_identity=principal_identity")
        self.assertEqual(data.execute('SELECT pg_catalog.pg_current_snapshot()::text').fetchone(), original_snapshot)
        data.execute('ROLLBACK')
        self.admin.execute("SET lock_timeout='0'")
        # A later mapping change cannot be made current merely by taking a
        # lock after the RR snapshot. The row-lock witness must refuse.
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        data.execute('SELECT pg_catalog.pg_current_snapshot()')
        self.admin.execute("UPDATE truss.action_subject_binding SET principal_identity=%s WHERE subject_kind='human'", (b'new-original-human',))
        with self.assertRaises(psycopg.errors.SerializationFailure):
            data.execute('SELECT truss.acquire_action_subject_cut()')
        data.execute('ROLLBACK')

    def test_owned_action_role_cut_is_private_and_lives_until_outer_commit(self):
        data,old_host,assembly,old_tx=self.ready(document_ids=('adoc',))
        old_host.detach();data.commit()
        self.admin.execute('BEGIN')
        host=adopt_psycopg_host(self.admin);tx=host.adopt_transaction().value
        preparation=bootstrap_role_catalog_cut_issuer_in_transaction(host,tx,executor_role='consumer')
        self.assertIsInstance(preparation,Ok,repr(preparation))
        result=bootstrap_owned_action_role_cut_in_transaction(host,tx)
        self.assertIsInstance(result,Ok,repr(result))
        self.assertFalse(result.value.security_ready)
        owner=result.value.caller_oid;issuer=result.value.owner_oid
        with self.admin.cursor() as cursor:
            verify_role_catalog_cut_issuer_with_cursor(cursor,owner_oid=preparation.value.owner_oid,caller_oid=preparation.value.caller_oid)
        host.detach();self.admin.commit()
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            data.execute('SELECT truss.acquire_owned_action_role_catalog_cut()')
        owner_name=self.admin.execute('SELECT rolname FROM pg_catalog.pg_roles WHERE oid=%s',(owner,)).fetchone()[0]
        # Test-only composing entry point: proves owner-only native calling and
        # lock lifetime, not Subject admission or an action execution capability.
        self.admin.execute("""CREATE FUNCTION public.test_owned_action_cut() RETURNS void
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS
            'BEGIN PERFORM truss.acquire_owned_action_role_catalog_cut();END;'""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.test_owned_action_cut()')
        self.admin.execute(sql.SQL('ALTER FUNCTION public.test_owned_action_cut() OWNER TO {}').format(sql.Identifier(owner_name)))
        self.admin.execute('REVOKE ALL ON FUNCTION public.test_owned_action_cut() FROM PUBLIC')
        self.admin.execute('GRANT EXECUTE ON FUNCTION public.test_owned_action_cut() TO consumer')
        data.execute('BEGIN ISOLATION LEVEL READ COMMITTED')
        data.execute('SELECT public.test_owned_action_cut()')
        held=self.admin.execute("""SELECT relation::regclass::text FROM pg_catalog.pg_locks
            WHERE pid=%s AND mode='ShareLock' AND granted
            AND relation IN ('pg_catalog.pg_authid'::regclass,'pg_catalog.pg_auth_members'::regclass)
            ORDER BY relation::regclass::text""",(data.info.backend_pid,)).fetchall()
        self.assertEqual(held,[('pg_auth_members',),('pg_authid',)])
        self.admin.execute("SET lock_timeout='150ms'")
        try:
            with self.assertRaises(psycopg.errors.LockNotAvailable):
                self.admin.execute('ALTER ROLE consumer CONNECTION LIMIT -1')
        finally:self.admin.execute("SET lock_timeout='0'")
        data.execute('COMMIT')
        self.admin.execute('ALTER ROLE consumer CONNECTION LIMIT -1')
        with self.admin.cursor() as cursor:
            verify_owned_action_role_cut_with_cursor(cursor,issuer_owner_oid=issuer,action_owner_oid=owner)
        self.admin.execute('GRANT EXECUTE ON FUNCTION truss.acquire_owned_action_role_catalog_cut() TO consumer')
        try:
            with self.admin.cursor() as cursor:
                with self.assertRaises(ValueError):
                    verify_owned_action_role_cut_with_cursor(cursor,issuer_owner_oid=issuer,action_owner_oid=owner)
        finally:self.admin.execute('REVOKE ALL ON FUNCTION truss.acquire_owned_action_role_catalog_cut() FROM consumer')
        self.admin.execute('DROP FUNCTION public.test_owned_action_cut()')
