# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual native fresh lifecycle fields and insert-only event evidence."""
import dataclasses
import hashlib
import json
import unittest
from unittest.mock import patch
from pg8000.exceptions import DatabaseError
from test_catalog_staging import CatalogNativeFixture, ROOT, native_document
from test_preparation import prepare
from truss import CatalogDocument
from truss._catalog_staging import stage_catalog_report_basis
from truss._catalog_report import require_current_catalog_report_basis
from truss import _catalog_lifecycle as lifecycle

class CatalogLifecycleTests(CatalogNativeFixture, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:c.run((ROOT/'packages/postgresql/native/catalog-report/empty-graph.sql').read_text())
        finally:c.close()

    def report(self):
        basis=stage_catalog_report_basis(self.connection,self.prepared,origin_bytes=b'{}')
        from truss._catalog_report import _original_bases
        result=_original_bases[id(basis)][6]
        self.start=lifecycle._issued[id(result)][7]
        return basis
    def cut(self):return tuple(self.connection.run('SELECT original_writer_xid::text,operation_ordinal::text,effect_generation::text FROM truss.row_home_operation')[0])
    def collect(self):return lifecycle.collect_catalog_lifecycle(self.connection,self.prepared,'1',self.cut(),self.start)

    def test_original_fields_and_unchanged_commit_barrier(self):
        basis=self.report();value=json.loads(basis.basis_bytes)
        self.assertEqual(value['targetReportInterfaceVersion'],'truss-acceptance-report/0.3.0-proposal')
        self.assertEqual(value['fields']['reactivations'],[])
        policy=(ROOT/'packages/python/src/truss/_profiles/fresh-catalog-lifecycle.json').read_bytes()
        self.assertEqual(value['fields']['lifecycleProfile']['sha256'],hashlib.sha256(policy).hexdigest())
        evidence=json.loads(bytes.fromhex(value['lifecycleEvidenceHex']))
        self.assertEqual(evidence['expectedInsertEvents'],value['nativeCut']['effectGeneration'])
        self.assertFalse(value['acceptedReportQualified'])
        self.assertFalse(value['supportSemanticsQualified'])
        original=json.loads(self.prepared.report_evidence_bytes)
        for field in ('ownerObservations','observationCoverage','coreAssertionIdentities'):
            self.assertEqual(value[field],original[field])
        require_current_catalog_report_basis(basis,self.connection,self.prepared)
        with self.assertRaises(DatabaseError) as caught:self.connection.run('COMMIT')
        self.assertEqual(caught.exception.args[0]['C'],'55000')

    def test_restored_retirement_refuses_even_with_same_final_rows(self):
        self.report()
        self.connection.run('UPDATE truss.type_def SET retired_rev=1')
        self.connection.run('UPDATE truss.type_def SET retired_rev=NULL')
        with self.assertRaises(DatabaseError) as caught:self.collect()
        self.assertEqual(caught.exception.args[0]['C'],'55000')

    def test_observer_disabled_on_every_contributing_table_refuses(self):
        self.report()
        for table in ('schema_rev','schema_doc','type_def','prop_def','key_def','key_lifecycle_history','rel_def','rel_endpoint','relationship_lineage','schema_head','catalog_acceptance_report'):
            with self.subTest(table=table):
                self.connection.run('SAVEPOINT observer_test')
                self.connection.run('ALTER TABLE truss.'+table+' DISABLE TRIGGER runtime_catalog_generation')
                with self.assertRaises(DatabaseError):self.collect()
                self.connection.run('ROLLBACK TO observer_test');self.connection.run('RELEASE observer_test')

    def test_observer_body_substitution_refuses(self):
        self.report()
        self.connection.run("CREATE OR REPLACE FUNCTION truss.runtime_observe_catalog_generation() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN RETURN NULL; END;$$")
        with self.assertRaises(DatabaseError):self.collect()

    def test_noop_update_is_not_insert_only(self):
        self.report();self.connection.run('UPDATE truss.prop_def SET name=name')
        with self.assertRaises(DatabaseError):self.collect()

    def test_policy_copy_foreign_preparation_and_stale_custody_refuse(self):
        self.report();result=self.collect()
        with self.assertRaises(ValueError):lifecycle.require_current_catalog_lifecycle(dataclasses.replace(result),self.connection,self.prepared)
        foreign=prepare((native_document('foreign'),))
        with self.assertRaises(ValueError):lifecycle.require_current_catalog_lifecycle(result,self.connection,foreign)
        with patch.object(lifecycle,'_policy_bytes',return_value=b'{}'):
            with self.assertRaises(DatabaseError):self.collect()

    def test_missing_policy_rolls_back_whole_stage(self):
        with patch.object(lifecycle,'_policy_bytes',side_effect=FileNotFoundError('missing original policy')):
            with self.assertRaises(FileNotFoundError):self.report()
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])

    def test_all_definition_families_and_two_documents(self):
        document={'umf':'0.7.0','id':'cohort','vocabularies':{},'extensions':{},'modules':[{'id':'m','namespace':'m','elements':[
            *[{'id':name,'kind':'record','members':[{'module':'m','element':name+'-label'}],'keys':[{'id':'label-key','name':'label-key','fields':[{'module':'m','element':name+'-label'}],'primary':True}],'extensions':{}} for name in ('A','B')],
            *[{'id':name+'-label','name':name+'-label','kind':'field','scalarType':'string','nullability':'required','cardinality':'one','extensions':{}} for name in ('A','B')]],
            'relationships':[{'id':'A-B','name':'A-B','source':[{'module':'m','element':'A'}],'target':[{'module':'m','element':'B','key':'label-key'}],'sourceMultiplicity':{'min':0,'max':1},'targetMultiplicity':{'min':0,'max':2},'targetLifecycle':'independent','directed':True}]}]}
        self.connection.run('ROLLBACK');self.connection.run('BEGIN')
        self.prepared=prepare((CatalogDocument('cohort','r1',json.dumps(document).encode()),native_document('other')));self.admit(self.prepared)
        value=json.loads(self.report().basis_bytes)
        self.assertEqual(value['fields']['counts']['relationshipsAdded'],'1')
        self.assertEqual(value['fields']['counts']['keysAdded'],'2')
        self.assertEqual(value['fields']['reactivations'],[])

    def test_unexpected_schema_change_refuses(self):
        self.report()
        self.connection.run("INSERT INTO truss.schema_change SELECT 1,0,'type',type_id,'{}'::jsonb,'{}'::jsonb FROM truss.type_def")
        with self.assertRaises(DatabaseError):self.collect()

    def test_original_retained_identity_is_not_fresh(self):
        self.connection.run('ROLLBACK');self.connection.run('BEGIN')
        wire=self.connection.run('SELECT truss.runtime_capture_catalog_prestate()')[0][0]
        prestate=json.loads(bytes.fromhex(wire));prestate['types']=[{'type_id':123,'retired_rev':0}]
        self.connection.run("SELECT * FROM truss.runtime_admit_operation('catalog-acceptance',decode('01','hex'),decode(:input,'hex'),decode(:prestate,'hex'),decode('04','hex'),decode('05','hex'),decode('06','hex'))",input=self.prepared.input_bytes.hex(),prestate=json.dumps(prestate).encode().hex())
        with self.assertRaises(DatabaseError):self.report()

    def test_substituted_response_cannot_supply_lifecycle_authority(self):
        self.report()
        self.cut_value=self.cut()
        original_run=self.connection.run
        def substitute(sql,**parameters):
            rows=original_run(sql,**parameters)
            value=json.loads(rows[0][0]);value['acceptedReportQualified']=True
            return [[json.dumps(value)]]
        with patch.object(self.connection,'run',side_effect=substitute):
            with self.assertRaises(ValueError):
                lifecycle.collect_catalog_lifecycle(self.connection,self.prepared,'1',self.cut_value,self.start)

    def test_staged_without_original_start_cannot_issue_lifecycle(self):
        self.stage()
        with self.assertRaises(ValueError):
            lifecycle.collect_catalog_lifecycle(self.connection,self.prepared,'1',self.cut(),lifecycle.LifecycleStart())

    def test_column_filtered_observer_cannot_hide_retirement(self):
        self.report()
        self.connection.run('DROP TRIGGER runtime_catalog_generation ON truss.prop_def')
        self.connection.run('CREATE TRIGGER runtime_catalog_generation AFTER INSERT OR UPDATE OF name OR DELETE ON truss.prop_def FOR EACH ROW EXECUTE FUNCTION truss.runtime_observe_catalog_generation()')
        self.connection.run('ALTER TABLE truss.prop_def ENABLE ALWAYS TRIGGER runtime_catalog_generation')
        before=self.cut()
        self.connection.run('UPDATE truss.prop_def SET retired_rev=1')
        self.connection.run('UPDATE truss.prop_def SET retired_rev=NULL')
        self.assertEqual(self.cut(),before)
        with self.assertRaises(DatabaseError):self.collect()

    def test_spoofed_start_cut_refuses_before_sql(self):
        class NoCalls:
            def run(self,*args,**kwargs):raise AssertionError('SQL must not run')
        class Spoof:
            def __eq__(self,other):return True
            def __getitem__(self,key):return '0'
        for cut in (Spoof(),('1','0',0,'[]'),('1','0','0'),('1','0','0','[]','extra')):
            with self.assertRaises(ValueError):lifecycle.begin_catalog_lifecycle(NoCalls(),self.prepared,cut)

    def test_deferred_observer_refuses_at_original_start(self):
        self.connection.run('DROP TRIGGER runtime_catalog_generation ON truss.prop_def')
        self.connection.run('CREATE CONSTRAINT TRIGGER runtime_catalog_generation AFTER INSERT OR UPDATE OR DELETE ON truss.prop_def DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_observe_catalog_generation()')
        self.connection.run('ALTER TABLE truss.prop_def ENABLE ALWAYS TRIGGER runtime_catalog_generation')
        with self.assertRaises(DatabaseError):self.report()
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
