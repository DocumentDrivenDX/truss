# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original private physical completion custody; never report admission/finalization.

The trusted administrative port and physical report bytes remain explicitly
component-scoped. No public capability, settlement or head writer is provided.
"""
from dataclasses import dataclass
import json
import weakref
from ._catalog_report import require_current_catalog_report_basis
from .preparation import _require_original_preparation

@dataclass(frozen=True,slots=True,weakref_slot=True)
class CatalogCompletionPrestate:
    original_bytes: bytes
    scope: str = 'original_catalog_completion_physical_prestate_only'

_issued={}

def _text_row(connection,sql,**parameters):
    rows=connection.run(sql,**parameters)
    if len(rows)!=1 or len(rows[0])!=1 or type(rows[0][0]) is not str:
        raise ValueError('Complete native physical completion response required')
    value=rows[0][0].encode('utf8')
    if len(value)>16777216:raise ValueError('Physical completion retention bound exceeded')
    return value

def capture_catalog_completion_prestate(connection,prepared,basis):
    require_current_catalog_report_basis(basis,connection,prepared)
    payload=json.loads(basis.basis_bytes);cut=payload['nativeCut'];rev=payload['fields']['rev']
    original=_text_row(connection,'SELECT truss.runtime_capture_catalog_completion_prestate(:w,:o,:g,CAST(:rev AS pg_catalog.int4))::pg_catalog.text',
        w=cut['writerXid'],o=cut['operationOrdinal'],g=cut['effectGeneration'],rev=rev)
    require_current_catalog_report_basis(basis,connection,prepared)
    observed=json.loads(original)
    if any(observed[key]!=value for key,value in (
        ('writerXid',cut['writerXid']),('operationOrdinal',cut['operationOrdinal']),
        ('effectGeneration',cut['effectGeneration']),('revision',rev))):
        raise ValueError('Original physical prestate cut required')
    result=CatalogCompletionPrestate(original);key=id(result)
    _issued[key]=(weakref.ref(result,lambda ref:_issued.pop(key,None)),connection,prepared,basis,original)
    return result

def _require_completion_prestate(connection,prepared,prestate,report_bytes):
    original=_issued.get(id(prestate))
    if (type(prestate) is not CatalogCompletionPrestate or original is None
        or original[0]() is not prestate or original[1] is not connection
        or original[2] is not prepared or type(prestate.original_bytes) is not bytes
        or prestate.original_bytes!=original[4]
        or type(prestate.scope) is not str or prestate.scope!='original_catalog_completion_physical_prestate_only'):
        raise ValueError('Original bound physical completion prestate required')
    _require_original_preparation(prepared)
    if type(report_bytes) is not bytes or not 1<=len(report_bytes)<=4194304:
        raise ValueError('Exact bounded physical report bytes required')
    return original

def verify_catalog_completion_physical(connection,prepared,prestate,report_bytes):
    original=_require_completion_prestate(connection,prepared,prestate,report_bytes)
    payload=json.loads(original[4]);generation=str(int(payload['effectGeneration'])+2)
    return _text_row(connection,"SELECT truss.runtime_verify_catalog_completion_physical(:w,:o,:g,CAST(:rev AS pg_catalog.int4),CAST(:prestate AS pg_catalog.jsonb),pg_catalog.decode(:report,'hex'))::pg_catalog.text",
        w=payload['writerXid'],o=payload['operationOrdinal'],g=generation,rev=payload['revision'],
        prestate=original[4].decode('utf8'),report=report_bytes.hex())

def collect_catalog_revision_obligation(connection,prepared,prestate,report_bytes):
    """Collect an actual required revision; missing payload is never zero facts.

    This administrative source extractor issues no feed payload or authority.
    Original Python custody and fresh native physical/source correspondence are
    required independently of whether any feed row was registered.
    """
    original=_require_completion_prestate(connection,prepared,prestate,report_bytes)
    prior=json.loads(original[4]);generation=str(int(prior['effectGeneration'])+2)
    result=_text_row(connection,"SELECT truss.runtime_collect_catalog_revision_obligation(:w,:o,:g,CAST(:prestate AS pg_catalog.jsonb),pg_catalog.decode(:report,'hex'))::pg_catalog.text",
        w=prior['writerXid'],o=prior['operationOrdinal'],g=generation,
        prestate=original[4].decode('utf8'),report=report_bytes.hex())
    observed=json.loads(result)
    expected={'interfaceVersion':'truss-catalog-revision-obligation/0.1',
        'scope':'original_catalog_revision_required_fact_only',
        'writerXid':prior['writerXid'],'operationOrdinal':prior['operationOrdinal'],
        'effectGeneration':generation,'revision':prior['revision'],
        'requiredFactKind':'revision','requiredFactCount':'1',
        'originalInputHex':prepared.input_bytes.hex(),'originalReportHex':report_bytes.hex(),
        'payload':{'state':'unavailable','reason':'complete_report_issuer_missing'},
        'acceptedReportQualified':False,'feedFactQualified':False}
    if any(type(observed.get(key)) is not type(value) or observed[key]!=value
           for key,value in expected.items()):
        raise ValueError('Original required revision obligation correspondence required')
    return result
