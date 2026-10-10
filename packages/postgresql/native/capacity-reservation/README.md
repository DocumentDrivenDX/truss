# Private capacity accounting components

`accounting.sql` supplies three actual PostgreSQL functions for the proposed
serialized singleton ledger. They are unadopted components, with no PUBLIC
EXECUTE, public Python/TypeScript API, release registration or installer readiness.
The original native0.16 layout plus reservation extension must exist first.

- `capacity_reserve_original` requires an already assigned actual transaction,
  compares complete installed layout/resource bytes, locks head before ledger,
  refuses an occupied slot or incompatible operation frontier and reserves the
  original issued ordinal/context/plan and immutable initial budgets.
- `capacity_transfer_original` resolves exactly one unfinished operation in the
  actual transaction, compares its ordinal/full context with the held reservation,
  and transfers supplied new-row/positive-growth capacity into retained totals.
  Removed bytes reduce retained totals without refunding remaining capacity.
  No new `FOR UPDATE` lookup is performed by this observer-side helper; its original
  reserve UPDATE must still own the ledger. It refuses foreign/absent custody.
- `capacity_release_original` requires the corresponding finalized operation and
  no unfinished actual-transaction operation, then clears only unused remaining
  capacity and the slot. Retained totals remain unchanged and the transaction
  keeps its native lock until actual termination.

These functions do not authenticate supplied plans/deltas or independently
recompute complete retained inventory, enforce per-row codecs/overhead, establish
current security or prove stored application-finalized authority. The protected
original event/finalizer must derive complete OLD/NEW membership and exact deltas,
validate all original resource/issuer/security/phase/generation obligations and
invoke these private functions inside the same original operation containment.
Native counter arithmetic is not a substitute for that producer. Do not grant
ordinary callers access to invent reservations, deltas or finalization.

The UMF PostgreSQL adapter retains/reloads/exports all six CREATE/REVOKE statements
in `docs/helix/02-design/contracts/capacity-accounting-v0.1.proposal.umf.json`.
Its partial declaration extractor reports zero declarations/six unhandled
statements, complete=false. The actual owner export is executed by
`check_capacity_accounting_native.py` in the design-audit evidence directory.

The latest34-observation PostgreSQL16.15 receipt covers reserve-before-registry,
actual original context correspondence, overrun/negative/foreign-profile/plan
refusals with ledger rollback, unused-only release, unfinished-frontier refusal,
A preservation after B rollback, original host rollback and actual ordinary-role
42501 denial. Synthetic one-byte artifacts, supplied carrier deltas and an explicit
administrative phase fixture qualify helper preconditions/arithmetic only. The
schedule burns fault ordinal1 before submitting B at2; it is not a native or host
issuer factory. Prior receipts/producers remain archived as historical evidence.

Next: register original helper identities/dependencies/attributes/roles, bind the
actual original issuer/account and semantic plan/event producer, derive complete
custody bytes plus native overhead, implement full retained-parity/commit guards,
and replay formal traces against ordinary-role real effects. All seven mandatory
native bodies and complete installation/publication gates remain required.

`custody-codec.sql` adds four private candidate functions for complete operation
and touch row framing. The profile includes every column, identity, generation,
presence marker and original carrier, with a preflighted8MiB output bound and an
exact column-profile refusal. Its12-check native receipt compares actual stored
rows and framing boundaries against an independent Python oracle. UMF retains
and exports all eight CREATE/REVOKE statements; declaration coverage is incomplete.
See the installation plan's “Complete-row custody accounting codec” section for
its grammar, counter-conversion obligation and remaining native work/overhead
and protected-producer gaps. Its length-only wrappers now drive the candidate native observers below;
complete protected installation remains unqualified.

`custody-size.sql` supplies three private length-only functions using the same
complete column profile and frame-size formula. The24-check native receipt
verifies stored-row sizes, exact8MiB/one-over boundaries and malformed length
refusals without transferring large carriers. It depends on the original codec
column validator. Complete protected delta derivation, retained parity, native
work/overhead and installer registration remain required before ledger binding.

`inventory.sql` supplies a private complete retained-row/byte parity verifier.
It takes head then ledger exclusion and scans all operation/touch rows across
transactions/phases, refusing RLS/inheritance and comparing original framed sizes
with retained counters. The14-check native receipt establishes administrative
membership/parity controls and rollback restoration. Original protected writers,
registered objects/resource profile and bounded native work remain prerequisites;
this verifier is not yet composed with protected event/finalizer producers.

`observation.sql` binds native operation/touch INSERT and UPDATE events to the
complete OLD/NEW size helpers and private transfer routine. DELETE/TRUNCATE
refuse. The32-check native composition receipt verifies independent framed totals,
shrink without refund, finalization capacity, event/constraint rollback and host
rollback. This is administrative component evidence; trigger/dependency inventory,
protected semantic/finalizer authority, resource adoption and all seven mandatory
bodies remain uninstalled. Its BEFORE UPDATE ordering requires closed original
trigger dependencies and complete parity before commit/publication.

`commit-check.sql` supplies an explicit private capacity closeout check: full
retained parity, complete reservation release and no retained unfinished operation.
The48-check native composition receipt includes actual COMMIT, independent
connection visibility, counter corruption/orphan refusal and preserved committed
state after rollback. It is not automatic deferred/commit-hook enforcement and
does not replace the seven semantic guards. The protected finalizer/installer must
register and enforce its original invocation under a bounded full-cohort profile.

The13-check boundary receipt now executes65536-row and512MiB complete-frame
limits for operation, touch and mixed populations, with one-row/exact-one-byte
aggregate refusals and rollback restoration. Native compressible fixtures and
single-run timings establish logical framed limits only; physical/native-work,
security, cleanup, complete deferred invocation and installer qualification remain
open. Earlier5/9-check boundary receipts retain their original producers.

`commit-cache.sql` adds a fixed four-column native memo and deferred capacity
callback. Ledger changes invalidate the actual-transaction proof; repeated queued
events share one complete closeout verification. The30-check native receipt covers
early/later checks, equal-image/new-epoch invalidation, rollback, overflow and actual
COMMIT refusal for an unreleased operation or corrupt counters. UMF retains the
source and one table/FK declaration. This unadopted adjunct still needs core/browser
projection, original installed identity/ACL/profile/account closure and all seven
semantic bodies. The callback's native cache is not cumulative work or authorization.
