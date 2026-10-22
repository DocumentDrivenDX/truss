# SPDX-License-Identifier: MIT OR Apache-2.0
"""Managed platform ACLs injected by a native PostgreSQL event trigger.

The trigger is owned by the fixture superuser. Installation runs as a separate
database owner with CREATEROLE, so successful cases cannot disable the trigger
or manufacture a successful result in Python.
"""
from uuid import uuid4
from urllib.parse import urlparse, urlunparse

import psycopg
import unittest

from truss import (CatalogRuntimeConfiguration, InstallRefused, Ok,
                   Error, adopt_psycopg_host, create_reference_assembly)
from native_fixture import configure_shared_psycopg_fixture, connect as connect_native


class ManagedPlatformGrantsNativeTests(unittest.TestCase):
    """Use the suite's PostgreSQL 18.6 worker and a fresh database per case."""

    @classmethod
    def setUpClass(cls):
        cls.worker_fixture = None
        if not __import__('os').environ.get('TRUSS_NATIVE_WORKER'):
            raise RuntimeError('Managed grant tests require the owned PostgreSQL worker runner')
        configure_shared_psycopg_fixture(cls)

    def setUp(self):
        self.suffix = uuid4().hex[:10]
        self.database = 'managed_' + self.suffix
        self.installer_role = 'mg_installer_' + self.suffix
        self.allowed_role = 'mg_platform_' + self.suffix
        self.rogue_role = 'mg_rogue_' + self.suffix
        self.consumer_role = 'mg_consumer_' + self.suffix

        self.worker_admin = self.worker_fixture.admin
        self.roles_before = {row[0] for row in
                             self.worker_admin.run('SELECT rolname FROM pg_catalog.pg_roles')}
        self.addCleanup(self._cleanup_fixture)
        self.worker_admin.run(f'CREATE ROLE "{self.installer_role}" LOGIN CREATEROLE')
        self.worker_admin.run(f'CREATE ROLE "{self.allowed_role}" NOLOGIN')
        self.worker_admin.run(f'CREATE ROLE "{self.rogue_role}" NOLOGIN')
        self.worker_admin.run(f'CREATE DATABASE "{self.database}" OWNER "{self.installer_role}"')

        base_uri = self.worker_fixture.owner['uri']
        parsed = urlparse(base_uri)
        target_uri = urlunparse(parsed._replace(path='/' + self.database))
        self.admin = connect_native(target_uri, timeout=20)
        observer_params = psycopg.conninfo.conninfo_to_dict(target_uri)
        self.observer = psycopg.connect(**observer_params, autocommit=True,
                                        options='-c statement_timeout=10000')
        self._create_grant_trigger()

        installer_params = {**observer_params, 'user': self.installer_role}
        self.installer_params = installer_params
        self.connection = psycopg.connect(**installer_params, autocommit=True,
                                          options='-c statement_timeout=10000')
        self.connection.execute('BEGIN')
        self.host = adopt_psycopg_host(self.connection, statement_timeout_ms=10000,
                                       operation_timeout_ms=30000)
        self.tx = self.host.adopt_transaction().value
        self.assembly = create_reference_assembly(
            CatalogRuntimeConfiguration(), self.host).value

    def reconnect_installer(self):
        self.host.detach()
        if not self.connection.closed:
            self.connection.rollback()
            self.connection.close()
        self.connection = psycopg.connect(**self.installer_params, autocommit=True,
                                          options='-c statement_timeout=10000')
        self.connection.execute('BEGIN')
        self.host = adopt_psycopg_host(self.connection, statement_timeout_ms=10000,
                                       operation_timeout_ms=30000)
        self.tx = self.host.adopt_transaction().value
        self.assembly = create_reference_assembly(
            CatalogRuntimeConfiguration(), self.host).value

    def _create_grant_trigger(self):
        """Grant real object ACLs after Truss creates each supported object."""
        self.observer.execute('CREATE SEQUENCE public.managed_grant_event_count')
        self.observer.execute('CREATE SEQUENCE public.managed_grant_rogue_count')
        # Prime the nontransactional witnesses so the first event is visibly
        # greater than the baseline even though a fresh sequence starts at
        # last_value=1 with is_called=false.
        self.observer.execute("SELECT pg_catalog.nextval('public.managed_grant_event_count')")
        self.observer.execute("SELECT pg_catalog.nextval('public.managed_grant_rogue_count')")
        self.observer.execute('''
          CREATE FUNCTION public.managed_grant_fixture() RETURNS event_trigger
          LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
          DECLARE item record; target_name text; rogue_name text; rogue_class text;
          BEGIN
            target_name := current_setting('truss.fixture_grantee', true);
            rogue_name := current_setting('truss.fixture_rogue', true);
            rogue_class := current_setting('truss.fixture_rogue_class', true);
            IF current_setting('truss.fixture_count_events', true) = 'on' THEN
              PERFORM pg_catalog.nextval('public.managed_grant_event_count');
            END IF;
            IF target_name IS NOT NULL AND target_name <> '' THEN
            FOR item IN SELECT * FROM pg_catalog.pg_event_trigger_ddl_commands() LOOP
              IF item.object_type = 'schema' AND item.object_identity = 'truss' THEN
                EXECUTE pg_catalog.format('GRANT USAGE, CREATE ON SCHEMA %I TO %I WITH GRANT OPTION',
                    'truss', target_name);
                IF rogue_name IS NOT NULL AND rogue_name <> '' AND rogue_class = 'schema' THEN
                  EXECUTE pg_catalog.format('GRANT USAGE ON SCHEMA %I TO %I', 'truss', rogue_name);
                  IF current_setting('truss.fixture_count_rogues', true) = 'on' THEN
                    PERFORM pg_catalog.nextval('public.managed_grant_rogue_count');
                  END IF;
                END IF;
              ELSIF item.schema_name = 'truss' AND item.object_type IN ('table','sequence') THEN
                EXECUTE pg_catalog.format('GRANT ALL PRIVILEGES ON %s %s TO %I WITH GRANT OPTION',
                    upper(item.object_type), item.object_identity, target_name);
                IF rogue_name IS NOT NULL AND rogue_name <> '' AND rogue_class = 'relation' AND item.object_type='table' THEN
                  EXECUTE pg_catalog.format('GRANT SELECT ON %s %s TO %I',
                      upper(item.object_type), item.object_identity, rogue_name);
                  IF current_setting('truss.fixture_count_rogues', true) = 'on' THEN
                    PERFORM pg_catalog.nextval('public.managed_grant_rogue_count');
                  END IF;
                END IF;
                IF rogue_name IS NOT NULL AND rogue_name <> '' AND rogue_class = 'sequence' AND item.object_type='sequence' THEN
                  EXECUTE pg_catalog.format('GRANT SELECT ON SEQUENCE %s TO %I',
                      item.object_identity, rogue_name);
                  IF current_setting('truss.fixture_count_rogues', true) = 'on' THEN
                    PERFORM pg_catalog.nextval('public.managed_grant_rogue_count');
                  END IF;
                END IF;
                IF item.object_identity = 'truss.catalog_runtime_installation' THEN
                  EXECUTE pg_catalog.format('GRANT SELECT (singleton) ON TABLE %s TO %I WITH GRANT OPTION',
                      item.object_identity, target_name);
                  IF rogue_name IS NOT NULL AND rogue_name <> '' AND rogue_class = 'column' THEN
                    EXECUTE pg_catalog.format('GRANT SELECT (singleton) ON TABLE %s TO %I',
                        item.object_identity, rogue_name);
                    IF current_setting('truss.fixture_count_rogues', true) = 'on' THEN
                      PERFORM pg_catalog.nextval('public.managed_grant_rogue_count');
                    END IF;
                  END IF;
                END IF;
                IF item.object_type='table' AND rogue_name IS NOT NULL AND rogue_name <> ''
                   AND rogue_class='type' THEN
                  EXECUTE pg_catalog.format('GRANT USAGE ON TYPE %s TO %I',
                      item.object_identity, rogue_name);
                  IF current_setting('truss.fixture_count_rogues', true) = 'on' THEN
                    PERFORM pg_catalog.nextval('public.managed_grant_rogue_count');
                  END IF;
                END IF;
              ELSIF item.schema_name = 'truss' AND item.object_type = 'function' THEN
                EXECUTE pg_catalog.format('GRANT EXECUTE ON FUNCTION %s TO %I WITH GRANT OPTION',
                    item.object_identity, target_name);
                IF rogue_name IS NOT NULL AND rogue_name <> '' AND rogue_class = 'routine' THEN
                  EXECUTE pg_catalog.format('GRANT EXECUTE ON FUNCTION %s TO %I',
                      item.object_identity, rogue_name);
                  IF current_setting('truss.fixture_count_rogues', true) = 'on' THEN
                    PERFORM pg_catalog.nextval('public.managed_grant_rogue_count');
                  END IF;
                END IF;
              ELSIF item.schema_name = 'truss' AND item.object_type = 'type' THEN
                EXECUTE pg_catalog.format('GRANT USAGE ON TYPE %s TO %I WITH GRANT OPTION',
                    item.object_identity, target_name);
                IF rogue_name IS NOT NULL AND rogue_name <> '' AND rogue_class = 'type' THEN
                  EXECUTE pg_catalog.format('GRANT USAGE ON TYPE %s TO %I',
                      item.object_identity, rogue_name);
                  IF current_setting('truss.fixture_count_rogues', true) = 'on' THEN
                    PERFORM pg_catalog.nextval('public.managed_grant_rogue_count');
                  END IF;
                END IF;
              END IF;
            END LOOP;
            END IF;
          END $$
        ''')
        self.observer.execute('''CREATE EVENT TRIGGER managed_grant_fixture
          ON ddl_command_end EXECUTE FUNCTION public.managed_grant_fixture()''')
        self.observer.execute('''
          CREATE FUNCTION public.managed_late_grant_fixture() RETURNS event_trigger
          LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
          DECLARE target_name text; item record; mode_name text; role_name text;
          BEGIN
            target_name := current_setting('truss.fixture_late_rogue', true);
            mode_name := current_setting('truss.fixture_late_mode', true);
            role_name := current_setting('truss.fixture_late_role', true);
            IF (target_name IS NOT NULL AND target_name <> '')
               OR (mode_name IS NOT NULL AND mode_name <> '') THEN
              FOR item IN SELECT * FROM pg_catalog.pg_event_trigger_ddl_commands() LOOP
                IF item.object_type = 'schema' AND item.object_identity = 'truss'
                   AND pg_catalog.obj_description('truss'::pg_catalog.regnamespace, 'pg_namespace') =
                     'Truss installed runtime: exact active release and layout from truss.runtime_current_installation()' THEN
                  IF target_name IS NOT NULL AND target_name <> '' THEN
                    EXECUTE pg_catalog.format('GRANT USAGE ON SCHEMA %I TO %I', 'truss', target_name);
                    IF current_setting('truss.fixture_count_rogues', true) = 'on' THEN
                      PERFORM pg_catalog.nextval('public.managed_grant_rogue_count');
                    END IF;
                  END IF;
                  IF mode_name = 'missing_client' THEN
                    EXECUTE pg_catalog.format('REVOKE EXECUTE ON FUNCTION truss.catalog_status() FROM %I', role_name);
                  ELSIF mode_name = 'missing_public' THEN
                    EXECUTE 'REVOKE EXECUTE ON FUNCTION truss.person_accepted_document(text,integer,text,text) FROM PUBLIC';
                  ELSIF mode_name = 'grant_option' THEN
                    EXECUTE pg_catalog.format('GRANT EXECUTE ON FUNCTION truss.catalog_status() TO %I WITH GRANT OPTION', role_name);
                  END IF;
                END IF;
              END LOOP;
            END IF;
          END $$
        ''')
        self.observer.execute('''CREATE EVENT TRIGGER managed_late_grant_fixture
          ON ddl_command_end WHEN TAG IN ('COMMENT')
          EXECUTE FUNCTION public.managed_late_grant_fixture()''')

    def tearDown(self):
        self._cleanup_fixture()

    def _cleanup_fixture(self):
        errors = []
        host = getattr(self, 'host', None)
        if host is not None:
            try:
                host.detach()
            except Exception as error:
                errors.append(error)
            self.host = None
        for name in ('connection', 'observer', 'admin'):
            connection = getattr(self, name, None)
            if connection is None:
                continue
            if not getattr(connection, 'closed', False):
                try:
                    if isinstance(connection, psycopg.Connection):
                        connection.rollback()
                except Exception as error:
                    errors.append(error)
                try:
                    connection.close()
                except Exception as error:
                    errors.append(error)
            setattr(self, name, None)
        worker_admin = getattr(self, 'worker_admin', None)
        if worker_admin is None:
            if errors:
                raise RuntimeError('Managed-grant fixture cleanup failed') from errors[0]
            return
        database = getattr(self, 'database', None)
        if database is not None:
            try:
                exists = worker_admin.run(
                    'SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_database WHERE datname=:database)',
                    database=database)[0][0]
                if exists:
                    worker_admin.run(f'DROP DATABASE "{database}" WITH (FORCE)')
            except Exception as error:
                errors.append(error)
        roles_before = getattr(self, 'roles_before', set())
        try:
            added_roles = {row[0] for row in
                           worker_admin.run('SELECT rolname FROM pg_catalog.pg_roles')} - roles_before
            def ident(name):
                return '"' + name.replace('"', '""') + '"'
            memberships = worker_admin.run('''SELECT granted.rolname,member.rolname
                FROM pg_catalog.pg_auth_members membership
                JOIN pg_catalog.pg_roles granted ON granted.oid=membership.roleid
                JOIN pg_catalog.pg_roles member ON member.oid=membership.member''')
            for granted, member in memberships:
                if granted in added_roles or member in added_roles:
                    worker_admin.run(f'REVOKE {ident(granted)} FROM {ident(member)} CASCADE')
            for role in sorted(added_roles):
                try:
                    worker_admin.run(f'DROP OWNED BY {ident(role)}')
                except Exception as error:
                    errors.append(error)
            for role in sorted(added_roles):
                try:
                    worker_admin.run(f'DROP ROLE {ident(role)}')
                except Exception as error:
                    errors.append(error)
        except Exception as error:
            errors.append(error)
        if errors:
            raise RuntimeError('Managed-grant fixture cleanup failed') from errors[0]

    def install(self, *, tolerated=(), rogue_class=None, late_rogue=False,
                late_mode=None, registrar_role=None, count_events=False,
                count_rogues=False):
        self.connection.execute("SELECT pg_catalog.set_config('truss.fixture_grantee', %s, true)",
                                (self.allowed_role,))
        self.connection.execute("SELECT pg_catalog.set_config('truss.fixture_rogue', %s, true)",
                                (self.rogue_role if rogue_class else '',))
        self.connection.execute("SELECT pg_catalog.set_config('truss.fixture_rogue_class', %s, true)",
                                (rogue_class or '',))
        self.connection.execute("SELECT pg_catalog.set_config('truss.fixture_late_rogue', %s, true)",
                                (self.rogue_role if late_rogue else '',))
        self.connection.execute("SELECT pg_catalog.set_config('truss.fixture_late_mode', %s, true)",
                                (late_mode or '',))
        self.connection.execute("SELECT pg_catalog.set_config('truss.fixture_late_role', %s, true)",
                                (registrar_role or '',))
        self.connection.execute("SELECT pg_catalog.set_config('truss.fixture_count_events', %s, true)",
                                ('on' if count_events else 'off',))
        self.connection.execute("SELECT pg_catalog.set_config('truss.fixture_count_rogues', %s, true)",
                                ('on' if count_rogues else 'off',))
        return self.assembly.install_in_transaction(
            self.tx, tolerated_grantees=tuple(tolerated), registrar_role=registrar_role)

    def rogue_count(self):
        return self.observer.execute(
            'SELECT last_value FROM public.managed_grant_rogue_count').fetchone()[0]

    def event_count(self):
        return self.observer.execute(
            'SELECT last_value FROM public.managed_grant_event_count').fetchone()[0]

    def test_empty_policy_names_trigger_grantee_and_rolls_back_prior_install_work(self):
        self.connection.execute('CREATE TEMP TABLE caller_work(value text)')
        self.connection.execute("INSERT INTO caller_work VALUES ('keep')")
        before_event_count = self.event_count()

        result = self.install(count_events=True)

        self.assertEqual(result, Ok(InstallRefused(
            code='third_party_grant', role_name=self.allowed_role,
            object_class='schema', phase='pre_ownership')))
        self.assertEqual(self.connection.execute('SELECT value FROM caller_work').fetchall(),
                         [('keep',)])
        self.assertEqual(self.connection.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')"
        ).fetchone(), (False,))
        self.assertEqual(self.observer.execute(
            'SELECT count(*) FROM pg_catalog.pg_roles WHERE rolname LIKE %s',
            ('truss_owner_%',)).fetchone()[0],
            sum(name.startswith('truss_owner_') for name in self.roles_before))
        self.assertGreater(self.event_count(), before_event_count)

    def test_trigger_injects_schema_relation_sequence_routine_type_and_column_grants(self):
        self.connection.execute("SELECT pg_catalog.set_config('truss.fixture_grantee', %s, true)",
                                (self.allowed_role,))
        self.connection.execute('CREATE SCHEMA truss')
        self.connection.execute('CREATE TABLE truss.fixture_probe(singleton boolean)')
        self.connection.execute('CREATE SEQUENCE truss.fixture_sequence')
        self.connection.execute("CREATE TYPE truss.fixture_kind AS ENUM ('one')")
        self.connection.execute("CREATE FUNCTION truss.fixture_routine() RETURNS integer LANGUAGE sql AS 'SELECT 1'")
        self.host.detach()
        self.connection.commit()

        self.assertTrue(self.observer.execute(
            'SELECT pg_catalog.has_schema_privilege(%s, %s, %s)',
            (self.allowed_role, 'truss', 'CREATE')).fetchone()[0])
        self.assertTrue(self.observer.execute(
            'SELECT pg_catalog.has_table_privilege(%s, %s, %s)',
            (self.allowed_role, 'truss.fixture_probe', 'SELECT')).fetchone()[0])
        self.assertTrue(self.observer.execute(
            'SELECT pg_catalog.has_sequence_privilege(%s, %s, %s)',
            (self.allowed_role, 'truss.fixture_sequence', 'USAGE')).fetchone()[0])
        self.assertTrue(self.observer.execute(
            'SELECT pg_catalog.has_function_privilege(%s, %s, %s)',
            (self.allowed_role, 'truss.fixture_routine()', 'EXECUTE')).fetchone()[0])
        self.assertTrue(self.observer.execute(
            'SELECT pg_catalog.has_type_privilege(%s, %s, %s)',
            (self.allowed_role, 'truss.fixture_kind', 'USAGE')).fetchone()[0])
        self.assertTrue(self.observer.execute(
            'SELECT pg_catalog.has_column_privilege(%s, %s, %s, %s)',
            (self.allowed_role, 'truss.fixture_probe', 'singleton', 'SELECT')).fetchone()[0])
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.connection.execute('ALTER EVENT TRIGGER managed_grant_fixture DISABLE')

    def test_tolerated_grants_remain_native_and_policy_records_resolved_identity(self):
        result = self.install(tolerated=(self.allowed_role,))
        self.assertIsInstance(result, Ok, repr(result))
        self.assertNotIsInstance(result.value, InstallRefused, repr(result))
        self.host.detach()
        self.connection.commit()

        # Observe PostgreSQL ACLs independently of Truss' retained evidence.
        self.assertTrue(self.observer.execute(
            'SELECT pg_catalog.has_schema_privilege(%s, %s, %s)',
            (self.allowed_role, 'truss', 'USAGE')).fetchone()[0])
        self.assertTrue(self.observer.execute(
            'SELECT pg_catalog.has_schema_privilege(%s, %s, %s)',
            (self.allowed_role, 'truss', 'CREATE')).fetchone()[0])
        self.assertTrue(self.observer.execute(
            'SELECT pg_catalog.has_table_privilege(%s, %s, %s)',
            (self.allowed_role, 'truss.catalog_runtime_installation', 'SELECT')).fetchone()[0])
        self.assertTrue(self.observer.execute('''
          SELECT bool_and(is_grantable) FROM pg_catalog.aclexplode(
            (SELECT nspacl FROM pg_catalog.pg_namespace WHERE nspname='truss'))
          WHERE grantee=(SELECT oid FROM pg_catalog.pg_roles WHERE rolname=%s)
        ''', (self.allowed_role,)).fetchone()[0])

        managed = self.observer.execute(
            'SELECT managed_grants FROM truss.catalog_runtime_installation WHERE singleton'
        ).fetchone()[0]
        expected_oid = self.observer.execute(
            'SELECT oid FROM pg_catalog.pg_roles WHERE rolname=%s',
            (self.allowed_role,)).fetchone()[0]
        self.assertEqual(managed['interfaceVersion'], 'truss-managed-grants/0.1')
        self.assertEqual(managed['roles'], [{'name': self.allowed_role, 'oid': expected_oid}])
        self.assertTrue(any(row['class'] == 'schema' and row['phase'] == 'pre_ownership'
                            and row['granteeOid'] == expected_oid
                            and row['privilege'] == 'CREATE' and row['grantOption']
                            for row in managed['observations']))
        self.assertTrue(any(row['class'] == 'sequence' and row['phase'] == 'pre_ownership'
                            and row['granteeOid'] == expected_oid
                            and row['grantOption']
                            for row in managed['observations']))
        self.assertTrue(self.observer.execute('''
          SELECT evtenabled='O' FROM pg_catalog.pg_event_trigger
          WHERE evtname='managed_grant_fixture'
        ''').fetchone()[0])

    def test_trusted_installer_membership_in_tolerated_role_keeps_admin_operations(self):
        self.worker_admin.run(
            f'GRANT "{self.allowed_role}" TO "{self.installer_role}" WITH INHERIT TRUE, SET FALSE')
        installed = self.install(tolerated=(self.allowed_role,))
        attempt = getattr(self.host._custody, 'last_attempt', None)
        self.assertIsInstance(installed, Ok,
                              f'{installed!r}; native_attempt={getattr(attempt, "error", None)!r}')
        self.assertNotIsInstance(installed.value, InstallRefused, repr(installed))
        self.assertTrue(self.observer.execute(
            'SELECT pg_catalog.pg_has_role(%s,%s,\'MEMBER\')',
            (self.installer_role, self.allowed_role)).fetchone()[0])
        status = self.assembly.status_in_transaction(self.tx)
        attempt = getattr(self.host._custody, 'last_attempt', None)
        self.assertIsInstance(status, Ok,
                              f'{status!r}; native_attempt={getattr(attempt, "error", None)!r}')
        self.assertTrue(status.value.installed)
        recovery = self.assembly.admin_install_recovery_in_transaction(self.tx)
        self.assertIsInstance(recovery, Ok, repr(recovery))

    def test_reconnect_cannot_widen_stored_policy_and_native_role_replacement_refuses(self):
        result = self.install(tolerated=(self.allowed_role,))
        self.assertIsInstance(result, Ok, repr(result))
        self.assertNotIsInstance(result.value, InstallRefused, repr(result))
        self.host.detach()
        self.connection.commit()
        original = self.observer.execute(
            'SELECT managed_grants FROM truss.catalog_runtime_installation WHERE singleton'
        ).fetchone()[0]

        self.reconnect_installer()
        status = self.assembly.status_in_transaction(self.tx)
        self.assertIsInstance(status, Ok, repr(status))
        self.assertTrue(status.value.installed)
        widened = self.assembly.install_in_transaction(
            self.tx, tolerated_grantees=(self.rogue_role,))
        self.assertEqual(widened, Ok(InstallRefused(code='already_installed')))
        self.host.detach()
        self.connection.rollback()
        self.assertEqual(self.observer.execute(
            'SELECT managed_grants FROM truss.catalog_runtime_installation WHERE singleton'
        ).fetchone()[0], original)

        renamed = self.allowed_role + '_renamed'
        self.observer.execute(psycopg.sql.SQL('ALTER ROLE {} RENAME TO {}').format(
            psycopg.sql.Identifier(self.allowed_role), psycopg.sql.Identifier(renamed)))
        self.observer.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(
            psycopg.sql.Identifier(self.allowed_role)))
        self.reconnect_installer()
        from truss import Error
        status = self.assembly.status_in_transaction(self.tx)
        self.assertIsInstance(status, Error)
        self.assertEqual(status.error.sql_state, '55000')
        drifted = self.assembly.install_in_transaction(
            self.tx, tolerated_grantees=(self.allowed_role,))
        self.assertEqual(drifted, Ok(InstallRefused(code='incompatible')))

    def test_ordinary_client_inheriting_platform_role_is_refused_as_raw_access_leak(self):
        installed = self.install(tolerated=(self.allowed_role,))
        self.assertIsInstance(installed, Ok, repr(installed))
        self.assertNotIsInstance(installed.value, InstallRefused, repr(installed))
        self.host.detach()
        self.connection.commit()
        self.observer.execute(psycopg.sql.SQL('CREATE ROLE {} LOGIN').format(
            psycopg.sql.Identifier(self.consumer_role)))
        self.observer.execute(psycopg.sql.SQL('GRANT {} TO {} WITH SET FALSE').format(
            psycopg.sql.Identifier(installed.value.registrar_role),
            psycopg.sql.Identifier(self.consumer_role)))
        self.observer.execute(psycopg.sql.SQL('GRANT {} TO {} WITH INHERIT TRUE, SET FALSE').format(
            psycopg.sql.Identifier(self.allowed_role), psycopg.sql.Identifier(self.consumer_role)))
        has_raw_access = self.observer.execute(
            'SELECT pg_catalog.has_table_privilege(%s,\'truss.object\',\'SELECT\')',
            (self.consumer_role,)).fetchone()[0]
        self.assertTrue(has_raw_access)

        client_params = {**self.installer_params, 'user': self.consumer_role}
        client = psycopg.connect(**client_params, autocommit=True,
                                 options='-c statement_timeout=10000')
        self.addCleanup(client.close)
        client.execute('BEGIN')
        client_host = adopt_psycopg_host(client, statement_timeout_ms=10000,
                                         operation_timeout_ms=30000)
        client_assembly = create_reference_assembly(
            CatalogRuntimeConfiguration(), client_host).value
        status = client_assembly.status_in_transaction(
            client_host.adopt_transaction().value)
        self.assertIsInstance(status, Error,
                              f'{status!r}; native_attempt={client_host._custody.last_attempt.error!r}')
        self.assertEqual(status.error.sql_state, 'P1403',
                         f'native_attempt={client_host._custody.last_attempt.error!r}')
        client_host.detach()

    def test_protected_security_activation_refuses_before_any_native_ddl(self):
        installed = self.install(tolerated=(self.allowed_role,))
        self.assertIsInstance(installed, Ok, repr(installed))
        self.assertNotIsInstance(installed.value, InstallRefused, repr(installed))
        self.host.detach()
        self.connection.commit()

        self.observer.execute('BEGIN')
        protected_host = adopt_psycopg_host(self.observer, statement_timeout_ms=10000,
                                             operation_timeout_ms=30000)
        protected_tx = protected_host.adopt_transaction().value
        installation_id = installed.value.installation_id.encode('utf8')
        before_sequence = self.observer.execute(
            'SELECT last_value FROM public.managed_grant_event_count').fetchone()[0]
        before_acl = self.observer.execute(
            "SELECT nspacl::text FROM pg_catalog.pg_namespace WHERE nspname='truss'"
        ).fetchone()[0]
        self.observer.execute("SELECT pg_catalog.set_config('truss.fixture_count_events', 'on', true)")

        from truss._security_home_installation import bootstrap_security_homes_in_transaction
        result = bootstrap_security_homes_in_transaction(
            protected_host, protected_tx, installation_identity=installation_id,
            authored_profile=b'managed-grants-protected-profile', max_retained=32)

        self.assertIsInstance(result, Error, repr(result))
        self.assertEqual(result.error.message,
                         'Protected activation is incompatible with the installed managed-grant policy')
        self.assertEqual(result.error.catalog_code, 'unsupported_profile')
        self.assertEqual(self.observer.execute(
            'SELECT last_value FROM public.managed_grant_event_count').fetchone()[0],
            before_sequence)
        self.assertEqual(self.observer.execute(
            "SELECT nspacl::text FROM pg_catalog.pg_namespace WHERE nspname='truss'"
        ).fetchone()[0], before_acl)
        self.assertEqual(self.observer.execute('''
          SELECT count(*) FROM pg_catalog.pg_class c
          JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
          WHERE n.nspname='truss' AND c.relname IN
            ('policy_generation_guard','policy_publication_claim','policy_publication_capacity')
        ''').fetchone(), (0,))
        protected_host.detach()
        self.observer.rollback()

    def test_tolerated_install_registration_module_write_journal_feed_and_ack(self):
        import json
        import os
        from truss import (CatalogDocument, ModuleAccessGrant, FeedPage,
                           FeedAcknowledged)
        from truss.contracts import MapValue, TextValue
        from truss.groups import AuthoredValue, CreateObject, GroupSuccess, RootlessOwnership
        from test_catalog_relational_support import relational_document

        installed = self.install(tolerated=(self.allowed_role,))
        self.assertIsInstance(installed, Ok, repr(installed))
        self.assertNotIsInstance(installed.value, InstallRefused, repr(installed))
        self.host.detach()
        self.connection.commit()

        reader_role = 'mg_reader_' + self.suffix
        writer_role = 'mg_writer_' + self.suffix
        self.observer.execute(psycopg.sql.SQL('CREATE ROLE {} LOGIN').format(
            psycopg.sql.Identifier(self.consumer_role)))
        for role in (reader_role, writer_role):
            self.observer.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(
                psycopg.sql.Identifier(role)))
        self.observer.execute(psycopg.sql.SQL('GRANT {} TO {} WITH SET FALSE').format(
            psycopg.sql.Identifier(installed.value.registrar_role),
            psycopg.sql.Identifier(self.consumer_role)))

        consumer_params = {**self.installer_params, 'user': self.consumer_role}
        consumer = psycopg.connect(**consumer_params, autocommit=True,
                                   options='-c statement_timeout=10000')
        consumer.execute('BEGIN')
        consumer_host = adopt_psycopg_host(consumer, statement_timeout_ms=10000,
                                           operation_timeout_ms=30000)
        consumer_tx = consumer_host.adopt_transaction().value
        consumer_assembly = create_reference_assembly(
            CatalogRuntimeConfiguration(), consumer_host).value
        documents = []
        for identity in ('adoc', 'zdoc'):
            source = relational_document()
            source['id'] = identity
            documents.append(CatalogDocument(identity, 'r1',
                json.dumps(source, indent=2, ensure_ascii=False).encode('utf8')))
        prepared = consumer_assembly.prepare_catalog(
            tuple(documents), source_version=json.loads(documents[0].content)['umf'],
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        accepted = consumer_assembly.accept_in_transaction(
            consumer_tx, prepared, request_key='managed-platform-model')
        self.assertIsInstance(accepted, Ok, repr(accepted))
        view = consumer_assembly.catalog_view_in_transaction(
            consumer_tx, consumer_assembly.catalog_view_request()).value.view
        definitions = {(item.reference.owner.document_id, item.reference.authored_identity): item.reference
                       for item in view.definitions if item.reference.kind == 'type'}
        consumer_host.detach()
        consumer.commit()
        consumer.close()

        self.observer.execute('BEGIN')
        admin_host = adopt_psycopg_host(self.observer, statement_timeout_ms=10000,
                                        operation_timeout_ms=30000)
        admin_tx = admin_host.adopt_transaction().value
        admin_assembly = create_reference_assembly(
            CatalogRuntimeConfiguration(), admin_host).value
        configured = admin_assembly.configure_module_access_in_transaction(admin_tx,
            tuple(ModuleAccessGrant(document_id, 'm', reader_role, writer_role)
                  for document_id in ('adoc', 'zdoc')))
        self.assertIsInstance(configured, Ok, repr(configured))
        enrolled = admin_assembly.register_feed_consumer_in_transaction(
            admin_tx, consumer_id='managed-platform-feed', reader_role=reader_role)
        self.assertIsInstance(enrolled, Ok, repr(enrolled))
        admin_host.detach()
        self.observer.commit()
        self.observer.execute(psycopg.sql.SQL('GRANT {}, {} TO {} WITH SET FALSE').format(
            psycopg.sql.Identifier(reader_role), psycopg.sql.Identifier(writer_role),
            psycopg.sql.Identifier(self.consumer_role)))

        consumer = psycopg.connect(**consumer_params, autocommit=True,
                                   options='-c statement_timeout=10000')
        consumer.execute('BEGIN')
        consumer_host = adopt_psycopg_host(consumer, statement_timeout_ms=10000,
                                           operation_timeout_ms=30000)
        consumer_tx = consumer_host.adopt_transaction().value
        consumer_assembly = create_reference_assembly(
            CatalogRuntimeConfiguration(), consumer_host).value
        create = CreateObject(type_definition_pin=definitions[('adoc', 'A')].definition_pin,
            values=(AuthoredValue(name='A-label', value=TextValue(kind='string', text='platform-write')),
                    AuthoredValue(name='A-value', value=TextValue(kind='string', text='retained'))),
            ownership=RootlessOwnership(), alias='managed-object')
        context = consumer_assembly.group_context_in_transaction(consumer_tx).value
        applied = consumer_assembly.apply_in_transaction(consumer_tx,
            context.input((create,), MapValue(entries=())), context.request('managed-platform-write'),
            documents=tuple(item.document for item in prepared.documents),
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        self.assertIsInstance(applied, Ok, repr(applied))
        self.assertIsInstance(applied.value, GroupSuccess, repr(applied.value))
        consumer_host.detach()
        consumer.commit()
        consumer.close()
        self.assertEqual(self.observer.execute('SELECT count(*) FROM truss.journal').fetchone(), (1,))

        consumer = psycopg.connect(**consumer_params, autocommit=True,
                                   options='-c statement_timeout=10000')
        consumer.execute('BEGIN')
        consumer_host = adopt_psycopg_host(consumer, statement_timeout_ms=10000,
                                           operation_timeout_ms=30000)
        consumer_tx = consumer_host.adopt_transaction().value
        consumer_assembly = create_reference_assembly(
            CatalogRuntimeConfiguration(), consumer_host).value
        feed = consumer_assembly.feed(consumer_assembly.feed_selection).capability
        page = feed.read_feed_in_transaction(
            consumer_tx, consumer_id='managed-platform-feed')
        self.assertIsInstance(page, Ok, repr(page))
        self.assertIsInstance(page.value, FeedPage,
                              f'{page.value!r}; native_attempt={consumer_host._custody.last_attempt.error!r}')
        acknowledged = feed.acknowledge_feed_in_transaction(consumer_tx, page.value)
        self.assertIsInstance(acknowledged, Ok, repr(acknowledged))
        self.assertIsInstance(acknowledged.value, FeedAcknowledged, repr(acknowledged.value))
        consumer_host.detach()
        consumer.commit()
        consumer.close()

    def test_one_unlisted_grantee_refuses_and_leaves_caller_state_usable(self):
        self.connection.execute('CREATE TEMP TABLE caller_work(value text)')
        self.connection.execute("INSERT INTO caller_work VALUES ('before')")
        before_rogue_count = self.rogue_count()

        result = self.install(tolerated=(self.allowed_role,), rogue_class='schema',
                              count_rogues=True)

        self.assertEqual(result, Ok(InstallRefused(
            code='third_party_grant', role_name=self.rogue_role,
            object_class='schema', phase='pre_ownership')))
        self.assertEqual(self.connection.execute('SELECT value FROM caller_work').fetchall(),
                         [('before',)])
        self.assertEqual(self.connection.execute('SELECT 42').fetchone(), (42,))
        self.assertEqual(self.observer.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')"
        ).fetchone(), (False,))
        self.assertGreater(self.rogue_count(), before_rogue_count)

    def test_late_event_grant_refusal_is_contained_and_stale_handle_stays_invalid(self):
        self.connection.execute('CREATE TEMP TABLE caller_work(value text)')
        self.connection.execute("INSERT INTO caller_work VALUES ('before')")
        before_rogue_count = self.rogue_count()

        result = self.install(tolerated=(self.allowed_role,), late_rogue=True,
                              count_rogues=True)

        self.assertEqual(result, Ok(InstallRefused(
            code='third_party_grant', role_name=self.rogue_role,
            object_class='schema', phase='post_installation')))
        self.assertEqual(self.connection.execute('SELECT value FROM caller_work').fetchall(),
                         [('before',)])
        self.connection.commit()
        stale = self.assembly.install_in_transaction(
            self.tx, tolerated_grantees=(self.allowed_role,))
        self.assertIsInstance(stale, Error)
        self.assertEqual(stale.error.code, 'invalid_transaction')
        self.host.detach()
        self.assertEqual(self.observer.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')"
        ).fetchone(), (False,))
        self.assertGreater(self.rogue_count(), before_rogue_count)

    def test_late_declared_acl_mutations_refuse_contained(self):
        for mode in ('missing_client', 'missing_public', 'grant_option'):
            with self.subTest(mode=mode):
                self.host.detach()
                self.connection.rollback()
                self.connection.execute('BEGIN')
                self.host = adopt_psycopg_host(self.connection, statement_timeout_ms=10000,
                                               operation_timeout_ms=30000)
                self.tx = self.host.adopt_transaction().value
                self.assembly = create_reference_assembly(
                    CatalogRuntimeConfiguration(), self.host).value
                self.connection.execute('CREATE TEMP TABLE caller_work(value text)')
                self.connection.execute("INSERT INTO caller_work VALUES ('before')")
                registrar = 'mg_registrar_' + self.suffix
                result = self.install(tolerated=(self.allowed_role,), late_mode=mode,
                                      registrar_role=registrar)
                self.assertIsInstance(result, Error, repr(result))
                self.assertEqual(result.error.code, 'invalid_transaction')
                self.assertEqual(self.connection.execute(
                    'SELECT value FROM caller_work').fetchall(), [('before',)])
                self.assertEqual(self.connection.execute('SELECT 42').fetchone(), (42,))
                self.assertEqual(self.observer.execute(
                    "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')"
                ).fetchone(), (False,))

    def test_unlisted_object_grantees_report_the_native_object_class(self):
        for object_class in ('relation', 'sequence', 'routine', 'type', 'column'):
            with self.subTest(object_class=object_class):
                # Every refused install must be rolled back before the next independent
                # trigger scenario; otherwise the prior refusal intentionally leaves
                # its transaction usable and the next call sees an installed layout.
                self.host.detach()
                self.connection.rollback()
                self.connection.execute('BEGIN')
                self.host = adopt_psycopg_host(self.connection, statement_timeout_ms=10000,
                                               operation_timeout_ms=30000)
                self.tx = self.host.adopt_transaction().value
                self.assembly = create_reference_assembly(
                    CatalogRuntimeConfiguration(), self.host).value
                before_rogue_count = self.rogue_count()
                result = self.install(tolerated=(self.allowed_role,), rogue_class=object_class,
                                      count_rogues=True)
                self.assertEqual(result, Ok(InstallRefused(
                    code='third_party_grant', role_name=self.rogue_role,
                    object_class=object_class, phase='pre_ownership')))
                self.assertEqual(self.observer.execute(
                    "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')"
                ).fetchone(), (False,))
                self.assertGreater(self.rogue_count(), before_rogue_count)

    def test_invalid_bounded_names_are_rejected_before_database_effects(self):
        invalid = (
            (self.allowed_role, self.allowed_role),
            ('PUBLIC',),
            ('bad\x00name',),
            ('x' * 64,),
            (self.installer_role,),
            tuple('managed_' + str(index) for index in range(33)),
        )
        for names in invalid:
            with self.subTest(names=names):
                result = self.assembly.install_in_transaction(
                    self.tx, tolerated_grantees=names)
                self.assertEqual(result, Ok(InstallRefused(code='invalid_roles')))
                self.assertEqual(self.observer.execute(
                    "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')"
                ).fetchone(), (False,))


if __name__ == '__main__':
    import unittest
    unittest.main()
