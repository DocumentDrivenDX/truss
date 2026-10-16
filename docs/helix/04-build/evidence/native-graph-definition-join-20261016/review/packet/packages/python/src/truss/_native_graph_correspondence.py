"""Actual-context/native association definition data; never a native permit."""
from dataclasses import dataclass
from hashlib import sha256
import json
from ._native_model_correspondence import capture_native_model_correspondence_with_cursor,_ref,_only,_positive,_column
from ._owner_evidence_json import decode_issued_model_requirements_json,decode_owner_evidence_json


def _endpoint(endpoint,records):
    row=_only([r for r in records if _ref(r['record'])==_ref(endpoint['target'])],'Exact endpoint Record required')
    key=endpoint['key'];selected=row['selectedKey']
    if key!={'record':row['record'],'id':selected['id'],'fields':selected['fields']}:
        raise ValueError('Original ordered endpoint Key required')
    return row


def _join(model,requirements,check_deadline):
    """Pure supplied-data join; only the factory obtains original issued inputs."""
    graph=decode_issued_model_requirements_json(requirements)
    original=decode_issued_model_requirements_json(model.requirements)
    mapped=decode_owner_evidence_json(model.report)
    if (graph.get('version')!='weft.current-presence.graph-requirements/0.1-candidate'
            or graph.get('scope')!='original-association-endpoint-requirements-only'
            or any(graph.get(k) is not False for k in ('complete','authority','securityReady'))
            or graph.get('nativeAdmission')!='required'
            or any(graph.get(k)!=original[k] for k in ('sourceRequestJson','sourceRequestSha256','preparationSha256','modelPins'))
            or graph.get('modelRequirementsSha256')!=sha256(model.requirements).hexdigest()):
        raise ValueError('Same actual context Graph and Model requirements required')
    associations=graph.get('associations')
    if type(associations) is not list or len(associations)>256:raise ValueError('Bounded original association census required')
    native=decode_owner_evidence_json(model.observation.accepted_assessment)['inventory']
    inventory=decode_owner_evidence_json(model.observation.native_inventory)
    records=mapped['records'];results=[];seen=set();native_seen=set()
    pins={p['documentId']:p['revision'] for p in graph['modelPins']}
    for ordinal,a in enumerate(associations):
        check_deadline();ref=a['reference'];kind=a['kind']
        if type(a.get('ordinal')) is not int or a['ordinal']!=ordinal:raise ValueError('Original association occurrence order required')
        if kind=='record-members':
            owner=_endpoint({'target':a['owner'],'key':a['key']},records)
            identity=(*_ref(a['owner']),'record-members')
            if ref!={'documentId':identity[0],'moduleId':identity[2],'elementId':identity[3]} or a['revision']!=identity[1]:raise ValueError('Original nominal association Record required')
            members={_ref(f['field']):f['propertyId'] for f in owner['fields']};endpoints=[]
            for endpoint in a['endpoints']:
                target=_endpoint(endpoint,records);fields=[_ref(m['field']) for m in endpoint['members']]
                if not fields or len(fields)!=len(target['selectedKey']['fields']) or any(f not in members for f in fields):raise ValueError('Original association member properties required')
                endpoints.append({'role':endpoint['role'],'targetTypeId':target['typeId'],'memberPropertyIds':[members[f] for f in fields]})
            result={'ordinal':ordinal,'kind':kind,'reference':ref,'ownerTypeId':owner['typeId'],'endpoints':endpoints}
        elif kind=='core-relationship':
            if set(ref)!={'documentId','moduleId','relationshipId'} or any(type(v) is not str or not v for v in ref.values()) or pins.get(ref['documentId'])!=a['revision']:raise ValueError('Original nominal graph identity required')
            identity=(ref['documentId'],a['revision'],ref['moduleId'],ref['relationshipId'],kind)
            if a['witness']!={'kind':'opaque-existential'} or a['associationRecord'] is not None or len(a['sources'])!=1 or len(a['targets'])!=1:raise ValueError('Singular opaque graph realization required')
            row=_only([r for r in native['relationships'] if (r['document_id'],r['module'],r['rel_id'])==(identity[0],identity[2],identity[3]) and r['retired_rev'] is None],'Exact active native graph definition required')
            number=_positive(row['rel_type_id']);authored=a['authored']
            if number in native_seen:raise ValueError('Distinct native graph identity required')
            native_seen.add(number)
            if (authored.get('directed') is not True or row['directed'] is not True or row['assoc_type_id'] is not None or 'associationRecord' in authored
                    or row['lifecycle']!=authored['targetLifecycle'] or row['composition'] is not authored.get('composition',False) or row['inverse']!=authored.get('inverse')):raise ValueError('Original native graph declaration required')
            endpoints=a['endpoints'];output=[]
            if len(endpoints)!=2 or {e['side'] for e in endpoints}!={'source','target'} or len({e['role'] for e in endpoints})!=2:raise ValueError('Complete distinct native graph roles required')
            for side in ('source','target'):
                endpoint=_only([e for e in endpoints if e['side']==side],'Original graph side required');target=_endpoint(endpoint,records)
                declaration=a['sources' if side=='source' else 'targets'][0]
                if (endpoint['declarationOrdinals']!=[0] or type(endpoint['declarationOrdinals'][0]) is not int or declaration['record']!=target['record']
                        or side=='target' and (declaration['key']!=endpoint['key'] or row['target_key']!=endpoint['key']['id'])):raise ValueError('Original declared endpoint Key required')
                bounds=authored[side+'Multiplicity'];low=bounds['min'];high=bounds['max']
                if (type(low) is not int or low<0 or not (high=='*' or type(high) is int and high>=low)
                        or type(row[side+'_min']) is not int or row[side+'_min']!=low
                        or high=='*' and row[side+'_max'] is not None
                        or high!='*' and (type(row[side+'_max']) is not int or row[side+'_max']!=high)):raise ValueError('Original native graph multiplicity required')
                output.append({'role':endpoint['role'],'side':side,'targetTypeId':target['typeId'],'key':endpoint['key'],'keyNum':target['selectedKey']['keyNum']})
            pairs=[r for r in native['endpoints'] if r['rel_type_id']==number]
            if len(pairs)!=1 or any(type(pairs[0][k]) is not int for k in ('source_type','target_type')) or (pairs[0]['source_type'],pairs[0]['target_type'])!=tuple(e['targetTypeId'] for e in output):raise ValueError('Complete typed native graph alternatives required')
            home=_only([r for r in inventory['relations'] if r['name']=='edge'],'Original native edge home required')
            columns={name:_column(home,name,oid) for name,oid in [('id','20'),('rel_type_id','23'),('ver','20'),('source_id','20'),('source_type','23'),('target_id','20'),('target_type','23'),('props','3802')]}
            result={'ordinal':ordinal,'kind':kind,'reference':ref,'relationshipTypeId':number,'home':{'relationOid':home['oid'],'columns':columns},'endpoints':output,'witness':a['witness']}
        else:raise ValueError('Supported original association requirements required')
        if identity in seen:raise ValueError('Distinct original association selection required')
        seen.add(identity);results.append(result)
    report={'version':'truss.native-graph.correspondence/0.1-candidate','scope':'actual-context-native-association-definition-correspondence','complete':False,'authority':False,'securityReady':False,'nativeAdmission':'required','preparationSha256':graph['preparationSha256'],'modelCorrespondenceSha256':sha256(model.report).hexdigest(),'graphRequirementsSha256':sha256(requirements).hexdigest(),'associations':results,'unresolved':['whole-source semantic admission and complete codecs/domains','complete graph occurrences and fact/Key population correspondence','authenticated continuously held operation/source/current authority and final guarded release']}
    raw=json.dumps(report,separators=(',',':')).encode()
    if len(raw)>4_000_000:raise ValueError('Native graph correspondence capacity exceeded')
    check_deadline();return raw


@dataclass(frozen=True)
class NativeGraphCorrespondence:
    model:object
    requirements:bytes
    report:bytes


def capture_native_graph_correspondence_with_cursor(cursor,*,current,accepted_request):
    from weft import weft as native
    cls=getattr(native,'CurrentPresencePreparation',None)
    if cls is None or type(current) is not cls or not callable(getattr(cls,'graph_requirements_json',None)):raise ValueError('Actual opt-in Graph presence preparation required')
    parent=cls.source_preparation(current);cursor._deadline.check()
    model=capture_native_model_correspondence_with_cursor(cursor,current=current,accepted_request=accepted_request)
    requirements=cls.graph_requirements_json(current).encode();cursor._deadline.check()
    report=_join(model,requirements,cursor._deadline.check)
    if (model.current is not current or model.parent is not parent or cls.source_preparation(current) is not parent
            or sha256(cls.json(current).encode()).hexdigest()!=json.loads(report)['preparationSha256']):raise ValueError('Original Graph preparation and parent must remain held')
    cursor._deadline.check();return NativeGraphCorrespondence(model,requirements,report)
