"""Held registered originals -> actual presence context -> whole UMF inspector.

Called only inside the host's authenticated native guards. No returned data is
public until the host's closing source/caller/current checks finish.
"""
from dataclasses import dataclass
from hashlib import sha256
from time import monotonic
from ._current_disclosure_originals import CurrentDisclosureOriginals
from ._current_disclosure_computation import open_current_disclosure_computation
from ._current_disclosure_session import evaluate_stage_inspect
from ._current_disclosure_stage import stage_current_disclosure
from ._current_disclosure_wire import disclosure_initializer,disclosure_fact_cut,VERSION
from ._current_query_sources import _DISCLOSURE_PROFILE
from ._current_query_evaluation import CurrentQueryLimit,wire
from ._owner_evidence_json import decode_owner_evidence_json,same_owner_evidence


@dataclass(frozen=True,slots=True)
class _HeldDisclosureEvaluation:
    native:object
    parent:object
    current:object
    staged:object

    def require_original_parent(self):
        if self.native.CurrentPresencePreparation.source_preparation(self.current) is not self.parent:
            raise ValueError('Original presence parent must remain held through release guards')


def evaluate_and_stage_current_disclosure(cursor,captured,subject,*,sql,parameters,document_ids,
        bun_executable,maximum_rows,maximum_scan_rows,maximum_bytes):
    from ._current_disclosure_context_capture import ContextDisclosureCapture,_inputs
    sources=captured.sources
    raw,modules,opaque,original=_inputs(sources,sql,parameters,document_ids)
    import weft.weft as native
    cursor._deadline.check()
    if type(captured) is ContextDisclosureCapture:
        current=captured.definitions.model.current;parent=captured.definitions.model.parent
        if (type(current) is not native.CurrentPresencePreparation
                or native.CurrentPresencePreparation.source_preparation(current) is not parent
                or decode_owner_evidence_json(captured.definitions.requirements)['sourceRequestJson']!=raw.decode()):
            raise ValueError('Original captured compiler context required')
    else:
        parent=native.prepare_application_lineage(raw.decode());current=parent.prepare_current_presence()
    preparation_raw=native.CurrentPresencePreparation.json(current).encode();preparation=decode_owner_evidence_json(preparation_raw)
    packet=decode_owner_evidence_json(native.CurrentPresencePreparation.native_request_json(current).encode())
    owner=original['owner'];profile_row=next(r for r in opaque if r['role']=='presence-designation')
    if (packet['authority'] is not False or packet['securityReady'] is not False or packet['nativeAdmission']!='required'
            or packet['sourceRequestJson']!=raw.decode() or packet['sourceRequestSha256']!=sha256(raw).hexdigest()
            or packet['preparationSha256']!=sha256(preparation_raw).hexdigest()
            or packet['sourceProfileJson']!=profile_row['utf8'] or packet['sourceProfileSha256']!=profile_row['sha256']
            or packet['primaryAction']!=owner['disclosure']['readAction']
            or not same_owner_evidence(packet['binding'],original['presence-designation']['binding'])
            or not same_owner_evidence(packet['modelPins'],[m['pin'] for m in modules])):
        raise ValueError('Actual held presence context/source correspondence required')
    requirements=preparation['readRequirements'];scans=requirements['scans']
    if len(scans)!=1:raise ValueError('Original single direct-projection scan required')
    fields=[]
    for field in requirements['fields']:
        if field['role']!='projection' or field['scan']!=scans[0]['scan']:
            raise ValueError('Original direct projection only')
        if field['field'] not in fields:fields.append(field['field'])
    selection={'type':scans[0]['target'],'fields':fields}
    owner_raw=next(r['utf8'].encode() for r in opaque if r['role']=='owner')
    initial,registered_receipt,receipt=disclosure_initializer(sources.initialize_bytes,owner_raw,selection)
    if registered_receipt!=sources.source_receipt:
        raise ValueError('Exact original native registration receipt required')
    generation=cursor.execute('SELECT pg_catalog.pg_current_xact_id()::pg_catalog.text',prepare=False).fetchone()[0]
    registered=decode_owner_evidence_json(sources.initialize_bytes)['sources']
    cut={'version':'umf.security.logical-facts/0.1','trusted':True,'generation':generation,'expectedGeneration':generation,
        'policy':{'id':registered['policy']['id'],'revision':registered['policy']['revision']},'ontology':registered['policy']['ontology'],
        'protection':{'id':registered['catalog']['id'],'revision':registered['catalog']['revision']},'domains':registered['closure']['pins'],
        'owner':{'id':owner['id'],'revision':owner['revision']},'subject':{'type':registered['ontology']['subject'],'key':[{'string':subject.key}]},
        'context':[],'valueProfiles':[],'maxFacts':10000,'maxSteps':1000000}
    cut_raw=disclosure_fact_cut(cut,facts=captured.facts_bytes,coverage=captured.coverage_bytes,
        graphs=captured.graphs_bytes,graph_coverage=captured.graph_coverage_bytes)
    evaluation=wire({'version':VERSION,'kind':'evaluate-disclosure','requestId':'evaluate','sourceReceipt':receipt})[:-1]+b',"cut":'+cut_raw+b'}'
    if len(evaluation)>4194304:raise CurrentQueryLimit('Bounded complete original native facts required')
    cursor._deadline.check()
    facts=decode_owner_evidence_json(captured.facts_bytes)
    def stage(producer_raw):
        return stage_current_disclosure(cursor,native=native,current=current,preparation_json=preparation_raw,
            producer_result_bytes=producer_raw,facts=facts,selection=selection,maximum_rows=maximum_rows,
            maximum_scan_rows=maximum_scan_rows,maximum_bytes=maximum_bytes)
    with open_current_disclosure_computation(bun_executable=bun_executable,timeout_seconds=min(60,cursor._deadline.end-monotonic())) as child:
        candidate=evaluate_stage_inspect(child,cursor._deadline,initial,evaluation,stage)
    cursor._deadline.check()
    if native.CurrentPresencePreparation.source_preparation(current) is not parent:
        raise ValueError('Original native parent custody required through inspection')
    return _HeldDisclosureEvaluation(native,parent,current,candidate)
