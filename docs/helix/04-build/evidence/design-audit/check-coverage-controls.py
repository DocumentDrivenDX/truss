"""Independent corruption controls for document allocation; not runtime coverage."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[3]
scanner = Path(__file__).with_name('coverage.py')
results = []
for control in ['original', 'missing TD', 'missing STP', 'missing declaration section',
                'duplicate criterion', 'missing primary allocation', 'empty inventory']:
    with tempfile.TemporaryDirectory(prefix='truss-coverage-control-') as temporary:
        candidate = Path(temporary)
        for directory in ['01-frame/user-stories', '02-design/technical-designs', '03-test/test-plans']:
            shutil.copytree(root / directory, candidate / directory)
        story = next((candidate / '01-frame/user-stories').glob('US-001-*.md'))
        plan = next((candidate / '03-test/test-plans').glob('STP-001-*.md'))
        if control == 'missing TD':
            next((candidate / '02-design/technical-designs').glob('TD-001-*.md')).unlink()
        elif control == 'missing STP':
            plan.unlink()
        elif control == 'missing declaration section':
            story.write_text(story.read_text().replace('## Acceptance Criteria\n', '## Removed Declaration\n'))
        elif control == 'duplicate criterion':
            story.write_text(story.read_text().replace('## Acceptance Criteria\n', '## Acceptance Criteria\n\n- [ ] **US-001-AC1** — duplicate\n'))
        elif control == 'missing primary allocation':
            plan.write_text('\n'.join(line for line in plan.read_text().split('\n') if not line.startswith('| US-001-AC1 |')))
        elif control == 'empty inventory':
            for file in (candidate / '01-frame/user-stories').glob('US-*.md'):
                file.unlink()
        for optimized in [False, True]:
            command = [sys.executable, *(['-O'] if optimized else []), str(scanner), str(candidate)]
            run = subprocess.run(command, text=True, capture_output=True)
            try:
                observation = json.loads(run.stdout)
            except json.JSONDecodeError:
                raise RuntimeError(f'{control}: scanner produced no structured observation: {run.stderr}')
            expected_pass = control == 'original'
            passed = (run.returncode == 0) == expected_pass and bool(observation['errors']) != expected_pass
            if expected_pass:
                passed = passed and observation['stories'] == 45 and observation['criteria'] == 167 and observation['pairsWithAllReferences'] == 45
            results.append({'control': control, 'optimized': optimized, 'passed': passed, 'errors': observation['errors']})
receipt = {'scope': 'document allocation corruption sensitivity only; no semantic/native coverage', 'controls': len(results), 'failures': [r for r in results if not r['passed']], 'results': results}
Path(__file__).with_name('coverage-controls.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ['scope', 'controls', 'failures']}, indent=2))
if receipt['failures']:
    raise SystemExit(1)
