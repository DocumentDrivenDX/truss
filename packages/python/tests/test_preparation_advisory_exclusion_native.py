# SPDX-License-Identifier: MIT OR Apache-2.0
"""Direct native advisory acquisition exclusion, not complete authority closure."""
from importlib.resources import files
import psycopg
import test_preparation_literal_permit_native as original

_NAMES = ('pg_advisory_lock','pg_advisory_lock_shared','pg_try_advisory_lock',
 'pg_try_advisory_lock_shared','pg_advisory_xact_lock','pg_advisory_xact_lock_shared',
 'pg_try_advisory_xact_lock','pg_try_advisory_xact_lock_shared')


class PreparationAdvisoryExclusionNativeTests(original.PreparationLiteralPermitNativeTests):
    test_original_coordinator_cannot_remint_in_later_transaction = None

    def prepare_component(self, admin, owner):
        super().prepare_component(admin,owner)
        if getattr(self,'unsafe_set_role',False):
            admin.execute('CREATE ROLE advisory_set_holder NOLOGIN;CREATE ROLE advisory_execution_holder NOLOGIN')
            admin.execute('GRANT advisory_execution_holder TO advisory_set_holder WITH INHERIT TRUE')
            admin.execute('GRANT advisory_set_holder TO products_person WITH INHERIT FALSE, SET TRUE')
            admin.execute('GRANT EXECUTE ON FUNCTION pg_catalog.pg_advisory_xact_lock(int4,int4) TO advisory_execution_holder')

    def after_claim_commit(self, admin, session, coordinator, anchor, nonce, params):
        data = session.connection
        data.execute("SELECT truss.literal_permit_probe(%s,%s,'cut')",(anchor,nonce))
        if getattr(self,'unsafe_set_role',False):
            # Direct actor does not inherit this grant. SET ROLE can obtain it,
            # including the second role's inherited EXECUTE privilege.
            self.assertFalse(coordinator.execute("SELECT has_function_privilege(session_user,'pg_catalog.pg_advisory_xact_lock(int4,int4)','EXECUTE')").fetchone()[0])
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with coordinator.transaction():
                    coordinator.execute("SELECT truss.literal_permit_probe(%s,%s,'issue')",(anchor,nonce))
            return
        for name in _NAMES:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with coordinator.transaction():
                    coordinator.execute('SELECT pg_catalog.'+name+'(42,43)')
        # Excluded privileged guarded mint still works after all direct routes
        # have been removed from the original ordinary executor.
        with coordinator.transaction(force_rollback=True):
            coordinator.execute("SELECT truss.literal_permit_probe(%s,%s,'issue')",(anchor,nonce))
            data.execute("SELECT truss.literal_permit_probe(%s,%s,'require')",(anchor,nonce))

    def test_set_reachable_role_inherited_execute_refuses(self):
        self.unsafe_set_role = True
        self.test_engine_capture_and_independently_committed_native_claim()
