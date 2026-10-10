import copy,json,unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from truss._row_touch_registry import COLUMNS,decode_touch_registry

ROOT=Path(__file__).resolve().parents[3]
RECEIPT=ROOT/'docs/helix/04-build/evidence/design-audit/touch-transition-descriptor-native.json'

def vectors():
    data=json.loads(RECEIPT.read_text())
    return [c['rows'][0] for c in data['originalCaptures'] if tuple(c['columns'])==COLUMNS and c['rows']]

def decode(rows,**overrides):
    args=dict(installation='fixture',actual_xid=rows[0][0] if rows else '123',columns=COLUMNS,
              rows=rows,command='SELECT',affected_rows=str(len(rows)),maximum_rows=10,maximum_bytes=100000)
    args.update(overrides);return decode_touch_registry(**args)

class TouchRegistryTests(unittest.TestCase):
    def test_original_native_vectors_full_cells_and_immutable_custody(self):
        original=vectors();self.assertEqual(len(original),4)
        for row in original:
            result=decode([row])[0];self.assertEqual(result.cells,tuple(row))
            self.assertEqual(result.custody.original.hex(),row[11])
            with self.assertRaises(FrozenInstanceError):result.cells=()
            changed=copy.deepcopy(row);changed[6]='999';self.assertNotEqual(result.cells[6],changed[6])
    def test_seal_history_signed_native_identity_and_duplicate_multiset(self):
        row=copy.deepcopy(vectors()[0]);row[6:8]=['2','1']
        for index,value in [(2,'-9223372036854775808'),(3,'-2147483648'),(4,'0'),(5,'2147483647')]:row[index]=value
        self.assertEqual(decode([row])[0].cells,tuple(row))
        with self.assertRaises(ValueError):decode([row,row])
        other=copy.deepcopy(row);other[1]='edge';self.assertEqual(len(decode([row,other])),2)
    def test_native_and_original_custody_corruptions_refuse(self):
        base=vectors()[0]
        for index,values in {0:['0'],1:['unknown'],2:['-0','01','9223372036854775808'],3:['2147483648'],6:['0','01','9223372036854775808'],7:['0','2'],8:['ff','FF','0',''],9:['ff'],10:['ff'],11:['ff']}.items():
            for value in values:
                row=copy.deepcopy(base);row[index]=value
                with self.subTest(index=index,value=value),self.assertRaises(ValueError):decode([row],actual_xid=base[0])
        with self.assertRaises(ValueError):decode([base],installation='foreign')
        row=copy.deepcopy(base);row[5]=None
        with self.assertRaises(ValueError):decode([row])
    def test_exact_logical_bounds_and_complete_descriptor_completion(self):
        row=vectors()[0];size=sum(len(v) for v in row if v is not None)
        self.assertEqual(len(decode([row],maximum_rows=1,maximum_bytes=size)),1)
        for options in [dict(maximum_rows=0),dict(maximum_bytes=size-1),dict(maximum_rows=True),dict(maximum_bytes=1.0),dict(columns=COLUMNS[::-1]),dict(command='UPDATE'),dict(affected_rows='0'),dict(affected_rows=1)]:
            with self.subTest(options=options),self.assertRaises(ValueError):decode([row],**options)
        self.assertEqual(decode([]),())
