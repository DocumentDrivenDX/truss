"""Audit independent successful selected-module observations without relabelling failures."""
import ast,gzip,hashlib,json,re,zipfile
from pathlib import Path
root=Path('/Users/erik/Projects/truss');base=root/'docs/helix/04-build/evidence/design-audit/managed-grants-20261022'
old=json.loads((base/'attempt-2/qualification.json').read_bytes());first=json.loads((base/'attempt-2/selected-components/qualification.json').read_bytes());last=json.loads((base/'attempt-2/selected-components/route-correction-qualification.json').read_bytes())
def digest(raw):return hashlib.sha256(raw).hexdigest()
assert first['wheelSha256']==last['wheel']['sha256']==old['wheelSha256']
assert first['workerStopped'] and first['workerBaselineRestored'] and first['inputsUnchanged'] and last['passed']
allowed={'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json','packages/python/tests/test_catalog_codes_native.py'}
changed=[]
for name,h in old['inputBasis'].items():
 p=Path(name) if Path(name).is_absolute() else root/name
 now=digest(p.read_bytes())
 if now!=h:
  assert name in allowed,name
  changed.append({'path':name,'priorSha256':h,'currentSha256':now})
assert {r['path'] for r in changed}==allowed
prior_archive=base/'hf61/hohfeld-followup-managed-grants-hf61-final-35fd.zip'
name='packages/python/tests/test_catalog_codes_native.py'
with zipfile.ZipFile(prior_archive) as z:prior=z.read(name)
assert digest(prior)==old['inputBasis'][name]
class StripTestBodies(ast.NodeTransformer):
 def visit_FunctionDef(self,node):
  if node.name.startswith('test_'):node.body=[ast.Pass()];return node
  return self.generic_visit(node)
def support(raw):return ast.dump(StripTestBodies().visit(ast.parse(raw)),include_attributes=False)
assert support(prior)==support((root/name).read_bytes()),'Supporting imports/helpers/setup changed'
kept=first['outcomes'][:14];assert all(r['passed'] for r in kept)
rows=[]
for row in kept:
 p=base/'attempt-2/selected-components'/row['log'];assert digest(p.read_bytes())==row['logSha256'];raw=gzip.decompress(p.read_bytes())
 assert re.search(rb'\nOK\s*$',raw) and f"Ran {row['tests']} test".encode() in raw
 assert 'test_catalog_codes_native' not in (root/'packages/python/tests'/row['module']).read_text()
 rows.append({'module':row['module'],'tests':row['tests'],'passed':True,'observation':str(p.relative_to(root)),'sha256':row['logSha256'],'baselineRestored':row['baselineRestored']})
for name,row in last['tests'].items():
 p=root/row['output'];raw=p.read_bytes();assert digest(raw)==row['outputSha256'] and row['passed'];assert re.search(rb'\nOK\s*$',raw) and f"Ran {row['count']} test".encode() in raw
 source='packages/python/tests/'+name+'.py';assert digest((root/source).read_bytes())==last['testSourceSha256BeforeAfter'][source]['after']
 rows.append({'module':name+'.py','tests':row['count'],'passed':True,'observation':row['output'],'sha256':row['outputSha256'],'cleanup':last['cleanup']})
assert len(rows)==17 and len({r['module'] for r in rows})==17 and {r['module'] for r in rows}==set(first['modules'])
for n,h in first['exactInstalledWheelSourcePayload'].items():assert digest((root/'packages/python/src'/n).read_bytes())==h
record={'scope':'17 explicitly selected modules successful across independent observations on one exact installed candidate2 wheel; not one fresh17-module run or fullsuite/release acceptance','passed':True,'modules':17,'tests':sum(r['tests'] for r in rows),'skips':0,'wheelSha256':old['wheelSha256'],'nativeManifestSha256':last['wheel']['nativeManifestSha256'],'sourcePayloadUnchanged':True,'priorInputChanges':changed,'supportingImportsHelpersSetupASTUnchanged':True,'reusedModulesDoNotImportChangedCodesTestModule':True,'first14PassedTests':sum(r['tests'] for r in kept),'remaining3PassedTests':last['totalTests'],'outcomes':rows,'originalFailedObservationPreserved':'attempt-2/selected-components/test_catalog_codes_native.log.gz','legacyFullSuite':'unresolved, not credited as passing; attempt-1 retained','producerSha256':digest(Path(__file__).read_bytes())}
(base/'selected-regression-aggregate.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k not in ('outcomes','priorInputChanges')}))
