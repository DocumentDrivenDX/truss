# SPDX-License-Identifier: MIT OR Apache-2.0
"""TN11 actual buffering/revocation and native-lock timeout containment.

Uses genuine owner generation/capture/compilation from the temporal engine
fixture. No fake owner enrollment or synthetic successful native response.
"""
import json
from threading import Event,Thread
from time import monotonic
from unittest.mock import patch
import psycopg
from truss import Ok,Error
from truss.query import QueryRows,QueryRefused
from truss.catalog_runtime import _release,_pin_cursor
from truss._temporal_query_execution import run_read
import test_temporal_engine_native as engine


class TemporalTargetReleaseTests(engine.TemporalEngineNativeTests):
    for _name in tuple(n for n in dir(engine.TemporalEngineNativeTests) if n.startswith('test_')):
        locals()[_name]=None

    def read_entry(self):
        row=self.ready_engine()
        sql='SELECT '+','.join(engine.quoted(element)+' AS '+engine.quoted(name) for module,element,name in row.UMF_FIELDS)+ \
            ' FROM "A" ORDER BY "A-label" ASC'
        return self.entry(row,sql)

    def test_revoked_current_authority_withholds_buffered_native_temporal_rows(self):
        from truss.access import TrussReadRefused
        from truss import _temporal_query_execution as execution
        entry,parameters=self.read_entry();original=execution.decode_rows;observed=[]
        def revoke_after_actual_decode(*args,**kwargs):
            result=original(*args,**kwargs)
            self.assertIsInstance(result,QueryRows,repr(result));self.assertEqual(len(result.rows),6)
            observed.append({'bufferedRows':len(result.rows),'completeDescriptors':len(result.column_descriptors)})
            self.admin.execute('REVOKE group_writer FROM consumer')
            return result
        try:
            with patch.object(execution,'decode_rows',side_effect=revoke_after_actual_decode):
                with self.assertRaises(TrussReadRefused) as denied:self.target(entry).read(entry,parameters)
            self.assertEqual(len(observed),1)
            self.assertIsInstance(denied.exception.original,Ok,repr(denied.exception.original))
            self.assertEqual(denied.exception.original.value,QueryRefused(code='unauthorized'))
        finally:self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
        self.assertEqual(len(self.target(entry).read(entry,parameters)),6)
        print('temporal-native-final-authority '+json.dumps({'observations':observed,
            'releasedRows':0,'regrantRealReadRows':6,'scope':'actual native authority revoked after real buffering'},sort_keys=True))

    def test_expired_native_temporal_lock_wait_cancels_and_preserves_caller_work(self):
        entry,parameters=self.read_entry();program=entry.artifact();request=program['request']
        binding=json.loads(request['target']['bindingJson']);manifest,digest,_=_release()
        c,h,a,tx=self.consumer()
        c.execute('CREATE TEMP TABLE temporal_prior_work(value int)')
        c.execute('INSERT INTO temporal_prior_work VALUES(9)')
        pid=c.info.backend_pid;observed_wait=Event();stop=Event();observer_errors=[]
        def observe_lock():
            try:
                with psycopg.connect(**psycopg.conninfo.conninfo_to_dict(self.info.connection_uri),
                                     autocommit=True,options='-c statement_timeout=1000') as observer:
                    while not stop.is_set():
                        waiting=observer.execute("SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_locks "
                            "WHERE pid=%s AND relation='truss.object'::regclass AND NOT granted)",(pid,)).fetchone()[0]
                        if waiting:observed_wait.set();return
                        stop.wait(.01)
            except BaseException as error:observer_errors.append(repr(error))
        self.admin.execute('BEGIN');self.admin.execute('LOCK TABLE truss.object IN ACCESS EXCLUSIVE MODE')
        worker=Thread(target=observe_lock,daemon=True);worker.start()
        started=monotonic()
        try:
            result=run_read(h,tx,engine_program=entry.artifact_json,sql=request['sql'],
                document_ids=tuple(m['pin']['documentId'] for m in request['modules']),parameters={},
                maximum_rows=binding['maximumResultRows'],maximum_scan_rows=binding['maximumScanRows'],
                maximum_bytes=binding['maximumBytes'],manifest=manifest,digest=digest,pin_cursor=_pin_cursor,
                operation_deadline=started+2)
        finally:
            stop.set();worker.join(5);self.admin.rollback()
        self.assertFalse(worker.is_alive());self.assertEqual(observer_errors,[])
        self.assertTrue(observed_wait.is_set(),'Must actually wait on the native object relation; a pre-SQL timeout is insufficient')
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.code,'cancelled')
        self.assertFalse(h._custody.quarantined)
        self.assertEqual(c.info.transaction_status,psycopg.pq.TransactionStatus.INTRANS)
        self.assertEqual(c.execute('SELECT * FROM temporal_prior_work').fetchall(),[(9,)])
        self.assertEqual(c.info.backend_pid,pid)
        print('temporal-native-deadline-containment '+json.dumps({'backendPid':pid,'actualObjectLockWait':True,
            'elapsedSeconds':monotonic()-started,'resultCode':result.error.code,'nativeState':result.error.sql_state,
            'callerTransaction':'INTRANS','priorWorkPreserved':True,'quarantined':False},sort_keys=True))
        h.detach();c.rollback()
