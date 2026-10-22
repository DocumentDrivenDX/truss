# SPDX-License-Identifier: MIT OR Apache-2.0
"""HF-02 original request recovery; current rows never reconstruct the request."""
from dataclasses import replace
import uuid
from unittest.mock import patch
import psycopg
from truss import Ok, Error, adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration,ModuleAccessGrant
from truss.contracts import ABSENT,MapValue,MapEntry,TextValue
from truss.groups import (Delete,UpdateObject,StoredObjectReference,GroupSuccess,GroupFailed,GroupUnavailable,
    CommittedReceiptReplay,SameTransactionReplay,UnauthorizedPerson,RequestConflict,InvalidGroupInput,Unchanged,CreateEdge,NullOrderKey)
import test_edge_mutations_native as fixtures


class GroupRequestRecoveryNativeTests(fixtures.EdgeMutationTests):
    for _name in tuple(n for n in dir(fixtures.EdgeMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def frame(self,semantic,request):
        from truss import freeze_group_request,FrozenGroupRequest
        result=freeze_group_request(semantic,request,documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,FrozenGroupRequest)
        return result.value

    def recovery(self,assembly,transaction,frame):
        result=assembly.recover_group_request_in_transaction(transaction,frame)
        self.assertIsInstance(result,Ok,repr(result));return result.value

    def test_freeze_is_pure_and_missing_request_never_executes(self):
        c,h,a,t=self.ready(document_ids=('adoc',));semantic,request=self.input(a,t)
        with patch('psycopg.Cursor.execute',side_effect=AssertionError('Freeze must not query')),patch('subprocess.run',side_effect=AssertionError('Freeze must not run a process')):
            frame=self.frame(semantic,request)
        before=self.group_effect_counts();sequence=self.admin.execute('SELECT last_value,is_called FROM truss.id_seq').fetchone()
        routes=self.admin.execute('SELECT count(*) FROM truss.request_receipt_route_guard').fetchone()
        result=self.recovery(a,t,frame)
        self.assertIsInstance(result,GroupUnavailable);self.assertEqual(result.reason,'request_not_observed')
        h.detach();c.commit();self.assertEqual(self.group_effect_counts(),before)
        self.assertEqual(self.admin.execute('SELECT last_value,is_called FROM truss.id_seq').fetchone(),sequence)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.request_receipt_route_guard').fetchone(),routes)

    def test_delete_recovery_does_not_resolve_deleted_target(self):
        c,h,a,t=self.ready(document_ids=('adoc',));created,_,_=self.run_group(a,t,(self.create(),),'create-target')
        identity=created.response.semantic.results[0].identity
        semantic,request=self.input(a,t,(Delete(operation='delete_object',target=StoredObjectReference(identity=identity),expected_version='1'),))
        frame=self.frame(semantic,request)
        deleted=a.apply_in_transaction(t,semantic,request,documents=self.documents).value
        self.assertIsInstance(deleted,GroupSuccess);self.assertIsNot(deleted.group_id,ABSENT)
        h.detach();c.commit();c,h,a,t=self.consumer()
        before=self.group_effect_counts()
        with patch.object(type(a),'get_object_in_transaction',side_effect=AssertionError('Recovery must not resolve current targets')):
            recovered=self.recovery(a,t,frame)
        self.assertIsInstance(recovered.response,CommittedReceiptReplay)
        self.assertEqual(recovered.response.semantic,deleted.response.semantic)
        self.assertEqual(recovered.response.receipt_token,deleted.response.receipt_token)
        self.assertEqual(recovered.group_id,deleted.group_id);self.assertEqual(self.group_effect_counts(),before)

    def test_unlink_recovery_preserves_original_edge_result(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        seeded,_,_=self.run_group(a,t,(self.create(alias='a'),self.create(record='B',label='b',value='b',alias='b')))
        left,right=[r.identity for r in seeded.response.semantic.results]
        pin=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        linked,_,_=self.run_group(a,t,(CreateEdge(relationship_definition_pin=pin,source=StoredObjectReference(identity=left),target=StoredObjectReference(identity=right),values=(),order_key=NullOrderKey()),))
        edge=linked.response.semantic.results[0].identity
        semantic,request=self.input(a,t,(Delete(operation='delete_edge',target=StoredObjectReference(identity=edge),expected_version='1'),))
        frame=self.frame(semantic,request);deleted=a.apply_in_transaction(t,semantic,request,documents=self.documents).value
        self.assertIsInstance(deleted,GroupSuccess,repr(deleted));h.detach();c.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
        c,h,a,t=self.consumer();recovered=self.recovery(a,t,frame)
        self.assertEqual(recovered.response.semantic,deleted.response.semantic);self.assertEqual(recovered.group_id,deleted.group_id)

    def test_noop_recovery_after_later_deletion_has_original_result_and_group_id(self):
        c,h,a,t=self.ready(document_ids=('adoc',));created,_,_=self.run_group(a,t,(self.create(),))
        identity=created.response.semantic.results[0].identity
        operation=UpdateObject(target=StoredObjectReference(identity=identity),set=(self.create().values[0],),unset=(),expected_version='1')
        semantic,request=self.input(a,t,(operation,));frame=self.frame(semantic,request)
        nooped=a.apply_in_transaction(t,semantic,request,documents=self.documents).value
        self.assertIsInstance(nooped.response.semantic.results[0],Unchanged)
        h.detach();c.commit();c,h,a,t=self.consumer()
        self.run_group(a,t,(Delete(operation='delete_object',target=StoredObjectReference(identity=identity),expected_version='1'),))
        h.detach();c.commit();c,h,a,t=self.consumer()
        result=self.recovery(a,t,frame)
        self.assertIsInstance(result.response,CommittedReceiptReplay)
        self.assertEqual(result.response.semantic,nooped.response.semantic);self.assertEqual(result.group_id,nooped.group_id)

    def test_two_groups_same_transaction_have_distinct_stable_identity(self):
        c,h,a,t=self.ready(document_ids=('adoc',));context=a.group_context_in_transaction(t).value
        first=context.input((self.create(label='first'),),MapValue(entries=()));r1=context.request('first')
        second=context.input((self.create(label='second'),),MapValue(entries=()));r2=context.request('second')
        f1=self.frame(first,r1);f2=self.frame(second,r2)
        g1=a.apply_in_transaction(t,first,r1,documents=self.documents).value;g2=a.apply_in_transaction(t,second,r2,documents=self.documents).value
        self.assertNotEqual(g1.group_id,g2.group_id)
        for g in (g1,g2):self.assertEqual(str(uuid.UUID(g.group_id)),g.group_id)
        pending=self.recovery(a,t,f1);self.assertIsInstance(pending.response,SameTransactionReplay);self.assertEqual(pending.group_id,g1.group_id)
        h.detach();c.commit();c,h,a,t=self.consumer()
        self.assertEqual(self.recovery(a,t,f1).group_id,g1.group_id);self.assertEqual(self.recovery(a,t,f2).group_id,g2.group_id)

    def test_changed_complete_input_conflicts_without_reapplication(self):
        c,h,a,t=self.ready(document_ids=('adoc',));semantic,request=self.input(a,t)
        original=self.frame(semantic,request);a.apply_in_transaction(t,semantic,request,documents=self.documents)
        h.detach();c.commit();c,h,a,t=self.consumer()
        changed=replace(semantic,asserted_origin=MapValue(entries=(MapEntry(key='x-action',value=TextValue(kind='string',text='different')),)))
        result=self.recovery(a,t,self.frame(changed,request))
        self.assertIsInstance(result,GroupFailed);self.assertIsInstance(result.failure,RequestConflict)
        self.assertIsInstance(self.recovery(a,t,original),GroupSuccess)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))

    def test_other_person_does_not_share_original_request_scope(self):
        c,h,a,t=self.ready(document_ids=('adoc',));semantic,request=self.input(a,t);frame=self.frame(semantic,request)
        a.apply_in_transaction(t,semantic,request,documents=self.documents);h.detach();c.commit()
        self.admin.execute('CREATE ROLE other_request_person LOGIN');self.addCleanup(self.admin.execute,'DROP ROLE other_request_person')
        self.admin.execute('GRANT group_writer TO other_request_person WITH SET FALSE')
        p=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);p['user']='other_request_person'
        c=psycopg.connect(**p,autocommit=True,options='-c statement_timeout=10000');c.execute('BEGIN')
        h=adopt_psycopg_host(c);self.consumer_connections.append((c,h));a=create_reference_assembly(CatalogRuntimeConfiguration(),h).value;t=h.adopt_transaction().value
        result=self.recovery(a,t,frame);self.assertIsInstance(result,GroupFailed);self.assertIsInstance(result.failure,UnauthorizedPerson)

    def test_retained_owner_denial_precedes_changed_input_conflict(self):
        c,h,a,t=self.ready();semantic,request=self.input(a,t);frame=self.frame(semantic,request)
        a.apply_in_transaction(t,semantic,request,documents=self.documents);h.detach();c.commit()
        for role in ('other_request_reader','other_request_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN');ah=adopt_psycopg_host(self.admin);at=ah.adopt_transaction().value;aa=create_reference_assembly(CatalogRuntimeConfiguration(),ah).value
        self.assertIsInstance(aa.configure_module_access_in_transaction(at,(ModuleAccessGrant('zdoc','m','other_request_reader','other_request_writer'),)),Ok)
        ah.detach();self.admin.commit()
        self.admin.execute('GRANT other_request_writer,group_reader TO consumer WITH SET FALSE');self.admin.execute('REVOKE group_writer FROM consumer')
        c,h,a,t=self.consumer()
        changed=replace(semantic,asserted_origin=MapValue(entries=()))
        for frozen in (frame,self.frame(changed,request)):
            result=self.recovery(a,t,frozen);self.assertIsInstance(result,GroupFailed);self.assertIsInstance(result.failure,UnauthorizedPerson)

    def test_rolled_back_request_is_unobserved_and_never_reapplied(self):
        c,h,a,t=self.ready(document_ids=('adoc',));semantic,request=self.input(a,t);frame=self.frame(semantic,request)
        applied=a.apply_in_transaction(t,semantic,request,documents=self.documents).value
        self.assertIsInstance(applied,GroupSuccess);h.detach();c.rollback()
        c,h,a,t=self.consumer();before=self.group_effect_counts()
        result=self.recovery(a,t,frame)
        self.assertIsInstance(result,GroupUnavailable);self.assertEqual(result.reason,'request_not_observed')
        h.detach();c.commit();self.assertEqual(self.group_effect_counts(),before)

    def test_corrupt_frame_is_local_typed_refusal_without_host_execution(self):
        c,h,a,t=self.ready(document_ids=('adoc',));semantic,request=self.input(a,t);frame=self.frame(semantic,request)
        corrupt=replace(frame,input=replace(frame.input,sha256='0'*64))
        with patch.object(type(h),'_run_operation',side_effect=AssertionError('Invalid frame must not execute')):
            result=self.recovery(a,t,corrupt)
        self.assertIsInstance(result,GroupFailed);self.assertIsInstance(result.failure,InvalidGroupInput)

    def test_original_source_frame_cannot_be_replaced_on_recovery(self):
        c,h,a,t=self.ready(document_ids=('adoc',));semantic,request=self.input(a,t);frame=self.frame(semantic,request)
        a.apply_in_transaction(t,semantic,request,documents=self.documents);h.detach();c.commit()
        from truss import freeze_group_request
        changed=tuple(replace(d,content=d.content+b'\n') for d in self.documents)
        altered=freeze_group_request(semantic,request,documents=changed).value
        c,h,a,t=self.consumer();before=self.group_effect_counts();result=self.recovery(a,t,altered)
        self.assertIsInstance(result,GroupFailed);self.assertIsInstance(result.failure,InvalidGroupInput)
        self.assertIsInstance(self.recovery(a,t,frame),GroupSuccess)
        h.detach();c.commit();self.assertEqual(self.group_effect_counts(),before)

    def test_read_only_recovery_refuses_unselected_lock_profile(self):
        c,h,a,t=self.ready(document_ids=('adoc',));semantic,request=self.input(a,t);frame=self.frame(semantic,request)
        a.apply_in_transaction(t,semantic,request,documents=self.documents);h.detach();c.commit()
        c,h,a,t=self.consumer();h.detach();c.rollback();c.execute('BEGIN READ ONLY')
        h=adopt_psycopg_host(c);self.addCleanup(h.detach)
        a=create_reference_assembly(CatalogRuntimeConfiguration(),h).value;t=h.adopt_transaction(access_mode='read_only').value
        result=self.recovery(a,t,frame)
        self.assertIsInstance(result,GroupUnavailable);self.assertEqual(result.reason,'profile')
