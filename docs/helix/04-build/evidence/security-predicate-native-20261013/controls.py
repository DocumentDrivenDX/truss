import hashlib,json,pathlib,re,subprocess,random
from truss.catalog_runtime import _release
root=pathlib.Path('/private/tmp/truss-security-main-integration')
assets=root/'packages/python/src/truss/_catalog_runtime'
manifest,digest,sources=_release()
assert manifest['releaseId']=='truss-catalog-runtime/0.37-candidate'
assert digest==hashlib.sha256((assets/'manifest.json').read_bytes()).hexdigest()
verified=[]
for name,expected in manifest['files'].items():
 assert hashlib.sha256((assets/name).read_bytes()).hexdigest()==expected,name
 verified.append(name)
original=subprocess.check_output(['git','show','HEAD:packages/python/src/truss/_catalog_runtime/manifest.json'],cwd=root)
assert (assets/'upgrade-source-036.json').read_bytes()==original
assert json.loads(original)['releaseId']=='truss-catalog-runtime/0.36-candidate'
replacements=[]
for source in sources:
 replacements.extend(re.findall(r"CREATE FUNCTION\s+truss\.\w+[\s\S]*?\bAS\s+(?:\$\$[\s\S]*?\$\$|'(?:[^']|'')*')\s*;",source))
assert len(replacements)==120
helper=[r for r in replacements if r.startswith('CREATE FUNCTION truss.valid_scalar_property(')]
assert len(helper)==1
assert 'IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp' in helper[0]
assert '9223372036854775807' in helper[0] and '9223372036854775808' in helper[0]
assert 'COLLATE pg_catalog."C"' in helper[0]
# A mathematical translation check, not execution or refinement of PostgreSQL.
rng=random.Random(370013)
tokens=[str(x) for x in range(-1000,1001)]+[str(x) for p in (-(2**63),2**63-1) for x in range(p-1000,p+1001)]
tokens += [str(rng.randrange(-(10**22),10**22)) for _ in range(10000)]
tokens += ['-0','0','00','-00','01','+1','1.0','1e0','','-',' 0','0 ','1\n','１２','1'*10000]
for token in tokens:
 lexical=bool(re.fullmatch(r'-?(0|[1-9][0-9]*)',token))
 if lexical:
  magnitude=token[1:] if token.startswith('-') else token
  limit='9223372036854775808' if token.startswith('-') else '9223372036854775807'
  compared=len(magnitude)<19 or len(magnitude)==19 and magnitude<=limit
  expected= (len(magnitude)<=19 and -(2**63)<=int(token)<=2**63-1)
  assert compared==expected,token
paths=['packages/python/src/truss/catalog_runtime.py','packages/python/src/truss/_catalog_runtime/manifest.json','packages/python/src/truss/_catalog_runtime/upgrade-source-036.json','packages/python/src/truss/_catalog_runtime/scalars.sql','packages/python/src/truss/_catalog_runtime/groups.sql','packages/python/src/truss/_catalog_runtime/operations.sql','packages/python/src/truss/_catalog_runtime/read.sql','packages/python/src/truss/_catalog_runtime/query.sql','packages/python/src/truss/_catalog_runtime/migrations.sql','packages/python/src/truss/_catalog_runtime/runtime.sql','packages/python/tests/test_core08_catalog_native.py','packages/python/tests/test_security_predicate_native.py']
result={'scope':'Read-only source review and actual Python release loader, source inventory/hash controls; lexical comparison independently translated to Python, not a PostgreSQL execution/refinement proof. No native database mutation.', 'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'releaseId':manifest['releaseId'],'manifestDigest':digest,'manifestFilesVerified':len(verified),'original036ManifestExact':True,'extractedReplacementCount':len(replacements),'translatedLexicalCases':len(tokens),'sourceDigests':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}}
path=pathlib.Path('/private/tmp/truss-runtime037-astra-20261013/controls.json');path.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='sourceDigests'},indent=2))
