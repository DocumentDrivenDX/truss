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
