"""Journal inserts remain checked after earlier commit guards have fired."""
import psycopg
from truss.groups import GroupSuccess
import test_object_mutations_native as base


class JournalRowGuardTests(base.ObjectMutationTests):
    for _name in tuple(n for n in dir(base.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name] = None

    def tearDown(self):
        self.admin.execute('DROP TABLE IF EXISTS public.late_journal_fault CASCADE')
        self.admin.execute('DROP FUNCTION IF EXISTS public.defer_late_journal()')
        self.admin.execute('DROP FUNCTION IF EXISTS public.inject_late_journal(boolean)')
        super().tearDown()

    def test_late_journal_inserts_and_partition_clones(self):
        connection, host, assembly, tx = self.ready()
        self.admin.execute("CREATE TABLE truss.journal_future_guard_test PARTITION OF truss.journal FOR VALUES FROM ('2050-01-01') TO ('2051-01-01')")
        attributes = self.admin.execute("""SELECT c.relname,t.tgenabled,t.tgdeferrable,t.tginitdeferred,
            t.tgfoid='truss.runtime_owned_journal_insert_check()'::regprocedure
            FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
            WHERE t.tgname='runtime_owned_journal_insert_commit' ORDER BY c.relname""").fetchall()
        self.assertEqual(attributes,[(name,'A',True,True,True) for name in
            ('journal','journal_future_guard_test','journal_runtime_horizon')])
        self.admin.execute("""CREATE FUNCTION public.inject_late_journal(use_leaf boolean) RETURNS void
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
            BEGIN
             IF use_leaf THEN
              INSERT INTO truss.journal_future_guard_test
              SELECT (jsonb_populate_record(NULL::truss.journal,to_jsonb(j)||
                jsonb_build_object('seq',nextval('truss.journal_seq'),'entity_id',j.entity_id+1000000,'at','2050-01-02T00:00:00Z'))).*
              FROM truss.journal j WHERE j.xid=pg_current_xact_id() LIMIT 1;
             ELSE
              INSERT INTO truss.journal
              SELECT (jsonb_populate_record(NULL::truss.journal,to_jsonb(j)||
                jsonb_build_object('seq',nextval('truss.journal_seq'),'entity_id',j.entity_id+1000000))).*
              FROM truss.journal j WHERE j.xid=pg_current_xact_id() LIMIT 1;
             END IF;
            END $$""")
        self.admin.execute('CREATE TABLE public.late_journal_fault (id int)')
        self.admin.execute('GRANT INSERT ON public.late_journal_fault TO consumer')
        self.admin.execute("""CREATE FUNCTION public.defer_late_journal() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
            BEGIN PERFORM public.inject_late_journal(false);RETURN NULL;END $$""")
        self.admin.execute('CREATE CONSTRAINT TRIGGER late_journal_fault AFTER INSERT ON public.late_journal_fault DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.defer_late_journal()')
        for mode in ('after_flush','late_trigger','direct_future_partition','immediate'):
            with self.subTest(mode=mode):
                result,_,_=self.run_group(assembly,tx,(self.create(),))
                self.assertIsInstance(result,GroupSuccess,repr(result))
                connection.execute('SET CONSTRAINTS ALL IMMEDIATE')
                connection.execute('SET CONSTRAINTS ALL DEFERRED')
                if mode=='late_trigger':
                    connection.execute('INSERT INTO public.late_journal_fault VALUES (1)')
                elif mode=='immediate':
                    connection.execute('SET CONSTRAINTS ALL IMMEDIATE')
                    with self.assertRaisesRegex(psycopg.errors.ObjectNotInPrerequisiteState,'complete mutation journal required'):
                        connection.execute('SELECT public.inject_late_journal(false)')
                    host.detach();connection.rollback()
                else:
                    connection.execute('SELECT public.inject_late_journal(%s)',(mode=='direct_future_partition',))
                if mode!='immediate':
                    host.detach()
                    with self.assertRaisesRegex(psycopg.errors.ObjectNotInPrerequisiteState,'complete mutation journal required'):
                        connection.commit()
                    connection.rollback()
                self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
                self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(),(0,))
                connection,host,assembly,tx=self.consumer()
