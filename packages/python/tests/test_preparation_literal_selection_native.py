"""Original enrolled Weft SQL inside private native permit checks."""
from importlib.resources import files
import psycopg
import test_preparation_literal_permit_native as original


class PreparationLiteralSelectionNativeTests(original.PreparationLiteralPermitNativeTests):
    test_original_coordinator_cannot_remint_in_later_transaction = None

    def prepare_component(self, admin, owner):
        super().prepare_component(admin,owner)
        admin.execute(files('truss').joinpath('_security_bootstrap','preparation-literal-selection.sql').read_text())
        admin.execute("CREATE FUNCTION truss.literal_selection_probe(a int4,n uuid) RETURNS jsonb LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ SELECT truss.select_preparation_literal_rows(a,n) $$")
        admin.execute('REVOKE ALL ON FUNCTION truss.literal_selection_probe(int4,uuid) FROM PUBLIC')
        admin.execute('GRANT EXECUTE ON FUNCTION truss.literal_selection_probe(int4,uuid) TO products_person')
        admin.execute("CREATE FUNCTION truss.literal_selection_corrupt_probe() RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ UPDATE truss.object SET props='{}'::jsonb WHERE type_id=1 AND props->'1'->>'text'='baz' $$")
        admin.execute('REVOKE ALL ON FUNCTION truss.literal_selection_corrupt_probe() FROM PUBLIC')
        admin.execute('GRANT EXECUTE ON FUNCTION truss.literal_selection_corrupt_probe() TO products_person')

    def after_claim_commit(self, admin, session, coordinator, anchor, nonce, params):
        # Keep the original attempt untouched: the parent permit negatives
        # intentionally invalidate cuts and are covered in their own module.
        data = session.connection
        data.execute("SET LOCAL statement_timeout='10s'")
        data.execute("SELECT truss.literal_permit_probe(%s,%s,'cut')",(anchor,nonce))
        def select():
            return data.execute('SELECT truss.literal_selection_probe(%s,%s)',(anchor,nonce)).fetchone()[0]
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            with data.transaction(): select()
        with coordinator.transaction(force_rollback=True):
            coordinator.execute("SELECT truss.literal_permit_probe(%s,%s,'issue')",(anchor,nonce))
            result = select()
            self.assertFalse(result['authority']);self.assertFalse(result['securityReady'])
            self.assertEqual(result['preflightsCompleted'],4)
            self.assertEqual(len(result['rows']),1)
            self.assertEqual(result['rows'][0][2],'bar')
            # Same-D mutation of a different, unselected row must still fail
            # population validation before any authorized selected row returns.
            with data.transaction(force_rollback=True):
                # D sees its own assessor corruption without replacing RR.
                data.execute("SELECT truss.literal_selection_corrupt_probe()")
                with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                    with data.transaction(): select()
            self.assertEqual(select()['rows'],result['rows'])
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            with data.transaction(): select()
