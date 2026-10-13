"""Map original Weft dependency references to assessed native catalog homes.

This does not interpret policy expressions, authorize rows, or issue SQL.
Association Record references retain object-table homes, not invented edge types.
"""
import json
from hashlib import sha256

def map_catalog_dependencies(assessment_bytes,response_bytes,original_request=None):
    if any(type(raw) is not bytes or not 1<=len(raw)<=16777216 for raw in (assessment_bytes,response_bytes)):raise ValueError('Bounded original mapping carriers required')
    assessment=json.loads(assessment_bytes);handoff=json.loads(response_bytes)['handoff'];inventory=assessment['inventory']
    ontology=None
    if original_request is not None:
        if type(original_request) is not bytes or not 1<=len(original_request)<=4_000_000:raise ValueError('Bounded original ontology request required')
        request=json.loads(original_request)
        if sha256(request['ontologyJson'].encode()).hexdigest()!=handoff['ontologySha256']:raise ValueError('Original compiler ontology bytes required')
        ontology=json.loads(request['ontologyJson'])
    def ref(value):
        if type(value) is not dict or set(value)!={'documentId','moduleId','elementId'} or any(type(v) is not str for v in value.values()):raise ValueError('Exact original qualified reference required')
        return tuple(value[k] for k in ('documentId','moduleId','elementId'))
    def index(rows,address):
        result={}
        for row in rows:
            if row['retired_rev'] is None:result.setdefault(address(row),[]).append(row)
        return result
    types=index(inventory['types'],lambda r:(r['document_id'],r['module'],r['element']))
    properties=index(inventory['properties'],lambda r:(r['type_id'],r['definition_document_id'],r['declaration_module'],r['element']))
    keys=index(inventory['keys'],lambda r:(r['type_id'],r['key_id']))
    def one(rows):
        if len(rows)!=1:raise ValueError('Unique active native dependency required')
        return rows[0]
    def type_home(reference):
        d,m,e=ref(reference)
        row=one(types.get((d,m,e),[]))
        if row['kind']!='record' or type(row['type_id']) is not int or row['type_id']<1:raise ValueError('Original native Record home required')
        return row['type_id']
    def property_home(target,reference):
        owner=type_home(target);d,m,e=ref(reference)
        row=one(properties.get((owner,d,m,e),[]))
        if type(row['prop_id']) is not int or row['prop_id']<1 or row['home'] not in ('json','row'):raise ValueError('Original native property home required')
        return {'reference':reference,'typeId':str(owner),'propertyId':str(row['prop_id']),'home':row['home']}
    def key_home(value):
        owner=type_home(value['target']);row=one(keys.get((owner,value['keyId']),[]))
        properties=[property_home(value['target'],f) for f in value['fields']]
        if row['prop_ids']!=[int(p['propertyId']) for p in properties]:raise ValueError('Exact original native key field order required')
        return {'target':value['target'],'typeId':str(owner),'keyId':value['keyId'],'keyNumber':str(row['key_num']),'fields':properties}
    def association_home(reference,action_keys):
        result={'reference':reference,'typeId':str(type_home(reference)),'home':'truss.object'}
        if ontology is None:return result
        declaration=one([a for a in ontology['associations'] if ref(a['type'])==ref(reference)])
        witness_key=one([k for k in action_keys if ref(k['target'])==ref(reference) and k['keyId']==declaration['keyId']])
        result['key']=key_home(witness_key)
        roles=set();endpoints=[]
        choices=ontology['entities']+ontology['associations']
        for endpoint in declaration['endpoints']:
            role=endpoint['role']
            if type(role) is not str or not role or role in roles:raise ValueError('Original unique endpoint role required')
            roles.add(role)
            choice=one([e for e in choices if ref(e['type'])==ref(endpoint['target'])])
            target_key=one([k for k in action_keys if ref(k['target'])==ref(endpoint['target']) and k['keyId']==choice['keyId']])
            native_key=key_home(target_key)
            source_fields=[property_home(reference,f) for f in endpoint['fields']]
            if len(source_fields)!=len(native_key['fields']) or not source_fields:raise ValueError('Original endpoint key arity required')
            endpoints.append({'role':role,'target':endpoint['target'],'key':native_key,'pairs':[{'associationField':source,'targetKeyField':target} for source,target in zip(source_fields,native_key['fields'])]})
        result['endpoints']=endpoints
        return result
    scans=[];seen=set()
    for scan in handoff['scans']:
        occurrence=scan['scan']
        if type(occurrence) is not str or occurrence in seen:raise ValueError('Unique original scan occurrence required')
        seen.add(occurrence)
        actions=[]
        for action in scan['actions']:
            actions.append({'action':action['action'],'ruleIds':action['ruleIds'],'context':action['context'],
                'associations':[association_home(a,action['keys']) for a in action['associations']],
                'fields':[{'target':f['target'],'fields':[property_home(f['target'],v) for v in f['fields']]} for f in action['fields']],
                'keys':[key_home(k) for k in action['keys']]})
        scans.append({'scan':occurrence,'target':scan['target'],'typeId':str(type_home(scan['target'])),'home':'truss.object','projectionFields':[property_home(scan['target'],f) for f in scan['projectionFields']],'queryFields':[property_home(scan['target'],f) for f in scan['queryFields']],'actions':actions})
    scan_index={s['scan']:s for s in scans}
    uses=[]
    for use in handoff['uses']:
        scan=scan_index.get(use['scan'])
        if scan is None:raise ValueError('Original use scan occurrence required')
        if ref(scan['target'])!=ref(use['target']):raise ValueError('Original use/scan target correspondence required')
        uses.append({**use,'native':property_home(use['target'],use['field'])})
    result=json.dumps({'version':'truss.native-security-dependencies/0.1' if ontology is None else 'truss.native-security-dependencies/0.2','scope':'original_compiler_dependency_to_native_catalog_correspondence_only','revision':assessment['revision'],'installationId':assessment['installationId'],'releaseSha256':assessment['releaseSha256'],'scans':scans,'uses':uses,'securityReady':False},sort_keys=True,separators=(',',':')).encode()
    if len(result)>16777216:raise ValueError('Native dependency mapping output budget exceeded')
    return result
