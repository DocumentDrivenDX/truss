"""Full reified graph capture/evaluation/buffered-release composition spike.

Trusted administrative host, subject selection and mapping custody are premises.
This is not compiler admission or a protected ordinary-caller API. Fixed table
cuts cover selected facts/catalog receipts through synchronous publication;
routine/role/configuration closure must be supplied by the admitted host layer.
"""
from pathlib import Path
from hashlib import sha256
import json, os, subprocess
from truss.catalog_runtime import _pin_cursor
from truss.psycopg_host import PsycopgHost
from truss._security_catalog_assessment import capture_accepted_catalog
from truss._owner_evidence_json import decode_owner_evidence_json
from security_graph_read import _text_rows
from security_ontology_edge_projection import SPECS, PAIRS, project_full_ontology_edge_cells
from security_owned_read import _pin_owned_evaluator_sources, _read_owned_resource_receipt

ROOT=Path(__file__).resolve().parent.parent
TABLES=('object','edge','schema_head','schema_rev','schema_doc',
        'catalog_registration_request','catalog_acceptance_report',
        'type_def','prop_def','key_def','rel_def','rel_endpoint',
        'relationship_lineage','schema_change','catalog_runtime_installation','runtime_release',
        'runtime_catalog_rebind_transition')


def _capture(cursor,request):
    assessment=capture_accepted_catalog(cursor,request)
    inventory=json.loads(assessment)['inventory']
    def one(rows):
        if len(rows)!=1:raise ValueError('Unique original ontology source home required')
        return rows[0]
    types={};properties={};relationships={}
    for name,fields in SPECS.items():
        record=one([r for r in inventory['types'] if (r['document_id'],r['module'],r['element'])==('adoc','m',name) and r['retired_rev'] is None])
        if record['kind']!='record' or record['provisional']:raise ValueError('Original accepted ontology Record required')
        types[name]=str(record['type_id']);properties[name]={}
        for field in fields:
            prop=one([p for p in inventory['properties'] if p['type_id']==record['type_id'] and p['element']==field and p['retired_rev'] is None])
            family='boolean' if field=='active' else 'integer' if field=='salary' else 'string'
            if (prop['definition_document_id'],prop['declaration_module'],prop['home'],prop['cardinality'],prop['nullability'],prop['scalar_type'])!=('adoc','m','json','one','required',family):
                raise ValueError('Original accepted ontology scalar carrier required')
            properties[name][str(prop['prop_id'])]=(field,family)
        key=one([k for k in inventory['keys'] if k['type_id']==record['type_id'] and k['key_id']=='pk' and k['retired_rev'] is None])
        expected=[int(p) for p,(field,_) in properties[name].items() if field==fields[0]]
        if key['prop_ids']!=expected:raise ValueError('Original authored ontology key order required')
    for name,(left,right) in PAIRS.items():
        rel=one([r for r in inventory['relationships'] if (r['definition_document_id'],r['module'],r['rel_id'])==('adoc','m',name) and r['retired_rev'] is None])
        if (rel['definition_source_kind'],rel['directed'],rel['composition'],rel['target_key'],rel['assoc_type_id'])!=('accepted_document',True,False,'pk',None):
            raise ValueError('Original accepted ontology relationship declaration required')
        endpoint=one([r for r in inventory['endpoints'] if r['rel_type_id']==rel['rel_type_id']])
        if (str(endpoint['source_type']),str(endpoint['target_type']))!=(types[left],types[right]):
            raise ValueError('Original ontology typed relationship endpoints required')
        relationships[name]=str(rel['rel_type_id'])
    raw_objects=tuple(_text_rows(cursor,'SELECT id::pg_catalog.text,type_id::pg_catalog.text,props::pg_catalog.text,(root_id IS NOT NULL)::pg_catalog.text FROM ONLY truss.object ORDER BY id',4))
    edges=tuple(_text_rows(cursor,'SELECT id::pg_catalog.text,rel_type_id::pg_catalog.text,source_id::pg_catalog.text,source_type::pg_catalog.text,target_id::pg_catalog.text,target_type::pg_catalog.text FROM ONLY truss.edge ORDER BY id',6))
    names={value:name for name,value in types.items()};objects=[]
    for identity,type_id,raw,root in raw_objects:
        if root!='false' or type_id not in names:raise ValueError('Complete root ontology population required')
        props=decode_owner_evidence_json(raw.encode());recipe=properties[names[type_id]]
        if type(props) is not dict or set(props)!=set(recipe):raise ValueError('Exact ontology property bag required')
        fields={}
        for address,(field,family) in recipe.items():
            value=props[address];payload='value' if family=='boolean' else 'text'
            if (type(value) is not dict or set(value)!={'kind',payload} or value['kind']!=family
                    or type(value[payload]) is not (bool if family=='boolean' else str)):
                raise ValueError('Exact original typed ontology scalar required')
            fields[field]=value[payload]
        objects.append((identity,type_id,fields))
    cells=project_full_ontology_edge_cells(tuple(objects),edges,types,relationships)
    return assessment,raw_objects,edges,cells


def _prepare_ontology_resource_operation(original_request,subject,*,compiler=None):
    """Prepare the fixed source/fact/evaluation operation, without disclosure.

    No caller-supplied SQL or evaluator; exact request bytes are copied before
    host entry. Other installed populations refuse rather than silently filter.
    Bounded retained inputs/output; no total process-allocation claim.
    """
    if (type(original_request) is not bytes
            or not 1<=len(original_request)<=4000000 or type(subject) is not str
            or not 1<=len(subject.encode())<=4096):
        raise ValueError('Original bounded ontology publication context required')
    request=bytes(original_request);prepared=_pin_owned_evaluator_sources()
    sources=(Path(__file__),ROOT/'scripts/security_ontology_edge_projection.py')
    pins=tuple((p,sha256(p.read_bytes()).digest()) for p in sources)+tuple(prepared.pins)
    def execute(cursor,observed):
        if observed[0][2:]!=('read_committed','read_write'):
            raise ValueError('Original fresh READ COMMITTED read-write ontology publication required')
        _pin_cursor(cursor)
        previous=_text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",1)
        if len(previous)!=1:raise ValueError('Original ontology search path required')
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        from psycopg import sql
        for table in TABLES:
            cursor.execute(sql.SQL('LOCK TABLE ONLY {} IN SHARE MODE NOWAIT').format(sql.Identifier('truss',table)),prepare=False)
        before=_capture(cursor,request)
        staff=[g for g in before[3] if g['fields']==[[['domain','m','staffId'],'staffId',25]]]
        if len(staff)!=1 or [subject] not in staff[0]['rows']:
            raise ValueError('Original captured ontology Staff Subject required')
        payload=json.dumps({'cells':before[3],'subjectKey':[{'string':subject}],'resultMode':'resources'})
        if len(payload.encode())>1048576:raise ValueError('Bounded ontology policy input required')
        evaluated=subprocess.run([os.environ.get('TRUSS_BUN_EXECUTABLE','bun'),str(prepared.tool),'--named-source'],cwd=ROOT,input=payload,capture_output=True,text=True,timeout=10)
        if evaluated.returncode or len(evaluated.stdout.encode())>65536:raise ValueError('Original ontology policy evaluation refused')
        decision=_read_owned_resource_receipt(evaluated.stdout)
        if compiler is not None:
            compiled_receipt=compiler(cursor,request,before,subject,decision)
            if type(compiled_receipt) is not dict:
                import inspect
                if inspect.iscoroutine(compiled_receipt) or inspect.isgenerator(compiled_receipt):compiled_receipt.close()
                raise ValueError('Original synchronous graph compiler correspondence receipt required')
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        if _capture(cursor,request)!=before:raise ValueError('Original ontology source/facts changed before publication')
        if any(sha256(p.read_bytes()).digest()!=digest for p,digest in pins):raise ValueError('Original ontology evaluator sources changed')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(previous[0][0],),prepare=False)
        return json.dumps(decision,separators=(',',':'),ensure_ascii=False).encode()
    return execute


def publish_owned_ontology_resource_read(host,transaction,original_request,subject,publisher):
    """Administrative selected subject; fixed buffered publication operation."""
    if type(host) is not PsycopgHost or not callable(publisher):
        raise ValueError('Original bounded ontology publication context required')
    execute=_prepare_ontology_resource_operation(original_request,subject)
    return host._run_published_operation(transaction,execute,publisher)
