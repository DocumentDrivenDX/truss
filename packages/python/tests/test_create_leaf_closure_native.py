# SPDX-License-Identifier: MIT OR Apache-2.0
"""Direct regression controls for replacing duplicate CREATE history reconstruction."""
import psycopg
from truss import Ok,Error
import test_group_create_native as base

class CreateLeafClosureTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_second_create_failure_is_contained_and_preserves_caller_work(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        original,request=self.input(assembly,tx,operations=(self.create(label='first',alias='first'),self.create(label='second',alias='second')))
        connection.execute("CREATE TEMP TABLE prior(value text);INSERT INTO prior VALUES('kept')")
        self.admin.execute("""CREATE FUNCTION public.fail_second_create() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN IF NEW.props::text LIKE '%second%' THEN RAISE EXCEPTION 'second create reached' USING ERRCODE='P9999';END IF;RETURN NEW;END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.fail_second_create()')
        self.admin.execute('CREATE TRIGGER fail_second BEFORE INSERT ON truss.object FOR EACH ROW EXECUTE FUNCTION public.fail_second_create()')
        result=assembly.apply_in_transaction(tx,original,request,documents=self.documents)
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'P9999')
        self.assertEqual(connection.execute('TABLE prior').fetchall(),[('kept',)])
        host.detach();connection.commit()
        for table in ('object','journal','runtime_object_transition','runtime_object_attempt'):
            self.assertEqual(self.admin.execute(psycopg.sql.SQL('SELECT count(*) FROM truss.{}').format(psycopg.sql.Identifier(table))).fetchone(),(0,))

    def test_rewritten_progress_refuses_at_create(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        original,request=self.input(assembly,tx)
        connection.execute("CREATE TEMP TABLE prior(value text);INSERT INTO prior VALUES('kept')")
        self.admin.execute("""CREATE FUNCTION public.rewrite_create_progress() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN IF NEW.next_index=1 THEN NEW.results:='[{"tampered":true}]'::jsonb;END IF;RETURN NEW;END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.rewrite_create_progress()')
        self.admin.execute('CREATE TRIGGER rewrite_progress BEFORE UPDATE ON truss.runtime_object_attempt FOR EACH ROW EXECUTE FUNCTION public.rewrite_create_progress()')
        result=assembly.apply_in_transaction(tx,original,request,documents=self.documents)
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'55000')
        self.assertEqual(connection.execute('TABLE prior').fetchall(),[('kept',)])
        host.detach();connection.commit()
        for table in ('object','journal','runtime_object_transition','runtime_object_attempt'):
            self.assertEqual(self.admin.execute(psycopg.sql.SQL('SELECT count(*) FROM truss.{}').format(psycopg.sql.Identifier(table))).fetchone(),(0,))
