# SPDX-License-Identifier: MIT OR Apache-2.0
"""Compiled meaning may be shared; live writer selections must not collide."""
import json
from unittest.mock import patch
import psycopg
from truss import (CatalogDocument,CatalogRuntimeConfiguration,ModuleAccessGrant,Ok,
    adopt_psycopg_host,create_reference_assembly)
from truss.contracts import MapValue,TextValue
from truss.groups import AuthoredValue,CreateObject,GroupSuccess,RequestNone,RootlessOwnership
import test_catalog_runtime_native as base

class RecordSchemaSelectionTests(base.PublicCatalogRuntimeTests):
    for name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[name]=None

    def ready(self):
        self.install()
        modules=[]
        for module,record in (('left','A'),('right','B')):
            modules.append({'id':module,'namespace':module,'extensions':{},'elements':[
                {'id':record,'kind':'record','members':[{'module':module,'element':'code'}],
                 'keys':[{'id':'identity','name':'identity','primary':True,'fields':[{'module':module,'element':'code'}]}],
                 'extensions':{}},
                {'id':'code','name':'code','kind':'field','scalarType':'string',
                 'nullability':'required','cardinality':'one','extensions':{}}]})
        raw=json.dumps({'umf':'0.10.0','id':'shared-doc','vocabularies':{},'extensions':{},'modules':modules}).encode()
        self.documents=(CatalogDocument('shared-doc','v1',raw),)
        c,h,a,t=self.consumer()
        accepted=a.accept_in_transaction(t,a.prepare_catalog(self.documents),request_key='two-modules')
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(h._custody.last_attempt.error))
        view=a.catalog_view_in_transaction(t,a.catalog_view_request()).value.view
        self.types={entry.reference.authored_identity:entry.reference for entry in view.definitions if entry.reference.kind=='type'}
        h.detach();c.commit()
        for role in ('left_reader','left_writer','right_reader','right_writer','other_consumer'):
            login='LOGIN' if role=='other_consumer' else 'NOLOGIN'
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} '+login).format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute("ALTER ROLE consumer SET track_functions='all'")
        self.admin.execute("ALTER ROLE other_consumer SET track_functions='all'")
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin)
        self.tx=self.host.adopt_transaction().value
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        configured=self.assembly.configure_module_access_in_transaction(self.tx,(
            ModuleAccessGrant('shared-doc','left','left_reader','left_writer'),
            ModuleAccessGrant('shared-doc','right','right_reader','right_writer')))
        self.assertIsInstance(configured,Ok,repr(configured))
        self.host.detach();self.admin.commit()
        self.admin.execute('GRANT left_writer TO consumer WITH SET FALSE')
        self.admin.execute('GRANT right_writer TO other_consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))

    def writer(self,user='consumer',connection=None):
        if connection is None:
            params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=user
            connection=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000')
            self.addCleanup(connection.close)
        # Function counters can remain pending in this backend after commit.
        # Flush while idle so the next transaction's observations exclude them.
        connection.execute('SELECT pg_stat_force_next_flush()')
        connection.execute('BEGIN')
        host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000)
        self.addCleanup(host.detach);self.consumer_connections.append((connection,host))
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        return connection,host,assembly,host.adopt_transaction().value

    def create(self,assembly,tx,record,code):
        operation=CreateObject(type_definition_pin=self.types[record].definition_pin,
            values=(AuthoredValue(name='code',value=TextValue(kind='string',text=code)),),
            ownership=RootlessOwnership(),alias='row')
        context=assembly.group_context_in_transaction(tx).value
        result=assembly.apply_in_transaction(tx,context.input((operation,),MapValue(entries=())),
            RequestNone(),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(assembly._host._custody.last_attempt.error))
        self.assertIsInstance(result.value,GroupSuccess,repr(result))

    def selection(self,assembly):
        from truss._schema_memory import record_schemas
        selected=record_schemas(assembly._record_schema_state['key'])
        self.assertIsNotNone(selected)
        return selected

    def calls(self,connection):
        return dict(connection.execute('''SELECT p.proname,sum(s.calls)
            FROM pg_stat_xact_user_functions s JOIN pg_proc p ON p.oid=s.funcid
            WHERE s.schemaname='truss' GROUP BY p.proname''').fetchall())

    def test_disjoint_writers_share_basis_without_reusing_the_wrong_record_subset(self):
        self.ready();import truss._record_schema as schema
        with patch.object(schema,'compile_records',wraps=schema.compile_records) as compile_once:
            c1,h1,a1,t1=self.writer();self.create(a1,t1,'A','a1');left=self.selection(a1)
            first=self.calls(c1);h1.detach();c1.commit()
            c2,h2,a2,t2=self.writer('other_consumer');self.create(a2,t2,'B','b1');right=self.selection(a2)
            second=self.calls(c2);h2.detach();c2.commit()
            self.assertEqual(left.basis,right.basis)
            self.assertEqual(set(left.types_by_pin),{self.types['A'].definition_pin})
            self.assertEqual(set(right.types_by_pin),{self.types['B'].definition_pin})
            self.assertEqual(compile_once.call_count,2)
            for calls in (first,second):
                self.assertEqual(calls.get('writer_schema_basis'),1)
                self.assertEqual(calls.get('runtime_owned_application_values'),1)
                self.assertEqual(calls.get('owned_object_values',0),0)
            c1,h1,a1,t1=self.writer(connection=c1);self.create(a1,t1,'A','a2')
            warm=self.calls(c1)
            self.assertEqual(warm.get('writer_schema_basis',0),0)
            self.assertEqual(warm.get('runtime_owned_application_values'),1)
            self.assertEqual(compile_once.call_count,2)
            h1.detach();c1.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0],3)

    def test_grant_adds_record_to_existing_connection_without_a_catalog_revision(self):
        self.ready();import truss._record_schema as schema
        with patch.object(schema,'compile_records',wraps=schema.compile_records) as compile_once:
            c,h,a,t=self.writer();self.create(a,t,'A','a1');old=self.selection(a)
            h.detach();c.commit()
            self.admin.execute('GRANT right_writer TO consumer WITH SET FALSE')
            c,h,a,t=self.writer(connection=c);self.create(a,t,'B','b1');current=self.selection(a)
            self.create(a,t,'A','a2')
            self.assertEqual(old.basis,current.basis)
            self.assertEqual(set(current.types_by_pin),{self.types['A'].definition_pin,self.types['B'].definition_pin})
            calls=self.calls(c)
            self.assertEqual(calls.get('writer_schema_basis'),1)
            self.assertEqual(calls.get('runtime_owned_application_values'),2)
            self.assertEqual(calls.get('owned_object_values',0),0)
            self.assertEqual(compile_once.call_count,2)
            h.detach();c.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0],3)
