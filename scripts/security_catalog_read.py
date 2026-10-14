"""Accepted-catalog Record capture into the shared named UMF policy fixture.

Association Records retain their actual object homes. No edge type is invented.
Administrative subject selection and trusted installed source/issuer remain
premises; this is not protected query admission or current authority issuance.
"""
from pathlib import Path
import hashlib,json,subprocess
from truss._security_mapping import PreparedSecurityMapping,_pin_cursor
from truss._security_catalog_assessment import capture_accepted_catalog
from truss._owner_evidence_json import decode_owner_evidence_json
from security_owned_read import _pin_owned_evaluator_sources,_read_owned_resource_receipt
from security_graph_read import _property,_text_rows
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'docs/helix/04-build/evidence/security-named-source-profile'


def _catalog_record_recipe(assessment,transport,document):
    """Map exact original transport references to unique active native homes."""
    inventory=assessment['inventory'];recipes=[]
    def one(rows):
        if len(rows)!=1:raise ValueError('Unique accepted catalog capture home required')
        return rows[0]
    for record in transport['records']:
        ref=record['type'];identity=(ref['documentId'],ref['moduleId'],ref['elementId'])
        owner=one([r for r in inventory['types'] if (r['document_id'],r['module'],r['element'])==identity and r['retired_rev'] is None])
        if owner['kind']!='record' or owner['provisional'] or type(owner['type_id']) is not int or owner['type_id']<=0:
            raise ValueError('Active accepted Record capture required')
        fields=[]
        # The exact named source owns membership; transport owns required fields.
        definition=one([e for m in document['modules'] if m['id']==ref['moduleId'] for e in m['elements'] if e['id']==ref['elementId']])
        for member in definition['members']:
            field={'documentId':ref['documentId'],'moduleId':member['module'],'elementId':member['element']}
            if field not in transport['fields']:continue
            prop=one([p for p in inventory['properties'] if p['type_id']==owner['type_id'] and p['definition_document_id']==field['documentId'] and p['declaration_module']==field['moduleId'] and p['element']==field['elementId'] and p['retired_rev'] is None])
            if (prop['home']!='json' or prop['cardinality']!='one' or prop['nullability']!='required'
                    or prop['scalar_type'] not in ('string','boolean') or type(prop['prop_id']) is not int or prop['prop_id']<=0):
                raise ValueError('Selected accepted JSON scalar capture required')
            fields.append((field,str(prop['prop_id']),prop['scalar_type']))
        key=one([k for k in inventory['keys'] if k['type_id']==owner['type_id'] and k['key_id']==record['keyId'] and k['retired_rev'] is None])
        key_props=[one([p for f,p,family in fields if f==key_field]) for key_field in record['keyFields']]
        if key['prop_ids']!=[int(p) for p in key_props]:raise ValueError('Exact original accepted key field order required')
        recipes.append((owner['type_id'],ref,tuple(fields),bool(record['endpoints'])))
    if len({r[0] for r in recipes})!=len(recipes):raise ValueError('Distinct accepted Record homes required')
    return tuple(recipes)


def _catalog_record_cells(recipes,rows):
    groups={type_id:{'relation':['truss','object'],'fields':[[[f['documentId'],f['moduleId'],f['elementId']],address,25 if family=='string' else 16] for f,address,family in fields],
                     'associations':[[ref['documentId'],ref['moduleId'],ref['elementId']]] if association else [],'rows':[]}
            for type_id,ref,fields,association in recipes}
    fields_by_type={str(type_id):fields for type_id,ref,fields,association in recipes}
    for _,type_id,props_text,root in rows:
        if type_id not in fields_by_type or root!='false':raise ValueError('Complete selected root Record capture required')
        props=decode_owner_evidence_json(props_text.encode())
        if type(props) is not dict:raise ValueError('Accepted native property bag required')
        groups[int(type_id)]['rows'].append([_property(props,address,family) for f,address,family in fields_by_type[type_id]])
    return list(groups.values())


def run_owned_catalog_resource_read(host,transaction,mapping,subject_key,*,fact_relations=None):
    """Historical accepted-source decision; no authority from a retained mapping."""
    if type(mapping) is not PreparedSecurityMapping:
        raise ValueError('Original accepted-catalog fixture mapping required')
    # Read each carrier once before source I/O or host callbacks.
    original_request,assessment,expected_guard=mapping.original_request,mapping.accepted_catalog_assessment,mapping.native_guard
    if (type(assessment) is not bytes or not 1<=len(assessment)<=16777216
            or type(original_request) is not bytes or not 1<=len(original_request)<=4_000_000
            or type(subject_key) is not str):
        raise ValueError('Original accepted-catalog fixture mapping required')
    expected_request=decode_owner_evidence_json((BASE/'mapping-request.json').read_bytes())
    if decode_owner_evidence_json(original_request)!=expected_request:
        raise ValueError('Exact shared named accepted source required')
    # Retained assessment is compared to current native state inside the cut.
    prepared=_pin_owned_evaluator_sources()
    extra=[Path(__file__),ROOT/'scripts/security_graph_read.py',BASE/'transport.json']
    pins=prepared.pins+tuple((p,hashlib.sha256(p.read_bytes()).digest()) for p in extra)
    transport=decode_owner_evidence_json((BASE/'transport.json').read_bytes())
    document=json.loads(expected_request['modules'][0]['documentJson'])
    if (type(expected_guard) is not tuple or len(expected_guard)!=3
            or any(type(v) is not bytes or not 1<=len(v)<=32768 for v in expected_guard[:2])
            or type(expected_guard[2]) is not int or not 1<=expected_guard[2]<=9223372036854775807):
        raise ValueError('Original prepared native authority comparison required')
    def guard(cursor):
        cursor.execute('SELECT installation_identity_bytes,policy_profile_bytes,generation FROM truss.policy_generation_guard WHERE singleton=1 FOR SHARE NOWAIT',prepare=False)
        if (cursor.description is None or tuple(d.name for d in cursor.description)!=('installation_identity_bytes','policy_profile_bytes','generation') or tuple(d.type_code for d in cursor.description)!=(17,17,20)):
            raise ValueError('Exact native authority guard descriptors required')
        rows=cursor.fetchmany(2)
        if (len(rows)!=1 or len(rows[0])!=3 or tuple(type(v) for v in rows[0])!=(bytes,bytes,int) or rows!=[expected_guard]):
            raise ValueError('Original current native authority comparison required')
    def execute(cursor,observation):
        _pin_cursor(cursor)
        cursor.execute("SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",prepare=False)
        paths=cursor.fetchmany(2)
        if len(paths)!=1 or type(paths[0][0]) is not str:raise ValueError('Original catalog read caller path required')
        original_path=paths[0][0]
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        if cursor.fetchmany(2)!=[('pg_catalog, pg_temp',)]:raise ValueError('Pinned catalog read path required')
        guard(cursor)
        cursor.execute('LOCK TABLE ONLY truss.object IN SHARE MODE NOWAIT',prepare=False)
        if capture_accepted_catalog(cursor,original_request)!=assessment:raise ValueError('Original current accepted catalog correspondence required')
        recipes=_catalog_record_recipe(json.loads(assessment),transport,document)
        # The list is entirely source-assessed native positive integer IDs.
        ids=','.join(str(r[0]) for r in recipes)
        rows=_text_rows(cursor,'SELECT id::pg_catalog.text,type_id::pg_catalog.text,props::pg_catalog.text,(root_id IS NOT NULL)::pg_catalog.text FROM ONLY truss.object WHERE type_id IN ('+ids+') ORDER BY type_id,id',4)
        payload=json.dumps({'cells':_catalog_record_cells(recipes,rows),'subjectKey':[{'string':subject_key}],'resultMode':'resources','authorityGeneration':str(expected_guard[2])})
        if len(payload.encode())>1048576:raise ValueError('Bounded original accepted-catalog evaluator input required')
        result=subprocess.run(['/opt/homebrew/bin/bun',str(prepared.tool),'--named-source'],cwd=ROOT,input=payload,capture_output=True,text=True,timeout=4)
        if result.returncode or len(result.stdout.encode())>65536:raise ValueError('Original accepted-catalog UMF evaluation refused')
        _pin_cursor(cursor)
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        if cursor.fetchmany(2)!=[('pg_catalog, pg_temp',)]:raise ValueError('Pinned late catalog read path required')
        guard(cursor)
        if capture_accepted_catalog(cursor,original_request)!=assessment:raise ValueError('Accepted catalog changed during owned evaluation')
        if any(hashlib.sha256(p.read_bytes()).digest()!=pin for p,pin in pins):raise ValueError('Original accepted-catalog evaluator sources changed')
        receipt=_read_owned_resource_receipt(result.stdout)
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
        if cursor.fetchmany(2)!=[(original_path,)]:raise ValueError('Original catalog read path restoration required')
        return receipt
    if fact_relations is None:return host._run_operation(transaction,execute)
    from truss._psycopg_fact_cut import _FactRelationComparison,_prepare_fenced_fact_cut
    if (type(fact_relations) is not tuple or len(fact_relations)!=1
            or type(fact_relations[0]) is not _FactRelationComparison
            or (fact_relations[0].schema,fact_relations[0].name)!=('truss','object')):
        raise ValueError('Exact accepted object fact cut required')
    acquire=_prepare_fenced_fact_cut(fact_relations,lambda c:execute(c,host._observe(c)))
    def guarded(c,o):
        _pin_cursor(c)
        return acquire(c)
    return host._run_operation(transaction,guarded)
