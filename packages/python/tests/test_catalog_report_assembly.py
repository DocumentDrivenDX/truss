"""Untrusted offline vectors exercise shape/codec, never acceptance."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from truss._catalog_report_assembly import encode_unissued_complete_report_wire,ENFORCEMENT_SHA256
from truss._catalog_report_semantics import canonical_numeric_free
from truss._report_schema import validate_complete_report
ROOT=Path(__file__).resolve().parents[3]

def vector():
    report=json.loads((ROOT/'docs/helix/03-test/report-wire-untrusted.fixture.json').read_bytes())['report']
    report['interfaceVersion']='truss-acceptance-report/0.3.0-proposal'
    report['lifecycleProfile']=dict(report['reportProfile'])
    report['reactivations']=[]
    enforcement={'identity':'truss-catalog-enforcement-projection','version':'0.1.0','sha256':ENFORCEMENT_SHA256}
    report['assertions']['reportProfile']=enforcement
    digest=sha256(b'truss-canonical/0.1.0\ntruss-catalog-assertion-inventory/0.1.0\n'+canonical_numeric_free(report['assertions']['entries'])).hexdigest()
    report['assertions']['assertionInventorySha256']=digest
    sources={'originalInstalledExecution':report['originalExecution'],
        'admittedLayout':report['acceptedInput']['layoutProfile'],
        'registeredEnforcementReportProfile':enforcement,
        'registeredAcceptanceReportProfile':report['reportProfile']}
    projection={'producedFields':{k:v for k,v in report.items() if k not in ('reportProfile','originalExecution','assertions')},
        'enforcementSourceFields':{'catalogRevision':report['rev'],'entries':report['assertions']['entries'],
            'assertionInventorySha256':digest}}
    return report,projection,sources

class ReportAssemblyTests(unittest.TestCase):
    def test_complete_wire_and_owner_schema_agree(self):
        report,projection,sources=vector()
        result=encode_unissued_complete_report_wire(projection,sources)
        self.assertEqual(bytes.fromhex(result.original_utf8_hex),canonical_numeric_free(report))
        validate_complete_report(report)
        script="""
import {createProposedComposedAcceptanceReportHandoff} from './packages/umf-bun/src/canonical-report-handoff';
const codec=await createProposedComposedAcceptanceReportHandoff('/Users/erik/Projects/umf/package.json');
const reports=JSON.parse(await Bun.stdin.text());
console.log(JSON.stringify(reports.map(report=>{try{codec.prepare(new TextEncoder().encode(JSON.stringify(report)));return true}catch{return false}})));
"""
        candidates=[report]
        for key in ('origin','journalOrigin','captureProfile','contextEvidence'):
            candidate=copy.deepcopy(report);candidate['originalExecution'][key]={};candidates.append(candidate)
        candidate=copy.deepcopy(report);candidate['counts']['typesAdded']='01';candidates.append(candidate)
        checked=subprocess.run(['/opt/homebrew/bin/bun','-e',script],cwd=ROOT,input=json.dumps(candidates).encode(),capture_output=True,check=True)
        self.assertEqual(json.loads(checked.stdout),[True]+[False]*(len(candidates)-1))
        for candidate in candidates[1:]:
            with self.assertRaises(ValueError):validate_complete_report(candidate)

    def test_nested_execution_and_wrong_digest_refuse(self):
        _,projection,sources=vector()
        for key in ('origin','journalOrigin','captureProfile','contextEvidence'):
            changed=copy.deepcopy(sources);changed['originalInstalledExecution'][key]={}
            with self.subTest(key=key),self.assertRaises(ValueError):encode_unissued_complete_report_wire(projection,changed)
        projection['enforcementSourceFields']['assertionInventorySha256']='0'*64
        with self.assertRaisesRegex(ValueError,'digest correspondence'):encode_unissued_complete_report_wire(projection,sources)

    def test_schema_substitution_refuses(self):
        report,_,_=vector()
        with patch('truss._report_schema.SCHEMA_PINS',{'acceptance-report-v0.3.proposal.schema.json':'0'*64}):
            with self.assertRaisesRegex(ValueError,'schema pin mismatch'):validate_complete_report(report)
        with patch('truss._report_schema.SCHEMA_PINS',{'missing.schema.json':'0'*64}):
            with self.assertRaises(FileNotFoundError):validate_complete_report(report)

    def test_every_required_field_and_extra_claim_refuse(self):
        report,_,_=vector()
        for key in report:
            candidate=copy.deepcopy(report);del candidate[key]
            with self.subTest(key=key),self.assertRaises(ValueError):validate_complete_report(candidate)
        report['accepted']=True
        with self.assertRaises(ValueError):validate_complete_report(report)
