# SPDX-License-Identifier: MIT OR Apache-2.0
"""HF05 native candidate sources; compiler/public composition is a separate gate."""
import json
import os
import time
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import psycopg
from truss import Ok, QueryRefused
from truss.catalog_runtime import _release
from truss.contracts import BooleanValue, TextValue
from truss.groups import AuthoredValue, GroupSuccess, UpdateObject, StoredObjectReference
import test_compiled_query_native as fixtures


class QuerySelectiveSourcesTests(fixtures.CompiledQueryTests):
    for _name in tuple(n for n in dir(fixtures.CompiledQueryTests) if n.startswith('test_')):
        locals()[_name]=None

    def binding(self, connection, scan=10000, maximum_bytes=1048576):
        manifest,digest,_=_release()
        raw=connection.execute('SELECT truss.person_query_binding(%s::jsonb,%s,1000,%s,%s,%s)',
            ('["adoc"]',scan,maximum_bytes,manifest['releaseId'],digest)).fetchone()[0]
        return json.loads(bytes(raw))['bindingJson']

    def coordinates(self):
        return self.admin.execute("SELECT t.type_id,p.prop_id,k.key_id FROM truss.type_def t JOIN truss.prop_def p USING(type_id) JOIN truss.key_def k USING(type_id) WHERE t.element='A' AND p.element='A-label' AND k.retired_rev IS NULL AND cardinality(k.prop_ids)=1 ORDER BY k.key_num LIMIT 1").fetchone()

    def test_original_umf_key_projection_is_exact_or_explicitly_unindexable(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        # Original native owner encoder produces tuples. Independent expected values
        # include lexical length boundaries, non-ASCII order and valid larger keys.
        for value in ('','a','z','aa','é','😀','x'*127,'x'*128,'x'*1024,'x'*1025):
            raw=self.admin.execute("SELECT convert_to('umf-key-tuple-v1:hex:'||encode(truss.encode_umf_scalar_key_tuple(%s::jsonb,'[{}]'),'hex'),'UTF8')",
                (json.dumps([{'kind':'string','text':value}]),)).fetchone()[0]
            actual=self.admin.execute('SELECT truss.runtime_query_single_string_key(%s)',(raw,)).fetchone()[0]
            self.assertEqual(actual,value if len(value.encode('utf8'))<=1024 else None)
        for raw in (b'',b'garbage',b'umf-key-tuple-v1:hex:554d464b3101048000',b'umf-key-tuple-v1:hex:554d464b31010401ff'):
            self.assertIsNone(self.admin.execute('SELECT truss.runtime_query_single_string_key(%s)',(raw,)).fetchone()[0])

    def test_selected_source_and_ordered_seek_retain_native_refusals(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        self.assertIsInstance(self.run_group(a,t,(self.create(label='z',alias='z'),self.create(label='aa',alias='aa'),self.create(label='a',alias='a')))[0],GroupSuccess)
        selected_type,property_id,key=self.coordinates();binding=self.binding(c)
        selected=json.dumps({str(property_id):{'kind':'string','text':'aa'}})
        rows=c.execute('SELECT * FROM truss.person_query_selected_objects(%s::jsonb,%s,%s::jsonb)',(binding,selected_type,selected)).fetchall()
        self.assertEqual([r[1][str(property_id)]['text'] for r in rows],['aa'])
        for after,expected in [(None,['a','aa']),('a',['aa','z']),('zz',[])]:
            rows=c.execute('SELECT * FROM truss.person_query_seek_objects(%s::jsonb,%s,%s,%s,2)',(binding,selected_type,key,after)).fetchall()
            self.assertEqual(sorted(r[1][str(property_id)]['text'] for r in rows),expected)
        small=self.binding(c,scan=1)
        with self.assertRaises(psycopg.Error) as raised:
            with c.transaction():c.execute('SELECT * FROM truss.person_query_seek_objects(%s::jsonb,%s,%s,NULL,2)',(small,selected_type,key)).fetchall()
        self.assertEqual(raised.exception.sqlstate,'54000')
        self.assertEqual(c.execute('SELECT 42').fetchone(),(42,))
        self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.query_selected_objects(jsonb,int,jsonb) FROM group_writer')
        self.assertFalse(self.admin.execute("SELECT has_function_privilege('consumer','truss.query_selected_objects(jsonb,int,jsonb)','EXECUTE')").fetchone()[0])
        with self.assertRaises(psycopg.Error) as raised:
            with c.transaction():c.execute('SELECT * FROM truss.person_query_selected_objects(%s::jsonb,%s,%s::jsonb)',(binding,selected_type,selected)).fetchall()
        self.assertEqual(raised.exception.sqlstate,'42501')
        self.admin.execute('GRANT EXECUTE ON FUNCTION truss.query_selected_objects(jsonb,int,jsonb) TO group_writer')
        self.admin.execute('REVOKE group_writer FROM consumer')
        with self.assertRaises(psycopg.Error) as raised:
            with c.transaction():c.execute('SELECT * FROM truss.person_query_selected_objects(%s::jsonb,%s,%s::jsonb)',(binding,selected_type,selected)).fetchall()
        # The finite person gate rejects the now-unenrolled native caller.
        self.assertEqual(raised.exception.sqlstate,'P1403')

    def test_selected_string_operand_preserves_exact_token_bound_with_json_overhead(self):
        c,h,a,t=self.ready(document_ids=('adoc',));selected_type,property_id,key=self.coordinates();binding=self.binding(c)
        for value in ('x'*1048576,'\x01'*1048576):
            cells=json.dumps({str(property_id):{'kind':'string','text':value}})
            self.assertEqual(c.execute('SELECT * FROM truss.person_query_selected_objects(%s::jsonb,%s,%s::jsonb)',(binding,selected_type,cells)).fetchall(),[])
        cells=json.dumps({str(property_id):{'kind':'string','text':'x'*1048577}})
        with self.assertRaises(psycopg.Error) as raised:
            with c.transaction():c.execute('SELECT * FROM truss.person_query_selected_objects(%s::jsonb,%s,%s::jsonb)',(binding,selected_type,cells)).fetchall()
        self.assertEqual(raised.exception.sqlstate,'54000')

    def test_selected_boolean_cells_preserve_true_and_false(self):
        def boolean(source):next(e for e in source['modules'][0]['elements'] if e['id']=='A-value')['scalarType']='boolean'
        c,h,a,t=self.ready(boolean,document_ids=('adoc',));operations=[]
        for value in (False,True):
            original=self.create(label=str(value),alias=str(value))
            operations.append(replace(original,values=(original.values[0],AuthoredValue(name='A-value',value=BooleanValue(value=value)))))
        self.assertIsInstance(self.run_group(a,t,tuple(operations))[0],GroupSuccess)
        selected_type,_,_=self.coordinates();binding=self.binding(c)
        property_id=self.admin.execute("SELECT prop_id FROM truss.prop_def WHERE type_id=%s AND element='A-value'",(selected_type,)).fetchone()[0]
        for value in (False,True):
            cells=json.dumps({str(property_id):{'kind':'boolean','value':value}})
            rows=c.execute('SELECT * FROM truss.person_query_selected_objects(%s::jsonb,%s,%s::jsonb)',(binding,selected_type,cells)).fetchall()
            self.assertEqual([row[1][str(property_id)] for row in rows],[{'kind':'boolean','value':value}])

    def test_data_wrapper_preserves_statement_snapshot_with_volatile_countercontrol(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        seeded=self.run_group(a,t,(self.create(label='stable',value='before-stable',alias='stable'),self.create(label='volatile',value='before-volatile',alias='volatile')))[0]
        self.assertIsInstance(seeded,GroupSuccess);identities={r.alias:r.identity for r in seeded.response.semantic.results}
        h.detach();c.commit();c,h,a,t=self.consumer()
        selected_type,_,_=self.coordinates();binding=self.binding(c)
        property_id=self.admin.execute("SELECT prop_id FROM truss.prop_def WHERE type_id=%s AND element='A-value'",(selected_type,)).fetchone()[0]
        signature='truss.person_query_objects(jsonb,int)'
        source=self.admin.execute('SELECT pg_get_functiondef(%s::regprocedure)',(signature,)).fetchone()[0]
        self.assertEqual(self.admin.execute('SELECT provolatile FROM pg_proc WHERE oid=%s::regprocedure',(signature,)).fetchone(),('s',))
        lock_key=918234570
        try:
            for mode in ('volatile','stable'):
                # Fixture-only barrier changes no data predicate or returned cell.
                # Restore exact source before cleanup; this is snapshot evidence,
                # not certification of an administratively modified installation.
                self.admin.execute(source.replace('RETURN QUERY',f'PERFORM pg_catalog.pg_advisory_xact_lock({lock_key});\n RETURN QUERY',1))
                self.admin.execute(f'ALTER FUNCTION {signature} {mode.upper()}')
                self.admin.execute('SELECT pg_advisory_lock(%s)',(lock_key,))
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future=pool.submit(lambda:c.execute('SELECT * FROM truss.person_query_objects(%s::jsonb,%s)',(binding,selected_type),prepare=False).fetchall())
                    try:
                        deadline=time.monotonic()+10
                        while not self.admin.execute("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=%s AND wait_event='advisory')",(c.info.backend_pid,)).fetchone()[0]:
                            if future.done():self.fail('Native source returned before the controlled data boundary: '+repr(future.result()))
                            if time.monotonic()>deadline:self.fail('Native source did not reach the controlled advisory barrier')
                            time.sleep(0.01)
                        writer,writer_host,writer_assembly,writer_tx=self.consumer()
                        update=UpdateObject(target=StoredObjectReference(identity=identities[mode]),set=(AuthoredValue(name='A-value',value=TextValue(kind='string',text='after-'+mode)),),unset=(),expected_version='1')
                        changed=self.run_group(writer_assembly,writer_tx,(update,),'snapshot-update-'+mode)[0]
                        self.assertIsInstance(changed,GroupSuccess,repr(changed));writer_host.detach();writer.commit()
                    finally:self.admin.execute('SELECT pg_advisory_unlock(%s)',(lock_key,))
                    rows=future.result(timeout=10)
                observed=next(props[str(property_id)]['text'] for identity,props in rows if str(identity)==identities[mode].id)
                self.assertEqual(observed,('before-' if mode=='stable' else 'after-')+mode)
                # The fixture barrier is transaction-scoped on the reader.
                h.detach();c.rollback();c,h,a,t=self.consumer();binding=self.binding(c)
        finally:
            self.admin.execute('SELECT pg_advisory_unlock_all()')
            self.admin.execute(source)

    def test_populated_10001_managed_objects_select_without_legacy_source_scan(self):
        def single_primary(source):
            record=next(e for e in source['modules'][0]['elements'] if e['id']=='A')
            primary=next(k for k in record['keys'] if k.get('primary'))
            primary['fields']=[{'module':'m','element':'A-label'}]
            record['keys']=[primary]
        c,h,a,t=self.ready(single_primary,document_ids=('adoc',));batches=[]
        for start in range(0,10001,1000):
            started=time.monotonic();operations=tuple(self.create(label=f'k{i:05}',value='sparse' if i%997==0 else 'ordinary',alias=f'item{i}') for i in range(start,min(start+1000,10001)))
            result=self.run_group(a,t,operations,f'indexed-population-{start}')[0]
            self.assertIsInstance(result,GroupSuccess,repr(result))
            batches.append({'start':start,'objects':len(operations),'seconds':time.monotonic()-started})
            print(json.dumps({'managedPopulationBatch':batches[-1]}),flush=True)
        h.detach();c.commit();c,h,a,t=self.consumer()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(10001,))
        selected_type,property_id,key=self.coordinates();binding=self.binding(c)
        self.admin.execute('ANALYZE truss.object');self.admin.execute('ANALYZE truss.object_key_bucket')
        legacy=a.query_in_transaction(t,sql='SELECT COUNT(*) FROM "A" a',document_ids=('adoc',))
        self.assertIsInstance(legacy,Ok,repr(legacy));self.assertIsInstance(legacy.value,QueryRefused);self.assertEqual(legacy.value.code,'limits')
        selections=[]
        for value,expected in [('k09999',1),('absent',0)]:
            self.admin.execute('SELECT pg_stat_clear_snapshot()')
            before=self.admin.execute("SELECT idx_scan FROM pg_stat_user_indexes WHERE indexrelname='object_query_cells_gin'").fetchone()[0]
            cells=json.dumps({str(property_id):{'kind':'string','text':value}});started=time.monotonic()
            rows=c.execute('SELECT * FROM truss.person_query_selected_objects(%s::jsonb,%s,%s::jsonb)',(binding,selected_type,cells)).fetchall()
            self.assertEqual(len(rows),expected)
            h.detach();c.commit();c.execute('SELECT pg_stat_force_next_flush()')
            self.admin.execute('SELECT pg_stat_clear_snapshot()')
            after_scans=self.admin.execute("SELECT idx_scan FROM pg_stat_user_indexes WHERE indexrelname='object_query_cells_gin'").fetchone()[0]
            self.assertGreater(after_scans,before,'Actual native source must use the selected GIN index')
            plan=self.admin.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT o.id FROM truss.object o WHERE o.type_id=%s AND o.props @> %s::jsonb LIMIT 10001',(selected_type,cells)).fetchone()[0]
            self.assertIn('object_query_cells_gin',json.dumps(plan))
            selections.append({'key':value,'rows':len(rows),'seconds':time.monotonic()-started,'actualSourceGinScans':after_scans-before,'nativeCandidatePlan':plan})
            c,h,a,t=self.consumer();binding=self.binding(c)
        self.admin.execute('SELECT pg_stat_clear_snapshot()')
        seek_before=self.admin.execute("SELECT idx_scan FROM pg_stat_user_indexes WHERE indexrelname='object_key_query_string_order'").fetchone()[0]
        for after,expected in [(None,['k00000','k00001','k00002']),('k09998',['k09999','k10000']),('k10000',[])]:
            rows=c.execute('SELECT * FROM truss.person_query_seek_objects(%s::jsonb,%s,%s,%s,3)',(binding,selected_type,key,after)).fetchall()
            self.assertEqual(sorted(r[1][str(property_id)]['text'] for r in rows),expected)
        h.detach();c.commit();c.execute('SELECT pg_stat_force_next_flush()');self.admin.execute('SELECT pg_stat_clear_snapshot()')
        seek_after=self.admin.execute("SELECT idx_scan FROM pg_stat_user_indexes WHERE indexrelname='object_key_query_string_order'").fetchone()[0]
        self.assertGreater(seek_after,seek_before)
        key_number=self.admin.execute('SELECT key_num FROM truss.key_def WHERE type_id=%s AND key_id=%s',(selected_type,key)).fetchone()[0]
        seek_plan=self.admin.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT k.object_id FROM truss.object_key_bucket k WHERE k.type_id=%s AND k.key_num=%s AND truss.runtime_query_single_string_key(k.key_bytes) IS NOT NULL AND (truss.runtime_query_single_string_key(k.key_bytes) COLLATE "C")>(%s COLLATE "C") ORDER BY truss.runtime_query_single_string_key(k.key_bytes) COLLATE "C" LIMIT 3',(selected_type,key_number,'k09998')).fetchone()[0]
        self.assertIn('object_key_query_string_order',json.dumps(seek_plan))
        c,h,a,t=self.consumer();binding=self.binding(c)
        self.assertIsInstance(self.run_group(a,t,(self.create(label='x'*1025,alias='long-key'),),'valid-long-key')[0],GroupSuccess)
        with self.assertRaises(psycopg.Error) as raised:
            with c.transaction():c.execute('SELECT * FROM truss.person_query_seek_objects(%s::jsonb,%s,%s,%s,3)',(binding,selected_type,key,'k09998')).fetchall()
        self.assertEqual(raised.exception.sqlstate,'54000','An unindexable key requires the complete bounded fallback, never silent omission')
        h.detach();c.rollback();c,h,a,t=self.consumer()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(10001,))
        receipt={'scope':'Native source component,10001 public-group-created committed objects; exact compiled-query composition not yet qualified',
            'managedBatches':batches,'selectedReads':selections,'orderedSourceIndexScans':seek_after-seek_before,'nativeSeekPlan':seek_plan,'validLongKeyFallback':'54000 complete source bound; caller rollback preserves prior10001 committed objects','serverVersion':c.execute('SHOW server_version').fetchone()[0]}
        if os.environ.get('TRUSS_HF05_SELECTIVE_RECEIPT'):Path(os.environ['TRUSS_HF05_SELECTIVE_RECEIPT']).write_text(json.dumps(receipt,indent=2)+'\n')
