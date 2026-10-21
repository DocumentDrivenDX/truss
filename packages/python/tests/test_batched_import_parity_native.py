# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original per-record versus explicit chunked imports on one native cohort."""
from dataclasses import replace
import json
import os
from pathlib import Path
import threading
import time

import psutil
import psycopg

from truss import Ok, ModuleAccessGrant, adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration
from truss.batched_import import ObjectImportDraft, EdgeImportDraft, BatchedImportExecutionResult
from truss.contracts import MapValue, MapEntry, TextValue, TypedIdentity
from truss.groups import Delete, StoredObjectReference, NullOrderKey
from truss.imports import (ImportReported, ImportCreated, ImportSkipped, ImportRejected,
                           ImportConsistencyLimits, check_import_report_consistency)
import test_batched_import_native as batched_tests


class BatchedImportParityNativeTests(batched_tests.BatchedImportTests):
    for _name in tuple(name for name in dir(batched_tests.BatchedImportTests) if name.startswith('test_')):
        locals()[_name] = None

    def enable_second_module_writer(self, assembly):
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin)
        transaction = host.adopt_transaction().value
        admin_assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
        result = admin_assembly.configure_module_access_in_transaction(
            transaction, (ModuleAccessGrant('zdoc', 'm', 'group_reader', 'group_writer'),))
        self.assertIsInstance(result, Ok, repr(result))
        host.detach()
        self.admin.commit()

    def values(self, record, label, value):
        return self.create(label=label, value=value, record=record).values

    def source(self, *, author='parity-test', at='2024-02-03T04:05:06Z', system='truss'):
        return MapValue(entries=(MapEntry(key='author', value=TextValue(kind='string', text=author)),
            MapEntry(key='at', value=TextValue(kind='string', text=at)),
            MapEntry(key='system', value=TextValue(kind='string', text=system))))

    def make_legacy_object(self, assembly, tx, doc, record_id, values, source=None):
        return assembly.object_import_record_in_transaction(transaction=tx, document_id=doc,
            module_id='m', record_id=record_id, values=values, source=source).value

    def make_legacy_edge(self, assembly, tx, doc, endpoints):
        return assembly.edge_import_record_in_transaction(transaction=tx, document_id=doc,
            module_id='m', relationship_id='A-B', source_endpoint=endpoints[0], target_endpoint=endpoints[1],
            values=(), order_key=NullOrderKey()).value

    def measured(self, host, backend_pid, operation):
        process = psutil.Process()
        backend = psutil.Process(backend_pid)
        samples = {'client': [], 'backend': []}
        stop = threading.Event()

        def sample():
            while not stop.is_set():
                for label, selected in (('client', process), ('backend', backend)):
                    try:
                        samples[label].append(selected.memory_info().rss)
                    except (psutil.Error, OSError):
                        pass
                stop.wait(0.01)

        thread = threading.Thread(target=sample, daemon=True)
        started = time.perf_counter()
        thread.start()
        try:
            result = operation()
        finally:
            stop.set()
            thread.join(timeout=2)
        return result, {'seconds': time.perf_counter() - started,
            'clientPeakRssBytes': max(samples['client'], default=None),
            'backendPeakRssBytes': max(samples['backend'], default=None),
            'clientRssSampleCount': len(samples['client']),
            'backendRssSampleCount': len(samples['backend'])}

    def instrument(self, host):
        original = host._cursor
        queries = []

        class Counted:
            def __init__(self, cursor): self.cursor = cursor
            def __getattr__(self, name): return getattr(self.cursor, name)
            def execute(self, query, *args, **kwargs):
                queries.append(str(query))
                return self.cursor.execute(query, *args, **kwargs)

        host._cursor = lambda: Counted(original())
        return queries

    def summarize(self, report):
        rows = []
        for outcome in report.outcomes:
            identity = getattr(outcome, 'identity', None)
            normalized = None
            if type(identity) is TypedIdentity:
                matches=[r.authored_identity for r in self.types.values() if r.type_id==identity.type_id and r.definition_pin==identity.definition_pin]
                normalized=(tuple(matches) or ('relationship',),identity.owner.module_id)
            rows.append((type(outcome).__name__, outcome.input_index,
                         getattr(outcome, 'reason', None), getattr(outcome, 'code', None),
                         getattr(outcome, 'version', None), normalized))
        return tuple(rows)

    def test_legacy_parity_for_source_failures_duplicate_skip_mixed_edges_and_reserved_identity(self):
        connection, host, assembly, tx = self.ready()
        self.enable_second_module_writer(assembly)
        created, _, _ = self.run_group(assembly, tx, (
            self.create(document='adoc', record='A', label='endpoint-a', value='endpoint-a', alias='a'),
            self.create(document='adoc', record='B', label='endpoint-b', value='endpoint-b', alias='b'),
            self.create(document='zdoc', record='A', label='endpoint-a', value='endpoint-a', alias='za'),
            self.create(document='zdoc', record='B', label='endpoint-b', value='endpoint-b', alias='zb')))
        self.assertEqual(created.outcome, 'success', repr(created))
        endpoints = {
            'adoc': (created.response.semantic.results[0].identity,
                     created.response.semantic.results[1].identity),
            'zdoc': (created.response.semantic.results[2].identity,
                     created.response.semantic.results[3].identity),
        }
        host.detach(); connection.commit()
        connection, host, assembly, tx = self.consumer()
        legacy_context = assembly.import_context_in_transaction(tx).value
        batched_context = assembly.batched_import_context_in_transaction(tx).value
        origin = MapValue(entries=(MapEntry(key='x-initiated-by', value=TextValue(kind='string', text='parity')),))

        route_records = {}
        for doc in ('adoc', 'zdoc'):
            valid_values = self.values('A', doc+'-shared', doc+'-duplicate-key')
            source = self.source()
            first = self.make_legacy_object(assembly, tx, doc, 'A', valid_values, source)
            duplicate = replace(first, payload=self.artifact(b'invalid replacement bytes'))
            bad_time = self.make_legacy_object(assembly, tx, doc, 'A',
                self.values('A', doc+'-bad-time', doc+'-bad-time-key'),self.source())
            bad_time=replace(bad_time,payload=legacy_context.object_payload(()))
            mismatch_identity = self.make_legacy_object(assembly, tx, doc, 'A',
                self.values('A', doc+'-identity', doc+'-identity-key'))
            mismatch_payload = legacy_context.object_payload(
                self.values('A', doc+'-payload', doc+'-different-primary-key'))
            mismatch = replace(mismatch_identity, payload=mismatch_payload)
            second = self.make_legacy_object(assembly, tx, doc, 'B',
                self.values('B', doc+'-second', doc+'-second-key'), self.source(author='second'))
            edge = self.make_legacy_edge(assembly, tx, doc, endpoints[doc])
            route_records[doc] = (first, duplicate, bad_time, mismatch, second, edge)

        legacy_input = legacy_context.input(route_records['adoc'], load_id='parity-legacy', asserted_origin=origin)
        legacy_result = assembly.import_in_transaction(tx, legacy_input, documents=self.documents,
            bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(legacy_result, ImportReported, repr(legacy_result))

        drafts = (
            ObjectImportDraft(document_id='zdoc', module_id='m', record_id='A',
                values=self.values('A', 'zdoc-shared', 'zdoc-duplicate-key'), source=self.source()),
            ObjectImportDraft(document_id='zdoc', module_id='m', record_id='A',
                values=self.values('A', 'zdoc-bad-time', 'zdoc-bad-time-key'),
                source=self.source()),
            ObjectImportDraft(document_id='zdoc', module_id='m', record_id='A',
                values=self.values('A', 'zdoc-identity', 'zdoc-identity-key')),
            ObjectImportDraft(document_id='zdoc', module_id='m', record_id='B',
                values=self.values('B', 'zdoc-second', 'zdoc-second-key'), source=self.source(author='second')),
            EdgeImportDraft(document_id='zdoc', module_id='m', relationship_id='A-B',
                source_endpoint=endpoints['zdoc'][0], target_endpoint=endpoints['zdoc'][1], values=(),
                order_key=NullOrderKey()),
        )
        built = assembly.build_import_records_in_transaction(tx, drafts)
        self.assertIsInstance(built, Ok, repr(built))
        batch_records = list(built.value.records)
        batch_records[1]=replace(batch_records[1],payload=built.value.context.object_payload(()))
        batch_records.insert(1, replace(batch_records[0], payload=self.artifact(b'invalid replacement bytes')))
        batch_records[3] = replace(batch_records[3], payload=built.value.context.object_payload(
            self.values('A', 'zdoc-payload', 'zdoc-different-primary-key')))
        batch_input = built.value.context.input(tuple(batch_records), load_id='parity-batch',
            asserted_origin=origin, chunk_size=3)
        batch_result = assembly.import_batched_in_transaction(tx, batch_input, documents=self.documents)
        self.assertIsInstance(batch_result, BatchedImportExecutionResult, repr(batch_result))
        self.assertIsInstance(batch_result.result, ImportReported, repr(batch_result))

        legacy_report = legacy_result.report
        batch_report = batch_result.result.report
        self.assertEqual(self.summarize(legacy_report), self.summarize(batch_report))
        self.assertEqual([type(item) for item in legacy_report.outcomes],
            [ImportCreated, ImportSkipped, ImportRejected, ImportRejected, ImportCreated, ImportCreated])
        self.assertEqual([item.code for item in legacy_report.outcomes if type(item) is ImportRejected],
            ['invalid_payload', 'invalid_payload'])
        for report in (legacy_report, batch_report):
            self.assertEqual(check_import_report_consistency(report, expected_input_count='6',
                limits=ImportConsistencyLimits(maximum_records=1024, maximum_decimal_digits=20,
                    maximum_text_units=1048576)).result, 'consistent')

        legacy_created = [item for item in legacy_report.outcomes if type(item) is ImportCreated]
        batch_created = [item for item in batch_report.outcomes if type(item) is ImportCreated]
        host.detach(); connection.commit()
        for created_item in legacy_created:
            kind = 'e' if created_item.input_index=='5' else 'o'
            row = self.admin.execute('SELECT load_id,source FROM truss.record_source WHERE entity_kind=%s AND entity_id=%s',
                (kind, int(created_item.identity.id))).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'parity-legacy')
        for created_item in batch_created:
            kind = 'e' if created_item.input_index=='5' else 'o'
            row = self.admin.execute('SELECT load_id,source FROM truss.record_source WHERE entity_kind=%s AND entity_id=%s',
                (kind, int(created_item.identity.id))).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'parity-batch')

        connection, host, assembly, tx = self.consumer()
        for doc, index in (('adoc', 0), ('zdoc', 0)):
            created_item = legacy_created[0] if doc == 'adoc' else batch_created[0]
            deletion = Delete(operation='delete_object', target=StoredObjectReference(identity=created_item.identity))
            deleted, _, _ = self.run_group(assembly, tx, (deletion,), 'reserve-'+doc)
            self.assertEqual(deleted.outcome, 'success', repr(deleted))
            input_value = legacy_context.input((route_records[doc][0],), load_id='reserved-'+doc, asserted_origin=origin) if doc == 'adoc' else built.value.context.input((batch_records[0],), load_id='reserved-'+doc, asserted_origin=origin)
            outcome = assembly.import_in_transaction(tx, input_value, documents=self.documents,
                bun_executable='/opt/homebrew/bin/bun') if doc == 'adoc' else assembly.import_batched_in_transaction(tx, input_value, documents=self.documents).result
            self.assertEqual(outcome.report.outcomes[0].reason, 'reserved_identity')
        host.detach(); connection.rollback()

    def test_legacy_vs_chunked_statement_time_and_rss_samples(self):
        connection, host, assembly, tx = self.ready()
        self.enable_second_module_writer(assembly)
        queries = self.instrument(host)
        backend_pid = connection.info.backend_pid
        measurements = []
        for trial,count in ((trial,count) for trial in range(3) for count in (32,64,128)):
            values = tuple(self.values('A', f'legacy-{trial}-{count}-{i}', f'legacy-key-{trial}-{count}-{i}')
                           for i in range(count))
            queries.clear()
            legacy_ctx = assembly.import_context_in_transaction(tx).value
            queries.clear()
            legacy_records, legacy_build_stats = self.measured(host, backend_pid, lambda: tuple(
                assembly.object_import_record_in_transaction(tx, document_id='adoc', module_id='m',
                    record_id='A', values=item).value for item in values))
            legacy_builder_statements = len(queries)
            queries.clear()
            legacy_input = legacy_ctx.input(legacy_records, load_id=f'legacy-{count}',
                asserted_origin=MapValue(entries=()))
            legacy_executed, legacy_execute_stats = self.measured(host, backend_pid, lambda:
                assembly.import_in_transaction(tx, legacy_input, documents=self.documents,
                    bun_executable='/opt/homebrew/bin/bun'))
            self.assertIsInstance(legacy_executed, ImportReported, repr(legacy_executed))
            legacy_execute_statements = len(queries)

            drafts = tuple(ObjectImportDraft(document_id='zdoc', module_id='m', record_id='A', values=item)
                           for item in values)
            queries.clear()
            built, batch_build_stats = self.measured(host, backend_pid, lambda:
                assembly.build_import_records_in_transaction(tx, drafts))
            self.assertIsInstance(built, Ok, repr(built))
            batch_builder_statements = len(queries)
            batch_input = built.value.context.input(built.value.records, load_id=f'batch-{count}',
                asserted_origin=MapValue(entries=()), chunk_size=128)
            queries.clear()
            batched, batch_execute_stats = self.measured(host, backend_pid, lambda:
                assembly.import_batched_in_transaction(tx, batch_input, documents=self.documents))
            self.assertIsInstance(batched, BatchedImportExecutionResult, repr(batched))
            self.assertIsInstance(batched.result, ImportReported, repr(batched))
            batch_execute_statements = len(queries)
            self.assertEqual(self.summarize(legacy_executed.report), self.summarize(batched.result.report))
            measurements.append({'records': count,'trial':trial,
                'legacy': {'builderStatements': legacy_builder_statements,
                           'executeStatements': legacy_execute_statements,
                           'builder': legacy_build_stats, 'execute': legacy_execute_stats},
                'batched': {'builderStatements': batch_builder_statements,
                            'executeStatements': batch_execute_statements,
                            'builder': batch_build_stats, 'execute': batch_execute_stats}})

        count = 1024
        drafts = tuple(ObjectImportDraft(document_id='zdoc', module_id='m', record_id='A',
            values=self.values('A', f'batch-1024-{i}', f'batch-1024-key-{i}')) for i in range(count))
        queries.clear()
        built, batch_build_stats = self.measured(host, backend_pid, lambda:
            assembly.build_import_records_in_transaction(tx, drafts))
        self.assertIsInstance(built, Ok, repr(built))
        builder_statements = len(queries)
        batch_input = built.value.context.input(built.value.records, load_id='batch-1024',
            asserted_origin=MapValue(entries=()), chunk_size=128)
        queries.clear()
        batched, execute_stats = self.measured(host, backend_pid, lambda:
            assembly.import_batched_in_transaction(tx, batch_input, documents=self.documents))
        self.assertIsInstance(batched, BatchedImportExecutionResult, repr(batched))
        self.assertIsInstance(batched.result, ImportReported, repr(batched))
        self.assertEqual(batched.result.report.counts.created_pending, '1024')
        measurements.append({'records': 1024, 'legacy': None,
            'batched': {'builderStatements': builder_statements,
                        'executeStatements': len(queries), 'builder': batch_build_stats,
                        'execute': execute_stats}})
        print('E2_NATIVE_PARITY_PERF='+json.dumps(measurements, sort_keys=True))
        if os.environ.get('TRUSS_BATCH_PARITY_MEASUREMENT'):
            Path(os.environ['TRUSS_BATCH_PARITY_MEASUREMENT']).write_text(json.dumps(measurements,indent=2)+'\n')
        host.detach(); connection.rollback()


if __name__ == '__main__':
    import unittest
    unittest.main()
