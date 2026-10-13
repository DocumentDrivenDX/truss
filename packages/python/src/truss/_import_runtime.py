"""Host-owned imports through the existing protected group and source producers."""
import base64,json
from hashlib import sha256
from uuid import uuid4
from .contracts import (ABSENT,ProfilePin,SelectedMutationConfiguration,MapValue,MapEntry,TextValue,NullValue,BooleanValue)
from .execution import Ok,Error,ExecutionFailure
from .imports import (ImportInput,ObjectImportRecord,EdgeImportRecord,ImportReported,ImportInvalid,ImportExecutionFailed,
    ImportReport,ImportCounts,ImportCreated,ImportSkipped,ImportRejected,ImportAttemptUnknown,PendingBatch,RolledBackBatch,TransactionUnresolvedBatch)
from .groups import (CreateObject,CreateEdge,AuthoredValue,RootlessOwnership,StoredObjectReference,NullOrderKey,TextOrderKey,
    RequestNone,GroupSuccess)
from ._group_runtime import GroupRuntimeContext,_wire,_bytes,_artifact,_identity,apply_group
from ._acceptance_json import decode_acceptance_json
from ._umf_key_tuples import KeyTupleRequest,encode_key_tuples
from .psycopg_host import _HostOperationReservation
from .preparation import CatalogDocument
from ._catalog_report_semantics import canonical_numeric_free

class _RecordRefused(Exception):
    pass


_DIAGNOSTIC=ProfilePin(identity='truss-import-input-diagnostic',version='0.1',sha256=sha256(b'Closed import invalid-input code; no native diagnostic disclosure;v1').hexdigest())


def _cell(value):
    if type(value) is not dict:raise ValueError('Exact scalar cell required')
    if value=={'kind':'null'}:return NullValue()
    if value.get('kind')=='boolean' and set(value)=={'kind','value'}:return BooleanValue(value=value['value'])
    if value.get('kind') in ('string','integer','decimal','timestamp','binary') and set(value)=={'kind','text'}:return TextValue(kind=value['kind'],text=value['text'])
    raise ValueError('Selected scalar cell required')


def _payload(record,metadata):
    value=decode_acceptance_json(base64.b64decode(record.payload.bytes_base64,validate=True))
    fields={'interfaceVersion','kind','values','source','ownership' if type(record) is ObjectImportRecord else 'orderKey'}
    if set(value)-fields or value.get('interfaceVersion')!='truss-import-payload/0.1.0' or value.get('kind')!=record.kind or type(value.get('values')) is not list:
        raise ValueError('Closed original import payload required')
    values=tuple(AuthoredValue(name=v['name'],value=_cell(v['value'])) for v in value['values'])
    if len(values)>1024 or len({v.name for v in values})!=len(values) or any(set(v)!= {'name','value'} for v in value['values']):raise ValueError('Unique authored scalar values required')
    if 'source' in value:
        source=value['source']
        if type(source) is not dict or set(source)!= {'kind','entries'} or source['kind']!='map' or type(source['entries']) is not list:raise ValueError('Source map required')
        entries=tuple(MapEntry(key=e['key'],value=_cell(e['value'])) for e in source['entries'])
        if len({e.key for e in entries})!=len(entries) or any(set(e)!= {'key','value'} for e in source['entries']):raise ValueError('Unique source fields required')
        if any(e.key in ('author','at','system') and not (type(e.value) is NullValue or type(e.value) is TextValue and e.value.kind=='string') for e in entries):raise ValueError('Known source facts are string or null')
    if type(record) is ObjectImportRecord:
        if value.get('ownership')!={'state':'rootless'}:raise ValueError('Rootless imported objects required')
        for primary in metadata['primaryFields']:
            if not any(v.name==primary['name'] and _wire(v.value)==primary['value'] for v in values):raise ValueError('Original primary payload agreement required')
        return CreateObject(type_definition_pin=metadata['definitionPin'],values=values,ownership=RootlessOwnership())
    order=value.get('orderKey')
    if order=={'state':'null'}:order_key=NullOrderKey()
    elif type(order) is dict and set(order)=={'state','text'} and order['state']=='text':order_key=TextOrderKey(text=order['text'])
    else:raise ValueError('Exact edge order key required')
    return CreateEdge(relationship_definition_pin=record.identity.relationship_definition_pin,source=StoredObjectReference(identity=record.identity.source),
        target=StoredObjectReference(identity=record.identity.target),values=values,order_key=order_key)


def run_import(host,transaction,input,documents,manifest,digest,pin_cursor,*,bun_executable='bun'):
    if type(input) is not ImportInput or type(documents) is not tuple or any(type(d) is not CatalogDocument for d in documents) or any(type(r) not in (ObjectImportRecord,EdgeImportRecord) for r in input.records):
        return ImportInvalid(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"shape"}'))
    try:
        original=canonical_numeric_free(_wire(input))
        if len(input.records)>128 or len(original)>8388608 or type(input.asserted_origin) is not MapValue or not 1<=len(input.load_id.encode('utf8'))<=4096 or '\0' in input.load_id:raise ValueError('Import envelope limits')
        if len({e.key for e in input.asserted_origin.entries})!=len(input.asserted_origin.entries) or any(not (type(e.value) is NullValue or type(e.value) is TextValue and e.value.kind=='string') for e in input.asserted_origin.entries):raise ValueError('Selected scalar asserted origin required')
        if any(e.key=='x-load-id' for e in input.asserted_origin.entries):raise ValueError('Load id is separately supplied')
        for record in input.records:
            payload=base64.b64decode(record.payload.bytes_base64,validate=True)
            if not 1<=len(payload)<=1048576 or sha256(payload).hexdigest()!=record.payload.sha256:raise ValueError('Original payload byte/hash integrity')
        sources={d.document_id:d.content for d in documents}
        if len(sources)!=len(documents) or any(type(r) is ObjectImportRecord and r.identity.type.owner.document_id not in sources for r in input.records):raise ValueError('Complete unique caller-known documents')
    except (ValueError,TypeError,UnicodeError,AttributeError):
        return ImportInvalid(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"envelope"}'))
    attempt_id=uuid4().hex;outcomes=[];batches=[];visited=set();configuration=None;context=None
    def report(status='processed'):
        pending={b.batch_id for b in batches if b.disposition=='pending'}
        rolled={b.batch_id for b in batches if b.disposition=='rolled_back'}
        unresolved={b.batch_id for b in batches if b.disposition=='transaction_unresolved'}
        counts=ImportCounts(created_committed='0',created_pending=str(sum(type(o) is ImportCreated and o.batch_id in pending for o in outcomes)),
            created_rolled_back=str(sum(type(o) is ImportCreated and o.batch_id in rolled for o in outcomes)),created_commit_unknown='0',
            created_transaction_unresolved=str(sum(type(o) is ImportCreated and o.batch_id in unresolved for o in outcomes)),attempt_unknown=str(sum(type(o) is ImportAttemptUnknown for o in outcomes)),
            skipped=str(sum(type(o) is ImportSkipped for o in outcomes)),rejected=str(sum(type(o) is ImportRejected for o in outcomes)),unprocessed=str(len(input.records)-len(visited)))
        return ImportReport(attempt_id=attempt_id,input_count=str(len(input.records)),executed_catalog_revision=context['catalog']['revision'],import_profile=input.import_profile,
            selected_configuration=configuration,input_sha256=sha256(b'truss-canonical/0.1.0\ntruss-import-input/0.1.0\n'+original).hexdigest(),execution='host_adopted',status=status,
            outcomes=tuple(sorted(outcomes,key=lambda o:int(o.input_index))),batches=tuple(batches),unprocessed_indices=tuple(str(i) for i in range(len(input.records)) if i not in visited),counts=counts)
    def release_report(cursor,observed):
        pin_cursor(cursor)
        for outcome in outcomes:
            if type(outcome) not in (ImportCreated,ImportSkipped):continue
            record=input.records[int(outcome.input_index)]
            cursor.execute('SELECT truss.import_report_record_authority(%s,%s,%s,%s)',(_bytes(_wire(record.identity)),record.kind,manifest['releaseId'],digest),prepare=False);cursor.fetchone()
        return True
    def interrupted(error):
        custody=host._transactions.get(transaction._key)
        if context is None or host._custody.quarantined or custody is None or not custody.usable:
            return ImportExecutionFailed(error=error,report=None)
        admitted=host._run_operation(transaction,release_report)
        if isinstance(admitted,Error):
            recovery=admitted.error
            if recovery.code=='transaction_unusable' or recovery.retry_scope=='whole_transaction':error=recovery
            return ImportExecutionFailed(error=error,report=None)
        retained_report=report('interrupted')
        return ImportExecutionFailed(error=error,report=retained_report if len(_bytes(_wire(retained_report)))<=8388608 else None)
    try:
        with _HostOperationReservation(host):
            def admit(cursor,observed):
                pin_cursor(cursor);cursor.execute('SELECT truss.import_context(%s,%s)',(manifest['releaseId'],digest),prepare=False)
                native=json.loads(bytes(cursor.fetchone()[0]))
                if _wire(input.layout_profile)!=native['layoutProfile'] or _wire(input.import_profile)!=native['importProfile'] or _wire(input.value_profile)!=native['valueProfile'] or _wire(input.catalog)!=native['catalog']:
                    raise ValueError('Selected original import context required')
                if any(_wire(r.payload_profile)!=native['importPayloadProfile'] for r in input.records):raise ValueError('Selected import payload profile required')
                cursor.execute('SELECT pg_current_xact_id()::text',prepare=False);native['hostTransactionId']='truss-pending-transaction:'+native['sourceEpoch']+':'+cursor.fetchone()[0]
                return native
            admitted=host._run_operation(transaction,admit)
            if isinstance(admitted,Error):return ImportExecutionFailed(error=admitted.error,report=None)
            context=admitted.value;selected=context['selectedConfiguration']
            configuration=SelectedMutationConfiguration(source_epoch=selected['sourceEpoch'],installation_id=selected['installationId'],generation=selected['generation'],
                key_reuse=selected['keyReuse'],journal_mode=selected['journalMode'],configuration_profile=ProfilePin(**selected['configurationProfile']),installed_producer_inventory_sha256=selected['installedProducerInventorySha256'])
            group_context=GroupRuntimeContext(layout_profile=input.layout_profile,mutation_profile=ProfilePin(**context['mutationProfile']),value_profile=input.value_profile,
                request_fingerprint_profile=ProfilePin(**context['requestFingerprintProfile']),authorized_scope_identity=context['authorizedScopeIdentity'],source_epoch=context['sourceEpoch'],history_profile=context['historyProfile'])
            order=sorted(range(len(input.records)),key=lambda i:(type(input.records[i]) is EdgeImportRecord,i))
            for index in order:
                record=input.records[index];batch_id=attempt_id+':'+str(index);known=[None];entered=[False];submitted=[False];before_attempt=host._custody.last_attempt
                def execute(cursor,observed):
                    entered[0]=True
                    pin_cursor(cursor)
                    cursor.execute('SELECT truss.import_context(%s,%s)',(manifest['releaseId'],digest),prepare=False)
                    if json.loads(bytes(cursor.fetchone()[0]))!= {k:v for k,v in context.items() if k!='hostTransactionId'}:raise ValueError('Original import context changed')
                    if type(record) is ObjectImportRecord:
                        cursor.execute('SELECT truss.import_identity_key_selection(%s,%s,%s)',(_bytes(_wire(record.identity)),manifest['releaseId'],digest),prepare=False)
                        metadata=json.loads(bytes(cursor.fetchone()[0]))
                        request=KeyTupleRequest(record.identity.type.owner.module_id,metadata['recordId'],metadata['keyId'],tuple(c.value for c in record.identity.components))
                        original_key=encode_key_tuples(sources[record.identity.type.owner.document_id],(request,),bun_executable=bun_executable)[0]
                        cursor.execute('SELECT truss.import_object_identity(%s,%s,%s,%s,%s)',(_bytes(_wire(record.identity)),sources[record.identity.type.owner.document_id],original_key.tuple_bytes,manifest['releaseId'],digest),prepare=False)
                    else:cursor.execute('SELECT truss.import_edge_identity(%s,%s,%s)',(_bytes(_wire(record.identity)),manifest['releaseId'],digest),prepare=False)
                    metadata=json.loads(bytes(cursor.fetchone()[0]))
                    if metadata['state']=='skipped':return ImportSkipped(input_index=str(index),batch_id=batch_id,reason=metadata['reason'],identity=_identity(metadata['identity']) if 'identity' in metadata else ABSENT)
                    try:operation=_payload(record,metadata)
                    except (ValueError,TypeError,KeyError):known[0]='invalid_payload';raise _RecordRefused('Eligible import payload refused')
                    origin=MapValue(entries=input.asserted_origin.entries+(MapEntry(key='x-load-id',value=TextValue(kind='string',text=input.load_id)),))
                    capture=[];submitted[0]=True
                    applied=apply_group(host,transaction,group_context.input((operation,),origin),RequestNone(),documents,manifest,digest,pin_cursor,
                        bun_executable=bun_executable,_cursor=cursor,_attempt_capture=capture)
                    if not isinstance(applied,Ok) or not isinstance(applied.value,GroupSuccess):known[0]='unsupported_profile';raise _RecordRefused('Import group refused')
                    created=applied.value.response.semantic.results[0]
                    cursor.execute('SELECT truss.import_record_source(%s::uuid,%s,%s)',(capture[0],_bytes(_wire(record)),input.load_id),prepare=False);cursor.fetchone()
                    return ImportCreated(input_index=str(index),batch_id=batch_id,identity=created.identity,version=created.version)
                result=host._run_operation(transaction,execute)
                if isinstance(result,Ok):
                    visited.add(index)
                    outcomes.append(result.value);batches.append(PendingBatch(batch_id=batch_id,input_indices=(str(index),),host_transaction_id=context['hostTransactionId']));continue
                failure=result.error
                native_attempt=host._custody.last_attempt if host._custody.last_attempt is not before_attempt else None
                contained=native_attempt is not None and native_attempt.phase=='contained' and not host._custody.quarantined
                observed=native_attempt.result if native_attempt is not None else None
                custody=host._transactions.get(transaction._key)
                retained=contained and custody is not None and custody.usable
                proof=_bytes({'attempt':attempt_id,'index':str(index),'error':_wire(failure),
                    'nativeAttemptReference':None if native_attempt is None else native_attempt.reference,
                    'phase':None if native_attempt is None else native_attempt.phase,'hostTransactionId':context['hostTransactionId']})
                rejected=known[0] or {'22023':'invalid','23505':'conflict','42501':'unauthorized','0A000':'unsupported_profile','P1004':'missing_endpoint','P1005':'dependencies'}.get(failure.sql_state)
                if contained and failure.code=='execution_obligation' and failure.retry_scope=='none' and rejected is not None:
                    visited.add(index);outcomes.append(ImportRejected(input_index=str(index),batch_id=batch_id,code=rejected))
                    batches.append(RolledBackBatch(batch_id=batch_id,input_indices=(str(index),),rollback_evidence_sha256=sha256(proof).hexdigest()));continue
                if entered[0]:
                    visited.add(index)
                    if type(observed) in (ImportCreated,ImportSkipped):outcomes.append(observed)
                    else:outcomes.append(ImportAttemptUnknown(input_index=str(index),batch_id=batch_id,recovery_reference=batch_id))
                    batches.append(RolledBackBatch(batch_id=batch_id,input_indices=(str(index),),rollback_evidence_sha256=sha256(proof).hexdigest()) if contained
                        else TransactionUnresolvedBatch(batch_id=batch_id,input_indices=(str(index),),recovery_reference=batch_id))
                if not retained:
                    batches[:]=[TransactionUnresolvedBatch(batch_id=b.batch_id,input_indices=b.input_indices,recovery_reference=b.batch_id) if b.disposition=='pending' else b for b in batches]
                return interrupted(failure)
            completed_report=report()
            if len(_bytes(_wire(completed_report)))>8388608:
                return interrupted(ExecutionFailure('execution_obligation','Import report byte ceiling exceeded'))
            released=host._run_operation(transaction,release_report)
            if isinstance(released,Error):
                custody=host._transactions.get(transaction._key)
                if host._custody.quarantined or host._custody.last_attempt.phase!='contained' or custody is None or not custody.usable:
                    batches[:]=[TransactionUnresolvedBatch(batch_id=b.batch_id,input_indices=b.input_indices,recovery_reference=b.batch_id) if b.disposition=='pending' else b for b in batches]
                return ImportExecutionFailed(error=released.error,report=None)
            return ImportReported(report=completed_report)
    except ValueError:
        return ImportExecutionFailed(error=ExecutionFailure('execution_obligation','Original host import scope unavailable'),report=None)
