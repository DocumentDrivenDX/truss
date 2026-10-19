# SPDX-License-Identifier: MIT OR Apache-2.0
"""Composer source custody across revisions; not native evolution acceptance."""
import base64
import copy
import json
import unittest
from hashlib import sha256
from truss.contracts import ProfilePin
from truss._catalog_view_build import build_catalog_view


class CatalogViewRevisionTests(unittest.TestCase):
    def test_current_record_and_retained_key_use_their_own_original_archives(self):
        first={'id':'d','modules':[{'id':'m','elements':[
            {'id':'Item','kind':'record','members':[{'module':'m','element':'code'}],
             'keys':[{'id':'primary','primary':True,'fields':[{'module':'m','element':'code'}]}]},
            {'id':'code','kind':'field','name':'code','scalarType':'string'}]}]}
        second=copy.deepcopy(first)
        second['modules'][0]['elements'][0]['members'].append({'module':'m','element':'note'})
        second['modules'][0]['elements'].append({'id':'note','kind':'field','name':'note','scalarType':'string'})
        def document(revision,value):
            original=json.dumps(value,separators=(',',':'))
            return {'rev':revision,'ord':0,'doc_id':'d','doc_revision':str(revision),
                    'document':original,'content_sha256':sha256(original.encode()).hexdigest()}
        def source(revision):
            return {'definition_rev':revision,'definition_doc_ord':0,'definition_document_id':'d','retired_rev':None}
        basis={'revision':'2','installationId':'composer-fixture','releaseId':'fixture',
               'releaseSha256':'a'*64,'registrationId':'fixture','reportSha256':'b'*64,
               'documents':[document(1,first),document(2,second)],
               'types':[dict(source(2),document_id='d',module='m',element='Item',type_id=1)],
               'properties':[dict(source(1),declaration_module='m',element='code',type_id=1,prop_id=1),
                             dict(source(2),declaration_module='m',element='note',type_id=1,prop_id=2)],
               'keys':[dict(source(1),type_id=1,key_id='primary',key_num=1,prop_ids=[1])],
               'relationships':[],'endpoints':[]}
        view=build_catalog_view(basis,ProfilePin(identity='fixture',version='1',sha256='c'*64))
        definitions={entry.reference.kind:entry for entry in view.definitions if entry.reference.kind!='property'}
        self.assertEqual(definitions['type'].provenance.accepted_catalog_revision,'2')
        self.assertEqual(definitions['key'].provenance.accepted_catalog_revision,'1')
        self.assertEqual([ref.authored_identity for ref in definitions['type'].dependencies],['code','note'])
        self.assertEqual(json.loads(base64.b64decode(definitions['key'].definition.bytes_base64)),first['modules'][0]['elements'][0]['keys'][0])
        reversed_archives=dict(basis,documents=list(reversed(basis['documents'])))
        self.assertEqual(build_catalog_view(reversed_archives,view.layout_profile).original_bytes,view.original_bytes)
        duplicate=copy.deepcopy(basis);duplicate['documents'].append(duplicate['documents'][0])
        with self.assertRaisesRegex(ValueError,'Unique accepted archive'):
            build_catalog_view(duplicate,view.layout_profile)
