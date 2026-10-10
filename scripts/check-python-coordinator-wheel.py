#!/usr/bin/env python3
"""Installed-wheel coordinator controls with synthetic host; no native authority."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import truss._query_execution as coordinator
root = Path(__file__).resolve().parents[1]
loaded = Path(coordinator.__file__).resolve()
assert loaded.is_relative_to(Path(sys.prefix).resolve()) and not loaded.is_relative_to(root)
delivery_path = root / 'docs/helix/04-build/evidence/design-audit/python-weft-coordinator-wheel-component.json'
delivery = json.loads(delivery_path.read_bytes())
modules = delivery['trussWheelDelivery']['modules']
expected = next(m['sha256'] for m in modules if m['path'] == 'truss/_query_execution.py')
assert hashlib.sha256(loaded.read_bytes()).hexdigest() == expected
result = subprocess.run([sys.executable, '-W', 'error', '-m', 'unittest', 'discover',
 '-s', str(root/'packages/python/tests'), '-p', 'test_query_execution.py', '-v'],
 cwd=Path(sys.prefix), capture_output=True, text=True, timeout=60)
assert result.returncode == 0, result.stdout + result.stderr
assert 'Ran 11 tests' in result.stderr and result.stderr.rstrip().endswith('OK')
sources = ['packages/python/tests/test_query_execution.py', 'packages/python/tests/test_weft.py']
receipt = {
 'scope': 'Installed current base wheel and synthetic-host coordinator controls only',
 'loadedCoordinator': str(loaded), 'coordinatorSha256': expected,
 'deliveryReceiptSha256': hashlib.sha256(delivery_path.read_bytes()).hexdigest(),
 'python': sys.version, 'tests': 11, 'output': result.stdout + result.stderr,
 'sources': [{'path': p, 'sha256': hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in sources],
 'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'nativeDatabaseExecuted': False, 'originalSecurityAuthorityQualified': False,
 'completePythonEngineQualified': False,
}
(root/'docs/helix/04-build/evidence/design-audit/python-coordinator-installed-controls.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({'installedModules': len(modules), 'tests': 11, 'completePythonEngineQualified': False}))
