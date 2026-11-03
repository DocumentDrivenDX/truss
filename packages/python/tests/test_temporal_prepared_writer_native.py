# SPDX-License-Identifier: MIT OR Apache-2.0
"""Real PV1 cold/warm preparation and supplied-packet refusal controls.

Requires actual enrolled owner artifacts. No native execution from collection.
"""
import base64
import copy
from hashlib import sha256
import json
from unittest.mock import patch
from truss import Ok,Error,LocalTimestampValue
from truss.contracts import MapValue
from truss.groups import GroupSuccess,GroupFailed,GroupUnavailable,UnauthorizedPerson,RequestNone,StoredObjectReference
from truss import temporal
import test_local_timestamp_query_native as local_fixture
import test_temporal_catalog_acceptance_native as acceptance_fixture


class TemporalPreparedWriterNativeTests(local_fixture.LocalTimestampQueryTests):
    for _name in tuple(n for n in dir(local_fixture.LocalTimestampQueryTests) if n.startswith('test_')):
        locals()[_name]=None
    registration_snapshot=acceptance_fixture.TemporalCatalogAcceptanceTests.registration_snapshot

    def track(self,host):
        commands=[];original=host._cursor
        class Observed:
            def __init__(self,inner):self.inner=inner
            def __getattr__(self,name):return getattr(self.inner,name)
            def __enter__(self):self.inner.__enter__();return self
            def __exit__(self,*args):return self.inner.__exit__(*args)
            def execute(self,query,*args,**kw):
                commands.append(query);return self.inner.execute(query,*args,**kw)
        host._cursor=lambda:Observed(original())
        self.addCleanup(setattr,host,'_cursor',original)
        return commands

    def test_real_cold_warm_temporal_prepared_create_update_and_replay(self):
        import truss._record_schema as schemas
        c,h,a,tx=self.ready_temporal();selected=a.temporal_values();commands=self.track(h)
        value=LocalTimestampValue(text='2000-02-29T12:34:56.000001')
        with patch.object(schemas,'compile_records',wraps=schemas.compile_records) as compile_once:
            first,original,request=self.run_group(selected,tx,(self.local_create('prepared-cold',value),),'prepared-cold')
            self.assertIsInstance(first,GroupSuccess,repr(first));identity=first.response.semantic.results[0].identity
            self.assertEqual(compile_once.call_count,1)
            self.assertTrue(any('person_temporal_writer_schema_basis' in q for q in commands))
            self.assertTrue(any('person_apply_temporal_group_prepared' in q for q in commands))
            commands.clear()
            second,_,_=self.run_group(selected,tx,(self.local_create('prepared-warm',value),),'prepared-warm')
            self.assertIsInstance(second,GroupSuccess,repr(second));self.assertEqual(compile_once.call_count,1)
            self.assertFalse(any('writer_schema_basis' in q for q in commands))
            self.assertTrue(any('person_apply_temporal_group_prepared' in q for q in commands))
            commands.clear()
            update=temporal.UpdateObject(target=StoredObjectReference(identity=identity),
                set=(temporal.AuthoredValue(name='A-local',value=LocalTimestampValue(text='2024-01-01T00:00:00.000001')),),unset=(),expected_version='1')
            updated,_,_=self.run_group(selected,tx,(update,),'prepared-update')
            self.assertIsInstance(updated,GroupSuccess,repr(updated));self.assertEqual(compile_once.call_count,1)
            self.assertFalse(any('writer_schema_basis' in q for q in commands))
            self.assertTrue(any('person_apply_temporal_group_prepared' in q for q in commands))
        h.detach();c.commit();c,h,a,tx=self.consumer();selected=a.temporal_values()
        replay=selected.apply_in_transaction(tx,original,request,documents=self.documents)
        from truss.groups import CommittedReceiptReplay
        self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
        self.assertEqual(replay.value.response.semantic,first.response.semantic)
        self.assertEqual(dict(self.selected_read(selected,tx,identity).values)['A-local'],LocalTimestampValue(text='2024-01-01T00:00:00.000001'))
        print('temporal-native-prepared-cold-warm '+json.dumps({'compiledSchemas':1,'preparedCreates':2,'preparedUpdates':1,
            'warmBasisQueries':0,'reopenedExactReplay':True,'manifestSha256':__import__('truss.catalog_runtime',fromlist=['_release'])._release()[1]},sort_keys=True))

    def test_supplied_temporal_prepared_faults_refuse_without_effects_or_fallback(self):
        import truss._record_preparation as preparation
        from truss.groups import UnauthorizedPerson
        c,h,a,tx=self.ready_temporal();selected=a.temporal_values();commands=self.track(h)
        value=LocalTimestampValue(text='2000-02-29T12:34:56.000001')
        good,_,_=self.run_group(selected,tx,(self.local_create('prepared-baseline',value),),'prepared-baseline')
        self.assertIsInstance(good,GroupSuccess,repr(good))
        before=self.registration_snapshot(c);original_prepare=preparation.prepare_records;observations=[]
        for fault,expected in (('profile','profile'),('missing-pin','profile'),('input-hash','observation'),
                ('native-schema','observation'),('owner-source','observation'),('person','observation'),
                ('schema-pin','invalid_input'),('ordinal','invalid_input'),('altered-value','invalid_input')):
            issued=[]
            def damage(*args,**kwargs):
                packet=original_prepare(*args,**kwargs);self.assertIsNotNone(packet)
                packet=copy.deepcopy(packet);issued.append(sha256(json.dumps(packet,sort_keys=True).encode()).hexdigest())
                if fault=='profile':packet['profile']='truss-application-record-preparation/0.1'
                elif fault=='missing-pin':packet.pop('valueProfile')
                elif fault=='input-hash':packet['inputSha256']='0'*64
                elif fault=='native-schema':packet['basis']['nativeSchemaSha256']='0'*64
                elif fault=='owner-source':packet['basis']['ownerSourceSha256']='0'*64
                elif fault=='person':packet['basis']['personOid']='0'
                elif fault=='schema-pin':next(iter(packet['schemas'].values()))['definitionPin']='0'*64
                elif fault=='ordinal':packet['operations'][0]['operationIndex']=1
                elif fault=='altered-value':
                    prop=str(self.property_ids['A-local']);packet['operations'][0]['propsSet'][prop]['text']='2001-01-01T00:00:00.000001'
                return packet
            context=selected.group_context_in_transaction(tx);self.assertIsInstance(context,Ok)
            original=context.value.input((self.local_create('fault-'+fault,value),),MapValue(entries=()))
            commands.clear()
            with patch.object(preparation,'prepare_records',side_effect=damage):
                result=selected.apply_in_transaction(tx,original,RequestNone(),documents=self.documents)
            self.assertEqual(len(issued),1)
            if expected=='profile':
                self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'0A000')
            else:
                self.assertIsInstance(result,Ok,repr(result))
                if expected=='observation':self.assertEqual(result.value,GroupUnavailable(reason='observation'))
                else:
                    self.assertIsInstance(result.value,GroupFailed,repr(result))
                    diagnostic=json.loads(base64.b64decode(result.value.failure.diagnostic.bytes_base64,validate=True))
                    self.assertEqual(diagnostic['nativeState'],'22023')
            self.assertEqual(self.registration_snapshot(c),before)
            self.assertEqual(sum('person_apply_temporal_group_prepared' in q for q in commands),1)
            self.assertFalse(any('person_apply_temporal_group(' in q or 'person_apply_group(' in q for q in commands))
            observations.append({'fault':fault,'originalPacketSha256':issued[0],'expected':expected,'effects':0,'fallbackCalls':0})
        self.admin.execute('REVOKE group_writer FROM consumer')
        try:
            context=selected.group_context_in_transaction(tx)
            self.assertEqual(context,Ok(UnauthorizedPerson()))
        finally:self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
        self.assertEqual(self.registration_snapshot(c),before)
        positive,_,_=self.run_group(selected,tx,(self.local_create('prepared-restored',value),),'prepared-restored')
        self.assertIsInstance(positive,GroupSuccess,repr(positive))
        print('temporal-native-prepared-refusals '+json.dumps(observations,sort_keys=True))
