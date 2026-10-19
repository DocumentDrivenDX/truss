# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native state attribution primitive; administrative fixture grants no authority."""
from pathlib import Path
import unittest
from test_native_pg8000 import NativeBoundaryFixture

class NativeStateOwnerTests(NativeBoundaryFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        root = Path(__file__).resolve().parents[3]
        self.connection.run('BEGIN')
        for path in ('docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
                     'packages/postgresql/native/row-image/codec.sql',
                     'packages/postgresql/native/row-image/state-owner.sql'):
            self.connection.run((root/path).read_text())

    def _value(self, **changes):
        values = ['501', "'object'", '100', '2', 'NULL', 'NULL', '2', '301', '601',
                  "decode('00ff','hex')", "decode('02','hex')", "decode('03','hex')", "decode('04','hex')"]
        for index, value in changes.items():
            values[int(index)] = value
        return 'ROW(' + ','.join(values) + ')::truss.row_home_state'

    def _observe(self, value):
        return self.connection.run('SELECT owner_kind,owner_id::text,discriminator_id::text,'
            'property_owner_type_id::text,property_id::text,original_image '
            'FROM truss.row_image_state_owner_original(' + value + ')')[0]

    def test_exact_object_edge_and_signed_identities(self):
        obj = self._observe(self._value())
        edge = self._observe(self._value(**{'1':"'edge'",'2':'NULL','3':'NULL','4':'100','5':'10','6':'3'}))
        self.assertEqual(obj[:5], ['object','100','2','2','301'])
        self.assertEqual(edge[:5], ['edge','100','10','3','301'])
        signed = self._observe(self._value(**{'2':'-100','3':'-2','6':'-2','7':'-301'}))
        self.assertEqual(signed[:5], ['object','-100','-2','-2','-301'])
        expected = self.connection.run('SELECT truss.row_image_state_original('+self._value()+')')[0][0]
        self.assertEqual(obj[5], expected)
        changed = self._observe(self._value(**{'12':"decode('0400ff','hex')"}))
        self.assertNotEqual(obj[5], changed[5])

    def test_missing_or_mixed_fields_refuse(self):
        from pg8000.exceptions import DatabaseError
        changes = [{str(i):'NULL'} for i in (0,1,2,3,6,7,8,9,10,11,12)]
        changes += [{'4':'100'}, {'5':'10'}, {'6':'3'}, {'0':'0'}, {'1':"'other'"}]
        changes += [{'8':'0'}] + [{str(i):"decode('','hex')"} for i in (9,10,11,12)]
        for change in changes:
            with self.subTest(change=change):
                self.connection.run('SAVEPOINT attribution')
                with self.assertRaises(DatabaseError): self._observe(self._value(**change))
                self.connection.run('ROLLBACK TO SAVEPOINT attribution')
                self.connection.run('RELEASE SAVEPOINT attribution')

    def test_relation_profile_drift_refuses(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run('ALTER TABLE truss.row_home_state ADD COLUMN unregistered text')
        value=self._value().replace(')::truss.row_home_state',',NULL)::truss.row_home_state')
        with self.assertRaises(DatabaseError):
            self._observe(value)

    def test_actual_trigger_old_and_new_preserve_owner_and_full_bytes(self):
        # Replica mode skips unrelated FK fixture setup only. The measured
        # trigger is ALWAYS and fires on the actual original state relation.
        self.connection.run('SET LOCAL session_replication_role=replica')
        self.connection.run('CREATE TABLE public.state_attribution_events '
            '(event text,side text,kind text,owner bigint,discriminator int,property_owner int,property int,image bytea)')
        self.connection.run("""CREATE FUNCTION public.capture_state_attribution() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN
          IF TG_OP<>'INSERT' THEN
            INSERT INTO public.state_attribution_events SELECT TG_OP,'old',a.*
              FROM truss.row_image_state_owner_original(OLD) a;
          END IF;
          IF TG_OP<>'DELETE' THEN
            INSERT INTO public.state_attribution_events SELECT TG_OP,'new',a.*
              FROM truss.row_image_state_owner_original(NEW) a;
          END IF;
          RETURN NULL;
        END $$""")
        self.connection.run('CREATE TRIGGER measured_state_attribution AFTER INSERT OR UPDATE OR DELETE '
            'ON truss.row_home_state FOR EACH ROW EXECUTE FUNCTION public.capture_state_attribution()')
        self.connection.run('ALTER TABLE truss.row_home_state ENABLE ALWAYS TRIGGER measured_state_attribution')
        edge=self._value(**{'0':'502','1':"'edge'",'2':'NULL','3':'NULL','4':'100','5':'10','6':'3','8':'602'})
        for value in (self._value(),edge):
            self.connection.run('INSERT INTO truss.row_home_state SELECT ('+value+').*')
        self.connection.run("UPDATE truss.row_home_state SET source_bytes=decode('0400ff','hex') WHERE state_id=501")
        self.connection.run('DELETE FROM truss.row_home_state WHERE state_id=502')
        rows=self.connection.run('SELECT event,side,kind,owner::text,discriminator::text,property_owner::text,property::text,image '
            'FROM public.state_attribution_events ORDER BY event,side,kind')
        self.assertEqual(len(rows),5)
        for row in rows:
            expected=['object','100','2','2','301'] if row[2]=='object' else ['edge','100','10','3','301']
            self.assertEqual(row[2:7],expected)
        update={row[1]:row[7] for row in rows if row[0]=='UPDATE'}
        self.assertNotEqual(update['old'],update['new'])
