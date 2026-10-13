"""Exact extracted current guard: descriptor-before-fetch and value controls."""
from pathlib import Path
from hashlib import sha256
from types import SimpleNamespace
from decimal import Decimal
import ast,json
SOURCE=Path('/private/tmp/truss-security-main-integration/scripts/security_catalog_read.py')
raw=SOURCE.read_bytes();tree=ast.parse(raw)
outer=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_owned_catalog_resource_read')
guard=next(n for n in outer.body if isinstance(n,ast.FunctionDef) and n.name=='guard')
expected=(b'identity',b'profile',1)
ns={'expected_guard':expected}
exec(compile(ast.fix_missing_locations(ast.Module(body=[guard],type_ignores=[])),str(SOURCE),'exec'),ns)
names=('installation_identity_bytes','policy_profile_bytes','generation')
oids=(17,17,20)
def description(names=names,oids=oids):return tuple(SimpleNamespace(name=n,type_code=o) for n,o in zip(names,oids))
class Cursor:
 def __init__(self,desc,rows):self.description=desc;self.rows=rows;self.fetches=0
 def execute(self,sql,**kwargs):assert sql.endswith(' FOR SHARE NOWAIT')
 def fetchmany(self,n):assert n==2;self.fetches+=1;return self.rows
results=[]
def check(name,desc,rows,valid=False,fetches=1):
 c=Cursor(desc,rows)
 try:ns['guard'](c)
 except ValueError as error:
  assert not valid
  assert str(error)==('Exact native authority guard descriptors required' if fetches==0 else 'Original current native authority comparison required')
 else:assert valid,name
 assert c.fetches==fetches,(name,c.fetches)
 results.append({'control':name,'passed':True,'fetches':c.fetches})
check('exact-native-triple',description(),[expected],True)
check('missing-description',None,[expected],fetches=0)
for width in (0,1,2,4):check('descriptor-width:'+str(width),description()[:width] if width<3 else description()+(SimpleNamespace(name='extra',type_code=25),),[expected],fetches=0)
for i in range(3):
 n=list(names);n[i]='wrong';check('descriptor-name:'+str(i),description(n),[expected],fetches=0)
 o=list(oids);o[i]=19;check('foreign-name-oid:'+str(i),description(oids=o),[expected],fetches=0)
for name,rows in [('zero-rows',[]),('two-rows',[expected,expected]),('short-row',[(b'identity',b'profile')]),('long-row',[expected+(0,)]),('bool-generation',[(b'identity',b'profile',True)]),('numeric-generation',[(b'identity',b'profile',Decimal(1))]),('bytearray-identity',[(bytearray(b'identity'),b'profile',1)]),('bytearray-profile',[(b'identity',bytearray(b'profile'),1)]),('identity-drift',[(b'other',b'profile',1)]),('profile-drift',[(b'identity',b'other',1)]),('generation-drift',[(b'identity',b'profile',2)])]:check(name,description(),rows)
for generation in (2,9223372036854775807):
 ns['expected_guard']=(b'identity',b'profile',generation);check('exact-generation:'+str(generation),description(),[ns['expected_guard']],True)
out={'scope':'Exact guard function extracted from source, synthetic cursor; no native SQL, loader-constructor, transaction, or authority proof.','sourceSha256':sha256(raw).hexdigest(),'passed':len(results),'controls':results}
Path(__file__).with_name('guard-results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'passed':len(results),'sourceSha256':out['sourceSha256']}))
