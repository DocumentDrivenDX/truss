# SPDX-License-Identifier: MIT OR Apache-2.0
"""Canonical object/cursor integer wire controls; no native fixture is started."""
import copy
import json
import unittest

from truss._temporal_read import decode_object,decode_cursor
import test_temporal_private_transport as object_fixture


class TemporalNativeIntegerTransportTests(unittest.TestCase):
    def original(self):
        return object_fixture.TemporalPrivateTransportTests.envelope(self)

    def cursor(self):
        manifest,digest,obj=self.original()
        return manifest,digest,{'profile':'truss-python-temporal-object-page/0.1','installationId':'installation',
            'sourceEpoch':'epoch','releaseSha256':digest,'documentId':'doc','moduleId':'m','recordId':'r',
            'typeId':'3','definitionPin':'a'*64,'catalogRevision':'4','afterId':'17',
            'valueProfile':obj['valueProfile'],'queryAbi':obj['queryAbi']}

    def bad_values(self,maximum):
        return (True,False,1,1.0,1.5,None,'','0','00','01','+1','-1','1.0','1e0',' 1','1 ','1\n',
                '١','９',str(maximum+1),'9'*100)

    def test_object_integer_fields_refuse_coercions_and_overflow(self):
        manifest,digest,original=self.original()
        for field,maximum in (('id',9223372036854775807),('typeId',2147483647),('version',9223372036854775807),
                              ('catalogRevision',2147483647),('recordRevision',2147483647)):
            for invalid in self.bad_values(maximum):
                value=copy.deepcopy(original);value[field]=invalid
                with self.subTest(field=field,value=repr(invalid)),self.assertRaises(ValueError):
                    decode_object(json.dumps(value).encode(),manifest,digest)

    def test_cursor_integer_fields_refuse_coercions_and_overflow(self):
        manifest,digest,original=self.cursor()
        for field,maximum in (('typeId',2147483647),('catalogRevision',2147483647),('afterId',9223372036854775807)):
            for invalid in self.bad_values(maximum):
                value=copy.deepcopy(original);value[field]=invalid
                with self.subTest(field=field,value=repr(invalid)),self.assertRaises(ValueError):
                    decode_cursor(value,manifest,digest)

    def test_owned_root_identity_uses_the_same_exact_native_ranges(self):
        manifest,digest,original=self.original()
        original['profile']='truss-python-temporal-logical-object/0.1'
        original['root']={'id':'1','typeId':'1','definitionPin':'b'*64,'owner':{'documentId':'root','moduleId':'m'}}
        self.assertEqual(decode_object(json.dumps(original).encode(),manifest,digest).object.ownership.root.identity.id,'1')
        for field,maximum in (('id',9223372036854775807),('typeId',2147483647)):
            for invalid in self.bad_values(maximum):
                value=copy.deepcopy(original);value['root'][field]=invalid
                with self.subTest(field=field,value=repr(invalid)),self.assertRaises(ValueError):
                    decode_object(json.dumps(value).encode(),manifest,digest)

    def test_exact_object_and_cursor_minimum_and_native_maximum_boundaries(self):
        manifest,digest,obj=self.original();_,_,cursor=self.cursor()
        for upper in (False,True):
            for field,maximum in (('id',9223372036854775807),('typeId',2147483647),('version',9223372036854775807),
                                  ('catalogRevision',2147483647),('recordRevision',2147483647)):
                obj[field]=str(maximum if upper else 1)
            for field,maximum in (('typeId',2147483647),('catalogRevision',2147483647),('afterId',9223372036854775807)):
                cursor[field]=str(maximum if upper else 1)
            decoded=decode_object(json.dumps(obj).encode(),manifest,digest).object
            continuation=decode_cursor(cursor,manifest,digest)
            self.assertEqual(decoded.id,9223372036854775807 if upper else 1)
            self.assertEqual(decoded.type_id,2147483647 if upper else 1)
            self.assertEqual(decoded.version,9223372036854775807 if upper else 1)
            self.assertEqual(decoded.catalog_revision,2147483647 if upper else 1)
            self.assertEqual(decoded.record_revision,2147483647 if upper else 1)
            self.assertEqual(continuation.type_id,2147483647 if upper else 1)
            self.assertEqual(continuation.catalog_revision,2147483647 if upper else 1)
            self.assertEqual(continuation.after_id,9223372036854775807 if upper else 1)
