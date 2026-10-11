#!/usr/bin/env python3
"""Focused public-release consumer verification; no full semantic-corpus claim."""
import argparse,hashlib,importlib.metadata,json,os,re,subprocess,sys,tempfile,time,zipfile
from pathlib import Path
import pgserver,truss
from truss import LocalPostgres
from truss._runtime_profile import RUNTIME_PROFILE,RUNTIME_DISTRIBUTION,RUNTIME_VERSION,SERVER_VERSION
from native_fixture import WorkerCluster
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('runtime_wheel',type=Path);p.add_argument('truss_wheel',type=Path);p.add_argument('checksums',type=Path);p.add_argument('--run-id',required=True)
a=p.parse_args()
if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',a.run_id):raise ValueError('Fresh run id required')
out=ROOT/'docs/helix/04-build/evidence/design-audit'/a.run_id;out.mkdir()
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
entries={line.split()[1]:line.split()[0] for line in a.checksums.read_text().splitlines()}
assert entries[a.runtime_wheel.name]==sha(a.runtime_wheel)
url=RUNTIME_PROFILE['repository']+'/releases/download/'+RUNTIME_PROFILE['releaseTag']+'/'+a.runtime_wheel.name
installed=importlib.metadata.distribution(RUNTIME_DISTRIBUTION)
direct=json.loads(installed.read_text('direct_url.json'));assert direct['url']==url;assert direct['archive_info']['hashes']['sha256']==sha(a.runtime_wheel)
assert installed.version==RUNTIME_VERSION
payloads={}
for wheel,package in [(a.runtime_wheel,pgserver),(a.truss_wheel,truss)]:
 loaded=Path(package.__file__).resolve().parent;assert not loaded.is_relative_to(ROOT/'packages')
 with zipfile.ZipFile(wheel) as archive:
  members=[n for n in archive.namelist() if n.startswith(package.__name__+'/') and not n.endswith('/')]
  for name in members:assert (loaded.parent/name).read_bytes()==archive.read(name),name
 payloads[package.__name__]={'sha256':sha(wheel),'members':len(members),'loaded':str(loaded)}
checks={};begin=time.perf_counter()
with tempfile.TemporaryDirectory(prefix='truss-release-smoke-',dir='/tmp') as folder:
 data=Path(folder)/'data'
 def query(server,sql):return subprocess.check_output([str(server.psql_path),server.info.connection_uri,'-X','-q','-A','-t','-v','ON_ERROR_STOP=1','-c',sql],text=True).strip()
 with LocalPostgres(data) as server:
  assert server.info.server_version==SERVER_VERSION
  assert query(server,"SELECT current_setting('listen_addresses')='' AND current_setting('unix_socket_directories')<>''")=='t'
  query(server,"CREATE TABLE release_probe(value text); INSERT INTO release_probe VALUES ('released18.6'); CREATE EXTENSION vector")
  assert query(server,"SELECT extversion FROM pg_extension WHERE extname='vector'")=='0.8.6'
 assert not (data/'postmaster.pid').exists()
 with LocalPostgres(data) as server:assert query(server,'SELECT value FROM release_probe')=='released18.6'
 assert not (data/'postmaster.pid').exists()
 checks.update(nativeVersion=True,unixSocketNoTcp=True,pgvector=True,retainedCommitRestart=True,ownedStopConfirmed=True)
env={**os.environ,'PYTHONPATH':os.pathsep.join([str(ROOT/'scripts'),str(ROOT/'packages/python/tests')]),'TRUSS_NATIVE_EVIDENCE_DIR':str(out),'TRUSS_CENSUS_POSTGRES_BIN':str(Path(pgserver.__file__).parent/'pginstall/bin')}
with WorkerCluster() as worker:
 result=subprocess.run([sys.executable,str(ROOT/'scripts/run-python-test-module.py'),'test_psycopg_host_native','-v'],cwd=sys.prefix,env={**env,**worker.environment()},capture_output=True,timeout=120)
 (out/'supported-driver.log').write_bytes(result.stdout+result.stderr)
 assert result.returncode==0 and b'Ran 26 tests' in result.stderr
 worker.verify_clean();checks.update(driver26Tests=True,sharedDatabaseRoleBaselineRestored=True)
result=subprocess.run([sys.executable,str(ROOT/'scripts/check-native-worker-fixtures.py'),'worker-controls.json'],cwd=sys.prefix,env=env,capture_output=True,timeout=120)
(out/'worker-controls.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0
assert json.loads((out/'worker-controls.json').read_text())['passed'];checks['cleanupCollision21Controls']=True
(out/'SHA256SUMS').write_bytes(a.checksums.read_bytes())
receipt={'passed':True,'scope':'Published-wheel fresh binary installation, exact installed payloads, native version/vector/socket startup, retained commit/restart, supported driver and worker cleanup/collision controls; not full current Truss corpus or Lakebase acceptance','sourceRevision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'runtimeDistribution':RUNTIME_DISTRIBUTION,'runtimeVersion':RUNTIME_VERSION,'postgresql':SERVER_VERSION,'releaseUrl':RUNTIME_PROFILE['repository']+'/releases/tag/'+RUNTIME_PROFILE['releaseTag'],'assetUrl':url,'directInstall':direct,'payloads':payloads,'checks':checks,'elapsedSeconds':time.perf_counter()-begin,'python':sys.version,'producerSha256':sha(Path(__file__)),'sourceSha256':{name:sha(ROOT/name) for name in ['scripts/native_fixture.py','scripts/run-python-test-module.py','scripts/check-native-worker-fixtures.py','packages/python/tests/test_psycopg_host_native.py']},'completeRuntimeQualified':False,'lakebaseQualified':False}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'passed':True,'checks':checks,'elapsedSeconds':receipt['elapsedSeconds']}))
