"""Owned test service for external-peer guarded native TLS qualification.

Uses the original native fixture; not a production service or backend admission.
"""
import json,secrets,ssl,sys
from unittest.mock import patch
import psycopg
import test_security_catalog_channel_native as native
from security_catalog_channel import AuthenticatedReadChannel
from security_channel_tls_fixture import owned_tls
from truss import Ok,Error


def serve(*,refuse_event_triggers=False):
 if type(refuse_event_triggers) is not bool:raise ValueError('Exact owner fixture mode required')
 cls=native.AuthenticatedCatalogChannelTests
 fixture=cls('test_authenticated_wire_read_binds_original_native_subject_and_cuts')
 try:
  cls.setUpClass()
  fixture.setUp()
  mapping,c,h,t,selection,inspector,relations,cut=fixture.source_setup();calls=[]
  if refuse_event_triggers:
   fixture.admin.execute('SET LOCAL event_triggers=off')
   encoder=patch.object(native.source.subject,'encode_literal_key_tuple');observed_encoder=encoder.start();fixture.addCleanup(encoder.stop)
  context,client=owned_tls(fixture);credential=secrets.token_bytes(32)
  def operation(publish):
   calls.append(True)
   def guarded(packet):
    fixture.assertEqual(c.execute('SELECT SESSION_USER::text,CURRENT_USER::text').fetchone(),('consumer','consumer'))
    fixture.assertEqual(fixture.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)").fetchone(),(2,))
    publish(packet)
   return native.source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,fixture.host,fixture.tx,mapping,selection,inspector,relations,cut,guarded)
  server=AuthenticatedReadChannel(credential,operation,tls_context=context,bind_address=('0.0.0.0',0));fixture.addCleanup(server.server_close)
  certificate=ssl.DER_cert_to_PEM_cert(client.get_ca_certs(binary_form=True)[0])
  # Owner hands only channel credential/public certificate to its admitted peer.
  # Never persist this descriptor to evidence or expose SQL credentials.
  print(json.dumps({'port':server.server_address[1],'credential':credential.hex(),'certificate':certificate,'sqlPort':int(psycopg.conninfo.conninfo_to_dict(fixture.info.connection_uri).get('port','5432'))}),flush=True)
  server.timeout=45
  for _ in range(3):server.handle_request()
  fixture.assertEqual(calls,[True])
  observations={'operationCalls':len(calls),'channelConsumed':server._consumed}
  if refuse_event_triggers:
   fixture.assertIsInstance(server._outcome,Error);fixture.assertIsNotNone(server._failure)
   fixture.assertEqual(str(fixture.host._custody.last_attempt.error),'Original native event trigger execution required')
   observed_encoder.assert_not_called()
   observations.update({'nativeEventTriggerDriftRefused':True,'encodingCalls':0})
  else:
   fixture.assertIsInstance(server._outcome,Ok);fixture.assertIsNone(server._failure)
   observations['nativeConsumerAndBothSourceCutsBeforeWire']=True
  print(json.dumps(observations),flush=True)
 finally:
  failures=[]
  try:fixture.tearDown()
  except BaseException as error:failures.append(error)
  try:
   if not fixture.doCleanups():failures.append(RuntimeError('Original fixture cleanup refused'))
  except BaseException as error:failures.append(error)
  try:
   cls.doClassCleanups()
   failures.extend(item[1] for item in cls.tearDown_exceptions)
  except BaseException as error:failures.append(error)
  if failures:raise RuntimeError('Original service cleanup failed') from failures[0]

if __name__=='__main__':
 if sys.argv[1:] not in ([],['--refuse-event-triggers']):raise ValueError('Original owner fixture mode required')
 serve(refuse_event_triggers=bool(sys.argv[1:]))
