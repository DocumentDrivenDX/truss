"""Original UMF table archive membership counterexamples; not a complete verifier."""
import hashlib,importlib.metadata,json,sys,tempfile
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import pg8000.native,pgserver
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
out=HERE/'installation-archive-membership-native.json'
if out.exists():raise SystemExit('Receipt exists')
source=ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql';original=source.read_bytes()
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15':raise ValueError('Pinned runtime required')
expected=tuple((role,'fixture:'+role,('opaque administrative fixture '+role).encode()) for role in ('bundle','expected_inventory','installed_inventory','input','marker'))
checks=[];c=None
with tempfile.TemporaryDirectory(prefix='truss-archive-membership-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
 try:
  uri=urlparse(server.get_uri());opts=parse_qs(uri.query);host=opts.get('host',[uri.hostname])[0];port=int(opts.get('port',[uri.port or 5432])[0])
  c=pg8000.native.Connection(user='postgres',database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=30)
  version=c.run('SHOW server_version')[0][0]
  if version!='16.15':raise ValueError('Native version mismatch')
  c.run(original.decode());c.run('BEGIN')
  c.run("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0','fixture-installation','fixture-layout',decode(repeat('00',32),'hex'),'fixture-profile',decode(repeat('11',32),'hex'),'fixture-database','truss','2030-01-01T00:00:00Z','2030-01-01T00:00:00Z')")
  def insert(role,identity,value):
   c.run("INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('fixture-installation',:role,:identity,:value,sha256(convert_to(CAST(:identity AS text),'UTF8')))",role=role,identity=identity,value=value)
  for entry in expected:insert(*entry)
  def observe():
   rows=c.run("SELECT artifact_role,artifact_identity,artifact_bytes,encode(artifact_sha256,'hex'),encode(artifact_identity_sha256,'hex') FROM truss.installation_archive WHERE installation_id='fixture-installation' ORDER BY archive_row_id")
   values=tuple((role,identity,bytes(value)) for role,identity,value,bytehash,idhash in rows)
   for role,identity,value,bytehash,idhash in rows:
    if hashlib.sha256(value).hexdigest()!=bytehash or hashlib.sha256(identity.encode()).hexdigest()!=idhash:raise ValueError('Original digest correspondence missing')
   return values
  before=observe()
  if before!=expected:raise ValueError('Complete fixture archive mismatch')
  checks.append({'id':'complete-fixture-archive-original-bytes','members':[[role,identity,value.hex()] for role,identity,value in before],'completeReleaseQualified':False})
  for kind in ('missing','duplicate','changed','extra'):
   c.run('SAVEPOINT archive_drift')
   if kind=='missing':c.run("DELETE FROM truss.installation_archive WHERE artifact_identity='fixture:input'")
   elif kind=='duplicate':insert(*expected[0])
   elif kind=='changed':c.run("UPDATE truss.installation_archive SET artifact_bytes=decode('ff','hex') WHERE artifact_identity='fixture:input'")
   else:insert('input','fixture:extra',b'extra')
   c.run('SET CONSTRAINTS ALL IMMEDIATE');actual=observe()
   if actual==expected or c.run('SELECT count(*) FROM truss.installation_marker')[0][0]!=1:raise ValueError('Marker/membership counterexample missing')
   checks.append({'id':'native-archive-'+kind+'-with-marker','rows':len(actual),'markerPresent':True,'fixtureMembershipMatches':False,'constraintsCheckedImmediately':True})
   c.run('ROLLBACK TO SAVEPOINT archive_drift');c.run('RELEASE SAVEPOINT archive_drift')
   if observe()!=before:raise ValueError('Original archive rollback differs')
   checks.append({'id':'archive-'+kind+'-rollback','originalBytesExact':True})
  c.run('ROLLBACK')
 finally:
  if c is not None:c.close()
  server.cleanup()
if source.read_bytes()!=original:raise ValueError('Source drift')
r={'scope':'Native original UMF-exported installation archive table and opaque administrative fixture membership; not installer/status/verifier or release qualification','serverVersion':version,'observations':checks,'sourceSha256':{str(source.relative_to(ROOT)):hashlib.sha256(original).hexdigest()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'installationQualified':False,'limitations':['Five opaque fixture artifacts do not represent a registered complete release or actual inventory/receipt','Administrative DML counterexamples, not ordinary-writer bypass or security qualification','Complete release membership, native observer authority/cut/account and public APIs remain missing']}
with out.open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'installationQualified':False}))
