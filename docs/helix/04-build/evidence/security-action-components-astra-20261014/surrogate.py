import json,hashlib,subprocess
from pathlib import Path
from truss.bulk_action_gateway import ActionRegistration,GatewayRefusal
root=Path('/private/tmp/truss-security-main-integration')
fixture=json.loads(Path('/Users/erik/Projects/weft/tests/mutation/fixtures/postgres-owner-plan.json').read_text())
results=[]
for name,role,action_id in [('role-lone','\ud800','set-active'),('action-lone','bulk-editor','\udfff'),('nul-positive','a\0b','set-active')]:
    request=json.loads(json.dumps(fixture['request']))
    doc=json.loads(request['model']['utf8'])
    a=doc['modules'][0]['extensions']['umf.actions']['actions'][0]
    a['authorization']['roles']=[role];a['id']=action_id
    body=json.dumps(doc,ensure_ascii=True,separators=(',',':'))
    digest=hashlib.sha256(body.encode()).hexdigest()
    request['model']['utf8']=body;request['model']['sha256']=digest
    request['modelPin']['sha256']=digest
    request['action']['documentSha256']=digest;request['action']['identity']['action']=action_id
    payload={'model':request['model'],'action':request['action'],'pin':request['modelPin']}
    run=subprocess.run(['/opt/homebrew/bin/bun',str(root/'packages/python/tests/owner_action_preparation.ts')],input=json.dumps(payload),capture_output=True,text=True,timeout=30)
    row={'name':name,'ownerExit':run.returncode,'stderr':run.stderr}
    if run.returncode==0:
        prepared=run.stdout.strip().encode();registry=ActionRegistration(lambda *args:prepared)
        try:
            t=registry.register(json.dumps(request['model']).encode(),json.dumps(request['action']).encode(),prepared)
            p=registry.family_policy(t);row['gateway']='accepted';row['familyHex']=p.family_identity.hex()
        except GatewayRefusal as e:row['gateway']='refused';row['reason']=str(e)
        (Path(__file__).parent/(name+'-request.json')).write_text(json.dumps(payload,indent=2))
        (Path(__file__).parent/(name+'-preparation.json')).write_bytes(prepared)
    results.append(row)
(Path(__file__).parent/'surrogate-results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results))
