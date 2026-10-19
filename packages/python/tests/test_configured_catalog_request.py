# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original configured request encoding; no installed authority claim."""
import json
import unittest
from dataclasses import replace
from test_catalog_support import selected
from truss._native_catalog_request import (
    ConfiguredCatalogSelection, NativeCatalogStageInput, encode_catalog_stage)
from truss._native_pg8000 import NativeBoundaryRefusal


class ConfiguredCatalogRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared=selected()

    def request(self, **changes):
        selection=ConfiguredCatalogSelection("installed'identity", 'epoch', 'incarnation',
            b'capture-profile', b'configuration-profile')
        return replace(NativeCatalogStageInput(self.prepared, b'{"x-action":"register"}',
            b'definition', b'obligations', b'group', selection), **changes)

    def test_configured_selection_is_retained_and_encoded_without_text_interpolation(self):
        request=self.request()
        encoded=encode_catalog_stage(request, '0')
        self.assertIn('truss.runtime_stage_catalog_configured(', encoded.sql)
        self.assertNotIn(request.configuration.installation, encoded.sql)
        self.assertIn(request.configuration.installation.encode().hex(), encoded.sql)
        self.assertEqual(len(encoded.sql), encoded.encoded_bytes)
        retained=json.loads(encoded.original_configuration)
        self.assertEqual(retained['originHex'], request.origin.hex())
        self.assertEqual(retained['installation'], request.configuration.installation)
        self.assertEqual(retained['configurationProfileHex'], request.configuration.configuration_profile.hex())

    def test_only_none_selects_legacy_route(self):
        encoded=encode_catalog_stage(self.request(configuration=None), '0')
        self.assertIn('truss.runtime_stage_catalog_issued(', encoded.sql)
        self.assertIsNone(encoded.original_configuration)
        for selection in (False, {}, 'legacy'):
            with self.subTest(selection=selection), self.assertRaises(NativeBoundaryRefusal):
                encode_catalog_stage(self.request(configuration=selection), '0')

    def test_origin_type_refuses_before_configured_expansion(self):
        for origin in (None, {}, 'text', bytearray(b'{}'), b''):
            with self.subTest(origin=origin), self.assertRaises(NativeBoundaryRefusal):
                encode_catalog_stage(self.request(origin=origin), '0')

    def test_invalid_identity_profiles_and_known_context_overflow_refuse(self):
        selection=self.request().configuration
        for bad in (replace(selection, installation='\0'),
                    replace(selection, source_epoch='\ud800'),
                    replace(selection, incarnation='a'*1025),
                    replace(selection, incarnation='\u0001'*1024),
                    replace(selection, capture_profile=b''),
                    replace(selection, configuration_profile=bytearray(b'p')),
                    replace(selection, capture_profile=b'p'*1500)):
            with self.subTest(selection=bad), self.assertRaises(NativeBoundaryRefusal):
                encode_catalog_stage(self.request(configuration=bad), '0')

    def test_escaped_and_unicode_identities_preserve_exact_selection(self):
        selection=replace(self.request().configuration, installation='quoted"\\\u0001é',
                          source_epoch='紀元', incarnation='instance😀')
        encoded=encode_catalog_stage(self.request(configuration=selection), '0')
        retained=json.loads(encoded.original_configuration)
        self.assertEqual(retained['installation'], selection.installation)
        self.assertEqual(retained['sourceEpoch'], selection.source_epoch)
        self.assertEqual(retained['incarnation'], selection.incarnation)
        self.assertIn(selection.installation.encode().hex(), encoded.sql)
        self.assertEqual(len(encoded.sql), encoded.encoded_bytes)
