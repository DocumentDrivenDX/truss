"""One original compiler context joined to complete native captures; no permit."""
from dataclasses import dataclass
import json
from ._current_query_sources import capture_current_query_sources_with_cursor,_DISCLOSURE_PROFILE
from ._current_disclosure_originals import CurrentDisclosureOriginals
from ._current_disclosure_facts import capture_current_disclosure_facts_with_cursor,CurrentDisclosureFactCapture,_identity
from ._native_graph_correspondence import capture_native_graph_correspondence_with_cursor,NativeGraphCorrespondence
from ._current_query_evaluation import wire,CurrentQueryLimit
from ._owner_evidence_json import decode_owner_evidence_json,same_owner_evidence


def _inputs(sources,sql,parameters,document_ids):
    if sources.source_profile!=_DISCLOSURE_PROFILE or type(sources.query_originals) is not CurrentDisclosureOriginals:
        raise ValueError('Distinct registered original disclosure source profile required')
    request=decode_owner_evidence_json(sources.accepted_request_bytes)
    if set(document_ids)!={m['pin']['documentId'] for m in request['modules']} or parameters:
        raise ValueError('Complete original direct-projection model closure required')
    opaque=decode_owner_evidence_json(sources.query_originals.opaque_sources_bytes)
    original={r['role']:decode_owner_evidence_json(r['utf8'].encode()) for r in opaque}
    modules=[dict(m,selectedModuleIds=[x['id'] for x in decode_owner_evidence_json(m['documentJson'].encode())['modules']]) for m in request['modules']]
    raw=wire({'interfaceVersion':'weft-application-lineage/0.4-candidate','modules':modules,'sql':sql,'parameters':{},'opaqueSources':opaque})
    if len(raw)>4_000_000:raise CurrentQueryLimit('Bounded original presence request required')
    return raw,modules,opaque,original


def _ref(identity):return {'documentId':identity['documentId'],'moduleId':identity['module'],'elementId':identity['element']}
def _id(ref):return tuple(ref[k] for k in ('documentId','moduleId','elementId'))
def _graph_id(ref):return tuple(ref[k] for k in ('documentId','moduleId','relationshipId'))


def _coverage_membership(rows):
    result={}
    for row in rows:
        if (type(row) is not dict or set(row)!={'type','complete','fields'}
                or row['complete'] is not True or type(row['fields']) is not list):
            raise ValueError('Complete issued Record/member coverage correspondence required')
        record=_identity(row['type']);fields=tuple(_identity(f) for f in row['fields'])
        if record in result or len(set(fields))!=len(fields):
            raise ValueError('Distinct complete Record/member coverage required')
        result[record]=frozenset(fields)
    return result


def _join_population(definitions,captured):
    """Compare definition IDs to every native/logical occurrence; no policy logic."""
    model=decode_owner_evidence_json(definitions.model.report)
    graph=decode_owner_evidence_json(definitions.report)
    records={str(r['typeId']):r for r in model['records']}
    facts=decode_owner_evidence_json(captured.facts_bytes)
    coverage=decode_owner_evidence_json(captured.coverage_bytes)
    expected=[{'type':_ref(r['record']),'complete':True,'fields':[_ref(f['field']) for f in r['fields']]} for r in records.values()]
    if _coverage_membership(coverage)!=_coverage_membership(expected):
        raise ValueError('Complete issued Record/member coverage correspondence required')
    if len(facts)!=len(captured.rows):raise ValueError('Complete native/logical object occurrence correspondence required')
    objects={}
    for row,fact in zip(captured.rows,facts,strict=True):
        object_id,type_id=row[:2]
        if type_id not in records or fact['type']!=_ref(records[type_id]['record']) or (object_id,type_id) in objects:
            raise ValueError('Original typed native object occurrence required')
        objects[(object_id,type_id)]=fact
    selected={str(a['relationshipTypeId']):a for a in graph['associations'] if a['kind']=='core-relationship'}
    graphs=decode_owner_evidence_json(captured.graphs_bytes);covered=decode_owner_evidence_json(captured.graph_coverage_bytes)
    expected=[{'relationship':a['reference'],'complete':True,'roles':[e['role'] for e in a['endpoints']],'fields':[]} for a in selected.values()]
    if (len(covered)!=len(expected) or {_graph_id(c['relationship']) for c in covered}!={_graph_id(c['relationship']) for c in expected}
            or any(not same_owner_evidence(c,next(e for e in expected if e['relationship']==c['relationship'])) for c in covered)):
        raise ValueError('Complete issued graph coverage correspondence required')
    if len(graphs)!=len(captured.graph_rows):raise ValueError('Complete native/logical graph occurrence correspondence required')
    seen=set()
    for row,logical in zip(captured.graph_rows,graphs,strict=True):
        edge_id,relationship_id,version,source_id,source_type,target_id,target_type=row
        if relationship_id not in selected or edge_id in seen:raise ValueError('Distinct original native graph occurrence required')
        seen.add(edge_id);association=selected[relationship_id];endpoints=[]
        for endpoint,object_id,type_id in zip(association['endpoints'],(source_id,target_id),(source_type,target_type),strict=True):
            fact=objects.get((object_id,type_id))
            if type_id!=str(endpoint['targetTypeId']) or fact is None:raise ValueError('Issued typed endpoint population correspondence required')
            endpoints.append({'role':endpoint['role'],'key':fact['key']})
        expected={'relationship':association['reference'],'witness':{'kind':'opaque-existential','id':edge_id},'endpoints':endpoints}
        if not same_owner_evidence(logical,expected):raise ValueError('Original graph occurrence projection correspondence required')


@dataclass(frozen=True,slots=True)
class ContextDisclosureCapture:
    facts:CurrentDisclosureFactCapture
    definitions:NativeGraphCorrespondence
    @property
    def sources(self):return self.facts.sources
    @property
    def facts_bytes(self):return self.facts.facts_bytes
    @property
    def coverage_bytes(self):return self.facts.coverage_bytes
    @property
    def graphs_bytes(self):return self.facts.graphs_bytes
    @property
    def graph_coverage_bytes(self):return self.facts.graph_coverage_bytes


def capture_context_disclosure_with_cursor(cursor,*,sql,parameters,document_ids,bun_executable='bun'):
    sources=capture_current_query_sources_with_cursor(cursor)
    raw,_,_,_=_inputs(sources,sql,parameters,document_ids)
    import weft.weft as native
    cursor._deadline.check();parent=native.prepare_application_lineage(raw.decode());current=parent.prepare_current_presence()
    definitions=capture_native_graph_correspondence_with_cursor(cursor,current=current,accepted_request=sources.accepted_request_bytes)
    captured=capture_current_disclosure_facts_with_cursor(cursor,bun_executable=bun_executable)
    if captured.sources!=sources or definitions.model.parent is not parent:raise ValueError('Original registered source and compiler parent must remain held')
    _join_population(definitions,captured);cursor._deadline.check()
    return ContextDisclosureCapture(captured,definitions)


def verify_context_disclosure_with_cursor(cursor,captured,*,bun_executable='bun'):
    if type(captured) is not ContextDisclosureCapture:raise ValueError('Original context disclosure capture required')
    cursor._deadline.check();current=captured.definitions.model.current
    definitions=capture_native_graph_correspondence_with_cursor(cursor,current=current,accepted_request=captured.sources.accepted_request_bytes)
    facts=capture_current_disclosure_facts_with_cursor(cursor,bun_executable=bun_executable)
    if (definitions.model.parent is not captured.definitions.model.parent or definitions.model.current is not current
            or definitions.model.report!=captured.definitions.model.report or definitions.requirements!=captured.definitions.requirements
            or definitions.report!=captured.definitions.report or facts!=captured.facts):
        raise ValueError('Original complete context disclosure capture changed before closing')
    _join_population(definitions,facts);cursor._deadline.check()
