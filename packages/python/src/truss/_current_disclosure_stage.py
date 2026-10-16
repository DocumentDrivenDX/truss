"""Conditional tagged staging only; caller/source/UMF/closing guards are external.

No data returned here is public or a native permit. The held original UMF child
must inspect reconstructed_batch before any consumer can release a result.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from uuid import uuid4
from psycopg import sql,RawCursor
from psycopg.rows import tuple_row
from ._owner_evidence_json import decode_owner_evidence_json,same_owner_evidence
from ._current_disclosure_wire import object_members,array_members
from ._current_query_evaluation import CurrentQueryLimit,wire,identity
from ._security_catalog_subject_installation import _text_rows


@dataclass(frozen=True,slots=True)
class _StagedDisclosure:
    names:tuple[str,...]
    field_indexes:tuple[int,...]
    reconstructed_batch:bytes
    transport_report:bytes


def _population(facts,selection,result,batch):
    population=[{'type':f['type'],'key':f['key']} for f in facts if same_owner_evidence(f['type'],selection['type'])]
    expected={identity(r):r for r in population}
    if len(expected)!=len(population):raise ValueError('Distinct complete original resource census required')
    decisions=result['decisions'];seen=set();permitted=[]
    for row in decisions:
        key=identity(row['resource'])
        if key not in expected or key in seen or row['decision'] not in ('permit','deny'):
            raise ValueError('Complete determinate original resource census required')
        seen.add(key)
        if row['decision']=='permit':permitted.append(row['resource'])
    if (seen!=set(expected) or not same_owner_evidence(permitted,result['resources'])
            or len(batch['rows'])!=len(permitted)):
        raise ValueError('Complete original eligible resource correspondence required')
    return permitted


def _reconstruct_batch(batch_raw,returned,descriptors,resource_count,field_count):
    """Restore producer order from checked private keys, never SQL row order."""
    restored={};expected_keys={str(n) for n in range(resource_count)}
    for row in returned:
        carrier=decode_owner_evidence_json(row[-1].encode())
        if (type(carrier) is not dict or set(carrier)!={'version','rows'}
                or carrier['version']!='weft.stage-row-tuple/0.1-candidate'
                or type(carrier['rows']) is not list or len(carrier['rows'])!=1):
            raise ValueError('Exact checked source tuple required')
        source=carrier['rows'][0]
        if type(source) is not dict or set(source)!={'scan','key'} or type(source['key']) is not str:
            raise ValueError('Exact checked source row required')
        key=source['key'];unique=[None]*field_count
        if key in restored or key not in expected_keys:
            raise ValueError('Distinct complete source rows required')
        if len(row)!=len(descriptors)+1:raise ValueError('Exact checked output width required')
        for position,descriptor in enumerate(descriptors):
            index=descriptor['headerColumn']
            if type(index) is not int or not 0<=index<field_count or type(row[position]) is not str:
                raise ValueError('Exact checked header position required')
            if unique[index] is not None and unique[index]!=row[position]:
                raise ValueError('Repeated projections must retain exact cells')
            unique[index]=row[position]
        if any(c is None for c in unique):raise ValueError('Complete public Field reconstruction required')
        restored[key]=b'['+b','.join(c.encode() for c in unique)+b']'
    if len(restored)!=resource_count:raise ValueError('Complete native result reconstruction required')
    original=object_members(batch_raw)
    return b'{'+b','.join(json.dumps(k).encode()+b':'+(b'['+b','.join(restored[str(n)] for n in range(resource_count))+b']' if k=='rows' else v) for k,v in original.items())+b'}'


def stage_current_disclosure(cursor,*,native,current,preparation_json,producer_result_bytes,
        facts,selection,maximum_rows,maximum_scan_rows,maximum_bytes):
    cursor._deadline.check()
    preparation=decode_owner_evidence_json(preparation_json)
    result=decode_owner_evidence_json(producer_result_bytes)
    if (result.get('version')!='umf.security.logical-disclosure-batch/0.1-candidate'
            or result.get('status')!='rendered' or result.get('authority') is not False
            or result.get('complete') is not False):
        raise ValueError('Actual original rendered disclosure required')
    batch_raw=object_members(producer_result_bytes)['batch'];batch=decode_owner_evidence_json(batch_raw)
    resources=_population(facts,selection,result,batch)
    if len(resources)>min(maximum_scan_rows,maximum_rows,4096):raise CurrentQueryLimit('Complete disclosure population exceeds limit')
    header={k:v for k,v in batch.items() if k!='rows'}
    refs=[column['field'] for column in batch['columns']]
    if not same_owner_evidence(refs,selection['fields']):raise ValueError('Exact original selected disclosure fields required')
    requirements=preparation['readRequirements'];scans=requirements['scans']
    if len(scans)!=1 or not same_owner_evidence(scans[0]['target'],selection['type']):
        raise ValueError('Exact original single scan required')
    scan=scans[0]['scan'];fields=[]
    for field in refs:
        uses=[r for r in requirements['fields'] if same_owner_evidence(r['field'],field)]
        if not uses or any(r['role']!='projection' or not same_owner_evidence(r['fieldIdentity'],uses[0]['fieldIdentity']) for r in uses):
            raise ValueError('Exact original projection Field identity required')
        fields.append(uses[0]['fieldIdentity'])
    row_raws=array_members(object_members(batch_raw)['rows']);cells=[array_members(row) for row in row_raws]
    if any(len(row)!=len(fields) for row in cells):raise ValueError('Complete rectangular original cells required')
    if len(batch_raw)>maximum_bytes:raise CurrentQueryLimit('Bounded original disclosure output required')
    table='truss_presence_'+uuid4().hex
    columns=[f'cell_{n}' for n in range(len(fields))]
    statement=sql.SQL('CREATE TEMP TABLE {}(eligible boolean NOT NULL,private_key text PRIMARY KEY,{}) ON COMMIT DROP').format(
        sql.Identifier(table),sql.SQL(',').join(sql.SQL('{} text NOT NULL').format(sql.Identifier(c)) for c in columns))
    created=False
    try:
        cursor.execute(statement,prepare=False);created=True
        names=_text_rows(cursor,'SELECT pg_catalog.pg_my_temp_schema()::pg_catalog.regnamespace::pg_catalog.text',limit=1)
        if len(names)!=1:raise ValueError('Actual owned temporary namespace required')
        schema=names[0][0]
        insertion=sql.SQL('INSERT INTO {}.{} VALUES({})').format(sql.Identifier(schema),sql.Identifier(table),sql.SQL(',').join(sql.Placeholder() for _ in range(len(columns)+2)))
        for index,row in enumerate(cells):
            cursor._deadline.check();cursor.execute(insertion,(True,str(index),*(c.decode('utf8') for c in row)),prepare=False)
        binding={'version':'weft.postgresql.current-presence/0.1-candidate','capabilities':['tagged-current-projection'],
            'sourceRequestSha256':preparation['sourceRequestSha256'],'preparationSha256':sha256(preparation_json).hexdigest(),
            'sourceBindingSha256':preparation['binding']['sha256'],'relation':{'schema':schema,'table':table,'eligibleColumn':'eligible','rowKeyColumn':'private_key'},
            'header':header,'cells':[{'field':field,'column':column} for field,column in zip(fields,columns,strict=True)]}
        binding_raw=wire(binding)
        compiled_raw=native.CurrentPresencePreparation.lower_postgresql_current_presence_candidate_json(current,binding_raw.decode()).encode()
        compiled=decode_owner_evidence_json(compiled_raw)
        if (compiled['version']!='weft.postgresql.current-presence.sql/0.1-candidate' or compiled['authority'] is not False
                or compiled['securityReady'] is not False or compiled['nativeAdmission']!='required' or compiled['parameters']!=[]
                or not same_owner_evidence(compiled['disclosureHeader'],header)):
            raise ValueError('Actual original typed disclosure artifact required')
        # Capture every eligible native row and count independently of returned
        # tuples, before the application statement is executed.
        census=cursor.execute(sql.SQL('SELECT count(*)::text FROM {}.{} WHERE eligible IS TRUE').format(sql.Identifier(schema),sql.Identifier(table)),prepare=False).fetchone()
        if census!=(str(len(cells)),):raise ValueError('Complete independent native eligible count required')
        capture=sql.SQL('SELECT private_key,{} FROM {}.{} WHERE eligible IS TRUE ORDER BY private_key COLLATE pg_catalog."C"').format(sql.SQL(',').join(sql.Identifier(c) for c in columns),sql.Identifier(schema),sql.Identifier(table))
        cursor.execute(capture,prepare=False)
        if cursor.description is None or tuple(d.type_code for d in cursor.description)!=(25,)*(len(columns)+1):
            raise ValueError('Exact captured native TEXT descriptors required')
        captured=cursor.fetchmany(len(cells)+1)
        expected={str(index):tuple(c.decode('utf8') for c in row) for index,row in enumerate(cells)}
        if (len(captured)!=len(expected) or any(type(row) is not tuple or len(row)!=len(columns)+1 or any(type(c) is not str for c in row) for row in captured)
                or len({row[0] for row in captured})!=len(expected) or {row[0]:row[1:] for row in captured}!=expected):
            raise ValueError('Exact original producer/native materialization correspondence required')
        descriptors=compiled['resultColumns'];private=compiled['privateResultColumns']
        if (len(private)!=1 or private[0]['position']!=len(descriptors) or private[0]['name']!='__weft_source_rows'
                or any(d['position']!=n or d['encoding']!='weft.umf-disclosure-cell-text/0.1-candidate' or d['nativeType']!='text' for n,d in enumerate(descriptors))):
            raise ValueError('Exact tagged output order and private lineage required')
        cursor._deadline.check()
        with RawCursor(cursor.connection,row_factory=tuple_row) as raw:
            raw.execute(compiled['sql'],prepare=False,binary=False)
            if (raw.description is None or tuple(d.type_code for d in raw.description)!=(25,)*(len(descriptors)+1)
                    or tuple(d.name for d in raw.description)!=tuple(f'output_{n}' for n in range(len(descriptors)))+('__weft_source_rows',)):
                raise ValueError('Exact actual statement result descriptors required')
            returned=raw.fetchmany(maximum_rows+1)
        cursor._deadline.check()
        if len(returned)>maximum_rows or any(len(r)!=len(descriptors)+1 or any(type(c) is not str for c in r) for r in returned):
            raise CurrentQueryLimit('Complete bounded native disclosure result required')
        frame={'version':'weft.current-presence.transport-input/0.1-candidate','sourceRequestSha256':preparation['sourceRequestSha256'],
            'preparationSha256':sha256(preparation_json).hexdigest(),'materializationBindingSha256':sha256(binding_raw).hexdigest(),
            'compiledArtifactSha256':sha256(compiled_raw).hexdigest(),'expectedRowCount':census[0],'header':header,
            'rows':[{'key':r[0],'cells':list(r[1:])} for r in captured],'resultRows':[list(r) for r in returned]}
        frame_raw=wire(frame)
        if len(frame_raw)>16_000_000:raise CurrentQueryLimit('Bounded complete transport frame required')
        report_raw=native.CurrentPresencePreparation.check_postgresql_current_presence_candidate_json(current,binding_raw.decode(),frame_raw.decode()).encode()
        report=decode_owner_evidence_json(report_raw)
        wanted={k:frame[k] for k in ('sourceRequestSha256','preparationSha256','materializationBindingSha256','compiledArtifactSha256')}
        wanted.update(version='weft.current-presence.transport-result/0.1-candidate',matched=True,authority=False,securityReady=False,nativeAdmission='required',transportInputSha256=sha256(frame_raw).hexdigest(),unresolved=['actual complete authenticated native population/header/owner batch','whole UMF cell/domain/selection/value validation','closing authority checks and guarded release'])
        if not same_owner_evidence(report,wanted):raise ValueError('Actual held transport report correspondence required')
        rebuilt=_reconstruct_batch(batch_raw,returned,descriptors,len(resources),len(fields))
        if len(rebuilt)>maximum_bytes:raise CurrentQueryLimit('Bounded reconstructed disclosure required')
        return _StagedDisclosure(tuple(d['name'] for d in descriptors),tuple(d['headerColumn'] for d in descriptors),rebuilt,report_raw)
    finally:
        if created:
            cursor.execute(sql.SQL('DROP TABLE pg_temp.{}').format(sql.Identifier(table)),prepare=False)
