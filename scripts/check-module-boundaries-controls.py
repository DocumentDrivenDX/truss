#!/usr/bin/env python3
"""Exercise the real checker subprocess against disposable source mutations."""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / 'scripts/check-module-boundaries.py'
SOURCE = ROOT / 'packages/python/src/truss'


def run(source):
    process = subprocess.run([sys.executable, str(CHECKER), '--source', str(source), '--json'],
                             text=True, capture_output=True, timeout=30)
    result = json.loads(process.stdout)
    if process.returncode != (0 if result['passed'] else 1):
        raise AssertionError('Checker status/result mismatch')
    return result


def main():
    baseline = run(SOURCE)
    if not baseline['passed']:
        raise AssertionError(baseline['errors'])
    cases = [
        ('allowed-nested-import', 'numeric.py', '\ndef fixture():\n    from decimal import Decimal\n', None),
        ('forbidden-driver', 'numeric.py', '\ndef fixture():\n    import pgserver\n', 'forbidden import pgserver'),
        ('private-custody-access', 'numeric.py', '\nfrom ._operation_admission import AdmissionCustody\n', 'forbidden import truss._operation_admission'),
        ('absolute-private-access', 'cli.py', '\nfrom truss import _operation_admission\n', 'forbidden import truss._operation_admission'),
        ('escape-package', 'numeric.py', '\nfrom ..host import Driver\n', 'import escapes package'),
        ('dynamic-import', 'numeric.py', '\n__import__("pgserver")\n', 'dynamic source/import execution'),
        ('import-cycle', 'local_runtime.py', '\nfrom . import cli\n', 'Python import cycle'),
        ('unmapped-source', 'new_runtime.py', 'import subprocess\n', 'unmapped module'),
        ('wildcard', 'numeric.py', '\nfrom decimal import *\n', 'wildcard import'),
    ]
    observed = []
    for label, filename, addition, expected in cases:
        with tempfile.TemporaryDirectory(prefix='truss-module-control-') as temporary:
            source = Path(temporary) / 'truss'
            shutil.copytree(SOURCE, source, ignore=shutil.ignore_patterns('__pycache__'))
            path = source / filename
            path.write_text((path.read_text() if path.exists() else '') + addition)
            result = run(source)
            if expected is None:
                if not result['passed']:
                    raise AssertionError((label, result['errors']))
            elif result['passed'] or not any(expected in error for error in result['errors']):
                raise AssertionError((label, result))
            observed.append({'case': label, 'passed': result['passed'], 'errors': result['errors']})
    print(json.dumps({'scope': 'python-only', 'observedAt': datetime.now(timezone.utc).isoformat(),
                      'pythonVersion': sys.version.split()[0],
                      'checkerSha256': hashlib.sha256(CHECKER.read_bytes()).hexdigest(),
                      'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      'sourceSha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                       for path in sorted(SOURCE.rglob('*.py'))},
                      'baselineEdges': baseline['edgeCount'],
                      'controls': observed, 'controlCount': len(observed)}, sort_keys=True))


if __name__ == '__main__':
    main()
