"""Damaged manifest controls only; no native routine or installed privilege qualification."""
from pathlib import Path
import copy, hashlib, json, shutil, subprocess, sys, tempfile
here=Path(__file__).resolve().parent
repo=here.parents[4]
root=repo/'docs/helix'
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):
 raise SystemExit('usage: check-routine-design-controls.py NEW_RECEIPT_BASENAME.json')
destination=here/sys.argv[1]
if destination.exists():raise SystemExit('refusing to replace existing receipt')
relative=Path('02-design/contracts/reference-routine-design-v0.1.proposal.json')
original=json.loads((root/relative).read_text())
checker=here/'link-routine-trigger-design.py'
paths={str(relative),str(checker.relative_to(root))}
paths.update(x['path'] for x in original['governingSources'])
for routine in original['routines']:
 for reference in routine['originalTriggerReferences']:
  paths.add(reference['catalogPath'])
  paths.add(str((repo/reference['originalModelLocator']['modelPath']).relative_to(root)))
results=[]
with tempfile.TemporaryDirectory(prefix='truss-routine-design-') as temporary:
 candidate=Path(temporary)/'repo/docs/helix'
 for path in paths:
  target=candidate/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/path,target)
 for control in ['original','wrong attribute','wrong signature','wrong owner','missing dependency','governing pin substitution','duplicate routine','false qualification']:
  data=copy.deepcopy(original)
  if control=='wrong attribute':data['sharedSelectedAttributes']['volatility']='IMMUTABLE'
  elif control=='wrong signature':data['routines'][0]['sqlArgumentTypes']=['text']
  elif control=='wrong owner':data['routines'][0]['ownerResponsibility']='Application reader/writer'
  elif control=='missing dependency':data['routines'][1]['selectedValidatorDependencies']=[]
  elif control=='governing pin substitution':data['governingSources'][0]['sha256']='0'*64
  elif control=='duplicate routine':data['routines'][-1]=copy.deepcopy(data['routines'][0])
  elif control=='false qualification':data['nativeQualified']=True
  (candidate/relative).write_text(json.dumps(data))
  for optimized in [False,True]:
   run=subprocess.run([sys.executable,*(['-O'] if optimized else []),str(candidate/checker.relative_to(root)),'--check'],text=True,capture_output=True)
   passed=(run.returncode==0)==(control=='original')
   results.append({'control':control,'optimized':optimized,'passed':passed})
   if not passed:raise SystemExit(run.stdout+run.stderr)
receipt={'scope':'Selected design manifest/source correspondence and seven corruption refusals only; no native bodies, privileges, effects or support qualification','checkerSha256':hashlib.sha256(checker.read_bytes()).hexdigest(),'manifestSha256':hashlib.sha256((root/relative).read_bytes()).hexdigest(),'controls':len(results),'failures':[r for r in results if not r['passed']],'results':results}
with destination.open('x') as output:output.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['scope','controls','failures']},indent=2))
