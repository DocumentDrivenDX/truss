# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public catalog refusal codes without diagnostic-message parsing."""
import psycopg
from truss import Ok,Error
import test_catalog_runtime_native as catalog_tests

class CatalogCodeTests(catalog_tests.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(catalog_tests.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None

    def code(self,result,expected,state=None):
        self.assertIsInstance(result,Error);self.assertEqual(result.error.catalog_code,expected)
        if state is not None:self.assertEqual(result.error.sql_state,state)

    def test_public_registration_report_view_and_status_codes(self):
        self.install();connection,host,assembly,tx=self.consumer();prepared=self.prepared(assembly)
        connection.execute("CREATE TEMP TABLE catalog_prior(value text);INSERT INTO catalog_prior VALUES('kept')")
        self.code(assembly.accept_in_transaction(tx,None,request_key='invalid'),'invalid_input')
        self.code(assembly.accept_in_transaction(tx,prepared,request_key=''),'invalid_input')
        self.code(assembly.accept_in_transaction(tx,prepared,request_key='invalid-origin',origin_bytes=b'[]'),'invalid_input')
        self.code(assembly.report_in_transaction(tx,revision=0),'invalid_input')
        missing=assembly.accept_in_transaction(None,prepared,request_key='invalid-handle')
        self.assertIsInstance(missing,Error);self.assertEqual(missing.error.code,'invalid_transaction');self.assertIsNone(missing.error.catalog_code)
        # A real staging uniqueness violation must not be classified as request replay conflict.
        self.admin.execute('CREATE UNIQUE INDEX test_single_revision ON truss.schema_rev ((true))')
        integrity=assembly.accept_in_transaction(tx,prepared,request_key='unique-control')
        self.code(integrity,None,'23505');self.admin.execute('DROP INDEX truss.test_single_revision')
        registered=assembly.accept_in_transaction(tx,prepared,request_key='one')
        self.assertIsInstance(registered,Ok)
        self.code(assembly.accept_in_transaction(tx,prepared,request_key='one',origin_bytes=b'{"x-action":"changed"}'),'request_conflict','P1001')
        from truss import CatalogDocument,CatalogUnchanged
        import json
        from test_catalog_relational_support import relational_document
        unchanged=assembly.accept_in_transaction(tx,prepared,request_key='second')
        self.assertIsInstance(unchanged,Ok);self.assertIsInstance(unchanged.value,CatalogUnchanged)
        source=relational_document();source['id']='adoc'
        changed=assembly.prepare_catalog((CatalogDocument('adoc','r2',json.dumps(source).encode()),),bun_executable='/opt/homebrew/bin/bun')
        self.code(assembly.accept_in_transaction(tx,changed,request_key='changed'),'unsupported_profile','0A000')
        self.assertIsInstance(assembly.report_in_transaction(tx),Ok)
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        for result in (assembly.accept_in_transaction(tx,prepared,request_key='denied'),assembly.report_in_transaction(tx),
                       assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request()),assembly.status_in_transaction(tx)):
            self.code(result,'unauthorized','42501')
        self.assertEqual(connection.execute('TABLE catalog_prior').fetchall(),[('kept',)])
        host.detach();connection.rollback()
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(0,))

    def test_retry_and_status_release_mismatch_keep_original_error_fields(self):
        self.install();connection,host,assembly,tx=self.consumer();prepared=self.prepared(assembly)
        self.admin.execute("CREATE FUNCTION public.catalog_retry_control() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'retry control' USING ERRCODE='40001';END $$")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.catalog_retry_control()')
        self.admin.execute('CREATE TRIGGER catalog_retry_control BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION public.catalog_retry_control()')
        retry=assembly.accept_in_transaction(tx,prepared,request_key='retry-control')
        self.assertIsInstance(retry,Error);self.assertEqual(retry.error.code,'retry');self.assertEqual(retry.error.retry_scope,'whole_transaction');self.assertEqual(retry.error.sql_state,'40001');self.assertIsNone(retry.error.catalog_code)
        self.admin.execute('DROP TRIGGER catalog_retry_control ON truss.schema_rev')
        host.detach();connection.rollback();connection,host,assembly,tx=self.consumer()
        # Administrative negative fixture only; normal installation markers stay immutable.
        self.admin.execute('ALTER TABLE truss.catalog_runtime_installation DISABLE TRIGGER catalog_immutable')
        try:self.admin.execute("UPDATE truss.catalog_runtime_installation SET release_id='different-profile'")
        finally:self.admin.execute('ALTER TABLE truss.catalog_runtime_installation ENABLE ALWAYS TRIGGER catalog_immutable')
        mismatch=assembly.status_in_transaction(tx);self.code(mismatch,'unsupported_profile')
        self.assertEqual(mismatch.error.code,'invalid_transaction')
        host.detach();connection.rollback()
