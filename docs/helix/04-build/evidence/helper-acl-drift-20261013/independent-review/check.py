"""Original verifier AST with bounded synthetic native descriptors/rows; no DB."""
from pathlib import Path
import ast,json,types,hashlib
source=Path('/private/tmp/truss-security-main-integration/scripts/security_catalog_subject_read.py');sql=Path('/private/tmp/truss-security-main-integration/scripts/security-catalog-subject.sql');root=Path('/private/tmp/helper-acl-review-20261013')
fn=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_verify_helpers');env={'json':json};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),env)
bodies=[part.split('$$;',1)[0] for part in sql.read_text().split('AS $$')[1:]]
class Cursor:
 def __init__(self,mode,target='catalog_subject_current'):
  self.mode=mode;self.target=target;self.owner='10' if mode=='reverse' else '2';self.caller='2' if mode in ('reverse','owner_is_caller') else '10';self.phase=None;self.fetches=[]
 def execute(self,q,params=(),**kw):
  if q.startswith('SELECT c.relowner'):self.phase='owner';self.rows=[(self.owner,'false','false','false')];width=4
  elif q.startswith('SELECT oid::'):
   self.phase='caller';self.rows=[(self.caller,)];width=1
   if self.mode=='caller_missing':self.rows=[]
   if self.mode=='caller_duplicate':self.rows*=2
   if self.mode=='caller_nontext':self.rows=[(int(self.caller),)]
  elif 'aclexplode' in q:
   self.phase='acl:'+params[0];width=4;self.rows=[(self.owner,self.owner,'EXECUTE','false'),(self.caller,self.owner,'EXECUTE','false')]
   if params[0]==self.target:
    if self.mode in ('public','null_default'):self.rows=([self.rows[0]] if self.mode=='null_default' else self.rows)+[('0',self.owner,'EXECUTE','false')]
    if self.mode=='third_role':self.rows.append(('20',self.owner,'EXECUTE','false'))
    if self.mode=='caller_grantable':self.rows[1]=(self.caller,self.owner,'EXECUTE','true')
    if self.mode=='owner_grantable':self.rows[0]=(self.owner,self.owner,'EXECUTE','true')
    if self.mode=='wrong_grantor':self.rows[1]=(self.caller,'20','EXECUTE','false')
    if self.mode=='wrong_privilege':self.rows[1]=(self.caller,self.owner,'SELECT','false')
    if self.mode=='missing_caller':self.rows=self.rows[:1]
    if self.mode=='missing_owner':self.rows=self.rows[1:]
    if self.mode=='duplicate':self.rows.append(self.rows[1])
    if self.mode=='empty':self.rows=[]
   self.rows.sort(key=lambda x:(int(x[0]),int(x[1]),x[2],x[3]))
  else:
   name=params[0];self.phase='metadata:'+name;width=19
   if name=='catalog_subject_current':language,ret,names,modes,typ,body='plpgsql','25',['actor','staff_id'],['i','t'],['25','25'],bodies[0]
   else:language,ret,names,modes,typ,body='sql','2249',['actor','installation_id','database_oid','role_oid'],['i','t','t','t'],['25']*4,bodies[1]
   self.rows=[(self.owner,language,'f','1','25',ret,'true','false','true','v','u','false','0','["search_path=pg_catalog, pg_temp"]',body,json.dumps(names),json.dumps(modes),json.dumps(typ),'true')]
  self.description=[types.SimpleNamespace(type_code=25) for _ in range(width)]
  if self.mode=='caller_foreign_descriptor' and self.phase=='caller':self.description[0].type_code=19
  if self.phase=='acl:'+self.target:
   if self.mode=='acl_foreign_descriptor':self.description[0].type_code=19
   if self.mode=='acl_wrong_width':self.description=self.description[:3]
 def fetchmany(self,n):self.fetches.append(self.phase);return self.rows[:n]
rows=[]
for mode in ['baseline','reverse','owner_is_caller','caller_missing','caller_duplicate','caller_nontext','caller_foreign_descriptor']:
 c=Cursor(mode);error=None
 try:env['_verify_helpers'](c,sql.read_text())
 except ValueError as e:error=str(e)
 if mode in ('baseline','reverse'):assert error is None
 else:assert error is not None
 if mode=='caller_foreign_descriptor':assert 'caller' not in c.fetches
 rows.append({'control':mode,'passed':True,'refusal':error})
for target in ('catalog_subject_current','catalog_subject_context'):
 for mode in ['public','null_default','third_role','caller_grantable','owner_grantable','wrong_grantor','wrong_privilege','missing_caller','missing_owner','duplicate','empty','acl_foreign_descriptor','acl_wrong_width']:
  c=Cursor(mode,target)
  try:env['_verify_helpers'](c,sql.read_text())
  except ValueError as e:error=str(e)
  else:raise AssertionError((target,mode))
  if mode.startswith('acl_'):assert c.phase=='acl:'+target and c.phase not in c.fetches
  else:assert error=='Exact installed catalog subject helper ACL required'
  rows.append({'control':target+':'+mode,'passed':True,'refusal':error})
r={'scope':'Original verifier function AST with synthetic stock-shaped native descriptor/ACL rows; not SQL privilege or native refinement evidence','passed':len(rows),'controls':rows,'sourcePins':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,sql]}};(root/'results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':len(rows),'sourcePins':r['sourcePins']}))
