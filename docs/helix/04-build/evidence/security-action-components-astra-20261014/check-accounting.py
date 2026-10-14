import ast,hashlib,json,subprocess
from pathlib import Path
root=Path('/private/tmp/truss-security-main-integration');out=Path(__file__).resolve().parent
relative='packages/python/src/truss/_action_role_installation.py'
new=(root/relative).read_bytes()
old=subprocess.check_output(['git','show','2848c33de8eb574a94f818a75bfb590b2c9e1384:'+relative],cwd=root)
def gate(source):
    tree=ast.parse(source)
    matches=[n for n in ast.walk(tree) if isinstance(n,ast.If) and any(isinstance(x,ast.Constant) and x.value=='Complete native action role enrollment capacity exceeded' for s in n.body for x in ast.walk(s))]
    assert len(matches)==1
    return compile(ast.Expression(matches[0].test),'<actual-capacity-expression>','eval')
prior,current=gate(old),gate(new)
def exceeded(code,store,rows):return eval(code,{'len':len,'sum':sum,'store_identity':store,'rows':rows})
row=(b'["m","set"]',b'"r"',1,b'{"pin":"conditional-arithmetic-fixture"}')
fixed=sum(len(x) for x in (row[0],row[1],row[3]))+32
store=b's'*(4096-fixed)
checks=[('former-store-amplification-admitted',exceeded(prior,b's'*4096,[row]*4096) is False),('fixed-store-amplification-refused',exceeded(current,b's'*4096,[row]*4096) is True),('exact-four-MiB-admitted',exceeded(current,store,[row]*1024) is False),('one-byte-per-row-over-refused',exceeded(current,store+b's',[row]*1024) is True)]
assert all(v for _,v in checks)
result={'status':'passed','checks':[{'name':k,'passed':v} for k,v in checks],'sourceSha256':hashlib.sha256(new).hexdigest(),'priorSourceSha256':hashlib.sha256(old).hexdigest(),'scope':'Executes only the exact parsed old/current capacity expression over controlled tuples. Does not qualify full native enrollment, original ticket admissibility, total heap, or SQL storage overhead.'}
(out/'accounting-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
