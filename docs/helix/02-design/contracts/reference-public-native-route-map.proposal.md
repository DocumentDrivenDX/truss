# Public capability to protected native route map

Design handoff for the existing catalog/mutation/group/import/history/feed facade declarations and CONTRACT-007. Method names below are public TypeScript selectors, not new SQL signatures or native identities. Implementations keep the original public input/result contracts. Complete native dependency inventories and separately imported administrative tooling remain required before full installer readiness.

| Existing public selector | Original native responsibility and route | Required boundary before returning |
| --- | --- | --- |
| CatalogCapability.acceptInTransaction | Catalog producer: complete source admission, original acceptance/report/catalog effects and head publication last | Atomic original revision/report result is pending supplied outer transaction; no independent commit |
| CatalogCapability.report | Public report reader: complete retained report/source owner union | Fresh current authority, complete original report or explicit unavailable; not schema-head visibility alone |
| MutationCapability.applyInTransaction | Graph producer: same original operation admission/finalization path as one-operation group | Complete canonical/key/row-home/participation/current-union checks; pending IDs/results |
| GroupCapability.applyInTransaction, request none | Graph/operation/journal coordinators: complete bounded ordered semantic group | One original supplied transaction; no receipt arbitration or replay outcomes |
| GroupCapability.applyInTransaction, request present | Receipt coordinator first arbitrates original namespace/input; graph route only for admitted new request | Equal committed input returns original semantic receipt under fresh authority; conflict/expiry cannot apply; new complete receipt remains atomic with graph effects |
| ImportCapability.runBatches | Import orchestrator uses graph/group routes in separately owned batch transactions | Retain each confirmed prior batch and complete interrupted progress; whole import is not one atomic network batch |
| ImportCapability.applyInTransaction | Import orchestrator uses original supplied transaction and graph/group routes | Scope report retains outer transaction ownership; no silent inner commit or loss of earlier progress |
| HistoryCapability.pageJournal | Qualified journal reader over complete original event groups and current owner union | Exact page/boundary/protection evidence; no staged/provisional publication |
| HistoryCapability.reconstruct | Qualified history reader combines admitted original local/archive coverage | Complete historical state without current-row fallback; missing coverage explicitly unavailable |
| HistoryCapability.historicalSource | Qualified retained source reader | Exact original source/version and complete current retained-owner authority |
| FeedCapability.discoverNext | Feed reader/coordinator: admitted consumer/configuration generation and complete transaction eligibility | Original prerequisites and complete visibility; no visible-prefix discovery |
| FeedCapability.observeFreshness | Feed reader: original consumer generation, complete source/target boundary and protection observations | Freshness evidence does not advance a checkpoint or prove downstream application |
| FeedCapability.readFragment | Feed reader: selected original feed transaction/member group | Complete original fragment/cursor custody and owner-union authority; fragment completion does not acknowledge application |
| FeedCapability.acknowledgeInTransaction | Feed coordinator: original verified downstream application evidence and source checkpoint transition | Advanced/equal/conflict/unavailable per existing contract; successful source update is pending supplied outer transaction |

## Common original invocation chain

Resolve the selected capability and exact original installation/profile/source/binding generation before SQL. Admit the complete input and enclosing resource account, retain original actor/current authority and acquire original affine transaction/operation custody. Dispatch only the registered parameterized entry or admitted statement sequence for that method. A public method can require several native statements; it cannot escape issuer-wide mediation or silently replace the original transaction.

Public writers admit original operation generation/capacity, acquire the complete required exclusions, capture unavoidable old/new effects, perform original canonical mutation, collect complete affected scopes, validate final canonical/key/row-home/participation state and prepare/reserve/append complete history. Receipt and feed paths additionally preserve their original arbitration/protection prerequisites. Finalizing one operation cannot remove it from the surviving transaction's commit-check cohort. Current-union checks remain mandatory at outer commit.

Public readers use admitted ordinary disclosure routes, complete definition/decoder interpretation and original current-authority rechecks. Private observers may establish hidden integrity facts for a protected writer but cannot supply broader public read results. Compiled reads additionally run Weft's exact registered prerequisite/data/publication sequence; this map does not lower SQL or reinterpret unknown obligations.

Native command success remains distinct from operation success and confirmed outer transaction settlement. A method returning pending effects does not publish durable IDs, receipts or feed checkpoints. Owned execution publishes only after its original confirmed commit; adopted execution retains original host settlement responsibility. Cancellation, parser failure and unknown native settlement preserve original recovery and cannot replay mutation or return a lease to the pool.

## Scope still to compose

This map closes the named six-facade responsibility routes; it does not claim the complete public API inventory. Direct read/traversal, compiled execution, acceptance/runtime construction and separately imported bootstrap/migration/retention/receipt/feed administrative tooling each need their own exact registered route inventory. The public/private access plan and sixteen-selector worklist are inputs to each route's body closure, not a license to grant a family role every helper. The typed SQL view decision remains separate and pending.

Implementation must retain the method→exact native callable/statement→private dependency→store/column/sequence→actor/resource/publication correspondence and independently observe it under the existing per-story test allocations. Missing or extra native paths prevent readiness; a successful facade typecheck is not that evidence.

## Direct and compiled read entries

| Existing selector | Native route and original obligations |
| --- | --- |
| DirectReadCapability.lookup | Ordinary qualified key reader. Observe the complete routed collision cohort, compare original full namespace/tuple bytes using the admitted UMF encoding and decode the complete owned value. Reservations/guards never become live results; hidden integrity scope cannot become public disclosure. |
| DirectReadCapability.page | Ordinary qualified bounded record reader with complete selected definition/decoder and original cursor context. Each page independently admits authority and native completion; a cursor does not promise cross-page snapshot continuity. |
| DirectReadCapability.catalogView | Qualified catalog reader preserving original source/accepted revision/report owner meaning. Filtered visibility cannot claim a complete catalog inventory. |
| DirectReadCapability.traverse | Qualified bounded graph reader plus original private stage producer when selected. Complete endpoint/relationship authority and original stage/account custody remain required; stage creation is not graph mutation authority. |
| DirectReadCapability.resumeTraversal; nextTraversalPage | Original stage service verifies issuer, stage identity, generation, source/context and current authority. No reconstructed caller handle, replacement stage or stale cursor acquires continuity. |
| DirectReadCapability.releaseTraversal | Original stage service releases only its retained traversal resource under original issuer custody. This selector has no TransactionHandle and must not manufacture one, settle a host transaction or interpret resource release as rollback. |
| CompiledExecutionCapability.executeInTransaction | Registered Weft artifact bridge: exact artifact/obligation admission, native original preparation, ordered owner-wide guards, unchanged data SQL, complete private result and prepublication rechecks in the same supplied transaction. Unknown obligations refuse; this route never compiles or rewrites SQL. |

## Separately imported construction and administration

createReferenceAssembly and capability-handle selection are inert and confer no native authority. observeReadiness explicitly observes the selected original installation/profile; it cannot install objects or replace per-call admission. dispose closes assembly admission and follows original resource/recovery custody without ending adopted host transactions. Recreating an assembly cannot acquire unresolved predecessor custody.

createFeedLifecycleTooling and createReceiptLifecycleTooling are also inert projections of an existing assembly. Their configuration/profile bytes are not privilege grants. Administrative methods require their own original acting administrator, exact current native procedure rights, exclusion and recovery. Ordinary application membership cannot reach those rights through the construction export.

| Existing declared tooling family | Administrative native responsibility and mandatory separation |
| --- | --- |
| Bootstrap definition/generation/inventory/dependency reconciliation | Installation administrator enumerates full source/native effects, converts original populated state and publishes readiness only after complete correspondence. A collector/report cannot write the marker by itself. |
| KeyProfileMigrationTooling.migrate; reconcile | Original key migration administrator retains complete old/new source/key/owner/high-water custody and exact original attempt recovery. A recovery reference is a lookup locator, not permission to rerun migration. |
| RetentionTooling.dropInTransaction | Retention administrator validates original complete protection/coverage and complete selected cleanup cohort before deletion/horizon advancement. Archive observation cannot settle native commit; successful effects remain subject to supplied outer transaction. |
| ReceiptLifecycleTooling.protection; expiry | Original receipt protection/expiry coordinator enforces trusted committed observation clock, full namespace/input/result custody and monotonic protection. This is separate from graph mutation and request-free execution; expiry cannot authorize reapplication. |
| FeedLifecycleTooling.administration; registration; workers | Original consumer/configuration/worker administrator validates exact generation, proof-verifier registration and durable source/target boundaries. Admin possession cannot fabricate verified downstream application evidence. |
| FeedLifecycleTooling.extraction; confirmation; abandonment; restart | Original seed lifecycle producer retains complete seed/source/protection/cancellation and attempt custody. Independent current-authority rechecks and actual source settlement govern activation; restart cannot erase unresolved prior attempt. |
| PhysicalJobTooling admit/observe/run index/statistics methods | Physical optimization administrator admits original job in a transaction, independently observes committed admission and dispatches only that exact committed attempt. Do not run a pending attempt or change canonical meaning to make an index/statistics job pass. |
| ConformanceTooling | Explicit assessor/runner invocation over exact original corpus and selected profiles. Test/probe privileges are separately admitted; construction/import cannot provision, mutate or start a worker. Unavailable native prerequisites remain unavailable outcomes. |

This extension supplies the remaining read and administrative responsibility boundaries. The body author must still expand every tooling sub-interface to exact methods/signatures and full native callable/statement dependencies, preserving its existing declaration. Do not call the resulting inventory complete until its original declaration export closure and advertised SQL surfaces have been compared bidirectionally. Optional typed views and unresolved owner semantics cannot be silently included or omitted.

The [administrative method inventory](reference-administrative-method-routes.proposal.json) expands fourteen selected interfaces into 35 exact declaration signatures with their original responsibility and supplied/service-owned transaction boundary. Native callable identities and full dependency evidence remain unset. This selected inventory does not include bootstrap collectors, constructors or the complete transitive service/export closure.

## Bootstrap generation, installation and collection boundaries

BootstrapGenerationTooling.generate is pure bounded computation using the pinned UMF APIs and registered composition. It owns no native transaction, acquires no connection and runs no qualification tests. Supplied qualification evidence is independently readmitted; a generated candidate with unverified qualification is not a QualifiedBootstrapCandidate. Therefore this method belongs outside the native callable inventory even though it is administrative tooling.

BootstrapInstallationTooling.installFresh explicitly owns and commits an administrative transaction, rather than adopting a runtime TransactionHandle. Its input requires a qualified original candidate and actual administrative authority. Under original namespace exclusion it checks fresh-install preconditions, applies complete original effects, independently reconciles the installed inventory, publishes the marker only after admission and reports installed only after original confirmed commit. A source candidate or a visible marker alone cannot produce that result. Populated conversion stays a distinct original conversion path, never installFresh against a nonempty namespace.

BootstrapInstallationTooling.reconcileInstallation observes only the original registered attempt. It is read-only and cannot recreate the request, reapply DDL, issue a new attempt or turn absence without termination into rolled_back. Original application/cleanup/commit uncertainty retains its declared recovery result. createBootstrapInstallationTooling remains inert and does not inspect the namespace or issue attempt custody.

The current BootstrapCollectionRequest/Result and BootstrapNativeInventory declarations describe data/evidence, not a separately callable public collector service. Do not invent a collector method from their names or grant them installation rights. The installer’s private native catalog collector needs its exact statement/dependency/privilege closure under the existing collection profile and original attempt. Complete missing/extra/implicit effects, source identity, native dependency and administrative bypass checks remain the original STP-045 obligations.

This distinction removes a false method-inventory gap without claiming native collection is implemented. Bootstrap’s three actual method selectors and inert constructor are now assigned their original pure/owned/read-only boundaries; private collection remains a required installer dependency.
