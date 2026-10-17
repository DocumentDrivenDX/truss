"""Actual ordinary Subject transaction retains source/data cuts after helper return.

No graph activation, role-catalog issuer or full guarded-release qualification.
"""
import json,os
from pathlib import Path
import psycopg
from unittest.mock import patch
from truss import Ok,Error
from truss._current_query_subjects import observe_current_query_subject_in_transaction
from psycopg import sql
import test_current_query_subjects_native as base
from truss._security_catalog_assessment import SOURCE_TABLES


class CurrentQuerySubjectCutNativeTests(base.CurrentQuerySubjectsNativeTests):
    test_ordinary_session_observes_only_enrolled_subject_and_original_key=None

    def test_source_key_edge_cuts_block_writers_until_caller_settlement(self):
        base.CurrentQuerySubjectsNativeTests.test_ordinary_session_observes_only_enrolled_subject_and_original_key(self)
        caller=self.consumer_connections[-1][0]
        homes=tuple(dict.fromkeys((*SOURCE_TABLES,'source_epoch_current','source_epoch_registry',
            'installation_marker','installation_archive','catalog_subject_map','module_access',
            'object','object_key_bucket','edge')))
        self.assertEqual(caller.execute('SELECT session_user,current_user').fetchone(),('consumer','consumer'))
        rows=self.admin.execute("SELECT c.relname,l.mode FROM pg_catalog.pg_locks l JOIN pg_catalog.pg_class c ON c.oid=l.relation JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE l.pid=%s AND l.locktype='relation' AND l.granted AND n.nspname='truss' AND l.mode='ShareLock' ORDER BY c.relname",(caller.info.backend_pid,)).fetchall()
        self.assertEqual([name for name,mode in rows],sorted(homes))
        # Empty edge populations still require the physical relation cut.
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
        blocked=[]
        with psycopg.connect(**psycopg.conninfo.conninfo_to_dict(self.info.connection_uri),autocommit=True) as writer:
            for home in homes:
                writer.execute('BEGIN')
                try:
                    with self.assertRaises(psycopg.errors.LockNotAvailable):
                        writer.execute(sql.SQL('LOCK TABLE ONLY {} IN ROW EXCLUSIVE MODE NOWAIT').format(sql.Identifier('truss',home)))
                    blocked.append(home)
                finally:writer.rollback()
            for home in ('object','object_key_bucket','edge'):
                writer.execute('BEGIN');writer.execute("SET LOCAL lock_timeout='100ms'")
                try:
                    with self.assertRaises(psycopg.errors.LockNotAvailable):
                        writer.execute(sql.SQL('DELETE FROM ONLY {} WHERE false').format(sql.Identifier('truss',home)))
                finally:writer.rollback()
            # Releasing the actual ordinary transaction must release its locks;
            # private-host or Python lease identity is not a substitute.
            for connection,host in self.consumer_connections:
                host.detach()
                if not connection.closed:connection.rollback()
            writer.execute('BEGIN')
            for home in homes:
                writer.execute(sql.SQL('LOCK TABLE ONLY {} IN ROW EXCLUSIVE MODE NOWAIT').format(sql.Identifier('truss',home)))
            writer.rollback()
            # A pre-existing edge writer must refuse observation before the
            # original Key encoder runs, with no partial Subject or retained cut.
            writer.execute('BEGIN');writer.execute('LOCK TABLE ONLY truss.edge IN ROW EXCLUSIVE MODE NOWAIT')
            blocked_connection,blocked_host,_,blocked_tx=self.consumer()
            bun=os.environ['TRUSS_BUN_EXECUTABLE']
            try:
                with patch('truss._current_query_subjects.encode_string_key_tuples') as encoder:
                    refused=observe_current_query_subject_in_transaction(blocked_host,blocked_tx,self.current_subject_registration,bun_executable=bun)
                    self.assertIsInstance(refused,Error);encoder.assert_not_called()
                self.assertEqual(self.admin.execute('SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=%s AND mode=%s AND granted',(blocked_connection.info.backend_pid,'ShareLock')).fetchone(),(0,))
            finally:
                blocked_host.detach();blocked_connection.rollback();writer.rollback()
            fresh_connection,fresh_host,_,fresh_tx=self.consumer()
            restored=observe_current_query_subject_in_transaction(fresh_host,fresh_tx,self.current_subject_registration,bun_executable=bun)
            self.assertIsInstance(restored,Ok,str(fresh_host._custody.last_attempt.error))
            self.assertEqual(restored.value.key,'alice');fresh_host.detach();fresh_connection.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=%s AND mode=%s AND granted',(caller.info.backend_pid,'ShareLock')).fetchone(),(0,))
        target=os.environ.get('TRUSS_SUBJECT_CUT_EVIDENCE')
        if target:
            Path(target).write_text(json.dumps({'caller':'consumer','sourceAndDataHomes':list(homes),
                'blockedNativeWriterLocks':blocked,'blockedNoopWrites':['object','object_key_bucket','edge'],
                'allWriterLocksSucceedAfterCallerRollback':True,'edgePopulation':0,
                'preexistingEdgeWriterRefusesBeforeKeyEncoding':True,'failedHelperRetainsNoPartialShareCut':True,'freshObservationAfterWriterRollback':'alice',
                'graphActivation':False,'roleCatalogIssuer':False,'casePromotion':0},indent=2)+'\n')
