"""Original owner ticket→private native role enrollment, not permission."""
import json
import hashlib
from pathlib import Path
import subprocess
import psycopg
import test_group_create_native as base
from truss import Ok, Error, adopt_psycopg_host
from truss.bulk_action_gateway import ActionRegistration
from truss._action_role_installation import bootstrap_action_roles_in_transaction
from truss._action_subject_installation import bootstrap_action_subjects_in_transaction
from truss._security_preparation_authority import capture_preparation_data_with_cursor
from truss._action_authority_observation import observe_current_action_authority_with_cursor


class ActionRoleInstallationNativeTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name] = None

    def test_original_registry_ticket_and_complete_native_role_mapping(self):
        data, old_host, assembly, old_tx = self.ready(document_ids=('adoc',))
        old_host.detach(); data.commit()
        fixture = json.loads(Path('/Users/erik/Projects/weft/tests/mutation/fixtures/postgres-owner-plan.json').read_text())
        request = fixture['request']
        # Original owner admits a two-role OR variant; only the second role
        # will be held in the positive schedule, distinguishing OR from AND.
        document = json.loads(request['model']['utf8'])
        document['modules'][0]['extensions']['umf.actions']['actions'][0]['authorization']['roles'] = ['bulk-editor','reviewer']
        request['model']['utf8'] = json.dumps(document)
        digest = hashlib.sha256(request['model']['utf8'].encode()).hexdigest()
        request['model']['sha256'] = digest
        request['modelPin']['sha256'] = digest
        request['action']['documentSha256'] = digest
        self.admin.execute('CREATE ROLE action_reviewer NOLOGIN')
        self.addCleanup(self.admin.execute,'DROP ROLE action_reviewer')
        def original_owner(model, action):
            payload = {'model':json.loads(model),'action':json.loads(action),'pin':request['modelPin']}
            result = subprocess.run(['/opt/homebrew/bin/bun',str(Path(__file__).with_name('owner_action_preparation.ts'))],input=json.dumps(payload),capture_output=True,text=True,timeout=30)
            if result.returncode:
                raise ValueError('Original owner refused')
            return result.stdout.strip().encode()
        registry = ActionRegistration(original_owner)
        model_bytes = json.dumps(request['model']).encode()
        action_bytes = json.dumps(request['action']).encode()
        ticket = registry.register(model_bytes,action_bytes,original_owner(model_bytes,action_bytes))
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        for invalid in ((), (('not-declared','group_reader'),), (('bulk-editor','consumer'),('reviewer','action_reviewer'))):
            refused = bootstrap_action_roles_in_transaction(host,tx,registration=registry,entries=((ticket,invalid),),store_identity=b'original-store-config')
            self.assertIsInstance(refused, Error)
        # The native LOGIN rejection is a guarded operation failure; reconcile
        # the original installer transaction rather than reusing its handle.
        host.detach(); self.admin.rollback()
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        installed = bootstrap_action_roles_in_transaction(host,tx,registration=registry,entries=((ticket,(('bulk-editor','group_reader'),('reviewer','action_reviewer'))),),store_identity=b'original-store-config')
        self.assertIsInstance(installed, Ok, str(host._custody.last_attempt.error))
        self.assertFalse(installed.value.security_ready)
        self.assertEqual(installed.value.store_identity,b'original-store-config')
        subject = bootstrap_action_subjects_in_transaction(host,tx,bindings=(('consumer',b'original-human','human'),))
        self.assertIsInstance(subject, Ok, str(host._custody.last_attempt.error))
        host.detach(); self.admin.commit()
        rows = self.admin.execute('SELECT family_identity,role_identity,r.rolname FROM truss.action_role_binding b JOIN pg_catalog.pg_roles r ON r.oid=b.native_role_oid ORDER BY role_identity').fetchall()
        self.assertEqual(rows,[(b'["sales","set-active"]',b'"bulk-editor"','group_reader'),(b'["sales","set-active"]',b'"reviewer"','action_reviewer')])
        for query in ('SELECT * FROM truss.action_role_binding','DELETE FROM truss.action_role_binding',"SELECT nextval('truss.action_role_binding_binding_id_seq')"):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                data.execute(query)
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        with data.cursor() as cursor:
            original = capture_preparation_data_with_cursor(cursor)
        def observe():
            self.admin.execute('BEGIN')
            self.admin.execute('LOCK TABLE ONLY truss.action_subject_binding,truss.action_role_binding IN SHARE MODE NOWAIT')
            self.admin.execute('LOCK TABLE pg_catalog.pg_authid,pg_catalog.pg_auth_members IN SHARE MODE NOWAIT')
            with self.admin.cursor() as cursor:
                return observe_current_action_authority_with_cursor(cursor,original=original,
                    registration=registry,ticket=ticket,store_identity=b'original-store-config')
        denied = observe()
        self.assertTrue(denied.human_enrolled)
        self.assertFalse(denied.role_match)  # Module writer is not bulk-editor.
        self.assertFalse(denied.security_ready)
        self.admin.commit()
        self.admin.execute('GRANT action_reviewer TO consumer WITH SET FALSE')
        allowed = observe()
        self.assertTrue(allowed.role_match)
        writer = psycopg.connect(**psycopg.conninfo.conninfo_to_dict(self.info.connection_uri),autocommit=True)
        self.addCleanup(writer.close)
        writer.execute("SET lock_timeout='150ms'")
        with self.assertRaises(psycopg.errors.LockNotAvailable):
            writer.execute('REVOKE action_reviewer FROM consumer')
        with self.assertRaises(psycopg.errors.LockNotAvailable):
            writer.execute('UPDATE truss.action_role_binding SET native_role_oid=native_role_oid')
        self.admin.commit()
        writer.execute("UPDATE truss.action_subject_binding SET subject_kind='service'")
        service = observe()
        self.assertTrue(service.role_match)
        self.assertFalse(service.human_enrolled)
        self.admin.commit()
        writer.execute("UPDATE truss.action_subject_binding SET subject_kind='human'")
        data.execute('ROLLBACK')
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        with data.cursor() as cursor:
            original = capture_preparation_data_with_cursor(cursor)
        membership = "SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid=m.roleid WHERE r.rolname='action_reviewer' AND m.member=(SELECT oid FROM pg_catalog.pg_roles WHERE rolname=session_user))"
        self.assertEqual(data.execute(membership).fetchone(), (True,))
        writer.execute('REVOKE action_reviewer FROM consumer')
        self.assertEqual(data.execute(membership).fetchone(), (True,))
        fresh = observe()
        self.assertFalse(fresh.role_match)
        self.admin.commit()
        data.execute('ROLLBACK')
