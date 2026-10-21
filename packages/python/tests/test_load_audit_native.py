# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native invocation-summary audit disclosure and rollback controls."""
from dataclasses import replace

from truss import (Error, Ok, ModuleAccessGrant, ModuleAuditGrant, LoadAuditInvocationSummary,
                   LoadAuditListingEnd, adopt_psycopg_host, create_reference_assembly,
                   CatalogRuntimeConfiguration)
from truss.batched_import import ObjectImportDraft
from truss.contracts import MapValue, MapEntry, TextValue
from truss.imports import ImportReported
import test_batched_import_native as batch_tests


class LoadAuditNativeTests(batch_tests.BatchedImportTests):
    for _name in tuple(n for n in dir(batch_tests.BatchedImportTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_invocation_audit_summary_pages_complete_counts_and_scope(self):
        connection,host,assembly,tx=self.ready()
        built=self.build(assembly,tx,3,prefix='audit-')
        rolled_input=built.context.input(built.records[:1],load_id='audit-rolled-back',
            asserted_origin=MapValue(entries=()),chunk_size=1)
        rolled=assembly.import_batched_in_transaction(tx,rolled_input,documents=self.documents)
        self.assertIsInstance(rolled.result,ImportReported,repr(rolled))
        host.detach();connection.rollback()
        self.assertEqual(self.admin.execute(
            'SELECT count(*) FROM truss.runtime_import_load_chunk WHERE load_id=%s',
            ('audit-rolled-back',)).fetchone(),(0,))

        connection,host,assembly,tx=self.consumer()
        built=self.build(assembly,tx,3,prefix='audit-')
        bad=replace(built.records[2],payload=built.context.object_payload(()))
        asserted=MapValue(entries=(MapEntry(key='x-private-origin',
            value=TextValue(kind='string',text='origin-secret')),))
        create_input=built.context.input((built.records[0],built.records[1],bad),
            load_id='audit-created-and-rejected',asserted_origin=asserted,chunk_size=2)
        create_result=assembly.import_batched_in_transaction(tx,create_input,documents=self.documents)
        self.assertIsInstance(create_result.result,ImportReported,repr(create_result))
        self.assertEqual((create_result.result.report.counts.created_pending,
                          create_result.result.report.counts.skipped,
                          create_result.result.report.counts.rejected),('2','0','1'))
        host.detach();connection.commit()
        raw_origin,origin_digest=self.admin.execute(
            'SELECT original_asserted_origin::text,asserted_origin_sha256 '
            'FROM truss.runtime_import_load_chunk WHERE load_id=%s ORDER BY chunk_index LIMIT 1',
            ('audit-created-and-rejected',)).fetchone()
        self.assertIn('origin-secret',raw_origin)

        connection,host,assembly,tx=self.consumer()
        skipped_input=built.context.input(built.records[:2],load_id='audit-fully-skipped',
            asserted_origin=MapValue(entries=()),chunk_size=2)
        skipped=assembly.import_batched_in_transaction(tx,skipped_input,documents=self.documents)
        self.assertIsInstance(skipped.result,ImportReported,repr(skipped))
        self.assertEqual((skipped.result.report.counts.created_pending,
                          skipped.result.report.counts.skipped,
                          skipped.result.report.counts.rejected),('0','2','0'))
        host.detach();connection.commit()

        self.admin.execute('BEGIN')
        admin_host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        admin_tx=admin_host.adopt_transaction().value
        self.assertIsInstance(admin_assembly.configure_module_access_in_transaction(admin_tx,
            (ModuleAccessGrant('zdoc','m','group_reader','group_writer'),)),Ok)
        self.admin.execute('CREATE ROLE import_audit_reader NOLOGIN NOINHERIT')
        self.admin.execute("CREATE FUNCTION truss.current_query_protection_marker() RETURNS text LANGUAGE sql VOLATILE AS 'SELECT ''protected''::text'")
        protected_grant=admin_assembly.grant_module_audit_access_in_transaction(admin_tx,
            ModuleAuditGrant(document_id='adoc',module_id='m',auditor_role='import_audit_reader'))
        self.assertIsInstance(protected_grant,Error,repr(protected_grant))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_import_audit_access WHERE document_id=%s AND module=%s',
            ('adoc','m')).fetchone(),(0,))
        self.assertEqual(self.admin.execute("SELECT pg_catalog.has_schema_privilege('import_audit_reader','truss','USAGE')").fetchone(),(False,))
        self.assertEqual(self.admin.execute("SELECT pg_catalog.has_function_privilege('import_audit_reader','truss.page_import_load_audit(jsonb,int,bytea,text,text)','EXECUTE')").fetchone(),(False,))
        self.admin.execute('DROP FUNCTION truss.current_query_protection_marker()')
        for document_id in ('adoc','zdoc'):
            grant=admin_assembly.grant_module_audit_access_in_transaction(admin_tx,
                ModuleAuditGrant(document_id=document_id,module_id='m',auditor_role='import_audit_reader'))
            self.assertIsInstance(grant,Ok,repr(grant))
        admin_host.detach();self.admin.commit()
        self.addCleanup(self.admin.execute,'DROP ROLE IF EXISTS import_audit_reader')
        self.admin.execute('GRANT import_audit_reader TO consumer WITH INHERIT TRUE, SET FALSE')

        connection,host,assembly,tx=self.consumer()
        zdoc=assembly.build_import_records_in_transaction(tx,(
            ObjectImportDraft(document_id='zdoc',module_id='m',record_id='A',
                values=self.create(document='zdoc',label='other-module',value='other-module').values),))
        self.assertIsInstance(zdoc,Ok,repr(zdoc)+' '+str(host._custody.last_attempt.error))
        zinput=zdoc.value.context.input(zdoc.value.records,load_id='audit-other-module',
            asserted_origin=MapValue(entries=()),chunk_size=1)
        zresult=assembly.import_batched_in_transaction(tx,zinput,documents=self.documents)
        self.assertIsInstance(zresult.result,ImportReported,repr(zresult))
        host.detach();connection.commit()

        connection,host,assembly,tx=self.consumer()
        filters={'documentId':'adoc','moduleId':'m'}
        rolled_page=assembly.page_import_load_audit_in_transaction(tx,
            filters={**filters,'loadId':'audit-rolled-back'},maximum_entries=2)
        self.assertIsInstance(rolled_page,Ok,repr(rolled_page))
        self.assertIsInstance(rolled_page.value,LoadAuditListingEnd,repr(rolled_page.value))
        first=assembly.page_import_load_audit_in_transaction(tx,filters=filters,maximum_entries=2)
        self.assertIsInstance(first,Ok,repr(first)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(first.value,LoadAuditInvocationSummary,repr(first.value))
        pages=[first.value]
        while pages[-1].next_page_cursor is not None:
            next_page=assembly.page_import_load_audit_in_transaction(tx,filters=filters,
                cursor=pages[-1].next_page_cursor,maximum_entries=2)
            self.assertIsInstance(next_page,Ok,repr(next_page)+' '+str(host._custody.last_attempt.error))
            if isinstance(next_page.value,LoadAuditListingEnd):break
            self.assertIsInstance(next_page.value,LoadAuditInvocationSummary,repr(next_page.value))
            pages.append(next_page.value)
        self.assertEqual({page.load_id for page in pages},
            {'audit-created-and-rejected','audit-fully-skipped'})
        self.assertNotIn('audit-other-module',{page.load_id for page in pages})
        created_page=next(page for page in pages if page.load_id=='audit-created-and-rejected')
        self.assertEqual((created_page.created_count,created_page.skipped_count,created_page.rejected_count),('2','0','1'))
        self.assertEqual(created_page.asserted_origin_sha256,origin_digest)
        self.assertEqual(len(created_page.chunks),2)
        skipped_page=next(page for page in pages if page.load_id=='audit-fully-skipped')
        self.assertEqual((skipped_page.created_count,skipped_page.skipped_count,skipped_page.rejected_count),('0','2','0'))
        self.assertFalse(hasattr(created_page,'asserted_origin'))
        self.assertNotIn('origin-secret',repr(created_page))
        end=assembly.page_import_load_audit_in_transaction(tx,filters=filters,
            cursor=pages[-1].next_page_cursor,maximum_entries=2)
        self.assertIsInstance(end,Ok,repr(end));self.assertIsInstance(end.value,LoadAuditListingEnd)
        host.detach();connection.rollback()


if __name__ == '__main__':
    import unittest
    unittest.main()
