import unittest
from pathlib import Path
import re
from truss._operation_registry import COLUMNS, decode_operation_registry


class OperationRegistryTests(unittest.TestCase):
    def row(self, phase='admitted', ordinal='0'):
        bits={'admitted':(None,None,None,None),'effects_ready':('7',None,None,None),
              'row_sealed':('7','7',None,None),'application_finalized':('7','7','7','ff')}
        a,b,c,result=bits[phase]
        return ['18446744073709551615',ordinal,'mutation',phase,'7',a,b,c]+['00']*7+[result]

    def decode(self, rows, **options):
        args=dict(actual_xid='18446744073709551615',columns=COLUMNS,rows=rows,command='SELECT',
                  affected_rows=str(len(rows)),maximum_rows=10,maximum_bytes=4096)
        args.update(options)
        return decode_operation_registry(**args)

    def test_all_phases_and_full_unordered_surviving_multiset(self):
        rows=[self.row(p,str(i)) for i,p in enumerate(('application_finalized','admitted','row_sealed','effects_ready'))]
        decoded=self.decode(rows)
        self.assertEqual(decoded,tuple(tuple(r) for r in rows))
        rows[0][8]='ff'; self.assertEqual(decoded[0][8],'00')
        self.assertEqual(self.decode([]),())

    def test_independent_numeric_null_phase_and_carrier_refusals(self):
        mutations=[(0,'1'),(1,'01'),(1,'9223372036854775808'),(1,True),(2,'unknown'),(3,'unknown'),
                   (4,'-1'),(5,'7'),(8,None),(8,''),(8,'0'),(8,'AA'),(8,'zz'),(8,'é'),(8,'🙂'),(8,'\ud800'),(15,'00')]
        for column,value in mutations:
            row=self.row();row[column]=value
            with self.subTest(column=column,value=value):
                with self.assertRaises(ValueError): self.decode([row])
        row=self.row('application_finalized');row[7]='6'
        with self.assertRaises(ValueError): self.decode([row])
        with self.assertRaises(ValueError): self.decode([self.row(),self.row()])

    def test_original_descriptor_completion_and_exact_byte_bounds(self):
        source=Path(__file__).resolve().parents[3]/'docs/helix/02-design/contracts/row-operation-registry-observation-v0.1.proposal.sql'
        self.assertEqual(COLUMNS,tuple(re.findall(r'\bAS ([a-z_]+)',source.read_text().split('FROM truss.row_home_operation')[0])[1:]))
        row=self.row(); exact=sum(len(v.encode()) for v in row if v is not None)
        self.assertEqual(self.decode([row],maximum_bytes=exact),(tuple(row),))
        for options in ({'maximum_bytes':exact-1},{'maximum_rows':0},{'maximum_bytes':True},
                        {'actual_xid':None},{'columns':COLUMNS[::-1]},{'affected_rows':'0'},{'command':'UPDATE'}):
            with self.assertRaises(ValueError): self.decode([row],**options)
