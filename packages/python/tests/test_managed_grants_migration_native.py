# SPDX-License-Identifier: MIT OR Apache-2.0
"""Migration-tool verification of persisted managed grants on the current target."""
from uuid import uuid4
import unittest

import psycopg

from truss import (CatalogRuntimeConfiguration, InstallRefused, Ok,
                   adopt_psycopg_host, create_reference_assembly)
from truss.migrations import RuntimeMigrations
from truss.recovery_registry import HostRecoveryRegistry
from native_fixture import DatabaseFixture, WorkerCluster, connect as connect_native


class ManagedGrantsMigrationNativeTests(unittest.TestCase):
    def test_current_status_accepts_only_the_saved_native_policy(self):
        suffix = uuid4().hex[:10]
        allowed = 'mgm_platform_' + suffix
        rogue = 'mgm_rogue_' + suffix

        with WorkerCluster() as worker:
            fixture = DatabaseFixture(worker.root)
            connection = host = None
            try:
                uri = fixture.get_uri()
                fixture.admin.run(f'ALTER ROLE "{fixture.role}" LOGIN CREATEROLE')
                fixture.admin.run(f'CREATE ROLE "{allowed}" NOLOGIN')
                fixture.admin.run(f'CREATE ROLE "{rogue}" NOLOGIN')
                observer = connect_native(uri, timeout=20)
                try:
                    observer.run('''CREATE FUNCTION public.managed_grants_column_fixture()
                      RETURNS event_trigger LANGUAGE plpgsql SECURITY DEFINER
                      SET search_path=pg_catalog AS $$
                      DECLARE item record; grantee text;
                      BEGIN
                        grantee := current_setting('truss.fixture_grantee', true);
                        IF grantee IS NULL OR grantee = '' THEN RETURN; END IF;
                        FOR item IN SELECT * FROM pg_catalog.pg_event_trigger_ddl_commands() LOOP
                          IF item.schema_name='truss'
                             AND item.object_identity='truss.catalog_runtime_installation'
                             AND EXISTS (
                               SELECT 1 FROM pg_catalog.pg_attribute a
                               JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
                               JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
                               WHERE n.nspname='truss' AND c.relname='catalog_runtime_installation'
                                 AND a.attname='managed_grants' AND a.attnum>0 AND NOT a.attisdropped
                             ) THEN
                            EXECUTE pg_catalog.format(
                              'GRANT SELECT (managed_grants) ON TABLE truss.catalog_runtime_installation TO %I WITH GRANT OPTION',
                              grantee);
                          END IF;
                        END LOOP;
                      END $$''')
                    observer.run('''CREATE EVENT TRIGGER managed_grants_column_fixture
                      ON ddl_command_end EXECUTE FUNCTION public.managed_grants_column_fixture()''')
                finally:
                    observer.close()

                parsed = psycopg.conninfo.conninfo_to_dict(uri)
                installer_params = {**parsed, 'user': fixture.role}
                connection = psycopg.connect(**installer_params, autocommit=True,
                                             options='-c statement_timeout=10000')
                connection.execute('BEGIN')
                connection.execute("SELECT pg_catalog.set_config('truss.fixture_grantee', %s, true)",
                                   (allowed,))
                host = adopt_psycopg_host(connection, statement_timeout_ms=10000,
                                          operation_timeout_ms=30000)
                tx = host.adopt_transaction().value
                assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
                installed = assembly.install_in_transaction(tx, tolerated_grantees=(allowed,))
                self.assertIsInstance(installed, Ok, repr(installed))
                self.assertNotIsInstance(installed.value, InstallRefused, repr(installed))
                host.detach()
                connection.commit()
                connection.close()
                connection = host = None

                migrations = RuntimeMigrations(
                    lambda: psycopg.connect(**parsed, autocommit=True,
                                            options='-c statement_timeout=10000'),
                    HostRecoveryRegistry(fixture.root / ('managed-grants-' + suffix + '.sqlite')))
                current = migrations.status()
                self.assertEqual(current['state'], 'current')
                self.assertEqual(migrations.verify(), current)
                with self.assertRaisesRegex(ValueError, 'Already at latest'):
                    migrations.prepare()

                with psycopg.connect(**parsed, autocommit=True) as admin:
                    policy, registrar = admin.execute('''
                      SELECT i.managed_grants, r.rolname
                      FROM truss.catalog_runtime_installation i
                      JOIN pg_catalog.pg_roles r ON r.oid=i.registrar_oid
                      WHERE i.singleton
                    ''').fetchone()
                    allowed_oid = admin.execute(
                        'SELECT oid FROM pg_catalog.pg_roles WHERE rolname=%s', (allowed,)).fetchone()[0]
                    self.assertEqual(policy['roles'], [{'name': allowed, 'oid': allowed_oid}])
                    self.assertTrue(any(row['class'] == 'column' and row['phase'] == 'post_installation'
                                        and row['granteeOid'] == allowed_oid
                                        and row['privilege'] == 'SELECT' and row['grantOption']
                                        for row in policy['observations']))
                    self.assertTrue(admin.execute('''
                      SELECT has_column_privilege(%s,'truss.catalog_runtime_installation',
                                                  'managed_grants','SELECT')
                    ''', (allowed,)).fetchone()[0])

                    # PostgreSQL can record an inherited grant-option path as
                    # the selected role. This duplicate ordinary grant remains
                    # profile-exact and therefore must verify successfully.
                    admin.execute(psycopg.sql.SQL(
                        'GRANT EXECUTE ON FUNCTION truss.catalog_status() TO {} WITH GRANT OPTION'
                    ).format(psycopg.sql.Identifier(allowed)))
                    admin.execute(psycopg.sql.SQL('SET ROLE {}').format(psycopg.sql.Identifier(allowed)))
                    admin.execute(psycopg.sql.SQL(
                        'GRANT EXECUTE ON FUNCTION truss.catalog_status() TO {}'
                    ).format(psycopg.sql.Identifier(registrar)))
                    admin.execute('RESET ROLE')
                    selected_grant = admin.execute('''
                      SELECT a.grantee::pg_catalog.regrole::text,
                             a.grantor::pg_catalog.regrole::text,
                             a.privilege_type, a.is_grantable
                      FROM pg_catalog.pg_proc p
                      CROSS JOIN LATERAL pg_catalog.aclexplode(p.proacl) a
                      WHERE p.oid='truss.catalog_status()'::pg_catalog.regprocedure::oid
                        AND a.grantee=(SELECT oid FROM pg_catalog.pg_roles WHERE rolname=%s)
                        AND a.grantor=(SELECT oid FROM pg_catalog.pg_roles WHERE rolname=%s)
                    ''', (registrar, allowed)).fetchall()
                    self.assertIn((registrar, allowed, 'EXECUTE', False), selected_grant)
                    self.assertEqual(migrations.status()['state'], 'current')

                    admin.execute(psycopg.sql.SQL(
                        'GRANT EXECUTE ON FUNCTION truss.catalog_status() TO {} WITH GRANT OPTION'
                    ).format(psycopg.sql.Identifier(registrar)))
                    with self.assertRaisesRegex(ValueError, 'Installed privileges drifted'):
                        migrations.status()
                    admin.execute(psycopg.sql.SQL(
                        'REVOKE GRANT OPTION FOR EXECUTE ON FUNCTION truss.catalog_status() FROM {} CASCADE'
                    ).format(psycopg.sql.Identifier(registrar)))

                    admin.execute(psycopg.sql.SQL(
                        'GRANT EXECUTE ON FUNCTION truss.catalog_status() TO {} WITH GRANT OPTION'
                    ).format(psycopg.sql.Identifier(rogue)))
                    admin.execute(psycopg.sql.SQL('SET ROLE {}').format(psycopg.sql.Identifier(rogue)))
                    admin.execute(psycopg.sql.SQL(
                        'GRANT EXECUTE ON FUNCTION truss.catalog_status() TO {}'
                    ).format(psycopg.sql.Identifier(registrar)))
                    admin.execute('RESET ROLE')
                    with self.assertRaisesRegex(ValueError, 'Unexpected native owner or grant'):
                        migrations.status()
                    admin.execute(psycopg.sql.SQL(
                        'REVOKE EXECUTE ON FUNCTION truss.catalog_status() FROM {} CASCADE'
                    ).format(psycopg.sql.Identifier(rogue)))
                    self.assertEqual(migrations.status()['state'], 'current')

                    admin.execute(psycopg.sql.SQL(
                        'GRANT SELECT (managed_grants) ON TABLE truss.catalog_runtime_installation TO {}'
                    ).format(psycopg.sql.Identifier(rogue)))
                    with self.assertRaisesRegex(ValueError, 'Unexpected native owner or grant'):
                        migrations.status()
                    admin.execute(psycopg.sql.SQL(
                        'REVOKE SELECT (managed_grants) ON TABLE truss.catalog_runtime_installation FROM {}'
                    ).format(psycopg.sql.Identifier(rogue)))

                    admin.execute(psycopg.sql.SQL(
                        'GRANT SELECT ON TABLE truss.object TO {}'
                    ).format(psycopg.sql.Identifier(rogue)))
                    with self.assertRaisesRegex(ValueError, 'Unexpected native owner or grant'):
                        migrations.status()
                    admin.execute(psycopg.sql.SQL(
                        'REVOKE SELECT ON TABLE truss.object FROM {}'
                    ).format(psycopg.sql.Identifier(rogue)))

                    admin.execute(psycopg.sql.SQL('GRANT {} TO {} WITH INHERIT TRUE, SET FALSE').format(
                        psycopg.sql.Identifier(allowed), psycopg.sql.Identifier(registrar)))
                    with self.assertRaisesRegex(ValueError, 'inherits a tolerated platform-grant role'):
                        migrations.status()
                    admin.execute(psycopg.sql.SQL('REVOKE {} FROM {}').format(
                        psycopg.sql.Identifier(allowed), psycopg.sql.Identifier(registrar)))

                    renamed = allowed + '_renamed'
                    admin.execute(psycopg.sql.SQL('ALTER ROLE {} RENAME TO {}').format(
                        psycopg.sql.Identifier(allowed), psycopg.sql.Identifier(renamed)))
                    with self.assertRaisesRegex(ValueError, 'managed|tolerated|identity|role'):
                        migrations.status()
                    admin.execute(psycopg.sql.SQL('ALTER ROLE {} RENAME TO {}').format(
                        psycopg.sql.Identifier(renamed), psycopg.sql.Identifier(allowed)))
                    self.assertEqual(migrations.status()['state'], 'current')
            finally:
                if host is not None:
                    host.detach()
                if connection is not None and not connection.closed:
                    connection.rollback()
                    connection.close()
                fixture.cleanup()
                worker.verify_clean()
