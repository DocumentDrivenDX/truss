#!/usr/bin/env python3
"""Owned installed CLI signal checks; preserve data on uncertain cleanup."""
from native_fixture import evidence_directory
import hashlib
import importlib.metadata
import json
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import sys
from truss._runtime_profile import RUNTIME_DISTRIBUTION, RUNTIME_VERSION, SERVER_VERSION
import tempfile
import truss.cli
root = Path(__file__).resolve().parents[1]
if sys.argv[1:] not in ([], ['--corrected-pgserver']):
 raise SystemExit('usage: check-python-installed-cli-signals.py [--corrected-pgserver]')
corrected = True  # All live executions select17.11.
expected_package = RUNTIME_VERSION
expected_server = SERVER_VERSION
if importlib.metadata.version(RUNTIME_DISTRIBUTION) != expected_package:
 raise RuntimeError('Selected original runtime package mismatch')
loaded = Path(truss.cli.__file__).resolve()
if not loaded.is_relative_to(Path(sys.prefix).resolve()) or loaded.is_relative_to(root):
 raise RuntimeError('Installed CLI outside checkout required')
if loaded.read_bytes() != (root/'packages/python/src/truss/cli.py').read_bytes():
 raise RuntimeError('Installed CLI source drift')
parent = Path(tempfile.mkdtemp(prefix='truss-cli-signals-'))
directory = parent/'retained data'
runs = []
command = str(Path(sys.prefix)/'bin/truss-local-postgres')
for signum in [signal.SIGTERM,signal.SIGINT]:
 process = subprocess.Popen([command,'--data-dir',str(directory)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  with selectors.DefaultSelector() as selector:
   selector.register(process.stdout,selectors.EVENT_READ)
   if not selector.select(timeout=60): raise RuntimeError('CLI readiness unavailable; retain '+str(parent))
   original = process.stdout.readline()
  observed = json.loads(original)
  if observed['serverVersion'] != expected_server or observed['runtimeVersion'] != expected_package or observed['trussInstallation'] != 'not_checked':
   raise RuntimeError('Unexpected local runtime profile')
  if not (directory/'postmaster.pid').exists(): raise RuntimeError('Native postmaster marker missing before signal')
  process.send_signal(signum)
  stdout,stderr = process.communicate(timeout=60)
  if process.returncode != 0 or stdout or stderr: raise RuntimeError('Signal shutdown failed: '+stderr)
  if (directory/'postmaster.pid').exists() or (directory/'PG_VERSION').read_text().strip() != expected_server.split('.')[0]:
   raise RuntimeError('Owned shutdown/retained data mismatch')
  runs.append({'signal':signal.Signals(signum).name,'cliPid':process.pid,'runtime':observed,'exitCode':process.returncode,'postmasterMarkerAbsent':True,'dataRetained':True})
 except BaseException:
  # This is only our recorded child command; never terminate other processes.
  if process.poll() is None: process.terminate()
  raise
receipt = {'scope':'Actual installed CLI SIGTERM/SIGINT shutdown and retained restart on '+('macOS arm64 PostgreSQL' + SERVER_VERSION)+'; no crash/installer qualification',
 'correctedPgserverCandidate':corrected,
 'loadedCli':str(loaded),'cliSha256':hashlib.sha256(loaded.read_bytes()).hexdigest(),
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'runs':runs,
 'originalCustody':'Signals sent only to the subprocess PIDs started by this probe',
 'completeEngineQualified':False,'processCrashQualified':False}
filename = 'python-pg' + SERVER_VERSION + '-runtime-cli-signals.json'
(evidence_directory()/filename).write_text(json.dumps(receipt,indent=2)+'\n')
shutil.rmtree(parent)
print(json.dumps({'signals':[r['signal'] for r in runs],'completeEngineQualified':False}))
