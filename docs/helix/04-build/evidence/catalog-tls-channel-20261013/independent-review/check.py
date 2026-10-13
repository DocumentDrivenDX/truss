from pathlib import Path
import sys,ssl,socket,http.client,threading,time,unittest,tempfile,json,hashlib,atexit
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src'),str(ROOT/'packages/python/tests')]
from security_catalog_channel import AuthenticatedReadChannel,REQUEST,ROUTE
from security_channel_tls_fixture import owned_tls
from truss.execution import Ok
FILES=['scripts/security_catalog_channel.py','packages/python/tests/security_channel_tls_fixture.py','packages/python/tests/test_security_catalog_channel_native.py']
source_pins={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
checks=[];owner=unittest.TestCase();atexit.register(owner.doCleanups);server_context,client_context=owned_tls(owner)
directory=next(fn.__self__ for fn,a,k in owner._cleanups if isinstance(getattr(fn,'__self__',None),tempfile.TemporaryDirectory));directory_path=Path(directory.name)
def check(n,p):assert p,n;checks.append({'name':n,'passed':True})
check('owned directory0700 and key0600 without reading key bytes',directory_path.stat().st_mode&0o777==0o700 and (directory_path/'private-key.pem').stat().st_mode&0o777==0o600)
check('client verifies CA and hostname with TLS1.3 minimum',client_context.verify_mode==ssl.CERT_REQUIRED and client_context.check_hostname and client_context.minimum_version==ssl.TLSVersion.TLSv1_3)
credential=bytes(range(32));calls=[]
def operation(publish):calls.append(True);publish(b'{"rows":[]}');return Ok(b'{"rows":[]}')
server=AuthenticatedReadChannel(credential,operation,tls_context=server_context)
worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.01},daemon=True);worker.start()
def request(ctx=client_context,selected=credential,timeout=3):
 c=http.client.HTTPSConnection(*server.server_address,timeout=timeout,context=ctx)
 try:
  c.connect();version=c.sock.version();certificate=c.sock.getpeercert()
  c.request('POST',ROUTE,REQUEST,{'Authorization':'Bearer '+selected.hex(),'Content-Type':'application/json'})
  r=c.getresponse();return r.status,r.read(),version,certificate
 finally:c.close()
def failure(n,fn,types=(ssl.SSLError,OSError,http.client.HTTPException)):
 try:fn()
 except types:check(n,not calls)
 else:raise AssertionError(n)
try:
 failure('untrusted default CA refuses before operation',lambda:request(ssl.create_default_context()),(ssl.SSLCertVerificationError,))
 def wrong_name():
  with socket.create_connection(server.server_address,timeout=3) as raw:
   with client_context.wrap_socket(raw,server_hostname='localhost'):pass
 failure('trusted CA wrong hostname refuses before operation',wrong_name,(ssl.SSLCertVerificationError,))
 legacy=ssl.create_default_context(cafile=str(directory_path/'certificate.pem'));legacy.minimum_version=ssl.TLSVersion.TLSv1_2;legacy.maximum_version=ssl.TLSVersion.TLSv1_2
 failure('TLS1.2-only client cannot enter original server HTTP path',lambda:request(legacy))
 server_context.minimum_version=ssl.TLSVersion.TLSv1_2
 def weakened():
  c=http.client.HTTPSConnection(*server.server_address,timeout=3,context=legacy)
  try:
   c.connect();check('weak-context countercheck actually negotiates TLS1.2',c.sock.version()=='TLSv1.2')
   c.request('POST',ROUTE,REQUEST,{'Authorization':'Bearer '+credential.hex(),'Content-Type':'application/json'})
   r=c.getresponse();r.read()
  finally:c.close()
 failure('postconstruction weakened minimum still rejects negotiatedTLS1.2 before HTTP',weakened)
 server_context.minimum_version=ssl.TLSVersion.TLSv1_3
 with socket.create_connection(server.server_address,timeout=3) as raw:
  raw.sendall(b'POST /protected/read HTTP/1.1\r\nHost: localhost\r\n\r\n')
  try:answer=raw.recv(4096)
  except (ConnectionResetError,ssl.SSLError):answer=b''
  check('plaintext request cannot dispatch or receive HTTP decision on TLS listener',not calls and not answer.startswith(b'HTTP/'))
 status,body,version,cert=request(selected=bytes(32))
 check('wrong bearer over verifiedTLS gets401 without operation',(status,body)==(401,b'{}') and not calls and version=='TLSv1.3')
 status,body,version,cert=request()
 check('verified TLS1.3 original bearer publishes once',(status,body,version)==(200,b'{"rows":[]}','TLSv1.3') and calls==[True])
 check('certificate verified against exact IP SAN',('IP Address','127.0.0.1') in cert['subjectAltName'])
 check('TLS channel reuse refuses with no second operation',request()[:2]==(403,b'{}') and calls==[True])
finally:server.shutdown();server.server_close();worker.join(3)
check('TLS server and sockets settle',not worker.is_alive())
for name,ctx in [('wrong object',object()),('client context',ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)),('weak minimum',ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER))]:
 if name=='weak minimum':ctx.minimum_version=ssl.TLSVersion.TLSv1_2
 try:bad=AuthenticatedReadChannel(credential,operation,tls_context=ctx)
 except ValueError:check('constructor refuses '+name,True)
 else:bad.server_close();raise AssertionError(name)
calls.clear();server=AuthenticatedReadChannel(credential,operation,tls_context=server_context);worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.01},daemon=True);worker.start();raw=socket.create_connection(server.server_address,timeout=3)
queued=[];start=time.monotonic();client=None
try:
 # Incomplete TLS record, continuously progressing but never a full ClientHello.
 raw.sendall(b'\x16\x03\x01\x10\x00\x01')
 def valid():
  try:queued.append(request(timeout=8))
  except BaseException as e:queued.append(type(e).__name__)
 client=threading.Thread(target=valid,daemon=True);client.start()
 while time.monotonic()-start<6.3 and client.is_alive():
  try:raw.sendall(b'\x00')
  except OSError:break
  time.sleep(0.25)
 client.join(3);elapsed=time.monotonic()-start
 check('progressing incomplete TLS handshake is bounded before queued valid operation',not client.is_alive() and len(queued)==1 and type(queued[0]) is tuple and queued[0][:3]==(200,b'{"rows":[]}','TLSv1.3') and calls==[True] and elapsed<8)
finally:
 raw.close()
 if client:client.join(8)
 server.shutdown();server.server_close();worker.join(3)
check('stalled-handshake server shuts down cleanly',not worker.is_alive())
owner.doCleanups();check('ephemeral certificate and private key directory removed',not directory_path.exists())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==s for p,s in source_pins.items())
result={'scope':'Actual loopback TLS and synthetic original operation only; no native database, private key bytes or bearer token retained','count':len(checks),'controls':checks,'incompleteHandshakeElapsedSeconds':round(elapsed,3),'sourceSha256':source_pins}
(OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'controls':len(checks),'passed':True,'handshakeElapsedSeconds':round(elapsed,3)}))
