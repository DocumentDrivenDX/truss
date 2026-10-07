"""Authored source/statement mapping only; not complete physical/native coverage."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[5]
def load(path):
    return json.loads((root / path).read_text())
def digest(path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()
model_path = 'docs/helix/02-design/models/truss-layout-0.2.umf.json'
model = load(model_path)
model_hash = digest(model_path)
source_hash = digest('docs/helix/02-design/contracts/storage-layout.sql')
composition_path = 'docs/helix/04-build/evidence/design-audit/bootstrap-statement-composition.json'
composition = load(composition_path)
if composition['modelSha256'] != model_hash:
    raise ValueError('stale statement composition')
statements = composition['statements']
if [s['ordinal'] for s in statements] != [str(i) for i in range(len(statements))]:
    raise ValueError('noncontiguous statement inventory')
for statement in statements:
    if hashlib.sha256(statement['sql'].encode()).hexdigest() != statement['sha256']:
        raise ValueError('statement byte/hash mismatch')
joins = composition['joins']
if len(joins) != len(statements) + 1:
    raise ValueError('incomplete composition joins')
composed = joins[0] + ''.join(s['sql'] + joins[i + 1] for i, s in enumerate(statements))
if hashlib.sha256(composed.encode()).hexdigest() != composition['joinedSqlSha256']:
    raise ValueError('composition hash mismatch')
seen = set()
table_sources = {}
constraint_paths = set()
constraint_entries = {}
index_creators = set()
mapped = {s['ordinal']: [] for s in statements}
inputs = ['docs/helix/02-design/models/truss-layout-0.2.physical-ids.draft.json',
          'docs/helix/02-design/models/truss-layout-0.2.initialization-ids.draft.json',
          'docs/helix/02-design/models/truss-layout-0.2.constraint-ids.draft.json',
          'docs/helix/02-design/models/truss-layout-0.2.supporting-index-ids.draft.json']
for path in inputs:
    allocation = load(path)
    if allocation['sourceSha256'] != source_hash or allocation['complete'] is not False:
        raise ValueError('stale source or unsupported completeness claim')
    for entry in allocation['entries']:
        identity = entry['entryId']
        if identity in seen:
            raise ValueError('duplicate authored identity')
        seen.add(identity)
        locator = entry['capturedModelLocator']
        ordinal = locator['statementIndex']
        if locator['modelPath'] != model_path or locator['modelSha256'] != model_hash or ordinal not in mapped:
            raise ValueError('stale model or unknown statement')
        pointer = locator['jsonPointer']
        if '/stmts/items/' + ordinal + '/members/stmt/' not in pointer:
            raise ValueError('pointer/statement mismatch')
        node = model
        for component in pointer.lstrip('/').split('/'):
            key = component.replace('~1', '/').replace('~0', '~')
            node = node[int(key)] if isinstance(node, list) else node[key]
        if not isinstance(node, dict):
            raise ValueError('expected exact native node')
        if entry['objectKind'] == 'table':
            table_sources[pointer] = identity
        if entry['objectKind'] == 'constraint':
            parent = pointer.split('/members/tableElts/')[0]
            if entry['parentId'] != table_sources.get(parent):
                raise ValueError('constraint parent ownership mismatch')
            if node != entry['originalNativeNode'] or node['members']['contype']['value'] != entry['nativeKind']:
                raise ValueError('constraint native node/kind mismatch')
            if entry['nativeBinding'] != {'state': 'unresolved'} or pointer in constraint_paths:
                raise ValueError('unsupported native binding or duplicate constraint source')
            constraint_paths.add(pointer)
            constraint_entries[identity] = entry
        if entry['objectKind'] == 'supporting-index':
            creator = constraint_entries.get(entry['creatingConstraintId'])
            if not creator or creator['nativeKind'] not in {'CONSTR_PRIMARY', 'CONSTR_UNIQUE'}:
                raise ValueError('missing or invalid supporting index creator')
            if creator['entryId'] in index_creators or entry['parentId'] != creator['parentId'] or locator != creator['capturedModelLocator']:
                raise ValueError('duplicate creator or wrong index source/parent')
            if entry['nativeBinding'] != {'state': 'unresolved'}:
                raise ValueError('unqualified index binding claim')
            index_creators.add(creator['entryId'])
        mapped[ordinal].append({'physicalIdentity': identity, 'objectKind': entry['objectKind'], 'capturedSourcePath': pointer, 'statementSqlSha256': statements[int(ordinal)]['sha256']})
observed = load('docs/helix/04-build/evidence/design-audit/baseline-constraint-source.json')
if observed['modelSha256'] != model_hash:
    raise ValueError('stale constraint source observation')
expected_constraint_paths = {r['sourcePath'] for r in observed['observations'] if r['classification'] == 'catalog-constraint-candidate'}
if constraint_paths != expected_constraint_paths:
    raise ValueError('missing or extra catalog-constraint source allocation')
if index_creators != {identity for identity, e in constraint_entries.items() if e['nativeKind'] in {'CONSTR_PRIMARY', 'CONSTR_UNIQUE'}}:
    raise ValueError('incomplete supporting index creator closure')
receipt = {'scope': 'Authored native source-node to guarded statement-export mapping; no complete physical-effect inventory or native qualification', 'modelSha256': model_hash, 'sourceSha256': source_hash, 'inputPins': [{'path': p, 'sha256': digest(p)} for p in inputs + [composition_path]], 'authoredEntries': len(seen), 'statements': len(statements), 'unmappedStatements': [k for k, v in mapped.items() if not v], 'physicalCoverageComplete': False, 'mapping': mapped}
Path(__file__).with_name('bootstrap-source-mapping.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ['authoredEntries', 'statements', 'unmappedStatements', 'physicalCoverageComplete']}, indent=2))
if receipt['unmappedStatements']:
    raise SystemExit(1)
