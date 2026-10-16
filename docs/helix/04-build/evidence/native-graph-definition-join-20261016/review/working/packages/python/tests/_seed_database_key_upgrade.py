"""Seed genuine predecessor key bytes/receipts using the predecessor package."""
import os,pickle,sys
from pathlib import Path
from types import SimpleNamespace
from truss.groups import GroupSuccess
from test_group_create_native import PublicCreateGroupTests
import truss

assert Path(truss.__file__).resolve().is_relative_to(Path(os.environ['TRUSS_DB_KEY_PREDECESSOR']).resolve())
fixture=PublicCreateGroupTests('test_create_commit_read_and_original_durable_replay')
fixture.info=SimpleNamespace(connection_uri=sys.argv[1]);fixture.setUp()
c,h,a,t=fixture.ready()
input,request=fixture.input(a,t,(fixture.create(label='legacy-é',value='legacy-value'),))
created=fixture.apply(a,t,input,request);assert isinstance(created,GroupSuccess)
h.detach();c.commit()
keys=fixture.admin.execute('SELECT storage_row_id,namespace_bytes,key_bytes,original_context_bytes FROM truss.object_key_bucket ORDER BY storage_row_id').fetchall()
reservations=fixture.admin.execute('SELECT storage_row_id,namespace_bytes,key_bytes,original_reservation_bytes FROM truss.object_key_reservation_bucket ORDER BY storage_row_id').fetchall()
Path(sys.argv[2]).write_bytes(pickle.dumps((fixture.documents,created.response.semantic.results[0].identity,keys,reservations)))
for connection,host in fixture.consumer_connections:host.detach();connection.close()
fixture.host.detach();fixture.admin.close()
