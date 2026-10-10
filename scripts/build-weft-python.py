"""Build the original frozen Weft Python extension, never working-tree sources."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile

revision = 'f05f2df09e9c2494ac8c6d703dfe38413dbc4181'
if len(sys.argv) != 5:
 raise SystemExit('usage: build-weft-python.py REPOSITORY OUTPUT TOOLCHAIN_ROOT PYTHON')
repository, output, toolchain, python = map(Path, sys.argv[1:])
output = output.resolve()
if output.exists() and any(output.iterdir()):
 raise SystemExit('Output must be empty to prevent source substitution')
output.mkdir(parents=True, exist_ok=True)
archive = subprocess.check_output(['git','-C',str(repository),'archive',revision])
if hashlib.sha256(archive).hexdigest() != '1784d4283b4060c39af2dee6a283472cd539eacc119abb8576a57ae106fb51ea':
 raise SystemExit('Frozen source archive differs from original Truss compiler build')
with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
 for member in tree.getmembers():
  if member.name.startswith('/') or '..' in PurePosixPath(member.name).parts or member.issym() or member.islnk():
   raise SystemExit('Unsafe source archive member')
 tree.extractall(output)
maturin = toolchain / 'venv/bin/maturin'
assert subprocess.check_output([str(maturin),'--version'],text=True).strip() == 'maturin 1.9.6'
env = dict(os.environ,CARGO_HOME=str(toolchain/'cargo'),RUSTUP_HOME=str(toolchain/'rustup'))
env['PATH'] = str(toolchain/'cargo/bin') + os.pathsep + env.get('PATH','')
subprocess.run([str(maturin),'build','--manifest-path','crates/weft-python/Cargo.toml',
 '--locked','--offline','--release','--features','truss-postgresql-qualified',
 '--interpreter',str(python),'--out',str(output/'dist')],cwd=output,env=env,check=True)
wheels = list((output/'dist').glob('*.whl'))
assert len(wheels) == 1
wheel = wheels[0]
source_paths = ['crates/weft-python/src/lib.rs','crates/weft-python/Cargo.toml',
 'crates/weft-python/pyproject.toml','Cargo.lock']
receipt = {
 'revision':revision,'sourceArchiveSha256':hashlib.sha256(archive).hexdigest(),
 'features':['truss-postgresql-qualified'],'maturin':'1.9.6',
 'rust':subprocess.check_output([str(toolchain/'cargo/bin/rustc'),'--version'],env=env,text=True).strip(),
 'python':subprocess.check_output([str(python),'--version'],text=True).strip(),
 'buildOptions':['locked','offline','release'],
 'sources':[{'path':p,'sha256':hashlib.sha256((output/p).read_bytes()).hexdigest()} for p in source_paths],
 'wheel':{'path':str(wheel),'filename':wheel.name,'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest()},
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'qualification':'Original pinned Python extension build only; no Truss host or native database qualification',
}
(output/'truss-weft-python-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
