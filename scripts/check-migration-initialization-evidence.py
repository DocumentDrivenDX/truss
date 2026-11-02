#!/usr/bin/env python3
"""Compare original native captures without changing migration admission."""
import argparse
from hashlib import sha256
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def qualify(expected, observed):
    if expected.keys() != observed.keys():
        raise ValueError('Native inventory surfaces changed')
    changes = []
    for surface, rows in expected.items():
        actual = observed[surface]
        if rows == actual:
            continue
        if surface != 'relations' or len(rows) != len(actual):
            raise ValueError('Native difference outside original horizon relation')
        for before, after in zip(rows, actual, strict=True):
            if before == after:
                continue
            if (before[0] != 'journal_runtime_horizon'
                    or before[:7] + before[8:] != after[:7] + after[8:]):
                raise ValueError('Native difference outside original horizon bounds')
            changes.append({'before': before, 'after': after})
    if len(changes) > 1:
        raise ValueError('Multiple horizon changes')
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    migration = root / 'packages/python/src/truss/_migrations'
    manifest_raw = (migration / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    result = []
    for label, wheel in manifest['sourceWheels'].items():
        path = args.captures / (label + '-native-inventory.json')
        if not path.exists():
            raise ValueError('Missing original native capture: ' + label)
        raw = path.read_bytes()
        capture = json.loads(raw)
        if capture['source'] != label:
            raise ValueError('Original capture source mismatch')
        digest = wheel['runtimeManifestSha256']
        profile_raw = (migration / (digest + '.json')).read_bytes()
        if sha256(profile_raw).hexdigest() != manifest['files'][digest + '.json']:
            raise ValueError('Frozen native profile integrity failure')
        changes = qualify(json.loads(profile_raw)['inventory'], capture['inventory'])
        result.append({'source': label, 'runtimeManifestSha256': digest,
                       'wheelSha256': wheel['sha256'],
                       'captureSha256': sha256(raw).hexdigest(),
                       'inventorySha256': sha256(canonical(capture['inventory'])).hexdigest(),
                       'changes': changes})
    print(json.dumps({'manifestSha256': sha256(manifest_raw).hexdigest(),
                      'scope': 'Exact native definition comparison only; no admission or migration qualification',
                      'sources': result}, indent=2))


if __name__ == '__main__':
    main()
