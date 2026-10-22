from pathlib import Path
import sys,json,hashlib,tempfile,os,subprocess,zipfile
import psycopg
from truss import LocalPostgres
from truss._migration_verify import acl,roles,context,canonical
ROOT=Path('/Users/erik/Projects/truss');OUT=Path('/private/tmp/truss-full-acl-capture');OUT.mkdir(exist_ok=True)
model=Path('/private/tmp/truss-runtime074-ny-v2/model.json');repo=ROOT/'packages/python/src/truss/_migrations';manifest=json.loads((repo/'manifest.json').read_bytes())
with LocalPostgres(OUT/'data') as pg:
 for label,entry in manifest['sourceWheels'].items():
  wheel=Path('/private/tmp/truss-runtime-migration-wheelhouse')/entry['filename']
  if not wheel.exists():wheel=Path('/private/tmp/truss-public-047-assets')/entry['filename']
  assert hashlib.sha256(wheel.read_bytes()).hexdigest()==entry['sha256']
  source=OUT/label;zipfile.ZipFile(wheel).extractall(source)
  with psycopg.connect(pg.info.connection_uri,autocommit=True) as c:c.execute('CREATE DATABASE '+label)
  params=psycopg.conninfo.conninfo_to_dict(pg.info.connection_uri);params['dbname']=label;uri=psycopg.conninfo.make_conninfo(**params)
  result=subprocess.run([sys.executable,str(ROOT/'packages/python/tests/runtime_migration_fixture.py'),uri,str(model),str(OUT/(label+'-population.json'))],env={**os.environ,'PYTHONPATH':str(source)},capture_output=True,text=True)
  (OUT/(label+'-producer.log')).write_text(result.stdout+result.stderr)
  assert result.returncode==0,result.stderr
  with psycopg.connect(uri,autocommit=True) as c:
   with c.cursor() as cursor:
    ctx,owner,registrar=context(cursor);mapping=roles(cursor,owner,registrar);profile={kind:[] for kind in ['owner','registrar','administrator','reader','writer','feed','audit','public']}
    for kind,name,objowner,grantee,priv,grantable,grantor in acl(cursor,full_names=True):
     kinds=mapping[grantee];assert len(kinds)==1
     profile[next(iter(kinds))].append([kind,name,priv,grantable])
    for rows in profile.values():rows.sort()
  digest=entry['runtimeManifestSha256'];supplement=dict(runtimeManifestSha256=digest,aclNameProfile='truss-native-acl-names/0.2',acl=profile)
  (OUT/(digest+'.acl.json')).write_bytes(canonical(supplement));print(label,digest,flush=True)
  with psycopg.connect(uri,autocommit=True) as c:
   for role in ['migration_reader','migration_writer','migration_feed','migration_audit','migration_person']:c.execute(psycopg.sql.SQL('ALTER ROLE {} RENAME TO {}').format(psycopg.sql.Identifier(role),psycopg.sql.Identifier(label+'_'+role)))
