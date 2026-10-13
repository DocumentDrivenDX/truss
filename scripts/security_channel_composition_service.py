"""Owned test service for external-peer guarded native TLS qualification.

Uses the original native fixture; not a production service or backend admission.
"""
import json,secrets,ssl,sys
from unittest.mock import patch
import psycopg
import test_security_catalog_channel_native as native
from security_catalog_channel import AuthenticatedReadChannel
from security_channel_tls_fixture import owned_tls
from truss import Ok,Error,adopt_psycopg_host


def serve(*,refuse_event_triggers=False,refuse_helper_public_grant=False,refuse_helper_owner=False):
 flags=(refuse_event_triggers,refuse_helper_public_grant,refuse_helper_owner)
 if any(type(flag) is not bool for flag in flags) or sum(flags)>1:raise ValueError('Exact owner fixture mode required')
 cls=native.AuthenticatedCatalogChannelTests
 fixture=cls('test_authenticated_wire_read_binds_original_native_subject_and_cuts')
 try:
  cls.setUpClass()
  fixture.setUp()
  mapping,c,h,t,selection,inspector,relations,cut=fixture.source_setup();calls=[]
  if refuse_helper_owner or refuse_helper_public_grant:
   fixture.admin.execute('ALTER FUNCTION truss.catalog_subject_current(text) OWNER TO postgres' if refuse_helper_owner else 'GRANT EXECUTE ON FUNCTION truss.catalog_subject_current(text) TO PUBLIC')
   fixture.host.detach();fixture.admin.commit();fixture.admin.execute('BEGIN')
   fixture.host=adopt_psycopg_host(fixture.admin);fixture.tx=fixture.host.adopt_transaction().value
  if refuse_event_triggers:fixture.admin.execute('SET LOCAL event_triggers=off')
  if any(flags):
   encoder=patch.object(native.source.subject,'encode_literal_key_tuple');observed_encoder=encoder.start();fixture.addCleanup(encoder.stop)
  context,client=owned_tls(fixture);credential=secrets.token_bytes(32)
  def operation(publish):
   calls.append(True)
   def guarded(packet):
    fixture.assertEqual(c.execute('SELECT SESSION_USER::text,CURRENT_USER::text').fetchone(),('consumer','consumer'))
    fixture.assertEqual(fixture.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)").fetchone(),(2,))
    publish(packet)
   return native.source.subject.publish_registered_ddl_epoch_guarded_native_catalog_resource_read(h,t,fixture.host,fixture.tx,mapping,selection,inspector,relations,cut,fixture.registered_subjects,guarded)
  server=AuthenticatedReadChannel(credential,operation,tls_context=context,bind_address=('0.0.0.0',0));fixture.addCleanup(server.server_close)
  certificate=ssl.DER_cert_to_PEM_cert(client.get_ca_certs(binary_form=True)[0])
  # Owner hands only channel credential/public certificate to its admitted peer.
  # Never persist this descriptor to evidence or expose SQL credentials.
  print(json.dumps({'port':server.server_address[1],'credential':credential.hex(),'certificate':certificate,'sqlPort':int(psycopg.conninfo.conninfo_to_dict(fixture.info.connection_uri).get('port','5432'))}),flush=True)
  server.timeout=45
  for _ in range(3):server.handle_request()
  fixture.assertEqual(calls,[True])
  observations={'operationCalls':len(calls),'channelConsumed':server._consumed}
  if any(flags):
   fixture.assertIsInstance(server._outcome,Error);fixture.assertIsNotNone(server._failure)
   primary=fixture.host._custody.last_attempt.error
   fixture.assertEqual(str(primary),'Original native event trigger execution required' if refuse_event_triggers else ('Exact installed catalog subject helper snapshot required' if refuse_helper_owner else 'Exact installed catalog subject helper ACL required'))
   observed_encoder.assert_not_called()
   observations.update({'nativeEventTriggerDriftRefused':refuse_event_triggers,'nativeHelperPublicGrantRefused':refuse_helper_public_grant,'nativeHelperOwnerRefused':refuse_helper_owner,'encodingCalls':0})
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
 if sys.argv[1:] not in ([],['--refuse-event-triggers'],['--refuse-helper-public-grant'],['--refuse-helper-owner']):raise ValueError('Original owner fixture mode required')
 serve(refuse_event_triggers=sys.argv[1:]==['--refuse-event-triggers'],refuse_helper_public_grant=sys.argv[1:]==['--refuse-helper-public-grant'],refuse_helper_owner=sys.argv[1:]==['--refuse-helper-owner'])
