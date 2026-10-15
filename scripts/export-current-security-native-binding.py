"""Exact named owner source -> public catalog/seed/readback -> actual binding.

Disposable PG18 only. No source editing, synthetic layout or security admission.
A typed admission refusal is retained as such, without fabricating a binding.
"""
import argparse
from dataclasses import asdict
from hashlib import sha256
from importlib.resources import files
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'packages/python/examples'))
from adopter_workflow import transaction,success,expect
import psycopg
from psycopg import sql
from truss import CatalogDocument,LocalPostgres,ModuleAccessGrant,ObjectFound,Error,CatalogRegistration
from truss.contracts import MapValue,TextValue,BooleanValue
from truss.groups import AuthoredValue,CreateObject,RootlessOwnership,GroupSuccess
from truss.catalog_runtime import _release,_pin_cursor

_SOURCE='2216a7ad3093c90437db035fb337d21ac67589dee5eb148b0eb4d7fd1ff75059'
_SCENARIOS='de7e5a72f59fde30b5d57704f9f1513bafbf0e77a8f9094ae566fbbd582ecc3f'


def _bytes(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf8')


def _input(value):
    if type(value) is not dict or len(value)!=1:raise ValueError('Original exact scalar required')
    if set(value)=={'string'} and type(value['string']) is str:return TextValue(kind='string',text=value['string'])
    if set(value)=={'integerToken'} and type(value['integerToken']) is str:return TextValue(kind='integer',text=value['integerToken'])
    if set(value)=={'boolean'} and type(value['boolean']) is bool:return BooleanValue(value=value['boolean'])
    raise ValueError('Original selected String/Integer/Boolean seed required')


def _literal(value):
    if type(value) is str:return {'string':value}
    if type(value) is bool:return {'boolean':value}
    if type(value) is TextValue and value.kind=='integer':return {'integerToken':value.text}
    raise ValueError('Complete original scalar readback required')


def run(source_path,scenarios_path,output,bun='bun'):
    output=output.resolve()
    if output.exists() and any(output.iterdir()):raise ValueError('New empty output directory required')
    original=source_path.read_bytes();scenario_bytes=scenarios_path.read_bytes()
    if sha256(original).hexdigest()!=_SOURCE or sha256(scenario_bytes).hexdigest()!=_SCENARIOS:
        raise ValueError('Exact committed named owner source/scenarios required')
    source=json.loads(original);scenarios=json.loads(scenario_bytes)
    if scenarios['baseFixtureSha256']!=_SOURCE or len(source['closure']['documents'])!=1:
        raise ValueError('Original source/scenario correspondence required')
    entry=source['closure']['documents'][0];document=entry['document'];content=_bytes(document)
    content_sha=sha256(content).hexdigest();logical_revision=entry['revision']
    documents=(CatalogDocument(document['id'],logical_revision,content,content_sha),)
    fields={(m['id'],e['id']):e for m in document['modules'] for e in m['elements'] if e['kind']=='field'}
    facts=scenarios['cut']['facts']
    output.mkdir(parents=True,exist_ok=True)
    for name,raw in (('original-source.json',original),('original-read-scenarios.json',scenario_bytes),('original-core.json',content)):
        (output/name).write_bytes(raw)
    manifest,digest,_=_release()
    manifest_bytes=files('truss').joinpath('_catalog_runtime/manifest.json').read_bytes()
    if sha256(manifest_bytes).hexdigest()!=digest:raise ValueError('Original runtime manifest bytes required')
    report={'status':'pending','authority':False,'securityReady':False,'sourceSha256':_SOURCE,'scenariosSha256':_SCENARIOS,
        'coreExtraction':{'pointer':'/closure/documents/0/document','serialization':'UTF-8 compact JSON; original object/list order and values retained; exact original envelope archived',
                          'logicalRevision':logical_revision,'contentSha256':content_sha},
        'runtime':manifest['releaseId'],'runtimeSha256':digest,'layout':manifest['layoutProfile'],
        'scope':'Public catalog/mutation/readback and actual native layout only. No installed policy/ontology/protection, Subject mapping, token implementation or current-query authority.'}
    def finish():
        report['artifacts']={p.name:sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file() and p.suffix=='.json' and p.name!='receipt.json'}
        (output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
        return report
    with LocalPostgres(output/'postgres') as runtime:
        params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
        with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as admin:
            with transaction(admin) as (assembly,tx):installed=success(assembly.install_in_transaction(tx))
            admin.execute('CREATE ROLE named_query_person LOGIN;CREATE ROLE named_query_reader NOLOGIN;CREATE ROLE named_query_writer NOLOGIN')
            admin.execute(sql.SQL('GRANT {} TO named_query_person WITH SET FALSE').format(sql.Identifier(installed.registrar_role)))
            with psycopg.connect(**dict(params,user='named_query_person'),autocommit=True,options='-c statement_timeout=10000') as person:
                with transaction(person) as (assembly,tx):
                    prepared=assembly.prepare_catalog(documents,source_version='0.8.0',bun_executable=bun)
                    (output/'original-prepared-acceptance.json').write_bytes(prepared.input_bytes)
                    accepted=assembly.accept_in_transaction(tx,prepared,request_key='named-current-source',bun_executable=bun)
                    if isinstance(accepted,Error):
                        report.update(status='refused',stage='accept_in_transaction',failure=asdict(accepted.error))
                        report['catalogHead']=admin.execute('SELECT rev FROM truss.schema_head WHERE id=1').fetchone()[0]
                        report['acceptedDocumentCount']=admin.execute('SELECT count(*) FROM truss.schema_doc').fetchone()[0]
                        return finish()
                    registration=expect(success(accepted),CatalogRegistration)
                    (output/'accepted-report.json').write_bytes(registration.report_bytes)
                with transaction(admin) as (assembly,tx):
                    success(assembly.configure_module_access_in_transaction(tx,tuple(ModuleAccessGrant(document['id'],m['id'],'named_query_reader','named_query_writer') for m in document['modules'])))
                admin.execute('GRANT named_query_reader,named_query_writer TO named_query_person WITH SET FALSE')
                admin.execute(sql.SQL('REVOKE {} FROM named_query_person').format(sql.Identifier(installed.registrar_role)))
                with transaction(person) as (assembly,tx):
                    operations=[]
                    for fact in facts:
                        target=fact['type']
                        if target['documentId']!=document['id'] or fact['absent']:raise ValueError('Exact complete seed Record required')
                        reference=success(assembly.get_type_reference_in_transaction(tx,document_id=target['documentId'],module_id=target['moduleId'],record_id=target['elementId']))
                        if reference is None:raise ValueError('Actual accepted original Record required')
                        values=[]
                        for member in fact['fields']:
                            field=member['field']
                            if field['documentId']!=document['id']:raise ValueError('Original field document required')
                            values.append(AuthoredValue(name=fields[(field['moduleId'],field['elementId'])]['name'],value=_input(member['value'])))
                        operations.append(CreateObject(type_definition_pin=reference.definition_pin,values=tuple(values),ownership=RootlessOwnership()))
                    context=success(assembly.group_context_in_transaction(tx))
                    applied=expect(success(assembly.apply_in_transaction(tx,context.input(tuple(operations),MapValue(entries=())),context.request('named-current-seed'),documents=documents,bun_executable=bun)),GroupSuccess)
                    identities=tuple(item.identity for item in applied.response.semantic.results)
                readbacks=[]
                with transaction(person,read_only=True) as (assembly,tx):
                    accepted_source=success(assembly.accepted_document_in_transaction(tx,document_id=document['id']))
                    if accepted_source.content!=content or accepted_source.sha256!=content_sha or accepted_source.document_revision!=logical_revision:
                        raise ValueError('Exact accepted source/revision/digest correspondence required')
                    for fact,identity in zip(facts,identities,strict=True):
                        target=fact['type']
                        obj=expect(success(assembly.get_object_in_transaction(tx,document_id=document['id'],module_id=target['moduleId'],record_id=target['elementId'],object_id=int(identity.id))),ObjectFound).object
                        if obj.ownership.state!='rootless':raise ValueError('Original rootless seed ownership required')
                        actual={name:_literal(value) for name,value in obj.values}
                        expected={fields[(v['field']['moduleId'],v['field']['elementId'])]['name']:v['value'] for v in fact['fields']}
                        if actual!=expected or obj.retained:raise ValueError('Complete original seed values required')
                        key=expect(success(assembly.lookup_key_in_transaction(tx,document_id=document['id'],module_id=target['moduleId'],record_id=target['elementId'],key_id='pk',values=tuple(_input(value) for value in fact['key']),original_document=content,bun_executable=bun)),ObjectFound)
                        if key.object.id!=obj.id:raise ValueError('Original business Key must resolve actual object')
                        readbacks.append({'originalFact':fact,'nativeId':str(obj.id),'nativeTypeId':str(obj.type_id),'nativeVersion':str(obj.version),'values':actual})
                    def export(cursor,observed):
                        _pin_cursor(cursor)
                        cursor.execute('SELECT truss.query_binding(%s::jsonb,%s,%s,%s,%s,%s)',(json.dumps([document['id']]),10000,10000,16777216,manifest['releaseId'],digest),prepare=False)
                        rows=cursor.fetchmany(2)
                        if len(rows)!=1:raise ValueError('One actual binding required')
                        return bytes(rows[0][0])
                    bundle_bytes=success(assembly._host._run_operation(tx,export))
                bundle=json.loads(bundle_bytes);binding=bundle['bindingJson'].encode('utf8')
                if json.loads(binding)!=bundle['binding'] or bundle['binding']['releaseId']!=manifest['releaseId'] or bundle['binding']['releaseSha256']!=digest:
                    raise ValueError('Exact actual native binding required')
                if any(field['identity']['element']=='clear' for record in bundle['binding']['records'] for field in record['fields']):
                    raise ValueError('Declaration-only clear must have no storage property')
                report.update(status='exported',actorOid=bundle['actorOid'],catalogRevision=accepted_source.catalog_revision,
                    revisionCorrespondence={'originalLogicalRevision':logical_revision,'acceptedDocumentRevision':accepted_source.document_revision,'acceptedContentSha256':accepted_source.sha256,'artifactIdentity':accepted_source.artifact_identity})
                for name,raw in (('accepted-document.json',accepted_source.content),('native-query-bundle.json',bundle_bytes),('native-binding.json',binding),
                    ('native-runtime-manifest.json',manifest_bytes),('seed-readbacks.json',_bytes(readbacks)),('original-owner-storage.json',_bytes(source['owner']))):
                    (output/name).write_bytes(raw)
    return finish()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('scenarios',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--bun',default='bun');args=parser.parse_args()
    result=run(args.source,args.scenarios,args.output,args.bun)
    print(json.dumps(result,indent=2))
    sys.exit(0 if result['status']=='exported' else 2)
