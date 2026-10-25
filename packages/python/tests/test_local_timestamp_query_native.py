# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public local/date/instant carrier acceptance, create and guarded read proof."""
from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch
import json
import os
from pathlib import Path
import psycopg

from truss import (CatalogDocument, CatalogRuntimeConfiguration, ModuleAccessGrant, Ok,
                   ObjectFound, adopt_psycopg_host,
                   create_reference_assembly)
from truss._catalog_source_reference import TEMPORAL_PROFILE
from truss.contracts import LocalTimestampValue, MapValue, NullValue, TextValue
from truss.groups import AuthoredValue, GroupSuccess, RootlessOwnership, CreateObject, RequestNone
import test_object_mutations_native as base
from test_catalog_relational_support import relational_document


class LocalTimestampQueryTests(base.ObjectMutationTests):
    for _name in tuple(n for n in dir(base.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name] = None

    @classmethod
    def setUpClass(cls):
        worker=os.environ.get('TRUSS_NATIVE_WORKER')
        if worker:
            from native_fixture import DatabaseFixture
            from types import SimpleNamespace
            cls._shared_worker_fixture=DatabaseFixture(Path(worker))
            cls.addClassCleanup(cls._shared_worker_fixture.cleanup)
            cls.info=SimpleNamespace(connection_uri=cls._shared_worker_fixture.get_uri())
            return
        cls._shared_worker_fixture=None
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        if cls._shared_worker_fixture is not None:
            return
        super().tearDownClass()

    def temporal_fields(self, source):
        source['vocabularies']={'umf.access':{'version':'0.1.0'}}
        module=source['modules'][0]
        for name,scalar,nullability in (('A-on','date','absent-allowed'),
                                         ('A-at','timestamp','required'),
                                         ('A-local','timestamp','absent-allowed')):
            module['elements'].append({'id':name,'name':name,'kind':'field','scalarType':scalar,
                'nullability':nullability,'cardinality':'one','extensions':{}})
            next(e for e in module['elements'] if e['id']=='A')['members'].append({'module':'m','element':name})
        views=[]
        for record in (e for e in module['elements'] if e['kind']=='record'):
            fields=[]
            key_fields={tuple((f['module'],f['element'])) for key in record['keys'] for f in key['fields']}
            for member in record['members']:
                field=next(e for e in module['elements'] if e['id']==member['element'])
                optional=field['nullability']=='absent-allowed'
                view={'field':member,'row':{'missing':optional,'null':optional},
                    'create':{'missing':optional,'null':optional},
                    'mutable':(member['module'],member['element']) not in key_fields,'generated':False}
                if field['scalarType']=='timestamp':
                    view['temporal']='local' if field['id']=='A-local' else 'instant'
                fields.append(view)
            views.append({'record':{'module':record and 'm','element':record['id']},
                'selectedKey':{'module':'m','element':record['id'],'key':'a-primary'},'fields':fields})
        module['extensions']={'umf.access':{'views':views,'columns':[],'search':[],'searchBindings':[]}}

    def ready(self, mutate_source=None, *, document_ids=('adoc',), support_profile=TEMPORAL_PROFILE):
        self.install()
        connection,host,assembly,tx=self.consumer()
        documents=[]
        for identity in document_ids:
            source=deepcopy(relational_document());source['id']=identity
            self.temporal_fields(source)
            if mutate_source is not None:mutate_source(source)
            documents.append(CatalogDocument(identity,'r1',json.dumps(source,indent=2).encode()))
        prepared=assembly.prepare_catalog(tuple(documents),source_version='0.10.0',
            support_profile=support_profile,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.prepared=prepared
        self.documents=tuple(d.document for d in prepared.documents)
        registered=assembly.accept_in_transaction(tx,prepared,request_key='temporal-model')
        self.assertIsInstance(registered,Ok,repr(registered)+' '+str(host._custody.last_attempt.error))
        self.registered=registered.value
        view=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request()).value.view
        self.types={(d.reference.owner.document_id,d.reference.authored_identity):d.reference
            for d in view.definitions if d.reference.kind=='type'}
        host.detach();connection.commit()
        for role in ('group_reader','group_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        configured=self.assembly.configure_module_access_in_transaction(self.tx,
            (ModuleAccessGrant('adoc','m','group_reader','group_writer'),))
        self.assertIsInstance(configured,Ok);self.host.detach();self.admin.commit()
        self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        return self.consumer()

    def create_temporal(self, label, instant, local, date_value):
        operation=self.create(label=label,alias=label)
        return replace(operation,values=operation.values+(
            AuthoredValue(name='A-at',value=TextValue(kind='timestamp',text=instant)),
            AuthoredValue(name='A-local',value=local),
            AuthoredValue(name='A-on',value=date_value)))

    def test_public_accept_apply_read_all_temporal_families_and_presence(self):
        connection,host,assembly,tx=self.ready()
        context=assembly.group_context_in_transaction(tx).value
        operations=(
            self.create_temporal('both','2024-01-01T00:00:00.123456Z',
                LocalTimestampValue(text='2024-01-01T09:00:00.000001'),TextValue(kind='date',text='2024-01-01')),
            self.create_temporal('none','2024-01-02T00:00:00Z',NullValue(),NullValue()),
            replace(self.create(label='missing',alias='missing'),values=self.create(label='missing',alias='missing').values+(
                AuthoredValue(name='A-at',value=TextValue(kind='timestamp',text='2024-01-03T00:00:00Z')),)),
        )
        probes=self.admin.execute("SELECT p.name,p.scalar_type,p.nullability,truss.valid_property_definition(p),truss.valid_property_value(v.cell,p) FROM truss.prop_def p JOIN (VALUES ('A-at','{\"kind\":\"timestamp\",\"text\":\"2024-01-01T00:00:00.123456Z\"}'::jsonb),('A-local','{\"kind\":\"localTimestamp\",\"text\":\"2024-01-01T09:00:00.000001\"}'::jsonb),('A-on','{\"kind\":\"date\",\"text\":\"2024-01-01\"}'::jsonb)) v(name,cell) ON v.name=p.name ORDER BY p.name").fetchall()
        self.assertEqual(len(probes),3,repr(probes))
        self.assertTrue(all(row[3] and row[4] for row in probes),repr(probes))
        self.assertEqual(next(row[1] for row in probes if row[0]=='A-local'),'localTimestamp',repr(probes))
        identities=[]
        for operation in operations:
            applied=assembly.apply_in_transaction(tx,context.input((operation,),MapValue(entries=())),
                RequestNone(),documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
            self.assertIsInstance(applied,Ok,repr(applied));self.assertIsInstance(applied.value,GroupSuccess,repr(applied))
            identities.append(applied.value.response.semantic.results[0].identity)
        identity=identities[0]
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        read=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(read.value,ObjectFound,repr(read))
        values=dict(read.value.object.values)
        self.assertEqual(values['A-local'],LocalTimestampValue(text='2024-01-01T09:00:00.000001'))
        self.assertEqual(values['A-on'],TextValue(kind='date',text='2024-01-01'))
        self.assertEqual(values['A-at'],TextValue(kind='timestamp',text='2024-01-01T00:00:00.123456Z'))
        null_identity=identities[1]
        null_read=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(null_identity.id))
        self.assertIsInstance(null_read.value,ObjectFound,repr(null_read))
        null_values=dict(null_read.value.object.values)
        # get_object's established generic carrier renders JSON null as None;
        # the checked temporal query surface preserves the richer NullValue
        # envelope separately.
        self.assertIsNone(null_values['A-local'])
        self.assertIsNone(null_values['A-on'])
        missing_identity=identities[2]
        missing_read=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(missing_identity.id))
        self.assertIsInstance(missing_read.value,ObjectFound,repr(missing_read))
        missing_values=dict(missing_read.value.object.values)
        self.assertNotIn('A-local',missing_values)
        self.assertNotIn('A-on',missing_values)
        host.detach();connection.rollback()

    def test_new_instant_profile_has_finite_known_offset_grammar(self):
        # Exercise the installed native helper directly. The legacy timestamp
        # helper remains a separate contract and is deliberately not changed.
        c,host,assembly,tx=self.ready()
        for token in ('0001-01-01T00:00:00Z','2024-02-29T12:34:56.123456000+01:30',
                      '9999-12-31T23:59:59.999999Z'):
            self.assertIsNotNone(c.execute('SELECT truss.query_temporal_instant_key(%s)',(token,)).fetchone()[0])
        for token in ('1970-01-01T00:00:00-00:00','0001-01-01T00:00:00+00:01',
                      '9999-12-31T23:59:59-00:01','2024-01-01t00:00:00Z',
                      '2024-01-01T00:00:00z','1900-02-29T00:00:00Z',
                      '2024-01-01T00:00:00.1234561Z','2024-01-01T00:00:00.1234560001Z'):
            with self.assertRaises(psycopg.Error) as raised:
                with c.transaction():
                    c.execute('SELECT truss.query_temporal_instant_key(%s)',(token,)).fetchone()
            self.assertEqual(raised.exception.sqlstate,'22023',token)
        self.assertEqual(c.execute('SELECT truss.query_timestamp_instant_key(%s,%s)',
            ('1970-01-01T00:00:00-00:00','umf-rfc3339-exact-instant/1.0.0')).fetchone()[0],
            ['0',''])
        host.detach();c.rollback()

    def test_native_temporal_requirements_reject_empty_and_malformed_kinds(self):
        c,host,assembly,tx=self.ready()
        manifest,digest,_=__import__('truss.catalog_runtime',fromlist=['_release'])._release()
        raw=c.execute('SELECT truss.person_query_temporal_binding(%s::jsonb,10000,1000,1048576,%s,%s)',
            ('["adoc"]',manifest['releaseId'],digest)).fetchone()[0]
        binding=json.loads(bytes(raw))['bindingJson']
        selected_type=self.admin.execute("SELECT type_id FROM truss.type_def WHERE element='A' AND retired_rev IS NULL").fetchone()[0]
        record={'documentId':'adoc','revision':'r1','module':'m','element':'A'}
        field={'documentId':'adoc','revision':'r1','module':'m','element':'A-local'}
        presence={'missing':True,'null':True}
        malformed=[
            {'version':'truss.temporal-source-guard/0.1','record':record,'fields':[]},
            {'version':'truss.temporal-source-guard/0.1','record':record,'fields':[
                {'field':field,'presence':presence}]},
            {'version':'truss.temporal-source-guard/0.1','record':record,'fields':[
                {'field':field,'kind':None,'presence':presence}]},
        ]
        for requirements in malformed:
            with self.assertRaises(psycopg.Error) as raised:
                with c.transaction():
                    c.execute('SELECT * FROM truss.person_query_temporal_objects(%s::jsonb,%s,%s::jsonb)',
                        (binding,selected_type,json.dumps(requirements))).fetchall()
            self.assertEqual(raised.exception.sqlstate,'22023',repr(requirements)+' '+str(raised.exception))
        host.detach();c.rollback()

    def test_native_plan_refuses_stripped_owner_local_declaration_paths(self):
        c,host,assembly,tx=self.ready()
        original=json.loads(self.prepared.declarations_bytes)
        documents=self.prepared.archive_documents_bytes
        origin=b'{}'
        def plan(declarations):
            return self.admin.execute('SELECT truss.catalog_expected_records(%s,%s,%s,transaction_timestamp(),transaction_timestamp(),1,0,0,0)',
                (json.dumps(declarations,separators=(',',':')).encode(),documents,origin)).fetchone()[0]
        # The accepted owner result and exact descriptor both make a positive
        # source-derived plan; each mutation below is a distinct hostile packet.
        self.assertIsInstance(plan(original),dict)
        stripped_descriptor=deepcopy(original)
        local_field=next(field for record in stripped_descriptor[0]['records'] for field in record['fields']
            if field['reference']['element']=='A-local')
        local_field.pop('nativeDescriptor')
        stripped_owner=deepcopy(original)
        owner_record=next(record for record in stripped_owner[0]['accessAdmission']['records']
            if record['ref']=={'module':'m','element':'A'})
        owner_record['fields']=[field for field in owner_record['fields'] if field['ref']['element']!='A-local']
        stripped_record=deepcopy(original)
        stripped_record[0]['records']=[record for record in stripped_record[0]['records'] if record['elementId']!='A']
        empty_records=deepcopy(original)
        empty_records[0]['records']=[]
        for tampered in (stripped_descriptor,stripped_owner,stripped_record,empty_records):
            with self.assertRaises(psycopg.Error) as raised:
                with self.admin.transaction():plan(tampered)
            self.assertEqual(raised.exception.sqlstate,'22023',str(raised.exception))
        host.detach();c.rollback()

if __name__=='__main__':
    import unittest
    unittest.main()
