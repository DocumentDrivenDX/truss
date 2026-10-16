"""Pure original source binding; no native authority or policy interpretation."""
from dataclasses import replace
import hashlib,json
from ._security_mapping import PreparedSecurityMapping
from ._security_relationship_source import PreparedRelationshipSecuritySource,snapshot_relationship_security_source,capture_relationship_source_comparison
from ._security_graph_source import PreparedGraphSecuritySource,snapshot_graph_security_source
from ._security_source_epoch_installation import _MANIFEST_SHA256

def _snapshot_source_binding(mapping,fact_relations,barrier):
    """Private byte/recipe binding packet; not an authenticated issuer artifact."""
    from ._psycopg_fact_cut import _prepare_fenced_fact_cut,_FactRelationComparison,_FactColumnComparison
    if type(mapping) not in (PreparedSecurityMapping,PreparedGraphSecuritySource,PreparedRelationshipSecuritySource):raise ValueError('Exact bounded catalog source binding bytes required')
    mapping=snapshot_relationship_security_source(mapping) if type(mapping) is PreparedRelationshipSecuritySource else snapshot_graph_security_source(mapping) if type(mapping) is PreparedGraphSecuritySource else replace(mapping)
    request,assessment=mapping.original_request,mapping.accepted_catalog_assessment
    if (type(request) is not bytes or not 1<=len(request)<=4000000
            or type(assessment) is not bytes or not 1<=len(assessment)<=1048576):
        raise ValueError('Exact bounded catalog source binding bytes required')
    if (type(fact_relations) is not tuple or not 1<=len(fact_relations)<=32
            or any(type(r) is not _FactRelationComparison or type(r.columns) is not tuple
                   or len(r.columns)>1600 or any(type(c) is not _FactColumnComparison for c in r.columns) for r in fact_relations)):
        raise ValueError('Exact bounded source fact recipe shapes required')
    fact_relations=tuple(replace(r,columns=tuple(replace(c) for c in r.columns)) for r in fact_relations)
    _prepare_fenced_fact_cut(fact_relations,lambda c:None,existing_locks=True)
    from ._psycopg_epoch_cut import _DDLBarrierComparison
    if type(barrier) is not _DDLBarrierComparison:raise ValueError('Exact native source barrier binding required')
    barrier=replace(barrier)
    if (type(barrier) is not _DDLBarrierComparison or type(barrier.owner_oid) is not int
            or not 1<=barrier.owner_oid<=4294967295 or type(barrier.function_oid) is not int
            or not 1<=barrier.function_oid<=4294967295 or type(barrier.source) is not str
            or not 1<=len(barrier.source.encode('utf8'))<=65536 or type(barrier.include_alter_routine) is not bool or type(barrier.include_schema_ddl) is not bool or type(barrier.include_database_ddl) is not bool):
        raise ValueError('Exact native source barrier binding required')
    return mapping,fact_relations,barrier


def derive_catalog_source_epoch_profile(mapping,fact_relations,barrier,*,subject_source):
    mapping,fact_relations,barrier=_snapshot_source_binding(mapping,fact_relations,barrier)
    request,assessment=mapping.original_request,mapping.accepted_catalog_assessment
    if type(subject_source) is not bytes or not 1<=len(subject_source)<=65536:
        raise ValueError('Exact bounded Subject helper bytes required')
    recipes=[]
    for r in sorted(fact_relations,key=lambda r:r.oid):
        columns=[(c.name,c.number,c.type_oid,c.type_modifier,c.not_null,c.collation_oid,c.generated,c.identity) for c in r.columns]
        recipes.append({'schema':r.schema,'name':r.name,'oid':r.oid,'ownerOid':r.owner_oid,'guardSha256':hashlib.sha256(r.guard_source.encode('utf8')).hexdigest(),'columnsSha256':hashlib.sha256(json.dumps(columns,separators=(',',':'),ensure_ascii=False).encode('utf8')).hexdigest(),'columnCount':len(columns)})
    packet={'interfaceVersion':'truss-owned-catalog-source-profile/0.4',
            'sourceEpochManifestSha256':_MANIFEST_SHA256,
            'requestSha256':hashlib.sha256(request).hexdigest(),
            'acceptedCatalogSha256':hashlib.sha256(assessment).hexdigest(),
            'subjectHelperSha256':hashlib.sha256(subject_source).hexdigest(),
            'ddlBarrier':{'ownerOid':barrier.owner_oid,'functionOid':barrier.function_oid,'sourceSha256':hashlib.sha256(barrier.source.encode('utf8')).hexdigest(),'includeAlterRoutine':barrier.include_alter_routine,'includeSchemaDdl':barrier.include_schema_ddl,'includeDatabaseDdl':barrier.include_database_ddl},
            'factCuts':recipes}
    if type(mapping) is PreparedGraphSecuritySource:
        packet['interfaceVersion']='truss-owned-graph-source-profile/0.1-candidate'
        packet['compilerRequestSha256']=hashlib.sha256(mapping.native_dependencies).hexdigest()
        packet['compilerOutputSha256']=hashlib.sha256(mapping.original_response).hexdigest()
        if mapping.guarded_response is not None:
            from ._security_guarded_source import capture_guarded_source_comparison
            packet['sourceContextSha256']=capture_guarded_source_comparison(mapping.native_dependencies,mapping.guarded_response).source_sha256
    if type(mapping) is PreparedRelationshipSecuritySource:
        packet['interfaceVersion']='truss-owned-relationship-source-profile/0.1-candidate'
        packet['compilerRequestSha256']=hashlib.sha256(mapping.native_dependencies).hexdigest()
        packet['compilerOutputSha256']=hashlib.sha256(mapping.original_response).hexdigest()
        packet['sourceContextSha256']=capture_relationship_source_comparison(mapping.native_dependencies,mapping.original_response).source_sha256
    raw=json.dumps(packet,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf8')
    if len(raw)>65536:raise ValueError('Bounded native catalog source profile required')
    return raw

