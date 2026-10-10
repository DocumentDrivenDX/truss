#!/usr/bin/env python3
"""Run the actual compiler inventory against disposable known import graphs."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / 'scripts/inspect-typescript-boundaries.ts'


def fixture(root, index):
    for package in ('portable', 'adapter'):
        home = root / 'packages' / package
        (home / 'src').mkdir(parents=True)
        (home / 'package.json').write_text(json.dumps({'name': '@fixture/' + package}))
        (home / 'src/index.ts').write_text(index if package == 'adapter' else 'export const value = 1;\n')
    (root / 'packages/portable/src/private.ts').write_text('export type Internal = string;\n')


def main():
    cases = [
        ('public-and-private', '''import {value} from '@fixture/portable';
export {value} from '../../portable/src/index';
import type {Internal} from '../../portable/src/private';
const text = "import {fake} from './missing'";
// import {fake} from './missing'
''', 0, 3, 1, 0, 0),
        ('dynamic-literal-and-computed', '''const known = import('../../portable/src/index');
const computed = import('data:' + 'fixture');
''', 0, 1, 0, 0, 1),
        ('unresolved-local', "export {missing} from './missing';\n", 1, 1, 0, 1, 0),
    ]
    observations = []
    for name, source, status, edge_count, private_count, unresolved_count, dynamic_count in cases:
        with tempfile.TemporaryDirectory(prefix='truss-ts-inventory-control-') as temporary:
            root = Path(temporary)
            fixture(root, source)
            output = root / 'receipt.json'
            run = subprocess.run(['bun', str(SCANNER), str(output), str(root)],
                                 text=True, capture_output=True, timeout=30)
            if run.returncode != status:
                raise AssertionError((name, run.returncode, run.stderr))
            receipt = json.loads(output.read_text())
            actual = (receipt['edgeCount'], len(receipt['privateCrossPackage']),
                      len(receipt['unresolvedLocal']), len(receipt['dynamic']))
            if actual != (edge_count, private_count, unresolved_count, dynamic_count):
                raise AssertionError((name, actual))
            observations.append({'case': name, 'exitStatus': run.returncode,
                                 'edges': edge_count, 'privateEdges': private_count,
                                 'unresolvedLocal': unresolved_count, 'dynamicReview': dynamic_count})
    print(json.dumps({'scope': 'compiler inventory controls; not boundary enforcement',
                      'scannerSha256': hashlib.sha256(SCANNER.read_bytes()).hexdigest(),
                      'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      'cases': observations}, sort_keys=True))


if __name__ == '__main__':
    main()
