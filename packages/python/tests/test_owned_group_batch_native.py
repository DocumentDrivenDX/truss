"""Basic public multi-object create/update/commit/read workflow."""
from truss import Ok, ObjectFound, HistoryEntity, HistoricalRecord, HistoricalDeleted
from truss.contracts import ABSENT, MapValue, TextValue
from truss.groups import AuthoredValue, GroupSuccess, StoredObjectReference, UpdateObject, AliasObjectReference, Delete
import test_group_create_native as base


class OwnedGroupBatchTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_creation_history_survives_delete_in_the_same_group(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        context = assembly.group_context_in_transaction(tx).value
        operations = (self.create(label='short-lived', value='original', alias='created'),
                      Delete(operation='delete_object',
                             target=AliasObjectReference(alias='created'), expected_version='1'))
        result = assembly.apply_in_transaction(tx, context.input(operations, MapValue(entries=())),
                                               context.request('create-and-delete'), documents=self.documents)
        self.assertIsInstance(result, Ok, repr(result))
        self.assertIsInstance(result.value, GroupSuccess, repr(result))
        created, deleted = result.value.response.semantic.results
        self.assertEqual((created.outcome, deleted.outcome), ('created', 'deleted'))
        host.detach(); connection.commit()

        connection, host, assembly, tx = self.consumer()
        entity = HistoryEntity(kind='object', document_id='adoc', module_id='m',
                               definition_id='A', id=int(created.identity.id))
        original = assembly.reconstruct_in_transaction(tx, entity=entity, version=1)
        removed = assembly.reconstruct_in_transaction(tx, entity=entity, version=2)
        self.assertIsInstance(original, Ok, repr(original))
        self.assertIsInstance(original.value, HistoricalRecord, repr(original))
        self.assertIsInstance(removed, Ok, repr(removed))
        self.assertIsInstance(removed.value, HistoricalDeleted, repr(removed))
        self.assertEqual(original.value.record, removed.value.before)
        host.detach(); connection.rollback()

    def test_batch_updates_preserve_keys_and_committed_values(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        labels = {f'row-{i:02d}' for i in range(64)}
        context = assembly.group_context_in_transaction(tx).value
        original = context.input(tuple(self.create(label=label, value='before', alias=ABSENT)
                                       for label in sorted(labels)), MapValue(entries=()))
        created = assembly.apply_in_transaction(tx, original, context.request('batch-create'),
                                                documents=self.documents)
        self.assertIsInstance(created, Ok, repr(created))
        self.assertIsInstance(created.value, GroupSuccess)
        identities = tuple(r.identity for r in created.value.response.semantic.results)
        host.detach(); connection.commit()

        connection, host, assembly, tx = self.consumer()
        context = assembly.group_context_in_transaction(tx).value
        changes = tuple(UpdateObject(target=StoredObjectReference(identity=identity),
                                     set=(AuthoredValue(name='A-value', value=TextValue(kind='string', text='after')),),
                                     unset=(), expected_version='1') for identity in identities)
        updated = assembly.apply_in_transaction(tx, context.input(changes, MapValue(entries=())),
                                                context.request('batch-update'), documents=self.documents)
        self.assertIsInstance(updated, Ok, repr(updated))
        self.assertIsInstance(updated.value, GroupSuccess)
        host.detach(); connection.commit()

        connection, host, assembly, tx = self.consumer()
        page = assembly.page_objects_in_transaction(tx, document_id='adoc', module_id='m',
                                                     record_id='A', limit=128)
        self.assertIsInstance(page, Ok, repr(page))
        self.assertIsNone(page.value.continuation)
        self.assertEqual(len(page.value.objects), 64)
        self.assertEqual({dict(o.values)['A-label'] for o in page.value.objects}, labels)
        for obj in page.value.objects:
            self.assertEqual(dict(obj.values)['A-value'], 'after')
            self.assertEqual(obj.version, 2)
        for label in ('row-00', 'row-31', 'row-63'):
            found = assembly.lookup_key_in_transaction(tx, document_id='adoc', module_id='m',
                                                       record_id='A', key_id='z-alt', values=(label,))
            self.assertIsInstance(found, Ok, repr(found))
            self.assertIsInstance(found.value, ObjectFound, repr(found))
            self.assertEqual(dict(found.value.object.values)['A-label'], label)
            self.assertEqual(dict(found.value.object.values)['A-value'], 'after')
            self.assertEqual(found.value.object.version, 2)
        host.detach(); connection.commit()

    def test_unique_updates_keep_trailing_noop_and_duplicate_order(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        context = assembly.group_context_in_transaction(tx).value
        original = context.input(tuple(self.create(label=f'buffer-{i}', value='before', alias=ABSENT)
                                       for i in range(3)), MapValue(entries=()))
        created = assembly.apply_in_transaction(tx, original, context.request('buffer-create'),
                                                documents=self.documents)
        self.assertIsInstance(created, Ok, repr(created))
        identities = tuple(r.identity for r in created.value.response.semantic.results)
        host.detach(); connection.commit()

        def update(identity, value, version):
            return UpdateObject(target=StoredObjectReference(identity=identity),
                                set=(AuthoredValue(name='A-value', value=TextValue(kind='string', text=value)),),
                                unset=(), expected_version=version)

        connection, host, assembly, tx = self.consumer()
        context = assembly.group_context_in_transaction(tx).value
        operations = tuple(update(identity, 'after' if i < 2 else 'before', '1')
                           for i, identity in enumerate(identities))
        result = assembly.apply_in_transaction(tx, context.input(operations, MapValue(entries=())),
                                               context.request('buffer-update'), documents=self.documents)
        self.assertIsInstance(result, Ok, repr(result))
        self.assertIsInstance(result.value, GroupSuccess)
        self.assertEqual(tuple(r.version for r in result.value.response.semantic.results), ('2', '2', '1'))
        host.detach(); connection.commit()

        connection, host, assembly, tx = self.consumer()
        context = assembly.group_context_in_transaction(tx).value
        operations = (update(identities[0], 'again', '2'), update(identities[0], 'final', '3'))
        result = assembly.apply_in_transaction(tx, context.input(operations, MapValue(entries=())),
                                               context.request('duplicate-update'), documents=self.documents)
        self.assertIsInstance(result, Ok, repr(result))
        self.assertIsInstance(result.value, GroupSuccess)
        self.assertEqual(tuple(r.version for r in result.value.response.semantic.results), ('3', '4'))
        host.detach(); connection.commit()

        connection, host, assembly, tx = self.consumer()
        for identity, value, version in zip(identities, ('final', 'after', 'before'), (4, 2, 1)):
            found = assembly.get_object_in_transaction(tx, document_id='adoc', module_id='m',
                                                       record_id='A', object_id=int(identity.id))
            self.assertIsInstance(found, Ok, repr(found))
            self.assertIsInstance(found.value, ObjectFound)
            self.assertEqual(dict(found.value.object.values)['A-value'], value)
            self.assertEqual(found.value.object.version, version)
        host.detach(); connection.commit()
