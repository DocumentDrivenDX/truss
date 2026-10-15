"""Fresh original Products catalog/binding and published compiler compatibility probe."""
import argparse
from pathlib import Path
import subprocess,json,hashlib,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[5]/'packages/python/examples'))
from adopter_workflow import transaction,success
import psycopg
from psycopg import sql
from truss import LocalPostgres,CatalogDocument,ModuleAccessGrant,CatalogRegistration
from truss.catalog_runtime import _release,_pin_cursor
from truss._preparation_program import compile_preparation_program
import weft
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('umf_repository',type=Path);parser.add_argument('output',type=Path)
parser.add_argument('--bun',default='bun');args=parser.parse_args()
root=args.output.resolve();root.mkdir()
import weft.weft as native
binary_sha=hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest()
assert weft.__version__=='0.4.30' and binary_sha=='32e8c830bbdbbd98b9577f19dbd0a5cfbacdf9a3d7610df525b29b385ff2b78f', 'Use the verified published macOS arm64 Weft wheel'
raw=subprocess.check_output(['git','-C',str(args.umf_repository.resolve()),'show','ed6766987cd403fb513a82d49102596f6e727235:docs/helix/04-build/evidence/security/preparation-sources-20261015/input.json'])
assert hashlib.sha256(raw).hexdigest()=='4ef6a9faf4c8e098f43a1949bc425145570f6e7616f22af9dabbe773c00d9e19'
p=json.loads(raw);request=json.loads(p['request']['utf8']);model=request['model'];content=model['utf8'].encode();document=json.loads(content)
assert hashlib.sha256(content).hexdigest()==model['sha256']==request['modelPin']['sha256']
(root/'original-input.json').write_bytes(raw);(root/'original-model.json').write_bytes(content)
manifest,digest,_=_release()
assert digest=='99ae7218e0e3e68e0a3682e43949089185d967eb21bbf31deb0b8f8f6fc2de9a'
with LocalPostgres(root/'postgres') as runtime:
 params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
 with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as admin:
  with transaction(admin) as (a,t):installed=success(a.install_in_transaction(t))
  admin.execute('CREATE ROLE products_person LOGIN;CREATE ROLE products_reader NOLOGIN;CREATE ROLE products_writer NOLOGIN')
  admin.execute(sql.SQL('GRANT {} TO products_person WITH SET FALSE').format(sql.Identifier(installed.registrar_role)))
  with psycopg.connect(**dict(params,user='products_person'),autocommit=True,options='-c statement_timeout=10000') as person:
   with transaction(person) as (a,t):
    prepared=a.prepare_catalog((CatalogDocument(document['id'],request['modelPin']['revision'],content,model['sha256']),),source_version='0.8.0',bun_executable=args.bun)
    accepted=success(a.accept_in_transaction(t,prepared,request_key='original-products'))
    assert isinstance(accepted,CatalogRegistration),repr(accepted)
   with transaction(admin) as (a,t):success(a.configure_module_access_in_transaction(t,(ModuleAccessGrant(document['id'],'sales','products_reader','products_writer'),)))
   admin.execute('GRANT products_reader TO products_person WITH SET FALSE')
   admin.execute(sql.SQL('REVOKE {} FROM products_person').format(sql.Identifier(installed.registrar_role)))
   with transaction(person,read_only=True) as (a,t):
    def export(cursor,observed):
     _pin_cursor(cursor)
     cursor.execute('SELECT truss.query_binding(%s::jsonb,%s,%s,%s,%s,%s)',(json.dumps([document['id']]),10000,10000,16777216,manifest['releaseId'],digest),prepare=False)
     return bytes(cursor.fetchone()[0])
    bundle_raw=success(a._host._run_operation(t,export))
   bundle=json.loads(bundle_raw);binding_raw=bundle['bindingJson'].encode()
   (root/'native-query-bundle.json').write_bytes(bundle_raw);(root/'native-binding.json').write_bytes(binding_raw)
   binding={'mediaType':'application/json','utf8':binding_raw.decode(),'sha256':hashlib.sha256(binding_raw).hexdigest()}
   outcome={'scope':'Fresh public catalog and actual binding; no seed, SCRAM/Subject/security admission or effects claim','runtime':manifest['releaseId'],'runtimeSha256':digest,'bindingSha256':binding['sha256'],'authority':False,'securityReady':False,'compilerVersion':weft.__version__,'compilerBinarySha256':binary_sha,'compilerSourcePin':'50464e03edc9db6dd1ea566f2e110b2aa4e6164f'}
   try:
    program=compile_preparation_program(weft.MutationCompiler,compiler_source_pin='50464e03edc9db6dd1ea566f2e110b2aa4e6164f',configuration=p['configuration']['utf8'].encode(),request=p['request']['utf8'].encode(),binding_artifact=json.dumps(binding,separators=(',',':')).encode(),evidence=('Actual fresh Truss066 public catalog binding',))
    outcome['compilerOutcome']='lowered'
    (root/'fresh-compile-response.json').write_bytes(program.compile_response);(root/'fresh-lowering.json').write_bytes(program.lowering)
   except Exception as e:
    outcome.update(compilerOutcome='refused',exceptionType=type(e).__name__,message=str(e))
   (root/'receipt.json').write_text(json.dumps(outcome,indent=2)+'\n');print(json.dumps(outcome,indent=2))
