"""Independent review-record shape controls; no artifact or authority admission."""
from copy import deepcopy
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

contracts = Path(__file__).resolve().parents[3] / '02-design/contracts'
schema = json.loads((contracts / 'reference-composition-review-v0.1.proposal.schema.json').read_bytes())
upstream = json.loads((contracts / 'acceptance-input-v0.1.schema.json').read_bytes())
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema, registry=Registry().with_resource(
    upstream['$id'], Resource.from_contents(upstream)))
# These seven identities come from the correspondence table, not schema enumeration.
boundaries = ['umf_acceptance', 'physical_installation', 'acceptance_history',
              'storage_compiler', 'execution_security_resources', 'installation_upgrades',
              'typescript_python']
incomplete = {'state': 'incomplete', 'remaining': ['Original selected evidence unavailable']}
reviewed = {'state': 'reviewed', 'evidence': {
    'identity': 'synthetic-shape-only', 'bytesBase64': 'e30=', 'sha256': 'a' * 64}}
base = {'interfaceVersion': 'truss-reference-composition-review/0.1.0-proposal',
        'scope': 'review_record_only', 'boundaries': [
            {'boundary': name, 'membership': [], 'authored': incomplete,
             'independentReview': incomplete, 'nativeQualification': incomplete}
            for name in boundaries]}
cases = [('explicit-incomplete-seven-boundaries', base, True)]
for name, mutate in [
    ('missing-boundary', lambda d: d['boundaries'].pop()),
    ('duplicate-boundary', lambda d: d['boundaries'].__setitem__(0, d['boundaries'][1])),
    ('authority-scope-substitution', lambda d: d.__setitem__('scope', 'activation_permit')),
    ('missing-evidence', lambda d: d['boundaries'][0].__setitem__('authored', {'state': 'reviewed'})),
    ('independent-before-authored', lambda d: d['boundaries'][0].__setitem__('independentReview', reviewed)),
    ('native-before-review', lambda d: d['boundaries'][0].__setitem__('nativeQualification', reviewed)),
]:
    changed = deepcopy(base); mutate(changed); cases.append((name, changed, False))
changed = deepcopy(base)
changed['boundaries'][0].update(authored=reviewed, independentReview=reviewed)
cases.append(('reviewed-source-with-incomplete-native', changed, True))
changed = deepcopy(changed); changed['boundaries'][0]['nativeQualification'] = reviewed
cases.append(('synthetic-reviewed-evidence-shape-only', changed, True))
for name, value, expected in cases:
    if validator.is_valid(value) != expected:
        raise SystemExit('Unexpected review-record shape outcome: ' + name)
print(str(len(cases)) + ' independent review-shape controls passed; synthetic evidence grants no compatibility or authority')

# Preserve full source equality, not digest-only correspondence, for this draft.
import base64
from hashlib import sha256
repo = contracts.parents[3]
record = json.loads((Path(__file__).resolve().parent / 'reference-composition-incomplete.json').read_bytes())
validator.validate(record)
# Required roots come from the reference composition correspondence, separately
# from the inspected record. Schema dependency closure is checked by the separate
# closure verifier; neither inventory establishes semantic/native compatibility.
required_roots = {
    'umf_acceptance': ['acceptance-report-v0.3.proposal.schema.json'],
    'physical_installation': ['CONTRACT-008-layout-bootstrap.md'],
    'acceptance_history': ['history-event-v0.2.proposal.schema.json',
                           'retained-history-archive-v0.2.proposal.schema.json'],
    'storage_compiler': ['consumer-read-integration.proposal.md'],
    'execution_security_resources': ['installed-context-admission.proposal.md'],
    'installation_upgrades': ['bindings/truss-layout-migration-v0.1.proposal.d.ts'],
    'typescript_python': ['acceptance-input-v0.1.schema.json'],
}

def original_root_membership(rows):
    if len(rows) != len(required_roots) or {r['boundary'] for r in rows} != set(required_roots):
        return False
    for row in rows:
        members = row['membership']
        roles = [m['role'] for m in members]
        identities = [m['artifact']['identity'] for m in members]
        if len(set(roles)) != len(roles) or len(set(identities)) != len(identities):
            return False
        actual = {(m['role'], m['artifact']['identity']) for m in members
                  if m['role'].startswith('candidate-source:')}
        expected = {('candidate-source:' + name,
                     'docs/helix/02-design/contracts/' + name)
                    for name in required_roots[row['boundary']]}
        if actual != expected:
            return False
    return True

# Small projections retain independent identity/role mutations without copying
# megabytes of original captured bytes. Full record shape and byte checks remain.
projection = [{'boundary': r['boundary'], 'membership': [
    {'role': m['role'], 'artifact': {'identity': m['artifact']['identity']}}
    for m in r['membership']]} for r in record['boundaries']]
if not original_root_membership(projection):
    raise SystemExit('Required original candidate root membership changed')
controls = 0
for index in range(len(projection)):
    for mutation in ['omit', 'relabel', 'duplicate', 'swap']:
        changed = deepcopy(projection)
        members = changed[index]['membership']
        root_index = next(i for i, m in enumerate(members)
                          if m['role'].startswith('candidate-source:'))
        if mutation == 'omit':
            members.pop(root_index)
        elif mutation == 'relabel':
            members[root_index]['role'] = 'schema-dependency:substituted'
        elif mutation == 'duplicate':
            members.append(deepcopy(members[root_index]))
        else:
            members[root_index]['artifact']['identity'] = 'docs/helix/02-design/contracts/acceptance-report-v0.1.schema.json'
        if original_root_membership(changed):
            raise SystemExit('Root omission/substitution control admitted: ' + mutation)
        controls += 1
print(str(controls) + ' independent candidate-root membership controls passed')
for row in record['boundaries']:
    for member in row['membership']:
        artifact = member['artifact']
        path = repo / artifact['identity']
        if not path.resolve().is_relative_to(contracts.resolve()):
            raise SystemExit('Captured root escaped the contract inventory')
        original = base64.b64decode(artifact['bytesBase64'], validate=True)
        if original != path.read_bytes() or sha256(original).hexdigest() != artifact['sha256']:
            raise SystemExit('Captured original root changed: ' + artifact['identity'])
print('Seven-boundary incomplete record and complete original root bytes verified; no compatibility admission')
