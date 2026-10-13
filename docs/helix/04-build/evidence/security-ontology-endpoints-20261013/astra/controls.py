from pathlib import Path
import sys,json,copy,subprocess
from hashlib import sha256
from truss._security_catalog_mapping import map_catalog_dependencies
root=Path('/private/tmp/truss-security-main-integration');out=Path(__file__).parent
extension=Path('/private/tmp/weft-security-mapping-native-20261013/weft.so');sys.path.insert(0,str(extension.parent));import weft
assert Path(weft.__file__).resolve()==extension.resolve()
def encoded(v):return json.dumps(v,separators=(',',':')).encode()
def ref(e):return {'documentId':'domain','moduleId':'m','elementId':e}
base=json.loads((root/'packages/python/tests/fixtures/security-mapping-request.json').read_bytes())
def authored(compound=False,self_target=False):
 r=copy.deepcopy(base);m=json.loads(r['modules'][0]['documentJson']);o=json.loads(r['ontologyJson']);elements=m['modules'][0]['elements']
 def element(n):return next(e for e in elements if e['id']==n)
 def binding(n):return next(e for e in o['entities']+o['associations'] if e['type']['elementId']==n)
 def add(owner,name):
  elements.append({'id':name,'kind':'field','scalarType':'string','nullability':'required','cardinality':'one','extensions':{},'name':name})
  element(owner)['members'].append({'module':'m','element':name});binding(owner)['fields'].append({'ref':ref(name),'protection':'unprotected'})
 if compound:
  add('Resource','resourceRegion');add('Ownership','ownerRegion');element('Resource')['keys'][0]['fields'].append({'module':'m','element':'resourceRegion'})
  next(e for e in binding('Ownership')['endpoints'] if e['role']=='resource')['fields'].append(ref('ownerRegion'))
 if self_target:
  add('Assignment','assignmentManager');binding('Assignment')['endpoints'].append({'role':'manager','target':ref('Staff'),'fields':[ref('assignmentManager')]})
 r['modules'][0]['documentJson']=encoded(m).decode();r['modules'][0]['pin']['sha256']=sha256(r['modules'][0]['documentJson'].encode()).hexdigest();r['ontologyJson']=encoded(o).decode()
 profile=json.loads(r['queryProfileJson']);profile['modelPins']=[r['modules'][0]['pin']];profile['ontologySha256']=sha256(r['ontologyJson'].encode()).hexdigest();r['queryProfileJson']=encoded(profile).decode()
 return r,m,o

def assessment(model):
 inv={'types':[],'properties':[],'keys':[]}
 for module in model['modules']:
  for record in [e for e in module['elements'] if e['kind']=='record']:
   owner=len(inv['types'])+1;inv['types'].append({'document_id':model['id'],'module':module['id'],'element':record['id'],'type_id':owner,'kind':'record','retired_rev':None})
   for f in record['members']:inv['properties'].append({'type_id':owner,'definition_document_id':model['id'],'declaration_module':f['module'],'element':f['element'],'prop_id':len(inv['properties'])+1,'home':'json','retired_rev':None})
   for n,key in enumerate(record['keys'],1):inv['keys'].append({'type_id':owner,'key_id':key['id'],'key_num':n,'prop_ids':[next(p['prop_id'] for p in inv['properties'] if p['type_id']==owner and p['element']==f['element'] and p['declaration_module']==f['module']) for f in key['fields']],'retired_rev':None})
 return {'inventory':inv,'revision':'1','installationId':'synthetic','releaseSha256':'synthetic'}
results=[];packets={}
for name,c,s in [('baseline',False,False),('compound',True,False),('selfTarget',False,True),('compoundSelfTarget',True,True)]:
 r,m,o=authored(c,s);response=json.loads(weft.prepare_security_mapping_json(encoded(r).decode()));assert response['status']=='prepared',response
 a=assessment(m);mapped=json.loads(map_catalog_dependencies(encoded(a),encoded(response),encoded(r)));assert mapped['version'].endswith('/0.2') and mapped['securityReady'] is False
 endpoints=[e for scan in mapped['scans'] for action in scan['actions'] for assoc in action['associations'] for e in assoc['endpoints']]
 assert len(endpoints)==(10 if s else 8)
 for scan in mapped['scans']:
  for action in scan['actions']:
   for association in action['associations']:
    assert association['key']['target']==association['reference']
    assert association['key'] in action['keys']
 for e in endpoints:
  if e['role']=='resource':assert [(p['associationField']['reference']['elementId'],p['targetKeyField']['reference']['elementId']) for p in e['pairs']]==([('ownerResource','resourceId'),('ownerRegion','resourceRegion')] if c else [('ownerResource','resourceId')])
  if e['role']=='manager':assert e['target']==ref('Staff') and e['pairs'][0]['associationField']['reference']==ref('assignmentManager')
 results.append({'case':name,'result':'accepted','evidence':'Genuine compiler with synthetic native IDs','endpointOccurrences':len(endpoints)});packets[name]=(r,a,response)
 (out/(name+'-request.json')).write_bytes(encoded(r));(out/(name+'-response.json')).write_bytes(encoded(response))
# Exact v0.1 compatibility against the pre-endpoint implementation.
r,a,h=packets['baseline'];ns={};exec(compile(subprocess.check_output(['git','show','70ddb9dc:packages/python/src/truss/_security_catalog_mapping.py'],cwd=root,text=True),'prior-reviewed-mapper','exec'),ns)
old=ns['map_catalog_dependencies'](encoded(a),encoded(h));assert map_catalog_dependencies(encoded(a),encoded(h))==old
results.append({'case':'legacyNoSourceByteIdentical','result':'accepted','evidence':'Exact comparison to reviewed 70ddb9dc helper'})
# Selected endpoint mapper controls deliberately mutate trusted packets and repin
# their digest; they do not establish original compiler admission of these packets.
for case in ['sourceWhitespace','duplicateRole','emptyRole','missingRole','wrongArity','unknownTarget','missingTargetKey','wrongTargetKey','wrongSourceOwner','wrongSourceDocument','reversedNativeCompositeKey','missingAssociation','duplicateAssociation','mutableSource','oversizedSource']:
 r,a,h=copy.deepcopy(packets['compound']);o=json.loads(r['ontologyJson']);assoc=next(x for x in o['associations'] if x['type']==ref('Ownership'));endpoint=assoc['endpoints'][0]
 if case=='sourceWhitespace':r['ontologyJson']+=' '
 elif case=='duplicateRole':assoc['endpoints'][1]['role']=endpoint['role']
 elif case=='emptyRole':endpoint['role']=''
 elif case=='missingRole':del endpoint['role']
 elif case=='wrongArity':endpoint['fields'].pop()
 elif case=='unknownTarget':endpoint['target']=ref('Unknown')
 elif case in ('missingTargetKey','wrongTargetKey'):
  for scan in h['handoff']['scans']:
   for act in scan['actions']:
    if case=='missingTargetKey':act['keys']=[k for k in act['keys'] if k['target']!=endpoint['target']]
    else:
     for k in act['keys']:
      if k['target']==endpoint['target']:k['keyId']='other'
 elif case=='wrongSourceOwner':endpoint['fields'][0]=ref('staffId')
 elif case=='wrongSourceDocument':endpoint['fields'][0]['documentId']='other'
 elif case=='reversedNativeCompositeKey':
  for key in a['inventory']['keys']:
   if len(key['prop_ids'])==2:key['prop_ids'].reverse()
 elif case=='missingAssociation':o['associations'].remove(assoc)
 elif case=='duplicateAssociation':o['associations'].append(copy.deepcopy(assoc))
 if case!='sourceWhitespace':r['ontologyJson']=encoded(o).decode();h['handoff']['ontologySha256']=sha256(r['ontologyJson'].encode()).hexdigest()
 raw=encoded(r)
 if case=='mutableSource':raw=bytearray(raw)
 if case=='oversizedSource':raw=b' '*(4_000_000+1)
 try:map_catalog_dependencies(encoded(a),encoded(h),raw)
 except (ValueError,KeyError) as e:results.append({'case':case,'result':'refused','errorType':type(e).__name__,'reason':str(e),'evidence':'Selected mutated packet control'})
 else:raise AssertionError(case+' unexpectedly accepted')
result={'scope':'Genuine owner compiler positive source fixtures with synthetic native IDs; selected negative endpoint mapper controls deliberately mutate/refingerprint packets. No native database execution or complete closure/authenticity proof.','compiler':str(extension),'compilerSha256':sha256(extension.read_bytes()).hexdigest(),'controls':results}
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':len(results),'results':str(out/'results.json')}))
