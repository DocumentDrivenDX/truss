"""Source-derived expected feed index/reference effects; never native inventory."""
import copy, hashlib, json
from pathlib import Path
base=Path('docs/helix/02-design/models/truss-feed-native-layout.physical-ids.proposal.json')
out=Path('docs/helix/02-design/models/truss-feed-native-layout.derived-effects.proposal.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
d=json.loads(base.read_text());model=json.loads(Path(d['sources'][0]['model']).read_text())
def require(ok,message):
 if not ok:raise ValueError(message)
def names(n):return [x['members']['String']['members']['sval']['value'] for x in n['items']]
expected=[]
for e in d['entries']:
 if e['objectKind']!='constraint':continue
 n=model
 for k in e['capturedModelLocator']['jsonPointer'].strip('/').split('/'):n=n[int(k)] if isinstance(n,list) else n[k]
 m=n['members'];kind=m['contype']['value'];table=e['parentId'].split('.')[-1]
 common={'creatorId':e['entryId'],'parentId':e['parentId'],'capturedModelLocator':e['capturedModelLocator'],'originalNativeNodeSha256':e['originalNativeNodeSha256'],'nativeBinding':{'state':'unresolved'}}
 if kind in ['CONSTR_PRIMARY','CONSTR_UNIQUE']:
  expected.append(dict(common,entryId='truss.feed.supporting-index.'+table+'.'+e['nativeName'],objectKind='expected_supporting_index',orderedColumnIds=['truss.feed.column.'+table+'.'+c for c in names(m['keys'])],constraintKind=kind,nativeName=None))
 if kind=='CONSTR_FOREIGN':
  require(len(names(m['fk_attrs']))==len(names(m['pk_attrs']))==3,'original complete FK arity')
  target=m['pktable']['members'];require(target['schemaname']['value']=='truss' and target['relname']['value']=='feed_tx','original reference target')
  expected.append(dict(common,entryId='truss.feed.reference.'+table+'.'+e['nativeName'],objectKind='source_foreign_key_reference',targetTableId='truss.feed.table.feed_tx',targetKeyCreatorId='truss.feed.constraint.feed_tx.feed_tx_pk',orderedColumnPairs=[{'sourceColumnId':'truss.feed.column.'+table+'.'+a,'targetColumnId':'truss.feed.column.feed_tx.'+b} for a,b in zip(names(m['fk_attrs']),names(m['pk_attrs']))],nativeActions={k:m[k]['value'] for k in ['fk_matchtype','fk_upd_action','fk_del_action']}))
# Authored semantic expectation is independent of the source walker and allocation.
context=['source_epoch','feed_profile','original_writer_xid']
index_specs={
 ('feed_tx','feed_tx_pk'):('CONSTR_PRIMARY',context),
 ('feed_member','feed_member_pk'):('CONSTR_PRIMARY',context+['registration_address']),
 ('feed_member','feed_member_delivery_unique'):('CONSTR_UNIQUE',context+['delivery_ordinal']),
 ('feed_prerequisite','feed_prerequisite_pk'):('CONSTR_PRIMARY',context+['prerequisite_address']),
 ('feed_configuration_prerequisite','feed_configuration_prerequisite_pk'):('CONSTR_PRIMARY',context+['configuration_address'])}
reference_specs={('feed_member','feed_member_tx_fk'),('feed_prerequisite','feed_prerequisite_tx_fk'),('feed_configuration_prerequisite','feed_configuration_prerequisite_tx_fk')}
def verify_semantics(entries):
 seen_indexes=set();seen_references=set()
 for e in entries:
  table=e['parentId'].split('.')[-1];creator=e['creatorId'].split('.')[-1];key=(table,creator)
  require(e['creatorId']=='truss.feed.constraint.'+table+'.'+creator,'creator table')
  if e['objectKind']=='expected_supporting_index':
   require(key in index_specs and key not in seen_indexes,'independent index membership');seen_indexes.add(key)
   kind,columns=index_specs[key]
   require(e['constraintKind']==kind and e['orderedColumnIds']==['truss.feed.column.'+table+'.'+c for c in columns],'independent index key/kind')
  elif e['objectKind']=='source_foreign_key_reference':
   require(key in reference_specs and key not in seen_references,'independent reference membership');seen_references.add(key)
   require(e['targetTableId']=='truss.feed.table.feed_tx' and e['targetKeyCreatorId']=='truss.feed.constraint.feed_tx.feed_tx_pk','independent target key')
   require(e['orderedColumnPairs']==[{'sourceColumnId':'truss.feed.column.'+table+'.'+c,'targetColumnId':'truss.feed.column.feed_tx.'+c} for c in context],'independent paired columns')
   require(e['nativeActions']=={'fk_matchtype':'s','fk_upd_action':'a','fk_del_action':'a'},'independent reference actions')
  else:raise ValueError('unknown effect kind')
 require(seen_indexes==set(index_specs) and seen_references==reference_specs,'complete independent membership')
verify_semantics(expected)
require(len(expected)==8,'independent effect count')
def verify(candidate):
 verify_semantics(candidate)
 require(candidate==expected,'complete original source correspondence')
 ids=[e['entryId'] for e in candidate];require(len(ids)==len(set(ids)) and not set(ids)&{e['entryId'] for e in d['entries']},'identity collision')
 require(sum(e['objectKind']=='expected_supporting_index' for e in candidate)==5,'index count')
 for e in candidate:
  if e['objectKind']=='source_foreign_key_reference':
   require(len(e['orderedColumnPairs'])==3,'complete reference arity')
   require([p['targetColumnId'].split('.')[-1] for p in e['orderedColumnPairs']]==['source_epoch','feed_profile','original_writer_xid'],'independent target order')
if not out.exists():
 out.write_text(json.dumps({'profile':'truss-feed-derived-effects/0.1.0','status':'unadopted_candidate','complete':False,'scope':'Five expected constraint-supporting indexes and three original FK relation/ordered-column references. Reference IDs describe source edges, not extra pg_constraint objects. No FK referencing-side index is inferred. Native names/OIDs, generated triggers, operator classes, collations, privileges and dependencies remain unresolved.','allocationPath':str(base),'allocationSha256':sha(base),'sources':d['sources'],'entries':expected},indent=2)+'\n')
a=json.loads(out.read_text());require(a['allocationSha256']==sha(base),'original allocation hash')
for s in a['sources']:
 require(sha(s['source'])==s['sourceSha256'] and sha(s['model'])==s['modelSha256'],'original source hashes')
verify(a['entries']);controls=[]
for label,mutate in [('omitted index',lambda x:x.pop(0)),('invented FK-side index',lambda x:x.append(dict(x[0],entryId='invented'))),('reversed reference columns',lambda x:next(e for e in x if 'orderedColumnPairs' in e)['orderedColumnPairs'].reverse()),('wrong creator',lambda x:x[0].update(creatorId=d['entries'][0]['entryId'])),('invented native name',lambda x:x[0].update(nativeName='guessed')),('forged native binding',lambda x:x[0].update(nativeBinding={'state':'resolved'}))]:
 x=copy.deepcopy(a['entries']);mutate(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
# These controls invoke the semantic oracle alone: source/allocation equality is
# deliberately unavailable, so matching a jointly changed candidate cannot pass.
semantic_controls=[]
for label,mutate in [
 ('wrong member address key',lambda x:next(e for e in x if e['creatorId'].endswith('.feed_member_pk'))['orderedColumnIds'].__setitem__(-1,'truss.feed.column.feed_member.delivery_ordinal')),
 ('delivery key treated as primary',lambda x:next(e for e in x if e['creatorId'].endswith('.feed_member_delivery_unique')).update(constraintKind='CONSTR_PRIMARY')),
 ('foreign key cascade substitution',lambda x:next(e for e in x if 'nativeActions' in e)['nativeActions'].update(fk_del_action='c')),
 ('source reference column substitution',lambda x:next(e for e in x if 'orderedColumnPairs' in e)['orderedColumnPairs'][0].update(sourceColumnId='truss.feed.column.feed_member.feed_profile'))]:
 x=copy.deepcopy(expected);mutate(x)
 try:verify_semantics(x)
 except ValueError:semantic_controls.append({'case':label,'refused':True})
 else:raise ValueError('semantic oracle accepted '+label)
r={'scope':a['scope'],'derivedEffectsSha256':sha(out),'expectedSupportingIndexes':5,'sourceForeignKeyReferences':3,'controls':controls,'independentSemanticControls':semantic_controls,'complete':False,'nativeExecution':False}
Path('docs/helix/04-build/evidence/design-audit/feed-derived-effects.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
