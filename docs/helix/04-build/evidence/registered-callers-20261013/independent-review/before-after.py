"""Exact retained snapshot AST before/final; comparison-only and no native proof."""
from pathlib import Path
import ast,json,hashlib
from truss import _security_catalog_subject_installation as m
OUT=Path(__file__).parent;ROOT=Path('/private/tmp/truss-security-main-integration')
before=OUT/'installer-observed.py';after=ROOT/'packages/python/src/truss/_security_catalog_subject_installation.py'
class Spoof(str):
 def __eq__(self,other):return True
 def __ne__(self,other):return False
records=[]
for label,path in [('observed-before',before),('final',after)]:
 tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='snapshot_catalog_subjects')
 env={'PendingCatalogSubjects':m.PendingCatalogSubjects,'_SOURCE_SHA256':m._SOURCE_SHA256};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'),env)
 for field,value in [('source_sha256',Spoof('foreign-source')),('status',Spoof('not-pending'))]:
  kwargs={'installation_id':'installation','source_sha256':m._SOURCE_SHA256,'bindings':((1,'s1'),)};kwargs[field]=value
  try:r=env['snapshot_catalog_subjects'](m.PendingCatalogSubjects(**kwargs));accepted=True;retained=type(r.source_sha256).__name__
  except ValueError:accepted=False;retained=None
  assert accepted==(label=='observed-before')
  records.append({'version':label,'field':field,'accepted':accepted,'retainedSourceHashType':retained})
 verifier=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify_registered_catalog_subjects_with_cursor')
 queries=[n.args[1].value for n in ast.walk(verifier) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_text_rows']
 unqualified=any('::text' in q for q in queries);assert unqualified==(label=='observed-before')
 records.append({'version':label,'unqualifiedTextCasts':unqualified,'queries':queries})
result={'scope':'Actual retained pre-fix/final snapshot AST and verifier SQL strings. String-subclass controls are comparison/custody evidence only. Native hostile-domain execution is parent-retained evidence, not replayed here.','controls':records,'sourceDigests':{label:hashlib.sha256(path.read_bytes()).hexdigest() for label,path in [('observed-before',before),('final',after)]}}
(OUT/'before-after-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'snapshotPairs':2,'queryPair':1,'passed':True}))
