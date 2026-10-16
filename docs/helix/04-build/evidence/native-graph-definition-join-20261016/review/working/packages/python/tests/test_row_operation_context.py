import copy
import json
import unittest
from dataclasses import FrozenInstanceError, replace
from truss._row_operation_context import ARTIFACT_FIELDS, decode_row_operation_context, check_context_group_manifest
from truss._row_operation_custody import decode_row_operation_custody
from truss._row_group_custody import decode_row_group_custody
from test_row_operation_custody import fixture as manifest_fixture
from test_row_group_custody import fixture as group_fixture


def fixtures():
    group=group_fixture();body=manifest_fixture(1)
    group['profile']=copy.deepcopy(body['profile'])
    body['operations'][0].update(operationIdentity=group['operationIdentity'],nativeGroupCustodyIdentity=group['operationIdentity'])
    sample=copy.deepcopy(body['originalLayout'])
    context={'interfaceVersion':'truss-row-operation-context/0.1.0','profile':copy.deepcopy(body['profile']),
        'installationIdentity':'fixture','originalWriterXid':'123','operationOrdinal':'7',
        'addressDomain':'truss-row-operation-address/0.1.0','authority':'actual-protected-native-registry-correspondence',
        'durability':'transaction-local-until-original-commit-observation',**{key:copy.deepcopy(sample) for key in ARTIFACT_FIELDS}}
    context['originalOperationDefinition']=copy.deepcopy(body['operations'][0]['originalOperationDefinition'])
    context['originalGroupAdmission']=copy.deepcopy(group['originalGroupAdmission'])
    return context,group,body


def decode(values):
    return tuple(fn(json.dumps(value).encode()) for fn,value in zip(
        (decode_row_operation_context,decode_row_group_custody,decode_row_operation_custody),values))


class OperationContextTests(unittest.TestCase):
    def test_complete_original_projection_and_local_native_distinction(self):
        values=fixtures();raw=json.dumps(values[0],indent=2).encode();context=decode_row_operation_context(raw)
        self.assertIs(context.original,raw)
        self.assertEqual(len(context.artifacts),9)
        with self.assertRaises(FrozenInstanceError):context.artifacts[0].identity='replacement'
        context,group,body=decode(values)
        self.assertEqual(check_context_group_manifest(context,group,body,0).operation_ordinal,'7')
        self.assertEqual(body.operations[0].ordinal,'0')

    def test_each_required_artifact_and_closed_native_context(self):
        for field in ARTIFACT_FIELDS:
            value=fixtures()[0];value.pop(field)
            with self.subTest(field=field),self.assertRaises(ValueError):decode_row_operation_context(json.dumps(value).encode())
        changes=[lambda v:v.update(extra=True),lambda v:v.update(originalWriterXid='01'),
            lambda v:v.update(originalWriterXid='18446744073709551616'),
            lambda v:v.update(operationOrdinal='9223372036854775808'),
            lambda v:v.update(authority='caller'),lambda v:v.update(durability='committed'),
            lambda v:v['originalOwnerUnion'].update(sha256='0'*64)]
        for change in changes:
            value=fixtures()[0];change(value)
            with self.assertRaises(ValueError):decode_row_operation_context(json.dumps(value).encode())

    def test_independent_correspondence_substitutions(self):
        context,group,body=decode(fixtures())
        changes=[(replace(context,profile=replace(context.profile,version='other')),group,body),
            (replace(context,address=replace(context.address,original=b'other')),group,body),
            (context,replace(group,kind='import'),body),
            (context,replace(group,admission=replace(group.admission,identity='other')),body),
            (context,group,replace(body,layout=replace(body.layout,identity='other'))),
            (context,group,replace(body,operations=(replace(body.operations[0],definition=replace(body.operations[0].definition,identity='other')),))),
            (context,group,replace(body,operations=(replace(body.operations[0],group_identity='other'),)))]
        for values in changes:
            with self.assertRaises(ValueError):check_context_group_manifest(*values,0)
        for position in (-1,1,True,'0'):
            with self.assertRaises(ValueError):check_context_group_manifest(context,group,body,position)


if __name__=='__main__':unittest.main()
