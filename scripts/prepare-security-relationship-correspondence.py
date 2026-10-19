# SPDX-License-Identifier: MIT OR Apache-2.0
"""Diagnostic correspondence from original assessment bytes; not authority."""
from pathlib import Path
import hashlib,json

def _original_json(raw):
 def pairs(items):
  result={}
  for key,value in items:
   if key in result:raise ValueError('Duplicate correspondence source member')
   result[key]=value
  return result
 def nonfinite(value):raise ValueError('Finite original correspondence source required')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=nonfinite)

def derive_relationship_correspondence(raw,physical_request_raw,sources):
 if type(raw) is not bytes or not 1<=len(raw)<=16777216 or type(physical_request_raw) is not bytes or not 1<=len(physical_request_raw)<=4000000:raise ValueError('Bounded original source inputs required')
 if type(sources) is not dict or set(sources)!={'document','resolution','policy','transport'} or any(type(v) is not bytes or not 1<=len(v)<=4000000 for v in sources.values()):raise ValueError('Exact original selected source bytes required')
 assessment=_original_json(raw);inventory=assessment['inventory']
 physical_request=_original_json(physical_request_raw)
 if len(physical_request['modules'])!=1:raise ValueError('Original single native source required')
 physical=physical_request['modules'][0]
 correspondence=_original_json(Path('docs/helix/04-build/evidence/security-ontology-shared-policy-20261014/binding-correspondence.json').read_bytes())
 correspondence['version']='truss.reified-security-binding-fixture/0.2-candidate'
 correspondence['scope']='Original supplied assessment correspondence only; not installed/authenticated protected authority.'
 hashof=lambda b:hashlib.sha256(b).hexdigest()
 transport=sources['transport']
 correspondence['logicalSourceDigests']={n:hashof(sources[f]) for n,f in [('document','document'),('resolution','resolution'),('policy','policy')]}
 correspondence['logicalSourceDigests']['transport']=hashof(transport)
 correspondence['physicalSourceSha256']=hashof(physical['documentJson'].encode());assert correspondence['physicalSourceSha256']==physical['pin']['sha256']
 correspondence['inventorySha256']=hashof(raw)
 def one(table,predicate):
  rows=[r for r in inventory[table] if predicate(r)]
  if len(rows)!=1:raise ValueError('Exact unique original native '+table+' correspondence required')
  return rows[0]
 def current(row):return row.get('retired_rev') is None and row.get('definition_source_kind')=='accepted_document' and str(row['definition_rev'])==assessment['revision']
 def typ(name):return one('types',lambda r:current(r) and r['document_id']=='adoc' and r['module']=='m' and r['element']==name and r['kind']=='record')
 def prop(name,field):return one('properties',lambda r:current(r) and r['type_id']==typ(name)['type_id'] and r['element']==field and r['declaration_module']=='m' and r['definition_document_id']=='adoc')
 for entry in correspondence['entities']:
  name=entry['nativeType']['elementId'];p=prop(name,entry['nativeKeyField']);key=one('keys',lambda r:current(r) and r['type_id']==typ(name)['type_id'] and r['key_id']==entry['nativeKeyId'] and r['prop_ids']==[p['prop_id']])
  entry['nativeType']['typeId']=str(typ(name)['type_id']);entry['nativePropertyId']=str(p['prop_id']);entry['nativeKeyNumber']=str(key['key_num'])
 for entry in correspondence['endpoints']:
  relation=one('relationships',lambda r:current(r) and r['document_id']=='adoc' and r['module']=='m' and r['rel_id']==entry['nativeRelationship'])
  target=entry['targetKeyType'];owner=entry['logicalAssociation']
  source,target=(target,owner) if entry['direction']=='incoming' else (owner,target)
  entry['nativeRelationshipId']=str(relation['rel_type_id']);entry['sourceTypeId']=str(typ(source)['type_id']);entry['targetTypeId']=str(typ(target)['type_id'])
  one('endpoints',lambda r:r['rel_type_id']==relation['rel_type_id'] and r['source_type']==int(entry['sourceTypeId']) and r['target_type']==int(entry['targetTypeId']))
 for member,name,field in [('active','Assignment','active'),('salary','Resource','salary')]:
  correspondence[member]['nativeTypeId']=str(typ(name)['type_id']);correspondence[member]['nativePropertyId']=str(prop(name,field)['prop_id'])
 relation=one('relationships',lambda r:current(r) and r['document_id']=='adoc' and r['module']=='m' and r['rel_id']=='ResourceRelatedResource')
 type_id=typ('Resource')['type_id'];one('endpoints',lambda r:r['rel_type_id']==relation['rel_type_id'] and r['source_type']==type_id and r['target_type']==type_id)
 correspondence['queryRelationships']=[{'logicalRelationship':{'documentId':'domain','moduleId':'m','relationshipId':'ResourceRelatedResource'},'nativeRelationship':{'documentId':'adoc','moduleId':'m','relationshipId':'ResourceRelatedResource'},'nativeRelationshipId':str(relation['rel_type_id']),'sourceTypeId':str(type_id),'targetTypeId':str(type_id)}]
 return json.dumps(correspondence,separators=(',',':')).encode()

if __name__=='__main__':
 root=Path('docs/helix/03-test/fixtures/security-public-relationship')
 evidence=Path('docs/helix/04-build/evidence/security-public-relationship-inventory-20261014')
 transport=Path('docs/helix/04-build/evidence/security-named-source-profile/transport.json').read_bytes();(root/'transport.json').write_bytes(transport)
 sources={name:(root/(name+'.json')).read_bytes() for name in ('document','resolution','policy','transport')}
 for suffix,policy_file in [('', 'policy'),('-observation-denied','policy-observation-denied')]:
  selected={**sources,'policy':(root/(policy_file+'.json')).read_bytes()}
  raw=derive_relationship_correspondence((evidence/'accepted-assessment.json').read_bytes(),(evidence/'physical-request.json').read_bytes(),selected)
  (root/('correspondence'+suffix+'-template.json')).write_bytes(raw)
 print(json.dumps({'status':'supplied-assessment-correspondence-only','variants':2}))
