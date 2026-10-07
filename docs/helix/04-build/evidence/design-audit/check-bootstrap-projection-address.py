"""Synthetic pointer experiment, not a production projection or native admission parser."""
from pathlib import Path
import hashlib, json, re
root = Path(__file__).resolve().parents[3]
path = root / '02-design/contracts/bindings/bootstrap-projection-address-v0.1.vectors.json'
raw = path.read_bytes()
if len(raw) > 32768:
    raise ValueError('experiment fixture bound')
fixture = json.loads(raw)
def resolve(basis, pointer):
    if len(pointer.encode('utf-8')) > 4096:
        raise ValueError('experiment path bound')
    if pointer == '':
        return [], basis
    if not pointer.startswith('/'):
        raise ValueError('string pointer required')
    encoded = pointer[1:].split('/')
    if len(encoded) > 128:
        raise ValueError('experiment depth bound')
    tokens = []
    for token in encoded:
        if re.search(r'~(?![01])', token):
            raise ValueError('escape')
        tokens.append(token.replace('~1', '/').replace('~0', '~'))
    value = basis
    for token in tokens:
        if type(value) is dict:
            if token not in value:
                raise ValueError('missing own member')
            value = value[token]
        elif type(value) is list:
            if re.fullmatch(r'0|[1-9][0-9]*', token) is None:
                raise ValueError('index grammar')
            maximum = str(len(value) - 1)
            if not value or len(token) > len(maximum) or (len(token) == len(maximum) and token > maximum):
                raise ValueError('index range before conversion')
            value = value[int(token)]
        else:
            raise ValueError('scalar traversal')
    return tokens, value
ids = set()
for case in fixture['vectors']:
    if case['id'] in ids:
        raise ValueError('duplicate fixture identity')
    ids.add(case['id'])
    try:
        tokens, value = resolve(fixture['basis'], case['pointer'])
        observed = {'kind': 'resolved', 'tokens': tokens, 'value': value}
    except ValueError:
        observed = {'kind': 'refused'}
    if observed != case['expected']:
        raise ValueError('fixture disagreement: ' + case['id'])
if path.read_bytes() != raw:
    raise ValueError('fixture changed during experiment')
result = {'status': 'pass', 'cases': len(ids), 'fixtureSha256': hashlib.sha256(raw).hexdigest(),
          'scope': fixture['scope'], 'nativeExecuted': False, 'profileAdopted': False,
          'notCovered': ['accessor/prototype rejection in JavaScript', 'resource producer qualification',
                         'original native fact custody', 'contribution membership/merge', 'complete installation basis']}
Path(__file__).with_name('bootstrap-projection-address-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'cases': result['cases']}))
