"""Produce original .23 facts using that installed public Python package."""
import pickle,sys
from pathlib import Path
from types import SimpleNamespace
from truss import Ok
from test_feed_runtime_native import FeedRuntimeTests

fixture=FeedRuntimeTests('test_complete_delivery_commit_rollback_retry_and_reader_refusal')
fixture.info=SimpleNamespace(connection_uri=sys.argv[1]);fixture.setUp()
connection,host,assembly,tx=fixture.enrolled()
import psycopg
fixture.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(fixture.installation.registrar_role)))
created,original_input,request=fixture.run_group(assembly,tx,(fixture.create(),),'upgrade-original')
identity=created.response.semantic.results[0].identity
host.detach();connection.commit()
connection,host,assembly,tx=fixture.consumer()
replay=assembly.apply_in_transaction(tx,original_input,request,documents=fixture.documents,bun_executable='/opt/homebrew/bin/bun')
assert isinstance(replay,Ok)
token=replay.value.response.receipt_token
report=assembly.report_in_transaction(tx).value.original_bytes
revision=fixture.read_page(assembly,tx);fixture.ack(assembly,tx,revision)
page=fixture.read_page(assembly,tx)
if hasattr(assembly,'acknowledge_feed_with_receipt_in_transaction'):
 receipt=assembly.acknowledge_feed_with_receipt_in_transaction(tx,page,destination_id='upgrade-test',request_sha256='a'*64,publication_id='original',receipt_bytes=b'original destination receipt')
 assert isinstance(receipt,Ok)
else:fixture.ack(assembly,tx,page)
host.detach();connection.commit()
Path(sys.argv[2]).write_bytes(pickle.dumps((fixture.documents,original_input,request,identity,token,report,page,fixture.create(label='after',value='after'))))
# The parent owns this local cluster; close all clients without dropping its facts.
for connection,host in fixture.consumer_connections:
 host.detach();connection.close()
fixture.host.detach();fixture.admin.close()
