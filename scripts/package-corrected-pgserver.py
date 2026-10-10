#!/usr/bin/env python3
"""Package the pinned private corrected candidate; never publish or adopt it."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
inputs = json.loads((root / 'docs/helix/04-build/evidence/design-audit/pgserver-corrected-build-inputs.json').read_text())
if len(sys.argv) != 3:
    raise SystemExit('usage: package-corrected-pgserver.py SOURCE_CHECKOUT NEW_WHEEL_DIRECTORY')
source, output = (Path(value).resolve() for value in sys.argv[1:])
if output.exists():
    raise RuntimeError('Use a new output directory; never overwrite an earlier wheel')

def run(arguments):
    return subprocess.check_output(arguments, cwd=source, text=True).strip()

def sha(data):
    return hashlib.sha256(data).hexdigest()

if run(['git', 'rev-parse', 'HEAD']) != inputs['pgserverRevision']:
    raise RuntimeError('Original pgserver revision drift')
if sha(subprocess.check_output(['git', 'archive', 'HEAD'], cwd=source)) != inputs['pgserverSourceArchiveSha256']:
    raise RuntimeError('Original pgserver source archive drift')
if sha((source / 'pgbuild/Makefile').read_bytes()) != inputs['candidateMakefileSha256']:
    raise RuntimeError('Selected native build recipe drift')
archive = source / 'pgbuild' / ('postgresql-' + inputs['postgresqlVersion'] + '.tar.gz')
if sha(archive.read_bytes()) != inputs['postgresqlSourceSha256']:
    raise RuntimeError('Original PostgreSQL source archive drift')
for name, version in inputs['wheelBuildDependencies'].items():
    if importlib.metadata.version(name) != version:
        raise RuntimeError('Wheel build dependency drift: ' + name)

# Only the declared native recipe and distribution identity may change tracked
# upstream files. Generated installation payloads are separately inventoried.
changed = set(run(['git', 'diff', '--name-only', 'HEAD']).splitlines())
if not changed <= {'pgbuild/Makefile', 'pyproject.toml'}:
    raise RuntimeError('Undeclared upstream source changes')
tracked_python = {name for name in run(['git', 'ls-tree', '-r', '--name-only', 'HEAD', 'src/pgserver']).splitlines()
    if name.endswith('.py')}
actual_python = {str(path.relative_to(source)) for path in (source / 'src/pgserver').rglob('*.py')}
if actual_python != tracked_python:
    raise RuntimeError('Undeclared Python source membership')
for name in tracked_python:
    if (source / name).read_bytes() != subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=source):
        raise RuntimeError('Original Python source drift: ' + name)
project = source / 'pyproject.toml'
original = subprocess.check_output(['git', 'show', 'HEAD:pyproject.toml'], cwd=source)
selected = original.replace(b'version = "0.1.4"',
    ('version = "' + inputs['candidateDistributionVersion'] + '"').encode())
if selected == original or project.read_bytes() not in (original, selected):
    raise RuntimeError('Undeclared distribution metadata')
native = source / 'src/pgserver/pginstall'
if run([str(native / 'bin/postgres'), '--version']) != 'postgres (PostgreSQL) ' + inputs['postgresqlVersion']:
    raise RuntimeError('Native server version mismatch')
if (native / 'lib/vector.so').exists():
    raise RuntimeError('Candidate explicitly excludes pgvector')
project.write_bytes(selected)
output.mkdir()
subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation',
    '--wheel-dir', str(output), str(source)], check=True)
wheels = list(output.glob('*.whl'))
if len(wheels) != 1:
    raise RuntimeError('Exactly one original candidate wheel required')
wheel = wheels[0]
with zipfile.ZipFile(wheel) as package:
    names = package.namelist()
    if len(names) != len(set(names)):
        raise RuntimeError('Duplicate wheel member')
    members = []
    for name in sorted(names):
        if name.startswith('pgserver/') and not name.endswith('/'):
            payload = package.read(name)
            original_path = source / 'src' / name
            if not original_path.is_file() or original_path.read_bytes() != payload:
                raise RuntimeError('Wheel/source payload mismatch: ' + name)
            members.append({'path': name, 'bytes': len(payload), 'sha256': sha(payload)})
    for required in ('pgserver/pginstall/bin/postgres', 'pgserver/pginstall/bin/psql',
                     'pgserver/pginstall/bin/initdb', 'pgserver/pginstall/bin/pg_ctl'):
        if required not in names:
            raise RuntimeError('Required packaged executable missing: ' + required)
receipt = {'scope': 'Built private corrected pgserver candidate; installed native qualification pending',
    'inputManifestSha256': sha((root / 'docs/helix/04-build/evidence/design-audit/pgserver-corrected-build-inputs.json').read_bytes()),
    'wheel': str(wheel), 'wheelSha256': sha(wheel.read_bytes()), 'members': members,
    'projectMetadataSha256': sha(selected), 'python': sys.version,
    'producerSha256': sha(Path(__file__).read_bytes()),
    'installedQualified': False, 'completeRuntimeQualified': False}
(output / 'corrected-pgserver-wheel.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'wheel': str(wheel), 'sha256': receipt['wheelSha256'], 'members': len(members)}))
