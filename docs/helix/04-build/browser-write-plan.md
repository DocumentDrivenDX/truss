# Browser public writes and sealed batch execution

Scope: continue CONTRACT-905's separate local-owner profile, using the existing
browser catalog/action/read-grant and original UMF/Weft producers. This does not
activate native66 security or amend Python/native contracts. Governing sources:
packages/browser/README.md, UMF CONTRACT-905 at40f01140 and original graph-write/1,
keys/1, manifest/1 meanings. Python remains the first-release interface; this
browser work enables the explicitly requested website UPDATE consumer.

## Next implementation tranche

Expose a bounded public `loadObjects(owner, input)` for the currently accepted
required-String Record profile. Input names the fully qualified accepted Record,
contains complete member values keyed by authored field identity, and carries a
caller-retained request key/attempt. It is an atomic local import, not an action
impersonation or an administrative SQL escape. Reuse existing catalog admission,
original member order and original UMF core Key encoding. Reject missing/extra
members, invalid String values, duplicate/live/reserved keys before effects.

Write actual truss.object, object_key_bucket, object_key_reservation_bucket and
key_bucket_guard together with creation journal entries and the original replay
outcome in one PGlite transaction. Namespace keys by the actual local store and
incarnation, accepted qualified type/key definition and source cut, using a
separate browser profile rather than fabricated native installation IDs. Retain
full original UMF receipt bytes in original_context_bytes and reservation
custody. Compare full namespace/key bytes after digest lookup; exclusive worker
ownership serializes writers. A rolled back ID may be skipped, never published.

Install finite journal coverage before effects: a browser-owned partition under
a recorded fixed horizon, no default partition and no whole native groups.sql
installation. Verify actual partition identity/bounds against the retained
marker; partial or foreign installation refuses. Expiry refuses clearly.
Basic logs/deadlines/input bounds suffice; no allocation instrumentation.

Use the same explicit settlement vocabulary as seals: identical original input
replays exact original outcome, changed input conflicts, confirmed rollback is
separate from ambiguous COMMIT/flush, and unknown fences. Retain pending control
before RPC. Recovery absence is unresolved. Durable success waits for syncToFs.
Expose bounded public logical object readback for this same issued owner/profile.
Replace administrative fixture seeding in the existing basic Chromium workflow
with this API and verify persisted values, key custody, journal and replay.

## Following tranche

Submit a retained seal as a worker-owned job, then execute its original frozen
batches through the original action recipe. Revalidate owner/action/read grant,
source cut, full original manifest, Key receipt, live key identity and version
before effects. No selection rerun or prefix trimming. Keep all item effects,
key updates/reservations, journal and exact batch outcome atomic; include no-op,
conflict/refusal and rich controls. Implement replay/recovery, cancellation and
retention with explicit local-bulk/1 semantics. Never promote preview/seal into
permission or return an executable plan method. Public feed/state/receipt views
must read committed outcomes. Required basic witnesses include three items/two
batches, all-or-nothing failed batch, stale key/version, duplicate submit and
reload recovery. Broader verification follows the functional interface.

Status: Astra Ultra approved the plan with finite source corrections. The local
load/read/recovery tranche is implemented; final basic Chromium and strict
TypeScript pass. Evidence: evidence/browser-load-20261015/. It uses explicit browser event/envelope
versions and an installed two-CHECK/partition adjunct, rather than claiming
native history compatibility. Frozen batch execution remains next. No new
release or crash-safety claim yet.
