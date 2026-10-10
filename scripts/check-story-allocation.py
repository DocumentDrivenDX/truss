#!/usr/bin/env python3
"""Check current declared criterion references; no semantic or runtime verdict."""
import hashlib
import json
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
if len(sys.argv) != 2:
    raise SystemExit('usage: check-story-allocation.py NEW_RECEIPT_PATH')
destination = Path(sys.argv[1]).resolve()
if destination.exists():
    raise SystemExit('refusing to replace existing receipt')
stories = sorted((root / 'docs/helix/01-frame/user-stories').glob('US-*.md'))
errors, sources, criteria, allocations = [], [], [], []
allowed_layers = {'Native integration', 'Contract', 'Native concurrency',
                  'Native performance integration', 'Performance integration', 'Contract review'}
if len(stories) != 45:
    errors.append('expected all 45 stories')
for story in stories:
    number = story.name.split('-', 2)[1]
    design = list((root / 'docs/helix/02-design/technical-designs').glob('TD-' + number + '-*.md'))
    tests = list((root / 'docs/helix/03-test/test-plans').glob('STP-' + number + '-*.md'))
    if len(design) != 1 or len(tests) != 1:
        errors.append({'story': number, 'error': 'missing or duplicate pair'})
        continue
    text = story.read_text()
    ids = re.findall(r'^- \[[ xX]\] \*\*(US-\d+-AC\d+)\*\*', text, re.M)
    if not ids:
        errors.append({'story': number, 'error': 'no declared criteria'})
    for path in [story, design[0], tests[0]]:
        sources.append({'path': str(path.relative_to(root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    for identity in ids:
        if identity in criteria or not identity.startswith('US-' + number + '-AC'):
            errors.append({'criterion': identity, 'error': 'duplicate or foreign declaration'})
        criteria.append(identity)
        if identity not in design[0].read_text():
            errors.append({'criterion': identity, 'error': 'missing design reference'})
        rows = re.findall(r'^\| ' + re.escape(identity) + r' \|.*$', tests[0].read_text(), re.M)
        if len(rows) != 1:
            errors.append({'criterion': identity, 'error': 'expected exactly one primary test row', 'rows': len(rows)})
        else:
            cells = [cell.strip() for cell in rows[0].strip('|').split('|')]
            if len(cells) != 6 or any(not cell for cell in cells):
                errors.append({'criterion': identity, 'error': 'incomplete primary allocation row'})
            elif cells[4] not in allowed_layers:
                errors.append({'criterion': identity, 'error': 'unrecognized primary layer', 'layer': cells[4]})
            elif '@covers ' + identity not in cells[3]:
                errors.append({'criterion': identity, 'error': 'missing original criterion annotation'})
            else:
                allocations.append({'criterion': identity, 'scenario': cells[1],
                                    'expected': cells[2], 'layer': cells[4], 'testInputs': cells[5]})
if len(criteria) != 167:
    errors.append('expected all 167 criteria')
receipt = {'scope': 'Declared story/design/test reference structure only; no semantic adequacy, implementation or native verdict',
           'stories': len(stories), 'criteria': len(criteria), 'errors': errors, 'sources': sources,
           'allocations': allocations,
           'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'designClosureProven': False, 'nativeExecuted': False}
with destination.open('x') as stream:
    stream.write(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'stories': len(stories), 'criteria': len(criteria), 'errors': len(errors)}))
raise SystemExit(bool(errors))
