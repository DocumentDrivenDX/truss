"""Recheck published byte fixtures, not a production canonicalizer."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
bindings = root / '02-design/contracts/bindings'
outcomes = []
for name in ('canonical-byte-v0.1.vectors.json', 'canonical-input-v0.1.vectors.json'):
    artifact = json.loads((bindings / name).read_text())
    for vector in artifact['vectors']:
        raw = bytes.fromhex(vector['canonicalUtf8Hex'])
        tree = json.loads(raw.decode('utf-8'))
        if 'canonicalUtf8' in vector:
            assert vector['canonicalUtf8'].encode('utf-8') == raw
        preimage = (artifact['profile'] + '\n' + vector['domain'] + '\n').encode('ascii') + raw
        assert hashlib.sha256(preimage).hexdigest() == vector['sha256'], vector['name']
        outcomes.append({'artifact': name, 'vector': vector['name'], 'digestMatches': True})
    if name == 'canonical-input-v0.1.vectors.json':
        vectors = artifact['vectors']
        assert vectors[1]['canonicalUtf8Hex'] == vectors[3]['canonicalUtf8Hex']
        assert vectors[1]['sha256'] != vectors[3]['sha256']
        assert vectors[1]['sha256'] != vectors[2]['sha256']
print(json.dumps({'scope': 'Published UTF-8/digest integrity and domain separation only; no canonical encoder or semantic qualification', 'cases': len(outcomes), 'outcomes': outcomes}, indent=2))
