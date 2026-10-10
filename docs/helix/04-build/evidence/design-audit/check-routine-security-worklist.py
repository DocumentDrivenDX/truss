"""Selected source worklist consistency only, not complete callable or native closure."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
REL = 'docs/helix/02-design/contracts/reference-routine-security-worklist.proposal.json'
raw = (ROOT / REL).read_bytes()
d = json.loads(raw)
for source in d['sourcePins']:
    b = (ROOT / 'docs/helix' / source['path']).read_bytes()
    if hashlib.sha256(b).hexdigest() != source['sha256']:
        raise ValueError('source drift: ' + source['path'])
expected = []
for source in d['sourcePins'][:2]:
    manifest = json.loads((ROOT / 'docs/helix' / source['path']).read_text())
    for routine in manifest['routines']:
        expected.append((routine.get('originalContractName', routine.get('selector')),
            routine.get('sqlArgumentTypes', [p['type'] for p in routine.get('parameters', [])]),
            routine.get('resultType', routine.get('returns')), routine['ownerResponsibility'], source['path']))
entries = d['entries']
if len(entries) != 16 or d['knownRoutineCount'] != 16 or len({r['selector'] for r in entries}) != 16:
    raise ValueError('selected membership count/collision')
for routine, (name, args, result, owner, source) in zip(entries[:12], expected):
    if (routine['selector'], routine['argumentTypes'], routine['resultType'], routine['ownerResponsibility'], routine['sourceManifest']) != (name, args, result, owner, source):
        raise ValueError('original manifest correspondence: ' + name)
contract = (ROOT / 'docs/helix' / d['sourcePins'][2]['path']).read_text()
if [r['selector'] for r in entries[12:]] != ['row_touch_reserve', 'row_touch_seal', 'row_touch_cleanup', 'row_journal_stage_cleanup']:
    raise ValueError('original custody membership')
for routine in entries[12:]:
    signature = routine['originalSignature']
    if '`' + signature + '`' not in contract:
        raise ValueError('original signature absent')
    argument_text, result = signature.split('(', 1)[1].split(') -> ')
    arguments = [part.strip().rsplit(' ', 1)[1] for part in argument_text.split(',')]
    if arguments != routine['argumentTypes'] or result != routine['resultType']:
        raise ValueError('signature reduction changed')
for routine in entries:
    if routine['nativeRoleBinding'] is not None or routine['effectivePrivilegeEvidence'] is not None:
        raise ValueError('unreviewed native binding substituted')
if d['nativeQualified'] is not False or d['installerReady'] is not False or not d['remainingScope']:
    raise ValueError('source worklist cannot imply closure')
receipt = {'scope': __doc__, 'worklistSha256': hashlib.sha256(raw).hexdigest(),
           'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'sourcePins': d['sourcePins'], 'knownMembership': 16,
           'originalManifestEntries': 12, 'originalCustodySignatures': 4,
           'sourceCorrespondence': True, 'nativeQualified': False, 'completeCallableClosure': False}
(ROOT / 'docs/helix/04-build/evidence/design-audit/routine-security-worklist-source.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Sixteen known source signatures verified; native and complete-callable closure remain unqualified.')
