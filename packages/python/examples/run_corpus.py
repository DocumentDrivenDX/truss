"""Run the separately versioned public Python preview corpus using public APIs."""
import argparse
import base64
from decimal import Decimal
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
from contextlib import ExitStack

import psycopg
from adopter_workflow import transaction, success, expect, sync_directory
from truss import (CatalogDocument, CapabilityAvailable, LocalPostgres, ModuleAccessGrant,
    ObjectFound, ObjectNotFound, QueryAbsent, QueryRows, QueryRelatedKeys, QueryRefused,
    ReceiptIncluded, FeedPage, FeedAcknowledged)
from truss.contracts import MapValue, MapEntry, TextValue, BooleanValue, NullValue
from truss.groups import (CreateObject, CreateEdge, UpdateObject, AuthoredValue,
    AliasObjectReference, StoredObjectReference, RootlessOwnership, NullOrderKey,
    RequestNone, GroupSuccess, GroupFailed, PropertyEquals)
from truss.imports import ImportReported, ImportCreated, ImportSkipped, ImportRejected

FORMAT = 'truss-public-python-preview/0.8'
SCOPE = 'single Python preview; not full conformance or interchange'
OPS = {'install', 'accept', 'configure', 'apply', 'replay', 'lookup', 'query',
       'reached', 'import', 'drain-feed'}
PROFILE = {'runtimeRelease': 'truss-catalog-runtime/0.34-candidate',
    'postgresql': '18.6', 'driver': 'psycopg3.3.6', 'weftBackendVersion': '0.4.7',
    'layout': {'identity': 'truss-layout', 'version': '0.16',
        'sha256': '261e32c6c62624418f124ac7fbe3c206338322a03755b7ac0f1a7c7d86002368'}}


def closed(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError('Unknown or missing corpus fields')


def typed(value):
    if type(value) is str:
        return {'kind': 'string', 'text': value}
    if type(value) is int:
        return {'kind': 'integer', 'text': str(value)}
    if type(value) is bool:
        return {'kind': 'boolean', 'value': value}
    if value is None:
        return {'kind': 'null'}
    if isinstance(value, QueryRelatedKeys):
        return {'kind': 'related-keys', 'items': [list(v) for v in value.items],
                'truncated': value.truncated}
    if isinstance(value, Decimal):
        return {'kind': 'decimal', 'text': str(value)}
    if isinstance(value, QueryAbsent):
        return {'kind': 'absent'}
    if isinstance(value, TextValue):
        return {'kind': value.kind, 'text': value.text}
    raise ValueError('Unsupported preview result value')


def authored(entries):
    result = []
    for entry in entries:
        closed(entry, ('name', 'value'))
        source = entry['value']
        if type(source) is not dict:
            raise ValueError('Explicit scalar carrier required')
        kind = source.get('kind')
        if kind in ('string', 'integer', 'decimal', 'timestamp', 'binary'):
            closed(source, ('kind', 'text'))
            if type(source['text']) is not str:
                raise ValueError('Exact text scalar required')
            value = TextValue(kind=kind, text=source['text'])
        elif kind == 'boolean':
            closed(source, ('kind', 'value'))
            if type(source['value']) is not bool:
                raise ValueError('Exact boolean scalar required')
            value = BooleanValue(value=source['value'])
        elif kind == 'null':
            closed(source, ('kind',))
            value = NullValue()
        else:
            raise ValueError('Unsupported preview scalar kind')
        result.append(AuthoredValue(name=entry['name'], value=value))
    return tuple(result)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate corpus member')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f'Nonfinite JSON constant: {value}')


def load_case(path):
    path = Path(path).resolve()
    original = path.read_bytes()
    data = json.loads(original, object_pairs_hook=unique_object, parse_constant=reject_constant)
    closed(data, ('format', 'id', 'profile', 'fixture', 'setup', 'phases', 'feedProjection', 'resultProjection', 'scope'))
    if data['format'] != FORMAT or data['profile'] != PROFILE or data['scope'] != SCOPE:
        raise ValueError('Unsupported corpus version or profile')
    fixture = data['fixture']
    closed(fixture, ('path', 'sha256', 'documentId', 'revision'))
    source_path = (path.parent / fixture['path']).resolve()
    if not source_path.is_relative_to(path.parent):
        raise ValueError('Fixture must remain within the portable case directory')
    source = source_path.read_bytes()
    if sha256(source).hexdigest() != fixture['sha256']:
        raise ValueError('Original corpus fixture digest differs')
    closed(data['setup'], ('actors', 'readerRole', 'writerRole', 'moduleId', 'consumerId'))
    if type(data['setup']['actors']) is not dict or 'admin' in data['setup']['actors']:
        raise ValueError('Reserved administrator actor alias')
    if data['resultProjection'] != {'install':['status','releaseId','installed'],'accept':['replayed','revision'],'configure':['status'],'apply/replay':['outcome','disposition','durability','results','failure code/condition IDs'],'lookup':['outcome','values'],'query':['outcome','columns','rows','refusal code'],'reached':['outcome','included','comparison identity'],'import':['status','execution','per-item index/outcome/disposition/reason/code'],'drain-feed':['declared feedProjection','committed ACK'],'retainedButNotCompared':['catalog report metadata','full group receipt/replay evidence','diagnostic prose','import batch IDs/containment evidence']}:
        raise ValueError('Unknown result expectation projection')
    for phase in data['phases']:
        closed(phase, ('actor', 'readOnly', 'settle', 'steps'))
        if phase['actor'] not in {'admin', *data['setup']['actors']} or type(phase['readOnly']) is not bool or phase['settle'] not in ('commit', 'rollback', 'per-delivery'):
            raise ValueError('Unknown caller transaction phase')
        for step in phase['steps']:
            closed(step, ('op', 'as', 'args', 'expect'))
            if step['op'] not in OPS or type(step['args']) is not dict or type(step['expect']) is not dict:
                raise ValueError('Unknown operation or expectation shape')
        if phase['settle'] == 'per-delivery' and (len(phase['steps']) != 1 or phase['steps'][0]['op'] != 'drain-feed' or phase['readOnly']):
            raise ValueError('Feed delivery needs its declared separate read/ACK transactions')
    return data, source, sha256(original).hexdigest()


class Runner:
    def __init__(self, case, source, directory, bun):
        self.case, self.directory, self.bun = case, directory, bun
        f = case['fixture']
        self.documents = (CatalogDocument(f['documentId'], f['revision'], source),)
        self.doc, self.module = f['documentId'], case['setup']['moduleId']
        self.types, self.properties, self.identities, self.saved = {}, {}, {}, {}
        self.observations = []

    def check(self, step, actual):
        # Compare JSON kinds as well as values: Python equality equates True with 1.
        encode = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
        if encode(actual) != encode(step['expect']):
            raise AssertionError(f"{step['as']}: expected {step['expect']!r}, observed {actual!r}")
        self.observations.append({'id': step['as'], 'op': step['op'], 'observed': actual})

    def identity_ref(self, kind, identity):
        for name, (actual_kind, original) in self.identities.items():
            if kind == actual_kind and identity == {'id': original.id, 'typeId': original.type_id,
                    'definitionPin': original.definition_pin,
                    'owner': {'documentId': original.owner.document_id, 'moduleId': original.owner.module_id}}:
                return name
        raise AssertionError('Feed identity has no actual returned binding')

    def operations(self, assembly, tx, operations):
        result = []
        for operation in operations:
            op = operation['op']
            if op == 'create-object':
                closed(operation, ('op', 'record', 'values', 'alias'))
                result.append(CreateObject(type_definition_pin=self.types[operation['record']].definition_pin,
                    values=authored(operation['values']), ownership=RootlessOwnership(), alias=operation['alias']))
            elif op == 'create-edge':
                closed(operation, ('op', 'relationship', 'sourceAlias', 'targetAlias', 'alias'))
                reference = success(assembly.get_relationship_reference_in_transaction(tx,
                    document_id=self.doc, module_id=self.module, relationship_id=operation['relationship']))
                result.append(CreateEdge(relationship_definition_pin=reference.definition_pin,
                    source=AliasObjectReference(alias=operation['sourceAlias']),
                    target=AliasObjectReference(alias=operation['targetAlias']), values=(),
                    order_key=NullOrderKey(), alias=operation['alias']))
            elif op == 'update-object':
                closed(operation, ('op', 'entity', 'values', 'expectedVersion'))
                result.append(UpdateObject(target=StoredObjectReference(identity=self.identities[operation['entity']][1]),
                    set=authored(operation['values']), unset=(), expected_version=operation['expectedVersion']))
            else:
                raise ValueError('Unknown group operation')
        return tuple(result)

    def group_result(self, result, operations):
        if isinstance(result, GroupFailed):
            value = {'outcome': 'failed', 'code': result.failure.code}
            if result.failure.code == 'precondition_failed':
                value['conditions'] = [c.condition_id for c in result.failure.failures]
            return value
        expect(result, GroupSuccess)
        for original, returned in zip(operations, result.response.semantic.results, strict=True):
            if returned.outcome == 'created':
                self.identities[original['alias']] = ('object' if original['op'] == 'create-object' else 'edge', returned.identity)
        return {'outcome': 'success', 'disposition': result.response.disposition,
            'durability': result.response.durability,
            'results': [v.outcome for v in result.response.semantic.results]}

    def call(self, assembly, tx, step, actor, admin):
        args, op = step['args'], step['op']
        if op == 'install':
            closed(args, ('registrarActor',))
            self.installation = success(assembly.install_in_transaction(tx))
            admin.execute(psycopg.sql.SQL('GRANT {} TO {} WITH SET FALSE').format(
                psycopg.sql.Identifier(self.installation.registrar_role),
                psycopg.sql.Identifier(self.case['setup']['actors'][args['registrarActor']])))
            return {'status': self.installation.status, 'releaseId': self.installation.release_id,
                    'installed': success(assembly.status_in_transaction(tx)).installed}
        if op == 'accept':
            closed(args, ('requestKey',))
            prepared = assembly.prepare_catalog(self.documents, bun_executable=self.bun)
            accepted = success(assembly.accept_in_transaction(tx, prepared, request_key=args['requestKey']))
            view = success(assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())).view
            if {'identity': view.layout_profile.identity, 'version': view.layout_profile.version,
                    'sha256': view.layout_profile.sha256} != self.case['profile']['layout']:
                raise AssertionError('Observed installed layout differs from case')
            for definition in view.definitions:
                r = definition.reference
                if r.kind == 'type':
                    self.types[r.authored_identity] = r
                if r.kind == 'property':
                    self.properties[(r.type_id, r.property_id)] = r.authored_identity
            return {'replayed': accepted.replayed, 'revision': view.catalog_revision}
        if op == 'configure':
            closed(args, ('grants', 'removeRegistrarActor'))
            setup = self.case['setup']
            success(assembly.configure_module_access_in_transaction(tx, (
                ModuleAccessGrant(self.doc, self.module, setup['readerRole'], setup['writerRole']),)))
            success(assembly.register_feed_consumer_in_transaction(tx,
                consumer_id=setup['consumerId'], reader_role=setup['readerRole']))
            for grant in args['grants']:
                closed(grant, ('actor', 'permission'))
                if grant['permission'] not in ('read', 'write'):
                    raise ValueError('Unknown module permission')
                role = setup['readerRole'] if grant['permission'] == 'read' else setup['writerRole']
                admin.execute(psycopg.sql.SQL('GRANT {} TO {} WITH SET FALSE').format(
                    psycopg.sql.Identifier(role), psycopg.sql.Identifier(setup['actors'][grant['actor']])))
            admin.execute(psycopg.sql.SQL('REVOKE {} FROM {}').format(
                psycopg.sql.Identifier(self.installation.registrar_role),
                psycopg.sql.Identifier(setup['actors'][args['removeRegistrarActor']])))
            return {'status': 'pending_commit'}
        if op == 'apply':
            closed(args, ('operations', 'requestKey', 'preconditions'))
            context = success(assembly.group_context_in_transaction(tx))
            operations = self.operations(assembly, tx, args['operations'])
            conditions = []
            for condition in args['preconditions']:
                closed(condition, ('op', 'entity', 'name', 'value', 'id', 'reason'))
                if condition['op'] != 'property-equals':
                    raise ValueError('Unknown precondition')
                value = authored([{'name': condition['name'], 'value': condition['value']}])[0].value
                conditions.append(PropertyEquals(id=condition['id'], reason=condition['reason'],
                    target=self.identities[condition['entity']][1], name=condition['name'], value=value))
            original = context.input(operations, MapValue(entries=()), preconditions=tuple(conditions))
            request = RequestNone() if args['requestKey'] is None else context.request(args['requestKey'])
            result = success(assembly.apply_in_transaction(tx, original, request,
                documents=self.documents, bun_executable=self.bun))
            self.saved[step['as']] = (original, request, args['operations'])
            return self.group_result(result, args['operations'])
        if op == 'replay':
            closed(args, ('original',))
            original, request, operations = self.saved[args['original']]
            result = success(assembly.apply_in_transaction(tx, original, request,
                documents=self.documents, bun_executable=self.bun))
            self.saved[step['as']] = result.response.receipt_token
            return self.group_result(result, operations)
        if op == 'reached':
            closed(args, ('token', 'consumer'))
            result = expect(success(assembly.reached_in_transaction(tx, self.saved[args['token']],
                consumer_id=args['consumer'])), ReceiptIncluded)
            return {'outcome': 'available', 'included': result.included,
                    'comparison': result.comparison_profile.identity}
        if op == 'lookup':
            closed(args, ('record', 'key', 'values'))
            result = success(assembly.lookup_key_in_transaction(tx, document_id=self.doc,
                module_id=self.module, record_id=args['record'], key_id=args['key'],
                values=tuple(args['values']), bun_executable=self.bun))
            if isinstance(result, ObjectNotFound):
                return {'outcome': 'not_found'}
            expect(result, ObjectFound)
            return {'outcome': 'found', 'values': {name: typed(value) for name, value in result.object.values}}
        if op == 'query':
            closed(args, ('sql', 'parameters', 'readProfile'))
            query = expect(assembly.compiled_execution(assembly.compiled_selection), CapabilityAvailable).capability
            result = success(query.query_in_transaction(tx, sql=args['sql'], document_ids=(self.doc,),
                parameters=args['parameters'], read_profile=args['readProfile']))
            if isinstance(result, QueryRefused):
                return {'outcome': 'refused', 'code': result.code}
            expect(result, QueryRows)
            return {'outcome': 'rows', 'columns': list(result.columns),
                    'rows': [[typed(value) for value in row] for row in result.rows]}
        if op == 'import':
            closed(args, ('record', 'loadId', 'records'))
            context = success(assembly.import_context_in_transaction(tx))
            records = []
            for row in args['records']:
                closed(row, ('as', 'values', 'payloadValues', 'source'))
                source = MapValue(entries=tuple(MapEntry(key=k, value=TextValue(kind='string', text=v)) for k, v in row['source'].items()))
                record = success(assembly.object_import_record_in_transaction(tx, document_id=self.doc,
                    module_id=self.module, record_id=args['record'], values=authored(row['values']), source=source))
                if row['payloadValues'] is not None:
                    record = replace(record, payload=context.object_payload(authored(row['payloadValues']), source=source))
                records.append(record)
            result = expect(assembly.import_in_transaction(tx,
                context.input(tuple(records), load_id=args['loadId'], asserted_origin=MapValue(entries=())),
                documents=self.documents, bun_executable=self.bun), ImportReported)
            outcomes = []
            for value in result.report.outcomes:
                normalized = {'index': value.input_index, 'outcome': value.outcome,
                    'disposition': next(b.disposition for b in result.report.batches if value.input_index in b.input_indices)}
                if isinstance(value, ImportCreated):
                    self.identities[args['records'][int(value.input_index)]['as']] = ('object', value.identity)
                elif isinstance(value, ImportSkipped):
                    normalized['reason'] = value.reason
                elif isinstance(value, ImportRejected):
                    normalized['code'] = value.code
                else:
                    raise AssertionError('Unexpected import execution outcome')
                outcomes.append(normalized)
            return {'status': result.report.status, 'execution': result.report.execution, 'outcomes': outcomes}
        raise ValueError('Unknown in-transaction operation')

    def drain(self, connection, step):
        args = step['args']
        closed(args, ('consumer', 'maximumPages'))
        if type(args['maximumPages']) is not int or not 1 <= args['maximumPages'] <= 32:
            raise ValueError('Finite feed page bound required')
        if self.case['feedProjection'] != {'journal': ['entity', 'kind', 'operation', 'version', 'properties', 'actor', 'source', 'target', 'orderKey'],
                'importSources': ['entity', 'loadId', 'source'], 'catalog': ['originalDocumentSha256'],
                'retainedButNotCompared': ['native timestamps', 'native xid/seq', 'opaque cursor bytes', 'physical reservations', 'remaining catalog metadata']}:
            raise ValueError('Unknown feed expectation projection')
        journal, sources, archived = [], [], set()
        sink = self.directory / 'sink'
        sink.mkdir(exist_ok=True)
        sync_directory(self.directory)
        for _ in range(args['maximumPages']):
            with transaction(connection, read_only=True) as (assembly, tx):
                page = expect(success(assembly.read_feed_in_transaction(tx, consumer_id=args['consumer'])), FeedPage)
            if sha256(page.content).hexdigest() != page.sha256:
                raise AssertionError('Original feed payload hash differs')
            payload = json.loads(page.content)
            for change in payload['changes']:
                wrapped = change['new_value']
                raw = base64.b64decode(wrapped['bytesBase64'], validate=True)
                if sha256(raw).hexdigest() != wrapped['bytesSha256']:
                    raise AssertionError('Original journal event hash differs')
                event = json.loads(raw)
                after = event['after']
                fact = {'entity': self.identity_ref(after['kind'], event['identity']),
                    'kind': after['kind'], 'operation': event['operation'], 'version': event['eventVersion'],
                    'properties': [{'fieldId': self.properties[(event['identity']['typeId'], p['propertyId'])],
                        'value': p['value']} for p in after['properties']], 'actor': event['origin']['databaseRole']}
                if after['kind'] == 'edge':
                    fact.update(source=self.identity_ref('object', after['source']),
                        target=self.identity_ref('object', after['target']), orderKey=after['orderKey'])
                journal.append(fact)
            for source in payload['sources']:
                matches = [name for name, (kind, identity) in self.identities.items()
                    if ('o' if kind == 'object' else 'e') == source['entity_kind'] and identity.id == str(source['entity_id'])]
                if len(matches) != 1:
                    raise AssertionError('Import source lacks an actual entity binding')
                sources.append({'entity': matches[0], 'loadId': source['load_id'],
                                'source': {k: typed(v) for k, v in source['source'].items()}})
            for revision in payload['catalogPrerequisites']:
                for document in revision['documents']:
                    archived.add(sha256(document['document'].encode('utf8')).hexdigest())
            with (sink / (page.sha256 + '.json')).open('wb') as output:
                output.write(page.content); output.flush(); os.fsync(output.fileno())
            sync_directory(sink)
            with transaction(connection) as (assembly, tx):
                expect(success(assembly.acknowledge_feed_in_transaction(tx, page)), FeedAcknowledged)
            if page.outcome == 'empty_interval':
                break
        else:
            raise AssertionError('Feed did not finish within the declared bound')
        return {'journal': journal, 'importSources': sources, 'catalog': sorted(archived), 'ack': 'committed'}

    def run(self):
        with LocalPostgres(self.directory / 'postgres') as runtime, ExitStack() as stack:
            params = psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
            admin = stack.enter_context(psycopg.connect(**params, autocommit=True, options='-c statement_timeout=10000'))
            actors = {'admin': admin}
            for alias, role in self.case['setup']['actors'].items():
                admin.execute(psycopg.sql.SQL('CREATE ROLE {} LOGIN').format(psycopg.sql.Identifier(role)))
                actors[alias] = stack.enter_context(psycopg.connect(**dict(params, user=role), autocommit=True, options='-c statement_timeout=10000'))
            for role in (self.case['setup']['readerRole'], self.case['setup']['writerRole']):
                admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            for phase in self.case['phases']:
                connection = actors[phase['actor']]
                if phase['settle'] == 'per-delivery':
                    self.check(phase['steps'][0], self.drain(connection, phase['steps'][0]))
                else:
                    with transaction(connection, read_only=phase['readOnly'], commit=phase['settle'] == 'commit') as (assembly, tx):
                        for step in phase['steps']:
                            self.check(step, self.call(assembly, tx, step, phase['actor'], admin))
        return {'format': FORMAT, 'id': self.case['id'], 'outcome': 'passed_preview',
                'scope': SCOPE, 'observations': self.observations}


def run_case(path, directory, bun='bun'):
    case, source, case_sha = load_case(path)
    directory = Path(directory).resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('New or empty case directory required')
    missing, ancestor = [], directory
    while not ancestor.exists():
        missing.append(ancestor); ancestor = ancestor.parent
    directory.mkdir(parents=True, exist_ok=True)
    for created in reversed(missing):
        sync_directory(created.parent)
    sync_directory(directory.parent)
    result = Runner(case, source, directory, bun).run()
    result['caseSha256'] = case_sha
    result['profile'] = case['profile']
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--bun', default='bun')
    args = parser.parse_args()
    print(json.dumps(run_case(args.case, args.directory, args.bun), indent=2))
