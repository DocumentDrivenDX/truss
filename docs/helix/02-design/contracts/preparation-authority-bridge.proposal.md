# Original-caller preparation authority bridge

Candidate realization of CONTRACT-005 for CONTRACT-013. No admitted native
permit, protected selection or seal is claimed by this proposal. Implemented
native components and conditional proofs are linked below; the remaining gates
must pass before the protected entrypoint is enrolled.

## Purpose and boundary

The engine owns a fresh RR/read-write connection authenticated as the original
initiating ordinary caller. It cannot adopt caller work, reconnect to a new
incarnation, change the data snapshot or substitute a service principal. A
separate engine-owned RC coordinator observes that actual native caller's
current authority. The first profile is explicitly module RBAC with original
field values; selected advanced ontology/masking/protection meaning refuses
until its original admission is qualified. Action-role authorization and
human attribution require the shared original action-gateway binding. Native
module membership proves neither of those obligations.

## Proposed source-owned surface

- `create_preparation_anchor(original_data_pid, registered_program_identity)`
  runs only through the registered private RC control issuer. It independently
  captures the actual original idle caller backend/database/person/incarnation,
  checks the selected installed source/program, and creates one protected
  immutable anchor with a native nonce and nonreused bounded integer identity.
  The original control transaction must confirm COMMIT before data BEGIN RR.
  Supplied PIDs/program identities select native objects; they cannot supply a
  principal, grants, source bytes, SQL, issuer or completion assertion.
- Engine `prepare_connection` and guarded pre-snapshot capture retain the same
  physical caller into one-shot BEGIN RR. The anchor is now RR-visible. New RC
  control rows committed afterward are never treated as RR-visible authority.
- Data acquires the original metadata/source cuts before its distinct RR
  lock-only authority cut. This preserves source/head-before-policy ordering.
  It does not evaluate permission from snapshot-old role rows.
- `issue_current_preparation_permit(anchor_nonce, original_data_xid8)` runs on
  the original RC coordinator. It derives the actual live peer and complete
  original source/owner/action/field scope under held exclusions, verifies the
  human/action-role provider when required, and refuses stale source, foreign
  caller/cut, unsupported view, advanced meaning or unbounded inputs. It must
  enforce one complete permit per original coordinator transaction.
- `verify_preparation_permit(anchor_nonce, original_coordinator_identity)` runs
  inside the source-owned RR SECURITY DEFINER selection and finalizer. It
  independently checks the RR-visible original immutable anchor, current native
  caller/PID/incarnation/full xid8, exact selected source/program/profile,
  original live coordinator and all its native permit addresses. It never
  accepts Python/JSON/GUC markers, an old grant row or a newly inserted lease row
  as authority. Direct enrolled callers without that native permit refuse.
- An explicit assignment requires its original object/Field action and original
  read or declared/granted blind-write authority **before inspecting whether the
  stored value equals the assigned value**. The same check applies to a no-op.
  Otherwise acknowledgement for equality and refusal for inequality creates a
  hidden-value guessing oracle. Retain the original assignment-derived
  `writeRequirements` and `readRequirements` unconditionally; do not replace
  assignment intent with the logical delta evaluator's changed-fields result.
  Stable RR data and SHARE locks do not establish fresh permission: the original
  RC coordinator and native caller/source/claim checks remain required.
- Bounded selection executes only the enrolled original Weft program and typed
  parameters. Every original preflight runs over the full authorized population
  in the same RR cut; nonzero violations and maxItems+1 overflow refuse without
  trimming. Original identity/version/key codecs, integer ordering and source
  correspondence remain mandatory. No caller SQL or Truss renderer fallback.
- Finalization rechecks current authority and original caller/source/cut before
  writing protected seal bytes and dispatching original data COMMIT. Data-owned
  native authority exclusions survive coordinator loss until the original data
  transaction ends. Broker-only locks do not close this COMMIT loss window.
  Original commit acknowledgement/unknown disposition remains Truss-owned.

## Native permit candidate and required proof

The pinned pgserver PostgreSQL18.6 runtime has no available pgcrypto extension.
Custom cryptography is not introduced. The candidate uses the immutable
pre-RR anchor plus native transaction advisory permit locks. Its component
addresses must bind anchor identity, original data PID and both 32-bit pieces
of the full native xid8 under distinct fixed tags. A single coherent original
issuer/transaction must own all pieces; unions of separate permits are invalid.
Anchor-native person/backend/database identity and exact original source bind
the remainder of the context. IDs must refuse overflow/reset/reuse.

Two-integer advisory mint entrypoints are callable through PUBLIC by default.
Their effective execution must be denied to the ordinary caller and private
coordinator; only the original NOLOGIN issuer owner may invoke the selected
transaction mint routine. Exact alternate mint/helper routes, PUBLIC/inherited
rights, source/ABI/owner/DDL closure and release semantics require native tests.
This is a **dedicated database candidate**, not a shared-database support claim.
Original bigint group-lock behavior cannot silently change. PostgreSQL's
[18.6 implementation](https://github.com/postgres/postgres/blob/REL_18_6/src/backend/utils/adt/lockfuncs.c)
uses separate representations for bigint and two-integer advisory keys; source
inspection does not replace an original native namespace/privilege witness.

The [nine conditional proof queries](../../04-build/evidence/security-preparation-permit-formal-20261014/receipt.json)
prove full-xid partition injectivity and encoded current-authority/one-permit
laws, with SAT stale-permission, xid32-only, broker-only fence and fragment-union
controls. They assume authentic issuance, complete scope, liveness and writer
participation; there is no native SQL/issuer/selection refinement theorem.

## Implemented components and open gates

[Native evidence](../../04-build/evidence/security-preparation-authority-20261014/receipt.json)
implements current native owner/person observation, original peer/cut checks,
separate RC and RR lock-only issuers, and actual coordinator-disconnect/data
completion exclusion controls. These comparisons remain `security_ready=false`.

The original generic products metadata source-epoch issuer now has retained
native evidence. Still required: complete source/DDL barriers beyond that
metadata-only profile; protected anchor/permit homes and immutable native enrollment;
advisory privilege/namespace/one-permit closure; shared human/action-role binding;
same-store original current Weft selection enrollment; native direct-call,
cross-session/replay/expiry/connection-loss and seal-COMMIT race tests. Missing
dependencies refuse. No US-046 or shared-security backend case is promoted.

## Owner-private tuple binding primitive

`_security_bootstrap/preparation-permit-mint.sql` now provides a **private
primitive**, not a guarded issuer. Its candidate ABI is
`mint_preparation_permit_binding(int4 anchor, int4 data_pid, xid8 data_xid) → void`.
PUBLIC execution is revoked; no ordinary/coordinator role may receive execution.
Only a separately qualified original native authority guard may call it after
the complete original anchor/source/Subject/action-role admission. No production
installer or protected entrypoint consumes this primitive yet.

Within the original RC/read-write coordinator transaction it mints one native
backend-specific exclusive slot and four shared component addresses (anchor,
data PID, low/high full xid8 pieces). Shared component modes allow different
coordinators to share equal individual values; verification must require all
addresses under **one original backend**, never a union. A second live tuple in
the same coordinator transaction refuses; native completion releases the locks.
This is not an at-most-once historical anchor-use guarantee across transactions
or subtransaction rollback, and grants no input/peer/current-authority admission.

[Native evidence](../../04-build/evidence/security-preparation-permit-binding-20261014/receipt.json)
retains the actual maximum-xid failure of NUMERIC division followed by truncation
and its repair using the exact integral quotient. The earlier bit-vector theorem
did not establish PostgreSQL division semantics. Ten native boundary vectors,
concurrent coherent backends, duplicate-tuple refusal and completion release now
pass; there is still no all-input SQL refinement theorem or permit activation.

`preparation-permit-binding-check.sql` now provides the owner-private candidate
`check_preparation_permit_binding(int4 anchor, int4 coordinator_pid) → bool`.
It derives the actual data PID/full xid8 inside the original RR backend and
requires all five addresses under one live native coordinator PID/database.
PUBLIC execution is revoked. The native test uses a diagnostic wrapper solely
to observe the predicate; no protected data or production guard is exposed.

[Checker evidence](../../04-build/evidence/security-preparation-permit-check-20261014/receipt.json)
covers true original binding, foreign data and anchor/coordinator mismatch,
original COMMIT and actual coordinator disconnect while the data snapshot stays
fixed. A retained weakened control deliberately re-mints the same tuple in a new
coordinator transaction: the bare predicate becomes true again. Therefore it
does **not** establish original anchor/attempt/coordinator incarnation, historical
single issuance, current authority or scope. Only the original guarded issuer
and protected consumer may compose those obligations; a true predicate or copied
Python comparison cannot authorize selection or seal.

The [integer codec proof](../../04-build/evidence/security-preparation-integer-xid-formal-20261014/receipt.json)
adds four UNSAT safety checks and one SAT discarded-high-marker control over all
nonzero unsigned 64-bit inputs: exact quotient/modulo reconstruction, signed
int32 bounds, unsigned OID round-trip and complete marker injectivity. These
formulas model integer division, not rounded PostgreSQL NUMERIC `/`. Native
`div`/`mod` and lock representation remain implementation premises, with separate
finite native witnesses. No complete SQL refinement or guarded authority theorem
is inferred from these results.

## Original coordinator transaction and shared store composition

The retained later-transaction remint counterexample requires the anchor to bind
more than the coordinator PID. The next candidate uses three original physical
connections in this order; this sequence is a design obligation, not implemented
anchor admission:

1. The engine opens the original SCRAM data connection D and keeps it idle before
   RR. Coordinator A begins RC and assigns its native full transaction ID before
   D starts RR. A stays in that original transaction through guarded issuance.
2. Control C observes both original native backend incarnations. Under the
   original shared store/source cut it verifies the committed context from
   `_action_store.py`, rather than accepting diagnostic store bytes. It records
   A's full transaction ID, PID, backend start and transaction start, D's actual
   database/login/backend incarnation, exact issued store/tenant/guard identities,
   original program/action/profile and bounded native anchor identity. C confirms
   actual COMMIT before D begins RR. No pending registration is committed context.
3. D begins its single RR transaction, reads that immutable original anchor and
   acquires store/source, Subject/role mappings, then policy/native role cuts.
   The current store context verifier is RC-only; D needs a separate original-row
   correspondence check and must not invoke the RC verifier under RR or infer
   current source from `binding_correspondence='matches'`.
4. A's private native guard compares its own actual `pg_current_xact_id()` with
   the anchor's original coordinator full xid8 before any private mint. A later
   transaction on the same PID cannot satisfy that equality. Fresh native peer
   reconciliation of D's claimed full xid uses the scoped private native status
   component, plus the original anchor's database/person/backend incarnation.
   Neither the full-xid helper nor advisory tuple alone admits the anchor.
5. Only after complete current original action/Subject/owner/source admission may
   A mint the coherent tuple. D's protected selector and finalizer check the same
   immutable anchor and original coordinator incarnation/transaction, alongside
   actual D full xid and native markers. Data-owned exclusions remain through
   original COMMIT acknowledgement. A loss, reconnected A, re-mint in a later A
   transaction or unavailable complete source refuses fresh use.

The [native full-xid receipt](../../04-build/evidence/security-preparation-peer-xid-20261014/receipt.json)
qualifies only its bounded PG18.6 component. It does not prove this handshake.
Required next native controls include same-PID/new-transaction remint refusal,
coordinator loss before/after mint, reused PID/backend start mismatch, forged
epoch with equal xid32, anchor mutation/direct issuance denial, fenced issued
store, incompatible guard epoch, foreign store/program and missing complete
current authority. Original registration receipts and replay namespaces remain
recognizable after fencing; rotating the guard epoch never creates a fresh
replay scope. Protected anchor storage/issuer, registered selection closure,
finalizer and the complete composed negative controls remain unimplemented.


## Implemented private attempt identity checkpoint

The [native anchor identity receipt](../../04-build/evidence/security-preparation-attempt-anchor-20261014/receipt.json)
now qualifies a private PG18.6 component of the candidate handshake. Original UMF
exports the immutable native storage. A direct trusted control issuer captures
the genuine shared store receipt, original idle data backend/person/incarnation
and active same-person coordinator/backend/full xid, then requires original
control COMMIT before the anchor can be read under a new data RR snapshot.
Owner-private coordinator/data predicates reject a later transaction on the
same coordinator backend even when unchecked fixture code re-mints identical
advisory markers. Native pending/same-snapshot visibility, wrong nonce/foreign
data, mutation denial and actual disconnect controls pass.

The anchor retains opaque program bytes without interpreting them as an
admitted program, policy or permission. No production installer or ordinary
anchor/mint/check grants exist. Diagnostic test wrappers expose predicates and
unchecked marker minting solely to retain the weakened counterexample. The
pre-RR anchor binds the data backend; its identity predicate alone is not a
historical one-use guarantee for a data transaction. Complete guarded issuance
must bind the actual D full xid, enforce lifecycle/scope and current permission,
and consume original registered selection before protected work.

The six new conditional identity queries (3 UNSAT, 3 SAT) include bare-tuple
replacement and identity-without-permission witnesses; they are not SQL
refinement or authorization proofs. Astra Ultra independently reproduced the
storage build and formal queries and inspected the source-pinned native log,
with no finding in this narrow scope. Source/helper/DDL custody, actual PID
reuse/wrap, historical one-use/savepoint behavior, current authority, protected
selection/finalization and COMMIT-loss closure remain open. No complete
CONTRACT-005 or owner-worktree bulk acceptance criterion is promoted.

## Excluded selection diagnostic — 2026-10-15

`packages/python/src/truss/_preparation_selection.py` executes the original
immutable enrolled program only through a direct administrative PG18.6
RR/read-only connection. It invokes the pinned native Weft replay itself,
checks the snapshot's installation/catalog/document pins, and submits the
original `$n` SQL through psycopg's raw cursors with stock UTF-8 TEXT adapters.
Every original population preflight precedes selection, including when a
predicate would select nothing. A nonzero count refuses. The server cursor
retrieves rows incrementally, refuses maxItems+1 without trimming and checks
raw UTF-8 bytes plus the JSON diagnostic row representation against the original
bounds. These are diagnostic row bounds, not a claim that a future prepared
manifest including its metadata fits those bounds. No prepared manifest is
created. The original lowering bytes retain parameter and column mappings.
The cursor closes and the original transaction context is rechecked before
buffered rows return, with `authority=false` and `security_ready=false`.

Basic native evidence: `test_preparation_selection_native.py` executes the
freshly enrolled original compiler program against the two seeded products,
selects `bar`, refuses an ordinary RR/read-only caller, then refuses an invalid
storage cell outside that selection. The basic PG18.6 workflow passed
(1 test, 7.413 seconds); Astra Ultra reviewed the plan and completed component.
This does not qualify WHERE-false/LIMIT-zero variants, overflow, complete
source/DDL/writer closure, current authority, permit minting, protected
selection/finalization or hold-through-COMMIT. No ordinary grants, public
assembly provider, new registry or native helper are introduced. The next
integration remains the source-owned guard composition above; this diagnostic
must never be accepted as its permit or authorization result.

## Private selected-literal permit composition — 2026-10-15

The source-owned component
`packages/python/src/truss/_security_bootstrap/preparation-literal-permit.sql`
composes the existing original anchor, a8f73415 independently committed claim,
03a241d0 Subject correspondence and literal current checks with the existing
private native advisory binding. All four new routines remain excluded-owner
private, with PUBLIC execution revoked; there is no production installer or
ordinary SDK grant:

- `acquire_preparation_literal_permit_cut(int4,uuid) → void` runs on original D.
  It acquires original source/head/mapping cuts before lock-only SHARE on
  module access and the two native role catalogs. It evaluates no current
  permission from D's old RR snapshot.
- `require_preparation_literal_data_cut(int4) → void` verifies the actual held
  relation modes over the selected source, bridge, mapping and authority homes.
  Shared role catalogs use native shared-database lock identity. It never
  acquires or repairs a missing cut.
- `issue_preparation_literal_permit(int4,uuid) → void` runs inside original C.
  It derives the committed original claim, requires D's held cuts, invokes the
  actual original literal checks and private mint, then rechecks original
  coordinator/claim/source/cut correspondence. No supplied success flag, actor,
  SQL or transport token can mint a permit.
- `require_preparation_literal_permit(int4,uuid) → void` runs inside original D.
  It verifies held cuts **before** existing identity helpers that could otherwise
  reacquire them. It verifies the original immutable anchor/program/source and
  actual D full xid8 against original C's physical binding. It never reads E's
  later claim through D's older snapshot. Original C must be idle in its
  original transaction/incarnation before and after verification.

Successful C statement completion and leaving that original connection idle
until D settles are trusted engine sequencing requirements. After issuance,
the engine must retain D's original cuts continuously; any rollback that could
release them invalidates the whole attempt. Reacquiring the same lock modes
cannot prove uninterrupted custody and cannot resume an admitted operation.
The native lock census establishes present ownership, not lock history. Mint locks become
visible before the C issuer's final checks finish; an active C is therefore
insufficient. The native physical binding itself is not an authenticated
issuance receipt. The source-owned protected selector and finalizer must call
this check internally before any protected effect; neither is implemented by
these routines. No ordinary caller receives this checker as a permission API.

`test_preparation_literal_permit_native.py` exercises the original SCRAM D/C/E
workflow with actual original producers. It covers successful mint/check,
missing permit or D exclusions, duplicate mint, active C, same-PID later C
transaction, rollback-lost policy/source cuts without implicit repair, removal
of C's permit addresses, a blocked real membership revocation after C releases
its permit and authority locks, and refusal of
direct ordinary invocation. The selected original snapshot/full xid8 survives
the rollback controls. Both focused PG18.6 workflows passed (2 tests,
20.538 seconds); see [the compact component receipt](../../04-build/evidence/preparation-literal-permit-20261015.json).
These are component workflows, not full guard qualification.

Full original helper/DDL/shared-writer/legacy-serving/effect closure, exclusion
of ordinary raw advisory mint routes, guarded operation deadlines, protected
selection/finalization and dispatch/COMMIT acknowledgement remain required.
Data-owned policy locks improve lifetime custody but do not discharge those
other duties. This component does not activate the protected public profile or
change the false authority/security-ready claims of earlier diagnostics.
