# SPDX-License-Identifier: MIT OR Apache-2.0
"""Python handoff parity with the original TypeScript and native codecs."""
import json
import subprocess
import unittest
from pathlib import Path
from truss._canonical_wire_tree import prepare_canonical_wire_tree
from truss._catalog_report_semantics import canonical_numeric_free
from test_native_pg8000 import NativeBoundaryFixture
ROOT=Path(__file__).resolve().parents[3]
VECTORS=(b'null',b'false',b'[]',b'{"b":"line\\n\\u0000","a":true}',
         '{"😀":"é","\ue000":"𐀀","a":[null,false,"\\\""]}'.encode(),
         b'{"10":"ten","2":"two","01":"one","4294967295":"max","0":"zero"}',
         json.dumps({'9'*5000:'long numeric-looking key','2':'index'},separators=(',',':')).encode())

class CanonicalWireTreeTests(unittest.TestCase):
    def test_original_typescript_handoff_parity(self):
        for wire in VECTORS:
            with self.subTest(wire=wire):
                result=prepare_canonical_wire_tree(wire)
                owner=subprocess.run(['/opt/homebrew/bin/bun',str(ROOT/'packages/python/tests/tools/canonical-wire-tree.ts')],
                    input=wire,capture_output=True,check=True)
                expected=json.loads(owner.stdout)
                self.assertEqual(result.original_utf8_hex,expected['originalUtf8Hex'])
                self.assertEqual(result.native_tree_text,expected['nativeTreeText'])
                self.assertEqual(result.native_task_count,expected['nativeTaskCount'])
                self.assertEqual(result.scope,expected['scope'])
    def test_numbers_duplicates_and_nonoriginal_bytes_refuse(self):
        for wire in (b'1',b'{"a":null,"a":true}',b'"\\ud800"',bytearray(b'null')):
            with self.subTest(wire=wire):
                with self.assertRaises(ValueError):prepare_canonical_wire_tree(wire)

class NativeCanonicalWireTreeTests(NativeBoundaryFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:
            c.run('CREATE SCHEMA truss')
            for name in ('canonical-string-bytes','canonical-tree-bytes'):
                c.run((ROOT/f'packages/postgresql/native/{name}.sql').read_text())
        finally:c.close()
    def test_independent_native_canonical_bytes(self):
        for wire in VECTORS:
            result=prepare_canonical_wire_tree(wire)
            expected=canonical_numeric_free(json.loads(wire))
            actual=self.connection.run("SELECT encode(truss.runtime_canonical_tree_bytes(CAST(:tree AS jsonb)),'hex')",
                tree=result.native_tree_text)[0][0]
            self.assertEqual(bytes.fromhex(actual),expected)
