"""Retain supported-driver epoch-cut component evidence; no backend acceptance."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,uuid
import psycopg
from psycopg import pq
root=Path.cwd();out=root/'docs/helix/04-build/evidence/python-psycopg-epoch-cut'/str(uuid.uuid4());out.mkdir(parents=True)
paths=list((root/'packages/python/src/truss').glob('*.py'))
paths += [root/p for p in ('packages/python/tests/test_psycopg_epoch_cut_native.py','packages/python/tests/test_psycopg_host_native.py','scripts/check-python-psycopg-epoch-cut-native.py','scripts/check-module-boundaries.py','docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql')]
paths += [root/f'packages/postgresql/native/{n}.sql' for n in ('source-epoch-immutability','source-epoch-lock','source-epoch-issue','source-epoch-fresh-lock','source-epoch-read-fence','source-epoch-fenced-fresh-lock','source-epoch-routine-ddl-barrier')]
pins={}
for p in paths:
 raw=p.read_bytes();name=str(p.relative_to(root));pins[name]=hashlib.sha256(raw).hexdigest();dest=out/'preimages'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
binary_root=Path(os.environ['TRUSS_CENSUS_POSTGRES_BIN']).parent
binary_pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in binary_root.rglob('*') if p.is_file()}
env=dict(os.environ,PYTHONPATH='packages/python/src:packages/python/tests',TRUSS_PSYCOPG_EPOCH_EVIDENCE=str(out))
result=subprocess.run([sys.executable,'-m','unittest','test_psycopg_epoch_cut_native','test_psycopg_host_native','-v'],env=env,capture_output=True,text=True,timeout=90)
(out/'native.stdout.log').write_text(result.stdout);(out/'native.stderr.log').write_text(result.stderr)
boundary=subprocess.run([sys.executable,'scripts/check-module-boundaries.py'],capture_output=True,text=True,timeout=60)
(out/'boundaries.stdout.log').write_text(boundary.stdout);(out/'boundaries.stderr.log').write_text(boundary.stderr)
unchanged=all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in pins.items())
cleanup=json.loads((out/'cleanup.json').read_text()) if (out/'cleanup.json').exists() else None
passed=(result.returncode==0 and 'Ran 34 tests' in result.stderr and 'skipped' not in result.stderr and boundary.returncode==0 and unchanged and cleanup=={'stopExitCode':0,'statusExitCode':3,'socketAbsent':True})
receipt={'status':'component-passed' if passed else 'component-failed','sourceDigests':pins,'nativeBinaryDigests':binary_pins,'nativeExitCode':result.returncode,'boundaryExitCode':boundary.returncode,'sourceUnchanged':unchanged,'cleanup':cleanup,'python':sys.version,'psycopg':psycopg.__version__,'implementation':pq.__impl__,'libpq':pq.version(),'server':160015,'tests':34,'scope':'Eight original supported-driver epoch-cut composition controls plus26 adoption regressions. Administrative original comparison/installed fixture only. Callback guarded by original host lease/savepoint and fresh native epoch SHARE acquisition; no persisted capability. Does not qualify full source/authority/data cuts, authenticated caller/issuer, installed source ACL closure, arbitrary callbacks, independent dependency/package delivery, complete protected executor, commit recovery or final disclosure.'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'evidence':str(out)}))
if not passed:raise SystemExit(1)
