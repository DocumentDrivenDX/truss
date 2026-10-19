# SPDX-License-Identifier: MIT OR Apache-2.0
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

class TlsChannelTests(unittest.TestCase):
 def setUp(self):
  import ssl
  from security_channel_tls_fixture import owned_tls
  self.context,self.client_context=owned_tls(self);self.credential=secrets.token_bytes(32);self.calls=[]
  def operation(publish):self.calls.append(True);packet=b'{"rows":[]}';publish(packet);return Ok(packet)
  self.server=AuthenticatedReadChannel(self.credential,operation,tls_context=self.context)
  self.worker=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':0.01});self.worker.start();self.addCleanup(self.stop)
 def stop(self):
  self.server.shutdown();self.server.server_close();self.worker.join(5);self.assertFalse(self.worker.is_alive())
 def request(self,context=None):
  c=http.client.HTTPSConnection(*self.server.server_address,timeout=12,context=context or self.client_context)
  try:
   c.request('POST',ROUTE,REQUEST,{'Authorization':'Bearer '+self.credential.hex(),'Content-Type':'application/json'})
   self.assertEqual(c.sock.version(),'TLSv1.3')
   r=c.getresponse();return r.status,r.read()
  finally:c.close()
 def test_verified_certificate_then_one_original_publication(self):
  import ssl
  with self.assertRaises(ssl.SSLCertVerificationError):self.request(ssl.create_default_context())
  wrong_name=http.client.HTTPSConnection('localhost',self.server.server_address[1],timeout=10,context=self.client_context)
  try:
   with self.assertRaises(ssl.SSLCertVerificationError):wrong_name.request('POST',ROUTE,REQUEST)
  finally:wrong_name.close()
  self.assertEqual(self.calls,[]);self.assertEqual(self.request(),(200,b'{"rows":[]}'))
 def test_weakened_owner_context_does_not_admit_negotiated_tls12(self):
  import ssl
  self.context.minimum_version=ssl.TLSVersion.TLSv1_2
  legacy=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);legacy.check_hostname=False;legacy.verify_mode=ssl.CERT_NONE
  legacy.minimum_version=legacy.maximum_version=ssl.TLSVersion.TLSv1_2
  c=http.client.HTTPSConnection(*self.server.server_address,timeout=10,context=legacy)
  try:
   with self.assertRaises((OSError,http.client.HTTPException)):
    c.request('POST',ROUTE,REQUEST,{'Authorization':'Bearer '+self.credential.hex(),'Content-Type':'application/json'});c.getresponse()
  finally:c.close()
  self.assertEqual(self.calls,[]);self.context.minimum_version=ssl.TLSVersion.TLSv1_3
  self.assertEqual(self.request()[0],200)
 def test_incomplete_tls_handshake_expires_and_queued_verified_peer_runs(self):
  attacker=socket.create_connection(self.server.server_address,timeout=10);outcome=[];started=time.monotonic()
  client=threading.Thread(target=lambda:outcome.append(self.request()));client.start()
  try:
   client.join(9);self.assertFalse(client.is_alive());self.assertEqual(outcome,[(200,b'{"rows":[]}')])
   self.assertLess(time.monotonic()-started,9);self.assertEqual(self.calls,[True])
  finally:attacker.close();client.join(3)

class ListenerAdmissionTests(unittest.TestCase):
 def test_external_plaintext_and_ambiguous_addresses_refuse_before_bind(self):
  from unittest.mock import patch
  credential=bytes(32)
  with patch('security_catalog_channel.HTTPServer.__init__') as bind:
   for address in [('0.0.0.0',0),('192.0.2.1',443),('localhost',0),('::1',0),('127.0.0.1',True),('127.0.0.1',-1),('127.0.0.1',65536),['127.0.0.1',0]]:
    with self.assertRaises(ValueError):AuthenticatedReadChannel(credential,lambda publish:None,bind_address=address)
   bind.assert_not_called()

 def test_wildcard_listener_requires_verified_tls_and_retains_one_operation(self):
  from security_channel_tls_fixture import owned_tls
  server_context,client_context=owned_tls(self);credential=secrets.token_bytes(32);calls=[]
  def operation(publish):
   calls.append(True);packet=b'{"rows":[]}';publish(packet);return Ok(packet)
  server=AuthenticatedReadChannel(credential,operation,tls_context=server_context,bind_address=('0.0.0.0',0))
  worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.01});worker.start()
  try:
   self.assertEqual(server.server_address[0],'0.0.0.0')
   raw=socket.create_connection(('127.0.0.1',server.server_address[1]),timeout=10)
   with client_context.wrap_socket(raw,server_hostname='127.0.0.1') as wire:
    self.assertEqual(wire.version(),'TLSv1.3')
    wire.sendall(b'POST '+ROUTE.encode()+b' HTTP/1.1\r\nHost: original\r\nAuthorization: Bearer '+credential.hex().encode()+b'\r\nContent-Type: application/json\r\nContent-Length: '+str(len(REQUEST)).encode()+b'\r\n\r\n'+REQUEST)
    response=http.client.HTTPResponse(wire);response.begin()
    self.assertEqual((response.status,response.read()),(200,b'{"rows":[]}'))
   self.assertEqual(calls,[True]);self.assertTrue(server._consumed)
  finally:
   server.shutdown();server.server_close();worker.join(5);self.assertFalse(worker.is_alive())
