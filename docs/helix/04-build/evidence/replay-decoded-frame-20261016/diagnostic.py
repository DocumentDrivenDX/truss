"""Disposable test-only PostgreSQL function timing of the original workload."""
import json,unittest
from pathlib import Path
import test_group_capacity_native as base
class CapacityFunctionCost(base.GroupCapacityTests):
    for _name in tuple(n for n in dir(base.GroupCapacityTests) if n.startswith('test_')):locals()[_name]=None
    def consumer(self,*args,**kwargs):
        self.admin.execute("ALTER ROLE consumer SET track_functions='all'")
        return super().consumer(*args,**kwargs)
    def test_original_1024_workflow(self):
        try:
            base.GroupCapacityTests.test_1024_real_creates_updates_replay_and_ordered_public_readback(self)
        finally:
            self.admin.execute('SELECT pg_stat_clear_snapshot()')
            rows=self.admin.execute('SELECT schemaname,funcname,calls,total_time,self_time FROM pg_stat_user_functions ORDER BY self_time DESC').fetchall()
            Path('/private/tmp/truss-capacity-function-cost-20261016.json').write_text(json.dumps({'scope':'Test-only function timings, complete original1024 create/update/commit/replay/readback workload; diagnostic overhead prevents isolated performance qualification','functions':rows},indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
