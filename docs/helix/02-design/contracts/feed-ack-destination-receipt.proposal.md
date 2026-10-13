# Destination receipt retention with source ACK

Public candidate API for CONTRACT-006 and the Python feed capability,
2026-10-13. Runtime0.38 implements this addition on PostgreSQL18.6/psycopg3.3.6.

Current `acknowledge_feed_in_transaction` retains the consumer's last prior/next
cursor and feed digest. It retains no destination receipt. `reread_feed` proves
source delivery reproducibility, not source-side receipt persistence. Plain ACK and reread APIs alone cannot satisfy exact downstream receipt reconciliation after an uncertain
source COMMIT.

Add two ordinary authorized feed operations:

```python
acknowledge_feed_with_receipt_in_transaction(
    tx, page, *, destination_id, request_sha256, publication_id, receipt_bytes
)
reconcile_feed_ack_in_transaction(
    read_only_tx, page, *, destination_id, request_sha256,
    publication_id, receipt_bytes
)
```

The exported carriers are FeedAckReceipt, FeedReceiptAcknowledged and
FeedAckReconciled. The write returns a
pending source receipt with advanced/equal disposition; the host owns settlement.
The read returns matched, missing or conflicting plus the observed checkpoint.
Authorization/context/resource failures remain explicit unavailable/execution
outcomes; they never disclose a conflicting receipt to an unauthorized person.

An append-only source row binds the native validated installation/source epoch,
consumer/registration, exact original prior/next cursor bytes and feed digest to
destination identity, destination request digest, publication identity and exact
opaque receipt bytes. Hashes support indexing/integrity; retained exact bytes
establish equality. The interval is the immutable receipt identity: changing its
destination/request/publication/receipt payload conflicts rather than creating
another receipt. Bound identifiers and receipt bytes using ordinary input limits.

The write authorizes and locks the same consumer row without waiting/retrying.
An existing exact receipt returns equal, including after later checkpoint
advances, only after checking current authority and checkpoint inclusion. A
conflicting row refuses without advancing. For a new receipt, rederive the exact
source interval, compare the whole prior checkpoint, then advance and insert in
one contained database operation. Verify the retained row/checkpoint before
returning. A contained failure confirms rollback of this operation;
transaction-unusable or uncertain settlement outcomes retain their original
uncertainty. The caller commits or rolls back the outer transaction. Refuse a first receipt for a zero-width interval.

If an older plain ACK has advanced without a receipt, refuse retroactive proof.
Keep the existing plain ACK API and its caller-asserted meaning unchanged. A
receipt is not an upgrade to VerifiedApplication or an independent observation
of another database's commit, and grants no history deletion authority.

Reconciliation requires a read-only caller transaction with no assigned xid.
It performs no ACK write. Recheck current consumer/registration/module authority,
read the immutable exact interval receipt, compare its full binding/bytes, and
check the canonical checkpoint is at least its target. Keep earlier receipts
when later intervals advance, so recovery does not depend on last-ACK fields.
Missing means no matching committed receipt is visible in this observation;
it does not prove rollback, authorize destination republication or turn an
uncertain commit into success. Conflicting means the authorized interval has a
retained receipt with different immutable destination facts. Matched confirms
source-side retention and checkpoint inclusion only. Ashlar verifies its own
complete publication before asking for ACK.

The runtime includes an additive table, private binding helper and two entrypoint
routines, owner-only table access,
ordinary feed-role routine grants, public result carriers/provider methods,
and an additive runtime upgrade preserving original data/routine identities/ACLs.
The focused native workflow covers atomic rollback, committed fresh read-only matching,
exact equal retry, conflicting payload refusal, missing legacy receipt and
matching an earlier receipt after a later advance. No external database,
tracing, metrics, performance campaign or new retry loop is introduced.

Astra Ultra reviewed the implementation direction and these semantic boundaries.
Final implementation review and installed workflow evidence are recorded in
../../04-build/evidence/public-feed-ack-receipts-038-20261013.md.
