"""Exercise the document audit against isolated corruptions, never editing source artifacts."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
checks = []
with tempfile.TemporaryDirectory(prefix='truss-design-audit-') as folder:
    target = Path(folder) / 'helix'
    shutil.copytree(ROOT, target)
    plan = next((target / '03-test/test-plans').glob('STP-009-*'))
    original = plan.read_text()
    row = next(line for line in original.splitlines() if line.startswith('| US-009-AC1 |'))
    for name, content, expected in [
        ('valid inventory', original, 0),
        ('duplicate primary allocation', original.replace(row, row + '\n' + row), 1),
        ('missing allocation', original.replace(row, ''), 1),
        ('missing citation', original.replace('@covers US-009-AC1', 'no citation'), 1),
        ('undeclared criterion', original.replace('US-009-AC1', 'US-009-AC99'), 1),
    ]:
        plan.write_text(content)
        result = subprocess.run([sys.executable, str(HERE / 'coverage.py'), str(target)], capture_output=True, text=True)
        report = json.loads(result.stdout)
        if result.returncode != expected:
            raise AssertionError((name, result.returncode, report.get('errors'), result.stderr))
        checks.append({'case': name, 'exitCode': result.returncode, 'errors': report['errors']})
print(json.dumps({'scope': 'audit rejection behavior only', 'checks': checks}, indent=2))
