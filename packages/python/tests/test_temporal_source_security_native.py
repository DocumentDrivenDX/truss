# SPDX-License-Identifier: MIT OR Apache-2.0
"""ABI 1.3 temporal source shim authority, closure and context controls."""
import json

import psycopg

from truss import (CatalogRuntimeConfiguration, ModuleAccessGrant, Ok,
                   adopt_psycopg_host, create_reference_assembly)
from truss.catalog_runtime import _release
from truss.contracts import MapValue
from truss.groups import GroupSuccess, RequestNone

from test_temporal_source_guard_native import TemporalSourceGuardNativeTests


class TemporalSourceSecurityNativeTests(TemporalSourceGuardNativeTests):
    # Reuse its accepted-source helpers without repeating its guard tests.
    for _name in tuple(n for n in dir(TemporalSourceGuardNativeTests) if n.startswith('test_')):
        locals()[_name] = None

    @staticmethod
    def _invoke(connection, binding, type_id, requirements):
        return connection.execute(
            'SELECT * FROM truss.person_query_temporal_objects(%s::jsonb,%s,%s::jsonb)',
            (json.dumps(binding, separators=(',', ':')), int(type_id),
             json.dumps(requirements, separators=(',', ':'))),
        ).fetchall()

    @staticmethod
    def _invoke_page(connection, binding, type_id, key_id, requirements):
        return connection.execute(
            'SELECT * FROM truss.person_query_temporal_page_objects(%s::jsonb,%s,%s,%s::jsonb)',
            (json.dumps(binding, separators=(',', ':')), int(type_id), key_id,
             json.dumps(requirements, separators=(',', ':'))),
        ).fetchall()

    def _assert_sqlstate(self, connection, binding, type_id, requirements, state, diagnostic=None):
        with self.assertRaises(psycopg.Error) as raised:
            with connection.transaction():
                self._invoke(connection, binding, type_id, requirements)
        self.assertEqual(raised.exception.sqlstate, state, str(raised.exception))
        if diagnostic is not None:
            self.assertIn(diagnostic, str(raised.exception))

    def test_installed_temporal_abi13_shims_have_exact_owner_acl_and_stability(self):
        connection, host, binding, type_id, requirements = self._accepted_source()
        expected_abi = {
            'identity': 'truss-postgresql-logical-query',
            'version': '1.3',
            'sha256': '479a0ba01bf21e61163a0709c1a3b4dbaeb9d5db1a03791d2044857ae2de588d',
        }
        self.assertEqual(self.admin.execute('SELECT truss.query_temporal_abi()').fetchone()[0], expected_abi)
        self.assertEqual(binding['queryAbi'], expected_abi)
        self.assertEqual(len(self._invoke(connection, binding, type_id, requirements)), 6,
                         'The public temporal shim executes through the accepted ABI 1.3 source.')
        selected_key = next(item for item in binding['records']
                            if item['identity']['element'] == 'A')['keys'][0]['keyId']
        self.assertEqual(len(self._invoke_page(connection, binding, type_id, selected_key, requirements)), 6,
                         'The public temporal page shim uses the same full-source guard.')

        signatures = (
            ('truss.person_query_temporal_binding(jsonb,integer,integer,integer,text,text)', 'v', True, True),
            ('truss.person_query_temporal_objects(jsonb,integer,jsonb)', 's', True, True),
            ('truss.person_query_temporal_page_objects(jsonb,integer,text,jsonb)', 's', True, True),
            ('truss.query_temporal_binding(jsonb,integer,integer,integer,text,text)', 'v', True, False),
            ('truss.query_temporal_objects(jsonb,integer,jsonb)', 's', True, False),
            ('truss.query_temporal_page_objects(jsonb,integer,text,jsonb)', 's', True, False),
        )
        for signature, volatility, security_definer, public_execute in signatures:
            with self.subTest(signature=signature):
                row = self.admin.execute(
                    "SELECT p.proowner=i.owner_oid,p.provolatile,p.prosecdef,p.proconfig,"
                    "EXISTS(SELECT 1 FROM pg_catalog.aclexplode(coalesce(p.proacl,"
                    "pg_catalog.acldefault('f',p.proowner))) a WHERE a.grantee=0 "
                    "AND a.privilege_type='EXECUTE') "
                    "FROM pg_catalog.pg_proc p CROSS JOIN truss.catalog_runtime_installation i "
                    "WHERE i.singleton AND p.oid=%s::regprocedure",
                    (signature,),
                ).fetchone()
                self.assertEqual(row[:3], (True, volatility, security_definer), (signature, row))
                self.assertEqual(row[4], public_execute,
                    (signature, 'Only enrolled person shims have PUBLIC EXECUTE; private bodies do not'))
                self.assertIn('search_path=pg_catalog, pg_temp', row[3], (signature, row[3]))

        for person, internal in (
            ('truss.person_query_temporal_binding(jsonb,integer,integer,integer,text,text)',
             'truss.query_temporal_binding(jsonb,integer,integer,integer,text,text)'),
            ('truss.person_query_temporal_objects(jsonb,integer,jsonb)',
             'truss.query_temporal_objects(jsonb,integer,jsonb)'),
            ('truss.person_query_temporal_page_objects(jsonb,integer,text,jsonb)',
             'truss.query_temporal_page_objects(jsonb,integer,text,jsonb)'),
        ):
            self.assertTrue(self.admin.execute(
                'SELECT pg_catalog.has_function_privilege(\'consumer\',%s,\'EXECUTE\')', (person,)
            ).fetchone()[0], person)
            self.assertTrue(self.admin.execute(
                'SELECT pg_catalog.has_function_privilege(\'consumer\',%s,\'EXECUTE\')', (internal,)
            ).fetchone()[0], internal)
        host.detach()
        connection.rollback()

    def test_temporal_shim_refuses_abi_owner_acl_source_and_context_drift(self):
        connection, host, binding, type_id, requirements = self._accepted_source()
        wrong_abi = json.loads(json.dumps(binding))
        wrong_abi['queryAbi'] = self.admin.execute('SELECT truss.query_abi()').fetchone()[0]
        self._assert_sqlstate(connection, wrong_abi, type_id, requirements, '0A000',
                              'ABI 1.2 does not describe selected local timestamp carriers')

        wrong_context = json.loads(json.dumps(binding))
        wrong_context['releaseSha256'] = '0' * 64
        self._assert_sqlstate(connection, wrong_context, type_id, requirements, '0A000',
                              'selected query context required')

        wrong_source = json.loads(json.dumps(binding))
        wrong_source['documents'][0]['sha256'] = '0' * 64
        self._assert_sqlstate(connection, wrong_source, type_id, requirements, '55P03',
                              'original query source changed')

        # Keep the SECURITY DEFINER public shim at its installed owner so it
        # can enter the private body. Drift the internal routine owner; the
        # shim should then reject the changed private invocation owner.
        signature = 'truss.query_temporal_objects(jsonb,integer,jsonb)'
        owner_oid = self.admin.execute(
            'SELECT p.proowner FROM pg_catalog.pg_proc p WHERE p.oid=%s::regprocedure', (signature,)
        ).fetchone()[0]
        owner_name = self.admin.execute('SELECT rolname FROM pg_catalog.pg_roles WHERE oid=%s',
                                        (owner_oid,)).fetchone()[0]
        self.admin.execute('CREATE ROLE temporal_wrong_owner NOLOGIN')
        try:
            self.admin.execute('ALTER FUNCTION truss.query_temporal_objects(jsonb,integer,jsonb) '
                               'OWNER TO temporal_wrong_owner')
            self._assert_sqlstate(connection, binding, type_id, requirements, '55000',
                                  'original installed invocation owner required')
        finally:
            self.admin.execute(
                psycopg.sql.SQL('ALTER FUNCTION truss.query_temporal_objects(jsonb,integer,jsonb) OWNER TO {}')
                .format(psycopg.sql.Identifier(owner_name))
            )
            self.admin.execute('DROP ROLE temporal_wrong_owner')

        self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.query_temporal_objects(jsonb,integer,jsonb) FROM group_writer')
        try:
            self._assert_sqlstate(connection, binding, type_id, requirements, '42501',
                                  'original invocation EXECUTE grant required')
        finally:
            self.admin.execute('GRANT EXECUTE ON FUNCTION truss.query_temporal_objects(jsonb,integer,jsonb) TO group_writer')
        host.detach()
        connection.rollback()

    def test_temporal_person_admission_needs_module_role_even_for_registrar(self):
        # The ordinary consumer remains a registrar member. ABI 1.3 read
        # admission still requires an actual module reader/writer membership.
        connection, host, binding, type_id, requirements = self._accepted_source()
        registrar = self.installation.registrar_role
        self.admin.execute(
            psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(registrar))
        )
        self.admin.execute('REVOKE group_reader,group_writer FROM consumer')
        try:
            self._assert_sqlstate(connection, binding, type_id, requirements, 'P1403',
                                  'current person invocation admission required')
        finally:
            self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
            self.admin.execute(
                psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(registrar))
            )
        host.detach()
        connection.rollback()

    def test_temporal_source_requires_current_reader_for_aggregate_root(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc', 'zdoc'))
        self._store_rows(assembly, tx)
        self.admin.execute('CREATE ROLE temporal_root_reader NOLOGIN')
        self.admin.execute('CREATE ROLE temporal_root_writer NOLOGIN')
        self.addCleanup(self.admin.execute, 'DROP ROLE temporal_root_writer')
        self.addCleanup(self.admin.execute, 'DROP ROLE temporal_root_reader')
        self.admin.execute('BEGIN')
        admin_host = adopt_psycopg_host(self.admin)
        admin_assembly = create_reference_assembly(CatalogRuntimeConfiguration(), admin_host).value
        configured = admin_assembly.configure_module_access_in_transaction(
            admin_host.adopt_transaction().value,
            (ModuleAccessGrant('zdoc', 'm', 'temporal_root_reader', 'temporal_root_writer'),),
        )
        self.assertIsInstance(configured, Ok, repr(configured))
        admin_host.detach()
        self.admin.commit()
        self.admin.execute('GRANT temporal_root_writer TO consumer WITH SET FALSE')
        root_created = assembly.apply_in_transaction(
            tx, assembly.group_context_in_transaction(tx).value.input(
                (self.create(document='zdoc', record='B', label='root', alias='root'),),
                MapValue(entries=()),
            ),
            RequestNone(),
            documents=self.documents,
        )
        self.assertIsInstance(root_created, Ok, repr(root_created))
        self.assertIsInstance(root_created.value, GroupSuccess, repr(root_created))
        root_id = int(root_created.value.response.semantic.results[0].identity.id)
        host.detach()
        connection.commit()
        child_type = int(self.admin.execute(
            "SELECT type_id FROM truss.type_def WHERE document_id='adoc' AND element='A' AND retired_rev IS NULL"
        ).fetchone()[0])
        child_id = self.admin.execute('SELECT id FROM truss.object WHERE type_id=%s ORDER BY id LIMIT 1',
                                      (child_type,)).fetchone()[0]
        self.admin.execute('UPDATE truss.object SET root_id=%s,root_type=%s WHERE id=%s',
                           (root_id, self.admin.execute(
                               "SELECT type_id FROM truss.type_def WHERE document_id='zdoc' AND element='B'"
                           ).fetchone()[0], child_id))
        self.admin.execute('GRANT temporal_root_reader TO consumer WITH SET FALSE')
        connection, host, _, _ = self.consumer()
        manifest, digest, _ = _release()
        raw = connection.execute(
            'SELECT truss.person_query_temporal_binding(%s::jsonb,10000,1000,1048576,%s,%s)',
            ('["adoc","zdoc"]', manifest['releaseId'], digest),
        ).fetchone()[0]
        binding = json.loads(json.loads(bytes(raw))['bindingJson'])
        record = next(item for item in binding['records'] if item['identity']['element'] == 'A')
        fields = {item['identity']['element']: item['identity'] for item in record['fields']}
        requirements = {
            'version': 'truss.temporal-source-guard/0.1',
            'record': record['identity'],
            'fields': [{'field': fields['A-at'], 'kind': 'instant',
                        'presence': {'missing': False, 'null': False}}],
        }
        # This revocation is visible on the fresh statement. The current
        # query-scope gate refuses the selected root document before the later
        # aggregate-root check can run, and therefore releases no source rows.
        self.admin.execute('REVOKE temporal_root_reader,temporal_root_writer FROM consumer')
        self._assert_sqlstate(connection, binding, record['typeId'], requirements, 'P1403',
                              'complete selected_document reader required')
        host.detach()
        connection.rollback()


if __name__ == '__main__':
    import unittest
    unittest.main()
