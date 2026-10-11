"""Native feasibility fixture only; no Truss cancellation implementation claim."""
import sys
sys.path.insert(0, '/private/tmp/truss-main-integration-20261010/packages/python/src')
sys.path.insert(0, '/private/tmp/truss-main-integration-20261010/packages/python/tests')
sys.path.append('/private/tmp/truss-pg8000-runtime-env/lib/python3.11/site-packages')
import json, socket, struct, time
from concurrent.futures import ThreadPoolExecutor
from test_native_pg8000 import NativeBoundaryFixture
from truss._native_pg8000 import NativeBoundary

class Fixture(NativeBoundaryFixture): pass
Fixture.setUpClass()
fixture=Fixture();fixture.setUp();observer=None
try:
 b=fixture.boundary;c=fixture.connection
 observer=Fixture.Connection(**Fixture.kwargs)
 pid=b.run('SELECT pg_catalog.pg_backend_pid()')[0][0]
 b.run('CREATE TEMP TABLE cancel_prior(value text)')
 b.run('BEGIN');b.run("INSERT INTO cancel_prior VALUES ('host-before')")
 b.run("SET LOCAL statement_timeout='5s'");b.run('SAVEPOINT cancel_operation')
 with ThreadPoolExecutor(max_workers=1) as worker:
  future=worker.submit(b.run,'SELECT pg_catalog.pg_sleep(4)')
  active=False
  for _ in range(80):
   rows=observer.run('SELECT state, wait_event FROM pg_catalog.pg_stat_activity WHERE pid=:pid',pid=pid)
   if rows==[['active','PgSleep']]:active=True;break
   if future.done():break
   time.sleep(0.01)
  assert active,'Fixture did not observe original native sleep'
  peer=c._usock.getpeername();key=c._backend_key_data
  assert c._usock.family==socket.AF_UNIX and type(key) is bytes and len(key)==8
  started=time.monotonic()
  with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as channel:
   channel.settimeout(2)
   channel.connect(peer)
   channel.sendall(struct.pack('!II',16,80877102)+key)
   assert channel.recv(1)==b'','Expected cancellation channel EOF'
  eof=True
  state=None
  try:future.result(timeout=3)
  except Exception as error:
   fields=error.args[0] if error.args and type(error.args[0]) is dict else {}
   state=fields.get('C')
  call=b.last_call
  assert state=='57014' and call.capture_complete and call.final_status==b'E'
  elapsed=time.monotonic()-started
 b.run('ROLLBACK TO SAVEPOINT cancel_operation');b.run('RELEASE SAVEPOINT cancel_operation')
 rows=b.run('SELECT value FROM cancel_prior');assert rows==[['host-before']]
 b.run('COMMIT');assert b.last_call.final_status==b'I'
 receipt={'scope':'PG16.15 Unix cancellation feasibility; manually coordinated native fixture, not Truss cancellation API','cancelSocketEOF':eof,'originalCallDrained':True,'sqlState':state,'failedTransactionStatus':'E','originalCallCaptureComplete':call.capture_complete,'elapsedSeconds':round(elapsed,6),'operationRollbackConfirmed':True,'earlierHostWritePreserved':True,'hostCommitConfirmed':True,'secretMaterialRetainedInReceipt':False,'publicC02Complete':False}
 print(json.dumps(receipt,indent=2))
finally:
 if observer is not None:observer.close()
 fixture.tearDown();Fixture.tearDownClass()
