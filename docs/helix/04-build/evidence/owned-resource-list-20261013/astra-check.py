from pathlib import Path
import json,subprocess,copy,sys,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src')]
from security_owned_read import _read_owned_resource_receipt,_read_owned_evaluator_receipt
base=json.loads((OUT/'baseline.json').read_text());results=[]
def check(name,ok,extra=None):
 assert ok,name
 results.append({'name':name,'passed':True,**(extra or {})})
def evaluate(name,p,keys=None,legacy=False):
 r=subprocess.run(['/opt/homebrew/bin/bun','scripts/evaluate-security-captured-identity-fixture.ts'],cwd=ROOT,input=json.dumps(p),capture_output=True,text=True,timeout=10)
 if keys is None:check(name,r.returncode!=0 and r.stdout=='',{'refusal':True})
 else:
  assert r.returncode==0,(name,r.stderr)
  body=json.loads(r.stdout)
  if legacy:check(name,body['decision']=={'decision':'permit','output':[{'field':{'documentId':'domain','moduleId':'m','elementId':'salary'},'disposition':'withheld'}]})
  else:
   read=_read_owned_resource_receipt(r.stdout)
   check(name,set(read)=={'kind','rows'} and [v['key'][0]['string'] for v in read['rows']]==keys and all(set(v)=={'key','output'} and v['output']==[{'field':{'documentId':'domain','moduleId':'m','elementId':'salary'},'disposition':'withheld'}] for v in read['rows']))
  return body
mut=lambda:copy.deepcopy(base)
valid=evaluate('active resource only; no private identities',base,['r1'])
p=mut();p['cells'][0]['rows'][1][-1]='true';evaluate('new active membership admits sibling',p,['r1','r2'])
p=mut();[row.__setitem__(-1,'false') for row in p['cells'][0]['rows']];evaluate('all inactive gives empty rows',p,[])
p=mut();p['cells'][3]['rows']=[];evaluate('valid empty population preflights',p,[])
for empty in (False,True):
 p=mut();p['cells'][0]['rows'].append(copy.deepcopy(p['cells'][0]['rows'][0]))
 if empty:p['cells'][3]['rows']=[]
 evaluate('duplicate fact refuses '+('empty' if empty else 'nonempty'),p)
p=mut();p['cells'][0]['rows'].append(['a3','s1','p1','unknown']);evaluate('malformed late bool gives no partial output',p)
p=mut();p['cells'][4]['rows']=[];evaluate('missing selected subject refuses',p)
p=mut();p['cells'][4]['rows']*=2;evaluate('duplicate selected subject refuses',p)
p=mut();p['subjectKey']=[{'integer':'1'}];evaluate('wrong subject key family refuses',p)
p=mut();p['extra']=1;evaluate('extra envelope member refuses',p)
p=mut();p['resultMode']='other';evaluate('unknown result mode refuses',p)
p=mut();del p['subjectKey'];evaluate('unbound resources mode refuses',p)
p=mut();p['cells'].pop();evaluate('missing capture refuses',p)
p=mut();p['cells'][1]['associations']=[];evaluate('missing association capture refuses',p)
p=mut();p['cells'][0]['rows'][0].append('extra');evaluate('wrong row width refuses',p)
p=mut();p['cells'][0]['rows']=[];p['cells'][1]['rows']=[];p['cells'][2]['rows']=[['p1']];p['cells'][3]['rows']=[['other'+str(i)] for i in range(98)];evaluate('exact 100 total facts within work bound accepted',p,[])
p['cells'][3]['rows'].append(['overflow']);evaluate('101 total facts refused by original collection',p)
p=mut();p['cells'][3]['rows']=[['r1']];del p['resultMode'];evaluate('legacy bound single result preserved',p,['r1'],True)
evaluate('legacy unbound single result preserved',p['cells'],['r1'],True)
# Closed Python publication carrier only; literal/domain meaning belongs to UMF.
check('receipt accepts original withheld result',_read_owned_resource_receipt(json.dumps(valid))==valid)
empty={'kind':'owned-resource-list-fixture/0.1','rows':[]};check('receipt accepts empty result',_read_owned_resource_receipt(json.dumps(empty))==empty)
variants=[]
def variant(name,fn):
 p=copy.deepcopy(valid);fn(p);variants.append((name,p))
variant('extra top-level member',lambda p:p.update(identities=[]))
variant('wrong kind',lambda p:p.update(kind='other'))
variant('rows not list',lambda p:p.update(rows={}))
variant('rows above 100',lambda p:p.update(rows=p['rows']*101))
variant('extra row member',lambda p:p['rows'][0].update(rawCells=[]))
variant('missing key',lambda p:p['rows'][0].pop('key'))
variant('empty key',lambda p:p['rows'][0].update(key=[]))
variant('key above 32',lambda p:p['rows'][0].update(key=[{'string':'s'}]*33))
variant('output not list',lambda p:p['rows'][0].update(output={}))
variant('disposition unknown',lambda p:p['rows'][0]['output'][0].update(disposition='permit'))
variant('withheld leaks value',lambda p:p['rows'][0]['output'][0].update(value={'integer':'100'}))
variant('extra field ref member',lambda p:p['rows'][0]['output'][0]['field'].update(oid=123))
variant('missing field ref component',lambda p:p['rows'][0]['output'][0]['field'].pop('moduleId'))
variant('blank field ref component',lambda p:p['rows'][0]['output'][0]['field'].update(moduleId=''))
for name,p in variants:
 try:_read_owned_resource_receipt(json.dumps(p))
 except ValueError:check('receipt refuses '+name,True)
 else:raise AssertionError(name)
for name,raw in [('duplicate top-level key','{"kind":"owned-resource-list-fixture/0.1","rows":[],"rows":[]}'),('nonfinite','{"kind":"owned-resource-list-fixture/0.1","rows":[NaN]}')]:
 try:_read_owned_resource_receipt(raw)
 except ValueError:check('receipt refuses '+name,True)
 else:raise AssertionError(name)
paths=[ROOT/'scripts/evaluate-security-captured-identity-fixture.ts',ROOT/'scripts/security_owned_read.py',Path('/Users/erik/.codex/worktrees/security-main-integration/umf/src/extensions/security/evaluate.ts'),Path('/Users/erik/.codex/worktrees/security-main-integration/umf/tests/security/fixture.ts')]
def pin(p):b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
(OUT/'results.json').write_text(json.dumps({'count':len(results),'controls':results,'sourcePins':[pin(p) for p in paths],'scope':'Pure actual fixed evaluator through Bun and Python closed publication parser; not a native privilege or transaction replay.'},indent=2)+'\n')
print(json.dumps({'count':len(results),'pass':True}))
