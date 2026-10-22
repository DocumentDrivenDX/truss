from .groups import UnauthorizedPerson
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Explicit native chunk execution; original legacy per-record route is unchanged."""
import base64
import json
from contextlib import nullcontext
from hashlib import sha256
from uuid import uuid4
from .batched_import import (BatchedImportInput, BatchedImportRuntimeContext, BuiltImportRecords,
    ObjectImportDraft, EdgeImportDraft, BatchedImportExecutionResult, EmptyLoadDisposition)
from .contracts import (ABSENT, ProfilePin, ObjectKeySelection, ObjectKeyComponent, ReadTypeReference,
    QualifiedOwner, ExactArtifact, SelectedMutationConfiguration)
from .imports import (ImportCatalogPin, ObjectImportRecord, EdgeImportRecord, EdgeImportIdentity,
    ImportReported, ImportExecutionFailed, ImportInvalid, ImportReport, ImportCounts,
    ImportCreated, ImportSkipped, ImportRejected, PendingBatch)
from .execution import Ok, Error, ExecutionFailure
from ._group_runtime import _wire, _bytes, _identity, _artifact
from ._import_runtime import _cell, _DIAGNOSTIC
from .psycopg_host import _HostOperationReservation
from .preparation import CatalogDocument


def _context(value):
    return BatchedImportRuntimeContext(layout_profile=ProfilePin(**value['layoutProfile']),
        import_profile=ProfilePin(**value['importProfile']), value_profile=ProfilePin(**value['valueProfile']),
        payload_profile=ProfilePin(**value['importPayloadProfile']), catalog=ImportCatalogPin(
            revision=value['catalog']['revision'], model_bundle_sha256=value['catalog']['modelBundleSha256']))


def _configuration(value):
    selected=value['selectedConfiguration']
    return SelectedMutationConfiguration(source_epoch=selected['sourceEpoch'],installation_id=selected['installationId'],
        generation=selected['generation'],key_reuse=selected['keyReuse'],journal_mode=selected['journalMode'],
        configuration_profile=ProfilePin(**selected['configurationProfile']),installed_producer_inventory_sha256=selected['installedProducerInventorySha256'])


def context(host, transaction, manifest, digest, pin_cursor):
    def observe(cursor, observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.person_batched_import_context(%s,%s)', (manifest['releaseId'], digest), prepare=False)
        return _context(json.loads(bytes(cursor.fetchone()[0])))
    result=host._run_operation(transaction,observe,function_call=True)
    if isinstance(result,Error) and result.error.code=='execution_obligation' and result.error.sql_state=='P1403':
        return Ok(UnauthorizedPerson())
    return result


def _decimal(value, maximum_digits=20, *, zero=False):
    return (type(value) is str and value.isascii() and value.isdecimal()
        and len(value)<=maximum_digits and (value=='0' and zero or not value.startswith('0')))


def _exact_identity(value):
    if (type(value) is not dict or set(value)!={'id','typeId','definitionPin','owner'}
        or not _decimal(value['id']) or not _decimal(value['typeId'],10)
        or type(value['definitionPin']) is not str or not 1<=len(value['definitionPin'])<=65536
        or type(value['owner']) is not dict or set(value['owner'])!={'documentId','moduleId'}
        or any(type(v) is not str or not 1<=len(v.encode('utf8'))<=4096 for v in value['owner'].values())):
        raise ValueError('Closed exact native identity required')
    return _identity(value)


def _record(value):
    if type(value) is not dict or set(value)!={'kind','identity','payload','payloadProfile'} or value['kind'] not in ('object','edge'):
        raise ValueError('Closed original built import record required')
    artifact=_artifact(base64.b64decode(value['payload']['bytesBase64'],validate=True))
    if value['payload']!=_wire(artifact):raise ValueError('Original built payload byte/hash identity required')
    profile=ProfilePin(**value['payloadProfile']); selected=value['identity']
    if value['kind']=='edge':
        return EdgeImportRecord(identity=EdgeImportIdentity(relationship_definition_pin=selected['relationshipDefinitionPin'],
            source=_identity(selected['source']), target=_identity(selected['target'])), payload=artifact, payload_profile=profile)
    owner=selected['type']['owner']
    identity=ObjectKeySelection(type=ReadTypeReference(type_id=selected['type']['typeId'],
        definition_pin=selected['type']['definitionPin'], owner=QualifiedOwner(document_id=owner['documentId'],module_id=owner['moduleId'])),
        key_number=selected['keyNumber'],key_definition_pin=selected['keyDefinitionPin'],
        key_encoding_profile=ProfilePin(**selected['keyEncodingProfile']), components=tuple(ObjectKeyComponent(
            property_id=c['propertyId'],definition_pin=c['definitionPin'],value=_cell(c['value'])) for c in selected['components']))
    return ObjectImportRecord(identity=identity,payload=artifact,payload_profile=profile)


def build_records(host,transaction,drafts,manifest,digest,pin_cursor):
    if type(drafts) is not tuple or len(drafts)>1024 or any(type(d) not in (ObjectImportDraft,EdgeImportDraft) for d in drafts):
        return Error(ExecutionFailure('execution_obligation','Bounded original import drafts required'))
    original=_bytes(_wire(drafts))
    def observe(cursor,observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.person_build_import_records(%s,%s,%s)',(original,manifest['releaseId'],digest),prepare=False)
        value=json.loads(bytes(cursor.fetchone()[0]))
        if type(value) is not dict or set(value)!={'context','records'} or type(value['records']) is not list or len(value['records'])!=len(drafts):
            raise ValueError('Complete original builder output required')
        selected=_context(value['context'])
        records=tuple(_record(r) for r in value['records'])
        if any(r.kind!=d.kind or r.payload_profile!=selected.payload_profile for r,d in zip(records,drafts)):
            raise ValueError('Original builder order and payload profile required')
        return BuiltImportRecords(context=selected,records=records)
    result=host._run_operation(transaction,observe,function_call=True)
    if isinstance(result,Error) and result.error.code=='execution_obligation' and result.error.sql_state=='P1403':
        return Ok(UnauthorizedPerson())
    return result


def run_batched_import(host,transaction,input,documents,manifest,digest,pin_cursor,*,_engine=None):
    def wrapped(result,empty=None):return BatchedImportExecutionResult(result=result,empty_load_settlement=empty)
    def failed(error,report=None,empty=None):return wrapped(ImportExecutionFailed(error=error,report=report),empty)
    try:
        if type(input) is not BatchedImportInput or type(documents) is not tuple or any(type(d) is not CatalogDocument for d in documents):raise ValueError()
        original=_bytes(_wire(input)); sources=_bytes([{'documentId':d.document_id,'sourceText':d.content.decode('utf8')} for d in documents])
        if len(original)>8388608 or len(sources)>4194304 or len(input.records)>1024 or not input.chunk_size.isdecimal() or not 1<=int(input.chunk_size)<=128:raise ValueError()
        for record in input.records:
            payload=base64.b64decode(record.payload.bytes_base64,validate=True)
            if not 1<=len(payload)<=1048576 or sha256(payload).hexdigest()!=record.payload.sha256:raise ValueError()
    except (ValueError,TypeError,AttributeError,UnicodeError):
        return wrapped(ImportInvalid(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"envelope"}')))
    invocation=str(uuid4()); outcomes=[];batches=[]; native_context=None;empty=None
    ordered=sorted(range(len(input.records)),key=lambda i:(input.records[i].kind=='edge',i))
    total=max(1,(len(ordered)+int(input.chunk_size)-1)//int(input.chunk_size))
    def report(status):
        configuration=_configuration(native_context)
        dispositions={b.batch_id:b.disposition for b in batches};visited={int(o.input_index) for o in outcomes}
        def created(state):return str(sum(type(o) is ImportCreated and dispositions[o.batch_id]==state for o in outcomes))
        return ImportReport(attempt_id=invocation,input_count=str(len(input.records)),executed_catalog_revision=native_context['catalog']['revision'],
            import_profile=input.import_profile,selected_configuration=configuration,input_sha256=sha256(b'truss-batched-import-input/0.1.0\n'+original).hexdigest(),
            execution='host_adopted' if _engine is None else 'engine_owned',status=status,
            outcomes=tuple(sorted(outcomes,key=lambda o:int(o.input_index))),batches=tuple(batches),
            unprocessed_indices=tuple(str(i) for i in range(len(input.records)) if i not in visited),
            counts=ImportCounts(created_committed=created('committed'),created_pending=created('pending'),created_rolled_back=created('rolled_back'),
                created_commit_unknown=created('commit_unknown'),created_transaction_unresolved=created('transaction_unresolved'),attempt_unknown='0',
                skipped=str(sum(type(o) is ImportSkipped for o in outcomes)),rejected=str(sum(type(o) is ImportRejected for o in outcomes)),
                unprocessed=str(len(input.records)-len(visited))))
    def release(cursor,observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.person_validate_batched_import_report(%s,%s,%s,%s,%s)',
            (original,_bytes(_wire(tuple(outcomes))),_bytes(native_context),manifest['releaseId'],digest),prepare=False)
        cursor.fetchone()
        return True
    def interrupted(error):
        nonlocal host,transaction
        if native_context is None:return failed(error,empty=empty)
        if _engine is not None:
            try:host,transaction=_engine.begin()
            except Exception:return failed(error,empty=empty)
        released=host._run_operation(transaction,release)
        if isinstance(released,Error) and error.code!='commit_unknown' and (released.error.code=='transaction_unusable' or released.error.retry_scope=='whole_transaction'):
            error=released.error
        return failed(error,report('interrupted') if isinstance(released,Ok) else None,empty)
    try:
        with _HostOperationReservation(host) if _engine is None else nullcontext():
            for chunk in range(total):
                indices=tuple(str(i) for i in ordered[chunk*int(input.chunk_size):(chunk+1)*int(input.chunk_size)])
                budget=getattr(host,'_batched_import_budget',None)
                if budget is None:budget={};host._batched_import_budget=budget
                for key in tuple(budget):
                    if key not in host._transactions:del budget[key]
                count,size=budget.get(transaction._key,(0,0));count+=len(indices);size+=len(original)+len(sources)
                budget[transaction._key]=(count,size)
                if count>4096 or size>268435456:return interrupted(ExecutionFailure('execution_obligation','Cumulative import submission budget exceeded',sql_state='54000'))
                def execute(cursor,observed):
                    pin_cursor(cursor)
                    cursor.execute('SELECT truss.person_process_import_chunk(%s,%s,%s::uuid,%s,%s,%s)',
                        (original,sources,invocation,chunk,manifest['releaseId'],digest),prepare=False)
                    value=json.loads(bytes(cursor.fetchone()[0]))
                    if type(value) is not dict or set(value)!={'context','outcomes','hostTransactionId'} or type(value['outcomes']) is not list:
                        raise ValueError('Closed native chunk result required')
                    if native_context is not None and value['context']!=native_context:
                        raise ValueError('Original import context changed')
                    decoded=[]
                    for outcome in value['outcomes']:
                        if type(outcome) is not dict or not _decimal(outcome.get('inputIndex'),4,zero=True):raise ValueError('Canonical original index required')
                        fields={'created':{'inputIndex','outcome','identity','version','groupAttemptId'},'skipped':{'inputIndex','outcome','reason'},'rejected':{'inputIndex','outcome','code'}}
                        expected=fields.get(outcome.get('outcome'))
                        if outcome.get('outcome')=='skipped' and 'identity' in outcome:expected=expected|{'identity'}
                        if expected is None or set(outcome)!=expected:raise ValueError('Closed native record outcome required')
                        if outcome['outcome']=='created':
                            if not _decimal(outcome['version']):raise ValueError('Exact created version required')
                            from uuid import UUID
                            if str(UUID(outcome['groupAttemptId']))!=outcome['groupAttemptId']:raise ValueError('Original group attempt required')
                        common={'input_index':outcome['inputIndex'],'batch_id':invocation+':'+str(chunk)}
                        if outcome['outcome']=='created':decoded.append(ImportCreated(**common,identity=_exact_identity(outcome['identity']),version=outcome['version']))
                        elif outcome['outcome']=='skipped':decoded.append(ImportSkipped(**common,reason=outcome['reason'],identity=_exact_identity(outcome['identity']) if 'identity' in outcome else ABSENT))
                        elif outcome['outcome']=='rejected':decoded.append(ImportRejected(**common,code=outcome['code']))
                        else:raise ValueError('Closed native chunk outcome required')
                    if tuple(sorted(o.input_index for o in decoded))!=tuple(sorted(indices)):
                        raise ValueError('Complete original chunk indices required')
                    # Decode all context fields under the savepoint before publishing effects.
                    _context(value['context']);_configuration(value['context'])
                    pending=(PendingBatch(batch_id=invocation+':'+str(chunk),input_indices=indices,host_transaction_id=value['hostTransactionId'])
                        if indices else EmptyLoadDisposition(load_attempt_id=invocation,disposition='pending',evidence=value['hostTransactionId']))
                    prefix='truss-pending-transaction:'+value['context']['sourceEpoch']+':'
                    if type(value['hostTransactionId']) is not str or not value['hostTransactionId'].startswith(prefix) or not _decimal(value['hostTransactionId'][len(prefix):]):
                        raise ValueError('Original pending transaction basis required')
                    if len(_bytes(value))>8388608:raise ValueError('Bounded native report required')
                    return value,tuple(decoded),pending
                result=host._run_operation(transaction,execute,function_call=True)
                if isinstance(result,Error):return interrupted(result.error)
                value,decoded,pending=result.value
                native_context=value['context'];batch_id=invocation+':'+str(chunk)
                outcomes.extend(decoded)
                if indices:
                    batches.append(pending)
                    if _engine is not None:
                        batches[-1],error=_engine.settle(batches[-1],commit=True)
                        if error is not None:return interrupted(error)
                else:
                    empty=pending
                    if _engine is not None:
                        if not host.detach():
                            empty=EmptyLoadDisposition(load_attempt_id=invocation,disposition='transaction_unresolved',evidence=invocation)
                            return failed(ExecutionFailure('transaction_unusable','Empty load completion unresolved'),empty=empty)
                        _engine.host=None
                        evidence=lambda command:sha256(b'truss-empty-load-settlement/0.1\n'+_bytes({'command':command,'loadAttemptId':invocation,'backendPid':str(_engine.connection.info.backend_pid)})).hexdigest()
                        settlements={command:EmptyLoadDisposition(load_attempt_id=invocation,disposition=state,evidence=evidence(command)) for command,state in (('COMMIT','committed'),('ROLLBACK','rolled_back'))}
                        observed,error=_engine.control('COMMIT',settlements)
                        empty=observed or EmptyLoadDisposition(load_attempt_id=invocation,disposition='commit_unknown' if _engine.submitted else 'transaction_unresolved',evidence=invocation)
                        if error is not None:return interrupted(error)
                if _engine is not None:host,transaction=_engine.begin()
            released=host._run_operation(transaction,release,function_call=True)
            if isinstance(released,Error):return failed(released.error,empty=empty)
            return wrapped(ImportReported(report=report('processed')),empty)
    except (ValueError,TypeError,KeyError,AttributeError):
        return failed(ExecutionFailure('execution_obligation','Batched import result or host scope unavailable'),empty=empty)
