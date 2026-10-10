"""Original hand-authored byte/hash checks, not a canonical encoder."""
import hashlib,json
from pathlib import Path
p=Path('docs/helix/02-design/contracts/bindings/feed-manifest-canonical.proposal.vectors.json');d=json.loads(p.read_text())
def require(ok,msg):
 if not ok:raise ValueError(msg)
checks=[]
for v in d['vectors']:
 raw=bytes.fromhex(v['canonicalUtf8Hex']);require(raw==v['canonicalToken'].encode(),'original bytes');require(len(raw)==int(v['canonicalByteLength']),'original length')
 tree=json.loads(raw);require(tree['xid']=='9007199254740993' and 'manifestSha256' not in tree,'exact text and self exclusion');require(tree['prerequisites'][0]['artifact']['bytesBase64']=='AP8=','opaque original carrier')
 domain='truss-feed-manifest/'+tree['interfaceVersion'].split('/')[-1];require(v['domain']==domain,'version domain')
 pre=(d['profile']+'\n'+domain+'\n').encode()+raw;require(pre==bytes.fromhex(v['framedPreimageHex']),'original frame');h=hashlib.sha256(pre).hexdigest();require(h==v['manifestSha256'],'manifest hash');require(hashlib.sha256(raw).hexdigest()==v['directTreeSha256'] and v['directTreeSha256']!=h,'distinct direct hash')
 full=bytes.fromhex(v['completeWireUtf8Hex']);require(full==v['completeWireCanonicalToken'].encode() and len(full)==int(v['completeWireByteLength']),'complete wire bytes/length')
 complete_tree=json.loads(full);require(complete_tree.pop('manifestSha256')==h and complete_tree==tree,'complete envelope semantic correspondence')
 require(v['completeWireCanonicalToken']==v['canonicalToken'].replace(',"members":',',"manifestSha256":"'+h+'","members":',1),'independent exact digest placement')
 require(hashlib.sha256(full).hexdigest()==v['completeWireArtifactSha256'] and v['completeWireArtifactSha256'] not in [h,v['directTreeSha256']],'complete artifact hash distinction')
 require(v['archiveProfile']=='truss-feed-manifest-artifact/'+tree['interfaceVersion'].split('/')[-1],'archive profile version')
 other='truss-feed-manifest/'+('0.2.0' if domain.endswith('0.1.0') else '0.1.0')
 controls={'wrong-domain':(d['profile']+'\n'+other+'\n').encode()+raw,'suffix-LF':pre+b'\n','prefix-BOM':b'\xef\xbb\xbf'+pre,'unframed':raw}
 for name,changed in controls.items():require(hashlib.sha256(changed).hexdigest()!=h,'changed preimage '+name)
 if v['id']=='MF-0.2.0-configuration-transition':
  require(tree['members'][0]['key']=={'installationId':'installation-1','kind':'key_profile_transition','migrationAttemptId':'attempt-1','sourceEpoch':'epoch-1'},'independent transition identity')
  config=tree['configurationPrerequisites'][0]['configuration'];require(config['generation']=='7' and config['journalMode']=='trigger' and config['keyReuse']=='forbid','independent configuration values')
 if v['id']=='MF-0.2.0-transition-revision-order':
  require([(m['key']['kind'],m['ordinal']) for m in tree['members']]==[('key_profile_transition','0'),('revision','1')],'independent mixed member order')
  require(tree['members'][1]['key']['revision']=='1' and tree['members'][1]['payloadSha256']=='4'*64,'independent revision payload pin')
 checks.append({'id':v['id'],'originalByteHashAgreement':True,'changedPreimageControls':list(controls)})
receipt={'scope':d['scope'],'vectorsSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'checks':checks,'productionEncoderExecuted':False,'nativeExecution':False,'complete':False}
Path('docs/helix/04-build/evidence/design-audit/feed-manifest-vectors.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'vectors':len(checks),'changedPreimages':sum(len(c['changedPreimageControls']) for c in checks),'nativeExecution':False}))
