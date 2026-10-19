# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fixed graph-to-original-ontology spike; administrative mapping, not admission.

Native row IDs only locate typed endpoints. Semantic keys come from authored
property mappings and are validated by the original UMF evaluator/codec.
"""
from pathlib import Path
import hashlib,json,subprocess
from truss._psycopg_fact_cut import _run_fenced_fact_operation
from truss._owner_evidence_json import decode_owner_evidence_json
from security_owned_read import _pin_owned_evaluator_sources,_read_owned_resource_receipt
ROOT=Path(__file__).resolve().parent.parent
# Separately authored fixture mappings. These are not accepted catalog bindings.
NODES={100:('Staff','staffId','1'),101:('Project','projectId','2'),102:('Resource','resourceId','3')}
EDGES={100:('Assignment','assignmentId','4',100,101,'assignmentStaff','assignmentProject'),
       102:('Ownership','ownerId','6',102,101,'ownerResource','ownerProject')}


def _text_rows(cursor,sql,width):
    cursor.execute(sql,prepare=False,binary=False)
    if cursor.description is None or len(cursor.description)!=width or any(d.type_code!=25 for d in cursor.description):
        raise ValueError('Exact graph projection TEXT descriptors required')
    rows=cursor.fetchmany(101)
    if len(rows)>100 or any(len(r)!=width or any(type(v) is not str for v in r) for r in rows):
        raise ValueError('Bounded complete graph projection rows required')
    return rows


def _property(props,address,family):
    value=props.get(address)
    payload='text' if family=='string' else 'value'
    if (type(value) is not dict or set(value)!={'kind',payload} or value['kind']!=family
            or type(value[payload]) is not (str if family=='string' else bool)):
        raise ValueError('Exact mapped native graph scalar required')
    return value[payload] if family=='string' else ('true' if value[payload] else 'false')


def _project_graph_cells(nodes,edges):
    """Total selected-row projection: never silently drop a broken endpoint."""
    groups={name:{'relation':['truss','object' if name in ('Staff','Project','Resource') else 'edge'],
                  'fields':[], 'associations':[], 'rows':[]} for name in ('Staff','Project','Resource','Assignment','Ownership')}
    def fields(name,names):
        groups[name]['fields']=[[['domain','m',field],field,16 if field=='active' else 25] for field in names]
        if name in ('Assignment','Ownership'):groups[name]['associations']=[['domain','m',name]]
    for _,(name,key,_) in NODES.items():fields(name,[key])
    for _,(name,key,_,_,_,source,target) in EDGES.items():fields(name,[key,source,target]+(['active'] if name=='Assignment' else []))
    identities={}
    for row_id,type_id,props_text,root in nodes:
        # SQL emits a non-null marker for root ownership; nested objects are outside this profile.
        if root!='false' or type_id not in {str(v) for v in NODES}:raise ValueError('Selected root graph node required')
        selected=NODES[int(type_id)];name,key,address=selected
        props=decode_owner_evidence_json(props_text.encode())
        if type(props) is not dict:raise ValueError('Native property bag required')
        semantic_key=_property(props,address,'string');identity=(row_id,type_id)
        if identity in identities:raise ValueError('Unique typed native node required')
        identities[identity]=semantic_key;groups[name]['rows'].append([semantic_key])
    for _,rel_id,source_id,source_type,target_id,target_type,props_text in edges:
        if rel_id not in {str(v) for v in EDGES}:raise ValueError('Selected graph association required')
        name,key,address,st,tt,source,target=EDGES[int(rel_id)]
        if (source_type,target_type)!=(str(st),str(tt)):raise ValueError('Original graph endpoint type correspondence required')
        try:source_key=identities[(source_id,source_type)];target_key=identities[(target_id,target_type)]
        except KeyError:raise ValueError('Complete original graph endpoint required') from None
        props=decode_owner_evidence_json(props_text.encode())
        if type(props) is not dict:raise ValueError('Native association property bag required')
        values=[_property(props,address,'string'),source_key,target_key]
        if name=='Assignment':values.append(_property(props,'5','boolean'))
        groups[name]['rows'].append(values)
    return list(groups.values())


def run_owned_graph_resource_read(host,transaction,epoch,relations,subject_key):
    """Historical decision in a joint object/edge cut; no live-subject authority."""
    if (type(subject_key) is not str or type(relations) is not tuple or len(relations)!=2
            or {(r.schema,r.name) for r in relations}!={('truss','object'),('truss','edge')}):
        raise ValueError('Exact fixed graph homes and administrative subject required')
    prepared=_pin_owned_evaluator_sources();self_source=Path(__file__);self_pin=hashlib.sha256(self_source.read_bytes()).digest()
    def execute(cursor):
        nodes=_text_rows(cursor,"SELECT id::pg_catalog.text,type_id::pg_catalog.text,props::pg_catalog.text,(root_id IS NOT NULL)::pg_catalog.text FROM ONLY truss.object WHERE type_id IN (100,101,102) ORDER BY type_id,id",4)
        edges=_text_rows(cursor,"SELECT id::pg_catalog.text,rel_type_id::pg_catalog.text,source_id::pg_catalog.text,source_type::pg_catalog.text,target_id::pg_catalog.text,target_type::pg_catalog.text,props::pg_catalog.text FROM ONLY truss.edge WHERE rel_type_id IN (100,102) ORDER BY rel_type_id,id",7)
        payload=json.dumps({'cells':_project_graph_cells(nodes,edges),'subjectKey':[{'string':subject_key}],'resultMode':'resources'})
        if len(payload.encode())>1048576:raise ValueError('Bounded original graph evaluator input required')
        result=subprocess.run(['/opt/homebrew/bin/bun',str(prepared.tool),'--named-source'],cwd=ROOT,input=payload,capture_output=True,text=True,timeout=4)
        if result.returncode or len(result.stdout.encode())>65536:raise ValueError('Original graph UMF fixture evaluation refused')
        if (hashlib.sha256(self_source.read_bytes()).digest()!=self_pin
                or any(hashlib.sha256(p.read_bytes()).digest()!=pin for p,pin in prepared.pins)):
            raise ValueError('Original graph evaluator sources changed')
        return _read_owned_resource_receipt(result.stdout)
    return _run_fenced_fact_operation(host,transaction,epoch,relations,execute)
