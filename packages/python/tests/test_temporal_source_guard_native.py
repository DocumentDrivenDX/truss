# SPDX-License-Identifier: MIT OR Apache-2.0
"""TN02–04 installed real-source controls. No prefilter or materialization claim
is accepted without first-fetch refusal and actual coordinated observations.
"""
import copy
import json
from uuid import uuid4
import psycopg
import temporal_native_fixture as fixture


class TemporalSourceGuardNativeTests(fixture.TemporalNativeFixture):
    def first_fetch_refuses(self, connection, statement, arguments, expected):
        released = []
        with self.assertRaises(psycopg.Error) as caught:
            with connection.transaction():
                with connection.cursor(name='temporal_' + uuid4().hex[:12]) as cursor:
                    cursor.execute(statement, arguments)
                    row = cursor.fetchone()
                    if row is not None:
                        released.append(row)
                    self.fail('Complete source fault released a first fetch or silently returned empty')
        self.assertEqual(caught.exception.sqlstate, expected)
        self.assertEqual(released, [])
        self.assertEqual(connection.execute('SELECT 42').fetchone(), (42,))

    def test_invalid_source_is_not_hidden_by_outer_filter_or_limit(self):
        connection, host, assembly, transaction = self.ready_temporal()
        binding, requirements = self.capture(connection)
        rows = self.admin.execute('SELECT id,props FROM truss.object WHERE type_id=%s ORDER BY id', (self.selected_type,)).fetchall()
        self.assertEqual([r[0] for r in rows], sorted(int(i.id) for i in self.identities))
        first, later = self.identities[0], self.identities[-1]
        for page in (False, True):
            call = self.source(page)
            args = self.source_arguments(binding, requirements, page)
            self.assertEqual(len(connection.execute('SELECT id FROM ' + call, args).fetchall()), 6)
            for field, cell in (
                ('A-date', {'kind': 'date', 'text': '1900-02-29'}),
                ('A-instant', {'kind': 'timestamp', 'text': '2024-01-01T00:00:00.0000000Z'}),
                ('A-local', {'kind': 'localTimestamp', 'text': '2024-01-01T00:00:00.0000000'})):
                for target in (first, later):
                    original = self.admin.execute('SELECT props FROM truss.object WHERE id=%s AND type_id=%s', (int(target.id), self.selected_type)).fetchone()[0]
                    try:
                        self.fault(target, field, cell)
                        # Only id is projected: every faulted temporal member is
                        # unprojected. First/last exclusion and LIMIT1 both run.
                        for predicate in ('q.id<>%s', 'q.id=%s'):
                            selected_id = int(target.id) if predicate=='q.id<>%s' else int(first.id)
                            with self.subTest(page=page, field=field, target=target.id, predicate=predicate):
                                self.first_fetch_refuses(connection,
                                    'SELECT q.id FROM ' + call + ' q WHERE ' + predicate + ' ORDER BY q.id LIMIT 1',
                                    args + (selected_id,), '22023')
                    finally:
                        self.restore_props(target, original)
                    self.assertEqual(len(connection.execute('SELECT id FROM ' + call, args).fetchall()), 6)

    def test_scan_and_byte_caps_refuse_complete_source(self):
        connection, host, assembly, transaction = self.ready_temporal()
        # Rootless complete bag charge is the sum of actual props::text bytes.
        charge = self.admin.execute('SELECT sum(octet_length(props::text)) FROM truss.object WHERE type_id=%s', (self.selected_type,)).fetchone()[0]
        self.assertGreater(charge, 20000)
        for page in (False, True):
            for scan, cap, state in ((6, charge, None), (5, charge, '54000'), (6, charge-1, '54000')):
                binding, requirements = self.capture(connection, scan=scan, maximum_bytes=cap)
                call = self.source(page); args = self.source_arguments(binding, requirements, page)
                with self.subTest(page=page, scan=scan, cap=cap):
                    if state is None:
                        self.assertEqual(len(connection.execute('SELECT id FROM ' + call, args).fetchall()), 6)
                    else:
                        self.first_fetch_refuses(connection, 'SELECT id FROM ' + call + ' LIMIT 1', args, state)

    def test_wrong_provenance_kind_and_presence_requirements_refuse(self):
        connection, host, assembly, transaction = self.ready_temporal()
        binding, original = self.capture(connection)
        self.assertEqual([f['kind'] for f in original['fields']], ['date', 'instant', 'local'])
        for page in (False, True):
            for mutation in ('empty', 'unprojected-member', 'duplicate', 'foreign', 'kind', 'presence', 'order', 'version', 'extra'):
                changed = copy.deepcopy(original)
                if mutation=='empty': changed['fields'] = []
                elif mutation=='unprojected-member': changed['fields'].pop()
                elif mutation=='duplicate': changed['fields'].append(copy.deepcopy(changed['fields'][-1]))
                elif mutation=='foreign': changed['fields'][-1]['field']['element'] = 'foreign'
                elif mutation=='kind': changed['fields'][-1]['kind'] = 'instant'
                elif mutation=='presence': changed['fields'][-1]['presence']['missing'] = False
                elif mutation=='order': changed['fields'].reverse()
                elif mutation=='version': changed['version'] = 'truss.temporal-source-guard/0.1'
                else: changed['override'] = True
                with self.subTest(page=page, mutation=mutation):
                    self.first_fetch_refuses(connection, 'SELECT id FROM ' + self.source(page) + ' LIMIT 1',
                                            self.source_arguments(binding, changed, page), '22023')

    def _public_instant_update(self, value):
        from truss import temporal
        from truss.contracts import TextValue
        from truss.groups import AuthoredValue,StoredObjectReference,GroupSuccess
        writer,host,assembly,transaction=self.consumer()
        result,_,_=self.run_group(assembly.temporal_values(),transaction,
            (temporal.UpdateObject(target=StoredObjectReference(identity=self.identities[0]),
                set=(AuthoredValue(name='A-instant',value=TextValue(kind='timestamp',text=value)),),unset=()),))
        self.assertIsInstance(result,GroupSuccess,repr(result))
        host.detach();writer.commit()
        return {'writerBackend':writer.info.backend_pid,'publicOutcome':result.outcome,'committed':True,'value':value}

    def _wait_advisory(self, connection, future):
        import time
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            self.admin.execute('SELECT pg_stat_clear_snapshot()')
            waiting=self.admin.execute("SELECT wait_event_type,wait_event FROM pg_stat_activity WHERE pid=%s",(connection.info.backend_pid,)).fetchone()
            if waiting==('Lock','advisory'):
                self.assertFalse(future.done(),'Reader must still be held before any result')
                return {'readerBackend':connection.info.backend_pid,'waitEventType':waiting[0],'waitEvent':waiting[1]}
            if future.done():self.fail('Reader completed before observed advisory barrier: '+repr(future.result()))
            time.sleep(0.01)
        self.fail('Bounded reader advisory wait was not observed')

    def _barriers(self):
        self.admin.execute('CREATE SCHEMA temporal_fixture')
        self.addCleanup(self.admin.execute,'DROP SCHEMA temporal_fixture CASCADE')
        self.admin.execute('GRANT USAGE ON SCHEMA temporal_fixture TO group_writer')
        self.admin.execute('''CREATE FUNCTION temporal_fixture.wait_binding(binding jsonb,lock_key bigint) RETURNS jsonb
            LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
            BEGIN PERFORM pg_advisory_xact_lock(lock_key);RETURN binding;END;$$''')
        self.admin.execute('''CREATE FUNCTION temporal_fixture.wait_count(source_count bigint,lock_key bigint) RETURNS bigint
            LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
            BEGIN PERFORM pg_advisory_xact_lock(lock_key);RETURN source_count;END;$$''')
        self.admin.execute('''CREATE FUNCTION temporal_fixture.refreshed_source(binding jsonb,selected_type int,requirements jsonb,selected_key text,lock_key bigint)
            RETURNS TABLE(id bigint,props jsonb) LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
            BEGIN PERFORM temporal_fixture.wait_binding(binding,lock_key);
             IF selected_key IS NULL THEN RETURN QUERY SELECT * FROM truss.person_query_temporal_objects(binding,selected_type,requirements);
             ELSE RETURN QUERY SELECT * FROM truss.person_query_temporal_page_objects(binding,selected_type,selected_key,requirements);END IF;
            END;$$''')
        for signature in ('wait_binding(jsonb,bigint)','wait_count(bigint,bigint)','refreshed_source(jsonb,int,jsonb,text,bigint)'):
            self.admin.execute('REVOKE ALL ON FUNCTION temporal_fixture.'+signature+' FROM PUBLIC')
            self.admin.execute('GRANT EXECUTE ON FUNCTION temporal_fixture.'+signature+' TO group_writer')

    def _native_tokens(self, connection, binding, requirements, page):
        rows=connection.execute('SELECT id,props FROM '+self.source(page)+' ORDER BY id',self.source_arguments(binding,requirements,page)).fetchall()
        return [(r[0],r[1][str(self.property_ids['A-instant'])]['text']) for r in rows]

    def test_stable_source_keeps_statement_snapshot_across_concurrent_public_update(self):
        from concurrent.futures import ThreadPoolExecutor
        connection,host,assembly,transaction=self.ready_temporal()
        self._barriers();events=[]
        self.assertEqual(connection.execute('SHOW transaction_isolation').fetchone(),('read committed',))
        binding,requirements=self.capture(connection)
        for page in (False,True):
            for mode in ('installed-stable','fixture-refreshed-countercontrol'):
                before=self._native_tokens(connection,binding,requirements,page)
                changed='1970-01-01T00:00:'+('11' if mode=='installed-stable' else '12')+'Z'
                lock_key=918735001+(10 if page else 0)+(1 if mode=='installed-stable' else 2)
                self.admin.execute('SELECT pg_advisory_lock(%s)',(lock_key,))
                if mode=='installed-stable':
                    call=self.source(page,binding_expression='temporal_fixture.wait_binding(%s::jsonb,%s)')
                    rest=(self.selected_type,'a-primary',json.dumps(requirements)) if page else (self.selected_type,json.dumps(requirements))
                    query='SELECT id,props FROM '+call+' ORDER BY id';args=(binding,lock_key)+rest
                else:
                    query='SELECT id,props FROM temporal_fixture.refreshed_source(%s::jsonb,%s,%s::jsonb,%s,%s) ORDER BY id'
                    args=(binding,self.selected_type,json.dumps(requirements),'a-primary' if page else None,lock_key)
                def fetch():
                    with connection.cursor(name='temporal_snapshot_'+uuid4().hex[:8]) as cursor:
                        cursor.execute(query,args)
                        return cursor.fetchall()
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future=pool.submit(fetch)
                    try:
                        waiting=self._wait_advisory(connection,future)
                        writer=self._public_instant_update(changed)
                        self.admin.execute('SELECT pg_advisory_unlock(%s)',(lock_key,))
                        result=future.result(timeout=8)
                        observed=[(r[0],r[1][str(self.property_ids['A-instant'])]['text']) for r in result]
                        expected=list(before)
                        if mode=='fixture-refreshed-countercontrol':expected[0]=(expected[0][0],changed)
                        self.assertEqual(observed,expected)
                        following=self._native_tokens(connection,binding,requirements,page)
                        self.assertEqual(following[0][1],changed)
                        events.append({'page':page,'mode':mode,'wait':waiting,'writer':writer,'before':before,'observed':observed,'following':following})
                    finally:
                        self.admin.execute('SELECT pg_advisory_unlock(%s)',(lock_key,))
                        if not future.done():connection.cancel()
                # Session advisory locks are transaction-level in the reader.
                # End that snapshot and release them before the next schedule.
                host.detach();connection.commit();connection,host,assembly,transaction=self.consumer()
                binding,requirements=self.capture(connection)
        print('temporal-statement-snapshot '+json.dumps({'isolation':'read committed','events':events},sort_keys=True))

    def test_buffered_source_uses_statement_snapshot_before_outer_gate(self):
        from concurrent.futures import ThreadPoolExecutor
        connection,host,assembly,transaction=self.ready_temporal()
        self._barriers();events=[]
        for page in (False,True):
            binding,requirements=self.capture(connection)
            before=self._native_tokens(connection,binding,requirements,page)
            lock_key=918735101+(1 if page else 0)
            self.admin.execute('SELECT pg_advisory_lock(%s)',(lock_key,))
            query=('WITH source AS MATERIALIZED (SELECT * FROM '+self.source(page)+'), '
                   'gate AS MATERIALIZED (SELECT temporal_fixture.wait_count((SELECT count(*) FROM source),%s) n) '
                   'SELECT q.id,q.props FROM source q CROSS JOIN gate g WHERE g.n=6 ORDER BY q.id LIMIT 1')
            args=self.source_arguments(binding,requirements,page)+(lock_key,)
            def fetch():
                with connection.cursor(name='temporal_buffer_'+uuid4().hex[:8]) as cursor:
                    cursor.execute(query,args);return cursor.fetchall()
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(fetch)
                try:
                    waiting=self._wait_advisory(connection,future)
                    changed='1970-01-01T00:00:'+('14' if page else '13')+'Z'
                    writer=self._public_instant_update(changed)
                    self.admin.execute('SELECT pg_advisory_unlock(%s)',(lock_key,))
                    result=future.result(timeout=8)
                    observed=[(r[0],r[1][str(self.property_ids['A-instant'])]['text']) for r in result]
                    self.assertEqual(observed,before[:1])
                    self.assertEqual(self._native_tokens(connection,binding,requirements,page)[0][1],changed)
                    events.append({'page':page,'wait':waiting,'writer':writer,'before':before,'observed':observed})
                finally:
                    self.admin.execute('SELECT pg_advisory_unlock(%s)',(lock_key,))
                    if not future.done():connection.cancel()
            host.detach();connection.commit();connection,host,assembly,transaction=self.consumer()
            binding,requirements=self.capture(connection)
            last=self.identities[-1]
            original=self.admin.execute('SELECT props FROM truss.object WHERE id=%s AND type_id=%s',(int(last.id),self.selected_type)).fetchone()[0]
            try:
                self.fault(last,'A-instant',{'kind':'timestamp','text':'2024-01-01T00:00:00.0000000Z'})
                self.first_fetch_refuses(connection,'SELECT id FROM '+self.source(page)+' LIMIT 1',self.source_arguments(binding,requirements,page),'22023')
            finally:self.restore_props(last,original)
        print('temporal-complete-buffer-snapshot '+json.dumps({'isolation':'read committed','events':events},sort_keys=True))
