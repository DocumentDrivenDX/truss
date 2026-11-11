# SPDX-License-Identifier: MIT OR Apache-2.0
"""Explicit ABI1.3 capture. Owner compiler alone interprets temporal tokens.

Capture produces inert original build inputs, never a data-execution permit.
No ordinary binding/cache entry is repinned or used as a temporal fallback.
"""
from collections.abc import Mapping
from decimal import Decimal
from hashlib import sha256
import json

from .execution import Error, Ok
from .query import QueryCatalogSources, QueryRefused
from ._owner_evidence_json import decode_owner_evidence_json
from ._temporal_profiles import abi

BACKEND = {'backendId':'truss.postgresql.runtime', 'backendVersion':'0.4.47',
           'targetProfile':'truss-runtime-pg18.6/0.7-temporal-candidate',
           'interfaceVersion':'weft-backend/0.2.10'}


def _text(value, maximum):
    return type(value) is str and 1<=len(value.encode('utf8'))<=maximum and '\0' not in value


def _parameters(parameters, temporal_parameters):
    if (not isinstance(parameters,Mapping) or not isinstance(temporal_parameters,Mapping)
            or len(parameters)+len(temporal_parameters)>1024
            or set(parameters)&set(temporal_parameters)):
        raise ValueError('Separate bounded parameter maps required')
    ordinary={}; temporal={}
    for name,value in parameters.items():
        if not _text(name,4096):raise ValueError('Bounded parameter name required')
        if type(value) is bool: family,token='boolean','true' if value else 'false'
        elif type(value) is int:
            if value.bit_length()>3483320:raise ValueError('Bounded integer parameter required')
            family,token='integer',str(Decimal(value))
        elif type(value) is Decimal:
            if not value.is_finite():raise ValueError('Finite exact decimal required')
            sign,digits,exponent=value.as_tuple()
            size=(len(digits)+exponent if exponent>=0 else len(digits)+1 if len(digits)+exponent>0 else 2-exponent)+sign
            if size>1048576:raise ValueError('Bounded decimal parameter required')
            family,token='decimal',format(value,'f')
        elif type(value) is str: family,token='string',value
        else:raise ValueError('Exact ordinary parameter required')
        if len(token.encode('utf8'))>1048576 or '\0' in token:raise ValueError('Bounded parameter token required')
        ordinary[name]={'family':family,'value':token}
    for name,value in temporal_parameters.items():
        if (not _text(name,4096) or not isinstance(value,Mapping) or set(value)!={'kind','value'}
                or type(value['kind']) is not str or value['kind'] not in ('date','instant','local')
                or not _text(value['value'],1048576)):
            raise ValueError('Exact selected temporal parameter shape required')
        # Preserve exact tokens. Semantic acceptance belongs to strict075 and
        # Weft, including calendar, width, fraction and offset refusal controls.
        temporal[name]={'kind':value['kind'],'value':value['value']}
    return ordinary,temporal


def capture_sources(host,transaction,*,sql,document_ids,parameters,temporal_parameters,
                    maximum_rows,maximum_scan_rows,maximum_bytes,manifest,digest,pin_cursor):
    try:
        if (not _text(sql,1048576) or type(document_ids) is not tuple or not 1<=len(document_ids)<=32
                or any(not _text(d,4096) for d in document_ids) or len(set(document_ids))!=len(document_ids)):
            raise ValueError('Bounded original query and unique documents required')
        ordinary,temporal=_parameters(parameters,temporal_parameters)
    except (ValueError,TypeError,UnicodeError):
        return Ok(QueryRefused(code='invalid_query'))
    if (any(type(v) is not int for v in (maximum_rows,maximum_scan_rows,maximum_bytes))
            or not 1<=maximum_rows<=10000 or not 1<=maximum_scan_rows<=10000 or not 1<=maximum_bytes<=16777216):
        return Ok(QueryRefused(code='limits'))
    if manifest['releaseId']!='truss-catalog-runtime/0.76-temporal-candidate':
        return Ok(QueryRefused(code='unsupported_query'))
    command='SELECT truss.person_query_temporal_binding(%s::pg_catalog.jsonb,%s,%s,%s,%s,%s)'
    arguments=(json.dumps(document_ids),maximum_scan_rows,maximum_rows,maximum_bytes,manifest['releaseId'],digest)
    def capture(cursor,observed):
        pin_cursor(cursor)
        cursor.execute(command,arguments,prepare=False)
        original=bytes(cursor.fetchone()[0]);bundle=decode_owner_evidence_json(original)
        binding_json=bundle['bindingJson'];binding=decode_owner_evidence_json(binding_json.encode())
        if (binding!=bundle['binding'] or binding['releaseId']!=manifest['releaseId']
                or binding['releaseSha256']!=digest or binding['queryAbi']!=abi()):
            raise ValueError('Actual original native0.76 ABI1.3 binding required')
        for module in bundle['modules']:
            if sha256(module['documentJson'].encode('utf8')).hexdigest()!=module['pin']['sha256']:
                raise ValueError('Exact original native admitted module bytes required')
        request={'interfaceVersion':'weft-compile/0.2.10','dialect':'weft-sql/0.2.0','sql':sql,
                 'temporalProfile':'umf.weft-binding-temporal/0.2','modules':bundle['modules'],
                 'parameters':ordinary,'exactParameters':{},'temporalParameters':temporal,
                 'options':{'allowCandidate':True},
                 'target':{key:BACKEND[key] for key in ('backendId','backendVersion','targetProfile')}}
        request['target'].update(bindingJson=binding_json,bindingSha256=sha256(binding_json.encode('utf8')).hexdigest())
        # A second native observation checks current person/module/capability
        # and exact source tuple before these inert inputs leave the operation.
        # Data execution must still capture/check afresh in its own operation.
        cursor.execute(command,arguments,prepare=False)
        if decode_owner_evidence_json(bytes(cursor.fetchone()[0]))!=bundle:
            return QueryRefused(code='stale_context')
        return QueryCatalogSources(request_json=json.dumps(request,ensure_ascii=False,separators=(',',':')))
    result=host._run_operation(transaction,capture)
    if isinstance(result,Error) and result.error.code=='execution_obligation':
        code={'P1403':'unauthorized','0A000':'unsupported_query','54000':'limits','55P03':'stale_context',
              '42883':'unsupported_query','3F000':'unsupported_query'}.get(result.error.sql_state)
        if code:return Ok(QueryRefused(code=code))
    return result
