# SPDX-License-Identifier: MIT OR Apache-2.0
"""Complete six-relationship native capture under caller-supplied held cuts."""
import json
from truss._security_catalog_assessment import capture_accepted_catalog
from truss._owner_evidence_json import decode_owner_evidence_json
from security_graph_read import _text_rows
from security_ontology_edge_projection import SPECS,PAIRS,project_public_relationship_edge_cells

def capture_relationship_facts(cursor,request):
    from security_ontology_read_cut import verify_held_ontology_fact_cut
    verify_held_ontology_fact_cut(cursor)
    assessment=capture_accepted_catalog(cursor,request,existing_source_cut=True)
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
    for name,(left,right) in {**PAIRS,'ResourceRelatedResource':('Resource','Resource')}.items():
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
    cells=project_public_relationship_edge_cells(tuple(objects),edges,types,relationships)
    return assessment,raw_objects,edges,cells

