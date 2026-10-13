"""Run two unchanged original consumer read cases on the authority database."""
import argparse
from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path

import psycopg
from adopter_workflow import transaction, success, expect
from truss import CatalogDocument, LocalPostgres, ModuleAccessGrant, QueryRows, ReceiptIncluded, AcceptedDocument
from truss.contracts import MapValue, TextValue
from truss.groups import (CreateObject, CreateEdge, AuthoredValue, AliasObjectReference,
    RootlessOwnership, NullOrderKey, GroupSuccess, CommittedReceiptReplay)

CASES = ('read.missing-key-is-no-rows', 'read.columns-and-filters')


def run_reads(corpus_path, directory, *, bun='bun'):
    corpus_path = Path(corpus_path).resolve()
    original = corpus_path.read_bytes()
    corpus = json.loads(original)
    if corpus['version'] != 1:
        raise ValueError('Original consumer corpus version 1 required')
    model_path = (corpus_path.parent / corpus['module']).resolve()
    if not model_path.is_relative_to(corpus_path.parent):
        raise ValueError('Original model must remain within the corpus directory')
    source = model_path.read_bytes()
    model = json.loads(source)
    if model['umf'] != '0.7.0' or len(model['modules']) != 1:
        raise ValueError('Selected original single-module model required')
    module = model['modules'][0]
    module_id, document_id = module['id'], model['id']
    documents = (CatalogDocument(document_id, sha256(source).hexdigest(), source),)
    fixture = corpus['fixtures']['basic']
    grants = [s for s in fixture if s['op'] == 'grant']
    seeds = [s for s in fixture if s['op'] == 'seed']
    if [s['op'] for s in fixture] != ['install', *['grant'] * len(grants), 'seed', 'sync'] or len(seeds) != 1:
        raise ValueError('Selected original basic setup required')
    selected = [next(c for c in corpus['cases'] if c['id'] == name) for name in CASES]
    if any(c['fixture'] != 'basic' for c in selected):
        raise ValueError('Original basic fixture required')
    directory = Path(directory).resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('New or empty runtime directory required')
    directory.mkdir(parents=True, exist_ok=True)
    observations = []
    with LocalPostgres(directory / 'postgres') as runtime, ExitStack() as stack:
        params = psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
        admin = stack.enter_context(psycopg.connect(**params, autocommit=True, options='-c statement_timeout=10000'))
        with transaction(admin) as (assembly, tx):
            installed = success(assembly.install_in_transaction(tx))
        people = {}
        for grant in grants:
            user = grant['user']
            admin.execute(psycopg.sql.SQL('CREATE ROLE {} LOGIN').format(psycopg.sql.Identifier(user)))
            people[user] = stack.enter_context(psycopg.connect(**dict(params, user=user), autocommit=True, options='-c statement_timeout=10000'))
            if grant.get('admin'):
                # Catalog administration does not make this person a database superuser.
                admin.execute(psycopg.sql.SQL('GRANT {} TO {} WITH SET FALSE').format(
                    psycopg.sql.Identifier(installed.registrar_role), psycopg.sql.Identifier(user)))
        registrar = next(g['user'] for g in grants if g.get('admin'))
        with transaction(people[registrar]) as (assembly, tx):
            prepared = assembly.prepare_catalog(documents, bun_executable=bun)
            success(assembly.accept_in_transaction(tx, prepared, request_key='original-consumer-model'))
            report=json.loads(success(assembly.report_in_transaction(tx)).original_bytes)
            original_evidence=json.loads(prepared.report_evidence_bytes)
            if report['source']['extensions']!=original_evidence['retainedExtensions']['extensions'] or report['source']['diagnostics']!=original_evidence['validation']['diagnostics'] or report['source']['documentInterpretations']!=original_evidence['validation']['documentInterpretations']:
                raise AssertionError('Original retained/partial interpretation report differs')
            retained_extensions=len(report['source']['extensions'])
            if not retained_extensions or not any(d['completeness']=='partial' for d in report['source']['documentInterpretations']):
                raise AssertionError('Original model must remain explicitly partially interpreted')
            view = success(assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())).view
            types = {d.reference.authored_identity: d.reference for d in view.definitions if d.reference.kind == 'type'}
        reader, writer = 'consumer_readers', 'consumer_writers'
        for role in (reader, writer):
            admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
        with transaction(admin) as (assembly, tx):
            success(assembly.configure_module_access_in_transaction(tx, (ModuleAccessGrant(document_id, module_id, reader, writer),)))
        for grant in grants:
            for permission in grant['modules'].get(module_id, []):
                if permission not in ('read', 'write'):
                    raise ValueError('Unsupported original grant')
                admin.execute(psycopg.sql.SQL('GRANT {} TO {} WITH SET FALSE').format(
                    psycopg.sql.Identifier(reader if permission == 'read' else writer), psycopg.sql.Identifier(grant['user'])))
        seed = seeds[0]
        with transaction(people[seed['as']]) as (assembly, tx):
            operations = []
            for record in seed['records']:
                if 'type' in record:
                    authored = next(e for e in module['elements'] if e['id'] == record['type'])
                    primary = next(k for k in authored['keys'] if k.get('primary'))
                    if len(primary['fields']) != 1:
                        raise ValueError('Selected single-field fixture key required')
                    key_field = next(e for e in module['elements'] if e['id'] == primary['fields'][0]['element'])
                    values = {key_field['name']: record['key'], **record['properties']}
                    if any(type(value) is not str for value in values.values()):
                        raise ValueError('Selected fixture uses scalar string values')
                    operations.append(CreateObject(type_definition_pin=types[record['type']].definition_pin,
                        values=tuple(AuthoredValue(name=name, value=TextValue(kind='string', text=value)) for name, value in values.items()),
                        ownership=RootlessOwnership(), alias=record['key']))
                else:
                    relation = next(r for r in module['relationships'] if r['name'] == record['relationship'])
                    reference = success(assembly.get_relationship_reference_in_transaction(tx,
                        document_id=document_id, module_id=module_id, relationship_id=relation['id']))
                    operations.append(CreateEdge(relationship_definition_pin=reference.definition_pin,
                        source=AliasObjectReference(alias=record['source']), target=AliasObjectReference(alias=record['target']),
                        values=(), order_key=NullOrderKey(), alias='fixture-edge'))
            context = success(assembly.group_context_in_transaction(tx))
            original_input = context.input(tuple(operations), MapValue(entries=()))
            request = context.request('original-consumer-fixture')
            expect(success(assembly.apply_in_transaction(tx, original_input, request, documents=documents, bun_executable=bun)), GroupSuccess)
        with transaction(people[seed['as']]) as (assembly, tx):
            replay = expect(success(assembly.apply_in_transaction(tx, original_input, request, documents=documents, bun_executable=bun)), GroupSuccess)
            token = expect(replay.response, CommittedReceiptReplay).receipt_token
        with transaction(people[seed['as']], read_only=True) as (assembly, tx):
            if not expect(success(assembly.reached_in_transaction(tx, token)), ReceiptIncluded).included:
                raise AssertionError('Original fixture commit is not source-visible')
        # The original sync has authority inclusion evidence; no replica sync is claimed.
        for case in selected:
            for step in case['steps']:
                if step['op'] != 'query':
                    raise ValueError('Selected original read step required')
                if 'requires' in step:
                    if set(step['requires']) != {'type', 'columns'}:
                        raise ValueError('Unsupported original capability requirement')
                    if step['requires']['type'] != module['namespace'] + '.UseCase':
                        raise ValueError('Unknown original type requirement')
                with transaction(people[step['as']], read_only=True) as (assembly, tx):
                    archived=expect(success(assembly.accepted_document_in_transaction(tx,document_id=document_id)),AcceptedDocument)
                    if archived.content!=source:raise AssertionError('Original consumer document bytes differ')
                    rows = expect(success(assembly.query_in_transaction(tx, sql=step['sql'], document_ids=(document_id,))), QueryRows)
                expected = step['expect']
                actual_rows = [dict(zip(rows.columns, row, strict=True)) for row in rows.rows]
                if actual_rows != expected['rows'] or ('columns' in expected and list(rows.columns) != expected['columns']):
                    raise AssertionError(f'Original expected read differs: {case["id"]}')
            observations.append({'id': case['id'], 'requires': [s.get('requires') for s in case['steps']],
                'authority': 'passed', 'replica': 'unavailable', 'replicaReason': 'no qualified replica deployment'})
    return {'scope': 'two original authority read variants; not complete corpus or interchange',
        'corpusSha256': sha256(original).hexdigest(), 'modelSha256': sha256(source).hexdigest(),
        'fixtureSync': 'committed original receipt included on authority', 'retainedExtensions':retained_extensions,
        'interpretation':'partial; actions/placement/replica semantics unselected', 'observations': observations}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('corpus', type=Path)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--bun', default='bun')
    args = parser.parse_args()
    print(json.dumps(run_reads(args.corpus, args.directory, bun=args.bun), sort_keys=True))
