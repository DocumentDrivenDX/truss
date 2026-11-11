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
        # ready_temporal() genuinely seeds six prepared objects and can warm
        # the process-wide cache. Isolate this test's real native selection,
        # clearing both its connection hint and the bounded schema cache.
        from collections import OrderedDict
        from truss import _schema_memory as memory
        a._record_schema_state.clear()
        with patch.object(memory,'_cache',OrderedDict()),patch.object(memory,'_cache_bytes',0), \
             patch.object(schemas,'compile_records',wraps=schemas.compile_records) as compile_once:
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

    def test_older_object_newer_catalog_supplied_temporal_patch_is_never_ignored(self):
        import truss._record_preparation as preparation
        from truss import CatalogDocument
        import psycopg
        c,h,a,tx=self.ready_temporal();identity=self.identities[0]
        # Genuine new accepted revision with retained source/owner custody,
        # while the public object still has its earlier stored revision.
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        next_document=CatalogDocument('adoc','r2',self.document.content+b'\n')
        try:
            prepared=a.temporal_values().prepare_catalog((next_document,))
            accepted=a.temporal_values().accept_in_transaction(tx,prepared,request_key='prepared-newer-catalog')
            self.assertIsInstance(accepted,Ok,repr(accepted));self.assertEqual(accepted.value.revision,2)
        finally:
            self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        h.detach();c.commit();self.documents=(next_document,);self.document=next_document
        c,h,a,tx=self.consumer();selected=a.temporal_values();commands=self.track(h)
        stored_revision=self.admin.execute('SELECT rev FROM truss.object WHERE id=%s AND type_id=%s',(int(identity.id),int(identity.type_id))).fetchone()[0]
        current_revision=self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1').fetchone()[0]
        self.assertLess(stored_revision,current_revision)
        current_identity=self.selected_read(selected,tx,identity).identity
        context=selected.group_context_in_transaction(tx);self.assertIsInstance(context,Ok)
        update=temporal.UpdateObject(target=StoredObjectReference(identity=current_identity),expected_version='1',unset=(),
            set=(temporal.AuthoredValue(name='A-local',value=LocalTimestampValue(text='2000-02-29T12:34:56.000001')),))
        original=context.value.input((update,),MapValue(entries=()));before=self.registration_snapshot(c)
        original_prepare=preparation.prepare_records;packets=[]
        def tamper(*args,**kwargs):
            packet=original_prepare(*args,**kwargs);self.assertIsNotNone(packet)
            packet=copy.deepcopy(packet);packets.append(packet)
            packet['operations'][0]['propsSet'][str(self.property_ids['A-local'])]['text']='2001-01-01T00:00:00.000001'
            return packet
        commands.clear()
        with patch.object(preparation,'prepare_records',side_effect=tamper):
            refused=selected.apply_in_transaction(tx,original,RequestNone(),documents=self.documents)
        self.assertEqual(len(packets),1);self.assertIsInstance(refused,Ok,repr(refused));self.assertIsInstance(refused.value,GroupFailed,repr(refused))
        diagnostic=json.loads(base64.b64decode(refused.value.failure.diagnostic.bytes_base64,validate=True))
        self.assertEqual(diagnostic['nativeState'],'22023');self.assertEqual(self.registration_snapshot(c),before)
        self.assertEqual(sum('person_apply_temporal_group_prepared' in q for q in commands),1)
        self.assertFalse(any('person_apply_temporal_group(' in q for q in commands))
        valid=selected.apply_in_transaction(tx,original,RequestNone(),documents=self.documents)
        self.assertIsInstance(valid,Ok,repr(valid));self.assertIsInstance(valid.value,GroupSuccess,repr(valid))
        self.assertEqual(dict(self.selected_read(selected,tx,current_identity).values)['A-local'],LocalTimestampValue(text='2000-02-29T12:34:56.000001'))
        print('temporal-prepared-older-object '+json.dumps({'storedRevision':stored_revision,'catalogRevision':current_revision,
            'tamperState':'22023','tamperEffects':0,'unpreparedFallbacks':0,'pairedValidPreparedUpdate':True},sort_keys=True))

    def test_native_schema_cumulative_byte_overflow_refuses_before_complete_aggregation(self):
        import psycopg
        c,h,a,tx=self.ready_temporal()
        before=self.admin.execute('SELECT truss.temporal_writer_basis_custody()').fetchone()[0]
        selected=self.admin.execute('SELECT type_id FROM truss.runtime_type_schema WHERE rev=(SELECT rev FROM truss.schema_head WHERE id=1) ORDER BY type_id LIMIT 2').fetchall()
        self.assertEqual(len(selected),2,'Actual fixture needs two native type schema rows for cumulative overflow')
        self.admin.execute('BEGIN')
        try:
            self.admin.execute("UPDATE truss.runtime_type_schema SET metadata=metadata||jsonb_build_object('x-negative-resource-control',repeat('x',9*1024*1024)) WHERE rev=(SELECT rev FROM truss.schema_head WHERE id=1) AND type_id=ANY(%s)",([v[0] for v in selected],))
            maximum,total=self.admin.execute("SELECT max(octet_length(to_jsonb(t)::text)),sum(octet_length(to_jsonb(t)::text)) FROM truss.runtime_type_schema t WHERE rev=(SELECT rev FROM truss.schema_head WHERE id=1)").fetchone()
            self.assertLess(maximum,16777216);self.assertGreater(total,16777216)
            with self.assertRaises(psycopg.Error) as refused:
                with self.admin.transaction():self.admin.execute('SELECT truss.temporal_writer_basis_custody()')
            self.assertEqual(refused.exception.sqlstate,'54000')
        finally:self.admin.rollback()
        self.assertEqual(self.admin.execute('SELECT truss.temporal_writer_basis_custody()').fetchone()[0],before)
        print('temporal-prepared-cumulative-budget '+json.dumps({'maximumIndividualRowBytes':maximum,'cumulativeRowBytes':int(total),
            'limitBytes':16777216,'refusalState':'54000','pairedRestoredNativeBasis':True},sort_keys=True))
