"""Focused tests for the immutable application-side value schema."""
import unittest

from truss._record_schema import SchemaCompilationError, compile_records
from truss.contracts import BooleanValue, MapEntry, MapValue, NullValue, SequenceValue, TextValue
from truss.groups import AuthoredValue


PIN = 'a' * 64


def prop(prop_id, name, family, *, nullability='required', facets=None):
    return {'prop_id': prop_id, 'name': name, 'home': 'json', 'scalar_type': family,
            'nullability': nullability, 'cardinality': 'one', 'facets': facets or {}, 'item': None}


def item_node(module, element, declaration):
    return {'reference': {'module': module, 'element': element}, 'declaration': declaration}


def item_chain():
    row = item_node('m', 'row', {'kind': 'field', 'nullability': 'required',
        'cardinality': 'map', 'itemType': {'module': 'm', 'element': 'leaf'}, 'facets': {}})
    leaf = item_node('m', 'leaf', {'kind': 'field', 'nullability': 'required',
        'cardinality': 'one', 'scalarType': 'integer', 'facets': {'integerWidth': {'bits': 64, 'signed': True}}})
    row['descendants'] = [leaf]
    return row


class RecordSchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = compile_records([{
            'typeId': '7', 'definitionPin': PIN,
            'properties': [
                prop(1, 'name', 'string'),
                prop(2, 'note', 'string', nullability='absent-allowed'),
                prop(3, 'count', 'integer', facets={'integerWidth': {'bits': 64, 'signed': True}}),
                prop(4, 'amount', 'decimal', facets={'precision': 6, 'scale': 2}),
                prop(5, 'enabled', 'boolean'),
                prop(6, 'binary', 'binary'),
                prop(7, 'when', 'date'),
                prop(8, 'at', 'timestamp'),
                {'prop_id': 9, 'name': 'matrix', 'home': 'json', 'scalar_type': None,
                 'nullability': 'required', 'cardinality': 'array', 'facets': {}, 'item': item_chain()},
            ],
        }])

    def test_validates_scalar_families_exact_facets_and_present_null(self):
        values = (
            AuthoredValue(name='name', value=TextValue(kind='string', text='A')),
            AuthoredValue(name='note', value=NullValue()),
            AuthoredValue(name='count', value=TextValue(kind='integer', text='-9223372036854775808')),
            AuthoredValue(name='amount', value=TextValue(kind='decimal', text='12.3400')),
            AuthoredValue(name='enabled', value=BooleanValue(value=True)),
            AuthoredValue(name='binary', value=TextValue(kind='binary', text='AA==')),
            AuthoredValue(name='when', value=TextValue(kind='date', text='2024-02-29')),
            AuthoredValue(name='at', value=TextValue(kind='timestamp', text='2024-02-29T12:30:00.1234567890-00:00')),
            AuthoredValue(name='matrix', value=SequenceValue(items=(
                MapValue(entries=(MapEntry(key='z', value=TextValue(kind='integer', text='2')),
                               MapEntry(key='a', value=TextValue(kind='integer', text='1')))),
            ))),
        )
        self.assertTrue(self.schema.validate_values('7', PIN, values, mode='create').valid)
        zero_exponent = (AuthoredValue(name='amount', value=TextValue(kind='decimal', text='0e9999999999999999999999')) ,)
        self.assertTrue(self.schema.validate_values('7', PIN, zero_exponent).valid)
        invalid = (
            AuthoredValue(name='count', value=TextValue(kind='integer', text='9223372036854775808')),
            AuthoredValue(name='amount', value=TextValue(kind='decimal', text='1.234')),
            AuthoredValue(name='enabled', value=TextValue(kind='string', text='true')),
            AuthoredValue(name='binary', value=TextValue(kind='binary', text='AB==')),
            AuthoredValue(name='when', value=TextValue(kind='date', text='2023-02-29')),
            AuthoredValue(name='at', value=TextValue(kind='timestamp', text='2024-02-29T12:60:00Z')),
            AuthoredValue(name='name', value=NullValue()),
        )
        result = self.schema.validate_values('7', PIN, invalid)
        self.assertFalse(result.valid)
        self.assertEqual([v.property_name for v in result.violations],
                         ['count', 'amount', 'enabled', 'binary', 'when', 'at', 'name'])

    def test_checks_recursive_arrays_and_maps_without_reordering_values(self):
        values = (AuthoredValue(name='matrix', value=SequenceValue(items=(
            MapValue(entries=(MapEntry(key='z', value=TextValue(kind='integer', text='2')),
                           MapEntry(key='a', value=TextValue(kind='integer', text='1')))),
        ))),)
        self.assertTrue(self.schema.validate_values('7', PIN, values).valid)
        bad = (AuthoredValue(name='matrix', value=SequenceValue(items=(
            MapValue(entries=(MapEntry(key='duplicate', value=TextValue(kind='integer', text='1')),
                           MapEntry(key='duplicate', value=TextValue(kind='integer', text='2')))),
        ))),)
        self.assertFalse(self.schema.validate_values('7', PIN, bad).valid)

    def test_create_requires_required_known_fields_but_unknown_retained_values_are_untouched(self):
        values = (AuthoredValue(name='name', value=TextValue(kind='string', text='n')),
                  AuthoredValue(name='extension:opaque', value=TextValue(kind='string', text='keep')))
        result = self.schema.validate_values('7', PIN, values, mode='create')
        self.assertEqual({v.property_name for v in result.violations},
                         {'count', 'amount', 'enabled', 'binary', 'when', 'at', 'matrix'})
        self.assertEqual(self.schema.validate_values('7', PIN, values).violations, ())

    def test_unset_and_pin_binding_are_exact(self):
        result = self.schema.validate_unsets('7', PIN, ('note', 'unknown'))
        self.assertTrue(result.valid)
        self.assertEqual(self.schema.lookup_record_by_pin(PIN).type_id, '7')
        from truss._schema_memory import _resident_size
        self.assertGreater(_resident_size(self.schema), 256)
        result = self.schema.validate_unsets('7', PIN, ('name',))
        self.assertEqual(result.violations[0].code, 'required_unset')
        with self.assertRaisesRegex(ValueError, 'Exact current record schema pin'):
            self.schema.validate_values('7', 'b' * 64, ())
        patch = self.schema.prepare_patch(None, PIN, (AuthoredValue(name='name', value=TextValue(kind='string', text='n')),))
        self.assertTrue(patch.eligible)

    def test_prepared_patch_maps_known_properties_and_preserves_unknown_exact_values(self):
        values = (
            AuthoredValue(name='name', value=TextValue(kind='string', text='n')),
            AuthoredValue(name='matrix', value=SequenceValue(items=(
                MapValue(entries=(MapEntry(key='z', value=TextValue(kind='integer', text='2')),
                               MapEntry(key='a', value=TextValue(kind='integer', text='1')))),
            ))),
            AuthoredValue(name='future:field', value=MapValue(entries=(
                MapEntry(key='b', value=TextValue(kind='string', text='β')),
                MapEntry(key='a', value=TextValue(kind='string', text='α')),
            ))),
        )
        patch = self.schema.prepare_patch('7', PIN, values)
        self.assertTrue(patch.eligible)
        self.assertEqual(patch.props_set['1'], {'kind': 'string', 'text': 'n'})
        self.assertEqual([entry['key'] for entry in patch.props_set['9']['items'][0]['entries']], ['a', 'z'])
        self.assertEqual([entry['key'] for entry in patch.retained_set['future:field']['entries']], ['a', 'b'])
        wire = patch.wire_payload()
        wire['retainedSet']['future:field']['entries'].clear()
        self.assertEqual(len(patch.retained_set['future:field']['entries']), 2)

    def test_prepared_patch_refuses_fast_path_for_invalid_unknown_cells_and_projects_unsets(self):
        bad = (AuthoredValue(name='future:date', value=TextValue(kind='date', text='2023-02-29')) ,)
        patch = self.schema.prepare_patch('7', PIN, bad)
        self.assertFalse(patch.eligible)
        self.assertEqual(dict(patch.retained_set), {})
        values = (AuthoredValue(name='name', value=TextValue(kind='string', text='n')) ,)
        patch = self.schema.prepare_patch('7', PIN, values, unset=('note', 'future:field'))
        self.assertTrue(patch.eligible)
        self.assertEqual(patch.props_unset, ('2',))
        self.assertEqual(patch.retained_unset, ('future:field',))

    def test_every_retained_container_level_respects_native_1024_member_bound(self):
        oversized_array = AuthoredValue(name='future:array', value=SequenceValue(items=tuple(
            TextValue(kind='string', text='x') for _ in range(1025))))
        oversized_map = AuthoredValue(name='future:map', value=MapValue(entries=tuple(
            MapEntry(key=str(index), value=TextValue(kind='string', text='x')) for index in range(1025))))
        for entry in (oversized_array, oversized_map):
            self.assertFalse(self.schema.validate_values('7', PIN, (entry,)).valid)
            patch = self.schema.prepare_patch('7', PIN, (entry,))
            self.assertFalse(patch.eligible)
            self.assertEqual(dict(patch.retained_set), {})

    def test_prepared_patch_refuses_invalid_property_names_and_oversized_authored_lists(self):
        cell = TextValue(kind='string', text='keep')
        for name in ('', 'x' * 4097, 'bad\x00name', 'é' * 2049):
            patch = self.schema.prepare_patch('7', PIN, (AuthoredValue(name=name, value=cell),))
            self.assertFalse(patch.eligible, repr(name))
            self.assertEqual(dict(patch.props_set), {})
            self.assertEqual(dict(patch.retained_set), {})

        values = tuple(AuthoredValue(name=f'extension:{index}', value=cell) for index in range(1025))
        patch = self.schema.prepare_patch('7', PIN, values)
        self.assertFalse(patch.eligible)
        self.assertEqual(dict(patch.props_set), {})
        self.assertEqual(dict(patch.retained_set), {})

        unsets = tuple(f'extension:{index}' for index in range(1025))
        patch = self.schema.prepare_patch('7', PIN, (), unset=unsets)
        self.assertFalse(patch.eligible)
        self.assertEqual(dict(patch.props_set), {})
        self.assertEqual(dict(patch.retained_set), {})
        self.assertEqual(patch.props_unset, ())
        self.assertEqual(patch.retained_unset, ())

    def test_compilation_refuses_incomplete_or_unsupported_item_chain(self):
        records = [{'typeId': '7', 'definitionPin': PIN, 'properties': [
            {'prop_id': 1, 'name': 'bad', 'home': 'json', 'scalar_type': None,
             'nullability': 'required', 'cardinality': 'map', 'facets': {}, 'item': None}
        ]}]
        with self.assertRaises(SchemaCompilationError):
            compile_records(records)


if __name__ == '__main__':
    unittest.main()
