import json,subprocess,unittest
from pathlib import Path
import test_group_capacity_native as base
report={'scope':'Observed stock PostgreSQL function counters; registration and completed workload phases included. Cancelled calls may be missing; nested total times overlap. Not capacity/speedup qualification.','sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'statementTimeoutMs':10000,'operationTimeoutMs':30000,'tracking':'all','consumerSettings':[]}
class Profile(base.GroupCapacityTests):
    def install(self):
        super().install()
        self.admin.execute("ALTER ROLE consumer SET track_functions='all'")
    def consumer(self):
        value=super().consumer()
        observed=value[0].execute('SHOW track_functions').fetchone()[0]
        report['consumerSettings'].append(observed)
        self.assertEqual(observed,'all')
        return value
    def tearDown(self):
        try:
            for connection,host in self.consumer_connections:
                host.detach()
                if not connection.closed:
                    connection.rollback();connection.close()
            self.admin.rollback()
            self.admin.execute('SELECT pg_stat_clear_snapshot()')
            rows=self.admin.execute("SELECT schemaname,funcname,calls,total_time,self_time FROM pg_stat_user_functions WHERE schemaname='truss' ORDER BY self_time DESC,funcname").fetchall()
            report['observedFunctions']=[dict(zip(('schema','function','calls','totalTimeMs','selfTimeMs'),r)) for r in rows]
            report['serverVersion']=self.admin.execute('SHOW server_version').fetchone()[0]
        except Exception as exc:
            report['captureError']=str(exc)
            raise
        finally:
            try:super().tearDown();report['fixtureCleanup']='completed'
            except Exception as exc:report['cleanupError']=str(exc);raise
            finally:Path('/private/tmp/truss-capacity-function-profile-report-20261016.json').write_text(json.dumps(report,indent=2)+'\n')
suite=unittest.TestSuite([Profile('test_1024_real_creates_updates_replay_and_ordered_public_readback')]);result=unittest.TextTestRunner(verbosity=2).run(suite)
report.update(testPassed=result.wasSuccessful(),failures=len(result.failures),errors=len(result.errors),testsRun=result.testsRun)
Path('/private/tmp/truss-capacity-function-profile-report-20261016.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if result.wasSuccessful() else 1)
