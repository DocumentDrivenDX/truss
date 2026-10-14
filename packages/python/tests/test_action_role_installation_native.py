"""Original owner ticket→private native role enrollment, not permission."""
import json
from pathlib import Path
import subprocess
import psycopg
import test_group_create_native as base
from truss import Ok, Error, adopt_psycopg_host
from truss.bulk_action_gateway import ActionRegistration
from truss._action_role_installation import bootstrap_action_roles_in_transaction


class ActionRoleInstallationNativeTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name] = None

    def test_original_registry_ticket_and_complete_native_role_mapping(self):
        data, old_host, assembly, old_tx = self.ready(document_ids=('adoc',))
        old_host.detach(); data.commit()
        fixture = json.loads(Path('/Users/erik/Projects/weft/tests/mutation/fixtures/postgres-owner-plan.json').read_text())
        request = fixture['request']
        def original_owner(model, action):
            payload = {'model':json.loads(model),'action':json.loads(action),'pin':request['modelPin']}
            result = subprocess.run(['/opt/homebrew/bin/bun',str(Path(__file__).with_name('owner_action_preparation.ts'))],input=json.dumps(payload),capture_output=True,text=True,timeout=30)
            if result.returncode:
                raise ValueError('Original owner refused')
            return result.stdout.strip().encode()
        registry = ActionRegistration(original_owner)
        ticket = registry.register(json.dumps(request['model']).encode(),json.dumps(request['action']).encode(),json.dumps(fixture['registry']['actions'][0]['preparation']).encode())
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        for invalid in ((), (('not-declared','group_reader'),), (('bulk-editor','consumer'),)):
            refused = bootstrap_action_roles_in_transaction(host,tx,registration=registry,entries=((ticket,invalid),),store_identity=b'original-store-config')
            self.assertIsInstance(refused, Error)
        # The native LOGIN rejection is a guarded operation failure; reconcile
        # the original installer transaction rather than reusing its handle.
        host.detach(); self.admin.rollback()
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        installed = bootstrap_action_roles_in_transaction(host,tx,registration=registry,entries=((ticket,(('bulk-editor','group_reader'),)),),store_identity=b'original-store-config')
        self.assertIsInstance(installed, Ok, str(host._custody.last_attempt.error))
        self.assertFalse(installed.value.security_ready)
        self.assertEqual(installed.value.store_identity,b'original-store-config')
        host.detach(); self.admin.commit()
        row = self.admin.execute('SELECT family_identity,role_identity,r.rolname FROM truss.action_role_binding b JOIN pg_catalog.pg_roles r ON r.oid=b.native_role_oid').fetchone()
        self.assertEqual(row,(b'["sales","set-active"]',b'"bulk-editor"','group_reader'))
        for query in ('SELECT * FROM truss.action_role_binding','DELETE FROM truss.action_role_binding',"SELECT nextval('truss.action_role_binding_binding_id_seq')"):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                data.execute(query)
