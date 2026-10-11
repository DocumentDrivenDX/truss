"""Real selected metadata policy on original Python UMF preparation and staging."""
import copy
import json
import unittest
from test_preparation import CONFIG,prepare
from test_catalog_staging import native_document,CatalogNativeFixture
from truss import CatalogDocument
from truss._catalog_support import PROFILE,evaluate_catalog_support
from truss._catalog_staging import stage_new_catalog,stage_catalog_report_basis


def selected(value=None):
    source=json.loads(native_document('support').content) if value is None else value
    config=copy.deepcopy(CONFIG);config['supportProfile']=dict(PROFILE)
    return prepare((CatalogDocument('support','r1',json.dumps(source).encode()),),config)

class CatalogSupportTests(unittest.TestCase):
    def test_known_original_metadata_and_fixture_unavailable(self):
        result=evaluate_catalog_support(selected())
        self.assertEqual(result['state'],'evaluated')
        self.assertGreater(len(result['requiredObservations']),0)
        self.assertGreater(len(result['retainedObservations']),0)
        self.assertFalse(result['assertionInventoryComplete'])
        self.assertFalse(result['supportSemanticsQualified'])
        self.assertEqual(evaluate_catalog_support(prepare((native_document('legacy'),))),{'state':'unavailable','reason':'unregistered_support_policy'})

    def test_missing_required_metadata_refuses_before_sql(self):
        class NoCalls:
            def run(self,*args,**kwargs):raise AssertionError('No SQL permitted')
        for target,field in ((0,'members'),(1,'name'),(1,'nullability'),(1,'cardinality')):
            value=json.loads(native_document('support').content)
            del value['modules'][0]['elements'][target][field]
            original=selected(value)
            for report in (False,True):
                with self.subTest(field=field,report=report),self.assertRaises(ValueError):
                    stage_new_catalog(NoCalls(),original,origin_bytes=b'{}',_report_basis=report)

    def test_unknown_required_scalar_refuses_and_absence_retains_duty(self):
        value=json.loads(native_document('support').content)
        value['modules'][0]['elements'][1]['scalarType']='vendor-number'
        original=selected(value)
        with self.assertRaises(ValueError):evaluate_catalog_support(original)
        del value['modules'][0]['elements'][1]['scalarType']
        result=evaluate_catalog_support(selected(value))
        self.assertEqual(result['unresolvedValueFamilies'],[{'documentId':'support','moduleId':'m','elementId':'label','duty':'value_family_unresolved'}])

    def test_unknown_extension_and_unspecified_are_preserved(self):
        value=json.loads(native_document('support').content)
        value['vocabularies']={'future':{'version':'99.0.0'}};value['extensions']={'future':{'opaque':'retain'}}
        field=value['modules'][0]['elements'][1];field['nullability']='unspecified';field['cardinality']='unspecified'
        original=selected(value);result=evaluate_catalog_support(original)
        self.assertEqual(original.documents[0].observation()['source']['modules'][0]['elements'][1]['nullability'],'unspecified')
        self.assertGreater(len(result['retainedExtensions']['extensions']),0)
        self.assertFalse(result['enforcementQualified'])

    def test_empty_membership_and_optional_absence_are_preserved(self):
        value=json.loads(native_document('support').content)
        value['modules'][0]['elements'][0]['members']=[]
        result=evaluate_catalog_support(selected(value))
        self.assertEqual(result['state'],'evaluated')
        self.assertFalse(result['assertionInventoryComplete'])

    def test_partial_selected_facets_refuse(self):
        value=json.loads(native_document('support').content)
        value['modules'][0]['elements'][1]['facets']={'vendor_limit':{'opaque':'retained'}}
        original=selected(value)
        with self.assertRaises(ValueError):evaluate_catalog_support(original)

    def test_profile_substitution_remains_unavailable(self):
        config=copy.deepcopy(CONFIG);config['supportProfile']=dict(PROFILE,sha256='0'*64)
        original=prepare((native_document('substitute'),),config)
        self.assertEqual(evaluate_catalog_support(original)['state'],'unavailable')

    def test_source_version_not_in_selected_policy_refuses(self):
        value=json.loads(native_document('support').content);value['umf']='0.8.0'
        with self.assertRaises(ValueError):evaluate_catalog_support(selected(value))

class CatalogSupportNativeTests(CatalogNativeFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from test_catalog_staging import ROOT
        connection=cls.Connection(**cls.kwargs)
        try:connection.run((ROOT/'packages/postgresql/native/catalog-report/empty-graph.sql').read_text())
        finally:connection.close()

    def test_actual_policy_decision_survives_native_staging(self):
        self.connection.run('ROLLBACK');self.connection.run('BEGIN')
        original=selected();self.admit(original)
        basis=stage_catalog_report_basis(self.connection,original,origin_bytes=b'{}')
        payload=json.loads(basis.basis_bytes)
        self.assertEqual(payload['supportPolicyDecision'],evaluate_catalog_support(original))
        self.assertEqual(payload['missingFields'],['interfaceVersion','reportProfile','originalExecution','umf','assertions','extensions'])
        self.assertFalse(payload['acceptedReportQualified'])
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[1]])
