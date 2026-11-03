# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure tuple/metadata custody controls, never native cursor qualification."""
import copy
import json
import unittest
from truss.contracts import LocalTimestampValue,TextValue
from truss.query import QueryAbsent
from truss._temporal_query_execution import _page_metadata,_after,_row_after


class TemporalContinuationTests(unittest.TestCase):
    def program(self):
        outputs=[{'name':name,'carrier':kind,'nullable':nullable,'missing':missing,
                  'source':{'documentId':'d','revision':'r','module':'m','element':name}}
                 for name,kind,nullable,missing in (
                     ('visible','string',False,False),('secondKey','string',False,False),
                     ('hiddenLocal','local',True,True),('date','date',False,False),
                     ('firstKey','string',False,False))]
        key={'module':'m','record':'R','key':'alternate-composite'}
        slots=[{'field':outputs[p-1]['source'],'direction':direction,'nulls':nulls,'kind':outputs[p-1]['carrier'],
                'outputPosition':p} for p,direction,nulls in ((3,'desc','first'),(5,'asc','last'),(2,'asc','last'))]
        return {'outputs':outputs,'selectedKey':key,'page':{'version':'weft.engine-temporal-page/0.2','selectedKey':key,
                'visibleOutputPositions':[4,1],'keyOutputPositions':[5,2],'sort':slots}}

    def row(self,local=None):
        return ('visible','repeat',LocalTimestampValue(text='2000-02-29T00:00:00.000000') if local is None else local,
                TextValue(kind='date',text='2000-02-29'),'repeat')

    def test_hidden_noncontiguous_composite_key_and_full_sort_tuple(self):
        program=self.program();packet=_row_after(program,self.row())
        self.assertEqual(packet['keyValues'],['repeat','repeat'])
        self.assertEqual(packet['sortValues'],[{'state':'present','value':'2000-02-29T00:00:00.000000'},
            {'state':'present','value':'repeat'},{'state':'present','value':'repeat'}])
        self.assertEqual(_after(program,json.dumps(packet),expected_values=tuple(packet['sortValues'])),packet)
        self.assertEqual(_page_metadata(program)['visibleOutputPositions'],[4,1])

    def test_missing_and_null_stay_distinct_without_client_comparison(self):
        program=self.program()
        row=list(self.row());row[2]=None
        for value,state in ((QueryAbsent(),'missing'),(None,'null')):
            row[2]=value;packet=_row_after(program,tuple(row))
            self.assertEqual(packet['sortValues'][0],{'state':state})
            self.assertEqual(_after(program,json.dumps(packet))['sortValues'][0],{'state':state})

    def test_complete_token_tuple_agreement_and_key_correspondence(self):
        program=self.program();packet=_row_after(program,self.row())
        for fault in ('tuple','key','arity','extra','state','foreign','required-missing'):
            altered=copy.deepcopy(packet);expected=tuple(packet['sortValues'])
            if fault=='tuple':expected=expected[1:]
            elif fault=='key':altered['keyValues'][1]='different'
            elif fault=='arity':altered['sortValues'].pop()
            elif fault=='extra':altered['extra']=True
            elif fault=='state':altered['sortValues'][0]['extra']=True
            elif fault=='foreign':altered['selectedKey']={**altered['selectedKey'],'key':'foreign'}
            else:altered['sortValues'][1]={'state':'missing'}
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                _after(program,json.dumps(altered),expected_values=expected)

    def test_page_metadata_corruption_refuses_even_with_no_rows(self):
        for fault in ('bool','duplicates','range','hidden','kind','source','nullable-key','unknown-member'):
            program=self.program()
            if fault=='bool':program['page']['visibleOutputPositions']=[True]
            elif fault=='duplicates':program['page']['keyOutputPositions']=[5,5]
            elif fault=='range':program['page']['sort'][0]['outputPosition']=0
            elif fault=='hidden':program['page']['visibleOutputPositions']=[1]
            elif fault=='kind':program['page']['sort'][0]['kind']='date'
            elif fault=='source':program['page']['sort'][0]['field']={'foreign':True}
            elif fault=='nullable-key':program['outputs'][4]['nullable']=True
            else:program['page']['extra']=True
            with self.subTest(fault=fault),self.assertRaises(ValueError):_page_metadata(program)

    def test_raw_guarded_instant_is_not_host_canonicalized(self):
        program=self.program();program['outputs'][2]['carrier']='instant';program['page']['sort'][0]['kind']='instant'
        row=list(self.row());row[2]=TextValue(kind='timestamp',text='2000-01-01T01:00:00.1+01:00')
        self.assertEqual(_row_after(program,row)['sortValues'][0]['value'],'2000-01-01T01:00:00.1+01:00')
        # Native strict075 canonicalization precedes F6 validation/issuance;
        # this helper never claims calendar validity or parses opaque bytes.
