"""Original UMF table archive membership counterexamples; not a complete verifier."""
import hashlib,importlib.metadata,json,sys,tempfile
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import pg8000.native,pgserver
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
out=HERE/'installation-archive-correspondence-expected-native.json'
if out.exists():raise SystemExit('Receipt exists')
source=ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql';original=source.read_bytes()
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15':raise ValueError('Pinned runtime required')
expected=tuple((role,'fixture:'+role,('opaque administrative fixture '+role).encode()) for role in ('bundle','expected_inventory','installed_inventory','input','marker'))
sys.path.insert(0,str(ROOT/'packages/python/src'))
from truss._installation_archive import compare_archive_rows
component=ROOT/'packages/python/src/truss/_installation_archive.py';component_original=component.read_bytes()
class OriginalConnection(pg8000.native.Connection):
 def handle_COMMAND_COMPLETE(self,data,context):
  super().handle_COMMAND_COMPLETE(data,context);context.original_completion=data
checks=[];c=None
with tempfile.TemporaryDirectory(prefix='truss-archive-membership-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
 try:
  uri=urlparse(server.get_uri());opts=parse_qs(uri.query);host=opts.get('host',[uri.hostname])[0];port=int(opts.get('port',[uri.port or 5432])[0])
  c=OriginalConnection(user='postgres',database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=30)
  version=c.run('SHOW server_version')[0][0]
  if version!='16.15':raise ValueError('Native version mismatch')
  c.run(original.decode());c.run('BEGIN')
  c.run("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0','fixture-installation','fixture-layout',decode(repeat('00',32),'hex'),'fixture-profile',decode(repeat('11',32),'hex'),'fixture-database','truss','2030-01-01T00:00:00Z','2030-01-01T00:00:00Z')")
  def insert(role,identity,value):
   c.run("INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('fixture-installation',:role,:identity,:value,sha256(convert_to(CAST(:identity AS text),'UTF8')))",role=role,identity=identity,value=value)
  for entry in expected:insert(*entry)
  def observe(expected_match=True):
   rows=c.run("SELECT archive_row_id::text AS archive_row_id,installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_sha256,artifact_identity_sha256 FROM truss.installation_archive WHERE installation_id='fixture-installation' ORDER BY archive_row_id")
   context=c._context;tag=context.original_completion
   if tag != ('SELECT '+str(len(rows))).encode()+b'\0' or [col['type_oid'] for col in context.columns]!=[25,25,25,25,17,17,17] or any(col['format']!=0 for col in context.columns):raise ValueError('Original native archive descriptor/completion mismatch')
   result=compare_archive_rows(tuple(col['name'] for col in context.columns),rows,'fixture-installation',expected,10,100000)
   if result.matches is not expected_match:raise ValueError('Independent expected correspondence verdict mismatch')
   checks.append({'id':'native-python-archive-correspondence-'+str(len(checks)),'rows':len(rows),'originalCompletionHex':tag.hex(),'descriptor':context.columns,'matches':result.matches,'originalCellsRetained':True})
   return tuple((row[2],row[3],row[4]) for row in result.original_rows)
  c.run('COMMIT');c.run('BEGIN')
  before=observe()
  if before!=expected:raise ValueError('Complete fixture archive mismatch')
  checks.append({'id':'complete-fixture-archive-original-bytes','members':[[role,identity,value.hex()] for role,identity,value in before],'completeReleaseQualified':False})
  for kind in ('missing','duplicate','changed','extra'):
   c.run('SAVEPOINT archive_drift')
   if kind=='missing':c.run("DELETE FROM truss.installation_archive WHERE artifact_identity='fixture:input'")
   elif kind=='duplicate':insert(*expected[0])
   elif kind=='changed':c.run("UPDATE truss.installation_archive SET artifact_bytes=decode('ff','hex') WHERE artifact_identity='fixture:input'")
   else:insert('input','fixture:extra',b'extra')
   c.run('SET CONSTRAINTS ALL IMMEDIATE');actual=observe(False)
   if actual==expected or c.run('SELECT count(*) FROM truss.installation_marker')[0][0]!=1:raise ValueError('Marker/membership counterexample missing')
   checks.append({'id':'native-archive-'+kind+'-with-marker','rows':len(actual),'markerPresent':True,'fixtureMembershipMatches':False,'constraintsCheckedImmediately':True})
   c.run('ROLLBACK TO SAVEPOINT archive_drift');c.run('RELEASE SAVEPOINT archive_drift')
   if observe()!=before:raise ValueError('Original archive rollback differs')
   checks.append({'id':'archive-'+kind+'-rollback','originalBytesExact':True})
  c.run('ROLLBACK')
  c.run('CREATE ROLE archive_observer_fixture LOGIN')
  c.run('GRANT USAGE ON SCHEMA truss TO archive_observer_fixture')
  c.run('GRANT SELECT ON truss.installation_marker,truss.installation_archive TO archive_observer_fixture')
  reader=pg8000.native.Connection(user='archive_observer_fixture',database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=30)
  query="SELECT artifact_role,artifact_identity,artifact_bytes FROM truss.installation_archive WHERE installation_id='fixture-installation' ORDER BY archive_row_id"
  try:
   rows=reader.run(query)
   if tuple((role,identity,bytes(value)) for role,identity,value in rows)!=expected:raise ValueError('Ordinary fixture observer full bytes differ')
   checks.append({'id':'ordinary-fixture-observer-full-archive','rows':len(rows),'originalBytesExact':True,'observerAuthorityQualified':False})
   c.run('REVOKE SELECT ON truss.installation_archive FROM archive_observer_fixture')
   try:reader.run(query)
   except pg8000.exceptions.DatabaseError as error:
    if error.args[0].get('C')!='42501':raise
    if reader.run('SELECT count(*) FROM truss.installation_marker')[0][0]!=1:raise ValueError('Readable marker missing')
    checks.append({'id':'revoked-archive-select-unavailable-with-readable-marker','sqlstate':'42501','markerPresent':True,'archiveObservation':'unavailable','archiveAbsentProven':False,'automaticRetry':False})
   else:raise ValueError('Revoked archive rights were accepted')
   c.run('GRANT SELECT ON truss.installation_archive TO archive_observer_fixture')
   rows=reader.run(query)
   if tuple((role,identity,bytes(value)) for role,identity,value in rows)!=expected:raise ValueError('Explicit restored observer bytes differ')
   checks.append({'id':'separate-explicit-read-after-right-restoration','originalBytesExact':True,'initializerReplay':False})
  finally:reader.close()
 finally:
  if c is not None:c.close()
  server.cleanup()
if source.read_bytes()!=original or component.read_bytes()!=component_original:raise ValueError('Source drift')
r={'scope':'Native original UMF-exported installation archive table and opaque administrative fixture membership; not installer/status/verifier or release qualification','serverVersion':version,'observations':checks,'sourceSha256':{str(source.relative_to(ROOT)):hashlib.sha256(original).hexdigest(),str(component.relative_to(ROOT)):hashlib.sha256(component_original).hexdigest()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'installationQualified':False,'limitations':['Five opaque fixture artifacts do not represent a registered complete release or actual inventory/receipt','Administrative DML counterexamples, not ordinary-writer bypass or security qualification','Complete release membership, native observer authority/cut/account and public APIs remain missing']}
with out.open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'installationQualified':False}))
