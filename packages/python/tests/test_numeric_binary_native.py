# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original numeric_send byte correspondence, not protected scalar admission."""
import struct
from test_numeric_witness_native import NumericWitnessNativeTests, ROOT

class NumericBinaryNativeTests(NumericWitnessNativeTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:c.run((ROOT/'packages/postgresql/native/row-image/numeric-binary-witness.sql').read_text())
        finally:c.close()
    def binary(self,raw):
        return self.connection.run('SELECT negative,digits,exponent::text FROM truss.numeric_binary_witness_original(:raw)',raw=raw)[0]
    def test_actual_native_numeric_send_correspondence(self):
        for token in ('0','-0.000','123.0000','-0.0000012300','9007199254740993',
                      '1000000000000000000000001','1e1000','1e-1000'):
            raw=bytes(self.connection.run('SELECT numeric_send(:token::numeric)',token=token)[0][0])
            self.assertEqual(self.binary(raw),self.witness(token))
    def test_invalid_native_frame_and_hidden_scale(self):
        from pg8000.exceptions import DatabaseError
        cases=[None,b'',struct.pack('!HhHH',1,0,0,0),struct.pack('!HhHHH',1,0,0,0,10000),
               struct.pack('!HhHHH',1,0,0,0,0),struct.pack('!HhHH',0,0,0xc000,0),
               struct.pack('!HhHH',0,0,0,16384),struct.pack('!HhHHH',1,-1,0,0,1)]
        for raw in cases:
            with self.subTest(raw=raw),self.assertRaises(DatabaseError) as caught:self.binary(raw)
            self.assertEqual(caught.exception.args[0]['C'],'22023')

    def test_exact_binary_boundary_and_group_profiles(self):
        from pg8000.exceptions import DatabaseError
        raw=struct.pack('!HhHH',16384,16383,0,0)+struct.pack('!H',1111)*16384
        result=self.binary(raw)
        self.assertEqual(result,[False,'1111'*16384,'0'])
        for invalid in (raw+b'\x00',struct.pack('!HhHH',16385,16384,0,0)+struct.pack('!H',1111)*16385,
                        struct.pack('!HhHHHH',2,0,0,0,1,0),struct.pack('!HhHHHH',2,0,0,0,0,1),
                        struct.pack('!HhHH',0,0,16384,0)):
            with self.assertRaises(DatabaseError) as caught:self.binary(invalid)
            self.assertEqual(caught.exception.args[0]['C'],'22023')
        self.assertEqual(self.binary(struct.pack('!HhHH',0,-32768,0,16383)),[False,'0','0'])
        self.assertEqual(self.binary(struct.pack('!HhHHH',1,-4096,0,16383,10)),[False,'1','-16383'])

    def test_source_binary_equality_and_native_special_refusal(self):
        from pg8000.exceptions import DatabaseError
        c=self.connection
        for source,native,expected in [('9007199254740993','9007199254740993',True),
                ('9007199254740993','9007199254740992',False),('1.2300e2','123.0000',True),
                ('-0.000','0.00',True),('-0.0012300','-0.00123',True)]:
            rows=c.run('SELECT truss.numeric_source_binary_equal_original(:source,numeric_send(:native::numeric))',source=source,native=native)
            self.assertEqual(rows,[[expected]])
        for native in ('NaN','Infinity','-Infinity'):
            with self.assertRaises(DatabaseError) as caught:
                c.run('SELECT truss.numeric_source_binary_equal_original(:source,numeric_send(:native::numeric))',source='0',native=native)
            self.assertEqual(caught.exception.args[0]['C'],'22023')

    def test_actual_numeric_send_group_limit_and_scale(self):
        from pg8000.exceptions import DatabaseError
        c=self.connection
        token='1111'*16384
        raw=bytes(c.run('SELECT numeric_send(:token::numeric)',token=token)[0][0])
        self.assertEqual(len(raw),32776)
        self.assertEqual(self.binary(raw),[False,token,'0'])
        larger=bytes(c.run('SELECT numeric_send(:token::numeric)',token=token+'1111')[0][0])
        with self.assertRaises(DatabaseError) as caught:self.binary(larger)
        self.assertEqual(caught.exception.args[0]['C'],'22023')
        for token,expected in [('1.2',[False,'12','-1']),('1.2300',[False,'123','-2']),
                               ('0',[False,'0','0']),('0.'+'0'*16383,[False,'0','0'])]:
            raw=bytes(c.run('SELECT numeric_send(:token::numeric)',token=token)[0][0])
            self.assertEqual(self.binary(raw),expected)
