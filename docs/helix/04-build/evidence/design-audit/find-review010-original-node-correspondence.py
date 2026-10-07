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
composition, _ = load(BASE + 'migration-homes-layout-profile-composition.json')
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
result = {'scope': 'exact preserved tagged-node candidates including parser locations; parent/evolution/composition identity review remains mandatory',
          'manifestSha256': manifest_hash, 'selectedModelPath': composition['modelPath'],
          'selectedModelSha256': selected_hash, 'counts': counts, 'entries': rows,
          'sourceCorrespondenceComplete': False, 'nativeInventoryQualified': False,
          'identityAssignmentsMade': 0}
(ROOT / (BASE + 'review010-original-node-correspondence.json')).write_text(
    json.dumps(result, separators=(',', ':')) + '\n')
print(json.dumps(counts))
