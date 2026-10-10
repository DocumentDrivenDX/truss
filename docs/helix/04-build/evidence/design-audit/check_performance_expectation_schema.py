"""Independent shape controls only; no benchmark or runner qualification."""
import json
from pathlib import Path
import sys
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

if len(sys.argv) != 1:
    raise SystemExit('No arguments admitted')
contracts = Path(__file__).resolve().parents[3] / '02-design' / 'contracts'
resources = []
seen = set()
for path in sorted(contracts.glob('*.schema.json')):
    schema = json.loads(path.read_bytes())
    identity = schema['$id']
    if identity in seen:
        raise ValueError('Duplicate original schema identity')
    seen.add(identity)
    resources.append((identity, Resource.from_contents(schema)))
registry = Registry().with_resources(resources)
new = json.loads((contracts / 'conformance-case-expected-v0.2.proposal.schema.json').read_bytes())
old = json.loads((contracts / 'conformance-case-expected-v0.1.proposal.schema.json').read_bytes())
profile = {'identity': 'shape', 'version': '0.1.0', 'sha256': 'a' * 64}
section = {'observationProfile': profile, 'observations': []}
base = {'interfaceVersion': 'truss-conformance-case-expected/0.2.0',
        'caseId': 'shape', 'grammarProfile': profile,
        **{name: section for name in ['result', 'state', 'journal', 'report', 'performance']}}
controls = 0

def check(value, expected, schema=new):
    global controls
    actual = Draft202012Validator(schema, registry=registry).is_valid(value)
    if actual != expected:
        raise ValueError('Independent shape expectation mismatch')
    controls += 1

check(base, True)
for name in ['result', 'state', 'journal', 'report', 'performance']:
    check({key: value for key, value in base.items() if key != name}, False)
check({**base, 'interfaceVersion': 'truss-conformance-case-expected/0.1.0'}, False)
check({**base, 'performance': {**section, 'callback': 'sample'}}, False)
artifact = {'identity': 'expected', 'bytesBase64': 'e30=', 'sha256': 'a' * 64}
observation = {'step': 'benchmark', 'boundary': 'committed',
               'comparatorProfile': profile, 'expected': artifact}
check({**base, 'performance': {**section, 'observations': [observation]}}, True)
check({**base, 'performance': {**section, 'observations': [{**observation, 'boundary': 'callback_returned'}]}}, False)
check({**base, 'performance': {**section, 'observations': [{key: value for key, value in observation.items() if key != 'comparatorProfile'}]}}, False)
legacy = {key: value for key, value in base.items() if key != 'performance'}
legacy['interfaceVersion'] = 'truss-conformance-case-expected/0.1.0'
check(legacy, True, old)
check({**legacy, 'performance': section}, False, old)
print(f'{controls} performance expectation shape controls passed; no runner or benchmark qualification')
