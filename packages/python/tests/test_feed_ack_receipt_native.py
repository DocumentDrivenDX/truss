# SPDX-License-Identifier: MIT OR Apache-2.0
"""Small ordinary-role source ACK receipt and uncertain-commit reconciliation flow."""
from truss import Ok,FeedReceiptAcknowledged,FeedAckReconciled,FeedUnavailable
import test_feed_runtime_native as feed_tests

class FeedAckReceiptTests(feed_tests.FeedRuntimeTests):
    for _name in tuple(n for n in dir(feed_tests.FeedRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None

    def invoke(self,assembly,tx,page,*,read=False,receipt=b'destination receipt\x00exact',publication='publication-1'):
        provider=assembly.feed(assembly.feed_selection).capability
        operation=provider.reconcile_feed_ack_in_transaction if read else provider.acknowledge_feed_with_receipt_in_transaction
        result=operation(tx,page,destination_id='delta-local',request_sha256='a'*64,publication_id=publication,receipt_bytes=receipt)
        if not isinstance(result,Ok):self.fail(repr(result)+' '+str(assembly._host._custody.last_attempt.error))
        return result.value

    def test_atomic_receipt_and_fresh_read_reconciliation(self):
        connection,host,assembly,tx=self.enrolled()
        page=self.read_page(assembly,tx)
        pending=self.invoke(assembly,tx,page)
        self.assertIsInstance(pending,FeedReceiptAcknowledged);self.assertEqual(pending.outcome,'advanced');self.assertEqual(pending.durability,'pending')
        self.assertEqual(pending.receipt.receipt_bytes,b'destination receipt\x00exact')
        host.detach();connection.rollback()
        connection,host,assembly,tx=self.readonly()
        missing=self.invoke(assembly,tx,page,read=True)
        self.assertIsInstance(missing,FeedAckReconciled);self.assertEqual(missing.outcome,'missing');self.assertIsNone(missing.receipt);self.assertEqual(missing.checkpoint,page.prior)
        host.detach();connection.rollback()
        connection,host,assembly,tx=self.consumer()
        self.assertEqual(self.invoke(assembly,tx,page).outcome,'advanced')
        host.detach();connection.commit()
        # Simulate lost COMMIT response: fresh observation performs no second ACK write.
        connection,host,assembly,tx=self.readonly()
        matched=self.invoke(assembly,tx,page,read=True)
        self.assertEqual(matched.outcome,'matched');self.assertEqual(matched.receipt,pending.receipt)
        conflicting=self.invoke(assembly,tx,page,read=True,receipt=b'different')
        self.assertEqual(conflicting.outcome,'conflicting');self.assertEqual(conflicting.receipt,pending.receipt)
        host.detach();self.assertIsNone(connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0]);connection.rollback()
        connection,host,assembly,tx=self.consumer()
        self.assertEqual(self.invoke(assembly,tx,page).outcome,'equal')
        conflict=self.invoke(assembly,tx,page,receipt=b'different')
        self.assertIsInstance(conflict,FeedUnavailable);self.assertEqual(conflict.reason,'conflict')
        self.run_group(assembly,tx,(self.create(label='after',value='after'),),'receipt-later')
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        later=self.read_page(assembly,tx)
        self.assertNotEqual(later.prior,later.next)
        self.ack(assembly,tx,later)
        host.detach();connection.commit()
        connection,host,assembly,tx=self.readonly()
        historical=self.invoke(assembly,tx,page,read=True)
        self.assertEqual(historical.outcome,'matched');self.assertEqual(historical.checkpoint,later.next)
        self.assertEqual(self.invoke(assembly,tx,later,read=True,publication='publication-2').outcome,'missing')
        host.detach();connection.rollback()
        connection,host,assembly,tx=self.consumer()
        backfill=self.invoke(assembly,tx,later,publication='publication-2')
        self.assertIsInstance(backfill,FeedUnavailable);self.assertEqual(backfill.reason,'conflict')
        host.detach();connection.rollback()
