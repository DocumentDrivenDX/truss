# Reference protected access composition

Status: authored responsibility and route plan; native roles, routine bodies, grants and support remain unqualified. This composes CONTRACT-001 and CONTRACT-005 with the original 0.12 store and sixteen-selector worklists. It does not replace their immutable source pins or fill native evidence fields with design labels.

## Responsibility boundaries

The table assigns responsibility labels, not SQL role names. Installation binds each label to exact native identities and effective privileges. The ordinary application actor has no canonical DML in this protected-procedure candidate. It receives only the exact admitted public entry signatures and independently qualified read surfaces. Baseline direct DML is a separate profile under CONTRACT-005; this candidate cannot remove or claim that profile's requirements.

The installation administrator owns protected objects and performs installation/conversion. Routine responsibilities receive only the relation/column/sequence rights required by their complete bodies; assigning a family never grants all its stores or all commands. They are not application-inheritable or SET-accessible roles. A producer requiring another responsibility calls an exact private entry under original custody rather than acquiring that role in its caller session. Native role coalescing must preserve every prohibition and undergo the complete transitive-path review; it is not an automatic optimization.

The integrity observer remains the separate non-login read-only responsibility selected in CONTRACT-005. It observes complete admitted hidden scope privately and cannot mutate, allocate IDs, publish, administer policies or authorize outer disclosure. Read surfaces must use the original actor/current authority and cannot borrow observer visibility. Administrative access is explicitly separate from ordinary enforcement claims.

## Complete declared-store route plan

Every original declared store occurs exactly once below. Read routes describe allowed logical surfaces, not raw SELECT grants. Complete column/row/payload disclosure must be derived separately; private auxiliary stores cannot be exposed by an automatically generated view. Writer routes require original operation or administrative custody, resource admission, authority and final native integrity checks.

| Original relation | Writer responsibility | Ordinary/public read route | Protected write route |
| --- | --- | --- | --- |
| setting | Installation administrator | Qualified configuration inspection | Installation/configuration admission |
| module_access | Policy administrator | Qualified grant administration and permitted authority inspection | Qualified policy transition |
| schema_rev | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| schema_head | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| schema_doc | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| schema_change | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| type_def | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| prop_def | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| key_def | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| rel_def | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| rel_endpoint | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| object | Graph mutation producer | Qualified graph read; edge_limit remains private integrity state | Atomic graph mutation and private integrity maintenance |
| edge | Graph mutation producer | Qualified graph read; edge_limit remains private integrity state | Atomic graph mutation and private integrity maintenance |
| edge_limit | Graph mutation producer | Qualified graph read; edge_limit remains private integrity state | Atomic graph mutation and private integrity maintenance |
| key_tombstone | Key mutation producer | Exact full-context key lookup only; guards/reservations remain private | Original key allocation/reservation/lifecycle procedure |
| record_source | Graph mutation producer | Qualified graph read; edge_limit remains private integrity state | Atomic graph mutation and private integrity maintenance |
| feed_consumer | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| journal | Journal publisher | Qualified complete history reconstruction/feed read | Journal publication; separately admitted retention |
| row_home_operation | Operation coordinator | No ordinary raw disclosure; public result/settlement only | Original operation/phase/touch/capacity procedure |
| row_home_journal_stage | Operation coordinator | No ordinary raw disclosure; public result/settlement only | Original operation/phase/touch/capacity procedure |
| row_home_state | Graph mutation producer | Qualified complete value read through admitted definition/decoder | Original complete row-home mutation |
| row_home_node | Graph mutation producer | Qualified complete value read through admitted definition/decoder | Original complete row-home mutation |
| row_home_scalar | Graph mutation producer | Qualified complete value read through admitted definition/decoder | Original complete row-home mutation |
| relationship_lineage | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| row_home_touch | Operation coordinator | No ordinary raw disclosure; public result/settlement only | Original operation/phase/touch/capacity procedure |
| row_home_capacity | Operation coordinator | No ordinary raw disclosure; public result/settlement only | Original operation/phase/touch/capacity procedure |
| key_bucket_guard | Key mutation producer | Exact full-context key lookup only; guards/reservations remain private | Original key allocation/reservation/lifecycle procedure |
| object_key_bucket | Key mutation producer | Exact full-context key lookup only; guards/reservations remain private | Original key allocation/reservation/lifecycle procedure |
| object_key_reservation_bucket | Key mutation producer | Exact full-context key lookup only; guards/reservations remain private | Original key allocation/reservation/lifecycle procedure |
| catalog_acceptance_report | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| installation_marker | Installation administrator | Admitted readiness/report inspection; archive internals private | Atomic installation/conversion admission |
| installation_archive | Installation administrator | Admitted readiness/report inspection; archive internals private | Atomic installation/conversion admission |
| feed_tx | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| feed_member | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| feed_prerequisite | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| feed_configuration_prerequisite | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| complete_feed_consumer | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| complete_feed_administration_receipt | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| complete_feed_seed_attempt | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| complete_feed_seed_artifact | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| key_lifecycle_history | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| installation_admission | Installation administrator | Admitted readiness/report inspection; archive internals private | Atomic installation/conversion admission |
| key_migration_receipt | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| request_receipt_route_guard | Receipt coordinator | Original request lookup/replay with fresh owner-union authority; guards/protections private | Original arbitration/publication/protection/expiry procedure |
| request_receipt | Receipt coordinator | Original request lookup/replay with fresh owner-union authority; guards/protections private | Original arbitration/publication/protection/expiry procedure |
| request_receipt_protection | Receipt coordinator | Original request lookup/replay with fresh owner-union authority; guards/protections private | Original arbitration/publication/protection/expiry procedure |

For graph reads, object/edge/record_source each retain original qualified owner intersections; row_home_state/node/scalar require complete owned state/root/payload and the admitted four-Field definition bundle. The graph family label does not admit edge_limit disclosure. Catalog reports, original source and retired/deleted history require their complete retained owner union, not merely visibility of the current schema head. Receipt guards and protections and feed prerequisite/configuration/seed state are internal even when an admitted status API exists.

## Original private entry routing

| Existing selector cohort | Permitted invocation boundary | Prohibited shortcut |
| --- | --- | --- |
| row_touch_observe; edge_limit_observe; edge_limit_catalog_observe | Installed original triggers under admitted writer/catalog operation, with original actor and generation | Ordinary direct EXECUTE, synthetic trigger invocation or actor supplied as a trusted argument |
| row_touch_commit_check; feed_current_union_check | Installed original deferred/current-union check paths under the same transaction's surviving operation cohort | Treating an earlier seal or filtered unfinished-operation set as commit proof |
| feed_union_validate_current_scope; edge_limit_verify_current_scope | Exact internal finalization/commit caller with complete original scope and exclusion | Arbitrary SQL/table/scope selection or exposed private count result |
| journal_capture_start; journal_observe_transition; journal_prepare_final; journal_reserve_positions; journal_append_group | Original journal coordinator following H1–H7 and exact phase/capture custody | Caller-created phase bytes, precommit publication, or reservation as commit evidence |
| row_touch_reserve; row_touch_seal | Original canonical admission/finalization caller, exact operation/generation and whole integrity scope | Capacity reset, sealing only visible rows, caller-chosen owner identity as authority |
| row_touch_cleanup; row_journal_stage_cleanup | Separately admitted retention administrator, complete original selected cohort and native termination | Application cleanup rights, partial returned cohort as completion or cleanup as rollback proof |

These routes cover sixteen existing selectors, not the entire future callable closure. Public mutation/read/import/catalog/report/receipt/feed/retention/recovery entry bodies must be enumerated with their complete private dependencies before installer readiness. No public entry is licensed merely because this document names its logical responsibility.

## Composition and failure order

1. Retain original native actor before elevated work; admit complete requested input, authority and resource context. Resolve the exact public entry and original transaction/operation identity.
2. Bind every reached store/column/sequence and helper to the intended responsibility and exact native definition. Check effective ACL, ownership, PUBLIC/default grants, inherited/SET/grant-option paths, policy applicability, resolution namespaces and transitive wrappers.
3. Execute only the admitted producer route. Internal observations preserve complete hidden scope but return facts only to original protected custody. Public errors, tracing and callbacks cannot disclose private IDs/counts/bytes.
4. Before publication recheck current actor/authority, definition/profile generation, complete original operation effects and native final integrity. Apply the existing outer-commit and original recovery rules; this access plan does not settle a transaction.
5. Installation compares its complete intended inventory against actual installed bodies, dependencies, roles, grants, policies, triggers and administrative/restore/replication paths before readiness. Missing, additional or changed access invalidates the affected capability. Unknown installation settlement retains original recovery custody.

This selects the responsibility and routing composition while preserving unresolved physical names, exact body-specific rights and native evidence. It does not grant unrestricted administrator escape paths ordinary-writer qualification, infer absence from inaccessible rows, or assert database isolation/resource behavior from source text.


## Public capability caller closure

This matrix resolves caller classes and private dependency routes for the existing ReferenceAssembly capability declarations. It does not invent SQL routine names: exact signatures/bodies must be bound from the installer inventory before readiness. Every reached function, trigger, view, operator, cast and effective role path belongs to that inventory, including dependencies not named in the sixteen-selector worklist. Ordinary callers may invoke only the selected public facade; private producer invocation remains original operation/issuer custody, not permission inferred from a function name.

| Original public capability surface | Original admission and caller boundary | Complete private dependency route |
| --- | --- | --- |
| directReads.lookup/page/catalogView | Supplied transaction; current qualified owner disclosure; exact selected read/profile/budget | Catalog/source selection, exact full-context key lookup where requested, private integrity observation, complete logical projection and publication recheck; no observer rows or guard disclosure |
| directReads.traverse/resumeTraversal/nextTraversalPage/releaseTraversal | Original admitted traversal identity/generation, selected transaction where declared; release retains its separate lifecycle admission | Original stage service, retained frontier/exclusion/protection and authority, bounded decoder/publication; release cannot mutate graph or settle caller transaction |
| catalog.acceptInTransaction/report | Supplied transaction; catalog exclusion, original acceptance producer and complete owner union; report has independent disclosure admission | UMF checks/transition, full native Validate/Transform, identity/key/relationship lineage, row/edge observers, immutable report before head, journal/feed complete publication; exact retry retains original report |
| groups.applyInTransaction; mutations.applyInTransaction | Supplied transaction; original actor, complete owner union, operation/generation and capacity admission | Key arbitration, canonical graph/row-home writes, unavoidable OLD/NEW touch observation, final integrity/row sealing, journal capture/reservation/append, complete feed union and deferred checks; receipt paths only when replay is selected |
| imports.applyInTransaction/runBatches | Adopted transaction for apply; explicitly owned whole batches for run; exact import origin and group semantics | Same mutation/group producer chain plus bounded source decoder and original batch result/settlement; no alternate bulk-DML path that omits triggers, reports or feed membership |
| history.pageJournal/reconstruct/historicalSource | Supplied transaction; complete retained owner/source authority, selected reconstruction/retention profile | Original complete journal groups, historical source/definition/value decoder and admitted archive provider when selected; current rows never repair missing history |
| feed.discoverNext/observeFreshness/readFragment | Supplied transaction; original registered consumer/generation and complete owner/configuration/prerequisite scope | Complete committed transaction/member/prerequisite inventory, current authority/fencing and bounded fragment decoder; filtered visible subset cannot establish complete feed |
| feed.acknowledgeInTransaction | Supplied transaction; original consumer generation and admitted applied-boundary/proof verification | Exact descriptor/application evidence, verifier registration, atomic fenced checkpoint/protection effects and deferred union checks; downstream receipt alone cannot advance source ACK |
| compiledExecution.executeInTransaction | Supplied original transaction; engine-issued artifact provenance, admitted binding/profile/parameter/decoder tuple | Accepted-catalog producer, same-context native profile/authority/integrity obligations, original SQL/Bind and buffered publication recheck; no arbitrary SQL entry or logical-to-physical fallback |

Assembly construction, capability selection and registration remain inert. observeReadiness is explicit read-only observation; it neither grants rights nor installs objects. dispose closes admission and releases only owned resources, preserving caller transaction/pool ownership and quarantining unresolved native work. These host surfaces require issuer-wide executor checks even when they have no SQL routine of their own.

Administrative tooling is a separate admitted caller class: bootstrap/conversion, policy transitions, physical jobs, key migration, feed registration/seed/generation transitions, receipt protection/expiry and retention/recovery. Bind each exact declared tooling method to its own original profile/authority/cohort and transitive body closure; do not grant these rights through graph mutation or read capability selection. Conformance and test fixtures are not administrative bypasses.

Initial compiled logical reads advertise no standalone SQL view. The protected profile exposes no implicit raw SELECT or canonical DML to ordinary callers. Any separately selected direct-DML or SQL-client read profile retains CONTRACT-005 obligations and requires an explicit original surface inventory; this candidate cannot silently revoke or replace it. Thus no table/view is licensed for public disclosure solely by the store responsibility table above.

### Native closure acceptance

PAC-01: invoke every declared public capability through its original admitted caller and independently inspect reached objects/roles; refuse any unregistered transitive callable or widened right before readiness. A positive public result alone is insufficient.

PAC-02: attempt direct invocation of private trigger/finalizer/journal/cleanup helpers and direct canonical DML/sequence manipulation as ordinary actor, including inherited/SET-capable roles and function-owner paths. Refuse all prohibited routes without effects; independently inspect actual effective rights.

PAC-03: inject an additional callable/operator/cast or advertised read surface into the installation while retaining the old inventory. Native correspondence/readiness must refuse rather than ignore the new entry.

PAC-04: use a permitted facade to reach hidden staging, guard, receipt protection, observer count or another owner's source/report through errors/results. Require full original disclosure enforcement, including after authority changes before publication.

PAC-05: exercise owned versus adopted transaction failure, savepoint rollback and outer commit for mutation/import/catalog/feed ACK; inspect complete surviving journal/feed cohort and earlier caller sentinel work. A shared private helper must not change settlement ownership.

These schedules remain not_run. Exact body-specific rights and transitive native closure are implementation outputs. The matrix closes the public capability caller/dependency design; tooling's complete method/body inventory and native security qualification remain separate required work.


## Administrative method closure

The following existing declaration methods supplement the public capability matrix. Names are TypeScript API selectors, not proposed SQL grants. Versioned feed0.1 and feed0.2 declarations remain separate selections; overlapping method names do not make their registrations or evidence interchangeable. Bootstrap and migration remain independently owned administrative operations rather than methods on an adopted runtime transaction.

| Owning declaration / exact method selectors | Required original custody and private effect boundary |
| --- | --- |
| BootstrapInstallationTooling.installFresh / reconcileInstallation | installFresh owns its administrative transaction and complete archive/inventory/marker admission. Reconciliation observes the original attempt read-only; missing marker without proved termination remains unknown, never permission to install again. |
| KeyProfileMigrationTooling.migrate / reconcile | Original source/target profile and full reservation/history/receipt conversion under exclusion; preserve IDs and complete original bytes. Reconcile original attempt before retry; no key reset/reallocation shortcut. |
| PhysicalOptimizationTooling.applyInTransaction | Supplied transaction, original selected optimization profile and bounded actual physical effects; never change logical identity/equality or infer new public read rights. |
| PhysicalJobTooling.admitIndexInTransaction / observeIndexAdmission / runIndexAttempt / observeIndex | Admission produces pending identity only; native committed observation precedes running the separately owned job. Bind exact original job/attempt/source and actual index status, including unknown/recovery; no caller-created committed token. |
| PhysicalJobTooling.admitStatisticsInTransaction / observeStatisticsAdmission / runStatisticsAttempt / observeStatistics | Same pending/committed separation with original statistics job/profile/attempt. Running a job does not commit an adopted caller transaction or prove all statistics ready from scheduling success. |
| RetentionTooling.dropInTransaction | Supplied transaction, complete selected cohort, original authority and all live protection/retention/archive prerequisites. Private cleanup cannot drop partial groups or turn cleanup into rollback/termination proof. |
| ReceiptProtectionTooling.extendInTransaction / observeProtection | Original request namespace, complete owner union, exact protection identity/generation and supplied transaction; observation cannot grant protection or expose private route guards. |
| ReceiptExpiryTooling.assessPurge / purgePayloadInTransaction / observeExpiry | Recheck original scope/protection under current exclusion at mutation; prior assessment is not authority. Preserve required receipt identity/recovery semantics after payload purge. |
| FeedAdministrativeTooling.applyInTransaction / observeReceipt | Original consumer/configuration generation and exact administration action; complete fenced effects in supplied transaction, observed receipt before durable claims. |
| FeedConsumerRegistration.registerInTransaction / observeRegistration | Original registered consumer/profile/owner union; pending registration is not committed readiness or proof of seed installation. |
| FeedWorkerAdministration.acquireInTransaction / observeClaim | Original worker/consumer generation and native claim arbitration; pending claim cannot authorize downstream install. Observation retains current committed fencing and original scope. |
| SeedExtractionTooling.extract / extractReplacement / extractRestarted | Original admitted registration/replacement/restart provenance, protected complete snapshot and bounded exact artifact; no current-row subset or default snapshot substituted for the admitted source. |
| SeedSourceConfirmation.confirmInTransaction | Supplied transaction, original seed artifact/application proof and current generation; complete source checkpoint/protection transition only after original required evidence. |
| SeedAbandonmentTooling.invalidateInTransaction / finishInTransaction | Fence original generation before cleanup; finish proves complete selected attempt termination/protection cleanup, preserving unknown outcomes until reconciled. |
| SeedRestartTooling.restartInTransaction / observeRestart | Original abandoned/restart source and new fenced attempt under supplied transaction; no reuse of stale extraction/claim or pending admission as durable restart. |
| Feed0.2 administrative/registration/worker/restart/confirmation/extraction methods | Preserve the corresponding FeedLifecycleV02 and FeedHostCompositionV02 request/result grammars and exact source/downstream key/profile registrations. Same-named0.1 methods cannot satisfy0.2 requirements. Shared abandonment retains its original declaration. |
| HostFeedDownstreamAdapterV02.installGeneration / reconcileInstallation | Host-owned downstream boundary: only original current_committed claim may install. Reconcile original downstream attempt; source ACK remains a distinct fenced source operation. Truss does not grant downstream credentials or choose its transaction by data. |
| HostConformanceRunner.prepareRun / run / abandonPreparedRun / reconcileRun; ConformanceEvidenceTooling.assess | Test administration is explicit and original-run scoped. Prepared evidence cannot authorize production writes; assessment of a receipt is not execution, cleanup or native qualification. |

ReceiptLifecycleTooling and FeedLifecycleTooling aggregate these original subinterfaces; construction creates no additional native entry. Registration factories capture explicitly supplied original services and profiles, but do not grant routine EXECUTE, administrative rights or readiness. Any later declared method must receive its own caller/effect row and transitive inventory before selection.

PAC-06 extends the existing planned closure controls: independently invoke every selected administrative method as its correct original administrator, then as an ordinary application actor, a stale generation and a foreign issuer. Permit only its declared authority/effect boundary. Include rolled-back pending job/registration tokens, unknown bootstrap/migration/downstream acknowledgment and cleanup faults; inspect source and downstream effects independently. All schedules remain not_run. Native method-to-body identity, grants/dependencies and production evidence remain implementation outputs.
