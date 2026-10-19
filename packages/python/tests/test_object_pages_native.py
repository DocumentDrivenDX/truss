# SPDX-License-Identifier: MIT OR Apache-2.0
"""Real public live ID-keyset pages with bounded exact object values."""
import concurrent.futures
import time
from dataclasses import replace
import psycopg
from truss import (Ok,Error,ObjectPage,ObjectNotFound,ObjectReadInvalid,ObjectReadUnavailable,
    create_reference_assembly,CatalogRuntimeConfiguration,adopt_psycopg_host)
from truss.groups import RequestNone,GroupSuccess
import test_group_create_native as group_tests

class ObjectPageTests(group_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(group_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def ready_objects(self):
        connection,host,assembly,tx=self.ready()
        operations=tuple(self.create(label=str(n),alias='item'+str(n)) for n in range(8))
        input,_=self.input(assembly,tx,operations=operations)
        result=self.apply(assembly,tx,input,RequestNone());self.assertIsInstance(result,GroupSuccess)
        self.identities=tuple(int(item.identity.id) for item in result.response.semantic.results)
        host.detach();connection.commit()
        return self.consumer()

    def page(self,assembly,tx,**options):
        return assembly.page_objects_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',**options)

    def test_committed_readonly_pages_use_last_returned_id_and_end(self):
        connection,host,assembly,tx=self.ready_objects();host.detach();connection.rollback();connection.execute('BEGIN READ ONLY')
        host=adopt_psycopg_host(connection);self.consumer_connections.append((connection,host))
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction(access_mode='read_only').value
        cursor=None;seen=[];sizes=[]
        while True:
            result=self.page(assembly,tx,limit=3,cursor=cursor)
            self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,ObjectPage)
            page=result.value;seen.extend(item.id for item in page.objects);sizes.append(len(page.objects))
            self.assertEqual(page.consistency,'live');self.assertEqual(page.catalog_revision,1)
            cursor=page.continuation
            if cursor is None:break
            self.assertEqual(cursor.after_id,page.objects[-1].id)
        self.assertEqual(tuple(seen),tuple(sorted(self.identities)));self.assertEqual(sizes,[3,3,2])
        empty=assembly.page_objects_in_transaction(tx,document_id='adoc',module_id='m',record_id='B')
        self.assertIsInstance(empty.value,ObjectPage);self.assertEqual(empty.value.objects,());self.assertIsNone(empty.value.continuation)
        hidden=assembly.page_objects_in_transaction(tx,document_id='zdoc',module_id='m',record_id='A')
        self.assertIsInstance(hidden.value,ObjectNotFound)
        host.detach();connection.rollback()

    def test_cursor_context_limits_and_catalog_advance_refuse(self):
        connection,host,assembly,tx=self.ready_objects()
        first=self.page(assembly,tx,limit=2).value;cursor=first.continuation
        self.assertIsInstance(self.page(assembly,tx,limit=0).value,ObjectReadInvalid)
        self.assertIsInstance(self.page(assembly,tx,limit=1001).value,ObjectReadInvalid)
        self.assertIsInstance(self.page(assembly,tx,maximum_bytes=1).value,ObjectReadUnavailable)
        self.assertIsInstance(self.page(assembly,tx,cursor=replace(cursor,record_id='B')).value,ObjectReadInvalid)
        bad=self.page(assembly,tx,cursor=replace(cursor,type_id=cursor.type_id+1)).value
        self.assertIsInstance(bad,ObjectReadUnavailable);self.assertEqual(bad.reason,'context')
        bad=self.page(assembly,tx,cursor=replace(cursor,source_epoch='different')).value
        self.assertIsInstance(bad,ObjectReadUnavailable);self.assertEqual(bad.reason,'context')
        self.assertIsInstance(self.page(assembly,tx,cursor=replace(cursor,after_id=True)).value,ObjectReadInvalid)
        # The position is editable routing, not a signed provenance statement.
        skipped=self.page(assembly,tx,cursor=replace(cursor,after_id=self.identities[-1])).value
        self.assertIsInstance(skipped,ObjectPage);self.assertEqual(skipped.objects,())
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        from truss import CatalogDocument
        from test_catalog_relational_support import relational_document
        import json
        source=relational_document();source['id']='more'
        prepared=assembly.prepare_catalog((CatalogDocument('more','r1',json.dumps(source).encode()),),bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(assembly.accept_in_transaction(tx,prepared,request_key='more'),Ok)
        stale=self.page(assembly,tx,cursor=cursor).value
        self.assertIsInstance(stale,ObjectReadUnavailable);self.assertEqual(stale.reason,'context')
        host.detach();connection.rollback()

    def test_exact_values_and_whole_page_byte_limit(self):
        from test_exact_scalar_values_native import ExactScalarTests
        from truss.contracts import TextValue
        connection,host,assembly,tx=self.ready(lambda source:ExactScalarTests.source(None,source))
        operation=ExactScalarTests.operation(self)
        other=replace(operation,alias='other',values=tuple(replace(v,value=TextValue(kind='string',text='other')) if v.name=='A-label' else v for v in operation.values))
        input,_=self.input(assembly,tx,operations=(operation,other))
        self.assertIsInstance(self.apply(assembly,tx,input,RequestNone()),GroupSuccess)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        first=self.page(assembly,tx,limit=1,maximum_bytes=6000).value
        self.assertIsInstance(first,ObjectPage);self.assertEqual(dict(first.objects[0].values)['n'],TextValue(kind='integer',text='9'*2500))
        self.assertIsNotNone(first.continuation)
        oversized=self.page(assembly,tx,limit=2,maximum_bytes=6000).value
        self.assertIsInstance(oversized,ObjectReadUnavailable);self.assertEqual(oversized.reason,'resource')
        second=self.page(assembly,tx,limit=1,maximum_bytes=6000,cursor=first.continuation).value
        self.assertIsInstance(second,ObjectPage);self.assertEqual(len(second.objects),1);self.assertIsNone(second.continuation)
        host.detach();connection.rollback()

    def test_revocation_after_buffered_page_does_not_publish(self):
        connection,host,assembly,tx=self.ready_objects()
        original=self.admin.execute("SELECT pg_get_functiondef('truss.page_objects(text,text,text,int,int,bytea,text,text)'::regprocedure)").fetchone()[0]
        needle=' PERFORM truss.runtime_person(false);\n IF NOT truss.runtime_can_read'
        self.assertIn(needle,original)
        self.admin.execute(original.replace(needle,' PERFORM pg_advisory_lock(928390);PERFORM pg_advisory_unlock(928390);\n'+needle))
        self.admin.execute('SELECT pg_advisory_lock(928390)')
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                pending=executor.submit(self.page,assembly,tx,limit=3)
                deadline=time.monotonic()+3;blocked=False
                while time.monotonic()<deadline:
                    blocked=self.admin.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=%s AND locktype='advisory' AND NOT granted)",(connection.info.backend_pid,)).fetchone()[0]
                    if blocked:break
                    time.sleep(.01)
                self.assertTrue(blocked,'page did not buffer rows before revocation')
                self.admin.execute('REVOKE group_writer FROM consumer')
                self.admin.execute('SELECT pg_advisory_unlock(928390)')
                refused=pending.result(timeout=5)
                self.assertIsInstance(refused,Error);self.assertEqual(refused.error.sql_state,'42501')
        finally:
            self.admin.execute('SELECT pg_advisory_unlock_all()');self.admin.execute(original)
        denied=self.page(assembly,tx)
        self.assertIsInstance(denied,Error);self.assertEqual(denied.error.sql_state,'42501')
        host.detach();connection.rollback()
