"""Original private report preparation/readback, never accepted report authority.

Final accepted construction and persistence belong inside the future protected
native statement. This basis cannot encode or publish an accepted report.
"""
from dataclasses import dataclass
import json
import weakref
from .preparation import _require_original_preparation

MISSING_FIELDS=('interfaceVersion','reportProfile','originalExecution','umf','assertions','pending_indexes','extensions')
@dataclass(frozen=True,slots=True,weakref_slot=True)
class CatalogReportBasis:
    basis_bytes: bytes
    scope: str = 'original_fresh_graph_catalog_report_basis_only'
    missing_fields: tuple[str,...] = MISSING_FIELDS

_original_bases={}
_original_starts={}
class _ReportStart:
    __slots__=('__weakref__',)

def begin_catalog_report(connection,prepared):
    _require_original_preparation(prepared)
    cut=_cut(connection)
    if cut[2]!='0':raise ValueError('Original pre-effect report cut required')
    result=_ReportStart();key=id(result)
    _original_starts[key]=(weakref.ref(result,lambda ref:_original_starts.pop(key,None)),connection,prepared,cut)
    return result

def _rows(connection,sql,**parameters):
    values=connection.run(sql,**parameters)
    names=[c['name'] for c in connection.columns]
    if len(names)!=len(set(names)):raise ValueError('Unique original report columns required')
    return [dict(zip(names,row,strict=True)) for row in values]

def _cut(connection):
    values=connection.run('SELECT * FROM truss.runtime_collect_empty_catalog_graph()')
    if len(values)!=1 or [c['name'] for c in connection.columns]!=['writer_xid','operation_ordinal','effect_generation','empty_scope']:
        raise ValueError('Original empty graph cut required')
    row=tuple(values[0])
    if any(type(v) is not str for v in row) or any(not v.isascii() or not v.isdecimal() or str(int(v))!=v for v in row[:3]):
        raise ValueError('Exact native report cut required')
    return row

def _report_counts(native):
    names={'typesAdded':'types_added','propertiesAdded':'properties_added',
           'keysAdded':'keys_added','relationshipsAdded':'relationships_added',
           'endpointsAdded':'endpoints_added','elementsRetired':'elements_retired'}
    result={}
    for report,source in names.items():
        value=native[source]
        if type(value) is not str or not value.isascii() or not value.isdecimal() or str(int(value))!=value or int(value)>16384:
            raise ValueError('Bounded canonical report counts required')
        result[report]=value
    return result

def _physical_snapshot(connection):
    # Preserve native canonical text as bytes; Python never parses native numbers.
    tables=('schema_head','schema_rev','schema_doc','type_def','prop_def','key_def',
            'key_lifecycle_history','rel_def','rel_endpoint','relationship_lineage',
            'catalog_acceptance_report','row_home_operation')
    arguments=[]
    for name in tables:
        arguments.append("'"+name+"',(SELECT pg_catalog.coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY pg_catalog.to_jsonb(r)::pg_catalog.text COLLATE pg_catalog.\"C\"),'[]'::pg_catalog.jsonb) FROM truss."+name+' r)')
    # COALESCE is SQL syntax, not a namespaced routine.
    sql=('SELECT pg_catalog.jsonb_build_object('+','.join(arguments)+')::pg_catalog.text').replace('pg_catalog.coalesce','COALESCE')
    rows=connection.run(sql)
    if len(rows)!=1 or len(rows[0])!=1 or type(rows[0][0]) is not str:
        raise ValueError('Original complete native report snapshot required')
    result=rows[0][0].encode('utf8')
    if len(result)>16777216:raise ValueError('Native report snapshot capacity exceeded')
    return result

def compose_catalog_report_basis(connection,prepared,catalog,start):
    original=_original_starts.get(id(start))
    if original is None or original[0]() is not start or original[1] is not connection or original[2] is not prepared:
        raise ValueError('Original one-use pre-effect report custody required')
    del _original_starts[id(start)]
    prior_cut=original[3]
    _require_original_preparation(prepared)
    cut=_cut(connection)
    if cut[:2]!=prior_cut[:2] or cut[3]!=prior_cut[3]:
        raise ValueError('Mixed original report operation or scope')
    evidence=json.loads(prepared.report_evidence_bytes)
    if evidence['scope']!='original_owner_report_preparation_only' or evidence['ingress']['state']!='available':
        raise ValueError('Original owner report evidence required')
    choices=prepared.input()
    inventory=_rows(connection,'SELECT family,identity::pg_catalog.text AS identity FROM truss.runtime_collect_new_catalog_inventory(CAST(:rev AS pg_catalog.int4))',rev=catalog.revision)
    if inventory!=json.loads(catalog.inventory_bytes):raise ValueError('Complete original native effect inventory required')
    counts=_rows(connection,'SELECT * FROM truss.runtime_collect_new_catalog_counts(CAST(:rev AS pg_catalog.int4))',rev=catalog.revision)
    if counts!=[json.loads(catalog.counts_bytes)]:raise ValueError('Original independent report counts required')
    homes=_rows(connection,'SELECT prop_id::pg_catalog.text AS property_id,type_id::pg_catalog.text AS owner_type_id,home FROM truss.prop_def WHERE since_rev=CAST(:rev AS pg_catalog.int4)',rev=catalog.revision)
    expected_homes={(json.loads(r['identity'])[0],json.loads(r['identity'])[1],'json') for r in inventory if r['family']=='property'}
    actual_homes=[(r['property_id'],r['owner_type_id'],r['home']) for r in homes]
    if len(actual_homes)!=len(expected_homes) or set(actual_homes)!=expected_homes:raise ValueError('Original complete report home correspondence required')
    documents=_rows(connection,'SELECT * FROM truss.runtime_collect_report_documents(CAST(:rev AS pg_catalog.int4))',rev=catalog.revision)
    if documents!=json.loads(catalog.documents_bytes):raise ValueError('Original current report document inventory required')
    expected=[{'doc_id':d['documentId'],'doc_revision':d['documentRevision'],'content_sha256':d['artifact']['sha256'],'ord':str(i)} for i,d in enumerate(choices['documents'])]
    if documents!=expected:raise ValueError('Complete native original document bijection required')
    provisional=connection.run('SELECT truss.runtime_require_empty_provisional_catalog(CAST(:rev AS pg_catalog.int4))',rev=catalog.revision)
    if provisional!=[['0']]:raise ValueError('Original complete empty provisional inventory required')
    physical=_physical_snapshot(connection)
    final_cut=_cut(connection)
    if final_cut!=cut:raise ValueError('Stale original report cut')
    fields={'rev':catalog.revision,'acceptedInput':choices,'documents':documents,
            'counts':_report_counts(json.loads(catalog.counts_bytes)),'provisional':[], 'rebinds':[],
            'diagnostics':evidence['validation']['diagnostics'],
            'documentInterpretations':evidence['validation']['documentInterpretations'],
            'extensions':evidence['retainedExtensions']['extensions'],
            'losses':evidence['ingress']['basis']['losses'],
            'transformRegistrations':evidence['ingress']['basis']['transformRegistrations']}
    payload={'fields':fields,'nativeCut':{'writerXid':cut[0],'operationOrdinal':cut[1],'effectGeneration':cut[2]},
             'noRebindEvidence':{'profile':'administrative-empty-graph-and-empty-journal-root/0.1','emptyScope':json.loads(cut[3]),'preEffectGeneration':prior_cut[2]},
             'ownerEvidenceHex':prepared.report_evidence_bytes.hex(),'missingFields':list(MISSING_FIELDS),
             'physicalSnapshotHex':physical.hex(),'nativeCounts':json.loads(catalog.counts_bytes),
             'fieldQualification':{'extensions':'partial_retention_only'},
             'acceptedReportQualified':False}
    result=CatalogReportBasis(json.dumps(payload,ensure_ascii=True,separators=(',',':')).encode())
    key=id(result)
    _original_bases[key]=(weakref.ref(result,lambda ref:_original_bases.pop(key,None)),connection,prepared,result.basis_bytes,cut)
    return result

def require_current_catalog_report_basis(basis,connection,prepared):
    """Original identity/cut check; no report publication or acceptance grant."""
    original=_original_bases.get(id(basis))
    if (type(basis) is not CatalogReportBasis or type(basis.basis_bytes) is not bytes
            or type(basis.scope) is not str or type(basis.missing_fields) is not tuple
            or any(type(v) is not str for v in basis.missing_fields)
            or original is None or original[0]() is not basis
            or original[1] is not connection or original[2] is not prepared
            or basis.basis_bytes!=original[3] or basis.scope!='original_fresh_graph_catalog_report_basis_only'
            or basis.missing_fields!=MISSING_FIELDS):
        raise ValueError('Original bound report basis required')
    _require_original_preparation(prepared)
    if _cut(connection)!=original[4]:raise ValueError('Stale original report basis')
    payload=json.loads(basis.basis_bytes)
    revision=payload['fields']['rev']
    # Re-run original source/native comparison: native generation can be reused
    # after host rollback/reapplication, so equality of counters is insufficient.
    if _physical_snapshot(connection).hex()!=payload['physicalSnapshotHex']:
        raise ValueError('Different native effects reused an original report cut')
    inventory=_rows(connection,'SELECT family,identity::pg_catalog.text AS identity FROM truss.runtime_collect_new_catalog_inventory(CAST(:rev AS pg_catalog.int4))',rev=revision)
    documents=_rows(connection,'SELECT * FROM truss.runtime_collect_report_documents(CAST(:rev AS pg_catalog.int4))',rev=revision)
    counts=_rows(connection,'SELECT * FROM truss.runtime_collect_new_catalog_counts(CAST(:rev AS pg_catalog.int4))',rev=revision)
    if documents!=payload['fields']['documents'] or len(counts)!=1 or _report_counts(counts[0])!=payload['fields']['counts']:
        raise ValueError('Original current report source correspondence required')
    if _cut(connection)!=original[4]:raise ValueError('Stale original report basis')
