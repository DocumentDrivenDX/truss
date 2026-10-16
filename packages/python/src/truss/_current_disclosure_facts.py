"""Private complete logical fact capture, not a caller or query permit.

The trusted private executor owns the actual native cursor and DDL/source
custody. Source/fact table cuts remain held until outer host settlement. No
query predicate, SQL fragment or caller-selected population is accepted here.
"""
from dataclasses import dataclass
import base64
import json
from ._current_query_sources import capture_current_query_sources_with_cursor, CurrentQuerySourceCapture
from ._current_query_pipe import _envelope
from ._owner_evidence_json import decode_owner_evidence_json
from ._security_catalog_subject_installation import _text_rows
from ._umf_key_tuples import (KeyTupleRequest, encode_key_tuples, key_value_from_cell,
                             _owner_key_value)
from ._current_query_originals import require_current_model_correspondence


@dataclass(frozen=True, slots=True)
class CurrentDisclosureFactCapture:
    sources: CurrentQuerySourceCapture
    facts_bytes: bytes
    coverage_bytes: bytes
    # Private actual row identity/version and original owner Key receipt.
    rows: tuple[tuple[str,str,str,bytes,bytes,bytes], ...]
    graphs_bytes: bytes
    graph_coverage_bytes: bytes
    graph_rows: tuple[tuple[str, ...], ...]


def _identity(ref):
    if type(ref) is not dict or set(ref) != {'documentId','moduleId','elementId'} or any(type(v) is not str or not v for v in ref.values()):
        raise ValueError('Original qualified fact identity required')
    return tuple(ref[k] for k in ('documentId','moduleId','elementId'))


def _cell(cell, family):
    if cell == {'kind':'null'}:
        return None
    if family == 'boolean' and type(cell) is dict and set(cell) == {'kind','value'} and cell['kind'] == family and type(cell['value']) is bool:
        return {'boolean':cell['value']}
    if (type(cell) is not dict or set(cell) != {'kind','text'} or cell['kind'] != family or type(cell['text']) is not str):
        raise ValueError('Exact native scalar fact cell required')
    token = cell['text']
    if family == 'binary':
        return {'binaryHex':base64.b64decode(token,validate=True).hex()}
    wrapper = {'string':'string','integer':'integerToken','decimal':'decimalToken'}.get(family)
    if wrapper is None:
        raise ValueError('Unsupported original fact scalar family')
    return {wrapper:token}


def _key_batches(document, pending):
    """Partition before dispatch within the original encoder's unchanged limits."""
    if not 0 < len(document) <= 1048576:
        raise ValueError('Bounded original fact Key document required')
    maximum=min(128,4194304//len(document))
    base=len(json.dumps({'sourceText':document.decode('utf-8'),'requests':[]},
                        ensure_ascii=True,separators=(',',':')).encode())
    batch=[];size=base
    for item in pending:
        request=item[2]
        wire={'identity':{'module':request.module_id,'element':request.record_id,'key':request.key_id},
              'values':[_owner_key_value(value) for value in request.values]}
        extra=len(json.dumps(wire,ensure_ascii=True,separators=(',',':')).encode())
        if base+extra>1048576:
            raise ValueError('Individual original fact Key request exceeds input limit')
        if batch and (len(batch)==maximum or size+1+extra>1048576):
            yield batch
            batch=[];size=base
        size+=extra+(1 if batch else 0)
        batch.append(item)
    if batch:
        yield batch


def _recipes(sources):
    original = _envelope(sources.initialize_bytes)['sources']
    assessment = decode_owner_evidence_json(sources.accepted_assessment_bytes)
    modules=require_current_model_correspondence(sources.initialize_bytes,sources.accepted_request_bytes)
    ontology = original['ontology']
    if ontology['context']:
        raise ValueError('Declared context fact capture is not implemented')
    inventory = assessment['inventory'];recipes=[];seen_types=set()
    for entity in ontology['entities']:
        ref = entity['type'];identity = _identity(ref)
        types = [t for t in inventory['types'] if (t['document_id'],t['module'],t['element']) == identity and t['retired_rev'] is None]
        if len(types) != 1 or types[0]['kind'] != 'record' or types[0]['provisional']:
            raise ValueError('Original active fact Record required')
        type_id = types[0]['type_id']
        if type(type_id) is not int or type_id < 1 or type_id in seen_types:
            raise ValueError('Distinct native fact Record identities required')
        seen_types.add(type_id);fields=[];seen_fields=set()
        for selected in entity['fields']:
            field=selected['ref'];field_id=_identity(field)
            if field_id in seen_fields:
                raise ValueError('Distinct original fact fields required')
            seen_fields.add(field_id)
            properties=[p for p in inventory['properties'] if p['type_id']==type_id and
                        (p['definition_document_id'],p['declaration_module'],p['element'])==field_id and p['retired_rev'] is None]
            if len(properties)!=1:
                raise ValueError('Original native fact Field correspondence required')
            prop=properties[0]
            if (prop['home']!='json' or prop['cardinality']!='one' or prop['nullability'] not in ('required','absent-allowed')
                    or prop['scalar_type'] not in ('string','boolean','integer','decimal','binary')):
                raise ValueError('Supported singular JSON fact Field required, including empty populations')
            fields.append((field,prop))
        keys=[k for k in inventory['keys'] if k['type_id']==type_id and k['key_id']==entity['keyId'] and k['retired_rev'] is None]
        if len(keys)!=1 or not keys[0]['prop_ids'] or any(not any(p['prop_id']==number for _,p in fields) for number in keys[0]['prop_ids']):
            raise ValueError('Complete ordered original fact Key fields required')
        recipes.append((type_id,ref,fields,keys[0],modules[identity[0]]['documentJson'].encode()))
    if not recipes or len(recipes)>256:
        raise ValueError('Bounded complete typed fact source required')
    return recipes


def capture_current_disclosure_facts_with_cursor(cursor, *, bun_executable='bun'):
    sources=capture_current_query_sources_with_cursor(cursor)
    if sources.source_profile != "truss-current-disclosure-sources/0.1-candidate":
        raise ValueError("Distinct registered disclosure fact source profile required")
    prior=_text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",limit=1)
    cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
    recipes=_recipes(sources);types=[r[0] for r in recipes];key_numbers=[r[3]['key_num'] for r in recipes]
    cursor.execute('LOCK TABLE ONLY truss.object,truss.object_key_bucket IN SHARE MODE NOWAIT',prepare=False)
    homes=_text_rows(cursor,"SELECT c.relname::text,c.relkind::text,c.relpersistence::text,c.relrowsecurity::text,c.relforcerowsecurity::text,(c.relowner=i.owner_oid)::text,EXISTS(SELECT 1 FROM pg_catalog.pg_inherits p WHERE p.inhrelid=c.oid OR p.inhparent=c.oid)::text FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace CROSS JOIN truss.catalog_runtime_installation i WHERE n.nspname='truss' AND c.relname IN ('object','object_key_bucket') AND i.singleton ORDER BY c.relname",limit=2)
    if homes != [(name,'r','p','false','false','true','false') for name in ('object','object_key_bucket')]:
        raise ValueError('Complete unfiltered native fact homes required')
    census=_text_rows(cursor,"SELECT count(*)::text,coalesce(sum(octet_length(props::text)),0)::text,coalesce(bool_or(root_id IS NOT NULL OR root_type IS NOT NULL),false)::text FROM ONLY truss.object WHERE type_id=ANY(%s::int[])",(types,),1)
    if len(census)!=1 or not census[0][0].isdigit() or int(census[0][0])>10000 or not census[0][1].isdigit() or int(census[0][1])>8388608 or census[0][2]!='false':
        raise ValueError('Bounded complete rootless fact population required')
    count=int(census[0][0])
    rows=_text_rows(cursor,'SELECT id::text,type_id::text,ver::text,props::text FROM ONLY truss.object WHERE type_id=ANY(%s::int[]) ORDER BY type_id,id',(types,),10000)
    if len(rows)!=count:
        raise ValueError('Complete original fact census correspondence required')
    key_census=_text_rows(cursor,'SELECT count(*)::text,coalesce(sum(octet_length(k.key_bytes)+octet_length(k.namespace_bytes)),0)::text FROM ONLY truss.object_key_bucket k JOIN ROWS FROM(pg_catalog.unnest(%s::int[]),pg_catalog.unnest(%s::smallint[])) w(type_id,key_num) ON w.type_id=k.type_id AND w.key_num=k.key_num',(types,key_numbers),1)
    if len(key_census)!=1 or key_census[0][0]!=str(count) or not key_census[0][1].isdigit() or int(key_census[0][1])>8388608:
        raise ValueError('Bounded complete native fact Key custody required')
    keys=_text_rows(cursor,"SELECT k.object_id::text,k.type_id::text,k.key_num::text,pg_catalog.encode(k.namespace_bytes,'hex'),pg_catalog.encode(k.key_bytes,'hex') FROM ONLY truss.object_key_bucket k JOIN ROWS FROM(pg_catalog.unnest(%s::int[]),pg_catalog.unnest(%s::smallint[])) w(type_id,key_num) ON w.type_id=k.type_id AND w.key_num=k.key_num ORDER BY k.type_id,k.object_id",(types,key_numbers),10000)
    key_map={(r[0],r[1],r[2]):(r[3],r[4]) for r in keys}
    if len(key_map)!=count:
        raise ValueError('Distinct complete native fact Key rows required')
    facts=[];private=[];coverage=[];retained_bytes=sum(len(r[3])+len(r[4]) for r in keys)
    for type_id,ref,fields,key,document in recipes:
        namespace_rows=_text_rows(cursor,"SELECT pg_catalog.encode(pg_catalog.convert_to(pg_catalog.jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',i.installation_id::text,'sourceEpoch',i.source_epoch::text,'typeId',%s::text,'keyNumber',%s::text,'definitionPin',d.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8'),'hex') FROM truss.runtime_current_installation() i CROSS JOIN LATERAL truss.runtime_definition('key',%s,%s) d",(str(type_id),str(key['key_num']),type_id,key['key_num']),1)
        if len(namespace_rows)!=1:
            raise ValueError('Original native fact Key namespace required')
        namespace=bytes.fromhex(namespace_rows[0][0])
        selected=[row for row in rows if row[1]==str(type_id)]
        key_fields=[next((field,prop) for field,prop in fields if prop['prop_id']==number) for number in key['prop_ids']]
        pending=[]
        for object_id,_,version,props_text in selected:
            props=decode_owner_evidence_json(props_text.encode());values=[];absent=[]
            if type(props) is not dict:
                raise ValueError('Original native fact property map required')
            for field,prop in fields:
                address=str(prop['prop_id'])
                if address not in props:
                    if prop['nullability']!='absent-allowed':
                        raise ValueError('Required fact Field absent')
                    absent.append(field)
                else:
                    literal=_cell(props[address],prop['scalar_type'])
                    if literal is None and prop['nullability']=='required':
                        raise ValueError('Required fact Field null')
                    values.append({'field':field,'value':literal})
            key_values=tuple(key_value_from_cell(props[str(prop['prop_id'])]) for _,prop in key_fields)
            request=KeyTupleRequest(ref['moduleId'],ref['elementId'],key['key_id'],key_values)
            pending.append((object_id,version,request,values,absent))
        # Original UMF keeps its own per-call limits. No partial result escapes.
        for batch in _key_batches(document,pending):
            cursor._deadline.check()
            encoded=encode_key_tuples(document,tuple(item[2] for item in batch),bun_executable=bun_executable,deadline=cursor._deadline)
            cursor._deadline.check()
            for (object_id,version,request,values,absent),original in zip(batch,encoded,strict=True):
                transport=('umf-key-tuple-v1:hex:'+original.tuple_bytes.hex()).encode('ascii')
                if key_map.get((object_id,str(type_id),str(key['key_num'])))!=(namespace.hex(),transport.hex()):
                    raise ValueError('Full original fact Key bytes disagree with native membership')
                facts.append({'type':ref,'key':[_owner_key_value(v) for v in request.values],'fields':values,'absent':absent})
                retained_bytes+=len(original.original_receipt_bytes)+len(namespace)+len(transport)
                if retained_bytes>16777216:
                    raise ValueError('Complete retained fact Key receipts exceed logical limit')
                private.append((object_id,str(type_id),version,original.original_receipt_bytes,namespace,transport))
        coverage.append({'type':ref,'complete':True,'fields':[field for field,_ in fields]})
    graphs_bytes,graph_coverage_bytes,graph_rows=_capture_graphs(cursor,sources,recipes,facts,private)
    facts_bytes=json.dumps(facts,separators=(',',':'),ensure_ascii=True).encode()
    coverage_bytes=json.dumps(coverage,separators=(',',':'),ensure_ascii=True).encode()
    if len(facts_bytes)+len(coverage_bytes)+len(graphs_bytes)+len(graph_coverage_bytes)>8388608:
        raise ValueError('Complete fact output exceeds logical limit')
    cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
    if cursor.fetchmany(2)!=prior:
        raise ValueError('Original fact capture search path restoration required')
    return CurrentDisclosureFactCapture(sources,facts_bytes,coverage_bytes,tuple(private),graphs_bytes,graph_coverage_bytes,graph_rows)

def _relationship_identity(ref):
    if type(ref) is not dict or set(ref)!={'documentId','moduleId','relationshipId'} or any(type(v) is not str or not v for v in ref.values()):
        raise ValueError('Original qualified graph relationship required')
    return tuple(ref[k] for k in ('documentId','moduleId','relationshipId'))


def _positive_native(value):
    if type(value) is not str or not 1<=len(value)<=19 or not value.isascii() or not value.isdecimal() or value.startswith('0') or int(value)>9223372036854775807:
        raise ValueError('Exact positive native graph identity required')
    return value


def _graph_recipes(sources, records):
    """Native correspondence only. Original UMF still validates ontology semantics."""
    original=_envelope(sources.initialize_bytes)['sources']
    modules=require_current_model_correspondence(sources.initialize_bytes,sources.accepted_request_bytes)
    inventory=decode_owner_evidence_json(sources.accepted_assessment_bytes)['inventory']
    entities={_identity(e['type']):e for e in original['ontology']['entities']}
    record_map={_identity(ref):(number,key) for number,ref,_,key,_ in records}
    recipes=[];seen=set();native_seen=set()
    for association in original['ontology']['associations']:
        if association.get('kind')=='record-members':continue
        if association.get('kind')!='core-relationship':
            raise ValueError('Original graph association selection required')
        relationship=association['relationship'];identity=_relationship_identity(relationship)
        if identity in seen:raise ValueError('Distinct graph relationship selection required')
        seen.add(identity)
        # Record-backed witnesses need a separate edge-property/key realization;
        # never turn their native attributes into an opaque existential.
        if association['witness']!={'kind':'opaque-existential'}:
            raise ValueError('Record-backed native graph witness capture remains required')
        document=decode_owner_evidence_json(modules[identity[0]]['documentJson'].encode())
        source_modules=[m for m in document['modules'] if m['id']==identity[1]]
        declarations=[r for m in source_modules for r in m.get('relationships',[]) if r['id']==identity[2]]
        if len(source_modules)!=1 or len(declarations)!=1:raise ValueError('Exact original graph declaration required')
        declaration=declarations[0]
        if declaration.get('directed') is not True or 'associationRecord' in declaration:
            raise ValueError('Original directed opaque graph declaration required')
        targets=declaration.get('target')
        if (type(targets) is not list or len(targets)!=1 or type(targets[0]) is not dict
                or type(targets[0].get('key')) is not str or not targets[0]['key']):
            raise ValueError('Explicit original graph target Key required')
        native=[r for r in inventory['relationships'] if (r['document_id'],r['module'],r['rel_id'])==identity and r['retired_rev'] is None]
        if len(native)!=1:raise ValueError('Exact active native graph definition required')
        native=native[0];number=native['rel_type_id']
        if type(number) is not int or not 0<number<=2147483647 or number in native_seen:
            raise ValueError('Distinct active native graph definition required')
        native_seen.add(number)
        if native['directed'] is not True or native['assoc_type_id'] is not None:
            raise ValueError('Native graph witness realization mismatch')
        for side in ('source','target'):
            multiplicity=declaration[side+'Multiplicity']
            low=multiplicity['min'];high=multiplicity['max']
            if type(low) is not int or low<0 or not (high=='*' or type(high) is int and high>=low):
                raise ValueError('Original graph multiplicity required')
            if native[side+'_min']!=low or native[side+'_max']!=(None if high=='*' else high):
                raise ValueError('Native graph multiplicity differs from original')
        if (native['lifecycle']!=declaration['targetLifecycle'] or native['composition'] is not declaration.get('composition',False)
                or native['inverse']!=declaration.get('inverse')):
            raise ValueError('Native graph lifecycle differs from original')
        endpoints=association['endpoints']
        if type(endpoints) is not list or len(endpoints)!=2 or {e['side'] for e in endpoints}!={'source','target'}:
            raise ValueError('Complete original binary graph roles required')
        roles=set();ordered=[]
        for side in ('source','target'):
            endpoint=next(e for e in endpoints if e['side']==side);role=endpoint['role'];target=endpoint['target'];target_id=_identity(target)
            if type(role) is not str or not role or role in roles or target_id not in record_map or target_id not in entities:
                raise ValueError('Distinct original graph endpoint roles required')
            roles.add(role);actual=declaration[side]
            if (len(actual)!=1 or target_id!=(identity[0],actual[0]['module'],actual[0]['element'])
                    or endpoint['keyId']!=entities[target_id]['keyId'] or record_map[target_id][1]['key_id']!=endpoint['keyId']
                    or 'key' in actual[0] and actual[0]['key']!=endpoint['keyId']):
                raise ValueError('Original typed graph endpoint Key correspondence required')
            ordered.append((role,target,record_map[target_id][0]))
        if native['target_key']!=declaration['target'][0].get('key'):
            raise ValueError('Native graph target Key differs from original')
        pairs=[r for r in inventory['endpoints'] if r['rel_type_id']==number]
        if len(pairs)!=1 or (pairs[0]['source_type'],pairs[0]['target_type'])!=(ordered[0][2],ordered[1][2]):
            raise ValueError('Complete native graph endpoint alternatives required')
        recipes.append((number,relationship,tuple(ordered)))
    if len(recipes)>256:raise ValueError('Bounded original graph source required')
    return recipes


def _capture_graphs(cursor,sources,records,facts,private):
    recipes=_graph_recipes(sources,records)
    if not recipes:return b'[]',b'[]',()
    if len(facts)!=len(private):raise ValueError('Complete original graph endpoint population required')
    record_types={str(number):ref for number,ref,_,_,_ in records};objects={}
    for fact,row in zip(facts,private,strict=True):
        object_id,type_id,version,*_=row
        _positive_native(object_id);_positive_native(type_id);_positive_native(version)
        if (object_id,type_id) in objects or type_id not in record_types or fact['type']!=record_types[type_id]:
            raise ValueError('Exact distinct original graph endpoint identity required')
        objects[object_id,type_id]=fact
    cursor.execute('LOCK TABLE ONLY truss.edge IN SHARE MODE NOWAIT',prepare=False)
    homes=_text_rows(cursor,"SELECT c.relkind::text,c.relpersistence::text,c.relrowsecurity::text,c.relforcerowsecurity::text,(c.relowner=i.owner_oid)::text,EXISTS(SELECT 1 FROM pg_catalog.pg_inherits p WHERE p.inhrelid=c.oid OR p.inhparent=c.oid)::text FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace CROSS JOIN truss.catalog_runtime_installation i WHERE n.nspname='truss' AND c.relname='edge' AND i.singleton",limit=1)
    if homes!=[('r','p','false','false','true','false')]:
        raise ValueError('Complete unfiltered native graph home required')
    numbers=[r[0] for r in recipes]
    census=_text_rows(cursor,"SELECT count(*)::text,coalesce(sum(octet_length(props::text)),0)::text,coalesce(bool_or(props<>'{}'::jsonb),false)::text FROM ONLY truss.edge WHERE rel_type_id=ANY(%s::int[])",(numbers,),1)
    if (len(census)!=1 or not census[0][0].isascii() or not census[0][0].isdigit() or int(census[0][0])+len(facts)>10000
            or not census[0][1].isascii() or not census[0][1].isdigit() or int(census[0][1])>8388608 or census[0][2]!='false'):
        raise ValueError('Bounded complete native opaque graph population required')
    rows=_text_rows(cursor,'SELECT id::text,rel_type_id::text,ver::text,source_id::text,source_type::text,target_id::text,target_type::text FROM ONLY truss.edge WHERE rel_type_id=ANY(%s::int[]) ORDER BY rel_type_id,id',(numbers,),10000)
    if len(rows)!=int(census[0][0]):raise ValueError('Complete native graph census correspondence required')
    selected={str(number):(ref,endpoints) for number,ref,endpoints in recipes};seen=set();graphs=[];retained=2
    coverage=[{'relationship':ref,'complete':True,'roles':[role for role,_,_ in endpoints],'fields':[]} for _,ref,endpoints in recipes]
    covered=json.dumps(coverage,separators=(',',':'),ensure_ascii=True).encode()
    retained+=len(covered)
    for edge_id,relationship_id,version,source_id,source_type,target_id,target_type in rows:
        cursor._deadline.check()
        for token in (edge_id,relationship_id,version,source_id,source_type,target_id,target_type):_positive_native(token)
        if edge_id in seen or relationship_id not in selected:raise ValueError('Distinct selected native graph occurrence required')
        seen.add(edge_id);relationship,endpoints=selected[relationship_id];projected=[]
        for (role,ref,number),object_id,type_id in zip(endpoints,(source_id,target_id),(source_type,target_type),strict=True):
            fact=objects.get((object_id,type_id))
            if type_id!=str(number) or fact is None or fact['type']!=ref:
                raise ValueError('Complete typed original graph endpoint required')
            projected.append({'role':role,'key':fact['key']})
        encoded_row=json.dumps({'relationship':relationship,'witness':{'kind':'opaque-existential','id':edge_id},'endpoints':projected},separators=(',',':'),ensure_ascii=True).encode()
        retained+=len(encoded_row)+(1 if graphs else 0)
        if retained>8388608:raise ValueError('Complete graph output exceeds logical limit')
        graphs.append(encoded_row)
    encoded=b'['+b','.join(graphs)+b']'
    return encoded,covered,tuple(rows)
