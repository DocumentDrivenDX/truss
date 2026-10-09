"""Original local control-frame seam, not a qualified issuer/account/settlement port."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import socket
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
  supplied=SuppliedSocket(transport)
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
  finally:connection.close()
 finally:server.cleanup()
receipt={'scope':'Five fixed local control submissions with original command/ready frames captured at instance handlers; no original issuer/account/permit, savepoint authority or unknown-outcome qualification',
 'pgserver':'0.1.4','serverVersion':version,'driver':'pg8000 1.31.5','driverCoreSha256':CORE_SHA,
 'controls':[s for s,_,_ in controls],'frames':connection.control_frames,
 'independentExpectedControlFrames':10,'driverPortQualified':False,
 'sourceSha256':{p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in [Path(__file__).name,'pg8000_instance_candidate.py','python_pg_receive_candidate.py','python_pg_frame_candidate.py']},
 'limitations':['Local trust only; no TLS/current-person admission','Probe cycle labels are not original issuer authority','No lost-response/cancellation/cleanup evidence','No pre-ingress/account or native preservation qualification']}
(HERE/'pg8000-local-control-native.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'controls':5,'originalExpectedFrames':10,'serverVersion':version,'driverPortQualified':False}))
