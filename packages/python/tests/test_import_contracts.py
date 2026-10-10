"""Local report accounting; fixtures are not native import evidence."""
import unittest
from dataclasses import fields, replace
from truss.contracts import *
from truss.imports import *
from truss.execution import ExecutionFailure

class ImportContractTests(unittest.TestCase):
    def setUp(self):
        self.pin = ProfilePin(identity='fixture', version='1', sha256='unverified')
        self.artifact = ExactArtifact(identity='payload', bytes_base64='opaque deferred input', sha256='unverified')
        self.identity = TypedIdentity(id='9007199254740993', type_id='t', definition_pin='pin', owner=QualifiedOwner(document_id='d', module_id='m'))
        self.config = SelectedMutationConfiguration(source_epoch='e', installation_id='i', generation='1', key_reuse='forbid', journal_mode='trigger', configuration_profile=self.pin, installed_producer_inventory_sha256='unverified')
        self.limits = ImportConsistencyLimits(maximum_records=16, maximum_decimal_digits=20, maximum_text_units=8192)
        self.outcome = ImportCreated(input_index='0', batch_id='b', identity=self.identity, version='1')
        self.batch = PendingBatch(batch_id='b', input_indices=('0',), host_transaction_id='host')
        self.report = self.make_report()

    def counts(self, **values):
        return ImportCounts(**{m.name: str(values.get(m.name, 0)) for m in fields(ImportCounts)})

    def make_report(self, **changes):
        base = dict(attempt_id='attempt', input_count='1', executed_catalog_revision='1', import_profile=self.pin, selected_configuration=self.config, input_sha256='unverified', execution='host_adopted', status='processed', outcomes=(self.outcome,), batches=(self.batch,), unprocessed_indices=(), counts=self.counts(created_pending=1))
        base.update(changes)
        return ImportReport(**base)

    def check(self, report, expected='1', limits=None):
        return check_import_report_consistency(report, expected_input_count=expected, limits=limits or self.limits).result

    def test_complete_creation_counts_for_every_batch_disposition(self):
        batches = [self.batch,
                   CommittedBatch(batch_id='b', input_indices=('0',), commit_evidence_sha256='unverified'),
                   RolledBackBatch(batch_id='b', input_indices=('0',), rollback_evidence_sha256='unverified'),
                   CommitUnknownBatch(batch_id='b', input_indices=('0',), recovery_reference='recovery'),
                   TransactionUnresolvedBatch(batch_id='b', input_indices=('0',), recovery_reference='recovery')]
        for batch in batches:
            with self.subTest(disposition=batch.disposition):
                execution = 'host_adopted' if batch.disposition == 'pending' else 'engine_owned'
                report = self.make_report(execution=execution, batches=(batch,), counts=self.counts(**{'created_'+batch.disposition:1}))
                self.assertEqual(self.check(report), 'consistent')
                self.assertIs(report.batches[0], batch)

    def test_all_record_outcomes_and_original_order(self):
        outcomes = (self.outcome, ImportSkipped(input_index='1', batch_id='b', reason='reserved_identity'),
                    ImportRejected(input_index='2', batch_id='b', code='invalid', path='source'),
                    ImportAttemptUnknown(input_index='3', batch_id='b', recovery_reference='recovery'))
        report = self.make_report(input_count='5', status='interrupted', outcomes=outcomes,
                    batches=(replace(self.batch, input_indices=('0','1','2','3')),), unprocessed_indices=('4',),
                    counts=self.counts(created_pending=1, skipped=1, rejected=1, attempt_unknown=1, unprocessed=1))
        self.assertEqual(self.check(report, '5'), 'consistent')
        self.assertIs(report.outcomes[1].identity, ABSENT)
        self.assertEqual(self.check(replace(report, outcomes=tuple(reversed(outcomes))), '5'), 'invalid')
        self.assertEqual(self.check(replace(report, status='processed'), '5'), 'invalid')
        self.assertEqual(self.check(replace(report, counts=self.counts(created_pending=5)), '5'), 'invalid')

    def test_duplicate_overlap_missing_and_swapped_batch_membership(self):
        controls = [replace(self.report, outcomes=(self.outcome,self.outcome)),
                    replace(self.report, outcomes=()),
                    replace(self.report, unprocessed_indices=('0',)),
                    replace(self.report, batches=(self.batch,self.batch)),
                    replace(self.report, batches=(replace(self.batch, input_indices=('0','0')),)),
                    replace(self.report, batches=(replace(self.batch, batch_id='other'),)),
                    replace(self.report, batches=()), replace(self.report, counts=self.counts(created_pending=99))]
        for report in controls:
            with self.subTest(report=report): self.assertEqual(self.check(report), 'invalid')

    def test_execution_ownership_is_not_inferred_from_shape(self):
        self.assertEqual(self.check(replace(self.report, execution='engine_owned')), 'invalid')
        for execution in ('host_adopted','outer_engine_scope'):
            for batch in (CommittedBatch(batch_id='b', input_indices=('0',), commit_evidence_sha256='fixture'), CommitUnknownBatch(batch_id='b', input_indices=('0',), recovery_reference='ref')):
                self.assertEqual(self.check(self.make_report(execution=execution, batches=(batch,))), 'invalid')
        self.assertEqual(self.check(replace(self.report, execution='outer_engine_scope')), 'consistent')

    def test_canonical_exact_counts_and_indices(self):
        for text in ('01','-1','1.0','١',''):
            self.assertEqual(self.check(replace(self.report, input_count=text)), 'invalid')
        self.assertEqual(self.check(self.report, '2'), 'invalid')
        for text in ('00','-1','١','1'):
            self.assertEqual(self.check(replace(self.report, outcomes=(replace(self.outcome,input_index=text),))), 'invalid')

    def test_empty_input_is_consistent_without_invented_inventory(self):
        empty = self.make_report(input_count='0', outcomes=(), batches=(), counts=self.counts())
        self.assertEqual(self.check(empty, '0'), 'consistent')
        self.assertEqual(self.check(empty, '0', replace(self.limits, maximum_records=0)), 'consistent')
        with self.assertRaises(ValueError): PendingBatch(batch_id='b', input_indices=(), host_transaction_id='host')

    def test_reduced_limits_refuse_before_hash_or_decimal_work(self):
        self.assertEqual(self.check(self.report, limits=replace(self.limits, maximum_records=0)), 'resource')
        self.assertEqual(self.check(self.report, limits=replace(self.limits, maximum_text_units=1)), 'resource')
        text_units = 0
        stack = [self.report, '1']
        while stack:
            item=stack.pop()
            if type(item) is str: text_units += len(item)
            elif type(item) is tuple: stack.extend(item)
            elif hasattr(item, '__dataclass_fields__'): stack.extend(getattr(item,m.name) for m in fields(item))
        self.assertEqual(self.check(self.report, limits=replace(self.limits, maximum_text_units=text_units)), 'consistent')
        self.assertEqual(self.check(self.report, limits=replace(self.limits, maximum_text_units=text_units-1)), 'resource')
        for changes in ({'maximum_records':True},{'maximum_decimal_digits':0},{'maximum_records':4097}):
            with self.assertRaises(ValueError): replace(self.limits, **changes)

    def test_execution_results_preserve_progress_and_family(self):
        error=ExecutionFailure('commit_unknown','fixture','qualified_request_lookup')
        failed=ImportExecutionFailed(error=error, report=self.report)
        self.assertIs(failed.report, self.report)
        self.assertIs(failed.error, error)
        self.assertEqual(check_import_execution_shape(failed, expected_execution='host_adopted').result, 'consistent')
        self.assertEqual(check_import_execution_shape(failed, expected_execution='engine_owned').result, 'invalid')
        self.assertIsNone(ImportExecutionFailed(error=error, report=None).report)
        invalid=ImportInvalid(diagnostic_profile=self.pin, diagnostic=self.artifact)
        self.assertFalse(hasattr(invalid,'report'))
        interrupted=replace(self.report,status='interrupted')
        limited=ImportResourceLimited(reason='report_bytes', resource_profile=self.pin, report=interrupted)
        self.assertIs(limited.report,interrupted)
        with self.assertRaises(ValueError): ImportResourceLimited(reason='report_bytes',resource_profile=self.pin,report=self.report)
        unknown=ImportAttemptUnknown(input_index='0', batch_id='b', recovery_reference='ref')
        with self.assertRaises(ValueError): ImportResourceLimited(reason='report_bytes',resource_profile=self.pin,report=replace(interrupted,outcomes=(unknown,)))
        batch=TransactionUnresolvedBatch(batch_id='b',input_indices=('0',),recovery_reference='ref')
        with self.assertRaises(ValueError): ImportResourceLimited(reason='report_bytes',resource_profile=self.pin,report=replace(interrupted,batches=(batch,)))

    def test_payload_stays_opaque_and_document_qualified(self):
        key=ObjectKeySelection(type=ReadTypeReference(type_id='t',definition_pin='p',owner=self.identity.owner),key_number='1',key_definition_pin='k',key_encoding_profile=self.pin,components=(ObjectKeyComponent(property_id='p',definition_pin='p',value=TextValue(kind='integer',text='9007199254740993')),))
        record=ObjectImportRecord(identity=key,payload=self.artifact,payload_profile=self.pin)
        input=ImportInput(layout_profile=self.pin,import_profile=self.pin,value_profile=self.pin,catalog=ImportCatalogPin(revision='1',model_bundle_sha256='unverified'),load_id='load',asserted_origin=NullValue(),records=(record,))
        self.assertIs(input.records[0].payload,self.artifact)
        self.assertFalse(hasattr(input.catalog,'state'))
        self.assertEqual(record.identity.type.owner.document_id,'d')
        with self.assertRaises(ValueError): replace(key,components=())

    def test_multiple_batches_and_unprocessed_partition(self):
        second = replace(self.outcome, input_index='1', batch_id='second')
        batches = (self.batch, replace(self.batch, batch_id='second', input_indices=('1',)))
        report = self.make_report(input_count='3',status='interrupted',outcomes=(self.outcome,second),batches=batches,unprocessed_indices=('2',),counts=self.counts(created_pending=2,unprocessed=1))
        self.assertEqual(self.check(report,'3'),'consistent')
        swapped = (replace(self.batch,input_indices=('1',)),replace(batches[1],input_indices=('0',)))
        self.assertEqual(self.check(replace(report,batches=swapped),'3'),'invalid')
        self.assertEqual(self.check(replace(report,unprocessed_indices=('2','2')),'3'),'invalid')
        self.assertEqual(self.check(replace(report,unprocessed_indices=('1',)),'3'),'invalid')
        self.assertEqual(self.check(replace(report,batches=(self.batch,replace(batches[1],input_indices=('0','1')))),'3'),'invalid')

    def test_primitive_arguments_refuse_before_traversal_or_comparison(self):
        class Trap:
            def __eq__(self, other): raise AssertionError('Compared foreign value')
        for value in (Trap(), (('1',),), None, 1):
            self.assertEqual(self.check(self.report, value), 'invalid')
            self.assertEqual(check_import_execution_shape(ImportReported(report=self.report), expected_execution=value).result, 'invalid')
        self.assertEqual(self.check(self.report, '9'*21), 'resource')
        report=self.make_report(input_count='10',status='interrupted',outcomes=(),batches=(),unprocessed_indices=tuple(str(i) for i in range(10)),counts=self.counts(unprocessed=10))
        self.assertEqual(self.check(report,'10'),'consistent')
        self.assertEqual(self.check(report,'10',replace(self.limits,maximum_decimal_digits=1)),'resource')
