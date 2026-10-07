"""Native AST observations only; no SQL parser, authored IDs or native binding."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
root = Path(__file__).resolve().parents[5]
model_path = 'docs/helix/02-design/models/truss-layout-0.2.umf.json'
raw = (root / model_path).read_bytes()
model = json.loads(raw)
prefix = '/modules/0/elements/0/extensions/umf.postgresql/root'
tree = model['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root']
rows = []
catalog_kinds = {'CONSTR_PRIMARY', 'CONSTR_UNIQUE', 'CONSTR_EXCLUSION', 'CONSTR_FOREIGN', 'CONSTR_CHECK'}
column_kinds = {'CONSTR_NULL', 'CONSTR_NOTNULL', 'CONSTR_DEFAULT', 'CONSTR_IDENTITY', 'CONSTR_GENERATED', 'CONSTR_ATTR_DEFERRABLE', 'CONSTR_ATTR_NOT_DEFERRABLE', 'CONSTR_ATTR_DEFERRED', 'CONSTR_ATTR_IMMEDIATE'}
def walk(node, path):
    if isinstance(node, dict):
        if node.get('kind') == 'object' and 'Constraint' in node.get('members', {}):
            constraint = node['members']['Constraint']
            kind = constraint['members']['contype']['value']
            match = re.search(r'/members/stmts/items/([0-9]+)/', path)
            if not match:
                raise ValueError('constraint without original statement')
            classification = 'catalog-constraint-candidate' if kind in catalog_kinds else 'column-or-constraint-attribute' if kind in column_kinds else 'uninterpreted'
            rows.append({'sourcePath': path + '/members/Constraint', 'statementOrdinal': match.group(1), 'nativeKind': kind, 'classification': classification, 'originalNativeNode': constraint})
        for key, value in node.items():
            walk(value, path + '/' + key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            walk(value, path + '/' + str(i))
walk(tree, prefix)
if (root / model_path).read_bytes() != raw or not rows:
    raise ValueError('source changed or no constraints observed')
receipt = {'scope': 'Complete traversal of Constraint-tagged nodes in this exact captured native tree only; not complete physical effect inventory, authored identity allocation or native catalog qualification', 'modelPath': model_path, 'modelSha256': hashlib.sha256(raw).hexdigest(), 'observedNodes': len(rows), 'nativeKindCounts': dict(sorted(Counter(r['nativeKind'] for r in rows).items())), 'uninterpretedKinds': sorted({r['nativeKind'] for r in rows if r['classification'] == 'uninterpreted'}), 'physicalCoverageComplete': False, 'observations': rows}
Path(__file__).with_name('baseline-constraint-source.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ['observedNodes', 'nativeKindCounts', 'uninterpretedKinds', 'physicalCoverageComplete']}, indent=2))
