import ast,unittest
from pathlib import Path
import test_security_helper_acl_native as tests
old=ast.parse(Path('/private/tmp/helper-acl-original-source.py').read_text())
function=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='_verify_helpers')
exec(compile(ast.Module(body=[function],type_ignores=[]),'original-helper-verifier','exec'),tests.source.subject.__dict__)
suite=unittest.TestSuite([tests.HelperAclNativeTests('test_public_execute_before_admission_refuses_without_setting_bypass')])
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
