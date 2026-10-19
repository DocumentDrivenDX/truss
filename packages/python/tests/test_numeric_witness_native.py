# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native mathematical witnesses; not original codec/facet admission."""
import json
import unittest
from pathlib import Path
from test_native_pg8000 import NativeBoundaryFixture
ROOT=Path(__file__).resolve().parents[3]

class NumericWitnessNativeTests(NativeBoundaryFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:
            c.run('CREATE SCHEMA truss')
            c.run((ROOT/'packages/postgresql/native/row-image/numeric-witness.sql').read_text())
        finally:c.close()
    def setUp(self):self.connection=self.Connection(**self.kwargs)
    def tearDown(self):self.connection.close()
    def witness(self,token):
        return self.connection.run('SELECT negative,digits,exponent::text FROM truss.numeric_witness_original(:token)',token=token)[0]
    def test_authored_witnesses_and_equality_pairs(self):
        corpus=json.loads((ROOT/'docs/helix/02-design/contracts/bindings/numeric-correspondence-v0.1.vectors.json').read_text())
        actual=[]
        for item in corpus['vectors']:
            result=self.witness(item['token']);actual.append(result)
            self.assertEqual(result,[item['negative'],item['digits'],item['exponent']])
        for pair in corpus['pairs']:
            self.assertEqual(actual[pair['left']]==actual[pair['right']],pair['mathematicallyEqual'])
            self.assertEqual(self.connection.run('SELECT truss.numeric_equal_original(:a,:b)',
                a=corpus['vectors'][pair['left']]['token'],b=corpus['vectors'][pair['right']]['token']),[[pair['mathematicallyEqual']]])
    def test_invalid_complete_tokens_and_zero_overflow(self):
        from pg8000.exceptions import DatabaseError
        for token,code in [(None,'22023'),('','22023'),('1\n','22023'),('+1','22023'),
                ('01','22023'),('NaN','22023'),('0e9223372036854775808','54000'),
                ('1.1e-9223372036854775808','54000'),('10e9223372036854775807','54000'),('1'*65537,'22023')]:
            with self.subTest(token=str(token)[:80]),self.assertRaises(DatabaseError) as caught:self.witness(token)
            self.assertEqual(caught.exception.args[0]['C'],code)
    def test_exact_boundaries_and_leading_exponent_zeros(self):
        self.assertEqual(self.witness('1e-9223372036854775808'),[False,'1','-9223372036854775808'])
        self.assertEqual(self.witness('1e9223372036854775807'),[False,'1','9223372036854775807'])
        self.assertEqual(self.witness('-0.000e+000000001'),[False,'0','0'])
        self.assertEqual(self.witness('1e'+'0'*1000+'2'),[False,'1','2'])

    def test_full_grammar_and_both_operand_validation(self):
        from pg8000.exceptions import DatabaseError
        invalid=['1 ',' 1','1\t','1\r','1\\n','1_0','1e','1e+','1.','.1',
                 '--1','1e1e1','\u0661','-01','Infinity','-Infinity','0e-9223372036854775809']
        for token in invalid:
            for left,right in [('0',token),(token,'0')]:
                with self.subTest(token=token,left=left),self.assertRaises(DatabaseError) as caught:
                    self.connection.run('SELECT truss.numeric_equal_original(:a,:b)',a=left,b=right)
                self.assertEqual(caught.exception.args[0]['C'],'54000' if token.endswith('5809') else '22023')

    def test_exact_token_limit_and_net_adjustment(self):
        token='1'*65536
        self.assertEqual(self.witness(token),[False,token,'0'])
        self.assertEqual(self.witness('1.0e-9223372036854775808'),[False,'1','-9223372036854775808'])
        self.assertEqual(self.witness('1.00e9223372036854775807'),[False,'1','9223372036854775807'])

    def test_original_spelling_is_preserved_independently(self):
        c=self.connection;c.run('CREATE TEMP TABLE original_numeric(token text,original bytea)')
        tokens=['-0.000e+000000001','1.2300e2','9007199254740993.000']
        for token in tokens:
            c.run('INSERT INTO original_numeric VALUES(:token,:original)',token=token,original=token.encode())
        rows=c.run('SELECT token,original,negative,digits,exponent::text FROM original_numeric CROSS JOIN LATERAL truss.numeric_witness_original(token)')
        self.assertEqual([(r[0],bytes(r[1])) for r in rows],[(t,t.encode()) for t in tokens])
        self.assertEqual(rows[0][2:],[False,'0','0'])
