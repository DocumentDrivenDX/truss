"""Complete-census correspondence only; no native authority or release proof."""
import copy
import json
import unittest
from decimal import Decimal
from truss._current_disclosure_stage import _population, _reconstruct_batch
from truss._current_disclosure_wire import array_members


class DisclosurePopulationTests(unittest.TestCase):
    def setUp(self):
        self.target={'documentId':'d','moduleId':'m','elementId':'Resource'}
        self.selection={'type':self.target,'fields':[]}
        self.resources=[{'type':self.target,'key':{'id':n}} for n in range(3)]
        self.facts=[dict(r,properties={}) for r in self.resources]
        self.result={'decisions':[{'resource':r,'decision':'permit' if n!=1 else 'deny'} for n,r in enumerate(self.resources)],'resources':[self.resources[0],self.resources[2]]}
        self.batch={'rows':[[{'kind':'withheld'}],[{'kind':'absent'}]]}

    def test_complete_census_and_producer_order(self):
        self.assertEqual(_population(self.facts,self.selection,self.result,self.batch),self.result['resources'])
        reordered=copy.deepcopy(self.result)
        reordered['decisions'].reverse();reordered['resources'].reverse()
        self.assertEqual(_population(list(reversed(self.facts)),self.selection,reordered,self.batch),reordered['resources'])
        unrelated={'type':dict(self.target,elementId='Other'),'key':{'id':0}}
        self.assertEqual(_population(self.facts+[unrelated],self.selection,self.result,self.batch),self.result['resources'])

    def test_missing_duplicate_foreign_and_indeterminate_decisions_refuse(self):
        variants=[]
        for mutate in (
            lambda r:r['decisions'].pop(),
            lambda r:r['decisions'].append(copy.deepcopy(r['decisions'][0])),
            lambda r:r['decisions'][0]['resource']['key'].update(id=999),
            lambda r:r['decisions'][0].update(decision='unknown'),
            lambda r:r['resources'].reverse(),
            lambda r:r['resources'].pop(),
        ):
            result=copy.deepcopy(self.result);mutate(result);variants.append(result)
        for result in variants:
            with self.subTest(result=result),self.assertRaises(ValueError):
                _population(self.facts,self.selection,result,self.batch)
        with self.assertRaises(ValueError):_population(self.facts+self.facts[:1],self.selection,self.result,self.batch)
        with self.assertRaises(ValueError):_population(self.facts,self.selection,self.result,{'rows':[]})

    def test_empty_population_is_explicit_and_complete(self):
        self.assertEqual(_population([],self.selection,{'decisions':[],'resources':[]},{'rows':[]}),[])
        with self.assertRaises(ValueError):_population(self.facts,self.selection,{'decisions':[],'resources':[]},{'rows':[]})
        denied={'decisions':[{'resource':r,'decision':'deny'} for r in self.resources],'resources':[]}
        self.assertEqual(_population(self.facts,self.selection,denied,{'rows':[]}),[])

    def test_raw_array_cells_preserve_number_and_unicode_tokens(self):
        cells=[b'{"kind":"original","value":1.2300e-999999}',b'{"kind":"original","value":"\\u0061"}',b'{"kind":"absent"}',b'{"kind":"withheld"}',b'{"kind":"original","value":null}']
        self.assertEqual(array_members(b' [ '+b' , '.join(cells)+b' ] '),cells)
        self.assertEqual(array_members(b'[]'),[])
        self.assertEqual(array_members(b'[[1,2],{"x":[3,4]}]'),[b'[1,2]',b'{"x":[3,4]}'])
        for raw in (b'{}',b'[NaN]',b'[1,]',b'[{"x":1,"x":2}]',b'["\\ud800"]',b'[1] trailing'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):array_members(raw)

    def test_reconstruction_preserves_producer_order_and_repeated_projection(self):
        header=b'{"version":"fixture-only","unknown":1.2300e-999999,"rows":[]}'
        def row(key,value):
            return (value,value,json.dumps({'version':'weft.stage-row-tuple/0.1-candidate','rows':[{'scan':'s0','key':key}]}))
        descriptors=[{'headerColumn':0},{'headerColumn':0}]
        first='{"kind":"absent"}';second='{"kind":"original","value":null}'
        result=_reconstruct_batch(header,[row('1',second),row('0',first)],descriptors,2,1)
        self.assertIn(b'"unknown":1.2300e-999999',result)
        self.assertIn(b'"rows":[['+first.encode()+b'],['+second.encode()+b']]',result)
        self.assertEqual(_reconstruct_batch(header,[],descriptors,0,1),header)
        for rows in ([row('0',first)], [row('0',first),row('0',first)], [row('2',first),row('0',first)], [(first,second,row('0',first)[-1]),row('1',second)]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                _reconstruct_batch(header,rows,descriptors,2,1)
        for descriptor in ({'headerColumn':True},{'headerColumn':1},{'headerColumn':-1}):
            with self.assertRaises(ValueError):_reconstruct_batch(header,[row('0',first)],[descriptor,descriptor],1,1)


if __name__=='__main__':unittest.main()
