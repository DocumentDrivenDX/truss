"""Basic public multi-object create/update/commit/read workflow."""
from truss import Ok, ObjectFound
from truss.contracts import ABSENT, MapValue, TextValue
from truss.groups import AuthoredValue, GroupSuccess, StoredObjectReference, UpdateObject
import test_group_create_native as base


class OwnedGroupBatchTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

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
