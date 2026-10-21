# SPDX-License-Identifier: MIT OR Apache-2.0
"""Installation admission refuses known preconditions before publishing DDL."""
from copy import deepcopy
from unittest.mock import patch

import psycopg

from truss import (CatalogRuntimeConfiguration, InstallRefused, Ok,
                   adopt_psycopg_host, create_reference_assembly)
from truss.catalog_runtime import _release
import test_catalog_runtime_native as catalog_tests


class InstallPreflightNativeTests(catalog_tests.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(catalog_tests.PublicCatalogRuntimeTests)
                       if n.startswith('test_')):
        locals()[_name] = None

    def test_busy_install_is_retryable_after_holder_rolls_back(self):
        holder = psycopg.connect(
            **psycopg.conninfo.conninfo_to_dict(self.info.connection_uri),
            autocommit=True)
        self.addCleanup(holder.close)
        holder.execute('BEGIN')
        holder.execute('SELECT pg_catalog.pg_advisory_xact_lock(1953658227,1735549296)')

        blocked = self.assembly.install_in_transaction(self.tx)
        self.assertEqual(blocked, Ok(InstallRefused(code='busy')))
        self.assertEqual(self.admin.execute('SELECT 42').fetchone(), (42,))
        self.assertEqual(self.admin.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')"
        ).fetchone(), (False,))

        holder.rollback()
        installed = self.assembly.install_in_transaction(self.tx)
        self.assertIsInstance(installed, Ok, repr(installed))
        self.assertNotIsInstance(installed.value, InstallRefused)
        self.installation = installed.value
        self.host.detach()
        self.admin.commit()

    def test_known_preflight_refusals_leave_schema_absent(self):
        self.assertEqual(
            self.assembly.install_in_transaction(
                self.tx, owner_role='pg_reserved', registrar_role='valid_role'),
            Ok(InstallRefused(code='invalid_roles')))
        manifest, digest, sources = _release()
        wrong_version = deepcopy(manifest)
        wrong_version['postgresVersion'] = '0'
        with patch('truss.catalog_runtime._release',
                   return_value=(wrong_version, digest, sources)):
            unsupported = self.assembly.install_in_transaction(self.tx)
        self.assertEqual(unsupported, Ok(InstallRefused(code='unsupported_postgres')))
        self.assertEqual(self.admin.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')"
        ).fetchone(), (False,))
        self.assertEqual(self.admin.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname LIKE 'truss_owner_%')"
        ).fetchone(), (False,))

    def test_existing_role_name_and_foreign_schema_are_typed_and_untouched(self):
        self.admin.execute('CREATE ROLE truss_owner_collision NOLOGIN')
        self.addCleanup(self.admin.execute, 'DROP ROLE IF EXISTS truss_owner_collision')
        role_collision = self.assembly.install_in_transaction(
            self.tx, owner_role='truss_owner_collision', registrar_role='truss_client_collision')
        self.assertEqual(role_collision, Ok(InstallRefused(code='role_exists')))
        self.assertEqual(self.admin.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='truss_client_collision')"
        ).fetchone(), (False,))
        self.assertEqual(self.admin.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')"
        ).fetchone(), (False,))

        self.admin.execute('CREATE SCHEMA truss')
        incompatible = self.assembly.install_in_transaction(self.tx)
        self.assertEqual(incompatible, Ok(InstallRefused(code='incompatible')))
        self.assertEqual(self.admin.execute(
            "SELECT count(*) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'"
        ).fetchone(), (0,))

    def test_marker_inspection_is_passive_and_requires_plain_builtin_table(self):
        def refuse_incompatible():
            result=self.assembly.install_in_transaction(self.tx)
            self.assertEqual(result,Ok(InstallRefused(code='incompatible')))

        self.admin.execute('CREATE TABLE public.install_marker_probe(executed boolean)')
        self.admin.execute("CREATE FUNCTION public.install_marker_probe() RETURNS text LANGUAGE plpgsql VOLATILE AS $$BEGIN INSERT INTO public.install_marker_probe VALUES(true); RETURN 'foreign'; END$$")
        self.admin.execute('CREATE SCHEMA truss')
        self.admin.execute('''CREATE VIEW truss.catalog_runtime_installation AS
            SELECT true::pg_catalog.bool AS singleton,public.install_marker_probe()::pg_catalog.text AS release_id,
              'foreign'::pg_catalog.text AS release_sha256,'{}'::pg_catalog.jsonb AS layout_profile''')
        refuse_incompatible()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM public.install_marker_probe').fetchone(),(0,))
        self.admin.execute('DROP SCHEMA truss CASCADE')

        self.admin.execute('CREATE SCHEMA truss')
        self.admin.execute('''CREATE TABLE truss.catalog_runtime_installation(
            singleton pg_catalog.bool,release_id pg_catalog.text,release_sha256 pg_catalog.text,
            layout_profile pg_catalog.jsonb)''')
        self.admin.execute('ALTER TABLE truss.catalog_runtime_installation ENABLE ROW LEVEL SECURITY')
        refuse_incompatible()
        self.admin.execute('DROP SCHEMA truss CASCADE')

        self.admin.execute('CREATE SCHEMA truss')
        self.admin.execute('''CREATE TABLE truss.catalog_runtime_installation(
            singleton pg_catalog.bool,release_id pg_catalog.text GENERATED ALWAYS AS ('foreign'::pg_catalog.text) STORED,
            release_sha256 pg_catalog.text,layout_profile pg_catalog.jsonb)''')
        refuse_incompatible()
        self.admin.execute('DROP SCHEMA truss CASCADE')

        self.admin.execute('CREATE SCHEMA truss')
        self.admin.execute('''CREATE TABLE truss.catalog_runtime_installation(
            singleton pg_catalog.text,release_id pg_catalog.text,release_sha256 pg_catalog.text,
            layout_profile pg_catalog.jsonb)''')
        refuse_incompatible()
        self.admin.execute('DROP SCHEMA truss CASCADE')

    def test_foreign_table_marker_is_refused_before_read(self):
        # A handlerless test FDW allows foreign-table DDL but cannot execute a
        # scan. The installer must reject by relkind before attempting one.
        self.admin.execute('CREATE FOREIGN DATA WRAPPER truss_marker_fdw')
        self.admin.execute('CREATE SERVER truss_marker_server FOREIGN DATA WRAPPER truss_marker_fdw')
        self.addCleanup(self.admin.execute,'DROP SERVER IF EXISTS truss_marker_server CASCADE')
        self.addCleanup(self.admin.execute,'DROP FOREIGN DATA WRAPPER IF EXISTS truss_marker_fdw CASCADE')
        self.admin.execute('CREATE SCHEMA truss')
        self.admin.execute('''CREATE FOREIGN TABLE truss.catalog_runtime_installation(
            singleton pg_catalog.bool,release_id pg_catalog.text,release_sha256 pg_catalog.text,
            layout_profile pg_catalog.jsonb) SERVER truss_marker_server OPTIONS (schema_name 'public',table_name 'catalog_runtime_installation')''')
        result=self.assembly.install_in_transaction(self.tx)
        self.assertEqual(result,Ok(InstallRefused(code='incompatible')))

    def test_unauthorized_and_read_only_installers_are_typed_without_ddl(self):
        self.admin.execute('CREATE ROLE truss_unprivileged_installer LOGIN')
        self.addCleanup(self.admin.execute, 'DROP ROLE IF EXISTS truss_unprivileged_installer')
        self.host.detach()
        self.admin.commit()

        parameters = psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        parameters['user'] = 'truss_unprivileged_installer'
        ordinary = psycopg.connect(**parameters, autocommit=True,
                                   options='-c statement_timeout=10000')
        self.addCleanup(ordinary.close)
        ordinary.execute('BEGIN')
        ordinary_host = adopt_psycopg_host(ordinary, statement_timeout_ms=10000,
                                           operation_timeout_ms=30000)
        self.addCleanup(ordinary_host.detach)
        ordinary_assembly = create_reference_assembly(
            CatalogRuntimeConfiguration(), ordinary_host).value
        ordinary_tx = ordinary_host.adopt_transaction()
        self.assertIsInstance(ordinary_tx, Ok, repr(ordinary_tx))
        refused = ordinary_assembly.install_in_transaction(
            ordinary_tx.value)
        self.assertEqual(refused, Ok(InstallRefused(code='unauthorized')))
        self.assertEqual(ordinary.execute('SELECT 42').fetchone(), (42,))
        ordinary_host.detach()
        ordinary.rollback()

        readonly = psycopg.connect(
            **psycopg.conninfo.conninfo_to_dict(self.info.connection_uri),
            autocommit=True, options='-c statement_timeout=10000')
        self.addCleanup(readonly.close)
        readonly.execute('BEGIN READ ONLY')
        readonly_host = adopt_psycopg_host(readonly, statement_timeout_ms=10000,
                                           operation_timeout_ms=30000)
        self.addCleanup(readonly_host.detach)
        readonly_assembly = create_reference_assembly(
            CatalogRuntimeConfiguration(), readonly_host).value
        readonly_tx = readonly_host.adopt_transaction(access_mode='read_only')
        self.assertIsInstance(readonly_tx, Ok, repr(readonly_tx))
        read_only_result = readonly_assembly.install_in_transaction(readonly_tx.value)
        self.assertEqual(read_only_result, Ok(InstallRefused(code='read_only')))
        self.assertEqual(readonly.execute('SELECT 42').fetchone(), (42,))
        self.assertEqual(self.admin.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname='truss')"
        ).fetchone(), (False,))
        readonly_host.detach()
        readonly.rollback()

    def test_compatible_installation_is_reported_without_reset(self):
        installed = self.assembly.install_in_transaction(self.tx)
        self.assertIsInstance(installed, Ok, repr(installed))
        self.installation = installed.value
        self.host.detach()
        self.admin.commit()
        before = self.admin.execute(
            'SELECT installation_id,owner_oid,registrar_oid,release_id,release_sha256 '
            'FROM truss.catalog_runtime_installation WHERE singleton').fetchone()

        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin, statement_timeout_ms=10000,
                                  operation_timeout_ms=30000)
        self.addCleanup(host.detach)
        assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
        tx = host.adopt_transaction().value
        result = assembly.install_in_transaction(tx)
        self.assertEqual(result, Ok(InstallRefused(code='already_installed')))
        self.assertEqual(self.admin.execute(
            'SELECT installation_id,owner_oid,registrar_oid,release_id,release_sha256 '
            'FROM truss.catalog_runtime_installation WHERE singleton').fetchone(), before)
        host.detach()
        self.admin.rollback()


if __name__ == '__main__':
    import unittest
    unittest.main()
