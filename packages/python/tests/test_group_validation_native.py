# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual deferred settlement and host-owned validation rollback."""
import psycopg
from truss import Ok,Error,CompletionObserved,GroupValidationObserved
from truss.contracts import MapValue
from truss.groups import GroupSuccess
import test_group_create_native as fixtures

class GroupValidationTests(fixtures.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(fixtures.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None

    def test_dry_run_checks_completion_without_durable_receipt_or_data(self):
        c,h,a,t=self.ready();c.execute('CREATE TEMP TABLE prior(value int)');c.execute('INSERT INTO prior VALUES(9)')
        context=a.group_context_in_transaction(t).value
        original=context.input((self.create(alias='dry'),),MapValue(entries=()))
        tables=('object','journal','runtime_object_attempt','runtime_object_transition')
        # Fixed read-only observer in the disposable fixture; no raw table or
        # sequence privileges are granted to the person (native admission forbids them).
        self.admin.execute("""CREATE FUNCTION public.validation_fixture_observation() RETURNS jsonb
            LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
            SELECT jsonb_build_object('object',(SELECT count(*) FROM truss.object),
              'journal',(SELECT count(*) FROM truss.journal),
              'runtime_object_attempt',(SELECT count(*) FROM truss.runtime_object_attempt),
              'runtime_object_transition',(SELECT count(*) FROM truss.runtime_object_transition),
              'sequenceCalled',(SELECT is_called FROM truss.id_seq)) $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.validation_fixture_observation()')
        before=c.execute('SELECT public.validation_fixture_observation()').fetchone()[0]
        result=a.dry_run_in_transaction(t,original,documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(h._custody.last_attempt.error));self.assertIsInstance(result.value,GroupValidationObserved,repr(result))
        self.assertEqual(result.value.operation_count,1);self.assertEqual(result.value.basis.durability,'rolled_back')
        self.assertEqual(result.value.basis.catalog_revision,'1');self.assertEqual(len(result.value.basis.input_sha256),64)
        after=c.execute('SELECT public.validation_fixture_observation()').fetchone()[0]
        self.assertEqual({name:after[name] for name in tables},{name:before[name] for name in tables})
        self.assertEqual(c.execute('SELECT * FROM prior').fetchall(),[(9,)])
        self.assertTrue(after['sequenceCalled'],'Sequence consumption does not rewind')
        self.assertIsInstance(self.apply(a,t,original,context.request('real-after-dry')),GroupSuccess)
        completed=a.complete_in_transaction(t);self.assertIsInstance(completed,Ok,repr(completed));self.assertIsInstance(completed.value,CompletionObserved)
        h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))

    def test_unrelated_host_constraint_is_not_forced(self):
        c,h,a,t=self.ready()
        c.execute('CREATE TEMP TABLE host_parent(id int PRIMARY KEY)')
        c.execute('CREATE TEMP TABLE host_child(id int REFERENCES host_parent(id) DEFERRABLE INITIALLY DEFERRED)')
        c.execute('INSERT INTO host_child VALUES(1)')
        result=a.complete_in_transaction(t);self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,CompletionObserved)
        # The host's own pending constraint is still deferred and can be repaired.
        c.execute('INSERT INTO host_parent VALUES(1)');h.detach();c.commit()

    def test_deferred_authority_failure_is_observed_and_prior_work_survives(self):
        c,h,a,t=self.ready();c.execute('CREATE TEMP TABLE prior(value int)');c.execute('INSERT INTO prior VALUES(9)')
        context=a.group_context_in_transaction(t).value
        self.assertIsInstance(self.apply(a,t,context.input((self.create(),),MapValue(entries=())),context.request('pending-revoke')),GroupSuccess)
        # A successful check must restore the original pending trigger queue.
        self.assertIsInstance(a.complete_in_transaction(t),Ok)
        self.admin.execute('REVOKE group_writer FROM consumer')
        result=a.complete_in_transaction(t)
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'P1403')
        self.assertEqual(c.execute('SELECT * FROM prior').fetchall(),[(9,)])
        h.detach()
        with self.assertRaises(psycopg.Error) as raised:c.commit()
        self.assertEqual(raised.exception.sqlstate,'P1403')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))

    def test_dry_run_forces_actual_deferred_failure_before_confirmed_rollback(self):
        from unittest.mock import patch
        import truss._group_runtime as runtime
        from truss import ObjectNotFound
        c,h,a,t=self.ready();c.execute('CREATE TEMP TABLE prior(value int)');c.execute('INSERT INTO prior VALUES(9)')
        context=a.group_context_in_transaction(t).value;original=context.input((self.create(),),MapValue(entries=()));identities=[]
        real=runtime.apply_group
        def revoke_after_real_effects(*args,**kwargs):
            result=real(*args,**kwargs);self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,GroupSuccess)
            identities.append(result.value.response.semantic.results[0].identity)
            self.admin.execute('REVOKE group_writer FROM consumer')
            return result
        with patch.object(runtime,'apply_group',side_effect=revoke_after_real_effects):result=a.dry_run_in_transaction(t,original,documents=self.documents)
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'P1403')
        self.assertEqual(c.execute('SELECT * FROM prior').fetchall(),[(9,)])
        self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
        observed=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identities[0].id))
        self.assertIsInstance(observed,Ok,repr(observed));self.assertIsInstance(observed.value,ObjectNotFound)
        h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
