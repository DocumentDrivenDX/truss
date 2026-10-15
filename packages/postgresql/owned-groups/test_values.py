"""Basic ordered value simulation on a publicly accepted numeric catalog."""
import json
from pathlib import Path
import psycopg
from truss._group_runtime import _wire
from truss.contracts import TextValue
import test_numeric_facets_native as numeric


class OwnedValueSimulationTests(numeric.NumericFacetTests):
    for name in tuple(n for n in dir(numeric.NumericFacetTests) if n.startswith('test_')):
        locals()[name]=None

    def test_preserve_ordered_exact_values_without_graph_effects(self):
        connection,host,assembly,tx=self.ready(self.fields)
        host.detach();connection.rollback()
        self.admin.execute((Path(__file__).with_name('values.sql')).read_text())
        type_id=self.admin.execute("SELECT type_id FROM truss.type_def WHERE document_id='adoc' AND element='A'").fetchone()[0]
        def inventory():
            return self.admin.execute('SELECT (SELECT count(*) FROM truss.object),(SELECT count(*) FROM truss.edge),(SELECT count(*) FROM truss.journal),(SELECT count(*) FROM truss.object_key_bucket),(SELECT count(*) FROM truss.request_receipt)').fetchone()
        original=inventory()
        def simulate(operation,prior=None):
            return self.admin.execute('SELECT truss.owned_object_values(%s,%s::jsonb,%s::jsonb,%s::jsonb)',
                (type_id,json.dumps(operation),None if prior is None else json.dumps(prior['props']),None if prior is None else json.dumps(prior['retained']))).fetchone()[0]
        first=simulate({'operation':'create_object','values':[_wire(v) for v in self.values()]})
        first_values={v['name']:v['value'] for v in first['values']}
        self.assertEqual(first_values['quantity'],{'kind':'integer','text':'9007199254740993'})
        self.assertEqual(first_values['amount'],{'kind':'decimal','text':'1.2300'})
        update={'operation':'update_object','set':[{'name':'amount','value':_wire(TextValue(kind='decimal',text='1.23000'))}], 'unset':[]}
        second=simulate(update,first)
        self.assertEqual({v['name']:v['value'] for v in second['values']}['amount'],{'kind':'decimal','text':'1.23000'})
        self.assertEqual(first_values['amount']['text'],'1.2300')
        self.assertEqual(second['keys'],first['keys'])
        with self.assertRaises(psycopg.Error) as refused:
            simulate({'operation':'update_object','set':[],'unset':['quantity']},second)
        self.assertEqual(refused.exception.sqlstate,'22023')
        self.assertEqual(inventory(),original)
