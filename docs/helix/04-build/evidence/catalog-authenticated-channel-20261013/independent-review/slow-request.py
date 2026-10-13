from pathlib import Path
import sys,socket,threading,time,json,hashlib,http.client
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
source_sha=hashlib.sha256((ROOT/'scripts/security_catalog_channel.py').read_bytes()).hexdigest()
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src')]
from security_catalog_channel import AuthenticatedReadChannel,REQUEST,ROUTE
from truss.execution import Ok
calls=[];secret=bytes(range(32))
def operation(publish):calls.append(True);publish(b'{}');return Ok(b'{}')
server=AuthenticatedReadChannel(secret,operation)
worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.01},daemon=True);worker.start()
peer=socket.create_connection(server.server_address,timeout=1);stopper=None
record={}
try:
 peer.sendall(b'POST /protected/read HTTP/1.1\r\nHost: localhost\r\nX-Slow: ')
 start=time.monotonic()
 while time.monotonic()-start<6.1:
  try:peer.sendall(b'x')
  except OSError:record['peerClosedDuringTrickle']=True;break
  time.sleep(0.4)
 record['incompleteUnauthenticatedHeaderSeconds']=round(time.monotonic()-start,3)
 valid=http.client.HTTPConnection(*server.server_address,timeout=0.25)
 try:
  valid.request('POST',ROUTE,REQUEST,{'Authorization':'Bearer '+secret.hex(),'Content-Type':'application/json'})
  response=valid.getresponse();record['queuedAuthenticatedStatus']=response.status;response.read()
 except TimeoutError:record['queuedAuthenticatedTimedOut']=True
 finally:valid.close()
 stopper=threading.Thread(target=server.shutdown,daemon=True);stopper.start();stopper.join(0.25)
 record['shutdownBlockedUntilUnauthenticatedPeerCloses']=stopper.is_alive()
 record['operationCallsBeforePeerClose']=len(calls)
finally:
 peer.close()
 if stopper is None:stopper=threading.Thread(target=server.shutdown,daemon=True);stopper.start()
 stopper.join(6);server.server_close();worker.join(6)
record['shutdownCompletedAfterPeerClose']=not stopper.is_alive() and not worker.is_alive()
assert hashlib.sha256((ROOT/'scripts/security_catalog_channel.py').read_bytes()).hexdigest()==source_sha
record['sourceSha256']=source_sha
record['scope']='Actual loopback HTTP server; bounded progressing-input request and queued valid fixture operation, no database lifecycle.'
(OUT/'slow-request-after.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
