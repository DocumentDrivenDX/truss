# SPDX-License-Identifier: MIT OR Apache-2.0
"""TN08 public PV1 composition. Requires the authentic enrolled owner binding.

All happy-path values enter through public DTOs/facade operations. No native
cell seed, fabricated owner result, or ordinary-provider fallback is used.
"""
import os

from truss import (Ok, LocalTimestampValue, CatalogRuntimeConfiguration,
                   adopt_psycopg_host, create_reference_assembly, ObjectReadRefused,
                   ObjectReadUnavailable, ObjectNotFound)
from truss import temporal
from truss.contracts import MapValue, NullValue, TextValue
from truss.groups import (RootlessOwnership, StoredObjectReference, GroupSuccess,
                          CommittedReceiptReplay, Delete,GroupFailed)
from truss.preview import GroupValidationObserved
from truss.history import HistoryEntity, HistoryPage, HistoricalRecord
from truss.imports import ImportReported, ImportCreated, ImportSkipped,ImportRejected
import temporal_native_fixture as fixture


class LocalTimestampQueryTests(fixture.TemporalNativeFixture):
    def local_create(self, label, value):
        return temporal.CreateObject(type_definition_pin=self.type_reference.definition_pin,
            ownership=RootlessOwnership(), alias=label,
            values=tuple(temporal.AuthoredValue(name=name, value=cell) for name, cell in (
                ('A-label', TextValue(kind='string', text=label)),
                ('A-value', TextValue(kind='string', text='shared-key')),
                ('A-date', TextValue(kind='date', text='2000-02-29')),
                ('A-instant', TextValue(kind='timestamp', text='2024-01-01T01:00:00.123456+01:00')),
                ('A-payload', TextValue(kind='string', text='ordinary sibling')),
            )) + (() if value is None else (temporal.AuthoredValue(name='A-local', value=value),)))

    def selected_read(self, values, tx, identity):
        result = values.get_object_in_transaction(tx, document_id='adoc', module_id='m',
                                                  record_id='A', object_id=int(identity.id))
        self.assertIsInstance(result, Ok, repr(result))
        self.assertIsInstance(result.value, temporal.ObjectFound, repr(result))
        return result.value.object

    def test_public_temporal_dry_run_failed_updates_and_per_record_import_effects(self):
        """TN08 real public writes: preserve pending state on dry-run/refusal."""
        c,h,a,tx=self.ready_temporal();selected=a.temporal_values()
        local=LocalTimestampValue(text='2000-02-29T12:34:56.000001')
        created,_,_=self.run_group(selected,tx,(self.local_create('dry-run-local',local),),'dry-run-local-create')
        self.assertIsInstance(created,GroupSuccess,repr(created))
        identity=created.response.semantic.results[0].identity
        h.detach();c.commit();c,h,a,tx=self.consumer();selected=a.temporal_values()
        # Fixed read-only observation follows the existing native validation
        # fixture pattern. No raw-table grants or native happy-path seeds.
        self.admin.execute("""CREATE FUNCTION public.temporal_fixture_state() RETURNS jsonb
          LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
          SELECT jsonb_build_object(
            'objects',(SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t.id,t.type_id),'[]') FROM truss.object t),
            'journal',(SELECT coalesce(jsonb_agg(v ORDER BY v::text),'[]') FROM (SELECT to_jsonb(t) v FROM truss.journal t) j),
            'attempts',(SELECT coalesce(jsonb_agg(v ORDER BY v::text),'[]') FROM (SELECT to_jsonb(t) v FROM truss.runtime_object_attempt t) j),
            'transitions',(SELECT coalesce(jsonb_agg(v ORDER BY v::text),'[]') FROM (SELECT to_jsonb(t) v FROM truss.runtime_object_transition t) j),
            'receipts',(SELECT coalesce(jsonb_agg(v ORDER BY v::text),'[]') FROM (SELECT to_jsonb(t) v FROM truss.request_receipt t) j),
            'schema',(SELECT coalesce(jsonb_agg(v ORDER BY v::text),'[]') FROM (SELECT to_jsonb(t) v FROM truss.runtime_type_schema t) j)) $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.temporal_fixture_state()')
        def snapshot():return c.execute('SELECT public.temporal_fixture_state()').fetchone()[0]
        before=snapshot();context=selected.group_context_in_transaction(tx).value
        update=temporal.UpdateObject(target=StoredObjectReference(identity=identity),expected_version='1',unset=(),
            set=(temporal.AuthoredValue(name='A-local',value=LocalTimestampValue(text='2024-01-01T00:00:00.000000')),))
        dry=selected.dry_run_in_transaction(tx,context.input((update,),MapValue(entries=())),documents=self.documents)
        self.assertIsInstance(dry,Ok,repr(dry));self.assertIsInstance(dry.value,GroupValidationObserved,repr(dry))
        self.assertEqual(dry.value.basis.durability,'rolled_back');self.assertEqual(snapshot(),before)
        self.assertEqual(dict(self.selected_read(selected,tx,identity).values)['A-local'],local)
        for name,value in (('A-local',TextValue(kind='timestamp',text='2024-01-01T00:00:00Z')),
                           ('A-date',NullValue()),('A-instant',LocalTimestampValue(text='2000-01-01T00:00:00.000000'))):
            with self.subTest(field=name):
                invalid=temporal.UpdateObject(target=StoredObjectReference(identity=identity),expected_version='1',unset=(),
                    set=(temporal.AuthoredValue(name=name,value=value),))
                failed,_,_=self.run_group(selected,tx,(invalid,))
                self.assertIsInstance(failed,GroupFailed,repr(failed));self.assertEqual(snapshot(),before)
        good=self.local_create('import-valid-per-record',local)
        bad=self.local_create('import-invalid-per-record',TextValue(kind='date',text='2000-02-29'))
        records=[]
        for operation in (good,bad):
            prepared=selected.object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',values=operation.values)
            self.assertIsInstance(prepared,Ok,repr(prepared));records.append(prepared.value)
        context=selected.import_context_in_transaction(tx).value
        imported=selected.import_in_transaction(tx,context.input(tuple(records),load_id='temporal-per-record',
            asserted_origin=MapValue(entries=())),documents=self.documents)
        self.assertIsInstance(imported,ImportReported,repr(imported))
        self.assertEqual(len(imported.report.outcomes),2)
        self.assertIsInstance(imported.report.outcomes[0],ImportCreated)
        self.assertIsInstance(imported.report.outcomes[1],ImportRejected)
        self.assertEqual(dict(self.selected_read(selected,tx,imported.report.outcomes[0].identity).values)['A-local'],local)
        after=snapshot();self.assertEqual(len(after['objects']),len(before['objects'])+1)
        self.assertEqual(self.selected_read(selected,tx,identity).version,1)
        h.detach();c.rollback()

    def test_public_accept_apply_read_all_temporal_families_and_presence(self):
        c, h, a, tx = self.ready_temporal()
        selected = a.temporal_values()
        local = LocalTimestampValue(text='2000-02-29T12:34:56.123456')
        applied, original_input, request = self.run_group(selected, tx, (
            self.local_create('local-value', local), self.local_create('local-null', NullValue()),
            self.local_create('local-absent', None)), 'public-local-presence')
        self.assertIsInstance(applied, GroupSuccess, repr(applied))
        identities = tuple(item.identity for item in applied.response.semantic.results)
        objects = tuple(self.selected_read(selected, tx, identity) for identity in identities)
        self.assertEqual(dict(objects[0].values)['A-local'], local)
        self.assertIsNone(dict(objects[1].values)['A-local'])
        self.assertNotIn('A-local', dict(objects[2].values))
        for obj in objects:
            self.assertEqual(dict(obj.values)['A-date'], TextValue(kind='date', text='2000-02-29'))
            self.assertEqual(dict(obj.values)['A-instant'], TextValue(kind='timestamp', text='2024-01-01T01:00:00.123456+01:00'))
        # Ordinary reads cannot acquire local meaning merely by installing0.76.
        ordinary = a.get_object_in_transaction(tx, document_id='adoc', module_id='m',
                                              record_id='A', object_id=int(identities[0].id))
        self.assertEqual(ordinary, Ok(ObjectReadUnavailable(reason='profile')))
        h.detach(); c.commit()
        rows = self.admin.execute("SELECT p.scalar_type,p.native_temporal,truss.valid_property_definition(p),"
            "truss.valid_property_value(o.props->p.prop_id::text,p),o.props->p.prop_id::text "
            "FROM truss.prop_def p JOIN truss.object o ON o.type_id=p.type_id "
            "WHERE p.element='A-local' AND o.id=ANY(%s) ORDER BY o.id",
            ([int(v.id) for v in identities],)).fetchall()
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row[0]=='localTimestamp' and row[1]['profile']=='truss.local-timestamp/0.1'
                            and row[2] for row in rows))
        self.assertTrue(all(row[3] for row in rows if row[4] is not None))
        c, h, a, tx = self.consumer()
        replay = a.temporal_values().apply_in_transaction(tx, original_input, request, documents=self.documents)
        self.assertIsInstance(replay, Ok, repr(replay))
        self.assertIsInstance(replay.value.response, CommittedReceiptReplay)
        self.assertEqual(replay.value.response.semantic, applied.response.semantic)
        self.assertEqual(self.selected_read(a.temporal_values(), tx, identities[0]).values, objects[0].values)
        h.detach(); c.rollback()

    def test_public_local_crud_import_cache_history_and_readonly(self):
        c, h, a, tx = self.ready_temporal()
        selected = a.temporal_values()
        original = LocalTimestampValue(text='2024-01-01T00:00:00.000001')
        changed = LocalTimestampValue(text='2024-02-29T23:59:59.999999')
        created, _, _ = self.run_group(selected, tx, (self.local_create('local-crud', original),), 'local-crud-create')
        self.assertIsInstance(created, GroupSuccess, repr(created))
        identity = created.response.semantic.results[0].identity
        h.detach(); c.commit()
        c, h, a, tx = self.consumer(); selected = a.temporal_values()
        update = temporal.UpdateObject(target=StoredObjectReference(identity=identity),
            set=(temporal.AuthoredValue(name='A-local', value=changed),), unset=(), expected_version='1')
        updated, update_input, update_request = self.run_group(selected, tx, (update,), 'local-crud-update')
        self.assertIsInstance(updated, GroupSuccess, repr(updated))
        self.assertEqual(dict(self.selected_read(selected, tx, identity).values)['A-local'], changed)
        # The selected path uses the unprepared temporal provider. Warm schema
        # state may never cause an ordinary prepared packet to be relabelled.
        before_cache = dict(a._record_schema_state)
        for _ in range(2):
            self.assertEqual(dict(self.selected_read(selected, tx, identity).values)['A-local'], changed)
        self.assertEqual(dict(a._record_schema_state), before_cache)
        h.detach(); c.commit()
        c, h, a, tx = self.consumer(); selected = a.temporal_values()
        replay = selected.apply_in_transaction(tx, update_input, update_request, documents=self.documents)
        self.assertIsInstance(replay.value.response, CommittedReceiptReplay)
        self.assertEqual(self.selected_read(selected, tx, identity).version, 2)
        unset = temporal.UpdateObject(target=StoredObjectReference(identity=identity), set=(), unset=('A-local',), expected_version='2')
        self.assertIsInstance(self.run_group(selected, tx, (unset,))[0], GroupSuccess)
        self.assertNotIn('A-local', dict(self.selected_read(selected, tx, identity).values))
        h.detach(); c.rollback()
        c, h, a, tx = self.consumer(); selected = a.temporal_values()
        self.assertEqual(dict(self.selected_read(selected, tx, identity).values)['A-local'], changed)
        # Import preserves the same typed local value and original payload;
        # identity replay skips rather than replacing retained source content.
        context = selected.import_context_in_transaction(tx)
        self.assertIsInstance(context, Ok, repr(context))
        record = selected.object_import_record_in_transaction(tx, document_id='adoc', module_id='m', record_id='A',
            values=self.local_create('local-import', original).values)
        self.assertIsInstance(record, Ok, repr(record))
        import_input = context.value.input((record.value,), load_id='local-import', asserted_origin=MapValue(entries=()))
        imported = selected.import_in_transaction(tx, import_input, documents=self.documents,
                                                  bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(imported, ImportReported, repr(imported))
        self.assertIsInstance(imported.report.outcomes[0], ImportCreated)
        imported_identity = imported.report.outcomes[0].identity
        self.assertEqual(dict(self.selected_read(selected, tx, imported_identity).values)['A-local'], original)
        h.detach(); c.commit()
        c, h, a, tx = self.consumer(); selected = a.temporal_values()
        imported = selected.import_in_transaction(tx, import_input, documents=self.documents)
        self.assertIsInstance(imported, ImportReported, repr(imported))
        self.assertIsInstance(imported.report.outcomes[0], ImportSkipped)
        entity = HistoryEntity(kind='object', document_id='adoc', module_id='m', definition_id='A', id=int(identity.id))
        history = selected.page_history_in_transaction(tx, entity=entity)
        self.assertIsInstance(history, Ok, repr(history)); self.assertIsInstance(history.value, HistoryPage)
        payloads = [event.content for event in history.value.events]
        self.assertTrue(any(original.text.encode() in raw for raw in payloads))
        self.assertTrue(any(changed.text.encode() in raw for raw in payloads))
        reconstructed = selected.reconstruct_in_transaction(tx, entity=entity, version=1)
        self.assertIsInstance(reconstructed.value, HistoricalRecord)
        self.assertIn(original.text.encode(), reconstructed.value.record)
        h.detach(); c.commit()
        # A genuine caller-owned read-only transaction can decode local, and
        # permission changes remain live across repeated reads.
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        self.admin.execute('REVOKE group_writer FROM consumer')
        c.execute('BEGIN READ ONLY'); h = adopt_psycopg_host(c)
        self.consumer_connections.append((c,h)); tx = h.adopt_transaction(access_mode='read_only').value
        a = create_reference_assembly(CatalogRuntimeConfiguration(),h).value; selected = a.temporal_values()
        self.assertEqual(dict(self.selected_read(selected,tx,identity).values)['A-local'],changed)
        self.admin.execute('REVOKE group_reader FROM consumer')
        denied = selected.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertEqual(denied, Ok(ObjectReadRefused()))
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        self.assertEqual(dict(self.selected_read(selected,tx,identity).values)['A-local'],changed)
        self.assertEqual(c.execute('SHOW transaction_read_only').fetchone(),('on',))
        h.detach(); c.rollback()
        self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
        c,h,a,tx = self.consumer(); selected = a.temporal_values()
        deletion = Delete(operation='delete_object',target=StoredObjectReference(identity=identity),expected_version='2')
        self.assertIsInstance(self.run_group(selected,tx,(deletion,),'local-delete')[0],GroupSuccess)
        self.assertEqual(selected.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',
                                                           object_id=int(identity.id)),Ok(ObjectNotFound()))
        h.detach(); c.commit()
