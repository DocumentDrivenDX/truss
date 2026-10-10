---
ddx:
  id: PLAN-PYTHON-CONSUMER-001
  type: implementation-plan
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.implementation-plan
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-006
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
---

# Python consumer integration: first real workflow

The consumer needs host-supplied PostgreSQL transactions, accepted UMF registration, catalog inspection, exact reads, grouped writes, imports, receipt visibility and status. Current Python exports provide local-server lifecycle, execution outcomes and draft group/import contracts with local report consistency; callable graph capabilities remain unbuilt. TypeScript capability declarations describe intended contracts, not implemented Python behavior. The next release must provide a tested embeddable Python implementation, rather than merely translating interfaces or emitting administrative fixture identities.

Prioritize this plan ahead of more isolated component probes. It narrows the first test input to a synthetic commerce catalog, not the required authority, durability, exact-value or recovery behavior. Full corpus, broader schema coverage, managed deployment profiles and migrations remain required follow-on exits in the existing implementation plan.

## Execution order and dependencies

| Work item | Deliverable | Can start now / dependency | Completion evidence |
| --- | --- | --- | --- |
| PY-C01 | Python contract package: generic execution outcomes, semantic result variants, exact identities, opaque receipt tokens, request selection, import reports and capability Protocols | Start now from original versioned TS bindings; review every discriminant and nested result | Shared language-neutral valid/invalid vectors; exhaustive consumer mapping; type checking; wheel consumer imports outside checkout |
| PY-C02 | Python ReferenceAssembly construction, explicit capability readiness, host connection executor and adopt_transaction | Start lifetime candidate work now; qualified adapter implementation requires selected/published E06 private original arbitration, host-command exclusion, transaction generation and cross-assembly custody; protected capabilities also need installed owner/profile closure | Real PostgreSQL caller ownership, isolation/access verification, per-call savepoint rollback, cancellation, unusable/unknown outcome, disposal; no implicit host commit or pool management |
| PY-C03 | Registered acceptance-input preparation from original full UMF document bytes and document-qualified bindings | Start bounded source/shape/profile preparation now; acceptance requires full UMF check coverage, custody and security owner admission | Original document retained exactly; unknown meaning retained/reported; declared module identity preserved; no synthetic accepted IDs |
| PY-C04 | Explicit install/status plus first accepted commerce catalog, report and catalog view | Security contract PA01–PA04, seven native bodies/PA05 and complete PKG release/observer closure | Fresh pgserver-based install outside checkout; real accepted installation/catalog/revision/head IDs; unsupported profile refusal; actual report enforcement coverage; rollback/late-failure/unknown-install recovery |
| PY-C05 | Group apply/apply_batch, host dry run and durable idempotent replay | Protected mutation/finalization/journal composition; original authenticated actor and request namespace | One real product/order relationship mutation; rollback leaves no graph/key/journal/receipt effects; same request returns original complete ordered result; changed input conflicts; flaky-network recovery never reexecutes an unresolved original attempt |
| PY-C06 | Direct lookup/page/relationships and compiled query capability | Accepted catalog/read authority; selected Weft PostgreSQL realization and original query obligations | Exact integer/decimal/timestamp values, absent/null/empty distinctions, authorized full-page publication, alias/count/filter scenarios against real rows; no alternate SQL compiler |
| PY-C07 | Readable committed mutation feed and durable ACK by ordinary authorized source role | Complete journal/feed publication and original consumer authority | Mutation/feed boundary atomicity, crash before/after ACK, duplicate delivery, revoked/foreign role denied ACK, last durable checkpoint survives reconnect; retained outstanding events cannot be silently lost |
| PY-C08 | Import capability and report | Reuse accepted catalog, mutation, authority and batch settlement from C04–C07 | Objects before edges; per-record original-index creation/skip/rejection/attempt-unknown; load/source provenance; adopted scope stays pending; interruption/resume and exact aggregate counts |
| PY-C09 | Receipt visibility reached_in_transaction | Close existing proposal against real receipt producer, original read authority and snapshot comparison profile | Same supplied read-only transaction; false vs unavailable distinct; invalid/expired/unauthorized/unsupported token cases; no new connection, waiting or retry loop |
| PY-C10 | Versioned consumer example and release qualification | All selected capabilities above qualified independently | Reproducible public Python client and CLI workflow plus installed shared corpus/native interchange. Consumer runs without Truss source checkout and receives only actual committed identities |

C01–C03 proceed while the security owner finishes the handoff. C02 can expose supported executor/readiness behavior before mutation is ready; construction must refuse unavailable selections honestly. C04–C07 are the highest-priority behavioral delivery. C08 and C09 reuse that runtime rather than spawning a second engine. Do not wait for complete TypeScript parity, every adapter, or every deployment profile before releasing a qualified Python capability. Do not declare a complete consumer workflow before all of its required calls work.

## Decisions the consumer can implement against

**Construction.** Proposed Python naming is `create_reference_assembly(executor, configuration, registrations)` and `executor.adopt_transaction(...)`, with snake_case capability methods. The host owns the live connection/transaction and any pool. Configuration selects explicit installation/database/schema/profile pins and requested capabilities; connection availability alone cannot establish readiness. These names are a proposal to settle in C01, not callable exports today. Python 3.11 remains the initial target; synchronous versus asynchronous driver support must be selected explicitly in C02 before publishing signatures. Avoid an async-looking API that blocks the event loop.

**Results.** Mirror `truss-execution-v0.1.d.ts`: outer `Outcome[T]` is `ok(value)` or `error(ExecutionFailure)`. Group semantic success/failure/unavailable and applied/replayed response are nested values. Caller-adopted application is pending until the host commits; it must not become a committed consumer Receipt merely because SQL returned. Preserve native execution-unknown and commit-unknown with original recovery references, independently from semantic invalidity. The consumer's four labels cannot erase unknown outcome or pending durability: mapping must retain those fields or add explicit pending/unknown variants. C01 must publish an exhaustive mapping table and refusal/retry scope vectors, not broad exception-to-Unavailable conversion.

**Request key.** No key maps to request selection `none`. A present key maps to the declared RequestIdentity in an independently authorized namespace, with exact key text and full verified semantic-input identity. A scope string is not namespace authorization. Repeat of the same authorized input returns the original complete ordered result, including no-op entries; a different input gives request_conflict. An expired/unavailable receipt is not permission to run again. No implicit retry loop, and no journal-only replay reconstruction. Consumer keys must never be silently normalized, truncated or randomized on retry.

**Receipt token and reached.** Publish an opaque versioned locator produced from qualified receipt evidence, never a caller-built xid/sequence token. Proposed `reached_in_transaction(transaction, request)` takes token and explicit reduced limits from the current visibility binding. Authenticated principal is captured from original admitted transaction/context; asserted principal text cannot grant access. Return available/included or unavailable/reason inside outer execution Outcome. It observes one supplied read snapshot; it does not promise future replication progress or wait for the token. Token issuance and comparison remain C05/C09 qualification work.

**Import.** Bind input/load id, original source facts and asserted origin to the declared import input/payload profiles. Keep indexed per-record outcomes and batch durability: created, skipped, rejected and attempt_unknown, plus unprocessed indices and distinct committed/pending/rolled-back/commit-unknown/transaction-unresolved counts. A record created inside a caller transaction is not durably created. Map consumer initiated_by into an explicitly admitted asserted-origin/source metadata field; it never overrides the captured actor. Exact batch shape and selected ceilings are part of C01/C08; do not reduce the report to three totals.

**Actor and action.** Preserve original authenticated connecting person across any privileged writer. assertedOrigin is separate provenance. Preserve consumer action name under the chosen namespaced `x-` origin key, subject to existing origin validation; callers cannot overwrite actor/db_role or invent an authenticated identity. C04/C05 tests must show connecting person and asserted action simultaneously in actual retained journal/report evidence. The security owner supplies the subject/authority protocol; Truss owns correct integration and persistence.

**Document/module registration.** Prepare AcceptanceInput from the full original UMF document and selected binding/profile evidence through the registered producer. Module references retain document qualification; do not infer a document from a module name. Accepted IDs come from actual acceptance and are pending inside an adopted transaction until committed. Preparation produces no accepted revision/head. C03/C04 tests include two documents with the same module name and foreign/missing profile refusal.

## First end-to-end acceptance scenario

Use synthetic commerce data with an exact price, a large integer identifier and a typed order-to-product relationship. Start the selected local pgserver runtime, explicitly install the qualified Truss profile, connect as the ordinary person, construct the selected assembly and adopt the host transaction. Prepare/accept the original UMF catalog and commit under host ownership. Read actual installation/catalog/head/report identities. Apply a request-enabled multi-operation group, then read by key/page and through Weft. Read its committed feed event and durably ACK as the ordinary authorized source role. Disconnect/reconnect and repeat the same request: observe the original result and durable ACK without duplicate mutation.

Repeat with caller rollback/dry run, changed input under the same key, dropped connection at unknown commit, revoked ACK authority, duplicate module names, absent/null/empty values, exact decimal/large integer values, invalid import record and a receipt not included in the supplied snapshot. Assertions compare real original evidence and full state/journal/receipt/feed effects, never invented catalog or feed IDs. CLI examples must distinguish pending from committed output.

## Work control and release gates

Truss owns Python contracts, executor composition, installed native engine, receipts/feed/import and examples. UMF owns metadata/value/check semantics and reusable DDL; Weft owns logical SQL compilation; the security owner owns shared subject/authority/resolver contracts. Do not fork these meanings to meet the schedule. The approved security handoff is now sent; its closed contract remains pending.

Merge each reviewed work item into main with its scoped tests and support statement. Preserve ongoing owner changes. Verify the complete implementation and consumer workflow before advertising APIs as ready. The first planning/type-binding deliverables can land immediately; behavioral delivery dates are not credible until PA01–PA05 and complete installation scope are closed. Measure progress by the milestone exits above, not growing private component test counts.

## PY-C02 arbitration implementation sequence — Astra Ultra review

The original HostOperationArbitration binding and CONTRACT-007 E06 govern this
implementation. First supply a pure exact-issued-handle custody lookup for
registration/preparation and recovery. It performs no native observation or
acquisition, and cannot be used as command authority. Current native observation
remains after operation acquisition under its separate native-call guard.

Then implement one explicitly shared registry with a shared lock and
exception-safe atomic state publication. Never run host callbacks/native probes
inside that lock. Register assemblies and prepare opaque original attempts
inertly; preserve exact executor issuer and original transaction generation.
Acquire records a single original decision; observation never acquires. Busy,
abandoned and closed decisions are terminal and cannot become admitted later.
Closing one assembly atomically abandons its prepared attempts while preserving
other assemblies and acquired/unresolved custody. Test close/acquire races and
lost acquire replies, rather than relying on the GIL or per-assembly maps.

Completion requires original producer custody plus the complete original native
and resource ledger. Distinguish restored caller_idle from transaction_ended;
a failed/unusable active caller or unknown cleanup stays unresolved. Preserve
commit_unknown recovery independently of cleanup. Duplicate matching completion
reconciles the original result; conflicting completion and an old released lease
cannot release a newer operation. Test before/after-publication faults.

Enforce all conjunctive selected profile ceilings: assemblies, prepared/retained
attempts, active/unresolved leases, actual and reserved registry/evidence bytes,
single attempt/completion buffers and terminal retention. Reserve worst-case
decision and containment metadata before publishing preparation/acquisition;
uncertain completion does not refund capacity. Count-only limits or estimated
Python object sizes cannot establish the full bounded-memory support claim.

Only after these transitions, native host-command exclusion and generation
recognition are qualified may C02 publish driver-backed adoption. The current
pure lookup and trusted-port tests are prerequisites, not registry/native
completion or a substitute for the first real consumer workflow.


Python arbitration progress: the [Astra Ultra-reviewed private registry iteration](evidence/python-contracts-iteration3.json) implements one original executor domain, shared atomic operation-slot transitions, exact completion context, terminal decision retention, publication-fault reconciliation and bounded encoded recovery admission. Native completion production/ledger verification, host-command exclusion, driver transaction generation and whole resource qualification remain C02 gates. This is an implementation prerequisite, not a public adoption release.

## PY-C02 native boundary sequence — Astra Ultra review

The next native milestone selects synchronous pg8000 native 1.31.5 over a
host-owned PostgreSQL connection. Attachment requires an original idle cycle
before host BEGIN: the driver's constructor resets its status to unknown after
startup, and unknown must not be treated as idle. Attaching midtransaction cannot
infer original savepoint history and must refuse.

First capture original command/error/ready evidence for the entire original
native call and guard returned prepared execution/close under the same operation
boundary. Extended execution has multiple ready cycles; a later send/receive
failure after an earlier ready remains unresolved. Preserve an original native
rollback even when the driver synthesizes an exception. Refuse competing
supported calls before driver invocation and quarantine incomplete capture or
unowned events. This reviewed private slice is recorded in
[evidence/python-contracts-iteration4.json](evidence/python-contracts-iteration4.json).

Then supply explicit host lifecycle controls and original generation/savepoint
history: repeated BEGIN preserves generation, chained end creates another, and
shadowed savepoint rollback/release uses original ordered history. Use a separate
issuer epoch and nonallocating xid observation where applicable; do not assign an
xid merely to observe a read transaction. Recover failed-state savepoints using
original cached generation evidence, then verify native state after rollback.

Finally integrate the original native call/resource ledger with shared operation
arbitration and adoption. Trusted host SQL and cooperative routing are explicit
profile assumptions, not arbitrary raw-alias exclusion or malicious-host safety.
Only qualified supported paths may publish public adoption. C02 remains open.

Native lifecycle progress: the reviewed iteration now implements typed host
controls and original generation/savepoint history, plus real private
HostExecutor adoption on pg8000 native/PostgreSQL16.15. Repeated BEGIN preserves
the generation; confirmed end and chain retire the original generation while
retaining custody. An ended port reports its original ended lifetime and cannot
adopt a later transaction. Host release/rollback/shadowing shares authoritative
native savepoint history with executor admission. Exact quoted identifiers
refuse truncation and invalid text. Original control descriptors/candidates stay
retained across native completion and publication failure.

The host holds one original operation token across each complete executor call.
This explicit outer scope closes observation/control/publication interleaving;
ports refuse calls without it. pg_catalog-qualified native probes return actual
profiles and a nonallocating optional xid. Failed-state cached observations are
limited to original cleanup correspondence. Public adoption still requires
integration of this native ledger with shared arbitration, containment/recovery
and the selected full resource profile. No security-owner authority contract is
inferred from these administrative native component tests. See
[evidence/python-contracts-iteration5.json](evidence/python-contracts-iteration5.json).

The native issuer reserves canonical positive uint64 epochs monotonically under
its original boundary lock before fresh BEGIN/chain submission. Failed or
uncertain reservations never rewind. Repeated BEGIN preserves the existing epoch;
exhaustion refuses fresh/chain controls before native effects. Iteration 6 now supplies the atomic original-generation claim before observation
across separate executors. The claim captures only its exact native adoption
probe and requires unchanged call revision through final publication. Competing
claims refuse before SQL. Known profile mismatch refunds that exact claim;
uncertain publication retains original custody across disposal and garbage
collection. Lost replies reconcile already published success or known refusal.
Count bounds refuse before SQL; they do not qualify total heap usage.

Astra Ultra independently passed all 19 adoption tests and approved this private
iteration. See [evidence/python-contracts-iteration6.json](evidence/python-contracts-iteration6.json).
C02 remains open for shared arbitration/native resource-ledger integration and
containment/recovery qualification before public adoption.


Iteration 7 composes native execution with the original private arbitration
registry rather than creating another operation owner. One retained session binds
the original admitted attempt/lease/context, generation and guard. Calls register
before native submission; pending binding reserves the original guard before
registry acquisition and prevents release across lost replies or allocation
failure. Completion attempts freeze ordinary submission; the session locator
identifies custody and does not manufacture a completion artifact. Shared service locking preserves sessions across multiple native
boundaries. Prepared resources preallocate custody before SQL and retain actual
original statement-name arguments and ParseComplete/CloseComplete events.
Driver exceptions and Python publication failures do not erase native facts.
Count exhaustion checks precede mutating resource preflight.

This is prerequisite composition, not completed operation release. All failed
creation paths conservatively quarantine. Successful release stays disabled until
buffer, restoration and containment obligations have qualified original producers;
unknown leases and native guards remain retained. C02 is still open. Continue by
implementing the selected result/buffer custody and cleanup producers, then
qualify native operation restoration/recovery against these retained ledgers.
Evidence: [evidence/python-contracts-iteration7.json](evidence/python-contracts-iteration7.json).


Iteration 8 qualifies a narrow private operation producer for exactly
`SELECT :value::pg_catalog.text` on pg8000 native1.31.5/PostgreSQL16.15.
Astra Ultra approved narrowing the plan to pure parameter text; DML requires
its own semantic dependency qualification. Native success, host writes,
contained 22021 failure and subsequent success use the same adopted generation.
Original frame/context/result custody, separate cleanup ingress/account/context
capacity, explicit named/unnamed resource acknowledgements and actual
caller-state/savepoint restoration precede completion and atomic handback.
Lost publication replies reconcile the original completion without replay;
unresolved transport/cleanup/bounds failures retain custody and quarantine.

This closes only the selected private fixture operation. C02 remains open for
public construction/adoption, complete installed security/profile closure and
capability-specific semantic operations. There is no released catalog, mutation,
import, reached or feed implementation. Whole-transaction retry precedence is
implemented defensively; this pure text fixture does not qualify real native
40001/40P01 capability scenarios. Host aliases/custom native callbacks remain
unsupported, and payload/count limits do not establish a whole-process heap bound.
The explicit Python import map now includes the execution/native modules from
iterations 2–8 without a directory-wide exemption.
Evidence: [evidence/python-contracts-iteration8.json](evidence/python-contracts-iteration8.json).

## PY-C01 public contracts sequence — Astra Ultra review

Iteration 9 starts the public Python contract surface from the original
versioned TypeScript bindings, not a new semantic engine. Publish exact-value,
profile, document-qualified identity, capability selection, request and complete
group input/result carriers. The group Protocol is synchronous for the selected
Python embedding direction; every transitive carrier it advertises must exist.
Request-free overloads exclude replay, request conflict and receipt availability
reasons. Preserve outer execution failure separately from semantic failure and
pending durability; constructor/type conformance proves no native authority.

Use explicit absence for optional fields, distinct null/presence carriers,
immutable tuple members and exact numeric/timestamp/source spelling. Shape
checking does not admit UMF domains, verify original artifact registration,
prove receipt durability or issue accepted IDs. Verify language-neutral
positive/negative shape vectors, complete outcome mapping, static typing and
installed `py.typed` imports outside the checkout. Pin the original binding bytes.

Astra Ultra approved this sequence. Remaining C01 work includes Import's separate
progress-preserving execution union and all catalog/direct/compiled/mutation/
history/feed carrier closures; receipt visibility remains its own proposal
capability. C01 is not complete from the first group slice. C02's factory requires
original registered profile/service admission and a packaged release-owned safe
construction diagnostic artifact; an unverified readiness label is no substitute.
PA01–PA05 and C04–C07 remain the operational critical path. No callable protected
engine capability or assembly factory follows from these public data contracts.

## PY-C01 import contracts and consistency — Astra Ultra review

The next iteration implements the complete import input/report/execution-result
carrier closure from the original versioned bindings, including document-qualified
object-key identity and selected mutation configuration. It retains indexed
progress, all five batch dispositions and all nine counts. Resource-limited
results require interrupted reports; scope/engine report specialization receives
explicit runtime checks as well as static typing. The callable import Protocol
and transaction-options/cancellation closure remain subsequent C01 work.

A public pure report-consistency check uses explicit finite reduced limits and
expected input count. It checks canonical exact indices/counts, ordered outcomes,
complete disjoint coverage, batch correspondence, independently derived counters
and execution-compatible dispositions. It returns fixed local validation reasons,
never execution results, admission evidence or proof of native durability. Host
commit confirmation is not part of this slice; scope reports claiming committed
or commit-unknown disposition refuse consistency under this selected subset.
Original report data and opaque deferred payload bytes remain untouched. Review
runtime/static negatives and installed wheel evidence before merging to main.

## PA01 installed inventory component — Astra Ultra review

After the import contract delivery, return to installed execution prerequisites.
Implement one reusable private collector/reconciler for all routines discovered
in the selected Truss namespace, the seven original declarations (four admission families, the epoch helper and
two catalog high-water functions)
and six source-authored relation homes. Package exact owner-export catalog SQL
and its pinned manifest. Retain native bodies, argument/result identities,
owner/namespace/language OIDs, settings and original NULL-versus-empty ACL,
grantor/grant-option and effective positive/negative privilege observations.
Reconcile complete selected membership in both directions, including unexpected
overloads. Use the same installed collector in native ordinary-role denial and
inherited/PUBLIC/table/column/schema drift tests.

The selected compatibility experiment is PG16.15 using the supported subset of
PG17 observation proposals. Require the explicit original pg_catalog,pg_temp
resolution context before using their unqualified casts. Do not mutate host
transaction/session settings from the collector. Retained row/text admission is
not pre-ingress or total-memory qualification. Multiple catalog queries keep
production cut/freshness unresolved; the harness separately controls all fixture
administration. Static string-bodied/dynamic references, external wrappers,
shared/SET-role routes, guards/defaults/policies/types and protected owner capture
remain explicit gaps. Scoped correspondence is not PA01 completion, protected
admission, installation readiness or a public capability.

Iteration 11 implements this private component. The original installed snapshot
exposed the absent configuration home; the harness then composes its original
owner export. A separately captured original native comparison baseline pins
rendering and raw ACL provenance without proving authority or freshness. The
reconciler bounds both packets, rejects malformed native identities and foreign
comparison objects, checks joins and complete definitions, and detects widened
PUBLIC/grant-option access even when effective rights stay unchanged. Transactional
fixture mutations restore the exact original catalog state. See
[evidence](evidence/python-contracts-iteration11.json) and its native receipt.
This remains a cooperative private administrative tool; it adds no public runtime
operation and does not close PA01 or installer readiness. Next work remains
protected capture/writer composition with the security owner, then the first
catalog/apply/read workflow under the original host transaction.

## PY-C02 automatic original host-call scope — Astra Ultra iteration 12

Compose a private synchronous host-session facade over the original native
boundary/tracker, executor and exactly one existing arbitration service. Hold the
physical guard through complete adoption/savepoint calls and Python publication;
reserve retained descriptors before submission. Preallocate savepoint handle,
replacement map and response custody for create/rollback/release. A lost reply
after exact publication can reconcile the original result; an uncertain native
or publication window retains its original token and closes admission.

Explicit host BEGIN/COMMIT/ROLLBACK remains caller-owned. Preserve actual native
COMMIT, ROLLBACK (including failed-transaction COMMIT), deferred-constraint abort
and unacknowledged sent COMMIT distinctly. Disposal must not end the caller
transaction. Test sequential reuse, multiple facades sharing the original domain,
busy/capacity refusal, failed-state restoration, allocation/publication faults,
BaseException and disposal during admitted publication in an installed wheel.

This does not create an E06 lease or completion by registration. A confirmed live
executor savepoint transfers into original transaction custody; it cannot claim
that all semantic-operation savepoints were released. Public adoption/factory
promotion still requires its control-specific original completion/resource
producer, qualified cancellation/recovery and assembled-operation admission.
Protected capabilities separately need the original PA02–PA05 owner composition.
Keep exports closed until those gates have authoritative passing evidence.

Iteration 12 delivers the private facade, preallocated native/port/executor
publication and settlement custody, and nonblocking shared executor map admission.
The final installed wheel passes 298 tests, including 29 native scope scenarios;
44 Python modules and six packaged owner assets match source byte for byte.
Actual COMMIT/ROLLBACK command acknowledgements remain known if Ready is lost,
with quarantined handback and original exclusion/generation retained. Error-based
settlement classifications still require complete matching Ready. Independent
connections verify persisted and discarded rows after the real native tag fault.
See [iteration 12 evidence](evidence/python-contracts-iteration12.json).
The public C02/E06 and protected owner gates above remain open; prioritize their
completion before promoting the facade or declaring the consumer workflow ready.


### Private installed inventory: role transition paths

PA01/PA02 now require eleven retained sections, including native PostgreSQL16.15
MEMBER, USAGE, SET and ADMIN reachability for the ordinary invoker. Direct effective
ACLs alone miss INHERIT FALSE / SET TRUE authority. The fixed invoker profile
refuses any distinct SET-capable or ADMIN-capable role even when the supplied
baseline matches the unsafe observation. Membership without INHERIT, SET or ADMIN
is observed as drift against the former baseline and may match a fresh scoped
baseline. Ten-section historical packets refuse instead of silently omitting
this new authority dimension.

The [reviewed native receipt](evidence/design-audit/installed-role-paths-reviewed-native.json)
retains63 matching observations and29 inventories. Real ordinary local-socket
sessions demonstrate direct and indirect SET ROLE registry writes and ADMIN-only
self-grant escalation, each denied by the observer; revocation restores the
original scoped match. The exact479-row budget succeeds and478 refuses at the
last role-reachability read. Twenty original source pins and preimages remain
unchanged. The independently staged wheel matches50 Python/SQL/JSON source files.
[Astra ultra review](evidence/design-audit/role-paths-astra-review.md) required
execution from frozen producer SQL, now applied and rerun; earlier development
failures and the pre-review passing run remain historical at their own sources.

This component does not provide authenticated production admission, a coherent
protected cut, arbitrary role-mutator closure or the seven missing semantic
operation bodies. Native fixture routines are the four admission helpers, epoch
helper and two catalog high-water helpers; they are not those semantic bodies.
Installer readiness, PA01/PA02 completion and full backend acceptance remain open.

The original candidate installed wheel passes302 tests; the [suite receipt](evidence/design-audit/role-paths-installed-suite.json) retains test-source pins and terminal output.
