import json, subprocess, hashlib, sys
from pathlib import Path
from truss import LocalPostgres
sql="""\\set ON_ERROR_STOP off
CREATE TABLE dry_run_probe(id integer, label text, CONSTRAINT dry_run_unique UNIQUE(id) DEFERRABLE INITIALLY DEFERRED);
INSERT INTO dry_run_probe VALUES(0,'committed-before-preview');
BEGIN;
UPDATE dry_run_probe SET label='caller-pending-before-preview' WHERE id=0;
SAVEPOINT preview;
INSERT INTO dry_run_probe VALUES(1,'first'),(1,'second');
SET CONSTRAINTS dry_run_unique IMMEDIATE;
\\echo validator_sqlstate :SQLSTATE
SELECT label FROM dry_run_probe WHERE id=0;
\\echo aborted_read_sqlstate :SQLSTATE
ROLLBACK TO SAVEPOINT preview;
SELECT json_build_object('label',(SELECT label FROM dry_run_probe WHERE id=0),'previewRows',(SELECT count(*) FROM dry_run_probe WHERE id=1))::text;
SAVEPOINT timing_check;
INSERT INTO dry_run_probe VALUES(2,'mode-first'),(2,'mode-second');
\\echo restored_mode_insert_sqlstate :SQLSTATE
SET CONSTRAINTS dry_run_unique IMMEDIATE;
\\echo restored_mode_validator_sqlstate :SQLSTATE
ROLLBACK TO SAVEPOINT timing_check;
ROLLBACK;
SELECT json_build_object('label',(SELECT label FROM dry_run_probe WHERE id=0),'previewRows',(SELECT count(*) FROM dry_run_probe WHERE id=1))::text;
"""
if len(sys.argv) != 3:
    raise SystemExit('Require a fresh data directory and fresh receipt path')
data_directory, receipt_path = map(Path, sys.argv[1:])
if data_directory.exists() or receipt_path.exists():
    raise SystemExit('Refuse existing data directory or receipt before native startup')
if not receipt_path.parent.is_dir():
    raise SystemExit('Receipt parent must already exist')
with LocalPostgres(data_directory) as runtime:
 cmd=[str(runtime.psql_path),runtime.info.connection_uri,'-X','-q','-A','-t']
 r=subprocess.run(cmd,input=sql,text=True,capture_output=True,timeout=30)
 expected=['validator_sqlstate 23505','aborted_read_sqlstate 25P02','{"label" : "caller-pending-before-preview", "previewRows" : 0}','restored_mode_insert_sqlstate 00000','restored_mode_validator_sqlstate 23505','{"label" : "committed-before-preview", "previewRows" : 0}']
 assert r.returncode==0 and r.stdout.splitlines()==expected,(r.returncode,r.stdout,r.stderr)
 x={'schema':'truss-dry-run-native-savepoint-witness/0.1','serverVersion':runtime.info.server_version,'runtimeVersion':runtime.info.runtime_version,'command':cmd,'sql':sql,'exitCode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'independentExpectedLines':expected,'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Native PostgreSQL deferred unique validation and savepoint/outer rollback only; administrative fixture, not Truss guard, ordinary-role security, driver containment or dry-run API qualification'}
 x['dataDirectory']=str(data_directory)
 x['preflight']='Data directory and receipt absent before native startup; not a hostile filesystem race guarantee'
 with receipt_path.open('x') as output:
  output.write(json.dumps(x,indent=2)+'\n')
print('Native deferred violation, aborted read, local containment and outer rollback matched six independent observations')
