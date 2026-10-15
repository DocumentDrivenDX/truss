"""Original native identity anchor only; no program/authority/permit admission."""
from importlib.resources import files
import uuid
import psycopg
from psycopg import sql
import test_group_create_native as base
from truss import Ok, adopt_psycopg_host
from truss._preparation_source_epoch import bootstrap_preparation_source_marker_in_transaction, issue_initial_preparation_source_epoch_in_transaction
from truss._security_source_epoch_installation import bootstrap_source_epoch_infrastructure_in_transaction
from truss._action_store import register_action_store_in_transaction


class PreparationAttemptAnchorNativeTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name] = None

    def test_original_anchor_rejects_same_backend_new_transaction_remint(self):
        data, host, assembly, tx = self.ready(document_ids=('adoc',))
        host.detach(); data.commit()
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin); tx = host.adopt_transaction().value
        def checked(result):
            self.assertIsInstance(result,Ok,str(host._custody.last_attempt.error)); return result.value
        marker = checked(bootstrap_preparation_source_marker_in_transaction(host,tx))
        infrastructure = checked(bootstrap_source_epoch_infrastructure_in_transaction(host,tx,installation_identity=marker.installation_id.encode()))
        checked(issue_initial_preparation_source_epoch_in_transaction(host,tx,marker=marker,infrastructure=infrastructure))
        checked(register_action_store_in_transaction(host,tx,tenant='attempt-anchor-native',registration_key=b'original-anchor-store',executor_roles=('consumer',)))
        host.detach(); self.admin.commit()
        owner = self.installation.owner_role
        self.admin.execute(sql.SQL('GRANT pg_read_all_stats TO {} WITH INHERIT TRUE').format(sql.Identifier(owner)))
        for source in ('preparation-attempt-anchor-storage.sql','preparation-peer-xid.sql',
                       'preparation-permit-mint.sql','preparation-permit-binding-check.sql','preparation-attempt-anchor.sql'):
            self.admin.execute(files('truss').joinpath('_security_bootstrap',source).read_text())
        for home,kind in (('preparation_attempt_anchor','TABLE'),('preparation_attempt_anchor_seq','SEQUENCE')):
            self.admin.execute(sql.SQL('ALTER '+kind+' truss.{} OWNER TO {}').format(sql.Identifier(home),sql.Identifier(owner)))
        signatures=('require_preparation_peer_xid(int4,xid8)','mint_preparation_permit_binding(int4,int4,xid8)',
            'check_preparation_permit_binding(int4,int4)','create_preparation_attempt_anchor(bytea,int4,int4,xid8,bytea)',
            'check_preparation_attempt_coordinator(int4,uuid)','check_preparation_attempt_data(int4,uuid)')
        for signature in signatures:
            self.admin.execute(sql.SQL('ALTER FUNCTION truss.'+signature+' OWNER TO {}').format(sql.Identifier(owner)))
        # These wrappers are fixture-only diagnostics. They return predicates or
        # mint unchecked markers to retain the weakened remint counterexample.
        # They are never installed by a production installer or exposed as data.
        probes=(
            ('anchor_coordinator_probe','a int4,n uuid','boolean','SELECT truss.check_preparation_attempt_coordinator(a,n)'),
            ('anchor_identity_probe','a int4,n uuid','boolean','SELECT truss.check_preparation_attempt_data(a,n)'),
            ('anchor_data_probe','a int4,n uuid,c int4','boolean','SELECT truss.check_preparation_attempt_data(a,n) AND truss.check_preparation_permit_binding(a,c)'),
            ('anchor_bare_probe','a int4,c int4','boolean','SELECT truss.check_preparation_permit_binding(a,c)'),
            ('anchor_mint_probe','a int4,p int4,x xid8','void','SELECT truss.mint_preparation_permit_binding(a,p,x)'),
        )
        for name,args,returns,body in probes:
            self.admin.execute('CREATE FUNCTION truss.'+name+'('+args+') RETURNS '+returns+' LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ '+body+' $$')
            types=','.join(arg.split()[1] for arg in args.split(','))
            self.admin.execute(sql.SQL('ALTER FUNCTION truss.'+name+'('+types+') OWNER TO {}').format(sql.Identifier(owner)))
            self.admin.execute('REVOKE ALL ON FUNCTION truss.'+name+'('+types+') FROM PUBLIC')
            self.admin.execute('GRANT EXECUTE ON FUNCTION truss.'+name+'('+types+') TO consumer')
        # Dedicated-database mint namespace premise is checked separately. This
        # fixture closes the PUBLIC two-int routes before creating any markers.
        for name in ('pg_advisory_lock','pg_advisory_lock_shared','pg_try_advisory_lock','pg_try_advisory_lock_shared',
                     'pg_advisory_xact_lock','pg_advisory_xact_lock_shared','pg_try_advisory_xact_lock','pg_try_advisory_xact_lock_shared'):
            self.admin.execute(sql.SQL('REVOKE ALL ON FUNCTION pg_catalog.{}(int4,int4) FROM PUBLIC').format(sql.Identifier(name)))
        for name in ('pg_try_advisory_xact_lock','pg_try_advisory_xact_lock_shared'):
            self.admin.execute(sql.SQL('GRANT EXECUTE ON FUNCTION pg_catalog.{}(int4,int4) TO {}').format(sql.Identifier(name),sql.Identifier(owner)))
        for query in ('SELECT * FROM truss.preparation_attempt_anchor',"SELECT nextval('truss.preparation_attempt_anchor_seq')",
                      "SELECT truss.create_preparation_attempt_anchor('x'::bytea,1,2,'1'::xid8,'x'::bytea)",
                      "SELECT truss.check_preparation_attempt_coordinator(1,'00000000-0000-0000-0000-000000000001'::uuid)"):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):data.execute(query)
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        coordinator=psycopg.connect(**dict(params,user='consumer'),autocommit=True)
        self.addCleanup(coordinator.close)
        coordinator_pid=coordinator.info.backend_pid
        coordinator.execute('BEGIN')
        original_xid=coordinator.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        def issue(xid):
            return self.admin.execute('SELECT * FROM truss.create_preparation_attempt_anchor(%s,%s,%s,%s::xid8,%s)',
                (b'original-anchor-store',data.info.backend_pid,coordinator_pid,str(xid),b'opaque-unregistered-program')).fetchone()
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):issue(int(original_xid)+2**32)
        data.execute('BEGIN')
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):issue(original_xid)
        data.execute('ROLLBACK')
        self.admin.execute('BEGIN')
        anchor,nonce=issue(original_xid)
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        self.assertFalse(data.execute('SELECT truss.anchor_identity_probe(%s,%s)',(anchor,nonce)).fetchone()[0])
        pending_snapshot=data.execute('SELECT pg_current_snapshot()::text').fetchone()
        self.admin.execute('COMMIT')
        self.assertFalse(data.execute('SELECT truss.anchor_identity_probe(%s,%s)',(anchor,nonce)).fetchone()[0])
        self.assertEqual(data.execute('SELECT pg_current_snapshot()::text').fetchone(),pending_snapshot)
        data.execute('ROLLBACK')
        for query in ('UPDATE truss.preparation_attempt_anchor SET program_identity=program_identity',
                      'DELETE FROM truss.preparation_attempt_anchor','TRUNCATE truss.preparation_attempt_anchor'):
            with self.assertRaises(psycopg.Error):self.admin.execute(query)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.preparation_attempt_anchor').fetchone(),(1,))
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        data_xid=data.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        snapshot=data.execute('SELECT pg_current_snapshot()::text').fetchone()
        self.assertTrue(coordinator.execute('SELECT truss.anchor_coordinator_probe(%s,%s)',(anchor,nonce)).fetchone()[0])
        def mint():coordinator.execute('SELECT truss.anchor_mint_probe(%s,%s,%s::xid8)',(anchor,data.info.backend_pid,data_xid))
        def check(nonce_value=nonce):return data.execute('SELECT truss.anchor_data_probe(%s,%s,%s)',(anchor,nonce_value,coordinator_pid)).fetchone()[0]
        self.assertTrue(data.execute('SELECT truss.anchor_identity_probe(%s,%s)',(anchor,nonce)).fetchone()[0])
        self.assertFalse(check())  # Native identity alone does not supply markers.
        mint();self.assertTrue(check());self.assertFalse(check(uuid.uuid4()))
        foreign=psycopg.connect(**dict(params,user='consumer'),autocommit=True)
        self.addCleanup(foreign.close);foreign.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        self.assertFalse(foreign.execute('SELECT truss.anchor_data_probe(%s,%s,%s)',(anchor,nonce,coordinator_pid)).fetchone()[0])
        foreign.execute('ROLLBACK')
        coordinator.execute('COMMIT');self.assertFalse(check())
        coordinator.execute('BEGIN')
        replacement_xid=coordinator.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        self.assertNotEqual(replacement_xid,original_xid)
        self.assertFalse(coordinator.execute('SELECT truss.anchor_coordinator_probe(%s,%s)',(anchor,nonce)).fetchone()[0])
        mint()
        # Bare tuple still matches, but immutable original transaction identity
        # refuses the exact retained same-PID/new-TX remint counterexample.
        self.assertTrue(data.execute('SELECT truss.anchor_bare_probe(%s,%s)',(anchor,coordinator_pid)).fetchone()[0])
        self.assertFalse(check())
        self.assertEqual(data.execute('SELECT pg_current_snapshot()::text').fetchone(),snapshot)
        coordinator.execute('ROLLBACK');data.execute('ROLLBACK')
        coordinator.execute('BEGIN')
        original_xid=coordinator.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        anchor,nonce=issue(original_xid)  # Original C autocommit acknowledgement.
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        data_xid=data.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        mint();self.assertTrue(check(nonce))
        snapshot=data.execute('SELECT pg_current_snapshot()::text').fetchone()
        coordinator.close()
        self.assertFalse(check(nonce))
        self.assertEqual(data.execute('SELECT pg_current_snapshot()::text').fetchone(),snapshot)
        data.execute('ROLLBACK')
