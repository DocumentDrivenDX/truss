# SPDX-License-Identifier: MIT OR Apache-2.0
"""Buffered independent creates preserve the general planner and final rules."""
import base64
import json

from truss import Ok
from truss.contracts import MapValue
from truss.groups import GroupFailed, GroupSuccess, RequestNone
import test_group_create_native as base


class RootlessPreparationTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_singleton_and_batch_plans_equal_the_general_path(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        # Run the retained general branch as a test-only reference, under the
        # same original caller and catalog, before any canonical object effects.
        # The two-argument entrypoint delegates to the application-aware planner.
        # Clone the implementation so this remains a differential behavior check
        # after that delegation, rather than asserting the wrapper's source text.
        definition = self.admin.execute("SELECT pg_get_functiondef('truss.runtime_owned_prepare_application(jsonb,jsonb,jsonb)'::regprocedure)").fetchone()[0]
        self.assertEqual(definition.count('rootless_creates:=coalesce('), 1)
        reference = definition.replace('truss.runtime_owned_prepare_application(', 'public.reference_rootless_prepare(', 1)
        reference = reference.replace('rootless_creates:=coalesce(', 'rootless_creates:=false AND coalesce(', 1)
        self.admin.execute(reference)
        self.addCleanup(self.admin.execute, 'DROP FUNCTION public.reference_rootless_prepare(jsonb,jsonb,jsonb)')
        self.admin.execute("""CREATE FUNCTION public.compare_rootless_plans() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE original_input jsonb; scope jsonb;
        BEGIN
          IF NEW.operation_index=0 THEN
            SELECT convert_from(input_bytes,'UTF8')::jsonb INTO STRICT original_input
              FROM truss.runtime_object_attempt WHERE id=NEW.attempt_id;
            scope:=NEW.plan->'initialScope';
            IF truss.runtime_owned_prepare(original_input,scope) IS DISTINCT FROM
               public.reference_rootless_prepare(original_input,scope,NULL) THEN
              RAISE EXCEPTION 'buffered and general preparation differ' USING ERRCODE='P9998';
            END IF;
          END IF;
          RETURN NEW;
        END $$""")
        self.addCleanup(self.admin.execute, 'DROP FUNCTION public.compare_rootless_plans()')
        self.admin.execute('CREATE TRIGGER compare_rootless_plans BEFORE INSERT ON truss.runtime_owned_operation FOR EACH ROW EXECUTE FUNCTION public.compare_rootless_plans()')
        for count in (1, 9):
            context = assembly.group_context_in_transaction(tx).value
            operations = tuple(self.create(label=f'{count}-{index}', record='A' if index % 2 == 0 else 'B', alias=f'item-{index}') for index in range(count))
            result = assembly.apply_in_transaction(tx, context.input(operations, MapValue(entries=())), RequestNone(), documents=self.documents)
            self.assertIsInstance(result, Ok, repr(result))
            self.assertIsInstance(result.value, GroupSuccess, repr(result))
            self.assertEqual(len(result.value.response.semantic.results), count)
        host.detach(); connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (10,))

    def test_empty_edges_still_refuse_required_relationships(self):
        def require_edge(source):
            source['modules'][0]['relationships'][0]['targetMultiplicity']['min'] = 1
        connection, host, assembly, tx = self.ready(require_edge, document_ids=('adoc',))
        context = assembly.group_context_in_transaction(tx).value
        result = assembly.apply_in_transaction(tx, context.input((self.create(),), MapValue(entries=())), RequestNone(), documents=self.documents)
        self.assertIsInstance(result, Ok, repr(result))
        self.assertIsInstance(result.value, GroupFailed, repr(result))
        self.assertEqual(json.loads(base64.b64decode(result.value.failure.inner_error.bytes_base64))['nativeState'], 'P1405')
        host.detach(); connection.commit()
        for table in ('object', 'edge', 'journal', 'runtime_object_attempt', 'runtime_owned_operation'):
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.' + table).fetchone(), (0,), table)
