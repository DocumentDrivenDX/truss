from pathlib import Path
import json,sys,subprocess,copy,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'packages/python/src'),str(ROOT/'scripts')]
import security_graph_read as graph

def props(address,text):return json.dumps({address:{'kind':'string','text':text}})
nodes=[['100','100',props('1','s1'),'false'],['200','101',props('2','p1'),'false'],['201','101',props('2','p2'),'false'],['300','102',props('3','r1'),'false'],['301','102',props('3','r2'),'false']]
edges=[['100','100','100','100','200','101',json.dumps({'4':{'kind':'string','text':'a1'},'5':{'kind':'boolean','value':True}})],['104','100','100','100','201','101',json.dumps({'4':{'kind':'string','text':'a2'},'5':{'kind':'boolean','value':False}})],['102','102','300','102','200','101',props('6','o1')],['103','102','301','102','201','101',props('6','o2')]]
checks=[];responses=[]
def check(n,p):assert p,n;checks.append({'name':n,'passed':True})
def invoke(ns=nodes,es=edges,subject='s1'):
 try:cells=graph._project_graph_cells(ns,es)
 except ValueError as e:return ('projection-refused',str(e))
 payload={'cells':cells,'subjectKey':[{'string':subject}],'resultMode':'resources'}
 r=subprocess.run(['/opt/homebrew/bin/bun',str(ROOT/'scripts/evaluate-security-captured-identity-fixture.ts'),'--named-source'],cwd=ROOT,input=json.dumps(payload),text=True,capture_output=True,timeout=8)
 if r.returncode:return ('evaluator-refused',r.stderr)
 return ('ok',json.loads(r.stdout))
s,r=invoke();check('actual original UMF baseline selects business r1 with salary withheld',s=='ok' and r['rows']==[{'key':[{'string':'r1'}],'output':[{'field':{'documentId':'domain','moduleId':'m','elementId':'salary'},'disposition':'withheld'}]}])
responses.append({'name':'baseline','result':r})
def changed_active(v0,v1):
 es=copy.deepcopy(edges)
 for i,v in enumerate((v0,v1)):
  p=json.loads(es[i][6]);p['5']['value']=v;es[i][6]=json.dumps(p)
 return es
for a,b,keys in ((True,True,['r1','r2']),(False,False,[]),(False,True,['r2'])):
 s,r=invoke(es=changed_active(a,b));check('active assignments '+str((a,b)),s=='ok' and [x['key'][0]['string'] for x in r['rows']]==keys)
s,r=invoke(es=edges[:2]);check('ownerless resources omitted by original policy',s=='ok' and r['rows']==[])
s,r=invoke(subject='unknown');check('unmapped administrative subject refuses',s=='evaluator-refused' and 'Unique original mapped subject required' in r)
# Endpoint and native mapped cell checks are actual Python projection checks.
for name,fn in [
 ('wrong source type',lambda ns,es:es[0].__setitem__(3,'102')),
 ('wrong target type',lambda ns,es:es[0].__setitem__(5,'100')),
 ('missing source',lambda ns,es:es[0].__setitem__(2,'999')),
 ('missing target',lambda ns,es:es[0].__setitem__(4,'999')),
 ('selected nested object',lambda ns,es:ns[0].__setitem__(3,'true')),
 ('unknown selected node type',lambda ns,es:ns[0].__setitem__(1,'999')),
 ('unknown selected relation type',lambda ns,es:es[0].__setitem__(1,'999')),
 ('duplicate typed native node',lambda ns,es:ns.append(ns[0][:])),
 ('missing business key',lambda ns,es:ns[0].__setitem__(2,'{}')),
 ('wrong scalar family',lambda ns,es:ns[0].__setitem__(2,'{"1":{"kind":"boolean","value":true}}')),
 ('extra scalar member',lambda ns,es:ns[0].__setitem__(2,'{"1":{"kind":"string","text":"s1","x":0}}')),
 ('invalid key payload',lambda ns,es:ns[0].__setitem__(2,'{"1":{"kind":"string","text":null}}')),
 ('invalid active payload',lambda ns,es:es[0].__setitem__(6,'{"4":{"kind":"string","text":"a1"},"5":{"kind":"boolean","value":1}}')),
 ('duplicate JSON property',lambda ns,es:ns[0].__setitem__(2,'{"1":{"kind":"string","text":"s1"},"1":{"kind":"string","text":"s2"}}'))]:
 ns=copy.deepcopy(nodes);es=copy.deepcopy(edges);fn(ns,es);s,r=invoke(ns,es);check(name+' fails before original evaluator',s=='projection-refused')
# Different native IDs must not make duplicate semantic identities valid.
for index,kind in ((0,'Staff'),(1,'Project'),(3,'Resource')):
 ns=copy.deepcopy(nodes);extra=ns[index][:];extra[0]='999';ns.append(extra)
 s,r=invoke(ns);check('duplicate original '+kind+' semantic key refuses',s=='evaluator-refused' and 'Unique original captured semantic identity required' in r)
for index,kind in ((0,'Assignment'),(2,'Ownership')):
 es=copy.deepcopy(edges);extra=es[index][:];extra[0]='999';es.append(extra)
 s,r=invoke(es=es);check('duplicate original '+kind+' semantic key refuses',s=='evaluator-refused' and 'Unique original captured semantic identity required' in r)
# Reusing a value in different original record domains is allowed; native IDs still only route edges.
ns=copy.deepcopy(nodes);ns[3][2]=props('3','s1');s,r=invoke(ns);check('same business text across distinct record domains stays distinct',s=='ok' and r['rows'][0]['key']==[{'string':'s1'}])
# Native IDs can change without changing original semantics if endpoint references change together.
ns=copy.deepcopy(nodes);es=copy.deepcopy(edges)
for n in ns:n[0]=str(int(n[0])+1000)
for e in es:e[0]=str(int(e[0])+1000);e[2]=str(int(e[2])+1000);e[4]=str(int(e[4])+1000)
s,r=invoke(ns,es);check('native identity renumbering preserves original business result',s=='ok' and r==responses[0]['result'])
# Shared flat evaluator remains compatible; every record duplicate is now rejected even outside subject selection.
payload=json.loads(Path('/private/tmp/resource-list-review-20261013/baseline.json').read_bytes())
for extra in (False,True):
 p=copy.deepcopy(payload)
 if extra:
  g=next(x for x in p['cells'] if x['fields'][0][0][2]=='resourceId');g['rows'].append(g['rows'][0][:])
 r=subprocess.run(['/opt/homebrew/bin/bun',str(ROOT/'scripts/evaluate-security-captured-identity-fixture.ts')],cwd=ROOT,input=json.dumps(p),text=True,capture_output=True,timeout=8)
 check('legacy flat '+('duplicate refusal' if extra else 'positive retained'),(r.returncode!=0 and 'Unique original captured semantic identity required' in r.stderr and not r.stdout) if extra else r.returncode==0)
# Final native-shaped extension: ownerless r3 and sibling p3/r4 are excluded.
for active2 in (False,True):
 ns=copy.deepcopy(nodes)+[['302','102',props('3','r3'),'false'],['303','102',props('3','r4'),'false'],['202','101',props('2','p3'),'false']]
 es=changed_active(True,active2)+[['105','102','303','102','202','101',props('6','o3')]]
 status,result=invoke(ns,es)
 check('ownerless/sibling resources excluded with active p2 '+str(active2),status=='ok' and [x['key'][0]['string'] for x in result['rows']]==(['r1','r2'] if active2 else ['r1']))

def pin(p):p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
record={'count':len(checks),'controls':checks,'genuineOwnerBaseline':responses,'sourcePins':[pin(ROOT/'scripts/security_graph_read.py'),pin(ROOT/'scripts/evaluate-security-captured-identity-fixture.ts'),pin(__file__)],'scope':'Actual fixed Python graph projection and genuine Bun original UMF named/legacy evaluator from synthetic original native text rows. No native query, source/lock/role custody or authenticated mapping qualification.'}
(OUT/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'controls':len(checks),'passed':True}))
