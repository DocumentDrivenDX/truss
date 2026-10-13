from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
import sys,json,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src')]
from security_owned_read import _verify_named_subject_helper
from truss._psycopg_dependency_fact_cut import _DependencyFactProvider
from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison
source=(ROOT/'scripts/security-named-subject.sql').read_text().split('AS $$',1)[1].split('$$;',1)[0]
expected=('20','sql','f','1','25','25','true','false','false','v','u','false','0','["search_path=pg_catalog"]',source,'["actor", "staff_id"]','["i", "t"]','["25", "25"]','true')
provider=_DependencyFactProvider('field',('domain','m','staffId'),_FactRelationComparison('truss','sec_staff',10,20,'body'),_FactColumnComparison('staff_id',1,25,-1,True,0))
class Cursor:
 def __init__(self,description=None,rows=None):self.description=description;self.rows=rows;self.executed=0;self.fetched=0
 def execute(self,*args,**kwargs):self.executed+=1
 def fetchmany(self,n):assert n==2;self.fetched+=1;return self.rows
checks=[]
def run(name,desc,rows,providers=(provider,),success=False,fetch=1):
 c=Cursor(desc,rows)
 try:_verify_named_subject_helper(c,providers);ok=True
 except ValueError:ok=False
 assert ok==success and c.fetched==fetch,(name,ok,c.fetched)
 checks.append({'name':name,'passed':True,'fetches':c.fetched})
def descriptors():return [SimpleNamespace(type_code=25) for _ in range(19)]
run('exact metadata snapshot',descriptors(),[expected],success=True)
for i in range(19):
 d=descriptors();d[i].type_code=19;run('foreign NAME descriptor position '+str(i),d,[expected],fetch=0)
for name,d in [('absent',None),('short',descriptors()[:-1]),('long',descriptors()+[SimpleNamespace(type_code=25)])]:run(name+' descriptor',d,[expected],fetch=0)
for i in range(19):
 row=list(expected);row[i]='changed';run('native value drift position '+str(i),descriptors(),[tuple(row)])
for name,rows in [('no row',[]),('duplicate row',[expected,expected]),('short row',[expected[:-1]]),('null body',[expected[:14]+(None,)+expected[15:]])]:run(name,descriptors(),rows)
for name,p in [('missing staff',()),('duplicate staff',(provider,provider)),('wrong schema',(replace(provider,relation=replace(provider.relation,schema='other')),)),('wrong home',(replace(provider,relation=replace(provider.relation,name='other')),)),('wrong reference',(replace(provider,reference=('foreign','m','staffId')),))]:run(name,descriptors(),[expected],p,fetch=0)
# Equal metadata under a different selected owner must not pass.
run('original selected owner mismatch',descriptors(),[expected],(replace(provider,relation=replace(provider.relation,owner_oid=21)),))
for name,p in [('missing column',replace(provider,column=None)),('wrong column',replace(provider,column=replace(provider.column,name='other'))),('wrong column type',replace(provider,column=replace(provider.column,type_oid=19)))]:run(name,descriptors(),[expected],(p,),fetch=0)
for name,source_override in [('nontext source',b'body'),('empty source',''),('oversize source','x'*65537)]:
 c=Cursor(descriptors(),[expected])
 try:_verify_named_subject_helper(c,(provider,),expected_source=source_override)
 except ValueError:assert c.executed==0 and c.fetched==0;checks.append({'name':name,'passed':True,'fetches':0})
 else:raise AssertionError(name)
c=Cursor(descriptors(),[expected]);_verify_named_subject_helper(c,(provider,),expected_source=source);assert c.fetched==1;checks.append({'name':'captured original expected source positive','passed':True,'fetches':1})
def pin(p):b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
(OUT/'metadata-results.json').write_text(json.dumps({'count':len(checks),'controls':checks,'sourcePins':[pin(ROOT/'scripts/security_owned_read.py'),pin(ROOT/'scripts/security-named-subject.sql'),pin(Path(__file__))],'scope':'Actual snapshot validator with synthetic catalog descriptors/rows; no driver constructor, native query, privilege or lifetime qualification.'},indent=2)+'\n')
print(json.dumps({'controls':len(checks),'pass':True}))
