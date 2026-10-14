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


def run(model_path,output,bun,*,bootstrap_source_epoch=False):
    source_epoch=None
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
    (output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--bun',default='bun')
    parser.add_argument('--bootstrap-source-epoch',action='store_true');args=parser.parse_args()
    run(args.model,args.output,args.bun,bootstrap_source_epoch=args.bootstrap_source_epoch)
