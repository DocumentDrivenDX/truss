# SPDX-License-Identifier: MIT OR Apache-2.0
"""Current UMF 0.10 relational source preparation; no owner transcript claims."""
import copy
import json
import unittest
from truss import CatalogDocument
from truss._catalog_support import DATE10_PROFILE, evaluate_catalog_support
from test_preparation import CONFIG, prepare


def relational_document():
    return {'umf':'0.10.0','id':'cohort','vocabularies':{},'extensions':{},'modules':[
        {'id':'m','namespace':'m','extensions':{},'elements':[
            *[{'id':name,'name':name,'kind':'record','members':[
                {'module':'m','element':name+'-label'}, {'module':'m','element':name+'-value'}],
                'keys':[{'id':'z-alt','name':'alt','fields':[{'module':'m','element':name+'-label'}]},
                    {'id':'a-primary','name':'primary','primary':True,'fields':[
                        {'module':'m','element':name+'-value'},{'module':'m','element':name+'-label'}]}],
                'extensions':{}} for name in ('A','B')],
            *[{'id':name+'-'+suffix,'name':name+'-'+suffix,'kind':'field','scalarType':'string',
               'nullability':'required','cardinality':'one','extensions':{}}
              for name in ('A','B') for suffix in ('label','value')]],
            'relationships':[{'id':'A-B','name':'A-B','source':[{'module':'m','element':'A'}],
                'target':[{'module':'m','element':'B','key':'a-primary'}],
                'sourceMultiplicity':{'min':0,'max':1},'targetMultiplicity':{'min':0,'max':2},
                'targetLifecycle':'independent','directed':True}]}]}


def relational_prepared(value=None, identities=('zdoc','adoc'), profile=DATE10_PROFILE):
    configuration=copy.deepcopy(CONFIG);configuration['supportProfile']=dict(profile)
    documents=[]
    for identity in identities:
        source=copy.deepcopy(relational_document() if value is None else value);source['id']=identity
        documents.append(CatalogDocument(identity,'r1',(' \n'+json.dumps(source)+'\n').encode()))
    return prepare(tuple(documents),configuration)


class CatalogRelationalSupportTests(unittest.TestCase):
    def test_current_relational_sources_and_native_declarations_are_preserved(self):
        prepared=relational_prepared()
        self.assertEqual(prepared.input()['supportProfile'],DATE10_PROFILE)
        self.assertEqual([d.source()['umf'] for d in prepared.documents],['0.10.0','0.10.0'])
        self.assertEqual([d.source()['id'] for d in prepared.documents],['zdoc','adoc'])
        support=evaluate_catalog_support(prepared)
        self.assertEqual(support['state'],'evaluated')
        self.assertEqual(support['closedSourceInventory']['state'],'supported')
        self.assertNotIn('entries',support['closedSourceInventory'])
        declarations=json.loads(prepared.declarations_bytes)
        self.assertEqual([d['records'][0]['documentId'] for d in declarations],['zdoc','adoc'])
        for document in prepared.documents:
            source=document.source();module=source['modules'][0]
            self.assertEqual(len(module['relationships']),1)
            self.assertEqual(module['relationships'][0]['target'][0]['key'],'a-primary')
            self.assertEqual([key['id'] for record in module['elements'] if record['kind']=='record' for key in record['keys']],
                ['z-alt','a-primary','z-alt','a-primary'])

    def test_declared_empty_relationships_remain_distinct_from_absence(self):
        for present in (False,True):
            source=relational_document();module=source['modules'][0]
            if present:module['relationships']=[]
            else:del module['relationships']
            prepared=relational_prepared(source,identities=('empty',))
            retained=prepared.documents[0].source()['modules'][0]
            self.assertEqual('relationships' in retained,present)
            self.assertEqual(retained.get('relationships',[]),[])

    def test_unknown_native_uuid_family_is_unavailable_for_storage(self):
        source=relational_document()
        field=next(e for e in source['modules'][0]['elements'] if e['id']=='A-label')
        field['scalarType']='uuid'
        support=evaluate_catalog_support(relational_prepared(source,identities=('uuid',)))
        self.assertEqual(support['closedSourceInventory']['state'],'unavailable')

    def test_invalid_source_does_not_produce_prepared_current_document(self):
        from truss import PreparationRejected
        source=relational_document();source['umf']='0.7.0'
        with self.assertRaises(PreparationRejected) as raised:relational_prepared(source,identities=('legacy',))
        self.assertEqual(raised.exception.reason,'unsupported_profile')


__all__=['relational_document','relational_prepared','CatalogRelationalSupportTests']
