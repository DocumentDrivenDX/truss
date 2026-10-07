"""Finite synthetic design experiment, not the production history reducer."""
import copy
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
VECTORS = ROOT / 'history-metadata-correspondence-v0.1.vectors.json'
raw = VECTORS.read_bytes()
if len(raw) > 65536:
    raise ValueError('experiment fixture byte ceiling exceeded')
cases = json.loads(raw)['cases']
expected_ids = {'metadata-first','metadata-between','metadata-last','missing-delta','missing-metadata','duplicate-metadata','wrong-delta-before','dropped-retained','snapshot-token-swap','wrong-start','retain-two-additions','retain-duplicate-name','retain-existing-replacement','retain-missing-delta','retain-not-absent-before','retain-token-swap'}
if len(cases) != len(expected_ids) or {c['id'] for c in cases} != expected_ids:
    raise ValueError('independent case membership required')

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def admit(case):
    events = case['events']
    if len(events) > 8:
        raise ValueError('experiment event ceiling exceeded')
    # Deliberately recompute an internally consistent count/digest for corrupt cases.
    # Neither establishes semantic boundary correspondence.
    digest = hashlib.sha256(canonical(events)).hexdigest()
    witnesses = [e for e in events if e['kind'] == 'metadata']
    if len(witnesses) != 1:
        return 'refused', digest
    witness = witnesses[0]
    if canonical(witness['before']) != canonical(case['start']):
        return 'refused', digest
    staged = copy.deepcopy(case['start'])
    for event in events:
        if event['kind'] == 'metadata':
            continue
        if event['kind'] == 'retain':
            changes = event['changes']
            if not changes or len(changes) > 8:
                return 'refused', digest
            seen = set()
            for change in changes:
                name = change['name']
                if name in seen or name in staged['retained'] or change['before'] != {'present': False}:
                    return 'refused', digest
                seen.add(name)
                if change['after'].get('present') is not True or 'value' not in change['after']:
                    return 'refused', digest
                staged['retained'][name] = copy.deepcopy(change['after']['value'])
            continue
        if event['kind'] != 'property':
            return 'refused', digest
        home = event['home']
        if home not in staged['props'] or canonical(staged['props'][home]) != canonical(event['before']):
            return 'refused', digest
        staged['props'][home] = copy.deepcopy(event['after'])
    after = witness['after']
    if any(canonical(staged[k]) != canonical(after[k]) for k in ('identity', 'props', 'retained')):
        return 'refused', digest
    if after['version'] != '2':
        return 'refused', digest
    return 'admitted', digest

results = []
for case in cases:
    actual, digest = admit(case)
    if actual != case['expected']:
        raise ValueError(f"{case['id']}: expected {case['expected']}, got {actual}")
    results.append({'id': case['id'], 'outcome': actual, 'syntheticEventCount': len(case['events']), 'syntheticDigest': digest})
receipt = {'scope': 'Synthetic exact-tree metadata boundary correspondence; digest uses experiment JSON, not adopted journal canonical encoding', 'vectorSha256': hashlib.sha256(raw).hexdigest(), 'helperSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'passed': len(results), 'cases': results, 'nativeEvidence': False, 'profileAdopted': False, 'exclusions': ['actual event wire and digest domain', 'historical definition interpretation', 'original source custody', 'native snapshot/staging/sequence/commit', 'authority', 'production resource accounting']}
(ROOT / 'history-metadata-correspondence-audit.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'passed': len(results), 'nativeEvidence': False}))
