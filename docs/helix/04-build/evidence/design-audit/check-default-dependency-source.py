"""Source function references in exact defaults; no native dependency resolver."""
from pathlib import Path
from collections import Counter
import hashlib
import json
root = Path(__file__).resolve().parents[5]
paths = ['docs/helix/04-build/evidence/design-audit/baseline-constraint-source.json',
         'docs/helix/02-design/models/truss-layout-0.2.column-semantics.draft.json',
         'docs/helix/02-design/models/truss-layout-0.2.umf.json']
raw = [(root / p).read_bytes() for p in paths]
observed, columns, model = [json.loads(b) for b in raw]
model_hash = hashlib.sha256(raw[2]).hexdigest()
if observed['modelSha256'] != model_hash:
    raise ValueError('stale native observations')
column_by_path = {e['capturedModelLocator']['jsonPointer']: e for e in columns['columns']}
def calls(node, path):
    if isinstance(node, dict):
        if node.get('kind') == 'object' and 'FuncCall' in node.get('members', {}):
            function = node['members']['FuncCall']
            names = function['members']['funcname']['items']
            yield {'sourcePath': path + '/members/FuncCall', 'nameComponents': [n['members']['String']['members']['sval']['value'] for n in names], 'originalNativeCall': function, 'nativeBinding': {'state': 'unresolved'}}
        for key, value in node.items():
            yield from calls(value, path + '/' + key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from calls(value, path + '/' + str(i))
defaults = []
for row in observed['observations']:
    if row['nativeKind'] != 'CONSTR_DEFAULT':
        continue
    column = column_by_path[row['sourcePath'].split('/members/constraints/')[0]]
    if column['capturedModelLocator']['modelSha256'] != model_hash:
        raise ValueError('stale column binding')
    node = model
    for part in row['sourcePath'].strip('/').split('/'):
        node = node[int(part)] if isinstance(node, list) else node[part]
    if node != row['originalNativeNode']:
        raise ValueError('default source substitution')
    defaults.append({'columnId': column['columnId'], 'parentId': column['parentId'], 'sourcePath': row['sourcePath'], 'originalDefaultNode': node, 'functionReferences': list(calls(node, row['sourcePath']))})
for p, b in zip(paths, raw):
    if (root / p).read_bytes() != b:
        raise ValueError('source changed during observation')
counts = Counter('.'.join(f['nameComponents']) for d in defaults for f in d['functionReferences'])
receipt = {'scope': 'Exact source default/function-reference/column ownership only; casts, overloads, regclass sequence references, function semantics/authority and all native dependencies remain unresolved', 'inputPins': [{'path': p, 'sha256': hashlib.sha256(b).hexdigest()} for p, b in zip(paths, raw)], 'defaultCount': len(defaults), 'functionReferenceCounts': dict(sorted(counts.items())), 'physicalCoverageComplete': False, 'defaults': defaults}
Path(__file__).with_name('default-dependency-source.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ['defaultCount', 'functionReferenceCounts', 'physicalCoverageComplete']}, indent=2))
