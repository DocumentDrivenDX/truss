"""Public group composition over protected native calls and original UMF encoding."""
from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
import base64
import json
from .contracts import ABSENT, ExactArtifact, ProfilePin, QualifiedOwner, TypedIdentity, MapValue, TextValue, NullValue, BooleanValue
from .execution import Ok, Error, Outcome
from .groups import (GroupSemanticInput, GroupSemanticResult, GroupOperation, CurrentCatalog, CreateObject, CreateEdge, UpdateObject, UpdateEdge, Delete, StoredObjectReference, AliasObjectReference, RootlessOwnership,
    RequestNone, RequestPresent, RequestIdentity, GroupSuccess, GroupFailed, GroupUnavailable,
    InvalidGroupInput, RequestConflict, GroupOperationFailure, AppliedPending, SameTransactionReplay,
    CommittedReceiptReplay, SameTransactionReplayEvidence, CommittedReceiptReplayEvidence,
    GroupPrecondition, UnauthorizedPerson, PreconditionFailed, FailedPrecondition, Created, Changed, Unchanged, Deleted, DeletedIdentity, AliasIdentity, JournalEventReference)
from .preparation import CatalogDocument
from ._umf_key_tuples import KeyTupleRequest, encode_string_key_tuples

_DIAGNOSTIC=ProfilePin(identity='truss-native-create-diagnostic',version='0.1',
    sha256=sha256(b'Native create result: closed outcome/code/operationIndex/nativeState; no database source diagnostic disclosure; v1').hexdigest())
_OBSERVATION=ProfilePin(identity='truss-native-create-replay-observation',version='0.1',
    sha256=sha256(b'Native READ COMMITTED visible exact receipt; original xid versus current xid; current authorized person and owners; v1').hexdigest())

@dataclass(frozen=True, slots=True, kw_only=True)
class GroupRuntimeContext:
    layout_profile: ProfilePin
    mutation_profile: ProfilePin
    value_profile: ProfilePin
    request_fingerprint_profile: ProfilePin
    authorized_scope_identity: str
    source_epoch: str
    history_profile: str

    def input(self,operations: tuple[GroupOperation,*tuple[GroupOperation,...]],asserted_origin: MapValue,*,preconditions: tuple[GroupPrecondition,...]=()) -> GroupSemanticInput:
        return GroupSemanticInput(layout_profile=self.layout_profile,mutation_profile=self.mutation_profile,
            value_profile=self.value_profile,catalog=CurrentCatalog(),operations=operations,asserted_origin=asserted_origin,preconditions=preconditions)

    def request(self,request_id: str) -> RequestPresent:
        return RequestPresent(identity=RequestIdentity(authorized_scope_identity=self.authorized_scope_identity,request_id=request_id))


def _wire(value):
    if is_dataclass(value):
        result={}
        for member in fields(value):
            child=getattr(value,member.name)
            if child is ABSENT or member.name=='preconditions' and child==():continue
            parts=member.name.split('_');name=parts[0]+''.join(part.title() for part in parts[1:])
            result[name]=_wire(child)
        return result
    if type(value) is tuple:return [_wire(child) for child in value]
    return value


def _bytes(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')


def _artifact(raw: bytes):
    digest=sha256(raw).hexdigest()
    return ExactArtifact(identity=digest,bytes_base64=base64.b64encode(raw).decode('ascii'),sha256=digest)


def _identity(value):
    return TypedIdentity(id=value['id'],type_id=value['typeId'],definition_pin=value['definitionPin'],
        owner=QualifiedOwner(document_id=value['owner']['documentId'],module_id=value['owner']['moduleId']))


def _semantic(value):
    results=[]
    for entry in value['results']:
        events=tuple(JournalEventReference(source_epoch=e['sourceEpoch'],history_profile=e['historyProfile'],xid=e['xid'],seq=e['seq']) for e in entry['events'])
        identity=_identity(entry['identity'])
        if entry['outcome']=='created' and entry['operation'] in ('create_object','create_edge'):
            results.append(Created(operation=entry['operation'],identity=identity,version=entry['version'],events=events,alias=entry.get('alias',ABSENT)))
        elif entry['outcome']=='changed' and entry['operation'] in ('update_object','update_edge'):
            results.append(Changed(operation=entry['operation'],identity=identity,version=entry['version'],events=events))
        elif entry['outcome']=='unchanged' and entry['operation'] in ('update_object','update_edge') and not events:
            results.append(Unchanged(operation=entry['operation'],identity=identity,version=entry['version']))
        elif entry['outcome']=='deleted' and entry['operation'] in ('delete_object','delete_edge'):
            results.append(Deleted(operation=entry['operation'],identity=identity,deletion_version=entry['deletionVersion'],
                deleted=tuple(DeletedIdentity(identity=_identity(v['identity']),deletion_version=v['deletionVersion']) for v in entry['deleted']),events=events))
        else:raise ValueError('Selected native object or edge result required')
    return GroupSemanticResult(executed_catalog_revision=value['executedCatalogRevision'],
        layout_profile=ProfilePin(**value['layoutProfile']),mutation_profile=ProfilePin(**value['mutationProfile']),results=tuple(results),
        aliases=tuple(AliasIdentity(alias=a['alias'],identity=_identity(a['identity'])) for a in value['aliases']))


def _result(raw: bytes):
    value=json.loads(raw)
    if value['outcome']=='unavailable':return GroupUnavailable(reason=value['reason'])
    if value['outcome']=='failed':
        evidence=_artifact(raw)
        if value['code']=='precondition_failed':
            return GroupFailed(failure=PreconditionFailed(failures=tuple(FailedPrecondition(condition_id=v['conditionId'],reason=v['reason'],rule=v['rule']) for v in value['failures'])))
        if value['code']=='invalid_input':return GroupFailed(failure=InvalidGroupInput(diagnostic_profile=_DIAGNOSTIC,diagnostic=evidence))
        if value['code']=='unauthorized_person':return GroupFailed(failure=UnauthorizedPerson())
        if value['code']=='request_conflict':return GroupFailed(failure=RequestConflict(diagnostic_profile=_DIAGNOSTIC,diagnostic=evidence))
        return GroupFailed(failure=GroupOperationFailure(operation_index=value['operationIndex'],error_profile=_DIAGNOSTIC,inner_error=evidence))
    semantic=_semantic(value['semantic'])
    if value['disposition']=='applied':return GroupSuccess(response=AppliedPending(semantic=semantic))
    observation=base64.b64decode(value['observationBase64'],validate=True)
    if sha256(observation).hexdigest()!=value['observationSha256']:raise ValueError('Original native replay observation required')
    evidence=_artifact(observation)
    if value['durability']=='pending':
        return GroupSuccess(response=SameTransactionReplay(semantic=semantic,
            replay=SameTransactionReplayEvidence(observation_profile=_OBSERVATION,evidence=evidence)))
    if value['durability']=='committed':
        return GroupSuccess(response=CommittedReceiptReplay(semantic=semantic,
            replay=CommittedReceiptReplayEvidence(observation_profile=_OBSERVATION,evidence=evidence)))
    raise ValueError('Actual native receipt durability required')


def group_context(host,transaction,manifest,digest,pin_cursor):
    def observe(cursor,observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.group_context(%s,%s)',(manifest['releaseId'],digest),prepare=False)
        value=json.loads(bytes(cursor.fetchone()[0]))
        return GroupRuntimeContext(layout_profile=ProfilePin(**value['layoutProfile']),mutation_profile=ProfilePin(**value['mutationProfile']),
            value_profile=ProfilePin(**value['valueProfile']),request_fingerprint_profile=ProfilePin(**value['requestFingerprintProfile']),authorized_scope_identity=value['authorizedScopeIdentity'],
            source_epoch=value['sourceEpoch'],history_profile=value['historyProfile'])
    return host._run_operation(transaction,observe)


def apply_group(host,transaction,input,request,documents,manifest,digest,pin_cursor,*,bun_executable='bun'):
    if type(input) is not GroupSemanticInput or type(request) not in (RequestNone,RequestPresent):
        return Ok(GroupFailed(failure=InvalidGroupInput(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"shape"}'))))
    if (type(input.catalog) is not CurrentCatalog or type(input.asserted_origin) is not MapValue
        or any(not (type(op) is CreateObject and type(op.ownership) is RootlessOwnership or type(op) is UpdateObject and op.ownership_change is ABSENT and type(op.target) in (StoredObjectReference,AliasObjectReference) or type(op) in (CreateEdge,UpdateEdge) or type(op) is Delete and op.operation in ('delete_object','delete_edge') and type(op.target) in (StoredObjectReference,AliasObjectReference)) for op in input.operations)):
        return Ok(GroupUnavailable(reason='profile'))
    if not 1<=len(input.operations)<=128 or any(len(op.values if type(op) in (CreateObject,CreateEdge) else op.set if type(op) in (UpdateObject,UpdateEdge) else ())>1024 for op in input.operations):
        return Ok(GroupUnavailable(reason='resource'))
    def scalar(value):return type(value) in (NullValue,TextValue,BooleanValue)
    def origin_scalar(value):return type(value) is NullValue or (type(value) is TextValue and value.kind=='string')
    if any(not scalar(v.value) for op in input.operations for v in (op.values if type(op) in (CreateObject,CreateEdge) else op.set if type(op) in (UpdateObject,UpdateEdge) else ())) or any(not origin_scalar(e.value) for e in input.asserted_origin.entries):
        return Ok(GroupUnavailable(reason='profile'))
    if type(documents) is not tuple or not 1<=len(documents)<=512 or any(type(d) is not CatalogDocument or type(d.document_id) is not str or type(d.content) is not bytes for d in documents):
        return Ok(GroupFailed(failure=InvalidGroupInput(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"original_documents"}'))))
    if len({d.document_id for d in documents})!=len(documents):
        return Ok(GroupFailed(failure=InvalidGroupInput(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"duplicate_documents"}'))))
    try:
        original_input=_bytes(_wire(input));original_request=_bytes(_wire(request))
        original_documents=_bytes([{'documentId':d.document_id,'sourceText':d.content.decode('utf8')} for d in documents])
    except (UnicodeError,ValueError,TypeError):
        return Ok(GroupFailed(failure=InvalidGroupInput(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"transport"}'))))
    if len(original_input)>1048576 or len(original_request)>65536 or len(original_documents)>4194304:
        return Ok(GroupUnavailable(reason='resource'))
    sources={d.document_id:d.content for d in documents}
    operation_index=[0]
    def apply(cursor,observed):
        pin_cursor(cursor)
        condition_keys=[]
        if input.preconditions:
            cursor.execute('SELECT truss.group_condition_key_metadata(%s,%s,%s,%s)',
                (original_input,original_documents,manifest['releaseId'],digest),prepare=False)
            for metadata in json.loads(bytes(cursor.fetchone()[0])):
                request=KeyTupleRequest(metadata['moduleId'],metadata['recordId'],metadata['keyId'],tuple(v['text'] for v in metadata['values']))
                original=encode_string_key_tuples(sources[metadata['documentId']],(request,),bun_executable=bun_executable)[0]
                condition_keys.append({'conditionIndex':str(metadata['index']),'tupleHex':original.tuple_bytes.hex(),
                    'receiptBase64':base64.b64encode(original.original_receipt_bytes).decode('ascii')})
        cursor.execute('SELECT truss.object_group_begin(%s,%s,%s,%s,%s,%s)',
            (original_input,original_documents,original_request,manifest['releaseId'],digest,_bytes(condition_keys)),prepare=False)
        begin=json.loads(bytes(cursor.fetchone()[0]))
        if begin['outcome']!='execute':return _result(_bytes(begin))
        attempt_id=begin['attemptId']
        for index,operation in enumerate(input.operations):
            operation_index[0]=index
            cursor.execute('SELECT truss.object_group_metadata(%s::uuid,%s)',(attempt_id,index),prepare=False)
            metadata=json.loads(bytes(cursor.fetchone()[0]));encoded_keys=[];requests=[];addresses=[]
            values={v['name']:v['value'] for v in metadata['values']}
            for key in metadata['keys']:
                if any(name not in values or values[name].get('kind')!='string' for name in key['names']):continue
                requests.append(KeyTupleRequest(metadata['moduleId'],metadata['recordId'],key['keyId'],tuple(values[name]['text'] for name in key['names'])))
                addresses.append(key['keyNumber'])
            if requests:
                originals=encode_string_key_tuples(sources[metadata['documentId']],tuple(requests),bun_executable=bun_executable)
                for address,original in zip(addresses,originals):
                    encoded_keys.append({'operationIndex':'0','keyNumber':address,'tupleHex':original.tuple_bytes.hex(),
                        'receiptBase64':base64.b64encode(original.original_receipt_bytes).decode('ascii')})
            original_keys=_bytes(encoded_keys)
            if len(original_keys)>8388608:raise ValueError('Bounded original key inventory required')
            cursor.execute('SELECT truss.object_group_step(%s::uuid,%s,%s)',(attempt_id,index,original_keys),prepare=False)
            cursor.fetchone()
        cursor.execute('SELECT truss.object_group_finish(%s::uuid)',(attempt_id,),prepare=False)
        return _result(bytes(cursor.fetchone()[0]))
    result=host._run_operation(transaction,apply)
    if isinstance(result,Error) and result.error.code=='execution_obligation':
        state=result.error.sql_state
        if state=='42501':return Ok(GroupFailed(failure=UnauthorizedPerson()))
        reason={'0A000':'profile','54000':'resource','55P03':'observation'}.get(state)
        if reason:return Ok(GroupUnavailable(reason=reason))
        if state in ('22023','23505','P1001','P1003','P1004','P1005'):
            code={'P1001':'request_conflict','P1003':'expected_version','P1004':'not_found','P1005':'dependencies','23505':'key_conflict','22023':'invalid_input'}[state]
            return Ok(_result(_bytes({'outcome':'failed','code':code,'operationIndex':str(operation_index[0]),'nativeState':state})))
    return result

# A real selected provider; native readiness and authority are checked per call.
from typing import Callable, Literal, overload
from .contracts import CapabilitySelection
from .execution import TransactionHandle
from .groups import GroupRequestSelection, GroupApplicationResult, RequestFreeGroupApplicationResult

@dataclass(frozen=True, slots=True, kw_only=True)
class NativeGroupCapability:
    selection: CapabilitySelection[Literal['group']]
    _apply: Callable[[TransactionHandle, GroupSemanticInput, GroupRequestSelection], Outcome[GroupApplicationResult]]

    @overload
    def apply_in_transaction(self,transaction: TransactionHandle,input: GroupSemanticInput,
                             request: RequestNone) -> Outcome[RequestFreeGroupApplicationResult]: ...
    @overload
    def apply_in_transaction(self,transaction: TransactionHandle,input: GroupSemanticInput,
                             request: RequestPresent) -> Outcome[GroupApplicationResult]: ...
    @overload
    def apply_in_transaction(self,transaction: TransactionHandle,input: GroupSemanticInput,
                             request: GroupRequestSelection) -> Outcome[GroupApplicationResult]: ...
    def apply_in_transaction(self,transaction: TransactionHandle,input: GroupSemanticInput,
                             request: GroupRequestSelection) -> Outcome[GroupApplicationResult]:
        return self._apply(transaction,input,request)

@dataclass(frozen=True, slots=True, kw_only=True)
class GroupCapabilityAvailable:
    capability: NativeGroupCapability
    status: Literal['ok'] = 'ok'
