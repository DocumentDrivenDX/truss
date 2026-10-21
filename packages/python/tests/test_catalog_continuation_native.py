# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native conditional catalog reads, source CAS, and registrar probes."""
import concurrent.futures
from dataclasses import replace
import json
import psycopg
import time
from truss import CatalogDocument
from test_catalog_relational_support import relational_document

from truss import (CatalogCASConflict, CatalogDocumentExpectation, CatalogInvalid, CatalogRefused,
    CatalogUnavailable, Ok, ReaderCatalogSnapshot, ReaderCatalogUnchanged,
    RegistrarStatus, adopt_psycopg_host, create_reference_assembly,
    CatalogRuntimeConfiguration)
import test_reader_catalog_native as reader_tests


class CatalogContinuationNativeTests(reader_tests.ReaderCatalogTests):
    for _name in tuple(n for n in dir(reader_tests.ReaderCatalogTests) if n.startswith('test_')):
        locals()[_name] = None

    def added(self,assembly,identity):
        source=relational_document();source['id']=identity
        document=CatalogDocument(identity,'r1',json.dumps(source,indent=2).encode())
        return document,assembly.prepare_catalog((document,),bun_executable='/opt/homebrew/bin/bun')

    def test_conditional_snapshot_unchanged_readonly_hit_and_revocation(self):
        connection,host,assembly,tx=self.reader()
        self.assertEqual(assembly.reader_catalog_if_changed_in_transaction(tx,validator='not-a-validator'),
                         Ok(CatalogInvalid(code='selection')))
        snapshot=assembly.reader_catalog_if_changed_in_transaction(tx)
        self.assertIsInstance(snapshot,Ok,repr(snapshot))
        self.assertIsInstance(snapshot.value,ReaderCatalogSnapshot)
        unchanged=assembly.reader_catalog_if_changed_in_transaction(tx,validator=snapshot.value.validator)
        self.assertEqual(unchanged,Ok(ReaderCatalogUnchanged(validator=snapshot.value.validator)))

        host.detach();connection.rollback();connection.execute('BEGIN READ ONLY')
        host=adopt_psycopg_host(connection);self.consumer_connections.append((connection,host))
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        tx=host.adopt_transaction(access_mode='read_only').value
        readonly_snapshot=assembly.reader_catalog_if_changed_in_transaction(tx)
        self.assertIsInstance(readonly_snapshot,Ok,repr(readonly_snapshot))
        self.assertIsInstance(readonly_snapshot.value,ReaderCatalogSnapshot)
        readonly_hit=assembly.reader_catalog_if_changed_in_transaction(tx,validator=readonly_snapshot.value.validator)
        self.assertEqual(readonly_hit,Ok(ReaderCatalogUnchanged(validator=readonly_snapshot.value.validator)))
        host.detach();connection.rollback();connection.execute('BEGIN')
        host=adopt_psycopg_host(connection);self.consumer_connections.append((connection,host))
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        tx=host.adopt_transaction().value

        self.admin.execute('REVOKE group_reader FROM consumer')
        refused=assembly.reader_catalog_if_changed_in_transaction(tx,validator=snapshot.value.validator)
        self.assertIsInstance(refused.value,CatalogRefused)
        self.assertEqual(refused.value.code,'unauthorized')
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        recovered=assembly.reader_catalog_if_changed_in_transaction(tx,validator=snapshot.value.validator)
        self.assertEqual(recovered,Ok(ReaderCatalogUnchanged(validator=snapshot.value.validator)))
        host.detach();connection.rollback()

    def test_conditional_reader_rechecks_authority_before_hit_and_snapshot_release(self):
        connection,host,assembly,tx=self.reader()
        initial=assembly.reader_catalog_if_changed_in_transaction(tx)
        self.assertIsInstance(initial.value,ReaderCatalogSnapshot)
        original=self.admin.execute("SELECT pg_get_functiondef('truss.reader_catalog_if_changed(int,int,text,text,text)'::regprocedure)").fetchone()[0]
        marker=' -- Re-read the whole authority basis immediately before either response. A\n'
        self.assertIn(marker,original)
        self.admin.execute(original.replace(marker,' PERFORM pg_advisory_lock(928382);PERFORM pg_advisory_unlock(928382);\n'+marker,1))
        try:
            for validator in (None,initial.value.validator):
                self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
                self.admin.execute('SELECT pg_advisory_lock(928382)')
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    pending=executor.submit(assembly.reader_catalog_if_changed_in_transaction,tx,validator=validator)
                    try:
                        deadline=time.monotonic()+3;blocked=False
                        while time.monotonic()<deadline:
                            blocked=self.admin.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=%s AND locktype='advisory' AND NOT granted)",(connection.info.backend_pid,)).fetchone()[0]
                            if blocked:break
                            time.sleep(.01)
                        self.assertTrue(blocked,'conditional reader did not reach the final authority check')
                        self.admin.execute('REVOKE group_reader FROM consumer')
                    finally:
                        self.admin.execute('SELECT pg_advisory_unlock(928382)')
                    observed=pending.result(timeout=5)
                self.assertIsInstance(observed.value,CatalogUnavailable,repr(observed))
                self.assertEqual(observed.value.code,'observation')
        finally:
            self.admin.execute('SELECT pg_advisory_unlock_all()')
            self.admin.execute(original)
            self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
            host.detach();connection.rollback()

    def test_source_document_cas_is_independent_of_global_head_and_replay_precedes_staleness(self):
        connection,host,assembly,tx=self.ready()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        self.assertEqual(assembly.registrar_status_in_transaction(tx),Ok(RegistrarStatus(True)))

        bdoc,prepared=self.added(assembly,'bdoc')
        accepted=assembly.accept_in_transaction(tx,prepared,request_key='bdoc-cas',
            expected_revision=1,expected_documents=(CatalogDocumentExpectation('bdoc',0),))
        self.assertIsInstance(accepted,Ok,repr(accepted));self.assertEqual(accepted.value.revision,2)
        cdoc,prepared_c=self.added(assembly,'cdoc')
        unrelated=assembly.accept_in_transaction(tx,prepared_c,request_key='cdoc-cas',
            expected_documents=(CatalogDocumentExpectation('cdoc',0),))
        self.assertIsInstance(unrelated,Ok,repr(unrelated));self.assertEqual(unrelated.value.revision,3)

        replay=assembly.accept_in_transaction(tx,prepared,request_key='bdoc-cas',
            expected_revision=1,expected_documents=(CatalogDocumentExpectation('bdoc',0),))
        self.assertIsInstance(replay,Ok,repr(replay));self.assertTrue(replay.value.replayed)
        changed_expectation=assembly.accept_in_transaction(tx,prepared,request_key='bdoc-cas',
            expected_revision=2,expected_documents=(CatalogDocumentExpectation('bdoc',2),))
        self.assertNotIsInstance(changed_expectation,Ok)
        self.assertEqual(assembly.catalog_revision_in_transaction(tx).value.catalog_revision,'3')

        stale=assembly.accept_in_transaction(tx,prepared_c,request_key='cdoc-stale',
            expected_documents=(CatalogDocumentExpectation('cdoc',0),))
        self.assertEqual(stale,Ok(CatalogCASConflict()))

        bdoc_v2=assembly.prepare_catalog((replace(bdoc,document_revision='r2',content=bdoc.content+b'\n'),),bun_executable='/opt/homebrew/bin/bun')
        same_document_stale=assembly.accept_in_transaction(tx,bdoc_v2,request_key='bdoc-stale-source',
            expected_documents=(CatalogDocumentExpectation('bdoc',1),))
        self.assertEqual(same_document_stale,Ok(CatalogCASConflict()))
        ddoc,prepared_d=self.added(assembly,'ddoc')
        absent=assembly.accept_in_transaction(tx,prepared_d,request_key='ddoc-absent',
            expected_documents=(CatalogDocumentExpectation('ddoc',0),))
        self.assertIsInstance(absent,Ok);self.assertEqual(absent.value.revision,4)
        stale_absent=assembly.accept_in_transaction(tx,prepared_d,request_key='ddoc-after-create',
            expected_documents=(CatalogDocumentExpectation('ddoc',0),))
        self.assertEqual(stale_absent,Ok(CatalogCASConflict()))
        edoc,prepared_e=self.added(assembly,'edoc')
        stale_global=assembly.accept_in_transaction(tx,prepared_e,request_key='edoc-global-stale',
            expected_revision=3,expected_documents=(CatalogDocumentExpectation('edoc',0),))
        self.assertEqual(stale_global,Ok(CatalogCASConflict()))
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        self.assertIsInstance(assembly.registrar_status_in_transaction(tx),Ok)
        self.assertEqual(assembly.registrar_status_in_transaction(tx).value,RegistrarStatus(False))
        host.detach();connection.rollback()


if __name__ == '__main__':
    import unittest
    unittest.main()
