# SPDX-License-Identifier: MIT OR Apache-2.0
"""Bounded exact census chunk controls; synthetic cursor, no native authority."""
from types import SimpleNamespace
import unittest
from truss._psycopg_source_census import _decode_census

class Cursor:
    def __init__(self,rows,names=('ordinal','total_bytes','chunk_hex'),oid=25):
        self.description=[SimpleNamespace(name=n,type_code=oid) for n in names]
        self.rows=list(rows)
    def fetchmany(self,size):
        result=self.rows[:size];del self.rows[:size];return result

def chunks(raw):
    return [(str(i),str(len(raw)),raw[i*4096:(i+1)*4096].hex()) for i in range((len(raw)+4095)//4096)]

class CensusChunkTests(unittest.TestCase):
    def test_exact_boundaries_and_utf8_split(self):
        for raw in [b'a',b'a'*4096,b'a'*4097,b'a'*4095+'雪'.encode()]:
            self.assertEqual(_decode_census(Cursor(chunks(raw))),raw)
    def test_malformed_incomplete_and_overflow_never_return_prefix(self):
        rows=chunks(b'a'*4097)
        for bad in [[],[(None,None,None)],rows[:1],rows[1:],rows+[rows[-1]],
                    [('00','1','61')],[('0','01','61')],[('0','16777217','61')],
                    [('0','1','6A')],[('0','1','zz')],[('0','1','6100')],
                    [('0','1','ff')],[('0','1',61)],
                    [rows[0],('1','4098','6161')]]:
            with self.subTest(bad=bad[:1]),self.assertRaises((ValueError,UnicodeError)):
                _decode_census(Cursor(bad))
    def test_unknown_descriptors_refuse(self):
        for cursor in [Cursor(chunks(b'a'),names=('bad','total_bytes','chunk_hex')),Cursor(chunks(b'a'),oid=23)]:
            with self.assertRaises(ValueError):_decode_census(cursor)

if __name__=='__main__':unittest.main()
