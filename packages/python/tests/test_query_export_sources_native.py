"""Native export sources only; administrative rows do not qualify public writes/SDKs."""
import json
import psycopg
from truss import Ok, ModuleAccessGrant, adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration
from truss.catalog_runtime import _release
import test_group_create_native as base


class QueryExportSourceTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def binding(self, connection, documents=('adoc',)):
        manifest, digest, _ = _release()
        raw = connection.execute('SELECT truss.query_binding(%s::jsonb,10000,10000,16777216,%s,%s)',
            (json.dumps(documents), manifest['releaseId'], digest)).fetchone()[0]
        return json.dumps(json.loads(bytes(raw))['binding'])

    def seed(self, document, record, count):
        selected_type = self.admin.execute('SELECT type_id FROM truss.type_def WHERE document_id=%s AND element=%s',
                                           (document, record)).fetchone()[0]
        self.admin.execute('''INSERT INTO truss.object(type_id,props,rev)
            SELECT %s,(SELECT jsonb_object_agg(p.prop_id::text,
                jsonb_build_object('kind','string','text',p.name||'-'||n::text))
                FROM truss.prop_def p WHERE p.type_id=%s AND p.retired_rev IS NULL),1
            FROM generate_series(1,%s) n''', (selected_type, selected_type, count))
        return selected_type

    def refusal(self, connection, state, query, parameters):
        connection.execute('SAVEPOINT expected_refusal')
        with self.assertRaises(psycopg.Error) as caught:
            connection.execute(query, parameters).fetchone()
        self.assertEqual(caught.exception.sqlstate, state)
        connection.execute('ROLLBACK TO SAVEPOINT expected_refusal')
        connection.execute('RELEASE SAVEPOINT expected_refusal')

    def test_sources_exceed_ordinary_cap_and_keep_complete_key_checks(self):
        connection, host, _, _ = self.ready(document_ids=('adoc',))
        host.detach()
        a = self.seed('adoc', 'A', 10001)
        b = self.seed('adoc', 'B', 10001)
        relationship = self.admin.execute("SELECT rel_type_id FROM truss.rel_def WHERE document_id='adoc' AND rel_id='A-B'").fetchone()[0]
        self.admin.execute('''WITH a AS (SELECT id,row_number() OVER(ORDER BY id) n FROM truss.object WHERE type_id=%s),
            b AS (SELECT id,row_number() OVER(ORDER BY id) n FROM truss.object WHERE type_id=%s)
            INSERT INTO truss.edge(rel_type_id,source_id,source_type,target_id,target_type,rev)
            SELECT %s,a.id,%s,b.id,%s,1 FROM a JOIN b USING(n)''', (a,b,relationship,a,b))
        binding = self.binding(connection)
        connection.execute("SET LOCAL work_mem='64kB'")
        for function, selected in (('query_objects', a), ('query_edges', relationship)):
            self.refusal(connection, '54000', f'SELECT count(*) FROM truss.{function}(%s::jsonb,%s)', (binding, selected))
        for function, selected in (('query_export_objects', a), ('query_export_edges', relationship)):
            self.assertEqual(connection.execute(f'SELECT count(*) FROM truss.{function}(%s::jsonb,%s)',
                                                (binding, selected)).fetchone(), (10001,))
        self.assertEqual(connection.execute("SELECT count(*) FROM truss.query_export_page_objects(%s::jsonb,%s,'a-primary')",
                                            (binding, a)).fetchone(), (10001,))
        self.admin.execute('''UPDATE truss.object SET props=(SELECT props FROM truss.object WHERE type_id=%s ORDER BY id LIMIT 1)
            WHERE id=(SELECT max(id) FROM truss.object WHERE type_id=%s) AND type_id=%s''', (a,a,a))
        self.refusal(connection, '55000', "SELECT count(*) FROM truss.query_export_page_objects(%s::jsonb,%s,'a-primary')", (binding, a))
        connection.rollback()

    def test_original_root_document_and_current_reader_are_required(self):
        connection, host, _, _ = self.ready(document_ids=('adoc','zdoc'))
        host.detach(); connection.rollback()
        for role in ('export_root_reader', 'export_root_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute, psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN')
        admin_host = adopt_psycopg_host(self.admin)
        admin_assembly = create_reference_assembly(CatalogRuntimeConfiguration(), admin_host).value
        configured = admin_assembly.configure_module_access_in_transaction(admin_host.adopt_transaction().value,
            (ModuleAccessGrant('zdoc','m','export_root_reader','export_root_writer'),))
        self.assertIsInstance(configured, Ok, repr(configured))
        admin_host.detach(); self.admin.commit()
        self.admin.execute('GRANT export_root_reader TO consumer WITH SET FALSE')
        root_type = self.seed('zdoc', 'B', 1)
        child_type = self.seed('adoc', 'A', 1)
        root = self.admin.execute('SELECT id FROM truss.object WHERE type_id=%s', (root_type,)).fetchone()[0]
        self.admin.execute('UPDATE truss.object SET root_id=%s,root_type=%s WHERE type_id=%s', (root, root_type, child_type))
        connection.execute('BEGIN READ ONLY')
        missing_root = self.binding(connection)
        self.refusal(connection, '0A000', 'SELECT count(*) FROM truss.query_export_objects(%s::jsonb,%s)', (missing_root, child_type))
        complete = self.binding(connection, ('adoc','zdoc'))
        self.assertEqual(connection.execute('SELECT count(*) FROM truss.query_export_objects(%s::jsonb,%s)',
                                            (complete, child_type)).fetchone(), (1,))
        self.admin.execute('REVOKE export_root_reader FROM consumer')
        self.refusal(connection, '42501', 'SELECT count(*) FROM truss.query_export_objects(%s::jsonb,%s)', (complete, child_type))
        connection.rollback()
