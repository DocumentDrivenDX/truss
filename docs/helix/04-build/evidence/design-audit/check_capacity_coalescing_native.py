"""Native deferred-check scheduling experiment, not Truss guards or installed state."""
import hashlib,importlib.metadata,json,sys,tempfile
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import pg8000.native,pg8000.exceptions,pgserver
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1]:raise SystemExit('Fresh receipt basename required')
out=HERE/sys.argv[1]
if out.exists():raise SystemExit('Receipt exists')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5':raise SystemExit('Original runtime/driver required')
checks=[]
def expect(name,expected,observed):
 if expected!=observed:raise ValueError(name+': mismatch')
 checks.append({'id':name,'expected':expected,'observed':observed})
with tempfile.TemporaryDirectory(prefix='truss-deferred-coalescing-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop');c=None
 try:
  uri=urlparse(server.get_uri());opts=parse_qs(uri.query);host=opts.get('host',[uri.hostname])[0];port=int(opts.get('port',[uri.port or 5432])[0])
  c=pg8000.native.Connection(user='postgres',database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=5)
  version=c.run('SHOW server_version')[0][0]
  if not version.startswith('16.15'):raise ValueError('Native version mismatch')
  for mode in ['first_only','generation']:
   # Closed source-only fixture names; no original Truss layout or routine edited.
   skip='m.verified>=0' if mode=='first_only' else 'm.verified=m.dirty'
   c.run(f'''CREATE SCHEMA {mode};
CREATE TABLE {mode}.inventory(id integer PRIMARY KEY,value integer NOT NULL);
CREATE TABLE {mode}.memo(singleton integer PRIMARY KEY CHECK(singleton=1),dirty bigint NOT NULL,verified bigint NOT NULL,scans integer NOT NULL);
INSERT INTO {mode}.memo VALUES(1,0,-1,0);
CREATE FUNCTION {mode}.invalidate() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 UPDATE {mode}.memo SET dirty=dirty+1 WHERE singleton=1; RETURN NEW; END $$;
CREATE TRIGGER invalidate AFTER INSERT OR UPDATE OR DELETE ON {mode}.inventory FOR EACH ROW EXECUTE FUNCTION {mode}.invalidate();
CREATE FUNCTION {mode}.check_all() RETURNS trigger LANGUAGE plpgsql AS $$ DECLARE m {mode}.memo%ROWTYPE; BEGIN
 SELECT * INTO STRICT m FROM {mode}.memo WHERE singleton=1;
 IF {skip} THEN RETURN NULL; END IF;
 IF EXISTS(SELECT 1 FROM {mode}.inventory WHERE value<0) THEN RAISE EXCEPTION 'fixture invalid inventory' USING ERRCODE='23514'; END IF;
 UPDATE {mode}.memo SET verified=dirty,scans=scans+1 WHERE singleton=1; RETURN NULL; END $$;
CREATE CONSTRAINT TRIGGER check_all AFTER UPDATE ON {mode}.memo DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION {mode}.check_all();''')
  for mode in ['first_only','generation']:
   c.run('BEGIN');c.run(f'INSERT INTO {mode}.inventory VALUES(1,1)')
   c.run('SET CONSTRAINTS ALL IMMEDIATE');c.run('SET CONSTRAINTS ALL DEFERRED')
   expect(mode+'-early-full-scan',[[1,1,1]],c.run(f'SELECT dirty,verified,scans FROM {mode}.memo'))
   c.run(f'UPDATE {mode}.inventory SET value=-1 WHERE id=1')
   if mode=='first_only':
    c.run('COMMIT');expect('broken-first-only-commits-invalid-row',[[-1]],c.run('SELECT value FROM first_only.inventory'))
   else:
    try:c.run('COMMIT')
    except pg8000.exceptions.DatabaseError as e:expect('generation-rechecks-later-write-at-commit','23514',e.args[0]['C'])
    else:raise ValueError('Expected invalid later write refusal')
    expect('failed-commit-restores-original-empty-inventory',[[0]],c.run('SELECT count(*) FROM generation.inventory'))
    expect('failed-commit-rolls-back-memo-and-work',[[0,-1,0]],c.run('SELECT dirty,verified,scans FROM generation.memo'))
  c.run('BEGIN');c.run('INSERT INTO generation.inventory VALUES(1,1)');c.run('SET CONSTRAINTS ALL IMMEDIATE');c.run('SET CONSTRAINTS ALL DEFERRED');c.run('UPDATE generation.inventory SET value=2 WHERE id=1');c.run('COMMIT')
  expect('valid-early-check-and-later-write-two-scans',[[2,2,2]],c.run('SELECT dirty,verified,scans FROM generation.memo'))
  expect('valid-later-write-committed',[[2]],c.run('SELECT value FROM generation.inventory'))
  c.run('BEGIN');c.run('INSERT INTO generation.inventory VALUES(2,1)');c.run('INSERT INTO generation.inventory VALUES(3,1)');c.run('UPDATE generation.inventory SET value=3 WHERE id=1');c.run('COMMIT')
  expect('three-deferred-events-one-additional-full-scan',[[5,5,3]],c.run('SELECT dirty,verified,scans FROM generation.memo'))
  c.run('BEGIN');c.run('SAVEPOINT failed_child');c.run('UPDATE generation.inventory SET value=-1 WHERE id=1')
  try:c.run('SET CONSTRAINTS ALL IMMEDIATE')
  except pg8000.exceptions.DatabaseError as e:expect('forced-check-child-failure','23514',e.args[0]['C'])
  else:raise ValueError('Expected forced invalid child refusal')
  c.run('ROLLBACK TO SAVEPOINT failed_child');c.run('RELEASE SAVEPOINT failed_child')
  expect('child-rollback-restores-generation-and-proof',[[5,5,3]],c.run('SELECT dirty,verified,scans FROM generation.memo'))
  c.run('UPDATE generation.inventory SET value=4 WHERE id=1');c.run('COMMIT')
  expect('surviving-child-followup-rechecked',[[6,6,4]],c.run('SELECT dirty,verified,scans FROM generation.memo'))
 finally:
  if c:c.close()
  server.cleanup()
receipt={'scope':'Native deferred-trigger scheduling/coalescing fixture and intentional first-only counterexample; not original Truss inventory/semantic guards','serverVersion':version,'observations':checks,'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'nativeTrussCorrespondenceReviewed':False,'installerReady':False,'acceptanceCasesPromoted':[],'limitations':['Fixture counter/generation is not installed Truss authority, issuer/security or cumulative native account','Committed memo scans roll back with PostgreSQL; original cumulative work must never refund on rollback','Generation invalidation must cover every original relevant write and be unforgeable before adoption','No concurrency/native work/overflow/cleanup/unknown-outcome or seven-body qualification','Truss resource-profile/layout extension and native invocation registration remain unresolved']}
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'installerReady':False}))
