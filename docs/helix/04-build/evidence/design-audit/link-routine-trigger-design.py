from pathlib import Path
import json,hashlib,sys
repo=Path(__file__).resolve().parents[5]; root=repo/'docs/helix'
if sys.argv[1:] not in ([], ['--check']):raise SystemExit('usage: link-routine-trigger-design.py [--check]')
p=root/'02-design/contracts/reference-routine-design-v0.1.proposal.json';manifest=json.loads(p.read_text())
byname={r['originalContractName']:r for r in manifest['routines']}
for r in byname.values():r['originalTriggerReferences']=[]
seen=set()
for basename in ['truss-row-home-triggers.physical-ids.proposal.json','truss-edge-limit-triggers.physical-ids.proposal.json','truss-feed-current-union-trigger-effects.proposal.json']:
 catalog_path=root/'02-design/models'/basename; raw=catalog_path.read_bytes();catalog=json.loads(raw)
 for entry in catalog['entries']:
  if entry['objectKind']!='trigger':continue
  locator=entry['capturedModelLocator'];modelpath=repo/locator['modelPath'];modelraw=modelpath.read_bytes()
  if hashlib.sha256(modelraw).hexdigest()!=locator['modelSha256']:raise RuntimeError('model mismatch')
  node=json.loads(modelraw)
  for key in locator['jsonPointer'].split('/')[1:]:
   key=key.replace('~1','/').replace('~0','~');node=node[int(key)] if isinstance(node,list) else node[key]
  if 'originalNativeNode' in entry and entry['originalNativeNode']!=node:raise RuntimeError('original node mismatch')
  names=[x['members']['String']['members']['sval']['value'] for x in node['members']['funcname']['items']]
  if len(names)!=2 or names[0]!='truss' or names[1] not in byname:raise RuntimeError('unknown original handler')
  if entry['entryId'] in seen:raise RuntimeError('duplicate original identity')
  seen.add(entry['entryId'])
  byname[names[1]]['originalTriggerReferences'].append({'entryId':entry['entryId'],'parentId':entry['parentId'],'catalogPath':str(catalog_path.relative_to(root)),'catalogSha256':hashlib.sha256(raw).hexdigest(),'catalogEntryIndex':catalog['entries'].index(entry),'originalModelLocator':locator,'originalCallableParts':names})
counts={name:len(r['originalTriggerReferences']) for name,r in byname.items()}
if counts!={'row_touch_observe':3,'row_touch_commit_check':3,'edge_limit_observe':2,'edge_limit_catalog_observe':1,'feed_current_union_check':4,'feed_union_validate_current_scope':0,'edge_limit_verify_current_scope':0}:raise RuntimeError(counts)
if sys.argv[1:] == ['--check']:
 if json.loads(p.read_text())!=manifest:raise SystemExit('stale trigger-to-handler design links')
else:p.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'originalTriggerIdentities':len(seen),'handlerReferences':counts,'nativeQualified':False},indent=2))
