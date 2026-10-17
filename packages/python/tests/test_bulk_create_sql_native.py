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
        definition=self.admin.execute("SELECT pg_get_functiondef('truss.runtime_owned_prepare(jsonb,jsonb)'::regprocedure)").fetchone()[0]
        self.assertEqual(definition.count('edge_creates:=NOT EXISTS('),1)
        reference=definition.replace('truss.runtime_owned_prepare(', 'public.reference_edge_prepare(',1)
        reference=reference.replace('edge_creates:=NOT EXISTS(', 'edge_creates:=false AND NOT EXISTS(',1)
        self.admin.execute(reference)
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.reference_edge_prepare(jsonb,jsonb)')
        self.admin.execute("""CREATE FUNCTION public.compare_edge_plans() RETURNS trigger LANGUAGE plpgsql AS $$
            DECLARE original_input jsonb;scope jsonb;
            BEGIN
              IF NEW.operation_index=0 THEN
                SELECT convert_from(input_bytes,'UTF8')::jsonb INTO STRICT original_input
                  FROM truss.runtime_object_attempt WHERE id=NEW.attempt_id;
                scope:=NEW.plan->'initialScope';
                IF truss.runtime_owned_prepare(original_input,scope) IS DISTINCT FROM
                   public.reference_edge_prepare(original_input,scope) THEN
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

    def test_thousand_updates_use_one_update_and_one_journal_insert(self):
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
            {'object':(1,1000),'journal':(1,2000),'runtime_object_transition':(1,1000),'object_key_bucket':(1,1000)})
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
