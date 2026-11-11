# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private transport component controls; these are not native admission proof."""
import base64
import copy
import json
from importlib.resources import files
import unittest

from truss import CatalogDocument, LocalTimestampValue, Ok
from truss import temporal
from truss.contracts import MapValue, ProfilePin, SequenceValue, TextValue
from truss.groups import FrozenGroupRequest, GroupFailed, RootlessOwnership
from truss.catalog_runtime import _release, _object_result
from truss._temporal_profiles import profiles, abi
from truss._temporal_read import decode_object
from truss._group_runtime import recover_group_request


class TemporalPrivateTransportTests(unittest.TestCase):
    def envelope(self):
        manifest,digest,_=_release()
        value={'profile':'truss-python-temporal-scalar-object/0.1','releaseId':manifest['releaseId'],
               'releaseSha256':digest,'documentId':'doc','moduleId':'m','recordId':'r',
               'id':'17','typeId':'3','definitionPin':'a'*64,'version':'2',
               'catalogRevision':'4','recordRevision':'4','createdAt':'2024-01-01T00:00:00.000000Z',
               'updatedAt':'2024-01-01T00:00:00.000001Z','valueProfile':profiles()['valueProfile'],
               'queryAbi':abi(),'values':[['local',{'kind':'localTimestamp','text':'2024-02-29T12:34:56.123456'}],
                 ['date',{'kind':'date','text':'2000-02-29'}],['instant',{'kind':'timestamp','text':'2024-01-01T00:00:00.0000000-00:00'}],
                 ['null',None],['ordinary',{'kind':'sequence','items':[{'kind':'string','text':'kept'}]}]],
               'retained':[['unknown',{'kind':'timestamp','text':'2024-01-01T00:00:00.0000000-00:00'}]]}
        return manifest,digest,value

    def test_selected_decode_keeps_ordinary_meanings_and_refuses_ordinary_provider(self):
        manifest,digest,value=self.envelope();raw=json.dumps(value).encode()
        decoded=decode_object(raw,manifest,digest).object
        values=dict(decoded.values)
        self.assertEqual(values['local'],LocalTimestampValue(text='2024-02-29T12:34:56.123456'))
        self.assertEqual(values['instant'],TextValue(kind='timestamp',text='2024-01-01T00:00:00.0000000-00:00'))
        self.assertEqual(values['ordinary'],SequenceValue(items=(TextValue(kind='string',text='kept'),)))
        self.assertIsNone(values['null'])
        self.assertEqual(dict(decoded.retained)['unknown'],values['instant'])
        with self.assertRaises(ValueError):_object_result(raw,manifest,digest)

    def test_local_decode_requires_complete_exact_selected_envelope(self):
        manifest,digest,original=self.envelope()
        for fault in ('old-profile','missing-value','wrong-value','missing-abi','wrong-abi','release','extra','retained-local','nested-local'):
            value=copy.deepcopy(original)
            if fault=='old-profile':value['profile']='truss-python-scalar-object/0.4'
            elif fault=='missing-value':del value['valueProfile']
            elif fault=='wrong-value':value['valueProfile']['sha256']='0'*64
            elif fault=='missing-abi':del value['queryAbi']
            elif fault=='wrong-abi':value['queryAbi']['version']='1.2'
            elif fault=='release':value['releaseSha256']='0'*64
            elif fault=='extra':value['ignored']=True
            elif fault=='retained-local':value['retained']=[value['values'][0]]
            else:value['values']=[['nested',{'kind':'sequence','items':[value['values'][0][1]]}]]
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                decode_object(json.dumps(value).encode(),manifest,digest)
        raw=json.dumps(original).encode()
        with self.assertRaises(ValueError):
            decode_object(raw[:-1]+b',"profile":"truss-python-temporal-scalar-object/0.1"}',manifest,digest)

    def test_real_private_freezer_keeps_bytes_and_ordinary_recovery_refuses_before_io(self):
        manifest,digest,_=_release();selected=profiles()
        pins={e['name']:e['pin'] for e in json.loads(files('truss').joinpath('_catalog_runtime/group-profiles.json').read_bytes())['profiles']}
        context=temporal.GroupRuntimeContext(layout_profile=ProfilePin(**manifest['layoutProfile']),
            mutation_profile=ProfilePin(**selected['mutationProfile']),value_profile=ProfilePin(**selected['valueProfile']),
            request_fingerprint_profile=ProfilePin(**pins['requestFingerprintProfile']),authorized_scope_identity='component-scope',
            source_epoch='component-epoch',history_profile='component-history',query_abi=ProfilePin(**abi()),
            release_id=manifest['releaseId'],release_sha256=digest)
        local=LocalTimestampValue(text='2000-02-29T12:34:56.123456')
        operation=temporal.CreateObject(type_definition_pin='a'*64,ownership=RootlessOwnership(),alias='new',
            values=(temporal.AuthoredValue(name='local',value=local),))
        input=context.input((operation,),MapValue(entries=()));request=context.request('exact-replay')
        original=b'{"original": "source bytes retained"}\n'
        frame=temporal.freeze_group_request(input,request,documents=(CatalogDocument('doc','r1',original),))
        self.assertIsInstance(frame,Ok);self.assertIsInstance(frame.value,FrozenGroupRequest,repr(frame))
        request_input=json.loads(base64.b64decode(frame.value.input.bytes_base64))
        self.assertEqual(request_input['interfaceVersion'],'truss-group-temporal-input/0.1.0')
        self.assertEqual(request_input['operations'][0]['values'][0]['value'],{'kind':'localTimestamp','text':local.text})
        self.assertEqual(json.loads(base64.b64decode(frame.value.documents.bytes_base64))[0]['sourceText'].encode(),original)
        class NoIO:
            def _run_operation(self,*args,**kwargs):raise AssertionError('ordinary recovery attempted native I/O')
        refused=recover_group_request(NoIO(),object(),frame.value,manifest,digest,None)
        self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,GroupFailed)
