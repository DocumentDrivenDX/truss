import importlib.util,sys,io,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('truss._epoch_descriptor_baseline','/private/tmp/epoch-descriptor-before-fix.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
import test_psycopg_epoch_cut_native as cases
cases._run_fenced_epoch_operation=module._run_fenced_epoch_operation
cases._EpochComparison=module._EpochComparison
output=io.StringIO();suite=unittest.TestSuite([cases.PsycopgEpochCutNativeTests('test_foreign_epoch_oid_refuses_before_custom_row_loader')])
result=unittest.TextTestRunner(stream=output).run(suite)
raw=output.getvalue();print(raw)
if len(result.failures)!=1 or result.errors or 'Lists differ: [True] != []' not in raw:raise AssertionError('Historical wrong-OID load counterexample missing')
print('Confirmed historical foreign Loader.load invocation before descriptor refusal')
