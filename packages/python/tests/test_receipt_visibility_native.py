"""Basic public committed receipt token and authority inclusion workflows."""
import base64,json
from truss import (Ok,ReceiptIncluded,ReceiptVisibilityUnavailable,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration)
from truss.contracts import ABSENT
from truss.groups import (GroupSuccess,CommittedReceiptReplay,SameTransactionReplay,UpdateObject,StoredObjectReference,Delete)
import test_object_mutations_native as mutation_tests

class ReceiptVisibilityTests(mutation_tests.ObjectMutationTests):
    for _name in tuple(n for n in dir(mutation_tests.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def readonly(self):
        connection,host,assembly,tx=self.consumer();host.detach();connection.execute('SET TRANSACTION READ ONLY')
        host=adopt_psycopg_host(connection);self.addCleanup(host.detach)
        return connection,host,create_reference_assembly(CatalogRuntimeConfiguration(),host).value,host.adopt_transaction(access_mode='read_only').value

    def changed_token(self,token,**changes):
        value=json.loads(base64.urlsafe_b64decode(token+'='*(-len(token)%4)));value.update(changes)
        return base64.urlsafe_b64encode(json.dumps(value,separators=(',',':')).encode()).decode().rstrip('=')

    def test_commit_token_readonly_reached_and_current_reader_authority(self):
        connection,host,assembly,tx=self.ready()
        applied,input,request=self.run_group(assembly,tx,(self.create(),),'receipt')
        self.assertIsInstance(applied,GroupSuccess);self.assertFalse(hasattr(applied.response,'receipt_token'));identity=applied.response.semantic.results[0].identity
        same=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable='/opt/homebrew/bin/bun').value
        self.assertIsInstance(same.response,SameTransactionReplay);self.assertFalse(hasattr(same.response,'receipt_token'))
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        replay=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable='/opt/homebrew/bin/bun').value
        self.assertIsInstance(replay.response,CommittedReceiptReplay);token=replay.response.receipt_token;self.assertIsNot(token,ABSENT)
        deleted,_,_=self.run_group(assembly,tx,(Delete(operation='delete_object',target=StoredObjectReference(identity=identity)),),'delete')
        self.assertIsInstance(deleted,GroupSuccess);host.detach();connection.commit()
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE');self.admin.execute('REVOKE group_writer FROM consumer')
        connection,host,assembly,tx=self.readonly()
        reached=assembly.reached_in_transaction(tx,token);self.assertIsInstance(reached,Ok);self.assertIsInstance(reached.value,ReceiptIncluded);self.assertTrue(reached.value.included)
        host.detach();connection.rollback();self.admin.execute('REVOKE group_reader FROM consumer')
        connection,host,assembly,tx=self.readonly()
        denied=assembly.reached_in_transaction(tx,token);self.assertEqual(denied.value.reason,'authorization')
        host.detach();connection.rollback()

    def test_noop_token_is_stable_and_missing_evidence_is_unavailable(self):
        connection,host,assembly,tx=self.ready()
        created,_,_=self.run_group(assembly,tx,(self.create(),));identity=created.response.semantic.results[0].identity
        self.assertFalse(hasattr(created.response,'receipt_token'))
        # The receipt must also work when its writer transaction has no creation
        # or update journal events to use as a position shortcut.
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        noop,input,request=self.run_group(assembly,tx,(UpdateObject(target=StoredObjectReference(identity=identity),set=(),unset=()),),'noop')
        self.assertIsInstance(noop,GroupSuccess);self.assertEqual(noop.response.semantic.results[0].events,())
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        first=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable='/opt/homebrew/bin/bun').value
        second=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable='/opt/homebrew/bin/bun').value
        self.assertIsInstance(first.response,CommittedReceiptReplay)
        self.assertEqual(first.response.semantic,noop.response.semantic)
        self.assertEqual(second.response.semantic,noop.response.semantic)
        token=first.response.receipt_token;self.assertTrue(token);self.assertEqual(token,second.response.receipt_token)
        host.detach();connection.rollback();connection,host,assembly,tx=self.readonly()
        connection.execute("SET LOCAL bytea_output='escape'")
        result=assembly.reached_in_transaction(tx,token);self.assertIsInstance(result.value,ReceiptIncluded);self.assertTrue(result.value.included)
        for candidate,reason in (('invalid!','invalid_token'),(self.changed_token(token,sourceEpoch='other'),'epoch_profile'),
            (self.changed_token(token,receiptStorageRowId='9223372036854775807'),'observation_integrity'),(self.changed_token(token,writerXid='0'),'observation_integrity')):
            unavailable=assembly.reached_in_transaction(tx,candidate);self.assertIsInstance(unavailable,Ok);self.assertIsInstance(unavailable.value,ReceiptVisibilityUnavailable);self.assertEqual(unavailable.value.reason,reason)
        self.assertEqual(connection.execute('SELECT 42').fetchone(),(42,));host.detach();connection.rollback()
