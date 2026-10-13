from pathlib import Path
import json,sys
from hashlib import sha256
from truss._security_catalog_mapping import map_catalog_dependencies
source=Path('/private/tmp/truss-ontology-endpoint-native-packets');out=Path(__file__).parent
sys.path.insert(0,'/private/tmp/weft-security-mapping-native-20261013');import weft
assert Path(weft.__file__).resolve()==Path('/private/tmp/weft-security-mapping-native-20261013/weft.so')
def identity(v):return tuple(v[k] for k in ('documentId','moduleId','elementId'))
def one(values):assert len(values)==1,values;return values[0]
results=[]
for name in ('baseline','compound'):
 raw={k:(source/(name+'-'+k+'.json')).read_bytes() for k in ('request','response','assessment','dependencies')};v={k:json.loads(b) for k,b in raw.items()};request=v['request'];handoff=v['response']['handoff'];assessment=v['assessment'];deps=v['dependencies'];inventory=assessment['inventory'];ontology=json.loads(request['ontologyJson'])
 assert weft.prepare_security_mapping_json(raw['request'].decode()).encode()==raw['response']
 assert map_catalog_dependencies(raw['assessment'],raw['response'],raw['request'])==raw['dependencies']
 assert sha256(request['ontologyJson'].encode()).hexdigest()==handoff['ontologySha256']
 assert deps['version']=='truss.native-security-dependencies/0.2' and deps['securityReady'] is False
 assert deps['revision']==assessment['revision'] and deps['installationId']==assessment['installationId'] and deps['releaseSha256']==assessment['releaseSha256']
 assert [s['scan'] for s in deps['scans']]==[s['scan'] for s in handoff['scans']]
 def type_id(reference):return one([t for t in inventory['types'] if (t['document_id'],t['module'],t['element'])==identity(reference) and t['retired_rev'] is None])['type_id']
 def property_id(target,field):return one([p for p in inventory['properties'] if p['type_id']==type_id(target) and (p['definition_document_id'],p['declaration_module'],p['element'])==identity(field) and p['retired_rev'] is None])['prop_id']
 endpoint_count=pair_count=0
 for scan,original_scan in zip(deps['scans'],handoff['scans']):
  assert scan['target']==original_scan['target'];assert [a['action'] for a in scan['actions']]==[a['action'] for a in original_scan['actions']]
  for action,original_action in zip(scan['actions'],original_scan['actions']):
   assert [a['reference'] for a in action['associations']]==original_action['associations']
   for association in action['associations']:
    declaration=one([a for a in ontology['associations'] if a['type']==association['reference']]);assert association['home']=='truss.object';assert int(association['typeId'])==type_id(declaration['type'])
    witness=one([k for k in original_action['keys'] if k['target']==declaration['type'] and k['keyId']==declaration['keyId']]);native_witness=one([k for k in inventory['keys'] if k['type_id']==type_id(declaration['type']) and k['key_id']==declaration['keyId'] and k['retired_rev'] is None]);assert association['key']['target']==declaration['type'];assert association['key']['keyId']==witness['keyId'];assert int(association['key']['keyNumber'])==native_witness['key_num'];assert [p['reference'] for p in association['key']['fields']]==witness['fields'];assert [int(p['propertyId']) for p in association['key']['fields']]==native_witness['prop_ids']
    assert [e['role'] for e in association['endpoints']]==[e['role'] for e in declaration['endpoints']]
    for endpoint,authored in zip(association['endpoints'],declaration['endpoints']):
     assert endpoint['target']==authored['target'];target=one([e for e in ontology['entities']+ontology['associations'] if e['type']==authored['target']]);key=one([k for k in original_action['keys'] if k['target']==authored['target'] and k['keyId']==target['keyId']]);nativekey=one([k for k in inventory['keys'] if k['type_id']==type_id(key['target']) and k['key_id']==key['keyId'] and k['retired_rev'] is None]);assert int(endpoint['key']['keyNumber'])==nativekey['key_num'];assert endpoint['key']['keyId']==target['keyId']
     assert [p['associationField']['reference'] for p in endpoint['pairs']]==authored['fields'];assert [p['targetKeyField']['reference'] for p in endpoint['pairs']]==key['fields']
     assert [int(p['targetKeyField']['propertyId']) for p in endpoint['pairs']]==nativekey['prop_ids']
     for p in endpoint['pairs']:
      assert int(p['associationField']['typeId'])==type_id(declaration['type']);assert int(p['targetKeyField']['typeId'])==type_id(authored['target'])
      assert int(p['associationField']['propertyId'])==property_id(declaration['type'],p['associationField']['reference']);assert int(p['targetKeyField']['propertyId'])==property_id(authored['target'],p['targetKeyField']['reference'])
     endpoint_count+=1;pair_count+=len(endpoint['pairs'])
 assert endpoint_count==8 and pair_count==(10 if name=='compound' else 8)
 for key,b in raw.items():(out/('native-'+name+'-'+key+'.json')).write_bytes(b)
 results.append({'case':name,'endpointOccurrences':endpoint_count,'orderedPairs':pair_count,'originalCompilerResponseByteIdentical':True,'mapperOutputByteIdentical':True,'independentNativeIdAndOntologyCorrespondence':True,'packetSha256':{k:sha256(b).hexdigest() for k,b in raw.items()}})
(out/'native-packet-results.json').write_text(json.dumps({'scope':'Read-only retained native packets; original compiler replay and independent ordered endpoint/property/key correspondence checks, no database rerun or provenance authentication theorem.','results':results},indent=2)+'\n');print(json.dumps(results,indent=2))
