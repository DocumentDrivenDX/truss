"""Logical fixture/shape/history expectation consistency; no native qualification."""
from pathlib import Path
import hashlib
import json

def require(condition):
    if not condition:
        raise ValueError('Original oracle correspondence mismatch')

ROOT = Path(__file__).resolve().parents[5]
TEST = ROOT / 'docs/helix/03-test'
logical_path = TEST / 'reference-account-items-expected-states.proposal.json'
raw = logical_path.read_bytes()
logical = json.loads(raw)
shape = json.loads((TEST / 'reference-account-items-row-shape.proposal.json').read_text())
history = json.loads((TEST / 'reference-note-journal-expectations.proposal.json').read_text())
for dependent in [shape, history]:
    require(dependent['logicalOraclePath'] == str(logical_path.relative_to(ROOT)))
    require(dependent['logicalOracleSha256'] == hashlib.sha256(raw).hexdigest())
    require(dependent['nativeExecuted'] is False)
states = logical['expectedStates']
require(set(shape['expectedCuts']) == set(states))
for name, state in states.items():
    values = [v for owner in state['objects'] for v in owner['values'].values()]
    present = sum(v['present'] for v in values)
    payloads = sum(v['present'] and v['value']['kind'] != 'null' for v in values)
    require(shape['expectedCuts'][name] == {'states': present, 'rootNodes': present, 'scalarPayloads': payloads})
baseline = states['M03_committed']
for name in ['M04_each_confirmed_refusal', 'M05_independent_committed_observer', 'M05_after_confirmed_rollback']:
    require(states[name] == baseline)
final = states['M06_after_confirmed_commit']
require(states['M05_original_transaction_pending'] == final)
require(baseline['edges'] == final['edges'] and baseline['businessKeys'] == final['businessKeys'])
require(len(baseline['objects']) == len(final['objects']) == 4)
changes = []
for before, after in zip(baseline['objects'], final['objects']):
    require(before['symbol'] == after['symbol'] and before['record'] == after['record'])
    require(set(before['values']) == set(after['values']))
    for field in before['values']:
        if before['values'][field] != after['values'][field]:
            changes.append((before['symbol'], field, before['values'][field], after['values'][field]))
require(changes == [('B', 'Item.note', {'present': False}, {'present': True, 'value': {'kind': 'null'}})])
siblings = history['expectedOrderedSiblings']
require(len(siblings) == 2 and [s['kind'] for s in siblings] == ['property', 'metadata'])
require([s['ordinal'] for s in siblings] == ['0', '1'])
require(siblings[0]['before'] == changes[0][2] and siblings[0]['after'] == changes[0][3])
def pointer(text):
    value = logical
    for token in text.split('/')[1:]:
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value
require(pointer(siblings[1]['beforeLogicalStatePointer']) == baseline['objects'][1])
require(pointer(siblings[1]['afterLogicalStatePointer']) == final['objects'][1])
require(baseline['objects'][1]['symbol'] == final['objects'][1]['symbol'] == history['typedEntity']['symbol'])
print('Six logical cuts, proposed row shapes and one exact B note delta agree; full native/history facts remain unqualified.')
