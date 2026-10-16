"""Supplied-fixture projection checks only; no native or semantic admission claim."""
import contextlib,hashlib,io,json, pathlib,unittest
import truss._current_disclosure_facts as implementation
import test_current_disclosure_graphs as tests
source_path=pathlib.Path(implementation.__file__)
source=source_path.read_text()
method='test_projection_preserves_typed_composite_keys_and_occurrences_under_permutation'
mutants={
 'stringified-composite-key':("'key':fact['key']","'key':str(fact['key'])"),
 'collapsed-parallel-witness':("'id':edge_id","'id':'90'"),
 'erased-relationship-identity':("relationship,endpoints=selected[relationship_id]","relationship,endpoints=selected['31']"),
}
results=[]
original=tests._capture_graphs
try:
 for name,replacement in [('baseline',None),*mutants.items()]:
  changed=source
  if replacement:
   old,new=replacement
   assert changed.count(old)==1,(name,changed.count(old))
   changed=changed.replace(old,new)
  namespace=dict(implementation.__dict__)
  exec(compile(changed,str(source_path),'exec'),namespace)
  tests._capture_graphs=namespace['_capture_graphs']
  output=io.StringIO()
  with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
   result=unittest.TextTestRunner(stream=output).run(unittest.TestSuite([tests.GraphCaptureTests(method)]))
  passed=result.wasSuccessful()
  assert passed==(replacement is None),(name,output.getvalue())
  results.append({'name':name,'successful':passed,'failures':len(result.failures),'errors':len(result.errors),'output':output.getvalue()})
finally:
 tests._capture_graphs=original
print(json.dumps({'scope':'supplied metadata and cursor; no native or semantic admission; no case promotion',
 'sourceSha256':hashlib.sha256(source.encode()).hexdigest(),
 'testSha256':hashlib.sha256(pathlib.Path(tests.__file__).read_bytes()).hexdigest(),
 'factPermutations':6,'edgePermutations':6,'combinations':36,'results':results},indent=2))
