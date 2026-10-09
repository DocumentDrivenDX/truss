"""Capture/check complete local schema dependencies; no semantic profile admission."""
import base64
from hashlib import sha256
import json
from pathlib import Path
import sys
from composition_schema_refs import static_refs

if sys.argv[1:] not in ([], ['--capture']):
    raise SystemExit('Only --capture or no arguments supported')
here = Path(__file__).resolve().parent
repo = here.parents[4]
contracts = repo / 'docs/helix/02-design/contracts'
record_path = here / 'reference-composition-incomplete.json'
record = json.loads(record_path.read_bytes())
roots = {
    'umf_acceptance': ['acceptance-report-v0.3.proposal.schema.json'],
    'acceptance_history': ['history-event-v0.2.proposal.schema.json',
                           'retained-history-archive-v0.2.proposal.schema.json'],
    'typescript_python': ['acceptance-input-v0.1.schema.json'],
}
registry = {}
for path in sorted(contracts.glob('*.schema.json')):
    schema = json.loads(path.read_bytes())
    identity = schema['$id']
    if identity in registry:
        raise SystemExit('Duplicate original schema identity')
    registry[identity] = (path, schema)



counts = {}
for row in record['boundaries']:
    if row['boundary'] not in roots:
        continue
    pending = [contracts / name for name in roots[row['boundary']]]
    closure = set()
    while pending:
        path = pending.pop()
        if path in closure:
            continue
        closure.add(path)
        schema = json.loads(path.read_bytes())
        for identity in static_refs(schema):
            if identity not in registry:
                raise SystemExit('Unavailable original local schema: ' + identity)
            pending.append(registry[identity][0])
    current = {member['artifact']['identity']: member for member in row['membership']}
    for path in sorted(closure):
        identity = str(path.relative_to(repo))
        original = path.read_bytes()
        if '--capture' in sys.argv and identity not in current:
            row['membership'].append({'role': 'schema-dependency:' + path.name,
                                      'artifact': {'identity': identity,
                                                   'bytesBase64': base64.b64encode(original).decode(),
                                                   'sha256': sha256(original).hexdigest()}})
        else:
            if identity not in current:
                raise SystemExit('Missing original schema membership: ' + identity)
            artifact = current[identity]['artifact']
            if base64.b64decode(artifact['bytesBase64'], validate=True) != original or artifact['sha256'] != sha256(original).hexdigest():
                raise SystemExit('Changed original schema membership: ' + identity)
    counts[row['boundary']] = len(closure)
if '--capture' in sys.argv:
    record_path.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'schemaClosurePerBoundary': counts,
                  'scope': 'Complete local schema reference membership only; semantic/native/owner/procedure composition incomplete'}))
