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
