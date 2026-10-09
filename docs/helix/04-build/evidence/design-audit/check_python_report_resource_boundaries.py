"""Observed host boundary distinctions; not native or shared-account qualification."""
import base64
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile
from python_report_wire_candidate import ReportWireCandidate
from test_python_report_wire_candidate import candidate, wire, CONTRACTS
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
codec=ReportWireCandidate(CONTRACTS)
large_members=candidate()
large_members['documents']=[{'doc_id': 'doc'+str(i), 'doc_revision':'r1',
    'content_sha256':'a'*64, 'ord':str(i)} for i in range(4097)]
large_scalar=candidate();large_scalar['lifecycleProfile']['identity']='x'*65537
controls=[('per-container-members-not-yet-aligned',wire(large_members),True,False),
          ('host-codec-pass-does-not-admit-native-scalar-capacity',wire(large_scalar),True,True)]
packets=[{'name':name,'bytesBase64':base64.b64encode(source).decode()} for name,source,_,_ in controls]
with tempfile.TemporaryDirectory(prefix='truss-report-resources-') as temporary:
    path=Path(temporary)/'cases.json';path.write_text(json.dumps(packets))
    run=subprocess.run(['bun',str(HERE/'check-python-report-interchange.ts'),str(path),
                        '/Users/erik/Projects/umf/package.json'],cwd=ROOT,capture_output=True,text=True)
    if run.returncode:raise RuntimeError(run.stdout+run.stderr)
    ts=json.loads(run.stdout)['results']
results=[]
for (name,source,expected_python,expected_ts),observed in zip(controls,ts):
    try:codec.prepare(source);accepted=True
    except Exception:accepted=False
    if observed['name']!=name or accepted!=expected_python or observed['accepted']!=expected_ts:
        raise RuntimeError('Unexpected controlled boundary '+name)
    results.append({'name':name,'sourceBytes':len(source),'sourceSha256':sha256(source).hexdigest(),
                    'pythonAccepted':accepted,'typescriptAccepted':observed['accepted']})
if len(ts)!=len(controls):raise RuntimeError('Complete original case membership required')
files=[Path(__file__),HERE/'check-python-report-interchange.ts',HERE/'python_report_wire_candidate.py',
       HERE/'python_raw_json_candidate.py',ROOT/'packages/postgresql/src/acceptance-json.ts',
       ROOT/'packages/postgresql/src/canonical-wire-tree.ts',ROOT/'packages/postgresql/native/canonical-string-bytes.sql']
receipt={'status':'observed_expected_profile_gaps','results':results,
         'sourceSha256':{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in files},
         'scope':'Two intentionally distinct candidate resource outcomes. Synthetic shape-valid documents do not establish complete report semantics. Native scalar 65536-byte declaration inspected; no native invocation performed. Neither shared resource profile nor cross-host native support is qualified.'}
(HERE/'python-report-resource-boundaries.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('2 resource-boundary distinctions observed; shared profile remains unadopted')
