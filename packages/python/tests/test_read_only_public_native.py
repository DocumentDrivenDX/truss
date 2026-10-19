# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual caller-owned read-only transaction workflows, with native permission changes."""
import concurrent.futures
import time
import psycopg
from truss import (Ok,Error,ObjectFound,ObjectNotFound,ReaderCatalog,AcceptedDocument,
    adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration)
from truss.groups import GroupSuccess,RequestNone
import test_reader_catalog_native as reader_tests

class ReadOnlyPublicTests(reader_tests.ReaderCatalogTests):
    for _name in tuple(n for n in dir(reader_tests.ReaderCatalogTests) if n.startswith('test_')):
        locals()[_name]=None

    def committed_object(self):
        connection,host,assembly,tx=self.ready()
        input,request=self.input(assembly,tx)
        created=self.apply(assembly,tx,input,request)
        self.assertIsInstance(created,GroupSuccess)
        identity=int(created.response.semantic.results[0].identity.id)
        host.detach();connection.commit()
        self.admin.execute('REVOKE group_writer FROM consumer');self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        connection.execute('BEGIN READ ONLY');host=adopt_psycopg_host(connection)
        self.addCleanup(host.detach);self.consumer_connections.append((connection,host))
        adopted=host.adopt_transaction(access_mode='read_only');self.assertIsInstance(adopted,Ok)
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        return connection,host,assembly,adopted.value,identity,input

    def object(self,assembly,tx,identity):
        return assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=identity)

    def test_create_commit_and_public_reads_in_actual_read_only_transaction(self):
        connection,host,assembly,tx,identity,input=self.committed_object()
        self.assertIsInstance(self.object(assembly,tx,identity).value,ObjectFound)
        self.assertIsInstance(assembly.reader_catalog_in_transaction(tx).value,ReaderCatalog)
        self.assertIsInstance(assembly.accepted_document_in_transaction(tx,document_id='adoc').value,AcceptedDocument)
        self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
        try:
            attempted=assembly.apply_in_transaction(tx,input,RequestNone(),documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
            self.assertIsInstance(attempted,Error);self.assertEqual(attempted.error.sql_state,'25006')
        finally:self.admin.execute('REVOKE group_writer FROM consumer')
        self.assertEqual(connection.execute('SHOW transaction_read_only').fetchone(),('on',))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))
        self.assertIsInstance(self.object(assembly,tx,identity).value,ObjectFound)
        self.admin.execute('REVOKE group_reader FROM consumer')
        refused=self.object(assembly,tx,identity)
        self.assertIsInstance(refused,Error);self.assertEqual(refused.error.sql_state,'42501')
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        self.assertIsInstance(self.object(assembly,tx,identity).value,ObjectFound)
        host.detach();connection.rollback()

    def test_policy_replaced_while_object_buffered_uses_current_roles(self):
        connection,host,assembly,tx,identity,input=self.committed_object()
        self.admin.execute('CREATE ROLE replacement_reader NOLOGIN');self.admin.execute('CREATE ROLE replacement_writer NOLOGIN')
        self.addCleanup(self.admin.execute,'DROP ROLE replacement_writer');self.addCleanup(self.admin.execute,'DROP ROLE replacement_reader')
        original=self.admin.execute("SELECT pg_get_functiondef('truss.get_object(text,text,text,bigint,int,text,text)'::regprocedure)").fetchone()[0]
        needle=" actor_oid:=truss.runtime_person(false);\n IF current_setting('transaction_read_only')='on' THEN"
        self.assertIn(needle,original)
        gated=original.replace(needle," PERFORM pg_advisory_lock(928372);PERFORM pg_advisory_unlock(928372);\n"+needle)
        self.admin.execute(gated);self.admin.execute('SELECT pg_advisory_lock(928372)')
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                pending=executor.submit(self.object,assembly,tx,identity)
                deadline=time.monotonic()+3;blocked=False
                while time.monotonic()<deadline:
                    blocked=self.admin.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=%s AND locktype='advisory' AND NOT granted)",(connection.info.backend_pid,)).fetchone()[0]
                    if blocked:break
                    time.sleep(.01)
                self.assertTrue(blocked,'reader did not buffer the object')
                self.admin.execute("UPDATE truss.module_access SET reader_role='replacement_reader',writer_role='replacement_writer' WHERE document_id='adoc' AND module='m'")
                self.admin.execute('SELECT pg_advisory_unlock(928372)')
                self.assertIsInstance(pending.result(timeout=5).value,ObjectNotFound)
                self.assertEqual(connection.execute('SHOW transaction_read_only').fetchone(),('on',))
        finally:
            self.admin.execute('SELECT pg_advisory_unlock_all()');self.admin.execute(original)
        self.admin.execute("UPDATE truss.module_access SET reader_role='group_reader',writer_role='group_writer' WHERE document_id='adoc' AND module='m'")
        self.assertIsInstance(self.object(assembly,tx,identity).value,ObjectFound)
        host.detach();connection.rollback()
