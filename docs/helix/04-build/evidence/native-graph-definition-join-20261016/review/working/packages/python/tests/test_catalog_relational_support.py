"""Original UMF authored key/relationship inventory; not accepted enforcement."""
import copy
import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from truss import CatalogDocument
from truss._catalog_support import (RELATIONAL_PROFILE, PROFILE,
    evaluate_catalog_support, _closed_source_inventory)
from truss._owner_evidence_json import decode_owner_evidence_json
from truss._catalog_report_semantics import compose_original_catalog_report_semantics
from test_preparation import prepare, CONFIG


def relational_document():
    return {'umf':'0.7.0','id':'cohort','vocabularies':{},'extensions':{},'modules':[
        {'id':'m','namespace':'m','extensions':{},'elements':[
            *[{'id':name,'kind':'record','members':[
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


def relational_prepared(value=None, identities=('zdoc','adoc'), profile=RELATIONAL_PROFILE):
    configuration=copy.deepcopy(CONFIG);configuration['supportProfile']=dict(profile)
    documents=[]
    for identity in identities:
        source=copy.deepcopy(relational_document() if value is None else value);source['id']=identity
        documents.append(CatalogDocument(identity,'r1',(' \n'+json.dumps(source)+'\n').encode()))
    return prepare(tuple(documents),configuration)


class CatalogRelationalSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared=relational_prepared()
        cls.evidence=decode_owner_evidence_json(cls.prepared.report_evidence_bytes)

    def inventory(self, observations=None, core=None):
        return _closed_source_inventory(self.prepared,
            self.evidence['ownerObservations'] if observations is None else observations,
            self.evidence['coreAssertionIdentities'] if core is None else core,relational=True)

    def test_complete_multidocument_record_qualified_authored_occurrences(self):
        support=evaluate_catalog_support(self.prepared);inventory=support['closedSourceInventory']
        self.assertEqual(inventory['state'],'inventoried')
        self.assertEqual(inventory['scope'],'original_0.7_explicit_scalar_string_records_keys_relationships')
        authored=[e for e in inventory['entries'] if e['assertion']['kind']=='authored']
        self.assertEqual(len(authored),10)
        addresses={(e['assertion']['owner']['documentId'],e['assertion']['sourcePointer']) for e in authored}
        self.assertEqual(len(addresses),10)
        self.assertEqual(sum(e['assertion']['authoredIdentity']=='a-primary' for e in authored),4)
        self.assertTrue(all('sourceIdentityProfile' not in e['assertion'] for e in authored))
        self.assertTrue(all(e['enforcement']=='none' and e['reason']=='unqualified' for e in authored))
        projection=compose_original_catalog_report_semantics(self.prepared,support)
        self.assertEqual(projection['state'],'source_fields_ready')
        schema=json.loads((Path(__file__).resolve().parents[3]/'docs/helix/02-design/contracts/enforcement-report-v0.1.schema.json').read_bytes())
        validator=Draft202012Validator({'$schema':schema['$schema'],'type':'array',
            'items':{'$ref':'#/$defs/entry'},'$defs':schema['$defs']})
        validator.validate(projection['assertionEntries'])
        self.assertTrue(list(validator.iter_errors(inventory['entries'])))
        self.assertFalse(inventory['acceptedReportQualified'])
        self.assertEqual(self.prepared.input()['supportProfile'],RELATIONAL_PROFILE)

    def test_old_profile_still_excludes_relational_inventory(self):
        prepared=relational_prepared(identities=('old',),profile=PROFILE)
        self.assertEqual(evaluate_catalog_support(prepared)['closedSourceInventory']['state'],'unavailable')

    def test_missing_duplicate_authored_id_and_other_record_artifact_refuse(self):
        for mutation in ('missing','duplicate','authored_id','wrong_record_artifact','wrong_document'):
            core=copy.deepcopy(self.evidence['coreAssertionIdentities'])
            entries=core['entries'];keys=[e for e in entries if e['ruleName']=='core.keys']
            if mutation=='missing':entries.remove(keys[0])
            elif mutation=='duplicate':entries.append(copy.deepcopy(keys[0]))
            elif mutation=='authored_id':keys[0]['assertion']['authoredIdentity']='other'
            elif mutation=='wrong_record_artifact':keys[0]['ownerEvidence']=keys[2]['ownerEvidence']
            else:keys[0]['assertion']['owner']['documentId']='other'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):self.inventory(core=core)

    def test_ordered_owner_key_and_relationship_meaning_substitution_refuses(self):
        for operation in ('keys','relationships'):
            observations=copy.deepcopy(self.evidence['ownerObservations'])
            selected=next(o for o in observations['observations'] if o['operation']==operation)
            meaning=selected['result']['observation']['meaning']
            if operation=='keys':meaning['keys'][1]['fields'].reverse()
            else:meaning['relationships'][0]['targetMultiplicity']['max']=3
            with self.subTest(operation=operation), self.assertRaises(ValueError):self.inventory(observations=observations)

    def test_absent_and_authored_empty_lists_are_distinct(self):
        for present in (False,True):
            source=relational_document();module=source['modules'][0]
            if present:module['relationships']=[]
            else:del module['relationships']
            for element in module['elements'][:2]:del element['keys']
            prepared=relational_prepared(source,identities=('empty',))
            inventory=evaluate_catalog_support(prepared)['closedSourceInventory']
            self.assertEqual(inventory['state'],'inventoried')
            self.assertFalse(any(e['ruleName'] in ('core.keys','core.relationships') for e in inventory['entries']))
            evidence=decode_owner_evidence_json(prepared.report_evidence_bytes)
            states=[o['result']['observation']['meaning']['state'] for o in evidence['ownerObservations']['observations'] if o['operation'] in ('keys','relationships')]
            self.assertEqual(states,['known' if present else 'missing','missing','missing'])

    def test_authored_empty_keys_refuse_under_original_umf_schema(self):
        from truss import PreparationRejected
        source=relational_document();source['modules'][0]['relationships']=[]
        source['modules'][0]['elements'][0]['keys']=[]
        with self.assertRaises(PreparationRejected) as refused:relational_prepared(source,identities=('empty',))
        self.assertIn(b'keys',b''.join(refused.exception.diagnostics))

    def test_cross_module_endpoint_order_and_unbounded_multiplicity_preserved(self):
        source=relational_document();module=source['modules'][0]
        moved=[e for e in module['elements'] if e['id']=='B' or e['id'].startswith('B-')]
        module['elements']=[e for e in module['elements'] if e not in moved]
        for ref in moved[0]['members']:ref['module']='q'
        for key in moved[0]['keys']:
            for ref in key['fields']:ref['module']='q'
        source['modules'].append({'id':'q','namespace':'q','elements':moved,'extensions':{}})
        relation=module['relationships'][0]
        relation['source']=[{'module':'q','element':'B'},{'module':'m','element':'A'}]
        relation['target']=[{'module':'q','element':'B','key':'a-primary'},{'module':'m','element':'A','key':'a-primary'}]
        relation['sourceMultiplicity']['max']='*'
        prepared=relational_prepared(source,identities=('cross',))
        self.assertEqual(evaluate_catalog_support(prepared)['closedSourceInventory']['state'],'inventoried')
        original=prepared.documents[0].observation()['source']['modules'][0]['relationships'][0]
        self.assertEqual(original,relation)

    def test_unknown_nested_qualifiers_remain_unavailable(self):
        for path in ('key','field_ref','relationship','source_endpoint','target_endpoint','multiplicity'):
            source=relational_document();module=source['modules'][0]
            key=module['elements'][0]['keys'][0];relation=module['relationships'][0]
            selected={'key':key,'field_ref':key['fields'][0],'relationship':relation,
                'source_endpoint':relation['source'][0],'target_endpoint':relation['target'][0],
                'multiplicity':relation['sourceMultiplicity']}[path]
            selected['futureQualifier']={'opaque':True}
            with self.subTest(path=path):
                prepared=relational_prepared(source,identities=('unknown',))
                try:result=evaluate_catalog_support(prepared)
                except ValueError:continue
                self.assertEqual(result['closedSourceInventory']['state'],'unavailable')

if __name__=='__main__':unittest.main(verbosity=2)
