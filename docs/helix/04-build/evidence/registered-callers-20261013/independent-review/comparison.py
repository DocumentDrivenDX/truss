"""Real bounded registration snapshot and verifier, synthetic native rows."""
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,json
from truss import _security_catalog_subject_installation as m
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent;checks=[]
source=(ROOT/'scripts/security-catalog-subject.sql').read_bytes()
base=m.PendingCatalogSubjects('installation',m._SOURCE_SHA256,((11,'s1'),(12,'s2'),(13,'s3')))
def check(n,fn):fn();checks.append({'name':n,'passed':True})
def eq(a,b):assert a==b,(a,b)
def refused(fn):
 try:fn()
 except (ValueError,TypeError,UnicodeError):return
 raise AssertionError('Refusal required')
check('exact snapshot detached equivalent',lambda:(eq(m.snapshot_catalog_subjects(base),base),eq(m.snapshot_catalog_subjects(base) is base,False)))
for name,value in [('installation_id',''),('installation_id','a'*1025),('installation_id',b'x'),('source_sha256','x'),('source_sha256',b'x'),('status','committed'),('security_ready',True),('bindings',()),('bindings',list(base.bindings)),('bindings',((True,'s1'),)),('bindings',((0,'s1'),)),('bindings',((4294967296,'s1'),)),('bindings',((11,''),)),('bindings',((11,b's1'),)),('bindings',((11,'a\0b'),)),('bindings',((11,'a'*4097),)),('bindings',((12,'s1'),(11,'s2'))),('bindings',((11,'s1'),(11,'s2'))),('bindings',tuple((i,'s1') for i in range(1,258)))]:
 check('snapshot refuses '+name+' '+repr(value)[:70],lambda n=name,v=value:refused(lambda:m.snapshot_catalog_subjects(replace(base,**{n:v}))))
class Spoof(str):
 def __eq__(self,other):return True
 def __ne__(self,other):return False
for name,value in [('source_sha256',Spoof('foreign')),('status',Spoof('committed'))]:
 check('snapshot exact string '+name,lambda n=name,v=value:refused(lambda:m.snapshot_catalog_subjects(replace(base,**{n:v}))))
check('256 ordered unique bindings accepted',lambda:eq(len(m.snapshot_catalog_subjects(replace(base,bindings=tuple((i,'s1') for i in range(1,257)))).bindings),256))
class Cursor:
 def __init__(self,mode):self.mode=mode;self.calls=[];self.fetches=[];self.phase=None
 def execute(self,q,*args,**kw):
  self.phase='installation' if 'FROM truss.catalog_runtime_installation' in q else 'map';self.calls.append(q)
  rows=[('installation',)] if self.phase=='installation' else [(str(o),k) for o,k in base.bindings]
  if self.mode=='wrong-installation' and self.phase=='installation':rows=[('other',)]
  if self.phase=='map':
   if self.mode=='missing':rows=rows[:-1]
   if self.mode=='extra':rows=rows+[('14','s4')]
   if self.mode=='duplicate':rows=rows+[rows[-1]]
   if self.mode=='rebound':rows[0]=('11','s2')
   if self.mode=='reordered':rows.reverse()
   if self.mode=='byte-key':rows[0]=('11',b's1')
  self.rows=rows;self.description=[SimpleNamespace(type_code=25)]*(1 if self.phase=='installation' else 2)
  if self.mode==self.phase+'-descriptor':self.description[0]=SimpleNamespace(type_code=19)
 def fetchmany(self,n):self.fetches.append(self.phase);return self.rows[:n]
def verify(mode='baseline',subjects=base,raw=source):
 c=Cursor(mode);called=[]
 def helpers(cursor,text,*,expected_callers):called.append(expected_callers);eq(text,source.decode())
 with patch.object(m,'verify_catalog_subject_helpers_with_cursor',helpers):m.verify_registered_catalog_subjects_with_cursor(c,subjects,raw)
 return c,called
def good():
 c,called=verify();eq(called,[(11,12,13)]);eq(c.fetches,['installation','map'])
 for q in c.calls:assert '::text' not in q,q
check('native full map and exact caller set; safe native text casts',good)
for mode in ('wrong-installation','missing','extra','duplicate','rebound','reordered','byte-key','installation-descriptor','map-descriptor'):
 def probe(mode=mode):
  c=Cursor(mode)
  with patch.object(m,'verify_catalog_subject_helpers_with_cursor',lambda *a,**kw:None):refused(lambda:m.verify_registered_catalog_subjects_with_cursor(c,base,source))
  if mode.endswith('-descriptor'):assert mode.removesuffix('-descriptor') not in c.fetches
 check('native registration refuses '+mode,probe)
for raw in (bytearray(source),b'foreign',source+b'\n'):
 check('helper source refuses '+type(raw).__name__+' '+str(len(raw)),lambda raw=raw:refused(lambda:verify(raw=raw)))
record={'scope':'Real registered comparison/verification code with synthetic descriptor/row and helper-check seam; no native SQL execution, installer authenticity or lifetime claim.','count':len(checks),'passed':True,'controls':checks,'sourceSha256':hashlib.sha256((ROOT/'packages/python/src/truss/_security_catalog_subject_installation.py').read_bytes()).hexdigest()}
(OUT/'comparison-results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'count':len(checks),'passed':True}))
