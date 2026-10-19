# SPDX-License-Identifier: MIT OR Apache-2.0
"""Current UMF 0.10 source preparation custody; no native authority."""
import base64
from hashlib import sha256
import json
from pathlib import Path
import unittest
from truss import CatalogDocument, PreparationRejected, prepare_acceptance, prepare_catalog
from truss.catalog_preparation import _configuration
from truss._catalog_report_semantics import canonical_numeric_free

FIXTURES=Path(__file__).parent/'fixtures'
CORE=(FIXTURES/'security-association-core010.json').read_bytes()
BINDING=(FIXTURES/'security-association-binding010.json').read_bytes()

def current_configuration():
 return canonical_numeric_free(_configuration())

def prepare(core=CORE):
 return prepare_catalog((CatalogDocument('domain','schema-natural-1',core),),source_version='0.10.0',bun_executable='/missing/bun')

class SecurityPreparationTests(unittest.TestCase):
 def test_current_source_validation_and_exact_original_artifact_custody(self):
  result=prepare();carrier=result.input()['documents'][0];observed=result.documents[0]
  self.assertEqual(result.input()['binding'],{'state':'absent'})
  self.assertNotIn('bytesBase64',carrier['artifact'])
  self.assertEqual(carrier['artifact']['sha256'],sha256(CORE).hexdigest())
  self.assertEqual(observed.document.content,CORE)
  interpretation=observed.observation()
  self.assertEqual(interpretation['originalText'],CORE.decode('utf8'))
  self.assertEqual(interpretation['source'],json.loads(CORE))
  self.assertTrue(interpretation['sourceValidation']['valid'])
  self.assertFalse(interpretation['sourceValidation']['complete'])
  self.assertEqual(interpretation['sourceValidation']['diagnostics'][0]['code'],'EXPERIMENTAL_CORE_SEMANTIC_TYPES')
  archived=json.loads(result.archive_documents_bytes)[0]
  self.assertEqual(archived['originalText'],CORE.decode('utf8'))
  self.assertEqual(archived['validation']['sourceValidation'],interpretation['sourceValidation'])
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
  diagnostic=json.loads(caught.exception.diagnostics[0]);self.assertEqual(diagnostic['documentId'],'domain')
  owner=diagnostic['validation'];self.assertFalse(owner['valid'])
  self.assertTrue(any(item['code']=='SEMANTIC_TYPE_STRUCTURE' and item['path']=='/modules/0/elements/0/kind' and item['severity']=='error' for item in owner['diagnostics']))
 def test_present_association_binding_is_retained_without_semantic_claim(self):
  choices=json.loads(current_configuration())
  choices['binding']={'state':'present','vocabulary':{'identity':'truss-binary-association-candidate','version':'0.1.0','sha256':sha256(b'opaque association vocabulary pin').hexdigest()},
   'artifact':{'identity':'opaque-association-binding','bytesBase64':base64.b64encode(BINDING).decode('ascii'),'sha256':sha256(BINDING).hexdigest()}}
  prepared=prepare_acceptance((CatalogDocument('domain','schema-natural-1',CORE),),canonical_numeric_free(choices),bun_executable='/missing/bun')
  self.assertEqual(prepared.input()['binding'],choices['binding'])
  self.assertFalse(prepared.provenance.installation_profiles_verified)
  self.assertEqual(prepared.provenance.scope,'original_umf_preparation_only')
  self.assertNotIn('acceptedIds',prepared.input())
  self.assertEqual(prepared.documents[0].document.content,CORE)
 def test_present_binding_digest_substitution_is_rejected(self):
  choices=json.loads(current_configuration())
  choices['binding']={'state':'present','vocabulary':{'identity':'truss-binary-association-candidate','version':'0.1.0','sha256':sha256(b'opaque association vocabulary pin').hexdigest()},
   'artifact':{'identity':'opaque-association-binding','bytesBase64':base64.b64encode(BINDING).decode('ascii'),'sha256':'0'*64}}
  with self.assertRaises(PreparationRejected) as caught:
   prepare_acceptance((CatalogDocument('domain','schema-natural-1',CORE),),canonical_numeric_free(choices),bun_executable='/missing/bun')
  self.assertEqual(caught.exception.reason,'invalid_input')
  self.assertEqual(caught.exception.diagnostics,())

if __name__=='__main__':unittest.main()
