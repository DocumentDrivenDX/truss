"""Exact-input unchanged registration, durable requests and caller settlement."""
import json
import os
import psycopg
from truss import Ok,Error,CatalogUnchanged,CatalogDocument
import test_catalog_runtime_native as catalog_tests

class CatalogUnchangedTests(catalog_tests.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(catalog_tests.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_registration_retry_preserves_legacy_report_after_preparation_change(self):
        from truss.preparation import prepare_acceptance
        from truss._catalog_report_semantics import canonical_numeric_free
        self.install();connection,host,assembly,tx=self.consumer()
        ordinary=self.prepared(assembly)
        choices={key:value for key,value in ordinary.input().items() if key not in ('interfaceVersion','documents')}
        legacy=prepare_acceptance(tuple(prepared_documents(ordinary)),canonical_numeric_free(choices),
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertEqual(legacy.input_bytes,ordinary.input_bytes)
        original=assembly.accept_in_transaction(tx,legacy,request_key='original')
        self.assertIsInstance(original,Ok,repr(original))
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        replay=assembly.accept_in_transaction(tx,ordinary,request_key='original')
        self.assertIsInstance(replay,Ok,repr(replay))
        self.assertTrue(replay.value.replayed)
        self.assertEqual(replay.value.report_bytes,original.value.report_bytes)
        unchanged=assembly.accept_in_transaction(tx,ordinary,request_key='new-key')
        self.assertIsInstance(unchanged,Ok,repr(unchanged))
        self.assertIsInstance(unchanged.value,CatalogUnchanged)
        self.assertEqual(unchanged.value.registration_id,original.value.registration_id)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(1,))

    def test_pending_committed_retry_and_original_report_are_distinct(self):
        self.install();connection,host,assembly,tx=self.consumer();prepared=self.prepared(assembly)
        original=assembly.accept_in_transaction(tx,prepared,request_key='original',origin_bytes=b'{"x-action":"register"}')
        self.assertIsInstance(original,Ok)
        origin=b'{"x-action":"check"}'
        unchanged=assembly.accept_in_transaction(tx,prepared,request_key='check',origin_bytes=origin)
        self.assertIsInstance(unchanged,Ok);self.assertIsInstance(unchanged.value,CatalogUnchanged)
        result=unchanged.value
        self.assertEqual((result.outcome,result.status,result.replayed),('unchanged','pending_commit',False))
        self.assertEqual((result.revision,result.registration_id,result.report_bytes),
                         (original.value.revision,original.value.registration_id,original.value.report_bytes))
        self.assertEqual((result.request_key,result.asserted_origin_bytes,result.actor),('check',origin,'consumer'))
        self.assertEqual(json.loads(result.report_bytes)['assertedOrigin'],{'x-action':'register'})
        retry=assembly.accept_in_transaction(tx,prepared,request_key='check',origin_bytes=origin)
        self.assertIsInstance(retry,Ok);self.assertTrue(retry.value.replayed)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(1,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_registration_request').fetchone(),(1,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_acceptance_report').fetchone(),(1,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_unchanged_request').fetchone(),(1,))
        connection,host,assembly,tx=self.consumer()
        retry=assembly.accept_in_transaction(tx,prepared,request_key='check',origin_bytes=origin)
        self.assertIsInstance(retry,Ok);self.assertIsInstance(retry.value,CatalogUnchanged);self.assertTrue(retry.value.replayed)
        connection.execute("CREATE TEMP TABLE unchanged_prior(value text);INSERT INTO unchanged_prior VALUES('kept')")
        conflict=assembly.accept_in_transaction(tx,prepared,request_key='check',origin_bytes=b'{}')
        self.assertIsInstance(conflict,Error);self.assertEqual(conflict.error.catalog_code,'request_conflict')
        changed_documents=tuple(CatalogDocument(d.document_id,d.document_revision,d.content+b' ') for d in prepared_documents(prepared))
        changed=assembly.prepare_catalog(changed_documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        conflict=assembly.accept_in_transaction(tx,changed,request_key='check',origin_bytes=origin)
        self.assertIsInstance(conflict,Error);self.assertEqual(conflict.error.catalog_code,'request_conflict')
        self.assertEqual(connection.execute('TABLE unchanged_prior').fetchall(),[('kept',)])
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        denied=assembly.accept_in_transaction(tx,prepared,request_key='check',origin_bytes=origin)
        self.assertIsInstance(denied,Error);self.assertEqual(denied.error.catalog_code,'unauthorized')
        host.detach();connection.rollback()

    def test_rollback_and_suppressed_alias_do_not_publish_success(self):
        self.install();connection,host,assembly,tx=self.consumer();prepared=self.prepared(assembly)
        self.assertIsInstance(assembly.accept_in_transaction(tx,prepared,request_key='original'),Ok)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        self.admin.execute("CREATE FUNCTION public.suppress_unchanged() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL;END $$")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.suppress_unchanged()')
        self.admin.execute('CREATE TRIGGER suppress_unchanged BEFORE INSERT ON truss.catalog_unchanged_request FOR EACH ROW EXECUTE FUNCTION public.suppress_unchanged()')
        refused=assembly.accept_in_transaction(tx,prepared,request_key='suppressed')
        self.assertIsInstance(refused,Error);self.assertEqual(refused.error.sql_state,'55000')
        self.admin.execute('DROP TRIGGER suppress_unchanged ON truss.catalog_unchanged_request')
        self.assertIsInstance(assembly.accept_in_transaction(tx,prepared,request_key='rolled-back'),Ok)
        host.detach();connection.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_unchanged_request').fetchone(),(0,))
        # Trusted administrative corruption fixture: neither public endpoint may
        # interpret a key present in both request stores as an ordinary retry.
        self.admin.execute('ALTER TABLE truss.catalog_unchanged_request DISABLE TRIGGER catalog_unchanged_completion')
        try:
            self.admin.execute("INSERT INTO truss.catalog_unchanged_request SELECT installation_id,actor_oid,actor_name,request_key,registration_id,origin_bytes FROM truss.catalog_registration_request")
        finally:self.admin.execute('ALTER TABLE truss.catalog_unchanged_request ENABLE ALWAYS TRIGGER catalog_unchanged_completion')
        connection,host,assembly,tx=self.consumer()
        refused=assembly.accept_in_transaction(tx,prepared,request_key='original')
        self.assertIsInstance(refused,Error);self.assertEqual(refused.error.sql_state,'55000')
        host.detach();connection.rollback()

    def test_deferred_completion_rechecks_authorization(self):
        self.install();connection,host,assembly,tx=self.consumer();prepared=self.prepared(assembly)
        self.assertIsInstance(assembly.accept_in_transaction(tx,prepared,request_key='original'),Ok)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.accept_in_transaction(tx,prepared,request_key='check'),Ok)
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        host.detach()
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_unchanged_request').fetchone(),(0,))

def prepared_documents(prepared):
    for document in json.loads(prepared.archive_documents_bytes):
        yield CatalogDocument(document['documentId'],document['revision'],document['originalText'].encode())
