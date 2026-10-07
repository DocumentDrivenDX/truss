"""Declared PRD allocation only: no semantic completeness or execution claim."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
prd = (ROOT / '01-frame/prd.md').read_text()
declared = set(map(int, re.findall(r'^- \*\*FR-(\d+)\*\*', prd, re.M)))
errors = []
inventory = {n: {'requirement': f'FR-{n}', 'features': [], 'stories': []} for n in sorted(declared)}

def requirements(value):
    numbers = set()
    for lo, hi in re.findall(r'FR-(\d+)\s+to\s+FR-(\d+)', value):
        numbers.update(range(int(lo), int(hi) + 1))
    numbers.update(map(int, re.findall(r'FR-(\d+)', value)))
    return numbers

for directory, field, kind in [('features', 'Covered PRD Requirements', 'features'),
                               ('user-stories', 'PRD Requirements', 'stories')]:
    for path in sorted((ROOT / '01-frame' / directory).glob('*.md')):
        text = path.read_text()
        # Accept both established Markdown placements of the field colon.
        match = re.search(r'^\*\*' + field + r':?\*\*:?\s*(.+)$', text, re.M)
        if not match:
            errors.append(f'{path.name}: missing declared requirement field')
            continue
        for n in sorted(requirements(match.group(1))):
            if n not in declared:
                errors.append(f'{path.name}: undeclared FR-{n}')
            else:
                inventory[n][kind].append(str(path.relative_to(ROOT)))
for entry in inventory.values():
    for kind in ['features', 'stories']:
        if not entry[kind]:
            errors.append(f'{entry["requirement"]}: no declared {kind} allocation')
print(json.dumps({'scope': 'explicit PRD numbered requirement declarations and feature/story header allocations only; excludes semantic adequacy, nonfunctional metrics and runtime evidence',
                  'requirements': len(declared), 'errors': errors, 'inventory': list(inventory.values())}, indent=2))
if errors:
    sys.exit(1)
