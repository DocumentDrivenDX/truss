"""Map original Weft dependency references to assessed native catalog homes.

This does not interpret policy expressions, authorize rows, or issue SQL.
Association Record references retain object-table homes, not invented edge types.
"""
import json

def map_catalog_dependencies(assessment_bytes,response_bytes):
    if any(type(raw) is not bytes or not 1<=len(raw)<=16777216 for raw in (assessment_bytes,response_bytes)):raise ValueError('Bounded original mapping carriers required')
    assessment=json.loads(assessment_bytes);handoff=json.loads(response_bytes)['handoff'];inventory=assessment['inventory']
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
    scans=[];seen=set()
    for scan in handoff['scans']:
        occurrence=scan['scan']
        if type(occurrence) is not str or occurrence in seen:raise ValueError('Unique original scan occurrence required')
        seen.add(occurrence)
        actions=[]
        for action in scan['actions']:
            actions.append({'action':action['action'],'ruleIds':action['ruleIds'],'context':action['context'],
                'associations':[{'reference':a,'typeId':str(type_home(a)),'home':'truss.object'} for a in action['associations']],
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
    result=json.dumps({'version':'truss.native-security-dependencies/0.1','scope':'original_compiler_dependency_to_native_catalog_correspondence_only','revision':assessment['revision'],'installationId':assessment['installationId'],'releaseSha256':assessment['releaseSha256'],'scans':scans,'uses':uses,'securityReady':False},sort_keys=True,separators=(',',':')).encode()
    if len(result)>16777216:raise ValueError('Native dependency mapping output budget exceeded')
    return result
