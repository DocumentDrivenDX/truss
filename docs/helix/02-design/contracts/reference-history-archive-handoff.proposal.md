# Reference durable history archive handoff proposal

The [S3 provider candidate](reference-history-s3-profile.proposal.md) makes version custody, conditional submission and retention/recovery obligations concrete. It remains proposed and unqualified; this provider-neutral procedure remains governing.

This is the provider-neutral reference procedure for CONTRACT-002's selected reconstructable history and short/zero local retention. Reuse the existing retained-history-archive v0.2 candidate and retention tooling request/result; introduce no parallel archive wire or drop-by-certificate API. Exact provider/build/durability/retrieval/resource/security qualification remains required before activation.

1. Through a protected bounded export operation, admit one original complete committed history cut and every required entity/version group, source/definition/owner dependency and retained baseline. Preserve the exact archive bytes and original profile tuple; row pages, live state or a matching digest count cannot supply missing group membership. Reserve the complete original collection/encoding/copy account and retain immutable export custody. Do not hold an open Truss transaction merely to wait for external storage.
2. Outside the database transaction, submit the original immutable artifact to the qualified provider with stable original export identity, exact full-byte digest/length and target namespace/context. Provider retry is for the same original artifact/attempt, never a new history observation. Lost acknowledgment requires observing the original provider write; it cannot authorize local deletion. A same identity with changed bytes conflicts, and same digest with unequal full bytes is not equivalence. Exact provider idempotency and conditional immutability must be qualified rather than inferred from an API method name.
3. Before proposing cleanup, independently verify confirmed provider durability and bounded complete retrieval of those original bytes through the actual future recovery identity/credentials/profile. Validate length, bytes, hash and complete archive/dependency interpretation under original custody. A successful upload callback, eventual listing, provider checksum alone, local cache hit or retry count is insufficient. Unavailable, truncated, stale, wrong namespace or unauthorized retrieval leaves local retention protected.
4. Retain original provider observation and complete coverage evidence privately. Admit a provider lifetime/immutability guarantee covering the advertised reconstruction horizon and protected consumer/receipt obligations; expiring retrieval evidence cannot stand in for continuing recoverability. Exact provider deletion/overwrite/admin paths and failure assumptions belong to its profile. A replica or local temp file without that qualification cannot discharge durable handoff.
5. Start the existing protected retention transaction with original candidate/horizon inventory and procedure profile. Recollect actual current complete protection/owner/group/partition/definition/consumer/receipt dependencies under its qualified cut and lock order. Revalidate that the independently verified archive covers every original dependency that would be lost. Concurrent new protections, changed source epoch/horizon or incomplete coverage refuses cleanup. Earlier export/provider evidence does not waive this fresh admission or grant new authority.
6. Publish the new declared horizon and exact native removal atomically through existing retention tooling, returning its pending result until outer commit is confirmed. Failed/unknown cleanup preserves original outcome/recovery custody; a durable external artifact does not classify database COMMIT. A confirmed rollback leaves the local horizon intact even if an unused archive exists. A later authorized cleanup must re-admit current protections instead of reusing a prior permit. External orphan cleanup has its own protected policy and cannot delete an artifact still supporting any admitted horizon or recovery obligation.

Zero local retention means eligible local history may be removed only after this complete handoff and current protection admission; it does not mean writers can omit history or request receipts. Provider outage stops new cleanup and yields explicit unavailable reconstruction when required archived evidence cannot be retrieved. It cannot fabricate history from current rows or silently downgrade an advertised horizon.

Every network/provider action has finite original submission, lookup/retrieval byte/work/deadline and containment limits, charged across retries and copies. Native retention uses its separate enclosing operation and recovery reserve. Missing provider bounds or unresolved possibly durable writes remain explicit custody; no retry budget reset, partial retrieval success or unbounded wait is permitted. Exact limits/mechanisms must be selected in the provider profile, preserving current request/consumer protection lifetimes.

Qualification schedules must inject lost upload acknowledgment, changed bytes under the same export identity, corruption/truncation on retrieval, changed protections between verification and drop, expired provider authority, provider overwrite/delete paths and lost native COMMIT acknowledgment. Independent observations verify local history/horizon, complete recovery contents and actual provider/native settlement separately. These schedules and provider selection remain unexecuted; this procedure supplies design ordering, not a durability claim.

## Shared local backlog admission

For the reference short/zero-window composition, select a finite bound on charged
local retained-history content, including required local prerequisites and
in-flight writer reservations. Define the exact encoded charge unit and duplicate
dependency treatment in the original resource profile. This is a logical content
bound; it is not a PostgreSQL disk-size or vacuum reclamation guarantee. Provider
transfer/retrieval work and durable request-receipt storage keep their separate
accounts and protection rules.

Before history-producing effects, the original protected writer procedure admits
a complete conservative reservation for its full possible event/prerequisite
inventory under the same native arbitration as concurrent reservations and
retention release. Admit only when existing charged content plus every live
reservation plus this reservation fits the selected bound. An isolated host
counter, snapshot-only sum or check followed by an unguarded append is insufficient.
Reserve rollback/recovery work separately; capacity refusal must leave graph,
catalog, journal and request-receipt effects absent, preserving prior caller work
under the selected savepoint contract. The exact native producer, common lock
order and UMF-authored account storage remain required composition outputs.

Finalization compares the complete actual encoded inventory against the original
reservation and publishes its charge atomically with history. An underestimated
reservation refuses and contains the entire operation; it cannot omit events,
obtain an unguarded post-effect allowance or silently raise the limit. Confirmed
rollback removes the reservation with the operation. An uncertain response retains
original settlement custody; host timeout, connection loss or a restarted worker
cannot release capacity based on an assumed rollback. Native current-account
observation must preserve charges for actual committed history and prevent an
unresolved original attempt from being submitted twice.

Archive confirmation alone does not release this local-content charge. Release
only the exact charged inventory actually removed by a qualified native retention
transaction, atomically with removal and horizon publication; content kept because
of a consumer, shared dependency or active partition remains charged. Failed or
unknown cleanup cannot produce a separate optimistic decrement. Retry and restart
reconcile the original account/removal correspondence before admitting release.
This composes the selected original resource/retention services and does not
introduce a caller-held capacity permit or replace the security owner's authority.

Qualification must independently race two writers whose individual reservations
fit but whose sum exceeds capacity; exactly the admitted work may produce effects.
Also exercise one underestimated full group, rollback after reservation, lost
writer COMMIT acknowledgment, durable upload without eligible partition removal,
shared prerequisites retained by another cohort, lost cleanup COMMIT acknowledgment
and restart. Observe original complete charges, reservations, history, receipt and
horizon inventories rather than trusting the account producer's returned total.
These schedules extend STP-018 HSEL-08 and STP-019 AH-05/06; none have run.
