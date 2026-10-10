"""Fault-injected manifests: verify scoped audit refuses stale/misdirected evidence."""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

base = Path('docs/helix/04-build/evidence/design-audit')
manifest = json.loads(Path('docs/helix/02-design/models/truss-relationship-lineage-candidate.physical-ids.draft.json').read_text())
cases = []
def add(name, change):
    value = copy.deepcopy(manifest)
    change(value)
    cases.append((name, value))
add('stale-source', lambda x: x.update(sourceSha256='0' * 64))
add('stale-model', lambda x: x.update(modelSha256='0' * 64))
add('duplicate-label', lambda x: x['entries'][1].update(id=x['entries'][0]['id']))
add('wrong-column-name', lambda x: x['entries'][1].update(nativeName='identity_profile'))
add('fabricated-emission-ordinal', lambda x: x['entries'][0]['capturedModelLocator'].update(generatedStatementOrdinal=0))
add('wrong-primary-index-basis', lambda x: x['entries'][12]['capturedModelLocator'].update(jsonPointer=x['entries'][7]['capturedModelLocator']['jsonPointer']))
add('overclaimed-completeness', lambda x: x.update(complete=True))
add('wrong-attribute-parent', lambda x: x['entries'][13].update(parent=x['entries'][3]['id']))
add('wrong-attribute-node', lambda x: x['entries'][13]['capturedModelLocator'].update(jsonPointer=x['entries'][14]['capturedModelLocator']['jsonPointer']))
results = []
def require(condition, detail):
    if not condition:
        raise RuntimeError(detail)

with tempfile.TemporaryDirectory(prefix='truss-lineage-binding-controls-') as directory:
    for name, value in [('original', manifest), *cases]:
        path = Path(directory) / (name + '.json')
        path.write_text(json.dumps(value))
        expected_success = name == 'original'
        for mode, flags in [('normal', []), ('optimized', ['-O'])]:
            run = subprocess.run([sys.executable, *flags, str(base / 'check-relationship-lineage-bindings.py'), '--manifest', str(path), '--check-only'], capture_output=True, text=True)
            require((run.returncode == 0) == expected_success, (name, mode, run.stdout, run.stderr))
            if not expected_success:
                require('AuditRefusal' in run.stderr, (name, mode, 'failed outside intended audit refusal'))
            results.append({'case': name, 'mode': mode, 'expected': 'pass' if expected_success else 'refuse', 'observed': 'pass' if run.returncode == 0 else 'refuse'})
receipt = {'scope': 'One original plus nine fault-injected allocation manifests in normal and optimized Python; scoped audit behavior only, no native/exporter qualification', 'cases': results}
(base / 'relationship-lineage-binding-controls.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
