"""Append-only registrations preserve old identities and real public operations."""
import json
import concurrent.futures
import time
from dataclasses import replace
import psycopg
from truss import (Ok,Error,CatalogDocument,CatalogUnchanged,ModuleAccessGrant,ObjectFound,ObjectReadUnavailable,
    create_reference_assembly,CatalogRuntimeConfiguration,adopt_psycopg_host)
from truss.groups import GroupSuccess,AppliedPending,CommittedReceiptReplay,GroupUnavailable
from truss.contracts import ProfilePin
from truss.catalog_view import CatalogViewUnavailable
import test_group_create_native as group_tests
from test_catalog_relational_support import relational_document

class CatalogAdditionTests(group_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(group_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def added(self,assembly,identity):
        source=relational_document();source['id']=identity
        document=CatalogDocument(identity,'r1',json.dumps(source,indent=2).encode())
        return document,assembly.prepare_catalog((document,),bun_executable='/opt/homebrew/bin/bun')

    def test_add_document_preserves_old_read_create_keys_and_receipt(self):
        connection,host,assembly,tx=self.ready()
        original_documents=self.documents;original_types=dict(self.types)
        original_input,original_request=self.input(assembly,tx)
        original_group=self.apply(assembly,tx,original_input,original_request)
        original_object=original_group.response.semantic.results[0].identity
        host.detach();connection.commit()
        old_report=self.admin.execute('SELECT report_bytes FROM truss.catalog_acceptance_report WHERE rev=1').fetchone()[0]
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        connection,host,assembly,tx=self.consumer()
        new_document,prepared=self.added(assembly,'bdoc')
        registered=assembly.accept_in_transaction(tx,prepared,request_key='add-bdoc')
        self.assertIsInstance(registered,Ok);self.assertEqual(registered.value.revision,2)
        view=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request())
        self.assertIsInstance(view,Ok);self.assertEqual(view.value.view.catalog_revision,'2')
        legacy=replace(assembly.catalog_view_request(),view_profile=ProfilePin(identity='truss-complete-catalog-view',version='0.1',sha256='9e845234a67c6dbb4ee7a1c178c9ccd915c26300460cc2fc2b355d2cf25479ad'))
        stale=assembly.catalog_view_in_transaction(tx,legacy)
        self.assertIsInstance(stale.value,CatalogViewUnavailable);self.assertEqual(stale.value.reason,'profile')
        actual_types={(d.reference.owner.document_id,d.reference.authored_identity):d.reference
                      for d in view.value.view.definitions if d.reference.kind=='type'}
        for key,value in original_types.items():self.assertEqual(actual_types[key],value)
        self.assertGreater(int(actual_types[('bdoc','A')].type_id),max(int(r.type_id) for r in original_types.values()))
        historical=assembly.report_in_transaction(tx,revision=1)
        self.assertIsInstance(historical,Ok);self.assertEqual(historical.value.original_bytes,bytes(old_report))
        self.assertTrue(assembly.accept_in_transaction(tx,prepared,request_key='add-bdoc').value.replayed)
        unchanged=assembly.accept_in_transaction(tx,prepared,request_key='bdoc-check')
        self.assertIsInstance(unchanged.value,CatalogUnchanged);self.assertEqual(unchanged.value.registration_id,registered.value.registration_id)
        host.detach();connection.commit()
        self.documents=original_documents+(new_document,);self.types=actual_types
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        self.assertIsInstance(self.assembly.configure_module_access_in_transaction(self.tx,(ModuleAccessGrant('bdoc','m','group_reader','group_writer'),)),Ok)
        self.host.detach();self.admin.commit()
        connection,host,assembly,tx=self.consumer()
        old=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(original_object.id))
        self.assertIsInstance(old.value,ObjectFound)
        self.assertEqual((old.value.object.catalog_revision,old.value.object.record_revision),(2,1))
        old_key=assembly.lookup_key_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=('value','one'),bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(old_key.value,ObjectFound);self.assertEqual(old_key.value.object.id,int(original_object.id))
        replay=self.apply(assembly,tx,original_input,original_request)
        self.assertIsInstance(replay.response,CommittedReceiptReplay);self.assertEqual(replay.response.semantic,original_group.response.semantic)
        new_input,new_request=self.input(assembly,tx,operations=(self.create(document='bdoc',label='new',alias='new'),))
        stale_input=replace(new_input,mutation_profile=ProfilePin(identity='truss-rootless-string-create',version='0.1',sha256='f77c86906a35d8ca16bb00b7b068eaa023d224b3792353365089e8d718f92b71'))
        stale=assembly.apply_in_transaction(tx,stale_input,new_request,documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(stale.value,GroupUnavailable);self.assertEqual(stale.value.reason,'profile')
        new_request=assembly.group_context_in_transaction(tx).value.request('new-bdoc-object')
        created=self.apply(assembly,tx,new_input,new_request)
        self.assertIsInstance(created.response,AppliedPending);self.assertEqual(created.response.semantic.executed_catalog_revision,'2')
        new_id=int(created.response.semantic.results[0].identity.id)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.object WHERE id=%s',(new_id,)).fetchone(),(2,))
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.journal WHERE entity_id=%s',(new_id,)).fetchone(),(2,))
        connection,host,assembly,tx=self.consumer();host.detach();connection.rollback();connection.execute('BEGIN READ ONLY')
        host=adopt_psycopg_host(connection);self.consumer_connections.append((connection,host))
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        tx=host.adopt_transaction(access_mode='read_only').value
        for doc,identity in (('adoc',int(original_object.id)),('bdoc',new_id)):
            result=assembly.get_object_in_transaction(tx,document_id=doc,module_id='m',record_id='A',object_id=identity)
            self.assertIsInstance(result.value,ObjectFound);self.assertEqual(result.value.object.catalog_revision,2)
            source=assembly.accepted_document_in_transaction(tx,document_id=doc)
            self.assertIsInstance(source,Ok);self.assertEqual(source.value.catalog_revision,2)
            self.assertEqual(source.value.source_catalog_revision,1 if doc=='adoc' else 2)
            self.assertEqual(source.value.registration_id,json.loads(bytes(old_report))['registrationId'] if doc=='adoc' else registered.value.registration_id)
            key=assembly.lookup_key_in_transaction(tx,document_id=doc,module_id='m',record_id='A',key_id='a-primary',values=('value','one' if doc=='adoc' else 'new'),bun_executable='/opt/homebrew/bin/bun')
            self.assertIsInstance(key.value,ObjectFound);self.assertEqual(key.value.object.id,identity)
        catalog=assembly.reader_catalog_in_transaction(tx)
        self.assertIsInstance(catalog,Ok);self.assertEqual({m['documentId'] for m in catalog.value.modules},{'adoc','bdoc'})
        host.detach();connection.rollback()

    def test_multiple_pending_registrations_rollback_and_changed_document_refusal(self):
        self.install();connection,host,assembly,tx=self.consumer()
        document,prepared=self.added(assembly,'first')
        first=assembly.accept_in_transaction(tx,prepared,request_key='first')
        self.assertIsInstance(first,Ok)
        _,second=self.added(assembly,'second')
        self.assertIsInstance(assembly.accept_in_transaction(tx,second,request_key='second'),Ok)
        unchanged=assembly.accept_in_transaction(tx,prepared,request_key='first-check')
        self.assertIsInstance(unchanged.value,CatalogUnchanged)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(2,))
        connection,host,assembly,tx=self.consumer()
        _,third=self.added(assembly,'third')
        self.assertIsInstance(assembly.accept_in_transaction(tx,third,request_key='rolled-back'),Ok)
        host.detach();connection.rollback()
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(2,))
        self.assertEqual(self.admin.execute("SELECT count(*) FROM truss.schema_doc WHERE doc_id='third'").fetchone(),(0,))
        connection,host,assembly,tx=self.consumer()
        changed=assembly.prepare_catalog((replace(document,document_revision='r2'),),bun_executable='/opt/homebrew/bin/bun')
        denied=assembly.accept_in_transaction(tx,changed,request_key='changed-first')
        self.assertIsInstance(denied,Error);self.assertEqual(denied.error.catalog_code,'unauthorized')
        host.detach();connection.rollback()

    def test_readonly_head_advance_refuses_buffered_observation(self):
        connection,host,assembly,tx=self.ready()
        input,request=self.input(assembly,tx);created=self.apply(assembly,tx,input,request)
        identity=int(created.response.semantic.results[0].identity.id)
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer();host.detach();connection.rollback();connection.execute('BEGIN READ ONLY')
        host=adopt_psycopg_host(connection);self.consumer_connections.append((connection,host))
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction(access_mode='read_only').value
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        writer,writer_host,writer_assembly,writer_tx=self.consumer();_,prepared=self.added(writer_assembly,'concurrent')
        original=self.admin.execute("SELECT pg_get_functiondef('truss.get_object(text,text,text,bigint,int,text,text)'::regprocedure)").fetchone()[0]
        needle=" actor_oid:=truss.runtime_person(false);\n IF current_setting('transaction_read_only')='on' THEN"
        self.assertIn(needle,original)
        self.admin.execute(original.replace(needle," PERFORM pg_advisory_lock(928381);PERFORM pg_advisory_unlock(928381);\n"+needle))
        self.admin.execute('SELECT pg_advisory_lock(928381)')
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                pending=executor.submit(assembly.get_object_in_transaction,tx,document_id='adoc',module_id='m',record_id='A',object_id=identity)
                deadline=time.monotonic()+3;blocked=False
                while time.monotonic()<deadline:
                    blocked=self.admin.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=%s AND locktype='advisory' AND NOT granted)",(connection.info.backend_pid,)).fetchone()[0]
                    if blocked:break
                    time.sleep(.01)
                self.assertTrue(blocked,'reader did not buffer the original catalog observation')
                accepted=writer_assembly.accept_in_transaction(writer_tx,prepared,request_key='concurrent-addition')
                self.assertIsInstance(accepted,Ok);writer_host.detach();writer.commit()
                self.admin.execute('SELECT pg_advisory_unlock(928381)')
                refused=pending.result(timeout=5)
                self.assertIsInstance(refused.value,ObjectReadUnavailable);self.assertEqual(refused.value.reason,'observation')
        finally:
            self.admin.execute('SELECT pg_advisory_unlock_all()');self.admin.execute(original)
        read=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=identity)
        self.assertIsInstance(read.value,ObjectFound);self.assertEqual(read.value.object.catalog_revision,2)
        host.detach();connection.rollback()

    def test_same_assembly_rollback_reaccept_replaces_default_source(self):
        connection,host,assembly,tx=self.ready()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        document,prepared=self.added(assembly,'cache')
        self.assertIsInstance(assembly.accept_in_transaction(tx,prepared,request_key='cache-model'),Ok)
        connection.rollback();connection.execute('BEGIN');tx=host.adopt_transaction().value
        changed=replace(document,content=document.content+b'\n')
        prepared=assembly.prepare_catalog((changed,),bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(assembly.accept_in_transaction(tx,prepared,request_key='cache-model'),Ok)
        connection.commit()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        self.assertIsInstance(self.assembly.configure_module_access_in_transaction(self.tx,(ModuleAccessGrant('cache','m','group_reader','group_writer'),)),Ok)
        self.host.detach();self.admin.commit()
        connection.execute('BEGIN');tx=host.adopt_transaction().value
        reference=assembly.get_type_reference_in_transaction(tx,document_id='cache',module_id='m',record_id='A')
        self.assertIsInstance(reference,Ok);self.types[('cache','A')]=reference.value
        # Preparing an unrelated source must not erase accepted convenience data.
        self.added(assembly,'not-accepted')
        input,request=self.input(assembly,tx,operations=(self.create(document='cache'),))
        result=assembly.apply_in_transaction(tx,input,request,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,GroupSuccess)
        self.assertIsInstance(result.value.response,AppliedPending)
        host.detach();connection.rollback()
