import base64
from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
import unittest
from truss._row_operation_custody import decode_row_operation_custody


def fixture(count=2):
    def artifact(identity):
        original = identity.encode()
        return {'identity': identity, 'bytesBase64': base64.b64encode(original).decode(),
                'sha256': sha256(original).hexdigest()}
    return {'interfaceVersion': 'truss-row-operation-custody/0.1.0',
        'profile': {'identity': 'unadmitted-fixture', 'version': '0.1', 'sha256': 'a' * 64},
        'originalLayout': artifact('layout'), 'originalHome': artifact('home'),
        'originalOwnerProperty': artifact('property'),
        'operations': [{'ordinal': str(i), 'operationIdentity': 'native-' + str(7 + 4*i),
            'operationKind': 'mutation', 'originalOperationDefinition': artifact('definition'),
            'originalInput': artifact('input'), 'originalPrestate': artifact('absent-carrier'),
            'admittedCandidate': artifact('candidate'), 'nativeGroupCustodyIdentity': 'group-' + str(i),
            'effectObligationDefinition': artifact('obligation')} for i in range(count)],
        'groupResolution': 'original-native-effects-readiness-before-seal',
        'completionEvidence': 'resolved-independently-not-embedded-future-digest',
        'transactionAuthority': 'actual-native-touch-context-not-caller-manifest'}


class RowOperationCustodyTests(unittest.TestCase):
    def test_original_bytes_and_immutable_complete_projection(self):
        original = json.dumps(fixture(), indent=2).encode()
        body = decode_row_operation_custody(original)
        self.assertIs(body.original, original)
        self.assertEqual([(r.ordinal, r.identity) for r in body.operations], [('0', 'native-7'), ('1', 'native-11')])
        self.assertEqual(body.operations[0].prestate.original, b'absent-carrier')
        self.assertIsInstance(body.operations, tuple)
        with self.assertRaises(FrozenInstanceError): body.operations[0].prestate.identity = 'replacement'

    def test_complete_local_order_and_artifact_refusals(self):
        changes = [lambda d: d.update(extra='unknown'),
            lambda d: d['operations'][0].update(ordinal='7'),
            lambda d: d['operations'][0].update(ordinal='00'),
            lambda d: d['operations'][1].update(operationIdentity='native-7'),
            lambda d: d['operations'][0].pop('originalPrestate'),
            lambda d: d['operations'][0].update(originalPrestate=None),
            lambda d: d['operations'][0]['originalInput'].update(sha256='0' * 64),
            lambda d: d['operations'][0]['originalInput'].update(bytesBase64='not-base64!'),
            lambda d: d['operations'][0].update(operationKind='unknown'),
            lambda d: d.update(transactionAuthority='caller')]
        for i, change in enumerate(changes):
            with self.subTest(control=i):
                value=fixture(); change(value)
                with self.assertRaises(ValueError): decode_row_operation_custody(json.dumps(value).encode())

    def test_complete_operation_count_bound(self):
        self.assertEqual(len(decode_row_operation_custody(json.dumps(fixture(1024)).encode()).operations), 1024)
        for count in (0, 1025):
            with self.assertRaises(ValueError): decode_row_operation_custody(json.dumps(fixture(count)).encode())


if __name__ == '__main__': unittest.main()
