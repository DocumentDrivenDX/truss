# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original owner ticket→private native role enrollment, not permission."""
import json
from dataclasses import replace
import hashlib
from pathlib import Path
import subprocess
import psycopg
import test_group_create_native as base
from truss import Ok, Error, adopt_psycopg_host
from truss.bulk_action_gateway import ActionRegistration
from truss._preparation_source_epoch import bootstrap_preparation_source_marker_in_transaction, issue_initial_preparation_source_epoch_in_transaction
from truss._security_source_epoch_installation import bootstrap_source_epoch_infrastructure_in_transaction
from truss._action_store import ActionStoreObservation, register_action_store_in_transaction, observe_action_store_in_transaction, verify_action_store_context_with_cursor, verify_action_store_enrollment_context_with_cursor
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
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        def checked(result):
            self.assertIsInstance(result, Ok, str(host._custody.last_attempt.error))
            return result.value
        marker = checked(bootstrap_preparation_source_marker_in_transaction(host,tx))
        infrastructure = checked(bootstrap_source_epoch_infrastructure_in_transaction(host,tx,installation_identity=marker.installation_id.encode()))
        checked(issue_initial_preparation_source_epoch_in_transaction(host,tx,marker=marker,infrastructure=infrastructure))
        pending = checked(register_action_store_in_transaction(host,tx,tenant='action-role-native',registration_key=b'original-role-store',executor_roles=('consumer',)))
        raw=json.loads(pending.receipt_bytes)
        uncommitted=ActionStoreObservation(pending.registration_key,pending.receipt_bytes,
            bytes.fromhex(raw['storeIdentityHex']),bytes.fromhex(raw['tenantIdentityHex']),
            bytes.fromhex(raw['epochIdentityHex']),raw['installationId'],'matches')
        with self.admin.cursor() as cursor:
            with self.assertRaisesRegex(ValueError,'Original committed issued store enrollment required'):
                verify_action_store_enrollment_context_with_cursor(cursor,uncommitted,uncommitted.installation_id)
        host.detach(); self.admin.commit()
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        store = checked(observe_action_store_in_transaction(host,tx,registration_key=b'original-role-store'))
        self.assertFalse(store.authority)
        host.detach(); self.admin.commit()
        fixture = json.loads((Path(__file__).with_name('fixtures')/'umf010-owner-plan.json').read_text())
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
        # Raw configuration, a pending registration and fenced observations do
        # not identify an original committed current store.
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        mutable = tuple(replace(store,**{name:bytearray(getattr(store,name))}) for name in
                        ('registration_key','receipt_bytes','store_identity','tenant_identity','epoch_identity'))
        for invalid_store in (b'original-store-config',pending,replace(store,binding_correspondence='fenced'),*mutable):
            refused = bootstrap_action_roles_in_transaction(host,tx,registration=registry,
                entries=((ticket,(('bulk-editor','group_reader'),('reviewer','action_reviewer'))),),store_context=invalid_store)
            self.assertIsInstance(refused,Error)
        host.detach(); self.admin.rollback()
        # Dataclass construction is not issuance: every changed original native
        # component must fail before the enrollment home is created.
        for forged in (replace(store,store_identity=b'forged-store'),replace(store,tenant_identity=b'forged-tenant'),
                       replace(store,epoch_identity=b'forged-epoch'),replace(store,receipt_bytes=store.receipt_bytes+b' ')):
            self.admin.execute('BEGIN')
            host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
            refused = bootstrap_action_roles_in_transaction(host,tx,registration=registry,
                entries=((ticket,(('bulk-editor','group_reader'),('reviewer','action_reviewer'))),),store_context=forged)
            self.assertIsInstance(refused,Error)
            host.detach(); self.admin.rollback()
            self.assertEqual(self.admin.execute("SELECT pg_catalog.to_regclass('truss.action_role_binding')").fetchone(),(None,))
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        for invalid in ((), (('not-declared','group_reader'),), (('bulk-editor','consumer'),('reviewer','action_reviewer'))):
            refused = bootstrap_action_roles_in_transaction(host,tx,registration=registry,entries=((ticket,invalid),),store_context=store)
            self.assertIsInstance(refused, Error)
        # The native LOGIN rejection is a guarded operation failure; reconcile
        # the original installer transaction rather than reusing its handle.
        host.detach(); self.admin.rollback()
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        installed = bootstrap_action_roles_in_transaction(host,tx,registration=registry,entries=((ticket,(('bulk-editor','group_reader'),('reviewer','action_reviewer'))),),store_context=store)
        self.assertIsInstance(installed, Ok, str(host._custody.last_attempt.error))
        self.assertFalse(installed.value.security_ready)
        self.assertIs(type(installed.value.store_identity),bytes)
        self.assertEqual(installed.value.store_identity,store.store_identity)
        subject = bootstrap_action_subjects_in_transaction(host,tx,bindings=(('consumer',b'original-human','human'),),with_action_roles=True)
        self.assertIsInstance(subject, Ok, str(host._custody.last_attempt.error))
        self.assertTrue(subject.value.mapping_cut)
        host.detach(); self.admin.commit()
        originals = self.admin.execute('SELECT original_model_artifact,original_action_pin,original_preparation_artifact,declared_roles,person_required FROM truss.action_family_registration').fetchall()
        held_original = registry.original(ticket)
        self.assertEqual(originals,[(held_original.model,held_original.action_pin,held_original.preparation,[b'"bulk-editor"',b'"reviewer"'],True)])
        for query in ('UPDATE truss.action_family_registration SET original_action_pin=original_action_pin',
                      'DELETE FROM truss.action_family_registration','TRUNCATE truss.action_family_registration CASCADE'):
            with self.assertRaises(psycopg.Error):self.admin.execute(query)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.action_family_registration').fetchone(),(1,))
        rows = self.admin.execute('SELECT family_identity,role_identity,r.rolname FROM truss.action_role_binding b JOIN pg_catalog.pg_roles r ON r.oid=b.native_role_oid ORDER BY role_identity').fetchall()
        self.assertEqual(rows,[(b'["sales","set-active"]',b'"bulk-editor"','group_reader'),(b'["sales","set-active"]',b'"reviewer"','action_reviewer')])
        for query in ('SELECT * FROM truss.action_family_registration','DELETE FROM truss.action_family_registration',"SELECT nextval('truss.action_family_registration_family_registration_id_seq')",'SELECT * FROM truss.action_role_binding','DELETE FROM truss.action_role_binding',"SELECT nextval('truss.action_role_binding_binding_id_seq')"):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                data.execute(query)
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        with data.cursor() as cursor:
            original = capture_preparation_data_with_cursor(cursor)
        def observe(mutation=None):
            self.admin.execute('BEGIN')
            with self.admin.cursor() as cursor:
                verify_action_store_context_with_cursor(cursor,store)
            if mutation is not None:self.admin.execute(mutation)
            self.admin.execute('LOCK TABLE ONLY truss.action_family_registration,truss.action_subject_binding,truss.action_role_binding IN SHARE MODE NOWAIT')
            self.admin.execute('LOCK TABLE pg_catalog.pg_authid,pg_catalog.pg_auth_members IN SHARE MODE NOWAIT')
            with self.admin.cursor() as cursor:
                return observe_current_action_authority_with_cursor(cursor,original=original,
                    registration=registry,ticket=ticket,store_context=store)
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
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        data.execute('SELECT truss.acquire_action_mapping_cut()')
        before = data.execute('SELECT pg_catalog.pg_current_snapshot()::text').fetchone()
        with self.assertRaises(psycopg.errors.LockNotAvailable):
            writer.execute('UPDATE truss.action_role_binding SET native_role_oid=native_role_oid')
        with self.assertRaises(psycopg.errors.LockNotAvailable):
            writer.execute('UPDATE truss.action_subject_binding SET subject_kind=subject_kind')
        self.assertEqual(data.execute('SELECT pg_catalog.pg_current_snapshot()::text').fetchone(),before)
        self.assertEqual(data.execute('COMMIT').statusmessage,'COMMIT')
        writer.execute('UPDATE truss.action_role_binding SET native_role_oid=native_role_oid')
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        data.execute('SELECT pg_catalog.pg_current_snapshot()')
        writer.execute('UPDATE truss.action_role_binding SET native_role_oid=native_role_oid')
        with self.assertRaises(psycopg.errors.SerializationFailure):
            data.execute('SELECT truss.acquire_action_mapping_cut()')
        data.execute('ROLLBACK')
        # Independent weakened native control: an incomplete map cannot be
        # accepted merely because the remaining declared role still matches.
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        with data.cursor() as cursor:
            original = capture_preparation_data_with_cursor(cursor)
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        with self.assertRaisesRegex(ValueError,'Complete exact original current role mapping required'):
            observe("DELETE FROM truss.action_role_binding WHERE role_identity=convert_to('\"reviewer\"','UTF8')")
        self.admin.execute('ROLLBACK')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.action_role_binding').fetchone(),(2,))
        # An unresolved extra target must not disappear behind an inner join
        # while the complete valid role map remains present.
        extra = """INSERT INTO truss.action_role_binding(family_registration_id,installation_id,
            store_identity,family_identity,role_identity,native_role_oid,original_action_pin,profile_id,profile_version)
            SELECT family_registration_id,installation_id,store_identity,family_identity,
            convert_to('"future-role"','UTF8'),0::oid,original_action_pin,profile_id,profile_version
            FROM truss.action_role_binding ORDER BY binding_id LIMIT 1"""
        with self.assertRaisesRegex(ValueError,'Complete exact original current role mapping required'):
            observe(extra)
        self.admin.execute('ROLLBACK')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.action_role_binding').fetchone(),(2,))
        self.assertTrue(observe().role_match)
        self.admin.execute('COMMIT')
        data.execute('ROLLBACK')
