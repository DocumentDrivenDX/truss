# Response to the Hohfeld Truss requests

These are the proposed boundaries for the next Truss release. They accompany the
[complete disposition and implementation plan](hohfeld-followup-plan-20261021.md),
which identifies the source snapshot, existing deliveries and acceptance gates.
The supplied request snapshot uses Truss 0.0.45. Execution begins from verified
public Truss 0.0.47, Weft 0.4.49, UMF 0.10.0 and the qualified local PostgreSQL
18.6/psycopg 3.3.6 tuple. The v0.0.47 runtime migration tranche is complete;
these semantic boundaries govern the following release. Later claims require
their own evidence.

## Replay and receipt visibility

**R18.3: recovery should survive deletion; a request must still bind its original
input and authorization scope.** We accept recovery of the original result without
reconstructing objects that may have changed or disappeared. We do not accept
returning a result solely because a caller presents a reused key. Preserve the
original canonical request/digest, reject different input under the same identity,
and reauthorize against retained ownership. Another person has a different request
scope; cross-person replay would require an explicitly authorized shared namespace.
The corpus should distinguish these two requirements rather than treating both as
the same retry guarantee. [ADR-005](../02-design/adr/ADR-005-complete-group-request-receipts.md)
and [CONTRACT-009](../02-design/contracts/CONTRACT-009-group-planning-and-locks.md).

**R7: a receipt missing from the read snapshot is not necessarily an invalid
token.** It may belong to an uncommitted transaction, a rollback or an identity
that was never issued. We cannot promise to distinguish those from row absence
alone. Keep the documented pending/rolled-back `not_yet` behavior unless a new
issuance proof makes a stronger answer possible. Malformed tokens should remain
typed invalid input. We accept clearer authorization versus timeout/integrity
outcomes where disclosure-safe, without exposing hidden receipt existence.
[Receipt contract](../02-design/contracts/CONTRACT-006-change-feed.md).

**R7/R17.6: source delivery and downstream application are different evidence.**
An acknowledged source checkpoint does not independently prove an Ashlar commit.
Applied progress needs durable downstream deduplication and an atomic state/position
update. Receipt inclusion is supported within its declared scope; opaque token
strings, transaction IDs and observation times are not a general ordering API.

## Complete results, query diagnostics and resource limits

**R17.2: do not silently truncate a complete entity.** We accept selectable facts,
facts with paging and more explicit relationship projection. The current 100-key
bound remains until a replacement is qualified. A bounded relationship page or
partial result with an explicit continuation is a different contract from a
complete entity. Duplicate output names should still refuse; callers must use
distinct aliases or explicit projections in the existing profile.
[Current query limits](releases/v0.0.45.md).

**R17.4/R13/R22: better errors must not disclose unauthorized objects.** Syntax
versus unsupported-construct codes and typed nonmember refusals are reasonable.
Distinguishing a nonexistent type from a real type in a module the caller cannot
read may reveal protected catalog contents. Those cases may deliberately share a
disclosure-safe result. A database token alone does not confer enrollment; keep
minimal person-status access scoped to enrolled people unless a separately public
health probe is designed. Do not convert every privilege error into a business
denial and conceal a broken installation.
[Isolation contract](../02-design/contracts/CONTRACT-005-module-isolation.md).

**R17.5: increasing the scan ceiling is not the performance fix.** We accept a
bounded indexed key/equality/keyset path. Raising the 10,000-row source-population
cap without changing the execution plan only admits more work. Keep the current
ABI behavior until selective-source bounds, native plans and large-population
controls establish the replacement. The same applies to claims of linear import
cost: eligible set-based DML already exists, but the measured residual growth still
needs diagnosis. Fewer client statements alone do not prove efficient native work.

## Data fidelity and mutation semantics

**R18.7/R19.1: blanket unknown-property rejection conflicts with Truss's retention
contract.** Unknown values must be retained under their original names and reported,
not dropped. Enforce authored facets, declared key mutability and selected resource
limits. Do not invent a universal rule that every empty or long key is invalid.
A stricter host can declare and select such a profile.
[PRD FR-11](../01-frame/prd.md).

**R18.8: do not silently normalize stored values.** Exact decimal/timestamp tokens
are preserved today. Value-equivalence comparison can be useful, but needs an
explicit UMF-owned or selected profile rule. It must not rewrite originals or
change history, no-op detection or condition semantics accidentally.

**R18.4/5/12/15/17: retain the selected group semantics.** Restrictive delete and an
explicitly selected owned cascade remain the policies; do not offer unconditional
cascade or reveal hidden incident edges. Versions increment per changing operation;
no-ops preserve them. Conditions evaluate locked prestate, not earlier operations
of the same group. A nonexistent endpoint must not make a relationship condition
pass as if it were a valid empty object. Condition IDs remain unique within a
group. Document these rules; alternatives require deliberate new profiles.
[Mutation contract](../02-design/contracts/CONTRACT-004-mutation-and-conformance.md)
and [group contract](../02-design/contracts/CONTRACT-009-group-planning-and-locks.md).

**R18.16/19: do not fabricate a failing operation index.** Improve graph/multiplicity
diagnostics and identify a rule/entity where authorized. A final-state failure can
have several contributing operations; returning no attributable index is more
accurate than blaming the last delete. Ordinary key collisions already have native
first/middle/last and tombstone controls; reproduce the conflicting host result
before changing that path.

**R16.5: required-field addition is bounded evolution, not arbitrary extension
editing.** Accept a narrow paired core/known-DDD addition on an empty Record after
dependency validation and exclusion against racing writes. Populated records need
explicit defaults/backfill/conversion or a typed incompatibility refusal. Unknown
extension content remains preserved; ignoring its changes is not compatibility.
The active UMF physical-table migration work does not automatically implement
Truss's generic-layout catalog evolution.

## Audit, lifecycle and performance claims

**R20: observation time is not commit time.** Retain newest-observed audit semantics.
Do not relabel observation timestamps or transaction IDs as a total commit order.
Key/version projections need ordinary data-read authorization in addition to any
audit entitlement; an audit grant alone must not expose values. We accept improved
relationship-only and multi-module discovery. Legacy load audits cannot be invented
after the fact: use verified migration/backfill or an explicit unavailable boundary.
[Audit guide](../../../packages/python/README.md).

**R21.4/5: preserve data through explicit forward migration and preserve grant-batch
atomicity.** The migration tranche is already active. Export/import is not a general
substitute for preserving identities, receipts, history and feed state. A failed
module-access batch changes nothing; independent calls already let a host choose
best-effort per-module progress. A new skip mode must be explicit.
[Migration plan](runtime-migration-restoration-plan.md).

**Overhead question 4: a validator is intentionally context-bound.** Current limits,
person, installation/release and transaction/role context participate in validity.
Align caller limits to obtain reuse. A content-only fingerprint could be added
separately, but cannot authorize reuse or bypass a smaller result bound.
[Embedding contract](../02-design/contracts/CONTRACT-007-embedding-and-execution.md).

**R10/R12 and latency asks: keep delivery claims proportional to evidence.**
GitHub release assets are a usable published dependency; an index rollout, extra
driver tuples and managed Lakebase qualification need their own selected gates.
No dates or universal latency guarantee are established. Singleton/action targets
remain open in the latest host measurements. Enumeration/list targets passed that
local workload only. Hohfeld already adopted combined reads, so another instruction
to adopt them would be stale. Do not remove current authorization, rollback
containment or original-source custody to meet a statement budget.

## Corrections before requesting new work

`GroupOperationFailure.operation_code` is already public in the 0.0.45 tag.
Registration already emits element-specific missing-name diagnostics, while UMF
itself still permits optional names. Conditional catalogs, document CAS, combined
preparation/reads, pending tokens, preview, batching, audit grants and immutable
verification/compile reuse are delivered in their qualified subsets. The remaining
disputed error, collision and import-invariant reports should become minimal
public-wheel reproductions; do not assume old prose proves a current defect.

Raw Weft extension-profile refusal is a separate compiler issue. Select and qualify
the proper entrypoint/profile; stripping extensions from the original model does
not establish support for that model. Preserve the source and unknown content.

These boundaries leave substantial accepted work for the next release: typed
errors and original-request recovery, required-field admission, query facts and
paging, selective sources, residual import/write cost, completion checks and audit
discovery. Their order and native acceptance gates are in the linked plan.
