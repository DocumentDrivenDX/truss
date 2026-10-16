from pathlib import Path
import hashlib,json,subprocess,tarfile,io,sys,os,unittest
from types import SimpleNamespace
p=Path(__file__).resolve().parent;s=Path('/private/tmp/truss-native-graph-definition-review-20261016');H=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((s/'manifest.json').read_bytes());repo='/Users/erik/Projects/truss';base='586e1dec20332b18411c5fd7a28ecd743d9ee570'
for n,h in m.items():
 b=(s/n).read_bytes();assert H(b)==h,n;t=p/'packet'/n;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(b)
(p/'packet/manifest.json').write_bytes((s/'manifest.json').read_bytes());e=p/'packet/docs/helix/04-build/evidence/native-graph-definition-join-20261016';ret=json.loads((e/'retention.json').read_bytes())
for n,h in ret['sourceFiles'].items():assert H((p/'packet'/n).read_bytes())==h
for n,h in ret['files'].items():assert H((e/n).read_bytes())==h
pre=json.loads((e/'preflight.json').read_bytes());post=json.loads((e/'postflight.json').read_bytes());assert pre['sources']==post['sources'] and post['sourceEndpointsMatch'] and post['fixtureCleanup'] and not post['newFixtureRoots']
for n,h in pre['sources'].items():
 b=(p/'packet'/n).read_bytes() if (p/'packet'/n).exists() else subprocess.check_output(['git','-C',repo,'show',base+':'+n]);assert H(b)==h,n
work=p/'working';work.mkdir();tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','-C',repo,'archive',base,'packages/python/src','packages/python/tests','docs/helix/04-build/evidence/actual-graph-requirements-20261016']))).extractall(work)
for n in ret['sourceFiles']:(work/n).write_bytes((p/'packet'/n).read_bytes())
weft=Path('/private/tmp/truss-graph-requirements-final-weft-installed-20261016');native=next((weft/'weft').glob('*.so'));assert H(native.read_bytes())=='7e6384ddada0f67a45839a222ffb059e04a5de00f6a9281ad811eefacdeffa42'
os.environ['TRUSS_GRAPH_JOIN_WEFT_QUALIFICATION']='1';os.environ.pop('TRUSS_NATIVE_MODEL_JOIN_QUALIFICATION',None);sys.path[:0]=[str(work/'packages/python/src'),str(work/'packages/python/tests'),str(weft)]
with (p/'pure-tests.log').open('w') as log:
 result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(['test_native_graph_correspondence','test_native_model_correspondence']));assert result.wasSuccessful();counts={'discovered':result.testsRun,'skipped':len(result.skipped),'passed':result.testsRun-len(result.skipped)}
from truss._native_graph_correspondence import _join
from truss._native_model_correspondence import _join as model_join
ob=SimpleNamespace(accepted_request=(e/'accepted-request.json').read_bytes(),accepted_assessment=(e/'accepted-assessment.json').read_bytes(),runtime_release=(e/'runtime-release.json').read_bytes(),native_inventory=(e/'native-inventory.json').read_bytes());gr=(e/'graph-requirements.json').read_bytes();g=json.loads(gr);mq=(e/'model-requirements.json').read_bytes();mp=model_join(ob,mq,g['preparationSha256'],lambda:None);assert mp==(e/'model-report.json').read_bytes();model=SimpleNamespace(observation=ob,requirements=mq,report=mp);assert _join(model,gr,lambda:None)==(e/'graph-report.json').read_bytes();assert json.loads(ob.accepted_assessment)['version']=='truss.accepted-catalog-assessment/0.2-candidate'
report={'passed':True,'frozenFilesVerified':len(m),'selectedPrePostSourcePinsVerified':len(pre['sources']),'base':base,'pureTests':counts,'suppliedNativeModelAndGraphReportsReproducedByteExact':True,'actualAssessmentVersion':'truss.accepted-catalog-assessment/0.2-candidate','nativeModuleSha256':H(native.read_bytes()),'SQLExecuted':False};(p/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
