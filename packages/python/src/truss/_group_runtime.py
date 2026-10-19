# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public group composition over protected native calls and original UMF encoding."""
from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
import base64
import json
from .contracts import SequenceValue,ABSENT, Absent, ExactArtifact, ProfilePin, QualifiedOwner, TypedIdentity, MapValue, MapEntry, TextValue, NullValue, BooleanValue
from .execution import Ok, Error, ExecutionFailure, Outcome
from .catalog_view import CatalogDefinitionReference
from .groups import (GroupSemanticInput, GroupSemanticResult, GroupOperation, CurrentCatalog, CreateObject, CreateEdge, UpdateObject, UpdateEdge, Delete, StoredObjectReference, AliasObjectReference, RootlessOwnership, OwnedOwnership,
    RequestNone, RequestPresent, RequestIdentity, GroupSuccess, GroupFailed, GroupUnavailable,
    InvalidGroupInput, RequestConflict, GroupOperationFailure, AppliedPending, SameTransactionReplay,
    CommittedReceiptReplay, SameTransactionReplayEvidence, CommittedReceiptReplayEvidence,
    GroupPrecondition, UnauthorizedPerson, PreconditionFailed, FailedPrecondition, Created, Changed, Unchanged, Deleted, DeletedIdentity, AliasIdentity, JournalEventReference)
from .preparation import CatalogDocument
from ._receipt_position import decode_receipt_position

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


@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogRevisionProbe:
    catalog_revision: str
    document_id: str | Absent = ABSENT
    document_revision: str | Absent = ABSENT
    source_catalog_revision: str | Absent = ABSENT


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedGroup:
    catalog_revision: str
    context: GroupRuntimeContext
    types: tuple[CatalogDefinitionReference | None, ...]
    relationships: tuple[CatalogDefinitionReference | None, ...]


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
            failures=tuple(FailedPrecondition(condition_id=v['conditionId'],reason=v['reason'],rule=v['rule']) for v in value['failures'])
            if not failures:raise ValueError('Nonempty failed preconditions required')
            return GroupFailed(failure=PreconditionFailed(failures=(failures[0],*failures[1:])))
        if value['code']=='invalid_input':return GroupFailed(failure=InvalidGroupInput(diagnostic_profile=_DIAGNOSTIC,diagnostic=evidence))
        if value['code']=='unauthorized_person':return GroupFailed(failure=UnauthorizedPerson())
        if value['code']=='request_conflict':return GroupFailed(failure=RequestConflict(diagnostic_profile=_DIAGNOSTIC,diagnostic=evidence))
        return GroupFailed(failure=GroupOperationFailure(operation_index=value['operationIndex'],error_profile=_DIAGNOSTIC,inner_error=evidence))
    semantic=_semantic(value['semantic'])
    token=value.get('receiptToken')
    if token is not None:decode_receipt_position(token)
    else:token=ABSENT
    if value['disposition']=='applied':return GroupSuccess(response=AppliedPending(semantic=semantic,receipt_token=token))
    observation=base64.b64decode(value['observationBase64'],validate=True)
    if sha256(observation).hexdigest()!=value['observationSha256']:raise ValueError('Original native replay observation required')
    evidence=_artifact(observation)
    if value['durability']=='pending':
        return GroupSuccess(response=SameTransactionReplay(semantic=semantic,
            replay=SameTransactionReplayEvidence(observation_profile=_OBSERVATION,evidence=evidence),receipt_token=token))
    if value['durability']=='committed':
        token=value.get('receiptToken',ABSENT)
        if token is not ABSENT:decode_receipt_position(token)
        return GroupSuccess(response=CommittedReceiptReplay(semantic=semantic,
            replay=CommittedReceiptReplayEvidence(observation_profile=_OBSERVATION,evidence=evidence),receipt_token=token))
    raise ValueError('Actual native receipt durability required')


def group_context(host,transaction,manifest,digest,pin_cursor):
    def observe(cursor,observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.group_context(%s,%s)',(manifest['releaseId'],digest),prepare=False)
        value=json.loads(bytes(cursor.fetchone()[0]))
        return _runtime_context(value)
    return host._run_operation(transaction,observe, function_call=True)


def _bounded_name(value):
    try:
        return type(value) is str and 1<=len(value.encode('utf-8'))<=4096 and '\0' not in value
    except UnicodeEncodeError:
        return False


def _named(entries):
    return type(entries) is tuple and len(entries)<=128 and all(type(entry) is tuple and len(entry)==3 and all(_bounded_name(part) for part in entry) for entry in entries)


def _runtime_context(value):
    return GroupRuntimeContext(layout_profile=ProfilePin(**value['layoutProfile']),mutation_profile=ProfilePin(**value['mutationProfile']),
        value_profile=ProfilePin(**value['valueProfile']),request_fingerprint_profile=ProfilePin(**value['requestFingerprintProfile']),authorized_scope_identity=value['authorizedScopeIdentity'],
        source_epoch=value['sourceEpoch'],history_profile=value['historyProfile'])


def _definition(value):
    if value is None:return None
    owner=QualifiedOwner(document_id=value['owner']['documentId'],module_id=value['owner']['moduleId'])
    if value['kind']=='type':
        return CatalogDefinitionReference(kind='type',definition_pin=value['definitionPin'],type_id=value['typeId'],authored_identity=value['authoredIdentity'],owner=owner)
    if value['kind']=='relationship':
        return CatalogDefinitionReference(kind='relationship',definition_pin=value['definitionPin'],relationship_id=value['relationshipId'],authored_identity=value['authoredIdentity'],owner=owner)
    raise ValueError('Selected type or relationship reference required')


def catalog_revision(host,transaction,manifest,digest,pin_cursor,document_id):
    if document_id is not None and not _bounded_name(document_id):
        return Error(ExecutionFailure('execution_obligation','Bounded document selection required',catalog_code='invalid_input'))
    def observe(cursor,observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.catalog_revision(%s,%s,%s)',(manifest['releaseId'],digest,document_id),prepare=False)
        value=json.loads(bytes(cursor.fetchone()[0]))
        return CatalogRevisionProbe(catalog_revision=value['catalogRevision'],
            document_id=value['documentId'] if 'documentId' in value else ABSENT,
            document_revision=value['documentRevision'] if 'documentRevision' in value else ABSENT,
            source_catalog_revision=value['sourceCatalogRevision'] if 'sourceCatalogRevision' in value else ABSENT)
    return host._run_operation(transaction,observe, function_call=True)


def prepare_group(host,transaction,manifest,digest,pin_cursor,records,relationships):
    if not _named(records) or not _named(relationships):
        return Error(ExecutionFailure('execution_obligation','Bounded named record set required',catalog_code='invalid_input'))
    original_records=json.dumps([{'documentId':document,'moduleId':module,'recordId':record} for document,module,record in records],separators=(',',':')).encode()
    original_relationships=json.dumps([{'documentId':document,'moduleId':module,'relationshipId':relationship} for document,module,relationship in relationships],separators=(',',':')).encode()
    def observe(cursor,observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.prepare_group(%s,%s,%s,%s)',(original_records,original_relationships,manifest['releaseId'],digest),prepare=False)
        value=json.loads(bytes(cursor.fetchone()[0]))
        return PreparedGroup(catalog_revision=value['catalogRevision'],context=_runtime_context(value['context']),
            types=tuple(_definition(entry) for entry in value['types']),relationships=tuple(_definition(entry) for entry in value['relationships']))
    return host._run_operation(transaction,observe, function_call=True)


def apply_group(host,transaction,input,request,documents,manifest,digest,pin_cursor,*,bun_executable='bun',_cursor=None,_attempt_capture=None,_schema_state=None):
    if type(input) is not GroupSemanticInput or type(request) not in (RequestNone,RequestPresent):
        return Ok(GroupFailed(failure=InvalidGroupInput(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"shape"}'))))
    selected_owned = input.mutation_profile == ProfilePin(identity='truss-owned-scalar-graph',version='0.1',sha256='5f5badaa3b0beb01fef08d48883395eabc8499155d4c31f7ef802e63d49a6dde')
    def ownership(value):
        return (type(value) is RootlessOwnership or selected_owned and type(value) is OwnedOwnership
                and type(value.root) in (StoredObjectReference,AliasObjectReference))
    if (type(input.catalog) is not CurrentCatalog or type(input.asserted_origin) is not MapValue
        or any(not (type(op) is CreateObject and ownership(op.ownership) or type(op) is UpdateObject and (op.ownership_change is ABSENT or selected_owned and ownership(op.ownership_change)) and type(op.target) in (StoredObjectReference,AliasObjectReference) or type(op) in (CreateEdge,UpdateEdge) or type(op) is Delete and op.operation in ('delete_object','delete_edge') and type(op.target) in (StoredObjectReference,AliasObjectReference)) for op in input.operations)):
        return Ok(GroupUnavailable(reason='profile'))
    if not 1<=len(input.operations)<=(1024 if selected_owned else 128) or any(len(op.values if type(op) in (CreateObject,CreateEdge) else op.set if type(op) in (UpdateObject,UpdateEdge) else ())>1024 for op in input.operations):
        return Ok(GroupUnavailable(reason='resource'))
    def scalar(value):return type(value) in (NullValue,TextValue,BooleanValue)
    def container(value):
        pending=[(value,0)];count=0
        while pending:
            member,depth=pending.pop();count+=1
            if depth>32 or count>4096:return False
            if scalar(member):continue
            if type(member) is SequenceValue:
                if type(member.items) is not tuple or len(member.items)>1024:return False
                pending.extend((child,depth+1) for child in member.items)
            elif type(member) is MapValue:
                if type(member.entries) is not tuple or len(member.entries)>1024:return False
                if any(type(entry) is not MapEntry or type(entry.key) is not str for entry in member.entries):return False
                # Native admission reports duplicate map keys as invalid input.
                pending.extend((entry.value,depth+1) for entry in member.entries)
            else:return False
            if count+len(pending)>4096:return False
        return True
    def origin_scalar(value):return type(value) is NullValue or (type(value) is TextValue and value.kind=='string')
    if any(not (container(v.value) if type(op) in (CreateObject,UpdateObject) else scalar(v.value)) for op in input.operations for v in (op.values if type(op) in (CreateObject,CreateEdge) else op.set if type(op) in (UpdateObject,UpdateEdge) else ())) or any(not origin_scalar(e.value) for e in input.asserted_origin.entries):
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
    def apply(cursor,observed):
        pin_cursor(cursor)
        prepared=None
        if selected_owned and _schema_state is not None:
            from ._record_preparation import prepare_records
            prepared=prepare_records(cursor,_schema_state,input,original_input,original_documents,manifest['releaseId'],digest)
        if prepared is None:
            cursor.execute('SELECT truss.apply_group(%s,%s,%s,%s,%s)',
                (original_input,original_documents,original_request,manifest['releaseId'],digest),prepare=False)
        else:
            cursor.execute('SELECT truss.apply_group_prepared(%s,%s,%s,%s,%s,%s::jsonb)',
                (original_input,original_documents,original_request,manifest['releaseId'],digest,_bytes(prepared).decode('utf8')),prepare=False)
        raw=bytes(cursor.fetchone()[0])
        if _attempt_capture is not None:
            value=json.loads(raw)
            if value.get('disposition')=='applied' and value.get('outcome')=='success':
                _attempt_capture.append(value['attemptId'])
        result=_result(raw)
        if _schema_state is not None and type(result) is GroupUnavailable and result.reason=='observation':
            _schema_state.clear()
        return result
    if _cursor is not None:return Ok(apply(_cursor,None))
    result=host._run_operation(transaction,apply, function_call=True)
    # Revocation can remove EXECUTE before the native facade can return its
    # typed refusal. Only translate a permission failure the host contained;
    # unresolved transaction/connection failures retain their execution outcome.
    if (isinstance(result,Error) and result.error.code=='execution_obligation'
            and result.error.sql_state=='42501'):
        return Ok(GroupFailed(failure=UnauthorizedPerson()))
    return result

# A real selected provider; native readiness and authority are checked per call.
from typing import Callable, Literal, overload
from .contracts import SequenceValue,CapabilitySelection
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
