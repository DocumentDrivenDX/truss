# SPDX-License-Identifier: MIT OR Apache-2.0
"""Decode the owner-selected property envelope after guarded native execution.

Raw temporal spelling stays exact. This adds no temporal token admission or
calendar oracle; the installed strict075 source guard owns that boundary.
"""
from .contracts import LocalTimestampValue,TextValue
from .query import QueryAbsent,QueryColumnDescriptor,QueryRows,QueryRefused
from ._query_runtime import _decode_scalar,_immutable_metadata
from ._owner_evidence_json import decode_owner_evidence_json


def decode_rows(rows,program,*,maximum_rows,maximum_bytes,catalog_revision):
    outputs=program['outputs'];columns=program['artifact']['columns']
    if not outputs or len(outputs)!=len(columns) or len({o['name'] for o in outputs})!=len(outputs):
        raise ValueError('Complete unique selected temporal column inventory required')
    descriptors=[]
    for index,(output,column) in enumerate(zip(outputs,columns,strict=True),1):
        expected={'name','carrier','nullable','missing','source','representation','modelPins'}
        temporal=output['carrier'] in ('date','instant','local')
        if (set(output)!=expected|({'decoder'} if temporal else set())
                or column['position']!=index or type(column['position']) is not int
                or column['outputName']!=output['name'] or column['sourceIdentities']!=[output['source']]
                or column['representation']!=output['representation']
                or output['modelPins']!=program['artifact']['modelPins']
                or type(output['nullable']) is not bool or type(output['missing']) is not bool
                or column['nullable'] is not (output['nullable'] or output['missing'])):
            raise ValueError('Exact original output/native column correspondence required')
        representation=output['representation']
        if temporal and (output['decoder']!={'profile':'truss-temporal/0.2','kind':output['carrier'],
                'temporalProfile':'umf.weft-binding-temporal/0.2'} or representation!={
                'kind':'value','descriptor':output['source'],'nativeNull':True}):
            raise ValueError('Original selected temporal decoder/representation required')
        frozen=_immutable_metadata(column)
        descriptors.append(QueryColumnDescriptor(position=index,output_name=output['name'],
            representation=frozen['representation'],source_identities=frozen['sourceIdentities'],
            sql_nullable=column['nullable'],logical_type=frozen['representation'].get('logicalType'),
            value_descriptor=_immutable_metadata(output),type_graph=(),original=frozen))
    if len(rows)>maximum_rows:return QueryRefused(code='limits')
    decoded=[];charged=0
    for row in rows:
        if len(row)!=len(outputs):raise ValueError('Complete original native temporal row required')
        values=[]
        for raw,output in zip(row,outputs,strict=True):
            if type(raw) is not str:raise ValueError('Original nonnull native text carrier required')
            charged+=len(raw.encode('utf8'))
            if charged>maximum_bytes:return QueryRefused(code='limits')
            cell=raw
            if output['representation']['kind']=='value':
                cell=decode_owner_evidence_json(raw.encode('utf8'))
                if output['missing'] or output['nullable']:
                    if cell=={'state':'absent'} and output['missing']:
                        values.append(QueryAbsent());continue
                    if cell=={'state':'null'} and output['nullable']:
                        values.append(None);continue
                    if type(cell) is not dict or set(cell)!={'state','value'} or cell['state']!='value':
                        raise ValueError('Exact original presence envelope required')
                    cell=cell['value']
            carrier=output['carrier']
            if carrier in ('date','instant','local'):
                if type(cell) is not str:raise ValueError('Exact guarded temporal source text required')
                value=(LocalTimestampValue(text=cell) if carrier=='local'
                       else TextValue(kind='timestamp' if carrier=='instant' else 'date',text=cell))
            else:
                if output['representation']['kind']=='scalar' and carrier=='boolean':
                    if raw not in ('true','false'):raise ValueError('Exact boolean text required')
                    cell=raw=='true'
                value=_decode_scalar(cell,carrier)
            values.append(value)
        decoded.append(tuple(values))
    return QueryRows(columns=tuple(o['name'] for o in outputs),rows=tuple(decoded),catalog_revision=catalog_revision,
                     column_descriptors=tuple(descriptors))


def typed_rows(entry,program,native):
    """Convert already guarded output using explicit owner kind metadata.

This is a result-carrier conversion, never source or parameter admission. Raw
source tokens remain in QueryRows; the UMF Rust oracle validates the resulting
carrier through its existing temporal_token entrypoint before model release.
"""
    from datetime import date,datetime
    from umf_access.types import MISSING
    from umf_access.values import temporal_token
    outputs=program['outputs'];columns=program['artifact']['columns']
    if program['version']=='weft.engine-page/0.4':
        from ._temporal_query_execution import _page_metadata
        positions=_page_metadata(program)['visibleOutputPositions']
        # Full descriptors still include every hidden ordering/Key column.
        # Only the explicitly selected visible outputs reach the public model.
        outputs=[outputs[p-1] for p in positions]
    if (native.columns!=tuple(entry.result.model_fields)
            or native.columns!=tuple(o['name'] for o in outputs)
            or tuple(d.original for d in native.column_descriptors)!=tuple(_immutable_metadata(c) for c in columns)):
        raise ValueError('Whole original typed output and native metadata required')
    result=[]
    for row in native.rows:
        if len(row)!=len(outputs):raise ValueError('Whole original typed row required')
        values={}
        for output,value in zip(outputs,row,strict=True):
            kind=output['carrier'];name=output['name']
            if type(value) is QueryAbsent:
                if output['missing'] is not True:raise ValueError('Required temporal output absent')
                values[name]=MISSING;continue
            if value is None:
                if output['nullable'] is not True:raise ValueError('Required temporal output null')
                values[name]=None;continue
            if kind=='local':
                if type(value) is not LocalTimestampValue:raise ValueError('Selected canonical local carrier required')
                converted=datetime.fromisoformat(value.text)
                if temporal_token('local',converted)!=value.text:raise ValueError('Owner local carrier correspondence required')
                value=converted
            elif kind in ('date','instant'):
                if type(value) is not TextValue or value.kind!=('date' if kind=='date' else 'timestamp'):
                    raise ValueError('Original guarded temporal text carrier required')
                converted=date.fromisoformat(value.text) if kind=='date' else datetime.fromisoformat(value.text)
                token=temporal_token(kind,converted)
                if kind=='date' and token!=value.text:raise ValueError('Owner date carrier correspondence required')
                value=converted
            values[name]=value
        result.append(entry.result.model_validate(values,strict=True))
    return result
