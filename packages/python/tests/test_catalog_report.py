"""Original owner evidence and native fresh-graph report basis; no acceptance."""
import dataclasses
import json
from pathlib import Path
import unittest
from test_catalog_staging import CatalogNativeFixture
from test_preparation import prepare,document
from truss import CatalogDocument
from truss._catalog_staging import stage_catalog_report_basis
from truss._catalog_report import require_current_catalog_report_basis
ROOT=Path(__file__).resolve().parents[3]

class NativeCatalogReportTests(CatalogNativeFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:c.run((ROOT/'packages/postgresql/native/catalog-report/empty-graph.sql').read_text())
        finally:c.close()
    def report(self,connection=None):
        return stage_catalog_report_basis(self.connection if connection is None else connection,self.prepared,origin_bytes=b'{}')
    def test_complete_original_basis_and_current_custody(self):
        result=self.report();payload=json.loads(result.basis_bytes)
        self.assertFalse(payload['acceptedReportQualified'])
        self.assertEqual(payload['fields']['rebinds'],[])
        self.assertEqual(payload['fields']['counts']['typesAdded'],'1')
        self.assertEqual(bytes.fromhex(payload['ownerEvidenceHex']),self.prepared.report_evidence_bytes)
        self.assertIn('journal',payload['noRebindEvidence']['emptyScope'])
        self.assertEqual(payload['noRebindEvidence']['preEffectGeneration'],'0')
        self.assertIn('assertions',result.missing_fields)
        require_current_catalog_report_basis(result,self.connection,self.prepared)
        with self.assertRaises(ValueError):require_current_catalog_report_basis(dataclasses.replace(result),self.connection,self.prepared)
        with self.assertRaises(ValueError):require_current_catalog_report_basis(result,object(),self.prepared)
        self.connection.run('UPDATE truss.prop_def SET name=name')
        with self.assertRaises(ValueError):require_current_catalog_report_basis(result,self.connection,self.prepared)
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])
    def refused(self,sqlstate):
        from pg8000.exceptions import DatabaseError
        with self.assertRaises(DatabaseError) as error:self.report()
        self.assertEqual(error.exception.args[0]['C'],sqlstate)
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT effect_generation::text FROM truss.row_home_operation'),[['0']])
    def test_equal_generation_cannot_hide_changed_native_values(self):
        result=self.report()
        generation=self.connection.run('SELECT effect_generation::text FROM truss.row_home_operation')[0][0]
        self.connection.run("UPDATE truss.prop_def SET name='changed' WHERE name IS NOT NULL")
        self.connection.run('UPDATE truss.row_home_operation SET effect_generation=CAST(:generation AS bigint)',generation=generation)
        with self.assertRaisesRegex(ValueError,'Different native effects'):
            require_current_catalog_report_basis(result,self.connection,self.prepared)

    def test_erased_prior_graph_write_cannot_claim_empty_start(self):
        self.connection.run("INSERT INTO truss.key_bucket_guard VALUES(sha256('namespace'::bytea),sha256('key'::bytea),0)")
        self.connection.run('DELETE FROM truss.key_bucket_guard')
        self.refused('55000')

    def test_populated_key_guard_refuses_before_effects(self):
        self.connection.run("INSERT INTO truss.key_bucket_guard VALUES(sha256('namespace'::bytea),sha256('key'::bytea),0)")
        self.refused('55000')
    def test_nonempty_journal_stage_is_not_ignored(self):
        self.connection.run("INSERT INTO truss.row_home_journal_stage SELECT original_writer_xid,operation_ordinal,'start',0,0,'stage' FROM truss.row_home_operation")
        self.refused('55000')
    def test_journal_child_is_uncovered_not_silently_omitted(self):
        self.connection.run('CREATE TABLE truss.journal_child PARTITION OF truss.journal DEFAULT')
        self.refused('0A000')
    def test_rls_and_extra_scope_refuse(self):
        for sql,state in (('ALTER TABLE truss.object ENABLE ROW LEVEL SECURITY','55000'),('CREATE TABLE truss.extra_graph(value text)','0A000')):
            self.connection.run('SAVEPOINT source_probe')
            self.connection.run(sql);self.refused(state)
            self.connection.run('ROLLBACK TO SAVEPOINT source_probe')
    def test_old_repeatable_read_snapshot_refuses(self):
        self.connection.run('ROLLBACK')
        self.connection.run('BEGIN ISOLATION LEVEL REPEATABLE READ')
        self.connection.run('SELECT count(*) FROM truss.key_bucket_guard')
        other=self.Connection(**self.kwargs)
        try:
            other.run("INSERT INTO truss.key_bucket_guard VALUES(sha256('namespace'::bytea),sha256('key'::bytea),0)")
            self.admit(self.prepared)
            self.refused('0A000')
        finally:
            self.connection.run('ROLLBACK')
            other.run('DELETE FROM truss.key_bucket_guard')
            other.close()

    def test_truncate_committed_graph_state_refuses(self):
        self.connection.run('ROLLBACK')
        other=self.Connection(**self.kwargs)
        try:
            other.run("INSERT INTO truss.key_bucket_guard VALUES(sha256('namespace'::bytea),sha256('key'::bytea),0)")
            self.connection.run('BEGIN');self.admit(self.prepared)
            self.connection.run('TRUNCATE truss.key_bucket_guard CASCADE')
            self.refused('55000')
        finally:
            self.connection.run('ROLLBACK')
            other.run('DELETE FROM truss.key_bucket_guard');other.close()

    def test_raw_writer_lock_conflict_refuses_without_waiting(self):
        other=self.Connection(**self.kwargs)
        try:
            other.run('BEGIN');other.run('LOCK TABLE truss.object IN ROW EXCLUSIVE MODE')
            self.refused('55P03')
        finally:other.run('ROLLBACK');other.close()
    def test_late_graph_effect_rolls_back_all_staging(self):
        self.connection.run('CREATE TEMP TABLE host_work(value text)')
        self.connection.run("INSERT INTO host_work VALUES('preserve')")
        original=self.connection
        class LatePort:
            @property
            def columns(self):return original.columns
            def run(self,sql,**parameters):
                if sql.startswith('SELECT truss.runtime_require_empty_provisional_catalog'):
                    original.run("INSERT INTO truss.object(type_id,rev) SELECT type_id,since_rev FROM truss.type_def")
                return original.run(sql,**parameters)
        from pg8000.exceptions import DatabaseError
        with self.assertRaises(DatabaseError):self.report(LatePort())
        self.assertEqual(original.run('SELECT count(*) FROM truss.object'),[[0]])
        self.assertEqual(original.run('SELECT count(*) FROM truss.schema_doc'),[[0]])
        self.assertEqual(original.run('SELECT effect_generation::text,phase FROM truss.row_home_operation'),[['0','admitted']])
        self.assertEqual(original.run('SELECT value FROM host_work'),[['preserve']])
