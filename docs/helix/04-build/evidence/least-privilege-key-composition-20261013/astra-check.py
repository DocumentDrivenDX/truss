from pathlib import Path
import sys,json,hashlib,copy
root=Path('/private/tmp/truss-security-main-integration');out=Path(__file__).parent
sys.path.insert(0,'/private/tmp/subject-consumer-python')
import weft
from truss._umf_key_tuples import encode_literal_key_tuple
assert Path(weft.__file__).resolve()==Path('/private/tmp/subject-consumer-python/weft.so').resolve()
request=(root/'packages/python/tests/fixtures/security-mapping-request.json').read_text()
source=json.loads(request)['modules'][0]['documentJson'].encode()
probe={'sourceSha256':hashlib.sha256(source).hexdigest(),'identity':{'module':'m','element':'Staff','key':'pk'}}
controls=[]
def check(name,value):
 assert value,name
 controls.append({'name':name,'passed':True})
def inspect(p):return json.loads(weft.inspect_security_mapping_subject_key_json(request,json.dumps(p)))
check('original Weft selects declared Staff/pk from exact original source',inspect(probe)=={'interfaceVersion':'weft-security-subject-selection/0.1.0','status':'inspected','securityReady':False})
for name,mutate in [('wrong source',lambda p:p.update(sourceSha256='0'*64)),('wrong module',lambda p:p['identity'].update(module='other')),('wrong subject',lambda p:p['identity'].update(element='Project')),('wrong key',lambda p:p['identity'].update(key='missing'))]:
 p=copy.deepcopy(probe);mutate(p);r=inspect(p);check(name+' refuses',r['status']=='refused' and r['securityReady'] is False)
tuple_result=encode_literal_key_tuple(source,('m','Staff','pk'),('{"string":"s1"}',),bun_executable='/opt/homebrew/bin/bun')
receipt=json.loads(tuple_result.original_receipt_bytes)
check('original UMF tuple bytes match fixed independent s1 vector',tuple_result.tuple_bytes==bytes.fromhex('554d464b310104027331'))
retained=json.loads(Path('/private/tmp/ordinary-key-composition.json').read_bytes())
check('pure original receipt agrees with retained native composition receipt',receipt==retained['receipt'])
check('original source and literal text retained exactly',tuple_result.original_document==source and tuple_result.literal_texts==('{"string":"s1"}',))
for name,literal in [('wrong literal family','{"integer":"1"}'),('required null','null')]:
 try:encode_literal_key_tuple(source,('m','Staff','pk'),(literal,),bun_executable='/opt/homebrew/bin/bun')
 except ValueError:check(name+' refuses',True)
 else:raise AssertionError(name)
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
result={'controls':controls,'count':len(controls),'sourcePins':[pin(__file__),pin(weft.__file__),pin(root/'packages/python/tests/fixtures/security-mapping-request.json'),pin(root/'packages/python/src/truss/_umf_key_tuples.py'),pin(root/'packages/python/src/truss/_umf_keys08/producer.js'),pin(root/'packages/python/src/truss/_umf_keys08/bridge.mjs')],'scope':'Independent genuine original Weft selection and UMF encoding only; reads parent native retained receipt but does not independently exercise a native transaction or privileges.'}
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'controls':len(controls),'passed':True}))
