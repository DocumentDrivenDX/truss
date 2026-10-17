---
ddx:
  id: CONTRACT-013
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.prd
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: FEAT-003
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
    - id: ADR-003
      kind: informed_by
---

# CONTRACT-013: Frozen-manifest bulk action adoption

## Consolidation scope amendment — 2026-10-16

This historical draft is preserved from the earlier authorized bulk-action work.
It does not claim that its planned tests or protected executor are complete.
Current owner amendments govern every requirement below: Python-first delivery,
basic functionality tests, stock PostgreSQL practical limits and the existing
native statement/operation deadlines. Receiver/exporter, custom tracing/metrics,
formal-model and elaborate qualification prescriptions below are historical
optional proposals, not required implementation or release gates. A proposed
upstream60-second allowance cannot widen current native10-second SQL or30-second
operation limits. Host connection/transaction ownership and no hidden retries
remain unchanged. Existing `bulk_action_gateway.py`, action-store and authority
components on main must be reused and qualified; planned paths or statements
that no gateway exists describe the historical checkpoint, not current main.
Any cited evidence absent from main is **unverified historical evidence**, not
completion. Current public capability claims require their actual scoped tests.


**Version:** proposed `truss.actions.bulk/1`, `truss.actions.guard/1`, `truss.actions.snapshot/1`.

## Purpose

Adopt UMF CONTRACT-902/903/904 into Truss's protected native execution boundary. Upstream artifacts live in repository `umf` under `docs/helix/02-design/contracts/CONTRACT-902-portable-action-plan.md`, `CONTRACT-903-frozen-action-manifest.md`, `CONTRACT-904-bulk-action-coordination.md`. Selection is Weft CONTRACT-006 `weft.update-selection/1`, repository `weft`. Original owner artifacts are pinned build/runtime dependencies; local reimplementations of their semantic authority are forbidden.

## Scope and Boundaries

One admitted PostgreSQL store, namespace and accepted model revision. Python3.11 first under ADR-003; pure core/TypeScript stays host-I/O-free. The native proof profile is explicitly pinned to the adopted PostgreSQL/runtime/layout/driver release; earlier pgserver17.11 component evidence does not qualify a newer profile or bulk execution. Host supplies authenticated human/service, connections and queue scheduling. Complete native admission/installation, original authority and dependency closure remain required before any effects. Existing synthetic components are not exemptions.

## Normative Surface

### Registration and materialization API

`registerBulkActions(assembly, configuration): BulkActions` is inert trusted host registration, never execution readiness. Configuration is `{profiles:{plan:Profile,manifest:Profile,bulk:Profile,selection:Profile,guard:Profile,snapshot:Profile},action:ActionPin,ownerArtifacts:Artifact[],limits:Limits}` with exact upstream profiles plus truss guard/snapshot identities above. The assembly supplies original catalog/value/key inspectors, shared security admission, resource account and transaction executor. US-049 implements/adopts the bounded Python UMF-action gateway and registry; ordinary Truss mutation APIs do not imply its full action execution qualification. It uses original UMF schemas/approved semantic corpus/owner preparation and full original action declarations, with exact tx/1 outcomes. Native custody and completion use the adopted CONTRACT-007 baseline through supported driver APIs; historical raw-frame/private-hook proposals are not prerequisites. It is a conforming consumer of owner semantics, not a second authority. No certified TypeScript consumer is relabelled as a qualified Python gateway. Missing original dependency/authority evidence refuses. Manifest metadata cannot install this configuration.

`BulkActions.materialize(plan:Artifact, context): MaterializeResult` performs qualified selection/sealing in an engine-owned REPEATABLE READ read-write preparation transaction. context is the assembly's existing authenticated human/service/current-policy and connection-lifetime capability, not a caller-asserted principal JSON member. Result is `{status:"sealed",manifest:Artifact}` or `{status:"denied"|"unsupported",code:string}` or CONTRACT-904 ControlFailure or ControlUnknown. Before dispatch, context contains the qualified original control-attempt/recovery capability. Lost seal-control COMMIT acknowledgement retains that capability and reports ControlUnknown; it cannot return failed or re-materialize as an assumed rollback. recoverControl settles original sealed/result/custody under current authorization; unknown control disposition cannot be relabelled sealed. No raw connection/SQL capability is exposed to plan/action handlers. `submit`, `claim`, `execute`, `lookup`, `reconcile`, `recoverControl`, `review`, `cancel`, `status` implement the exact upstream bulk operations through the same authenticated assembly boundary. Method names/arguments/results are CONTRACT-904 with context passed out of band. No caller-owned outer transaction may encompass a multi-batch job; materialization and each batch use separate engine-owned transactions with confirmed completion. Individual internal action gateway calls adopt the engine-owned batch transaction, never commit or retry independently. Full item replay request locks are acquired in the complete CONTRACT-009 level4 set BEFORE the job-control lock; the gateway consumes preheld original lock/custody evidence and may not reacquire earlier-level locks.

### Engine-owned preparation and current authorization

The assembly MUST supply one original protected action-store registration shared by registry, Subject/roles, delegation, guards, cut/seal storage, jobs and replay. It retains exact original canonical store identity bytes, trusted tenant and namespace-lifetime epoch, and independently binds them to the actual native installation/database/schema/source incarnation. A physical installation UUID, connection URI, source marker, registry ticket or caller-authored store bytes alone cannot issue this registration. Trusted native installation/registration confirms persistent issuance before returning an admitted capability; native consumers compare full identity and original correspondence under the shared lock order. Connection reopen and action revision changes do not mint a new logical store or reset token recognition. Lost issuance acknowledgement retains the original native installation/registration attempt and its CONTRACT-007 custody/recovery boundary; qualifying this issuer includes its durable registration observation. CONTRACT-904 recoverControl has a closed operation union that does not include store registration, so it cannot silently serve this purpose. Missing/foreign/fenced or unverified restart/restore correspondence refuses fresh admission. Fencing or epoch replacement preserves original recovery custody and cannot reset token recognition or create a fresh replay namespace; any retained observation still requires qualified current disclosure and restore correspondence. Role enrollment and sealing consume this shared issued boundary; preparation cannot invent another store convention.

Materialization owns a read-write preparation transaction: it reads business data and persists the protected seal atomically. The host supplies original authenticated context and admitted connection providers; it cannot supply a principal assertion, authorization verdict, snapshot text or seal as authority. Individual selection/preflight/Key/guard queries MUST consume the same fixed data cut. Ordinary caller transactions and ordinary READ COMMITTED catalog APIs do not by themselves qualify this preparation boundary.

The first preparation profile preserves the initiating native caller as the data transaction's original connecting person. Engine ownership means a fresh engine-controlled connection/transaction authenticated through the host's qualified provider, not a transaction begun earlier by the caller. A privileged procedure owner and a separate coordinator identity MUST NOT replace that original caller's authority. A service-to-human preparation profile requires its own original protected delegation and cannot infer the human from supplied IDs. Worker delegation remains separately qualified under US-049.

Selection executes through an originally installed protected native entrypoint consuming admitted Weft lowering and exact typed parameters. Enrollment grants neither raw canonical-table access nor arbitrary SQL submission. The entrypoint MUST require original live bridge/cut/actor custody; a direct call outside admitted preparation MUST refuse, including calls by the otherwise enrolled native caller. Complete authorized-population preflight and Key/identity/version selection retain their original semantics. A first module-access profile MUST explicitly refuse selected finer-grained policy or field-protection meaning lacking original qualification.

Current authorization and frozen data are separate obligations. The selected native profile MUST bind original initiating human/service, installation/epoch, accepted catalog and policy basis to the exact preparation connection/transaction incarnation and fixed cut. It MUST establish current authorization after acquiring the required exclusions and retain those exclusions through seal persistence and confirmed native completion. Every participating policy/catalog/role/source writer and every relevant bypass path MUST be accounted for; a cooperative lock without complete writer participation cannot establish current authority.

A separately engine-owned READ COMMITTED authority/control connection MAY provide current-authority admission only through an owner-defined, versioned native bridge. Such a bridge MUST bind its original authority evidence to the exact fixed data transaction and authorized selection view, retain original connection/attempt custody, obey the shared lock order, and prevent stale or foreign authority evidence from sealing. It MUST NOT expose raw privileged connections or let caller-authored IDs/snapshot values issue admission. Two separately valid connections do not establish this binding by themselves. Where the selected profile cannot protect a relevant authority source, preparation refuses TRS-BULK-ADMISSION before protected selection or seal publication.

Authority/catalog changes completed before protected admission MUST be observed or cause refusal. Once admitted, participating changes either wait for preparation completion or invalidate preparation before publication under the owner-defined protocol. A late lock does not refresh a REPEATABLE READ snapshot; stale correspondence or serialization failure refuses the original preparation, with confirmed rollback or original ControlUnknown recovery as appropriate. No automatic callback replay or hidden substitution of a newer cut is permitted. Later review, submission and execution perform their own current authorization; the seal grants no lasting permission.

### Read basis and canonical guard

Materialization begins a PostgreSQL REPEATABLE READ read-write transaction for selection and protected seal-control persistence. Its snapshot is established by the first relevant query; head/authority locks and fresh original-source validation follow the existing fixed-snapshot admission procedure. The implementation MUST revalidate snapshot/catalog/authority correspondence after acquisition, refusing a stale cut or serialization conflict rather than pretending a later snapshot was obtained after locking. All head/authority protections remain held through seal persistence and native completion. All selection rows, Key tuples, complete canonical identities and row versions are read under that same snapshot and original authorized view. A separately issued opaque Basis.cut under truss.actions.snapshot/1 identifies this exact cut/store/epoch; it is not PostgreSQL txid_snapshot text relabelled as a portable ordered commit version. Original selection artifact, mapping/native-source correspondence and guarded publication are checked before sealing. No SQL LIMIT may silently cut matching work; read maxItems+1 to detect overflow while preserving the actual account/deadline requirements. ORDER BY actual native integer object ID in ascending mathematical order (2 before10) establishes stable manifest order, not display-name collation.

`truss.actions.guard/1` identity is exact positive canonical base-10 text of the original Truss object ID, scoped by store/epoch and the pinned Record/type binding. version is exact positive canonical base-10 original object ver text. Both remain opaque to portable consumers: do not compare lexically, infer a different type or coerce through binary floating point. Execute resolves the retained Key tuple to the original object ID/type and compares whole-row ver under the complete mutation/group locks. A different object, absent object, changed ver, catalog/profile drift or epoch mismatch refuses/conflicts before any graph effect. Bulk-profile admission requires immutable-ID nonreuse and monotone nonreset row versions within the namespace; ordinary allocator/version behavior without proof of these premises cannot qualify a guard. Native/bypass writers must participate in version/invariant enforcement or the profile refuses them explicitly.

Snapshot cut control state is emitted only by the trusted read adapter; store/epoch/key/version content in a client Artifact cannot issue it. Materialization resolves the portable action identity/document hash to the exact executor RevisionRef and retains it in Manifest.action. It returns sealed only after durable complete manifest storage with original initiating human/store/epoch/read-cut/guard/selection custody and confirmed transaction termination. submit refuses unless original bytes match that retained seal for the same human/store/epoch; recomputed client digests or plain identity/version guard text cannot issue a seal. Selection statements are supplied by the original Weft selection lowering, never a Truss SQL source parser. Unknown/unsupported selection semantic or a missing compiler-lowering/native correspondence refuses before executing SQL.

### Batch composition and replay

For an action declaring `umf.actions.roles/1`, the original authenticated human MUST hold at least one exact declared role under CONTRACT-901. The executor's original protected membership/Subject binding supplies these roles inside the current native authorization and commit boundary. Module read/write permission, a worker's role, a declaration's role list and an owner preparation obligation marked checked MUST NOT substitute for that binding. Unknown or absent action-role binding refuses. The first products action retains its declared `bulk-editor` role and `person-required` attribution; the native catalog/data export grants no action eligibility. Protected replay discovery uses its independently installed action-family binding under CONTRACT-901, with current authorization before token observation; it is not inferred from revision authorization.

Use CONTRACT-007 engine-owned connection-affine transaction completion and CONTRACT-009 discovery, complete lock closure, ordered group simulation and final invariants. Every item uses original UMF action/Field/Key semantics through US-049's qualified gateway. The guarded coordination pass precedes any tx/1 fresh invocation; all absent/deleted/rebound/version-changed targets produce batch conflict/PAP_GUARD without invented item terminal results. Once guards pass, tx/1 ENTITY_MISSING and other stage precedence remain unchanged. US-049 also qualifies the independently issued bulk-initiator/1 delegated human session binding: original human remains the tx/1 principal and current-policy subject; worker is separately authenticated service, not human impersonation. Enforce per-action required effects/constraints and complete batch final invariants; a group cannot weaken tx/1. If an invariant cannot be met at the required per-action point, refuse that arrangement instead of claiming bulk composition supports it.

Retain native control homes for job/manifest, claim/fence/cancel state and complete batch/item outcomes in a versioned fixed-layout migration. Job control row is locked before batch admission and held through native completion; all worker/cancel/retirement routes participate. Reconcile this lock position with CONTRACT-009's existing catalog/authority/namespace/request order: acquire its complete levels 1–4 before the job-control lock, then business/group locks. No path may hold the job lock while waiting for an earlier catalog/authority/namespace/request lock. Job lookup/cancel without business execution uses the same prefix needed for current-authorized control access. Leases cannot authorize takeover while native custody is uncertain.

Graph data, item replay outcomes, batch complete-result receipt, job committed-prefix advance, journal and selected outbox facts commit together. These homes are fixed metadata/control structures, never a new table per model/action/job. Full original bytes and native outcome/manifest correspondence join installation/admission evidence. No raw consumer INSERT into control tables or elevated synthetic registry writes. Complete no-op result vectors remain durable; changed items retain original semantic order. Job status counts only confirmed contiguous batch outcomes. Warehouse publication is separate; apply existing qualified feed/readAtLeast semantics only when claimed.

### Original native attempt custody and reconciliation

Before any effect transaction obtains job/business locks, the qualified host opens that original physical effect connection/session and captures its exact installation/epoch/connection incarnation and native transaction custody. A separately admitted control connection durably records the original attempt/fence and confirms effect-admitted registration before business writes can begin. It does not acquire a job lock already held by the effect transaction; the effect connection has no job lock at this registration point. The control route uses the global lock prefix, then the effect route independently acquires the complete same prefix and checks the confirmed original registration/fence. Namespace transitions, cancellation and competing workers must observe both routes; no effect may start solely because a worker submitted a claimed xid.

If an actual xid8 is used, assign/capture it on the ORIGINAL effect transaction before registration and retain the original driver/caller/installation correspondence outside that transaction. Qualification must establish that this is the same transaction that subsequently owns effects and locks, and the registration cannot become an untrusted caller assertion. Reconciliation uses retained original driver custody/native termination plus fresh original receipt observation: confirmed COMMIT with matching original outcome returns it; confirmed ROLLBACK/native noncommit with an admitted attempt and no terminal outcome stops with PAP_ABORT_DISPOSITION_UNKNOWN; unresolved native status/connection ownership stays reconciling. pg_xact_status NULL, receipt not-found or expired lease never proves rollback. The conservative first proof does not resume stopped jobs or retry admitted business work; this includes a crash after invariant rollback but before durable stop. Markers without confirmed commit block effects and retain their own uncertainty. Native instance loss/restore without a complete original graph/control/outcome consistency proof fences the namespace.

### Diagnostics and finite resources

Adopt original shared diagnostic/capture pipeline and its exact existing contracts; no parallel bulk-specific telemetry transport. Bulk diagnostics use existing trusted attemptId/runId correlation and safe operation/outcome slots; job/batch/fence correspondence is retained in separately protected audit/control state, never added as unknown exporter fields. Raw SQL/parameters/guard/business values are excluded before sinks. Failed exporter cannot change commit/lock/recovery meaning. TD-048/STP-048 allocate traced/untraced real-receiver correlation, privacy and outage tests under the already selected o11y-otel concern.

Upstream100-item/10000-item/16MiB/60-second limits apply. Register an 8 MiB maximum retained result per batch and 256 MiB maximum retained manifest/outcomes per job; admit finite complete manifest/control space at seal/submit and reserve full configured result space for each batch before its writes and refuse PAP_LIMIT on exhaustion. Actual retained manifest/control/outcomes MUST fit the256MiB job cap. Later batch capacity refusal may stop a partially completed job; its committed prefix is retained explicitly. It cannot omit/truncate receipts or masquerade as whole-job success. No truncation or result-vector reconstruction from journals. Durable namespace nonreuse and retention are CONTRACT-904 namespace-lifetime rules, stronger than ordinary group minimum retention; existing ordinary groups remain unchanged. No universal CPU/heap ceiling or throughput claim.

## Precedence and Compatibility

UMF owns actions, exact values and portable bulk semantics; Weft owns source selection; Truss owns physical correspondence and constraints. Existing CONTRACT-001/003/004/005/006/007/009/010/012 apply without relaxation. New native homes require a qualified shipped migration and accepted installer; proposals alone confer no support. Queue restart/restore must preserve original intent/outcome consistency or fence the namespace. Unknown profiles/content refuse; do not fall back to direct writes or recompile a queued job against a newer model.

## Error Semantics

Preserve CONTRACT-904 outcomes/codes. TRS-BULK-ADMISSION denotes missing protected assembly/native profile, TRS-BULK-SNAPSHOT unavailable coherent read-cut/source custody, TRS-BULK-CAPACITY unavailable complete-result reservation. Original native/storage constraint errors retain existing protected-safe translation. Failed means confirmed rollback; indeterminate means original native outcome remains uncertain. Current authorization precedes protected manifest/receipt disclosure, including discovery. New attempt authorization cannot settle unknown original work.

## Examples

Materialize two customers in one admitted snapshot, seal original guards and batchSize1. Execute batch0 under the protected group path; a later edit to customer1 produces an original batch1 conflict and stopped job, preserving batch0. A key reassignment between selection and execution fails native identity comparison. Loss after batch0 outer commit must return its retained receipt rather than call update_object again.


## First direct-action prerequisite: owned completion

The proposed `truss.actions.owned-completion/0.1` profile uses one fresh,
engine-owned psycopg connection authenticated as the original enrolled human
through the existing local SCRAM adapter. It begins READ COMMITTED/read-write
from IDLE and retains the original connection, backend PID and adopted transaction.
It refuses a non-idle or substituted connection and never repairs, reopens or
retries it. Caller-owned transaction adoption keeps its existing contract.
This component alone authorizes no action and issues no tx/1 receipt.

The invocation's absolute operation deadline includes settlement; COMMIT cannot
start with a fresh full budget. Before settlement, original host custody must
be usable, the connection must remain INTRANS rather than INERROR, and the
original adopted host must detach without handing the connection to a caller.
The session attempts completion once. Reuse the existing owned-import control
path and supported psycopg command/status/error APIs. Native COMMIT acknowledgement
and matching IDLE establish commit; an actual ROLLBACK acknowledgement or native
commit error with confirmed rollback establishes rollback. A tag without its
matching native state does not establish settlement.

A definitive settlement survives later cursor/deadline cleanup failure. Retain
that failure separately and quarantine/close the connection without reuse.
Missing or contradictory acknowledgement remains unresolved. Closing a connection
proves neither commit nor rollback; do not issue a competing rollback or retry
an unresolved COMMIT. Original invocation identity/custody must remain available
for the later protected reconciliation path. Stock PostgreSQL synchronous_commit
and durability settings remain explicit native deployment assumptions; this
component makes no crash/restore continuity claim.

The protected action provider must still bind the complete accepted action,
issued revision/store, authenticated Subject, current ACTION roles, independent
replay-discovery policy, exact frames and actual effects to this same transaction.
Only its finalized native outcome plus confirmed completion can become an SDK
Committed result. The ordinary group receipt and this session's completion
observation are not substitutes for an authoritative action outcome.
