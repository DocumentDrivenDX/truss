"""Exact tagged-node candidates only; no identity reassignment or native proof."""
import collections
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[5]
BASE = 'docs/helix/04-build/evidence/design-audit/'

def digest(b):
    return hashlib.sha256(b).hexdigest()

def load(path, expected=None):
    b = (ROOT / path).read_bytes()
    if expected is not None and digest(b) != expected:
        raise ValueError('source hash mismatch: ' + path)
    return json.loads(b), digest(b)

def node_hash(node):
    return digest(json.dumps(node, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True).encode())

def at(node, pointer):
    for part in pointer.split('/')[1:]:
        key = part.replace('~1', '/').replace('~0', '~')
        node = node[int(key)] if isinstance(node, list) else node[key]
    return node

manifest, manifest_hash = load(BASE + 'review010-prior-identity-catalogs.json')
composition, _ = load(BASE + 'request-receipt-layout-profile-composition.json')
selected, selected_hash = load(composition['modelPath'], composition['modelSha256'])
prefix = '/modules/0/elements/0/extensions/umf.postgresql/root/members/stmts'
index = collections.defaultdict(list)

def walk(node, pointer):
    if isinstance(node, dict):
        if node.get('kind') in ('object', 'array'):
            index[node_hash(node)].append(pointer)
        for key, value in node.items():
            walk(value, pointer + '/' + key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            walk(value, pointer + '/' + str(i))

walk(at(selected, prefix), prefix)
models = {}
rows = []
for catalog in manifest['catalogs']:
    data, _ = load(catalog['path'], catalog['sha256'])
    for entry in data['entries']:
        loc = entry['capturedModelLocator']
        path = loc.get('modelPath', loc.get('model'))
        if path not in models:
            models[path] = load(path, loc['modelSha256'])[0]
        # Recheck each locator pin, even when a model was previously cached.
        load(path, loc['modelSha256'])
        original = at(models[path], loc['jsonPointer'])
        h = node_hash(original)
        if 'originalNativeNode' in entry and entry['originalNativeNode'] != original:
            raise ValueError('original node substitution: ' + catalog['path'])
        if entry.get('originalNativeNodeSha256', h) != h:
            raise ValueError('original node digest mismatch: ' + catalog['path'])
        candidates = index.get(h, [])
        rows.append({'authoredId': entry.get('entryId', entry.get('id')),
                     'catalogPath': catalog['path'], 'originalLocator': loc,
                     'originalTaggedNodeSha256': h,
                     'selectedCandidatePointers': candidates,
                     'state': 'unique_exact_node_candidate' if len(candidates) == 1
                     else 'ambiguous_exact_node_candidates' if candidates
                     else 'no_exact_node_candidate'})
counts = dict(collections.Counter(r['state'] for r in rows))

def decode(node):
    if node['kind'] == 'object':
        return {k: decode(v) for k, v in node['members'].items()}
    if node['kind'] == 'array':
        return [decode(v) for v in node['items']]
    return json.loads(node['value']) if node['kind'] == 'number' else node.get('value')

def without_locations(node):
    if isinstance(node, dict):
        return {k: without_locations(v) for k, v in node.items()
                if k not in ('location', 'stmt_location', 'stmt_len')}
    if isinstance(node, list):
        return [without_locations(v) for v in node]
    return node

# Names select diagnostic before/after candidates only, never authored identities.
statements = decode(at(selected, prefix))
tables = {n['stmt']['CreateStmt']['relation']['relname']: n['stmt']['CreateStmt']
          for n in statements if 'CreateStmt' in n['stmt']}
baseline_path = 'docs/helix/02-design/models/truss-layout-0.2.physical-ids.draft.json'
baseline = load(baseline_path)[0]
unmatched = {r['authoredId'] for r in rows if r['state'] == 'no_exact_node_candidate'}
diagnostics = []
for entry in baseline['entries']:
    if entry['entryId'] not in unmatched:
        continue
    ni = entry['nativeIdentity']
    name = ni['name'] if entry['objectKind'] == 'table' else ni['relation']['name']
    candidate = tables.get(name)
    if candidate is not None and entry['objectKind'] == 'column':
        candidate = next((c['ColumnDef'] for c in candidate['tableElts']
                          if c.get('ColumnDef', {}).get('colname') == ni['name']), None)
    loc = entry['capturedModelLocator']
    original = decode(at(models[loc['modelPath']], loc['jsonPointer']))
    state = 'absent_named_candidate' if candidate is None else 'parser_locations_only' if without_locations(original) == without_locations(candidate) else 'definition_changed'
    diagnostics.append({'authoredId': entry['entryId'], 'state': state,
                        'originalDefinition': original, 'namedCandidateDefinition': candidate})
result = {'scope': 'exact preserved tagged-node candidates including parser locations; parent/evolution/composition identity review remains mandatory',
          'manifestSha256': manifest_hash, 'selectedModelPath': composition['modelPath'],
          'selectedModelSha256': selected_hash, 'counts': counts, 'entries': rows,
          'sourceCorrespondenceComplete': False, 'nativeInventoryQualified': False,
          'identityAssignmentsMade': 0,
          'baselineDiagnosticScope': 'named before/after lookup, dropping only parser location fields for comparison; not identity allocation or native equivalence',
          'baselineDiagnostics': diagnostics,
          'baselineDiagnosticCounts': dict(collections.Counter(d['state'] for d in diagnostics))}
(ROOT / (BASE + 'review011-original-node-correspondence.json')).write_text(
    json.dumps(result, separators=(',', ':')) + '\n')
print(json.dumps(counts))

# Preserve original authored custody while diagnosing this additive composition.
previous, _ = load(BASE + 'review010-original-node-correspondence.json')
old = {e['authoredId']: e for e in previous['entries']}
new = {e['authoredId']: e for e in rows}
if old.keys() != new.keys():
    raise ValueError('authored identity membership changed')
changes = []
prior_unique = 0
for identity, entry in new.items():
    prior = old[identity]
    for key in ('catalogPath', 'originalLocator', 'originalTaggedNodeSha256'):
        if entry[key] != prior[key]:
            raise ValueError('original custody changed: ' + identity)
    if prior['state'] == 'unique_exact_node_candidate':
        prior_unique += 1
        if entry['state'] != prior['state'] or entry['selectedCandidatePointers'] != prior['selectedCandidatePointers']:
            raise ValueError('prior exact candidate changed: ' + identity)
    if prior['state'] != entry['state']:
        changes.append(entry)
receipt_catalog = 'docs/helix/02-design/models/truss-receipt-candidate.physical-ids.draft.json'
if len(changes) != 49 or any(e['state'] != 'unique_exact_node_candidate' or e['catalogPath'] != receipt_catalog for e in changes):
    raise ValueError('unexpected receipt composition transition')
transition = {'scope': 'Original authored identity/source custody preserved from 0.10 to 0.11; exact-node candidates only, not reviewed identity adoption or native qualification',
              'previousCounts': previous['counts'], 'currentCounts': counts,
              'unchangedPriorUniqueCandidates': prior_unique,
              'newReceiptUniqueCandidates': len(changes),
              'changedCatalogs': dict(collections.Counter(e['catalogPath'] for e in changes)),
              'identityAssignmentsMade': 0, 'nativeQualified': False}
(ROOT / (BASE + 'review011-original-node-transition.json')).write_text(json.dumps(transition, indent=2) + '\n')
