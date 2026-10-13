"""Actual loopback HTTP controls; no SQL topology/auth issuer qualification."""
import http.client,threading,secrets,unittest,sys,socket,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from security_catalog_channel import AuthenticatedReadChannel,REQUEST,ROUTE
from truss.execution import Ok,Error

class ChannelTests(unittest.TestCase):
 def setUp(self):
  self.credential=secrets.token_bytes(32);self.calls=[]
  def operation(publish):
   self.calls.append(True);packet=b'{"rows":[]}';publish(packet);return Ok(packet)
  self.server=AuthenticatedReadChannel(self.credential,operation)
  self.worker=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':0.01})
  self.worker.start();self.addCleanup(self.stop)
 def stop(self):
  self.server.shutdown();self.server.server_close();self.worker.join(5)
  self.assertFalse(self.worker.is_alive())
 def request(self,*,credential=None,body=REQUEST,route=ROUTE,method='POST',headers=None):
  c=http.client.HTTPConnection(*self.server.server_address,timeout=10)
  try:
   h={'Authorization':'Bearer '+(self.credential if credential is None else credential).hex(),'Content-Type':'application/json'}
   if headers:h.update(headers)
   c.request(method,route,body,h);response=c.getresponse();return response.status,response.read()
  finally:c.close()
 def test_exact_authenticated_request_one_delivery_then_no_reuse(self):
  self.assertEqual(self.request(),(200,b'{"rows":[]}'));self.assertEqual(self.calls,[True])
  self.assertEqual(self.request(),(403,b'{}'));self.assertEqual(self.calls,[True])
 def test_unknown_credentials_and_subject_or_sql_substitution_never_dispatch(self):
  for credential in (bytes(32),bytes(31),bytes(33)):
   self.assertEqual(self.request(credential=credential),(401,b'{}'))
  for change in ({'body':b'{"operation":"read-resource","actor":"admin"}'},{'route':'/sql'},{'route':ROUTE+'?actor=admin'},{'method':'GET'},{'headers':{'X-Subject':'admin'}},{'headers':{'Transfer-Encoding':'chunked'}},{'headers':{'Content-Type':'text/plain'}}):
   self.assertEqual(self.request(**change),(403,b'{}'))
  self.assertEqual(self.calls,[])
  self.assertEqual(self.request()[0],200)
 def test_native_failure_is_generic_and_consumes_original_operation(self):
  def fail(publish):self.calls.append(True);raise RuntimeError('private SQL credential and diagnostic')
  self.server._operation=fail
  self.assertEqual(self.request(),(503,b'{}'));self.assertEqual(self.request(),(403,b'{}'));self.assertEqual(self.calls,[True])
 def test_wrong_completion_cannot_append_diagnostic_after_delivery_or_retry(self):
  def fail(publish):self.calls.append(True);publish(b'{"rows":[]}');raise RuntimeError('private diagnosis')
  self.server._operation=fail
  self.assertEqual(self.request(),(200,b'{"rows":[]}'));self.assertEqual(self.request(),(403,b'{}'));self.assertEqual(self.calls,[True])

 def test_progressing_unauthenticated_headers_have_absolute_deadline(self):
  attacker=socket.create_connection(self.server.server_address,timeout=10)
  attacker.sendall(b'POST /protected/read HTTP/1.1\r\nHost: local\r\nX-Slow: ')
  outcome=[];started=time.monotonic()
  def valid():outcome.append(self.request())
  client=threading.Thread(target=valid);client.start()
  try:
   while time.monotonic()-started<6 and client.is_alive():
    try:attacker.sendall(b'x')
    except OSError:break
    time.sleep(0.2)
   client.join(3)
   self.assertFalse(client.is_alive());self.assertEqual(outcome,[(200,b'{"rows":[]}')])
   self.assertLess(time.monotonic()-started,8);self.assertEqual(self.calls,[True])
  finally:attacker.close();client.join(3)

 def test_malformed_headers_and_normalized_target_never_dispatch(self):
  for target,extra in ((b'/protected/read',b'Invalid Header: x\r\nX-Subject: admin\r\n'),(b'/protected/read',b'Transfer-Encoding : chunked\r\n'),(b'//protected/read',b'')):
   with socket.create_connection(self.server.server_address,timeout=10) as c:
    request=b'POST '+target+b' HTTP/1.1\r\nHost: local\r\nAuthorization: Bearer '+self.credential.hex().encode()+b'\r\nContent-Type: application/json\r\nContent-Length: '+str(len(REQUEST)).encode()+b'\r\n'+extra+b'\r\n'+REQUEST
    c.sendall(request);response=http.client.HTTPResponse(c);response.begin()
    self.assertEqual((response.status,response.read()),(403,b'{}'))
  self.assertEqual(self.calls,[])
