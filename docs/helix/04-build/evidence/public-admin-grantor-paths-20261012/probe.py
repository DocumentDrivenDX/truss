"""Actual ordinary-role grantor paths; observe before deriving profile claims."""
import json,unittest
from pathlib import Path
from truss import Ok,Error
import psycopg
from test_catalog_runtime_native import PublicCatalogRuntimeTests
observations=[]
class Probe(PublicCatalogRuntimeTests):
 def test_probe(self):
  self.install();connection,host,assembly,tx=self.consumer()
  for inherit,set_role in [(True,False),(False,True),(False,False),(True,True)]:
   self.admin.execute('CREATE ROLE grantor_path NOLOGIN;CREATE ROLE grantable_storage NOLOGIN')
   try:
    self.admin.execute('GRANT USAGE ON SCHEMA truss TO grantable_storage')
    self.admin.execute('GRANT SELECT(installation_id) ON truss.catalog_runtime_installation TO grantable_storage')
    self.admin.execute('GRANT grantable_storage TO grantor_path WITH ADMIN TRUE, INHERIT FALSE, SET FALSE')
    self.admin.execute(f'GRANT grantor_path TO consumer WITH INHERIT {inherit}, SET {set_role}')
    admitted=isinstance(assembly.status_in_transaction(tx),Ok)
    connection.execute('SAVEPOINT native_grantor')
    exposed=False;state=None
    try:
     if set_role:connection.execute('SET ROLE grantor_path')
     connection.execute('GRANT grantable_storage TO consumer WITH SET TRUE')
     if set_role:connection.execute('RESET ROLE')
     connection.execute('SET ROLE grantable_storage')
     exposed=len(connection.execute('SELECT installation_id FROM truss.catalog_runtime_installation').fetchall())==1
     connection.execute('RESET ROLE')
    except psycopg.Error as e:state=e.sqlstate
    finally:
     connection.execute('ROLLBACK TO SAVEPOINT native_grantor');connection.execute('RELEASE SAVEPOINT native_grantor')
    observations.append({'inherit':inherit,'set':set_role,'native_private_access':exposed,'native_refusal_sqlstate':state,'public_admitted':admitted})
   finally:
    self.admin.execute('REVOKE grantor_path FROM consumer')
    self.admin.execute('DROP OWNED BY grantor_path,grantable_storage;DROP ROLE grantor_path,grantable_storage')
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Probe('test_probe')]))
 if not result.wasSuccessful():raise SystemExit(1)
 Path(__file__).with_name('observed.json').write_text(json.dumps(observations,indent=2)+'\n')
