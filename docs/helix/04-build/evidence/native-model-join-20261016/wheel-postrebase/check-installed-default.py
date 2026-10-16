from pathlib import Path
import sys,importlib.abc,unittest,json
root=Path(__file__).parent;installed=root/'installed';sys.path[:0]=[str(installed),'/private/tmp/truss-disclosure-main-integration-20261016/packages/python/tests'];attempts=[]
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname=='weft' or fullname.startswith('weft.'):
   attempts.append(fullname);raise ModuleNotFoundError('Optional Weft intentionally unavailable')
sys.meta_path.insert(0,Block());import truss,truss._native_model_correspondence as module,truss._owner_evidence_json as codec
assert Path(truss.__file__).is_relative_to(installed) and Path(module.__file__).is_relative_to(installed) and Path(codec.__file__).is_relative_to(installed)
assert not hasattr(truss,'NativeModelCorrespondence')
import test_native_model_correspondence as tests
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests));assert result.wasSuccessful() and result.testsRun==14 and len(result.skipped)==3 and not attempts
r={'loadedPackage':truss.__file__,'joinModule':module.__file__,'decoderModule':codec.__file__,'defaultTests':14,'passed':11,'skipped':3,'weftImportAttempts':attempts,'noRootExport':True,'nativeAuthority':False};(root/'installed-default.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
