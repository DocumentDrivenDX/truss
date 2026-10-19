# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native observed CoreLiteral texts handed to original UMF; no release authority.
@covers US-056-AC2
@covers US-056-AC10
"""
import json,hashlib,os,sys,tempfile,unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from time import sleep
import psycopg
from truss import LocalPostgres
from truss.execution import Ok,Error
from truss.psycopg_host import adopt_psycopg_host
from truss._psycopg_subject_observation import _SubjectSelection,_observe_ordinary_subject,_observe_ordinary_subject_key
from truss._umf_key_tuples import encode_literal_key_tuple
from test_umf_literal_key_tuples import key_source,FIXTURE

class NativeLiteralSubjectKeyTests(unittest.TestCase):
 def test_native_five_family_subject_values_use_original_semantic_owner(self):
  directory=os.environ.get('TRUSS_SUBJECT_OWNER_MODULE_DIR')
  if not directory:raise RuntimeError('Original compiled subject-inspection owner required')
  sys.path.insert(0,directory);import weft
  self.assertEqual(Path(weft.__file__).resolve(),(Path(directory)/'weft.so').resolve())
  kinds=['string','boolean','integer','decimal','binary']
  source=key_source([{'id':'k'+str(i),'scalarType':kind,**({'precision':30,'scale':4}if kind=='decimal'else{})}for i,kind in enumerate(kinds)])
  document=json.loads(source);request=json.loads((FIXTURE/'security-mapping-request.json').read_bytes())
  request['modules'][0]['documentJson']=source.decode();request['modules'][0]['pin']['sha256']=hashlib.sha256(source).hexdigest()
  def ref(element):return {'documentId':document['id'],'moduleId':'m','elementId':element}
  ontology=json.loads(request['ontologyJson']);ontology.update(subject=ref('Staff'),entities=[{'type':ref('Staff'),'keyId':'pk','fields':[{'ref':ref('k'+str(i)),'protection':'unprotected'}for i in range(5)]}],associations=[],context=[])
  request['ontologyJson']=json.dumps(ontology)
  policy=json.loads(request['policyJson']);policy['rules']=[{'id':'allow','effect':'permit','actions':['read'],'target':[ref('Staff')],'condition':{'op':'literal','value':True}}];request['policyJson']=json.dumps(policy)
  profile=json.loads(request['queryProfileJson']);profile.update(modelPins=[request['modules'][0]['pin']],policySha256=hashlib.sha256(request['policyJson'].encode()).hexdigest(),ontologySha256=hashlib.sha256(request['ontologyJson'].encode()).hexdigest(),targets=[ref('Staff')],bindings=[]);request['queryProfileJson']=json.dumps(profile)
  request['sql']='SELECT r.k0 FROM Staff r';request['parameters']={}
  original_request=json.dumps(request).encode()
  with tempfile.TemporaryDirectory(prefix='native-literal-key-',dir='/private/tmp') as directory:
   with LocalPostgres(Path(directory)/'data') as runtime:
    params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
    with psycopg.connect(**params,autocommit=True) as admin:
     admin.execute('CREATE ROLE literal_alice LOGIN;CREATE ROLE literal_delegate;GRANT literal_delegate TO literal_alice;CREATE SCHEMA literal_diag;GRANT USAGE ON SCHEMA literal_diag TO literal_alice')
     admin.execute("""CREATE FUNCTION literal_diag.subject(actor text) RETURNS TABLE(k0 text,k1 text,k2 text,k3 text,k4 text)
      LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
      SELECT jsonb_build_object('string','Δ'||chr(65279))::text,jsonb_build_object('boolean',true)::text,
       jsonb_build_object('integerToken',9007199254740993::numeric::text)::text,
       jsonb_build_object('decimalToken',9007199254740993.0000::numeric::text)::text,
       jsonb_build_object('binaryHex',encode(decode('0001','hex'),'hex'))::text
       WHERE actor=SESSION_USER::text AND SESSION_USER='literal_alice' $$""")
     options=dict(params,user='literal_alice',options='-c statement_timeout=2000')
     with psycopg.connect(**options) as connection:
      connection.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
      host=adopt_psycopg_host(connection);transaction=host.adopt_transaction(isolation='repeatable_read',access_mode='read_only');self.assertIsInstance(transaction,Ok)
      selection=_SubjectSelection(original_request,source,'m','Staff','pk','literal_alice','literal_diag','subject',tuple('k'+str(i)for i in range(5)))
      observed=_observe_ordinary_subject(host,transaction.value,selection,weft.inspect_security_mapping_subject_key_json);self.assertIsInstance(observed,Ok)
      observation=observed.value
      key=encode_literal_key_tuple(source,observation.identity,observation.values,bun_executable='/opt/homebrew/bin/bun')
      expected=[{'string':'Δ\uFEFF'},{'boolean':True},{'integerToken':'9007199254740993'},{'decimalToken':'9007199254740993.0000'},{'binaryHex':'0001'}]
      self.assertEqual(json.loads(key.original_receipt_bytes)['values'],expected)
      self.assertEqual(key.literal_texts,observation.values)
      encodings=('core-literal-json',)*5
      def bound():return _observe_ordinary_subject_key(host,transaction.value,selection,weft.inspect_security_mapping_subject_key_json,encodings,bun_executable='/opt/homebrew/bin/bun')
      for invalid in [('core-literal-json',)*4,('core-literal-json',)*33,('foreign',)*5]:
       invoked=[]
       with self.assertRaises(ValueError):_observe_ordinary_subject_key(host,transaction.value,selection,lambda *_:invoked.append(True),invalid,bun_executable='/opt/homebrew/bin/bun')
       self.assertEqual(invoked,[])
      combined=bound();self.assertIsInstance(combined,Ok);self.assertEqual(combined.value.tuple_bytes,key.tuple_bytes)
      self.assertEqual(combined.value.original_receipt_bytes,key.original_receipt_bytes)
      self.assertIsInstance(_observe_ordinary_subject_key(host,transaction.value,selection,weft.inspect_security_mapping_subject_key_json,('string',)*5,bun_executable='/opt/homebrew/bin/bun'),Error)
      self.assertIsInstance(bound(),Ok) # Original codec refusal was locally contained.
      nested=[]
      def nested_encoder(*args,**kwargs):
       nested.append(host._run_operation(transaction.value,lambda *_:'forbidden nested publication'))
       return encode_literal_key_tuple(*args,**kwargs)
      with patch('truss._umf_key_tuples.encode_literal_key_tuple',side_effect=nested_encoder):self.assertIsInstance(bound(),Ok)
      self.assertEqual(len(nested),1);self.assertIsInstance(nested[0],Error)
      def role_changing_encoder(*args,**kwargs):
       result=encode_literal_key_tuple(*args,**kwargs)
       connection.execute('SET LOCAL ROLE literal_delegate')
       return result
      with patch('truss._umf_key_tuples.encode_literal_key_tuple',side_effect=role_changing_encoder):self.assertIsInstance(bound(),Error)
      self.assertEqual(connection.execute('SELECT CURRENT_USER::text').fetchone(),('literal_alice',))
      self.assertIsInstance(bound(),Ok)
      for i,foreign in [(0,'{"boolean":true}'),(2,'{"integerToken":"01"}'),(3,'{"decimalToken":"1.00001"}')]:
       values=list(observation.values);values[i]=foreign
       with self.assertRaises(ValueError):encode_literal_key_tuple(source,observation.identity,tuple(values),bun_executable='/opt/homebrew/bin/bun')
      entered=[]
      def delayed_encoder(*args,**kwargs):
       entered.append(True);sleep(.2)
       return encode_literal_key_tuple(*args,**kwargs)
      host._deadline_ms=100
      with patch('truss._umf_key_tuples.encode_literal_key_tuple',side_effect=delayed_encoder):
       expired=bound();self.assertIsInstance(expired,Error)
      self.assertEqual(entered,[True])
      self.assertEqual(key.literal_texts,observation.values)
      connection.close() # No uncertain host reuse or durability inference.

      host.detach()
      replacement=psycopg.connect(**options)
      replacement.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
      replacement_host=adopt_psycopg_host(replacement)
      replacement_transaction=replacement_host.adopt_transaction(isolation='repeatable_read',access_mode='read_only');self.assertIsInstance(replacement_transaction,Ok)
      changed=[]
      def changed_transaction_encoder(*args,**kwargs):
       candidate=encode_literal_key_tuple(*args,**kwargs)
       replacement.rollback();replacement.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY');changed.append(True)
       return candidate
      try:
       with patch('truss._umf_key_tuples.encode_literal_key_tuple',side_effect=changed_transaction_encoder):
        changed_result=_observe_ordinary_subject_key(replacement_host,replacement_transaction.value,selection,weft.inspect_security_mapping_subject_key_json,encodings,bun_executable='/opt/homebrew/bin/bun')
       self.assertIsInstance(changed_result,Error);self.assertEqual(changed,[True]);self.assertTrue(replacement_host._custody.quarantined)
      finally:replacement.close();replacement_host.detach()
      output=os.environ.get('TRUSS_LITERAL_SUBJECT_EVIDENCE')
      if output:Path(output).write_text(json.dumps({'serverVersion':admin.execute('SHOW server_version').fetchone()[0],'originalRequest':request,'nativeText':observation.values,'nativeUtf8Hex':observation.utf8_hex,'originalReceipt':key.original_receipt_bytes.decode(),'tupleHex':key.tuple_bytes.hex(),'expectedValues':expected,'negativeCases':['wrong scalar family','noncanonical integer','nonrepresentable decimal'],'compositionControls':['one-operation tuple/receipt correspondence','codec refusal contained','nested host operation refused','post-codec effective role change refused/restored','deadline after entered encoding refuses publication','replaced native transaction refuses and quarantines'],'scope':'Historical native observation/semantic encoding only; original helper/host/code trusted; no existence/current authority/key issuance/protected release'},indent=2)+'\n')
