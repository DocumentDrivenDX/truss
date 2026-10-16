"""Conditional supplied-cut probe. No database or native admission evidence."""
import argparse,contextlib,hashlib,json,pathlib,subprocess
from truss._current_disclosure_wire import disclosure_fact_cut,frame_digest
from truss._current_disclosure_computation import open_current_disclosure_computation
from truss._current_disclosure_pipe import CurrentDisclosurePipe,VERSION
parser=argparse.ArgumentParser();parser.add_argument('umf_root',type=pathlib.Path);args=parser.parse_args()
root=pathlib.Path.cwd();fixture=root/'packages/python/tests/fixtures/current-disclosure/native-graph-capture.json'
corpus=json.loads(fixture.read_bytes());entry=args.umf_root/'tools/security/current-native-disclosure-child-main.ts'
observations=[]
for cohort,packets,omit in [('packaged-missing-graphs-control',corpus['packets'][:3],True),('current-source-parallel',corpus['packets'][3:6],False)]:
 for packet in packets:
  cut=dict(packet['cut']);arrays={k:json.dumps(cut.pop(k),separators=(',',':')).encode() for k in ('facts','coverage','graphs','graphCoverage')}
  if omit:arrays.update(graphs=b'[]',graphCoverage=b'[]')
  raw=disclosure_fact_cut(cut,facts=arrays['facts'],coverage=arrays['coverage'],graphs=arrays['graphs'],graph_coverage=arrays['graphCoverage'])
  initial=json.dumps(corpus['initialize'],separators=(',',':')).encode();receipt=frame_digest(initial)
  request=json.dumps({'version':VERSION,'kind':'evaluate-disclosure','requestId':'evaluate','sourceReceipt':receipt},separators=(',',':')).encode()[:-1]+b',"cut":'+raw+b'}'
  manager=(open_current_disclosure_computation(bun_executable='/opt/homebrew/bin/bun',timeout_seconds=20) if omit else CurrentDisclosurePipe(('/opt/homebrew/bin/bun',str(entry)),timeout_seconds=20))
  with manager as child:
   initialized=json.loads(child.exchange(initial,source_receipt=receipt));assert initialized['kind']=='initialized'
   response=json.loads(child.exchange(request,source_receipt=receipt));result=response['result']
   assert result['status']==('refused' if omit else 'rendered'),result
   if not omit:assert [r['key'][0]['string'] for r in result['resources']]==packet['expectedKeys']
  assert child._cleanup_complete
  observations.append({'cohort':cohort,'packet':packet['id'],'requestSha256':hashlib.sha256(request).hexdigest(),'response':response,'cleanupComplete':child._cleanup_complete})
def git(*arguments):return subprocess.check_output(('git','-C',str(args.umf_root),*arguments),text=True).strip()
print(json.dumps({'scope':'supplied-cut component only; no SQL, native admission, whole compiler/driver integration, or case promotion',
 'fixtureSha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'sourceRevision':git('rev-parse','HEAD'),
 'sourceTrackedStatus':git('status','--short','--untracked-files=no'),
 'sourceEntrySha256':hashlib.sha256(entry.read_bytes()).hexdigest(),
 'sourceRuntimeSha256':hashlib.sha256((args.umf_root/'src/extensions/security/catalog-runtime-candidate.ts').read_bytes()).hexdigest(),
 'packagedConsumerManifest':json.loads((root/'packages/python/src/truss/_current_disclosure_owner/consumer-manifest.json').read_bytes()),
 'observations':observations},indent=2))
