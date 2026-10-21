# SPDX-License-Identifier: MIT OR Apache-2.0
"""Strict adapters for native module-audit grants and import-load pages."""
from __future__ import annotations

import json
import re

from .execution import Error, Ok
from .load_audit import (AuditAccessUpdated, LoadAuditEntry, LoadAuditPage,
                         LoadAuditCursor, LoadAuditListingCursor, LoadAuditListingEnd,
                         LoadAuditChunkSummary, LoadAuditInvocationSummary,
                         LoadAuditUnavailable, ModuleAuditGrant,
                         MutationGroupAuditEntry, MutationGroupAuditPage,
                         MutationGroupAuditListingCursor,MutationGroupAuditListingEnd)

_SHA = re.compile(r'[0-9a-f]{64}\Z')
_INDEX = re.compile(r'(?:0|[1-9][0-9]{0,3})\Z')
_UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate native import audit member')
        result[key] = value
    return result


def _no_numbers(_token):
    raise ValueError('Numeric native import audit token')


def _json(raw: bytes):
    if type(raw) is not bytes or not 1 <= len(raw) <= 1_048_576:
        raise ValueError('Bounded native import audit response required')
    return json.loads(raw, object_pairs_hook=_unique_object, parse_int=_no_numbers,
                      parse_float=_no_numbers, parse_constant=_no_numbers)


def _decode_grant(raw: bytes, grant: ModuleAuditGrant) -> AuditAccessUpdated:
    value = _json(raw)
    if type(value) is not dict or value != {'outcome': 'granted'}:
        raise ValueError('Exact native module audit grant response required')
    return AuditAccessUpdated(document_id=grant.document_id,
                              module_id=grant.module_id,
                              auditor_role=grant.auditor_role)


def _decode_page(raw: bytes) -> LoadAuditPage:
    value = _json(raw)
    expected = {'outcome', 'invocationId', 'loadId', 'assertedOriginSha256', 'nativeActor',
                'nativeActorName', 'observedAt', 'createdCount', 'skippedCount', 'rejectedCount',
                'loadCreatedCount', 'loadSkippedCount', 'loadRejectedCount', 'inputSha256',
                'inputCount', 'totalChunks', 'observedChunks', 'state', 'entries', 'nextChunk'}
    if type(value) is not dict or set(value) != expected or value['outcome'] != 'page':
        raise ValueError('Exact native load audit page required')
    if (type(value['invocationId']) is not str or not _UUID.fullmatch(value['invocationId'])
            or type(value['loadId']) is not str or not value['loadId']
            or type(value['nativeActor']) is not str
            or not re.fullmatch(r'[1-9][0-9]{0,9}',value['nativeActor'])
            or int(value['nativeActor'])>4294967295
            or type(value['nativeActorName']) is not str or not value['nativeActorName']
            or len(value['nativeActorName'].encode('utf8'))>256
            or not _canonical_observed_at(value['observedAt'])
            or not _SHA.fullmatch(value['assertedOriginSha256'])
            or not _SHA.fullmatch(value['inputSha256'])):
        raise ValueError('Canonical original load audit identity required')
    if (type(value['inputCount']) is not str or not re.fullmatch(r'(?:0|[1-9][0-9]{0,3})', value['inputCount'])
            or int(value['inputCount']) > 1024
            or type(value['totalChunks']) is not str or not re.fullmatch(r'[1-9][0-9]{0,3}', value['totalChunks'])
            or int(value['totalChunks']) > 1024
            or type(value['observedChunks']) is not list
            or any(type(item) is not str or not re.fullmatch(r'(?:0|[1-9][0-9]{0,3})', item)
                   or int(item) > 1023
                   for item in value['observedChunks'])
            or len(set(value['observedChunks'])) != len(value['observedChunks'])
            or value['state'] not in ('partial', 'complete')
            or value['nextChunk'] is not None and
              (type(value['nextChunk']) is not str or not re.fullmatch(r'(?:0|[1-9][0-9]{0,3})', value['nextChunk'])
               or int(value['nextChunk']) >= int(value['totalChunks']))):
        raise ValueError('Canonical import load chunk basis required')
    count_fields=('createdCount','skippedCount','rejectedCount')
    if any(type(value[key]) is not str or not re.fullmatch(r'(?:0|[1-9][0-9]{0,3})',value[key])
           or int(value[key])>128 for key in count_fields):
        raise ValueError('Canonical current chunk outcome counts required')
    aggregate=(value['loadCreatedCount'],value['loadSkippedCount'],value['loadRejectedCount'])
    if value['state']=='complete':
        if any(type(item) is not str or not re.fullmatch(r'(?:0|[1-9][0-9]{0,3})',item)
               or int(item)>1024 for item in aggregate):
            raise ValueError('Complete import aggregate counts required')
    elif any(item is not None for item in aggregate):
        raise ValueError('Partial import cannot claim complete aggregate counts')
    if type(value['entries']) is not list or len(value['entries']) > 128:
        raise ValueError('Bounded complete chunk entries required')
    entries = []
    seen = set()
    for item in value['entries']:
        fields = {'inputIndex', 'outcome', 'recordKind', 'identity',
                  'payloadProfile', 'payloadSha256', 'groupAttemptId'}
        if type(item) is not dict or set(item) != fields:
            raise ValueError('Closed metadata-only load audit entry required')
        if (type(item['inputIndex']) is not str or not _INDEX.fullmatch(item['inputIndex'])
                or int(item['inputIndex']) > 1023
                or item['inputIndex'] in seen
                or item['outcome'] not in ('created', 'skipped', 'rejected')
                or item['recordKind'] not in ('object', 'edge', 'unknown')
                or type(item['identity']) is not dict
                or type(item['payloadProfile']) is not dict
                or type(item['payloadSha256']) is not str
                or item['payloadSha256'] and not _SHA.fullmatch(item['payloadSha256'])
                or item['groupAttemptId'] is not None and type(item['groupAttemptId']) is not str
                or item['outcome'] == 'created' and not item['groupAttemptId']
                or item['outcome'] != 'created' and item['groupAttemptId'] is not None):
            raise ValueError('Canonical metadata-only load audit entry required')
        if item['recordKind'] == 'unknown':
            if (item['identity'] != {'kind': 'unknown'} or item['payloadProfile'] != {}
                    or item['payloadSha256']):
                raise ValueError('Unknown load identity cannot carry unqualified content')
        elif item['recordKind'] == 'object':
            identity = item['identity']
            if (set(identity) != {'kind', 'typeId', 'definitionPin', 'owner',
                                  'keyNumber', 'keyDefinitionPin'}
                    or identity['kind'] != 'object'
                    or any(type(identity[key]) is not str or not identity[key]
                           for key in ('typeId', 'definitionPin', 'keyNumber', 'keyDefinitionPin'))
                    or type(identity['owner']) is not dict
                    or set(identity['owner']) != {'documentId', 'moduleId'}
                    or any(type(identity['owner'][key]) is not str or not identity['owner'][key]
                           for key in ('documentId', 'moduleId'))):
                raise ValueError('Closed object identity metadata required')
        else:
            identity = item['identity']
            if (set(identity) != {'kind', 'relationshipDefinitionPin', 'source', 'target'}
                    or identity['kind'] != 'edge'
                    or type(identity['relationshipDefinitionPin']) is not str
                    or not identity['relationshipDefinitionPin']):
                raise ValueError('Closed edge identity metadata required')
            for endpoint in ('source', 'target'):
                part = identity[endpoint]
                if (type(part) is not dict or set(part) != {'id', 'typeId', 'definitionPin', 'owner'}
                        or any(type(part[key]) is not str or not part[key]
                               for key in ('id', 'typeId', 'definitionPin'))
                        or type(part['owner']) is not dict
                        or set(part['owner']) != {'documentId', 'moduleId'}
                        or any(type(part['owner'][key]) is not str or not part['owner'][key]
                               for key in ('documentId', 'moduleId'))):
                    raise ValueError('Closed edge endpoint metadata required')
        seen.add(item['inputIndex'])
        entries.append(LoadAuditEntry(input_index=item['inputIndex'],
            outcome=item['outcome'], record_kind=item['recordKind'],
            identity=item['identity'], payload_profile=item['payloadProfile'],
            payload_sha256=item['payloadSha256'], group_attempt_id=item['groupAttemptId']))
    next_cursor = (None if value['nextChunk'] is None else
                   LoadAuditCursor(invocation_id=value['invocationId'],
                                   chunk_index=value['nextChunk']))
    return LoadAuditPage(invocation_id=value['invocationId'], load_id=value['loadId'],
        asserted_origin_sha256=value['assertedOriginSha256'], native_actor=value['nativeActor'],
        native_actor_name=value['nativeActorName'],observed_at=value['observedAt'],
        created_count=value['createdCount'],skipped_count=value['skippedCount'],
        rejected_count=value['rejectedCount'],load_created_count=value['loadCreatedCount'],
        load_skipped_count=value['loadSkippedCount'],load_rejected_count=value['loadRejectedCount'],
        input_sha256=value['inputSha256'], input_count=value['inputCount'],
        total_chunks=value['totalChunks'], observed_chunks=tuple(value['observedChunks']),
        state=value['state'], entries=tuple(entries), next_cursor=next_cursor)


def _decode_listing_cursor(value) -> LoadAuditListingCursor | None:
    if value is None:
        return None
    fields={'profile','installationId','sourceEpoch','releaseId','releaseSha256',
            'frontierXid','filtersSha256','afterObservedAt','afterInvocationId'}
    if type(value) is not dict or set(value) != fields or value.get('profile') != 'truss-import-load-audit-cursor/0.2':
        raise ValueError('Exact import audit listing cursor required')
    for name in ('installationId','sourceEpoch','releaseId'):
        if type(value[name]) is not str or not value[name] or len(value[name].encode('utf8')) > 256:
            raise ValueError('Bounded import audit listing identity required')
    for name in ('releaseSha256','filtersSha256'):
        if type(value[name]) is not str or not _SHA.fullmatch(value[name]):
            raise ValueError('Canonical import audit listing digest required')
    if (type(value['frontierXid']) is not str
            or not re.fullmatch(r'[1-9][0-9]{0,19}', value['frontierXid'])
            or int(value['frontierXid']) > 18446744073709551615
            or not _canonical_observed_at(value['afterObservedAt'])
            or type(value['afterInvocationId']) is not str or not _UUID.fullmatch(value['afterInvocationId'])):
        raise ValueError('Canonical import audit listing position required')
    return LoadAuditListingCursor(installation_id=value['installationId'],source_epoch=value['sourceEpoch'],
        release_id=value['releaseId'],release_sha256=value['releaseSha256'],frontier_xid=value['frontierXid'],
        filters_sha256=value['filtersSha256'],after_observed_at=value['afterObservedAt'],
        after_invocation_id=value['afterInvocationId'])


def _canonical_observed_at(value):
    if type(value) is not str or not re.fullmatch(
            r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z', value):
        return False
    from datetime import datetime
    try:
        datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        return False
    return True


def _valid_filter_time(value):
    if type(value) is not str or not re.fullmatch(
            r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})', value):
        return False
    from datetime import datetime
    try:
        datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError:
        return False
    return True


def _decode_load_audit_summary(value):
    expected={'outcome','invocationId','loadId','assertedOriginSha256','nativeActorOid',
        'nativeActorName','inputSha256','inputCount','totalChunks','observedChunkCount',
        'observedChunks','state','observedAtFrom','observedAtUntil','createdCount',
        'skippedCount','rejectedCount','chunks'}
    if (type(value) is not dict or value.get('outcome')!='summary'
            or set(value)!=expected|{'nextPageCursor'}):
        raise ValueError('Exact metadata-only load invocation summary required')
    if (type(value['invocationId']) is not str or not _UUID.fullmatch(value['invocationId'])
            or type(value['loadId']) is not str or not 1<=len(value['loadId'].encode('utf8'))<=4096
            or type(value['nativeActorOid']) is not str
            or not re.fullmatch(r'[1-9][0-9]{0,9}',value['nativeActorOid'])
            or int(value['nativeActorOid'])>4294967295
            or type(value['nativeActorName']) is not str or not value['nativeActorName']
            or len(value['nativeActorName'].encode('utf8'))>256
            or not _SHA.fullmatch(value['assertedOriginSha256'])
            or not _SHA.fullmatch(value['inputSha256'])
            or not _canonical_observed_at(value['observedAtFrom'])
            or not _canonical_observed_at(value['observedAtUntil'])
            or value['observedAtFrom']>value['observedAtUntil']):
        raise ValueError('Canonical load invocation identity and time range required')
    for field, maximum, minimum in (('inputCount',1024,0),('totalChunks',1024,1),
        ('observedChunkCount',1024,1),('createdCount',1024,0),('skippedCount',1024,0),
        ('rejectedCount',1024,0)):
        raw=value[field]
        if type(raw) is not str or not re.fullmatch(r'(?:0|[1-9][0-9]{0,3})',raw) or not minimum<=int(raw)<=maximum:
            raise ValueError('Canonical bounded load invocation count required')
    chunks=value['chunks'];observed=value['observedChunks']
    if (type(chunks) is not list or not 1<=len(chunks)<=1024
            or len(chunks)!=int(value['observedChunkCount'])
            or type(observed) is not list or len(observed)!=len(chunks)
            or value['state'] not in ('partial','complete')
            or int(value['observedChunkCount'])>int(value['totalChunks'])
            or value['state']=='complete' and int(value['observedChunkCount'])!=int(value['totalChunks'])
            or value['state']=='partial' and int(value['observedChunkCount'])==int(value['totalChunks'])):
        raise ValueError('Complete visible load chunk census required')
    decoded=[];seen=[]
    for item in chunks:
        fields={'chunkIndex','observedAt','createdCount','skippedCount','rejectedCount'}
        if type(item) is not dict or set(item)!=fields:
            raise ValueError('Closed load chunk summary required')
        index=item['chunkIndex']
        if (type(index) is not str or not re.fullmatch(r'(?:0|[1-9][0-9]{0,3})',index)
                or int(index)>=int(value['totalChunks']) or not _canonical_observed_at(item['observedAt'])):
            raise ValueError('Canonical load chunk position required')
        counts=[]
        for field in ('createdCount','skippedCount','rejectedCount'):
            raw=item[field]
            if type(raw) is not str or not re.fullmatch(r'(?:0|[1-9][0-9]{0,3})',raw) or int(raw)>1024:
                raise ValueError('Canonical load chunk count required')
            counts.append(int(raw))
        if sum(counts)>128:
            raise ValueError('Load chunk outcome counts exceed its input bound')
        decoded.append(LoadAuditChunkSummary(chunk_index=index,observed_at=item['observedAt'],
            created_count=item['createdCount'],skipped_count=item['skippedCount'],rejected_count=item['rejectedCount']))
        seen.append(index)
    if (len(set(seen))!=len(seen) or seen!=observed
            or [int(item) for item in observed]!=sorted(int(item) for item in observed)
            or sum(int(item.created_count) for item in decoded)!=int(value['createdCount'])
            or sum(int(item.skipped_count) for item in decoded)!=int(value['skippedCount'])
            or sum(int(item.rejected_count) for item in decoded)!=int(value['rejectedCount'])
            or int(value['createdCount'])+int(value['skippedCount'])+int(value['rejectedCount'])>int(value['inputCount'])
            or value['state']=='complete' and int(value['createdCount'])+int(value['skippedCount'])+int(value['rejectedCount'])!=int(value['inputCount'])
            or (value['state']=='complete'
                and [int(item) for item in observed]!=list(range(int(value['totalChunks']))))
            or min(item.observed_at for item in decoded)!=value['observedAtFrom']
            or max(item.observed_at for item in decoded)!=value['observedAtUntil']):
        raise ValueError('Load chunk census does not match the summary')
    return LoadAuditInvocationSummary(invocation_id=value['invocationId'],load_id=value['loadId'],
        asserted_origin_sha256=value['assertedOriginSha256'],native_actor_oid=value['nativeActorOid'],
        native_actor_name=value['nativeActorName'],input_sha256=value['inputSha256'],input_count=value['inputCount'],
        total_chunks=value['totalChunks'],observed_chunk_count=value['observedChunkCount'],
        observed_chunks=tuple(observed),state=value['state'],observed_at_from=value['observedAtFrom'],
        observed_at_until=value['observedAtUntil'],created_count=value['createdCount'],
        skipped_count=value['skippedCount'],rejected_count=value['rejectedCount'],chunks=tuple(decoded),
        next_page_cursor=_decode_listing_cursor(value.get('nextPageCursor')))


def _decode_listing_page(raw: bytes):
    value = _json(raw)
    if type(value) is not dict:
        raise ValueError('Exact import audit listing response required')
    if value.get('outcome') == 'end':
        if set(value) != {'outcome','nextPageCursor'} or value['nextPageCursor'] is not None:
            raise ValueError('Exact exhausted import audit listing required')
        return LoadAuditListingEnd()
    return _decode_load_audit_summary(value)


def _decode_mutation_page(raw: bytes) -> MutationGroupAuditPage:
    value = _json(raw)
    fields = {'outcome', 'attemptId', 'nativeActorOid', 'nativeActorName', 'assertedAction',
              'writerXid', 'observedAt', 'ownerScopes', 'operationCount', 'eventCount', 'entries'}
    if type(value) is not dict or set(value) != fields or value['outcome'] != 'page':
        raise ValueError('Exact whole mutation-group audit page required')
    if (type(value['attemptId']) is not str or not re.fullmatch(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', value['attemptId'])
            or type(value['nativeActorOid']) is not str
            or not re.fullmatch(r'[1-9][0-9]{0,9}',value['nativeActorOid'])
            or int(value['nativeActorOid'])>4294967295
            or type(value['nativeActorName']) is not str or not value['nativeActorName']
            or len(value['nativeActorName'].encode('utf8'))>256
            or not _canonical_observed_at(value['observedAt'])
            or value['assertedAction'] is not None and (type(value['assertedAction']) is not str
                or not 1 <= len(value['assertedAction'].encode('utf8')) <= 4096)
            or type(value['writerXid']) is not str or not re.fullmatch(r'[1-9][0-9]{0,18}', value['writerXid'])):
        raise ValueError('Canonical retained mutation-group identity required')
    for key, maximum in (('operationCount', 1024), ('eventCount', 4096)):
        item = value[key]
        if type(item) is not str or not re.fullmatch(r'(?:0|[1-9][0-9]{0,3})', item) or int(item) > maximum:
            raise ValueError('Bounded mutation-group census required')
    if type(value['entries']) is not list or len(value['entries']) != int(value['eventCount']):
        raise ValueError('Complete whole-group audit entries required')
    scopes=value['ownerScopes']
    if type(scopes) is not list or len(scopes)>4096:
        raise ValueError('Bounded mutation owner scopes required')
    normalized_scopes=[]
    for scope in scopes:
        if (type(scope) is not dict or set(scope)!={'documentId','moduleId'}
                or any(type(scope[key]) is not str or not 1<=len(scope[key].encode('utf8'))<=4096
                       for key in ('documentId','moduleId'))):
            raise ValueError('Qualified mutation owner scope required')
        normalized_scopes.append(scope)
    if len({(scope['documentId'],scope['moduleId']) for scope in normalized_scopes})!=len(normalized_scopes):
        raise ValueError('Duplicate mutation owner scope refused')
    entries = []
    allowed_ops = {'create', 'metadata', 'delete', 'property', 'rebind',
                   'create_object', 'update_object', 'delete_object',
                   'create_edge', 'update_edge', 'delete_edge'}
    for item in value['entries']:
        if (type(item) is not dict or set(item) != {'operationIndex', 'entityKind', 'entityId',
                'entityType', 'operation', 'observedAt'}
                or type(item['operationIndex']) is not str
                or not re.fullmatch(r'(?:0|[1-9][0-9]{0,3})', item['operationIndex'])
                or int(item['operationIndex']) >= int(value['operationCount'])
                or item['entityKind'] not in ('object', 'edge')
                or type(item['entityId']) is not str or not re.fullmatch(r'[1-9][0-9]{0,18}', item['entityId'])
                or type(item['entityType']) is not str or not re.fullmatch(r'[1-9][0-9]{0,9}', item['entityType'])
                or item['operation'] not in allowed_ops
                or type(item['observedAt']) is not str or not item['observedAt']):
            raise ValueError('Closed metadata-only mutation event required')
        entries.append(MutationGroupAuditEntry(operation_index=item['operationIndex'],
            entity_kind=item['entityKind'], entity_id=item['entityId'], entity_type=item['entityType'],
            operation=item['operation'], observed_at=item['observedAt']))
    return MutationGroupAuditPage(attempt_id=value['attemptId'], native_actor=value['nativeActorOid'],
        native_actor_name=value['nativeActorName'],asserted_action=value['assertedAction'],
        writer_xid=value['writerXid'],operation_count=value['operationCount'],
        event_count=value['eventCount'],entries=tuple(entries),observed_at=value['observedAt'],
        owner_scopes=tuple(normalized_scopes))


def _decode_mutation_listing_cursor(value) -> MutationGroupAuditListingCursor | None:
    if value is None:return None
    fields={'profile','installationId','sourceEpoch','releaseId','releaseSha256',
            'frontierXid','filtersSha256','afterObservedAt','afterAttemptId'}
    if type(value) is not dict or set(value)!=fields or value.get('profile')!='truss-mutation-group-audit-cursor/0.2':
        raise ValueError('Exact mutation audit listing cursor required')
    for name in ('installationId','sourceEpoch','releaseId'):
        if type(value[name]) is not str or not value[name] or len(value[name].encode('utf8'))>256:
            raise ValueError('Bounded mutation audit listing identity required')
    for name in ('releaseSha256','filtersSha256'):
        if type(value[name]) is not str or not _SHA.fullmatch(value[name]):
            raise ValueError('Canonical mutation audit listing digest required')
    if (type(value['frontierXid']) is not str
            or not re.fullmatch(r'[1-9][0-9]{0,19}',value['frontierXid'])
            or int(value['frontierXid'])>18446744073709551615
            or not _canonical_observed_at(value['afterObservedAt'])
            or type(value['afterAttemptId']) is not str or not _UUID.fullmatch(value['afterAttemptId'])):
        raise ValueError('Canonical mutation audit listing position required')
    return MutationGroupAuditListingCursor(installation_id=value['installationId'],source_epoch=value['sourceEpoch'],
        release_id=value['releaseId'],release_sha256=value['releaseSha256'],frontier_xid=value['frontierXid'],
        filters_sha256=value['filtersSha256'],after_observed_at=value['afterObservedAt'],after_attempt_id=value['afterAttemptId'])


def _decode_mutation_listing_page(raw: bytes):
    value=_json(raw)
    if type(value) is not dict:raise ValueError('Exact mutation audit listing response required')
    if value.get('outcome')=='end':
        if set(value)!={'outcome','nextPageCursor'} or value['nextPageCursor'] is not None:
            raise ValueError('Exact exhausted mutation audit listing required')
        return MutationGroupAuditListingEnd()
    if 'nextPageCursor' not in value:raise ValueError('Mutation audit listing continuation required')
    next_cursor=_decode_mutation_listing_cursor(value.pop('nextPageCursor'))
    page=_decode_mutation_page(json.dumps(value,separators=(',',':'),ensure_ascii=False).encode('utf8'))
    from dataclasses import replace
    return replace(page,next_page_cursor=next_cursor)


def _reason(error: Error) -> str | None:
    if error.error.code != 'execution_obligation':
        return None
    return {'42501': 'unauthorized', '54000': 'resource', '0A000': 'unsupported_profile',
            '22023': 'observation', '55P03': 'observation', 'P1002': 'observation',
            'P1010': 'observation',
            'P0002': 'not_found'}.get(error.error.sql_state)


def grant_module_audit_access(host, transaction, grant, manifest, digest, pin_cursor):
    """Admin-only grant registration. Membership is checked for every owner on reads."""
    from .psycopg_host import PsycopgHost
    if type(host) is not PsycopgHost or type(grant) is not ModuleAuditGrant:
        return Ok(LoadAuditUnavailable(reason='observation'))
    try:
        malformed = any(type(value) is not str or not 1 <= len(value.encode('utf8')) <= limit
                        for value, limit in ((grant.document_id, 65536),
                                             (grant.module_id, 65536),
                                             (grant.auditor_role, 256)))
    except UnicodeError:
        malformed = True
    if malformed:
        return Ok(LoadAuditUnavailable(reason='observation'))

    def register(cursor, _observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.grant_import_audit_access(%s,%s,%s)',
            (grant.document_id, grant.module_id, grant.auditor_role), prepare=False)
        return _decode_grant(bytes(cursor.fetchone()[0]), grant)

    result = host._run_operation(transaction, register, function_call=True)
    reason = _reason(result) if isinstance(result, Error) else None
    return Ok(LoadAuditUnavailable(reason=reason)) if reason else result


def read_import_load_chunk(host, transaction, cursor: LoadAuditCursor,
                           page_limit: int, manifest, digest, pin_cursor):
    """Read one whole committed chunk after native full-owner authorization."""
    from .psycopg_host import PsycopgHost
    if (type(host) is not PsycopgHost or type(cursor) is not LoadAuditCursor
            or type(cursor.invocation_id) is not str
            or type(cursor.chunk_index) is not str or type(page_limit) is not int
            or not 1 <= page_limit <= 128):
        return Ok(LoadAuditUnavailable(reason='observation'))
    try:
        import uuid
        selected_invocation = str(uuid.UUID(cursor.invocation_id))
        if (selected_invocation != cursor.invocation_id
                or not re.fullmatch(r'(?:0|[1-9][0-9]{0,3})', cursor.chunk_index)
                or int(cursor.chunk_index)>1023):
            return Ok(LoadAuditUnavailable(reason='observation'))
        selected_chunk = int(cursor.chunk_index)
    except (ValueError, TypeError, AttributeError):
        return Ok(LoadAuditUnavailable(reason='observation'))

    def observe(cursor, _observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.read_import_load_chunk(%s::uuid,%s,%s,%s,%s)',
            (selected_invocation, selected_chunk, page_limit, manifest['releaseId'], digest),
            prepare=False)
        return _decode_page(bytes(cursor.fetchone()[0]))

    result = host._run_operation(transaction, observe, function_call=True)
    reason = _reason(result) if isinstance(result, Error) else None
    return Ok(LoadAuditUnavailable(reason=reason)) if reason else result


def page_import_load_audit(host, transaction, filters, cursor: LoadAuditListingCursor | None,
                           maximum_entries: int, manifest, digest, pin_cursor):
    """Discover whole committed chunks at a frozen frontier, with a bound cursor."""
    from .psycopg_host import PsycopgHost
    from dataclasses import asdict
    if (type(host) is not PsycopgHost or type(filters) is not dict
            or type(maximum_entries) is not int or not 1 <= maximum_entries <= 128
            or cursor is not None and type(cursor) is not LoadAuditListingCursor):
        return Ok(LoadAuditUnavailable(reason='observation'))
    allowed={'invocationId','loadId','nativeActorOid','documentId','moduleId',
             'observedAtFrom','observedAtUntil'}
    try:
        selected_filters=json.dumps(filters,ensure_ascii=False,separators=(',',':'),sort_keys=True,allow_nan=False)
        filter_bytes=selected_filters.encode('utf8')
    except (TypeError,ValueError,UnicodeError):
        return Ok(LoadAuditUnavailable(reason='observation'))
    if (set(filters)-allowed or any(type(key) is not str or type(value) is not str
            for key,value in filters.items())
            or not {'documentId','moduleId'}<=set(filters)
            or any(not 1<=len(filters[key].encode('utf8'))<=4096 for key in ('documentId','moduleId'))
            or any(key in filters and not _valid_filter_time(filters[key])
                   for key in ('observedAtFrom','observedAtUntil'))
            or len(filter_bytes)>8192):
        return Ok(LoadAuditUnavailable(reason='observation'))
    selected_cursor=None
    if cursor is not None:
        try:
            fields=asdict(cursor)
            fields={'profile':fields.pop('profile'),'installationId':fields.pop('installation_id'),
                'sourceEpoch':fields.pop('source_epoch'),'releaseId':fields.pop('release_id'),
                'releaseSha256':fields.pop('release_sha256'),'frontierXid':fields.pop('frontier_xid'),
                'filtersSha256':fields.pop('filters_sha256'),'afterObservedAt':fields.pop('after_observed_at'),
                'afterInvocationId':fields.pop('after_invocation_id')}
            _decode_listing_cursor(fields)
            selected_cursor=json.dumps(fields,ensure_ascii=False,separators=(',',':'),sort_keys=True,
                allow_nan=False).encode('utf8')
            if len(selected_cursor)>8192:
                return Ok(LoadAuditUnavailable(reason='observation'))
        except (TypeError,ValueError,UnicodeError):
            return Ok(LoadAuditUnavailable(reason='observation'))

    def observe(native_cursor, _observed):
        pin_cursor(native_cursor)
        native_cursor.execute('SELECT truss.page_import_load_audit(%s::jsonb,%s,%s,%s,%s)',
            (selected_filters,maximum_entries,selected_cursor,manifest['releaseId'],digest),prepare=False)
        return _decode_listing_page(bytes(native_cursor.fetchone()[0]))

    result=host._run_operation(transaction,observe,function_call=True)
    reason=_reason(result) if isinstance(result,Error) else None
    return Ok(LoadAuditUnavailable(reason=reason)) if reason else result


def read_mutation_group_audit(host, transaction, attempt_id: str, maximum_events: int,
                              manifest, digest, pin_cursor):
    """Read one whole committed owned-profile mutation attempt for its auditors."""
    from .psycopg_host import PsycopgHost
    if (type(host) is not PsycopgHost or type(attempt_id) is not str
            or type(maximum_events) is not int or not 1 <= maximum_events <= 1024):
        return Ok(LoadAuditUnavailable(reason='observation'))
    try:
        import uuid
        selected_attempt = str(uuid.UUID(attempt_id))
        if selected_attempt != attempt_id:
            return Ok(LoadAuditUnavailable(reason='observation'))
    except (ValueError, TypeError, AttributeError):
        return Ok(LoadAuditUnavailable(reason='observation'))

    def observe(cursor, _observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.read_mutation_group_audit(%s::uuid,%s,%s,%s)',
            (selected_attempt, maximum_events, manifest['releaseId'], digest), prepare=False)
        return _decode_mutation_page(bytes(cursor.fetchone()[0]))

    result = host._run_operation(transaction, observe, function_call=True)
    reason = _reason(result) if isinstance(result, Error) else None
    return Ok(LoadAuditUnavailable(reason=reason)) if reason else result


def page_mutation_group_audit(host,transaction,filters,cursor: MutationGroupAuditListingCursor | None,
                              maximum_events: int,manifest,digest,pin_cursor):
    """Discover whole metadata-only mutation groups at a frozen frontier."""
    from .psycopg_host import PsycopgHost
    from dataclasses import asdict
    if (type(host) is not PsycopgHost or type(filters) is not dict
            or type(maximum_events) is not int or not 1<=maximum_events<=1024
            or cursor is not None and type(cursor) is not MutationGroupAuditListingCursor):
        return Ok(LoadAuditUnavailable(reason='observation'))
    allowed={'attemptId','documentId','moduleId','entityId','entityType','entityKey',
             'nativeActorOid','assertedAction','observedAtFrom','observedAtUntil'}
    try:
        selected_filters=json.dumps(filters,ensure_ascii=False,separators=(',',':'),sort_keys=True,allow_nan=False)
        filter_bytes=selected_filters.encode('utf8')
    except (TypeError,ValueError,UnicodeError):
        return Ok(LoadAuditUnavailable(reason='observation'))
    if (set(filters)-allowed or any(type(key) is not str for key in filters)
            or any(type(value) is not str for key,value in filters.items()
                   if key not in ('entityKey',))
            or not {'documentId','moduleId'}<=set(filters)
            or any(not 1<=len(filters[key].encode('utf8'))<=4096 for key in ('documentId','moduleId'))
            or any(key in filters and not _valid_filter_time(filters[key])
                   for key in ('observedAtFrom','observedAtUntil'))
            or len(filter_bytes)>65536):
        return Ok(LoadAuditUnavailable(reason='observation'))
    selected_cursor=None
    if cursor is not None:
        try:
            fields=asdict(cursor)
            fields={'profile':fields.pop('profile'),'installationId':fields.pop('installation_id'),
                'sourceEpoch':fields.pop('source_epoch'),'releaseId':fields.pop('release_id'),
                'releaseSha256':fields.pop('release_sha256'),'frontierXid':fields.pop('frontier_xid'),
                'filtersSha256':fields.pop('filters_sha256'),'afterObservedAt':fields.pop('after_observed_at'),
                'afterAttemptId':fields.pop('after_attempt_id')}
            _decode_mutation_listing_cursor(fields)
            selected_cursor=json.dumps(fields,ensure_ascii=False,separators=(',',':'),sort_keys=True,
                allow_nan=False).encode('utf8')
            if len(selected_cursor)>8192:
                return Ok(LoadAuditUnavailable(reason='observation'))
        except (TypeError,ValueError,UnicodeError):
            return Ok(LoadAuditUnavailable(reason='observation'))
    def observe(native_cursor,_observed):
        pin_cursor(native_cursor)
        native_cursor.execute('SELECT truss.page_mutation_group_audit(%s::jsonb,%s,%s,%s,%s)',
            (selected_filters,maximum_events,selected_cursor,manifest['releaseId'],digest),prepare=False)
        return _decode_mutation_listing_page(bytes(native_cursor.fetchone()[0]))
    result=host._run_operation(transaction,observe,function_call=True)
    reason=_reason(result) if isinstance(result,Error) else None
    return Ok(LoadAuditUnavailable(reason=reason)) if reason else result

