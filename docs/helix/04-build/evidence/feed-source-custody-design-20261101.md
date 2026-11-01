---
ddx:
  id: truss.evidence.feed-source-custody-design-20261101
  type: evidence
  activity: build
  status: draft
  authoring:
    home: repo
---

# Truss feed source custody: implementation boundary and qualification plan — 2026-11-01

## Decision

Do not add a source-holder API to the v0.0.51 lineage yet. The smallest safe increment is a source-owner design with a hard boundary: Truss can bind and renew its own feed registration, epoch, consumer, cursor and retained page; Ashlar's source holder must independently renew destination registration and protected ACK scope. Current Truss has no authority over that external registration. A Python handle or an advisory lock without complete native path coverage would only look like custody.

This packet records a proposed API and implementation/qualification sequence. It changes no contract status and authorizes no ACK or native run. The governing Ashlar artifacts are CONTRACT-001 (especially proposed source-holder ports and A1), CONTRACT-002 (read boundary), CONTRACT-003 (complete publication vector and exact source envelope), CONTRACT-004 (original source and ACK authority), and TD-009. Ashlar's `source-holder-truss051-capability-20261029.md` and `source-holder-a1-live-port-gap-20261024.md` preserve the selected package observations and earlier candidate failures.

## v0.0.51 source surface observed

The source snapshot is tag `v0.0.51`, commit `26c1b9171718ad0f6291b82f65c8cef0406886fb`, in `/private/tmp/truss-holder-051-codex`. The inspected methods in `packages/python/src/truss/catalog_runtime.py` are:

- `read_feed_in_transaction(transaction, consumer_id, ...)` returns the next complete committed transaction or safe empty interval.
- `reread_feed_in_transaction(transaction, page, ...)` reproduces the retained page and checks original bytes, registration, cursors and digest.
- `acknowledge_feed_with_receipt_in_transaction(transaction, page, destination_id, request_sha256, publication_id, receipt_bytes)` submits the exact receipt.
- `reconcile_feed_ack_in_transaction(...)` checks the retained receipt outcome.

`FeedPage` and `FeedAckReceipt` retain exact cursor/page and receipt bytes. SQL in `_catalog_runtime/feed.sql` and `feed-receipts.sql` checks current authority and page correspondence; ACK locks the consumer row and advances its checkpoint atomically with receipt retention, while reconciliation is a separate read-only operation. The registration method is installation-administrator-only. There is no exported source custody open/renew/close handle or destination registration registry.

`read_feed` and `reread_feed` are operation-scoped checks. `reread_feed` can reproduce an old retained page after the checkpoint advanced, and neither call holds the consumer registration/checkpoint against another ACK for the time between calls. ACK compare-and-set and exact receipt reconciliation remain useful primitives but do not make a live source interval.

## Narrow API proposal

Keep the upstream handle about Truss-owned state only. Do not add a Truss-owned destination registry. Ashlar's source-holder orchestrator composes this handle with its independently authorized destination-registration/ACK-scope owner and with managed-read/native-pin handles.

Proposed public immutable selection and handle (field names remain provisional):

```python
@dataclass(frozen=True)
class FeedSourceSelection:
    installation_id: str
    source_epoch: str
    release_id: str
    release_sha256: str
    consumer_id: str
    registration_id: str
    checkpoint: FeedCursor
    page: FeedPage
    maximum_facts: int
    maximum_bytes: int

@dataclass(frozen=True)
class FeedSourceCustodyHandle:
    custody_id: str
    selection_sha256: str
```

The public handle is only a backend-bound lookup key. It contains no lock token, session credential, or authority that can be replayed on another connection. The private native custody row retains the full binding and internal random token. Proposed capability surface (names provisional):

```python
capability.open_feed_source_custody_in_transaction(
    transaction, *, selection: FeedSourceSelection,
    request_bytes: bytes, destination_registration_bytes: bytes,
    ack_scope_bytes: bytes,
) -> Outcome[FeedSourceCustodyHandle | FeedUnavailable]

capability.renew_feed_source_custody_in_transaction(
    transaction, *, handle: FeedSourceCustodyHandle, phase: CustodyPhase
) -> Outcome[FeedSourceObservation | FeedUnavailable]

capability.acknowledge_feed_receipt_under_custody_in_transaction(
    transaction, *, handle: FeedSourceCustodyHandle,
    destination_id: str, request_sha256: str, publication_id: str,
    receipt_bytes: bytes
) -> Outcome[FeedReceiptAcknowledged | FeedUnavailable]

capability.reconcile_feed_ack_under_custody_in_transaction(
    transaction, *, handle: FeedSourceCustodyHandle,
    destination_id: str, request_sha256: str, publication_id: str,
    receipt_bytes: bytes
) -> Outcome[FeedAckReconciled | FeedUnavailable]

capability.close_feed_source_custody_in_transaction(
    transaction, *, handle: FeedSourceCustodyHandle, phase: CustodyPhase
) -> Outcome[FeedSourceClosed | FeedUnavailable]
```

The opened handle is bound to one live backend session and one exact selection. Calls fail closed if the transaction belongs to another backend, the original connection was lost, or any retained field differs. The handle's opaque local value is a routing aid, never authority. Native routines must validate backend/session binding, private registration and required locks on every call.

`renew` independently checks current installation/release identity, source epoch, current feed consumer ID/registration, current authorization, exact current page and exact retained page. The checkpoint is phase-sensitive:

| Phase | Admitted checkpoint |
| --- | --- |
| `before_ack` | Exact page prior cursor |
| `ack_unresolved` | Exact prior or exact next cursor only |
| `ack_reconciled` | Exact next cursor |
| `no_publication_close` | Exact prior cursor |
| `committed_close` | Exact next cursor |

Any other cursor, registration, epoch, installation, release, current/retained page or authority result refuses. An uncertain ACK is reconciled from a fresh read-only transaction; it is never blindly resubmitted. Close performs its own phase-specific reread before releasing custody. If the caller connection is gone, close cannot claim success; the handle remains incomplete and the caller must preserve original recovery custody.

The source holder retains the exact `request_bytes`, `destination_registration_bytes`, and `ack_scope_bytes` supplied at open and rebinds them on each renewal and ACK/reconcile call. Truss validates unchanged byte correspondence and request digest; the bytes remain opaque to Truss and do not establish external authority. The Ashlar holder must ask its independently registered destination authority to renew the exact registration and ACK scope and compare its original bytes/identity on every renewal. A string argument such as `destination_id`, a caller Boolean, verifier report, or digest alone does not admit this authority. A mismatch refuses even if the source bytes are unchanged.

## Exact source mutation and migration inventory

The repository-wide search was narrowed to `runtime_feed_consumer`, `runtime_feed_ack_receipt`, and feed registration/ACK entry points. The current mutation surface is finite and directly locatable:

| State or path | Current writer/read path | Existing guard and gap |
| --- | --- | --- |
| Feed consumer table | `_catalog_runtime/feed.sql:111-115` creates `runtime_feed_consumer`; no lock or mutation trigger is attached. | Public relation privileges are revoked by the installation profile, but there is no trigger-level defense for owner/administrator DML or TRUNCATE. |
| Consumer enrollment | `catalog_runtime.py:1526-1554`, `register_feed_consumer_in_transaction`, installation-administrator-only. It takes the consumer row `FOR UPDATE NOWAIT`; for a new row it INSERTs, creates the genesis cursor, then UPDATEs checkpoint bytes. | This is the only Python consumer-row enrollment path found. It takes no source custody lock before the row lock. |
| Legacy ACK | `_catalog_runtime/feed.sql:287-312`, `acknowledge_feed`. It checks source authorization, locks the consumer row `FOR UPDATE NOWAIT`, validates the exact delivered interval, and UPDATEs checkpoint/last-ACK fields. | No custody lock. Existing CAS and transaction atomicity do not protect the gap between read and ACK. |
| Receipt ACK | `_catalog_runtime/feed-receipts.sql:41-72`, `acknowledge_feed_with_receipt`. It validates receipt binding, locks the consumer row `FOR UPDATE NOWAIT`, checks retained receipt or calls legacy ACK, then inserts exact receipt bytes. | No custody lock before its first row lock. Receipt rows have UPDATE/DELETE immutability but no TRUNCATE guard. |
| Receipt reconciliation | `_catalog_runtime/feed-receipts.sql:74-97`, `reconcile_feed_ack`. It requires an unassigned read-only transaction, reads current consumer and retained receipt, and returns exact checkpoint/binding/receipt correspondence. | Read-only and operation-scoped; it does not lock or reserve the consumer row. It must be paired with the live same-backend fence and phase checks. |
| Current/retained page | `_catalog_runtime/feed.sql:268-285` `read_feed`; `315-340` `reread_feed`. | They recheck authority and page context within each call. `read_feed` checks checkpoint unchanged during that call. `reread_feed` can reproduce the original retained page after ACK and does not prove the current checkpoint. Neither fences between calls. |
| Runtime migration | `_migration_execute.py:27-34` takes transaction-exclusive advisory lock `(1953658227,1735549296)` and then `ACCESS EXCLUSIVE NOWAIT` on every Truss table before recipe steps. | This protects current migration execution from concurrent table users, but it has no source-handle session-lock counterpart. Do not reuse this key for a long-lived source handle: normal graph/catalog writers and installation coordination also use it. |
| Runtime installation | `catalog_runtime.py:525-527` uses `(1953658227,1735549296)` to serialize installation. It only publishes a fresh install; an existing matching installation returns `already_installed`. | No active consumer handle can exist for an absent schema. It remains installation coordination and should not be coupled to a long-lived feed lock. |
| Fresh namespace construction | `_catalog_installation.py:187-195` takes `(1953658227,1)` after BEGIN and refuses unless the Truss namespace is absent. | It is a one-time fresh install path, not an in-place consumer migration. It cannot affect an existing handle without out-of-band namespace DDL. |
| Normal graph/catalog writers | `operations.sql`, `definition-source.sql`, `keys.sql` use `(1953658227,1735549296)` in transaction scope. | These can append future feed facts but do not rewrite the selected committed page or consumer checkpoint. Holding this key during custody would block unrelated Truss writes and is not proposed. |
| Direct administrative recovery | `lifecycle.sql:46-74`, `admin_install_recovery`, only reports owner/registrar role identity. | It does not alter feed state. |

The installation profile revokes direct relation rights from public roles and the private preparation exclusion revokes ordinary callers' direct advisory-lock acquisition functions (`_security_bootstrap/preparation-advisory-exclusion.sql`). A source API cannot simply issue raw `pg_advisory_lock` from an ordinary Python cursor. Lock acquisition/release must run in owner-controlled SECURITY DEFINER routines with exact ACLs. Public `pg_advisory_unlock`, `_shared`, or `_all` access must also be reviewed/revoked for the source principal; otherwise it could release a session fence.

No second Python writer for `runtime_feed_consumer` was found. Two SQL routines advance its checkpoint; the owner enrollment path creates the initial registration/cursor. Migration is recipe-driven and obtains one global advisory gate plus all-table exclusive locks. Owner/superuser DDL outside the supported installer/migration path remains an explicit trusted-administrator boundary; no database lock can defend against a superuser that deliberately destroys the installed guard.

## Minimal versioned SQL lock protocol and API diff

This is the proposed smallest complete protocol for supported Truss paths. It does not hold the existing global writer/install key for the handle lifetime.

1. **Add a new lock namespace in a new runtime release.** Define a dedicated feed-custody transition key distinct from `(1953658227,1735549296)` and `(1953658227,1)`. A custody handle holds a session-level shared lock on it and a session-level exclusive per-consumer key derived from a domain-separated digest of the exact UTF-8 consumer ID. Hash collision may cause harmless contention/refusal, never alias authorization. Migration takes a transaction-level exclusive transition lock before its existing global lock/table locks. This blocks supported migrations while a handle lives without blocking normal graph writes.
2. **Handle same-backend mutation explicitly.** Session locks do not fence the backend that owns them. Add a private native active-custody row binding random handle/token, backend PID plus backend start identity, installation/epoch/release, consumer/registration, original checkpoint/page and limits. Consumer enrollment, legacy ACK, and direct consumer-table DML must refuse while an active custody row exists. The only permitted state change under that row is the holder's handle-bound receipt ACK. Its SECURITY DEFINER wrapper checks the exact handle token/scope, sets a transaction-local internal token, calls the private ACK core, and clears the token on every exit. A BEFORE INSERT/UPDATE/DELETE trigger on `runtime_feed_consumer` refuses any DML while custody is active unless the internal token matches the private row; without active custody it uses a nonblocking per-consumer transaction advisory lock. Never return the internal token through a routine or diagnostic.
3. **Fence competing sessions before row locks.** The holder owns a session-level exclusive per-consumer lock. Every ACK wrapper and enrollment path acquires the corresponding transaction-level per-consumer key before `SELECT ... FOR UPDATE`; it returns typed `55P03` if another backend owns the handle. This gives bounded refusal instead of waiting behind a row lock. Receipt ACK calls the private ACK core without trying to bypass the active-custody check. Legacy ACK refuses if a custody row is active, even when called by the handle-owning backend.
4. **Protect receipt integrity and replacement paths.** Add a BEFORE TRUNCATE statement guard to `runtime_feed_consumer` and `runtime_feed_ack_receipt`; it refuses while any active custody exists. Add the exclusive transition lock to `_migration_execute.exclude` before migration steps. Current fresh installation only operates on an absent namespace; active-release migrations use the recipe gate. Revoke public direct session advisory unlock/unlock-all access for the selected source principal; only SECURITY DEFINER owner routines may acquire/release custody locks. Owner/superuser bypass DDL remains an explicit trusted-administrator exclusion.
5. **Extend the Python protocol after those SQL routines exist.** Add immutable `FeedSourceSelection` and `FeedSourceCustodyHandle`; add `open/renew/close_feed_source_custody_in_transaction` to `NativeFeedCapability`, `NativeCatalogCapability` delegation and `CatalogRuntime`. Every call requires an active `TransactionHandle` on the opened native connection identity, PID and backend start. Open locks first, then reads and rereads the selected page at its retained fact/byte bounds. Renew retains original selected bytes and applies the phase table above. Close repeats phase checks before releasing native locks. Add handle-bound receipt ACK/reconcile methods that pass the handle internally and cannot switch backends; the existing unbound methods stay available for their current operation-scoped callers but are forbidden to the source-holder path.

The selected page identity is the complete immutable `FeedPage`; selection also retains its fact/byte bounds because current defaults are operation parameters, not page fields. Open refuses `empty_interval` for receipt ACK custody. At `before_ack`, current `read_feed.prior` must equal the original prior cursor and the full current page must match. At `ack_unresolved`, exact receipt reconciliation admits only `(missing, prior)` or `(matched, next)`; conflict, any other checkpoint, or changed registration refuses. Reconciled/committed close requires next; no-publication close requires prior. Every phase rereads the original retained page. Ashlar independently renews destination registration/ACK scope; Truss compares only exact separately admitted binding bytes and never asserts external authority itself.

No code-only read check provides this guarantee. After implementation, native tests must prove session locks survive caller transaction commit, reject cross-backend reuse, refuse enrollment/legacy ACK/direct DML on the same backend while a handle is open, admit only the exact handle-bound receipt ACK, reject ordinary direct DML and TRUNCATE from another backend, block migration, and release on close/backend death. The source profile's advisory unlock ACLs, routine-owner closure, lock ordering, migration artifact and install manifest need independent native inspection.

## Implementation and native qualification sequence

1. **Freeze authority and lifecycle.** Review this API against the exact current Ashlar CONTRACT-001/002/003/004 and TD-009. Name which external owner admits destination registration/ACK scope; specify max interval, renewal cadence, cancellation behavior, and exact unknown-commit recovery. Do not expose an API until the external authority interface is fixed.
2. **Inventory all writers.** The read-only source inventory in this packet found one installation-administrator enrollment path, two SQL ACK paths, and no other Python consumer-table writer. It also located receipt reconciliation, the table ACL/trigger gaps, the recipe migration gate, fresh-install paths and existing unrelated writer locks. The source inventory is complete for the v0.0.51 repository snapshot; Sol must still verify the installed routine/ACL closure natively.
3. **Implement schema and routines privately.** In a new release candidate, add versioned SQL for the custody binding, protected lock/handle routines, DML/TRUNCATE guards, migration transition lock and handle-bound receipt ACK/reconciliation; update all corresponding release manifests/migration artifacts and Python capability types. Do not grant direct consumer writes. Open must acquire locks atomically, observe exact selection, and bind the original request plus opaque destination evidence. Close and stale-backend handling must fail closed. This is not a Python-only change.
4. **Add focused source tests.** Fake-level checks cover type/byte integrity, phase cursor rules, changed installation/epoch/registration/page/destination scope, duplicate close, lost connection, cancellation, primary-error preservation and no ACK retry. These tests are necessary but do not prove native enforcement.
5. **Run controlled local native qualification only after the owner authorizes it.** Use the exact supported Truss runtime and its dedicated owned pgserver worker from the current installation/migration plan; never the shared default cluster. In a fresh database/roles, prove: open captures original registration/cursor; a competing ACK and re-registration refuse while held; feed page remains exact; handle's same-backend ACK commits once; another ACK cannot overtake; fresh transaction reconciliation returns exact receipt; pre/post-close phase rules work; outer commit response loss is reconciled without resubmission; rollback, backend termination and process restart release session locks but leave stale handle rows non-authoritative; migration waits/refuses under bounded policy; ordinary roles cannot forge rows, invoke private routines, disable triggers or bypass lock paths; cleanup restores inventory and stops the worker.
6. **Independent review and publication.** Review source/SQL, lock ordering, installation membership, migration route and ACL closure independently. Compare source, wheel, installed module and generated native manifest hashes. Keep the evidence at component scope until complete profile review and ordinary source/ACK authority are admitted. No source mutation or ACK is needed to test refusal/fencing cases; a successful ACK case requires a separately authorized native test fixture and must not run as part of this current task.

## Current blockers

- The selected public API has no source lifetime, held session owner or close operation.
- Existing reads do not fence checkpoint changes between calls; exact ACK CAS alone cannot prove the entire pre-ACK interval.
- The located paths do not yet participate in a source custody fence; in particular same-backend mutations must be rejected except for the exact handle-bound receipt ACK, and the full installed ACL/routine closure remains to be independently inventoried.
- External destination registration and ACK-scope authority is absent from Truss. The upstream handle can carry those bytes only as opaque correspondence unless a separate Ashlar owner admits them.
- Prior candidate evidence reports unresolved outer commit/rollback and lost-commit behavior, owner/ACL alignment, migration installation route and no-effect close. Its native attempt did not complete checkpoint admission, holder ACK or fresh reconciliation. The candidate is not inherited as qualification.
- The native-lock path is not a tractable isolated Python increment. It changes versioned SQL, triggers, routine ACLs, installation/migration manifests, and both current ACK variants; source-level tests cannot establish same-backend token enforcement or session-lock behavior. It needs a distinct implementation iteration with native qualification and independent Sol review before exposure.

Until these blockers close, Truss 0.0.51 remains read/reread plus exact-receipt ACK/reconciliation at operation scope. Ashlar's source-holder gate remains closed. This design does not enable a campaign, create external authority, or claim retained-file/native-pin custody.

## Work performed for this packet

Read-only review of Truss v0.0.51 source and its AGENTS.md, plus the cited Ashlar contracts, TD-009 and the two source-holder evidence records. The old `/private/tmp/truss-holder-v050` directory was inspected read-only; it contains no checked-out Python/SQL source. No native database was started, no tests were run, no source or ACK call was made, and no push occurred.

## v0.0.51 candidate implementation disposition

The branch `codex/feed-source-custody-052` is a source-only design candidate. No runtime or SQL source was changed. The full fence is not an independently verifiable patch against the current release artifacts: `truss._migration_recipe.load_recipe()` verifies the exact active `_catalog_runtime/manifest.json`, every file named by it, the target configuration, every edge artifact, and exact ACL evidence for every endpoint. `_migration_execute.execute()` only runs the declared forward recipe and verifies source/target inventories, ACLs, preservation, ownership and target activation. A modified feed routine that is absent from a new target manifest cannot be installed into an existing 0.0.51 schema; adding a Python façade would falsely advertise enforcement.

The minimum next code change is one versioned, fully packaged runtime/migration cohort, with the following indivisible diff:

- `_catalog_runtime/feed.sql`: add private custody state, consumer DML guard and statement-level TRUNCATE guard; make legacy ACK and consumer enrollment take the per-consumer transaction fence and refuse active custody; preserve existing operation-scoped API behavior outside custody.
- `_catalog_runtime/feed-receipts.sql`: add protected open/renew/close plus handle-bound ACK/reconcile routines; only the bound ACK routine may authorize the exact checkpoint mutation while custody is active. Keep destination registration and ACK-scope authority external to Truss.
- `_migration_execute.py`: take a new versioned transaction-exclusive feed-custody transition lock before any DDL; keep the current unrelated install/global gate and deterministic table-lock order.
- `catalog_runtime.py`, `feed.py`, capability contracts/delegates: add closed immutable selection/handle/phase types and open/renew/close/ACK/reconcile methods; enforce same live connection and fail-closed state/error semantics.
- `_catalog_runtime/manifest.json`: hash the new SQL/profile files and publish the exact new runtime identity. `_installation/statements.json` and its manifest need changes only if installer bootstrap/ACL closure is required for the new routines; that decision must be made from the actual target role profile.
- `_migrations/manifest.json`, target runtime profile/inventory, exact ACL profile, forward edge recipe and edge hash: declare the new endpoint and complete upgrade route from every currently admitted source. Preserve all prior endpoint and edge artifacts as immutable. Update receipt-model/deployment evidence only if the new schema changes those modeled relations.
- Focused source tests: typed selection closure and immutability; phase/checkpoint table; preserved exact request/destination/ACK-scope bytes; wrong backend, changed registration/page/epoch, duplicate close, and no-ACK-retry behavior. Native tests, which are mandatory for the fence, remain a separate post-review gate.

The code task cannot be called complete until the cohort can be loaded by `load_recipe()` and its target ACL/runtime profiles are internally consistent. It cannot be called production-qualified until Sol independently reviews the candidate and the controlled native qualification in the prior section proves lock persistence, same-backend bypass refusal, competing-session refusal, migration exclusion, truncate/DML guards, exact bound ACK, close and backend-death behavior. No native DB, ACK, cloud resource, push or tag has been used by this candidate.

## Candidate source implementation update — supersedes earlier lock proposal

The earlier session-advisory-lock proposal above was replaced in the working
candidate after inventory and concurrency review. The current candidate uses
the per-consumer row lock as its serialization primitive. Open obtains
`runtime_feed_consumer FOR UPDATE NOWAIT` before checking/inserting private
custody state. Existing consumer enrollment and both ACK writers already use
that row lock; legacy and receipt ACK additionally refuse an active custody row.
An always-enabled consumer DML trigger requires an unreturned transaction-local
token matching the backend PID/start-bound private row. Open/renew/close and
handle-bound ACK/reconcile compare the exact opaque request, destination
registration and ACK-scope bytes. The random internal token is generated from
a separate server-generated UUID, never returned to Python. Private table DML
is revoked from PUBLIC; statement TRUNCATE guards cover consumer and receipt
tables; stale cleanup requires the exact PID and `backend_start` pair to be
absent.

The migration race is closed by acquiring the global administration lock and
then deterministic `ACCESS EXCLUSIVE NOWAIT` locks on all Truss relations
before checking for active custody rows. Checking after table-lock acquisition
is essential: an already committed open is visible and refused, an open still
in progress blocks acquisition, and a later open cannot pass the consumer-row
lock. A source-level test pins this ordering. This candidate does not use
session advisory locks, and so the session unlock/unlock-all ACL analysis in
the earlier proposal is no longer part of the chosen protocol.

Each custody row also records the XID that created it. Renew, ACK, reconcile
and close refuse when called from that same transaction, so open must commit
before any follow-up handle operation; after commit, a later transaction on
the same backend can use the handle. Reconciliation remains a fresh read-only,
unassigned transaction because its check uses
`pg_current_xact_id_if_assigned()` without assigning one.

Sol's source review then identified and closed two additional edges. The
consumer trigger now checks both `OLD.consumer_id` and `NEW.consumer_id` on
UPDATE and rejects any identity rewrite; removal/re-registration still passes
through the old-ID guard and cannot replace an active registration. Migration
now invokes the owner-controlled stale-row pruner only after taking the full
Truss relation locks. It deletes only rows whose exact `(backend_pid,
backend_start)` is absent from `pg_stat_activity`, then refuses if any live
custody remains. This provides an authorized migration recovery path for dead
backend rows without expiring a live handle. The prune routine needs target
ownership/EXECUTE assignment in the not-yet-generated 0.75 migration artifact.

The candidate runtime manifest is now `truss-catalog-runtime/0.75-candidate`
and pins the new source file; `scripts/build-feed-source-custody-runtime-manifest.py`
rebuilds the content hashes. `_verified_release()` successfully validated the
manifest and loaded 51 SQL sources. Five focused contract test functions
passed under Python 3.11 by direct invocation. `git diff --check` passed. The
pytest runner is unavailable in the isolated venv, and no SQL parser/native
database execution has been performed.

This is not yet installable/upgradable: the existing migration artifact
generator only admits the older receipt/routine delta and has no target
inventory, exact ACL profile, ownership/grant statements or forward edge for
this new table/trigger/function cohort. Therefore the runtime API must remain a
candidate and must not be called production. Next steps are Sol's independent
review of the SQL/lock protocol, then extension of the native artifact builder
to capture the 0.75 target and author a complete 0.74-to-0.75 edge, followed by
controlled local native qualification. The external destination/ACK authority
remains Ashlar-owned throughout.
