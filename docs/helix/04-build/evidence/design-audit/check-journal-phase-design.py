"""Selected source design admission only; no body, native privilege or installer proof."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
PATH = 'docs/helix/02-design/contracts/reference-journal-phase-design-v0.1.proposal.json'
original = json.loads((ROOT / PATH).read_text())

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
    for routine, stage in zip(document['routines'], ['start', 'transition', 'final', 'reserved', 'publication']):
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
print('Original design admitted; seven damaged design controls refused.')
