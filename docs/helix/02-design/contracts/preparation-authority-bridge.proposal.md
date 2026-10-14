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

Still required: original generic products source-epoch issuance and source/DDL
barriers; protected anchor/permit homes and immutable native enrollment;
advisory privilege/namespace/one-permit closure; shared human/action-role binding;
same-store original current Weft selection enrollment; native direct-call,
cross-session/replay/expiry/connection-loss and seal-COMMIT race tests. Missing
dependencies refuse. No US-046 or shared-security backend case is promoted.
