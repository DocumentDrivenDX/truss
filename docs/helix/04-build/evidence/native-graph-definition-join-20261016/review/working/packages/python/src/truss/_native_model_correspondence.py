"""Actual-context/native identity join data; never a native authority witness."""
from dataclasses import dataclass
from hashlib import sha256
import json
from ._native_source_observation import capture_native_source_observation_with_cursor
from ._owner_evidence_json import decode_owner_evidence_json,decode_issued_model_requirements_json

MAX_REPORT_BYTES=4_000_000
MAX_REQUIREMENTS_BYTES=16_000_000


def _ref(value):
    if type(value) is not dict or set(value)!={'documentId','revision','module','element'} or any(type(v) is not str or not v for v in value.values()):
        raise ValueError('Complete original model identity required')
    return tuple(value[k] for k in ('documentId','revision','module','element'))


def _positive(value,maximum=2147483647):
    if type(value) is not int or not 1<=value<=maximum:raise ValueError('Exact native identity required')
    return value


def _only(values,message):
    if len(values)!=1:raise ValueError(message)
    return values[0]


def _column(relation,name,type_oid):
    column=_only([c for c in relation['columns'] if c['name']==name],'Original native object column required')
    if column['typeOid']!=type_oid or column['typmod']!=-1 or column['collationOid']!='0' or column['dropped'] is not False or column['generated'] or column['identity'] or column['notNull'] is not True:
        raise ValueError('Supported original native object column required')
    return {'attnum':column['attnum'],'typeOid':column['typeOid']}


def _join(observation,requirements,preparation_sha256,check_deadline):
    if type(requirements) is not bytes or not 1<=len(requirements)<=MAX_REQUIREMENTS_BYTES:raise ValueError('Bounded issued requirements required')
    issued=decode_issued_model_requirements_json(requirements)
    if (type(issued) is not dict or issued.get('version')!='weft.current-presence.model-requirements/0.1-candidate'
            or issued.get('scope')!='original-record-field-key-requirements-only' or issued.get('complete') is not False
            or issued.get('authority') is not False or issued.get('securityReady') is not False
            or issued.get('nativeAdmission')!='required' or issued.get('preparationSha256')!=preparation_sha256
            or type(issued.get('sourceRequestJson')) is not str):raise ValueError('Original incomplete requirements profile required')
    original=issued['sourceRequestJson'].encode()
    if sha256(original).hexdigest()!=issued.get('sourceRequestSha256'):raise ValueError('Original requirements source hash required')
    source=decode_owner_evidence_json(original);accepted=decode_owner_evidence_json(observation.accepted_request)
    assessment=decode_owner_evidence_json(observation.accepted_assessment);inventory=decode_owner_evidence_json(observation.native_inventory)
    modules=source.get('modules')
    if (type(modules) is not list or not modules or len(modules)>256
            or type(accepted.get('modules')) is not list or len(modules)!=len(accepted['modules'])
            or assessment.get('version')!='truss.accepted-catalog-assessment/0.2-candidate'
            or inventory.get('version')!='truss.native-source.inventory/0.2-candidate'
            or issued.get('modelPins')!=assessment.get('modelPins')
            or issued['modelPins']!=[m['pin'] for m in modules]
            or any(m['pin']!=a['pin'] or m['documentJson']!=a['documentJson'] for m,a in zip(modules,accepted['modules']))):
        raise ValueError('Exact accepted original model sources required')
    pins={p['documentId']:p for p in issued['modelPins']}
    if len(pins)!=len(modules):raise ValueError('Distinct original model pins required')
    homes=inventory['relations'];home=_only([r for r in homes if r['name']=='object'],'Original native object home required')
    slots={name:_column(home,name,oid) for name,oid in [('id','20'),('type_id','23'),('props','3802')]}
    records=issued.get('records')
    if type(records) is not list or not 1<=len(records)<=4096:raise ValueError('Complete bounded Record requirements required')
    native=assessment['inventory'];results=[];seen=set();native_seen=set()
    for record in records:
        check_deadline();ref=record['record'];identity=_ref(ref)
        if identity in seen or pins.get(identity[0],{}).get('revision')!=identity[1]:raise ValueError('Distinct pinned Record requirements required')
        seen.add(identity)
        row=_only([t for t in native['types'] if (t['document_id'],t['module'],t['element'])==(identity[0],identity[2],identity[3]) and t['retired_rev'] is None],'Exact active native Record required')
        if row['kind']!='record' or row['provisional'] is not False:raise ValueError('Original realized native Record required')
        type_id=_positive(row['type_id'])
        if type_id in native_seen:raise ValueError('Distinct native Record IDs required')
        native_seen.add(type_id);properties=[p for p in native['properties'] if p['type_id']==type_id and p['retired_rev'] is None]
        fields=record['fields']
        if type(fields) is not list or len(fields)!=len(properties) or not fields:raise ValueError('Complete original property membership required')
        mapped=[];by_ref={};prop_ids=set()
        for field in fields:
            field_ref=field['field'];fid=_ref(field_ref)
            if fid in by_ref or pins.get(fid[0],{}).get('revision')!=fid[1]:raise ValueError('Distinct pinned Field requirements required')
            prop=_only([p for p in properties if (p['definition_document_id'],p['declaration_module'],p['element'])==(fid[0],fid[2],fid[3])],'Exact native property membership required')
            prop_id=_positive(prop['prop_id']);descriptors=field['descriptors']
            if (prop_id in prop_ids or prop['home']!='json' or prop['cardinality']!='one'
                    or prop['scalar_type'] not in ('string','boolean','integer','decimal','binary')
                    or prop['nullability'] not in ('required','absent-allowed')
                    or type(descriptors) is not list or len(descriptors)!=1):raise ValueError('Supported singular native JSON property required')
            descriptor=descriptors[0]
            if (descriptor.get('identity')!=field_ref or descriptor.get('kind')!='scalar'
                    or descriptor.get('availability')!=prop['nullability']
                    or type(descriptor.get('type')) is not dict or descriptor['type'].get('family')!=prop['scalar_type']
                    or descriptor['type'].get('nullable') is not False):raise ValueError('Original scalar descriptor/native labels required')
            prop_ids.add(prop_id);by_ref[fid]=prop_id
            mapped.append({'field':field_ref,'propertyId':prop_id,'jsonKey':str(prop_id)})
        key=record['selectedKey'];ordered=[_ref(f) for f in key['fields']]
        if not ordered or len(set(ordered))!=len(ordered) or any(f not in by_ref for f in ordered):raise ValueError('Complete ordered original Key required')
        key_row=_only([k for k in native['keys'] if k['type_id']==type_id and k['key_id']==key['id'] and k['retired_rev'] is None],'Exact native selected Key required')
        if type(key_row['prop_ids']) is not list or any(type(v) is not int or not 1<=v<=2147483647 for v in key_row['prop_ids']) or key_row['prop_ids']!=[by_ref[f] for f in ordered]:raise ValueError('Original ordered native Key properties required')
        key_num=_positive(key_row['key_num'],32767)
        results.append({'record':ref,'typeId':type_id,'objectHome':{'relationOid':home['oid'],'columns':slots},'fields':mapped,'selectedKey':{'id':key['id'],'fields':key['fields'],'keyNum':key_num,'propertyIds':key_row['prop_ids']}})
    sources=[('accepted-request',observation.accepted_request),('accepted-assessment',observation.accepted_assessment),('runtime-release',observation.runtime_release),('native-inventory',observation.native_inventory),('issued-requirements',requirements)]
    report={'version':'truss.native-model.correspondence/0.1-candidate','scope':'actual-context-native-record-member-key-correspondence','complete':False,'authority':False,'securityReady':False,'nativeAdmission':'required','preparationSha256':preparation_sha256,'sources':[{'role':role,'sha256':sha256(raw).hexdigest(),'bytes':len(raw)} for role,raw in sources],'records':results,'unresolved':['whole-source UMF semantic admission','full original facets/domain/comparator/codec equivalence and native key namespace/bytes','graph and context correspondence; other property/home realizations','authenticated continuously held native operation/source/authority witness','closing guards and guarded release']}
    raw=json.dumps(report,separators=(',',':'),ensure_ascii=True).encode()
    if len(raw)>MAX_REPORT_BYTES:raise ValueError('Native correspondence report capacity exceeded')
    decode_owner_evidence_json(raw);check_deadline();return raw


@dataclass(frozen=True,slots=True)
class NativeModelCorrespondence:
    observation:object
    requirements:bytes
    report:bytes
    current:object
    parent:object


def capture_native_model_correspondence_with_cursor(cursor,*,current,accepted_request):
    # The optional compiler is imported only on explicit invocation. No supplied
    # JSON, callback or metadata object supplies the native current argument.
    # The returned dataclass is data, not an unforgeable witness/capability.
    from weft import weft as native
    cls=native.CurrentPresencePreparation
    if type(current) is not cls or not callable(getattr(cls,'model_requirements_json',None)):
        raise ValueError('Actual opt-in presence preparation required')
    parent=cls.source_preparation(current);cursor._deadline.check()
    requirements=cls.model_requirements_json(current).encode();preparation=cls.json(current).encode();cursor._deadline.check()
    observation=capture_native_source_observation_with_cursor(cursor,accepted_request)
    report=_join(observation,requirements,sha256(preparation).hexdigest(),cursor._deadline.check)
    if cls.json(current).encode()!=preparation:raise ValueError('Original preparation report must remain held')
    if cls.source_preparation(current) is not parent:raise ValueError('Original issued parent must remain held')
    cursor._deadline.check()
    return NativeModelCorrespondence(observation,requirements,report,current,parent)
