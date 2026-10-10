"""Verify current component evidence pins and enumerate unfilled native gates."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads((ROOT/path).read_bytes())
paths=['docs/helix/02-design/contracts/CONTRACT-001-storage-layout.md','docs/helix/02-design/contracts/reference-routine-design-v0.1.proposal.json','docs/helix/04-build/evidence/design-audit/row-image-visibility-native.json','docs/helix/04-build/evidence/design-audit/python-scalar-shape-installed-suite.json','docs/helix/04-build/row-finalization-native-execution-handoff.md']
original={p:(ROOT/p).read_bytes() for p in paths}
routines=read(paths[1]);native=read(paths[2]);wheel=read(paths[3])
if routines['nativeQualified'] or routines['installerReady']:raise ValueError('Unexpected readiness promotion requires full audit')
missing=[]
for routine in routines['routines']:
 fields=[key for key,value in routine['unresolvedNativeBinding'].items() if value is None]
 missing.append({'routine':routine['originalContractName'],'missingNativeFields':fields})
if len(missing)!=7 or sum(len(r['missingNativeFields']) for r in missing)!=49:raise ValueError('Native gate set changed; review new artifacts')
for path,expected in native['sourceSha256'].items():
 if sha((ROOT/path).read_bytes())!=expected:raise ValueError('Native source drift: '+path)
producer=HERE/'check_row_image_visibility_native.py'
if sha(producer.read_bytes())!=native['producerSha256']:raise ValueError('Native producer drift')
for module in wheel['modules']:
 if sha((ROOT/'packages/python/src'/module['path']).read_bytes())!=module['sha256']:raise ValueError('Wheel source drift: '+module['path'])
for path,expected in wheel['sourceTestSha256'].items():
 if sha((ROOT/path).read_bytes())!=expected:raise ValueError('Installed test drift: '+path)
if native['rowTouchObserverQualified'] or wheel['completeEngineQualified'] or wheel['installationQualified']:raise ValueError('Unexpected qualification promotion')
visible=[o for o in native['observations'] if o['id']=='native-rls-valid-prefix-is-not-complete-value']
if len(visible)!=1 or visible[0]['originalRows']!=8 or visible[0]['visibleRows']!=6 or not visible[0]['physicalTreePassed'] or visible[0]['completeScopeQualified']:raise ValueError('Visibility counterexample missing')
gates=[
 {'step':'RF01','status':'not_qualified','remaining':'Original authenticated subject, complete authority/cut/owner/property association and version'},
 {'step':'RF02','status':'counterexample_verified','remaining':'Original complete integrity visibility independent of caller RLS disclosure, complete owner/property selection and shared accounting'},
 {'step':'RF03','status':'physical_component_verified','remaining':'Protected native full-scope root/reachability/acyclicity with original custody and resource/depth bounds'},
 {'step':'RF04','status':'physical_component_only','remaining':'Original definition/member order, required fields, child types and full unknown-content correspondence'},
 {'step':'RF05','status':'carrier_shape_only','remaining':'Original numeric token/native value, full facets, temporal profile and admitted native codec correspondence'},
 {'step':'RF06','status':'not_qualified','remaining':'Bidirectional complete candidate/key/journal/report/group parity before seal'},
 {'step':'deferred_closure','status':'not_qualified','remaining':'Complete current transaction touch/contributor/application/reservation closure and selected edge/feed validators'},
 {'step':'settlement_publication','status':'not_qualified','remaining':'Qualified original connection/attempt, commit evidence, unknown-outcome reconciliation and publication drain'},
]
if any((ROOT/p).read_bytes()!=raw for p,raw in original.items()):raise ValueError('Audit input drift')
receipt={'scope':'Current checked-in evidence pin and remaining-native-gate audit; no test rerun or installed qualification','sourceSha256':{p:sha(raw) for p,raw in original.items()},'nativeObservations':len(native['observations']),'installedComponentTests':wheel['testsPassed'],'sourceModulesMatchingInstalledReceipt':len(wheel['modules']),'gates':gates,'missingRoutines':missing,'missingNativeFields':49,'completeEngineReady':False,'producerSha256':sha(Path(__file__).read_bytes())}
out=HERE/'row-finalization-readiness-audit.json'
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'native':len(native['observations']),'tests':wheel['testsPassed'],'modules':len(wheel['modules']),'missingNativeFields':49,'completeEngineReady':False}))
