import hashlib,json,re,zipfile
from pathlib import Path
root=Path('/Users/erik/Projects/truss');base=root/'docs/helix/04-build/evidence/design-audit/managed-grants-20261022';tmp=Path('/private/tmp/truss-managed-grants-qualification');wheel=tmp/'dist-final-3/truss_toolkit-0.0.48-py3-none-any.whl'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((base/p).read_bytes())
selected=read('attempt-4/selected-components/qualification.json');remaining=read('attempt-5/qualification.json');hf=read('attempt-5/hf-corpus/qualification.json');migration=read('attempt-5/migrations/qualification.json');work=read('attempt-5/public-workload/report.json');supp=read('supplemental/final-3/managed_grants_lifecycle_installed.json');capture=read('runtime-migration-captures/receipt.json');payload=read('build/payload-verification-final-3.json') if (base/'build/payload-verification-final-3.json').exists() else json.loads((tmp/'dist-final-3/payload-verification.json').read_bytes())
expected='7a41a223033c1af0da4a2df2d377c672fcd3b3be1fcfc5b5bf8232d009725ed4';native='35fd797b5cf48dd888c68e53b9e599df20cffe00f8f3d33e1563820ea808d59f'
assert h(wheel)==expected==selected['wheelSha256']==remaining['wheelSha256']==payload['wheelSha256']
assert selected['passed'] and selected['tests']==116 and len(selected['outcomes'])==19 and selected['workerStopped'] and selected['workerBaselineRestored'] and selected['inputsUnchanged']
assert all(r['passed'] and r['baselineRestored'] for r in selected['outcomes'])
assert remaining['passed'] and remaining['inputBasisUnchanged'] and all(r['returncode']==0 for r in remaining['steps'])
assert hf['passed'] and hf['tests']==61 and hf['skipped']==0 and hf['nativeManifestSha256']==native
protected=(base/'attempt-5/protected-regression.log').read_text();assert 'Ran 9 tests' in protected and re.search(r'\nOK\s*$',protected)
assert migration['passed'] and migration['tests']==80 and migration['skipped']==0 and migration['targetManifestSha256']==native and len(migration['sources'])==3
assert work['passed'] and work['functionalPassed'] and work['runtimeManifestSha256']==native and work['runtimePackage']['mode']=='installed' and work['sqlSubmissionCounts']['enabled']
assert len(work['cases'])==1;case=work['cases'][0];assert case['status']=='passed' and case['loaded']==1000 and case['createdEdges']==1000 and case['readSamples']==1000 and case['committedUpdates']==200 and case['reopenedValuesVerified']
assert supp['provenance']['wheelSha256']==expected and supp['provenance']['managedTargetSha256']==native
assert all(supp['cleanup'].values())
assert supp['checks']['supported_additive_evolution']['historicalSourceAndObjectPreserved'] and supp['checks']['supported_additive_evolution']['managedCarrierPreserved']
variation=supp['checks']['selected_acl_variation'];assert variation['aclRestored'] and variation['addAndRemoveAcceptedByStatus'] and variation['policyCarrierUnchanged']
retirement=supp['retirement'];assert retirement['nativeAttempt']['sqlstate']=='0A000' and retirement['nativeAttempt']['message']=='record retirement requires explicit support' and all(retirement[k] for k in ['managedCarrierPreserved','objectAndJournalPreserved','selectedAclPreserved','sourceHistoryPreserved'])
for row in capture['preservedBaselineArtifacts']['files']:assert h(root/'packages/python/src/truss/_migrations'/row['path'])==row['sha256']
assert capture['preservedBaselineArtifacts']['count']==15
with zipfile.ZipFile(wheel) as z:
 paths=[n for n in z.namelist() if n.startswith('truss/') and not n.endswith('/')];assert len(paths)==459
 for n in paths:assert z.read(n)==(root/'packages/python/src'/n).read_bytes()
 assert hashlib.sha256(z.read('truss/_catalog_runtime/manifest.json')).hexdigest()==native
profile=root/'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json';assert h(profile)=='0945348e235fbcdd29cf499bd02457c4d618017582d34d83bf28d69d7854c859'
for n,digest in json.loads(profile.read_bytes())['producers'].items():assert h(root/n)==digest
archive=base/'hf61/final-cli-migration-35fd.zip';assert h(archive)=='4be0ed4a0ad6f781cc160325caaf24f15d19fd365663a3e6f9ff7d920baf5ce6'
refs=['attempt-4/selected-components/qualification.json','attempt-4/boundaries.log','attempt-4/boundary-controls.log','attempt-5/qualification.json','attempt-5/hf-corpus/qualification.json','attempt-5/protected-regression.log','attempt-5/migrations/qualification.json','attempt-5/public-workload/report.json','supplemental/final-3/managed_grants_lifecycle_installed.json','runtime-migration-captures/receipt.json','managed-grants-model.json','build/final-3-environment.json','build/final-2-to-final-3-payload.json','attempt-1/qualification.json','attempt-1/installed-suite/installed-suite.json','attempt-4/hf-corpus.log']
record={'scope':'Bounded local macOS ARM64 qualification of the managed-grants change; explicit selected components and original workload only','boundedLocalGatesPassed':True,'completeReleaseQualified':False,'legacyFullSuiteQualified':False,'hostedLinux':'not_run','lakebaseAcceptance':'not_run','ArrasAdoption':'separate_gate','published':False,'wheelSha256':expected,'sdistSha256':payload['sdistSha256'],'nativeManifestSha256':native,'packageFilesVerified':459,'selectedModules':19,'selectedTests':116,'hfCases':61,'protectedTests':9,'migrationTests':80,'migrationSources':3,'skipsInPositiveTestGates':0,'publicWorkload':{'objects':1000,'edges':1000,'readSamples':1000,'committedUpdates':200,'reopenedValuesVerified':True,'sqlSubmissions':case['driverSqlSubmissions']['total'],'performanceScope':'Measured local observations with counter overhead; no general latency budget or capacity maximum claim'},'managedLifecycleSupplement':'passed on exact final wheel; unsupported retirement refuses with contained no-effects behavior','historicalMigrationFilesPreserved':15,'priorFailures':'Retained original observations; not relabelled as passes. Legacy broad suite remains incomplete/unqualified.','receipts':{n:h(base/n) for n in refs},'producerSha256':h(Path(__file__))}
with (base/'local-qualification.json').open('x') as f:f.write(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='receipts'}))
