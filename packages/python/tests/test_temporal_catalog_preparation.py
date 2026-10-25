# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure PWS03 proof that local storage derives only from UMF owner inspection."""
import json
from hashlib import sha256
from pathlib import Path
import unittest

from truss._catalog_source_reference import TEMPORAL_PROFILE
from truss._catalog_support import evaluate_catalog_support
from truss.preparation import CatalogDocument, PreparationRejected
from truss.catalog_preparation import prepare_catalog
from truss.catalog_runtime import _catalog_preparation_matches_current


FIXTURE = Path(__file__).parent / 'fixtures' / 'pws03-local-timestamp-access.json'


class TemporalCatalogPreparationTests(unittest.TestCase):
    def setUp(self):
        self.content = FIXTURE.read_bytes()
        self.source = json.loads(self.content)
        self.document = CatalogDocument(self.source['id'], 'fixture-r1', self.content)

    def test_owner_inspection_derives_distinct_local_family(self):
        prepared = prepare_catalog((self.document,), support_profile=TEMPORAL_PROFILE)
        # This is the exact profile/configuration gate called by public
        # accept_in_transaction before native effects.
        self.assertTrue(_catalog_preparation_matches_current(prepared))
        declarations = json.loads(prepared.declarations_bytes)
        record = next(record for record in declarations[0]['records'] if record['elementId'] == 'Order')
        field = next(field for field in record['fields'] if field['fieldId'] == 'placedAt')
        self.assertEqual(field['declaration']['scalarType'], 'timestamp')
        self.assertEqual(field['nativeDescriptor'], {
            'nativeScalarType': 'localTimestamp',
            'nativeTemporal': {
                'profile': 'truss.local-timestamp/0.1', 'kind': 'local',
                'source': {
                    'documentId': self.source['id'],
                    'sha256': sha256(self.content).hexdigest(),
                    'record': {'module': 'commerce', 'element': 'Order'},
                    'field': {'module': 'commerce', 'element': 'placedAt'},
                    'fieldViewPointer': '/modules/0/extensions/umf.access/views/0/fields/3',
                },
            },
        })
        self.assertEqual(declarations[0]['accessAdmissionProfile']['manifestSha256'],
                         prepared.access_admission_manifest_sha256)
        support = evaluate_catalog_support(prepared)
        self.assertEqual(support['state'], 'evaluated')
        self.assertEqual(support['registrationSummary']['interfaceVersion'],
                         'truss-registration-preparation/2.1')

    def test_legacy_preparation_profile_still_matches_accept_gate(self):
        prepared = prepare_catalog((self.document,))
        self.assertTrue(_catalog_preparation_matches_current(prepared))

    def test_owner_refusal_blocks_local_family_derivation(self):
        source = json.loads(self.content)
        del source['modules'][0]['extensions']['umf.access']['views'][0]['fields'][3]['temporal']
        content = json.dumps(source, separators=(',', ':')).encode()
        with self.assertRaises(PreparationRejected) as caught:
            prepare_catalog((CatalogDocument(source['id'], 'fixture-r2', content),),
                            support_profile=TEMPORAL_PROFILE)
        self.assertEqual(caught.exception.reason, 'unsupported_profile')


if __name__ == '__main__':
    unittest.main()
