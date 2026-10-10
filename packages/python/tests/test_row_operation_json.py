"""Custody syntax profile controls; no native registry or semantic admission."""
import unittest
from truss._acceptance_json import (
    AcceptanceJsonError, decode_acceptance_json, decode_row_operation_json,
)


class RowOperationJsonTests(unittest.TestCase):
    def test_full_eight_mib_syntax_ceiling_and_original_bytes(self):
        original = b'"' + b'a' * (8_388_608 - 2) + b'"'
        result = decode_row_operation_json(original)
        self.assertEqual(len(result), 8_388_608 - 2)
        self.assertEqual(result[:1], 'a')
        self.assertEqual(result[-1:], 'a')
        self.assertEqual(original[:1], b'"')
        with self.assertRaises(AcceptanceJsonError) as caught:
            decode_row_operation_json(original + b' ')
        self.assertEqual(caught.exception.reason, 'resource')

    def test_larger_profile_does_not_widen_acceptance(self):
        original = b'"' + b'a' * 1_048_576 + b'"'
        self.assertEqual(len(decode_row_operation_json(original)), 1_048_576)
        with self.assertRaises(AcceptanceJsonError) as caught:
            decode_acceptance_json(original)
        self.assertEqual(caught.exception.reason, 'resource')

    def test_complete_ordered_syntax_does_not_rewrite_native_identity(self):
        original = b'{ "operations": [ {"ordinal":"0","operationIdentity":"native-7"}, {"ordinal":"1","operationIdentity":"native-11"} ] }'
        result = decode_row_operation_json(original)
        self.assertEqual(result['operations'], [
            {'ordinal': '0', 'operationIdentity': 'native-7'},
            {'ordinal': '1', 'operationIdentity': 'native-11'},
        ])
        # This incomplete body is valid syntax only, never semantic admission.
        self.assertEqual(original[:2], b'{ ')

    def test_strict_grammar_remains_shared(self):
        for original in (b'{"a":1}', b'{"a":NaN}', b'{"a":null,"a":null}',
                         b'"\\ud800"', b'"\xff"', b'{} trailing'):
            for decoder in (decode_acceptance_json, decode_row_operation_json):
                with self.subTest(original=original, decoder=decoder.__name__):
                    with self.assertRaises(AcceptanceJsonError):
                        decoder(original)

    def test_array_bound_and_immutable_byte_input(self):
        self.assertEqual(len(decode_row_operation_json(b'[' + b','.join([b'null'] * 4096) + b']')), 4096)
        for original in (b'[' + b','.join([b'null'] * 4097) + b']', bytearray(b'{}'), memoryview(b'{}')):
            with self.subTest(type=type(original)):
                with self.assertRaises(AcceptanceJsonError):
                    decode_row_operation_json(original)


if __name__ == '__main__':
    unittest.main()
