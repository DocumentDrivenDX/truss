"""Retained native side attribution, without original producer authority."""
from test_native_state_owner import NativeStateOwnerTests
from pathlib import Path

class NativeDependentOwnerTests(NativeStateOwnerTests):
    def setUp(self):
        super().setUp()
        root=Path(__file__).resolve().parents[3]
        self.connection.run((root/'packages/postgresql/native/row-image/dependent-owner.sql').read_text())

    def _node(self, **changes):
        cells=['501','601','NULL',"'root'",'NULL','NULL','NULL',"'scalar'","decode('05','hex')","decode('06','hex')"]
        for key,value in changes.items(): cells[int(key)]=value
        return 'ROW('+','.join(cells)+')::truss.row_home_node'

    def _scalar(self, **changes):
        cells=['501','601',"'string'","'value'",'NULL','NULL','NULL','NULL','NULL','NULL','NULL',"decode('07','hex')","decode('08','hex')"]
        for key,value in changes.items(): cells[int(key)]=value
        return 'ROW('+','.join(cells)+')::truss.row_home_scalar'

    def _dependent(self, kind, value=None, event=None, state=None, state_expected=None, node=None, node_expected=None):
        state=state or self._value();state_expected=state_expected or self._value()
        node=node or self._node();node_expected=node_expected or self._node()
        value=value or (self._node() if kind=='node' else self._scalar())
        event=event or value
        arguments=[value,'truss.row_image_'+kind+'_original('+event+')']
        if kind=='scalar': arguments += [node,'truss.row_image_node_original('+node_expected+')']
        arguments += [state,'truss.row_image_state_original('+state_expected+')']
        return self.connection.run('SELECT owner_kind,owner_id::text,discriminator_id::text,property_owner_type_id::text,property_id::text,original_image '
            'FROM truss.row_image_'+kind+'_owner_original('+','.join(arguments)+')')[0]

    def test_node_and_scalar_original_side_bytes(self):
        from truss._row_image import decode_row_image
        from truss._row_event_attribution import attribute_row_event
        side=tuple(decode_row_image(self.connection.run('SELECT truss.row_image_'+kind+'_original('+value+')')[0][0])
            for kind,value in (('state',self._value()),('node',self._node()),('scalar',self._scalar())))
        for kind in ('node','scalar'):
            row=self._dependent(kind)
            self.assertEqual(row[:5],['object','100','2','2','301'])
            value=self._node() if kind=='node' else self._scalar()
            expected=self.connection.run('SELECT truss.row_image_'+kind+'_original('+value+')')[0][0]
            self.assertEqual(row[5],expected)
            projected=attribute_row_event('INSERT',None,decode_row_image(row[5]),(),side,3,1048576).new_owner
            self.assertEqual(row[:5],[projected.kind,projected.owner_id,projected.discriminator_id,
                                     projected.property_owner_type_id,projected.property_id])

    def test_substituted_parent_event_and_inactive_slots_refuse(self):
        from pg8000.exceptions import DatabaseError
        cases=[('node',{'state':self._value(**{'12':"decode('0400','hex')"})}),
          ('node',{'event':self._node(**{'9':"decode('0600','hex')"})}),
          ('node',{'value':self._node(**{'0':'502'})}),
          ('node',{'value':self._node(**{'4':'0'})}),
          ('node',{'value':self._node(**{'8':'NULL'})}),
          ('scalar',{'node':self._node(**{'9':"decode('0600','hex')"})}),
          ('scalar',{'node':self._node(**{'0':'502'})}),
          ('scalar',{'value':self._scalar(**{'4':'true'})}),
          ('scalar',{'value':self._scalar(**{'11':'NULL'})}),
          ('scalar',{'state':self._value(**{'12':"decode('0400','hex')"})})]
        for kind,kwargs in cases:
            with self.subTest(kind=kind,kwargs=kwargs):
                self.connection.run('SAVEPOINT dependent')
                with self.assertRaises(DatabaseError): self._dependent(kind,**kwargs)
                self.connection.run('ROLLBACK TO SAVEPOINT dependent')
                self.connection.run('RELEASE SAVEPOINT dependent')

    def test_scalar_families_keep_exact_physical_payloads(self):
        families=[{'2':"'boolean'",'3':'NULL','4':'false'},
          {'2':"'integer'",'3':'NULL','5':'9007199254740993::numeric','6':"'9007199254740993'"},
          {'2':"'decimal'",'3':'NULL','5':'123.450::numeric','6':"'123.450'"},
          {'2':"'binary'",'3':'NULL','7':"decode('00ff','hex')"},
          {'2':"'timestamp'",'3':'NULL','8':"'2026-10-11T00:00:00Z'"},
          {'2':"'timestamp'",'3':'NULL','8':"'2026-10-11T00:00:00Z'",'9':"'2026-10-11T00:00:00Z'::timestamptz"},
          {'2':"'opaque'",'3':'NULL','10':"decode('00ff','hex')"}]
        for fields in families:
            with self.subTest(fields=fields):
                value=self._scalar(**fields)
                result=self._dependent('scalar',value=value)
                original=self.connection.run('SELECT truss.row_image_scalar_original('+value+')')[0][0]
                self.assertEqual(result[5],original)

    def test_actual_deleted_parent_cascade_uses_retained_originals(self):
        self.connection.run('SET LOCAL session_replication_role=replica')
        for kind,value in (('state',self._value()),('node',self._node()),('scalar',self._scalar())):
            self.connection.run('INSERT INTO truss.row_home_'+kind+' SELECT ('+value+').*')
        self.connection.run('SET LOCAL session_replication_role=origin')
        self.connection.run('CREATE TEMP TABLE original_sides AS SELECT s AS state,n AS node,c AS scalar,'
            'truss.row_image_state_original(s) AS state_image,truss.row_image_node_original(n) AS node_image,'
            'truss.row_image_scalar_original(c) AS scalar_image '
            'FROM truss.row_home_state s JOIN truss.row_home_node n USING(state_id) '
            'JOIN truss.row_home_scalar c USING(state_id,node_id)')
        self.connection.run('DELETE FROM truss.row_home_state WHERE state_id=501')
        for kind in ('state','node','scalar'):
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_'+kind),[[0]])
        result=self.connection.run('SELECT a.owner_kind,a.owner_id::text,a.discriminator_id::text,a.property_owner_type_id::text,a.property_id::text '
            'FROM original_sides o CROSS JOIN LATERAL truss.row_image_scalar_owner_original(o.scalar,'
            'o.scalar_image,o.node,o.node_image,o.state,o.state_image) a')
        self.assertEqual(result,[['object','100','2','2','301']])
