"""Contract carriers do not assert native support or issue authority."""
import unittest
import json
from pathlib import Path
from dataclasses import FrozenInstanceError, replace
from truss.contracts import *
from truss.groups import *
from truss.execution import ExecutionFailure, TransactionHandle
from truss._host_contracts import TransactionHandle as PrivateHandle

class PublicContractTests(unittest.TestCase):
    def setUp(self):
        self.pin = ProfilePin(identity='fixture', version='1', sha256='unverified')
        self.artifact = ExactArtifact(identity='fixture', bytes_base64='unverified', sha256='unverified')
        self.identity = TypedIdentity(id='9007199254740993', type_id='type', definition_pin='pin', owner=QualifiedOwner(document_id='doc-a', module_id='shared'))
        self.event = JournalEventReference(source_epoch='epoch', history_profile='history', xid='9007199254740993', seq='1')
        self.unchanged = Unchanged(operation='update_object', identity=self.identity, version='1')
        self.semantic = GroupSemanticResult(executed_catalog_revision='1', layout_profile=self.pin, mutation_profile=self.pin, results=(self.unchanged,), aliases=())

    def test_exact_values_keep_spelling_order_and_presence(self):
        decimal = TextValue(kind='decimal', text='9007199254740993.00000000000000001')
        values = (NullValue(), BooleanValue(value=False), decimal,
                  TextValue(kind='integer', text='9007199254740993'), TextValue(kind='string', text=''),
                  TextValue(kind='binary', text='AA=='), TextValue(kind='timestamp', text='2026-10-10T00:00:00Z'),
                  OpaqueValue(format='future', source_text=' { "x": 1 } ', sha256='unverified'))
        sequence = SequenceValue(items=values)
        mapping = MapValue(entries=(MapEntry(key='b', value=sequence), MapEntry(key='a', value=NullValue())))
        record = RecordValue(definition_pin='pin', fields=(RecordField(field_id='field', value=mapping),))
        self.assertIs(record.fields[0].value.entries[0].value, sequence)
        self.assertEqual(sequence.items[2].text, decimal.text)
        self.assertNotEqual(AbsentPresence(), PresentValue(value=NullValue()))
        self.assertIs(RequestIdentity(authorized_scope_identity='s', request_id='k').claimed_sha256, ABSENT)
        self.assertNotEqual(self.identity.owner, replace(self.identity.owner, document_id='doc-b'))
        with self.assertRaises(FrozenInstanceError): decimal.text = 'rounded'

    def test_invalid_shapes_do_not_coerce(self):
        factories = [lambda: BooleanValue(value=1), lambda: TextValue(kind='decimal', text=0.1),
                     lambda: SequenceValue(items=[]), lambda: RequestIdentity(authorized_scope_identity='s', request_id='k', claimed_sha256=None),
                     lambda: replace(self.semantic, results=()),
                     lambda: Created(operation='create_object', identity=self.identity, version='1', events=())]
        for factory in factories:
            with self.subTest(factory=factory), self.assertRaises(ValueError): factory()

    def test_request_free_refuses_receipt_replay_and_conflict(self):
        pending = SameTransactionReplay(semantic=self.semantic, replay=SameTransactionReplayEvidence(observation_profile=self.pin, evidence=self.artifact))
        committed = CommittedReceiptReplay(semantic=self.semantic, replay=CommittedReceiptReplayEvidence(observation_profile=self.pin, evidence=self.artifact))
        self.assertEqual((pending.durability, pending.replay.basis), ('pending', 'same_transaction'))
        self.assertEqual((committed.durability, committed.replay.basis), ('committed', 'committed_receipt'))
        request = RequestPresent(identity=RequestIdentity(authorized_scope_identity='s', request_id='k'))
        excluded = (GroupSuccess(response=pending), GroupSuccess(response=committed),
                    GroupFailed(failure=RequestConflict(diagnostic_profile=self.pin, diagnostic=self.artifact)),
                    GroupUnavailable(reason='receipt'), GroupUnavailable(reason='receipt_expired'))
        for result in excluded:
            validate_request_result(request, result)
            with self.assertRaises(ValueError): validate_request_result(RequestNone(), result)
        validate_request_result(RequestNone(), GroupSuccess(response=AppliedPending(semantic=self.semantic)))
        self.assertEqual(self.semantic.results[0].events, ())
        with self.assertRaises(ValueError): GroupSuccess(response=AppliedCommitted(semantic=self.semantic))

    def test_handle_nominality_and_readonly_description(self):
        self.assertIs(TransactionHandle, PrivateHandle)
        handle = TransactionHandle(object(), 'unregistered', 'read_committed', 'read_only')
        for name, value in [('ownership', 'engine'), ('isolation', 'serializable'), ('access_mode', 'read_write')]:
            with self.assertRaises(AttributeError): setattr(handle, name, value)
        self.assertEqual(handle.ownership, 'caller')

    def test_retry_scope_correlations_are_runtime_validated(self):
        for code, scope in [('retry', 'none'), ('commit_unknown', 'whole_transaction'), ('cancelled', 'qualified_request_lookup')]:
            with self.assertRaises(ValueError): ExecutionFailure(code, 'fixture', scope)
        self.assertEqual(ExecutionFailure('retry', 'fixture', 'whole_transaction').retry_scope, 'whole_transaction')
        self.assertEqual(ExecutionFailure('commit_unknown', 'fixture', 'qualified_request_lookup').code, 'commit_unknown')

    def test_language_neutral_exact_value_vectors(self):
        fixture = Path(__file__).resolve().parents[3] / 'docs/helix/03-test/fixtures/python-group-contract-values.json'
        vectors = json.loads(fixture.read_text())
        for data in vectors['positive']:
            with self.subTest(data=data):
                self.assertEqual(TextValue(**data).text, data['text'])
        for data in vectors['negative']:
            with self.subTest(data=data), self.assertRaises(ValueError): TextValue(**data)
