import base64
from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
import unittest
from truss._row_group_custody import decode_row_group_custody
from truss._row_operation_address import encode_row_operation_address


def fixture():
    raw=b'original family admission'
    return {'interfaceVersion':'truss-row-group-custody/0.1.0',
        'profile':{'identity':'unadmitted-fixture','version':'0.1','sha256':'a'*64},
        'addressDomain':'truss-row-operation-address/0.1.0',
        'operationIdentity':encode_row_operation_address('fixture','123','7').decode(),
        'operationKind':'mutation',
        'originalGroupAdmission':{'identity':'family','bytesBase64':base64.b64encode(raw).decode(),'sha256':sha256(raw).hexdigest()},
        'authority':'actual-original-operation-admission-not-caller-address',
        'completionEvidence':'resolved-independently-not-embedded-future-digest'}


class GroupCustodyTests(unittest.TestCase):
    def test_original_immutable_projection_all_families(self):
        for kind in ('mutation','import','catalog-transform','catalog-acceptance','home-migration','administrative-repair'):
            value=fixture(); value['operationKind']=kind
            raw=json.dumps(value,indent=2).encode(); body=decode_row_group_custody(raw)
            self.assertIs(body.original,raw)
            self.assertEqual(body.kind,kind)
            self.assertEqual(body.address.operation_ordinal,'7')
            self.assertEqual(body.admission.original,b'original family admission')
            with self.assertRaises(FrozenInstanceError): body.profile.identity='replacement'

    def test_closed_carrier_artifact_and_address_refusals(self):
        changes=[lambda v:v.pop('operationIdentity'),lambda v:v.update(extra=True),
            lambda v:v.update(finalizationDigest='0'*64),lambda v:v.update(operationKind='unknown'),
            lambda v:v.update(authority='caller'),lambda v:v.update(addressDomain='other'),
            lambda v:v['profile'].pop('sha256'),lambda v:v['originalGroupAdmission'].update(extra=True),
            lambda v:v['originalGroupAdmission'].update(sha256='0'*64),
            lambda v:v['originalGroupAdmission'].update(bytesBase64='bad!'),
            lambda v:v.update(operationIdentity='unresolved'),
            lambda v:v.update(operationIdentity=v['operationIdentity']+'\n'),
            lambda v:v.update(operationIdentity=123)]
        for i,change in enumerate(changes):
            with self.subTest(control=i):
                value=fixture();change(value)
                with self.assertRaises(ValueError):decode_row_group_custody(json.dumps(value).encode())

    def test_duplicate_numeric_and_future_completion_syntax(self):
        raw=json.dumps(fixture()).encode()
        for bad in (b'{"x":1}',raw[:-1]+b',"operationKind":"import"}',raw[:-1]+b',"futureSeal":null}'):
            with self.assertRaises(ValueError):decode_row_group_custody(bad)

    def test_empty_artifact_does_not_establish_family_admission(self):
        value=fixture();value['originalGroupAdmission'].update(bytesBase64='',sha256=sha256(b'').hexdigest())
        self.assertEqual(decode_row_group_custody(json.dumps(value).encode()).admission.original,b'')


if __name__=='__main__':unittest.main()
