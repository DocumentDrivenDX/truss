# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private original C/D mint/check composition; no public protected execution."""
from importlib.resources import files
from concurrent.futures import ThreadPoolExecutor
import time
import psycopg
import test_preparation_literal_authority_native as original


class _CoordinatorEnded(Exception):
    pass


class PreparationLiteralPermitNativeTests(original.PreparationLiteralAuthorityNativeTests):
    # The parent negative source test remains covered by its own test module.
    test_changed_native_principal_refuses_original_subject_key = None

    def prepare_component(self, admin, owner):
        super().prepare_component(admin,owner)
        for name in ('preparation-advisory-exclusion.sql','preparation-permit-mint.sql','preparation-permit-binding-check.sql','preparation-literal-permit.sql'):
            admin.execute(files('truss').joinpath('_security_bootstrap',name).read_text())
        # Assessor-only dispatch, no production installer/SDK grant. The raw
        # private primitives themselves remain inaccessible to the person.
        admin.execute("CREATE FUNCTION truss.literal_permit_probe(a int4,n uuid,operation text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' AS $$ BEGIN CASE operation WHEN 'cut' THEN PERFORM truss.acquire_preparation_literal_permit_cut(a,n); WHEN 'issue' THEN PERFORM truss.issue_preparation_literal_permit(a,n); WHEN 'require' THEN PERFORM truss.require_preparation_literal_permit(a,n); ELSE RAISE EXCEPTION 'unknown assessor operation'; END CASE; END; $$")
        admin.execute('REVOKE ALL ON FUNCTION truss.literal_permit_probe(int4,uuid,text) FROM PUBLIC')
        admin.execute('GRANT EXECUTE ON FUNCTION truss.literal_permit_probe(int4,uuid,text) TO products_person')

    def after_claim_commit(self, admin, session, coordinator, anchor, nonce, params):
        super().after_claim_commit(admin,session,coordinator,anchor,nonce,params)
        data = session.connection
        def invoke(connection,operation):
            return connection.execute('SELECT truss.literal_permit_probe(%s,%s,%s)',(anchor,nonce,operation)).fetchone()
        # Successful current checks alone do not mint a permit; D's exclusions
        # must exist before C can issue, and D cannot repair a lost cut on use.
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            with coordinator.transaction(): invoke(coordinator,'issue')
        data.execute('SAVEPOINT original_authority_cut')
        invoke(data,'cut')
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            with data.transaction(): invoke(data,'require')
        if getattr(self,'end_original_coordinator',False):
            invoke(coordinator,'issue')
            invoke(data,'require')
            coordinator.execute('ROLLBACK')
            coordinator.execute('BEGIN')
            coordinator.execute('SELECT pg_current_xact_id()')
            with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                with coordinator.transaction(): invoke(coordinator,'issue')
            with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                with data.transaction(): invoke(data,'require')
            raise _CoordinatorEnded()
        with coordinator.transaction(force_rollback=True):
            invoke(coordinator,'issue')
            invoke(data,'require')
            with ThreadPoolExecutor(max_workers=1) as worker:
                future = worker.submit(coordinator.execute,'SELECT pg_sleep(0.5)')
                deadline = time.monotonic()+2
                while not admin.execute("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=%s AND wait_event='PgSleep')",(coordinator.info.backend_pid,)).fetchone()[0]:
                    if time.monotonic()>deadline: self.fail('Original active C not observed')
                    time.sleep(.01)
                with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                    with data.transaction(): invoke(data,'require')
                future.result(timeout=3)
            invoke(data,'require')
            with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                with coordinator.transaction(): invoke(coordinator,'issue')
            data.execute('ROLLBACK TO original_authority_cut')
            with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                with data.transaction(): invoke(data,'require')
            self.assertEqual(data.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND relation='truss.module_access'::regclass AND mode='ShareLock' AND granted").fetchone(),(0,))
            # Assessor reset only, never an admitted operation continuation.
            invoke(data,'cut')
            data.execute('ROLLBACK TO bridge_cut')
            with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                with data.transaction(): invoke(data,'require')
            self.assertEqual(data.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND relation='truss.preparation_program_registration'::regclass AND mode='ShareLock' AND granted").fetchone(),(0,))
        invoke(data,'cut')
        # D alone still excludes role mutation after C drops its permit/locks.
        admin.execute("SET lock_timeout='1ms'")
        with self.assertRaises(psycopg.errors.LockNotAvailable):
            admin.execute('REVOKE preparation_bulk_editor FROM products_person')
        # C's savepoint rollback removed its actual native permit addresses.
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            with data.transaction(): invoke(data,'require')
        self.assertEqual(data.execute('SELECT pg_current_snapshot()::text,pg_current_xact_id()::text').fetchone(),self.original_snapshot)
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with coordinator.transaction():
                coordinator.execute('SELECT truss.issue_preparation_literal_permit(%s,%s)',(anchor,nonce))

    def test_original_coordinator_cannot_remint_in_later_transaction(self):
        self.end_original_coordinator = True
        with self.assertRaises(_CoordinatorEnded):
            self.test_engine_capture_and_independently_committed_native_claim()
