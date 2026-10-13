"""Bounded synthetic ordering/readback controls; not native SQL qualification."""
import json
from pathlib import Path
from hashlib import sha256
from unittest.mock import patch
import truss._security_catalog_source_installation as m

ROOT=Path('/private/tmp/truss-security-main-integration')
SOURCE=ROOT/'packages/python/src/truss/_security_catalog_source_installation.py'
manifest,digest,_=m._release()
assessment=b'original assessment'
mapping=m.PreparedSecurityMapping(b'original request',b'',accepted_catalog_assessment=assessment)
results=[]

class Cursor:
 def __init__(self,mode='ok'):
  self.mode=mode;self.path='hostile, pg_catalog';self.rows=[];self.archives=[];self.queries=[];self.marker=None;self.pinned=False
 def execute(self,sql,params=None,**kw):
  self.queries.append(sql)
  assert self.pinned
  if sql=="SELECT pg_catalog.current_setting('search_path')":self.rows=[(self.path,)]
  elif "current_setting('transaction_isolation')" in sql:
   profile=['read committed','off',manifest['postgresVersion']]
   if self.mode.startswith('profile:'):profile[int(self.mode[-1])]='wrong'
   self.rows=[tuple(profile)]
  elif "set_config('search_path'" in sql:
   self.path=params[0] if params else 'pg_catalog, pg_temp';self.rows=[(self.path,)]
  else:
   assert self.path=='pg_catalog, pg_temp'
   if sql.startswith('SELECT rev '):self.rows=[(1,)]
   elif sql.startswith('SELECT installation_id::text'):self.rows=[('installation',123)]
   elif sql.startswith('SELECT (SELECT count(*)'):
    self.rows=[(1,0,0,0)] if self.mode=='existing' else [(0,0,0,0)]
   elif sql.startswith('SELECT d.oid::text'):self.rows=[('1','db','2','2026-10-13 12:00:00+00')]
   elif sql.startswith('INSERT INTO truss.installation_marker'):
    identity,release,bundle,inventory,db,clock,_=params
    self.marker=('truss-bootstrap-marker/0.1.0',identity,release,bundle,'truss-accepted-catalog/0.1.0',inventory,db,'truss',clock,'true');self.rows=[]
   elif sql.startswith('INSERT INTO truss.installation_archive'):
    identity,role,name,raw,name_digest=params
    self.archives.append((role,name,raw,sha256(raw).digest(),name_digest,identity));self.rows=[]
   elif sql.startswith('SELECT marker_interface_version'):
    row=list(self.marker)
    if self.mode.startswith('marker:'):row[int(self.mode.split(':')[1])]='changed'
    self.rows=[] if self.mode=='marker-missing' else [tuple(row)]
   elif sql.startswith('SELECT artifact_role'):
    self.rows=sorted(self.archives,key=lambda row:row[1])
    if self.mode.startswith('archive:'):
     row=list(self.rows[0]);row[int(self.mode.split(':')[1])]='changed';self.rows[0]=tuple(row)
    elif self.mode=='archive-missing':self.rows.pop()
    elif self.mode=='archive-extra':self.rows.append(self.rows[-1])
   else:raise AssertionError(sql)
 def fetchmany(self,n):return self.rows[:n]

class Host:
 def __init__(self,mode='ok'):self.cursor=Cursor(mode);self.calls=0
 def _run_operation(self,transaction,action):
  self.calls+=1
  return action(self.cursor,None)

def pin(c):c.pinned=True
def admin(c,owner):assert c.path=='pg_catalog, pg_temp' and owner==123
def capture(c,request):
 assert c.path=='pg_catalog, pg_temp' and request==b'original request'
 return b'changed' if c.mode=='source-drift' else assessment

with patch.object(m,'PsycopgHost',Host),patch.object(m,'_pin_cursor',pin),patch.object(m,'installation_administrator_with_cursor',admin),patch.object(m,'capture_accepted_catalog',capture):
 host=Host();value=m.bootstrap_catalog_source_marker_in_transaction(host,object(),mapping)
 assert value.status=='pending_commit' and value.security_ready is False
 assert host.cursor.path=='hostile, pg_catalog' and len(host.cursor.archives)==3
 assert value.inventory_sha256==sha256(assessment).hexdigest() and value.release_sha256==digest
 results.append({'control':'positive-safe-path-exact-readback-restoration','passed':True})
 for mode in ['profile:0','profile:1','profile:2','source-drift','existing','marker-missing','archive-missing','archive-extra']+[f'marker:{i}' for i in range(10)]+[f'archive:{i}' for i in range(6)]:
  host=Host(mode)
  try:m.bootstrap_catalog_source_marker_in_transaction(host,object(),mapping)
  except ValueError as error:
   if mode.startswith('marker'):assert str(error)=='Exact original catalog source marker readback required'
   if mode.startswith('archive'):assert str(error)=='Exact original catalog source archive readback required'
   if mode.startswith('profile') or mode in ('source-drift','existing'):assert not host.cursor.archives and host.cursor.marker is None
  else:raise AssertionError(mode)
  results.append({'control':mode,'passed':True})
 for field,raw in [('original_request',b''),('original_request',bytearray(b'x')),('original_request',b'x'*4000001),('accepted_catalog_assessment',b''),('accepted_catalog_assessment',memoryview(b'x')),('accepted_catalog_assessment',b'x'*1048577)]:
  from dataclasses import replace
  host=Host();result=m.bootstrap_catalog_source_marker_in_transaction(host,object(),replace(mapping,**{field:raw}))
  assert isinstance(result,m.Error) and host.calls==0
  results.append({'control':f'pre-host:{field}:{type(raw).__name__}:{len(raw)}','passed':True})
out={'scope':'Actual Python initializer with synthetic cursor/host and substituted trusted dependencies. No native execution, SQL refinement, rollback or authority claim.','sourceSha256':sha256(SOURCE.read_bytes()).hexdigest(),'manifestSha256':digest,'controls':results,'passed':len(results)}
Path(__file__).with_name('results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'passed':len(results),'sourceSha256':out['sourceSha256']}))
