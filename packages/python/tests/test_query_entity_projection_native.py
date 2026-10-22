# SPDX-License-Identifier: MIT OR Apache-2.0
"""HF-04 selected facts and explicit relationships through the shared compiler."""
from unittest.mock import patch
from truss import Ok, QueryRows, QueryPage, QueryRefused, QueryEntityProjection, QueryRelatedKeys
from truss.groups import CreateEdge, NullOrderKey, StoredObjectReference, Delete, GroupSuccess
import test_compiled_query_native as fixtures


class QueryEntityProjectionTests(fixtures.CompiledQueryTests):
    for _name in tuple(n for n in dir(fixtures.CompiledQueryTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_selectable_facts_preserve_requested_order_and_compiler_types(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        created,_,_=self.run_group(a,t,(self.create(),));self.assertIsInstance(created,GroupSuccess)
        capability=a.compiled_execution(a.compiled_selection).capability
        no_facts=capability.query_in_transaction(t,sql='SELECT a.* FROM "A" a',document_ids=('adoc',),entity_projection=QueryEntityProjection())
        self.assertIsInstance(no_facts.value,QueryRows,repr(no_facts))
        self.assertEqual(no_facts.value.columns,('A-label','A-value'))
        selected=capability.query_in_transaction(t,sql='SELECT a.* FROM "A" a',document_ids=('adoc',),entity_projection=QueryEntityProjection(facts=('updatedAt','version')))
        self.assertIsInstance(selected.value,QueryRows,repr(selected))
        self.assertEqual(selected.value.columns,('A-label','A-value','_updated_at','_version'))
        self.assertEqual(selected.value.rows[0][-1],1)
        self.assertRegex(selected.value.rows[0][-2],r'^\d{4}-\d{2}-\d{2}T.*\.\d{6}Z$')
        self.assertEqual(selected.value.column_descriptors[-1].logical_type,{'family':'integer','facets':{},'nullable':False})

    def test_facts_pages_and_projection_bound_continuation(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        self.assertIsInstance(self.run_group(a,t,(self.create(label='a',alias='a'),self.create(label='b',alias='b')))[0],GroupSuccess)
        selection=QueryEntityProjection(facts=('version',))
        page=a.query_page_in_transaction(t,sql='SELECT a.* FROM "A" a',document_ids=('adoc',),limit=1,entity_projection=selection)
        self.assertIsInstance(page.value,QueryPage,repr(page));self.assertIsNotNone(page.value.next_cursor)
        self.assertEqual(page.value.columns,('A-label','A-value','_version'))
        self.assertEqual(len(page.value.column_descriptors),3)
        changed=a.query_page_in_transaction(t,sql='SELECT a.* FROM "A" a',document_ids=('adoc',),limit=1,cursor=page.value.next_cursor,entity_projection=QueryEntityProjection())
        self.assertIsInstance(changed.value,QueryRefused);self.assertEqual(changed.value.code,'stale_context')
        tail=a.query_page_in_transaction(t,sql='SELECT a.* FROM "A" a',document_ids=('adoc',),limit=1,cursor=page.value.next_cursor,entity_projection=selection)
        self.assertIsInstance(tail.value,QueryPage,repr(tail));self.assertIsNone(tail.value.next_cursor)
        self.assertEqual(tail.value.column_descriptors,page.value.column_descriptors)
        self.assertEqual([page.value.rows[0][0],tail.value.rows[0][0]],['a','b'])

    def test_explicit_relationship_projection_keeps_100_101_completeness_boundary(self):
        def unbounded(source):source['modules'][0]['relationships'][0]['targetMultiplicity']['max']='*'
        c,h,a,t=self.ready(unbounded,document_ids=('adoc',))
        objects=(self.create(alias='parent'),)+tuple(self.create(record='B',label=f'b{i:03}',alias=f'b{i}') for i in range(101))
        seeded,_,_=self.run_group(a,t,objects,'seed-objects');self.assertIsInstance(seeded,GroupSuccess,repr(seeded))
        identities=[r.identity for r in seeded.response.semantic.results];parent=identities[0]
        pin=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        edges=tuple(CreateEdge(relationship_definition_pin=pin,source=StoredObjectReference(identity=parent),target=StoredObjectReference(identity=child),values=(),order_key=NullOrderKey()) for child in identities[1:])
        linked,_,_=self.run_group(a,t,edges,'seed-edges');self.assertIsInstance(linked,GroupSuccess,repr(linked))
        complete=QueryEntityProjection(facts=('version',),relationships=True)
        refused=a.query_in_transaction(t,sql='SELECT a.* FROM "A" a',document_ids=('adoc',),entity_projection=complete)
        self.assertIsInstance(refused.value,QueryRefused,repr(refused));self.assertEqual(refused.value.code,'limits')
        fields_only=a.query_in_transaction(t,sql='SELECT a.* FROM "A" a',document_ids=('adoc',),entity_projection=QueryEntityProjection())
        self.assertIsInstance(fields_only.value,QueryRows,repr(fields_only));self.assertEqual(len(fields_only.value.columns),2)
        bounded=a.query_in_transaction(t,sql='SELECT a.*, RELATED_KEYS(a."A-B", 2) AS links FROM "A" a',document_ids=('adoc',),entity_projection=QueryEntityProjection())
        self.assertIsInstance(bounded.value,QueryRows,repr(bounded));keys=bounded.value.rows[0][-1]
        self.assertIsInstance(keys,QueryRelatedKeys);self.assertEqual(len(keys.items),2);self.assertTrue(keys.truncated)
        removed,_,_=self.run_group(a,t,(Delete(operation='delete_edge',target=StoredObjectReference(identity=linked.response.semantic.results[-1].identity)),),'remove-one')
        self.assertIsInstance(removed,GroupSuccess)
        exact=a.query_in_transaction(t,sql='SELECT a.* FROM "A" a',document_ids=('adoc',),entity_projection=complete)
        self.assertIsInstance(exact.value,QueryRows,repr(exact));self.assertEqual(len(exact.value.rows[0][-1]),100)

    def test_invalid_fact_selection_refuses_before_host_execution(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        for selection in (QueryEntityProjection(facts=('version','version')),QueryEntityProjection(facts=('invented',)),QueryEntityProjection(relationships=1)):
            with patch.object(type(h),'_run_operation',side_effect=AssertionError('Invalid projection must not execute')):
                result=a.query_in_transaction(t,sql='SELECT a.* FROM "A" a',document_ids=('adoc',),entity_projection=selection)
            self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,QueryRefused);self.assertEqual(result.value.code,'invalid_query')
