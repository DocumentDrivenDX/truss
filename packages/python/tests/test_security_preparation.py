"""Original security cohort through public preparation; no native authority."""
import base64
from hashlib import sha256
import json
from pathlib import Path
import unittest
from truss import CatalogDocument, PreparationRejected, prepare_acceptance

ROOT=Path(__file__).resolve().parents[3]
FIXTURES=Path(__file__).parent/'fixtures'
CORE=(FIXTURES/'security-association-core.json').read_bytes()
BINDING=(FIXTURES/'security-association-binding.json').read_bytes()

def configuration():
 value=json.loads((ROOT/'docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').read_bytes())['input']
 value={k:v for k,v in value.items() if k not in ('interfaceVersion','documents')}
 value['transforms']=[]
 value['binding']={'state':'present','vocabulary':{'identity':'truss-binary-association-candidate','version':'0.1.0','sha256':sha256(b'not-registered-authority').hexdigest()},'artifact':{'identity':'original-association-candidate','bytesBase64':base64.b64encode(BINDING).decode(),'sha256':sha256(BINDING).hexdigest()}}
 return value

def prepare(core=CORE,choices=None):
 return prepare_acceptance((CatalogDocument('domain','schema-natural-1',core),),json.dumps(configuration() if choices is None else choices).encode())

class SecurityPreparationTests(unittest.TestCase):
 def test_original_security_source_and_present_binding_are_preserved(self):
  choices=configuration();result=prepare(choices=choices);carrier=result.input()['documents'][0]
  self.assertEqual(base64.b64decode(carrier['artifact']['bytesBase64']),CORE)
  self.assertEqual(result.input()['binding'],choices['binding'])
  self.assertEqual(result.documents[0].document.content,CORE)
  self.assertFalse(result.provenance.installation_profiles_verified)
  self.assertEqual(result.provenance.scope,'original_umf_preparation_only')
 def test_complete_owned_security_declarations(self):
  result=prepare();declarations=json.loads(result.declarations_bytes)
  self.assertEqual(len(declarations),1)
  self.assertEqual(len(declarations[0]['records']),5)
  self.assertEqual(sum(len(record['fields']) for record in declarations[0]['records']),9)
  self.assertEqual(sum(len(record['keys']) for record in declarations[0]['records']),5)
  self.assertEqual(declarations[0]['relationships'],[])
 def test_invalid_security_core_is_owner_rejected(self):
  source=json.loads(CORE);source['modules'][0]['elements'][0]['kind']='unissued-kind'
  with self.assertRaises(PreparationRejected) as caught:prepare(json.dumps(source).encode())
  self.assertEqual(caught.exception.reason,'invalid_document')
  diagnostic=json.loads(caught.exception.diagnostics[0]);self.assertEqual(diagnostic['documentId'],'domain');self.assertEqual(diagnostic['originalError']['code'],'INVALID_DOCUMENT')
  owner=json.loads(diagnostic['originalError']['message'])
  self.assertTrue(any(item['code']=='CORE_SCHEMA_PROPERTIES' and item['path']=='/modules/0/elements/0/kind' and item['severity']=='error' for item in owner))
 def test_binding_digest_substitution_refuses(self):
  choices=configuration();choices['binding']['artifact']['sha256']='0'*64
  with self.assertRaises(PreparationRejected) as caught:prepare(choices=choices)
  self.assertEqual(caught.exception.reason,'invalid_input')
  self.assertEqual(caught.exception.diagnostics,())
 def test_preparation_does_not_register_binding_semantics(self):
  choices=configuration();choices['binding']['vocabulary']['identity']='unknown-original-vocabulary'
  result=prepare(choices=choices)
  self.assertEqual(result.input()['binding'],choices['binding'])
  self.assertFalse(result.provenance.installation_profiles_verified)
  self.assertNotIn('acceptedIds',result.input())

if __name__=='__main__':unittest.main()
