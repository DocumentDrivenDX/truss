"""Existing column/source definition correspondence; no native semantic inference."""
from pathlib import Path
import hashlib
import json
root = Path(__file__).resolve().parents[5]
def load(path):
    return json.loads((root / path).read_text())
def digest(path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()
base_path = 'docs/helix/02-design/models/truss-layout-0.2.physical-ids.draft.json'
profile_path = 'docs/helix/02-design/models/truss-layout-0.2.column-semantics.draft.json'
model_path = 'docs/helix/02-design/models/truss-layout-0.2.umf.json'
base, profile, model = load(base_path), load(profile_path), load(model_path)
tables = {e['capturedModelLocator']['jsonPointer']: e['entryId'] for e in base['entries'] if e['objectKind'] == 'table'}
columns = {e['entryId']: e for e in base['entries'] if e['objectKind'] == 'column'}
if profile['complete'] is not False or profile['sourceSha256'] != digest('docs/helix/02-design/contracts/storage-layout.sql'):
    raise ValueError('stale source or false completeness')
seen = set()
for entry in profile['columns']:
    identity = entry['columnId']
    if identity in seen or identity not in columns:
        raise ValueError('duplicate or unknown column')
    seen.add(identity)
    original = columns[identity]
    locator = entry['capturedModelLocator']
    if locator != original['capturedModelLocator'] or locator['modelSha256'] != digest(model_path) or entry['nativeIdentity'] != original['nativeIdentity']:
        raise ValueError('column source/identity mismatch')
    pointer = locator['jsonPointer']
    if entry['parentId'] != tables.get(pointer.split('/members/tableElts/')[0]):
        raise ValueError('wrong column owner')
    node = model
    for part in pointer.lstrip('/').split('/'):
        key = part.replace('~1', '/').replace('~0', '~')
        node = node[int(key)] if isinstance(node, list) else node[key]
    if node != entry['originalNativeDefinition'] or sorted(node['members']) != entry['nativeFieldNames'] or entry['nativeBinding'] != {'state': 'unresolved'}:
        raise ValueError('incomplete/substituted source or premature native claim')
if seen != set(columns):
    raise ValueError('incomplete authored column inventory')
receipt = {'scope': 'Full original ColumnDef and existing authored column/table correspondence only; no resolved native type/default/nullability/collation or implicit dependencies', 'columns': len(seen), 'inputPins': [{'path': p, 'sha256': digest(p)} for p in [base_path, profile_path, model_path]], 'physicalCoverageComplete': False}
Path(__file__).with_name('column-source-semantics.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
