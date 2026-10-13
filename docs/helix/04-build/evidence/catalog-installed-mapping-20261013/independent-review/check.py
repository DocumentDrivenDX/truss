"""Actual archive helpers with synthetic cursor/host seams; no native lifecycle."""
from pathlib import Path
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import patch
from dataclasses import replace
import inspect,json
import truss._security_catalog_source_installation as m

ROOT=Path('/private/tmp/truss-security-main-integration')
BASE=ROOT/'docs/helix/04-build/evidence/accepted-catalog-policy-read-20261013'
SOURCE=ROOT/'packages/python/src/truss/_security_catalog_source_installation.py'
fields=('original_request','original_response','accepted_catalog_assessment','native_dependencies')
q=(BASE/'request.json').read_bytes();r=(BASE/'owner-response.json').read_bytes();a=(BASE/'assessment.json').read_bytes()
d=m.map_catalog_dependencies(a,r,q)
release=(ROOT/'packages/python/src/truss/_catalog_runtime/manifest.json').read_bytes()
def mapping():return m.PreparedSecurityMapping(q,r,a,d)
original=(q,r,a,d)
archives=m._catalog_source_archives(mapping(),release)
assert len(archives)==6 and [row[2] for row in archives]==[release,a,a,q,r,d]
expected=sorted([(role,name,raw,sha256(raw).digest(),sha256(name.encode()).digest(),'installation') for role,name,raw in archives],key=lambda row:row[1])
names=('artifact_role','artifact_identity','artifact_bytes','artifact_sha256','artifact_identity_sha256','installation_id');oids=(25,25,17,17,17,25)
def desc(names=names,oids=oids):return tuple(SimpleNamespace(name=n,type_code=o) for n,o in zip(names,oids))
class Cursor:
 def __init__(self,description=None,rows=None):self.description=description;self.rows=expected if rows is None else rows;self.fetches=0;self.executed=[]
 def execute(self,sql,**kwargs):self.executed.append(sql)
 def fetchmany(self,n):assert n==7;self.fetches+=1;return self.rows
results=[{'control':'six-exact-original-archive-carriers','passed':True}]
def verify(name,description,rows=None,valid=False,before_fetch=False):
 c=Cursor(description,rows)
 try:m.verify_catalog_source_archive_with_cursor(c,mapping(),'installation')
 except ValueError as error:
  assert not valid,(name,error)
  assert str(error)==('Exact catalog source archive descriptors required' if before_fetch else 'Original installed catalog mapping archive required')
 else:assert valid,name
 assert c.fetches==(0 if before_fetch else 1)
 assert c.executed[0]=='LOCK TABLE ONLY truss.installation_archive IN SHARE MODE NOWAIT'
 assert c.executed[1].startswith('SELECT artifact_role') and 'FROM ONLY truss.installation_archive' in c.executed[1]
 results.append({'control':name,'passed':True,'fetches':c.fetches})
verify('exact-six',desc(),valid=True)
verify('no-descriptors',None,before_fetch=True)
verify('descriptor-width',desc()[:-1],before_fetch=True)
for i in range(6):
 n=list(names);n[i]='wrong';verify('wrong-name:'+str(i),desc(n),before_fetch=True)
 o=list(oids);o[i]=19;verify('foreign-oid:'+str(i),desc(oids=o),before_fetch=True)
 rows=list(expected);row=list(rows[0]);row[i]=b'changed' if i in (2,3,4) else 'changed';rows[0]=tuple(row);verify('changed-field:'+str(i),desc(),rows)
 rows=list(expected);rows.pop(i);verify('missing-original-row:'+str(i),desc(),rows)
for i in (2,3,4):
 rows=list(expected);row=list(rows[0]);row[i]=bytearray(row[i]);rows[0]=tuple(row);verify('mutable-decoded-field:'+str(i),desc(),rows)
verify('extra-row',desc(),expected+[expected[-1]])
verify('wrong-row-width',desc(),[expected[0][:-1]]+expected[1:])
verify('wrong-installation',desc(),[row[:-1]+('other',) for row in expected])

class Host:
 def __init__(self,original_mapping,field=None):self.original=original_mapping;self.field=field;self.calls=0
 def _run_operation(self,transaction,install):
  self.calls+=1
  if self.field:object.__setattr__(self.original,self.field,getattr(self.original,self.field)+b' ')
  captured=inspect.getclosurevars(install).nonlocals
  assert captured['mapping'] is not self.original
  assert tuple(getattr(captured['mapping'],f) for f in fields)==original
  assert captured['request']==q and captured['assessment']==a
  assert m._catalog_source_archives(captured['mapping'],release)==archives
  return 'captured'
with patch.object(m,'PsycopgHost',Host):
 for field in fields:
  value=mapping();h=Host(value,field)
  assert m.bootstrap_catalog_source_marker_in_transaction(h,object(),value)=='captured' and h.calls==1
  results.append({'control':'initializer-original-replacement:'+field,'passed':True})
 for field,maximum in zip(fields,(4000000,16777216,1048576,16777216)):
  for label,raw in [('empty',b''),('mutable',bytearray(b'x')),('oversized',b'x'*(maximum+1))]:
   value=replace(mapping(),**{field:raw});h=Host(value)
   assert isinstance(m.bootstrap_catalog_source_marker_in_transaction(h,object(),value),m.Error) and h.calls==0
   results.append({'control':'pre-host-shape:'+field+':'+label,'passed':True})

for field in fields:
 value=mapping();entered=[]
 class Resource:
  def joinpath(self,*args):return self
  def read_bytes(self):
   entered.append(True);object.__setattr__(value,field,getattr(value,field)+b' ');return release
 c=Cursor(desc())
 with patch.object(m,'files',lambda _:Resource()):m.verify_catalog_source_archive_with_cursor(c,value,'installation')
 assert entered==[True] and c.fetches==1 and getattr(value,field)!=dict(zip(fields,original))[field]
 results.append({'control':'verifier-pre-file-snapshot:'+field,'passed':True})
try:m._catalog_source_archives(replace(mapping(),native_dependencies=d+b' '),release)
except ValueError as error:assert str(error)=='Original native dependency archive correspondence required'
else:raise AssertionError('Dependency drift accepted')
results.append({'control':'derived-dependency-drift-refused','passed':True})
out={'scope':'Actual archive functions; synthetic cursor and host callback inspection; original mapper recomputes dependencies from retained historical genuine native packets. No native SQL/lifecycle, full compiler validation, issuer or authority proof.','sourceSha256':sha256(SOURCE.read_bytes()).hexdigest(),'passed':len(results),'controls':results,'inputDigests':{p.name:sha256(p.read_bytes()).hexdigest() for p in (BASE/'request.json',BASE/'owner-response.json',BASE/'assessment.json')}}
Path(__file__).with_name('results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'passed':len(results),'sourceSha256':out['sourceSha256']}))
