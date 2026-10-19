# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original SCRAM D/C/E workflow with selected definition custody adjunct."""
from concurrent.futures import ThreadPoolExecutor
from importlib.resources import files
import json
import os
from pathlib import Path
import time
import psycopg
from psycopg import sql
from truss._preparation_bridge_inventory import preparation_bridge_inventory_source
import test_preparation_data_claim_native as original


class PreparationBridgeInventoryNativeTests(original.PreparationDataClaimNativeTests):
    expected_home_count = 7
    expected_sequence_count = 3
    def prepare_component(self, admin, owner):
        for name in ('preparation-catalog-cut.sql', 'preparation-program-binding.sql'):
            admin.execute(files('truss').joinpath('_security_bootstrap', name).read_text())
        admin.execute(preparation_bridge_inventory_source())
        for signature in ('acquire_preparation_catalog_cut()', 'resolve_preparation_program_binding(int4,uuid,xid8)',
                          'read_preparation_program_sources(int8)', 'preparation_bridge_inventory()', 'acquire_preparation_bridge_cut(int4,uuid)',
                          'observe_preparation_bridge(int4,uuid)'):
            admin.execute(sql.SQL('ALTER FUNCTION truss.'+signature+' OWNER TO {}').format(sql.Identifier(owner)))
        # Fixture assessor only. No production installer or ordinary SDK grants.
        admin.execute('CREATE FUNCTION truss.bridge_inventory_probe(a int4,n uuid,d bool) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET lock_timeout=\'1ms\' AS $$ BEGIN IF d THEN RETURN truss.acquire_preparation_bridge_cut(a,n); ELSE RETURN truss.observe_preparation_bridge(a,n); END IF; END $$')
        admin.execute(sql.SQL('ALTER FUNCTION truss.bridge_inventory_probe(int4,uuid,bool) OWNER TO {}').format(sql.Identifier(owner)))
        admin.execute('REVOKE ALL ON FUNCTION truss.bridge_inventory_probe(int4,uuid,bool) FROM PUBLIC')
        admin.execute('GRANT EXECUTE ON FUNCTION truss.bridge_inventory_probe(int4,uuid,bool) TO products_person')

    def before_claim(self, admin, session, coordinator, anchor, nonce, params):
        data = session.connection
        data.execute("SET LOCAL lock_timeout='1ms'")
        coordinator.execute("SET LOCAL lock_timeout='1ms'")
        coordinator.execute("SET LOCAL bytea_output='escape'")
        # Participating DDL retains its epoch writer locks even after its
        # catalog operation has returned; D must refuse until it settles.
        with psycopg.connect(**params, autocommit=True) as writer:
            writer.execute('BEGIN')
            writer.execute("COMMENT ON TABLE umf_security.preparation_data_claim IS 'uncommitted'")
            with self.assertRaises(psycopg.errors.LockNotAvailable):
                with data.transaction():
                    data.execute('SELECT truss.bridge_inventory_probe(%s,%s,true)', (anchor, nonce))
            writer.execute('ROLLBACK')
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with coordinator.transaction():
                coordinator.execute('SELECT truss.observe_preparation_bridge(%s,%s)', (anchor, nonce))
        data.execute('SAVEPOINT bridge_cut')
        self.original_inventory = data.execute('SELECT truss.bridge_inventory_probe(%s,%s,true)', (anchor, nonce)).fetchone()[0]
        self.original_snapshot = data.execute('SELECT pg_current_snapshot()::text,pg_current_xact_id()::text').fetchone()
        self.assertEqual(len(self.original_inventory['homes']), self.expected_home_count)
        self.assertEqual(len(self.original_inventory['sequenceDefinitions']), self.expected_sequence_count)
        self.assertFalse(self.original_inventory['authority'])
        self.assertEqual({h['kind'] for h in self.original_inventory['homes']}, {'r', 'S'})

    def after_claim_commit(self, admin, session, coordinator, anchor, nonce, params):
        data = session.connection
        def observe():
            return coordinator.execute('SELECT truss.bridge_inventory_probe(%s,%s,false)', (anchor, nonce)).fetchone()[0]
        # Release all C inspection relation locks before the queued-lock control.
        with coordinator.transaction(force_rollback=True):
            self.assertEqual(observe(), self.original_inventory)
        refusals = []
        for command in ("ALTER TABLE umf_security.preparation_data_claim ADD COLUMN rejected integer",
                        "COMMENT ON TABLE truss.preparation_program_registration IS 'rejected'",
                        'ALTER FUNCTION umf_security.require_preparation_data_claim(int4,uuid) STABLE'):
            with self.assertRaises(psycopg.errors.LockNotAvailable) as caught:
                admin.execute(command)
            refusals.append(caught.exception.sqlstate)
        # Real event-supported DDL refuses at the epoch fence, never queues on
        # its target. A separate explicit LOCK creates the implicit-lock queue.
        with psycopg.connect(**params, autocommit=True) as blocker:
            blocker.execute('BEGIN')
            blocker.execute("SET LOCAL statement_timeout='5s'")
            def queue_lock():
                try:
                    blocker.execute('LOCK TABLE umf_security.preparation_data_claim IN ACCESS EXCLUSIVE MODE')
                except psycopg.errors.QueryCanceled:
                    return 'cancelled'
                return 'granted'
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(queue_lock)
                try:
                    deadline = time.monotonic()+3
                    while not admin.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=%s AND relation='umf_security.preparation_data_claim'::regclass AND mode='AccessExclusiveLock' AND NOT granted)", (blocker.info.backend_pid,)).fetchone()[0]:
                        if time.monotonic() >= deadline: self.fail('Explicit queued relation lock not observed')
                        time.sleep(.01)
                    started = time.monotonic()
                    with self.assertRaises(psycopg.errors.LockNotAvailable):
                        with coordinator.transaction(): observe()
                    elapsed = time.monotonic()-started
                    self.assertLess(elapsed, 1)
                    self.assertEqual(data.execute('SELECT pg_current_snapshot()::text,pg_current_xact_id()::text').fetchone(), self.original_snapshot)
                finally:
                    blocker.cancel()
                self.assertEqual(future.result(timeout=5), 'cancelled')
            blocker.execute('ROLLBACK')
        with coordinator.transaction(force_rollback=True):
            self.assertEqual(observe(), self.original_inventory)
        # Live lock census, not a remembered success flag: rollback removes the
        # actual D cut while its original full XID and snapshot remain unchanged.
        data.execute('ROLLBACK TO bridge_cut')
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            with coordinator.transaction(): observe()
        self.assertEqual(data.execute('SELECT truss.bridge_inventory_probe(%s,%s,true)', (anchor, nonce)).fetchone()[0], self.original_inventory)
        directory = os.environ.get('TRUSS_BRIDGE_INVENTORY_EVIDENCE')
        if directory:
            root = Path(directory);root.mkdir(parents=True, exist_ok=True)
            (root/'inventory.json').write_text(json.dumps(self.original_inventory, indent=2)+'\n')
            (root/'observations.json').write_text(json.dumps({'ddlRefusals':refusals,'queuedExplicitLockRefused':True,
                'queuedRefusalSeconds':elapsed,'originalSnapshotAndXidRetained':True,
                'rolledBackCutRefused':True,'uncommittedDdlExcludedD':True,'ordinaryDirectCallRefused':True,'authority':False}, indent=2)+'\n')
