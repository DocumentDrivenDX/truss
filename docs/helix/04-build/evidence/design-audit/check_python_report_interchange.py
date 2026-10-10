"""Independent expected wire decisions through Python and TypeScript candidates."""
from copy import deepcopy
from hashlib import sha256
import base64
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from python_report_wire_candidate import ReportWireCandidate, PINS
from test_python_report_wire_candidate import candidate, wire, CONTRACTS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DEPENDENCIES = '/Users/erik/Projects/umf/package.json'
codec = ReportWireCandidate(CONTRACTS)
controls = []


def add(name, source, accepted):
    controls.append({'name': name, 'bytesBase64': base64.b64encode(source).decode('ascii'),
                     'expectedAccepted': accepted})


base = candidate()
add('complete-nineteen-field-report', wire(base), True)
add('whitespace-preserved', b' \n'+wire(base)+b'\t\n', True)
unicode_report = deepcopy(base)
unicode_report['lifecycleProfile']['identity'] = 'é/e\u0301/𐀀/$a'
add('unicode-and-literal-alias-preserved', wire(unicode_report), True)
add('escaped-versus-literal-original-bytes', json.dumps(unicode_report, ensure_ascii=True).encode(), True)
for field in base:
    changed = deepcopy(base); del changed[field]
    add('missing-'+field, wire(changed), False)
for version in ['truss-acceptance-report/0.1.0', 'truss-acceptance-report/0.2.0-proposal', 'unknown']:
    changed = deepcopy(base); changed['interfaceVersion'] = version
    add('wrong-version-'+version, wire(changed), False)
changed = deepcopy(base); changed['counts']['typesAdded'] = 9007199254740993
add('outer-large-number-refuses', wire(changed), False)
changed = deepcopy(base); changed['counts']['typesAdded'] = False
add('boolean-is-not-integral-text', wire(changed), False)
changed = deepcopy(base); changed['accepted'] = True
add('unknown-acceptance-claim-refuses', wire(changed), False)
add('duplicate-member-refuses', b'{"rev":"1",'+wire(base)[1:], False)
changed = deepcopy(base); changed['lifecycleProfile']['identity'] = '\0'
add('byte-report-NUL-preserved-without-text-admission', wire(changed), True)
changed = deepcopy(base); changed['lifecycleProfile']['identity'] = '\ud800'
add('unpaired-surrogate-refuses', json.dumps(changed).encode(), False)
add('above-source-byte-bound-refuses', b' '*1048577, False)
changed = deepcopy(base); changed['documents'] = []
changed['originalExecution']['origin']['databaseRole'] = 'invented'
add('shape-valid-forgery-remains-codec-only', wire(changed), True)

artifact = {'identity': 'synthetic', 'bytesBase64': 'e30=', 'sha256': 'a'*64}
changed = deepcopy(base)
changed['reactivations'] = [{'identity': {'kind': 'key', 'typeId': '1', 'keyNumber': '1'},
    'owner': {'documentId': 'doc', 'moduleId': 'module'}, 'lineage': artifact,
    'beforeRetiredRevision': '1', 'beforeDefinition': artifact, 'afterDefinition': artifact}]
add('complete-nested-key-reactivation', wire(changed), True)
del changed['reactivations'][0]['identity']['typeId']
add('nested-owner-local-key-identity-required', wire(changed), False)
present, absent = {'present': True, 'value': {'kind': 'null'}}, {'present': False}
event = {'interfaceVersion': 'truss-history-event/0.2.0-proposal', 'sourceEpoch': 'epoch',
    'historyProfile': 'synthetic', 'xid': '1', 'seq': '1',
    'identity': {'id': '1', 'typeId': '1', 'definitionPin': 'synthetic',
                 'owner': {'documentId': 'doc', 'moduleId': 'module'}},
    'eventVersion': '2', 'eventCatalogRevision': '1',
    'mutationGroup': {'profile': 'truss-history-group/0.1.0', 'eventCount': '1', 'orderedEventDigest': '0'*64},
    'origin': {'asserted': {'kind': 'null'}, 'databaseRole': 'role'},
    'operation': 'rebind', 'retainedName': 'a', 'propertyId': '1',
    'beforeDefinitionContext': 'before', 'afterDefinitionPin': 'after',
    'retainedBefore': present, 'retainedAfter': absent, 'propertyBefore': absent, 'propertyAfter': present}
changed = deepcopy(base); changed['rebinds'] = [event]
add('complete-v02-history-rebind', wire(changed), True)
for field, value in [('interfaceVersion', 'truss-history-event/0.1.0'), ('operation', 'retain')]:
    invalid = deepcopy(changed); invalid['rebinds'][0][field] = value
    add('nested-rebind-wrong-'+field, wire(invalid), False)

# The report/event/presence wrappers contribute four containers. Each sequence
# contributes an object and an items array; the final null carrier adds one.
# Thus 61 sequences reach depth127, while 62 require depth129 above the cap128.
for count, leaf, accepted, name in [
    (61, {'kind': 'null'}, True, 'deep-exact-value-within-report-depth-bound'),
    (62, {'kind': 'null'}, False, 'deep-exact-value-above-report-depth-bound'),
    (61, {'kind': 'integer', 'text': True}, False, 'deep-invalid-exact-value-still-schema-refuses'),
]:
    value = leaf
    for _ in range(count): value = {'kind': 'sequence', 'items': [value]}
    deep_report = deepcopy(base); deep_event = deepcopy(event)
    deep_event['retainedBefore'] = {'present': True, 'value': value}
    deep_report['rebinds'] = [deep_event]
    add(name, wire(deep_report), accepted)

with tempfile.TemporaryDirectory(prefix='truss-report-interchange-') as temporary:
    inventory = Path(temporary)/'cases.json'
    inventory.write_text(json.dumps(controls))
    run = subprocess.run(['bun', str(HERE/'check-python-report-interchange.ts'),
                          str(inventory), DEPENDENCIES], cwd=ROOT,
                         text=True, capture_output=True)
    if run.returncode: raise RuntimeError(run.stdout+run.stderr)
    original_ts = json.loads(run.stdout)
if original_ts['schemaPins'] != dict(PINS): raise RuntimeError('Original schema bundle disagreement')
if len(original_ts['results']) != len(controls): raise RuntimeError('Complete case membership required')
results = []
for control, ts in zip(controls, original_ts['results']):
    source = base64.b64decode(control['bytesBase64'])
    try:
        retained = codec.prepare(source).original.source_bytes
        python = {'accepted': True, 'retainedMatches': retained == source,
                  'sha256': sha256(retained).hexdigest()}
    except Exception:
        python = {'accepted': False}
    if ts['name'] != control['name'] or python['accepted'] != control['expectedAccepted'] or ts['accepted'] != control['expectedAccepted']:
        raise RuntimeError('Independent expected wire decision disagrees: '+control['name'])
    if python['accepted'] and (not python['retainedMatches'] or not ts['retainedMatches'] or python['sha256'] != ts['sha256']):
        raise RuntimeError('Original byte custody disagrees: '+control['name'])
    results.append({'name': control['name'], 'expectedAccepted': control['expectedAccepted'],
                    'originalSourceSha256': sha256(source).hexdigest(), 'python': python, 'typescript': ts})
files = [Path(__file__), HERE/'check-python-report-interchange.ts', HERE/'python_report_wire_candidate.py',
         HERE/'python_raw_json_candidate.py', HERE/'test_python_report_wire_candidate.py',
         ROOT/'packages/umf-bun/src/canonical-report-handoff.ts',
         ROOT/'packages/postgresql/src/acceptance-json.ts', ROOT/'packages/postgresql/src/canonical-wire-tree.ts',
         ROOT/'docs/helix/03-test/report-wire-untrusted.fixture.json',
         ROOT/'packages/postgresql/native/canonical-string-bytes.sql']
receipt = {'status': 'passed', 'cases': len(results), 'python': sys.version,
           'host': {'system': platform.system(), 'machine': platform.machine()},
           'dependencies': {name: importlib.metadata.version(name) for name in ['jsonschema','referencing','attrs','jsonschema-specifications','rpds-py']},
           'schemaPins': dict(PINS), 'sourceSha256': {str(path.relative_to(ROOT)):sha256(path.read_bytes()).hexdigest() for path in files},
           'results': results, 'scope': 'Private composed report schema decision and original-byte parity only. Explicit independently expected positive/negative cases; shape-valid forgeries remain codec-only. No native writer/reader interchange, complete semantic report, authority, commit or resource-profile qualification.'}
(HERE/'python-report-interchange.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(str(len(results))+' independent expected shared report wire controls passed')
