# SPDX-License-Identifier: MIT OR Apache-2.0
"""HF-02 independently expected person admission, damage and disclosure controls."""
import json
import psycopg
from truss import Error, Ok
from truss.groups import GroupFailed, UnauthorizedPerson
import test_hohfeld_disputes_native as baseline


class PersonInvocationNativeTests(baseline.HohfeldDisputesNativeTests):
    for _name in tuple(n for n in dir(baseline.HohfeldDisputesNativeTests) if n.startswith('test_')):
        locals()[_name] = None

    def observe(self, identity, result, *, desired, facts=None):
        super().observe(identity,result,desired=desired,facts=facts)
        if identity.startswith(('nonmember.','damaged-grant.')):
            self.assertTrue(desired,repr(result))

    test_nonmember_all_selected_surfaces_have_typed_denial = baseline.HohfeldDisputesNativeTests.test_capture_nonmember_context_references_reads_groups_and_imports
    test_damaged_original_entrypoint_grant_is_execution_error = baseline.HohfeldDisputesNativeTests.test_capture_damaged_function_grant_separate_from_enrollment

    def test_damaged_private_dependency_is_execution_error(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        self.assertIsInstance(a.group_context_in_transaction(t),Ok)
        self.admin.execute(psycopg.sql.SQL('REVOKE EXECUTE ON FUNCTION truss.runtime_group_profiles() FROM {}').format(psycopg.sql.Identifier(self.installation.owner_role)))
        self.assertFalse(self.admin.execute('SELECT has_function_privilege(%s,%s,%s)',(self.installation.owner_role,'truss.runtime_group_profiles()','EXECUTE')).fetchone()[0])
        result=a.group_context_in_transaction(t)
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'42501')
        self.assertEqual(c.execute('SELECT 42').fetchone(),(42,))

    def test_damaged_mutation_grants_are_not_business_denial(self):
        c,h,a,t=self.ready(document_ids=('adoc',));semantic,request=self.input(a,t)
        before=self.group_effect_counts()
        self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.apply_group(bytea,bytea,bytea,text,text),truss.apply_group_prepared(bytea,bytea,bytea,text,text,jsonb) FROM group_writer')
        result=a.apply_in_transaction(t,semantic,request,documents=self.documents)
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'42501')
        self.assertEqual(self.group_effect_counts(),before)
        self.assertEqual(c.execute('SELECT 42').fetchone(),(42,))

    def test_reader_keeps_context_but_cannot_apply_and_prior_work_survives(self):
        c,h,a,t=self.ready(document_ids=('adoc',));semantic,request=self.input(a,t)
        h.detach();c.rollback()
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE');self.admin.execute('REVOKE group_writer FROM consumer')
        c,h,a,t=self.consumer();c.execute("CREATE TEMP TABLE prior_person_work(value text);INSERT INTO prior_person_work VALUES('kept')")
        context=a.group_context_in_transaction(t)
        self.assertIsInstance(context,Ok);self.assertNotIsInstance(context.value,UnauthorizedPerson)
        result=a.apply_in_transaction(t,semantic,request,documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,GroupFailed)
        self.assertIsInstance(result.value.failure,UnauthorizedPerson)
        self.assertEqual(c.execute('TABLE prior_person_work').fetchall(),[('kept',)])
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))

    def test_normal_context_stays_three_statements(self):
        c,h,a,t=self.ready(document_ids=('adoc',));original=h._cursor;queries=[]
        class Counted:
            def __init__(self,cursor):self.cursor=cursor
            def __getattr__(self,name):return getattr(self.cursor,name)
            def execute(self,query,*args,**kwargs):
                queries.append(str(query));return self.cursor.execute(query,*args,**kwargs)
        h._cursor=lambda:Counted(original())
        result=a.group_context_in_transaction(t)
        self.assertIsInstance(result,Ok,repr(result));self.assertNotIsInstance(result.value,UnauthorizedPerson)
        self.assertEqual(len(queries),3,queries)

    def test_public_shim_does_not_grant_private_implementation_or_table_access(self):
        c,h,a,t=self.ready(document_ids=('adoc',));h.detach();c.rollback()
        self.admin.execute('REVOKE group_writer FROM consumer')
        self.assertTrue(self.admin.execute("SELECT has_function_privilege('consumer','truss.person_group_context(text,text)','EXECUTE')").fetchone()[0])
        self.assertFalse(self.admin.execute("SELECT has_function_privilege('consumer','truss.group_context(text,text)','EXECUTE')").fetchone()[0])
        c,h,a,t=self.consumer();result=a.group_context_in_transaction(t)
        self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,UnauthorizedPerson)
        h.detach();c.rollback()
        for query in ('SELECT count(*) FROM truss.module_access',"SELECT truss.group_context('untrusted','untrusted')"):
            with self.subTest(query=query):
                with self.assertRaises(psycopg.Error) as raised:c.execute(query)
                self.assertEqual(raised.exception.sqlstate,'42501')
        with self.assertRaises(psycopg.Error) as raised:c.execute("SELECT truss.person_group_context('untrusted','untrusted')")
        self.assertEqual(raised.exception.sqlstate,'P1403')

    def test_changed_original_entrypoint_owner_is_integrity_error(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        self.admin.execute('CREATE ROLE changed_invocation_owner NOLOGIN')
        self.addCleanup(self.admin.execute,'DROP ROLE changed_invocation_owner')
        self.admin.execute('ALTER FUNCTION truss.group_context(text,text) OWNER TO changed_invocation_owner')
        result=a.group_context_in_transaction(t)
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'55000')
        self.assertEqual(c.execute('SELECT 42').fetchone(),(42,))
