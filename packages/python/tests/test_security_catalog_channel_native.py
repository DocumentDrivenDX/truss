# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual authenticated loopback channel + original native guarded publication."""
import http.client,threading,secrets,json,os
from pathlib import Path
from unittest.mock import patch
from truss import Ok,Error
import test_security_catalog_source_cut_native as source
from security_channel_tls_fixture import owned_tls
import ssl
from security_catalog_channel import AuthenticatedReadChannel,REQUEST,ROUTE

class AuthenticatedCatalogChannelTests(source.CatalogSourceCutTests):
 for name in tuple(n for n in dir(source.CatalogSourceCutTests) if n.startswith('test_')):locals()[name]=None
 def channel(self,operation):
  credential=secrets.token_bytes(32);server_context,client_context=owned_tls(self);server=AuthenticatedReadChannel(credential,operation,tls_context=server_context)
  worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.01});worker.start()
  def stop():server.shutdown();server.server_close();worker.join(5);self.assertFalse(worker.is_alive())
  self.addCleanup(stop)
  def request(body=REQUEST,selected=credential,route=ROUTE):
   c=http.client.HTTPSConnection(*server.server_address,timeout=60,context=client_context)
   try:
    c.request('POST',route,body,{'Authorization':'Bearer '+selected.hex(),'Content-Type':'application/json'})
    r=c.getresponse();return r.status,r.read()
   finally:c.close()
  return server,request
 def test_authenticated_wire_read_binds_original_native_subject_and_cuts(self):
  """@covers US-056-AC2; @covers US-056-AC8; @covers US-057-AC7; prerequisites only."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();calls=[];states=[]
  def operation(publish):
   calls.append(True)
   def guarded_publish(packet):
    self.assertEqual(c.execute('SELECT SESSION_USER::text,CURRENT_USER::text').fetchone(),('consumer','consumer'))
    self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)").fetchone(),(2,))
    states.append('native-cuts-before-wire');publish(packet)
   return source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,guarded_publish)
  server,request=self.channel(operation)
  untrusted=http.client.HTTPSConnection(*server.server_address,timeout=10,context=ssl.create_default_context())
  try:
   with self.assertRaises(ssl.SSLCertVerificationError):untrusted.request('POST',ROUTE,REQUEST)
  finally:untrusted.close()
  self.assertEqual(calls,[])
  self.assertEqual(request(selected=bytes(32)),(401,b'{}'))
  self.assertEqual(request(body=b'{"operation":"read-resource","actor":"postgres"}'),(403,b'{}'))
  self.assertEqual(request(route='/sql'),(403,b'{}'));self.assertEqual(calls,[])
  status,packet=request();self.assertEqual(status,200)
  decision=json.loads(packet);self.assertEqual([r['key'] for r in decision['rows']],[[{'string':'r1'}]])
  self.assertEqual(decision['rows'][0]['output'][0]['disposition'],'withheld')
  self.assertEqual(calls,[True]);self.assertEqual(states,['native-cuts-before-wire'])
  self.assertEqual(request(),(403,b'{}'));self.assertEqual(calls,[True])
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:(Path(directory)/'wire-decision.json').write_bytes(packet)
 def test_original_native_refusal_exposes_no_diagnostic_and_cannot_retry(self):
  """@covers US-056-AC9; @covers US-057-AC7; prerequisites only."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();calls=[]
  self.admin.execute('SET LOCAL event_triggers=off')
  def operation(publish):
   calls.append(True)
   return source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,publish)
  server,request=self.channel(operation)
  with patch.object(source.subject,'encode_literal_key_tuple') as encoder:
   self.assertEqual(request(),(503,b'{}'));encoder.assert_not_called()
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original native event trigger execution required')
  self.assertEqual(request(),(403,b'{}'));self.assertEqual(calls,[True])
