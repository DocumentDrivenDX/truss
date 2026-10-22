# SPDX-License-Identifier: MIT OR Apache-2.0
"""Runtime routine recipes follow ordered SQL fragments and native overloads."""
import json
import unittest
from unittest.mock import patch

from truss._preparation_source_epoch import _runtime_inventory, _runtime_recipe
from truss.catalog_runtime import _release


def function(name, args, body, *, replace=False):
    operation = 'CREATE OR REPLACE FUNCTION' if replace else 'CREATE FUNCTION'
    return (f'{operation} truss.{name}({args}) RETURNS integer '
            'LANGUAGE sql IMMUTABLE AS $$' + body + '$$;')


class _InventoryCursor:
    def __init__(self, *, actual_body):
        self.actual_body = actual_body
        self.rows = []
        self.routine_lookup_params = None

    def execute(self, query, params=None, **kwargs):
        if 'SELECT registrar_oid FROM' in query:
            self.rows = [(11,)]
            return
        if 'SELECT current_user::' in query:
            self.rows = [(20,)]
            return
        if 'to_regprocedure' in query:
            self.rows = [(123,)] if params == ('truss.select_value(integer)',) else [(None,)]
            return
        if 'to_regtype' in query:
            self.rows = [(23,), (23,)]
            return
        if 'to_jsonb(p)' in query:
            self.routine_lookup_params = params
            actual = {
                'oid': '123', 'proowner': '10', 'prokind': 'f',
                'prorettype': '23', 'proretset': False,
                'proargtypes': ['23'], 'pronargs': 1,
                'proallargtypes': None, 'proargnames': ['arg'],
                'proargmodes': None, 'pronargdefaults': 0,
                'prosecdef': False, 'proisstrict': False,
                'provolatile': 'i', 'proparallel': 'u',
                'proleakproof': False, 'prosupport': '-',
                'proconfig': None, 'prosrc': self.actual_body,
            }
            self.rows = [(json.dumps(actual), 'sql', None)]
            self.rows = [(json.dumps(actual), 'sql', None, 'select_value(integer)')]
            return
        if 'aclexplode' in query:
            self.rows = [(10, 10, 'EXECUTE', False)]
            return
        raise AssertionError(f'Unexpected inventory query: {query}')

    def fetchmany(self, count):
        rows, self.rows = self.rows[:count], self.rows[count:]
        return rows

    def fetchone(self):
        rows = self.fetchmany(1)
        return rows[0] if rows else None


class PreparationRuntimeRecipeTests(unittest.TestCase):
    def test_package_recipe_tracks_overloads_and_later_runtime_replacement(self):
        _, _, sources = _release()
        recipe = _runtime_recipe(sources)
        overloaded = [row for row in recipe if row['name'] == 'truss.object_group_begin']
        current = [row for row in recipe if row['name'] == 'truss.runtime_current_installation']
        self.assertEqual(len(overloaded), 1)
        self.assertEqual(len(current), 1)
        self.assertIn('Managed grant policy shape or bounds changed', current[0]['body'])

    def test_ordered_replace_overrides_only_matching_signature(self):
        sources = [
            function('select_value', 'selected integer', 'SELECT selected'),
            function('select_value', 'selected text', 'SELECT 7'),
            function('select_value', 'selected integer', 'SELECT selected + 1', replace=True),
        ]
        recipe = _runtime_recipe(sources)
        self.assertEqual(len(recipe), 2)
        self.assertEqual(recipe[0]['body'], 'SELECT selected + 1')
        self.assertEqual(recipe[1]['body'], 'SELECT 7')

    def test_native_inventory_rejects_changed_routine_body(self):
        sources = [function('select_value', 'arg integer', 'SELECT arg')]
        with patch('truss._preparation_source_epoch._expected_runtime_acls', return_value={'select_value(integer)': {(10, 'EXECUTE', False)}}):
            with self.assertRaisesRegex(ValueError, 'Original runtime body and execution attributes required'):
                _runtime_inventory(_InventoryCursor(actual_body='SELECT arg + 1'), sources, 10)

    def test_native_inventory_accepts_matching_exact_overload(self):
        sources = [function('select_value', 'arg integer', 'SELECT arg')]
        cursor = _InventoryCursor(actual_body='SELECT arg')
        with patch('truss._preparation_source_epoch._expected_runtime_acls', return_value={'select_value(integer)': {(10, 'EXECUTE', False)}}):
            result = _runtime_inventory(cursor, sources, 10)
        self.assertEqual(cursor.routine_lookup_params, ('select_value', 1, '23'))
        self.assertIn(b'"signature":"truss.select_value(integer)"', result)

    def test_unparsed_function_declaration_refuses_incomplete_recipe(self):
        sources = [function('select_value', 'arg integer', 'SELECT arg'),
                   'CREATE FUNCTION truss.unqualified(arg integer) RETURNS integer LANGUAGE c AS \'x\';']
        with self.assertRaisesRegex(ValueError, 'Complete original runtime routine recipe required'):
            _runtime_recipe(sources)


if __name__ == '__main__':
    unittest.main()
