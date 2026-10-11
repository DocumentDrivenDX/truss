"""Native argument decoding only; does not invoke or qualify admission routines."""
import unittest
from dataclasses import replace
from test_native_pg8000 import NativeBoundaryFixture
from truss._native_admission_request import NativeAdmissionInput, encode_admission_request

class NativeAdmissionEncodingTests(NativeBoundaryFixture, unittest.TestCase):
    def test_four_family_argument_values_decode_exactly_in_postgresql(self):
        base = NativeAdmissionInput('base', 'catalog-acceptance', (bytes(range(256)),) * 6)
        for family in ('base', 'asserted', 'epoch', 'configuration'):
            fields = dict(family=family)
            expected = [9223372036854775807, base.kind, *base.artifacts]
            if family != 'base':
                fields.update(asserted=b'\x00\xff', capture_profile=b'\xffprofile')
                expected.extend((fields['asserted'], fields['capture_profile']))
            if family in ('epoch', 'configuration'):
                fields.update(installation="雪';--", source_epoch='é', incarnation='😀')
                expected.extend((fields['installation'], fields['source_epoch'], fields['incarnation']))
            if family == 'configuration':
                fields['configuration_profile'] = b'\x00configuration'
                expected.append(fields['configuration_profile'])
            packet = encode_admission_request(replace(base, **fields), '9223372036854775807')
            # Evaluate the exact argument expressions; no routine or authority fixture is installed.
            expressions = packet.sql.split('(', 1)[1][:-1]
            with self.subTest(family=family):
                self.assertEqual(self.boundary.run('SELECT ' + expressions), [expected])
