# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native F8 structural components; not installed candidate acceptance/CRUD."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import unittest
import psycopg
from psycopg.types.json import Jsonb
from truss.preparation import CatalogDocument
from truss._temporal_preparation import inspection_packet, temporal_declarations
from test_temporal_canonical_text_native import TemporalCanonicalTextNativeTests, ROOT


class TemporalTransportComponentNativeTests(unittest.TestCase):
    cleanup_owned_runtime = classmethod(TemporalCanonicalTextNativeTests.cleanup_owned_runtime.__func__)

    @classmethod
    def setUpClass(cls):
        TemporalCanonicalTextNativeTests.setUpClass.__func__(cls)
        for filename in ('temporal-preparation.sql', 'temporal-cells.sql'):
            cls.connection.execute((ROOT / 'packages/python/src/truss/_catalog_runtime' / filename).read_text(), prepare=False)

    def packet(self):
        path = Path(__file__).parent / 'fixtures/temporal/complete-owner-inspection.json'
        raw = path.read_bytes()
        provenance = json.loads(path.with_name('complete-owner-inspection-provenance.json').read_bytes())
        self.assertEqual(sha256(raw).hexdigest(), provenance['resultSha256'])
        fixture = json.loads(raw)
        request = fixture['request']
        document = CatalogDocument('source-original', 'r1', json.dumps(request['document'], ensure_ascii=True).encode())
        packet = inspection_packet(document, selected=request['selected'], bindings=request['bindings'],
            source_id=request['sourceId'], owner_profile={'identity': 'DEV-canonical-source-inspection',
            'version': provenance['commit'], 'sha256': provenance['resultSha256']},
            result_bytes=json.dumps(fixture['result'], ensure_ascii=True).encode())
        declarations = [temporal_declarations(document, packet)]
        documents = [{'documentId': document.document_id, 'revision': document.document_revision,
                      'originalText': document.content.decode()}]
        summary = {'interfaceVersion': 'truss-registration-preparation/2.1', 'documents': [{
            'documentId': document.document_id, 'contentSha256': sha256(document.content).hexdigest(),
            'inspection': packet}]}
        return documents, declarations, summary

    def validate(self, documents, declarations, summary):
        self.connection.execute('SELECT truss.catalog_temporal_declarations_valid(%s,%s,%s)',
                                (Jsonb(documents), Jsonb(declarations), Jsonb(summary))).fetchone()

    def test_complete_original_owner_descriptor_inverse_correspondence(self):
        self.validate(*self.packet())

    def test_native_refuses_stripped_foreign_duplicate_or_relabelled_transport(self):
        for mutation in ('descriptor', 'owner-field', 'owner-record', 'hash', 'pointer', 'duplicate', 'core', 'summary', 'empty'):
            documents, declarations, summary = self.packet()
            local = declarations[0]['records'][0]['fields'][-1]
            packet = summary['documents'][0]['inspection']
            owner = json.loads(packet['resultJson'])
            if mutation == 'descriptor': del local['nativeDescriptor']
            elif mutation == 'owner-field': owner['records'][0]['fields'].pop()
            elif mutation == 'owner-record': owner['records'].pop()
            elif mutation == 'hash': packet['contentSha256'] = '0' * 64
            elif mutation == 'pointer': local['nativeDescriptor']['nativeTemporal']['source']['fieldViewPointer'] = '/modules/0'
            elif mutation == 'duplicate': declarations[0]['records'][0]['fields'].append(copy.deepcopy(local))
            elif mutation == 'core': local['declaration']['scalarType'] = 'localTimestamp'
            elif mutation == 'summary': summary['interfaceVersion'] = 'truss-registration-preparation/2.0'
            else: declarations = []
            if mutation in ('owner-field', 'owner-record'):
                packet['resultJson'] = json.dumps(owner)
                packet['resultSha256'] = sha256(packet['resultJson'].encode()).hexdigest()
            with self.subTest(mutation=mutation), self.assertRaises(psycopg.Error) as caught:
                self.validate(documents, declarations, summary)
            self.assertEqual(caught.exception.sqlstate, '22023')
        self.validate(*self.packet())

    def test_native_local_canonical_cell_and_nullable_state(self):
        for cell, allow_null, expected in (({'kind': 'localTimestamp', 'text': '2024-02-29T12:34:56.123456'}, False, True),
                ({'kind': 'localTimestamp', 'text': '2024-02-29T12:34:56.1'}, False, False),
                ({'kind': 'localTimestamp', 'text': '2024-02-29T12:34:56.0000000'}, False, False),
                ({'kind': 'localTimestamp', 'text': '2023-02-29T12:34:56.000000'}, False, False),
                ({'kind': 'timestamp', 'text': '2024-02-29T12:34:56.000000'}, False, False),
                ({'kind': 'null'}, False, False), ({'kind': 'null'}, True, True)):
            with self.subTest(cell=cell, allow_null=allow_null):
                actual = self.connection.execute('SELECT truss.valid_local_timestamp_cell(%s,%s)', (Jsonb(cell), allow_null)).fetchone()[0]
                self.assertEqual(actual, expected)
