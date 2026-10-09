"""Independent inspection shape expectations; no native authority or outcome proof."""
from copy import deepcopy
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
contracts = Path(__file__).resolve().parents[3] / '02-design/contracts'
schema = json.loads((contracts / 'layout-migration-inspection-v0.1.proposal.schema.json').read_bytes())
source = json.loads((contracts / 'acceptance-input-v0.1.schema.json').read_bytes())
registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in (schema, source))
Draft202012Validator.check_schema(schema)
artifact = {'identity': 'synthetic', 'bytesBase64': 'e30=', 'sha256': 'a' * 64}
profile = {'identity': 'synthetic', 'version': '0.1', 'sha256': 'b' * 64}
pin = {'version': '1.0.0', 'bundleSha256': 'c' * 64, 'inventorySha256': 'd' * 64}
observed = {'outcome': 'observed', 'layout': pin, 'installation': artifact,
            'nativeObservation': artifact, 'scope': 'current_installation_observation_only'}
matches = {'outcome': 'matches', 'expected': pin, 'installation': artifact,
           'nativeObservation': artifact, 'correspondence': artifact,
           'scope': 'current_installation_verification_only'}
drift = {'outcome': 'drift', 'expected': pin, 'nativeObservation': artifact,
         'differences': artifact, 'scope': 'current_installation_verification_only'}
unknown = {'outcome': 'observation_unavailable', 'reason': 'custody'}
cases = [('inspectionRequest', {'procedure': profile, 'resource': profile}, True),
         ('verificationRequest', {'procedure': profile, 'resource': profile, 'expected': pin}, True),
         ('status', observed, True), ('status', unknown, True),
         ('verification', matches, True), ('verification', drift, True), ('verification', unknown, True),
         ('verification', observed, False), ('status', matches, False),
         ('status', {**unknown, 'layout': pin}, False),
         ('verification', {**matches, 'commitObservation': artifact}, False),
         ('verification', {**drift, 'correspondence': artifact}, False),
         ('inspectionRequest', {'procedure': profile}, False)]
changed = deepcopy(matches); del changed['correspondence']; cases.append(('verification', changed, False))
changed = deepcopy(observed); changed['layout']['version'] = '01.0.0'; cases.append(('status', changed, False))
for definition, value, expected in cases:
    validator = Draft202012Validator({'$ref': schema['$id'] + '#/$defs/' + definition}, registry=registry)
    if validator.is_valid(value) != expected:
        raise SystemExit('Inspection carrier differs from expectation: ' + definition)
if Draft202012Validator(schema, registry=registry).is_valid(matches):
    raise SystemExit('Definitions-only root accepted a payload')
print(str(len(cases)+1) + ' independent inspection schema controls passed; native inspection unqualified')
