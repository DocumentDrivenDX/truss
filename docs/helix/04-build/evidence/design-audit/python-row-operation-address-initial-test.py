from dataclasses import FrozenInstanceError
import json
import unittest
from truss._row_operation_address import encode_row_operation_address as encode, decode_row_operation_address as decode, check_custody_addresses
from truss._row_operation_custody import decode_row_operation_custody
from test_row_operation_custody import fixture


class RowOperationAddressTests(unittest.TestCase):
    def test_exact_native_domains_and_scalar_spelling(self):
        original = encode('é"\\\n', '18446744073709551615', '9223372036854775807')
        self.assertEqual(original, b'["truss-row-operation-address/0.1.0","\xc3\xa9\\"\\\\\\n","18446744073709551615","9223372036854775807"]')
        address = decode(original)
        self.assertIs(address.original, original)
        with self.assertRaises(FrozenInstanceError): address.writer_xid = '1'

    def test_noncanonical_and_foreign_address_refusals(self):
        original = encode('installation', '7', '11')
        for raw in (original+b'\n', b' '+original, original.replace(b',', b', '),
                    original.replace(b'/0.1.0', b'/0.2.0'), original.replace(b'"7"', b'"07"'),
                    original.replace(b'"7"', b'7'), original[:-1]+b',"extra"]'):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError): decode(raw)
        for xid, ordinal in [('18446744073709551616','0'),('1','9223372036854775808'),('1','-1'),(True,'0')]:
            with self.assertRaises(ValueError): encode('installation', xid, ordinal)

    def test_complete_manifest_addresses_keep_native_gaps(self):
        value = fixture()
        for operation, ordinal in zip(value['operations'], ['7','11']):
            token = encode('installation','42',ordinal).decode()
            operation['operationIdentity'] = token
            operation['nativeGroupCustodyIdentity'] = token
        body = decode_row_operation_custody(json.dumps(value).encode())
        addresses = check_custody_addresses(body,'installation','42')
        self.assertEqual([a.operation_ordinal for a in addresses], ['7','11'])
        self.assertEqual([o.ordinal for o in body.operations], ['0','1'])
        for installation, xid in [('foreign','42'),('installation','43')]:
            with self.assertRaises(ValueError): check_custody_addresses(body,installation,xid)
        value['operations'][1]['nativeGroupCustodyIdentity'] = encode('installation','42','12').decode()
        with self.assertRaises(ValueError): check_custody_addresses(decode_row_operation_custody(json.dumps(value).encode()),'installation','42')


if __name__ == '__main__': unittest.main()
