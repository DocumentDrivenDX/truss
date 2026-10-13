from pathlib import Path
import json,hashlib,subprocess,shutil
root=Path('/private/tmp/truss-security-main-integration');out=Path(__file__).parent;ev=root/'docs/helix/04-build/evidence/accepted-catalog-fact-guard-20261013';dest=ev/'independent-review'
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
parent=json.loads((ev/'receipt.json').read_bytes());guard=json.loads((out/'guard-results.json').read_bytes());legacy=json.loads((out/'results.json').read_bytes());formal=out/'formal-replica/docs/helix/04-build/evidence/accepted-catalog-fact-guard-20261013/formal';proof=json.loads((formal/'receipt.json').read_bytes())
for r in (guard,legacy):
 for name in ('sourcePins','nativePacketPins','inputPins'):
  for p in r.get(name,[]):assert pin(Path(p['path']))['sha256']==p['sha256'],p['path']
assert guard['count']==49 and legacy['count']==39 and all(c['passed'] for r in (guard,legacy) for c in r['controls'])
for name,digest in parent['sourceDigests'].items():assert pin(root/name)['sha256']==digest,name
assert (formal/'receipt.json').read_bytes()==(ev/'formal/receipt.json').read_bytes()
for p in formal.glob('*.smt2'):assert p.read_bytes()==(ev/'formal'/p.name).read_bytes()
assert [q['observed'] for q in proof['queries']]==['unsat','unsat','sat','sat']
assert parent['nativeGuardSeconds']==19.285 and 'Ran 3 tests in 19.285s' in (ev/'native.log').read_text() and (ev/'native.log').read_text().rstrip().endswith('OK')
assert 'Ran 3 tests in 4.199s' in (ev/'epoch-regression.log').read_text() and (ev/'epoch-regression.log').read_text().rstrip().endswith('OK')
assert "caught.exception.diag.message_primary,'selected authorization fact cut excludes same-backend writes'" in (root/'packages/python/tests/test_security_catalog_guard_native.py').read_text()
assert pin(root/'packages/postgresql/native/authorization-fact-write-fence.sql')['sha256']==hashlib.sha256(subprocess.check_output(['git','show','HEAD:packages/postgresql/native/authorization-fact-write-fence.sql'],cwd=root)).hexdigest()
report={
 'status':'no-actionable-findings-within-reviewed-scope','reviewer':'Independent Astra Ultra review','date':'2026-10-13',
 'gitHead':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
 'scope':'Existing fact qualifier/recipe extraction and epoch routing, opt-in exact accepted object guard before source/fact capture, and same-backend fixture countercontrol. No implementation edits or native mutations by reviewer.','findings':[],
 'independentControls':{'guardAndExtraction':49,'legacyAcceptedCatalog':39,'allPassed':True,
  'extraction':'AST-identical validation, copied recipe and nested acquire body compared with original HEAD; original epoch/DDL delegation remains AST-identical.',
  'checks':'Prepared recipe captures original immutable scalar values. Invalid bindings and all twelve guard-field drifts refuse. Foreign relation/guard/column descriptors refuse before fetch. Selected object guard precedes host observation, native catalog capture, row capture and evaluator. Disabled guard refuses before capture. None retains legacy behavior.',
  'descriptorUnitTest':'Actual test_fact_cut_descriptor_boundary passed, covering three adverse stages.',
  'qualification':'Native rows and host/capture shells are synthetic. Selected and legacy paths execute genuine original UMF evaluation on retained actual capture rows. No independently executed native lock/trigger/host-containment assertion.'},
 'formalReplay':{'solver':proof['solver'],'queries':4,'unsat':2,'sat':2,'byteIdenticalToParent':True,
  'method':'Exact script and pinned source copies executed in owned replica; emitted SMT also replayed. Original repository proof outputs unchanged.',
  'scope':'Arbitrary-state one-step invariant over an unbounded fact array, conditional on continuously held conflicting cut, faithful atomic participating DML, installed before-effect guard, and fixed other policy inputs. Pure policy equality follows by congruence.',
  'limits':'No native/source/trigger/driver/savepoint refinement, complete effect inventory, hook lifetime or original evaluator implementation theorem.'},
 'parentNativeEvidenceInspected':{'guardTests':3,'guardSeconds':19.285,'epochRegressionTests':3,'epochRegressionSeconds':4.199,'postgresql':'18.6','runtime':'0.42',
  'countercontrol':'Original lock-only path changes active Assignment facts in its own backend after capture and still emits r1 from captured facts. This is uncommitted, not a successful commit or deferred-constraint claim.',
  'guarded':'All four INSERT/UPDATE/DELETE/TRUNCATE probes raise55000 with the exact original fact-guard primary message. Ten Records and original r1/Withheld output survive. Disabled guard refuses before evaluator with exact contained error and no cleanup error.',
  'cleanup':json.loads((ev/'cleanup.json').read_bytes()),'epochCleanup':json.loads((ev/'epoch-cleanup.json').read_bytes()),'notIndependentlyRerun':True},
 'reviewImprovement':'Added exact primary-message assertions to all four native write probes to distinguish this guard from unrelated55000 refusals; final native replay passes.',
 'limits':['New selected table cut does not add a source epoch or complete authority fence; original epoch composition remains separate.','Installed original guard lifetime, faithful atomic participating DML and continuously held cuts are premises.','Legacy None remains explicitly unqualified for same-backend exclusion.','No complete native home/DDL/role/ACL/handler/config/callable source lifetime or ABA closure, issuer authentication, protected admission or final release theorem.','Private administrative Subject fixture; separate two-host ordinary-caller route is not conflated with this counterexample.','No backend-case promotion or completion of all132 required cases.'],
 'sourcePins':[pin(root/n) for n in parent['sourceDigests']],
 'governedDocumentationPins':[pin(root/n) for n in ['docs/helix/02-design/contracts/CONTRACT-007-embedding-and-execution.md','docs/helix/03-test/test-plan.md','docs/helix/04-build/implementation-plan.md']],
 'parentEvidencePins':[pin(ev/n) for n in ['receipt.json','native.log','cleanup.json','epoch-regression.log','epoch-cleanup.json','formal/receipt.json']],
 'independentEvidencePins':[pin(out/n) for n in ['check.py','guard-results.json','legacy_check.py','results.json','fact-cut-pre-extraction.py','descriptor.log','retain_review.py']]+[pin(formal/'receipt.json')]
}
(out/'review.json').write_text(json.dumps(report,indent=2)+'\n');dest.mkdir(exist_ok=True)
for n in ('review.json','check.py','guard-results.json','legacy_check.py','results.json','fact-cut-pre-extraction.py','descriptor.log','retain_review.py'):shutil.copyfile(out/n,dest/n)
shutil.copytree(formal,dest/'formal-replay',dirs_exist_ok=True)
print(dest/'review.json')
