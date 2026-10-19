# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native caller/subject adapter integration in an isolated local server."""
import json,os,subprocess,tempfile,unittest
from pathlib import Path
import psycopg
from truss import LocalPostgres
ROOT=Path(__file__).resolve().parents[3]
class PrincipalRuntimeNativeTests(unittest.TestCase):
 def test_original_native_caller_subject_and_quarantine(self):
  with tempfile.TemporaryDirectory(prefix='truss-principal-runtime-',dir='/private/tmp') as directory:
   with LocalPostgres(Path(directory)/'data') as runtime:
    params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
    with psycopg.connect(**params,autocommit=True) as admin:
     admin.execute('CREATE ROLE principal_alice LOGIN;CREATE ROLE principal_bob LOGIN;CREATE ROLE principal_delegate;GRANT principal_delegate TO principal_alice;CREATE SCHEMA principal_diag')
     admin.execute("""CREATE FUNCTION principal_diag.observe() RETURNS TABLE(native_superuser text,native_bypass text,native_encoding text)
      LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
      SELECT rolsuper::text,rolbypassrls::text,current_setting('client_encoding')::text FROM pg_catalog.pg_roles WHERE rolname=SESSION_USER $$;
      CREATE FUNCTION principal_diag.subject_text(actor text) RETURNS TABLE(staff_id text)
      LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
      SELECT 'alice'::text WHERE actor=SESSION_USER::text AND SESSION_USER='principal_alice' $$;
      CREATE FUNCTION principal_diag.subject_name(actor name) RETURNS TABLE(staff_id text)
      LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
      SELECT 'alice'::text WHERE actor=SESSION_USER AND SESSION_USER='principal_alice' $$;
      CREATE FUNCTION principal_diag.subject_composite(actor text) RETURNS TABLE(staff_id text,ordinal text)
      LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
      SELECT 'alice'::text,'9007199254740993'::text WHERE actor=SESSION_USER::text AND SESSION_USER='principal_alice' $$;
      CREATE FUNCTION principal_diag.subject_typed(actor text) RETURNS TABLE(k0 text,k1 text,k2 text,k3 text,k4 text)
      LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
      SELECT jsonb_build_object('string','Δ'||chr(65279))::text,jsonb_build_object('boolean',true)::text,
       jsonb_build_object('integerToken',9007199254740993::numeric::text)::text,
       jsonb_build_object('decimalToken',9007199254740993.0000::numeric::text)::text,
       jsonb_build_object('binaryHex',encode(decode('0001','hex'),'hex'))::text
       WHERE actor=SESSION_USER::text AND SESSION_USER='principal_alice' $$;
      CREATE FUNCTION principal_diag.subject_wrong_type(actor text) RETURNS TABLE(staff_id name)
      LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$ SELECT 'alice'::name $$;
      GRANT USAGE ON SCHEMA principal_diag TO principal_alice,principal_bob""")
     config={'host':params['host'],'port':int(params.get('port',5432)),'database':params.get('dbname','postgres'),'user':params['user']}
     run=subprocess.run(['/opt/homebrew/bin/bun',str(ROOT/'tests/pg-principal-native-runner.ts')],input=json.dumps(config).encode(),capture_output=True,timeout=60,cwd=ROOT)
     self.assertEqual(run.returncode,0,run.stderr.decode());receipt=json.loads(run.stdout);self.assertEqual(len(receipt['cases']),13)
     receipt['serverVersion']=admin.execute('SHOW server_version').fetchone()[0]
     output=os.environ.get('TRUSS_PRINCIPAL_RUNTIME_EVIDENCE')
     if output:Path(output).write_text(json.dumps(receipt,indent=2)+'\n')
