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
                             _owner_key_value, _same_json_meaning)


@dataclass(frozen=True, slots=True)
class CurrentQueryFactCapture:
    sources: CurrentQuerySourceCapture
    facts_bytes: bytes
    coverage_bytes: bytes
    # Private actual row identity/version and original owner Key receipt.
    rows: tuple[tuple[str,str,str,bytes,bytes,bytes], ...]


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
    request = decode_owner_evidence_json(sources.accepted_request_bytes)
    assessment = decode_owner_evidence_json(sources.accepted_assessment_bytes)
    modules = {m['pin']['documentId']:m for m in request['modules']}
    closure = original['closure']
    if len(closure['documents']) != len(modules) or len(closure['pins']) != len(modules):
        raise ValueError('Complete original fact source closure required')
    seen = set()
    for entry in closure['documents']:
        document = entry['document'];name = document['id']
        if name in seen or name not in modules:
            raise ValueError('Exact original fact source documents required')
        seen.add(name);module = modules[name]
        if (entry['revision'] != module['pin']['revision']
                or [p for p in closure['pins'] if p['documentId'] == name] != [{'documentId':name,'revision':entry['revision']}]
                or not _same_json_meaning(document,decode_owner_evidence_json(module['documentJson'].encode()))):
            raise ValueError('Original accepted fact source correspondence required')
    ontology = original['ontology']
    if ontology['context']:
        raise ValueError('Declared context fact capture is not implemented')
    if any(a.get('kind') != 'record-members' for a in ontology['associations']):
        raise ValueError('Native graph fact capture remains required for core relationships')
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


def capture_current_query_facts_with_cursor(cursor, *, bun_executable='bun'):
    sources=capture_current_query_sources_with_cursor(cursor)
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
            encoded=encode_key_tuples(document,tuple(item[2] for item in batch),bun_executable=bun_executable)
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
    facts_bytes=json.dumps(facts,separators=(',',':'),ensure_ascii=True).encode()
    coverage_bytes=json.dumps(coverage,separators=(',',':'),ensure_ascii=True).encode()
    if len(facts_bytes)+len(coverage_bytes)>8388608:
        raise ValueError('Complete fact output exceeds logical limit')
    cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
    if cursor.fetchmany(2)!=prior:
        raise ValueError('Original fact capture search path restoration required')
    return CurrentQueryFactCapture(sources,facts_bytes,coverage_bytes,tuple(private))
