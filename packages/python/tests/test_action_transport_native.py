# SPDX-License-Identifier: MIT OR Apache-2.0
"""Generated UMF synchronous actions through the public Truss native groups."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import psycopg
import test_group_create_native as base
from truss import (ActionBinding, ActionRefusal, ActionWireError, SchemaBinding,
                   StagedAction, StagedBatch, TrussActionTransport, Ok)
from truss.groups import GroupSuccess
from truss.contracts import MapEntry, MapValue, TextValue
from truss.groups import RequestNone


UMF_ROOT = os.environ.get('TRUSS_UMF_SOURCE_ROOT')
BUN = os.environ.get('TRUSS_BUN_EXECUTABLE') or shutil.which('bun')


def _action_source(source):
    source['vocabularies']['umf.actions'] = {'version': '0.1.0'}
    module = source['modules'][0]
    action = {
        'id': 'create-a', 'name': 'Create A', 'description': 'Create one A record.',
        'parameters': [
            {'id': 'label', 'kind': 'value', 'field': {'module': 'm', 'element': 'A-label'}, 'required': True},
            {'id': 'value', 'kind': 'value', 'field': {'module': 'm', 'element': 'A-value'}, 'required': True},
        ],
        'outputs': [], 'preconditions': [], 'postconditions': [], 'reads': [],
        'writes': [{
            'id': 'create', 'record': {'module': 'm', 'element': 'A'},
            'selector': {'language': 'umf.actions.keys', 'version': '1',
                         'expression': '{"key":"z-alt","components":[{"input":"label"}]}',
                         'references': [{'parameter': 'label'}]},
            'maxEntities': 1, 'fields': [{'module': 'm', 'element': 'A-label'},
                                         {'module': 'm', 'element': 'A-value'}],
            'relationships': [], 'create': True, 'delete': False,
        }],
        'binding': {'kind': 'recipe', 'profile': {'id': 'graph-write', 'version': '2'},
                    'effects': [{'id': 'create-a', 'kind': 'create', 'record': {'module': 'm', 'element': 'A'},
                                 'key': 'z-alt', 'values': [
                                     {'field': {'module': 'm', 'element': 'A-label'}, 'value': {'parameter': 'label'}},
                                     {'field': {'module': 'm', 'element': 'A-value'}, 'value': {'parameter': 'value'}},
                                 ]}]},
        'failures': [],
        'authorization': {'kind': 'roles', 'profile': {'id': 'umf.actions.roles', 'version': '1'}, 'roles': ['group_writer']},
        'attribution': {'subject': 'person-required'}, 'atomicity': 'single-store',
        'idempotency': 'caller-key-optional',
        'result': {'identities': 'created-and-changed', 'version': 'store-opaque', 'receipt': 'read-at-least'},
    }
    module['extensions']['umf.actions'] = {'actions': [action]}
    return source


def _run_generator(root, bun, text, package_dir):
    script = r'''const root = process.env.TRUSS_UMF_SOURCE_ROOT;
const { generatePythonClient } = await import(new URL("src/access/index.ts", `file://${root}/`).href);
const input = JSON.parse(await Bun.stdin.text());
const result = generatePythonClient({text: input.text, package: "generated_actions"});
console.log(JSON.stringify(result));'''
    completed = subprocess.run([bun, '-e', script], cwd=root,
        input=json.dumps({'text': text}), text=True, capture_output=True, timeout=60,
        env={**os.environ, 'TRUSS_UMF_SOURCE_ROOT': str(root)})
    if completed.returncode:
        raise AssertionError('UMF generated client failed: ' + completed.stderr[-2000:])
    generated = json.loads(completed.stdout)
    for file in generated['files']:
        path = package_dir / file['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file['text'])
    return generated['sourceDigest']


class NativeGeneratedActionTransportTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    @unittest.skipUnless(UMF_ROOT and BUN, 'Set TRUSS_UMF_SOURCE_ROOT and install Bun for generated UMF native integration')
    def test_generated_sync_actions_use_owned_native_group_and_exact_receipts(self):
        root = Path(UMF_ROOT).resolve()
        self.assertTrue((root / 'src/access/index.ts').is_file())
        package_parent = Path(tempfile.mkdtemp(prefix='truss-umf-generated-'))
        self.addCleanup(shutil.rmtree, package_parent, True)
        package_dir = package_parent / 'generated_actions'
        sys.path.insert(0, str(package_parent))
        self.addCleanup(lambda: sys.path.remove(str(package_parent)) if str(package_parent) in sys.path else None)
        def remove_generated_modules():
            for name in tuple(sys.modules):
                if name == 'generated_actions' or name.startswith('generated_actions.'):
                    sys.modules.pop(name, None)
        self.addCleanup(remove_generated_modules)

        expected_text = None
        expected_digest = None

        def add_action(source):
            nonlocal expected_text, expected_digest
            source = _action_source(source)
            expected_text = json.dumps(source, indent=2, ensure_ascii=False).encode()
            expected_digest = _run_generator(root, BUN, expected_text.decode(), package_parent)

        connection, host, assembly, tx = self.ready(add_action, document_ids=('adoc',))
        self.assertEqual(expected_digest, hashlib.sha256(expected_text).hexdigest())
        generated = importlib.import_module('generated_actions')
        generated_models = importlib.import_module('generated_actions.models')
        self.assertEqual(generated_models.SOURCE_DIGEST, expected_digest)
        binding_state = {'last_native': None, 'dispatches': 0, 'lease_calls': 0, 'decoded_mutation_seen': False,
                         'observer_calls': 0, 'validation_calls': 0}
        connection_params = psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        connection_params['user'] = 'consumer'

        class Lease:
            def __enter__(self):
                binding_state['lease_calls'] += 1
                self.connection = psycopg.connect(**connection_params, autocommit=True,
                                                  options='-c statement_timeout=10000')
                return self.connection
            def __exit__(self, exc_type, exc, tb):
                self.connection.close()
            def discard(self):
                self.connection.close()

        def lease():
            return Lease()

        def observe(fresh_assembly, fresh_tx):
            binding_state['observer_calls'] += 1
            observed = fresh_assembly.accepted_document_in_transaction(fresh_tx, document_id='adoc')
            self.assertIsInstance(observed, Ok)
            self.assertEqual(observed.value.content, expected_text)
            self.assertEqual(observed.value.sha256, expected_digest)

        def decode(inputs):
            result = dict(inputs)
            # Mutating the detached decode input cannot rewrite the returned typed value.
            inputs['label'] = 'decoder-mutated'
            binding_state['decoded_mutation_seen'] = True
            return result

        def origin_map(request_key, full_request, flags=None):
            original_text = json.dumps(dict(full_request), ensure_ascii=False,
                sort_keys=True, separators=(',', ':'))
            if len(original_text.encode()) > 4000:
                raise ActionRefusal(ActionWireError.UNSUPPORTED, 'Native origin evidence is too large')
            entries = [MapEntry(key='umf.action', value=TextValue(kind='string', text='m.create-a')),
                       MapEntry(key='umf.schema', value=TextValue(kind='string', text=expected_digest)),
                       MapEntry(key='umf.original-request', value=TextValue(kind='string', text=original_text))]
            if request_key is not None:
                entries.append(MapEntry(key='umf.request-key', value=TextValue(kind='string', text=request_key)))
            for name, value in sorted((flags or {}).items()):
                entries.append(MapEntry(key='umf.batch.' + name, value=TextValue(kind='string', text=str(value).lower())))
            return MapValue(entries=tuple(entries))

        def wire_origin(request_key, full_request, flags=None):
            original_text = json.dumps(dict(full_request), ensure_ascii=False,
                sort_keys=True, separators=(',', ':'))
            result = {'umf.action': 'm.create-a', 'umf.schema': expected_digest,
                      'umf.original-request': original_text}
            if request_key is not None:
                result['umf.request-key'] = request_key
            for name, value in sorted((flags or {}).items()):
                result['umf.batch.' + name] = str(value).lower()
            return result

        def perform(fresh_assembly, fresh_tx, values, key, full_request):
            binding_state['dispatches'] += 1
            self.assertEqual(full_request['inputs'], values)
            ctx = fresh_assembly.group_context_in_transaction(fresh_tx)
            self.assertIsInstance(ctx, Ok)
            origin = origin_map(key, full_request)
            operation = self.create(label=values['label'], value=values['value'], alias='created')
            semantic_input = ctx.value.input((operation,), origin)
            request = ctx.value.request(key) if key is not None else RequestNone()
            result = fresh_assembly.apply_in_transaction(fresh_tx, semantic_input, request,
                documents=self.documents, bun_executable=BUN)
            if not isinstance(result, Ok) or not isinstance(result.value, GroupSuccess):
                raise ActionRefusal(ActionWireError.CONFLICT, 'Native group refused')
            native = result.value
            binding_state['last_native'] = native
            created = native.response.semantic.results[0]
            row = fresh_assembly.get_object_in_transaction(fresh_tx, document_id='adoc', module_id='m',
                record_id='A', object_id=int(created.identity.id))
            self.assertIsInstance(row, Ok)
            stored_values = dict(row.value.object.values)
            key_map = {'record': 'm.A', 'key': {'A-label': full_request['inputs']['label'],
                                                 'A-value': full_request['inputs']['value']}}
            self.assertEqual({name: stored_values[name] for name in ('A-label', 'A-value')}, key_map['key'])
            maps = {'created': [key_map], 'changed': []}
            body = {'created': maps['created'], 'changed': maps['changed'],
                    'counts': {'created': 1, 'changed': 0},
                    'consistency_token': native.response.receipt_token}
            digest = hashlib.sha256(json.dumps({'request': dict(full_request), 'asserted_origin': wire_origin(key, full_request)},
                ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            staged = StagedAction(body=body, native_group_success=native, native_key_maps=maps,
                request_digest=digest, request_key=key, asserted_origin=wire_origin(key, full_request))
            return staged

        def execute(fresh_assembly, fresh_tx, values, key, full_request):
            staged = perform(fresh_assembly, fresh_tx, values, key, full_request)
            cancellation = binding_state.pop('cancel_after_execute', None)
            if cancellation is not None:
                raise cancellation
            return staged

        def validate(fresh_assembly, fresh_tx, values, full_request):
            binding_state['validation_calls'] += 1
            binding_state['validation_args'] = (dict(values), dict(full_request))
            if type(values) is not dict or set(values) != {'label', 'value'}:
                return False
            ctx = fresh_assembly.group_context_in_transaction(fresh_tx)
            if not isinstance(ctx, Ok):return False
            semantic_input = ctx.value.input((self.create(label=values['label'], value=values['value'],
                alias='advisory'),), origin_map(None, full_request))
            checked = fresh_assembly.apply_in_transaction(fresh_tx, semantic_input, RequestNone(),
                documents=self.documents, bun_executable=BUN)
            binding_state['advisory_native'] = checked
            return isinstance(checked, Ok) and isinstance(checked.value, GroupSuccess)

        def validate_receipt(body, native):
            return (type(native) is GroupSuccess and len(native.response.semantic.results) == 1
                    and body['consistency_token'] == native.response.receipt_token
                    and body['created'][0]['key']['A-label'] in
                    ('first', 'second', 'late', 'ack-loss'))

        def execute_batch(fresh_assembly, fresh_tx, items, context):
            key = context['request_key']
            flags = dict(context['flags'])
            origin = origin_map(key, context['request'], flags)
            ctx = fresh_assembly.group_context_in_transaction(fresh_tx)
            self.assertIsInstance(ctx, Ok)
            ops = tuple(self.create(label=item['label'], value=item['value'], alias='batch-' + str(index))
                        for index, item in enumerate(items))
            semantic_input = ctx.value.input(ops, origin)
            request = ctx.value.request(key) if key is not None else RequestNone()
            result = fresh_assembly.apply_in_transaction(fresh_tx, semantic_input, request,
                documents=self.documents, bun_executable=BUN)
            if not isinstance(result, Ok) or not isinstance(result.value, GroupSuccess):
                raise ActionRefusal(ActionWireError.CONFLICT, 'Native atomic batch refused')
            native = result.value
            binding_state['last_native'] = native
            receipt_items, maps = [], []
            for created in native.response.semantic.results:
                row = fresh_assembly.get_object_in_transaction(fresh_tx, document_id='adoc', module_id='m',
                    record_id='A', object_id=int(created.identity.id))
                self.assertIsInstance(row, Ok)
                stored_values = dict(row.value.object.values)
                original = context['original_items'][len(receipt_items)]
                key_map = {'record': 'm.A', 'key': {'A-label': original['label'],
                                                     'A-value': original['value']}}
                self.assertEqual({name: stored_values[name] for name in ('A-label', 'A-value')}, key_map['key'])
                key_maps = {'created': [key_map], 'changed': []}
                maps.append(key_maps)
                receipt_items.append({'status': 'applied', 'receipt': {**key_maps, 'counts': {'created': 1, 'changed': 0}}})
            body = {'items': receipt_items, 'consistency_token': native.response.receipt_token}
            canonical = json.dumps({'request': dict(context['request']), 'asserted_origin': wire_origin(key, context['request'], flags)},
                ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
            staged = StagedBatch(body=body, native_group_success=native, native_key_maps=tuple(maps),
                request_digest=hashlib.sha256(canonical).hexdigest(), request_key=key,
                asserted_origin=wire_origin(key, context['request'], flags), flags=flags)
            return staged

        def validate_batch_receipt(body, native):
            binding_state['batch_validator'] = (type(native).__name__, len(body['items']))
            return type(native) is GroupSuccess

        action_binding = ActionBinding(action_id='m.create-a', decode=decode, execute=execute,
            validate=validate, validate_receipt=validate_receipt,
            execute_batch=execute_batch, validate_batch_receipt=validate_batch_receipt)
        def assembly_factory(native_host):
            return __import__('truss').create_reference_assembly(
                __import__('truss').CatalogRuntimeConfiguration(), native_host).value

        transport = TrussActionTransport(connection_factory=lease,
            assembly_factory=assembly_factory,
            schemas={expected_digest: SchemaBinding(schema=expected_digest, observe=observe,
                actions={'m.create-a': action_binding})},
            statement_timeout_ms=10000, operation_timeout_ms=30000)
        client = generated.SyncClient(transport)
        actions = generated.SyncActions(client)

        advisory = actions.create_a_validate(label='first', value='v1')
        self.assertTrue(advisory.valid)
        self.assertIsInstance(binding_state['advisory_native'], Ok)
        self.assertIsInstance(binding_state['advisory_native'].value, GroupSuccess)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (0,))

        single = actions.create_a(label='first', value='v1', idempotency_key='single-1')
        self.assertEqual(single.created[0].a_label, 'first')
        self.assertTrue(binding_state['decoded_mutation_seen'])
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (1,))
        dispatches = binding_state['dispatches']
        replay = actions.create_a(label='first', value='v1', idempotency_key='single-1')
        self.assertEqual(replay.created, single.created)
        self.assertEqual(binding_state['dispatches'], dispatches + 1)
        self.assertEqual(type(binding_state['last_native'].response).__name__, 'CommittedReceiptReplay')
        with self.assertRaises(generated.AccessError) as conflict:
            actions.create_a(label='different', value='v1', idempotency_key='single-1')
        self.assertEqual(conflict.exception.code, 'CONFLICT')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (1,))

        batch = actions.create_a_batch([
            generated.CreateAInput(label='second', value='v2'),
            generated.CreateAInput(label='late', value='v3'),
        ], atomic=True, stop_on_error=True, idempotency_key='batch-1')
        self.assertEqual(tuple(item.status for item in batch.items), ('applied', 'applied'))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (3,))
        self.assertEqual(len(binding_state['last_native'].response.semantic.results), 2)
        self.assertEqual(tuple(item.receipt.created[0].a_label for item in batch.items), ('second', 'late'))

        batch_dispatches = binding_state['observer_calls']
        batch_replay = actions.create_a_batch([
            generated.CreateAInput(label='second', value='v2'),
            generated.CreateAInput(label='late', value='v3'),
        ], atomic=True, stop_on_error=True, idempotency_key='batch-1')
        self.assertEqual(batch_replay, batch)
        self.assertEqual(tuple(item.receipt.created[0].a_label for item in batch_replay.items), ('second', 'late'))
        self.assertEqual(type(binding_state['last_native'].response).__name__, 'CommittedReceiptReplay')
        self.assertEqual(binding_state['observer_calls'], batch_dispatches + 1)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (3,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(), (3,))

        with self.assertRaises(generated.AccessError) as flag_conflict:
            actions.create_a_batch([
                generated.CreateAInput(label='second', value='v2'),
                generated.CreateAInput(label='late', value='v3'),
            ], atomic=True, stop_on_error=False, idempotency_key='batch-1')
        self.assertEqual(flag_conflict.exception.code, 'CONFLICT')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (3,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(), (3,))

        leases_before_unsupported = binding_state['lease_calls']
        with self.assertRaises(generated.AccessError) as unsupported:
            actions.create_a_batch([
                generated.CreateAInput(label='unavailable', value='v0'),
            ], atomic=False, stop_on_error=True, idempotency_key='unsupported-batch')
        self.assertEqual(unsupported.exception.code, 'UNSUPPORTED')
        self.assertEqual(binding_state['lease_calls'], leases_before_unsupported)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (3,))

        with self.assertRaises(generated.AccessError) as late_failure:
            actions.create_a_batch([
                generated.CreateAInput(label='duplicate', value='x'),
                generated.CreateAInput(label='duplicate', value='y'),
            ], atomic=True, stop_on_error=True, idempotency_key='late-failure')
        self.assertEqual(late_failure.exception.code, 'CONFLICT')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (3,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.request_receipt').fetchone(), (2,))

        original_execute = psycopg.Connection.execute
        lost = {'raised': False}

        def commit_and_drop_ack(native_connection, query, *args, **kwargs):
            result = original_execute(native_connection, query, *args, **kwargs)
            if query == 'COMMIT' and not lost['raised']:
                lost['raised'] = True
                raise OSError('injected loss after PostgreSQL committed')
            return result

        with patch.object(psycopg.Connection, 'execute', commit_and_drop_ack):
            with self.assertRaises(generated.WriteOutcomeUnknown) as unknown:
                actions.create_a(label='ack-loss', value='v4', idempotency_key='ack-loss-key')
        self.assertTrue(lost['raised'])
        self.assertEqual(unknown.exception.key, 'ack-loss-key')
        count_after_commit = self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0]
        self.assertEqual(count_after_commit, 4)
        recovered = actions.create_a(label='ack-loss', value='v4', idempotency_key='ack-loss-key')
        self.assertEqual(recovered.created[0].a_label, 'ack-loss')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (4,))

        import asyncio
        cancellation = asyncio.CancelledError('cancellation after native group execution')
        binding_state['cancel_after_execute'] = cancellation
        with self.assertRaises(asyncio.CancelledError) as cancelled:
            actions.create_a(label='cancelled', value='v5', idempotency_key='cancelled-key')
        # The registered handler raises after its actual group call below; the
        # same cancellation object must escape after owner rollback.
        self.assertIs(cancelled.exception, cancellation)
        self.assertEqual(tuple(item.key for item in generated.write_outcomes_unknown(cancelled.exception)),
                         ('cancelled-key',))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (4,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.request_receipt').fetchone(), (3,))
