"""Complete public results are retained once, with immutable operation slots."""
import psycopg
from truss import Ok, Error
from truss.contracts import MapValue, TextValue
from truss.groups import (AliasObjectReference, AuthoredValue, GroupSuccess, UpdateObject)
from truss._group_runtime import _wire
import test_group_create_native as base


class OperationResultSlotTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_created_changed_and_unchanged_results_commit_and_replay(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        context = assembly.group_context_in_transaction(tx).value
        update = UpdateObject(target=AliasObjectReference(alias='item'),
            set=(AuthoredValue(name='A-value', value=TextValue(kind='string', text='changed')),), unset=())
        original = context.input((self.create(), update, update), MapValue(entries=()))
        request = context.request('slots')
        result = assembly.apply_in_transaction(tx, original, request, documents=self.documents)
        self.assertIsInstance(result, Ok, repr(result)); self.assertIsInstance(result.value, GroupSuccess, repr(result))
        expected = _wire(result.value.response.semantic)
        self.assertEqual([r['outcome'] for r in expected['results']], ['created', 'changed', 'unchanged'])
        host.detach(); connection.commit()
        retained, count, slots = self.admin.execute("""SELECT a.results,a.result_count,
          (SELECT jsonb_agg(p.result ORDER BY p.operation_index) FROM truss.runtime_owned_operation p WHERE p.attempt_id=a.id)
          FROM truss.runtime_object_attempt a WHERE a.complete""").fetchone()
        self.assertEqual(retained, expected['results']); self.assertEqual(slots, retained)
        self.assertEqual(count, 3)
        with self.assertRaises(psycopg.errors.GeneratedAlways):
            self.admin.execute('UPDATE truss.runtime_object_attempt SET result_count=0')
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            self.admin.execute('UPDATE truss.runtime_owned_operation SET result=result')
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            self.admin.execute('DELETE FROM truss.runtime_owned_operation')
        connection, host, assembly, tx = self.consumer()
        replay = assembly.apply_in_transaction(tx, original, request, documents=self.documents)
        self.assertIsInstance(replay, Ok, repr(replay))
        self.assertEqual(replay.value.response.semantic, result.value.response.semantic)
        host.detach(); connection.commit()

    def test_rewritten_slot_refuses_and_preserves_prior_caller_work(self):
        self.refused_seal("NEW.result:='{\"tampered\":true}'::jsonb;")

    def test_late_before_trigger_cannot_rewrite_the_captured_plan(self):
        self.refused_seal("NEW.plan:=NEW.plan||'{\"tampered\":true}'::jsonb;")

    def refused_seal(self, change):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        connection.execute("CREATE TEMP TABLE prior_slot_work(value text);INSERT INTO prior_slot_work VALUES('kept')")
        self.admin.execute("CREATE FUNCTION public.rewrite_operation_result() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN " + change + "RETURN NEW;END $$")
        self.addCleanup(self.admin.execute, 'DROP FUNCTION public.rewrite_operation_result()')
        self.admin.execute('CREATE TRIGGER z_rewrite_result BEFORE UPDATE ON truss.runtime_owned_operation FOR EACH ROW EXECUTE FUNCTION public.rewrite_operation_result()')
        original, request = self.input(assembly, tx)
        result = assembly.apply_in_transaction(tx, original, request, documents=self.documents)
        self.assertIsInstance(result, Error, repr(result)); self.assertEqual(result.error.sql_state, '55000')
        self.assertEqual(connection.execute('TABLE prior_slot_work').fetchall(), [('kept',)])
        host.detach(); connection.commit()
        for table in ('object', 'journal', 'runtime_object_attempt', 'runtime_owned_operation', 'runtime_object_transition'):
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.' + table).fetchone(), (0,), table)
