# SPDX-License-Identifier: MIT OR Apache-2.0
"""Atomic owned imports composed through the existing protected group executor."""
import base64,json
from hashlib import sha256
from uuid import uuid4
from .contracts import ABSENT,ExactArtifact,MapValue,MapEntry,TextValue,NullValue,ProfilePin,SelectedMutationConfiguration
from .execution import Ok,Error,ExecutionFailure
from .imports import (OwnedImportInput,OwnedObjectImportRecord,OwnedEdgeImportRecord,ImportInvalid,ImportExecutionFailed,
    ImportReported,ImportReport,ImportCounts,ImportCreated,ImportSkipped,ImportRejected,PendingBatch,RolledBackBatch)
from .groups import (AuthoredValue,CreateObject,CreateEdge,RootlessOwnership,OwnedOwnership,StoredObjectReference,
    AliasObjectReference,NullOrderKey,TextOrderKey,RequestNone,GroupSuccess)
from ._group_runtime import GroupRuntimeContext,apply_group,_wire,_bytes,_artifact,_identity
from ._import_runtime import _cell,_group_refusal_state,_RecordRefused,_DIAGNOSTIC
from ._acceptance_json import decode_acceptance_json
from ._catalog_report_semantics import canonical_numeric_free
from .psycopg_host import _HostOperationReservation
from .preparation import CatalogDocument


def _payload(record,metadata,resolve,index):
    value=decode_acceptance_json(base64.b64decode(record.payload.bytes_base64,validate=True))
    final='ownership' if type(record) is OwnedObjectImportRecord else 'orderKey'
    if type(value) is not dict or set(value)-{'interfaceVersion','kind','values','source',final} or value.get('interfaceVersion')!='truss-owned-import-payload/0.1.0' or value.get('kind')!=record.kind or type(value.get('values')) is not list:
        raise ValueError('Closed owned import payload required')
    values=tuple(AuthoredValue(name=v['name'],value=_cell(v['value'],containers=True,recursive=True)) for v in value['values'])
    if len(values)>1024 or len({v.name for v in values})!=len(values) or any(set(v)!={'name','value'} for v in value['values']):raise ValueError('Unique original values required')
    if 'source' in value:
        source=value['source']
        if type(source) is not dict or set(source)!={'kind','entries'} or source['kind']!='map' or type(source['entries']) is not list:raise ValueError('Exact source map required')
        entries=tuple(MapEntry(key=e['key'],value=_cell(e['value'])) for e in source['entries'])
        if len({e.key for e in entries})!=len(entries) or any(set(e)!={'key','value'} for e in source['entries']):raise ValueError('Unique source members required')
        if any(e.key in ('author','at','system') and not(type(e.value) is NullValue or type(e.value) is TextValue and e.value.kind=='string') for e in entries):raise ValueError('Known source facts require string or null')
    if type(record) is OwnedObjectImportRecord:
        for field in metadata['primaryFields']:
            if not any(v.name==field['name'] and _wire(v.value)==field['value'] for v in values):raise ValueError('Original primary payload agreement required')
        ownership=value.get('ownership')
        if ownership=={'state':'rootless'}:selected=RootlessOwnership()
        elif type(ownership) is dict and set(ownership)=={'state','root'} and ownership['state']=='owned':selected=OwnedOwnership(root=resolve(ownership['root'],index))
        else:raise ValueError('Explicit original ownership required')
        return CreateObject(type_definition_pin=metadata['definitionPin'],values=values,ownership=selected,alias='import-'+str(index))
    order=value.get('orderKey')
    if order=={'state':'null'}:order_key=NullOrderKey()
    elif type(order) is dict and set(order)=={'state','text'} and order['state']=='text':order_key=TextOrderKey(text=order['text'])
    else:raise ValueError('Exact original edge order key required')
    return CreateEdge(relationship_definition_pin=record.identity.relationship_definition_pin,
        source=resolve(record.identity.source,index),target=resolve(record.identity.target,index),values=values,order_key=order_key)


def run_owned_import(host,transaction,input,documents,manifest,digest,pin_cursor,*,bun_executable='bun'):
    if type(input) is not OwnedImportInput or type(documents) is not tuple or any(type(d) is not CatalogDocument for d in documents):
        return ImportInvalid(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"shape"}'))
    try:
        original=canonical_numeric_free(_wire(input))
        if len(input.records)>1024 or len(original)>8388608 or type(input.asserted_origin) is not MapValue or not 1<=len(input.load_id.encode())<=4096 or '\0' in input.load_id:raise ValueError('Import envelope limits')
        if len({e.key for e in input.asserted_origin.entries})!=len(input.asserted_origin.entries) or any(e.key=='x-load-id' or not(type(e.value) is NullValue or type(e.value) is TextValue and e.value.kind=='string') for e in input.asserted_origin.entries):raise ValueError('Exact asserted origin required')
        for record in input.records:
            if type(record) not in (OwnedObjectImportRecord,OwnedEdgeImportRecord):raise ValueError('Owned import records required')
            raw=base64.b64decode(record.payload.bytes_base64,validate=True)
            if not 1<=len(raw)<=1048576 or sha256(raw).hexdigest()!=record.payload.sha256:raise ValueError('Original payload integrity')
        sources={d.document_id:d.content for d in documents}
        if len(sources)!=len(documents) or any(type(r) is OwnedObjectImportRecord and r.identity.type.owner.document_id not in sources for r in input.records):raise ValueError('Original caller-known documents required')
    except (ValueError,TypeError,AttributeError,UnicodeError):
        return ImportInvalid(diagnostic_profile=_DIAGNOSTIC,diagnostic=_artifact(b'{"code":"envelope"}'))
    batch_id=uuid4().hex;context=[None];entries=[];first_objects={};operation_indices={};outcomes=[];known=[None];failed_index=[None]
    def native_context(cursor):
        cursor.execute('SELECT truss.import_context(%s,%s)',(manifest['releaseId'],digest),prepare=False)
        return json.loads(bytes(cursor.fetchone()[0]))
    def key(cursor,selection,cache):
        payload=_bytes(selection if type(selection) is dict else _wire(selection))
        if payload not in cache:
            cursor.execute('SELECT truss.runtime_owned_import_reference(%s,%s,%s)',(payload,manifest['releaseId'],digest),prepare=False)
            cache[payload]=cursor.fetchone()[0]
        return cache[payload]
    def envelope(identity):return _bytes({'profile':context[0]['ownedImportProfile'],'identity':_wire(identity)})
    def finish_authority(cursor,selected_outcomes):
        if native_context(cursor)!=context[0]:raise ValueError('Original import context changed')
        for index,record in enumerate(input.records):
            item=selected_outcomes[index]
            identity=item.identity if type(item) in (ImportCreated,ImportSkipped) and item.identity is not ABSENT else None
            cursor.execute('SELECT truss.import_report_record_authority(%s,%s,%s,%s)',
                (_bytes({'originalIdentity':{'profile':context[0]['ownedImportProfile'],'identity':_wire(record.identity)},'outcomeIdentity':None if identity is None else _wire(identity)}),record.kind,manifest['releaseId'],digest),prepare=False)
            cursor.fetchone()
    def execute(cursor,observed):
        pin_cursor(cursor);context[0]=native_context(cursor);c=context[0]
        # Reuse identical selected references only inside this protected
        # transaction operation. No authorization decision survives the call.
        key_cache={}
        if any(_wire(value)!=c[name] for value,name in ((input.layout_profile,'layoutProfile'),(input.import_profile,'ownedImportProfile'),(input.value_profile,'valueProfile'),(input.catalog,'catalog'))) or any(_wire(r.payload_profile)!=c['ownedImportPayloadProfile'] for r in input.records):raise ValueError('Selected original owned import context required')
        cursor.execute('SELECT pg_current_xact_id()::text',prepare=False);transaction_id='truss-pending-transaction:'+c['sourceEpoch']+':'+cursor.fetchone()[0]
        # Resolve identities across the input before decoding any replacement.
        for index,record in enumerate(input.records):
            if type(record) is OwnedObjectImportRecord:
                cursor.execute('SELECT truss.import_object_identity(%s,%s,NULL,%s,%s)',(envelope(record.identity),sources[record.identity.type.owner.document_id],manifest['releaseId'],digest),prepare=False)
                metadata=json.loads(bytes(cursor.fetchone()[0]));route=key(cursor,record.identity,key_cache)
                entry={'metadata':metadata,'route':route}
                if metadata['state']=='eligible':
                    if route['keyIdentity'] in first_objects:entry['duplicate']=first_objects[route['keyIdentity']]
                    else:first_objects[route['keyIdentity']]=index
            else:
                source=key(cursor,record.identity.source,key_cache);target=key(cursor,record.identity.target,key_cache)
                if source['identity'] is not None and target['identity'] is not None:
                    selected={'relationshipDefinitionPin':record.identity.relationship_definition_pin,'source':source['identity'],'target':target['identity']}
                    cursor.execute('SELECT truss.import_edge_identity(%s,%s,%s)',(_bytes({'profile':c['ownedImportProfile'],'identity':selected}),manifest['releaseId'],digest),prepare=False)
                    metadata=json.loads(bytes(cursor.fetchone()[0]))
                else:metadata={'state':'eligible'}
                entry={'metadata':metadata,'source':source,'target':target}
            entries.append(entry)
        def resolve(selection,index):
            route=key(cursor,selection,key_cache)
            if route['identity'] is not None:return StoredObjectReference(identity=_identity(route['identity']))
            prior=first_objects.get(route['keyIdentity'])
            if prior is None:raise ValueError('Referenced primary identity is missing or reserved')
            if prior>=index or prior not in operation_indices:raise ValueError('References require an earlier eligible object')
            return AliasObjectReference(alias='import-'+str(prior))
        operations=[];edge_routes={}
        for index,(record,entry) in enumerate(zip(input.records,entries)):
            metadata=entry['metadata']
            if metadata['state']=='skipped':continue
            if 'duplicate' in entry:continue
            if type(record) is OwnedEdgeImportRecord:
                route=(record.identity.relationship_definition_pin,entry['source']['keyIdentity'],entry['target']['keyIdentity'])
                if route in edge_routes:entry['duplicate']=edge_routes[route];continue
                edge_routes[route]=index
            failed_index[0]=index;known[0]='invalid_payload'
            try:operation=_payload(record,metadata,resolve,index)
            except (ValueError,TypeError,KeyError,AttributeError):raise _RecordRefused('Atomic owned import payload or dependency refused',native_state='22023')
            operation_indices[index]=len(operations);operations.append(operation)
        known[0]=None;failed_index[0]=None;created={}
        if operations:
            group=GroupRuntimeContext(layout_profile=input.layout_profile,mutation_profile=ProfilePin(**c['mutationProfile']),value_profile=input.value_profile,
                request_fingerprint_profile=ProfilePin(**c['requestFingerprintProfile']),authorized_scope_identity=c['authorizedScopeIdentity'],source_epoch=c['sourceEpoch'],history_profile=c['historyProfile'])
            origin=MapValue(entries=input.asserted_origin.entries+(MapEntry(key='x-load-id',value=TextValue(kind='string',text=input.load_id)),))
            capture=[]
            applied=apply_group(host,transaction,group.input(tuple(operations),origin),RequestNone(),documents,manifest,digest,pin_cursor,bun_executable=bun_executable,_cursor=cursor,_attempt_capture=capture)
            if not isinstance(applied,Ok) or not isinstance(applied.value,GroupSuccess):
                raise _RecordRefused('Atomic owned import group refused',native_state=_group_refusal_state(applied.value) if isinstance(applied,Ok) else None)
            source_records=[]
            for index,operation_index in sorted(operation_indices.items()):
                result=applied.value.response.semantic.results[operation_index]
                original_record=_bytes(_wire(input.records[index]))
                source_records.append({'operationIndex':operation_index,
                    'originalRecordBase64':base64.b64encode(original_record).decode('ascii')})
                created[index]=result
            if source_records:
                cursor.execute('SELECT truss.runtime_owned_import_record_sources(%s::uuid,%s::jsonb,%s)',
                    (capture[0],_bytes(source_records).decode('utf8'),input.load_id),prepare=False);cursor.fetchone()
        for index,entry in enumerate(entries):
            metadata=entry['metadata']
            if metadata['state']=='skipped':outcomes.append(ImportSkipped(input_index=str(index),batch_id=batch_id,reason=metadata['reason'],identity=_identity(metadata['identity']) if 'identity' in metadata else ABSENT))
            elif 'duplicate' in entry:outcomes.append(ImportSkipped(input_index=str(index),batch_id=batch_id,reason='live_identity',identity=created[entry['duplicate']].identity))
            else:outcomes.append(ImportCreated(input_index=str(index),batch_id=batch_id,identity=created[index].identity,version=created[index].version))
        finish_authority(cursor,outcomes)
        return transaction_id
    def report(batch,selected_outcomes):
        c=context[0];selected=c['selectedConfiguration']
        configuration=SelectedMutationConfiguration(source_epoch=selected['sourceEpoch'],installation_id=selected['installationId'],generation=selected['generation'],
            key_reuse=selected['keyReuse'],journal_mode=selected['journalMode'],configuration_profile=ProfilePin(**selected['configurationProfile']),installed_producer_inventory_sha256=selected['installedProducerInventorySha256'])
        counts=ImportCounts(created_committed='0',created_pending=str(sum(type(o) is ImportCreated for o in selected_outcomes)),created_rolled_back='0',created_commit_unknown='0',created_transaction_unresolved='0',attempt_unknown='0',skipped=str(sum(type(o) is ImportSkipped for o in selected_outcomes)),rejected=str(sum(type(o) is ImportRejected for o in selected_outcomes)),unprocessed='0')
        result=ImportReport(attempt_id=batch_id,input_count=str(len(input.records)),executed_catalog_revision=c['catalog']['revision'],import_profile=input.import_profile,selected_configuration=configuration,
            input_sha256=sha256(b'truss-canonical/0.1.0\ntruss-owned-import-input/0.1.0\n'+original).hexdigest(),execution='host_adopted',status='processed',outcomes=tuple(selected_outcomes),batches=() if not input.records else (batch,),unprocessed_indices=(),counts=counts)
        if len(_bytes(_wire(result)))>8388608:return ImportExecutionFailed(error=ExecutionFailure('execution_obligation','Atomic import report exceeds capacity'),report=None)
        return ImportReported(report=result)
    with _HostOperationReservation(host):
        result=host._run_operation(transaction,execute)
        if isinstance(result,Ok):
            batch=PendingBatch(batch_id=batch_id,input_indices=tuple(str(i) for i in range(len(input.records))),host_transaction_id=result.value) if input.records else None
            return report(batch,outcomes)
        failure=result.error;attempt=host._custody.last_attempt
        code=known[0] or {'22023':'invalid','23505':'conflict','42501':'unauthorized','0A000':'unsupported_profile','P1004':'missing_reference','P1005':'dependencies'}.get(failure.sql_state)
        if code is None or len(entries)!=len(input.records) or failure.code!='execution_obligation' or attempt.phase!='contained' or host._custody.quarantined:
            return ImportExecutionFailed(error=failure,report=None)
        rejected=[]
        for index,entry in enumerate(entries):
            metadata=entry['metadata']
            if metadata['state']=='skipped':rejected.append(ImportSkipped(input_index=str(index),batch_id=batch_id,reason=metadata['reason'],identity=_identity(metadata['identity']) if 'identity' in metadata else ABSENT))
            else:rejected.append(ImportRejected(input_index=str(index),batch_id=batch_id,code=code if failed_index[0] is None or index==failed_index[0] else 'atomic_batch_rejected'))
        released=host._run_operation(transaction,lambda cursor,observed:(pin_cursor(cursor),finish_authority(cursor,rejected)))
        if isinstance(released,Error):return ImportExecutionFailed(error=released.error,report=None)
        batch=RolledBackBatch(batch_id=batch_id,input_indices=tuple(str(i) for i in range(len(input.records))),rollback_evidence_sha256=sha256(_bytes({'batchId':batch_id,'error':_wire(failure),'phase':attempt.phase})).hexdigest())
        return report(batch,rejected)
