"""Selected source design admission only; no body, native privilege or installer proof."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
PATH = 'docs/helix/02-design/contracts/reference-journal-phase-design-v0.1.proposal.json'
original = json.loads((ROOT / PATH).read_text())

def schema_closure(routines):
    registry = {}
    for path in (ROOT / 'docs/helix/02-design/contracts').rglob('*.schema.json'):
        body = json.loads(path.read_text())
        if '$id' in body:
            if body['$id'] in registry:
                raise ValueError('duplicate schema identity')
            registry[body['$id']] = (path, body)
    visited = set()
    def visit(identity):
        require(identity in registry, 'unresolved schema dependency')
        if identity in visited:
            return
        visited.add(identity)
        walk(registry[identity][1])
    def walk(value):
        if isinstance(value, dict):
            if '$ref' in value:
                identity = value['$ref'].split('#')[0]
                if identity:
                    visit(identity)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    for routine in routines:
        visit(routine['phaseBodySchema']['schemaId'])
    return [{'schemaId': identity,
             'path': str(registry[identity][0].relative_to(ROOT / 'docs/helix')),
             'sha256': hashlib.sha256(registry[identity][0].read_bytes()).hexdigest()}
            for identity in sorted(visited)]

def require(condition, message):
    if not condition:
        raise ValueError(message)

def validate(document):
    require(document['nativeQualified'] is False and document['installerReady'] is False,
            'unqualified design cannot claim readiness')
    attributes = {'language': 'plpgsql', 'volatility': 'VOLATILE', 'parallel': 'UNSAFE',
                  'nullInput': 'CALLED ON NULL INPUT', 'leakproof': False, 'security': 'DEFINER',
                  'searchPathRecipe': ['pg_catalog', {'trustedInstallationNamespace': True}, 'pg_temp'],
                  'publicExecute': False, 'ordinaryApplicationExecute': False}
    require(document['sharedSelectedAttributes'] == attributes, 'selected security attributes')
    sources = document['governingSources']
    require([s['path'] for s in sources] == [
        '02-design/contracts/CONTRACT-002-journal.md',
        '02-design/contracts/CONTRACT-005-module-isolation.md',
        '02-design/contracts/bindings/truss-journal-phase-resource-v0.2.proposal.json'], 'governing membership')
    for source in sources:
        require(hashlib.sha256((ROOT / 'docs/helix' / source['path']).read_bytes()).hexdigest()
                == source['sha256'], 'governing source drift')
    contract = (ROOT / 'docs/helix' / sources[0]['path']).read_text()
    names = ['journal_capture_start', 'journal_observe_transition', 'journal_prepare_final',
             'journal_reserve_positions', 'journal_append_group']
    require([r['selector'] for r in document['routines']] == names, 'phase membership/order')
    schemas = dict(zip(names, ['journal-start-capture-v0.2.proposal.schema.json',
        'journal-ordered-transition-v0.2.proposal.schema.json',
        'journal-final-preparation-v0.2.proposal.schema.json',
        'journal-reserved-positions-v0.2.proposal.schema.json',
        'journal-pending-publication-v0.2.proposal.schema.json']))
    for routine, stage in zip(document['routines'], ['start', 'transition', 'final', 'reserved', 'publication']):
        path = '02-design/contracts/' + schemas[routine['selector']]
        schema_bytes = (ROOT / 'docs/helix' / path).read_bytes()
        schema = json.loads(schema_bytes)
        require(routine.get('phaseBodySchema') == {'path': path, 'schemaId': schema['$id'],
                'sha256': hashlib.sha256(schema_bytes).hexdigest(),
                'byteEncodingProfile': 'truss-journal-phase-json/0.2.0-proposal'},
                'original phase schema and byte codec correspondence')
        args = [{'name': 'operation_context_bytes', 'type': 'bytea'}]
        if routine['selector'] == 'journal_observe_transition':
            args.append({'name': 'original_effect_bytes', 'type': 'bytea'})
        require(routine['parameters'] == args and routine['returns'] == 'bytea', 'original signature')
        signature = routine['selector'] + '(' + ', '.join(a['name'] + ' ' + a['type'] for a in args) + ') -> bytea'
        require('`' + signature + '`' in contract, 'signature absent from governing contract')
        require(routine['stage'] == stage and routine['ownerResponsibility'] == 'journal-phase-owner', 'phase ownership')
        for field in ['physicalIdentity', 'namespace', 'nativeRole', 'body', 'completeDependencies', 'privateCallerAcl', 'nativeEvidence']:
            require(routine[field] is None, 'unresolved binding replaced: ' + field)
    require(document['ownerForbiddenResponsibilities'] == ['parent readiness/sealing',
            'canonical graph/catalog/report mutation', 'stage deletion', 'sequence reset'], 'owner separation')
    require(document.get('phaseSchemaDependencies') == schema_closure(document['routines']),
            'complete original recursive phase schema dependencies')

validate(original)
controls = []
for label, mutate in [
    ('missing original effect argument', lambda d: d['routines'][1]['parameters'].pop()),
    ('PUBLIC execute enabled', lambda d: d['sharedSelectedAttributes'].update(publicExecute=True)),
    ('null input skipped', lambda d: d['sharedSelectedAttributes'].update(nullInput='STRICT')),
    ('producer owner can reset sequence', lambda d: d['ownerForbiddenResponsibilities'].pop()),
    ('invented physical identity', lambda d: d['routines'][0].update(physicalIdentity='new.phase.id')),
    ('false readiness', lambda d: d.update(installerReady=True)),
    ('substituted governing pin', lambda d: d['governingSources'][0].update(sha256='0' * 64)),
    ('missing phase schema', lambda d: d['routines'][0].pop('phaseBodySchema')),
    ('swapped phase schema', lambda d: d['routines'][0].update(phaseBodySchema=d['routines'][1]['phaseBodySchema'])),
    ('stale phase schema bytes', lambda d: d['routines'][2]['phaseBodySchema'].update(sha256='0' * 64)),
    ('wrong phase byte codec', lambda d: d['routines'][3]['phaseBodySchema'].update(byteEncodingProfile='event-codec')),
    ('missing recursive dependency', lambda d: d['phaseSchemaDependencies'].pop()),
    ('substituted recursive dependency', lambda d: d['phaseSchemaDependencies'][0].update(sha256='0' * 64)),
]:
    damaged = copy.deepcopy(original)
    mutate(damaged)
    try:
        validate(damaged)
    except ValueError as error:
        controls.append({'case': label, 'refused': True, 'reason': str(error)})
    else:
        raise ValueError('damaged design admitted: ' + label)
receipt = {'scope': __doc__, 'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'manifestSha256': hashlib.sha256((ROOT / PATH).read_bytes()).hexdigest(),
           'originalAdmitted': True, 'controls': controls, 'nativeQualified': False}
(ROOT / 'docs/helix/04-build/evidence/design-audit/journal-phase-design-controls.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Original design admitted; thirteen damaged design controls refused.')
