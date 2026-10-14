import hashlib,json,random,subprocess,sys
from pathlib import Path
from truss._action_identity_codec import encode_action_family,encode_action_role
from truss.bulk_action_gateway import ActionRegistration,GatewayRefusal
root=Path('/private/tmp/truss-security-main-integration')
out=Path(__file__).resolve().parent
checks=[]
def check(name,f):
    f(); checks.append({'name':name,'status':'passed'})
def equal(a,b):
    assert a==b,(a,b)
def refused(f):
    try:f()
    except (GatewayRefusal,ValueError):return
    raise AssertionError('unexpected acceptance')
# Actual independent Bun JSON.stringify byte oracle over bounded UTF-16 strings.
rng=random.Random(60314)
units=[0,1,8,9,10,12,13,31,32,34,47,92,127,0xe9,0x301,0x2028,0x2029,0xd800,0xdbff,0xdc00,0xdfff,0xffff]
rows=['a','a'*256,'\U0001f680'*128,'\ud83d\ude80','\ud800\ud800\udfff','\udfff\ud800']
rows += [''.join(chr(rng.choice(units)) for _ in range(rng.randint(1,100))) for _ in range(256)]
request=json.dumps(rows,ensure_ascii=True).encode()
js="const r=JSON.parse(await Bun.stdin.text()); process.stdout.write(JSON.stringify(r.map(x=>({role:Buffer.from(JSON.stringify(x)).toString('hex'),family:Buffer.from(JSON.stringify([x,'test'])).toString('hex')}))));"
run=subprocess.run(['/opt/homebrew/bin/bun','-e',js],input=request,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=15)
expected=json.loads(run.stdout)
for i,(value,want) in enumerate(zip(rows,expected)):
    check('original-bun-utf16-'+str(i),lambda value=value,want=want:(equal(encode_action_role(value).hex(),want['role']),equal(encode_action_family(value,'test').hex(),want['family'])))
for i,value in enumerate(['','a'*257,'\U0001f680'*129,None,1,b'a']):
    check('invalid-identity-'+str(i),lambda value=value:refused(lambda:encode_action_role(value)))
# Synthetic owner output only: qualifies local closed-shape and original-source selection.
def artifact(body):
    text=json.dumps(body,ensure_ascii=True,separators=(',',':'))
    return json.dumps({'mediaType':'application/json','utf8':text,'sha256':hashlib.sha256(text.encode()).hexdigest()}).encode()
def policy(change=None,prepared_change=None,pin_change=None):
    action={'id':'set','authorization':{'kind':'roles','profile':{'id':'umf.actions.roles','version':'1'},'roles':['r']},'attribution':{'subject':'person-required'}}
    doc={'modules':[{'id':'m','extensions':{'umf.actions':{'actions':[action]}}}]}
    if change:change(doc,action)
    model=artifact(doc); mh=json.loads(model)['sha256']
    pin={'documentSha256':mh,'identity':{'module':'m','action':'set'}}
    if pin_change:pin_change(pin)
    prep={'protocol':'umf.actions.plan-model/1','action':pin,'model':{'sha256':mh}}
    if prepared_change:prepared_change(prep)
    prep_bytes=artifact(prep); pin_bytes=json.dumps(pin).encode()
    registry=ActionRegistration(lambda *args:prep_bytes)
    t=registry.register(model,pin_bytes,prep_bytes)
    return registry.family_policy(t)
check('family-baseline',lambda:equal((policy().family_identity,policy().roles,policy().person_required),(b'["m","set"]',('r',),True)))
mutations={
 'authorization-kind':lambda d,a:a['authorization'].__setitem__('kind','permit'),
 'authorization-version':lambda d,a:a['authorization']['profile'].__setitem__('version','2'),
 'authorization-extra':lambda d,a:a['authorization'].__setitem__('extra',True),
 'roles-empty':lambda d,a:a['authorization'].__setitem__('roles',[]),
 'roles-over64':lambda d,a:a['authorization'].__setitem__('roles',[str(i) for i in range(65)]),
 'roles-duplicate':lambda d,a:a['authorization'].__setitem__('roles',['x','x']),
 'roles-bool':lambda d,a:a['authorization'].__setitem__('roles',[True]),
 'roles-long':lambda d,a:a['authorization'].__setitem__('roles',['x'*257]),
 'attribution-missing':lambda d,a:a.pop('attribution'),
 'attribution-extra':lambda d,a:a['attribution'].__setitem__('extra',True),
 'module-duplicate':lambda d,a:d['modules'].append(d['modules'][0]),
 'action-duplicate':lambda d,a:d['modules'][0]['extensions']['umf.actions']['actions'].append(a),
}
for name,mutation in mutations.items():check(name,lambda mutation=mutation:refused(lambda:policy(mutation)))
for field,value in [('protocol','wrong'),('action',{'wrong':True}),('model',{'sha256':'0'*64})]:
    check('preparation-'+field,lambda field=field,value=value:refused(lambda:policy(prepared_change=lambda p:p.__setitem__(field,value))))
check('identity-extra',lambda:refused(lambda:policy(pin_change=lambda p:p['identity'].__setitem__('extra',True))))
check('identity-missing-module',lambda:refused(lambda:policy(pin_change=lambda p:p['identity'].__setitem__('module','absent'))))
for roles in [['é','e\u0301'],['r','R'],['\x00','x'],[str(i) for i in range(64)]]:
    check('preserve-roles-'+str(len(checks)),lambda roles=roles:equal(policy(lambda d,a:a['authorization'].__setitem__('roles',roles)).roles,tuple(roles)))
paths=['packages/python/src/truss/_action_subject_installation.py','packages/python/src/truss/_security_bootstrap/action-subject-cut.sql','packages/python/src/truss/_action_identity_codec.py','packages/python/src/truss/bulk_action_gateway.py','packages/python/tests/test_action_identity_codec.py','packages/python/tests/fixtures/action-family-codec.json','packages/python/tests/test_bulk_action_gateway.py','packages/python/tests/test_action_subject_installation_native.py']
result={'status':'passed','controls':len(checks),'bunVectors':len(rows),'sourceHashes':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},'checks':checks,'limits':['Synthetic policy ports qualify local correspondence and refusal, not original owner semantics or authentication.','No native process run.','Bun vectors are finite independent codec correspondences, not a universal codec proof.']}
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'passed','controls':len(checks),'bunVectors':len(rows)}))
