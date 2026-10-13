import unittest,sys
from pathlib import Path
import truss
expected=Path('/private/tmp/truss-core08-keys-astra-20261013/wheel/truss/__init__.py')
assert Path(truss.__file__).resolve()==expected.resolve(),truss.__file__
print('Verified wheel import:',truss.__file__,flush=True)
suite=unittest.defaultTestLoader.loadTestsFromName('test_umf_key_tuples.OriginalUmfKeyTupleTests');result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())
