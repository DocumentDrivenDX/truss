# Installation-wide current-authority guard

Candidate realization of CONTRACT-005's current-authority exclusion, not an installed or adopted profile. Select one guard for the complete installation rather than inferring per-module guards from catalog labels. This permits conservative serialization of all participating grant/role/policy changes while preserving the full qualified owner union for authorization. More granular guards require a separately complete authority-dependency mapping.

## Fixed home and identity

The [table SQL](installation-policy-guard-v0.1.proposal.sql) and [UMF capture](installation-policy-guard-v0.1.proposal.umf.json) now retain this candidate declaration. The [private generation UPDATE](installation-policy-generation-advance-v0.1.proposal.sql) supplies a checked original-identity/profile/expected-generation effect after complete authority-delta parity; it does not itself establish proof or exclusion.

Allocate `truss.policy_generation_guard` with `singleton smallint PRIMARY KEY CHECK(singleton=1)`, exact installation identity bytes, policy-profile bytes and `generation bigint NOT NULL CHECK(generation>0)`. Identity/profile carriers are nonempty bytea and immutable for the installed profile. Initialization inserts exactly one row with generation 1 in the same verified bootstrap transaction as installation initialization. Missing, duplicate, incompatible or replaced guard refuses admission; no operation repairs it on demand.

The installer must inventory the table/columns/checks/PK and original identity/profile bytes, plus protected acquisition/update routines and effective privileges. Ordinary roles cannot modify/delete the row or reinitialize generation. The ready marker cannot publish until this home and controlled authority paths are included in complete native parity. This table is not yet in layout 0.9.

## Protected mutation protocol

Participating grant/helper, role membership, policy, helper ownership/security and relevant native privilege changes acquire required catalog locks first, then the installation guard exclusively, before business/owner locks. The profile must inventory every controlled/excluded administrative path. Unmediated superuser/owner actions invalidate qualification; a guard cannot physically constrain arbitrary external administration.

Capture complete original authority inputs, validate the intended delta, perform effects and independently compare resulting effective authority under the same exclusion. For an actual authority change, checked-increment generation exactly once before publication in the same transaction. At signed bigint exhaustion refuse and require explicit installation/profile transition; never wrap, reset or silently relabel continuity. No-op input alone is insufficient: native effective delta determines whether authority changed. Rollback restores effects and generation together. Original commit uncertainty remains executor recovery, not another update attempt.

## Guarded read/write admission

The [private acquisition SELECT](installation-policy-guard-acquire-v0.1.proposal.sql) returns four explicit fields and obtains the candidate native share lock only in a compatible scope. Decode exactly one row: singleton canonical text 1, even-length canonical native hex for the two nonempty original byte carriers, and positive canonical bigint generation within 1–9223372036854775807. Independently compare identity/profile with original installed admission before reading authority inputs. Zero/extra rows, SQL NULL, malformed/truncated bytes, descriptor substitution or unknown native completion refuses; there is no insert-on-miss repair. Native error attribution and actual lock/transaction custody remain CONTRACT-007 obligations.

A successful SELECT is only guard acquisition evidence. The selected profile must additionally prove a coherent current effective-authority observation while that exclusion remains held, including fixed-snapshot behavior. A serialization/snapshot conflict follows original transaction containment and retry rules; the helper cannot secretly retry inside a caller's old snapshot. The query is unavailable to an ordinary read-only data transaction and may only use a separately qualified coordinator when that profile is selected. Do not infer read-only support from capture/export success.

An operation admits the exact installation/profile and obtains the native share guard before disclosure or protected write authority. Observe generation and actual acting-role/effective inputs coherently with the complete owner union. Under a fixed data snapshot, qualification must show how current authority is observed; a snapshot-old guard/grant row cannot establish freshness. If the native row-lock/snapshot profile cannot establish it, refuse or use CONTRACT-005's qualified separate coordinator protocol. Do not change the caller's isolation/access mode, commit its transaction or invent a fresh snapshot in that transaction.

Retain guard/context custody through every required publication/operation boundary. The separate read-only coordinator, when selected, holds the same installation exclusion while supplying independently admitted current role/grant evidence; it does not become the data transaction owner. Coordinator disconnect/unknown release invalidates publication and retains recovery custody. Reentrant use must verify original admission rather than treat a copied generation as a lock token.

## Independent native schedules

PG-01 initializes exact identity/profile/generation and rejects missing/extra/substituted guard or unauthorized raw update.

PG-02 runs read-before-revoke and revoke-before-read under actual locks. A previously admitted read may finish while revocation waits; later admission observes the new authority or refuses. No wall-clock immediate revocation is claimed.

PG-03 changes native role membership/privilege/helper dependencies without changing module_access. The controlled path advances generation and admission compares full effective authority; excluded uncontrolled paths invalidate the profile.

PG-04 retains repeatable-read/read-only data snapshots across authority changes. Stale native observation refuses; separately qualified coordinator preserves data snapshot and current authority without hidden commit.

PG-05 forces failure after authority effects and around generation/commit acknowledgment. Rollback preserves original state; unknown outcomes reconcile exact originals with no replacement increment.

PG-06 tests no-op delta, generation maximum, owner-union change and lock-order inversion. No wrap/reset, stale union or acquisition of an earlier lock after the guard is allowed.

These tests remain not_run. Native locking, current observation, bounded inventory/resource admission, exact types/security/grants and deployment behavior require selected profiles and actual evidence. The guard supplies exclusion, not authorization or semantic equality by itself.


## Native proposal-source precursor — 2026-10-12

The actual three SQL files above now run in the public-created graph fixture on
PostgreSQL18.6. Native acquisition returns exact actual installation identity
bytes, fixture-profile bytes and generation1. A participating role changer waits
on the original share guard while an ordinary buffered read finishes, then
commits its role effect and checked generation2 together. Controlled restoration
advances3 without reset. A stale expected generation returns zero rows, and
rollback preserves both role flags and generation3. Source pins and88 total
ontology observations are retained in
`../../04-build/evidence/security-proposed-authority-guard-native-20261012/receipt.json`.

This is partial PG-02/03/05 feasibility, not their complete qualification. The
table is added as a standalone test extension after public installation; verified
bootstrap, protected routine/privilege parity, complete native authority-delta
comparison, all control-plane participants and coordinator lease/release remain
unimplemented. The proposed profile stays unadopted. Unmediated administration
can still bypass this cooperative guard and invalidate qualification.


### Native generation boundary controls — 2026-10-12

The existing ontology/authority regression now passes94 native observations.
Foreign installation/profile bytes produce zero generation advance; ordinary
reset refuses42501. Signed-bigint maximum remains exact and refuses advance
without wrap; rollback restores original role flags and generation3. Sources
and terminal output are retained under
`docs/helix/04-build/evidence/security-authority-generation-boundaries-20261012/receipt.json`.
This is partial original guard PG-01/05/06 evidence under CONTRACT-005/063, not
verified bootstrap, complete authority/participant parity or coordinator/public
release admission. No full PG schedule or original backend case is promoted.


### Native original coordinator loss — 2026-10-12

The ontology/authority regression now passes101 observations. After native
blocking evidence, termination of only the owned original coordinator releases
its exclusion; the participating authority writer commits generation4. Native
liveness probing fails before local close. The fixture withholds its pending
buffer, preserves the separate data transaction's INTRANS/prior work and a fresh
read sees revocation. Failed attempt and exact sources/results:
`docs/helix/04-build/evidence/security-coordinator-loss-20261012/receipt.json`.
Trace CONTRACT-005/063 and STP-057 L03/L11. This is native loss plus fixture
arbitration, not production lease/quarantine/recovery or streaming/cached-buffer
release. Full participant/source/caller/publication integration remains required;
no original backend case is promoted.


### Portable candidate guard observation decoder — 2026-10-12

`security-guard-observation.ts` now checks the original acquisition's four TEXT
OID25 descriptors, one four-cell row, canonical singleton/hex/positive bigint
and exact supplied identity/profile bytes. It rejects missing/extra/reordered
descriptors, sparse/extra rows, null/noncanonical/overflow values and getter/
iterator substitution. Local bound is32KiB per identity/profile, not a product
ceiling. Generation stays exact TEXT, including bigint maximum.

Six tests, strict security-source typing,102 native ontology observations and
Python boundaries723imports pass. Actual native descriptors/row decode identically
in Bun and Chromium153. Evidence:
`docs/helix/04-build/evidence/security-guard-observation-decoder-20261012/receipt.json`.
Trace original guard acquisition under CONTRACT-005/063. This returns candidate
values only: supplied expectations are not trusted issuers, copied values are
not native exclusion/completion evidence, and no AuthorityLease is created.
Production original source/caller/liveness, bootstrap and release remain required.


### Positive probe is insufficient for final release — 2026-10-12

The native ontology fixture now obtains a successful `SELECT 1` on the original
coordinator after verifying the waiting authority writer. It then terminates only
that owned coordinator, observes acknowledged revocation, and compares the retained
RA/RAB buffer with a fresh empty ordinary read. The fixture discards that buffer;
publishing it using the earlier positive probe would violate current authority.
A positive liveness response does not establish exclusion through later disclosure.

The five-event finite ordering model retains three solver queries: probe-only
stale-release SAT, exclusion-through-release stale-release UNSAT, and successful
release before loss SAT. An independent enumeration checks all120 total orders.
The UNSAT claim assumes the very exclusion-through-release property that production
coordination must implement; it does not establish that property for a native
connection or a host callback. It does not prove arbitrary concurrency, driver
refinement, identity custody, simultaneous events or clock expiry.

Sources,176 native observations and formal results are retained in
`../../04-build/evidence/security-positive-probe-release-20261012/receipt.json`.
Trace CONTRACT-063, STP-057 L03/L11 and US-057-AC2/AC7. No required case is
promoted. A future production admission path must refuse buffered publication
when continuous release exclusion cannot be established; merely adding a final
pre-publication probe does not close this race.


### Durable publication custody candidate — 2026-10-12

The transaction-held guard alone cannot exclude an authority acknowledgment
after coordinator loss but before final protected release. The candidate
`installation-publication-claim-v0.1.proposal.sql` adds a private durable claim
with exact original operation, installation, profile and generation bytes. It is
not adopted in the layout and is not an AuthorityLease issuer.

The original operation owner acquires schema-head then guard SHARE, registers
the original claim through `installation-publication-claim-register-v0.1.proposal.sql`,
and confirms its commit before any protected disclosure. An uncertain registration
retains recovery custody and withholds disclosure; it never retries with a new
operation identity. The claim persists after disconnect. Participating authority
writers acquire schema-head then guard UPDATE and freshly establish zero
outstanding claims before effects. Any claim, including one with incompatible
identity/profile, refuses the complete authority change. The
`installation-policy-generation-advance-v0.2.claim.proposal.sql` repeats that
condition at the post-effect generation gate; zero rows requires whole rollback.
Version0.1 writers are incompatible with this candidate and cannot coexist as
admitted participants. Complete native parity must enforce that distinction.

Only the original publication/recovery owner may settle the exact claim through
`installation-publication-claim-settle-v0.1.proposal.sql`, under the same SHARE
lock order, after every protected release has finished or was conclusively
withheld. Settlement commit must be confirmed. A timeout, coordinator death,
positive probe, copied token or caller statement never proves completion. No
TTL or automatic deletion is permitted. An unresolved claim can deny authority
changes indefinitely; recovery must establish original sink/resource completion
before settlement. Availability does not override this safety requirement.

The actual four new SQL sources execute in the public ontology fixture. A
committed claim survives termination of its owned coordinator; guarded generation
advance returns zero; four operation/installation/profile/generation mismatches
leave it intact; ordinary deletion refuses42501. Fixture-confirmed withholding
then permits exact settlement and a generation advance, which rolls back to
preserve the original subsequent fixture state. Native total183 observations.
Three finite formal queries retain durable stale-release UNSAT, successful
release after loss SAT and automatic-clear stale-release SAT; an independent
oracle enumerates all120 event orders. UNSAT assumes authentic settlement only
after release and complete writer participation. It proves neither premise nor
arbitrary concurrency/native SQL/driver/sink refinement.

Evidence and exact source delta:
`../../04-build/evidence/security-durable-publication-claim-20261012/receipt.json`.
Trace CONTRACT-005/063, STP-057 L03/L11, US-057-AC2/AC7. Production original
operation issuance, durable registry capacity/admission, bootstrap/privilege
parity, complete source/fact/authority participants, commit uncertainty and
final sink/recovery integration remain required. No original required case
is promoted and no ordinary security API is enabled.


### Overlapping publication and pending registration — 2026-10-12

Two exact original operation claims coexist. Duplicate registration refuses23505
without replacing either; stale generation registration returns zero. Settling
one claim leaves participating generation advance refused; rolled-back settlement
of the other leaves its durable row. Exact confirmed settlement of both permits
the existing guarded advance. A separate pending registration holds native guard
SHARE before commit. The participating authority writer actually waits on that
original PID, then a fresh post-drain statement sees the committed claim and
returns zero advance. Native suite total190 observations.

A finite transition explorer visits all58 reachable states/107 edges for exactly
two one-shot operations in one generation, with no acknowledgment while any
publication remains pending. Its automatic-clear-on-loss mutant reaches74 states
and9 unsafe states, including register/loss/ack before completion. This is bounded
model exploration, not arbitrary-cardinality induction or native refinement.
Original serialized registration, settlement after completion, fresh snapshot
and complete writer participation are premises.

Retained original SQL/test sources, successful and failed native logs, explorer
and receipt:
`../../04-build/evidence/security-overlapping-publication-claims-20261012/receipt.json`.
Trace CONTRACT-005/063, STP-057 L03/L11 and US-057-AC2/AC7. The first concurrent
observer incorrectly used an earlier data-writer PID; the corrected test uses
the actual authority writer PID and a blocker deadline below statement timeout.
Production issuer/sink authentication, capacity, uncertainty/recovery, bootstrap
and complete participant parity remain required; no backend acceptance case
is promoted.


### Arbitrary-claim inductive safety — 2026-10-12

The abstract publication model now has an inductive invariant over arbitrary
integer-indexed claim arrays: every pending protected release has an active
durable claim whose generation equals the current installation generation.
Initialization, registration, completion, settlement, native-loss stuttering and
guarded generation advance preserve it. A writer acknowledgment requires absence
of every active claim, so it cannot overlap a pending protected release. This
extends the formal cardinality scope beyond the earlier fixed two operations to
arbitrary finite sequences of these abstract atomic transitions.

Twelve Z3 obligations and retained-formula replays pass: eight UNSAT safety/gate
checks, one SAT reachable pending operation and three SAT premise-breaking
controls for early settlement, loss-triggered deletion and partial writer checks.
The prior independent two-claim finite explorer replays separately. Native loss
is modeled as leaving durable arrays unchanged; that is a premise of this model,
not an inferred guarantee for a concrete connection. Stale-registration refusal
checks the exact generation-equality gate, not source/issuer authentication.

The proof does not establish those transition premises for the SQL/driver/sink.
It assumes serialized complete registration/writer checks, authentic original
completion and settlement, durable state on loss, and complete participation.
Identity anti-reuse, registry capacity, commit uncertainty, fresh native snapshots,
source/fact coverage, sink authenticity, clock expiry, fairness/liveness and
production adoption remain open. In particular, the current delete-based0.1
claim candidate retains no native tombstone preventing reuse of settled operation
bytes; original issuer lifetime uniqueness is not established by this proof.

Exact formulas, proof source, counterexample witnesses, replay and hashes:
`../../04-build/evidence/security-publication-induction-20261012/receipt.json`.
Trace CONTRACT-005/063, STP-057 L03/L11 and US-057-AC2/AC7. Native190-observation
feasibility remains separately qualified; no required backend case is promoted.


### Retained original publication identities — 2026-10-12

The separately versioned0.2 tombstone candidate adds nonnull `settled` to the
private claim table. Registration still inserts exact original operation bytes
under a permanent primary key. Settlement updates only an unsettled matching
operation/installation/profile/generation to `settled=true`, retaining all original
bytes and generation. It never deletes the row. Repeated settlement returns zero
and requires original reconciliation, not an invented new completion.

The0.3 tombstone generation-advance source checks absence of every **unsettled**
claim, so completed identities do not block authority advancement. Earlier0.1
delete-based settlement and0.2 all-row generation gating are incompatible with
this candidate; production bootstrap/callable parity must forbid mixing them.
These are fresh fixture DDL/profile sources, not an installed layout migration.

Actual native SQL retains both original settled identities, rejects each replay
with23505 and returns zero for repeated settlement. Overlapping/pending
registration drain and generation advancement still pass; total193 observations.
The seven abstract lifetime checks include monotone retention across registration,
settlement and loss, replay refusal, a reachable fresh token, delete-based replay
and removal counterexamples. The latter proof assumes never-used registration
and retained tokens; native PK execution provides separate limited feasibility.
Neither establishes original issuer identity, authentic sink completion, concrete
SQL refinement or complete administration/privilege closure.

Permanent tombstones introduce retention and resource obligations. Production
must bound/admit registry work, refuse before disclosure on capacity exhaustion,
and preserve lifetime token uniqueness across cleanup, profile transitions and
restores. Compaction may not simply remove settled identities and reopen reuse.
Original commit uncertainty/reconciliation, bootstrap, complete participant
coverage and trusted settlement remain required.

Sources,193 native observations, seven formulas/results and hashes:
`../../04-build/evidence/security-publication-tombstones-20261012/receipt.json`.
Trace CONTRACT-005/063, STP-057 L03/L09/L11 and US-057-AC2/AC5/AC7. This extends
the candidate only; no required backend acceptance case is promoted.


### Bounded retained publication registration — 2026-10-12

The separately versioned0.3 capacity registration source admits original operation
bytes1..2048 and a verified-profile capacity integer1..1048576. These are local
implementation bounds, not shared semantics or product ceilings. Capacity counts
all retained identities, including settled tombstones. Exhaustion refuses before
disclosure, without deleting identities or choosing a new operation/profile.
The bounded count reads at most the selected capacity rows; this is a logical
row-count bound, not native heap, scan-cost, CPU or allocation qualification.

Count and insertion require original schema-head SHARE, guard SHARE, then
`installation-publication-claim-capacity-lock-v0.1.proposal.sql`'s SHARE ROW
EXCLUSIVE table lock, retained through commit/rollback. The count runs in a fresh
READ COMMITTED statement after acquisition. All registrants must follow this
order/source; uncapped0.2 registrations are incompatible with positive capacity
admission. Capacity must be fixed by authenticated original installation/profile,
never supplied as an ordinary caller option. That binding remains unimplemented.

The native fixture retains three earlier settled identities, refuses full/zero/
negative/oversized capacities and oversized operation bytes, then races two
registrants for the fourth slot. The second actually waits on the first's original
PID and its fresh count refuses after the first commits. Settlement of that
fourth identity does not reopen capacity. Suite total197 native observations.
Five integer-cardinality checks preserve the cap under fresh serialized counts
and retain a stale-shared-count oversubscription witness; they assume the
serialization/freshness and fixed-capacity premises rather than proving native
SQL refinement.

Sources, successful and failed native logs, formulas/results and hashes:
`../../04-build/evidence/security-publication-capacity-20261012/receipt.json`.
The first test binding used repeated positional parameters incorrectly; supported
psycopg named parameters now preserve the original SQL source. Trace
CONTRACT-005/063, STP-057 L03/L11 and US-057-AC2/AC7. Whole resource budgets,
original profile/issuer/sink authentication, complete participant/bootstrap
parity, uncertainty/recovery and safe lifetime retention remain required.
No required backend acceptance case is promoted.


### Capacity acquisition interruption containment — 2026-10-12

A blocked capacity acquisition now executes two native interruption schedules.
A150ms native lock timeout returns55P03. Separately, native blocker evidence
precedes cancellation of only the owned original waiter, whose actual command
returns57014. Both transactions are INERROR until confirmed rollback to the
admission savepoint. Earlier temporary-table work survives in INTRANS; actual
pg_locks inspection finds zero remaining schema-head/guard/claim locks acquired
inside the savepoint, and all four retained claim identities remain unchanged.
No claim registration or protected result is published by the refused attempt.
Suite total201 native observations.

Sources, terminal logs and native observations:
`../../04-build/evidence/security-publication-capacity-interruption-20261012/receipt.json`.
Trace CONTRACT-005/063, STP-057 L03/L11 and US-057-AC2/AC7. This qualifies the
explicitly confirmed native fixture branches only. Unknown interruption/rollback
outcomes still require original custody/quarantine; elapsed time or cancellation
request alone never establishes containment. Production host recovery, profile
binding, registry/issuer/sink and complete bootstrap/participant qualification
remain required. No original backend acceptance case is promoted.


### Native profile-bound publication capacity — 2026-10-12

The0.4 registration candidate removes the fifth capacity parameter. It joins
the original guard to a private native `policy_publication_capacity` row by
singleton and complete installation/profile bytes, then uses that row's checked
capacity. The new capacity home has a singleton PK, nonempty original bytes and
nonnull integer capacity1..1048576. Ordinary roles receive no access. Missing
or mismatched capacity homes refuse without repair. This is fresh fixture DDL,
not an adopted installation/migration or authenticated profile issuer.

Profile changes must take original guard UPDATE and complete native profile
transition/parity; registration retains schema-head/guard SHARE and the capacity
serialization lock through commit. Every admitted registrant must use the same
profile-bound source. Caller-supplied-capacity0.3/uncapped sources cannot coexist
as admitted alternatives. The native JOIN establishes byte correspondence only;
verified bootstrap, exact full native source/census and current issuer custody
remain required before production admission.

The fixture separately rolls back missing-row, wrong-installation, wrong-profile
and exhausted-profile mutations, each yielding zero registration rows. Ordinary
capacity UPDATE refuses42501. A matching original capacity5 admits the fifth
retained identity; the next operation refuses. Suite total205 observations.
Supported named psycopg bindings handle the repeated token parameter; the first
failed positional-binding run remains retained.

Sources, successful/failed terminal logs and hashes:
`../../04-build/evidence/security-native-capacity-profile-20261012/receipt.json`.
Trace CONTRACT-005/063, STP-057 L03/L11 and US-057-AC2/AC7. Resource budgets,
complete profile/source/participant/callable parity, original operation issuer,
authentic sink settlement and uncertainty/recovery remain unqualified. No
required backend acceptance case is promoted.
