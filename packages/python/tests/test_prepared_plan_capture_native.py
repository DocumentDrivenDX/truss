"""Canonical plan insertion faults preserve caller work and atomicity."""
from truss import Error
import test_group_create_native as base

class PreparedPlanCaptureTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_plan_insert_error_rolls_back_before_object_effect(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        connection.execute("CREATE TEMP TABLE prior_plan_work(value text);INSERT INTO prior_plan_work VALUES('kept')")
        original,request=self.input(assembly,tx)
        baseline=self.admin.execute('SELECT last_value,is_called FROM truss.id_seq').fetchone()
        self.admin.execute("""CREATE FUNCTION public.rewrite_prepared_plan() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN RAISE EXCEPTION 'injected plan insert failure' USING ERRCODE='55000';END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.rewrite_prepared_plan()')
        self.admin.execute('CREATE TRIGGER rewrite_plan BEFORE INSERT ON truss.runtime_owned_operation FOR EACH ROW EXECUTE FUNCTION public.rewrite_prepared_plan()')
        result=assembly.apply_in_transaction(tx,original,request,documents=self.documents)
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'55000')
        self.assertEqual(self.admin.execute('SELECT last_value,is_called FROM truss.id_seq').fetchone(),baseline)
        self.assertEqual(connection.execute('TABLE prior_plan_work').fetchall(),[('kept',)])
        host.detach();connection.commit()
        for table in ('object','journal','runtime_object_attempt','runtime_owned_operation','runtime_object_transition'):
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.'+table).fetchone(),(0,),table)

    def test_before_insert_suppression_refuses_before_object_effect(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        connection.execute("CREATE TEMP TABLE prior_plan_work(value text);INSERT INTO prior_plan_work VALUES('kept')")
        original,request=self.input(assembly,tx)
        baseline=self.admin.execute('SELECT last_value,is_called FROM truss.id_seq').fetchone()
        self.admin.execute("""CREATE FUNCTION public.suppress_prepared_plan() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN RETURN NULL;END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.suppress_prepared_plan()')
        self.admin.execute('CREATE TRIGGER suppress_plan BEFORE INSERT ON truss.runtime_owned_operation FOR EACH ROW EXECUTE FUNCTION public.suppress_prepared_plan()')
        result=assembly.apply_in_transaction(tx,original,request,documents=self.documents)
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'55000')
        self.assertEqual(self.admin.execute('SELECT last_value,is_called FROM truss.id_seq').fetchone(),baseline)
        self.assertEqual(connection.execute('TABLE prior_plan_work').fetchall(),[('kept',)])
        host.detach();connection.commit()
        for table in ('object','journal','runtime_object_attempt','runtime_owned_operation','runtime_object_transition'):
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.'+table).fetchone(),(0,),table)
