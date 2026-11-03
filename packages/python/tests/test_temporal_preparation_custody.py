# SPDX-License-Identifier: MIT OR Apache-2.0
"""F8 transport component using exact DEV owner inspection fixtures."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from truss.preparation import CatalogDocument
from truss._temporal_preparation import inspection_packet, temporal_declarations, validate_temporal_declarations

FIXTURES = Path(__file__).parent / 'fixtures/temporal'


class TemporalPreparationCustodyTests(unittest.TestCase):
    def setUp(self):
        raw = (FIXTURES / 'access-inspection-cases.json').read_bytes()
        provenance = json.loads((FIXTURES / 'access-inspection-provenance.json').read_bytes())
        self.assertEqual(sha256(raw).hexdigest(), provenance['sha256'])
        self.case = next(c for c in json.loads(raw)['cases'] if c['id'] == 'date-instant-local')
        request = self.case['request']
        content = json.dumps(request['document'], ensure_ascii=True).encode()
        self.document = CatalogDocument('original-document', 'original-revision', content)
        self.packet = inspection_packet(self.document, selected=request['selected'],
            bindings=request.get('bindings', []), source_id=request.get('sourceId', 'logical'),
            owner_profile={'identity': 'DEV-umf-codegen-exact-source-fixture', 'version': provenance['commit'],
                           'sha256': provenance['sha256']},
            result_bytes=json.dumps(self.case['expected'], ensure_ascii=True).encode())

    def test_original_declaration_and_complete_owner_result_retained(self):
        declarations = temporal_declarations(self.document, self.packet)
        local = declarations['records'][0]['fields'][-1]
        self.assertEqual(local['declaration']['scalarType'], 'timestamp')
        self.assertEqual(local['nativeDescriptor']['nativeScalarType'], 'localTimestamp')
        self.assertEqual(local['nativeDescriptor']['nativeTemporal']['source']['fieldViewPointer'],
                         '/modules/0/extensions/umf.access/views/0/fields/6')
        self.assertEqual(json.loads(self.packet['resultJson']), self.case['expected'])
        self.assertEqual(sum('nativeDescriptor' in f for r in declarations['records'] for f in r['fields']), 1)
        validate_temporal_declarations(self.document, self.packet, declarations)

    def test_stripped_changed_or_duplicate_descriptor_refuses(self):
        original = temporal_declarations(self.document, self.packet)
        for mutation in ('stripped', 'hash', 'pointer', 'ref', 'duplicate', 'core-relabel'):
            changed = copy.deepcopy(original)
            fields = changed['records'][0]['fields']
            descriptor = fields[-1]['nativeDescriptor']
            if mutation == 'stripped': del fields[-1]['nativeDescriptor']
            elif mutation == 'hash': descriptor['nativeTemporal']['source']['sha256'] = '0' * 64
            elif mutation == 'pointer': descriptor['nativeTemporal']['source']['fieldViewPointer'] = '/modules/0'
            elif mutation == 'ref': descriptor['nativeTemporal']['source']['field']['element'] = 'foreign'
            elif mutation == 'duplicate': fields.append(copy.deepcopy(fields[-1]))
            else: fields[-1]['declaration']['scalarType'] = 'localTimestamp'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_temporal_declarations(self.document, self.packet, changed)

    def test_changed_original_pin_or_owner_result_refuses(self):
        for mutation in ('revision', 'contentSha256', 'resultSha256', 'resultJson'):
            changed = copy.deepcopy(self.packet)
            changed[mutation] = 'changed'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                temporal_declarations(self.document, changed)

    def test_removed_duplicate_foreign_or_reordered_owner_members_refuse(self):
        for mutation in ('remove-record', 'remove-field', 'duplicate-field', 'foreign-ref', 'foreign-pointer', 'order', 'error'):
            changed = copy.deepcopy(self.packet)
            owner = json.loads(changed['resultJson'])
            fields = owner['records'][0]['fields']
            if mutation == 'remove-record': owner['records'] = []
            elif mutation == 'remove-field': fields.pop()
            elif mutation == 'duplicate-field': fields.append(copy.deepcopy(fields[-1]))
            elif mutation == 'foreign-ref': fields[-1]['ref']['element'] = 'foreign'
            elif mutation == 'foreign-pointer': fields[-1]['viewPointer'] = fields[0]['viewPointer']
            elif mutation == 'order': fields.reverse()
            else: owner['diagnostics'].append({'severity': 'error', 'code': 'owner-refusal'})
            changed['resultJson'] = json.dumps(owner)
            changed['resultSha256'] = sha256(changed['resultJson'].encode()).hexdigest()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                temporal_declarations(self.document, changed)

    def test_unknown_owner_content_and_diagnostics_are_not_discarded(self):
        owner = copy.deepcopy(self.case['expected'])
        owner['future-owner-content'] = {'retain': ['original']}
        owner['diagnostics'].append({'severity': 'warning', 'code': 'retained-warning', 'unknown': {'original': True}})
        raw = json.dumps(owner, indent=3).encode()
        packet = inspection_packet(self.document, selected=self.packet['selected'], bindings=[],
            source_id='logical', owner_profile=self.packet['ownerProfile'], result_bytes=raw)
        self.assertEqual(packet['resultJson'].encode(), raw)
        self.assertEqual(json.loads(packet['resultJson']), owner)

    def test_genuine_preparation_retains_noncompact21_and_durable_originals(self):
        from truss import prepare_catalog
        from truss._temporal_preparation import retain_temporal_preparation, support_profile
        from truss._catalog_source_reference import compact_catalog_sources, catalog_source_artifact
        raw = (FIXTURES / 'complete-owner-inspection.json').read_bytes()
        provenance = json.loads((FIXTURES / 'complete-owner-inspection-provenance.json').read_bytes())
        self.assertEqual(sha256(raw).hexdigest(), provenance['resultSha256'])
        case = json.loads(raw)
        request = case['request']
        source = request['document']
        document = CatalogDocument(source['id'], 'r-original', json.dumps(source, ensure_ascii=True).encode())
        ordinary = prepare_catalog((document,))
        packet = inspection_packet(document, selected=request['selected'], bindings=request['bindings'],
            source_id=request['sourceId'], owner_profile={'identity': 'DEV-canonical-source-inspector',
            'version': provenance['commit'], 'sha256': provenance['sourceFiles']['src/compilation/admission/access/index.ts']},
            result_bytes=json.dumps(case['result'], ensure_ascii=True).encode())
        temporal = retain_temporal_preparation(ordinary, (packet,))
        self.assertEqual(temporal.input()['supportProfile'], support_profile())
        from truss._catalog_support import evaluate_catalog_support
        from truss._catalog_report_semantics import compose_original_catalog_report_semantics
        support=evaluate_catalog_support(temporal)
        self.assertEqual(support['state'],'evaluated')
        self.assertEqual(compose_original_catalog_report_semantics(temporal,support)['sourceFormat'],'truss-registration-summary/2.1')
        self.assertTrue(compact_catalog_sources(ordinary))
        self.assertFalse(compact_catalog_sources(temporal))
        self.assertEqual(catalog_source_artifact(temporal, document.document_id),
                         temporal.input()['documents'][0]['artifact'])
        self.assertEqual(temporal.documents[0].document.content, document.content)
        self.assertEqual(temporal.documents[0].observation()['inspection'], packet)
        self.assertEqual(json.loads(temporal.archive_documents_bytes)[0]['validation']['inspection'], packet)
        declarations = json.loads(temporal.declarations_bytes)
        validate_temporal_declarations(document, packet, declarations[0])
        self.assertEqual(json.loads(temporal.report_evidence_bytes)['interfaceVersion'], 'truss-registration-preparation/2.1')
        self.assertEqual(json.loads(ordinary.report_evidence_bytes)['interfaceVersion'], 'truss-registration-preparation/2.0')
        with self.assertRaises(ValueError): retain_temporal_preparation(temporal, (packet,))
        with self.assertRaises(ValueError): retain_temporal_preparation(ordinary, ())
