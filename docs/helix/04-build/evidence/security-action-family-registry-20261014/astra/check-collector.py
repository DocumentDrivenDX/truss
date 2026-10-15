import json,hashlib,copy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from truss.bulk_action_gateway import ActionRegistration
from truss._action_identity_codec import encode_action_role
from truss._action_store import ActionStoreObservation
import truss._action_authority_observation as mod
out=Path(__file__).resolve().parent;root=Path('/private/tmp/truss-security-main-integration')
def artifact(value):
    body=json.dumps(value,separators=(',',':'));return json.dumps({'mediaType':'application/json','utf8':body,'sha256':hashlib.sha256(body.encode()).hexdigest()}).encode()
action={'id':'set','authorization':{'kind':'roles','profile':{'id':'umf.actions.roles','version':'1'},'roles':['first','second']},'attribution':{'subject':'person-required'}}
model=artifact({'modules':[{'id':'m','extensions':{'umf.actions':{'actions':[action]}}}]});digest=json.loads(model)['sha256']
pin=json.dumps({'documentSha256':digest,'identity':{'module':'m','action':'set'}}).encode()
prep=artifact({'protocol':'umf.actions.plan-model/1','action':json.loads(pin),'model':{'sha256':digest}})
registry=ActionRegistration(lambda *a:prep);ticket=registry.register(model,pin,prep)
record=json.loads((root/'docs/helix/04-build/evidence/action-store-20261014/receipt.json').read_text());raw=bytes.fromhex(record['actionStore']['receiptHex']);s=json.loads(raw)
store=ActionStoreObservation(bytes.fromhex(s['registrationKeyHex']),raw,bytes.fromhex(s['storeIdentityHex']),bytes.fromhex(s['tenantIdentityHex']),bytes.fromhex(s['epochIdentityHex']),s['installationId'],'matches')
orig=SimpleNamespace(identity=('db','200'))
base={'held':[('action_family_registration',),('action_role_binding',),('action_subject_binding',)],'declarations':[('10',pin.hex(),model.hex(),prep.hex(),json.dumps([encode_action_role(x).hex() for x in ('first','second')],separators=(',',':')),'true','true')],'subject':[('68756d616e','human')],'roles':[(encode_action_role('first').hex(),pin.hex(),'false','10','true'),(encode_action_role('second').hex(),pin.hex(),'true','10','true')]}
checks=[]
def observe(state,late_fail=False):
    calls=[]
    def rows(cursor,q,params=(),limit=256):
        if "SELECT c.relname::text" in q:key='held'
        elif 'FROM ONLY truss.action_family_registration' in q:key='declarations'
        elif 'FROM ONLY truss.action_subject_binding' in q:key='subject'
        elif 'FROM ONLY truss.action_role_binding' in q:key='roles'
        else:raise AssertionError(q)
        return state[key]
    def peer(*a):
        calls.append('peer')
        if late_fail and len(calls)==2:raise ValueError('late peer changed')
    with patch.object(mod,'_native_path',lambda *a:None),patch.object(mod,'verify_action_store_context_with_cursor',lambda *a:None),patch.object(mod,'verify_held_registered_role_catalog_cut_with_cursor',lambda *a:None),patch.object(mod,'verify_preparation_peer_with_cursor',peer),patch.object(mod,'_text_rows',rows):
        result=mod.observe_current_action_authority_with_cursor(object(),original=orig,registration=registry,ticket=ticket,store_context=store)
    assert calls==['peer','peer'];return result

def control(name,mutator=None,refuse=False,role_match=None,human=True,late=False):
    state=copy.deepcopy(base)
    if mutator:mutator(state)
    try:result=observe(state,late)
    except ValueError:
        assert refuse,name
    else:
        assert not refuse,name
        assert result.role_match is role_match and result.human_enrolled is human and result.security_ready is False,name
    checks.append({'name':name,'status':'passed'})
def field(state,key,row,index,value):
    x=list(state[key][row]);x[index]=value;state[key][row]=tuple(x)
control('second-only-role-OR',role_match=True)
control('neither-role',lambda s:field(s,'roles',1,2,'false'),role_match=False)
control('both-roles',lambda s:field(s,'roles',0,2,'true'),role_match=True)
control('first-only-role',lambda s:(field(s,'roles',0,2,'true'),field(s,'roles',1,2,'false')),role_match=True)
control('service-not-human',lambda s:field(s,'subject',0,1,'service'),role_match=True,human=False)
for idx in range(3):control('missing-mapping-cut-'+str(idx),lambda s,idx=idx:s['held'].pop(idx),True)
control('missing-declaration',lambda s:s.__setitem__('declarations',[]),True)
control('duplicate-declaration',lambda s:s['declarations'].append(s['declarations'][0]),True)
for i in range(1,7):control('declaration-field-'+str(i),lambda s,i=i:field(s,'declarations',0,i,'false' if i>4 else '00'),True)
control('reordered-declared-roles',lambda s:field(s,'declarations',0,4,json.dumps([encode_action_role(x).hex() for x in ('second','first')],separators=(',',':'))),True)
for i in range(2):control('missing-role-'+str(i),lambda s,i=i:s['roles'].pop(i),True)
control('duplicate-role',lambda s:s['roles'].append(s['roles'][0]),True)
control('extra-unresolved-role',lambda s:s['roles'].append(('ffff',pin.hex(),'false','10','false')),True)
for i,value in enumerate(['ff','ff','not-bool','11','false']):control('role-field-'+str(i),lambda s,i=i,value=value:field(s,'roles',0,i,value),True)
control('missing-subject',lambda s:s.__setitem__('subject',[]),True)
control('invalid-subject-kind',lambda s:field(s,'subject',0,1,'other'),True)
control('late-peer-refusal',refuse=True,late=True)
result={'status':'passed','count':len(checks),'sourceSha256':hashlib.sha256(Path(mod.__file__).read_bytes()).hexdigest(),'checks':checks,'scope':'Actual Python collector over finite synthetic native rows and native guard doubles. Establishes local complete-row comparisons and OR/Subject output behavior; not SQL/native/refinement or original owner authentication.'}
(out/'collector-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'passed','count':len(checks)}))
