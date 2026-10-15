# Actual browser frozen batch execution

Actual Chromium153/PGlite0.5.10/PostgreSQL18.6/Bun1.4.2. Public catalog/load/action/
read-grant, original Weft SQL lowering and original UMF Key/manifest preparation
lead to actual updates of three Products in two batches (two and one). Their
versions become2; the fourth object stays unchanged. Job reaches completed with
a contiguous two-batch prefix. Original first-batch replay and reopen recovery
are byte-identical. No administrative business data seeding is used.

Basic additional witnesses: two wholly no-op batches retain versions and emit
no journal entries; an intervening public update makes the frozen second item
stale, and conflict item1 leaves first item unchanged; one test-only SQL trigger
raises during the second item update after the first item has written, proving
actual rollback of its object/version/journal changes. The confirmed failure is
retained, recovered unchanged and stops the job. Final physical inspection finds
four objects, four exact key memberships/reservations, generation1, eight journal
rows (four creates, three original updates, one intervening update) and matching
original event byte hashes. Failed/no-op/stale batches add no business event.

Strict browser TypeScript passes. Two-CWD asset builds match the exact bundle
used by the final basic Chromium run:

- Manifest 1d8b6668d0e7596139b522e0cdc1829b06a2b26bc1e39bf8af4677c59465f387
- Provider 1a6f849ffd60af5510badb5ce018bfb5276d7dd70718d53ae83cbf40d2f3b809

Astra Ultra reviewed plan and completed source. Its finite correction restricts
lease-time evaluation to fresh durable effect admission. Admitted execution
continues checking exact owner/fence/state without interrupting a serialized
transaction because its lease expires. Completion conditions above passed; no
additional verification campaign was requested.

Before the business callback, a private PGlite effect-admission record commits
and flushes. Business effects, per-property browser journal, full verified item
results, receipt, original outcome and progress are then coatomic. Existing
admission never redispatches; original terminal result or indeterminate are the
only recovery outcomes. Missing never establishes rollback. Only original live
callback rollback acknowledgement allows a separately persisted terminal failure.
Uncertain commit/rollback/result flush/custody fences. No sidecar, native CDE or
pg_xact_status rollback inference is claimed.

Scope: required-String rootless Records and original bounded constant set recipe.
Browser journal carriers/adjunct remain separate from native history. Cancellation,
feed, retention, arbitrary crash/restore qualification, wider values/relationships
and complete local-bulk support remain unfinished. Python/native66/67 and published
Weft wheels are unchanged by this private browser source delivery.
