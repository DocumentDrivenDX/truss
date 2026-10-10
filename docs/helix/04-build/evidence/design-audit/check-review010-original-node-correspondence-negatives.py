"""Independent source-custody corruptions in disposable copied input trees."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[5]
BASE = 'docs/helix/04-build/evidence/design-audit/'
SCRIPT = ROOT / (BASE + 'find-review010-original-node-correspondence.py')
manifest = json.loads((ROOT / (BASE + 'review010-prior-identity-catalogs.json')).read_bytes())
composition = json.loads((ROOT / (BASE + 'migration-homes-layout-profile-composition.json')).read_bytes())
paths = {BASE + 'review010-prior-identity-catalogs.json',
         BASE + 'migration-homes-layout-profile-composition.json', composition['modelPath']}
for catalog in manifest['catalogs']:
    paths.add(catalog['path'])
    for entry in json.loads((ROOT / catalog['path']).read_bytes())['entries']:
        loc = entry['capturedModelLocator']
        paths.add(loc.get('modelPath', loc.get('model')))

for case in ('selected_model', 'original_model', 'catalog', 'node_locator'):
    with tempfile.TemporaryDirectory(prefix='truss-correspondence-') as tmp:
        root = Path(tmp)
        for path in paths:
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, root / path)
        catalog = manifest['catalogs'][0]
        data = json.loads((root / catalog['path']).read_bytes())
        if case == 'node_locator':
            data['entries'][0]['capturedModelLocator']['jsonPointer'] += '/members/relation'
            b = json.dumps(data).encode()
            (root / catalog['path']).write_bytes(b)
            m = json.loads((root / (BASE + 'review010-prior-identity-catalogs.json')).read_bytes())
            m['catalogs'][0]['sha256'] = hashlib.sha256(b).hexdigest()
            (root / (BASE + 'review010-prior-identity-catalogs.json')).write_text(json.dumps(m))
            expected = 'original node substitution'
        else:
            target = composition['modelPath'] if case == 'selected_model' else catalog['path'] if case == 'catalog' else data['entries'][0]['capturedModelLocator']['modelPath']
            with (root / target).open('ab') as out:
                out.write(b' ')
            expected = 'source hash mismatch'
        run = subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True)
        if run.returncode == 0 or expected not in run.stderr:
            raise AssertionError(case + ': wrong refusal: ' + run.stderr)
        print(case + ': rejected ' + expected)
