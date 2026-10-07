"""Discover model-directory authored entry catalogs by content, not filename."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
catalogs = []
owners = collections.defaultdict(list)
for path in sorted((ROOT / 'docs/helix/02-design/models').glob('*.json')):
    data = json.loads(path.read_bytes())
    entries = data.get('entries') if isinstance(data, dict) else None
    if not isinstance(entries, list) or not any(isinstance(e, dict) and
            ('entryId' in e or ('id' in e and 'kind' in e)) for e in entries):
        continue
    ids = []
    for entry in entries:
        identity = entry.get('entryId', entry.get('id'))
        if not isinstance(identity, str) or not identity or not isinstance(entry.get('capturedModelLocator'), dict):
            raise ValueError('unhandled authored entry: ' + str(path))
        if identity in ids:
            raise ValueError('duplicate within catalog: ' + identity)
        ids.append(identity)
        owners[identity].append(str(path.relative_to(ROOT)))
    catalogs.append({'path': str(path.relative_to(ROOT)),
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'complete': data.get('complete', False), 'entryIds': ids})
result = {'scope': 'content-discovered authored entry catalogs in docs/helix/02-design/models/*.json, including physical, constraint, supporting-index, initialization and derived effects; not all repository identities or native inventory',
          'catalogs': catalogs, 'distinctIds': len(owners),
          'repeatedIds': {k: v for k, v in owners.items() if len(v) > 1},
          'review010BindingComplete': False, 'nativeQualified': False}
(ROOT / 'docs/helix/04-build/evidence/design-audit/review010-prior-identity-catalogs.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'catalogs': len(catalogs), 'distinctIds': len(owners),
                  'repeatedIds': len(result['repeatedIds'])}))
