from pathlib import Path
import json,hashlib,sys
repo=Path(__file__).resolve().parents[5]; root=repo/'docs/helix'
if sys.argv[1:] not in ([], ['--check']):raise SystemExit('usage: link-routine-trigger-design.py [--check]')
p=root/'02-design/contracts/reference-routine-design-v0.1.proposal.json';manifest=json.loads(p.read_text())
def require(condition, message):
 if not condition:raise RuntimeError(message)
require(manifest['interfaceVersion']=='truss-reference-routine-design/0.1.0','design version')
require(manifest['status']=='selected_design_fields_incomplete_native_binding' and manifest['nativeQualified'] is False and manifest['installerReady'] is False,'unqualified design scope')
expected_attributes={'language':'plpgsql','volatility':'VOLATILE','parallel':'UNSAFE','nullInput':'CALLED ON NULL INPUT','leakproof':False,'security':'DEFINER','searchPathRecipe':['pg_catalog',{'trustedInstallationNamespace':True},'pg_temp'],'publicExecute':False,'ordinaryApplicationExecute':False}
require(manifest['sharedSelectedAttributes']==expected_attributes,'selected attribute mismatch')
expected_sources={'02-design/contracts/CONTRACT-001-storage-layout.md','02-design/contracts/CONTRACT-005-module-isolation.md','02-design/contracts/CONTRACT-006-change-feed.md','02-design/architecture.md'}
require(len(manifest['governingSources'])==4 and {x['path'] for x in manifest['governingSources']}==expected_sources,'governing source membership')
for source in manifest['governingSources']:
 require(hashlib.sha256((root/source['path']).read_bytes()).hexdigest()==source['sha256'],'governing source drift')
expected_owners={'row_touch_observe':'Touch observation owner','row_touch_commit_check':'Commit-check owner','edge_limit_observe':'Touch observation owner','edge_limit_catalog_observe':'Touch observation owner','feed_current_union_check':'Commit-check owner','feed_union_validate_current_scope':'Integrity/finalization owner','edge_limit_verify_current_scope':'Integrity/finalization owner'}
require(len(manifest['routines'])==7 and {r['originalContractName'] for r in manifest['routines']}==set(expected_owners),'required routine membership')
for routine in manifest['routines']:
 name=routine['originalContractName'];result='void' if name in ('feed_union_validate_current_scope','edge_limit_verify_current_scope') else 'trigger'
 require(routine['sqlArgumentTypes']==[] and routine['resultType']==result,'selected signature mismatch')
 require(routine['ownerResponsibility']==expected_owners[name],'selected owner responsibility mismatch')
 require(routine['invocationKind']==('installed_trigger_only' if result=='trigger' else 'registered_private_call_only'),'private invocation mismatch')
 dependencies=['edge_limit_verify_current_scope','feed_union_validate_current_scope'] if name=='row_touch_commit_check' else ['feed_union_validate_current_scope'] if name=='feed_current_union_check' else []
 require(routine['selectedValidatorDependencies']==[{'originalContractName':d,'when':'complete_feed_selected' if d.startswith('feed') else 'edge_limit_scope_selected'} for d in dependencies],'selected validator dependency mismatch')
 require(routine['unresolvedNativeBinding']=={k:None for k in ['physicalIdentity','namespace','bodyArtifact','nativeOwnerRole','completeDependencyInventory','exactPrivateCallerAcl','nativeQualificationReceipt']},'unresolved native binding changed; new reviewed profile required')
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
missing={name:[field for field,value in routine['unresolvedNativeBinding'].items() if value is None] for name,routine in byname.items()}
print(json.dumps({'scope':'Selected incomplete design/source correspondence only', 'designLinksConsistent':True,'originalTriggerIdentities':len(seen),'handlerReferences':counts,'nativeQualified':False,'installerReady':False,'missingNativeBindings':missing,'missingBindingCount':sum(map(len,missing.values()))},indent=2))
