# SPDX-License-Identifier: MIT OR Apache-2.0
"""A thousand public creates lower to a constant number of physical INSERTs."""
from truss import Ok
from truss.contracts import MapValue
from truss.groups import GroupSuccess,RequestNone
import test_group_create_native as base


class BulkCreateSqlTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_thousand_objects_use_one_insert_per_physical_home(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        self.admin.execute('CREATE TABLE public.bulk_statement_observation(home text, rows_written bigint)')
        self.addCleanup(self.admin.execute,'DROP TABLE IF EXISTS public.bulk_statement_observation')
        self.admin.execute('''CREATE FUNCTION public.observe_bulk_insert() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
            BEGIN
              INSERT INTO public.bulk_statement_observation SELECT TG_TABLE_NAME,count(*) FROM new_rows;
              RETURN NULL;
            END;$$''')
        self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.observe_bulk_insert() CASCADE')
        from psycopg import sql
        homes=('object','object_key_bucket','object_key_reservation_bucket','journal',
               'runtime_object_transition','runtime_owned_operation')
        for home in homes:
            self.admin.execute(sql.SQL('''CREATE TRIGGER observe_bulk_insert AFTER INSERT ON truss.{}
                REFERENCING NEW TABLE AS new_rows FOR EACH STATEMENT
                EXECUTE FUNCTION public.observe_bulk_insert()''').format(sql.Identifier(home)))
        context=assembly.group_context_in_transaction(tx).value
        operations=tuple(self.create(label=f'bulk-{i}',value=f'value-{i}',alias=f'row-{i}') for i in range(1000))
        result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),
            RequestNone(),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(result.value,GroupSuccess,repr(result))
        self.assertEqual(len(result.value.response.semantic.results),1000)
        host.detach();connection.commit()
        observed=self.admin.execute('SELECT home,count(*),sum(rows_written) FROM public.bulk_statement_observation GROUP BY home').fetchall()
        self.assertEqual({home:statements for home,statements,_ in observed},{home:1 for home in homes})
        counts={home:rows for home,_,rows in observed}
        for home in ('object','journal','runtime_object_transition','runtime_owned_operation'):
            self.assertEqual(counts[home],1000,home)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0],1000)
        values=self.admin.execute("""SELECT cell.value->>'text' FROM truss.object o
            CROSS JOIN LATERAL jsonb_each(o.props) cell
            JOIN truss.prop_def p ON p.type_id=o.type_id AND p.prop_id=cell.key::int
            WHERE p.name='A-value' ORDER BY o.id""").fetchall()
        # The public results preserve input order; canonical values survive the
        # batch independently of statement counting and retained plan metadata.
        self.assertEqual(len({r.identity.id for r in result.value.response.semantic.results}),1000)
        self.assertEqual(values,[(f'value-{i}',) for i in range(1000)])


import test_edge_mutations_native as edge_base
from truss.groups import StoredObjectReference


class BulkEdgeSqlTests(edge_base.EdgeMutationTests):
    for _name in tuple(n for n in dir(edge_base.EdgeMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def ready(self):
        def unbounded(source):
            relationship=source['modules'][0]['relationships'][0]
            relationship['sourceMultiplicity']={'min':0,'max':'*'}
            relationship['targetMultiplicity']={'min':0,'max':'*'}
        return super().ready(unbounded)

    def test_thousand_parallel_edges_use_one_insert_per_physical_home(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        self.admin.execute('CREATE TABLE public.bulk_edge_statement_observation(home text, rows_written bigint)')
        self.addCleanup(self.admin.execute,'DROP TABLE IF EXISTS public.bulk_edge_statement_observation')
        self.admin.execute('''CREATE FUNCTION public.observe_bulk_edge_insert() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
            BEGIN
              INSERT INTO public.bulk_edge_statement_observation SELECT TG_TABLE_NAME,count(*) FROM new_rows;
              RETURN NULL;
            END;$$''')
        self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.observe_bulk_edge_insert() CASCADE')
        from psycopg import sql
        homes=('edge','journal','runtime_edge_transition','runtime_owned_operation')
        for home in homes:
            self.admin.execute(sql.SQL('''CREATE TRIGGER observe_bulk_edge_insert AFTER INSERT ON truss.{}
                REFERENCING NEW TABLE AS new_rows FOR EACH STATEMENT
                EXECUTE FUNCTION public.observe_bulk_edge_insert()''').format(sql.Identifier(home)))
        context=assembly.group_context_in_transaction(tx).value
        operations=tuple(self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b),alias=f'edge-{i}') for i in range(1000))
        result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),
            RequestNone(),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(result.value,GroupSuccess,repr(result))
        host.detach();connection.commit()
        observed=self.admin.execute('SELECT home,count(*),sum(rows_written) FROM public.bulk_edge_statement_observation GROUP BY home').fetchall()
        self.assertEqual({home:(statements,int(rows)) for home,statements,rows in observed},
            {home:(1,1000) for home in homes})
        self.assertEqual(self.admin.execute('SELECT count(*),count(DISTINCT id),min(source_id),max(source_id),min(target_id),max(target_id) FROM truss.edge').fetchone(),
            (1000,1000,int(a.id),int(a.id),int(b.id),int(b.id)))

    def test_buffered_edge_plans_equal_the_retained_general_planner(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        definition=self.admin.execute("SELECT pg_get_functiondef('truss.runtime_owned_prepare_application(jsonb,jsonb,jsonb)'::regprocedure)").fetchone()[0]
        self.assertEqual(definition.count('edge_creates:=NOT EXISTS('),1)
        reference=definition.replace('truss.runtime_owned_prepare_application(', 'public.reference_edge_prepare(',1)
        reference=reference.replace('edge_creates:=NOT EXISTS(', 'edge_creates:=false AND NOT EXISTS(',1)
        self.admin.execute(reference)
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.reference_edge_prepare(jsonb,jsonb,jsonb)')
        self.admin.execute("""CREATE FUNCTION public.compare_edge_plans() RETURNS trigger LANGUAGE plpgsql AS $$
            DECLARE original_input jsonb;scope jsonb;
            BEGIN
              IF NEW.operation_index=0 THEN
                SELECT convert_from(input_bytes,'UTF8')::jsonb INTO STRICT original_input
                  FROM truss.runtime_object_attempt WHERE id=NEW.attempt_id;
                scope:=NEW.plan->'initialScope';
                IF truss.runtime_owned_prepare(original_input,scope) IS DISTINCT FROM
                   public.reference_edge_prepare(original_input,scope,NULL) THEN
                  RAISE EXCEPTION 'buffered and general edge preparation differ' USING ERRCODE='P9998';
                END IF;
              END IF;
              RETURN NEW;
            END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.compare_edge_plans()')
        self.admin.execute('CREATE TRIGGER compare_edge_plans BEFORE INSERT ON truss.runtime_owned_operation FOR EACH ROW EXECUTE FUNCTION public.compare_edge_plans()')
        for count in (1,9):
            context=assembly.group_context_in_transaction(tx).value
            operations=tuple(self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b),alias=f'edge-{i}') for i in range(count))
            result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),RequestNone(),documents=self.documents)
            self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error))
            self.assertIsInstance(result.value,GroupSuccess,repr(result))
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(10,))


    def test_value_update_preserves_thousand_unrelated_independent_edges(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        context=assembly.group_context_in_transaction(tx).value
        operations=tuple(self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b),alias=f'independent-{i}') for i in range(1000))
        result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),RequestNone(),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
        host.detach();connection.commit()
        before=self.admin.execute('SELECT to_jsonb(e) FROM truss.edge e ORDER BY id').fetchall()
        connection,host,assembly,tx=self.consumer()
        from truss.groups import UpdateObject,AuthoredValue
        from truss.contracts import TextValue
        context=assembly.group_context_in_transaction(tx).value
        operation=UpdateObject(target=StoredObjectReference(identity=a),set=(AuthoredValue(name='A-value',value=TextValue(kind='string',text='updated')),),unset=(),expected_version='1')
        result=assembly.apply_in_transaction(tx,context.input((operation,),MapValue(entries=())),RequestNone(),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT to_jsonb(e) FROM truss.edge e ORDER BY id').fetchall(),before)
        self.assertEqual(self.admin.execute('SELECT ver FROM truss.object WHERE id=%s',(int(a.id),)).fetchone(),(2,))

    def test_buffered_scope_equals_retained_observer_with_thousand_edges(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        context=assembly.group_context_in_transaction(tx).value
        operations=tuple(self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b),alias=f'scope-{i}') for i in range(1000))
        result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),RequestNone(),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
        edge=result.value.response.semantic.results[0].identity
        host.detach();connection.commit()
        definition=self.admin.execute("SELECT pg_get_functiondef('truss.owned_graph_scope(jsonb)'::regprocedure)").fetchone()[0]
        append='edge_images:=array_append(edge_images,observed.edge_image);'
        assembly_sql=" SELECT coalesce(jsonb_object_agg(c.edge_key,c.image),'{}'::jsonb) INTO edges\n FROM unnest(edge_keys,edge_images) AS c(edge_key,image);"
        self.assertEqual(definition.count(append),1);self.assertEqual(definition.count(assembly_sql),1)
        reference=definition.replace('truss.owned_graph_scope(', 'public.reference_graph_scope(',1)
        reference=reference.replace(append,'edges:=edges||jsonb_build_object(edge_key,observed.edge_image);').replace(assembly_sql,'')
        self.admin.execute(reference)
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.reference_graph_scope(jsonb)')
        self.admin.execute("""CREATE FUNCTION public.compare_scope_buffers() RETURNS trigger LANGUAGE plpgsql AS $$
            DECLARE seeds jsonb;BEGIN
              IF NEW.operation_index=0 THEN
                SELECT jsonb_agg(jsonb_build_object('typeId',split_part(n.node_key,':',1),'id',split_part(n.node_key,':',2)) ORDER BY n.ordinal)
                INTO seeds FROM jsonb_array_elements_text(NEW.plan->'initialScope'->'nodeOrder') WITH ORDINALITY n(node_key,ordinal);
                IF truss.owned_graph_scope(seeds) IS DISTINCT FROM public.reference_graph_scope(seeds) THEN
                  RAISE EXCEPTION 'buffered and retained scope observers differ' USING ERRCODE='P9998';END IF;
              END IF;RETURN NEW;END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.compare_scope_buffers() CASCADE')
        self.admin.execute('CREATE TRIGGER compare_scope_buffers BEFORE INSERT ON truss.runtime_owned_operation FOR EACH ROW EXECUTE FUNCTION public.compare_scope_buffers()')
        connection,host,assembly,tx=self.consumer()
        from truss.groups import UpdateEdge,AuthoredValue
        from truss.contracts import TextValue
        context=assembly.group_context_in_transaction(tx).value
        operation=UpdateEdge(target=StoredObjectReference(identity=edge),set=(AuthoredValue(name='note',value=TextValue(kind='string',text='buffered')),),unset=(),expected_version='1')
        updated=assembly.apply_in_transaction(tx,context.input((operation,),MapValue(entries=())),RequestNone(),documents=self.documents)
        self.assertIsInstance(updated,Ok,repr(updated)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(updated.value,GroupSuccess)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(1000,))


from truss import Error
from truss.contracts import TextValue
from truss.groups import UpdateObject,AuthoredValue


class BulkUpdateSqlTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def initialized_updates(self,count):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        context=assembly.group_context_in_transaction(tx).value
        operations=tuple(self.create(label=f'update-{i}',value=f'before-{i}',alias=f'row-{i}') for i in range(count))
        result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),RequestNone(),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,GroupSuccess)
        identities=tuple(r.identity for r in result.value.response.semantic.results)
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        return connection,host,assembly,tx,identities

    def updates(self,identities,*,unchanged=False):
        return tuple(UpdateObject(target=StoredObjectReference(identity=identity),
            set=(AuthoredValue(name='A-value',value=TextValue(kind='string',text=f'{"before" if unchanged else "after"}-{i}')),),
            unset=(),expected_version='1') for i,identity in enumerate(identities))

    def test_thousand_updates_use_set_based_writes_and_bounded_journal_batches(self):
        connection,host,assembly,tx,identities=self.initialized_updates(1000)
        before_keys=self.admin.execute('SELECT to_jsonb(k) FROM truss.object_key_bucket k ORDER BY storage_row_id').fetchall()
        self.admin.execute('CREATE TABLE public.bulk_update_observation(home text, rows_written bigint)')
        self.addCleanup(self.admin.execute,'DROP TABLE IF EXISTS public.bulk_update_observation')
        self.admin.execute('''CREATE FUNCTION public.observe_bulk_update() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN
            INSERT INTO public.bulk_update_observation SELECT TG_TABLE_NAME,count(*) FROM new_rows;
            RETURN NULL;END;$$''')
        self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.observe_bulk_update() CASCADE')
        from psycopg import sql
        for home,event in (('object','UPDATE'),('journal','INSERT'),('runtime_object_transition','INSERT'),('object_key_bucket','INSERT')):
            self.admin.execute(sql.SQL('''CREATE TRIGGER observe_bulk_update AFTER {} ON truss.{}
                REFERENCING NEW TABLE AS new_rows FOR EACH STATEMENT EXECUTE FUNCTION public.observe_bulk_update()''')
                .format(sql.SQL(event),sql.Identifier(home)))
        context=assembly.group_context_in_transaction(tx).value
        result=assembly.apply_in_transaction(tx,context.input(self.updates(identities),MapValue(entries=())),RequestNone(),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
        self.assertTrue(all(r.outcome=='changed' and r.version=='2' for r in result.value.response.semantic.results))
        host.detach();connection.commit()
        observed=self.admin.execute('SELECT home,count(*),sum(rows_written) FROM public.bulk_update_observation GROUP BY home').fetchall()
        self.assertEqual({home:(statements,int(rows)) for home,statements,rows in observed},
            {'object':(1,1000),'journal':(16,2000),'runtime_object_transition':(1,1000),'object_key_bucket':(1,1000)})
        import json
        after_keys=self.admin.execute('SELECT to_jsonb(k) FROM truss.object_key_bucket k ORDER BY storage_row_id').fetchall()
        # A-value participates in the composite primary key. The independent
        # label key keeps its original membership bytes; new primary tuples
        # receive permanent reservations while their old reservations survive.
        self.assertEqual(len(after_keys),len(before_keys))
        self.assertEqual(len({json.dumps(row,sort_keys=True) for row in before_keys}&{json.dumps(row,sort_keys=True) for row in after_keys}),1000)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object_key_reservation_bucket').fetchone(),(3000,))
        values=self.admin.execute("""SELECT o.ver,cell.value->>'text' FROM truss.object o
            CROSS JOIN LATERAL jsonb_each(o.props) cell JOIN truss.prop_def p ON p.type_id=o.type_id AND p.prop_id=cell.key::int
            WHERE p.name='A-value' ORDER BY o.id""").fetchall()
        self.assertEqual(values,[(2,f'after-{i}') for i in range(1000)])

    def test_noop_batch_preserves_versions_timestamps_and_journals(self):
        connection,host,assembly,tx,identities=self.initialized_updates(3)
        before=self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall()
        journals=self.admin.execute('SELECT count(*) FROM truss.journal').fetchone()
        context=assembly.group_context_in_transaction(tx).value
        result=assembly.apply_in_transaction(tx,context.input(self.updates(identities,unchanged=True),MapValue(entries=())),RequestNone(),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
        self.assertTrue(all(r.outcome=='unchanged' and r.version=='1' for r in result.value.response.semantic.results))
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall(),before)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(),journals)

    def test_late_update_fault_rolls_back_the_complete_batch(self):
        connection,host,assembly,tx,identities=self.initialized_updates(1000)
        before=self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall()
        journal_count=self.admin.execute('SELECT count(*) FROM truss.journal').fetchone()
        connection.execute("CREATE TEMP TABLE prior_update_work(value text);INSERT INTO prior_update_work VALUES('kept')")
        self.admin.execute('''CREATE FUNCTION public.reject_last_batch_update() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN
            IF NEW.id=(SELECT max(id) FROM truss.object) THEN RAISE EXCEPTION 'last update fault' USING ERRCODE='P9999';END IF;
            RETURN NEW;END;$$''')
        self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.reject_last_batch_update() CASCADE')
        self.admin.execute('CREATE TRIGGER reject_last_batch_update AFTER UPDATE ON truss.object FOR EACH ROW EXECUTE FUNCTION public.reject_last_batch_update()')
        try:
            context=assembly.group_context_in_transaction(tx).value
            result=assembly.apply_in_transaction(tx,context.input(self.updates(identities),MapValue(entries=())),RequestNone(),documents=self.documents)
            self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'P9999')
            self.assertEqual(connection.execute('TABLE prior_update_work').fetchall(),[('kept',)])
        finally:self.admin.execute('DROP TRIGGER reject_last_batch_update ON truss.object')
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall(),before)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(),journal_count)

    def test_relational_update_closure_agrees_with_retained_general_validator(self):
        connection,host,assembly,tx,identities=self.initialized_updates(9)
        definition=self.admin.execute("SELECT pg_get_functiondef('truss.runtime_owned_group_validate(uuid,boolean)'::regprocedure)").fetchone()[0]
        self.assertEqual(definition.count('independent_updates:=NOT EXISTS('),1)
        reference=definition.replace('truss.runtime_owned_group_validate(', 'public.reference_update_group_validate(',1)
        reference=reference.replace('independent_updates:=NOT EXISTS(', 'independent_updates:=false AND NOT EXISTS(',1)
        self.admin.execute(reference)
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.reference_update_group_validate(uuid,boolean)')
        self.admin.execute('''CREATE FUNCTION public.compare_update_closure() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
            PERFORM public.reference_update_group_validate(NEW.id,true);RETURN NEW;END;$$''')
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.compare_update_closure() CASCADE')
        self.admin.execute('''CREATE TRIGGER compare_update_closure AFTER UPDATE ON truss.runtime_object_attempt
            FOR EACH ROW WHEN (NEW.complete AND NOT OLD.complete) EXECUTE FUNCTION public.compare_update_closure()''')
        # Independent key-changing updates, a trailing no-op set, then another
        # group in the same transaction qualify both finish and later settlement.
        operations=self.updates(identities)
        noops=self.updates(identities,unchanged=True)
        context=assembly.group_context_in_transaction(tx).value
        first=assembly.apply_in_transaction(tx,context.input(operations[:4]+noops[4:],MapValue(entries=())),RequestNone(),documents=self.documents)
        self.assertIsInstance(first,Ok,repr(first)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(first.value,GroupSuccess)
        self.assertEqual([r.outcome for r in first.value.response.semantic.results],['changed']*4+['unchanged']*5)
        from dataclasses import replace
        next_operations=tuple(replace(operation,expected_version='2' if i<4 else '1') for i,operation in enumerate(operations))
        second=assembly.apply_in_transaction(tx,context.input(next_operations,MapValue(entries=())),RequestNone(),documents=self.documents)
        self.assertIsInstance(second,Ok,repr(second)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(second.value,GroupSuccess)
        self.assertEqual([r.outcome for r in second.value.response.semantic.results],['unchanged']*4+['changed']*5)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object WHERE ver=2').fetchone(),(9,))

    def test_analyzed_history_and_both_plan_modes_preserve_bulk_updates(self):
        connection,host,assembly,tx,identities=self.initialized_updates(1000)
        host.detach();connection.rollback()
        for round_index,mode in enumerate(('force_custom_plan','force_generic_plan')):
            # Production autovacuum updates these statistics as history grows.
            # Exercise both parameter-plan choices with retained prior groups.
            for table in ('runtime_object_transition','runtime_owned_operation','journal','object'):
                self.admin.execute('ANALYZE truss.'+table)
            connection,host,assembly,tx=self.consumer()
            connection.execute('SET LOCAL plan_cache_mode='+mode)
            context=assembly.group_context_in_transaction(tx).value
            operations=tuple(UpdateObject(target=StoredObjectReference(identity=identity),
                set=(AuthoredValue(name='A-value',value=TextValue(kind='string',text=f'round-{round_index}-{i}')),),
                unset=(),expected_version=str(round_index+1)) for i,identity in enumerate(identities))
            result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),RequestNone(),documents=self.documents)
            self.assertIsInstance(result,Ok,mode+' '+repr(result)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
            self.assertTrue(all(r.outcome=='changed' and r.version==str(round_index+2) for r in result.value.response.semantic.results))
            self.assertEqual(connection.execute('SHOW plan_cache_mode').fetchone(),(mode,))
            host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object WHERE ver=3').fetchone(),(1000,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object_key_reservation_bucket').fetchone(),(4000,))
