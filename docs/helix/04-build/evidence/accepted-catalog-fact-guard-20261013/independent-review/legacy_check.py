from pathlib import Path
from unittest.mock import patch
from dataclasses import replace
import sys,json,copy,hashlib,subprocess
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent;E=ROOT/'docs/helix/04-build/evidence/accepted-catalog-policy-read-20261013'
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src')]
import security_catalog_read as read
from truss._security_mapping import PreparedSecurityMapping
assessment=json.loads((E/'assessment.json').read_bytes());packet=json.loads((E/'capture.json').read_bytes())[0]
request=(E/'request.json').read_bytes();response=(E/'owner-response.json').read_bytes();original=(E/'assessment.json').read_bytes()
transport=json.loads((read.BASE/'transport.json').read_bytes());document=json.loads(json.loads(request)['modules'][0]['documentJson'])
checks=[]
def check(n,v):assert v,n;checks.append({'name':n,'passed':True})
def recipe(a=assessment,t=transport,d=document):return read._catalog_record_recipe(a,t,d)
recipes=recipe();check('retained actual native recipes match current selector exactly',json.loads(json.dumps(recipes))==packet['recipes'])
check('actual accepted native type IDs are source-derived 1..5',set(r[0] for r in recipes)=={1,2,3,4,5})
cells=read._catalog_record_cells(recipes,packet['rows']);check('all association and entity captures use object homes',all(g['relation']==['truss','object'] for g in cells))
check('association presence matches actual Record identities',sorted(g['associations'][0][2] for g in cells if g['associations'])==['Assignment','Ownership'])
payload={'cells':cells,'subjectKey':[{'string':'s1'}],'resultMode':'resources'}
r=subprocess.run(['/opt/homebrew/bin/bun',str(ROOT/'scripts/evaluate-security-captured-identity-fixture.ts'),'--named-source'],cwd=ROOT,input=json.dumps(payload),text=True,capture_output=True,timeout=8)
check('retained native rows through genuine original UMF match native decision',r.returncode==0 and json.loads(r.stdout)==json.loads((E/'decision.json').read_bytes()))
for label,mutate in [
 ('missing native type',lambda a:a['inventory']['types'].pop(0)),
 ('duplicate active type',lambda a:a['inventory']['types'].append(copy.deepcopy(a['inventory']['types'][0]))),
 ('wrong type document',lambda a:a['inventory']['types'][0].__setitem__('document_id','other')),
 ('wrong type module',lambda a:a['inventory']['types'][0].__setitem__('module','other')),
 ('wrong type kind',lambda a:a['inventory']['types'][0].__setitem__('kind','entity')),
 ('provisional type',lambda a:a['inventory']['types'][0].__setitem__('provisional',True)),
 ('retired type',lambda a:a['inventory']['types'][0].__setitem__('retired_rev',2)),
 ('noninteger native type',lambda a:a['inventory']['types'][0].__setitem__('type_id',True)),
 ('missing native property',lambda a:a['inventory']['properties'].pop(0)),
 ('duplicate active property',lambda a:a['inventory']['properties'].append(copy.deepcopy(a['inventory']['properties'][0]))),
 ('property wrong owner',lambda a:a['inventory']['properties'][0].__setitem__('type_id',99)),
 ('property wrong document',lambda a:a['inventory']['properties'][0].__setitem__('definition_document_id','other')),
 ('property wrong module',lambda a:a['inventory']['properties'][0].__setitem__('declaration_module','other')),
 ('retired property',lambda a:a['inventory']['properties'][0].__setitem__('retired_rev',2)),
 ('wrong property home',lambda a:a['inventory']['properties'][0].__setitem__('home','edge')),
 ('wrong property cardinality',lambda a:a['inventory']['properties'][0].__setitem__('cardinality','many')),
 ('wrong property nullability',lambda a:a['inventory']['properties'][0].__setitem__('nullability','nullable')),
 ('unsupported scalar',lambda a:a['inventory']['properties'][0].__setitem__('scalar_type','integer')),
 ('missing native key',lambda a:a['inventory']['keys'].pop(0)),
 ('duplicate native key',lambda a:a['inventory']['keys'].append(copy.deepcopy(a['inventory']['keys'][0]))),
 ('wrong native key property',lambda a:a['inventory']['keys'][0].__setitem__('prop_ids',[999])),
 ('retired native key',lambda a:a['inventory']['keys'][0].__setitem__('retired_rev',2))]:
 a=copy.deepcopy(assessment);mutate(a)
 try:recipe(a)
 except ValueError:check(label+' refuses',True)
 else:raise AssertionError(label)
# Conditional order check using a synthetic extension of one compared key, explicitly not native multi-field qualification.
t=copy.deepcopy(transport);a=copy.deepcopy(assessment);rec=t['records'][0];rec['keyFields'].append({'documentId':'domain','moduleId':'m','elementId':'assignmentStaff'})
fields=recipes[0][2];native_ids=[int(next(addr for ref,addr,family in fields if ref==f)) for f in rec['keyFields']]
a['inventory']['keys'][0]['prop_ids']=native_ids;check('synthetic compared key retains original declared order',bool(recipe(a,t)))
a['inventory']['keys'][0]['prop_ids']=list(reversed(native_ids))
try:recipe(a,t)
except ValueError:check('synthetic swapped compared native key order refuses',True)
else:raise AssertionError('swapped key')
# Current wrapper custody with actual retained native packet and genuine owner evaluator.
changed=json.loads(original);changed['revision']=str(int(changed['revision'])+1);changed=json.dumps(changed,sort_keys=True,separators=(',',':')).encode()
class Cursor:
 def execute(self,s,*a,**kw):assert s=='LOCK TABLE ONLY truss.object IN SHARE MODE NOWAIT'
class Host:
 def __init__(self):self.entered=0
 def _run_operation(self,t,fn):self.entered+=1;return fn(Cursor(),None)
real_run=read.subprocess.run

def invoke(carrier=original,orig_request=request,drift=False):
 h=Host();captures=[];mapping=PreparedSecurityMapping(orig_request,response,accepted_catalog_assessment=carrier)
 def capture(c,r):assert r==request;captures.append(True);return changed if drift and len(captures)==2 else original
 def evaluate(*a,**kw):
  out=real_run(*a,**kw)
  if drift and type(carrier) is bytearray:carrier[:]=changed
  return out
 try:
  with patch.object(read,'_pin_cursor',lambda c:None),patch.object(read,'capture_accepted_catalog',capture),patch.object(read,'_text_rows',lambda *a:packet['rows']),patch.object(read.subprocess,'run',evaluate):result=read.run_owned_catalog_resource_read(h,None,mapping,'s1')
  status='published'
 except ValueError as e:status=str(e);result=None
 return status,h.entered,len(captures),result
s,h,c,r=invoke();check('immutable exact native assessment completes genuine evaluation',s=='published' and h==1 and c==2 and r==json.loads((E/'decision.json').read_bytes()))
s,h,c,r=invoke(drift=True);check('changed post-evaluation native assessment refuses output',s=='Accepted catalog changed during owned evaluation' and r is None and c==2)
for label,carrier in [('bytearray',bytearray(original)),('empty',b''),('oversize',b'x'*16777217),('text',original.decode()),('memoryview',memoryview(original))]:
 s,h,c,r=invoke(carrier=carrier,drift=True);check(label+' assessment refuses before host',s=='Original accepted-catalog fixture mapping required' and h==0 and c==0)
for label,value in [('bytearray',bytearray(request)),('empty',b''),('oversize',b'x'*4000001)]:
 s,h,c,r=invoke(orig_request=value);check(label+' request refuses before host',s=='Original accepted-catalog fixture mapping required' and h==0 and c==0)
def pin(p):p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
record={'count':len(checks),'controls':checks,'sourcePins':[pin(ROOT/'scripts/security_catalog_read.py'),pin(ROOT/'scripts/evaluate-security-captured-identity-fixture.ts'),pin(__file__)],'nativePacketPins':[pin(E/n) for n in ('request.json','assessment.json','capture.json','decision.json')],'scope':'Actual native packet recipe/cell correspondence and genuine original UMF evaluator replay; adverse inventories are controlled substitutions. Host/cursor/recapture shells are synthetic for custody tests. Two-field order controls are explicitly synthetic compared-key checks, not native multi-field qualification.'}
(OUT/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'controls':len(checks),'passed':True}))
