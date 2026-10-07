"""Authored trigger and expected associated constraint identities; no native binding."""
import copy,hashlib,json
from pathlib import Path
path=Path('docs/helix/02-design/models/truss-feed-current-union-trigger-effects.proposal.json');candidate=json.loads(path.read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
node_sha=lambda n:hashlib.sha256(json.dumps(n,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def pointer(m,p):
 for bit in p.split('/')[1:]:m=m[int(bit)] if isinstance(m,list) else m[bit.replace('~1','/').replace('~0','~')]
 return m
allocation=json.loads(Path(candidate['tableAllocationPath']).read_text());tables={e['nativeName']:e['entryId'] for e in allocation['entries'] if e['objectKind']=='table'}
expected_tables=['feed_tx','feed_member','feed_prerequisite','feed_configuration_prerequisite']
def verify(c):
 require(c['complete'] is False and c['profile']=='truss-feed-trigger-effects/0.1.0','scoped profile');require(sha(c['tableAllocationPath'])==c['tableAllocationSha256'],'original table allocation')
 require(len(c['sources'])==1,'one original trigger source');src=c['sources'][0]
 require(sha(src['source'])==src['sourceSha256'] and sha(src['model'])==src['modelSha256'],'original source/model pins');m=json.loads(Path(src['model']).read_text())
 entries=c['entries'];require(len(entries)==8 and len({e['entryId'] for e in entries})==8,'eight distinct allocated identities');require(not ({e['entryId'] for e in entries}&{e['entryId'] for e in allocation['entries']}),'no reused baseline identities')
 for i,table in enumerate(expected_tables):
  trigger,constraint=entries[2*i:2*i+2];name=table+'_current_union_guard';tid='truss.feed.trigger.'+name
  for e in [trigger,constraint]:
   require(e['parentId']==tables[table] and e['nativeName']==name and e['nativeBinding']=={'state':'unresolved'},'original parent/name/unresolved binding')
   loc=e['capturedModelLocator'];require(loc['modelPath']==src['model'] and loc['modelSha256']==src['modelSha256'] and loc['jsonPointer']==f'/modules/0/elements/0/extensions/umf.postgresql/root/members/stmts/items/{i}/members/stmt/members/CreateTrigStmt','exact original node locator')
   node=pointer(m,loc['jsonPointer']);require(node_sha(node)==e['originalNativeNodeSha256'],'original retained node');n=node['members'];require(n['trigname']['value']==name and n['relation']['members']['relname']['value']==table and n['isconstraint']['value'] is True,'actual creator source')
  require(trigger['entryId']==tid and trigger['objectKind']=='trigger' and trigger['sourceEventMask']=='28' and trigger['row'] is True and trigger['timing']=='AFTER','trigger identity/events')
  require(trigger['deferrable'] is True and trigger['initiallyDeferred'] is True and trigger['callableReference']=={'schema':'truss','name':'feed_current_union_check','bodyState':'undefined_unqualified'},'original deferred callable source')
  require(constraint['entryId']=='truss.feed.trigger-constraint.'+name and constraint['objectKind']=='expected_trigger_constraint' and constraint['creatorId']==tid and constraint['constraintKind']=='CONSTRAINT_TRIGGER' and constraint['supportingIndexExpected'] is False and constraint['deferrable'] is True and constraint['initiallyDeferred'] is True,'associated constraint creator/meaning')
verify(candidate);controls=[]
for label,mutate in [('missing associated constraint',lambda c:c['entries'].pop()),('wrong trigger parent',lambda c:c['entries'][0].update(parentId=tables['feed_member'])),('wrong constraint creator',lambda c:c['entries'][1].update(creatorId=c['entries'][2]['entryId'])),('duplicate identity',lambda c:c['entries'][1].update(entryId=c['entries'][0]['entryId'])),('forged native binding',lambda c:c['entries'][0].update(nativeBinding={'state':'qualified'})),('invented supporting index',lambda c:c['entries'][1].update(supportingIndexExpected=True)),('altered source node hash',lambda c:c['entries'][2].update(originalNativeNodeSha256='0'*64)),('inflated completeness',lambda c:c.update(complete=True))]:
 x=copy.deepcopy(candidate);mutate(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
Path('docs/helix/04-build/evidence/design-audit/feed-trigger-effects.json').write_text(json.dumps({'scope':'Eight authored trigger/associated-constraint identities and original table/source/node/creator correspondence only; no installed object count or native enforcement proof','allocationPath':str(path),'allocationSha256':sha(path),'entries':8,'controls':controls,'nativeExecution':False,'complete':False},indent=2)+'\n');print(json.dumps({'entries':8,'refusals':len(controls),'nativeExecution':False}))
