#!/usr/bin/env python3
"""Install the selected released runtime; refuse source fallback and bad checksums."""
import argparse,hashlib,importlib.metadata,json,subprocess,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
profile=json.loads((ROOT/'packages/python/src/truss/_profiles/local-postgres-runtime.json').read_text())
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--wheelhouse',type=Path,default=ROOT/'.cache/pgserver'/('pg'+profile['serverVersion'])/'wheels')
p.add_argument('--truss-wheel',type=Path)
p.add_argument('--download-only',action='store_true')
a=p.parse_args()
for retired in ('pgserver','pgserver-pg16','pgserver-pg17'):
 try:importlib.metadata.version(retired)
 except importlib.metadata.PackageNotFoundError:continue
 raise RuntimeError('Use a fresh environment or uninstall conflicting distribution: '+retired)
a.wheelhouse.mkdir(parents=True,exist_ok=True)
release=profile['repository']+'/releases/';listing=release+'expanded_assets/'+profile['releaseTag']
subprocess.run([sys.executable,'-m','pip','download','--only-binary=:all:','--no-index','--no-deps','--find-links',listing,'--dest',str(a.wheelhouse),profile['distribution']+'=='+profile['distributionVersion']],check=True)
with urllib.request.urlopen(release+'download/'+profile['releaseTag']+'/SHA256SUMS',timeout=30) as response:checksums=response.read()
entries={line.split()[1]:line.split()[0] for line in checksums.decode().splitlines()}
wheels=list(a.wheelhouse.glob(profile['distribution'].replace('-','_')+'-'+profile['distributionVersion']+'-*.whl'))
if not wheels:raise RuntimeError('No released compatible wheel; source builds are disabled')
for wheel in wheels:
 if hashlib.sha256(wheel.read_bytes()).hexdigest()!=entries.get(wheel.name):raise RuntimeError('Released wheel checksum mismatch; remove stale or preliminary cache: '+str(wheel))
(a.wheelhouse/'SHA256SUMS').write_bytes(checksums)
print(json.dumps({'release':listing,'wheels':[str(w) for w in wheels],'checksumsVerified':True}),flush=True)
if not a.download_only:
 target=str(a.truss_wheel.resolve()) if a.truss_wheel else str(ROOT/'packages/python')
 # Truss's own pure-Python wheel may be built; every dependency must be binary.
 subprocess.run([sys.executable,'-m','pip','install','--only-binary=:all:','--find-links',str(a.wheelhouse),target+'[local,native,experimental-pg8000]'],check=True)
 subprocess.run([sys.executable,'-m','pip','install','--only-binary=:all:','--no-index','--no-deps','--force-reinstall','--find-links',str(a.wheelhouse),profile['distribution']+'=='+profile['distributionVersion']],check=True)
 subprocess.run([sys.executable,'-m','pip','check'],check=True)
