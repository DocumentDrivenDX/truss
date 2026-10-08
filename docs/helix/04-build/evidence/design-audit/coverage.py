"""Document inventory only; does not qualify semantic readiness or runtime support."""
from pathlib import Path
import json
import re
import sys
import hashlib

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
records = []
errors = []
stories = sorted((ROOT / '01-frame/user-stories').glob('US-*.md'))
if not stories:
    errors.append('missing story inventory')
seen_story_ids = set()
for story in stories:
    text = story.read_text()
    identities = re.findall(r'^  id: (US-\d+)$', text, re.M)
    if len(identities) != 1:
        errors.append(f'{story.name}: requires exactly one story identity')
        continue
    identity = identities[0]
    if identity in seen_story_ids:
        errors.append(f'{identity}: duplicate story identity')
    seen_story_ids.add(identity)
    number = identity[3:]
    if text.count('## Acceptance Criteria\n') != 1:
        errors.append(f'{identity}: requires exactly one acceptance declaration section')
        continue
    section = text.split('## Acceptance Criteria', 1)[1].split('\n## ', 1)[0]
    criteria = re.findall(r'\*\*(US-\d+-AC\d+)\*\*', section)
    if not criteria or len(criteria) != len(set(criteria)):
        errors.append(f'{identity}: missing or repeated criterion declaration')
    if any(not criterion.startswith(identity + '-AC') for criterion in criteria):
        errors.append(f'{identity}: foreign criterion declaration')
    entry = {'story': identity, 'criteria': criteria, 'artifacts': {}, 'missingReferences': {}}
    for prefix, directory in [('TD', '02-design/technical-designs'), ('STP', '03-test/test-plans')]:
        matches = list((ROOT / directory).glob(f'{prefix}-{number}-*.md'))
        if len(matches) > 1:
            errors.append(f'{identity}: duplicate {prefix}')
        if not matches:
            errors.append(f'{identity}: missing {prefix}')
        entry['artifacts'][prefix] = str(matches[0].relative_to(ROOT)) if matches else None
        refs = set(re.findall(r'US-\d+-AC\d+', matches[0].read_text())) if matches else set()
        entry['missingReferences'][prefix] = sorted(set(criteria) - refs)
        if entry['missingReferences'][prefix]:
            errors.append(f"{identity}: missing {prefix} references {entry['missingReferences'][prefix]}")
    entry['primaryAllocations'] = {}
    if entry['artifacts']['STP']:
        plan = (ROOT / entry['artifacts']['STP']).read_text()
        if plan.count('## Acceptance Criteria Test Mapping\n') != 1:
            errors.append(f'{identity}: requires exactly one primary mapping section')
            records.append(entry)
            continue
        matrix = plan.split('## Acceptance Criteria Test Mapping', 1)[1].split('\n## ', 1)[0]
        rows = [line for line in matrix.splitlines() if re.match(r'\| US-\d+-AC\d+ \|', line)]
        for criterion in criteria:
            matching = [row for row in rows if row.split('|')[1].strip() == criterion]
            if len(matching) != 1:
                errors.append(f'{identity}: {criterion} needs exactly one primary allocation row')
                continue
            cells = [cell.strip() for cell in matching[0].split('|')[1:-1]]
            if len(cells) != 6 or not cells[1] or not cells[2] or f'@covers {criterion}' not in cells[3] or not cells[4]:
                errors.append(f'{identity}: incomplete allocation row for {criterion}')
            else:
                entry['primaryAllocations'][criterion] = cells[4]
        unknown = [row.split('|')[1].strip() for row in rows if row.split('|')[1].strip() not in criteria]
        if unknown:
            errors.append(f'{identity}: undeclared allocation criteria {unknown}')
    records.append(entry)
# Expectation is supplied independently of the candidate inventory. Never regenerate it here.
expectation_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(__file__).with_name('expected-design-scope.json')
expectation_sha = None
try:
    raw_expectation = expectation_path.read_bytes()
    expectation_sha = hashlib.sha256(raw_expectation).hexdigest()
    expectation = json.loads(raw_expectation)
    if expectation.get('interfaceVersion') != 'truss-design-scope/0.1.0':
        raise ValueError('unsupported expectation version')
    expected = {}
    for entry in expectation['entries']:
        identity, criteria = entry['story'], entry['criteria']
        if identity in expected or not criteria or len(criteria) != len(set(criteria)):
            raise ValueError('duplicate story or invalid expected criteria')
        if not re.fullmatch(r'US-\d+', identity) or any(not re.fullmatch(re.escape(identity) + r'-AC\d+', c) for c in criteria):
            raise ValueError('invalid expectation identity')
        expected[identity] = set(criteria)
    if not expected:
        raise ValueError('empty expected scope')
    actual = {r['story']: set(r['criteria']) for r in records}
    for identity in sorted(set(expected) - set(actual)):
        errors.append(f'{identity}: missing expected story')
    for identity in sorted(set(actual) - set(expected)):
        errors.append(f'{identity}: unexpected story; reconcile governed scope')
    for identity in sorted(set(actual) & set(expected)):
        if actual[identity] != expected[identity]:
            errors.append(f'{identity}: criterion membership differs from expected scope')
except (OSError, ValueError, KeyError, TypeError) as failure:
    errors.append(f'invalid expected scope: {failure}')
complete = [r for r in records if all(r['artifacts'].values()) and not any(r['missingReferences'].values())]
result = {'scope': 'artifact existence, criterion references and primary allocation structure; no semantic/runtime qualification', 'expectedScopeSha256': expectation_sha, 'stories': len(records),
          'criteria': sum(len(r['criteria']) for r in records), 'pairsWithAllReferences': len(complete),
          'criteriaWithPairReferences': sum(len(r['criteria']) for r in complete),
          'errors': errors, 'inventory': records}
print(json.dumps(result, indent=2))
if errors:
    raise SystemExit(1)
