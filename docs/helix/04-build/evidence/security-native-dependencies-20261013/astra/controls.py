from pathlib import Path
import sys,json,copy
from hashlib import sha256
from truss._security_catalog_mapping import map_catalog_dependencies
root=Path('/private/tmp/truss-security-main-integration');out=Path(__file__).parent
extension=Path('/private/tmp/weft-security-mapping-native-20261013/weft.so');sys.path.insert(0,str(extension.parent));import weft
assert Path(weft.__file__).resolve()==extension.resolve()
request=(root/'packages/python/tests/fixtures/security-mapping-request.json').read_bytes()
response=weft.prepare_security_mapping_json(request.decode()).encode();handoff=json.loads(response);assert handoff['status']=='prepared'
(out/'genuine-response.json').write_bytes(response)
model=json.loads(json.loads(request)['modules'][0]['documentJson']);inventory={'types':[],'properties':[],'keys':[]}
for module in model['modules']:
 for record in [r for r in module['elements'] if r['kind']=='record']:
  owner=len(inventory['types'])+1;inventory['types'].append({'document_id':model['id'],'module':module['id'],'element':record['id'],'type_id':owner,'kind':'record','retired_rev':None})
  for member in record['members']:
   inventory['properties'].append({'type_id':owner,'definition_document_id':model['id'],'declaration_module':member['module'],'element':member['element'],'prop_id':len(inventory['properties'])+1,'home':'json','retired_rev':None})
  for number,key in enumerate(record['keys'],1):
   fields=[next(p['prop_id'] for p in inventory['properties'] if p['type_id']==owner and p['declaration_module']==f['module'] and p['element']==f['element']) for f in key['fields']]
   inventory['keys'].append({'type_id':owner,'key_id':key['id'],'key_num':number,'prop_ids':fields,'retired_rev':None})
assessment={'inventory':inventory,'revision':'1','installationId':'synthetic','releaseSha256':'synthetic'}
def encoded(v):return json.dumps(v,separators=(',',':')).encode()
def salary(a):return next(p for p in a['inventory']['properties'] if p['element']=='salary')
def record(a,name):return next(p for p in a['inventory']['types'] if p['element']==name)
def compound(a,h,reverse=False):
 owner=record(a,'Resource')['type_id'];key=next(k for k in a['inventory']['keys'] if k['type_id']==owner);key['prop_ids'].append(salary(a)['prop_id'])
 for scan in h['handoff']['scans']:
  for action in scan['actions']:
   for k in action['keys']:
    if k['target']['elementId']=='Resource':k['fields'].append({'documentId':'domain','moduleId':'m','elementId':'salary'})
 if reverse:key['prop_ids'].reverse()
cases=['baseline','missingType','duplicateType','retiredType','nonRecord','missingProperty','duplicateProperty','wrongPropertyOwner','wrongPropertyDocument','wrongPropertyModule','retiredProperty','missingKey','duplicateKey','retiredKey','compoundKey','reversedKey','duplicateScan','unknownUseScan','wrongUseTarget','mutableInput','oversizedInput']
results=[]
for case in cases:
 a=copy.deepcopy(assessment);h=copy.deepcopy(handoff)
 if case=='missingType':a['inventory']['types'].remove(record(a,'Assignment'))
 if case=='duplicateType':a['inventory']['types'].append(copy.deepcopy(record(a,'Resource')))
 if case=='retiredType':record(a,'Resource')['retired_rev']=1
 if case=='nonRecord':record(a,'Resource')['kind']='relationship'
 if case=='missingProperty':a['inventory']['properties'].remove(salary(a))
 if case=='duplicateProperty':a['inventory']['properties'].append(copy.deepcopy(salary(a)))
 if case=='wrongPropertyOwner':salary(a)['type_id']=record(a,'Staff')['type_id']
 if case=='wrongPropertyDocument':salary(a)['definition_document_id']='other'
 if case=='wrongPropertyModule':salary(a)['declaration_module']='other'
 if case=='retiredProperty':salary(a)['retired_rev']=1
 if case=='missingKey':a['inventory']['keys'].pop()
 if case=='duplicateKey':a['inventory']['keys'].append(copy.deepcopy(a['inventory']['keys'][0]))
 if case=='retiredKey':a['inventory']['keys'][0]['retired_rev']=1
 if case in ('compoundKey','reversedKey'):compound(a,h,case=='reversedKey')
 if case=='duplicateScan':h['handoff']['scans'][1]['scan']='s0'
 if case=='unknownUseScan':h['handoff']['uses'][0]['scan']='unknown'
 if case=='wrongUseTarget':h['handoff']['uses'][0]['target']['elementId']='Staff'
 raw=encoded(a)
 if case=='mutableInput':raw=bytearray(raw)
 if case=='oversizedInput':raw=b' '*(16777216+1)
 try:
  mapped=json.loads(map_catalog_dependencies(raw,encoded(h)))
  assert case in ('baseline','compoundKey'),case+' unexpectedly accepted'
  assert mapped['securityReady'] is False and [s['scan'] for s in mapped['scans']]==['s0','s1']
  assert len(mapped['uses'])==6
  assert [s['actions'][0]['action'] for s in mapped['scans']]==[s['actions'][0]['action'] for s in h['handoff']['scans']]
  assert all(v['home']=='truss.object' for s in mapped['scans'] for act in s['actions'] for v in act['associations'])
  for before,after in zip(h['handoff']['uses'],mapped['uses']):assert {k:v for k,v in after.items() if k!='native'}==before
  results.append({'case':case,'result':'accepted as expected'})
 except ValueError as e:
  assert case not in ('baseline','compoundKey'),str(e)
  results.append({'case':case,'result':'refused as expected','reason':str(e)})
result={'scope':'Genuine imported owner Weft response with synthetic native catalog IDs; mutated negative and compound-key packets exercise mapper only, not native acceptance or whole compiler equivalence.','compilerFile':str(extension),'compilerSha256':sha256(extension.read_bytes()).hexdigest(),'controls':results}
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':len(results),'results':str(out/'results.json')}))
