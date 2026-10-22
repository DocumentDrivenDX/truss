# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual public atomic capacity; no deadline increases or no-op substitutes."""
from dataclasses import replace
import json
import os
from pathlib import Path
import platform
import psycopg
from truss import Ok,Error,ObjectFound
from truss.contracts import MapValue,TextValue,ABSENT,ProfilePin
from truss.groups import (AuthoredValue,GroupSuccess,GroupUnavailable,RequestNone,
                          UpdateObject,StoredObjectReference,CommittedReceiptReplay)
from truss.object_read import ObjectPage
import test_group_create_native as base

class GroupCapacityTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def setUp(self):
        super().setUp()
        self.statistics_directory=os.environ.get('TRUSS_CAPACITY_FUNCTION_STATS')
        self.statistics_setup_error=None
        if self.statistics_directory:
            try:
                with self.admin.transaction():
                    self.admin.execute("ALTER ROLE consumer SET track_functions='all'")
            except Exception as error:
                self.statistics_setup_error=type(error).__name__

    def capture_statistics(self,connection,host,phase):
        """Optional completed-call observations; never qualify clean timing."""
        if not self.statistics_directory:return
        observation={'phase':phase,'test':self.id(),'source':os.environ.get('GITHUB_SHA','local'),
            'platform':platform.system().lower()+'-'+platform.machine(),'status':'unavailable',
            'columns':['schema','function','calls','totalMilliseconds','selfMilliseconds'],
            'scope':'Current transaction through this apply return; incomplete calls and later COMMIT work are excluded'}
        try:
            custody=host._custody
            if self.statistics_setup_error:
                observation['reason']='tracking_setup_'+self.statistics_setup_error
            elif connection.closed or connection.info.transaction_status!=psycopg.pq.TransactionStatus.INTRANS:
                observation['reason']='connection_not_in_usable_transaction'
            elif custody.quarantined or custody.pending is not None or custody.reservation is not None:
                observation['reason']='connection_custody_unavailable'
            else:
                # Contain only a diagnostic query failure, preserving all original
                # effects and the apply result. Never recover a failed host here.
                with connection.transaction():
                    observation['tracking']=connection.execute('SHOW track_functions').fetchone()[0]
                    if observation['tracking']=='all':
                        observation['functions']=connection.execute(
                            "SELECT schemaname,funcname,calls,total_time,self_time FROM pg_stat_xact_user_functions WHERE schemaname='truss' ORDER BY self_time DESC,funcname").fetchall()
                        observation['status']='captured'
                    else:observation['reason']='tracking_not_enabled'
        except Exception as error:
            observation.update(reason='collection_'+type(error).__name__,sqlState=getattr(error,'sqlstate',None))
        try:
            directory=Path(self.statistics_directory);directory.mkdir(parents=True,exist_ok=True)
            name=observation['platform']+'-'+self._testMethodName+'-'+phase+'.json'
            (directory/name).write_text(json.dumps(observation,indent=2)+'\n')
        except Exception as error:
            print('Capacity function statistics unavailable:',type(error).__name__)

    def _after_consumer_cleanup(self,backend_pids):
        if not self.statistics_directory:return
        observation={'test':self.id(),'source':os.environ.get('GITHUB_SHA','local'),
            'platform':platform.system().lower()+'-'+platform.machine(),'status':'unavailable',
            'recordedBackendPids':backend_pids,
            'columns':['schema','function','calls','totalMilliseconds','selfMilliseconds'],
            'scope':'All tracked completed Truss calls across this fixture, including registration, reads and settlement. Untracked admin work and incomplete calls are excluded. Diagnostic overhead is not clean timing; nested totals overlap.'}
        try:
            if self.statistics_setup_error:
                observation['reason']='tracking_setup_'+self.statistics_setup_error
            else:
                # Closing a client may precede backend exit/statistics flush.
                # One fresh check records this race; it does not wait or recover
                # a quarantined host to obtain diagnostic data.
                self.admin.execute('SELECT pg_catalog.pg_stat_clear_snapshot()').fetchone()
                pending=self.admin.execute("""SELECT pid FROM pg_catalog.pg_stat_activity
                    WHERE pid=ANY(%s::int[]) OR (datname=pg_catalog.current_database()
                        AND usename='consumer' AND backend_type='client backend') ORDER BY pid""",
                    ([pid for pid in backend_pids if type(pid) is int and pid>0],)).fetchall()
                observation['pendingBackendPids']=[row[0] for row in pending]
                observation['functions']=self.admin.execute("""SELECT schemaname,funcname,calls,total_time,self_time
                    FROM pg_catalog.pg_stat_user_functions WHERE schemaname='truss'
                    ORDER BY self_time DESC,funcname""").fetchall()
                observation['status']='partial' if pending or None in backend_pids else 'captured'
                if pending:observation['reason']='backend_exit_or_flush_pending'
                elif None in backend_pids:observation['reason']='backend_pid_unavailable'
        except Exception as error:
            observation.update(reason='collection_'+type(error).__name__,sqlState=getattr(error,'sqlstate',None))
        try:
            directory=Path(self.statistics_directory);directory.mkdir(parents=True,exist_ok=True)
            name=observation['platform']+'-'+self._testMethodName+'-cumulative-after-close.json'
            (directory/name).write_text(json.dumps(observation,indent=2)+'\n')
        except Exception as error:
            print('Capacity cumulative statistics unavailable:',type(error).__name__)

    def tearDown(self):
        self.admin.execute('DROP TRIGGER IF EXISTS capacity_late_fault ON truss.object')
        self.admin.execute('DROP FUNCTION IF EXISTS public.capacity_late_fault()')
        super().tearDown()

    def operations(self,count):
        return tuple(self.create(label=f'c{i:04d}',value=f'v{i:04d}',alias=ABSENT) for i in range(count))

    def assert_empty(self):
        for table in ('object','journal','object_key_bucket','object_key_reservation_bucket','request_receipt','runtime_object_attempt','runtime_owned_operation','runtime_object_transition'):
            self.assertEqual(self.admin.execute(psycopg.sql.SQL('SELECT count(*) FROM truss.{}').format(psycopg.sql.Identifier(table))).fetchone(),(0,),table)

    def test_1024_real_creates_updates_replay_and_ordered_public_readback(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        context=assembly.group_context_in_transaction(tx).value
        original=context.input(self.operations(1024),MapValue(entries=()))
        created=assembly.apply_in_transaction(tx,original,context.request('capacity-create'),documents=self.documents)
        self.capture_statistics(connection,host,'create')
        self.assertIsInstance(created,Ok,repr(created)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(created.value,GroupSuccess,repr(created))
        results=created.value.response.semantic.results
        self.assertEqual(len(results),1024);self.assertTrue(all(r.outcome=='created' for r in results))
        identities=tuple(r.identity for r in results)
        # The bound belongs to each group, not all creates in the caller's transaction.
        later=context.input((self.create(label='later-group',value='extra',record='B',alias=ABSENT),),MapValue(entries=()))
        following=assembly.apply_in_transaction(tx,later,context.request('following-group'),documents=self.documents)
        self.capture_statistics(connection,host,'following')
        self.assertIsInstance(following,Ok,repr(following));self.assertIsInstance(following.value,GroupSuccess,repr(following))
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        context=assembly.group_context_in_transaction(tx).value
        changes=tuple(UpdateObject(target=StoredObjectReference(identity=identity),
            set=(AuthoredValue(name='A-value',value=TextValue(kind='string',text=f'u{i:04d}')),),
            unset=(),expected_version='1') for i,identity in enumerate(identities))
        update=context.input(changes,MapValue(entries=()));request=context.request('capacity-update')
        updated=assembly.apply_in_transaction(tx,update,request,documents=self.documents)
        self.capture_statistics(connection,host,'update')
        self.assertIsInstance(updated,Ok,repr(updated)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(updated.value,GroupSuccess,repr(updated))
        self.assertEqual(len(updated.value.response.semantic.results),1024)
        self.assertTrue(all(r.outcome=='changed' for r in updated.value.response.semantic.results))
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        replay=assembly.apply_in_transaction(tx,update,request,documents=self.documents)
        self.capture_statistics(connection,host,'replay')
        self.assertIsInstance(replay,Ok,repr(replay));self.assertIsInstance(replay.value.response,CommittedReceiptReplay,repr(replay))
        self.assertEqual(replay.value.response.semantic,updated.value.response.semantic)
        objects=[];cursor=None
        while True:
            page=assembly.page_objects_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',limit=512,cursor=cursor)
            self.assertIsInstance(page,Ok,repr(page));self.assertIsInstance(page.value,ObjectPage,repr(page))
            objects.extend(page.value.objects);cursor=page.value.continuation
            if cursor is None:break
        self.assertEqual(tuple(o.identity.id for o in objects),tuple(i.id for i in identities))
        self.assertEqual(tuple(dict(o.values) for o in objects),tuple({'A-label':f'c{i:04d}','A-value':f'u{i:04d}'} for i in range(1024)))
        self.assertTrue(all(o.version==2 for o in objects))
        for index in (0,511,1023):
            label=f'c{index:04d}'
            found=assembly.lookup_key_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',key_id='z-alt',values=(label,))
            self.assertIsInstance(found,Ok,repr(found));self.assertIsInstance(found.value,ObjectFound,repr(found))
            self.assertEqual(found.value.object.identity.id,identities[index].id)
            self.assertEqual(dict(found.value.object.values)['A-value'],f'u{index:04d}')
            self.assertEqual(found.value.object.version,2)
        host.detach();connection.commit()

    def test_1025_refuses_in_host_and_native_without_durable_effects(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        context=assembly.group_context_in_transaction(tx).value
        original=context.input(self.operations(1025),MapValue(entries=()))
        refused=assembly.apply_in_transaction(tx,original,RequestNone(),documents=self.documents)
        self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,GroupUnavailable)
        self.assertEqual(refused.value.reason,'resource')
        host.detach();connection.commit();self.assert_empty()
        from truss._group_runtime import _bytes,_wire
        from truss.catalog_runtime import _release
        manifest,digest,_=_release()
        documents=_bytes([{'documentId':d.document_id,'sourceText':d.content.decode()} for d in self.documents])
        def native(input):
            return json.loads(bytes(connection.execute('SELECT truss.apply_group(%s,%s,%s,%s,%s)',
                (_bytes(_wire(input)),documents,_bytes(_wire(RequestNone())),manifest['releaseId'],digest)).fetchone()[0]))
        connection,host,assembly,tx=self.consumer()
        self.assertEqual(native(replace(original,operations=original.operations[:1]))['outcome'],'success')
        host.detach();connection.rollback();self.assert_empty()
        connection,host,assembly,tx=self.consumer()
        refusal=native(original);self.assertEqual(refusal['outcome'],'unavailable')
        host.detach();connection.commit();self.assert_empty()
        legacy=replace(original,operations=original.operations[:129],mutation_profile=ProfilePin(
            identity='truss-rootless-scalar-graph',version='0.4',sha256='b814eb5b33ff59340d2f9bd13866ccb97d49f42fd38ce1e9c97facab5668a2f8'))
        connection,host,assembly,tx=self.consumer()
        refused=assembly.apply_in_transaction(tx,legacy,RequestNone(),documents=self.documents)
        self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,GroupUnavailable)
        self.assertEqual(refused.value.reason,'resource')
        host.detach();connection.commit();self.assert_empty()
        connection,host,assembly,tx=self.consumer()
        self.assertEqual(native(legacy)['outcome'],'unavailable')
        host.detach();connection.commit();self.assert_empty()

    def test_effect_fault_at_index_1023_rolls_back_the_entire_group(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        connection.execute("CREATE TEMP TABLE prior_work(value text);INSERT INTO prior_work VALUES('kept')")
        self.admin.execute("CREATE FUNCTION public.capacity_late_fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.props::text LIKE '%capacity-late-1023%' THEN RAISE EXCEPTION 'late capacity effect' USING ERRCODE='P9999';END IF;RETURN NEW;END $$")
        self.admin.execute('CREATE TRIGGER capacity_late_fault BEFORE INSERT ON truss.object FOR EACH ROW EXECUTE FUNCTION public.capacity_late_fault()')
        operations=self.operations(1024)
        operations=operations[:-1]+(self.create(label='capacity-late-1023',value='last',alias=ABSENT),)
        context=assembly.group_context_in_transaction(tx).value
        result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),RequestNone(),documents=self.documents)
        self.capture_statistics(connection,host,'late-fault')
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'P9999',repr(result))
        self.assertEqual(connection.execute('TABLE prior_work').fetchall(),[('kept',)])
        host.detach();connection.commit();self.assert_empty()
