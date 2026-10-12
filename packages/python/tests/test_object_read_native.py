"""Public ordinary-person reads; administrative seed does not qualify writes."""
import json
import psycopg
from truss import (Ok,Error,ModuleAccessGrant,CatalogRuntimeConfiguration,create_reference_assembly,
    adopt_psycopg_host,ObjectFound,ObjectNotFound,ObjectReadInvalid,ObjectReadUnavailable)
import test_catalog_runtime_native as catalog_tests

class PublicObjectReadTests(catalog_tests.PublicCatalogRuntimeTests):
    # Reuse lifecycle only; the original catalog regression runs separately.
    for _name in tuple(n for n in dir(catalog_tests.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None
    def seed(self,optional=False):
        self.install()
        connection,host,assembly,tx=self.consumer()
        prepared=self.prepared(assembly)
        if optional:
            from truss import CatalogDocument
            from test_catalog_relational_support import relational_document
            documents=[]
            for identity in ('adoc','zdoc'):
                source=relational_document();source['id']=identity
                source['modules'][0]['elements'][0]['members'].append({'module':'m','element':'A-extra'})
                source['modules'][0]['elements'].append({'id':'A-extra','name':'A-extra','kind':'field','scalarType':'string',
                    'nullability':'absent-allowed','cardinality':'one','extensions':{}})
                documents.append(CatalogDocument(identity,'r1',json.dumps(source).encode()))
            prepared=assembly.prepare_catalog(tuple(documents),bun_executable='/opt/homebrew/bin/bun')
        accepted=assembly.accept_in_transaction(tx,prepared,request_key='read-fixture')
        self.assertIsInstance(accepted,Ok);host.detach();connection.commit()
        for role in ('object_reader','object_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN')
        self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        configured=self.assembly.configure_module_access_in_transaction(self.tx,(ModuleAccessGrant('adoc','m','object_reader','object_writer'),))
        self.assertIsInstance(configured,Ok);self.host.detach();self.admin.commit()
        self.admin.execute('GRANT object_reader TO consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        self.type_id=self.admin.execute("SELECT type_id FROM truss.type_def WHERE document_id='adoc' AND module='m' AND element='A'").fetchone()[0]
        props=self.admin.execute('SELECT prop_id,name FROM truss.prop_def WHERE type_id=%s ORDER BY prop_id',(self.type_id,)).fetchall()
        self.props={str(i):{'kind':'string','text':name+' λ'} for i,name in props}
        self.object_id=self.admin.execute("INSERT INTO truss.object(type_id,props,retained,rev,created_at,updated_at) VALUES(%s,%s::jsonb,%s::jsonb,1,'2026-10-12 01:02:03.123456+00','2026-10-12 01:02:04.654321+00') RETURNING id",(self.type_id,json.dumps(self.props),json.dumps({'note':{'kind':'string','text':''}}))).fetchone()[0]
        return self.consumer()
    def lookup(self,assembly,tx,**kwargs):
        return assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=self.object_id,**kwargs)
    def test_ordinary_reader_complete_values_without_registrar_or_raw_rights(self):
        connection,host,assembly,tx=self.seed()
        read=self.lookup(assembly,tx);self.assertIsInstance(read,Ok);self.assertIsInstance(read.value,ObjectFound)
        obj=read.value.object
        self.assertEqual(obj.id,self.object_id);self.assertEqual(obj.type_id,self.type_id)
        self.assertEqual(obj.values,(('A-label','A-label λ'),('A-value','A-value λ')))
        self.assertEqual(obj.retained,(('note',''),));self.assertEqual(obj.created_at,'2026-10-12T01:02:03.123456Z')
        self.assertEqual(obj.updated_at,'2026-10-12T01:02:04.654321Z');self.assertEqual(obj.version,1)
        self.assertEqual(connection.execute("SELECT has_table_privilege(current_user,'truss.object','SELECT')").fetchone(),(False,))
        self.admin.execute('REVOKE object_reader FROM consumer')
        refused=self.lookup(assembly,tx);self.assertIsInstance(refused,Error);self.assertEqual(refused.error.sql_state,'42501')
        self.admin.execute('GRANT object_writer TO consumer WITH SET FALSE')
        self.assertIsInstance(self.lookup(assembly,tx).value,ObjectFound)
        self.assertIsInstance(assembly.report_in_transaction(tx),Error)
    def test_hidden_missing_and_wrong_document_share_not_found(self):
        connection,host,assembly,tx=self.seed()
        for document,identity in (('zdoc',self.object_id),('adoc',self.object_id+999)):
            result=assembly.get_object_in_transaction(tx,document_id=document,module_id='m',record_id='A',object_id=identity)
            self.assertIsInstance(result.value,ObjectNotFound)
        self.admin.execute('REVOKE object_reader FROM consumer')
        self.assertIsInstance(self.lookup(assembly,tx),Error)
    def test_invalid_and_budget_refusal_preserve_prior_host_work(self):
        connection,host,assembly,tx=self.seed()
        connection.execute("CREATE TEMP TABLE prior(value text);INSERT INTO prior VALUES('kept')")
        self.assertIsInstance(assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=True).value,ObjectReadInvalid)
        self.assertIsInstance(self.lookup(assembly,tx,maximum_bytes=1).value,ObjectReadUnavailable)
        self.assertEqual(connection.execute('TABLE prior').fetchall(),[('kept',)])
        self.assertIsInstance(self.lookup(assembly,tx).value,ObjectFound)
    def test_malformed_unknown_and_unsupported_cells_are_not_omitted(self):
        connection,host,assembly,tx=self.seed()
        first=next(iter(self.props))
        for props in ({**self.props,first:{'kind':'string','text':'x','extra':True}},
                      {**self.props,'999999':{'kind':'string','text':'unknown'}},
                      {k:v for k,v in self.props.items() if k!=first}):
            self.admin.execute('UPDATE truss.object SET props=%s::jsonb WHERE id=%s',(json.dumps(props),self.object_id))
            result=self.lookup(assembly,tx)
            self.assertTrue(isinstance(result,Error) or isinstance(result.value,ObjectReadUnavailable))
        self.admin.execute('UPDATE truss.object SET props=%s::jsonb,retained=%s::jsonb WHERE id=%s',(json.dumps(self.props),json.dumps({'numeric':{'kind':'decimal','text':'1.1'}}),self.object_id))
        self.assertIsInstance(self.lookup(assembly,tx).value,ObjectReadUnavailable)

    def test_absent_null_and_empty_values_remain_distinct(self):
        connection,host,assembly,tx=self.seed(optional=True)
        prop_id=str(self.admin.execute("SELECT prop_id FROM truss.prop_def WHERE type_id=%s AND name='A-extra'",(self.type_id,)).fetchone()[0])
        for present,value in ((False,None),(True,{'kind':'null'}),(True,{'kind':'string','text':''})):
            props=dict(self.props)
            if present:props[prop_id]=value
            else:del props[prop_id]
            self.admin.execute('UPDATE truss.object SET props=%s::jsonb WHERE id=%s',(json.dumps(props),self.object_id))
            result=self.lookup(assembly,tx);self.assertIsInstance(result.value,ObjectFound)
            values=dict(result.value.object.values)
            if not present:self.assertNotIn('A-extra',values)
            else:self.assertEqual(values['A-extra'],None if value['kind']=='null' else '')
    def test_selected_release_and_fixed_snapshot_refuse(self):
        connection,host,assembly,tx=self.seed()
        connection.execute('SAVEPOINT wrong_release')
        with self.assertRaises(psycopg.errors.FeatureNotSupported):
            connection.execute('SELECT truss.get_object(%s,%s,%s,%s,%s,%s,%s)',
                ('adoc','m','A',self.object_id,1048576,'wrong-release','0'*64))
        connection.execute('ROLLBACK TO SAVEPOINT wrong_release');connection.execute('RELEASE SAVEPOINT wrong_release')
        self.assertIsInstance(self.lookup(assembly,tx).value,ObjectFound)
        host.detach();connection.rollback();connection.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        replacement=adopt_psycopg_host(connection);self.consumer_connections.append((connection,replacement))
        selected=create_reference_assembly(CatalogRuntimeConfiguration(),replacement).value
        adopted=replacement.adopt_transaction(isolation='repeatable_read').value
        self.assertIsInstance(self.lookup(selected,adopted).value,ObjectReadUnavailable)

    def test_wrong_revision_and_nonrepresentable_timestamps_refuse(self):
        connection,host,assembly,tx=self.seed()
        for revision,stamp in ((0,'2026-10-12'),(1,'infinity'),(1,'10000-01-01'),(1,'0001-01-01 BC')):
            self.admin.execute('UPDATE truss.object SET rev=%s,created_at=%s::timestamptz WHERE id=%s',(revision,stamp,self.object_id))
            self.assertIsInstance(self.lookup(assembly,tx).value,ObjectReadUnavailable)
    def test_unsafe_session_and_raw_rights_are_execution_errors(self):
        connection,host,assembly,tx=self.seed()
        self.admin.execute('GRANT SELECT ON truss.object TO consumer')
        refused=self.lookup(assembly,tx)
        self.assertIsInstance(refused,Error);self.assertEqual(refused.error.sql_state,'42501')
        self.admin.execute('REVOKE SELECT ON truss.object FROM consumer')
        self.assertIsInstance(self.lookup(assembly,tx).value,ObjectFound)

    def test_native_set_then_inherit_paths_and_nonreachable_mixed_paths(self):
        connection,host,assembly,tx=self.seed()
        # Each graph has consumer -> bridge -> storage. Native SET and native
        # column access are independent controls for the public guard decision.
        for label,first_inherit,first_set,last_inherit,last_set,exposed in (
            ('set_set',False,True,False,True,True),
            ('set_inherit',False,True,True,False,True),
            ('inherit_set',True,False,False,True,False),
            ('dormant',False,False,True,False,False),
        ):
            with self.subTest(path=label):
                self.admin.execute('CREATE ROLE path_bridge NOLOGIN; CREATE ROLE path_storage NOLOGIN')
                try:
                    self.admin.execute('GRANT USAGE ON SCHEMA truss TO path_bridge,path_storage')
                    self.admin.execute('GRANT SELECT(props) ON truss.object TO path_storage')
                    self.admin.execute(psycopg.sql.SQL('GRANT path_storage TO path_bridge WITH INHERIT {}, SET {}').format(
                        psycopg.sql.SQL(str(last_inherit)),psycopg.sql.SQL(str(last_set))))
                    self.admin.execute(psycopg.sql.SQL('GRANT path_bridge TO consumer WITH INHERIT {}, SET {}').format(
                        psycopg.sql.SQL(str(first_inherit)),psycopg.sql.SQL(str(first_set))))
                    result=self.lookup(assembly,tx)
                    if exposed:
                        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'42501')
                        connection.execute('SET ROLE '+('path_storage' if last_set else 'path_bridge'))
                        self.assertEqual(connection.execute('SELECT props FROM truss.object').fetchone()[0],self.props)
                        connection.execute('RESET ROLE')
                    else:
                        self.assertIsInstance(result.value,ObjectFound)
                        for query in ('SET ROLE path_storage','SELECT props FROM truss.object'):
                            connection.execute('SAVEPOINT native_denial')
                            with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.execute(query)
                            connection.execute('ROLLBACK TO SAVEPOINT native_denial');connection.execute('RELEASE SAVEPOINT native_denial')
                    self.admin.execute('REVOKE path_bridge FROM consumer')
                    self.assertIsInstance(self.lookup(assembly,tx).value,ObjectFound)
                finally:
                    self.admin.execute('REVOKE path_bridge FROM consumer')
                    self.admin.execute('DROP OWNED BY path_bridge,path_storage; DROP ROLE path_bridge,path_storage')
