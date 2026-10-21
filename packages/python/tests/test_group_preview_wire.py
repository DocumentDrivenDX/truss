# SPDX-License-Identifier: MIT OR Apache-2.0
"""Read-only preview carrier and strict native result projection controls."""
import json
import unittest

from truss._preview_runtime import _decode_preview_result
from truss.contracts import ProfilePin, TypedIdentity, QualifiedOwner
from truss.groups import CurrentCatalog, ObjectExists
from truss.preview import (GroupConditionPreviewInput, PreviewObserved,
                           PreviewRefused)


def _input():
    pin = ProfilePin(identity='selected', version='0.1', sha256='a' * 64)
    identity = TypedIdentity(id='1', type_id='2', definition_pin='pin',
        owner=QualifiedOwner(document_id='doc', module_id='mod'))
    return GroupConditionPreviewInput(layout_profile=pin, mutation_profile=pin,
        value_profile=pin, catalog=CurrentCatalog(),
        preconditions=(ObjectExists(id='condition-1', reason='check', target=identity),))


def _wire(*, passed=True):
    return json.dumps({'outcome': 'observed', 'conditions': [{
        'conditionId': 'condition-1', 'rule': 'object_exists', 'passed': passed}],
        'basis': {'catalogRevision': '3', 'snapshot': '100:105:101,103',
          'sourceEpoch': 'epoch-1', 'releaseId': 'release-1', 'releaseSha256': 'b' * 64,
          'layoutProfile': {'identity': 'selected', 'version': '0.1', 'sha256': 'a' * 64}}},
        separators=(',', ':')).encode()


class GroupPreviewWireTests(unittest.TestCase):
    def test_preview_is_an_observation_without_mutation_receipt_fields(self):
        result = _decode_preview_result(_wire(passed=False), _input())
        self.assertIsInstance(result, PreviewObserved)
        self.assertFalse(result.conditions[0].passed)
        self.assertEqual(result.basis.catalog_revision, '3')
        self.assertEqual(result.basis.snapshot, '100:105:101,103')
        self.assertEqual(result.basis.status, 'observed')
        self.assertFalse(hasattr(result, 'receipt_token'))
        self.assertFalse(hasattr(result, 'receipt'))

    def test_refusal_has_no_identity_or_native_diagnostic_carrier(self):
        result = PreviewRefused(reason='unauthorized')
        self.assertFalse(hasattr(result, 'condition_id'))
        self.assertFalse(hasattr(result, 'native_error'))

    def test_transient_basis_change_has_typed_observation_refusal(self):
        result = PreviewRefused(reason='observation')
        self.assertEqual(result.outcome, 'refused')
        self.assertEqual(result.reason, 'observation')

    def test_preview_rejects_non_tuple_or_unrecognized_conditions_at_construction(self):
        base = _input()
        for value in (None, [], 1, (object(),)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                GroupConditionPreviewInput(layout_profile=base.layout_profile,
                    mutation_profile=base.mutation_profile, value_profile=base.value_profile,
                    catalog=base.catalog, preconditions=value)

    def test_preview_requires_exact_ordered_condition_correspondence(self):
        raw = json.loads(_wire())
        raw['conditions'][0]['conditionId'] = 'other'
        with self.assertRaisesRegex(ValueError, 'correspondence'):
            _decode_preview_result(json.dumps(raw).encode(), _input())

    def test_preview_refuses_extra_members_and_numeric_tokens(self):
        raw = json.loads(_wire())
        raw['receiptToken'] = 'must-not-appear'
        with self.assertRaisesRegex(ValueError, 'observed-preview'):
            _decode_preview_result(json.dumps(raw).encode(), _input())
        with self.assertRaisesRegex(ValueError, 'Numeric'):
            _decode_preview_result(_wire().replace(b'"catalogRevision":"3"', b'"catalogRevision":3'), _input())


if __name__ == '__main__':
    unittest.main()
