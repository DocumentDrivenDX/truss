"""Preserved candidate custody and explicit allocator evolution; no native adoption."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BASE = 'docs/helix/04-build/evidence/design-audit/'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def load(path):
    data = (ROOT / path).read_bytes()
    return json.loads(data), digest(data)

def at(node, pointer):
    for part in pointer.split('/')[1:]:
        key = part.replace('~1', '/').replace('~0', '~')
        node = node[int(key)] if isinstance(node, list) else node[key]
    return node

prior, prior_hash = load(BASE + 'review011-original-node-correspondence.json')
receipt, receipt_hash = load(BASE + 'reference-history-layout-model-source.json')
old, old_hash = load(prior['selectedModelPath'])
new, new_hash = load(receipt['modelPath'])
if old_hash != prior['selectedModelSha256'] or new_hash != receipt['modelSha256']:
    raise ValueError('model source drift')
rows = []
for entry in prior['entries']:
    pointers = entry['selectedCandidatePointers']
    if entry['state'] != 'unique_exact_node_candidate':
        rows.append({'authoredId': entry['authoredId'], 'state': entry['state'],
                     'sourceReviewStillRequired': True})
        continue
    if len(pointers) != 1:
        raise ValueError('prior candidate count')
    pointer = pointers[0]
    original, selected = at(old, pointer), at(new, pointer)
    if entry['authoredId'] == 'truss.layout.sequence.journal_seq':
        if 'options' in original['members'] or 'options' not in selected['members']:
            raise ValueError('unexpected sequence evolution')
        stripped = dict(selected, members=dict(selected['members']))
        del stripped['members']['options']
        if stripped != original:
            raise ValueError('allocator identity or other definition substituted')
        state = 'original_candidate_with_explicit_settings_evolution'
    else:
        if original != selected:
            raise ValueError('unreviewed candidate change: ' + entry['authoredId'])
        state = 'unchanged_original_candidate'
    rows.append({'authoredId': entry['authoredId'], 'originalLocator': entry['originalLocator'],
                 'selectedPointer': pointer, 'state': state})
counts = {state: sum(row['state'] == state for row in rows)
          for state in sorted({row['state'] for row in rows})}
if counts != {'no_exact_node_candidate': 87, 'original_candidate_with_explicit_settings_evolution': 1,
              'unchanged_original_candidate': 479}:
    raise ValueError('original candidate coverage drift')
result = {'scope': 'source candidate continuity only; changed sequence settings require explicit adoption/conversion review; no native identity proof',
          'producerSha256': digest(Path(__file__).read_bytes()),
          'priorCorrespondenceSha256': prior_hash, 'compositionReceiptSha256': receipt_hash,
          'oldModelSha256': old_hash, 'newModelSha256': new_hash,
          'counts': counts, 'entries': rows, 'nativeAdoption': False}
(ROOT / (BASE + 'review012-original-node-transition.json')).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(counts))
