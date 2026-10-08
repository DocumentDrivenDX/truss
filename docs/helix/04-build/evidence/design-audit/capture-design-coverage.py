"""Capture/check exact document-allocation evidence; never adopts design or runtime support."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

here = Path(__file__).resolve().parent
root = here.parents[2]
scanner = here / 'coverage.py'
expectation = here / 'expected-design-scope.json'
receipt_path = here / 'coverage-current-design.json'
if sys.argv[1:] not in ([], ['--check']):
    raise SystemExit('usage: capture-design-coverage.py [--check]')
run = subprocess.run([sys.executable, str(scanner), str(root), str(expectation)], text=True, capture_output=True)
if run.returncode:
    sys.stderr.write(run.stdout + run.stderr)
    raise SystemExit('allocation refused; receipt not written')
receipt = json.loads(run.stdout)
if receipt['errors']:
    raise SystemExit('scanner reported errors; receipt not written')
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
receipt['artifactSha256'] = {name: digest(root / name) for row in receipt['inventory'] for name in row['artifacts'].values()}
receipt['storySha256'] = {str(p.relative_to(root)): digest(p) for p in sorted((root / '01-frame/user-stories').glob('US-*.md'))}
receipt['producerSha256'] = digest(Path(__file__))
receipt['scannerSha256'] = digest(scanner)
receipt['expectationPath'] = str(expectation.relative_to(root))
if sys.argv[1:] == ['--check']:
    retained = json.loads(receipt_path.read_text())
    if retained != receipt:
        raise SystemExit('stale or substituted allocation receipt; recapture after scope/design review')
else:
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'mode': 'check' if sys.argv[1:] else 'capture', 'stories': receipt['stories'], 'criteria': receipt['criteria'], 'artifactsPinned': len(receipt['artifactSha256']), 'expectedScopeSha256': receipt['expectedScopeSha256'], 'scope': receipt['scope']}, indent=2))
