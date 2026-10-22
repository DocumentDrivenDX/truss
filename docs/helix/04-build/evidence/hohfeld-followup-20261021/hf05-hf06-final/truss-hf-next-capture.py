from pathlib import Path
import sys,os,json,tempfile,subprocess,hashlib
import psycopg
from truss import LocalPostgres
from truss._migration_verify import structure,acl,roles,context,canonical
ROOT=Path('/Users/erik/Projects/truss');OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'packages/python/tests'))
from test_catalog_relational_support import relational_document
model=relational_document();model['id']='adoc';model['extensions']={'x-migration-opaque':{'future':[3,1,4],'null':None}};model['vocabularies']={'x-migration-opaque':{'version':'1.0.0'}}
(OUT/'model.json').write_text(json.dumps(model,indent=2))
oldroot=ROOT/'packages/python/src/truss/_migrations';oldmanifest=json.loads((oldroot/'manifest.json').read_bytes());old=json.loads((oldroot/(oldmanifest['target']+'.json')).read_bytes())
with LocalPostgres(OUT/'data') as pg:
 uri=pg.info.connection_uri
 result=subprocess.run([sys.executable,str(ROOT/'packages/python/tests/runtime_migration_fixture.py'),uri,str(OUT/'model.json'),str(OUT/'population.json')],text=True,capture_output=True)
 (OUT/'producer.stdout').write_text(result.stdout);(OUT/'producer.stderr').write_text(result.stderr)
 if result.returncode:raise RuntimeError(result.stderr)
 with psycopg.connect(uri,autocommit=True) as c:
  with c.cursor() as cursor:
   cursor.execute('SET search_path=pg_catalog,pg_temp');ctx,owner,registrar=context(cursor);inventory=structure(cursor);rolemap=roles(cursor,owner,registrar)
   prof={kind:[] for kind in ['owner','registrar','administrator','reader','writer','feed','audit','public']}
   for kind,name,objowner,grantee,priv,grantable,grantor in acl(cursor,full_names=True):
    kinds=rolemap.get(grantee)
    if not kinds or len(kinds)!=1:raise AssertionError((grantee,kinds))
    prof[next(iter(kinds))].append([kind,name,priv,grantable])
   for k in prof:prof[k].sort()
   cursor.execute('SELECT preparation_configuration FROM truss.catalog_runtime_installation');configuration=cursor.fetchone()[0]
   raw=(ROOT/'packages/python/src/truss/_catalog_runtime/manifest.json').read_bytes();digest=hashlib.sha256(raw).hexdigest()
   artifact=dict(inventory=inventory,acl=prof,configuration=configuration,manifest=json.loads(raw),sha256=digest,aclNameProfile='truss-native-acl-names/0.2',definitionAlternatives=old['definitionAlternatives'],initializationAlternatives=old['initializationAlternatives'])
   (OUT/'target.json').write_bytes(canonical(artifact))
   cursor.execute('SHOW TimeZone');print(digest,cursor.fetchone(),flush=True)
 # Logical restore into another database, verify exact known deparse forms only.
 with psycopg.connect(uri,autocommit=True) as c:c.execute('CREATE DATABASE restored')
 params=psycopg.conninfo.conninfo_to_dict(uri);params['dbname']='restored';restored_uri=psycopg.conninfo.make_conninfo(**params)
 from pgserver._commands import POSTGRES_BIN_PATH
 backup=OUT/'target.dump'
 for command in ([str(POSTGRES_BIN_PATH/'pg_dump'),'--dbname',uri,'--format=custom','--file',str(backup)],[str(POSTGRES_BIN_PATH/'pg_restore'),'--dbname',restored_uri,'--exit-on-error',str(backup)]):
  r=subprocess.run(command,capture_output=True,text=True)
  if r.returncode:raise RuntimeError(r.stderr)
 with psycopg.connect(restored_uri,autocommit=True) as restored:
  with restored.cursor() as rc:rc.execute('SET search_path=pg_catalog,pg_temp');restored_inventory=structure(rc)
 from truss._migration_verify import matches_inventory
 assert matches_inventory(restored_inventory,artifact),'Unreviewed restore definition delta'
 (OUT/'restored-inventory.json').write_bytes(canonical(restored_inventory))
