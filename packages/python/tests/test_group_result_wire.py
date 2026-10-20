# SPDX-License-Identifier: MIT OR Apache-2.0
"""Closed Python projection of the original PostgreSQL group result wire."""
import base64
import hashlib
import json
import unittest

from truss._group_runtime import _decode_group_result, _result
from truss.contracts import ABSENT
from truss.groups import (AppliedPending, CommittedReceiptReplay, SameTransactionReplay,
    GroupFailed, GroupOperationFailure, InvalidGroupInput, RequestConflict)


def _position():
    return {
        'interfaceVersion': 'truss-receipt-position/0.1.0',
        'positionProfile': {'identity': 'runtime-position', 'version': '0.1', 'sha256': 'a' * 64},
        'installationId': 'install-1', 'sourceEpoch': 'epoch-1',
        'receiptStorageRowId': '4', 'writerXid': '20',
    }


def _token():
    raw = json.dumps(_position(), ensure_ascii=False, separators=(',', ':')).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')


def _semantic():
    return {
        'interfaceVersion': 'truss-group-result/0.1.0',
        'executedCatalogRevision': '1',
        'layoutProfile': {'identity': 'layout', 'version': '0.1', 'sha256': 'a' * 64},
        'mutationProfile': {'identity': 'mutation', 'version': '0.1', 'sha256': 'b' * 64},
        'results': [{
            'outcome': 'unchanged', 'operation': 'update_object',
            'identity': {'id': '1', 'typeId': '2', 'definitionPin': 'pin',
                         'owner': {'documentId': 'doc', 'moduleId': 'mod'}},
            'version': '1', 'events': [],
        }],
        'aliases': [],
    }


def _observation(*, basis='same_transaction', observing_xid='20'):
    return {
        'profile': 'truss-native-create-replay-observation/0.1',
        'sourceEpoch': 'epoch-1', 'observingXid': observing_xid,
        'originalWriterXid': '20', 'receiptStorageId': '4', 'receiptGeneration': '0',
        'receiptSha256': 'c' * 64, 'actorOid': '10', 'actor': 'consumer',
        'scopeIdentity': 'scope-1', 'releaseId': 'release-1', 'releaseSha256': 'd' * 64,
        'basis': basis,
    }


def _replay(*, durability='pending', observation=None):
    basis = 'same_transaction' if durability == 'pending' else 'committed_receipt'
    xid = '20' if durability == 'pending' else '21'
    observed = _observation(basis=basis, observing_xid=xid) if observation is None else observation
    raw_observation = json.dumps(observed, ensure_ascii=False, separators=(',', ':')).encode()
    return {
        'outcome': 'success', 'disposition': 'replayed', 'durability': durability,
        'semantic': _semantic(), 'receiptToken': _token(),
        'observationBase64': base64.b64encode(raw_observation).decode(),
        'observationSha256': hashlib.sha256(raw_observation).hexdigest(),
    }


def _wire(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


class GroupResultWireTests(unittest.TestCase):
    def test_typed_operation_failure_preserves_optional_index_and_original_artifact(self):
        for index in (ABSENT, '17'):
            value = {'outcome': 'failed', 'code': 'key_conflict', 'nativeState': '23505'}
            if index is not ABSENT:
                value['operationIndex'] = index
            raw = _wire(value)
            result = _result(raw, request_present=False)
            self.assertIsInstance(result, GroupFailed)
            failure = result.failure
            self.assertIsInstance(failure, GroupOperationFailure)
            self.assertEqual((failure.code, failure.operation_code, failure.operation_index),
                ('group_failed', 'key_conflict', index))
            self.assertEqual(base64.b64decode(failure.inner_error.bytes_base64), raw)
            self.assertEqual(failure.inner_error.sha256, hashlib.sha256(raw).hexdigest())

    def test_invalid_input_without_index_is_group_input_and_indexed_is_operation_failure(self):
        unindexed = _wire({'outcome': 'failed', 'code': 'invalid_input', 'nativeState': '22023'})
        result = _result(unindexed, request_present=False)
        self.assertIsInstance(result.failure, InvalidGroupInput)
        self.assertEqual(base64.b64decode(result.failure.diagnostic.bytes_base64), unindexed)

        indexed = _wire({'outcome': 'failed', 'code': 'invalid_input', 'nativeState': '22023',
            'operationIndex': '0'})
        result = _result(indexed, request_present=False)
        self.assertIsInstance(result.failure, GroupOperationFailure)
        self.assertEqual((result.failure.code, result.failure.operation_code, result.failure.operation_index),
            ('group_failed', 'invalid_input', '0'))
        self.assertEqual(base64.b64decode(result.failure.inner_error.bytes_base64), indexed)

    def test_request_conflict_requires_a_present_request(self):
        raw = _wire({'outcome': 'failed', 'code': 'request_conflict', 'nativeState': 'P1001'})
        with self.assertRaisesRegex(ValueError, 'Request-free'):
            _result(raw, request_present=False)
        result = _result(raw, request_present=True)
        self.assertIsInstance(result.failure, RequestConflict)
        self.assertEqual(base64.b64decode(result.failure.diagnostic.bytes_base64), raw)

    def test_optional_failure_index_keeps_closed_native_grammar(self):
        malformed = (
            {'outcome': 'failed', 'code': 'key_conflict', 'nativeState': '23505', 'operationIndex': '00'},
            {'outcome': 'failed', 'code': 'key_conflict', 'nativeState': '23505', 'operationIndex': '-1'},
            {'outcome': 'failed', 'code': 'key_conflict', 'nativeState': '23505', 'operationIndex': '1024'},
            {'outcome': 'failed', 'code': 'key_conflict', 'nativeState': '23505', 'operationIndex': None},
            {'outcome': 'failed', 'code': 'key_conflict', 'nativeState': '23505', 'operationIndex': '0', 'extra': 'x'},
            {'outcome': 'failed', 'code': 'key_conflict', 'nativeState': 'P1001'},
        )
        for value in malformed:
            with self.subTest(value=value), self.assertRaises(ValueError):
                _result(_wire(value), request_present=True)

    def test_request_free_applied_null_token_is_absent(self):
        value = {
            'outcome': 'success', 'disposition': 'applied', 'durability': 'pending',
            'semantic': _semantic(), 'receiptToken': None,
            'attemptId': '00000000-0000-0000-0000-000000000001',
        }
        result = _result(_wire(value), request_present=False)
        self.assertIsInstance(result.response, AppliedPending)
        self.assertIs(result.response.receipt_token, ABSENT)

    def test_request_applied_and_replays_accept_original_tokens(self):
        applied = {
            'outcome': 'success', 'disposition': 'applied', 'durability': 'pending',
            'semantic': _semantic(), 'receiptToken': _token(),
            'attemptId': '00000000-0000-0000-0000-000000000001',
        }
        self.assertEqual(_result(_wire(applied), request_present=True).response.receipt_token, _token())
        same = _result(_wire(_replay()), request_present=True)
        self.assertIsInstance(same.response, SameTransactionReplay)
        committed = _result(_wire(_replay(durability='committed')), request_present=True)
        self.assertIsInstance(committed.response, CommittedReceiptReplay)

    def test_rejects_wrong_outcome_disposition_durability_and_token_shape(self):
        corruptions = []
        value = _replay(); value['outcome'] = 'unexpected'; corruptions.append(value)
        value = _replay(); value['disposition'] = 'unexpected'; corruptions.append(value)
        value = _replay(); value['durability'] = 'committed'; corruptions.append(value)
        value = _replay(); value['receiptToken'] = None; corruptions.append(value)
        value = _replay(); value['extra'] = True; corruptions.append(value)
        value = _replay(); value['observationBase64'] = base64.b64encode(
            json.dumps(_observation(observing_xid='020'), separators=(',', ':')).encode()).decode()
        value['observationSha256'] = hashlib.sha256(base64.b64decode(value['observationBase64'])).hexdigest()
        corruptions.append(value)
        applied = {'outcome': 'success', 'disposition': 'applied', 'durability': 'pending',
            'semantic': _semantic(), 'receiptToken': None,
            'attemptId': '00000000-0000-0000-0000-000000000001'}
        corruptions.append(applied)
        applied = {'outcome': 'success', 'disposition': 'applied', 'durability': 'pending',
            'semantic': _semantic(), 'receiptToken': None,
            'attemptId': '------------------------------------'}
        corruptions.append(applied)
        for value in corruptions:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    _result(_wire(value), request_present=True)

    def test_rejects_unknown_native_failure_mapping(self):
        for value in (
            {'outcome': 'failed', 'code': 'future_code', 'operationIndex': '0', 'nativeState': 'XX000'},
            {'outcome': 'failed', 'code': 'key_conflict', 'operationIndex': '00', 'nativeState': '23505'},
            {'outcome': 'failed', 'code': 'key_conflict', 'operationIndex': '0', 'nativeState': 'P1001'},
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    _result(_wire(value), request_present=True)

    def test_rejects_duplicate_members_and_numeric_tokens(self):
        applied = _wire({'outcome': 'success', 'disposition': 'applied', 'durability': 'pending',
            'semantic': _semantic(), 'receiptToken': _token(),
            'attemptId': '00000000-0000-0000-0000-000000000001'})
        duplicate = applied.replace(b'"outcome":"success"', b'"outcome":"failed","outcome":"success"', 1)
        with self.assertRaisesRegex(ValueError, 'Valid exact native group result'):
            _result(duplicate, request_present=True)
        # The valid native result grammar has no JSON numbers. Exercise the
        # decoder directly so closed-object validation cannot mask this check.
        with self.assertRaisesRegex(ValueError, 'Valid exact native group result'):
            _decode_group_result(b'{"outcome":"success","number":1}')

    def test_request_free_results_cannot_claim_receipt_state(self):
        for value in (
            {'outcome': 'unavailable', 'reason': 'receipt'},
            {'outcome': 'unavailable', 'reason': 'receipt_expired'},
            {'outcome': 'failed', 'code': 'request_conflict', 'operationIndex': '0', 'nativeState': 'P1001'},
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    _result(_wire(value), request_present=False)

    def test_rejects_unbound_or_inconsistent_original_observation(self):
        cases = []
        value = _observation(); value['unexpected'] = 'field'; cases.append(value)
        value = _observation(); value['sourceEpoch'] = 'other'; cases.append(value)
        value = _observation(); value['receiptStorageId'] = '5'; cases.append(value)
        value = _observation(); value['originalWriterXid'] = '19'; cases.append(value)
        value = _observation(basis='committed_receipt', observing_xid='21'); cases.append(value)
        for observation in cases:
            with self.subTest(observation=observation):
                with self.assertRaises(ValueError):
                    _result(_wire(_replay(observation=observation)), request_present=True)

    def test_rejects_observation_corruption_after_encoding(self):
        value = _replay()
        value['observationBase64'] = base64.b64encode(b'{"arbitrary":true}').decode()
        value['observationSha256'] = hashlib.sha256(base64.b64decode(value['observationBase64'])).hexdigest()
        with self.assertRaises(ValueError):
            _result(_wire(value), request_present=True)


if __name__ == '__main__':
    unittest.main()
