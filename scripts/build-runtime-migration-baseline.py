#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Reproduce the initial UMF0.10 migration inventories using real published wheels.

This bounded baseline builder admits only the reviewed routine/receipt delta.
Future storage changes require authored edges, not inferred SQL migrations.
"""
from pathlib import Path
import argparse
import sys,os,json,tempfile,subprocess,zipfile,hashlib
import psycopg
from truss import LocalPostgres
from truss._migration_verify import structure,acl,roles,context,canonical
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source44-wheel',required=True,type=Path)
parser.add_argument('--source46-wheel',required=True,type=Path)
parser.add_argument('--output',required=True,type=Path)
parser.add_argument('--initialization-time-zone',choices=('America/New_York','UTC'),default='America/New_York')
parser.add_argument('--initialization-peer',type=Path,help='Other qualified timezone capture; never infer native partition bounds')
args=parser.parse_args()
os.environ['TZ']=args.initialization_time_zone
OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'packages/python/tests'))
pinned=json.loads((ROOT/'packages/python/src/truss/_migrations/manifest.json').read_bytes())
for label,path in [('source44',args.source44_wheel),('source46',args.source46_wheel)]:
 if hashlib.sha256(path.read_bytes()).hexdigest()!=pinned['sourceWheels'][label]['sha256']:
  raise ValueError('Exact published source wheel required')
RUN=Path(tempfile.mkdtemp(prefix='truss-migration-artifacts-'));print(RUN,flush=True)
sourcewheel=args.source44_wheel
old=RUN/'source44';zipfile.ZipFile(sourcewheel).extractall(old)
currentwheel=args.source46_wheel
base=RUN/'source46';zipfile.ZipFile(currentwheel).extractall(base)
from test_catalog_relational_support import relational_document
model=relational_document();model['id']='adoc';model['extensions']={'x-migration-opaque':{'future':[3,1,4],'null':None}}
model['vocabularies']={'x-migration-opaque':{'version':'1.0.0'}}
(RUN/'model.json').write_text(json.dumps(model,indent=2))
profiles={};inventories={};routines={};data={}
with LocalPostgres(RUN/'data') as pg:
 uri=pg.info.connection_uri
 with psycopg.connect(uri,autocommit=True) as control:
  if control.execute('SHOW TimeZone').fetchone()!=(args.initialization_time_zone,):raise ValueError('Exact initializer timezone required')
 for label,path in [('source44',old),('source46',base),('target',ROOT/'packages/python/src')]:
  with psycopg.connect(uri,autocommit=True) as c:c.execute('CREATE DATABASE '+label)
  params=psycopg.conninfo.conninfo_to_dict(uri);params['dbname']=label;selected=psycopg.conninfo.make_conninfo(**params)
  env={**os.environ,'PYTHONPATH':str(path)}
  result=subprocess.run([sys.executable,str(ROOT/'packages/python/tests/runtime_migration_fixture.py'),selected,str(RUN/'model.json'),str(RUN/(label+'.json'))],env=env,text=True,capture_output=True)
  print(label,result.returncode,result.stdout,result.stderr,flush=True)
  if result.returncode:raise SystemExit(1)
  with psycopg.connect(selected,autocommit=True) as c:
   with c.cursor() as cursor:
    cursor.execute('SET search_path=pg_catalog,pg_temp')
    ctx,owner,registrar=context(cursor);inventory=structure(cursor);rolemap=roles(cursor,owner,registrar)
    prof={kind:[] for kind in ['owner','registrar','administrator','reader','writer','feed','audit','public']}
    for kind,name,objowner,grantee,priv,grantable,grantor in acl(cursor):
     kinds=rolemap.get(grantee)
     if not kinds or len(kinds)!=1:raise AssertionError((grantee,kinds))
     prof[next(iter(kinds))].append([kind,name,priv,grantable])
    for k in prof:prof[k].sort()
    cursor.execute('SELECT preparation_configuration FROM truss.catalog_runtime_installation')
    configuration=cursor.fetchone()[0]
    raw=(path/'truss/_catalog_runtime/manifest.json').read_bytes();digest=hashlib.sha256(raw).hexdigest()
    original=json.loads(raw)
    artifact={'inventory':inventory,'acl':prof,'configuration':configuration,'manifest':original,'sha256':digest}
    # Qualify the exact native deparse forms produced by a real logical restore.
    restored_name=label+'_restored'
    with psycopg.connect(uri,autocommit=True) as control:control.execute('CREATE DATABASE '+restored_name)
    restored_params={**params,'dbname':restored_name};restored_uri=psycopg.conninfo.make_conninfo(**restored_params)
    from importlib.resources import files as resource_files
    binaries=Path(str(resource_files('pgserver')))/'pginstall/bin';backup=RUN/(label+'.dump')
    subprocess.run([str(binaries/'pg_dump'),'--dbname',selected,'--format=custom','--file',str(backup)],check=True,capture_output=True)
    subprocess.run([str(binaries/'pg_restore'),'--dbname',restored_uri,'--exit-on-error',str(backup)],check=True,capture_output=True)
    with psycopg.connect(restored_uri,autocommit=True) as restored:
     with restored.cursor() as rc:
      rc.execute('SET search_path=pg_catalog,pg_temp');restored_inventory=structure(rc)
    alternatives=[]
    allowed={('constraints','installation_marker','installation_marker_identity_bounds'),('triggers','runtime_owned_operation','runtime_owned_operation_immutable')}
    for category,rows in inventory.items():
     observed=restored_inventory[category]
     if rows==observed:continue
     if len(rows)!=len(observed):raise ValueError('Logical restore changed inventory membership')
     for before,after in zip(rows,observed,strict=True):
      if before==after:continue
      key=(category,*before[:2])
      if key not in allowed or before[:-1]!=after[:-1]:raise ValueError('Unreviewed logical restore difference: '+repr(key))
      alternatives.append({'surface':category,'identity':before[:2],'definitions':[before[-1],after[-1]]})
    artifact['definitionAlternatives']=alternatives
    data[label]=artifact;routines[label]={(row[0],row[1]):row[2] for row in inventory['routines']}
  # Roles are cluster-wide: rename them after collecting this database's profile.
  with psycopg.connect(selected,autocommit=True) as c:
   for role in ['migration_reader','migration_writer','migration_feed','migration_audit','migration_person']:
    c.execute(psycopg.sql.SQL('ALTER ROLE {} RENAME TO {}').format(psycopg.sql.Identifier(role),psycopg.sql.Identifier(label+'_'+role)))
for label in ['source44','source46']:(OUT/(data[label]['sha256']+'.json')).write_bytes(canonical(data[label]))
(OUT/'target.json').write_bytes(canonical(data['target']))
steps={}
allowed={'catalog_accept_with_keys','get_object','process_import_chunk','query_binding_if_changed','query_scope','runtime_import_operation','runtime_owned_import_record_source_checked','runtime_person','runtime_current_installation','runtime_migration_immutable'}
for label in ('source44','source46'):
 unexpected={key[0] for key,value in routines['target'].items() if routines[label].get(key)!=value}-allowed
 if unexpected or set(routines[label])-set(routines['target']):raise ValueError('Unreviewed routine delta: '+repr(unexpected))
 old_tables={row[0] for row in data[label]['inventory']['relations'] if row[1]=='r'}
 new_tables={row[0] for row in data['target']['inventory']['relations'] if row[1]=='r'}
 if new_tables-old_tables!={'runtime_migration_receipt'} or old_tables-new_tables:raise ValueError('Unreviewed table delta')
# Source40-only table changes aren't resurrected. Only declared changed routines plus fresh receipt DDL.
migrations=(ROOT/'packages/python/src/truss/_catalog_runtime/migrations.sql').read_text()
# Full file is a declared single step; replace only the preexisting current-installation function.
migration_step=migrations.replace('CREATE FUNCTION truss.runtime_current_installation()','CREATE OR REPLACE FUNCTION truss.runtime_current_installation()')
for label in ['source44','source46']:
 changed=[]
 for key,definition in sorted(routines['target'].items()):
  if key[0] in ('runtime_current_installation','runtime_migration_immutable'):continue
  if routines[label].get(key)!=definition:
   changed.append(definition.replace('CREATE OR REPLACE FUNCTION','CREATE OR REPLACE FUNCTION',1))
 steps[data[label]['sha256']]=[migration_step]+changed
 print(label,'changed routines',len(changed),[k for k in routines['target'] if routines[label].get(k)!=routines['target'][k]],flush=True)
(OUT/'steps.json').write_bytes(canonical(steps))
(OUT/'ownership.json').write_bytes(canonical(['ALTER TABLE truss.runtime_migration_receipt OWNER TO {}','ALTER FUNCTION truss.runtime_migration_immutable() OWNER TO {}','REVOKE ALL ON TABLE truss.runtime_migration_receipt FROM PUBLIC','REVOKE ALL ON FUNCTION truss.runtime_migration_immutable() FROM PUBLIC','ALTER FUNCTION truss.query_binding_if_changed(jsonb,integer,integer,integer,text,text,text) OWNER TO {}','REVOKE ALL ON FUNCTION truss.query_binding_if_changed(jsonb,integer,integer,integer,text,text,text) FROM PUBLIC','ALTER FUNCTION truss.runtime_import_operation(jsonb,jsonb) OWNER TO {}','REVOKE ALL ON FUNCTION truss.runtime_import_operation(jsonb,jsonb) FROM PUBLIC','REVOKE ALL ON TYPE truss.runtime_migration_receipt FROM PUBLIC']))
# Capture exact newly added module signature from current runtime definition, not inferred names.
(OUT/'new-module-grants.json').write_bytes(canonical(['query_binding_if_changed(jsonb,integer,integer,integer,text,text,text)']))
manifest={'interfaceVersion':'truss-runtime-migration/0.1','target':data['target']['sha256'],'targetRelease':data['target']['manifest']['releaseId'],
 'sources':[data[l]['sha256'] for l in ['source44','source46']],
 'sourceWheels':{l:{'filename':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for l,p in [('source44',sourcewheel),('source46',currentwheel)]},
 'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.json')) if p.name!='manifest.json'}}
(OUT/'manifest.json').write_bytes(canonical(manifest));print('target',manifest['target'],flush=True)
(RUN/'complete.json').write_bytes(canonical(manifest))

(root_target:=OUT/(manifest['target']+'.json')).write_bytes((OUT/'target.json').read_bytes())
edges=[]
for label in ('source44','source46'):
 source=data[label]['sha256'];name='edge-'+source+'-'+manifest['target']+'.json'
 (OUT/name).write_bytes(canonical({'source':source,'target':manifest['target'],'steps':steps[source],
   'ownership':json.loads((OUT/'ownership.json').read_bytes()),'moduleGrants':json.loads((OUT/'new-module-grants.json').read_bytes())}))
 edges.append({'source':source,'target':manifest['target'],'direction':'forward','artifact':name})
 manifest['sourceWheels'][label].update(runtimeManifestSha256=source,tag='v0.0.44' if label=='source44' else 'v0.0.46')
manifest['edges']=edges
manifest['immutableFiles']=[e['artifact'] for e in edges]+[s+'.json' for s in manifest['sources']+[manifest['target']]]
for name in ('target.json','steps.json','ownership.json','new-module-grants.json'):(OUT/name).unlink()
manifest['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.json')) if p.name!='manifest.json'}
(OUT/'manifest.json').write_bytes(canonical(manifest))

# Both initializers execute the original released SQL. Their different native
# bounds remain different instants; canonical UTC observation is not conversion.
capture={'initializationTimeZone':args.initialization_time_zone,
         'inventories':{d['sha256']:hashlib.sha256(canonical(d['inventory'])).hexdigest() for d in data.values()}}
(OUT/'capture.txt').write_bytes(canonical(capture))
if args.initialization_peer:
 peer=args.initialization_peer
 prior=json.loads((peer/'capture.txt').read_bytes())
 if {prior['initializationTimeZone'],args.initialization_time_zone}!={'America/New_York','UTC'}:
  raise ValueError('The two exact initialization profiles are required')
 rules=[]
 for label,d in data.items():
  other=json.loads((peer/(d['sha256']+'.json')).read_bytes())
  if hashlib.sha256(canonical(other['inventory'])).hexdigest()!=prior['inventories'][d['sha256']]:
   raise ValueError('Peer native observation changed')
  for category,rows in d['inventory'].items():
   before=other['inventory'][category]
   if category!='relations':
    if rows!=before:raise ValueError('Unreviewed initialization definition difference: '+category)
    continue
   if len(rows)!=len(before):raise ValueError('Initialization membership changed')
   changed=[]
   for left,right in zip(before,rows,strict=True):
    if left==right:continue
    if left[0]!='journal_runtime_horizon' or left[:7]+left[8:]!=right[:7]+right[8:]:
     raise ValueError('Unreviewed native initialization difference')
    changed.append({'surface':'relations','identity':['journal_runtime_horizon'],
                    'rows':sorted([left,right],key=canonical)})
   if len(changed)!=1:raise ValueError('Exactly the observed horizon difference required')
   if rules and rules!=changed:raise ValueError('Source/target initialization profiles differ')
   rules=changed
 proof={'scope':'Original published-wheel initializers, exact native partition bounds; variants are distinct instants preserved without conversion',
        'observationTimeZone':'UTC','qualifiedTimeZones':['America/New_York','UTC'],
        'captures':sorted([prior,capture],key=lambda c:c['initializationTimeZone']),
        'sourceWheels':manifest['sourceWheels'],'rules':rules}
 name='native-initialization-profiles-0.1.json';(OUT/name).write_bytes(canonical(proof))
 for d in data.values():
  d['initializationAlternatives']=rules
  (OUT/(d['sha256']+'.json')).write_bytes(canonical(d))
 manifest['initializationProfiles']=name;manifest['immutableFiles'].append(name)
 manifest['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.json')) if p.name!='manifest.json'}
 (OUT/'manifest.json').write_bytes(canonical(manifest))

for relative,name in [('docs/helix/02-design/models/truss-runtime-migrations-0.1.umf.json','receipt-model-0.1.umf.json'),('docs/helix/04-build/evidence/runtime-migrations-20261021/receipt-model.json','receipt-model-0.1.evidence.json')]:
 (OUT/name).write_bytes((ROOT/relative).read_bytes())
manifest['receiptModel']={'artifact':'receipt-model-0.1.umf.json','evidence':'receipt-model-0.1.evidence.json','sourceFile':'migrations.sql'}
manifest['immutableFiles']+=['receipt-model-0.1.umf.json','receipt-model-0.1.evidence.json']
manifest['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.json')) if p.name!='manifest.json'}
(OUT/'manifest.json').write_bytes(canonical(manifest))

proof_bytes=(ROOT/'docs/helix/04-build/evidence/runtime-migrations-20261021/native-deparse-equivalence.json').read_bytes()
proof=json.loads(proof_bytes)
if proof['passed'] is not True or any(d['definitionAlternatives']!=proof['rules'] for d in data.values()):raise ValueError('Native deparse equivalence must be qualified before packaging')
name='native-deparse-equivalence-0.1.json';(OUT/name).write_bytes(proof_bytes)
manifest['definitionEquivalence']=name;manifest['immutableFiles'].append(name)
manifest['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.json')) if p.name!='manifest.json'}
(OUT/'manifest.json').write_bytes(canonical(manifest))
