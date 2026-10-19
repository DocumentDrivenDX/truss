"""A shorter text limit names the stored strings and keeps the old schema."""
import json
import os

from truss import (CatalogAcceptanceRefused, CatalogDocument, CatalogRegistration,
    CatalogStoredViolator, Ok)
from truss.contracts import MapValue, TextValue
from truss.groups import (AuthoredValue, CreateObject, GroupFailed, GroupSuccess,
    RequestNone, RootlessOwnership, StoredObjectReference, UpdateObject)

import test_group_create_native as create_tests


class TextLimitEvolutionTests(create_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(create_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None
    source_version = '0.8.0'

    def fields(self, source):
        source['umf'] = self.source_version
        module = source['modules'][0]
        record = next(element for element in module['elements'] if element['id'] == 'A')
        record['name'] = 'A'
        for name, family, unit, maximum in (('note', 'string', 'unicode-scalar', 8), ('blob', 'binary', 'byte', 2)):
            module['elements'].append({'id': name, 'name': name, 'kind': 'field', 'scalarType': family,
                'nullability': 'required', 'cardinality': 'one', 'extensions': {},
                'facets': {'length': {'max': maximum, 'unit': unit}}})
            record['members'].append({'module': 'm', 'element': name})

    def values(self, label, note, blob):
        return self.create(label=label, value=label).values + (
            AuthoredValue(name='note', value=TextValue(kind='string', text=note)),
            AuthoredValue(name='blob', value=TextValue(kind='binary', text=blob)))

    def object(self, alias, label, note, blob):
        return CreateObject(type_definition_pin=self.types[('adoc', 'A')].definition_pin,
            values=self.values(label, note, blob), ownership=RootlessOwnership(), alias=alias)

    def facets(self, element):
        return self.admin.execute(
            """SELECT p.facets FROM truss.prop_def p
               JOIN truss.type_def t ON t.type_id = p.type_id
               WHERE t.document_id = 'adoc' AND t.element = 'A' AND p.element = %s AND p.retired_rev IS NULL""",
            (element,)).fetchone()[0]

    def test_shorter_text_limit_lists_stored_violators_and_keeps_schema(self):
        connection, host, assembly, tx = self.ready(self.fields)
        short = self.object('short', 'short', 'ok', 'YQ==')
        long = self.object('long', 'long', 'toolong!', 'YWI=')
        semantic, request = self.input(assembly, tx, (short, long))
        created = self.apply(assembly, tx, semantic, request)
        self.assertIsInstance(created, GroupSuccess)
        violator = created.response.semantic.results[1].identity
        context = assembly.group_context_in_transaction(tx).value
        over = self.object('over', 'over', 'toolong!!', 'YQ==')
        self.assertIsInstance(assembly.apply_in_transaction(tx, context.input((over,), MapValue(entries=())),
            RequestNone(), documents=self.documents, bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun')).value, GroupFailed)
        host.detach()
        connection.commit()
        self.admin.execute('GRANT ' + self.installation.registrar_role + ' TO consumer WITH SET FALSE')
        connection, host, assembly, tx = self.consumer()
        original = json.loads(next(document.content for document in self.documents if document.document_id == 'adoc'))
        narrowed = json.loads(json.dumps(original))
        for field in narrowed['modules'][0]['elements']:
            if field['id'] == 'note':
                field['facets'] = {'length': {'max': 3, 'unit': 'unicode-scalar'}}
            if field['id'] == 'blob':
                field['facets'] = {'length': {'max': 1, 'unit': 'byte'}}
        prepared = assembly.prepare_catalog((CatalogDocument('adoc', 'r2', json.dumps(narrowed).encode()),),
            source_version=self.source_version, bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        before = self.admin.execute('SELECT rev FROM truss.schema_head').fetchone()[0]
        original_facets = (self.facets('note'), self.facets('blob'))
        refused = assembly.accept_in_transaction(tx, prepared, request_key='shorten-text')
        self.assertIsInstance(refused, Ok, repr(refused))
        self.assertIsInstance(refused.value, CatalogAcceptanceRefused)
        self.assertEqual({(item.field_id, item.rule, item.affected_object_count, item.stored_values) for item in refused.value.violations},
            {('note', 'property.facets', 1, (CatalogStoredViolator(violator.id, 'toolong!'),)),
             ('blob', 'property.facets', 1, (CatalogStoredViolator(violator.id, 'YWI='),))})
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone()[0], before)
        self.assertEqual((self.facets('note'), self.facets('blob')), original_facets)
        fix = UpdateObject(target=StoredObjectReference(identity=violator),
            set=(AuthoredValue(name='note', value=TextValue(kind='string', text='yes')),
                 AuthoredValue(name='blob', value=TextValue(kind='binary', text='YQ=='))),
            unset=(), expected_version='1')
        semantic, request = self.input(assembly, tx, (fix,), action='fix')
        request = assembly.group_context_in_transaction(tx).value.request('fix-text')
        self.assertIsInstance(self.apply(assembly, tx, semantic, request), GroupSuccess)
        accepted = assembly.accept_in_transaction(tx, prepared, request_key='shorten-text-valid')
        self.assertIsInstance(accepted, Ok, repr(accepted))
        self.assertIsInstance(accepted.value, CatalogRegistration)
        host.detach()
        connection.commit()
        self.assertEqual(self.facets('note'), {'length': {'max': 3, 'unit': 'unicode-scalar'}})
        self.assertEqual(self.facets('blob'), {'length': {'max': 1, 'unit': 'byte'}})
        self.assertGreater(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone()[0], before)
        connection, host, assembly, tx = self.consumer()
        report = json.loads(assembly.report_in_transaction(tx, revision=accepted.value.revision).value.original_bytes)
        self.assertTrue(any(rule['rule'] == 'property.facets' and rule['enforcement'] == 'engine' and rule['elementId'] == 'note' and rule['documentId'] == 'adoc' for rule in report['enforcement']))
        pin = assembly.get_type_reference_in_transaction(tx, document_id='adoc', module_id='m', record_id='A').value.definition_pin
        blocked = CreateObject(type_definition_pin=pin, values=self.values('blocked', 'abcd', 'YWI='), ownership=RootlessOwnership())
        context = assembly.group_context_in_transaction(tx).value
        self.assertIsInstance(assembly.apply_in_transaction(tx, context.input((blocked,), MapValue(entries=())),
            RequestNone(), documents=self.documents, bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun')).value, GroupFailed)
        host.detach()
        connection.rollback()
        self.admin.execute(
            """UPDATE truss.object AS stored SET props = stored.props || jsonb_build_object(property.prop_id::text, '{"kind":"string","text":"toolong!"}'::jsonb)
               FROM truss.prop_def AS property
               JOIN truss.type_def AS record ON record.type_id = property.type_id
               WHERE stored.id = %s AND stored.type_id = record.type_id AND record.document_id = 'adoc' AND property.element = 'note'""",
            (int(violator.id),))
        self.assertEqual(self.admin.execute(
            """SELECT stored.props->property.prop_id::text->>'text'
               FROM truss.object AS stored
               JOIN truss.prop_def AS property ON property.type_id = stored.type_id AND property.element = 'note' AND property.retired_rev IS NULL
               WHERE stored.id = %s""",
            (int(violator.id),)).fetchone()[0], 'toolong!')


class TextLimitEvolution07Tests(TextLimitEvolutionTests):
    source_version = '0.7.0'
