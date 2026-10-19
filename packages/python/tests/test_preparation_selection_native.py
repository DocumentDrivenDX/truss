# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic actual producer SQL selection; private excluded-admin diagnostic only."""
import psycopg
from truss._preparation_selection import diagnose_preparation_selection
import test_preparation_program_binding_native as original

_BINARY = '/private/tmp/weft-mutation-wheel-installed/weft/weft.abi3.so'


class PreparationSelectionNativeTests(original.PreparationProgramBindingNativeTests):
    def exercise(self, admin, data, params, enrolled):
        identity = admin.execute('SELECT program_id FROM truss.preparation_program_registration').fetchone()[0]
        def select():
            with psycopg.connect(**params, autocommit=True) as diagnostic:
                diagnostic.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
                try:
                    return diagnose_preparation_selection(diagnostic,program_id=identity,native_module_path=_BINARY)
                finally:
                    diagnostic.execute('ROLLBACK')
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
        try:
            with self.assertRaisesRegex(ValueError,'Excluded PG18.6 superuser'):
                diagnose_preparation_selection(data,program_id=identity,native_module_path=_BINARY)
        finally:
            data.execute('ROLLBACK')
        result = select()
        self.assertFalse(result.authority)
        self.assertEqual(result.preflights_completed,4)
        self.assertEqual(len(result.rows),1)
        self.assertEqual(result.rows[0][2],'bar')
        # This invalid row does not match the selector. Population validation
        # must still refuse before returning the otherwise valid selected row.
        admin.execute("INSERT INTO truss.object(type_id,props,rev) VALUES(1,'{}'::jsonb,1)")
        with self.assertRaisesRegex(ValueError,'complete-population preflight refused'):
            select()
