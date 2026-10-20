# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public group composition over protected native calls and original UMF encoding."""
from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
import base64
import json
import re
import uuid
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


def _closed_object(value, fields, description):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError(f'Exact native {description} required')
    return value


def _decode_group_result(raw):
    """Decode a byte-bounded, duplicate-free JSON result with no number tokens."""
    def unique_object(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate native group result member')
            result[key]=value
        return result
    def reject_number(_token):
        raise ValueError('Numeric native group result token')
    try:
        return json.loads(raw,object_pairs_hook=unique_object,parse_int=reject_number,
            parse_float=reject_number,parse_constant=reject_number)
    except (ValueError,UnicodeError,TypeError,RecursionError):
        raise ValueError('Valid exact native group result required') from None


def _native_receipt_observation(encoded, digest, token, durability):
    """Validate the exact observation shape emitted by object_group_finish."""
    if (type(encoded) is not str or len(encoded) > 1_398_104
            or type(digest) is not str or len(digest) != 64
            or any(char not in '0123456789abcdef' for char in digest)):
        raise ValueError('Bounded original native receipt observation required')
    try:
        observation_bytes=base64.b64decode(encoded,validate=True)
    except (ValueError,UnicodeError,base64.binascii.Error):
        raise ValueError('Canonical native receipt observation required') from None
    if (base64.b64encode(observation_bytes).decode('ascii') != encoded
            or sha256(observation_bytes).hexdigest() != digest):
        raise ValueError('Original native receipt observation digest required')
    from ._acceptance_json import decode_acceptance_json
    observation=_closed_object(decode_acceptance_json(observation_bytes),
        ('profile','sourceEpoch','observingXid','originalWriterXid','receiptStorageId',
         'receiptGeneration','receiptSha256','actorOid','actor','scopeIdentity',
         'releaseId','releaseSha256','basis'),'receipt observation')
    text_fields=('profile','sourceEpoch','observingXid','originalWriterXid','receiptStorageId',
        'receiptGeneration','receiptSha256','actorOid','actor','scopeIdentity',
        'releaseId','releaseSha256','basis')
    if any(type(observation[name]) is not str or not observation[name]
           or '\0' in observation[name] or len(observation[name].encode('utf-8')) > 4096
           for name in text_fields):
        raise ValueError('Complete native receipt observation fields required')
    if observation['profile'] != 'truss-native-create-replay-observation/0.1':
        raise ValueError('Supported native receipt observation profile required')
    if (not re.fullmatch('[1-9][0-9]*',observation['observingXid'])
            or not re.fullmatch('[1-9][0-9]*',observation['originalWriterXid'])
            or not re.fullmatch('[1-9][0-9]*',observation['receiptStorageId'])
            or not re.fullmatch('0|[1-9][0-9]*',observation['receiptGeneration'])
            or not re.fullmatch('[a-f0-9]{64}',observation['receiptSha256'])
            or not re.fullmatch('[1-9][0-9]*',observation['actorOid'])
            or int(observation['actorOid']) > 4294967295
            or not re.fullmatch('[a-f0-9]{64}',observation['releaseSha256'])):
        raise ValueError('Canonical native receipt observation identifiers required')
    if (int(observation['observingXid']) > 18446744073709551615
            or int(observation['originalWriterXid']) > 18446744073709551615
            or int(observation['receiptStorageId']) > 9223372036854775807
            or int(observation['receiptGeneration']) > 9223372036854775807):
        raise ValueError('Native receipt observation identifier range required')
    locator=decode_receipt_position(token)
    if (observation['sourceEpoch'] != locator.source_epoch
            or observation['originalWriterXid'] != locator.writer_xid
            or observation['receiptStorageId'] != locator.receipt_storage_row_id):
        raise ValueError('Original native receipt locator correspondence required')
    same_transaction=observation['observingXid'] == observation['originalWriterXid']
    expected_basis='same_transaction' if durability=='pending' else 'committed_receipt'
    if (observation['basis'] != expected_basis
            or same_transaction != (durability == 'pending')):
        raise ValueError('Native receipt durability correspondence required')
    return observation_bytes


def _result(raw: bytes, *, request_present: bool):
    if type(raw) is not bytes or len(raw)>18_500_000:
        raise ValueError('Bounded original native group result required')
    value=_decode_group_result(raw)
    if type(value) is not dict or type(value.get('outcome')) is not str:
        raise ValueError('Original native group outcome required')
    if value['outcome']=='unavailable':
        _closed_object(value,('outcome','reason'),'group unavailability')
        if value['reason'] not in ('profile','receipt','receipt_expired','observation','resource'):
            raise ValueError('Supported native group unavailability required')
        if not request_present and value['reason'] in ('receipt','receipt_expired'):
            raise ValueError('Request-free native result cannot claim receipt availability')
        return GroupUnavailable(reason=value['reason'])
    if value['outcome']=='failed':
        if value.get('code')=='precondition_failed':
            _closed_object(value,('outcome','code','failures'),'precondition result')
            rules=('object_exists','key_absent','property_equals','relationship_absent','relationship_count')
            if type(value['failures']) is not list or not value['failures']:
                raise ValueError('Nonempty original precondition failures required')
            for failure in value['failures']:
                _closed_object(failure,('conditionId','reason','rule'),'precondition failure')
                if (type(failure['conditionId']) is not str or not failure['conditionId']
                        or type(failure['reason']) is not str or not failure['reason']
                        or failure['rule'] not in rules):
                    raise ValueError('Original typed precondition failure required')
        else:
            required_fields=('outcome','code','nativeState')
            allowed_fields=(set(required_fields),set(required_fields)|{'operationIndex'})
            if type(value) is not dict or set(value) not in allowed_fields:
                raise ValueError('Exact native group failure required')
            native_codes={'invalid_input':'22023','key_conflict':'23505','request_conflict':'P1001',
                'expected_version':'P1003','not_found':'P1004','dependencies':'P1005',
                'unauthorized_person':'42501'}
            if (value.get('code') not in native_codes
                    or value['nativeState'] != native_codes[value['code']]):
                raise ValueError('Original native group failure mapping required')
            if 'operationIndex' in value and (type(value['operationIndex']) is not str
                    or not re.fullmatch('0|[1-9][0-9]*',value['operationIndex'])
                    or int(value['operationIndex']) > 1023):
                raise ValueError('Canonical original native operation ordinal required')
        evidence=_artifact(raw)
        if value['code']=='precondition_failed':
            failures=tuple(FailedPrecondition(condition_id=v['conditionId'],reason=v['reason'],rule=v['rule']) for v in value['failures'])
            if not failures:raise ValueError('Nonempty failed preconditions required')
            return GroupFailed(failure=PreconditionFailed(failures=(failures[0],*failures[1:])))
        if value['code']=='invalid_input' and 'operationIndex' not in value:
            return GroupFailed(failure=InvalidGroupInput(diagnostic_profile=_DIAGNOSTIC,diagnostic=evidence))
        if value['code']=='unauthorized_person':return GroupFailed(failure=UnauthorizedPerson())
        if value['code']=='request_conflict':
            if not request_present:raise ValueError('Request-free native result cannot claim a request conflict')
            return GroupFailed(failure=RequestConflict(diagnostic_profile=_DIAGNOSTIC,diagnostic=evidence))
        if value['code'] not in ('invalid_input','key_conflict','expected_version','not_found','dependencies'):
            raise ValueError('Selected native operation failure code required')
        return GroupFailed(failure=GroupOperationFailure(operation_index=value.get('operationIndex',ABSENT),
            operation_code=value['code'],error_profile=_DIAGNOSTIC,inner_error=evidence))
    if value['outcome']!='success':raise ValueError('Supported native group outcome required')
    disposition=value.get('disposition')
    if disposition=='applied':
        _closed_object(value,('outcome','disposition','durability','semantic','receiptToken','attemptId'),'applied group result')
        attempt_id=value['attemptId']
        try:
            canonical_attempt_id=type(attempt_id) is str and str(uuid.UUID(attempt_id)) == attempt_id
        except (ValueError, AttributeError):
            canonical_attempt_id=False
        if value['durability']!='pending' or not canonical_attempt_id:
            raise ValueError('Original pending group attempt required')
        if type(value['semantic']) is not dict or set(value['semantic'])!={'interfaceVersion','executedCatalogRevision','layoutProfile','mutationProfile','results','aliases'} or value['semantic']['interfaceVersion']!='truss-group-result/0.1.0':
            raise ValueError('Complete original semantic result required')
        token_value=value['receiptToken']
        if request_present:
            if type(token_value) is not str:raise ValueError('Original request receipt token required')
            decode_receipt_position(token_value)
            token=token_value
        else:
            if token_value is not None:raise ValueError('Request-free native result cannot carry a receipt token')
            token=ABSENT
        return GroupSuccess(response=AppliedPending(semantic=_semantic(value['semantic']),receipt_token=token))
    if disposition!='replayed':raise ValueError('Supported native group disposition required')
    _closed_object(value,('outcome','disposition','durability','semantic','receiptToken','observationBase64','observationSha256'),'replayed group result')
    if not request_present or value['durability'] not in ('pending','committed'):
        raise ValueError('Original request replay durability required')
    if type(value['receiptToken']) is not str:raise ValueError('Original request replay token required')
    if type(value['semantic']) is not dict or set(value['semantic'])!={'interfaceVersion','executedCatalogRevision','layoutProfile','mutationProfile','results','aliases'} or value['semantic']['interfaceVersion']!='truss-group-result/0.1.0':
        raise ValueError('Complete original semantic result required')
    semantic=_semantic(value['semantic'])
    observation=_native_receipt_observation(value['observationBase64'],value['observationSha256'],value['receiptToken'],value['durability'])
    evidence=_artifact(observation)
    if value['durability']=='pending':
        return GroupSuccess(response=SameTransactionReplay(semantic=semantic,
            replay=SameTransactionReplayEvidence(observation_profile=_OBSERVATION,evidence=evidence),receipt_token=value['receiptToken']))
    if value['durability']=='committed':
        return GroupSuccess(response=CommittedReceiptReplay(semantic=semantic,
            replay=CommittedReceiptReplayEvidence(observation_profile=_OBSERVATION,evidence=evidence),receipt_token=value['receiptToken']))
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
    if type(input.preconditions) is not tuple:
        return Ok(GroupFailed(failure=InvalidGroupInput(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"preconditions_shape"}'))))
    if (not 1<=len(input.operations)<=(1024 if selected_owned else 128)
        or len(input.preconditions)>(3072 if selected_owned else 128)
        or any(len(op.values if type(op) in (CreateObject,CreateEdge) else op.set if type(op) in (UpdateObject,UpdateEdge) else ())>1024 for op in input.operations)):
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
        result=_result(raw,request_present=type(request) is RequestPresent)
        if (_attempt_capture is not None and type(result) is GroupSuccess
                and type(result.response) is AppliedPending):
            decoded=_decode_group_result(raw)
            _attempt_capture.append(decoded['attemptId'])
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
