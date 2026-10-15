from pathlib import Path
import hashlib,json,shutil,subprocess,datetime
root=Path('/private/tmp/truss-security-main-integration');out=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parent=json.loads(Path('/private/tmp/truss-action-family-native-r8-source.json').read_bytes())
assert parent['exitCode']==0 and parent['sourceUnchanged'] and parent['sourceHashes']==parent['sourceHashesAfter']
for path,digest in parent['sourceHashes'].items():
    assert sha(root/path)==digest,path
    target=out/'sources'/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/path,target)
extra=['packages/python/src/truss/bulk_action_gateway.py','packages/python/src/truss/_action_identity_codec.py','packages/python/src/truss/_security_bootstrap/action-store-issuer.sql','packages/python/src/truss/_security_bootstrap/action-store-storage.sql','packages/python/src/truss/_security_bootstrap/action-subject-cut.sql','packages/python/src/truss/_catalog_runtime/migrations.sql']
pins=dict(parent['sourceHashes'])
for path in extra:
    pins[path]=sha(root/path)
    target=out/'sources'/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/path,target)
for name in ('truss-action-family-native-r8.log','truss-action-family-native-r8-source.json'):
    shutil.copyfile(Path('/private/tmp')/name,out/name)
for n in range(1,8):
    p=Path(f'/private/tmp/truss-action-family-native-r{n}.log')
    if p.exists():
        target=out/'historical'/p.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
assert 'Ran 6 tests in 105.380s' in (out/'truss-action-family-native-r8.log').read_text()
assert (out/'truss-action-family-native-r8.log').read_text().rstrip().endswith('OK')
checks=json.loads((out/'collector-results.json').read_bytes());custody=json.loads((out/'final-custody-results.json').read_bytes())
assert checks['count']==29 and checks['sourceSha256']==pins['packages/python/src/truss/_action_authority_observation.py']
assert custody['count']==32 and all(pins[p]==h for p,h in custody['sourceSha256'].items())
owner=Path('/Users/erik/.codex/worktrees/0ede/umf')
ownerpins={p:sha(owner/p) for p in ('native/postgresql/runtime.ts','src/adapters/postgresql/index.ts','src/model/document.ts','src/model/serialization.ts','package.json','bun.lock') if (owner/p).exists()}
(out/'source-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
(out/'owner-build-pins.json').write_text(json.dumps({'root':str(owner),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=owner,text=True).strip(),'clean':False,'sourceHashes':ownerpins,'parserVersion':'@libpg-query/parser@17.6.10','qualification':'Actual owner checkout replay, including working-tree sources; not a clean released-package or whole-toolchain provenance assertion.'},indent=2)+'\n')
report={
 'status':'review_complete_no_remaining_actionable_findings_within_stated_scope',
 'reviewer':'Independent Astra Ultra review requested by user',
 'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'repository':str(root),'baseHead':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
 'sourcePins':{'file':'source-pins.json','sha256':sha(out/'source-pins.json')},
 'fixedFindings':[
  {'issue':'Invalid current declaration/role rows could disappear behind INNER JOIN or validity WHERE filters.','resolution':'LEFT JOIN retains candidates; exact full-family row comparisons reject invalid, missing, duplicate or additional mappings.','evidence':'29 collector controls; source review; final native missing-role/extra-unresolved-role controls.'},
  {'issue':'Caller-owned mutable store fields could alias PendingActionRoles; validating before capture allowed slot substitution.','resolution':'All eight slots captured once; five exact immutable bounded byte carriers and exact labels validated only on private copy; malformed receipt exceptions normalized.','evidence':'Retained pre-fix actual-installer synthetic alias witness; final mutation/bytearray/memoryview/deep-receipt controls and supplied unit tests.'},
  {'issue':'Enrollment compared original store release to immutable genesis labels, allowing stale comparison after a current release overlay.','resolution':'Original runtime_current_installation() now supplies current release and digest.','evidence':'Source and native synthetic-ledger overlay countercontrol; explicitly not a genuine runtime upgrade test.'},
  {'issue':'pg_xact_status imposed undocumented recent-transaction lifetime on immutable stores.','resolution':'Visible distinct top-level issuer under exact native18.6/RC/read-write/no-SET-ROLE and original immutable issuance; actual same-issuer pending context refuses.','evidence':'Source/native test review; official PG18 documentation confirms aged-out pg_xact_status returns NULL.','source':'https://www.postgresql.org/docs/18/functions-info.html'}
 ],
 'independentChecks':{'collectorFiniteControls':29,'captureAndComparisonControls':29,'originalOwnerGeneratedArtifactByteComparisons':3,'suppliedUnitTests':2,'results':['collector-results.json','final-custody-results.json','context-unit-final.log','build.log'],'nativeLifecycleRerun':False},
 'parentNativeEvidence':{'file':'truss-action-family-native-r8.log','sha256':sha(out/'truss-action-family-native-r8.log'),'tests':6,'unittestSeconds':105.380,'composition':'Four native component test methods plus two pure context methods. Parent run inspected, not reviewer-run.','sourceManifest':'truss-action-family-native-r8-source.json','manifestSha256':sha(out/'truss-action-family-native-r8-source.json'),'all16SourcePinsMatch':True},
 'sourceReview':['Complete exact artifact/ordered role retention, parent/store correspondence, byte equality rather than digest identity, and missing-role refusal before OR observation.','Store → declaration → Subject → role mapping → native role catalog lock ordering; existing RR visibility caveat retained.','4MiB retained-artifact/mapping ledger includes repeated store identity; original storage byte correspondence and module-specific added imports reviewed.','Exact source pins, hostile namespace restoration, owner-only homes/allocators and direct trusted quiescent enrollment premises retained.'],
 'limits':['Finite synthetic controls establish Python boundary behavior only, not SQL/native refinement or authentication.','No arbitrary administrative mutation, later migration, complete source/helper/ACL/role lifecycle closure, native guard/program/permit/seal or production caller grants qualified.','Retained payload and row bounds do not bound total native scan, libpq heap, parser allocation or all CPU.','Original owner/driver/admin/source code are trusted configuration premises. No original required backend case is promoted; all132 remain in scope.','Historical r1-r7 evidence is retained separately and does not qualify final-source r8 by inheritance.','Initial local final-custody harness ran while the native context gate was being added and failed its synthetic positive setup; final harness supplies that gate explicitly. This was a test-double mismatch, not native product evidence.']
}
(out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'review':str(out/'review.json'),'sha256':sha(out/'review.json'),'sourcePins':str(out/'source-pins.json'),'independentControls':61,'unitTests':2,'native':'parent6/105.380s'}))
