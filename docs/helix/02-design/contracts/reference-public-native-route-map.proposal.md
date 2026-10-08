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
