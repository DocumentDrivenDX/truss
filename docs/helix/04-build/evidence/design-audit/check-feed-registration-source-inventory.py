"""Explicit feed runtime source families; no installable/native inventory claim."""
import copy,hashlib,json
from pathlib import Path
root=Path('docs/helix/04-build/evidence/design-audit')
def require(ok,msg):
 if not ok:raise ValueError(msg)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec={'feed-transaction-create':('InsertStmt',1),'feed-member-counter-reservation':('UpdateStmt',1),'feed-member-insert':('InsertStmt',1),'feed-prerequisite-counter-reservation':('UpdateStmt',2),'feed-prerequisite-insert':('InsertStmt',2)}
families=[];owner=None
for name,(kind,count) in spec.items():
 receipt_path=root/(name+'-source.json');receipt=json.loads(receipt_path.read_text());require(len(receipt['observations'])==1,'one original source observation');obs=receipt['observations'][0]
 if owner is None:owner=receipt['ownerSource']
 require(receipt['ownerSource']==owner,'same original UMF source tuple')
 require(obs['complete'] is False and obs['declarationCount']==0 and len(obs['unhandled'])==count,'original partial INSERT/UPDATE declaration scope')
 files=[]
 for field,hashfield in [('path','sourceSha256'),('artifactPath','artifactSha256'),('exportPath','exportSha256')]:
  require(sha(obs[field])==obs[hashfield],'original '+field);files.append({'path':obs[field],'sha256':obs[hashfield]})
 model=json.loads(Path(obs['artifactPath']).read_text());nodes=model['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root']['members']['stmts']['items'];require(len(nodes)==count and all(set(n['members']['stmt']['members'])=={kind} for n in nodes),'original statement kind/membership')
 families.append({'family':name,'statementKind':kind,'statementCount':count,'files':files,'captureReceipt':{'path':str(receipt_path),'sha256':sha(receipt_path)},'complete':False})
def verify(entries):
 require([e['family'] for e in entries]==list(spec),'complete ordered original families')
 require(len({f['path'] for e in entries for f in e['files']})==15,'distinct original source/model/export custody')
 for e in entries:
  kind,count=spec[e['family']];require(e['statementKind']==kind and e['statementCount']==count and e['complete'] is False,'independent family scope')
  require([f['path'] for f in e['files']]==['docs/helix/02-design/contracts/'+e['family']+'-v0.1.proposal.sql','docs/helix/02-design/contracts/'+e['family']+'-v0.1.proposal.umf.json','docs/helix/04-build/evidence/design-audit/'+e['family']+'.owner-export.sql'],'original family file paths')
  for f in e['files']:require(sha(f['path'])==f['sha256'],'original source file hash')
 require(sum(e['statementCount'] for e in entries)==7,'seven original registration statements')
verify(families);controls=[]
for label,mutate in [('omitted family',lambda x:x.pop()),('duplicate family',lambda x:x.append(copy.deepcopy(x[0]))),('invented complete claim',lambda x:x[0].update(complete=True)),('substituted source hash',lambda x:x[1]['files'][0].update(sha256='0'*64)),('narrower statement count',lambda x:x[0].update(statementCount=0))]:
 x=copy.deepcopy(families);mutate(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
r={'scope':'Five explicit private registration source families/seven statements; separate from eight lookup/finalization statements and installer. Family arrays are not a batch: select exactly the original route/statement ordinal and its statement-local bindings.','ownerSource':owner,'families':families,'controls':controls,'nativeExecution':False,'complete':False,'missingNativeOutputs':['complete original registration/comparison/guard native routine bodies and independent authority','complete helper/type/security/role/grant/dependency inventory','original codec/canonical/hash/clock/descriptor/accounting/termination producers','complete upstream required-effect and four-store event coverage','installation composition and independent native/bypass/state/resource qualification']}
(root/'feed-registration-source-inventory.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'families':5,'statements':7,'originalFilePins':15,'refusals':len(controls),'complete':False}))
