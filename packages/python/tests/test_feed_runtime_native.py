"""Basic public committed feed, caller settlement and ordinary-role ACK workflow."""
import json
from truss import (Ok,FeedPage,FeedAcknowledged,FeedUnavailable,ModuleAccessGrant,
    adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration)
from truss.groups import Delete,StoredObjectReference,GroupSuccess,CreateEdge,NullOrderKey
from truss.contracts import MapValue,MapEntry,TextValue
from truss.imports import ImportReported
import test_receipt_visibility_native as receipt_tests


class FeedRuntimeTests(receipt_tests.ReceiptVisibilityTests):
    for _name in tuple(n for n in dir(receipt_tests.ReceiptVisibilityTests) if n.startswith('test_')):
        locals()[_name]=None

    def enrolled(self):
        connection,host,assembly,tx=self.ready()
        host.detach();connection.rollback()
        self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin)
        self.addCleanup(admin_host.detach)
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        admin_tx=admin_host.adopt_transaction().value
        configured=admin_assembly.configure_module_access_in_transaction(admin_tx,(ModuleAccessGrant('zdoc','m','group_reader','group_writer'),))
        self.assertIsInstance(configured,Ok)
        enrolled=admin_assembly.register_feed_consumer_in_transaction(admin_tx,consumer_id='adapter',reader_role='group_reader')
        if not isinstance(enrolled,Ok):self.fail(repr(enrolled)+' '+str(admin_host._custody.last_attempt.error))
        admin_host.detach();self.admin.commit()
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        return self.consumer()

    def read_page(self,assembly,tx,**limits):
        provider=assembly.feed(assembly.feed_selection)
        self.assertEqual(provider.status,'ok')
        result=provider.capability.read_feed_in_transaction(tx,consumer_id='adapter',**limits)
        if not isinstance(result,Ok):self.fail(repr(result)+' '+str(assembly._host._custody.last_attempt.error))
        self.assertIsInstance(result.value,FeedPage)
        return result.value

    def ack(self,assembly,tx,page):
        provider=assembly.feed(assembly.feed_selection)
        self.assertEqual(provider.status,'ok')
        result=provider.capability.acknowledge_feed_in_transaction(tx,page)
        if not isinstance(result,Ok):self.fail(repr(result)+' '+str(assembly._host._custody.last_attempt.error))
        self.assertIsInstance(result.value,FeedAcknowledged)
        return result.value

    def test_complete_delivery_commit_rollback_retry_and_reader_refusal(self):
        connection,host,assembly,tx=self.enrolled()
        created,_,_=self.run_group(assembly,tx,(self.create(),),'feed-create')
        self.assertIsInstance(created,GroupSuccess);identity=created.response.semantic.results[0].identity
        context=assembly.import_context_in_transaction(tx).value
        record=assembly.object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id='B',
            values=self.create(label='imported',value='imported',record='B').values,
            source=MapValue(entries=(MapEntry(key='system',value=TextValue(kind='string',text='adapter')),))).value
        imported=assembly.import_in_transaction(tx,context.input((record,),load_id='feed-load',asserted_origin=MapValue(entries=())),
            documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(imported,ImportReported);target=imported.report.outcomes[0].identity
        relationship=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B').value
        linked,_,_=self.run_group(assembly,tx,(CreateEdge(relationship_definition_pin=relationship.definition_pin,
            source=StoredObjectReference(identity=identity),target=StoredObjectReference(identity=target),values=(),order_key=NullOrderKey()),),'feed-link')
        self.assertIsInstance(linked,GroupSuccess)
        unlinked,_,_=self.run_group(assembly,tx,(Delete(operation='delete_edge',target=StoredObjectReference(identity=linked.response.semantic.results[0].identity)),),'feed-unlink')
        self.assertIsInstance(unlinked,GroupSuccess)
        deleted,_,_=self.run_group(assembly,tx,(Delete(operation='delete_object',target=StoredObjectReference(identity=identity)),),'feed-delete')
        self.assertIsInstance(deleted,GroupSuccess)
        host.detach();connection.commit()
        connection,host,assembly,tx=self.readonly()
        revision=self.read_page(assembly,tx)
        payload=json.loads(revision.content)
        self.assertEqual(revision.outcome,'transaction');self.assertEqual(len(payload['revisions']),1)
        self.assertTrue(payload['revisions'][0]['reportBytesBase64'])
        self.assertEqual(payload['changes'],[])
        # Polling supports a real read-only transaction and assigns no xid.
        host.detach();self.assertIsNone(connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0]);connection.rollback()
        connection,host,assembly,tx=self.consumer()
        self.assertEqual(self.ack(assembly,tx,revision).outcome,'advanced')
        host.detach();connection.rollback()
        connection,host,assembly,tx=self.consumer()
        self.assertEqual(self.read_page(assembly,tx).content,revision.content)
        self.assertEqual(self.ack(assembly,tx,revision).outcome,'advanced')
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        self.assertEqual(self.ack(assembly,tx,revision).outcome,'equal')
        page=self.read_page(assembly,tx);payload=json.loads(page.content)
        self.assertEqual(page.outcome,'transaction')
        self.assertEqual([v['op'] for v in payload['changes']],['create','create','create','delete','delete'])
        self.assertTrue(payload['catalogPrerequisites']);self.assertTrue(payload['reservations'])
        self.assertEqual(payload['sources'][0]['load_id'],'feed-load')
        self.assertIn('edge_key',{v['kind'] for v in payload['reservations']})
        # The complete delete event remains present after the object is gone.
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object WHERE id=%s',(int(identity.id),)).fetchone()[0],0)
        self.assertEqual(self.ack(assembly,tx,page).outcome,'advanced')
        host.detach();connection.commit()
        connection,host,assembly,tx=self.readonly()
        empty=self.read_page(assembly,tx);self.assertEqual(empty.outcome,'empty_interval')
        host.detach();connection.rollback()
        self.admin.execute('REVOKE group_reader,group_writer FROM consumer')
        connection,host,assembly,tx=self.readonly()
        denied=assembly.read_feed_in_transaction(tx,consumer_id='adapter')
        # No hidden event or checkpoint is disclosed without source authority.
        self.assertTrue(not isinstance(denied,Ok) or isinstance(denied.value,FeedUnavailable))
        host.detach();connection.rollback()
