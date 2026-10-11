"""Verify the merged wheel without repeating unchanged focused test groups."""
import hashlib,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
import truss
from truss import LocalPostgres
from truss._runtime_profile import RUNTIME_DISTRIBUTION,RUNTIME_VERSION,SERVER_VERSION
root=Path(__file__).resolve().parents[5]
original,final,out=map(Path,sys.argv[1:])
if out.exists():raise RuntimeError('Use a fresh receipt')
covered=['truss/'+n+'.py' for n in ('__init__','local_runtime','psycopg_host','execution','_runtime_profile')]+['truss/_profiles/local-postgres-runtime.json']
unchanged={}
with zipfile.ZipFile(original) as before,zipfile.ZipFile(final) as after:
 for name in covered:
  assert before.read(name)==after.read(name),name
  unchanged[name]=hashlib.sha256(after.read(name)).hexdigest()
 loaded=Path(truss.__file__).resolve().parent
 members=[n for n in after.namelist() if n.startswith('truss/') and not n.endswith('/')]
 for name in members:assert (loaded.parent/name).read_bytes()==after.read(name),name
with tempfile.TemporaryDirectory(prefix='truss-final-wheel-',dir='/tmp') as folder:
 data=Path(folder)/'data'
 with LocalPostgres(data) as server:
  query=subprocess.check_output([str(server.psql_path),server.info.connection_uri,'-X','-A','-t','-v','ON_ERROR_STOP=1','-c',"SELECT current_setting('server_version'),current_setting('listen_addresses'),1"],text=True).strip()
  assert query==SERVER_VERSION+'||1',query
 assert not (data/'postmaster.pid').exists()
receipt={'passed':True,'sourceRevision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'runtimeDistribution':RUNTIME_DISTRIBUTION,'runtimeVersion':RUNTIME_VERSION,'postgresql':SERVER_VERSION,'wheelSha256':hashlib.sha256(final.read_bytes()).hexdigest(),'installedPayloadMembers':len(members),'functionalSourceUnchangedFromFocusedSmoke':unchanged,'nativeProbe':query,'ownedPostmasterStopped':True,'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Final merged artifact payload verification and native startup/query/shutdown; six focused groups retain their original tested wheel hash. Concurrent security changes outside these exercised runtime/driver modules retain separate evidence.'}
out.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'passed':True,'wheelSha256':receipt['wheelSha256']}))
