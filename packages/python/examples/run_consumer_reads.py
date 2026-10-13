"""Run selected unchanged consumer read/action workflows on the authority database."""
import argparse
from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
from uuid import uuid4

import psycopg
from adopter_workflow import transaction, success, expect
from truss import CatalogDocument, CapabilityAvailable, LocalPostgres, ModuleAccessGrant, QueryRows, QueryPage, QueryReadPosition, ReceiptIncluded, AcceptedDocument, ObjectFound, ObjectNotFound, ReaderCatalog
from truss.contracts import MapValue, MapEntry, TextValue, NullValue
from truss.imports import ImportReported, ImportCreated, ImportSkipped, ImportRejected, PendingBatch
from truss.groups import (CreateObject, CreateEdge, AuthoredValue, AliasObjectReference,
    RootlessOwnership, NullOrderKey, GroupSuccess, CommittedReceiptReplay, StoredObjectReference, ObjectExists, KeyAbsent, Created, Changed, UpdateObject, GroupFailed, PreconditionFailed, RequestNone)

CASES = ('read.missing-key-is-no-rows', 'read.columns-and-filters', 'read.relationship-filter-both-directions', 'read.key-lookup-whole-entity', 'read.relationship-columns-follow-ends', 'read.paging-by-key', 'read.repeated-relationship-predicates-mean-both', 'action.applies-atomically-and-reads-back', 'action.idempotent-retry-returns-the-original', 'action.update-bumps-the-version-once', 'import.entities-before-relationships', 'import.identity-skip-and-provenance', 'action.atomic-batch-is-all-or-nothing', 'action.dry-run-writes-nothing-and-keeps-the-key')


def run_reads(corpus_path, directory, *, bun='bun', case_ids=CASES):
    dry_case='action.dry-run-writes-nothing-and-keeps-the-key'
    if dry_case in case_ids and len(case_ids)>1:
        directory=Path(directory).resolve()
        if directory.exists() and any(directory.iterdir()):raise ValueError('New or empty runtime directory required')
        other=run_reads(corpus_path,directory/'primary',bun=bun,case_ids=tuple(name for name in case_ids if name!=dry_case))
        preview=run_reads(corpus_path,directory/'dry-run',bun=bun,case_ids=(dry_case,))
        if (other['corpusSha256'],other['modelSha256'])!=(preview['corpusSha256'],preview['modelSha256']):
            raise AssertionError('Original corpus/model changed between isolated workflows')
        return {**other,'observations':other['observations']+preview['observations'],
            'checked':list(dict.fromkeys(other['checked']+preview['checked'])),
            'caseIsolation':'dry-run uses a fresh original basic fixture'}
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
    selected = [next(c for c in corpus['cases'] if c['id'] == name) for name in case_ids]
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
            created = expect(success(assembly.apply_in_transaction(tx, original_input, request, documents=documents, bun_executable=bun)), GroupSuccess)
            fixture_objects = {record['key']: result.identity for record, result in zip(seed['records'], created.response.semantic.results, strict=True) if 'type' in record}
        with transaction(people[seed['as']]) as (assembly, tx):
            replay = expect(success(assembly.apply_in_transaction(tx, original_input, request, documents=documents, bun_executable=bun)), GroupSuccess)
            token = expect(replay.response, CommittedReceiptReplay).receipt_token
        with transaction(people[seed['as']], read_only=True) as (assembly, tx):
            if not expect(success(assembly.reached_in_transaction(tx, token)), ReceiptIncluded).included:
                raise AssertionError('Original fixture commit is not source-visible')
        # The original sync has authority inclusion evidence; no replica sync is claimed.
        for case in selected:
            case_input = case_request = case_actor = None
            cursors = {}
            tokens = {}
            invocations = {}
            batches = {}
            for step in case['steps']:
                if step['op']=='apply_batch':
                    if case['id']!='action.atomic-batch-is-all-or-nothing' or step['action']!='catalog.AddUseCase' or step['atomic'] is not True or step['as']!='erik' or set(step)-{'op','as','action','atomic','key','items','expect'} or sha256(source).hexdigest()!='849a4fc0ec421110f08ffa24ff366e2b6d9b69d221373357f1bea926c9a25696':
                        raise ValueError('Exact original atomic AddUseCase batch required')
                    items=step['items']
                    if len(items)!=2 or any(set(item)!={'code','name'} or any(type(v) is not str for v in item.values()) for item in items):
                        raise ValueError('Selected two-item string batch required')
                    original_items=tuple((item['code'],item['name']) for item in items)
                    saved=batches.get(step.get('key')) if 'key' in step else None
                    with transaction(people[step['as']]) as (assembly,tx):
                        if saved is not None:
                            prior_items,batch_input,batch_request,prior_semantic,prior_token=saved
                            if original_items!=prior_items:raise ValueError('Changed-input batch retry is outside this workflow')
                        else:
                            record=next(e for e in module['elements'] if e['id']=='UseCase')
                            primary=next(k for k in record['keys'] if k.get('primary'))
                            context=success(assembly.group_context_in_transaction(tx))
                            condition_ids={f'batch:{index}:fresh':'fresh' for index in range(len(items))}
                            conditions=tuple(KeyAbsent(id=identity,reason='a use case with that code exists',type_definition_pin=types['UseCase'].definition_pin,key_id=primary['id'],values=(TextValue(kind='string',text=items[index]['code']),)) for index,identity in enumerate(condition_ids))
                            operations=tuple(CreateObject(type_definition_pin=types['UseCase'].definition_pin,values=tuple(AuthoredValue(name=name,value=TextValue(kind='string',text=item[name])) for name in ('code','name')),ownership=RootlessOwnership(),alias=f'batch:{index}') for index,item in enumerate(items))
                            batch_input=context.input(operations,MapValue(entries=(MapEntry(key='x-action',value=TextValue(kind='string',text=step['action'])),)),preconditions=conditions)
                            batch_request=context.request(step['key']) if 'key' in step else RequestNone()
                        outcome=success(assembly.apply_in_transaction(tx,batch_input,batch_request,documents=documents,bun_executable=bun))
                        if 'error' in step['expect']:
                            failed=expect(expect(outcome,GroupFailed).failure,PreconditionFailed)
                            if any(f.condition_id not in condition_ids for f in failed.failures):raise AssertionError('Unknown native batch condition ID')
                            if step['expect']!={'error':'PreconditionFailed','failure_ids':[condition_ids[f.condition_id] for f in failed.failures]}:
                                raise AssertionError('Original atomic batch failure differs')
                        else:
                            applied=expect(outcome,GroupSuccess)
                            results=applied.response.semantic.results
                            if len(results)!=len(items) or any(not isinstance(result,Created) or result.operation!='create_object' or result.alias!=f'batch:{index}' for index,result in enumerate(results)):
                                raise AssertionError('Atomic batch requires two actual native object creations')
                    # Counts/tokens are exposed only after the caller's known commit.
                    if 'error' in step['expect']:continue
                    if saved is not None:
                        committed=expect(applied.response,CommittedReceiptReplay)
                        if committed.semantic!=prior_semantic or committed.receipt_token!=prior_token:
                            raise AssertionError('Atomic batch original semantic result/token differs')
                    else:
                        with transaction(people[step['as']]) as (assembly,tx):
                            committed=expect(expect(success(assembly.apply_in_transaction(tx,batch_input,batch_request,documents=documents,bun_executable=bun)),GroupSuccess).response,CommittedReceiptReplay)
                        if committed.semantic!=applied.response.semantic or not committed.receipt_token:
                            raise AssertionError('Atomic batch committed recovery differs')
                        batches[step['key']]=(original_items,batch_input,batch_request,committed.semantic,committed.receipt_token)
                    summary={'succeeded':len(results),'failed':0,'one_token':bool(committed.receipt_token),'replayed':list(range(len(results))) if applied.response.disposition=='replayed' else []}
                    if any(summary[name]!=value for name,value in step['expect']['batch'].items()):raise AssertionError('Original atomic batch summary differs')
                    with transaction(people[step['as']],read_only=True) as (assembly,tx):
                        if not expect(success(assembly.reached_in_transaction(tx,committed.receipt_token)),ReceiptIncluded).included:raise AssertionError('Atomic batch receipt not included')
                    continue
                if step['op']=='import' and case['id']=='import.identity-skip-and-provenance':
                    first=[{'type':'UseCase','key':'uc-7','properties':{'name':'Old'},'original_author':'ann','original_at':None},
                        {'type':'UseCase','key':'uc-1','properties':{'name':'overwritten?'}},
                        {'type':'UseCase','key':'uc-6','properties':{}},
                        {'relationship':'addresses','source':'ghost','target':'uc-7'}]
                    repeated=[{'type':'UseCase','key':'uc-7','properties':{'name':'Old'}}]
                    if set(step)!={'op','as','load_id','records','expect'} or step['as']!='erik' or step['load_id']!='L1' or step['records'] not in (first,repeated) or sha256(source).hexdigest()!='849a4fc0ec421110f08ffa24ff366e2b6d9b69d221373357f1bea926c9a25696':
                        raise ValueError('Exact original mixed-import workflow required; no import attempted')
                    host_rejections=[]
                    with transaction(people[step['as']]) as (assembly,tx):
                        capability=expect(assembly.imports(assembly.import_selection,documents=documents,bun_executable=bun),CapabilityAvailable).capability
                        context=success(capability.import_context_in_transaction(tx))
                        authored=next(e for e in module['elements'] if e['id']=='UseCase')
                        primary=next(k for k in authored['keys'] if k.get('primary'))
                        if len(primary['fields'])!=1:raise ValueError('Selected single-field original import key required')
                        key_field=next(e for e in module['elements'] if e['id']==primary['fields'][0]['element'])
                        inputs=[]
                        for record in step['records'][:3]:
                            values={key_field['name']:record['key'],**record['properties']}
                            provenance=None
                            if 'original_author' in record:
                                provenance=MapValue(entries=(MapEntry(key='author',value=TextValue(kind='string',text=record['original_author'])),MapEntry(key='at',value=NullValue())))
                            inputs.append(success(capability.object_import_record_in_transaction(tx,document_id=document_id,module_id=module_id,record_id='UseCase',values=tuple(AuthoredValue(name=name,value=TextValue(kind='string',text=value)) for name,value in values.items()),source=provenance)))
                        native=expect(capability.import_in_transaction(tx,context.input(tuple(inputs),load_id=step['load_id'],asserted_origin=MapValue(entries=()))),ImportReported).report
                        expected_types=(ImportCreated,ImportSkipped,ImportRejected) if step['records']==first else (ImportSkipped,)
                        if native.status!='processed' or native.unprocessed_indices or len(native.outcomes)!=len(expected_types) or any(not isinstance(outcome,kind) or outcome.input_index!=str(index) for index,(outcome,kind) in enumerate(zip(native.outcomes,expected_types,strict=True))):
                            raise AssertionError('Original mixed import requires complete native per-record results')
                        if step['records']==first:
                            found=expect(success(assembly.lookup_key_in_transaction(tx,document_id=document_id,module_id=module_id,record_id='UseCase',key_id=primary['id'],values=('uc-7',),original_document=source,bun_executable=bun)),ObjectFound).object
                            if found.identity!=native.outcomes[0].identity:raise AssertionError('Imported original identity differs from own-transaction key read')
                            solution=next(e for e in module['elements'] if e['id']=='Solution')
                            solution_key=next(k for k in solution['keys'] if k.get('primary'))
                            expect(success(assembly.lookup_key_in_transaction(tx,document_id=document_id,module_id=module_id,record_id='Solution',key_id=solution_key['id'],values=('ghost',),original_document=source,bun_executable=bun)),ObjectNotFound)
                            archived=expect(success(assembly.accepted_document_in_transaction(tx,document_id=document_id)),AcceptedDocument)
                            catalog=expect(success(assembly.reader_catalog_in_transaction(tx)),ReaderCatalog)
                            visible=next((m for m in catalog.modules if m['documentId']==document_id and m['moduleId']==module_id),None)
                            current_type=next((t for t in visible['types'] if t['recordId']=='Solution' and t['kind']=='record' and not t['provisional']),None) if visible is not None else None
                            if archived.content!=source or visible is None or visible['documentSha256']!=sha256(source).hexdigest() or current_type is None or not any(k['typeId']==current_type['typeId'] and k['keyId']==solution_key['id'] for k in visible['keys']):
                                raise ValueError('Current authorized source/catalog/key required for host endpoint rejection')
                            host_rejections.append((3,'relationship','missing_endpoint'))
                    # The original consumer summary combines actual native results and
                    # a separately identified host rejection, only after host commit.
                    counts={'created':int(native.counts.created_pending),'skipped':int(native.counts.skipped),'rejected':int(native.counts.rejected)+len(host_rejections)}
                    wanted=step['expect']['import']
                    kinds=['entity' for result in native.outcomes if isinstance(result,ImportRejected)]+[kind for _,kind,_ in host_rejections]
                    if any(counts[name]!=value for name,value in wanted.items() if name!='rejected_kinds') or 'rejected_kinds' in wanted and sorted(kinds)!=wanted['rejected_kinds']:
                        raise AssertionError('Original mixed import summary differs')
                    continue
                if step['op']=='import':
                    if case['id']!='import.entities-before-relationships' or sha256(source).hexdigest()!='849a4fc0ec421110f08ffa24ff366e2b6d9b69d221373357f1bea926c9a25696' or set(step)!={'op','as','load_id','records','expect'}:
                        raise ValueError('Selected original import workflow required; no import attempted')
                    if step['records']!=[{'relationship':'addresses','source':'sol-9','target':'uc-1'},{'type':'Solution','key':'sol-9','properties':{'name':'late'}}] or step['load_id']!='L2' or step['as']!='erik':
                        raise ValueError('Exact original import inputs required; no import attempted')
                    reports=[]
                    with transaction(people[step['as']]) as (assembly,tx):
                        capability=expect(assembly.imports(assembly.import_selection,documents=documents,bun_executable=bun),CapabilityAvailable).capability
                        context=success(capability.import_context_in_transaction(tx))
                        record=step['records'][1]
                        authored=next(e for e in module['elements'] if e['id']==record['type'])
                        primary=next(k for k in authored['keys'] if k.get('primary'))
                        if len(primary['fields'])!=1:raise ValueError('Selected single-field original import key required')
                        key_field=next(e for e in module['elements'] if e['id']==primary['fields'][0]['element'])
                        values={key_field['name']:record['key'],**record['properties']}
                        built=success(capability.object_import_record_in_transaction(tx,document_id=document_id,module_id=module_id,record_id=record['type'],values=tuple(AuthoredValue(name=name,value=TextValue(kind='string',text=value)) for name,value in values.items())))
                        origin=MapValue(entries=())
                        object_report=expect(capability.import_in_transaction(tx,context.input((built,),load_id=step['load_id'],asserted_origin=origin)),ImportReported).report
                        if object_report.status!='processed' or object_report.unprocessed_indices or len(object_report.outcomes)!=1 or not isinstance(object_report.outcomes[0],ImportCreated) or len(object_report.batches)!=1 or not isinstance(object_report.batches[0],PendingBatch):
                            raise AssertionError('Selected object import must complete with one pending created result')
                        reports.append(object_report)
                        endpoints=[]
                        for record_id,key in (('Solution',step['records'][0]['source']),('UseCase',step['records'][0]['target'])):
                            authored=next(e for e in module['elements'] if e['id']==record_id)
                            primary=next(k for k in authored['keys'] if k.get('primary'))
                            found=expect(success(assembly.lookup_key_in_transaction(tx,document_id=document_id,module_id=module_id,record_id=record_id,key_id=primary['id'],values=(key,),original_document=source,bun_executable=bun)),ObjectFound).object
                            endpoints.append(found.identity)
                        if endpoints[0]!=object_report.outcomes[0].identity:raise AssertionError('Imported identity differs from own-transaction key read')
                        relation=next(r for r in module['relationships'] if r['name']==step['records'][0]['relationship'])
                        built=success(capability.edge_import_record_in_transaction(tx,document_id=document_id,module_id=module_id,relationship_id=relation['id'],source_endpoint=endpoints[0],target_endpoint=endpoints[1],values=(),order_key=NullOrderKey()))
                        edge_report=expect(capability.import_in_transaction(tx,context.input((built,),load_id=step['load_id'],asserted_origin=origin)),ImportReported).report
                        if edge_report.status!='processed' or edge_report.unprocessed_indices or len(edge_report.outcomes)!=1 or not isinstance(edge_report.outcomes[0],ImportCreated) or len(edge_report.batches)!=1 or not isinstance(edge_report.batches[0],PendingBatch):
                            raise AssertionError('Selected edge import must complete with one pending created result')
                        reports.append(edge_report)
                    # Keep native reports pending as returned; only the host knows its
                    # outer commit. No combined report, commit evidence or token is invented.
                    imported={'created':sum(int(report.counts.created_pending) for report in reports),'skipped':sum(int(report.counts.skipped) for report in reports),'rejected':sum(int(report.counts.rejected) for report in reports)}
                    if imported!=step['expect']['import']:raise AssertionError('Original import counts differ')
                    continue
                if step['op'] == 'apply':
                    supported={'action.applies-atomically-and-reads-back':'catalog.AddSolution','action.idempotent-retry-returns-the-original':'catalog.AddUseCase','action.update-bumps-the-version-once':'catalog.CorrectSolution','action.dry-run-writes-nothing-and-keeps-the-key':'catalog.AddSolution'}
                    if case['id'] not in supported or step['action']!=supported[case['id']] or not {'op','as','action','inputs','expect'}<=set(step) or set(step)-{'op','as','action','inputs','expect','save','key','dry_run'}:
                        raise ValueError('Unsupported action case or controls; no action write attempted')
                    dry_run=step.get('dry_run',False)
                    if type(dry_run) is not bool or 'dry_run' in step and case['id']!=dry_case:
                        raise ValueError('Unsupported dry-run controls; no action write attempted')
                    if dry_run:
                        if set(step['expect'])!={'validation'} or set(step['expect']['validation'])-{'ok','effects','replay','failure_ids'}:
                            raise ValueError('Unsupported preview observations; no action write attempted')
                    elif set(step['expect'])-{'receipt','refs'} or set(step['expect'].get('receipt',{}))-{'created','linked','updated','replayed','token_is'}:
                        raise ValueError('Unsupported action observation; no action write attempted')
                    if sha256(source).hexdigest()!='849a4fc0ec421110f08ffa24ff366e2b6d9b69d221373357f1bea926c9a25696':
                        raise ValueError('Selected action handler requires the exact retained consumer document')
                    inputs=step['inputs'];case_actor=step['as']
                    updating=step['action']=='catalog.CorrectSolution'
                    record_id='Solution' if step['action'] in ('catalog.AddSolution','catalog.CorrectSolution') else 'UseCase'
                    required_inputs={'solution','level'} if updating else {'code','name','useCase'} if record_id=='Solution' else {'code','name'}
                    if set(inputs)!=required_inputs or any(type(value) is not str for value in inputs.values()):
                        raise ValueError('Selected action inputs are required strings')
                    invocation=(case_actor,step['key']) if 'key' in step else (case_actor,uuid4().hex)
                    if dry_run and invocation in invocations:raise ValueError('Committed-key preview is outside this selected workflow')
                    if invocation in invocations:
                        action,original_inputs,case_input,case_request=invocations[invocation]
                        if action!=step['action'] or original_inputs!=inputs:
                            raise ValueError('Changed-input retry is outside this selected workflow')
                        with transaction(people[case_actor]) as (assembly,tx):
                            applied=expect(success(assembly.apply_in_transaction(tx,case_input,case_request,documents=documents,bun_executable=bun)),GroupSuccess)
                    else:
                        with transaction(people[case_actor],commit=not dry_run) as (assembly,tx):
                            operations=[] if updating else [CreateObject(type_definition_pin=types[record_id].definition_pin,values=tuple(AuthoredValue(name=name,value=TextValue(kind='string',text=inputs[name])) for name in ('code','name')),ownership=RootlessOwnership(),alias='s')]
                            if updating:
                                record=next(e for e in module['elements'] if e['id']=='Solution')
                                primary=next(k for k in record['keys'] if k.get('primary'))
                                target=expect(success(assembly.lookup_key_in_transaction(tx,document_id=document_id,module_id=module_id,record_id='Solution',key_id=primary['id'],values=(inputs['solution'],),original_document=source,bun_executable=bun)),ObjectFound).object
                                operations.append(UpdateObject(target=StoredObjectReference(identity=target.identity),set=(AuthoredValue(name='coverageLevel',value=TextValue(kind='string',text=inputs['level'])),),unset=(),expected_version=str(target.version)))
                                preconditions=(ObjectExists(id='exists',reason='no such solution',target=target.identity),)
                            elif record_id=='Solution':
                                use_case=next(e for e in module['elements'] if e['id']=='UseCase')
                                use_case_key=next(k for k in use_case['keys'] if k.get('primary'))
                                target_result=success(assembly.lookup_key_in_transaction(tx,document_id=document_id,module_id=module_id,record_id='UseCase',key_id=use_case_key['id'],values=(inputs['useCase'],),original_document=source,bun_executable=bun))
                                if dry_run and isinstance(target_result,ObjectNotFound):
                                    archived=expect(success(assembly.accepted_document_in_transaction(tx,document_id=document_id)),AcceptedDocument)
                                    catalog=expect(success(assembly.reader_catalog_in_transaction(tx)),ReaderCatalog)
                                    visible=next((m for m in catalog.modules if m['documentId']==document_id and m['moduleId']==module_id),None)
                                    current_type=next((t for t in visible['types'] if t['recordId']=='UseCase' and t['kind']=='record' and not t['provisional']),None) if visible is not None else None
                                    if archived.content!=source or visible is None or visible['documentSha256']!=sha256(source).hexdigest() or current_type is None or not any(k['typeId']==current_type['typeId'] and k['keyId']==use_case_key['id'] for k in visible['keys']):
                                        raise ValueError('Current authorized fixture/key required for absence observation')
                                    validation={'ok':False,'failure_ids':['use_case_exists']}
                                    if validation!=step['expect']['validation']:raise AssertionError('Original absent-target preview differs')
                                    continue
                                target=expect(target_result,ObjectFound).object
                                relation=next(r for r in module['relationships'] if r['name']=='addresses')
                                reference=success(assembly.get_relationship_reference_in_transaction(tx,document_id=document_id,module_id=module_id,relationship_id=relation['id']))
                                operations.append(CreateEdge(relationship_definition_pin=reference.definition_pin,source=AliasObjectReference(alias='s'),target=StoredObjectReference(identity=target.identity),values=(),order_key=NullOrderKey()))
                                preconditions=(ObjectExists(id='use_case_exists',reason='no such use case',target=target.identity),)
                            else:
                                record=next(e for e in module['elements'] if e['id']==record_id)
                                primary=next(k for k in record['keys'] if k.get('primary'))
                                preconditions=(KeyAbsent(id='fresh',reason='a use case with that code exists',type_definition_pin=types[record_id].definition_pin,key_id=primary['id'],values=(TextValue(kind='string',text=inputs['code']),)),)
                            context=success(assembly.group_context_in_transaction(tx))
                            case_input=context.input(tuple(operations),MapValue(entries=(MapEntry(key='x-action',value=TextValue(kind='string',text=step['action'])),)),preconditions=preconditions)
                            case_request=context.request(step['key'] if 'key' in step else 'consumer-action:'+invocation[1])
                            outcome=success(assembly.groups(assembly.group_selection,documents=documents,bun_executable=bun).capability.apply_in_transaction(tx,case_input,case_request))
                            if dry_run and isinstance(outcome,GroupFailed) and isinstance(outcome.failure,PreconditionFailed):
                                validation={'ok':False,'failure_ids':[f.condition_id for f in outcome.failure.failures]}
                            else:
                                applied=expect(outcome,GroupSuccess)
                                if dry_run:
                                    kinds={'create_object':'Create','create_edge':'Link'}
                                    if any(not isinstance(r,Created) or r.operation not in kinds for r in applied.response.semantic.results):
                                        raise AssertionError('Unexpected native preview effect result')
                                    validation={'ok':True,'effects':[kinds[r.operation] for r in applied.response.semantic.results],'replay':applied.response.disposition=='replayed'}
                        if dry_run:
                            if validation!=step['expect']['validation']:raise AssertionError('Original rollback preview differs')
                            continue
                        invocations[invocation]=(step['action'],dict(inputs),case_input,case_request)
                    # Retain the original request: obtain a committed receipt by retrying
                    # only after the caller's known successful outer commit.
                    with transaction(people[case_actor]) as (assembly,tx):
                        replay=expect(success(assembly.apply_in_transaction(tx,case_input,case_request,documents=documents,bun_executable=bun)),GroupSuccess)
                        committed=expect(replay.response,CommittedReceiptReplay)
                        if committed.semantic!=applied.response.semantic:
                            raise AssertionError('Committed original action semantic result differs')
                    results=applied.response.semantic.results
                    if updating:
                        if len(results)!=1 or not isinstance(results[0],Changed) or results[0].operation!='update_object':
                            raise AssertionError('Original correction must change exactly one object')
                    elif len(results)!=(2 if record_id=='Solution' else 1) or any(not isinstance(result,Created) for result in results):
                        raise AssertionError('Original action must create one object and one edge')
                    receipt={'created':sum(r.operation=='create_object' for r in results),'linked':sum(r.operation=='create_edge' for r in results),'updated':sum(isinstance(r,Changed) and r.operation=='update_object' for r in results),'replayed':applied.response.disposition=='replayed'}
                    solution=next(e for e in module['elements'] if e['id']==record_id)
                    solution_key=next(k for k in solution['keys'] if k.get('primary'))
                    with transaction(people[case_actor],read_only=True) as (assembly,tx):
                        found=expect(success(assembly.lookup_key_in_transaction(tx,document_id=document_id,module_id=module_id,record_id=record_id,key_id=solution_key['id'],values=(inputs['solution'] if updating else inputs['code'],),original_document=source,bun_executable=bun)),ObjectFound).object
                        if found.identity!=results[0].identity:
                            raise AssertionError('Original created identity and business-key read differ')
                    if found.version!=int(results[0].version):
                        raise AssertionError('Created native version and fresh business-key read differ')
                    refs=[{'key':dict(found.values)['code'],'version':int(results[0].version)}]
                    expected_receipt=step['expect']['receipt']
                    receipt_matches=all(committed.receipt_token==tokens[want[1:]] if name=='token_is' else receipt[name]==want for name,want in expected_receipt.items())
                    if not receipt_matches or 'refs' in step['expect'] and refs!=step['expect']['refs']:
                        raise AssertionError('Original action receipt or references differ')
                    if 'save' in step:tokens[step['save']['token']]=committed.receipt_token
                    continue
                if step['op']=='reached':
                    with transaction(people[case_actor],read_only=True) as (assembly,tx):
                        included=expect(success(assembly.reached_in_transaction(tx,tokens[step['token'][1:]])),ReceiptIncluded).included
                    if included!=step['expect']['value']:
                        raise AssertionError('Original action receipt visibility differs')
                    continue
                if step['op'] == 'seed':
                    case_actor = step['as']
                    with transaction(people[case_actor]) as (assembly, tx):
                        operations = []
                        for record in step['records']:
                            if 'type' in record:
                                authored=next(e for e in module['elements'] if e['id']==record['type'])
                                primary=next(k for k in authored['keys'] if k.get('primary'))
                                if len(primary['fields'])!=1:raise ValueError('Selected single-field fixture key required')
                                key_field=next(e for e in module['elements'] if e['id']==primary['fields'][0]['element'])
                                values={key_field['name']:record['key'],**record['properties']}
                                if any(type(value) is not str for value in values.values()):raise ValueError('Selected fixture uses scalar strings')
                                operations.append(CreateObject(type_definition_pin=types[record['type']].definition_pin,values=tuple(AuthoredValue(name=name,value=TextValue(kind='string',text=value)) for name,value in values.items()),ownership=RootlessOwnership(),alias=record['key']))
                                continue
                            relation = next(r for r in module['relationships'] if r['name'] == record['relationship'])
                            reference = success(assembly.get_relationship_reference_in_transaction(tx, document_id=document_id, module_id=module_id, relationship_id=relation['id']))
                            operations.append(CreateEdge(relationship_definition_pin=reference.definition_pin, source=StoredObjectReference(identity=fixture_objects[record['source']]), target=StoredObjectReference(identity=fixture_objects[record['target']]), values=(), order_key=NullOrderKey()))
                        context = success(assembly.group_context_in_transaction(tx))
                        case_input = context.input(tuple(operations), MapValue(entries=()))
                        case_request = context.request(case['id'])
                        expect(success(assembly.apply_in_transaction(tx, case_input, case_request, documents=documents, bun_executable=bun)), GroupSuccess)
                    continue
                if step['op'] == 'sync':
                    if case_input is None:
                        raise ValueError('Sync requires a real public mutation')
                    with transaction(people[case_actor]) as (assembly, tx):
                        replay = expect(success(assembly.apply_in_transaction(tx, case_input, case_request, documents=documents, bun_executable=bun)), GroupSuccess)
                        token = expect(replay.response, CommittedReceiptReplay).receipt_token
                    with transaction(people[case_actor], read_only=True) as (assembly, tx):
                        if not expect(success(assembly.reached_in_transaction(tx, token)), ReceiptIncluded).included:
                            raise AssertionError('Case mutation is not source-visible')
                    continue
                if step['op'] != 'query':
                    raise ValueError('Selected original read step required')
                if 'requires' in step:
                    if not {'type', 'columns'} <= set(step['requires']) or set(step['requires']) - {'type', 'columns', 'relationships', 'count'}:
                        raise ValueError('Unsupported original capability requirement')
                    if 'count' in step['requires'] and step['requires']['count'] is not True:
                        raise ValueError('Selected count capability requires exact True')
                    record = next((e for e in module['elements'] if e['kind'] == 'record'
                        and module['namespace'] + '.' + e['name'] == step['requires']['type']), None)
                    if record is None:
                        raise ValueError('Unknown original type requirement')
                    members = {ref['element'] for ref in record['members'] if ref['module'] == module_id}
                    columns = {e['name'] for e in module['elements'] if e['id'] in members}
                    if any(name not in columns for name in step['requires']['columns']):
                        raise ValueError('Unknown original member requirement')
                    names = set()
                    for relation in module['relationships']:
                        for endpoint, name in (('source', relation['name']), ('target', relation.get('inverse'))):
                            if name and any(ref['module'] == module_id and ref['element'] == record['id']
                                    for ref in relation[endpoint]):
                                names.add(name)
                    if any(name not in names for name in step['requires'].get('relationships', [])):
                        raise ValueError('Unknown original relationship requirement')
                with transaction(people[step['as']], read_only=True) as (assembly, tx):
                    archived=expect(success(assembly.accepted_document_in_transaction(tx,document_id=document_id)),AcceptedDocument)
                    if archived.content!=source:raise AssertionError('Original consumer document bytes differ')
                    if 'limit' in step:
                        cursor = cursors[step['after'][1:]] if 'after' in step else None
                        rows = expect(success(assembly.query_page_in_transaction(tx,sql=step['sql'],document_ids=(document_id,),limit=step['limit'],cursor=cursor)), QueryPage)
                        if (rows.next_cursor is not None) != step['expect']['next_cursor']:
                            raise AssertionError('Original page continuation differs')
                        if 'save' in step:
                            cursors[step['save']['cursor']] = rows.next_cursor
                    else:
                        rows = expect(success(assembly.query_in_transaction(tx, sql=step['sql'], document_ids=(document_id,), read_profile='complete-entity' if case['id'] in ('read.key-lookup-whole-entity','read.relationship-columns-follow-ends','action.applies-atomically-and-reads-back','action.update-bumps-the-version-once','import.entities-before-relationships','import.identity-skip-and-provenance') else None)), QueryRows)
                if not isinstance(rows.as_of,QueryReadPosition) or not rows.as_of.value or rows.as_of.at.tzinfo is None or rows.as_of.at.utcoffset() is None or rows.as_of.semantics!='committed-lower-bound' or rows.as_of.caller_xid_assigned:
                    raise AssertionError('Original read answer needs an aware recorded position with declared semantics')
                if case['id'] in ('read.key-lookup-whole-entity','read.relationship-columns-follow-ends','action.applies-atomically-and-reads-back','action.update-bumps-the-version-once','import.entities-before-relationships','import.identity-skip-and-provenance'):
                    required={'_version','_created_by','_created_at','_updated_by','_updated_at'}
                    if not required <= set(rows.columns):
                        raise AssertionError('Original required whole-object metadata missing')
                expected = step['expect']
                actual_rows = [{name: list(value) if type(value) is tuple else value for name, value in zip(rows.columns, row, strict=True)} for row in rows.rows]
                # The original consumer _check_rows requires equal row count and
                # compares every authored expected field; whole-object expectations
                # deliberately omit other returned fields. Never trim actual rows.
                row_match='rows' not in expected or len(actual_rows)==len(expected['rows']) and all(all(name in actual and actual[name]==value for name,value in wanted.items()) for actual,wanted in zip(actual_rows,expected['rows'],strict=True))
                if not row_match or ('row_count' in expected and len(actual_rows)!=expected['row_count']) or ('columns' in expected and list(rows.columns) != expected['columns']):
                    raise AssertionError(f'Original expected read differs: {case["id"]}; columns={rows.columns!r}; actual={actual_rows!r}; expected={expected!r}')
            observations.append({'id': case['id'], 'requires': [s.get('requires') for s in case['steps']],
                'authority': 'passed', 'replica': 'unavailable', 'replicaReason': 'no qualified replica deployment'})
    return {'scope': 'selected original SQL/action observations; not complete adapter/corpus or interchange',
        'checked':['original SQL','expected row count and fields','expected columns','expected cursor presence','required whole-object metadata fields','answer position/time (committed lower bound)'] + (['selected action receipt and native references','committed original-request recovery','receipt reached'] if any(name.startswith('action.') for name in case_ids) else []) + (['dry-run rollback and unconsumed request key','authenticated absent-target preview'] if dry_case in case_ids else []) + (['original edge-first import input mapped through object-first public calls in one caller transaction','original import counts and relationship readback'] if 'import.entities-before-relationships' in case_ids else []) + (['native mixed-import created/skipped/rejected results','separately host-observed missing relationship endpoint','original import author and load provenance','repeated load invokes native import and skips'] if 'import.identity-skip-and-provenance' in case_ids else []),
        'batchScope':'one native atomic group; unique condition IDs mapped to authored labels; original committed semantic/token replay' if 'action.atomic-batch-is-all-or-nothing' in case_ids else None,
        'notChecked':['replica','complete consumer adapter mapping'],
        'corpusSha256': sha256(original).hexdigest(), 'modelSha256': sha256(source).hexdigest(),
        'fixtureSync': 'committed original receipt included on authority', 'retainedExtensions':retained_extensions,
        'interpretation':'partial; actions/placement/replica semantics unselected', 'observations': observations}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('corpus', type=Path)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--bun', default='bun')
    parser.add_argument('--case', action='append', dest='case_ids', help='Original case ID; unsupported cases fail explicitly')
    args = parser.parse_args()
    print(json.dumps(run_reads(args.corpus, args.directory, bun=args.bun, case_ids=tuple(args.case_ids) if args.case_ids else CASES), sort_keys=True))
