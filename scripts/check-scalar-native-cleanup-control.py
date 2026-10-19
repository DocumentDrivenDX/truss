# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual owned Docker cleanup after a controlled lost creation response."""
from pathlib import Path
import os,json,uuid,hashlib,subprocess,tempfile,shutil,sys,zipfile
root=Path.cwd();out=root/'docs/helix/04-build/evidence/scalar-native-cleanup-control'/str(uuid.uuid4());out.mkdir(parents=True)
real=shutil.which('docker')
if not real:raise RuntimeError('Actual Docker CLI required')
sha=lambda b:hashlib.sha256(b).hexdigest()
receipt=root/'docs/helix/04-build/evidence/scalar-native-cohort/cdb1c711-7889-400b-ba83-f8a8a090176b/receipt.json'
parent=json.loads(receipt.read_text());paths=[Path(p['path']) for p in parent['sourcePreimages']]+[Path(__file__).resolve(),receipt]
for p in parent['sourcePreimages']:
 if sha(Path(p['path']).read_bytes())!=p['sha256']:raise RuntimeError('Native source changed before cleanup control')
preimages={str(p):p.read_bytes() for p in paths};tag='controlled-lost-create-'+uuid.uuid4().hex
shimCode="#!/usr/bin/python3\nimport subprocess,sys,json\nfrom pathlib import Path\nargs=sys.argv[1:]\nr=subprocess.run([REAL,*args],capture_output=True,timeout=60)\nif args and args[0]=='run' and r.returncode==0:\n Path(CAPTURE).write_text(json.dumps({'id':r.stdout.decode().strip(),'cidfile':args[args.index('--cidfile')+1],'arguments':args}))\n sys.stderr.write(TAG+'\\n');sys.exit(1)\nsys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);sys.exit(r.returncode)\n"
with tempfile.TemporaryDirectory(prefix='truss-scalar-docker-control-',dir='/private/tmp') as temporary:
 shim=Path(temporary)/'docker';capture=out/'created.json'
 shim.write_text(shimCode.replace('REAL',repr(real)).replace('CAPTURE',repr(str(capture))).replace('TAG',repr(tag)));shim.chmod(0o700)
 (out/'docker-control.py').write_bytes(shim.read_bytes())
 env=os.environ.copy();env['PATH']=temporary+os.pathsep+env['PATH']
 run=subprocess.run([sys.executable,'scripts/check-scalar-native-cohort.py'],env=env,capture_output=True,text=True,timeout=90)
 (out/'control.log').write_text(run.stdout+run.stderr)
 if run.returncode==0 or not capture.exists():raise RuntimeError('Controlled lost creation response must fail after actual creation')
 created=json.loads(capture.read_text());nativeOut=Path(created['cidfile']).parent
 if not nativeOut.resolve().is_relative_to((root/'docs/helix/04-build/evidence/scalar-native-cohort').resolve()):raise RuntimeError('Owned fixture output required')
 failure=json.loads((nativeOut/'failure.json').read_text());cleanup=failure['cleanup']
 if tag not in failure['failure'] or cleanup['containerId']!=created['id'] or cleanup['exitCode']!=0 or not cleanup['recoveredByExactNameAndLabel']:raise RuntimeError('Lost creation response cleanup correspondence failed')
 inspected=subprocess.run([real,'inspect',created['id']],capture_output=True,text=True,timeout=20)
 (out/'independent-inspect.json').write_text(json.dumps({'exitCode':inspected.returncode,'stdout':inspected.stdout,'stderr':inspected.stderr},indent=2)+'\n')
 if inspected.returncode==0 or 'no such object:' not in inspected.stderr.lower():raise RuntimeError('Exact created container still exists or removal uncertain')
if any(Path(p).read_bytes()!=b for p,b in preimages.items()):raise RuntimeError('Control input changed')
with zipfile.ZipFile(out/'sources.zip','w',zipfile.ZIP_DEFLATED) as z:
 for i,(p,b) in enumerate(preimages.items()):z.writestr(str(i)+'/'+Path(p).name,b)
result={'status':'passed','fault':'actual Docker creation succeeds; controlled CLI shim loses result and returns nonzero before wrapper assigns container ID','wrapperExitCode':run.returncode,'fixtureFailure':str(nativeOut/'failure.json'),'fixtureFailureSha256':sha((nativeOut/'failure.json').read_bytes()),'createdContainerId':created['id'],'cleanup':cleanup,'independentInspectExitCode':inspected.returncode,'independentInspectStderr':inspected.stderr,'dockerCli':real,'shimSha256':sha((out/'docker-control.py').read_bytes()),'sourcePreimages':[{'path':p,'archive':str(i)+'/'+Path(p).name,'sha256':sha(b)} for i,(p,b) in enumerate(preimages.items())],'scope':'Actual owned fixture recovery/cleanup under controlled lost successful creation response; not proof of every daemon/network timeout or native security admission','acceptancePromoted':False}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'passed','sourcePins':len(preimages),'receipt':str(out/'receipt.json'),'cleanup':cleanup['exitCode']}))
