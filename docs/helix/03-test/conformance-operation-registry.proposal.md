# Conformance operation registry — authored method inventory

Companion to [case grammar](conformance-case-grammar.proposal.md). These entries bind existing declarations; they introduce no public methods. Status: proposed inventory, not a complete executable registry. Exact input/result schemas, identity paths, original profiles and semantic observation scope must be registered before execution.

## Capability carrier closeout — 2026-10-09

All twenty-two capability entries in the following table now have proposed
return-carrier mappings using existing payloads and the specialized
compositions described below. This closes the return-carrier authoring gap;
it does not close complete operation registration or administrative/executor
inventory. Catalog-view available/unavailable now has its explicit business
wrapper and exact outer Outcome member alongside its existing request schema.

The [fresh 153-schema receipt](../04-build/evidence/design-audit/schema-inventory-capability-wires-2026-10-09.json)
records strict combined registration/reference compilation with zero errors.
The seven capability composition checks pass 55 generic, 25 import, 14 catalog,
24 group, 19 mutation, 24 retained-history and 8 direct-lookup controls: 169
enumerated shape/layering witnesses. Earlier receipts retain their original
source hashes and scopes. This run does not establish complete inner-result
semantics, native effects, authority or implementation availability.

The next registry outputs are exact argument envelopes for methods with
separate origin/request/options arguments, original handle/verified-application
issuance, selected method/profile pins, complete identity paths and independent
observation procedures. Then freeze full cases and perform the contract-only
independent implementer review. Administrative/lifecycle/configuration methods
retain their separate missing carrier and procedure inventory. Nothing in this
closeout authorizes reducing the required corpus or replacing the protected
runtime with fixture results.

| Family | Existing capability method | Original declaration | Transaction and comparison boundary |
| --- | --- | --- | --- |
| catalog | acceptInTransaction | truss-catalog-capability-v0.1 | Original supplied transaction; complete acceptance/report/head state, pending until confirmed termination |
| catalog | report | truss-catalog-capability-v0.1 | Supplied read context; complete immutable original accepted report |
| mutation | applyInTransaction | truss-mutation-capability-v0.1 | Supplied transaction; exact single-write result plus full applicable state/journal |
| group | applyInTransaction, request state none | truss-group-capability-v0.1 | No receipt/replay outcomes; complete ordered results and one atomic operation scope |
| group replay | applyInTransaction, request state present | truss-group-capability-v0.1 | Original request/namespace authority, full semantic input and receipt result; replay may observe already committed original work |
| import | runBatches | truss-import-capability-v0.1 | Explicit owned batches; complete report retains prior committed progress on interruption |
| import | applyInTransaction | truss-import-capability-v0.1 | Supplied scope; original per-record savepoint outcomes remain pending |
| direct read | lookup | truss-direct-read-capability-v0.1 | Supplied context; complete exact object/key/edge lookup and non-disclosure |
| direct read | page | truss-direct-read-capability-v0.1 | Supplied context; complete n+1 observation and exclusive continuation |
| catalog view | catalogView | truss-direct-read-capability-v0.1 | One consistent definition context; full inventory versus declared projection |
| traversal | traverse | truss-direct-read-capability-v0.1 | Original snapshot/stage/cumulative work; human output interpretation remains pending |
| traversal | resumeTraversal | truss-direct-read-capability-v0.1 | Original stage and expected work version; no resource reset |
| traversal | nextTraversalPage | truss-direct-read-capability-v0.1 | Sealed original membership and current publication authority |
| traversal | releaseTraversal | truss-direct-read-capability-v0.1 | Retained original cleanup facade; no transaction argument or graph operation |
| history | pageJournal | truss-history-capability-v0.1 | Supplied context; bounded raw journal page, not complete reconstruction/feed |
| history | reconstruct | truss-history-capability-v0.1 | Original definition/baseline/sibling horizon and exact logical version |
| history | historicalSource | truss-history-capability-v0.1 | Retained original creation/owner context with current authority |
| compiled execution | executeInTransaction | truss-compiled-execution-capability-v0.1 | Exact registered Weft artifact/bridge and supplied context; independent logical result |
| feed v0.2 | discoverNext | truss-feed-key-transition-v0.2, FeedCapabilityV02 | Complete original manifest boundary under coherent safe watermark |
| feed v0.2 | readFragment | truss-feed-key-transition-v0.2, FeedCapabilityV02 | Original ordinal fragment and prerequisites, not invented journal positions |
| feed v0.2 | observeFreshness | truss-feed-key-transition-v0.2, FeedCapabilityV02 | Complete v0.2 source boundary, fact-clock and publishable/held/unavailable states |
| feed v0.2 | acknowledgeInTransaction | truss-feed-key-transition-v0.2, FeedCapabilityV02 | Original verified application; pending source checkpoint until supplied transaction settles |

Declaration files live under `docs/helix/02-design/contracts/bindings/`, with the basename in column three plus `.d.ts`. Group overload accepting unresolved request union is a typing convenience, not a third behavior. Case admission must narrow request-none/present before deciding required receipt observations.

## Feed construction boundary

The existing ReferenceAssembly.feed accessor returns historical FeedCapability v0.1. It cannot supply FeedCapabilityV02 by renaming a profile or structural coercion. Current complete key-transition/freshness cases explicitly construct createFeedCapabilityV02 with the existing assembly, selected feed capability and admitted FeedProofVerifierRegistrationV02. Construction is inert and does not start feed work. Original registration, proof/application/checkpoint/resource/native procedures still require their independent admission.

Keep legacy v0.1 cases version-scoped if independently selected. They cannot satisfy a v0.2 required case by losing its complete application/boundary semantics. An unavailable v0.2 constructor/profile blocks that case/full selected qualification rather than falling back to assembly.feed. No change to historical public declarations is required to expose this distinction.

## Registry completion obligations

### Closed descriptor and acyclic artifact custody

The [operation-registry descriptor schema](../02-design/contracts/conformance-operation-registry-v0.1.proposal.schema.json)
now closes registry and entry members. Each operation binds an exact profile,
registered declaration/method or original harness procedure, call procedure
bytes/profile, argument and result schema bytes with exact JSON pointers,
permitted scope kinds, semantic contract inventory, all four normative
observer registrations with independence evidence, and resource profile.
A performance observer is optional in shape but mandatory when the selected
case/profile requires performance. An explicit no-output report or journal
still requires its registered complete observer; omission is not emptiness.

Schema pointers resolve only against the supplied exact original schema
artifact after bounded parse/digest/profile admission. They select the intended
schema node, never a path on the observed result. Method names and call
procedure artifacts resolve through the original trusted host registration;
no imports, SQL strings or callbacks are executed from this descriptor.
Duplicate operation discriminators, unresolved declaration/method/profile,
unsupported scope kind, incomplete observation membership or unqualified
independence prevent registration. The shape-valid shared-observer fixture
does not supply independence simply by repeating an evidence artifact.

The descriptor deliberately does not embed identity-path artifact bytes or
their digest. The path artifact already embeds the registry artifact, so a
reverse reference would require circular hashes. The original host composition
selects both artifacts independently; admission verifies that the path's
registry equals these original bytes. Registry and grammar profiles identify
separately registered semantic procedures, not their own enclosing artifact's
self-hash. Preserve this acyclic source custody when constructing the complete
manifest and aliases. The new descriptor is not itself a populated registry.

Run `check-conformance-operation-registry.ts` in the design audit directory
with the installed Ajv Draft 2020-12 module path: fourteen controls cover
closed method/harness descriptors, required observer evidence, schema pointers,
scope kinds and prohibited executable/reverse-reference members. Duplicates,
unknown methods and insufficient independence deliberately remain shape-valid
semantic refusal controls. Populate and independently admit all required
operations under their exact methods/profiles before claiming execution readiness.

### Case-only multi-argument encoding

The definitions-only `conformance-capability-arguments-v0.1.proposal.schema.json`
closes four case input envelopes without changing public API requests:

| Member | Dispatch into existing method |
| --- | --- |
| catalogAcceptance | acceptInTransaction(original scope handle, input, assertedOrigin); origin reuses acceptance-input's existing CanonicalTree, not ExactValue or host numbers |
| requestFreeGroup | applyInTransaction(original scope handle, input, request-none) |
| requestBearingGroup | applyInTransaction(original scope handle, input, request-present) |
| importBatches | runBatches(input, constructed read-write TransactionOptions) |

For import, options declares the exact isolation and read-write access mode.
The required case-only cancellation member is none or a reference to an
original harness-issued signal. Resolve it through the admitted harness
procedure before constructing public options; only then may an actual
Cancellation `{signal}` be supplied. No JSON signal, caller-picked authority
or native handle is deserialized. Unknown/ended/unowned references refuse
dependent invocation. A none selection supplies no cancellation option.
The existing input-step scope carries transaction references separately;
these envelopes cannot end adopted transactions or create a different scope.

Run `check-conformance-capability-arguments.ts` in the design audit directory
with the installed Ajv Draft 2020-12 module path: fifteen controls cover each
envelope, exact origin, overload narrowing, required cancellation selection and
refusal of serialized handles/signals. This closes these argument carrier
shapes, not original artifact custody, scope/signal issuance, cancellation
containment or native method execution. Feed acknowledgment still requires its
separate original VerifiedApplicationV02 procedure; no case envelope can forge
that authority.

### Existing wire carriers and actual composition gaps

Retained reconstruct/historicalSource now have definitions-only
`retained-history-capability-wires-v0.1.proposal.schema.json`: select the
reconstructionRequest/Result/Outcome or sourceRequest/Result/Outcome member
for the corresponding method. The evidence definitions preserve original
baseline/event/definition inventory and current authority observations.
Historical source reuses the existing FeedSourceFact carrier at
seed-baseline-v0.1's `$defs/source`; this structural reuse qualifies neither
seed execution nor feed completeness. Preserve absent versus not_found,
deleted versus unwritten and history_unavailable versus unsupported meaning.
No current catalog revision is silently inserted into a reconstruction request.
Run `check-retained-history-capability-wires.ts` in the design audit directory
with the installed Ajv Draft 2020-12 module path: twenty-four composition
controls cover all business branches and required evidence/non-disclosure.
Actual historical horizons, retained owner/source correspondence, current
authority and native reconstruction remain unqualified. These carriers close
the missing history wrapper work in the table below; original semantic
registration is still required.

Paths below are under `docs/helix/02-design/contracts/`. Reuse the named
carriers, preserving their `$id` and exact registered bytes. A payload schema
is not automatically the complete capability argument or return schema. Every
`Outcome<T>` also needs the registered execution-failure branch. This matrix
covers the twenty-two capability entries above; the administrative inventory
below retains its separate completion obligations.

| Existing method / branch | Reusable carrier | Remaining complete operation encoding |
| --- | --- | --- |
| catalog acceptInTransaction | acceptance-input-v0.1; acceptance-report-v0.1; acceptance-rejection-v0.1 | Bind separate assertedOrigin argument and AcceptanceSemanticResult disposition/rejection wrapper, then outer Outcome; select lifecycle report version explicitly |
| catalog report | acceptance-report-v0.1 | Encode existing AcceptanceReportRequest revision and available/not_found/unavailable result wrapper, then Outcome |
| mutation applyInTransaction | group-input-v0.1 operation definitions; group-result-v0.1 semantic payload | Encode actual standalone MutationSemanticInput restrictions and MutationApplicationResult; group aliases/references and group response are not substitutes |
| group applyInTransaction, request none | group-input-v0.1; group-result-v0.1 | Bind separate request-none argument and RequestFreeGroupApplicationResult; exclude receipt/replay/conflict outcomes forbidden by this overload |
| group applyInTransaction, request present | group-input-v0.1 requestIdentity/requestSelection definitions; group-result-v0.1 | Bind original separate request argument and GroupApplicationResult/InTransactionGroupResponse, then Outcome; a committed GroupResponse cannot relabel pending application |
| import runBatches | import-input-v0.1; import-report-v0.1; import-resource-result-v0.1 | Bind separate read-write TransactionOptions and full ImportExecutionResult with engine_owned report discrimination; no generic Outcome wrapper |
| import applyInTransaction | same import carriers | Encode full ImportExecutionResult with host_adopted/outer_engine_scope report discrimination; preserve execution_failed report/null and prior progress |
| lookup | direct-lookup-request-v0.1; direct-lookup-result-v0.1 | Existing proposed direct-lookup-execution-outcome-v0.1 composes return; exact scope/profile registration remains |
| page | direct-page-request-v0.1; direct-page-result-v0.1 | Compose outer Outcome and actual transaction scope |
| catalogView | catalog-view-request-v0.1; catalog-view-v0.1 | Encode CatalogViewResult available/unavailable wrapper before Outcome; raw CatalogView is only its payload |
| traverse | direct-traversal-request-v0.1; direct-traversal-result-v0.1 | Compose Outcome and original snapshot/stage procedures; preserve pending human traversal interpretation |
| resumeTraversal | direct-traversal-resume-request-v0.1; direct-traversal-result-v0.1 | Compose Outcome and original stage/work-version correspondence |
| nextTraversalPage | direct-traversal-page-request-v0.1; direct-traversal-result-v0.1 | Compose Outcome and sealed original page/publication context |
| releaseTraversal | direct-traversal-release-request-v0.1; direct-traversal-release-result-v0.1 | Compose Outcome; method has no transaction argument |
| pageJournal | journal-page-request-v0.1; journal-page-result-v0.1 | Compose Outcome; select later complete-history journal proposal only through its separate adopted profile |
| reconstruct | history-record-v0.1 retained record payload | Encode existing ReconstructionRequest/ReconstructionResult and complete evidence, not a bare record or journal page |
| historicalSource | history-record-v0.1 retained record payload | Encode existing HistoricalSourceRequest/HistoricalSourceResult and original source evidence; current direct lookup cannot substitute |
| executeInTransaction | compiled-execution-request-v0.1; compiled-execution-result-v0.1 | Compose Outcome with exact selected Weft ABI/decoder registration and obligations; no parsed-query wire inferred |
| discoverNext v0.2 | feed-discovery-v0.2 root request and $defs/result | Compose Outcome and original complete discovery/watermark procedure |
| readFragment v0.2 | feed-fragment-request-v0.2; feed-fragment-page-v0.2 | Compose Outcome; fragment page cannot establish independent complete-feed membership alone |
| observeFreshness v0.2 | complete-feed-freshness-v0.2 $defs/request and $defs/result | Compose Outcome, original proof registration and native clock/boundary observations |
| acknowledgeInTransaction v0.2 | feed-acknowledgment-result-v0.2; selected application/boundary carriers | Encode ConsumerAcknowledgmentV02 arguments through original admitted VerifiedApplicationV02 issuance; never deserialize or cast JSON into that branded authority; compose Outcome |

Names without a `.schema.json` suffix in this table designate that schema file,
not a newly proposed API. For rows with missing wrappers, first derive the
closed carrier from the cited existing declaration and add independent
forbidden-branch controls. Register each exact argument separately or an
explicit case-only argument envelope; do not add envelope fields to public
requests. Scope handles, verified applications and other host-issued authority
come from original trusted procedures, never from a schema-valid JSON object.
This mapping prevents duplicate carrier work but is not an executable registry
or qualification of any method.

The proposed `capability-execution-outcomes-v0.1.proposal.schema.json` now
supplies the outer compositions for ten complete existing business-result
carriers. Register its exact `$defs` member rather than the root: directPage
for page; catalogViewResult/catalogView for catalogView; traversal for traverse/resumeTraversal/nextTraversalPage;
traversalRelease for releaseTraversal; journalPage for pageJournal;
compiledExecution for executeInTransaction; feedDiscovery, feedFragment,
feedFreshness and feedAcknowledgment for the corresponding v0.2 methods.
The root deliberately refuses all wires because this is a definition library,
not an untagged union that lets a method accept another method's result.
These compositions close the outer schema work identified in those table rows;
original method/profile/argument/observer/identity-path registration still
remains. The specialized compositions below close further carrier work while
retaining exact argument and original procedure registration obligations.
Import is explicitly excluded from generic Outcome composition.

Standalone mutation now has definitions-only
`mutation-capability-wires-v0.1.proposal.schema.json`. Register input/result/outcome
for the existing facade and operation only for its single-operation argument.
The input reuses original group common fields and exact indexed operation
branches, with aliases forbidden and stored references required for targets,
roots and endpoints. Register the original group schema bytes/digest alongside
this composition; changing branch order cannot silently preserve correspondence
by filename. The result reuses group operation-result branches, forbids an
allocation alias and keeps supplied-scope success pending. These restrictions
apply to registered structural slots, not recursive strings or ordinary JSON
properties. Run `check-mutation-capability-wires.ts` in the design audit
directory with the installed Ajv Draft 2020-12 module path: nineteen controls
cover all six operations, stored/alias restrictions and pending result layering.
Native reference/ownership/value/key/current-authority validation, full journal
effects and confirmed transaction termination remain unqualified.

Group now has definitions-only `group-capability-wires-v0.1.proposal.schema.json`.
Register requestFreeResult/requestFreeOutcome only for the request-none
overload, and requestBearingResult/requestBearingOutcome for request-present.
Reuse group-input's existing requestSelection/requestIdentity definitions for
the separate request argument; never insert it into GroupSemanticInput.
The result composition reuses the complete group semantic response but allows
applied only with pending durability in the supplied scope. Request-bearing
replay retains its original same-transaction or committed-receipt distinction;
request-free excludes replay, request_conflict and receipt/receipt_expired.
An unresolved union is a typing convenience, not permission to select the
broader comparator after observing a result. Run `check-group-capability-wires.ts`
in the design audit directory with the installed Ajv Draft 2020-12 module path:
twenty-four overload/layering controls pass. Original input/result order,
event/deletion completeness, request authority, full receipt correspondence
and native commit/replay observation remain required.

Catalog now reuses the existing v0.1 report/rejection/failure carriers through
`catalog-capability-wires-v0.1.proposal.schema.json`. Register reportRequest
for the existing revision request, acceptanceSemantic/acceptanceOutcome for
acceptInTransaction's result, and reportSemantic/reportOutcome for report's
result. All are exact `$defs` selections from a definitions-only library.
This preserves new/exact_repeat versus rejection and report
available/not_found/unavailable distinctions. The separate assertedOrigin
argument still needs exact CanonicalTree registration and original scope
binding; this library does not serialize authorization context or a handle.
Later lifecycle report proposals require separately selected versioned
composition, not widening this v0.1 carrier in place. Run
`check-catalog-capability-wires.ts` in the design audit directory with the
installed Ajv Draft 2020-12 module path: fourteen shape controls pass. The
synthetic empty rejection diagnostics are not proof of semantic completeness,
and no producer-backed accepted report, immutable insertion, head publication
or confirmed commit is qualified by these wrappers.

Import now has its own definitions-only
`import-execution-result-v0.1.proposal.schema.json`: register `$defs/engineOwned`
for runBatches and `$defs/inTransaction` for applyInTransaction. It composes
the existing reported/resource_limited/execution_failed/invalid branches and
reuses original report/resource/failure carriers. The report's execution
discriminator preserves engine_owned versus host_adopted/outer_engine_scope.
An execution_failed report is mandatory and nullable; absence is not null,
and null is semantically permitted only before any writer submission. This
schema does not prove that condition or allow removal of prior progress.
Transaction options and original live scope binding remain argument-registration
work. Run `check-import-execution-result.ts` in the design audit directory with
the installed Ajv Draft 2020-12 module path: twenty-five composition controls
cover every outer branch, ownership distinctions, omitted progress and
forbidden generic Outcome wrapping. Native progress, count coherence,
resource containment and actual transaction outcome remain unqualified.

Run `bun docs/helix/04-build/evidence/design-audit/check-capability-execution-outcomes.ts <installed-Ajv-2020-module-path>`.
Fifty-five controls check all ten registered definitions' outer error/required
value/closed branch/false durability shapes, the catalog-view business wrapper
and the definitions-only root.
They do not test complete inner business-result membership or qualify native
effects, termination, observer independence or support availability.
The separate [148-schema receipt](../04-build/evidence/design-audit/schema-inventory-outcomes-2026-10-09.json)
records strict combined registration/reference compilation with zero errors;
the earlier conformance carrier receipt remains preserved.

For direct `lookup`, reuse `direct-lookup-request-v0.1.schema.json` for the
request argument and `direct-lookup-result-v0.1.schema.json` for the inner
business result. The proposed `direct-lookup-execution-outcome-v0.1.proposal.schema.json`
composes the actual `Outcome<DirectLookupResult>` return using the existing
execution-failure schema. The transaction handle is supplied through original
scope registration, not serialized into the request. A withTransaction harness
wrapper has another outer outcome and cannot be flattened into this return.
Run `check-direct-lookup.ts` and `check-direct-lookup-outcome.ts` in the design
audit evidence directory with the installed Ajv Draft 2020-12 module path:
twenty-two existing request/inner-result and eight nested-outcome controls pass.
Exact registry/profile custody, complete fixture/observer semantics and native
effects/termination remain required; these shapes do not admit availability.

For every entry, the executable registry must pin exact original declaration and input/result schemas, full semantic contract inventory, capability selection, observer/profile/resource grammar, and generated identity paths. Symbolic step references must resolve before existing public input construction, never by modifying public wires. The registry must distinguish outer Outcome execution failure from inner business result, and import's distinct progress-bearing execution result.

Host transaction controls use trusted harness procedures, not Truss capability methods. Installation/status/explicit migrations, live provenance and administrative retention/tooling require their own exact existing declarations/procedures to be enumerated before claiming the full registry complete. Do not invent convenience methods to fill that inventory. Informative SQL is never dispatched as a substitute operation.

Independent controls must reject v0.1 feed masquerading as v0.2, request-free group expectations containing replay, import progress discarded inside a generic Outcome wrapper, release requiring an ended transaction, and a pending result labeled committed from savepoint release. These are required red integration controls, not passing runtime evidence.

## Administrative and executor inventory

| Family | Existing operation | Declaration | Required boundary |
| --- | --- | --- | --- |
| fresh installation | installFresh | truss-bootstrap-installation-v0.1, BootstrapInstallationTooling | Dedicated administrative transaction; qualified complete candidate, nonempty refusal and original confirmed commit |
| installation recovery | reconcileInstallation | Same | Read-only original attempt; no reinstall from missing observation |
| layout upgrade | apply | truss-layout-migration-v0.1.proposal, LayoutMigrationTooling | Explicit complete registered route in dedicated administrative transaction; preserve migrated/already_applied/committed_unverified versus unknown/refused/rolled_back outcomes |
| upgrade recovery | reconcile | Same | Read-only original recovery reference; no resubmission or inferred absence |
| retention | dropInTransaction | truss-retention-tooling-v0.1, RetentionTooling | Complete original eligibility/dependency cohort under supplied transaction; pending until confirmation |
| receipt protection | extendInTransaction; observeProtection | truss-receipt-protection-tooling-v0.1, ReceiptProtectionTooling | Pending monotonic protection change versus independent original committed observation |
| receipt expiry | assessPurge; purgePayloadInTransaction; observeExpiry | truss-receipt-expiry-tooling-v0.1, ReceiptExpiryTooling | Eligibility differs from removal; expired identity remains protected against reexecution |
| physical jobs | admitIndexInTransaction; observeIndexAdmission; runIndexAttempt; observeIndex | truss-physical-job-tooling-v0.1, PhysicalJobTooling | Pending admission, confirmed admission, explicit original execution and observation remain separate |
| statistics jobs | admitStatisticsInTransaction; observeStatisticsAdmission; runStatisticsAttempt; observeStatistics | Same | Acceptance commit alone cannot launch a pending job; original collection failure stays visible |
| executor | withTransaction | truss-execution-v0.1, Executor | Explicit owned callback scope; original confirmed commit, no automatic callback replay |
| executor | adoptTransaction | Same | Verify active original host handle/isolation/access mode without replacement or ownership transfer |
| executor | savepoint; rollbackToSavepoint; releaseSavepoint | Same | Original operation scope; release is not commit and rollback invalidates removed captures |

Executor.execute is a registered internal statement port, not a corpus escape hatch to dispatch arbitrary SQL. Native direct-SQL bypass tests use a separately host-admitted independent harness procedure and exact immutable statement fixture, with their own authority/resource/termination evidence. Host commit/rollback controls likewise remain trusted harness operations: Executor has no public commit-by-id method for adopted scopes.

The existing InstallationAdmissionSnapshot is a data projection, not a callable status API. Inspection/readiness cases bind the actual ReferenceAssembly.observeReadiness procedure or exact independently registered native verifier; do not invent inspectStatus from the snapshot's name. Pure layout migration planning is separately implemented tooling, not LayoutMigrationTooling.apply and not evidence that upgrades execute.

Conformance runner prepareRun/run/abandonPreparedRun/reconcileRun and assessor assess belong to the outer trusted harness lifecycle under truss-conformance-tooling-v0.1. They do not become recursive case operations unless a separately selected tooling test explicitly qualifies them. Preserve complete original run/cleanup evidence independently from implementation-under-test outcomes.

This completes the named administrative/executor inventory above, not the full executable registry. Live source lookup, remaining lifecycle/configuration methods, exact machine-readable input/result registrations and typed identity paths must still be resolved. Never fill those gaps from a guessed public method name or treat this table as a passing corpus.
