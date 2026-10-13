"""Native observed CoreLiteral texts handed to original UMF; no release authority.
@covers US-056-AC2
@covers US-056-AC10
"""
import json,hashlib,os,sys,tempfile,unittest
from pathlib import Path
from dataclasses import replace
import psycopg
from truss import LocalPostgres
from truss.execution import Ok
from truss.psycopg_host import adopt_psycopg_host
from truss._psycopg_subject_observation import _SubjectSelection,_observe_ordinary_subject
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
     admin.execute('CREATE ROLE literal_alice LOGIN;CREATE SCHEMA literal_diag;GRANT USAGE ON SCHEMA literal_diag TO literal_alice')
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
      for i,foreign in [(0,'{"boolean":true}'),(2,'{"integerToken":"01"}'),(3,'{"decimalToken":"1.00001"}')]:
       values=list(observation.values);values[i]=foreign
       with self.assertRaises(ValueError):encode_literal_key_tuple(source,observation.identity,tuple(values),bun_executable='/opt/homebrew/bin/bun')
      connection.rollback();self.assertEqual(key.literal_texts,observation.values)
      host.detach()
      output=os.environ.get('TRUSS_LITERAL_SUBJECT_EVIDENCE')
      if output:Path(output).write_text(json.dumps({'serverVersion':admin.execute('SHOW server_version').fetchone()[0],'originalRequest':request,'nativeText':observation.values,'nativeUtf8Hex':observation.utf8_hex,'originalReceipt':key.original_receipt_bytes.decode(),'tupleHex':key.tuple_bytes.hex(),'expectedValues':expected,'negativeCases':['wrong scalar family','noncanonical integer','nonrepresentable decimal'],'scope':'Historical native observation/semantic encoding only; original helper/host/code trusted; no existence/current authority/key issuance/protected release'},indent=2)+'\n')
