#!/usr/bin/env python3
"""Independent TLC verification and falsifiable controls; official tools supplied by host."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,tempfile
parser=argparse.ArgumentParser();parser.add_argument('--java',required=True);parser.add_argument('--jar',required=True);parser.add_argument('--python-receipt');args=parser.parse_args()
source=Path(__file__).resolve().parent;root=source.parents[4]
java=Path(args.java).resolve();jar=Path(args.jar).resolve();original=(source/'BulkUpdate.tla').read_text()
config=(source/'BulkUpdate.cfg').read_bytes();evidence=root/'docs/helix/04-build/evidence/bulk-update'
python_path=Path(args.python_receipt) if args.python_receipt else evidence/'batch-model-results.json'
python_original=python_path.read_bytes();python_report=json.loads(python_original)
python_source=(source/'check_model.py').read_bytes()
assert python_report.get('passed') is True and python_report['model'].get('safe') is True,'Python result not verified safe'
assert python_report['sourceSha256']==hashlib.sha256(python_source).hexdigest(),'Python receipt source differs'
def run(path):
 return subprocess.run([str(java),'-XX:+UseParallelGC','-Xmx768m','-cp',str(jar),'tlc2.TLC','-workers','1','-metadir',str(path/'states'),'-config','BulkUpdate.cfg','BulkUpdate.tla'],cwd=path,capture_output=True,text=True,timeout=120)
with tempfile.TemporaryDirectory(prefix='truss-tlc-final-') as directory:
 path=Path(directory);(path/'BulkUpdate.tla').write_text(original);(path/'BulkUpdate.cfg').write_bytes(config);result=run(path);log=result.stdout+result.stderr
 assert result.returncode==0 and 'No error has been found' in log,log[-2000:]
 (evidence/'tlc-model.log').write_text(log);banner=log.splitlines()[0]
 generated,distinct=map(int,re.search(r'(\d+) states generated, (\d+) distinct states found, 0 states left on queue',log).groups())
controls={
 'expired_admission':(' /\\ LiveClaim /\\ s.phase = "registered"',' /\\ s.phase = "registered"'),
 'partial_commit':(' /\\ Active /\\ ~s.restored /\\ \\A i \\in Batch(s.batch): s.staged[i] = 1',' /\\ Active /\\ ~s.restored'),
 'guard_race':(' /\\ ~Active /\\ s.versions[i] = 1',' /\\ s.versions[i] = 1'),
 'unconfirmed_marker':('!.phase = "marker_pending", !.marker_actual = "pending"','!.phase = "registered", !.marker_actual = "pending"')
}
results=[]
for name,(before,after) in controls.items():
 assert before in original,name;mutant=original.replace(before,after,1)
 with tempfile.TemporaryDirectory(prefix='truss-tlc-'+name+'-',dir=None) as directory:
  path=Path(directory);(path/'BulkUpdate.tla').write_text(mutant);(path/'BulkUpdate.cfg').write_bytes(config)
  result=run(path)
  log=result.stdout+result.stderr;assert 'is violated' in log and 'Invariant' in log,(name,log[-1500:])
  output=root/'docs/helix/04-build/evidence/bulk-update'/('tlc-negative-'+name+'.log');output.write_text(log)
  results.append({'id':name,'refused':True,'exitCode':result.returncode,'sourceSha256':hashlib.sha256(mutant.encode()).hexdigest(),'violation':[line for line in log.splitlines() if 'Invariant' in line and 'is violated' in line],'logSha256':hashlib.sha256(log.encode()).hexdigest()})
report={'scope':'Independent TLC mutations of bounded design model; no native proof','passed':True,'originalSha256':hashlib.sha256(original.encode()).hexdigest(),'results':results}
(root/'docs/helix/04-build/evidence/bulk-update/tlc-negative-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

assert (source/'BulkUpdate.tla').read_text()==original and (source/'BulkUpdate.cfg').read_bytes()==config,'Source changed during model run'
assert python_path.read_bytes()==python_original and (source/'check_model.py').read_bytes()==python_source,'Python source/receipt changed during model run'
assert python_report['model']['states']==distinct,'Python/TLA state correspondence changed'
receipt={'scope':'Two independent bounded design explorers; no native or liveness qualification','passed':True,'states':distinct,'generated':generated,'samePythonStateCount':True,
 'sourceSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [source/'check_model.py',source/'BulkUpdate.tla',source/'BulkUpdate.cfg',Path(__file__)]},
 'pythonReceiptSha256':hashlib.sha256(python_original).hexdigest(),'javaBinarySha256':hashlib.sha256(java.read_bytes()).hexdigest(),'tlcJarSha256':hashlib.sha256(jar.read_bytes()).hexdigest(),
 'tlcBanner':banner,'negativeControls':len(results)}
(evidence/'tlc-model-results.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
