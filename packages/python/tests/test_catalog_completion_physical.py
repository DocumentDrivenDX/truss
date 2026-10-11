"""Administrative post-head physical correspondence, never accepted catalog authority.

The report bytes are deliberately a non-semantic fixture. These tests establish
native image comparison and refusal, not a complete report producer or commit.
"""
import json
import unittest
from test_catalog_staging import CatalogNativeFixture,ROOT
from pg8000.exceptions import DatabaseError

class CatalogCompletionPhysicalTests(CatalogNativeFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:
            c.run((ROOT/'packages/postgresql/native/catalog-completion/physical-poststate.sql').read_text())
            c.run((ROOT/'packages/postgresql/native/catalog-report/empty-graph.sql').read_text())
        finally:c.close()
    def cut(self):
        return self.connection.run('SELECT original_writer_xid::text,operation_ordinal::text,effect_generation::text FROM truss.row_home_operation')[0]
    def capture(self,rev):
        w,o,g=self.cut()
        return self.connection.run('SELECT truss.runtime_capture_catalog_completion_prestate(:w,:o,:g,CAST(:rev AS int))::text',w=w,o=o,g=g,rev=rev)[0][0]
    def publish_fixture(self,rev,report=b'non-semantic physical fixture'):
        self.connection.run("INSERT INTO truss.catalog_acceptance_report VALUES(CAST(:rev AS int),decode(:report,'hex'))",rev=rev,report=report.hex())
        self.connection.run('UPDATE truss.schema_head SET rev=CAST(:rev AS int)',rev=rev)
    def verify(self,rev,prestate,report=b'non-semantic physical fixture',generation=None):
        w,o,g=self.cut()
        return self.connection.run("SELECT truss.runtime_verify_catalog_completion_physical(:w,:o,:g,CAST(:rev AS int),CAST(:prestate AS jsonb),decode(:report,'hex'))::text",w=w,o=o,g=g if generation is None else generation,rev=rev,prestate=prestate,report=report.hex())[0][0]
    def test_fresh_post_head_complete_images_without_commit_authority(self):
        catalog=self.stage();prestate=self.capture(catalog.revision)
        prior=json.loads(prestate)['effectGeneration']
        self.publish_fixture(catalog.revision)
        result=json.loads(self.verify(catalog.revision,prestate))
        self.assertEqual(int(result['effectGeneration']),int(prior)+2)
        self.assertEqual(result['scope'],'catalog_completion_physical_only')
        self.assertFalse(result['acceptedReportQualified'])
        self.assertEqual(self.connection.run('SELECT phase FROM truss.row_home_operation'),[['admitted']])
        with self.assertRaises(DatabaseError) as raised:self.connection.run('COMMIT')
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_pre_head_generation_cannot_be_reused(self):
        catalog=self.stage();prestate=self.capture(catalog.revision)
        old=json.loads(prestate)['effectGeneration']
        self.publish_fixture(catalog.revision)
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate,generation=old)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_same_count_changed_definition_refuses_even_with_counter_reset(self):
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision);g=self.cut()[2]
        self.connection.run("UPDATE truss.prop_def SET name='substituted'")
        self.connection.run('UPDATE truss.row_home_operation SET effect_generation=CAST(:g AS bigint)',g=g)
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_wrong_report_bytes_refuse(self):
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision)
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate,report=b'substituted')
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_extra_post_head_graph_effect_and_full_host_savepoint_rollback(self):
        self.connection.run('CREATE TEMP TABLE completion_host_work(value text)')
        self.connection.run("INSERT INTO completion_host_work VALUES('preserve')")
        self.connection.run('SAVEPOINT whole_catalog')
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision)
        self.connection.run("INSERT INTO truss.key_bucket_guard VALUES(sha256('namespace'::bytea),sha256('key'::bytea),0)")
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
        self.connection.run('ROLLBACK TO SAVEPOINT whole_catalog')
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])
        self.assertEqual(self.connection.run('SELECT value FROM completion_host_work'),[['preserve']])
    def test_original_python_basis_capture_and_poststate_composition(self):
        import dataclasses
        from truss._catalog_staging import stage_catalog_report_basis
        from truss._catalog_completion import capture_catalog_completion_prestate,verify_catalog_completion_physical
        basis=stage_catalog_report_basis(self.connection,self.prepared,origin_bytes=b'{}')
        capture=capture_catalog_completion_prestate(self.connection,self.prepared,basis)
        revision=json.loads(basis.basis_bytes)['fields']['rev']
        self.publish_fixture(revision)
        with self.assertRaises(ValueError):
            verify_catalog_completion_physical(self.connection,self.prepared,dataclasses.replace(capture),b'non-semantic physical fixture')
        result=json.loads(verify_catalog_completion_physical(self.connection,self.prepared,capture,b'non-semantic physical fixture'))
        self.assertFalse(result['acceptedReportQualified'])
    def test_extra_observed_event_restored_rows_still_refuses(self):
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision)
        self.connection.run('UPDATE truss.prop_def SET name=name')
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_descriptor_drift_with_unchanged_row_images_refuses(self):
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision)
        self.connection.run('ALTER TABLE truss.prop_def RENAME COLUMN name TO altered_name')
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_existing_target_report_refuses_prestate(self):
        catalog=self.stage()
        self.connection.run("INSERT INTO truss.catalog_acceptance_report VALUES(CAST(:rev AS int),decode('01','hex'))",rev=catalog.revision)
        with self.assertRaises(DatabaseError) as raised:self.capture(catalog.revision)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_operation_reset_fields_and_original_artifacts(self):
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision)
        self.assertEqual(self.connection.run('SELECT phase,readiness_generation,sealed_generation,application_generation,application_result_bytes FROM truss.row_home_operation'),[['admitted',None,None,None,None]])
        self.assertFalse(json.loads(self.verify(catalog.revision,prestate))['acceptedReportQualified'])
        with self.assertRaises(DatabaseError) as raised:
            self.connection.run("UPDATE truss.row_home_operation SET original_definition_bytes=decode('ff','hex')")
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_missing_head_and_report_refuse(self):
        for statement in ('DELETE FROM truss.schema_head','DELETE FROM truss.catalog_acceptance_report'):
            with self.subTest(statement=statement):
                self.connection.run('SAVEPOINT missing_probe')
                catalog=self.stage();prestate=self.capture(catalog.revision)
                if 'catalog_acceptance_report' in statement:
                    # Missing report while head advances gives only one event.
                    self.connection.run('UPDATE truss.schema_head SET rev=CAST(:rev AS int)',rev=catalog.revision)
                else:
                    self.publish_fixture(catalog.revision);self.connection.run(statement)
                with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate)
                self.assertEqual(raised.exception.args[0]['C'],'55000')
                self.connection.run('ROLLBACK TO SAVEPOINT missing_probe')
    def test_disabled_generation_observer_refuses(self):
        catalog=self.stage()
        self.connection.run('ALTER TABLE truss.schema_head DISABLE TRIGGER runtime_catalog_generation')
        with self.assertRaises(DatabaseError) as raised:self.capture(catalog.revision)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_ordinary_role_cannot_invoke_physical_collector(self):
        catalog=self.stage();w,o,g=self.cut()
        self.connection.run('CREATE ROLE catalog_physical_probe')
        self.connection.run('GRANT USAGE ON SCHEMA truss TO catalog_physical_probe')
        self.connection.run('GRANT EXECUTE ON FUNCTION truss.runtime_capture_catalog_completion_physical(text,text,text,int) TO catalog_physical_probe')
        self.connection.run('SET LOCAL ROLE catalog_physical_probe')
        with self.assertRaises(DatabaseError) as raised:
            self.connection.run('SELECT truss.runtime_capture_catalog_completion_physical(:w,:o,:g,CAST(:rev AS int))',w=w,o=o,g=g,rev=catalog.revision)
        self.assertEqual(raised.exception.args[0]['C'],'42501')
    def test_late_head_trigger_graph_effect_refuses(self):
        self.connection.run("CREATE FUNCTION truss.physical_late_graph() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN INSERT INTO truss.key_bucket_guard VALUES(sha256('late'::bytea),sha256('key'::bytea),0); RETURN NULL; END;$$")
        self.connection.run('CREATE TRIGGER physical_late_graph AFTER UPDATE ON truss.schema_head FOR EACH ROW EXECUTE FUNCTION truss.physical_late_graph()')
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision)
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_foreign_native_cut_refuses(self):
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision)
        value=json.loads(prestate);value['writerXid']=str(int(value['writerXid'])+1)
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,json.dumps(value))
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_extra_report_membership_refuses(self):
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision);g=self.cut()[2]
        self.connection.run("INSERT INTO truss.schema_rev(rev,origin) VALUES(CAST(:rev AS int),'{}'::jsonb)",rev=str(int(catalog.revision)+1))
        self.connection.run("INSERT INTO truss.catalog_acceptance_report VALUES(CAST(:rev AS int),decode('ff','hex'))",rev=str(int(catalog.revision)+1))
        self.connection.run('UPDATE truss.row_home_operation SET effect_generation=CAST(:g AS bigint)',g=g)
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_trigger_procedure_owner_drift_refuses(self):
        self.connection.run('CREATE ROLE catalog_trigger_owner')
        self.connection.run('CREATE FUNCTION truss.physical_owner_probe() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER AS $$BEGIN RETURN NULL; END;$$')
        self.connection.run('CREATE TRIGGER physical_owner_probe AFTER UPDATE ON truss.schema_head FOR EACH ROW EXECUTE FUNCTION truss.physical_owner_probe()')
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision)
        self.connection.run('ALTER FUNCTION truss.physical_owner_probe() OWNER TO catalog_trigger_owner')
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_rewrite_rule_action_drift_refuses(self):
        self.connection.run('CREATE RULE physical_rule_probe AS ON UPDATE TO truss.setting DO ALSO SELECT 1')
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision)
        self.connection.run('CREATE OR REPLACE RULE physical_rule_probe AS ON UPDATE TO truss.setting DO ALSO SELECT 2')
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_index_descriptor_rename_refuses(self):
        catalog=self.stage();prestate=self.capture(catalog.revision)
        self.publish_fixture(catalog.revision)
        self.connection.run('ALTER INDEX truss.module_access_qualified_pk RENAME TO changed_index_name')
        with self.assertRaises(DatabaseError) as raised:self.verify(catalog.revision,prestate)
        self.assertEqual(raised.exception.args[0]['C'],'55000')
    def test_hostile_scope_comparison_is_not_invoked(self):
        from truss._catalog_staging import stage_catalog_report_basis
        from truss._catalog_completion import capture_catalog_completion_prestate,verify_catalog_completion_physical
        basis=stage_catalog_report_basis(self.connection,self.prepared,origin_bytes=b'{}')
        capture=capture_catalog_completion_prestate(self.connection,self.prepared,basis)
        class Hostile:
            def __ne__(self,other):raise AssertionError('Hostile equality invoked')
        object.__setattr__(capture,'scope',Hostile())
        with self.assertRaises(ValueError):
            verify_catalog_completion_physical(self.connection,self.prepared,capture,b'non-semantic physical fixture')
