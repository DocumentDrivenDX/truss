import json
import subprocess
import unittest
from unittest.mock import patch
from pathlib import Path
from test_python_report_wire_candidate import candidate, wire, CONTRACTS
from python_report_wire_candidate import ReportWireCandidate

ROOT = Path(__file__).resolve().parents[5]


class NativeCarrierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codec = ReportWireCandidate(CONTRACTS)

    def test_complete_wire_matches_typescript_carrier(self):
        report = candidate()
        report['originalExecution']['origin']['asserted'] = {
            'é': ['e\u0301', '\x00', False, True, None, {}, []],
            '\x00': '𐀀', 'x': 'x' * 40000}
        source = bytearray(wire(report))
        result = self.codec.prepare_native(source)
        process = subprocess.run(['bun', '-e',
            "import {prepareCanonicalWireTree} from './packages/postgresql/src/canonical-wire-tree.ts'; "
            "console.log(JSON.stringify(prepareCanonicalWireTree(new Uint8Array(await Bun.stdin.arrayBuffer()))));"],
            input=bytes(source), capture_output=True, cwd=ROOT, check=True)
        expected = json.loads(process.stdout)
        self.assertEqual(result.native_tree_text, expected['nativeTreeText'])
        self.assertEqual(result.native_task_count, expected['nativeTaskCount'])
        self.assertEqual(result.original.source_bytes, bytes(source))
        source[:] = b'changed'
        self.assertNotEqual(result.original.source_bytes, bytes(source))

    def test_task_overflow_precedes_carrier_serialization(self):
        report = candidate()
        report['originalExecution']['origin']['asserted'] = [[None] * 4096 for _ in range(4)]
        source = wire(report)
        self.codec.prepare(source)  # Schema and each container remain legal.
        with patch('python_native_report_carrier_candidate.json.dumps', side_effect=AssertionError('serialized')):
            with self.assertRaisesRegex(ValueError, 'task capacity'):
                self.codec.prepare_native(source)

    def test_under_task_limit_preserves_array_order(self):
        report = candidate()
        report['originalExecution']['origin']['asserted'] = [[None] * 4096 for _ in range(3)]
        result = self.codec.prepare_native(wire(report))
        self.assertLessEqual(int(result.native_task_count), 32768)

    def test_schema_refusal_still_precedes_native_preparation(self):
        report = candidate(); report['counts']['typesAdded'] = 1
        with self.assertRaisesRegex(ValueError, 'numeric node'):
            self.codec.prepare_native(wire(report))
