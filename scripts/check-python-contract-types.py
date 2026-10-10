#!/usr/bin/env python3
"""Run pinned mypy against public consumers; negative markers are exact or fail.

Usage: mypy-environment-python scripts/check-python-contract-types.py PACKAGE_ROOT
PACKAGE_ROOT may be the source root or an installed wheel target.
"""
import os
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
package = Path(sys.argv[1]).resolve()
if not (package / 'truss' / 'py.typed').is_file():
    raise SystemExit('Missing installed typing marker')
fixtures = root / 'packages/python/tests/typing'
env = dict(os.environ, MYPYPATH=str(package))
for name, negative in [('group_consumer.py', False), ('group_consumer_invalid.py', True), ('import_consumer.py', False), ('import_consumer_invalid.py', True)]:
    path = fixtures / name
    result = subprocess.run([sys.executable, '-m', 'mypy', '--strict', '--follow-imports=silent', str(path)], env=env, cwd='/private/tmp', text=True, capture_output=True)
    errors = {int(n) for n in re.findall(r':(\d+): error:', result.stdout)}
    expected = {i for i, line in enumerate(path.read_text().splitlines(), 1) if '# bad_' in line}
    if (not negative and result.returncode != 0) or (negative and (result.returncode != 1 or errors != expected)):
        print(result.stdout + result.stderr)
        raise SystemExit('Consumer typing mismatch')
    print(f'{name}: {len(errors)} expected errors')
