import unittest
from dataclasses import replace
from truss._native_admission_request import NativeAdmissionInput, encode_admission_request
from truss._operation_admission import AdmissionRefusal

class NativeAdmissionRequestTests(unittest.TestCase):
    def setUp(self):
        self.base = NativeAdmissionInput('base', 'catalog-acceptance', (bytes(range(256)),) * 6)

    def test_binary_octets_and_text_are_lossless(self):
        result = encode_admission_request(self.base, '0')
        self.assertIs(result.original_input, self.base)
        self.assertEqual(result.sql.count(bytes(range(256)).hex()), 6)
        self.assertIn(self.base.kind.encode('utf8').hex(), result.sql)
        self.assertEqual(result.encoded_bytes, len(result.sql.encode('ascii')))

    def test_all_closed_families_and_bigint_maximum(self):
        for family in ('asserted', 'epoch', 'configuration'):
            fields = dict(family=family, asserted=b'\0\xff', capture_profile=b'p')
            if family in ('epoch', 'configuration'):
                fields.update(installation='雪', source_epoch='e', incarnation='c')
            if family == 'configuration': fields['configuration_profile'] = b'cfg'
            value = replace(self.base, **fields)
            result = encode_admission_request(value, '9223372036854775807')
            self.assertIn('9223372036854775807::pg_catalog.int8', result.sql)
            if family in ('epoch', 'configuration'): self.assertIn('雪'.encode('utf8').hex(), result.sql)

    def test_wrong_family_missing_extra_and_invalid_ordinal_refuse(self):
        for value in (replace(self.base, family='asserted'), replace(self.base, asserted=b'x'),
                      replace(self.base, incarnation='x'), replace(self.base, configuration_profile=b'x'),
                      replace(self.base, family='arbitrary'), replace(self.base, kind='a\0b'),
                      replace(self.base, kind='\ud800')):
            with self.subTest(value=value), self.assertRaises(AdmissionRefusal):
                encode_admission_request(value, '0')
        for ordinal in ('00', '-1', '1; SELECT 1', '9223372036854775808', True, 0):
            with self.subTest(ordinal=ordinal), self.assertRaises(AdmissionRefusal):
                encode_admission_request(self.base, ordinal)

    def test_encoding_budget_exact_boundary_and_expansion(self):
        result = encode_admission_request(self.base, '0')
        self.assertEqual(encode_admission_request(self.base, '0', maximum_sql_bytes=result.encoded_bytes), result)
        with self.assertRaises(AdmissionRefusal):
            encode_admission_request(self.base, '0', maximum_sql_bytes=result.encoded_bytes-1)
        with self.assertRaises(AdmissionRefusal):
            encode_admission_request(replace(self.base, artifacts=(b'x'*100000,)*6), '0')

    def test_hostile_inputs_are_never_interpreted(self):
        class Hostile:
            def __getattr__(self, name): raise AssertionError('foreign input access')
        with self.assertRaises(AdmissionRefusal): encode_admission_request(Hostile(), '0')
        with self.assertRaises(AdmissionRefusal): encode_admission_request(replace(self.base, artifacts=(Hostile(),)*6), '0')

    def test_native_kind_set_is_closed(self):
        for kind in ('mutation', 'import', 'catalog-transform', 'catalog-acceptance',
                     'home-migration', 'administrative-repair'):
            encode_admission_request(replace(self.base, kind=kind), '0')
        for kind in ('accept 雪', 'Mutation', '', 'mutation; SELECT 1'):
            with self.assertRaises(AdmissionRefusal):
                encode_admission_request(replace(self.base, kind=kind), '0')

    def test_asserted_inputs_share_native_aggregate_bound(self):
        artifacts = (b'x'*1048576,) * 3 + (b'x'*(1048576-4), b'x', b'x')
        for family in ('asserted', 'epoch', 'configuration'):
            fields = dict(family=family, artifacts=artifacts, asserted=b'a', capture_profile=b'p')
            if family in ('epoch', 'configuration'):
                fields.update(installation='i', source_epoch='e', incarnation='c')
            if family == 'configuration': fields['configuration_profile'] = b'x'*65536
            value = replace(self.base, **fields)
            encode_admission_request(value, '0', maximum_sql_bytes=16777216)
            with self.assertRaisesRegex(AdmissionRefusal, 'Aggregate original admission'):
                encode_admission_request(replace(value, asserted=b'aa'), '0', maximum_sql_bytes=16777216)
