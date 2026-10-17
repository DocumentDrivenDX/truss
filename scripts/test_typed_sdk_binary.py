"""Basic private conversion controls; no binary profile activation."""
import base64
import unittest
from types import SimpleNamespace
from pydantic import BaseModel,ConfigDict
from umf_access.types import MISSING
from truss.access import _binary_sdk_value,_typed_rows,_read_profile
from truss.contracts import TextValue
from truss.query import QueryRows,QueryAbsent

class BinaryRow(BaseModel):
    model_config=ConfigDict(strict=True)
    required:bytes
    optional:bytes|None|MISSING=MISSING
    label:str|None|MISSING=MISSING

class BinaryValueTests(unittest.TestCase):
    def test_exact_bytes_and_empty(self):
        for value in (b'',b'\x00\xff',bytes(range(256))):
            self.assertEqual(_binary_sdk_value(TextValue(kind='binary',text=base64.b64encode(value).decode())),value)
    def test_wrong_kind_and_noncanonical_text(self):
        for value in ('AP8=',TextValue(kind='string',text='AP8='),TextValue(kind='binary',text='AP9='),TextValue(kind='binary',text='AP8=\n'),TextValue(kind='binary',text='!!!!'),TextValue(kind='binary',text='AAAA'*(1048576//4+1))):
            with self.subTest(kind=type(value).__name__),self.assertRaises(ValueError):_binary_sdk_value(value)
    def test_explicit_profile_and_presence(self):
        entry=SimpleNamespace(result=BinaryRow)
        program={'compiler':'truss-runtime-binary','version':'weft.engine-read/0.2','outputs':[
            {'name':'required','carrier':'binary','nullable':False,'missing':False},
            {'name':'optional','carrier':'binary','nullable':True,'missing':True},
            {'name':'label','carrier':'string','nullable':True,'missing':True}]}
        columns=('required','optional','label');blob=TextValue(kind='binary',text='AP8=')
        rows=_typed_rows(entry,program,QueryRows(columns,((blob,QueryAbsent(),QueryAbsent()),(blob,None,None),(blob,TextValue(kind='binary',text=''),'label')),1))
        self.assertEqual(rows[0].required,b'\x00\xff');self.assertIs(rows[0].optional,MISSING);self.assertIs(rows[0].label,MISSING)
        self.assertIsNone(rows[1].optional);self.assertEqual(rows[2].optional,b'')
        for value in (QueryAbsent(),None,'AP8='):
            with self.subTest(value=type(value).__name__),self.assertRaises(ValueError):
                _typed_rows(entry,program,QueryRows(columns,((value,None,None),),1))
        with self.assertRaises(ValueError):_typed_rows(entry,program,QueryRows(('required','label','optional'),(),1))
        legacy={**program,'compiler':'truss-runtime','version':'weft.engine-read/0.1'}
        with self.assertRaises(ValueError):_typed_rows(entry,legacy,QueryRows(columns,((blob,QueryAbsent(),'label'),),1))
    def test_closed_compiler_version_pairs(self):
        for kind in ('read','page'):
            for compiler,version,expected in [('truss-runtime','0.1',True),('truss-runtime-binary','0.2',True),('truss-runtime','0.2',False),('truss-runtime-binary','0.1',False),('other','0.2',False)]:
                self.assertIs(_read_profile({'compiler':compiler,'version':'weft.engine-'+kind+'/'+version},kind),expected)
if __name__=='__main__':unittest.main()
