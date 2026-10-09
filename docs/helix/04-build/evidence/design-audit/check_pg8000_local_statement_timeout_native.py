"""Native statement timeout; cancellation error is separate from outer transaction termination."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import socket
import subprocess
import importlib.resources
import time
import tempfile
from urllib.parse import urlparse,parse_qs
import pg8000.core
import pgserver
from pg8000_instance_candidate import SuppliedSocket, RawConnection

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
CORE_SHA='cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26'
if importlib.metadata.version('pg8000')!='1.31.5' or hashlib.sha256(Path(pg8000.core.__file__).read_bytes()).hexdigest()!=CORE_SHA:
 raise SystemExit('Pinned original driver required')
if importlib.metadata.version('pgserver')!='0.1.4':raise SystemExit('Pinned pgserver required')

class ControlConnection(RawConnection):
 def __init__(self,*args,**kwargs):
  self.control_frames=[];self.probe_cycle='startup';self.inject_failure=False
  super().__init__(*args,**kwargs)
 def handle_COMMAND_COMPLETE(self,data,context):
  self.control_frames.append({'cycle':self.probe_cycle,'kind':'C','hex':self.original_frame(b'C',data).hex()})
  super().handle_COMMAND_COMPLETE(data,context)
 def handle_ERROR_RESPONSE(self,data,context):
  self.control_frames.append({'cycle':self.probe_cycle,'kind':'E','hex':self.original_frame(b'E',data).hex()})
  super().handle_ERROR_RESPONSE(data,context)
 def handle_READY_FOR_QUERY(self,data,context):
  self.control_frames.append({'cycle':self.probe_cycle,'kind':'Z','hex':self.original_frame(b'Z',data).hex()})
  super().handle_READY_FOR_QUERY(data,context)

with tempfile.TemporaryDirectory(prefix='truss-python-timeout-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
 psql=Path(str(importlib.resources.files('pgserver')))/'pginstall/bin/psql'
 def observe(sql):
  return subprocess.check_output([str(psql),server.get_uri(),'-X','-q','-A','-t','-v','ON_ERROR_STOP=1','-c',sql],text=True,timeout=30).strip()
 try:
  uri=urlparse(server.get_uri());options=parse_qs(uri.query)
  host=options.get('host',[uri.hostname])[0];port=int(options.get('port',[uri.port or 5432])[0])
  if host and host.startswith('/'):
   transport=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);transport.settimeout(10)
   transport.connect(str(Path(host)/f'.s.PGSQL.{port}'))
  else:transport=socket.create_connection((host,port),timeout=10)
  supplied=SuppliedSocket(transport)
  connection=ControlConnection(user='postgres',database='postgres',sock=supplied,ssl_context=False,startup_params={'client_encoding':'UTF8'})
  try:
   pid=int(connection.execute_simple('SELECT pg_backend_pid()::text').rows[0][0])
   observe('CREATE TABLE public.control_effect_probe(value text)')
   connection.execute_simple("SET statement_timeout = '50ms'")
   connection.execute_simple('BEGIN')
   connection.execute_simple("INSERT INTO public.control_effect_probe VALUES ('pending-original')")
   connection.probe_cycle='timed-out-statement'
   try:
    connection.execute_simple('SELECT pg_sleep(30)')
    raise AssertionError('Native statement timeout did not propagate')
   except pg8000.exceptions.DatabaseError as error:
    if error.args[0].get('C')!='57014':raise
   fault_frames=[f for f in connection.control_frames if f['cycle']=='timed-out-statement']
   if [frame['kind'] for frame in fault_frames]!=['E','Z']:
    raise ValueError('Original rejection frame order mismatch')
   error_frame=bytes.fromhex(fault_frames[0]['hex'])
   if error_frame[0:1]!=b'E' or int.from_bytes(error_frame[1:5],'big')!=len(error_frame)-1:
    raise ValueError('Original error framing mismatch')
   fields=error_frame[5:].split(b'\0')
   if b'C57014' not in fields:
    raise ValueError('Independent native query-cancel expectation mismatch')
   if fault_frames[1]['hex']!=(b'Z'+(5).to_bytes(4,'big')+b'E').hex():
    raise ValueError('Expected failed-transaction ReadyForQuery')
   if not supplied.file.closed:raise ValueError('Original adapter not quarantined')
   writes=supplied.file.remaining_writes
   try:
    connection.execute_simple('SELECT 1')
    raise AssertionError('Quarantined adapter submitted another command')
   except ValueError:
    pass
   if supplied.file.remaining_writes!=writes:raise ValueError('Unexpected send after quarantine')
   pending_state=observe(f'SELECT state FROM pg_stat_activity WHERE pid={pid}')
   if pending_state!='idle in transaction (aborted)':raise ValueError('Backend failed-transaction state mismatch')
   if observe('SELECT count(*) FROM public.control_effect_probe')!='0':raise ValueError('Uncommitted fixture became visible')
   version=connection.parameter_statuses.get('server_version')
   if version!='16.2':raise ValueError('Expected original local engine')
  finally:
   # Explicit probe cleanup, not an inferred outcome or automatic resubmission.
   transport.close()
  for _ in range(20):
   if observe(f'SELECT count(*) FROM pg_stat_activity WHERE pid={pid}')=='0':break
   time.sleep(0.05)
  else:raise ValueError('Original backend termination not observed')
  if observe('SELECT count(*) FROM public.control_effect_probe')!='0':raise ValueError('Original pending write persisted after termination')

 finally:server.cleanup()
receipt={'scope':'Original statement-timeout ErrorResponse and live aborted outer transaction on PostgreSQL16.2 local trust transport; no whole-transaction deadline or complete issuer/account/recovery qualification',
 'pgserver':'0.1.4','serverVersion':version,'driver':'pg8000 1.31.5','driverCoreSha256':CORE_SHA,
 'faultFrames':fault_frames,'backendStateBeforeExplicitSocketClose':pending_state,
 'newSubmissionRefusedWithoutSend':True,'backendTerminationAfterExplicitCloseObserved':True,
 'originalPendingWriteAbsentAfterTermination':True,'driverPortQualified':False,'wholeTransactionDeadlineQualified':False,
 'statementTimeoutMilliseconds':'50','nativeSqlState':'57014',
 'sourceSha256':{p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in [Path(__file__).name,'pg8000_instance_candidate.py','python_pg_receive_candidate.py','python_pg_frame_candidate.py']},
 'limitations':['Fixed pg_sleep statement with session statement_timeout50ms; no complete invocation/transaction deadline','No original issuer/account/control permit admission',
 'No ordinary-person/TLS qualification','No unknown COMMIT settlement or durable recovery registry qualification']}
(HERE/'pg8000-local-statement-timeout-native.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'serverVersion':version,'pendingAfterClientFailure':pending_state,'quarantinedWithoutResubmit':True,'terminatedAfterExplicitClose':True,'driverPortQualified':False}))
