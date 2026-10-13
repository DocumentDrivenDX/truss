from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
import sys,json,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'packages/python/src'),str(ROOT/'scripts')]
import truss._psycopg_epoch_cut as epoch
import security_catalog_subject_read as subject
from truss._security_mapping import PreparedSecurityMapping
from truss._psycopg_fact_cut import _FactRelationComparison
checks=[]
def check(n,p):assert p,n;checks.append({'name':n,'passed':True})
base=epoch._DDLBarrierComparison(20,30,'body')
def descriptors():return [SimpleNamespace(type_code=25) for _ in range(19)]
def rows(b):
 suffix=('30','20','truss','runtime_fence_routine_ddl_writer','plpgsql','f','0','true','false','false','v','["search_path=pg_catalog, pg_temp"]','body','false')
 rs=[('truss_routine_ddl_writer_barrier','ddl_command_start','A','20','["CREATE FUNCTION", "ALTER FUNCTION", "DROP FUNCTION", "CREATE PROCEDURE", "ALTER PROCEDURE", "DROP PROCEDURE"]',*suffix),('truss_table_ddl_writer_barrier','ddl_command_start','A','20','["CREATE TABLE", "ALTER TABLE", "DROP TABLE"]',*suffix)]
 if b.include_alter_routine:rs.append(('truss_z_routine_ddl_writer_barrier','ddl_command_start','A','20','["ALTER ROUTINE"]',*suffix))
 if b.include_schema_ddl:rs.append(('truss_schema_ddl_writer_barrier','ddl_command_start','A','20','["CREATE SCHEMA", "ALTER SCHEMA", "DROP SCHEMA"]',*suffix))
 return sorted(rs)
class Cursor:
 def __init__(self,d,r):self.description=d;self.rows=r;self.fetched=[];self.executed=[]
 def execute(self,*args,**kw):self.executed.append((args,kw))
 def fetchmany(self,n):self.fetched.append(n);return self.rows
def run(b,d,r,mutate=None):
 c=Cursor(d,r);entered=[];called=[];error=None
 def shell(h,t,e,fn):
  entered.append(True)
  if mutate:mutate()
  return fn(c)
 try:
  with patch.object(epoch,'_run_fenced_epoch_operation',shell):result=epoch._run_ddl_fenced_epoch_operation(None,None,None,b,lambda cur:called.append(cur) or 'done')
 except ValueError as e:error=str(e)
 return c,entered,called,error
check('legacy positional constructor defaults schema selection false',base.include_schema_ddl is False)
for a in (False,True):
 for s in (False,True):
  b=replace(base,include_alter_routine=a,include_schema_ddl=s);label=f'alter={a} schema={s}'
  c,entered,called,error=run(b,descriptors(),rows(b))
  check(label+' exact ordered rows accept',not error and called==[c] and c.fetched==[3+int(a)+int(s)])
  args,kw=c.executed[0]
  check(label+' uses static flag literals without bind adaptation',len(args)==1 and (('true' if s else 'false')+" AND e.evtname='truss_schema_ddl_writer_barrier'") in args[0] and kw=={'prepare':False,'binary':False})
  ds=descriptors();ds[18].type_code=19;c,entered,called,error=run(b,ds,rows(b))
  check(label+' foreign descriptor refuses before fetch',error=='Exact original DDL barrier TEXT descriptors required' and not c.fetched and not called)
extended=replace(base,include_schema_ddl=True,include_alter_routine=True)
for label,rs in [('missing schema',[r for r in rows(extended) if r[0]!='truss_schema_ddl_writer_barrier']),('duplicate schema',rows(extended)+[rows(extended)[1]]),('wrong order',list(reversed(rows(extended))))]:
 c,entered,called,error=run(extended,descriptors(),rs);check(label+' refuses callback',error=='Exact original installed DDL barriers required' and not called)
for i in range(19):
 rs=rows(extended);r=list(rs[1]);assert r[0]=='truss_schema_ddl_writer_barrier';r[i]='drift';rs[1]=tuple(r)
 c,entered,called,error=run(extended,descriptors(),rs);check('schema metadata field '+str(i)+' exact match required',error=='Exact original installed DDL barriers required' and not called)
for field in ('include_schema_ddl','include_alter_routine'):
 for value in (None,0,1,'true',[],object()):
  b=replace(base,**{field:value});c,entered,called,error=run(b,descriptors(),[])
  check(field+' nonbool '+type(value).__name__+' '+str(value)+' refuses before epoch host',bool(error) and not entered and not c.executed and not called)
changing=replace(extended)
c,entered,called,error=run(changing,descriptors(),rows(extended),lambda:object.__setattr__(changing,'include_schema_ddl',False))
check('schema selection captured before epoch host mutation',not error and called==[c] and c.fetched==[5])
mapping=PreparedSecurityMapping(b'request',b'{}',accepted_catalog_assessment=b'assessment');relations=(_FactRelationComparison('truss','object',10,20,'guard'),)
def derive(b):return subject.derive_catalog_source_epoch_profile(mapping,relations,b,subject_source=b'helper')
p0,p1=derive(base),derive(replace(base,include_schema_ddl=True))
j0,j1=json.loads(p0),json.loads(p1)
check('profile0.2 binds exact default false and optin true distinctly',j0['interfaceVersion']=='truss-owned-catalog-source-profile/0.2' and j0['ddlBarrier']['includeSchemaDdl'] is False and j1['ddlBarrier']['includeSchemaDdl'] is True and p0!=p1)
for value in (None,0,1,'true'):
 try:derive(replace(base,include_schema_ddl=value))
 except ValueError as e:check('profile refuses schema selection '+repr(value),str(e)=='Exact native source barrier binding required')
 else:raise AssertionError(value)
files=['packages/python/src/truss/_psycopg_epoch_cut.py','scripts/security_catalog_subject_read.py','packages/postgresql/native/source-epoch-schema-ddl-barrier.sql','packages/python/tests/test_security_catalog_source_cut_native.py']
record={'scope':'Actual Python readback and profile producer with synthetic native epoch/catalog carriers; no native event or lifecycle execution','count':len(checks),'controls':checks,'sourceSha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
(OUT/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'controls':len(checks),'passed':True}))
