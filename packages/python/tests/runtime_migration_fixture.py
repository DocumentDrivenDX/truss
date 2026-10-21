# SPDX-License-Identifier: MIT OR Apache-2.0
"""Separate-process public fixture producer; import selected wheel, never emulate it."""
import json
import sys
from pathlib import Path
import psycopg
from truss import (Ok,Error,adopt_psycopg_host,create_reference_assembly,
                   CatalogRuntimeConfiguration,CatalogDocument,ModuleAccessGrant)
from truss.contracts import MapValue,TextValue,MapEntry,NullValue
from truss.groups import (CreateObject,AuthoredValue,RootlessOwnership,CreateEdge,
                          StoredObjectReference,NullOrderKey,UpdateObject,RequestNone)
from truss.imports import ImportReported


def required(result,host=None):
    if not isinstance(result,Ok):
        raise RuntimeError(repr(result)+' '+str(getattr(getattr(host,'_custody',None),'last_attempt',None)))
    return result.value


def assembly(connection):
    host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000)
    return host,required(create_reference_assembly(CatalogRuntimeConfiguration(),host)),required(host.adopt_transaction())


def seed(uri,model_path,output):
    source=Path(model_path).read_bytes();document=CatalogDocument('adoc','r1',source)
    with psycopg.connect(uri,autocommit=True,options='-c statement_timeout=10000') as admin:
        admin.execute('BEGIN');host,engine,tx=assembly(admin)
        installed=required(engine.install_in_transaction(tx),host);host.detach();admin.commit()
        for role in ['migration_reader','migration_writer','migration_feed','migration_audit']:
            admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN NOINHERIT').format(psycopg.sql.Identifier(role)))
        admin.execute('CREATE ROLE migration_person LOGIN')
        admin.execute(psycopg.sql.SQL('GRANT {} TO migration_person WITH SET FALSE').format(psycopg.sql.Identifier(installed.registrar_role)))
        params=psycopg.conninfo.conninfo_to_dict(uri);params['user']='migration_person'
        with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as person:
            person.execute('BEGIN');host,engine,tx=assembly(person)
            prepared=engine.prepare_catalog((document,));registered=required(engine.accept_in_transaction(tx,prepared,request_key='migration-model'),host)
            host.detach();person.commit()
        admin.execute('BEGIN');host,engine,tx=assembly(admin)
        required(engine.configure_module_access_in_transaction(tx,(ModuleAccessGrant('adoc','m','migration_reader','migration_writer'),)),host)
        required(engine.register_feed_consumer_in_transaction(tx,consumer_id='migration-feed',reader_role='migration_feed'),host)
        # Public administrative audit facade, actual retained grant row.
        admin.execute("SELECT truss.grant_import_audit_access('adoc','m','migration_audit')")
        host.detach();admin.commit()
        admin.execute('GRANT migration_writer,migration_feed,migration_audit TO migration_person WITH SET FALSE')
        admin.execute(psycopg.sql.SQL('REVOKE {} FROM migration_person').format(psycopg.sql.Identifier(installed.registrar_role)))
        with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as person:
            person.execute('BEGIN');host,engine,tx=assembly(person)
            ref=required(engine.get_type_reference_in_transaction(tx,document_id='adoc',module_id='m',record_id='A'),host)
            context=required(engine.group_context_in_transaction(tx),host)
            operation=CreateObject(type_definition_pin=ref.definition_pin,values=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='one')),AuthoredValue(name='A-value',value=TextValue(kind='string',text='exact-value'))),ownership=RootlessOwnership(),alias='seed')
            request=context.request('migration-seed');semantic=context.input((operation,),MapValue(entries=()))
            result=required(engine.apply_in_transaction(tx,semantic,request,documents=(document,)),host)
            if result.response.semantic.results[0].outcome!='created':raise AssertionError(result)
            identity=result.response.semantic.results[0].identity
            host.detach();person.commit()
            person.execute('BEGIN');host,engine,tx=assembly(person)
            imported_record=required(engine.object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id='B',
                values=(AuthoredValue(name='B-label',value=TextValue(kind='string',text='imported')),
                        AuthoredValue(name='B-value',value=TextValue(kind='string',text='imported')),
                        AuthoredValue(name='future',value=NullValue())),
                source=MapValue(entries=(MapEntry(key='system',value=TextValue(kind='string',text='original-source')),))),host)
            import_context=required(engine.import_context_in_transaction(tx),host)
            imported=engine.import_in_transaction(tx,import_context.input((imported_record,),load_id='migration-load',asserted_origin=MapValue(entries=())),documents=(document,))
            if not isinstance(imported,ImportReported):raise AssertionError(imported)
            imported_identity=imported.report.outcomes[0].identity
            relationship=required(engine.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B'),host)
            group_context=required(engine.group_context_in_transaction(tx),host)
            operations=(CreateEdge(relationship_definition_pin=relationship.definition_pin,source=StoredObjectReference(identity=identity),target=StoredObjectReference(identity=imported_identity),values=(),order_key=NullOrderKey()),
                UpdateObject(target=StoredObjectReference(identity=imported_identity),set=(AuthoredValue(name='B-value',value=TextValue(kind='string',text='updated-import')),),unset=(),expected_version='1'))
            linked=required(engine.apply_in_transaction(tx,group_context.input(operations,MapValue(entries=())),RequestNone(),documents=(document,)),host)
            edge_identity=linked.response.semantic.results[0].identity
            host.detach();person.commit()
            # A real committed ACK protects a non-genesis continuation across upgrade.
            person.execute('BEGIN');host,engine,tx=assembly(person)
            page=required(engine.read_feed_in_transaction(tx,consumer_id='migration-feed'),host)
            acknowledged=required(engine.acknowledge_feed_in_transaction(tx,page),host)
            if acknowledged.outcome!='advanced':raise AssertionError(acknowledged)
            host.detach();person.commit()
        # Independent fixture expectations are retained alongside original IDs/source.
        Path(output).write_text(json.dumps({'installation':installed.installation_id,'owner':installed.owner_role,
            'registrar':installed.registrar_role,'objectId':identity.id,'definitionPin':ref.definition_pin,
            'document':source.decode(),'registeredRevision':registered.revision,'label':'one','value':'exact-value',
            'importedId':imported_identity.id,'edgeId':edge_identity.id},indent=2)+'\n')


if __name__=='__main__':seed(*sys.argv[1:])
