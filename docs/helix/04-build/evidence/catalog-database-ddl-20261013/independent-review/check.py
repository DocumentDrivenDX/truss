from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
import itertools,sys,json,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'packages/python/src'),str(ROOT/'scripts')]
import truss._psycopg_epoch_cut as epoch
import security_catalog_subject_read as subject
from truss._security_mapping import PreparedSecurityMapping
from truss._psycopg_fact_cut import _FactRelationComparison
checks=[]
def check(n,p):assert p,n;checks.append({'name':n,'passed':True})
base=epoch._DDLBarrierComparison(20,30,'body')
def descriptors(n):return [SimpleNamespace(type_code=25) for _ in range(n)]
def rows(b):
 suffix=('30','20','truss','runtime_fence_routine_ddl_writer','plpgsql','f','0','true','false','false','v','["search_path=pg_catalog, pg_temp"]','body','false')
 rs=[('truss_routine_ddl_writer_barrier','ddl_command_start','A','20','["CREATE FUNCTION", "ALTER FUNCTION", "DROP FUNCTION", "CREATE PROCEDURE", "ALTER PROCEDURE", "DROP PROCEDURE"]',*suffix),('truss_table_ddl_writer_barrier','ddl_command_start','A','20','["CREATE TABLE", "ALTER TABLE", "DROP TABLE"]',*suffix)]
 if b.include_alter_routine:rs.append(('truss_z_routine_ddl_writer_barrier','ddl_command_start','A','20','["ALTER ROUTINE"]',*suffix))
 if b.include_schema_ddl:rs.append(('truss_schema_ddl_writer_barrier','ddl_command_start','A','20','["CREATE SCHEMA", "ALTER SCHEMA", "DROP SCHEMA"]',*suffix))
 if b.include_database_ddl:rs.append(('truss_database_ddl_writer_barrier','ddl_command_start','A','20',None,*suffix))
 return sorted(rs)
class Cursor:
 def __init__(self,setting_rows,setting_desc,metadata_rows,metadata_desc):
  self.data=[(setting_rows,setting_desc),(metadata_rows,metadata_desc)];self.executed=[];self.fetched=[]
 def execute(self,*args,**kw):
  self.stage=len(self.executed);self.executed.append((args,kw));self.description=self.data[self.stage][1]
 def fetchmany(self,n):self.fetched.append((self.stage,n));return self.data[self.stage][0]
def run(b,metadata_rows=None,metadata_desc='default',setting_rows='default',setting_desc='default',mutate=None):
 c=Cursor([('on',)] if setting_rows=='default' else setting_rows,descriptors(1) if setting_desc=='default' else setting_desc,rows(b) if metadata_rows is None else metadata_rows,descriptors(19) if metadata_desc=='default' else metadata_desc)
 entered=[];called=[];error=None
 def shell(h,t,e,fn):
  entered.append(True)
  if mutate:mutate()
  return fn(c)
 try:
  with patch.object(epoch,'_run_fenced_epoch_operation',shell):epoch._run_ddl_fenced_epoch_operation(None,None,None,b,lambda cur:called.append(cur))
 except ValueError as e:error=str(e)
 return c,entered,called,error
check('legacy positional constructor defaults all three flags false',base.include_alter_routine is False and base.include_schema_ddl is False and base.include_database_ddl is False)
for a,s,d in itertools.product((False,True),repeat=3):
 b=replace(base,include_alter_routine=a,include_schema_ddl=s,include_database_ddl=d);label=f'flags={a},{s},{d}'
 c,entered,called,error=run(b)
 check(label+' exact ordered rows accept after setting gate',not error and called==[c] and c.fetched==[(0,2),(1,3+int(a)+int(s)+int(d))])
 check(label+' setting query is first and every SQL flag is static',c.executed[0][0]==("SELECT pg_catalog.current_setting('event_triggers')::pg_catalog.text",) and all(len(args)==1 for args,kw in c.executed) and (('true' if d else 'false')+" AND e.evtname='truss_database_ddl_writer_barrier'") in c.executed[1][0][0])
 c,entered,called,error=run(b,setting_rows=[('off',)])
 check(label+' event_triggers off refuses before metadata query',error=='Original native event trigger execution required' and len(c.executed)==1 and not called)
extended=replace(base,include_schema_ddl=True,include_alter_routine=True,include_database_ddl=True)
for label,rs in [('missing database',[r for r in rows(extended) if r[0]!='truss_database_ddl_writer_barrier']),('duplicate database',rows(extended)+[rows(extended)[0]]),('wrong order',list(reversed(rows(extended))))]:
 c,entered,called,error=run(extended,metadata_rows=rs);check(label+' refuses callback',error=='Exact original installed DDL barriers required' and not called)
for i in range(19):
 rs=rows(extended);r=list(rs[0]);assert r[0]=='truss_database_ddl_writer_barrier';r[i]='drift';rs[0]=tuple(r)
 c,entered,called,error=run(extended,metadata_rows=rs);check('database metadata field '+str(i)+' exact match required',error=='Exact original installed DDL barriers required' and not called)
for tags in ('null','[]','["COMMENT"]'):
 rs=rows(extended);r=list(rs[0]);r[4]=tags;rs[0]=tuple(r)
 c,entered,called,error=run(extended,metadata_rows=rs);check('SQL NULL tags distinct from '+tags,error=='Exact original installed DDL barriers required' and not called)
for field in ('include_database_ddl','include_schema_ddl','include_alter_routine'):
 for value in (None,0,1,'true',[],object()):
  b=replace(base,**{field:value});c,entered,called,error=run(b,metadata_rows=[])
  check(field+' nonbool '+type(value).__name__+' refuses before epoch host',bool(error) and not entered and not c.executed and not called)
for label,desc in [('none',None),('empty',[]),('two',descriptors(2)),('foreign NAME',[SimpleNamespace(type_code=19)])]:
 c,entered,called,error=run(extended,setting_desc=desc);check('setting '+label+' descriptor refuses before fetch',error=='Exact native event trigger setting descriptor required' and not c.fetched and len(c.executed)==1 and not called)
for label,rs in [('missing',[]),('two',[('on',),('on',)]),('null',[(None,)]),('text ON',[('ON',)]),('bool',[(True,)]),('extra column',[('on','on')]),('list row',[['on']])]:
 c,entered,called,error=run(extended,setting_rows=rs);check('setting '+label+' rows refuse before metadata',error=='Original native event trigger execution required' and c.fetched==[(0,2)] and len(c.executed)==1 and not called)
for i in range(19):
 ds=descriptors(19);ds[i].type_code=19;c,entered,called,error=run(extended,metadata_desc=ds)
 check('metadata foreign OID '+str(i)+' refuses before metadata fetch',error=='Exact original DDL barrier TEXT descriptors required' and c.fetched==[(0,2)] and not called)
changing=replace(extended)
c,entered,called,error=run(changing,mutate=lambda:object.__setattr__(changing,'include_database_ddl',False))
check('database selection captured before epoch host mutation',not error and called==[c] and c.fetched==[(0,2),(1,6)])
mapping=PreparedSecurityMapping(b'request',b'{}',accepted_catalog_assessment=b'assessment');relations=(_FactRelationComparison('truss','object',10,20,'guard'),)
def derive(b):return subject.derive_catalog_source_epoch_profile(mapping,relations,b,subject_source=b'helper')
p0,p1=derive(base),derive(replace(base,include_database_ddl=True));j0,j1=json.loads(p0),json.loads(p1)
check('profile0.3 binds exact default false and optin true distinctly',j0['interfaceVersion']=='truss-owned-catalog-source-profile/0.3' and j0['ddlBarrier']['includeDatabaseDdl'] is False and j1['ddlBarrier']['includeDatabaseDdl'] is True and p0!=p1)
for value in (None,0,1,'true'):
 try:derive(replace(base,include_database_ddl=value))
 except ValueError as e:check('profile refuses database selection '+repr(value),str(e)=='Exact native source barrier binding required')
 else:raise AssertionError(value)
files=['packages/python/src/truss/_psycopg_epoch_cut.py','scripts/security_catalog_subject_read.py','packages/postgresql/native/source-epoch-database-ddl-barrier.sql','packages/python/tests/test_security_catalog_source_cut_native.py']
record={'scope':'Actual Python readback and profile producer with synthetic native epoch/catalog carriers; no native event or lifecycle execution','count':len(checks),'controls':checks,'sourceSha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
(OUT/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'controls':len(checks),'passed':True}))
