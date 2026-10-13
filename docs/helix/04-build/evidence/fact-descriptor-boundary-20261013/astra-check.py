from pathlib import Path
from types import SimpleNamespace,ModuleType
from unittest.mock import patch
import json,sys,subprocess,hashlib
import truss._psycopg_fact_cut as current
import truss._psycopg_epoch_cut as epoch
ROOT=Path('/private/tmp/truss-security-main-integration')
OUT=Path(__file__).parent
WIDTHS=(7,12,9)
ROWS=[('10','20','r','p','false','false','false'),('A','62','0','','false','true','20','false','v','["search_path=pg_catalog, pg_temp"]','body','false'),('id','1','25','-1','true','0','','','false')]
results=[]
class Cursor:
    def __init__(self,bad=None):self.stage=0;self.description=None;self.bad=bad;self.fetches=[]
    def execute(self,statement,*a,**kw):
        if str(statement).startswith('SELECT'):
            self.stage+=1;self.description=[SimpleNamespace(type_code=25) for _ in range(WIDTHS[self.stage-1])]
            if self.bad and self.bad[0]==self.stage:
                kind=self.bad[1]
                if kind=='oid':self.description[self.bad[2]].type_code=19
                if kind=='none':self.description=None
                if kind=='short':self.description.pop()
                if kind=='long':self.description.append(SimpleNamespace(type_code=25))
    def fetchmany(self,n):
        assert n==2;self.fetches.append(self.stage)
        if self.bad and self.bad[0]==self.stage:
            kind=self.bad[1]
            if kind in ('oid','none','short','long'):raise AssertionError('foreign row loader reached')
            if kind=='empty':return []
            if kind=='duplicate':return [ROWS[self.stage-1]]*2
            if kind=='wrong':return [('different',)+ROWS[self.stage-1][1:]]
        return [ROWS[self.stage-1]]
def run(mod,bad,route):
    cursor=Cursor(bad);called=[]
    relation=mod._FactRelationComparison('truss','fact',10,20,'body',(mod._FactColumnComparison('id',1,25,-1,True,0),))
    def plain(h,t,c,acquire):return acquire(cursor)
    def ddl(h,t,c,d,acquire):return acquire(cursor)
    try:
        with patch.object(mod,'_run_fenced_epoch_operation',plain),patch.object(epoch,'_run_ddl_fenced_epoch_operation',ddl):
            value=mod._run_fenced_fact_operation(None,None,None,(relation,),lambda c:called.append(c) or 'complete',ddl_barrier='opaque-selected-premise' if route=='ddl' else None)
        result='complete';assert value=='complete'
    except ValueError:result='refused'
    except AssertionError as e:
        if str(e)!='foreign row loader reached':raise
        result='foreign-fetch'
    return result,cursor,called
for route in ('epoch','ddl'):
    r,c,called=run(current,None,route);assert r=='complete' and c.fetches==[1,2,3] and called==[c]
    results.append({'route':route,'case':'positive exact descriptors and rows','pass':True})
    for stage,width in enumerate(WIDTHS,1):
        variants=[(stage,'oid',i) for i in range(width)]+[(stage,k) for k in ('none','short','long','empty','duplicate','wrong')]
        for variant in variants:
            r,c,called=run(current,variant,route)
            assert r=='refused' and not called,(route,variant,r)
            if variant[1] in ('oid','none','short','long'):assert c.fetches==list(range(1,stage))
            else:assert c.fetches==list(range(1,stage+1))
            results.append({'route':route,'case':list(variant),'pass':True})
old_source=subprocess.check_output(['git','show','HEAD:packages/python/src/truss/_psycopg_fact_cut.py'],cwd=ROOT,text=True)
(OUT/'prechange.py').write_text(old_source)
old=ModuleType('truss._review_fact_cut_prechange');sys.modules[old.__name__]=old
exec(compile(old_source,str(OUT/'prechange.py'),'exec'),old.__dict__)
prechange=[]
for stage in (1,2,3):
    r,c,called=run(old,(stage,'oid',0),'epoch');assert r=='foreign-fetch' and stage in c.fetches and not called
    prechange.append({'stage':stage,'foreignFetchBeforeRefusal':True})
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
record={'currentControls':results,'count':len(results),'prechangeReproductions':prechange,'sourcePins':[pin(current.__file__),pin(OUT/'check.py'),pin(OUT/'prechange.py')],'scope':'Actual fact-cut acquire logic with synthetic descriptors/rows and replaced epoch/DDL host shells; verifies descriptor-before-fetch and callback ordering only, not native adaptation or transaction custody.'}
(OUT/'results.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'currentControls':len(results),'passed':True,'prechangeReproductions':3,'sourceSha256':record['sourcePins'][0]['sha256']}))
