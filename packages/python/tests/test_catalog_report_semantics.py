"""Independent canonical vectors and original source report-field projection."""
import base64
import copy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from test_catalog_support import selected
from test_preparation import CONFIG,prepare
from test_catalog_staging import native_document
from truss import CatalogDocument
from truss._catalog_support import PROFILE as SUPPORT_PROFILE,evaluate_catalog_support
from truss._catalog_report_semantics import canonical_numeric_free,compose_catalog_report_semantics

ROOT=Path(__file__).resolve().parents[3]

class CatalogReportSemanticsTests(unittest.TestCase):
    def test_independent_canonical_bytes_and_domain_vectors(self):
        vectors=json.loads((ROOT/'docs/helix/02-design/contracts/bindings/canonical-byte-v0.1.vectors.json').read_text())['vectors']
        for vector in vectors:
            raw=bytes.fromhex(vector['canonicalUtf8Hex'])
            with self.subTest(name=vector['name']):
                self.assertEqual(canonical_numeric_free(json.loads(raw)),raw)
                self.assertEqual(sha256(b'truss-canonical/0.1.0\n'+vector['domain'].encode()+b'\n'+raw).hexdigest(),vector['sha256'])
        self.assertEqual(canonical_numeric_free({'\U00010000':'é','\ue000':'\n\t'}),b'{"\xee\x80\x80":"\\u000a\\u0009","\xf0\x90\x80\x80":"\xc3\xa9"}')
        self.assertNotEqual(canonical_numeric_free('é'),canonical_numeric_free('e\u0301'))

    def test_canonical_refuses_numbers_surrogates_and_capacity(self):
        for value in (1,1.0,'\ud800',{'\ud800':None},[None]*4097):
            with self.subTest(kind=type(value)),self.assertRaises(ValueError):canonical_numeric_free(value)

    def test_projection_and_exact_digest(self):
        original=selected();support=evaluate_catalog_support(original)
        result=compose_catalog_report_semantics(original,support,'1')
        self.assertEqual(result['catalogRevision'],'1')
        self.assertEqual(result['extensions'],[])
        fields={'assertion','source','ruleName','ruleNameOrigin','enforcement','reason'}
        self.assertTrue(all(set(entry)==fields for entry in result['assertionEntries']))
        self.assertEqual(len(result['assertionEntries']),7)
        keys=[(e['assertion']['owner']['documentId'],e['assertion']['owner']['moduleId'],e['assertion']['sourcePointer'],e['ruleName']) for e in result['assertionEntries']]
        self.assertEqual(keys,sorted(keys,key=lambda key:tuple(v.encode() for v in key)))
        raw=base64.b64decode(result['canonicalAssertionBytesBase64'])
        self.assertEqual(json.loads(raw),result['assertionEntries'])
        self.assertEqual(result['assertionInventorySha256'],sha256(b'truss-canonical/0.1.0\ntruss-catalog-assertion-inventory/0.1.0\n'+raw).hexdigest())
        self.assertIn('installedLayoutProfile',result['unresolvedBindings'])
        self.assertNotIn('layoutProfile',result)
        self.assertFalse(result['acceptedReportQualified'])
        # Validate the governing entry subschema without inventing report identities.
        script="""
import Ajv from './packages/python/src/truss/_umf/runtime/node_modules/ajv/dist/2020.js';
const source=await Bun.file('./docs/helix/02-design/contracts/enforcement-report-v0.1.schema.json').json();
const validate=new Ajv({strict:true}).compile({$schema:source.$schema,type:'array',items:{$ref:'#/$defs/entry'},$defs:source.$defs});
const data=JSON.parse(await Bun.stdin.text());
if(!validate(data.projected))throw Error(JSON.stringify(validate.errors));
if(validate(data.original))throw Error('Owner evidence must not pass the closed entry schema');
console.log('closed enforcement entry schema passed; extra owner evidence refused');
"""
        checked=subprocess.run(['/opt/homebrew/bin/bun','-e',script],cwd=ROOT,
            input=json.dumps({'projected':result['assertionEntries'],'original':support['closedSourceInventory']['entries']}).encode(),
            capture_output=True,timeout=30)
        self.assertEqual(checked.returncode,0,checked.stderr.decode())

    def test_original_multidocument_membership(self):
        config=copy.deepcopy(CONFIG);config['supportProfile']=dict(SUPPORT_PROFILE)
        original=prepare((native_document('a'),native_document('b')),config)
        result=compose_catalog_report_semantics(original,evaluate_catalog_support(original),'2')
        self.assertEqual(len(result['umf']),1)
        self.assertEqual(result['umfMembership'][0]['documentIds'],['a','b'])
        self.assertEqual(result['umf'][0]['interpretationProfile'],original.input()['documents'][0]['umfProfile'])
        self.assertEqual(len(result['assertionEntries']),14)

    def test_original_support_and_profile_substitution_refuse(self):
        original=selected();support=evaluate_catalog_support(original)
        for change in ('omit','duplicate','policy'):
            modified=copy.deepcopy(support)
            if change=='omit':modified['closedSourceInventory']['entries'].pop()
            elif change=='duplicate':modified['closedSourceInventory']['entries'][-1]=modified['closedSourceInventory']['entries'][0]
            else:modified['supportedSubset']['sha256']='0'*64
            with self.subTest(change=change),self.assertRaises(ValueError):
                compose_catalog_report_semantics(original,modified,'1')
        with patch('truss._catalog_report_semantics.PROFILE_SHA256','0'*64),self.assertRaises(ValueError):
            compose_catalog_report_semantics(original,support,'1')
        for revision in ('0','01','-1','2147483648'):
            with self.subTest(revision=revision),self.assertRaises(ValueError):
                compose_catalog_report_semantics(original,support,revision)
