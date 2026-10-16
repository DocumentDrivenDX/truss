"""Public business-key lookup against real created objects and active memberships."""
import psycopg
from truss import (Ok,Error,ObjectFound,ObjectNotFound,ObjectReadInvalid,
    adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration)
import test_group_create_native as group_tests

class KeyLookupTests(group_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(group_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def lookup(self,assembly,tx,values,key='a-primary',document='adoc',source=None):
        return assembly.lookup_key_in_transaction(tx,document_id=document,module_id='m',record_id='A',key_id=key,values=values,
            original_document=source,bun_executable='/opt/homebrew/bin/bun')

    def test_create_lookup_commit_readonly_primary_and_alternate_keys(self):
        connection,host,assembly,tx=self.ready();label='é雪🚀|\\';value=''
        input,request=self.input(assembly,tx,(self.create(label=label,value=value),))
        created=self.apply(assembly,tx,input,request);identity=int(created.response.semantic.results[0].identity.id)
        initial=self.lookup(assembly,tx,(value,label));self.assertIsInstance(initial.value,ObjectFound)
        self.assertEqual(initial.value.object.id,identity);self.assertEqual(initial.value.object.version,1)
        host.detach();connection.commit()
        self.admin.execute('REVOKE group_writer FROM consumer');self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        connection.execute('BEGIN READ ONLY');host=adopt_psycopg_host(connection);self.addCleanup(host.detach);self.consumer_connections.append((connection,host))
        tx=host.adopt_transaction(access_mode='read_only').value;assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        before=self.admin.execute('SELECT count(*),sum(generation) FROM truss.key_bucket_guard').fetchone()
        for key,values in (('a-primary',(value,label)),('z-alt',(label,))):
            result=self.lookup(assembly,tx,values,key);self.assertIsInstance(result.value,ObjectFound)
            self.assertEqual(result.value.object.id,identity);self.assertEqual(dict(result.value.object.values),{'A-label':label,'A-value':value})
        self.assertIsInstance(self.lookup(assembly,tx,(label,value)).value,ObjectNotFound)
        self.assertIsInstance(self.lookup(assembly,tx,('not-present',),'z-alt').value,ObjectNotFound)
        self.assertIsInstance(self.lookup(assembly,tx,('not-present',),'unknown-key').value,ObjectNotFound)
        self.assertIsInstance(self.lookup(assembly,tx,(label,)).value,ObjectReadInvalid)
        source=next(d.content for d in self.documents if d.document_id=='adoc')
        self.assertIsInstance(self.lookup(assembly,tx,(value,label),document='zdoc',source=source).value,ObjectNotFound)
        self.assertIsInstance(self.lookup(assembly,tx,(value,label),source=source+b' ').value,ObjectReadInvalid)
        self.assertEqual(self.admin.execute('SELECT count(*),sum(generation) FROM truss.key_bucket_guard').fetchone(),before)
        self.assertEqual(connection.execute('SHOW transaction_read_only').fetchone(),('on',))
        self.admin.execute('REVOKE group_reader FROM consumer')
        refused=self.lookup(assembly,tx,(value,label),source=source);self.assertIsInstance(refused,Error);self.assertEqual(refused.error.sql_state,'42501')
        host.detach();connection.rollback()

    def test_duplicate_exact_membership_is_integrity_refusal(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        self.apply(assembly,tx,input,request);host.detach();connection.commit()
        identity=self.admin.execute("INSERT INTO truss.object(id,type_id,ver,props,retained,root_id,created_at,updated_at,rev) SELECT nextval('truss.id_seq'),type_id,ver,props,retained,root_id,created_at,updated_at,rev FROM truss.object LIMIT 1 RETURNING id").fetchone()[0]
        self.admin.execute("INSERT INTO truss.object_key_bucket(type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes) SELECT b.type_id,b.key_num,%s,b.namespace_bytes,b.key_bytes,b.original_context_bytes FROM truss.object_key_bucket b JOIN truss.key_def k USING(type_id,key_num) WHERE k.key_id='a-primary' LIMIT 1",(identity,))
        connection,host,assembly,tx=self.consumer()
        result=self.lookup(assembly,tx,('value','one'))
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')

    def test_unreadable_key_field_owner_does_not_expose_source_equality(self):
        def mixed(source):
            module=source['modules'][0]
            field=next(e for e in module['elements'] if e['id']=='A-label');module['elements'].remove(field)
            source['modules'].append({'id':'hidden','namespace':'hidden','extensions':{},'elements':[field],'relationships':[]})
            for element in module['elements']:
                for reference in element.get('members',[]):
                    if reference['element']=='A-label':reference['module']='hidden'
                for key in element.get('keys',[]):
                    for reference in key['fields']:
                        if reference['element']=='A-label':reference['module']='hidden'
        connection,host,assembly,tx=self.ready(mixed)
        source=next(d.content for d in self.documents if d.document_id=='adoc')
        for candidate in (source,source+b' '):
            result=self.lookup(assembly,tx,('value','one'),source=candidate)
            self.assertIsInstance(result.value,ObjectNotFound)
