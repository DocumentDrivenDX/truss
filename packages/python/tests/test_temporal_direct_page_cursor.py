# SPDX-License-Identifier: MIT OR Apache-2.0
"""PV5 transport custody only: fabricated seals never claim native issuance."""
import base64
import copy
from dataclasses import replace
import json
import unittest
from unittest.mock import Mock
from truss import temporal,Ok
from truss._temporal_read import decode_cursor,_page
from truss.object_read import ObjectReadInvalid,ObjectNotFound
import test_temporal_native_integer_transport as integer_fixture


class TemporalDirectPageCursorTests(unittest.TestCase):
    def original(self):
        return integer_fixture.TemporalNativeIntegerTransportTests().cursor()

    def test_original_bytes_are_required_exact_immutable_bounded_and_not_repr(self):
        manifest,digest,wire=self.original();cursor=decode_cursor(wire,manifest,digest)
        self.assertEqual(cursor.original_bytes,base64.b64decode(wire['originalCursorBase64']))
        self.assertNotIn(repr(cursor.original_bytes),repr(cursor))
        for invalid in (None,'token',bytearray(b'token'),b'',b'x'*65537):
            with self.subTest(value=type(invalid).__name__),self.assertRaises(ValueError):replace(cursor,original_bytes=invalid)
        for valid in (b'x',b'x'*65536):self.assertEqual(replace(cursor,original_bytes=valid).original_bytes,valid)
        with self.assertRaises(ValueError):replace(cursor,after_id=True)

    def test_unsigned_malformed_base64_or_metadata_mismatch_refuses(self):
        manifest,digest,wire=self.original()
        unsigned=copy.deepcopy(wire);unsigned.pop('originalCursorBase64')
        with self.assertRaises(ValueError):decode_cursor(unsigned,manifest,digest)
        for encoded in ('%%%',wire['originalCursorBase64']+'\n',base64.b64encode(b'{}').decode()):
            bad={**wire,'originalCursorBase64':encoded}
            with self.subTest(encoded=encoded),self.assertRaises(ValueError):decode_cursor(bad,manifest,digest)
        for field,value in (('afterId','18'),('installationId','other'),('sourceEpoch','other'),('definitionPin','b'*64)):
            with self.subTest(field=field),self.assertRaises(ValueError):decode_cursor({**wire,field:value},manifest,digest)

    def test_provider_passes_original_bytes_unchanged_and_refuses_modified_metadata_before_io(self):
        from truss._temporal_profiles import profiles,abi
        manifest,digest,wire=self.original();cursor=decode_cursor(wire,manifest,digest)
        native=Mock();native.fetchone.return_value=(None,)
        host=Mock();host._run_operation.side_effect=lambda tx,observe,**kw:Ok(observe(native,None))
        assembly=Mock();assembly._host=host
        args={'transaction':object(),'limit':2,'maximum_bytes':100000,'cursor':cursor,
              'document_id':'doc','module_id':'m','record_id':'r'}
        result=_page(assembly,args,manifest,digest,lambda c:None)
        self.assertIsInstance(result.value,ObjectNotFound)
        self.assertIs(native.execute.call_args.args[1][5],cursor.original_bytes)
        for changed in (replace(cursor,after_id=18),replace(cursor,source_epoch='other'),replace(cursor,original_bytes=b'{}')):
            host.reset_mock();result=_page(assembly,{**args,'cursor':changed},manifest,digest,lambda c:None)
            self.assertEqual(result,Ok(ObjectReadInvalid(code='cursor')));host._run_operation.assert_not_called()
