"""One adopter workflow for a composed subtree and its original receipts.

This is the next owned-provider implementation target, not a released capability.
All graph rows are created through the public API.
"""
import json
import os
from dataclasses import replace

from truss import (Ok, ObjectFound, ObjectNotFound, QueryRows, HistoryEntity, EdgeFound, EdgePage, TraversalHop, TraversalComplete,
                   HistoricalRecord, HistoricalDeleted)
from truss.groups import (OwnedOwnership, StoredObjectReference, AliasObjectReference,
                          CreateEdge, UpdateEdge, UpdateObject, EndpointChange,
                          NullOrderKey, Delete, GroupSuccess, GroupFailed,
                          CommittedReceiptReplay)
import test_receipt_visibility_native as receipt_tests


class OwnedObjectTests(receipt_tests.ReceiptVisibilityTests):
    for _name in tuple(n for n in dir(receipt_tests.ReceiptVisibilityTests) if n.startswith('test_')):
        locals()[_name] = None

    @staticmethod
    def owned_model(source):
        source['umf'] = '0.8.0'
        module = source['modules'][0]
        for element in module['elements']:
            if element['kind'] == 'record':
                element['name'] = element['id']
        module['relationships'].append({
            'id': 'children', 'name': 'children',
            'source': [{'module': 'm', 'element': 'A'}],
            'target': [{'module': 'm', 'element': 'A', 'key': 'a-primary'}],
            'sourceMultiplicity': {'min': 0, 'max': 1},
            'targetMultiplicity': {'min': 0, 'max': 4},
            'targetLifecycle': 'owned', 'directed': True,
        })

    def found(self, assembly, tx, identity):
        value = self.read(assembly, tx, identity)
        self.assertIsInstance(value, ObjectFound, repr(value))
        return value.object

    def test_subtree_reparent_dryrun_cascade_history_and_original_retry(self):
        self.workflow(include_query=False)

    def test_owned_descendant_query_attribution(self):
        self.workflow(include_query=True)

    def workflow(self, *, include_query):
        connection, host, assembly, tx = self.ready(self.owned_model, document_ids=('adoc',))
        relation = assembly.get_relationship_reference_in_transaction(
            tx, document_id='adoc', module_id='m', relationship_id='children').value
        independent = assembly.get_relationship_reference_in_transaction(
            tx, document_id='adoc', module_id='m', relationship_id='A-B').value

        def alias(name):
            return AliasObjectReference(alias=name)

        def stored(identity):
            return StoredObjectReference(identity=identity)

        def link(pin, source, target, name):
            return CreateEdge(relationship_definition_pin=pin, source=source,
                              target=target, values=(), order_key=NullOrderKey(), alias=name)

        created, original_input, original_request = self.run_group(assembly, tx, (
            self.create('first-root', 'first-root', alias='first-root'),
            self.create('second-root', 'second-root', alias='second-root'),
            replace(self.create('child', 'child', alias='child'),
                    ownership=OwnedOwnership(root=alias('first-root'))),
            replace(self.create('grandchild', 'grandchild', alias='grandchild'),
                    ownership=OwnedOwnership(root=alias('first-root'))),
            link(relation.definition_pin, alias('first-root'), alias('child'), 'parent-edge'),
            link(relation.definition_pin, alias('child'), alias('grandchild'), 'child-edge'),
            self.create('outside', 'outside', alias='outside', record='B'),
        ), 'owned-create')
        self.assertIsInstance(created, GroupSuccess, repr(created))
        first, second, child, grandchild, parent_edge, child_edge, outside = (
            result.identity for result in created.response.semantic.results)
        def check_edges(parent):
            for identity, source, target in ((parent_edge, parent, child), (child_edge, child, grandchild)):
                result = assembly.get_edge_in_transaction(tx, document_id='adoc', module_id='m',
                    relationship_id='children', edge_id=int(identity.id))
                self.assertIsInstance(result, Ok, repr(result))
                self.assertIsInstance(result.value, EdgeFound, repr(result.value))
                self.assertEqual((result.value.edge.source, result.value.edge.target), (source, target))
            result = assembly.page_edges_in_transaction(tx, document_id='adoc', module_id='m',
                relationship_id='children', anchor=child, direction='incoming', limit=1)
            self.assertIsInstance(result, Ok, repr(result))
            self.assertIsInstance(result.value, EdgePage, repr(result.value))
            self.assertEqual(tuple(edge.identity for edge in result.value.edges), (parent_edge,))
            empty = assembly.page_edges_in_transaction(tx, document_id='adoc', module_id='m',
                relationship_id='children', anchor=grandchild, direction='outgoing')
            self.assertIsInstance(empty, Ok, repr(empty))
            self.assertIsInstance(empty.value, EdgePage, repr(empty.value))
            self.assertEqual(empty.value.edges, ())
        check_edges(first)
        def check_traversal(root):
            result = assembly.traverse_in_transaction(tx, start=root,
                hops=(TraversalHop(relationship=relation),) * 2)
            self.assertIsInstance(result, Ok, repr(result))
            self.assertIsInstance(result.value, TraversalComplete, repr(result.value))
            self.assertEqual(tuple(obj.identity for obj in result.value.objects), (grandchild,))
            self.assertEqual(result.value.objects[0].ownership, OwnedOwnership(root=stored(root)))
            incoming = assembly.traverse_in_transaction(tx, start=grandchild,
                hops=(TraversalHop(relationship=relation, direction='incoming'),))
            self.assertIsInstance(incoming, Ok, repr(incoming))
            self.assertIsInstance(incoming.value, TraversalComplete, repr(incoming.value))
            self.assertEqual(tuple(obj.identity for obj in incoming.value.objects), (child,))
        check_traversal(first)
        for identity in (child, grandchild):
            self.assertEqual(self.found(assembly, tx, identity).ownership,
                             OwnedOwnership(root=stored(first)))
        keyed = assembly.lookup_key_in_transaction(tx, document_id='adoc', module_id='m',
            record_id='A', key_id='a-primary', values=('child', 'child'), bun_executable='/missing/bun')
        self.assertIsInstance(keyed, Ok, repr(keyed))
        self.assertIsInstance(keyed.value, ObjectFound, repr(keyed.value))
        self.assertEqual(keyed.value.object.identity, child)
        self.assertEqual(keyed.value.object.ownership, OwnedOwnership(root=stored(first)))
        page = assembly.page_objects_in_transaction(tx, document_id='adoc', module_id='m', record_id='A')
        self.assertIsInstance(page, Ok, repr(page))
        self.assertEqual({obj.identity for obj in page.value.objects}, {first, second, child, grandchild})
        first_page = assembly.page_objects_in_transaction(tx, document_id='adoc', module_id='m', record_id='A', limit=2)
        self.assertIsInstance(first_page, Ok, repr(first_page))
        self.assertEqual(tuple(obj.identity for obj in first_page.value.objects), (first, second))
        self.assertIsNotNone(first_page.value.continuation)
        tail = assembly.page_objects_in_transaction(tx, document_id='adoc', module_id='m', record_id='A',
            limit=2, cursor=first_page.value.continuation)
        self.assertIsInstance(tail, Ok, repr(tail))
        self.assertEqual(tuple(obj.identity for obj in tail.value.objects), (child, grandchild))
        self.assertTrue(all(obj.ownership == OwnedOwnership(root=stored(first)) for obj in tail.value.objects))
        host.detach()
        connection.commit()
        connection, host, assembly, tx = self.consumer()

        retarget = UpdateEdge(target=stored(parent_edge), set=(), unset=(),
                              expected_version='1', endpoint_change=EndpointChange(
                                  source=stored(second), target=stored(child)))
        refused, _, _ = self.run_group(assembly, tx, (retarget,), 'implicit-reparent')
        self.assertIsInstance(refused, GroupFailed, repr(refused))
        self.assertEqual(self.found(assembly, tx, grandchild).version, 1)
        move = (retarget, UpdateObject(target=stored(child), set=(), unset=(),
                                      expected_version='1',
                                      ownership_change=OwnedOwnership(root=stored(second))))
        dryrun, _, _ = self.run_group(assembly, tx, move, 'move-subtree')
        self.assertIsInstance(dryrun, GroupSuccess, repr(dryrun))
        self.assertEqual(self.found(assembly, tx, grandchild).ownership,
                         OwnedOwnership(root=stored(second)))
        host.detach()
        connection.rollback()
        connection, host, assembly, tx = self.consumer()
        self.assertEqual(self.found(assembly, tx, grandchild).ownership,
                         OwnedOwnership(root=stored(first)))
        moved, _, _ = self.run_group(assembly, tx, move, 'move-subtree')
        self.assertIsInstance(moved, GroupSuccess, repr(moved))
        self.assertEqual(self.found(assembly, tx, grandchild).version, 2)
        check_edges(second)
        check_traversal(second)
        if include_query:
            query = assembly.query_in_transaction(tx,
                sql='SELECT a.* FROM "A" a WHERE a."A-label" = :label',
                document_ids=('adoc',), parameters={'label': 'grandchild'}, read_profile='complete-entity')
            self.assertIsInstance(query, Ok, repr(query))
            self.assertIsInstance(query.value, QueryRows, repr(query.value))
            row = dict(zip(query.value.columns, query.value.rows[0], strict=True))
            self.assertEqual((row['_version'], row['_created_by'], row['_updated_by']),
                             (2, 'consumer', 'consumer'))
        linked, _, _ = self.run_group(assembly, tx, (
            link(independent.definition_pin, stored(child), stored(outside), 'independent'),
        ), 'independent-link')
        self.assertIsInstance(linked, GroupSuccess, repr(linked))
        independent_edge = linked.response.semantic.results[0].identity
        unchanged, _, _ = self.run_group(assembly, tx, (
            UpdateObject(target=stored(grandchild), set=(), unset=(), expected_version='2'),
        ), 'owned-noop-with-independent-boundary')
        self.assertIsInstance(unchanged, GroupSuccess, repr(unchanged))
        self.assertEqual(unchanged.response.semantic.results[0].outcome, 'unchanged')
        deletion = Delete(operation='delete_object', target=stored(second), expected_version='1')
        refused, _, _ = self.run_group(assembly, tx, (deletion,), 'blocked-cascade')
        self.assertIsInstance(refused, GroupFailed, repr(refused))
        self.assertEqual(self.found(assembly, tx, grandchild).version, 2)
        deleted, delete_input, delete_request = self.run_group(assembly, tx, (
            Delete(operation='delete_edge', target=stored(independent_edge)), deletion,
        ), 'delete-subtree')
        self.assertIsInstance(deleted, GroupSuccess, repr(deleted))
        self.assertEqual({entry.identity for entry in deleted.response.semantic.results[1].deleted},
                         {second, child, grandchild, parent_edge, child_edge})
        for identity in (second, child, grandchild):
            self.assertIsInstance(self.read(assembly, tx, identity), ObjectNotFound)
        host.detach()
        connection.commit()
        connection, host, assembly, tx = self.consumer()
        for input, request, semantic in (
            (original_input, original_request, created.response.semantic),
            (delete_input, delete_request, deleted.response.semantic),
        ):
            replay = assembly.apply_in_transaction(tx, input, request, documents=self.documents,
                bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
            self.assertIsInstance(replay, Ok, repr(replay))
            self.assertIsInstance(replay.value.response, CommittedReceiptReplay)
            self.assertEqual(replay.value.response.semantic, semantic)
        host.detach()
        connection.rollback()
        connection, host, assembly, tx = self.readonly()
        entity = HistoryEntity(kind='object', document_id='adoc', module_id='m',
                               definition_id='A', id=int(grandchild.id))
        for version, root in ((1, first), (2, second)):
            historical = assembly.reconstruct_in_transaction(tx, entity=entity, version=version)
            self.assertIsInstance(historical, Ok, repr(historical))
            self.assertIsInstance(historical.value, HistoricalRecord, repr(historical.value))
            self.assertEqual(json.loads(historical.value.record)['ownership']['root']['id'], root.id)
        removed = assembly.reconstruct_in_transaction(tx, entity=entity, version=3)
        self.assertIsInstance(removed.value, HistoricalDeleted)
        self.assertEqual(json.loads(removed.value.before)['ownership']['root']['id'], second.id)
        host.detach()
        connection.rollback()
