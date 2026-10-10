"""Feed source identity coverage only; no native/installer qualification."""
import copy,hashlib,json
from pathlib import Path
p=Path('docs/helix/02-design/models/truss-feed-native-layout.physical-ids.proposal.json');d=json.loads(p.read_text())
def require(ok,msg):
 if not ok:raise ValueError(msg)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=d['sources'][0];require(sha(source['source'])==source['sourceSha256'],'source hash');require(sha(source['model'])==source['modelSha256'],'model hash');model=json.loads(Path(source['model']).read_text())
expected=set()
def walk(n,p=''):
 if isinstance(n,dict):
  for k,v in n.items():
   q=p+'/'+k
   if k in ['CreateStmt','ColumnDef'] or (k=='Constraint' and v['members']['contype']['value'] in ['CONSTR_PRIMARY','CONSTR_UNIQUE','CONSTR_FOREIGN','CONSTR_CHECK']):expected.add(q)
   walk(v,q)
 elif isinstance(n,list):
  for i,v in enumerate(n):walk(v,p+'/'+str(i))
walk(model)
def verify(entries):
 ids=set();locations=set();counts={};tables={e['entryId'] for e in entries if e['objectKind']=='table'}
 require(tables=={'truss.feed.table.'+x for x in ['feed_tx','feed_member','feed_prerequisite','feed_configuration_prerequisite']},'independent table identities')
 for e in entries:
  require(e['entryId'] not in ids,'duplicate ID');ids.add(e['entryId']);require(e['nativeBinding']=={'state':'unresolved'},'native claim')
  if e['objectKind']!='table':require(e['parentId'] in tables,'original parent')
  loc=e['capturedModelLocator'];require(loc['modelPath']==source['model'] and loc['modelSha256']==source['modelSha256'],'original model custody');q=loc['jsonPointer'];require(q not in locations,'duplicate locator');locations.add(q);n=model
  for c in q.strip('/').split('/'):n=n[int(c)] if isinstance(n,list) else n[c]
  h=hashlib.sha256(json.dumps(n,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest();require(h==e['originalNativeNodeSha256'],'original node bytes')
  table_path=q if e['objectKind']=='table' else q.split('/members/tableElts/')[0]
  table_node=model
  for c in table_path.strip('/').split('/'):table_node=table_node[int(c)] if isinstance(table_node,list) else table_node[c]
  table_name=table_node['members']['relation']['members']['relname']['value'];original_parent='truss.feed.table.'+table_name
  native_name=table_name if e['objectKind']=='table' else n['members']['colname' if e['objectKind']=='column' else 'conname']['value']
  require(e['nativeName']==native_name,'native source name')
  require(e['entryId']==(original_parent if e['objectKind']=='table' else 'truss.feed.'+e['objectKind']+'.'+table_name+'.'+native_name),'original source identity')
  if e['objectKind']!='table':require(e['parentId']==original_parent,'original source parent correspondence')
  counts[e['objectKind']]=counts.get(e['objectKind'],0)+1
 require(locations==expected,'complete selected original source nodes');require(counts=={'table':4,'column':47,'constraint':17},'independent selected kind counts')
verify(d['entries']);controls=[]
for name,mutate in [('omitted source node',lambda x:x.pop()),('duplicate identity',lambda x:x.append(copy.deepcopy(x[0]))),('wrong parent',lambda x:next(e for e in x if e['objectKind']=='column').update(parentId='truss.feed.table.feed_member')),('substituted node',lambda x:x[0].update(originalNativeNodeSha256='0'*64)),('fabricated native binding',lambda x:x[0].update(nativeBinding={'state':'resolved'}))]:
 x=copy.deepcopy(d['entries']);mutate(x)
 try:verify(x)
 except ValueError:controls.append({'case':name,'refused':True})
 else:raise ValueError('accepted '+name)
r={'scope':d['scope'],'allocationSha256':sha(p),'entries':68,'counts':{'table':4,'column':47,'constraint':17},'selectedOriginalNodeCoverage':True,'controls':controls,'complete':False,'nativeExecution':False}
Path('docs/helix/04-build/evidence/design-audit/feed-physical-ids.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'entries':68,'refusals':len(controls),'complete':False,'nativeExecution':False}))
