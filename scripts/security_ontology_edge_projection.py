"""Explicit full-ontology graph binding to the original logical security fixture.

Logical endpoint fields are declared by the original logical document, not
pretended native properties. Native type/relationship selection is trusted
caller custody; this pure projection issues no source/authority admission.
"""
SPECS={'Client':('clientId',),'Project':('projectId',),'Staff':('staffId',),'Resource':('resourceId','salary'),'Assignment':('assignmentId','active'),'Ownership':('ownershipId',)}
PAIRS={'ProjectClient':('Project','Client'),'StaffAssignment':('Staff','Assignment'),'AssignmentProject':('Assignment','Project'),'OwnershipResource':('Ownership','Resource'),'OwnershipProject':('Ownership','Project')}
FIELDS={'Staff':('staffId',),'Project':('projectId',),'Resource':('resourceId',),'Assignment':('assignmentId','assignmentStaff','assignmentProject','active'),'Ownership':('ownerId','ownerResource','ownerProject')}


def project_full_ontology_edge_cells(objects,edges,types,relationships):
    """Total bounded projection; no row-order, alias, label or hash inference."""
    def refuse():raise ValueError('Original complete typed ontology edge projection required')
    def identifier(value,maximum):
        if type(value) is not str or not value or len(value)>len(str(maximum)) or not value.isascii() or not value.isdecimal() or value[0]=='0' or int(value)>maximum:refuse()
        return value
    if type(types) is not dict or set(types)!=set(SPECS) or type(relationships) is not dict or set(relationships)!=set(PAIRS):refuse()
    types={name:identifier(value,2147483647) for name,value in types.items()}
    relationships={name:identifier(value,2147483647) for name,value in relationships.items()}
    if len(set(types.values()))!=len(types) or len(set(relationships.values()))!=len(relationships):refuse()
    if type(objects) is not tuple or type(edges) is not tuple or len(objects)>100 or len(edges)>100:refuse()
    names={value:name for name,value in types.items()};links={value:name for name,value in relationships.items()};nodes={};ids=set();keys={name:set() for name in SPECS}
    for row in objects:
        if type(row) is not tuple or len(row)!=3:refuse()
        oid,type_id,fields=row;identifier(oid,9223372036854775807);identifier(type_id,2147483647)
        if type_id not in names or oid in ids or type(fields) is not dict:refuse()
        name=names[type_id]
        if len(fields)!=len(SPECS[name]) or any(type(k) is not str or len(k)>64 for k in fields):refuse()
        fields=dict(fields)
        if set(fields)!=set(SPECS[name]):refuse()
        key=fields[SPECS[name][0]]
        if type(key) is not str or not key or len(key.encode())>4096 or key in keys[name]:refuse()
        if name=='Assignment' and type(fields['active']) is not bool:refuse()
        ids.add(oid);keys[name].add(key);nodes[(oid,type_id)]=(name,fields)
    incidence={name:[] for name in PAIRS};seen=set()
    for row in edges:
        if type(row) is not tuple or len(row)!=6:refuse()
        eid,relation,source,source_type,target,target_type=row
        identifier(eid,9223372036854775807);identifier(relation,2147483647)
        for value in (source,target):identifier(value,9223372036854775807)
        for value in (source_type,target_type):identifier(value,2147483647)
        if eid in seen or relation not in links:refuse()
        seen.add(eid);name=links[relation];left=nodes.get((source,source_type));right=nodes.get((target,target_type))
        if left is None or right is None or (left[0],right[0])!=PAIRS[name]:refuse()
        incidence[name].append(((source,source_type),(target,target_type)))
    def endpoint(name,identity,reverse=False):
        matches=[source if reverse else target for source,target in incidence[name] if (target if reverse else source)==identity]
        if len(matches)!=1:refuse()
        _,fields=nodes[matches[0]];return fields[SPECS[nodes[matches[0]][0]][0]]
    groups={name:{'relation':['truss','object+typed-edge-path'],'fields':[[['domain','m',field],field,16 if field=='active' else 25] for field in fields],'associations':[['domain','m',name]] if name in ('Assignment','Ownership') else [],'rows':[]} for name,fields in FIELDS.items()}
    for identity,(name,fields) in nodes.items():
        if name=='Client':continue # Retained native source; this policy has no Client dependency.
        if name=='Project':endpoint('ProjectClient',identity)
        if name in ('Staff','Project','Resource'):values=[fields[SPECS[name][0]]]
        elif name=='Assignment':values=[fields['assignmentId'],endpoint('StaffAssignment',identity,True),endpoint('AssignmentProject',identity),'true' if fields['active'] else 'false']
        else:values=[fields['ownershipId'],endpoint('OwnershipResource',identity),endpoint('OwnershipProject',identity)]
        groups[name]['rows'].append(values)
    return list(groups.values())


def project_public_relationship_edge_cells(objects,edges,types,relationships):
    """Separate six-relationship fixture projection; no query permission issued.

    Public relationship occurrences are retained independently of private policy
    facts. Native source identity, codecs and held cuts remain caller premises.
    """
    def refuse():raise ValueError('Original complete public relationship projection required')
    if type(relationships) is not dict or set(relationships)!=set(PAIRS)|{'ResourceRelatedResource'}:refuse()
    if type(edges) is not tuple or len(edges)>100 or type(objects) is not tuple or len(objects)>100:refuse()
    query_id=relationships['ResourceRelatedResource']
    if type(query_id) is not str or not query_id.isascii() or not query_id.isdigit() or query_id[0:1]=='0' or not 1<=int(query_id)<=2147483647:refuse()
    if query_id in [relationships[n] for n in PAIRS]:refuse()
    policy=[];query=[];seen=set()
    for row in edges:
        if type(row) is not tuple or len(row)!=6 or any(type(v) is not str for v in row) or row[0] in seen:refuse()
        seen.add(row[0])
        if row[1]==query_id:query.append(row)
        else:policy.append(row)
    # Original whole policy projection validates every native object/key and
    # required private endpoint; query edges cannot hide those obligations.
    facts=project_full_ontology_edge_cells(objects,tuple(policy),types,{n:relationships[n] for n in PAIRS})
    resource_type=types['Resource'];nodes={(row[0],row[1]) for row in objects}
    for edge in query:
        for value,maximum in ((edge[0],9223372036854775807),(edge[2],9223372036854775807),(edge[4],9223372036854775807),(edge[3],2147483647),(edge[5],2147483647)):
            if type(value) is not str or not value.isascii() or not value.isdigit() or value[0:1]=='0' or not 1<=int(value)<=maximum:refuse()
        if edge[3]!=resource_type or edge[5]!=resource_type or (edge[2],edge[3]) not in nodes or (edge[4],edge[5]) not in nodes:refuse()
    return {'policyFacts':facts,'queryRelationshipOccurrences':tuple(query),'queryResourceIdentities':tuple((row[0],row[1],row[2]['resourceId']) for row in objects if row[1]==resource_type)}
