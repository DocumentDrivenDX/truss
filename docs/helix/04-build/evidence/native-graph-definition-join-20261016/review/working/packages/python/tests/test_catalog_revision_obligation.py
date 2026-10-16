"""Actual native required revision sources; no complete report/feed admission."""
import dataclasses
import json
import unittest
from pg8000.exceptions import DatabaseError
from test_catalog_staging import CatalogNativeFixture, ROOT, native_document
from test_preparation import prepare
from truss._catalog_staging import stage_catalog_report_basis
from truss._catalog_completion import (
    capture_catalog_completion_prestate, collect_catalog_revision_obligation)


class CatalogRevisionObligationTests(CatalogNativeFixture, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        connection = cls.Connection(**cls.kwargs)
        try:
            for source in ('catalog-report/empty-graph.sql',
                           'catalog-completion/physical-poststate.sql',
                           'catalog-completion/revision-obligation.sql'):
                connection.run((ROOT/'packages/postgresql/native'/source).read_text())
        finally:
            connection.close()

    def complete(self, *, fake_feed=False):
        basis = stage_catalog_report_basis(self.connection, self.prepared,
                                           origin_bytes=b'{"x-action":"register"}')
        prestate = capture_catalog_completion_prestate(self.connection, self.prepared, basis)
        revision = json.loads(basis.basis_bytes)['fields']['rev']
        report = b'non-semantic original report fixture'
        self.connection.run("INSERT INTO truss.catalog_acceptance_report VALUES(CAST(:rev AS int),decode(:report,'hex'))",
                            rev=revision, report=report.hex())
        self.connection.run('UPDATE truss.schema_head SET rev=CAST(:rev AS int)', rev=revision)
        if fake_feed:
            # Administrative fixture bytes deliberately confer no feed authority.
            self.connection.run("""INSERT INTO truss.feed_tx(
                source_epoch,feed_profile,original_writer_xid,
                original_context_bytes,manifest_profile_bytes)
                VALUES('fake-epoch','fake-profile',pg_current_xact_id(),
                       decode('01','hex'),decode('02','hex'))""")
        return prestate, report

    def collect(self, prestate, report):
        return json.loads(collect_catalog_revision_obligation(
            self.connection, self.prepared, prestate, report))

    def test_revision_only_requires_fact_with_empty_feed_and_cannot_commit(self):
        prestate, report = self.complete()
        result = self.collect(prestate, report)
        self.assertEqual(result['requiredFactCount'], '1')
        self.assertEqual(result['requiredFactKind'], 'revision')
        self.assertEqual(result['payload'], {
            'state':'unavailable', 'reason':'complete_report_issuer_missing'})
        self.assertIs(result['feedFactQualified'], False)
        self.assertIs(result['acceptedReportQualified'], False)
        for name in ('feed_tx','feed_member','feed_prerequisite','feed_configuration_prerequisite','object','edge','journal'):
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.'+name), [[0]])
        self.assertEqual(result['originalInputHex'], self.prepared.input_bytes.hex())
        self.assertEqual(result['originalReportHex'], report.hex())
        self.assertEqual(result['documents'][0]['originalDocumentHex'],
                         self.prepared.documents[0].document.content.hex())
        self.assertEqual(self.connection.run('SELECT phase FROM truss.row_home_operation'), [['admitted']])
        with self.assertRaises(DatabaseError) as raised:
            self.connection.run('COMMIT')
        self.assertEqual(raised.exception.args[0]['C'], '55000')

    def test_fake_feed_registration_does_not_supply_payload_or_remove_obligation(self):
        prestate, report = self.complete(fake_feed=True)
        result = self.collect(prestate, report)
        self.assertEqual(result['requiredFactCount'], '1')
        self.assertEqual(result['payload']['state'], 'unavailable')
        self.assertIs(result['feedFactQualified'], False)
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.feed_tx'), [[1]])

    def test_complete_ordered_two_document_sources_and_native_time_origin(self):
        self.connection.run('ROLLBACK')
        self.prepared = prepare((native_document('first'), native_document('second')))
        self.connection.run('BEGIN'); self.admit(self.prepared)
        prestate, report = self.complete()
        result = self.collect(prestate, report)
        self.assertEqual([d['documentId'] for d in result['documents']], ['first','second'])
        self.assertEqual([d['ordinal'] for d in result['documents']], ['0','1'])
        parent = self.connection.run("SELECT encode(record_send(r),'hex') FROM truss.schema_rev r WHERE r.rev=CAST(:rev AS int)", rev=result['revision'])[0][0]
        self.assertEqual(result['originalRevisionRecordHex'], parent)
        self.assertNotIn('acceptedAt', result)
        self.assertNotIn('databaseRole', result)

    def test_copied_prestate_and_wrong_report_refuse(self):
        prestate, report = self.complete()
        with self.assertRaises(ValueError): self.collect(dataclasses.replace(prestate), report)
        with self.assertRaises(DatabaseError) as raised: self.collect(prestate, b'substituted')
        self.assertEqual(raised.exception.args[0]['C'], '55000')

    def test_same_identity_document_substitution_refuses(self):
        prestate, report = self.complete()
        self.connection.run('UPDATE truss.schema_doc SET document=document || :suffix', suffix=' ')
        with self.assertRaises(DatabaseError) as raised: self.collect(prestate, report)
        self.assertEqual(raised.exception.args[0]['C'], '55000')

    def test_foreign_native_cut_refuses(self):
        prestate, report = self.complete()
        value = json.loads(prestate.original_bytes)
        with self.assertRaises(DatabaseError) as raised:
            self.connection.run("SELECT truss.runtime_collect_catalog_revision_obligation(:w,:o,:g,CAST(:pre AS jsonb),decode(:report,'hex'))",
                w=str(int(value['writerXid'])+1), o=value['operationOrdinal'],
                g=str(int(value['effectGeneration'])+2),
                pre=prestate.original_bytes.decode(), report=report.hex())
        self.assertEqual(raised.exception.args[0]['C'], '55000')

    def test_later_fake_feed_member_does_not_change_required_source(self):
        prestate, report = self.complete()
        before = collect_catalog_revision_obligation(self.connection, self.prepared, prestate, report)
        self.connection.run("""INSERT INTO truss.feed_tx(
            source_epoch,feed_profile,original_writer_xid,
            original_context_bytes,manifest_profile_bytes)
            VALUES('fake-epoch','fake-profile',pg_current_xact_id(),
                   decode('01','hex'),decode('02','hex'))""")
        self.connection.run("""INSERT INTO truss.feed_member(
            source_epoch,feed_profile,original_writer_xid,registration_address,
            fact_kind,original_fact_key_bytes,original_fact_key_profile_bytes,
            original_payload_bytes,original_payload_profile_bytes,
            original_payload_sha256,original_owner_context_bytes,
            original_write_at,original_fact_clock_bytes)
            VALUES('fake-epoch','fake-profile',pg_current_xact_id(),1,'revision',
              decode('01','hex'),decode('01','hex'),decode('02','hex'),
              decode('01','hex'),sha256(decode('02','hex')),decode('01','hex'),
              clock_timestamp(),decode('01','hex'))""")
        self.assertEqual(collect_catalog_revision_obligation(
            self.connection, self.prepared, prestate, report), before)
        # The separate whole-physical verifier continues to detect this change.
        from truss._catalog_completion import verify_catalog_completion_physical
        with self.assertRaises(DatabaseError) as raised:
            verify_catalog_completion_physical(self.connection, self.prepared, prestate, report)
        self.assertEqual(raised.exception.args[0]['C'], '55000')

    def test_whole_acceptance_savepoint_rollback_preserves_host_work(self):
        self.connection.run('CREATE TEMP TABLE obligation_host_work(value text)')
        self.connection.run("INSERT INTO obligation_host_work VALUES('preserve')")
        self.connection.run('SAVEPOINT acceptance')
        prestate, report = self.complete()
        self.assertEqual(self.collect(prestate, report)['requiredFactCount'], '1')
        self.connection.run('ROLLBACK TO SAVEPOINT acceptance')
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'), [[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.schema_rev WHERE rev>0'), [[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.schema_doc'), [[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'), [[0]])
        self.assertEqual(self.connection.run('SELECT value FROM obligation_host_work'), [['preserve']])
