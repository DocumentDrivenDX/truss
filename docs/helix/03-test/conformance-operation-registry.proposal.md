# Conformance operation registry — authored method inventory

Companion to [case grammar](conformance-case-grammar.proposal.md). These entries bind existing declarations; they introduce no public methods. Status: proposed inventory, not a complete executable registry. Exact input/result schemas, identity paths, original profiles and semantic observation scope must be registered before execution.

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

### Existing wire carriers and actual composition gaps

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
supplies the outer compositions for nine complete existing business-result
carriers. Register its exact `$defs` member rather than the root: directPage
for page; traversal for traverse/resumeTraversal/nextTraversalPage;
traversalRelease for releaseTraversal; journalPage for pageJournal;
compiledExecution for executeInTransaction; feedDiscovery, feedFragment,
feedFreshness and feedAcknowledgment for the corresponding v0.2 methods.
The root deliberately refuses all wires because this is a definition library,
not an untagged union that lets a method accept another method's result.
These compositions close the outer schema work identified in those table rows;
original method/profile/argument/observer/identity-path registration still
remains. Catalog, standalone mutation, group and import wrapper gaps are
unchanged. Import is explicitly excluded from generic Outcome composition.

Run `bun docs/helix/04-build/evidence/design-audit/check-capability-execution-outcomes.ts <installed-Ajv-2020-module-path>`.
Forty-six controls check all nine registered definitions' outer error/required
value/closed branch/false durability shapes and the definitions-only root.
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
