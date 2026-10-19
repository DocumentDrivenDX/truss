# SPDX-License-Identifier: MIT OR Apache-2.0
"""Administrative native catalog-cut feasibility; no protected provider or authority."""
import hashlib,json,re,sys,threading,time
from pathlib import Path
input=json.loads(sys.stdin.read());sys.path.insert(0,input['capturedModules'])
from pg8000.native import Connection
observations=[];folder=Path(input['evidence']);source=Path(input['source']).read_text()
def connect(database='postgres'):return Connection(user='postgres',unix_sock=input['unixSocket'],database=database,ssl_context=False,timeout=5)
def check(name,expected,observed):
 observations.append({'id':name,'expected':expected,'observed':observed})
 if type(expected) is not type(observed) or expected!=observed:raise AssertionError(name)
def image(con,label):
 rows=con.run(source);check(label+':one-original-result',True,len(rows)==1 and type(rows[0][0]) is str)
 b=rows[0][0].encode();(folder/(label+'.image.json')).write_bytes(b);return b
sha=lambda b:hashlib.sha256(b).hexdigest()
sections=re.findall("SELECT '([^']+)'::pg_catalog.text AS section",source)
# Explicit versioned view/aggregation expansion; no automatic interpretation.
names=sorted(set(sections)-{'pg_roles','foreign_routes'}|{'pg_authid','pg_foreign_data_wrapper','pg_foreign_server','pg_foreign_table','pg_user_mapping'})
lock='LOCK TABLE '+', '.join('pg_catalog.'+n for n in names)+' IN SHARE MODE'
(folder/'lock.sql').write_text(lock+';\n')
admin=connect();holder=connect();writer=connect()
try:
 check('exact-engine',[['180006']],admin.run("SELECT current_setting('server_version_num')::text"))
 admin.run("CREATE SCHEMA census_probe; CREATE TABLE census_probe.facts(value text); INSERT INTO census_probe.facts VALUES('original'); CREATE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 1::bigint'; CREATE ROLE census_actor; CREATE ROLE census_group;")
 admin.run('CREATE DATABASE census_other');other=connect('census_other')
 holder.run('BEGIN ISOLATION LEVEL READ COMMITTED');holder.run(lock)
 locks=holder.run("SELECT c.relname,l.mode,l.granted FROM pg_catalog.pg_locks l JOIN pg_catalog.pg_class c ON c.oid=l.relation WHERE l.pid=pg_catalog.pg_backend_pid() AND l.mode='ShareLock' ORDER BY c.relname")
 check('all-covered-catalog-locks',names,[r[0] for r in locks]);check('all-share-locks-granted',True,all(r[2] is True for r in locks))
 (folder/'locks.json').write_text(json.dumps(locks,indent=2)+'\n')
 baseline=image(holder,'held-baseline')
 actions=[('routine-body',"CREATE OR REPLACE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 333::bigint'"),('role-membership','GRANT census_group TO census_actor'),('role-default',"ALTER ROLE census_actor SET search_path='census_probe'"),('owner','ALTER FUNCTION census_probe.value() OWNER TO census_actor'),('column','ALTER TABLE census_probe.facts ADD COLUMN hidden text'),('policy','CREATE POLICY census_policy ON census_probe.facts USING (true)'),('foreign-route','CREATE FOREIGN DATA WRAPPER census_foreign NO HANDLER')]
 writer.run("SET lock_timeout='150ms'")
 for name,sql in actions:
  try:writer.run(sql);code='unexpected-success'
  except Exception as error:
   detail=error.args[0] if error.args and type(error.args[0]) is dict else {};code=detail.get('C','unqualified-error')
  check(name+':native-lock-conflict','55P03',code)
 writer.run("UPDATE census_probe.facts SET value='changed'")
 check('ordinary-data-not-source-write',[['changed']],writer.run('SELECT value FROM census_probe.facts'))
 check('held-source-stable',sha(baseline),sha(image(holder,'held-after-blocked-writes')))
 check('held-native-execution',[[1]],holder.run('SELECT census_probe.value()'))
 holder.run('COMMIT');writer.run(actions[0][1]);check('write-after-release',[[333]],writer.run('SELECT census_probe.value()'))
 # Decisive counterexample: a held lock cannot refresh an old MVCC snapshot.
 writer.run("CREATE OR REPLACE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 1::bigint'")
 holder.run('BEGIN ISOLATION LEVEL REPEATABLE READ');old=image(holder,'old-snapshot')
 writer.run(actions[0][1]);holder.run(lock)
 stale=image(holder,'old-snapshot-after-lock')
 check('stale-snapshot-survives-lock',sha(old),sha(stale))
 check('native-execution-sees-new-routine',[[333]],holder.run('SELECT census_probe.value()'))
 holder.run('COMMIT')
 holder.run('BEGIN ISOLATION LEVEL REPEATABLE READ');holder.run(lock)
 fresh=image(holder,'lock-before-first-snapshot');check('fresh-cut-detects-body-change',True,sha(fresh)!=sha(old))
 check('fresh-cut-native-execution',[[333]],holder.run('SELECT census_probe.value()'));holder.run('COMMIT')
 writer.run('BEGIN');writer.run("CREATE OR REPLACE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 444::bigint'")
 check('pending-writer-native-active',b'T'.hex(),writer._transaction_status.hex())
 writer_pid=writer.run('SELECT pg_catalog.pg_backend_pid()')[0][0]
 pending=admin.run("SELECT count(*)::text FROM pg_catalog.pg_locks WHERE pid=:pid AND relation='pg_catalog.pg_proc'::regclass AND mode='RowExclusiveLock' AND granted",pid=writer_pid)
 check('pending-writer-no-retained-proc-rowexclusive',[['0']],pending)
 holder.run('BEGIN ISOLATION LEVEL REPEATABLE READ');holder.run(lock)
 before_commit=image(holder,'lock-before-pending-writer-commit')
 check('lock-before-first-snapshot-pending-writer-old-source',True,b'SELECT 333::bigint' in before_commit and b'SELECT 444::bigint' not in before_commit)
 writer.run('COMMIT')
 after_commit=image(holder,'held-lock-after-pending-writer-commit')
 check('pending-commit-stale-held-image',sha(before_commit),sha(after_commit))
 check('pending-commit-current-native-execution',[[444]],holder.run('SELECT census_probe.value()'))
 remaining=holder.run("SELECT count(*)::text FROM pg_catalog.pg_locks WHERE pid=pg_catalog.pg_backend_pid() AND mode='ShareLock' AND granted")
 check('all-catalog-locks-still-held',[[str(len(names))]],remaining)
 holder.run('COMMIT')
 # A participating writer's transaction lock survives catalog statement end.
 key=57294010831
 writer.run('BEGIN');writer.run('SELECT pg_catalog.pg_advisory_xact_lock(:key)',key=key)
 writer.run("CREATE OR REPLACE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 555::bigint'")
 holder_pid=holder.run('SELECT pg_catalog.pg_backend_pid()')[0][0]
 holder.run('BEGIN ISOLATION LEVEL READ COMMITTED');thread_errors=[]
 def acquire():
  try:holder.run('SELECT pg_catalog.pg_advisory_xact_lock_shared(:key)',key=key)
  except BaseException as error:thread_errors.append(str(error))
 thread=threading.Thread(target=acquire);thread.start();deadline=time.monotonic()+3
 while not admin.run("SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_locks WHERE pid=:pid AND locktype='advisory' AND mode='ShareLock' AND NOT granted)",pid=holder_pid)[0][0]:
  if time.monotonic()>deadline:raise TimeoutError('Participating writer barrier wait not observed')
  time.sleep(.01)
 check('participating-writer-blocks-reader',True,thread.is_alive())
 writer.run('COMMIT');thread.join(5);check('writer-drain-completes-reader',False,thread.is_alive());check('writer-drain-no-driver-error',[],thread_errors)
 drained=image(holder,'cooperative-drained-current-source')
 check('post-barrier-read-committed-source-current',True,b'SELECT 555::bigint' in drained)
 check('post-barrier-read-committed-execution',[[555]],holder.run('SELECT census_probe.value()'))
 writer.run('BEGIN')
 try:writer.run('SELECT pg_catalog.pg_advisory_xact_lock(:key)',key=key);code='unexpected-success'
 except Exception as error:code=error.args[0].get('C','unqualified-error') if error.args and type(error.args[0]) is dict else 'unqualified-error'
 check('reader-barrier-blocks-new-participating-writer','55P03',code);writer.run('ROLLBACK')
 writer.run("CREATE OR REPLACE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 666::bigint'")
 bypassed=image(holder,'unparticipating-writer-bypass')
 check('unparticipating-administrative-writer-bypasses-barrier',[[666]],holder.run('SELECT census_probe.value() AS bypass_value'))
 check('unparticipating-writer-source-changes',True,sha(bypassed)!=sha(drained))
 check('cross-database-membership-initial',[[False]],holder.run("SELECT pg_catalog.pg_has_role('census_actor','census_group','MEMBER')"))
 other.run('BEGIN');other.run('SELECT pg_catalog.pg_advisory_xact_lock(:key)',key=key)
 check('same-key-other-database-lock-granted',[[True]],other.run("SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_locks WHERE pid=pg_catalog.pg_backend_pid() AND locktype='advisory' AND mode='ExclusiveLock' AND granted)"))
 other.run('GRANT census_group TO census_actor');other.run('COMMIT')
 cross=image(holder,'cross-database-shared-role-change')
 check('cross-database-shared-source-changes',True,sha(cross)!=sha(bypassed))
 check('cross-database-membership-now-visible',[[True]],holder.run("SELECT pg_catalog.pg_has_role('census_actor','census_group','MEMBER')"))
 holder.run('COMMIT');writer.run('BEGIN');writer.run('SELECT pg_catalog.pg_advisory_xact_lock(:key)',key=key);writer.run('COMMIT')
 check('reader-release-permits-participating-writer',b'I'.hex(),writer._transaction_status.hex())
 # Endpoint source equality can hide an intervening native execution (ABA).
 holder.run('BEGIN ISOLATION LEVEL READ COMMITTED')
 aba_before=image(holder,'aba-before')
 writer.run("CREATE OR REPLACE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 777::bigint'")
 aba_middle=image(holder,'aba-middle')
 check('aba-intermediate-source-differs',True,sha(aba_middle)!=sha(aba_before))
 check('aba-intermediate-native-call',[[777]],holder.run('SELECT census_probe.value() AS aba_middle_value'))
 writer.run("CREATE OR REPLACE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 666::bigint'")
 aba_after=image(holder,'aba-after')
 check('aba-endpoint-source-images-equal',sha(aba_before),sha(aba_after))
 check('aba-restored-native-call',[[666]],holder.run('SELECT census_probe.value() AS aba_restored_value'))
 # Source-only census deliberately omits application data values; this fixture
 # table is not an actual authorization provider.
 fact_before=holder.run('SELECT value FROM census_probe.facts')
 writer.run("UPDATE census_probe.facts SET value='changed-without-source-change'")
 check('application-data-change-native-visible',[['changed-without-source-change']],holder.run('SELECT value FROM census_probe.facts'))
 check('source-census-omits-application-data-change',sha(aba_after),sha(image(holder,'application-data-changed-source-equal')))
 writer.run("UPDATE census_probe.facts SET value='changed'")
 check('application-data-restored',fact_before,holder.run('SELECT value FROM census_probe.facts'))
 holder.run('COMMIT')
 (folder/'native.json').write_text(json.dumps({'status':'component-passed','observations':observations,'catalogs':names,'scope':'Excluded administrative PostgreSQL18.6 catalog ShareLock feasibility and native stale-snapshot and uncommitted writer counterexamples. Materialized pg8000 rows are not protected bounded original ingress. Cooperative transaction advisory barrier with fresh READ COMMITTED statement after acquisition; native lock wait/drain and blocking tested. Native two-commit routine ABA returns777 between byte-identical666 source images. Ordinary application-data changes are omitted by source census; the fixture data table is not an actual authorization provider. Tested finite DDL set only; no all-writer/catalog/extension/runtime configuration completeness, provider authentication, final authority/data cut, cooperative handback or backend acceptance.'},indent=2)+'\n')
 print(json.dumps({'status':'component-passed','observations':len(observations)}))
except BaseException as error:
 (folder/'native-failure.json').write_text(json.dumps({'status':'failed','observations':observations,'error':str(error)},indent=2)+'\n');raise
finally:
 writer.close()
 if 'other' in globals():other.close()
 if 'thread' in globals():thread.join(5)
 holder.close();admin.close()
