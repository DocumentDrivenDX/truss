# SPDX-License-Identifier: MIT OR Apache-2.0
"""Generation correspondence on real catalog staging; no acceptance authority."""
import unittest
from pg8000.exceptions import DatabaseError
from test_catalog_staging import CatalogNativeFixture

class CatalogGenerationNativeTests(CatalogNativeFixture, unittest.TestCase):
    def snapshot(self):
        return self.connection.run("SELECT jsonb_build_object('operation',(SELECT to_jsonb(o) FROM truss.row_home_operation o),'revisions',(SELECT jsonb_agg(to_jsonb(r) ORDER BY rev) FROM truss.schema_rev r),'documents',(SELECT jsonb_agg(to_jsonb(d) ORDER BY rev,ord) FROM truss.schema_doc d),'types',(SELECT jsonb_agg(to_jsonb(t) ORDER BY type_id) FROM truss.type_def t),'properties',(SELECT jsonb_agg(to_jsonb(p) ORDER BY prop_id) FROM truss.prop_def p))::text")[0][0]

    def test_suppression_and_rewrites_restore_original_catalog_and_host_work(self):
        self.connection.run('CREATE TEMP TABLE caller_work(value text)')
        self.connection.run("INSERT INTO caller_work VALUES('preserve')")
        for timing, body in (
            ('BEFORE', 'RETURN NULL;'),
            ('BEFORE', 'NEW.effect_generation:=NEW.effect_generation+1; RETURN NEW;'),
            ('BEFORE', "NEW.original_input_bytes:=decode('ff','hex'); RETURN NEW;"),
            ('AFTER', "IF pg_trigger_depth()=2 THEN UPDATE truss.row_home_operation SET effect_generation=effect_generation+1; END IF; RETURN NULL;"),
            ('AFTER', "IF pg_trigger_depth()=2 THEN UPDATE truss.row_home_operation SET original_input_bytes=decode('ff','hex'); END IF; RETURN NULL;"),
        ):
            with self.subTest(timing=timing, body=body):
                self.connection.run('SAVEPOINT trigger_case')
                self.connection.run('CREATE FUNCTION pg_temp.alter_operation() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN '+body+' END;$$')
                self.connection.run('CREATE TRIGGER alter_operation '+timing+' UPDATE ON truss.row_home_operation FOR EACH ROW EXECUTE FUNCTION pg_temp.alter_operation()')
                before=self.snapshot()
                with self.assertRaises(DatabaseError): self.stage()
                self.assertEqual(self.snapshot(),before)
                self.assertEqual(self.connection.run('SELECT value FROM caller_work'),[['preserve']])
                self.connection.run('ROLLBACK TO trigger_case')
                self.connection.run('RELEASE trigger_case')

    def test_equal_value_late_events_clear_all_proofs_and_preserve_originals(self):
        self.stage()
        for phase in ('effects_ready','row_sealed'):
            with self.subTest(phase=phase):
                self.connection.run("UPDATE truss.row_home_operation SET phase=:phase,readiness_generation=effect_generation,sealed_generation=CASE WHEN :phase='row_sealed' THEN effect_generation ELSE NULL END",phase=phase)
                original=self.connection.run('SELECT original_context_bytes,original_definition_bytes,original_input_bytes,original_prestate_bytes,admitted_candidate_bytes,effect_obligation_bytes,original_group_custody_bytes,effect_generation FROM truss.row_home_operation')[0]
                self.connection.run('UPDATE truss.prop_def SET name=name')
                after=self.connection.run('SELECT original_context_bytes,original_definition_bytes,original_input_bytes,original_prestate_bytes,admitted_candidate_bytes,effect_obligation_bytes,original_group_custody_bytes,effect_generation FROM truss.row_home_operation')[0]
                self.assertEqual(after[:-1],original[:-1])
                self.assertEqual(after[-1],original[-1]+1)
                self.assertEqual(self.connection.run('SELECT phase,readiness_generation,sealed_generation,application_generation,application_result_bytes FROM truss.row_home_operation'),[['admitted',None,None,None,None]])

    def test_generation_exhaustion_restores_catalog_effect(self):
        self.stage()
        self.connection.run('UPDATE truss.row_home_operation SET effect_generation=9223372036854775807')
        before=self.snapshot()
        self.connection.run('SAVEPOINT exhausted')
        with self.assertRaises(DatabaseError) as caught:
            self.connection.run("UPDATE truss.prop_def SET name='changed'")
        self.assertEqual(caught.exception.args[0]['C'],'54000')
        self.connection.run('ROLLBACK TO exhausted')
        self.assertEqual(self.snapshot(),before)
