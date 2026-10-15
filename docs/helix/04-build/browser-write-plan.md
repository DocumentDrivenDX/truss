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

## Submission checkpoint

Astra approved separating persistent submit/control/review from execution.
The implemented API uses a job submission key independently of a stable caller
control key/attempt. Full frozen manifest/source intent excludes seal-control
IDs, so two genuine seals of the same work identify one job. Original full first
seal remains evidence. Current action/model/cut authorization binds control
input; exact original outcome lookup precedes fresh seal admission. Semantic
refusals are retained as refusals, control rollback requires durable separate
noncommit confirmation, and unknown settlement fences. Recovery never executes.
Actual basic Chromium verifies original replay/reopen recovery, same-job fresh
control, distinct genuine seal equivalence and retained refusal recovery.
Claim and execution remain the next implementation step.

## Claim checkpoint

Astra approved a separate claim/recoverClaim control tranche. Actual PostgreSQL
clock supplies the retained 60-second lease; exact monotone lastFence persists
per job independently of active claims. Current authorization binds operation
and captured input before original control lookup. Replay never renews; expired
running claim refuses fresh claims until later explicit custody reconciliation.
Fresh admission verifies full retained source, contiguous progress and active
claim correspondence. Active claim, running state and original sampled result
are atomic. No business effects or claimed full local-bulk capability follow.
The basic existing Chromium workflow covers claim/replay/competing refusal and
reopen recovery, retaining physical creation-only state. Actual batch execution
remains next.

## Execution checkpoint

Astra approved an existing-PGlite effect-admission record committed and flushed
before the actual business transaction; no sidecar or pg_xact_status rollback
inference. The implemented executeBatch/recoverBatch path binds current owner,
action/read grant, exact source/seal and original batch/fence. Once admitted,
lease expiry cannot interrupt the serialized transaction; subsequent checks
retain exact ownership/fence/state correspondence. Existing admission returns
only retained original terminal outcome or indeterminate, never redispatch.

Original UMF preparation/manifest/inputs/selectors/Key receipts and current
object/key/version checks preflight the entire batch. Actual constant String
sets, versions, exact browser history, verified item outcomes, receipt and
contiguous progress are atomic. No-op preserves version/journal while retaining
its outcome. Same-instance callback rollback is confirmed before separate durable
conflict/rejected/failed terminal outcome; unknown commit/rollback/result flush
fences and prohibits retry/replacement fence. Basic Chromium now passes actual
three-item/two-batch updates, original replay/reopen recovery, no-op, stale second
item without first-item effects, and a test-only second-update SQL fault proving
rollback of first-item changes/history. There is no administrative business seed.

Scope remains required-String rootless Records and original bounded constant set
actions, not full local-bulk qualification/native904. Remaining browser work:
committed journal/feed reads, cancellation, retention, consumer integration and
release packaging. Native Python ownership/current0.2 protected execution and
other full-goal work retain their existing scope; this browser checkpoint does
not replace them. Native66/67 or published wheels are unchanged.

## Local journal-page checkpoint — 2026-10-15

The public owner-only `readFeed` now returns bounded committed journal row pages
with store/incarnation cursors and exact original event/origin bytes. Astra Ultra
review and the final basic Chromium workflow passed; see
[evidence](evidence/browser-feed-20261015/README.md). Pages may split a batch;
ACKs, retention and native-feed guarantees remain unfinished.

## Cancellation tranche — 2026-10-15

Implement `cancel` and `recoverCancel` with exact `{job,control}` inputs, current
issued owner/action/read-grant admission, and immutable original control results.
Serialize through the existing worker queue and job transaction. Cancel before
effect admission makes the job cancelled and invalidates its claim; retain the
committed prefix. An already admitted unresolved batch stays reconciling with a
retained cancel request, never an inferred rollback. Terminal original outcomes
remain recoverable. Completed/stopped/cancelled jobs retain their terminal state.
Claim and fresh execution of cancelled work refuse `PAP_CANCELLED`. Persist the
control result atomically with the state change and await flush. Lost responses
use recovery only; missing remains unresolved. Retain manifests/outcomes for the
store incarnation lifetime with no purge or token reuse. This follows original
UMF CONTRACT-904/905; it adds no native security or crash-recovery claim.

Basic witness: cancel a queued public job, exact replay and reopen recovery,
claim/execution refusal, and unchanged business/journal rows. Astra Ultra reviews
the plan and completed implementation before commit.

Cancellation checkpoint: public cancel/recoverCancel implemented and reviewed by
Astra Ultra; strict TypeScript, actual Chromium and two-CWD packaging passed.
See [basic evidence](evidence/browser-cancel-20261015/README.md). Lifetime retention
is explicit; no purge is implemented. Full local-bulk qualification, broader
browser values, consumer integration and native owned/security work remain.
