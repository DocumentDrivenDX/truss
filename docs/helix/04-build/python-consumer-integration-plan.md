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

## PY-C02 original control ledger and bounded detachment — next planned work

The next transport implementation must retain every native call and simple-query
Context from entry through response admission and exact handback. Attach the
original control ledger before adoption/profile-observation or lifecycle SQL;
reserve its descriptors and bounded receive/decode custody before submission.
The existing selected text-operation frame gate supplies reusable ingress and
Context custody, but its semantic cleanup/completion rules cannot substitute for
a host-control producer. A successful savepoint remains in the original live
transaction's custody; an unnamed or named resource created by this scope needs
its own confirmed release. The selected completed simple-query utility path leaves no resumable
statement/portal obligation; it still uses a native internal portal and can
destroy a preexisting unnamed statement/portal. The resource-free entry subset
must be qualified rather than inferring preservation from restored metadata.

Qualify original driver methods, dispatch, UTF8/text decoders and original host
resource baseline at entry and after gate detachment. Preserve the original
connection Context, dispatch, socket and method ownership; clear only this
scope's owned result/error references. Verify every admitted original native
call, port/executor publication and generation/savepoint transfer before handback.
A fault during installation, capture, detachment or publication retains the
original token/ledger and closes further admission. Recovery inspection reports
retained facts without replay or release permission. Pre-admission cancellation
submits no SQL; active cancellation never invents containment or rollback.

This control producer shares original executor/physical exclusion and does not
fabricate an E06 semantic lease during adoption. Public promotion requires its
actual qualification and selected host recovery profile. Protected PA02–PA05
bodies are a separate graph-operation gate, not a reason to postpone independent
transport work. ReferenceAssembly remains the separately governed inert
configuration, capability selection and recovery boundary; the partial native
host adapter must not take that name or declare those capabilities installed.

## PY-C02 snapshot-neutral profile refusal — Astra Ultra iteration 13

Astra's native counterexample found that the original SELECT profile probe pins
a repeatable-read or serializable snapshot even when adoption refuses. Prioritize
that correctness fix before composing the planned control ledger. The claimed
port performs only fixed SHOW transaction_isolation and SHOW
transaction_read_only prechecks. Retain both original calls, values, claim, token,
generation and ordered revisions. A complete actual mismatch can refund only
that unchanged original claim through distinct SHOW-only refusal evidence, which
contains no authenticated person/role/xid. Matching checks continue the original
full SELECT producer; SHOW-only evidence cannot publish a usable handle.
Disagreement in that later SELECT or an intervening call stays unresolved, since
SELECT may already have changed snapshot state. No unknown observation is
refundable. Test independent-connection visibility after refusal for both stronger
isolations and both mismatched isolation/access profiles, safe same-generation
adoption afterward, duplicate no-SQL refusal, second-SHOW loss and terminal
refusal reply loss. This fix does not release public adoption or qualify C02.

Iteration 13 implements the snapshot-refusal correction and extracts the existing
resource-free original driver predicate with an AST-identical body. The final
installed wheel passes 301 tests, including 22 adoption scenarios and four
independent-connection visibility subcases. Its 45 modules and six packaged owner
assets match source exactly. See [iteration 13 evidence](evidence/python-contracts-iteration13.json).
The planned composed control ledger above remains unfinished; this corrective
iteration does not promote the public adapter or complete C02.


### Combined-main validation of role reachability

Concurrent main iteration13 was integrated without replacing its snapshot-neutral
adoption correction. A fresh [combined wheel](evidence/design-audit/role-paths-merged-wheel.json)
matches all45 Python modules, six packaged SQL/JSON owner assets and py.typed.
Its [full installed suite](evidence/design-audit/role-paths-merged-suite.json)
passes305 tests. The [fresh native rerun](evidence/design-audit/installed-role-paths-merged-native.json)
passes63 observations with29 inventories at20 unchanged source pins. The updated
Python-only boundary checker passes200 edges. These records qualify the combined
candidate; the earlier302-test wheel remains evidence only for its captured source.
Complete protected admission and backend acceptance remain open.


### Reviewed role-route guard laws, upstream main

UMF main07357ead supplies [source-derived formal guard evidence](evidence/design-audit/role-paths-formal/integration.json)
for the exact installed collector from Truss11f14e23. Five UNSAT violations,
three SAT populations and three SAT erasures use the actual parsed predicate,
complete unfiltered finite `any` fold and terminal classification. All32 Python
predicate/fold vectors and29 original native predicate results match; Astra ultra
independently replayed all11 exact saved formulas and verified their byte hashes
and seven original source pins. Exact producer invocation controls also refuse.
No collector implementation changed for this proof; source correspondence is
explicitly rechecked in this integration receipt.

Complete authentic current native rows are an explicit analysis premise, not
provided by packet shape admission. This verifies the pure guard tail only,
not the whole validator, PostgreSQL role graph, coherent cut, protected native
admission or semantic operations. PA01–PA05 and complete installation/readiness
remain open. No ordinary writer grant, invoker-guard removal or acceptance
promotion follows from these laws.


### Iteration 14: compose original host control custody

Astra Ultra reviews this plan and the completed implementation before main publication.
Install a private original simple-query producer which reserves retained call records
and Context slots before send, enforces exact per-call protocol grammar, and restores
original host methods and Context before atomic scope handback. Share capacity across
connections through one producer per executor and a conjunctive boundary cap; busy or
exhausted reservation refuses without SQL. An explicit host-requested idle resource
baseline inventories named resources and retires unnamed resources. The text runner
must require that baseline on this composed path and retire its own unnamed resources
only through verified original cleanup. Preserve acknowledged commit meaning across
lost replies while retaining unresolved custody. Validate native malformed responses,
publication faults, resource preservation, and a baseline/begin/adopt/text/savepoint/
commit workflow. This remains private infrastructure: public ReferenceAssembly,
installation, mutation, import, feed and recovery qualification remain outstanding.


Iteration 14 implements the private composed producer and runner resource baseline.
The installed wheel passes 320 tests, including 19 control-custody scenarios; all
46 Python modules, six owner assets and the typing marker match source. See
[iteration 14 evidence](evidence/python-contracts-iteration14.json). Astra Ultra
approved the source, plan and original installed artifact. Integration with newly
landed security inventory changes and combined validation precede publication. This advances the control
ledger prerequisite; public adoption/recovery and the external interface remain open.


Combined iteration 14 integrates security main20c78c8c, preserving its role-path
inventory and source-derived guard evidence. The fresh combined installed wheel
passes 324 tests outside the checkout; all 46 modules, six owner assets and the
typing marker match source exactly. The Python boundary checker passes 212 imports.
See [combined artifact evidence](evidence/python-contracts-iteration14-combined.json).
This combined validation supersedes the original 320-test wheel for publication;
complete public interface and protected admission readiness remain open.


### Authenticated native inventory fixture and session lifetime

The original PostgreSQL16.15 / pgserver0.1.4+truss.pg16.15 / pg8000
1.31.5 candidate now has an owned Unix-socket SCRAM-SHA-256 fixture.
[Combined native evidence](evidence/design-audit/installed-scram-combined-native.json)
records82 observations and31 inventories with21 frozen source inputs. Wrong
credentials and nonexistent subjects refuse28P01; native backend-PID authentication
logs bind the ordinary connection to SCRAM. NOLOGIN refuses new sessions28000
and changes inventory qualification, while two established sessions remain usable.
Restored LOGIN permits a new session. LOGIN state cannot establish current-authority
revocation or retire an existing authenticated operation.

Four real failure controls verify secret redaction in receipts and subprocess stderr,
including an unwritable receipt sink, and cleanup of every connection and cluster
despite close failures. The helper executes captured bytes. Astra ultra feedback
was applied before the final combined run. Historical development receipts retain
their original pins; the first failed run identified backend-start log configuration
and was corrected with a fresh inspector.

The fresh combined-main installed wheel matches all53 source/owner/typing files.
[Combined suite](evidence/design-audit/scram-combined-installed-suite.json) passes328 tests;
[Python boundary evidence](evidence/design-audit/scram-combined-boundary.json) passes212 imports.
This qualifies only the stated local fixture and private inventory component. It
does not qualify TLS/production authentication, protected mapping, coherent current
cut, PA01/PA02 completion, seven semantic operation bodies or installer readiness.
Original UMF acceptance remains26/132; US-056-AC5/AC9/AC10 gain component evidence only.


### Installed elevation census across native namespaces

The fixed ordinary invoker profile now requires a twelfth `callable-definers`
section. It conservatively enumerates every native EXECUTE-accessible SECURITY
DEFINER across all schemas, retaining schema USAGE independently. Any nonempty
census refuses, including an identical unsafe expected baseline. Eleven-section
packets cannot assert absence. Future registered protected definer chains require
a distinct admitted profile; this rule is not a universal ban in UMF semantics.

[Final native evidence](evidence/design-audit/installed-definer-final-reviewed-native.json)
passes97 observations across35 inventories, with21 frozen source inputs. An
ordinary SCRAM session with direct UPDATE false calls an external PUBLIC-executable
definer owned by a separate nonlogin role. Its committed UPDATE changes the
protected row's native xmin, independently observed by the inspector; logical
revision stays unchanged. Matching unsafe baselines refuse. EXECUTE revocation
removes the route; schema-USAGE revocation retains and refuses the route. The
fixed native PREPARE/EXECUTE experiment revalidates and returns42501 with unchanged
xmin after schema revocation. This does not establish all retained-plan behavior.

Astra found an empty-final-section text-budget gap and an unsafe schema-USAGE
filter. Both were fixed and independently reviewed. The replayed80164-unit packet
passes exactly;80163 and80076 refuse. Native overflow at the additional final
census row refuses rather than silently treating an incomplete prefix as empty.
Earlier positive/failed runs and preimages stay historical at their original bytes,
including two rejected predictions about prepared calls.

The final separately installed53-file wheel passes334 tests;
[final suite receipt](evidence/design-audit/definer-paths-final-suite.json) and
[Astra review](evidence/design-audit/definer-paths-astra-review.json) retain exact
source/log/native pins. Python boundaries remain212 imports. This advances
PA01/PA02 and US-056-AC5/AC9/AC10 component evidence. It does not establish
complete call closure: operator/type/extension, trigger/default/RLS, indirect
resolution, protected capture/current cuts and the seven semantic bodies remain
unqualified. Existing source-derived role laws retain their historical module
pins; no new whole-program or temporal proof is claimed. Original acceptance
stays26/132.


### Native operator implementation route

[Final native operator evidence](evidence/design-audit/installed-operator-final-native.json)
passes107 observations across38 inventories with21 frozen inputs. An accessible
operator refers to a SECURITY DEFINER implementation in a distinct hidden schema.
The ordinary SCRAM caller has no direct UPDATE right and no USAGE on the function
schema, but invoking the operator commits an UPDATE, independently verified by
changed native xmin. The existing census retains that implementation and rejects
an identical unsafe baseline. Revoking implementation EXECUTE then produces42501
and unchanged xmin, restoring scoped correspondence. No new permission bypass
by ignoring EXECUTE was observed. Operator removal restores the original baseline.

[Installed suite](evidence/design-audit/operator-paths-suite.json) passes336 tests
on the unchanged53-source installed wheel. [Astra review](evidence/design-audit/operator-paths-astra-review.json) independently verifies current pins.
These controls support the conservative separation of function EXECUTE and schema
USAGE; they do not establish all operator support/selectivity, planner, type,
trigger/default/RLS or extension routes, nor complete protected capture/current
cuts. Original acceptance remains26/132. Source-derived proof scope is recorded
separately by UMF; native privilege observations do not supply a SQL refinement
proof or authenticate production authority.

UMF main `afc03d29` retains the [source-derived census/guard proof](https://github.com/DocumentDrivenDX/umf/blob/afc03d29/docs/helix/04-build/evidence/security/truss-definer-census-formal/cfa978ae-c2c9-4fef-b244-4495aab10da9/proof.json) and its independent Astra ultra replay: six exact SMT queries,64 actual-tail vectors and38 original native inventory tail replays. Native row completeness and privilege facts remain premises; this is not full SQL/Python/temporal or protected-admission refinement. All original acceptance obligations remain required.

### Iteration 15: original host-call recovery and disposal admission

Astra Ultra approved the plan before implementation. Reserve bounded opaque
recovery references in the original executor domain and retain them at the native
boundary before acquisition. Recovery must survive lost returns, BaseException,
disposal and facade collection. Freeze every returned outcome, including acquisition
refusal and commit_unknown, together with original call facts. Inspection publishes
no native handles, runs no SQL and neither acquires nor retries cleanup/publication.
Only the exact original release.published receipt proves historical handback;
later generations and owners cannot replace this call's evidence. Linearize ordinary
admission against shared executor disposal before token acquisition; keep disposal
distinct from unresolved quarantine. Explicit host BEGIN/COMMIT/ROLLBACK remain
available after disposal only while the original boundary and profile are healthy.
Test publication faults, known COMMIT with unresolved handback, newer generations,
forged/foreign references, facade collection and concurrent disposal/admission.
This is a private recovery observation, not a recovery procedure. Active native
cancellation and containment are the next mandatory C02 gate; public adoption,
ReferenceAssembly and protected capabilities remain unfinished.


Iteration 15 now implements private original-call recovery observations and shared
ordinary-admission closure. References and nine fact slots are retained before
acquisition; inspection uses the original synchronized release receipt and sealed
facts, never a newer owner or native call. Astra Ultra independently passed all
17 native recovery tests and approved the source/plan checkpoint. See
[iteration 15 evidence](evidence/python-contracts-iteration15.json). Merge the latest
reviewed SCRAM fixture work and validate the combined installed wheel before push.
Active cancellation and native containment are the next transport implementation;
public C02 and the complete external interface remain open.

Combined validation integrates security commit bb5eb75a with checkpoint 3e6fb741.
The installed wheel passed all 345 tests outside the checkout (43.744 seconds);
47 Python modules, six owner assets and py.typed match source, wheel and install
byte for byte. The module boundary check covers 216 imports. See
[combined iteration 15 evidence](evidence/python-contracts-iteration15-combined.json).
This completes the private recovery iteration; public C02 and installer readiness
remain open pending cancellation, containment and the semantic interface.

Concurrent security commit 71ba19f8 is also integrated: the rebuilt installed
wheel passed 351 tests in 41.260 seconds, with all 54 packaged files verified.
See [final combined evidence](evidence/python-contracts-iteration15-definer-combined.json).
Astra Ultra approved integration and independently passed 17 inventory tests.
The earlier 345-test artifact receipt remains historical.


### Iteration 16: active statement cancellation and native containment

Astra Ultra approved this plan for the private prepared-Execute runner path. This
continues PY-C02 under CONTRACT-007's original operation custody, cancellation
and disposal requirements. The preceding iteration15 evidence remains unchanged.

Select the existing synchronous pg8000 1.31.5 / PostgreSQL16.15 Unix-socket
operation profile first. Reserve cancellation intent, original boundary/call
references and bounded diagnostic results before native effects. Pre-admission
cancellation performs no SQL. During preparation, retain cancellation intent
rather than issuing a packet against an unrelated protocol phase. The prepared
execution path must expose original Execute/Sync flush completion; `_calling`
and a buffered send_EXECUTE alone cannot establish submission.

Cancellation dispatch uses the original BackendKeyData and exact original Unix
peer for one 16-byte CancelRequest. Protect the key and packet from repr, public
observations, diagnostics and receipts. No SQL cancellation function, authenticated
auxiliary session or automatic retry is introduced. A finite transport deadline
covers connection, write, EOF observation and cleanup without reset per stage.

Admit only one cancellation dispatch for the original call. Serialize its
publication against original call completion; a stale/foreign reference never
cancels a newer call. Until both cancel-socket EOF and the entire matching native
call's terminal response are observed, block subsequent statements, operation
rollback/release, resource cleanup and handback. Intermediate ReadyForQuery,
packet write success and EOF do not prove statement cancellation or rollback.
Transport uncertainty retains original custody and quarantines the context.
Original confirmed result/COMMIT remains authoritative.

Compose this with NativeOperationRunner: an active native cancellation must drain
the actual ErrorResponse and ReadyForQuery, then roll back to the original
operation savepoint, release it, restore original settings/resources and return
`cancelled` only after confirmed operation containment. Earlier host writes and
the outer transaction remain under host ownership. Failed containment returns
transaction_unusable; no whole host rollback or callback replay occurs.

Validation must include native long-running cancellation, preserved prior host
writes, reuse only after confirmed containment, cancellation during preparation,
late dispatch after original completion, duplicate/stale/foreign cancellation,
concurrent release/cleanup refusal, timeout/reset/incomplete drain, lost return,
disposal and original successful-result races. Retain actual native observations
without key material. Review source and installed artifact with Astra Ultra,
run applicable module-boundary and installed regression checks, then merge/push
main. Public ReferenceAssembly and full C02 remain open until all required
operation and recovery paths are qualified.

Protocol authority: [PostgreSQL16 cancellation flow](https://www.postgresql.org/docs/16/protocol-flow.html#PROTOCOL-FLOW-CANCELING-REQUESTS)
and [CancelRequest message format](https://www.postgresql.org/docs/16/protocol-message-formats.html#PROTOCOL-MESSAGE-FORMATS-CANCELREQUEST).
The original PostgreSQL16.15 libpq EOF barrier and backend idle-cancel handling
are source qualification inputs, not evidence that Truss already implements them.

Astra's approved linearization: a completion can win against cancellation and
retain a successful native result without ErrorResponse. Require the EOF barrier
only when dispatch was actually reserved; an unsent cancelled operation follows
its original savepoint cleanup. Keep dispatch settlement separate from original
native response facts, so a transport quarantine never erases confirmed C/E/Z.
The runner issues one-use private cancellation handles; foreign or reused handles
refuse before native acquisition. A latched signal during preparation reaches
the original prepared statement or stops ordinary scheduling before submission.
The existing result stream's original flush return is the selected submission
producer, checked against the exact execute resource/session/call/revision.

Native drain policy for this private slice: the original host socket must already
have an exact finite timeout greater than zero and at most two seconds. Selection
refuses an unbounded timeout before SQL; Truss does not change it. Original gate
read/message/byte budgets still apply. This bounds each blocking read, not an
absolute operation wall-clock deadline; that stronger deadline and all other
submission paths remain C02 qualification work. The cancellation socket has its
own absolute two-second dispatch deadline with no per-stage reset. Native complete
call settlement wins late intent; an earlier dispatch can still finish after a
successful native result, and success is retained once both barriers complete.

Iteration16 now implements the private prepared-Execute cancellation path. All
22 native cancellation tests pass independently under Astra Ultra; the separately
installed wheel passes375 tests in49.678 seconds. All55 packaged files match
source/wheel/install, and the module boundary check covers221 imports. See
[iteration16 evidence](evidence/python-contracts-iteration16.json) and the retained
[installed regression log](evidence/python-contracts-iteration16-installed.log).
The primitive feasibility fixture remains separately qualified by its original
script/receipt hashes and startup-version provenance. Original-call absolute
deadline enforcement, other native submission paths and public C02 remain open.
Next: qualify bounded original ingress deadlines and recovery procedure, then
compose the public ReferenceAssembly/adoption surface with truthful readiness.

Security sync at6305b5d7 adds PA02 original pre-entry provenance requirements and
the separately qualified UMF private capture candidate. Runtime bytes are
unchanged. Preserve original trusted-host custody and the invoker elevation guard;
the capture candidate does not qualify production actor mapping or seven semantic
bodies. No supplied actor label or post-elevation tuple substitutes for that owner
protocol in the Python assembly.

### Iteration17: single raw-stream ingress visits

Astra Ultra reviewed the next deadline plan and identified buffered receive and
outbound qualification gaps. This completed slice selects `readinto1` before
gate installation so each accounted ingress visit makes at most one underlying
raw-stream call and preserves already buffered byte order. Socket-layer syscall
retries and connection-owned buffer prefetch remain outside this counter.
Tests use an actual BufferedRWPair and a partial raw stream; native and installed
regressions must also pass before main integration.

Full absolute operation deadlines remain open: retain one original ordinary
clock and a distinct reserved settlement clock, qualify buffered writes/flush
and admission/result checkpoints, and restore exact original socket timeout
before handback. A genuine SocketIO timeout poisons its buffered wrapper;
incomplete original calls require quarantine, not a reconstructed stream or
optimistic drain. Cleanup permits alone cannot choose deadline phase because
ordinary baseline probes already use reserved close operations. No public C02
or ReferenceAssembly readiness is claimed by this ingress correction.

Iteration17 passes380 separately installed tests in49.478 seconds; all55
installed package files match source. Astra independently passes15 focused
checks, including the original native success/failure/success workflow. Python
module boundaries pass222 imports. See [receipt](evidence/python-contracts-iteration17.json)
and [installed log](evidence/python-contracts-iteration17-installed.log).

Security main15c8fcf9 was fast-forwarded before iteration17 integration. Its
39 native observations and eight replayed formulas qualify the isolated
authority-row primitive; ontology resolution, admitted subject mapping and
final publication custody remain open. Runtime source is unchanged, and no
protected entry or actor mapping is adopted from this candidate.

### Iteration18: original operation deadline scheduling custody

Extend the original private runner with a retained monotonic start captured
before parameter admission, a fixed ordinary cutoff, and one reserved settlement
cutoff. Every original native scheduling decision checks the same record, even
when baseline probes close resources with cleanup permits. Permit selection
does not change time phase. Stop expired ordinary admission; only a fully settled
original call may enter the operation-savepoint containment procedure. Preserve
original error and native facts if recovery exceeds its separate allowance.

Validate no-SQL pre-acquisition expiry, expired prepared execution with original
savepoint restoration and prior host work, fixed phase transitions, restoration
overrun quarantine and successful operation regressions. Astra reviews the plan,
implementation and installed evidence before main integration. This scheduling
prerequisite must not claim bounded pending I/O: original read timeout, buffered
write/flush accounting, transport timeout restoration and full wall-clock C02
qualification remain required follow-on work. No timer, callback retry or
replacement connection establishes native termination.

Iteration18 distinguishes expiry at the inner settled-statement checkpoint,
where the original live savepoint supports reserved containment, from expiry
while entering or performing normal success restoration. The latter conservatively
quarantines even if a savepoint remains live; it does not claim every healthy
pre-release expiry is contained. Completion seals its original clock basis
before publication; lost replies reconcile that record without a new deadline
or fresh SQL. Deadline admission runs once before mutating preflight, while
repeat resource-reservation validation retains structural checks.

Iteration18 passes392 separately installed tests in54.937 seconds. All56
package files match original source, retained wheel and installation; all49
test modules remain unchanged during the final run. Python module boundaries
pass224 imports. See [receipt](evidence/python-contracts-iteration18.json) and
[installed regression log](evidence/python-contracts-iteration18-installed.log).
Next qualify original pending ingress and outbound deadline enforcement, without
changing confirmed native facts or reconstructing a timed-out buffered stream.

Astra Ultra independently passes all12 deadline tests in3.671 seconds and
approves the integrated source and plan, including the conservative restoration
edge. Final artifact verification remains separate from those focused checks.

### Iteration19: original pending ingress deadline

Compose the original operation clock into each accounted `readinto1` visit.
Require the original exact AF_UNIX socket and BufferedRWPair selected under
cooperative host custody, capture the actual host socket timeout and preserve
a stricter finite value. Clamp only that original read to remaining ordinary
or settlement time, restore the exact original timeout in `finally`, and check
the same clock after the read. No cleanup permit changes the clock phase.

Timeout, partial/incomplete frame, restoration failure or changed original
transport quarantines the original operation. Preserve its call/token/context
and native facts; never rebuild the poisoned SocketIO wrapper, reconnect,
repeat a query or claim savepoint rollback from a timer. Successful reads must
restore timeout before buffered writes. Independently test actual pending
PostgreSQL execution, existing shorter host limits, success restoration and
failure custody. Astra Ultra reviews plan, source and installed evidence.
Buffered write/flush and full operation wall-clock qualification remain open;
this is the original receive enforcement path required by that larger profile.

Constructor provenance remains trusted: pg8000's untouched original connection
constructor creates the BufferedRWPair from its socket. Exact type and attachment
pins detect later substitution; they cannot independently prove pre-attachment
stream/socket correspondence, especially for injected `sock` construction.
The original cooperative host profile remains mandatory. The iteration18 real
slow-call fixture now correctly reaches pending ingress timeout quarantine,
rather than waiting past the deadline and claiming post-drain containment.

Security main7f29ae37 was fast-forwarded during iteration19. Its retained
76-observation raw ontology candidate and seven formal formulas qualify only
synthetic read admission. Production authenticated subject/owner artifact, typed
graph closure and final publication/drain remain open. The handoff changes no
Truss runtime or grants; Python original host custody remains mandatory.

Iteration19 passes406 separately installed tests in62.160 seconds. All57
package files and distribution metadata match the original source, retained
wheel and installation; all50 test-module hashes remain unchanged. The Python
module checker passes231 imports. Astra independently passes26 refined ingress
and deadline tests in5.378 seconds, after47 earlier composition checks.
See [receipt](evidence/python-contracts-iteration19.json) and
[installed log](evidence/python-contracts-iteration19-installed.log).
Next qualify original outbound write/flush deadline enforcement, then compose
public adoption/readiness only for the supported original executor profile.

### Iteration20: original outbound deadline and submission ledger

Select a direct original AF_UNIX `sendall` sink under the existing shared
transport timeout/deadline custody. Preserve exact protocol bytes and order,
retain a bounded original write record before each send, and quarantine any
partial/failed send without retry. The original BufferedRWPair reader remains
unchanged. Require a source-qualified successful final original driver return
with current call/revision custody at gate installation to establish the empty
writer baseline. A generic Ready or native-error complete call is insufficient:
execute_unnamed may have queued Bind bytes while reading an intermediate error.
Never flush unknown leftovers to initialize this sink. Untouched constructor,
selected driver methods and cooperative exclusion of raw writes remain required.

Use the same original clock and saved host timeout for sends and reads; restore
the exact timeout in finally, including setter/send reply loss. The flush method
is an original publication barrier after confirmed writes, not a new buffered
I/O loop. Cancellation stays latched until the exact Execute+Sync sequence is
confirmed; bytes can reach PostgreSQL before that barrier, so pre-barrier failure
is unknown rather than unsent. Requalify these races, original EOF/drain custody,
actual socket backpressure, byte ordering, bounded ledger and host reuse with
Astra Ultra. Full public C02 and protected capability readiness remain open.

[CPython3.11 sendall](https://docs.python.org/3.11/library/socket.html#socket.socket.sendall)
uses one total timeout across its internal partial sends. The selected source
version is3.11.17; no TLS, arbitrary socket injection or raw-alias profile is
qualified by this work.

Security mainfadc4890/e06dbeda was fast-forwarded before iteration20 installation
checks. Same-policy graph/raw parity and protected graph capture add retained
53/135-observation experimental evidence; no runtime/grant changes are adopted.
Production subject/owner artifacts, admitted mutation/callable closure, four-family
semantic bodies and final publication/drain remain open. Original exclusive host
custody and the invoker gate remain Python assembly prerequisites.

Iteration20 source/plan passed Astra Ultra review. The retained installed wheel
passed416 tests in53.020s against PostgreSQL16.15; all58 package files match
source/wheel/installation, four distribution metadata files match, and the51
test-module snapshot remained unchanged. Python module boundaries passed235 imports.
The evidence receipt retains exact hashes and the private-profile limitations.

### Iteration21: bounded original host controls and adoption

Astra Ultra reviewed the next prerequisite: the control/adoption ledger must
consume the same original monotonic clock and socket deadline as text execution.
Public Executor/ReferenceAssembly remain unexported: arbitrary Statement
execution, engine-owned with_transaction and protected capability bodies are
not implemented. This iteration qualifies the existing caller-owned control path.

Start one deadline at NativeHostSession invocation entry, before native acquisition.
Carry it through admission, bounded direct sends/reads, Python publication and
sealed original handback. Refuse expiry at the pre-acquisition checkpoint without SQL; a possibly
submitted or partially read call keeps its original ledger/token/context and
unknown outcome. Preserve independently known commit/rollback facts separately
from an unconfirmed handback. No retry, drain reconstruction or new recovery clock.

Require an explicit boundary-captured successful host setup call at the current
revision with final I/T before attaching a control gate. That setup call is
host-owned and outside this iteration's bounded-control claim. Revision zero,
last_call=None and idle status do not establish an untouched constructor or empty
writer: pg8000 resets its startup status to None. Never issue setup SQL implicitly
or flush unknown bytes. Qualify error-to-rollback only from retained original
control send/barrier and native completion evidence, not generic error Ready.

Verify the full existing control/recovery suites, actual blocked native control
with socket timeout, timeout restoration, expired pre-effect refusal, adoption
publication/handback expiry and retained known end facts. Astra reviews source and
installed wheel evidence before task-only main commit/push.

Retained error-to-rollback basis is limited to a sealed, released original control
ledger with exact current native completion and fully settled Q send barrier.
Ordinary boundary.run error has no such witness and refuses without retry/flush.
The host can explicitly settle through its tracker; bounded ordinary host-error
recovery remains a required public-adapter gate, not a supported claim here.

Expiry after acquisition but before the first native submission conservatively
retains the original attached ledger/token and closes admission: attachment or
Python publication may already exist. It never invents native transaction work,
returns a released no-effect result or resets the original clock.

Security main d79d806e adds authenticated graph caller147-observation evidence
and a14-observation original owner-binding audit. It changes only the handoff
document; no runtime/grant/source changes enter this wheel. Explicit owner storage
choices, production subject/current cut, complete callable/mutation closure,
semantic bodies and final publication/drain remain open. Do not manufacture
primary-key/relationship selections from unspecified logical metadata.

Astra Ultra approved iteration21 source/plan; independently11 native deadline
and recovery tests passed6.136s, earlier51 composed checks passed20.240s.
Next public-adapter gates: original simple host-error flush witness, Q cancellation
and original adoption latch, host-issued savepoint namespace and nonrewinding
uint64 counters, cumulative/cleanup resource profile, then precise public mapping.

Definitive iteration21 installed wheel passed427 tests in57.686s on PostgreSQL16.15.
All58 package payloads, four metadata files and52 test modules match the retained
source/wheel/install snapshot; module boundaries pass238 imports. The evidence
receipt pins exact bytes and retains the unfinished public-profile obligations.

### Iteration22: original simple host-error recovery

Astra Ultra approved qualifying only the actual pg8000 native simple binding:
exact str SQL, kwargs limited to stream/types, stream None. Native types is ignored
on this path and must not be traversed. Before effects, under the existing native
lock, pin original bound run/execute_simple/send_QUERY/_send_message/handle_messages,
canonical C/E/Z handlers and dispatch, and original stream/socket. Retain a nominal
immutable descriptor for the exact original revision/call; generic callbacks and
parameterized/streamed calls receive none.

The pinned execute_simple sends Q, flushes once and then handles responses with
no later writes. An exact complete original native Error+Ready E/I on that path
therefore witnesses the old writer's completed flush. Admit it only while descriptor,
native call, current revision/status and original transport still correspond;
never infer this from generic Error+Ready or flush queued bytes to discover state.
Host SQL itself remains trusted host work outside bounded-control qualification.

Verify division/uniqueness errors to bounded rollback, savepoint recovery preserving
prior host writes, stream=None/types-only selection without traversal, parameterized Parse-error exclusion plus a fault-fixture
genuine Describe error after successful Parse with queued Bind refusal, and missing/stale/foreign witness refusal
without SQL. Public adoption cancellation, savepoint/resource profiles and protected
capabilities remain open. Astra reviews completed source and installed evidence
before task-only main commit/push.

Source review closed an arbitrary-callback labeling bypass: a boolean cannot issue
simple-path evidence. A nominal immutable invocation packet carries exact SQL and
ignored types; inside the guard, the boundary captures the selected original bound
run and invokes that packet itself, independently of any callback argument. A valid
packet never invokes the callback. One-write original call association prevents a
structurally copied NativeCall from borrowing the descriptor. Nine native witness
tests cover both adversarial invocation paths and exact native recovery.

Concurrent main ac94538b corrects UMF host staging: optional primary markers
project absence/false to non-primary while preserving original source bytes.
Its owner-backed16-test55-assertion evidence uses mocked native staging and
does not qualify accepted publication. This TypeScript change and handoff are
preserved; no Python wheel source/test bytes change and no TS/native profile
support is inferred from the Python suite.

Astra Ultra approved iteration22 source/plan; independent38 composed native tests
passed23.127s. Definitive installed wheel passed436 tests in73.581s against
PostgreSQL16.15. All58 package files/four metadata files and53 test modules
match the original retained source/wheel/install snapshot; boundaries pass242
imports. The receipt records exact hashes and preserves the private-profile gates.

### Iteration23: persistent original adoption cancellation

Astra Ultra selected a distinct executor-issued AdoptionCancellation signal.
Bind it to exact preallocated custody before native observation, preserve a monotone
latch, and forward requests outside its lock to the exact active one-use Execute
child. A finished child does not clear context cancellation or rewrite its result.
Existing standalone per-run cancellation remains separate private qualification.

Pre-cancel before claim reservation returns cancelled with no SQL. After claim
reservation, cancellation before each observation/final publication wins a terminal
cancelled claim with no handle/refund when original state is clean. An already
active bounded Q settles; no Q cancel support is inferred. Unknown native state
retains unusable custody. Exact successful publication first preserves its original
Ok; a later request closes that context's new admission. No duplicate adoption or
disposal can erase the latch. New runner/registry/native-session/savepoint admission
refuses while exact previously issued savepoint cleanup and host-owned settlement
remain available. Unresolved native outcomes take precedence over cancellation.

Qualify before-observation and publication races, original active Execute cancel
with preserved prior host writes, late request, child races, native dispatch failure
and duplicate-generation refusal. The existing original cancel channel profile
requires a finite host socket timeout greater than zero and at most2s; unsupported
active cancel must refuse, never silently downgrade. Public Q/adoption cancellation
profile and complete external capabilities remain separate unimplemented gates.

Astra source review required preserving acquired binding reconciliation after a
latch, validating exact cleanup membership/native liveness before observation,
and retaining unusable native custody ahead of cancellation classification.
Ordinary operation cancellation is checked only at its original native admission
checkpoint, not again after resource preflight mutates custody. A distinct original
unsent-cancellation refusal returns cancelled only after confirmed containment.

SAVEPOINT has an explicit signal-lock admission point retaining its exact original
custody on the preallocated publication; release the lock before I/O. Cancellation
before that point refuses without a SAVEPOINT. Admission first permits that bounded
Q to settle and closes the next ordinary admission. Exact rollback/release cleanup
remains available. This does not introduce active Q cancellation support.

Concurrent main ad23e08b/d42e93ce records genuine owner/native provisional catalog
staging and proposed ontology association bindings. Installer-only staging remains
unpublished and synthetic admission; ontology roles cannot invent physical core
relationships. These owner/security gates remain prerequisites of public Python
catalog and protected operation capabilities.

Cancellation during setup after native binding and before the operation savepoint
exists conservatively retains transaction_unusable custody. This iteration does
not prove no-effect handback for those windows. A native regression checks a
post-binding request submits no baseline probe, retains the exact guard/session
and quarantines future calls. This limitation is separate from confirmed Execute
containment and remains a prerequisite of public adapter exposure.

Original outcome classification precedes the cancellation shortcut: quarantined
or otherwise unresolved custody remains transaction_unusable; a confirmed ended
or replaced native generation and disposed ordinary executor admission return
invalid_transaction with no SQL. Pure exact native liveness is checked before the
runner/session/direct-executor latch and registry preparation, outside registry
locks. Native regressions cover host commit, rollback, replacement generation and
disposal while retaining original cancellation/custody.

Concurrent main fe8a6705 adds the separately Astra-reviewed private association
source-correspondence component and39 tests. Preserve its exact original bytes,
fixtures and explicit module map; rebuild the combined wheel rather than promoting
its earlier source-tree evidence into installed-package qualification. Its frozen
mapping remains declaration correspondence, not authenticated/native authority or
accepted publication. This integration does not change the reviewed cancellation
paths or public exports.

Astra Ultra approved the final private source/plan; independent83 tests passed
13.919s. The definitive integrated installed wheel passed497 tests in65.603s
against PostgreSQL16.15. Exact60 package files, four distribution metadata files,
55 test modules, two original owner fixtures and the251-import checker remained
unchanged through the run. The retained receipt/log record the combined main
snapshot and keep public execution/security/cancellation gates explicit.

### Iteration24: original fresh-connection bootstrap

PY-C02 needs a usable fresh-connection path. Current native fixtures use an
uncaptured host SELECT before boundary attachment because pg8000 resets startup
status to None. That historical fixture cannot establish factory startup custody.
Astra Ultra selected private factory-owned bootstrap: create an unexposed exact
original pg8000 connection, retain original constructor/source and resource
custody, and issue only a one-use writer-empty witness after successful original
startup. It is never an idle witness or retrofit for an existing host connection.

The witness permits initial boundary attachment at status None and one fixed
bounded SHOW transaction_isolation using original accounted control framing,
direct outbound send and ingress/deadline custody. Require actual complete SHOW
and ReadyForQuery with final I, original settled send barrier and confirmed gate
restoration/release before returning the boundary or attaching a native tracker.
Never synthesize NativeCall, idle status or original constructor evidence. Never
flush unknown writer bytes to establish a baseline. Existing externally supplied
connections retain their separately qualified provenance requirement.

Constructor startup/authentication precedes the accounted gate: a finite socket
timeout is not whole-startup work/byte/deadline qualification or constructor
failure cleanup proof. Retain the factory-owned original connection/resources
before initialization, close/discard only those resources on failure without
submitting queued unknown writer bytes, and retain uncertain cleanup for explicit
owner recovery. No retry, implicit host transaction, pool or protected authority.

Native gates cover fresh pgserver connection through captured bootstrap, real
host baseline, begin/adoption, original text execution and host commit; foreign,
replayed/copied witness and constructor/driver mutation refusal; bounded SHOW
error/timeout/capture failure; original setup/cleanup and publication faults.
Record original source pins, safe bounded diagnostic references and immutable
installed-wheel evidence. This remains private until complete constructor,
active-Q cancellation, public C02 and protected installation exits are proven.

Astra's source review selects an adapted original constructor path: install an
exact factory-only instance close hook before calling the pinned constructor,
since its own startup exception handler otherwise emits TERMINATE/flush and drops
resource references. Restore original close on successful construction. Retain
available original socket/stream before shutdown, attempt both closures, and record
actual closure observations/failures. Never erase uncertain custody or apply this
creation cleanup after exposing the connection to its host.

Use closed exact-primitive AF_UNIX options with SSL False and finite timeout;
exclude supplied sockets, startup parameters, replication and callbacks. Start one
original deadline before construction and preserve it through SHOW. Startup/auth
parsing and I/O are still outside accounted ingress and no absolute startup bound
is claimed. Specialize the existing ledger to one exact fixed SHOW, retaining and
consuming startup witness before submission. Test original constructor close hook,
restoration on success, shutdown/stream/socket faults and publication loss without
issuing a second SHOW. Astra Ultra approved this private plan; public C02 remains
open.

Astra's adversarial review rejected caller-configured issuer registration. The
lower startup module now owns the fixed original constructor and retained record
registry; the upper factory only composes its original records. No generic
issuer/type/source binding or caller-supplied connection is accepted. Bound input
character length before strict UTF-8 encoding and reject startup NUL injection.
Pin selected callable symbols, including core.Context, before construction and
again after accounted SHOW restoration.

When original shutdown is unconfirmed, retain both original socket and buffered
writer without buffered close or flush. Explicit owner recovery uses those same
handles; it never reissues SHOW. Retain monotone cleanup failure facts, including
BaseException, before propagation. After exposure only the host owns lifetime.

Final retained iteration24 wheel passed515 tests in78.559s on CPython3.11.17,
pg8000 1.31.5 and corrected pgserver0.1.4+truss.pg16.15/PostgreSQL16.15.
The62 package files exactly match source, wheel and isolated installation; the
56 test modules, two owner fixtures, installed metadata and268-import checker
remained unchanged through the run. Retained receipt/log:
`evidence/python-contracts-iteration24.json` and
`evidence/python-contracts-iteration24-installed.log`. The completed private
workflow is original fresh connection, captured SHOW, host resource baseline,
begin/adoption, exact text query and host commit. Public and protected gates stay
open. The concurrent owner interpretation handoff0cf98abf is incorporated.

Astra Ultra approved the final source, plan and retained installed artifact, with
45 independent composed checks and all18 installed bootstrap cases passing.
No blocker remains within this private scope; constructor/startup accounting,
active Q cancellation, public C02 and protected authority gates remain open.

### Iteration25: public original UMF preparation

The consumer-facing priority is install → register original UMF → apply → read,
through public Python exports and real PostgreSQL effects. Previous private driver
checks do not establish those operations. Active simple-query cancellation is
unfinished and deferred; its unqualified prototype is archived outside this
checkout, and no prototype source is promoted into this iteration.

Expose `CatalogDocument` and `prepare_acceptance` from the Python package. Reuse
the original committed UMF producer and existing Truss AcceptanceInput inspector,
transition correspondence and declaration extraction. Package the original owner
bundle, original schema, bridge and runtime dependencies in the installed wheel;
seal their bytes in the release manifest. Require the declared Bun runtime rather
than reimplementing UMF semantics in Python.

The caller supplies exact document bytes, document-qualified identities/revisions
and explicit acceptance configuration. Preserve exact originals in digest-bound
artifact carriers and return original owner observations and declaration evidence.
Root installation/policy choices remain unverified. Preparation does not create
accepted IDs, a report/head, readiness or database effects. Its output feeds the
existing catalog acceptance pipeline; it is not a second catalog protocol.

Astra Ultra approved this independently useful C03 plan. Fifteen source tests
cover two documents sharing module/element names, exact source artifacts,
reversible 0.7 interpretation, invalid source/UTF-8/configuration, duplicate or
mismatched identities, missing runtime and altered producer assets. Tests also retain unknown extensions, refuse unsafe native numeric lexemes,
bound stdout/stderr during capture, reap timed-out children, and reject altered
configuration/document/profile correspondence and malformed responses. Astra
Ultra independently passed all15 tests and approved source after correcting
original diagnostic retention, exact numeric-free wire admission and capture
bounds. The executable README consumer example passes from the frozen installed
wheel outside the checkout. The fixed installed wheel passed530 tests in85.333s on CPython3.11.17,
Bun1.4.2, pg8000 1.31.5 and corrected pgserver/PostgreSQL16.15. All77
package files are exact across source, wheel and installation; test membership
and bytes remained unchanged. Retained evidence: `evidence/python-contracts-iteration25.json`
and `evidence/python-contracts-iteration25-installed.log`. Astra Ultra approved source, plan and final artifact; independently verified all
77package files,57test-module hashes, durable log and wheel hash, executed the
README consumer example under Python-I outside the checkout, and passed all15
installed preparation tests in4.045s. Approval is preparation-only.

Concurrent main changes through f432bf59 are integrated, including immutable
original binding archives and consistent omitted primary-key markers. A mixed
source/rebuild test run is excluded from qualification; its preparation failures
occurred while sealed assets changed. Qualify only the frozen final artifact.

Next implement actual native catalog acceptance and installation integration,
including original authority/origin, mandatory selected guard/finalizer routines,
atomic acceptance and accepted report/view. Do not turn unfinished unrelated
capabilities into blockers for independently qualified endpoints; do not bypass
protected acceptance gates to make a staging example look like registration.
The complete Python external-interface goal remains open.

### Iteration26: complete catalog acceptance path

The first real Python workflow remains installation → original UMF preparation →
`catalog.accept_in_transaction` → grouped object creation → object-ID lookup.
Use actual accepted native IDs and preserve outer transaction ownership. Source
staging success is not registration, and a full report must precede head
publication. The unconditional operation commit barrier stays until complete
independent native finalization is implemented and tested.

Current source gap: `collectCatalogReportPreparation` gathers original new-only
basis and counts, while `stageNewCatalogCohort` stages definitions. Neither
publishes an accepted report/head. The audit's acceptance exit sequence requires
actual installed root/report profile interpretation, complete originalExecution,
UMF/assertion meaning and enforcement inventory, original rebind/index effects,
complete extension disclosure, all seventeen report fields and independent native
comparison. The seven semantic routines have selected boundaries but no bodies;
capacity closeout alone is explicitly not their replacement.

The first executable semantic slice is `edge_limit_verify_current_scope() -> void`
under explicit private native test custody. It has no downstream validator
dependency and implements the selected complete final definition/edge/marker
multiset algorithm (EL01–EL05). The catalog-only native-test profile derives its whole scope internally from
`rel_def UNION edge.rel_type_id UNION edge_limit.rel_type_id` under the already-held
exclusive head and actual unique unfinished catalog operation. Include orphan
relationships so missing definitions refuse. There is no new opaque effect-byte
grammar, caller ID list or scope parameter; existing effect bytes do not yet have
an EL grammar. Affected-scope optimization and commit-union dispatch remain later
composition, not claims of this whole-catalog body.
The native body refuses incomplete/foreign scope, invalid bounds or any missing,
extra, duplicate, wrong-side, wrong-endpoint, wrong-relationship or wrong-edge
marker. Test self edges, both maximum-one orientations, retired definitions,
wrong-relationship markers selected through their canonical edge, stale custody,
savepoint rollback and repeated checking. Keep ordinary-role invocation denied.

Native semantic bodies may be implemented and qualified under explicit test
custody before the protected issuer is complete. This does not confer ordinary
role authority, install the whole profile or replace the unconditional commit
barrier. Integrated public acceptance still requires every selected body and the
complete protected invocation/installation/resource/authority proof. Astra Ultra approved this first semantic body plan and its explicit native test
custody/negative controls before implementation.

Integrated implementation sequence for the acceptance path:

1. Admit one coherent actual installed layout/security/driver/resource tuple and
   protected original caller/context source. Bind installed roles, callable bodies,
   effective privileges and original profile artifacts; caller-selected bytes from
   preparation cannot authorize effects. Keep issuer/authentication semantics owned
   by the existing security boundary. Implement missing Truss capture/custody
   composition without a competing ACL resolver or direct ordinary-role writes.
2. Complete the original report producer using existing pinned UMF observations,
   source identity inventories and actual staged/native effects. Every missing
   report field needs its original producer; unknown assertions retain explicit
   unenforced/unsupported evidence. New-only input cannot manufacture empty
   rebind/index/extension inventories. Present bindings require the registered
   physical interpretation currently absent; preserve their explicit refusal.
3. Implement selected native semantic observation, limit and finalization bodies,
   including complete transaction contributor/touch coverage, settled reservations,
   independent journal/feed union and repeated early-check safety. Compose the
   existing capacity and original row-image components rather than treating their
   individual successes as complete commit authority. Map exact installed routines,
   owners/dependencies/ACLs and trigger events in both directions.
4. Compare full retained report/source/native effect membership, insert immutable
   report bytes once, publish and verify head last under the same native operation.
   Report and head writes themselves advance semantic generation. Verify the actual
   resulting generation and full obligations after those writes before publishing
   final phase/result; an earlier seal cannot authorize them. Return only pending
   accepted results until the host confirms commit. Preserve
   unknown settlement and one-refusal/no-internal-retry behavior.
5. Export the actual Python capability through ReferenceAssembly, using original
   prepared input and qualified adopted host transactions. Test ordinary-person
   acceptance, complete report/readback, host rollback and commit, stale authority,
   copied context, direct helper denial, report/head/finalizer fault and lost commit
   acknowledgement. Then add one actual grouped object creation and exact lookup.

Review the concrete first native implementation slice with Astra Ultra before
source edits. Work stays on main and incorporates committed security changes.
The security chat currently carries explicit association storage values and source
pointers; it does not yet establish registered physical interpretation or protected
catalog publication. This work must account for those outputs without adopting
unfinished APIs. Full migration, broader Weft shapes and feed consumers do not
block independently qualified first capabilities; mandatory selected integrity and
authority gates still apply to each capability being published.

The installed runtime, original caller, exact IDs/report and native durable effects
are decisive evidence. More driver-only tests or an inert capability factory do
not satisfy this iteration. Original shared corpus/native interchange and the
remaining external-interface scope stay required goal exits.

The first semantic body is implemented under its private native-test profile.
Exact type/nullability/character-width checks precede identity casts; signed int4
relationship identities are preserved, and side comparisons explicitly use C.
The complete scope includes orphan IDs, identity duplication, retirement and all
marker occurrences; required-key conflicts are checked independently. Native
readback matches the loaded body and selected function attributes/ordinary grant
denial. The latest targeted run attempted21 tests:20 passed and1 skipped because
this corrected PostgreSQL16.15 build lacks ICU. All eleven authored vectors are
covered; corruption probes explicitly remove constraints only inside rolled-back
administrative setup. Resource boundaries and exclusive/shared-head waiters pass.
Retained receipt/log: `evidence/python-contracts-iteration26.json` and
`evidence/python-contracts-iteration26-native.log`. Full frozen-source regression attempted555 tests:554 passed and1 ICU probe
skipped in93.698s; all119 source pins remained unchanged. The full log is retained
in `evidence/python-contracts-iteration26-full.log`. Astra Ultra approved the source, plan and retained evidence. After integrating
security main375a6004, its five additional public preparation tests passed in2.316s;
these are separate from the frozen555-test membership. The unpackaged SQL is proven by actual
native load/readback/tests; Python wheel membership is not evidence of its install.

### Python native catalog staging iteration27

Astra Ultra approved porting the existing original `catalog-new-stage.ts` path
into Python and requiring independent verification before local savepoint release.
`_catalog_staging.stage_new_catalog` now consumes an original, unchanged public
UMF preparation and the caller's trusted native-style connection. Original
operation admission and host connection coordination remain external. It stages
complete documents, Records, Fields, keys and relationships with actual native IDs,
then verifies retained prestate, complete native inventories, document/source
correspondence, independent counts, every property storage home and whole-catalog
relationship marker correspondence. The immutable result is explicitly provisional.

The selected storage interpretation is the existing
`ADR-002-D4-absent-binding-json-default` route: every Field uses JSON only when the
binding is explicitly absent. Present bindings and transforms refuse before SQL;
this slice does not interpret their physical/security meaning. Original origin
UTF-8 is passed unchanged under an explicit strict numeric-free JSON profile;
numeric origin content, duplicate members and nonfinite values refuse. This
profile does not claim exact numeric origin-extension support.

Original preparation recognition retains weak instance identity and exact immutable
snapshots, validating exact nested carrier types before comparison. Copies,
modified source/declaration/archive/observation bytes, altered provenance and
custom-equality bytes subclasses cannot borrow the producer's provenance. This
recognition is not native operation or person authority.

Native tests stage the consumer's original five-Record, nine-Field, five-key core
and a separate two-Record/key/relationship cohort. Independent late home-readback
failure removes the entire new cohort and restores operation generation/phase,
while preserving earlier host work. Host rollback removes successful provisional
staging. The unconditional commit barrier still refuses commit; no report/head,
accepted IDs, installation readiness or public registration is published. Cleanup
failure retains both the primary failure and cleanup failure and reports containment
unconfirmed. The frozen full regression attempted572 tests:571 passed and1 ICU
probe skipped in122.802s. After final builtin/type qualification and correction
of its exact late-fault test seam, a fresh installed wheel passes all12 staging
tests in15.369s and all15 preparation tests in5.561s. All78 packaged files match
the final source and installed bytes. The receipt retains both source snapshots
and explicitly scopes the earlier full run versus the final installed delta.
Astra Ultra approved the final source, plan and retained artifacts, verified
all170 final pins and78 packaged files, and independently passed the12 installed
staging tests in12.907s. The full external interface remains unfinished.

After the reviewed wheel snapshot, security main7ab05500 was integrated without
overlapping source changes. All50 affected security association tests passed
in0.023s; their log and source pins are retained separately in iteration27.
The earlier full and installed-wheel evidence does not include this later delta.


### Iteration28: original catalog report integration

Continue the accepted-catalog path by composing original owner report producers
with real staged native IDs under one host savepoint. Preserve existing document
carriers and map six native counts to their declared report names. Bound optional
report extraction without rejecting valid original preparation. The native fresh
empty-graph profile includes journal, requires Read Committed, excludes raw writers
with SHARE NOWAIT, and refuses erased prior graph writes or uncovered physical
scope. Full native value readback prevents generation reuse from admitting stale
report evidence. Extension retention remains partial and is explicitly unqualified.

Astra Ultra reviewed the plan and found preparation capacity, count naming and
snapshot isolation defects. Those corrections have targeted evidence:16 preparation,
12 staging and10 report tests pass. The frozen pre-correction full regression attempted590 tests:589 passed and1 ICU
probe skipped in206.926s. Final output-limit/newline and TRUNCATE lock corrections
are separately qualified by40 installed-wheel tests (17 preparation,12 staging,
11 report) passing in24.852s. All79 packaged files match source/wheel/install.
Astra Ultra approved final source, plan and artifacts and independently passed
the two final regressions in4.096s. This iteration publishes no accepted report/head or ordinary-role grant;
protected finalization and public registration remain next deliverables toward
install → register → apply → read, followed by the rest of the full interface.
