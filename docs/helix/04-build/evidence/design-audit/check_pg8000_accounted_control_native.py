"""Original local control-frame seam, not a qualified issuer/account/settlement port."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import socket
import sys
import tempfile
from urllib.parse import urlparse,parse_qs
import pg8000.core
import pgserver
from pg8000_instance_candidate import RawConnection
from pg8000_accounted_instance_candidate import AccountedSocket
from truss._resource_account import BytePermitAccount

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
CORE_SHA='cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26'
if importlib.metadata.version('pg8000')!='1.31.5' or hashlib.sha256(Path(pg8000.core.__file__).read_bytes()).hexdigest()!=CORE_SHA:
 raise SystemExit('Pinned original driver required')
corrected = len(sys.argv)==3 and sys.argv[1]=='--corrected-pgserver'
if len(sys.argv)!=1 and not corrected: raise SystemExit('usage: check_pg8000_local_control_native.py [--corrected-pgserver NEW_RECEIPT_FILENAME]')
receipt_name = sys.argv[2] if corrected else 'pg8000-local-control-native.json'
if Path(receipt_name).name!=receipt_name or not receipt_name.endswith('.json'): raise SystemExit('Receipt basename required')
destination=HERE/receipt_name
if destination.exists(): raise SystemExit('Refusing to replace original receipt')
pgserver_version='0.1.4+truss.pg16.15' if corrected else '0.1.4'
if importlib.metadata.version('pgserver')!=pgserver_version:raise SystemExit('Pinned pgserver required')

class ControlConnection(RawConnection):
 def __init__(self,*args,**kwargs):
  self.control_frames=[];self.probe_cycle='startup'
  super().__init__(*args,**kwargs)
 def handle_COMMAND_COMPLETE(self,data,context):
  self.control_frames.append({'cycle':self.probe_cycle,'kind':'C','hex':self.original_frame(b'C',data).hex()})
  super().handle_COMMAND_COMPLETE(data,context)
 def handle_READY_FOR_QUERY(self,data,context):
  self.control_frames.append({'cycle':self.probe_cycle,'kind':'Z','hex':self.original_frame(b'Z',data).hex()})
  super().handle_READY_FOR_QUERY(data,context)

controls=[('BEGIN',b'BEGIN\0',b'T'),('SAVEPOINT original_probe',b'SAVEPOINT\0',b'T'),
 ('ROLLBACK TO SAVEPOINT original_probe',b'ROLLBACK\0',b'T'),
 ('RELEASE SAVEPOINT original_probe',b'RELEASE\0',b'T'),('ROLLBACK',b'ROLLBACK\0',b'I')]
with tempfile.TemporaryDirectory(prefix='truss-python-control-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
 try:
  uri=urlparse(server.get_uri());options=parse_qs(uri.query)
  host=options.get('host',[uri.hostname])[0];port=int(options.get('port',[uri.port or 5432])[0])
  if host and host.startswith('/'):
   transport=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);transport.settimeout(10)
   transport.connect(str(Path(host)/f'.s.PGSQL.{port}'))
  else:transport=socket.create_connection((host,port),timeout=10)
  producer=object()
  account=BytePermitAccount(producer,134217728,268435456,1024)
  supplied=AccountedSocket(transport,account,producer)
  connection=ControlConnection(user='postgres',database='postgres',sock=supplied,ssl_context=False,startup_params={'client_encoding':'UTF8'})
  try:
   for index,(sql,tag,state) in enumerate(controls):
    connection.probe_cycle=str(index)
    connection.execute_simple(sql)
    observed=[f for f in connection.control_frames if f['cycle']==str(index)]
    expected=[{'cycle':str(index),'kind':'C','hex':(b'C'+(len(tag)+4).to_bytes(4,'big')+tag).hex()},
              {'cycle':str(index),'kind':'Z','hex':(b'Z'+(5).to_bytes(4,'big')+state).hex()}]
    if observed!=expected:raise ValueError('Independent original control-frame mismatch')
   version=connection.parameter_statuses.get('server_version')
   if corrected and not version.startswith('16.15'): raise ValueError('Corrected native version required')
  finally:
   connection.close()
   account_after_close=account.snapshot(producer)
   if not account_after_close[3] or account_after_close[0]<=0 or account_after_close[1]!=0:
    raise ValueError('Original payload custody missing after close')
 finally:server.cleanup()
receipt={'scope':'Five fixed local control submissions with original command/ready frames captured at instance handlers; shared frame/slice payload account and conservative two core-copy charges exercised; no complete account, original savepoint authority or unknown-outcome qualification',
 'pgserver':pgserver_version,'serverVersion':version,'driver':'pg8000 1.31.5','driverCoreSha256':CORE_SHA,
 'controls':[s for s,_,_ in controls],'frames':connection.control_frames,
 'independentExpectedControlFrames':10,'driverPortQualified':False,
 'payloadAccountAfterClose':list(account_after_close),'payloadAccountLimits':{'live':134217728,'cumulative':268435456,'records':1024},
 'installedTrussModuleSha256':{n:hashlib.sha256((Path(__import__('truss').__file__).parent/n).read_bytes()).hexdigest() for n in ['_accounted_receive.py','_resource_account.py']},
 'sourceSha256':{p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in [Path(__file__).name,'pg8000_instance_candidate.py','pg8000_accounted_instance_candidate.py','python_pg_receive_candidate.py','python_pg_frame_candidate.py']},
 'limitations':['Local trust only; no TLS/current-person admission','Probe cycle labels are not original issuer authority','No lost-response/cancellation/cleanup evidence','Payload account excludes transport/object overhead, core/parser/outbound and containment; no native preservation qualification']}
with destination.open('x') as output: output.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'controls':5,'originalExpectedFrames':10,'serverVersion':version,'driverPortQualified':False}))
