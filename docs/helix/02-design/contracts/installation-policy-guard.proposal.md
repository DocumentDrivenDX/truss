# Installation-wide current-authority guard

Candidate realization of CONTRACT-005's current-authority exclusion, not an installed or adopted profile. Select one guard for the complete installation rather than inferring per-module guards from catalog labels. This permits conservative serialization of all participating grant/role/policy changes while preserving the full qualified owner union for authorization. More granular guards require a separately complete authority-dependency mapping.

## Fixed home and identity

Allocate `truss.policy_generation_guard` with `singleton smallint PRIMARY KEY CHECK(singleton=1)`, exact installation identity bytes, policy-profile bytes and `generation bigint NOT NULL CHECK(generation>0)`. Identity/profile carriers are nonempty bytea and immutable for the installed profile. Initialization inserts exactly one row with generation 1 in the same verified bootstrap transaction as installation initialization. Missing, duplicate, incompatible or replaced guard refuses admission; no operation repairs it on demand.

The installer must inventory the table/columns/checks/PK and original identity/profile bytes, plus protected acquisition/update routines and effective privileges. Ordinary roles cannot modify/delete the row or reinitialize generation. The ready marker cannot publish until this home and controlled authority paths are included in complete native parity. This table is not yet in layout 0.9.

## Protected mutation protocol

Participating grant/helper, role membership, policy, helper ownership/security and relevant native privilege changes acquire required catalog locks first, then the installation guard exclusively, before business/owner locks. The profile must inventory every controlled/excluded administrative path. Unmediated superuser/owner actions invalidate qualification; a guard cannot physically constrain arbitrary external administration.

Capture complete original authority inputs, validate the intended delta, perform effects and independently compare resulting effective authority under the same exclusion. For an actual authority change, checked-increment generation exactly once before publication in the same transaction. At signed bigint exhaustion refuse and require explicit installation/profile transition; never wrap, reset or silently relabel continuity. No-op input alone is insufficient: native effective delta determines whether authority changed. Rollback restores effects and generation together. Original commit uncertainty remains executor recovery, not another update attempt.

## Guarded read/write admission

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
