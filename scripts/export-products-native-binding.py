# SPDX-License-Identifier: MIT OR Apache-2.0
"""Accept original demo bytes and export observed native bindings on disposable PG18.

No protected RR/bulk claim. Role setup is installation operations; objects and
catalog acceptance use actual public Truss APIs. Never infer allocated IDs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'packages/python/examples'))
from adopter_workflow import transaction,success,expect
import psycopg
from psycopg import sql
from truss import CatalogDocument,LocalPostgres,ModuleAccessGrant,ObjectFound
from truss.contracts import MapValue,TextValue
from truss.groups import AuthoredValue,CreateObject,RootlessOwnership,GroupSuccess
from truss.catalog_runtime import _release,_pin_cursor


def run(model_path,output,bun,*,bootstrap_source_epoch=False,install_seal_storage=False,register_action_store=False,register_preparation_program=False):
    source_epoch=None;seal_storage=None;action_store=None
    output=output.resolve()
    if output.exists() and any(output.iterdir()):raise ValueError('New empty output directory required')
    output.mkdir(parents=True,exist_ok=True)
    original=model_path.read_bytes();packet=json.loads(original)
    snapshot=packet['configuration']['actions'][0]['snapshot']
    content=snapshot['utf8'].encode('utf8')
    if hashlib.sha256(content).hexdigest()!=snapshot['sha256']:raise ValueError('Original model snapshot digest required')
    document=json.loads(content)
    if document['umf']!='0.8.0' or document['id']!='product-action-demo':raise ValueError('Original demo core0.8 model required')
    documents=(CatalogDocument(document['id'],snapshot['sha256'],content,snapshot['sha256']),)
    manifest,digest,_=_release()
    with LocalPostgres(output/'postgres') as runtime:
        params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
        with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as admin:
            with transaction(admin) as (assembly,tx):installed=success(assembly.install_in_transaction(tx))
            admin.execute('CREATE ROLE products_person LOGIN')
            admin.execute('CREATE ROLE products_reader NOLOGIN')
            admin.execute('CREATE ROLE products_writer NOLOGIN')
            admin.execute(sql.SQL('GRANT {} TO products_person WITH SET FALSE').format(sql.Identifier(installed.registrar_role)))
            with psycopg.connect(**dict(params,user='products_person'),autocommit=True,options='-c statement_timeout=10000') as person:
                with transaction(person) as (assembly,tx):
                    prepared=assembly.prepare_catalog(documents,source_version='0.8.0',bun_executable=bun)
                    registered=success(assembly.accept_in_transaction(tx,prepared,request_key='original-products',bun_executable=bun))
                    if not hasattr(registered,'registration_id'):raise ValueError('Original catalog acceptance required')
                with transaction(admin) as (assembly,tx):
                    success(assembly.configure_module_access_in_transaction(tx,(ModuleAccessGrant(document['id'],'sales','products_reader','products_writer'),)))
                admin.execute('GRANT products_reader,products_writer TO products_person WITH SET FALSE')
                admin.execute(sql.SQL('REVOKE {} FROM products_person').format(sql.Identifier(installed.registrar_role)))
                if bootstrap_source_epoch:
                    from truss._preparation_source_epoch import bootstrap_preparation_source_marker_in_transaction,issue_initial_preparation_source_epoch_in_transaction
                    from truss._security_source_epoch_installation import bootstrap_source_epoch_infrastructure_in_transaction
                    with transaction(admin) as (assembly,tx):
                        marker=success(bootstrap_preparation_source_marker_in_transaction(assembly._host,tx))
                        infrastructure=success(bootstrap_source_epoch_infrastructure_in_transaction(assembly._host,tx,installation_identity=marker.installation_id.encode()))
                        source_epoch=success(issue_initial_preparation_source_epoch_in_transaction(assembly._host,tx,marker=marker,infrastructure=infrastructure))
                    with transaction(admin,read_only=True) as (assembly,tx):
                        def verify_epoch(cursor,observed):
                            _pin_cursor(cursor)
                            cursor.execute('SELECT r.installation_id,r.source_epoch,r.target_incarnation,r.profile_bytes,r.evidence_bytes FROM truss.source_epoch_registry r JOIN truss.source_epoch_current c ON c.installation_id=r.installation_id AND c.source_epoch=r.source_epoch WHERE c.singleton_id=1',prepare=False)
                            cut=source_epoch.comparison
                            if cursor.fetchmany(2)!=[(cut.installation,cut.epoch,cut.incarnation,cut.profile,cut.evidence)]:raise ValueError('Committed original metadata epoch readback required')
                        success(assembly._host._run_operation(tx,verify_epoch))
                if register_action_store:
                    from truss._action_store import register_action_store_in_transaction,observe_action_store_in_transaction,verify_action_store_context_with_cursor,ActionStoreObservation
                    from truss import Error
                    with transaction(admin) as (assembly,tx):
                        pending_store=success(register_action_store_in_transaction(assembly._host,tx,tenant='products-tenant',registration_key=b'original-products-store',executor_roles=('products_person',)))
                        before_commit=observe_action_store_in_transaction(assembly._host,tx,registration_key=b'original-products-store')
                        if not isinstance(before_commit,Error):raise ValueError('Uncommitted store cannot become issued context')
                    with transaction(person) as (assembly,tx):
                        action_store=success(observe_action_store_in_transaction(assembly._host,tx,registration_key=b'original-products-store'))
                        if not isinstance(action_store,ActionStoreObservation) or not action_store.binding_matches or action_store.receipt_bytes!=pending_store.receipt_bytes:raise ValueError('Original committed store readback required')
                        success(assembly._host._run_operation(tx,lambda cursor,observed:verify_action_store_context_with_cursor(cursor,action_store)))
                    with transaction(admin) as (assembly,tx):
                        replayed_store=success(register_action_store_in_transaction(assembly._host,tx,tenant='products-tenant',registration_key=b'original-products-store',executor_roles=('products_person',)))
                        if replayed_store.receipt_bytes!=pending_store.receipt_bytes:raise ValueError('Registration retry must preserve original namespace')
                        if not isinstance(register_action_store_in_transaction(assembly._host,tx,tenant='products-tenant',registration_key=b'new-store-key',executor_roles=('products_person',)),Error):raise ValueError('Different key must not replace original logical store')
                    with psycopg.connect(**dict(params,user='products_person'),autocommit=True,options='-c statement_timeout=10000') as reopened:
                        with transaction(reopened) as (assembly,tx):
                            again=success(observe_action_store_in_transaction(assembly._host,tx,registration_key=b'original-products-store'))
                            if again!=action_store:raise ValueError('Original store identity must survive connection reopen')
                    for query in ('SELECT * FROM truss.action_store_registration',"INSERT INTO truss.action_store_registration(singleton) VALUES(true)","SELECT truss.register_action_store_original('x'::bytea,'x'::bytea,ARRAY[]::oid[],'x','x'::bytea)"):
                        try:person.execute(query)
                        except psycopg.errors.InsufficientPrivilege:pass
                        else:raise ValueError('Ordinary caller cannot forge or issue a store')
                if install_seal_storage:
                    from truss._preparation_seal_installation import bootstrap_preparation_seal_storage_in_transaction,verify_preparation_seal_storage_with_cursor
                    with transaction(admin) as (assembly,tx):
                        seal_storage=success(bootstrap_preparation_seal_storage_in_transaction(assembly._host,tx))
                    with transaction(admin,read_only=True) as (assembly,tx):
                        def verify_seal(cursor,observed):
                            actual=verify_preparation_seal_storage_with_cursor(cursor,owner_oid=seal_storage.owner_oid)
                            if actual!=(seal_storage.table_oid,seal_storage.sequence_oid):raise ValueError('Committed original seal storage readback required')
                        success(assembly._host._run_operation(tx,verify_seal))
                    denied=person.execute("SELECT pg_catalog.has_table_privilege(current_user,'truss.runtime_preparation_seal','SELECT'),pg_catalog.has_table_privilege(current_user,'truss.runtime_preparation_seal','INSERT'),pg_catalog.has_sequence_privilege(current_user,'truss.runtime_preparation_seal_seq','USAGE')").fetchall()
                    if denied!=[(False,False,False)]:raise ValueError('Ordinary person seal read/write/allocation must remain unavailable')
                with transaction(person) as (assembly,tx):
                    reference=success(assembly.get_type_reference_in_transaction(tx,document_id=document['id'],module_id='sales',record_id='products'))
                    if reference is None:raise ValueError('Actual accepted products definition required')
                    context=success(assembly.group_context_in_transaction(tx))
                    operations=tuple(CreateObject(type_definition_pin=reference.definition_pin,
                        values=(AuthoredValue(name='id',value=TextValue(kind='string',text=key)),AuthoredValue(name='name',value=TextValue(kind='string',text=name))),
                        ownership=RootlessOwnership()) for key,name in [('bar','old'),('baz','keep')])
                    applied=expect(success(assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),context.request('products-seed'),documents=documents,bun_executable=bun)),GroupSuccess)
                    identities=tuple(r.identity for r in applied.response.semantic.results)
                with transaction(person,read_only=True) as (assembly,tx):
                    for identity,expected_name in zip(identities,('old','keep'),strict=True):
                        found=expect(success(assembly.get_object_in_transaction(tx,document_id=document['id'],module_id='sales',record_id='products',object_id=int(identity.id))),ObjectFound)
                        if dict(found.object.values)['name']!=expected_name:raise ValueError('Original public object readback required')
                    def export(cursor,observed):
                        _pin_cursor(cursor)
                        cursor.execute('SELECT truss.query_binding(%s::jsonb,%s,%s,%s,%s,%s)',(json.dumps([document['id']]),10000,10000,16777216,manifest['releaseId'],digest),prepare=False)
                        rows=cursor.fetchmany(2)
                        if len(rows)!=1:raise ValueError('Original complete native query binding required')
                        return bytes(rows[0][0])
                    bundle_bytes=success(assembly._host._run_operation(tx,export))
                if register_preparation_program:
                    import weft
                    from dataclasses import replace
                    from truss._preparation_program import compile_preparation_program,register_preparation_program_in_transaction
                    if action_store is None:raise ValueError('Original committed action store required')
                    source_packet=json.loads(original)
                    binding_text=json.loads(bundle_bytes)['bindingJson']
                    binding_artifact=json.dumps({'mediaType':'application/json','utf8':binding_text,'sha256':hashlib.sha256(binding_text.encode()).hexdigest()},separators=(',',':')).encode()
                    program=compile_preparation_program(weft.MutationCompiler,
                        compiler_source_pin='c0c6449481a87eed38d3f7a6ebebc1f4ab4beeb4',
                        configuration=json.dumps(source_packet['configuration'],separators=(',',':')).encode(),
                        request=json.dumps(source_packet['request'],separators=(',',':')).encode(),
                        binding_artifact=binding_artifact,evidence=('Original same-installation products binding; byte enrollment only',))
                    with transaction(admin) as (assembly,tx):
                        enrolled=success(register_preparation_program_in_transaction(assembly._host,tx,store_context=action_store,registration_key=b'products-program',program=program))
                    with transaction(admin) as (assembly,tx):
                        replayed=success(register_preparation_program_in_transaction(assembly._host,tx,store_context=action_store,registration_key=b'products-program',program=program))
                        if replayed!=enrolled:raise ValueError('Exact original program registration retry required')
                        changed=replace(program,configuration=program.configuration+b' ')
                        if not isinstance(register_preparation_program_in_transaction(assembly._host,tx,store_context=action_store,registration_key=b'products-program',program=changed),Error):raise ValueError('Changed original bytes must conflict on retry')
                    row=admin.execute('SELECT program_identity::text,original_configuration,original_request,original_plan_artifact,original_binding_artifact,original_lowering FROM truss.preparation_program_registration').fetchone()
                    if json.loads(enrolled.program_identity)!=row[0] or row[1:]!=(program.configuration,program.request,program.compile_response,program.binding_artifact,program.lowering):raise ValueError('Committed original program bytes required')
                    try:person.execute('SELECT * FROM truss.preparation_program_registration')
                    except psycopg.errors.InsufficientPrivilege:pass
                    else:raise ValueError('Ordinary caller cannot read private compiler packet')
                    for label,raw in [('configuration',program.configuration),('request',program.request),('compile-response',program.compile_response),('binding',program.binding_artifact),('lowering-invocation',program.lowering)]:
                        (output/('program-'+label+'.json')).write_bytes(raw)
                    (output/'program-registration.json').write_text(json.dumps({'programIdentity':json.loads(enrolled.program_identity),'authority':False,'scope':'Trusted administrative original compiler byte enrollment; not native program admission.'},indent=2)+'\n')
    bundle=json.loads(bundle_bytes)
    binding=bundle['bindingJson'].encode('utf8')
    if json.loads(binding)!=bundle['binding'] or bundle['binding']['releaseId']!=manifest['releaseId'] or bundle['binding']['releaseSha256']!=digest:
        raise ValueError('Actual matching native runtime binding required')
    artifacts={'original-demo-model.json':original,'accepted-document.json':content,
        'original-prepared-acceptance.json':prepared.input_bytes,'native-query-bundle.json':bundle_bytes,'native-binding.json':binding,
        'native-runtime-manifest.json':json.dumps(manifest,indent=2).encode('utf8')+b'\n'}
    for name,raw in artifacts.items():(output/name).write_bytes(raw)
    report={'scope':'Actual ordinary-person RC catalog/public mutation/readback and native binding export. No action, RR selection, bulk seal or security qualification.',
        'runtime':manifest['releaseId'],'runtimeSha256':digest,'layout':manifest['layoutProfile'],
        'documentSha256':snapshot['sha256'],'nativeObjectIds':[v.id for v in identities],
        'preparationOwnerRevision':prepared.provenance.owner_revision,
        'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in artifacts.items()}}
    if source_epoch is not None:
        cut=source_epoch.comparison
        report['metadataSourceEpoch']={'installation':cut.installation,'epoch':cut.epoch,'incarnation':cut.incarnation,'profile':json.loads(cut.profile),'evidence':json.loads(cut.evidence),'securityReady':False,'scope':'Committed catalog metadata and original runtime source only; not authority or bulk execution.'}
    if seal_storage is not None:
        report['sealStorage']={'installation':seal_storage.installation_id,'sourceSha256':seal_storage.source_sha256,'tableOid':seal_storage.table_oid,'sequenceOid':seal_storage.sequence_oid,'securityReady':False,'scope':'Committed private UMF-exported storage only; no seal writer or authority. Ordinary read/write/sequence usage unavailable.'}
    if action_store is not None:
        report['actionStore']={'receiptHex':action_store.receipt_bytes.hex(),'bindingCorrespondence':action_store.binding_correspondence,'authority':False,'scope':'Committed original shared store registration and reopen/retry; not authenticated action, permit or bulk execution.'}
    (output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--bun',default='bun')
    parser.add_argument('--bootstrap-source-epoch',action='store_true')
    parser.add_argument('--install-seal-storage',action='store_true')
    parser.add_argument('--register-action-store',action='store_true')
    parser.add_argument('--register-preparation-program',action='store_true');args=parser.parse_args()
    run(args.model,args.output,args.bun,bootstrap_source_epoch=args.bootstrap_source_epoch,install_seal_storage=args.install_seal_storage,register_action_store=args.register_action_store,register_preparation_program=args.register_preparation_program)
