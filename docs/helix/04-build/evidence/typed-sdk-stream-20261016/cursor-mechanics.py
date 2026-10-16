import json, subprocess, pathlib, time
import psycopg
root=pathlib.Path('/private/tmp/sdk-cursor-mechanics-20261016'); pg='/opt/homebrew/opt/postgresql@18/bin/'
checks=[]; started=False
try:
 subprocess.run([pg+'initdb','-D',str(root/'data'),'-A','trust','--no-locale'],check=True,stdout=subprocess.DEVNULL)
 subprocess.run([pg+'pg_ctl','-D',str(root/'data'),'-l',str(root/'server.log'),'-o',f'-k {root} -p 55509 -h "" -c shared_buffers=32MB','-w','start'],check=True,stdout=subprocess.DEVNULL); started=True
 dsn=f'host={root} port=55509 dbname=postgres'
 with psycopg.connect(dsn,autocommit=True) as admin:
  admin.execute('CREATE ROLE ordinary LOGIN'); admin.execute('CREATE TABLE fixture(id integer primary key)'); admin.execute('INSERT INTO fixture SELECT generate_series(1,2500)'); admin.execute('GRANT SELECT ON fixture TO ordinary')
  for hold in [False,True]:
   with psycopg.connect(dsn+' user=ordinary',autocommit=True) as reader:
    reader.execute('BEGIN READ ONLY'); reader.execute('DECLARE owned NO SCROLL INSENSITIVE CURSOR '+('WITH HOLD' if hold else 'WITHOUT HOLD')+' FOR SELECT id FROM fixture ORDER BY id')
    first=reader.execute('FETCH FORWARD 1000 FROM owned').fetchall(); assert len(first)==1000
    if hold: reader.execute('COMMIT')
    admin.execute('INSERT INTO fixture VALUES (9999)')
    assert reader.execute('SELECT count(*) FROM fixture').fetchone()[0]==2501
    admin.execute('REVOKE SELECT ON fixture FROM ordinary')
    assert reader.execute("SELECT has_table_privilege(current_user,'fixture','SELECT')").fetchone()[0] is False
    remaining=reader.execute('FETCH FORWARD 2000 FROM owned').fetchall(); assert len(remaining)==1500 and remaining[-1][0]==2500
    checks.append({'hold':hold,'fixedSnapshotRows':2500,'freshRcCount':2501,'freshPrivilegeDenied':True,'portalStillFetchesAfterRevoke':True})
    reader.execute('CLOSE owned'); assert reader.execute("SELECT count(*) FROM pg_cursors WHERE name='owned'").fetchone()[0]==0
    if not hold: reader.execute('COMMIT')
    admin.execute('GRANT SELECT ON fixture TO ordinary'); admin.execute('DELETE FROM fixture WHERE id=9999')
  with psycopg.connect(dsn,autocommit=True) as conn:
   conn.execute('BEGIN'); conn.execute('INSERT INTO fixture VALUES (7777)')
   refused=conn.info.transaction_status != psycopg.pq.TransactionStatus.IDLE
   assert refused; conn.execute('COMMIT'); assert admin.execute('SELECT count(*) FROM fixture WHERE id=7777').fetchone()[0]==1
   checks.append({'foreignTransactionPreconditionRefused':True,'foreignWorkPreserved':True})
   conn.execute('BEGIN READ ONLY'); conn.execute('DECLARE early NO SCROLL CURSOR FOR SELECT id FROM fixture'); conn.execute('FETCH FORWARD 1 FROM early'); conn.execute('ROLLBACK'); assert conn.execute("SELECT count(*) FROM pg_cursors WHERE name='early'").fetchone()[0]==0
   checks.append({'rollbackClosesPortal':True})
finally:
 if started: subprocess.run([pg+'pg_ctl','-D',str(root/'data'),'-m','immediate','-w','stop'],check=True,stdout=subprocess.DEVNULL)
 (root/'result.json').write_text(json.dumps({'checks':checks,'ownedServerStopped':started,'scope':'PostgreSQL mechanics only; no Truss or SDK qualification'},indent=2)+'\n')
print(json.dumps(checks))
