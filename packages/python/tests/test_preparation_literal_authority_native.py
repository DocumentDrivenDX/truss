"""Original literal packet + native current human/action/module checks, no permit."""
from importlib.resources import files
import json
import os
from pathlib import Path
import psycopg
from psycopg import sql
from truss._action_role_installation import bootstrap_action_roles_in_transaction
from truss._action_subject_installation import bootstrap_action_subjects_in_transaction
from truss._action_store import observe_action_store_in_transaction
from truss.bulk_action_gateway import ActionRegistration
import test_preparation_sources_native as original


class PreparationLiteralAuthorityNativeTests(original.PreparationSourcesNativeTests):
    expected_home_count = 13
    expected_sequence_count = 5

    def prepare_component(self, admin, owner):
        from adopter_workflow import transaction, success
        config = json.loads(admin.execute('SELECT original_configuration FROM truss.preparation_program_registration').fetchone()[0])
        action = config['actions'][0]
        encode = lambda value: json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
        registration = ActionRegistration(lambda model,pin: encode(action['preparation']))
        ticket = registration.register(encode(action['snapshot']),encode(action['pin']),encode(action['preparation']))
        admin.execute('CREATE ROLE preparation_bulk_editor NOLOGIN;GRANT preparation_bulk_editor TO products_person')
        with transaction(admin) as (assembly,tx):
            store = success(observe_action_store_in_transaction(assembly._host,tx,registration_key=b'original-products-store'))
        with transaction(admin) as (assembly,tx):
            success(bootstrap_action_roles_in_transaction(assembly._host,tx,registration=registration,
                entries=((ticket,(('bulk-editor','preparation_bulk_editor'),)),),store_context=store))
            success(bootstrap_action_subjects_in_transaction(assembly._host,tx,
                bindings=(('products_person',b'"products-person"','human'),),with_action_roles=True))
        super().prepare_component(admin,owner)
        admin.execute(files('truss').joinpath('_security_bootstrap','preparation-authority-lock.sql').read_text())
        admin.execute(files('truss').joinpath('_security_bootstrap','preparation-literal-authority.sql').read_text())
        admin.execute(sql.SQL('ALTER FUNCTION truss.check_preparation_module_authority(jsonb) OWNER TO {}').format(sql.Identifier(owner)))
        # Only the fixture assessor is exposed; native guard helpers stay private.
        admin.execute('CREATE FUNCTION truss.literal_authority_probe(a int4,n uuid) RETURNS jsonb LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET lock_timeout=\'1ms\' AS $$ SELECT truss.check_preparation_literal_authority(a,n) $$')
        admin.execute('REVOKE ALL ON FUNCTION truss.literal_authority_probe(int4,uuid) FROM PUBLIC')
        admin.execute('GRANT EXECUTE ON FUNCTION truss.literal_authority_probe(int4,uuid) TO products_person')

    def before_claim(self, admin, session, coordinator, anchor, nonce, params):
        super().before_claim(admin,session,coordinator,anchor,nonce,params)
        # All original mapping cuts are acquired by D before any policy use.
        self.assertEqual(admin.execute("SELECT count(*) FROM pg_locks WHERE pid=%s AND mode='ShareLock' AND granted AND relation IN ('truss.action_family_registration'::regclass,'truss.action_role_binding'::regclass,'truss.action_subject_binding'::regclass)",(session.connection.info.backend_pid,)).fetchone(),(3,))

    def after_claim_commit(self, admin, session, coordinator, anchor, nonce, params):
        # Keep the inherited D/C source and queued-lock controls first; their
        # savepoint rollback/reacquisition also exercises original mapping cuts.
        super().after_claim_commit(admin,session,coordinator,anchor,nonce,params)
        with coordinator.transaction(force_rollback=True):
            checked = coordinator.execute('SELECT truss.literal_authority_probe(%s,%s)',(anchor,nonce)).fetchone()[0]
            self.assertTrue(checked['currentChecksPassed'])
            self.assertFalse(checked['authority']);self.assertFalse(checked['securityReady'])
            self.assertEqual(checked['remainingNativeObligations']['status'],'required')
        # A committed membership revocation after D's snapshot must be observed
        # by fresh C, without replacing D's original snapshot or XID.
        admin.execute('REVOKE preparation_bulk_editor FROM products_person')
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with coordinator.transaction():
                coordinator.execute('SELECT truss.literal_authority_probe(%s,%s)',(anchor,nonce))
        self.assertEqual(session.connection.execute('SELECT pg_current_snapshot()::text,pg_current_xact_id()::text').fetchone(),self.original_snapshot)
        admin.execute('GRANT preparation_bulk_editor TO products_person')
        with coordinator.transaction(force_rollback=True):
            checked = coordinator.execute('SELECT truss.literal_authority_probe(%s,%s)',(anchor,nonce)).fetchone()[0]
            self.assertTrue(checked['currentChecksPassed'])
        writer = admin.execute("SELECT writer_role FROM truss.module_access WHERE document_id='product-action-demo' AND module='sales'").fetchone()[0]
        admin.execute(sql.SQL('REVOKE {} FROM products_person').format(sql.Identifier(writer)))
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with coordinator.transaction():
                coordinator.execute('SELECT truss.literal_authority_probe(%s,%s)',(anchor,nonce))
        admin.execute(sql.SQL('GRANT {} TO products_person').format(sql.Identifier(writer)))
        with coordinator.transaction(force_rollback=True):
            checked = coordinator.execute('SELECT truss.literal_authority_probe(%s,%s)',(anchor,nonce)).fetchone()[0]
            self.assertTrue(checked['currentChecksPassed'])
        self.assertEqual(session.connection.execute('SELECT pg_current_snapshot()::text,pg_current_xact_id()::text').fetchone(),self.original_snapshot)
        directory = os.environ.get('TRUSS_BRIDGE_INVENTORY_EVIDENCE')
        if directory:
            (Path(directory)/'current-check.json').write_text(json.dumps(checked,indent=2)+'\n')
