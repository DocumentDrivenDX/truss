# Design

Record architecture, decisions, contracts, and technical designs grounded
in the project's requirements.

[SPIKE-001](spikes/SPIKE-001-apache-age.md) ran Apache AGE 1.8.0 on
PostgreSQL 18.6 against truss's required capabilities; scripts and raw outputs
are in [`spikes/SPIKE-001-apache-age/`](spikes/SPIKE-001-apache-age/).
[SPIKE-002](spikes/SPIKE-002-storage-bake-off.md) ran the storage bake-off from
the [research plan](../01-frame/research-plan.md) on PostgreSQL 17.11 and 18.6,
with evidence in [`spikes/SPIKE-002-storage-bake-off/`](spikes/SPIKE-002-storage-bake-off/);
it recommends generic catalog storage (option C), with generated per-type tables
as a later optimization.
The [storage layout review](storage-layout-review.md) checks that layout
against graph-on-SQL practice, records which concerns SPIKE-002 settled, and
lists decisions and follow-up measurements for the storage ADR.

[ADR-002](adr/ADR-002-storage-strategy.md), **accepted** 2026-10-03, adopts
option C with one object table and a key table, with the constraints
SPIKE-002, SPIKE-003 and the review impose. Its storage-home thresholds, composition rule, edge ids and edge index
shape are provisional until validation measurements V1–V3, V5 and V7 report.

[ADR-001](adr/ADR-001-language-and-portable-core.md), **accepted** 2026-10-03,
confirms TypeScript with Bun for development, a host-neutral core in its own
package with Bun and `pg` adapters, exact value handling, and four recorded
triggers for a Rust core; Node support is provisional until check L1.

[CONTRACT-001](contracts/CONTRACT-001-storage-layout.md) (storage layout, with the
executable DDL [`storage-layout.sql`](contracts/storage-layout.sql) and its
[check](contracts/storage-layout.check.sql)), [CONTRACT-002](contracts/CONTRACT-002-journal.md)
(journal), [CONTRACT-003](contracts/CONTRACT-003-catalog-revision.md) (catalog
revision, ordered import and unknown entity types) and
[CONTRACT-004](contracts/CONTRACT-004-mutation-and-conformance.md) (mutation
protocol and the language-neutral conformance corpus) specify ADR-002 so that more
than one implementation can share the tables. They are drafts governed by the current PRD and feature requirements. [ADR-003](adr/ADR-003-conforming-implementations-and-shared-contracts.md)
(proposed) records how implementations in other languages conform.

## Current design set

Exact value and read-path procedures are in [CONTRACT-010](contracts/CONTRACT-010-exact-value-transport.md), with execution/occurrence custody in [CONTRACT-007](contracts/CONTRACT-007-embedding-and-execution.md). Current candidates include full scalar/state/tree observations, complete-owner reconciliation and a bounded selected-state batch route. Source archives and independent AST/manifest checks establish only their named correspondence; native profiles and Weft ABI/encoding adoption remain open. Use the implementation plan's consolidated native-value/compiled-read handoff for dependencies and primary tests. UMF remains the sufficient metadata baseline; Weft retains compilation and field resolution.



Public assembly candidates now expose [direct reads](contracts/bindings/truss-direct-read-capability-v0.1.d.ts) and [catalog acceptance/report retrieval](contracts/bindings/truss-catalog-capability-v0.1.d.ts), with an explicit [host recovery registry](contracts/bindings/truss-recovery-registry-v0.1.d.ts). [Accepted/rejected report types](contracts/bindings/truss-acceptance-report-v0.1.d.ts) preserve complete inventories and distinguish semantic results from outer transaction durability. These are reviewable draft interfaces, not published runtime capabilities.


Key admission is specified in [CONTRACT-003](contracts/CONTRACT-003-catalog-revision.md), with the [key-binding declaration](contracts/bindings/truss-key-bindings-v0.1.d.ts) separating UMF portable identity from Truss storage uniqueness. The binding preserves exact owning-Record and ordered property provenance. UMF has confirmed this scoped semantic split; native equality, guard procedures, migration and version-pinned public encoder consumption remain qualification gates. [CONTRACT-001](contracts/CONTRACT-001-storage-layout.md) describes the proposed large-key bucket profile, and [ADR-006](adr/ADR-006-exact-numeric-value-carriers.md) records the separately qualified decimal proposal.

The draft [architecture](architecture.md) defines an embeddable TypeScript toolkit and reference implementation. Weft owns source compilation; UMF owns metadata semantics. Eight [solution designs](solution-designs/) cover the features. CONTRACT-007–011 add embedding, bootstrap, group planning, exact transport and support evidence. The [UMF model candidates](models/) have bounded import/export evidence, not live-server parity or an authority transition.

[Current decision queue](../04-build/design-decision-queue.md) owns semantic closure; [coordination history](../04-build/design-coordination.md) retains dependency observations. [Story coverage](../04-build/design-coverage.md) records all 45 technical design/test pairs and 167 primary criterion allocations. [TP-001](../03-test/test-plan.md) supplies aggregate verification; the [implementation plan](../04-build/implementation-plan.md) separates authored design, reviewed design and qualified implementation. Material semantics and affected owner review still prevent full execution readiness; story artifacts are no longer missing.

ADR-001 and ADR-002 remain accepted; ADR-003–007 remain proposed. Native target qualification and backend distribution need decisions/evidence. Weft's active compiler work does not imply a Rust rewrite of Truss. See the [upstream refresh](../04-build/evidence/upstream-interface-refresh.md) before changing catalog identity or read mappings.

Callable facade additions: [retained history](contracts/bindings/truss-history-capability-v0.1.d.ts), [feed discovery](contracts/bindings/truss-feed-discovery-v0.1.d.ts), [feed delivery/acknowledgment](contracts/bindings/truss-feed-capability-v0.1.d.ts) and [compiled execution](contracts/bindings/truss-compiled-execution-capability-v0.1.d.ts). Declaration consumer witnesses enforce result distinctions only; registered bridge/proof/native profiles and outstanding seed/journal APIs and native worker/freshness profile qualification remain in the design decision queue.

[Host feed proof verifier](contracts/bindings/truss-feed-proof-verifier-v0.1.d.ts) is optional host-service injection, with a host-owned lifetime and runtime issuer custody. It does not implement a downstream database adapter or qualify cross-store durability.

[Worker acquisition tooling](contracts/bindings/truss-feed-worker-administration-v0.1.d.ts) preserves original procedure pins and separates pending acquisition from fresh committed observation. Initial consumer registration and downstream installation are separate authored declarations below; native profile qualification remains.

[Initial feed registration](contracts/bindings/truss-feed-registration-v0.1.d.ts) distinguishes pending protected registration, independently observed committed awaiting-seed state and active consumer progress. Native protection/commit observation remains a qualification gate.

[Host downstream installation adapter](contracts/bindings/truss-feed-downstream-adapter-v0.1.d.ts) preserves durable progress, generation fencing and original uncertain-attempt evidence. Its consumer witnesses reject pending claims and contradictory installed/unavailable states; native adapter qualification remains open.

[Complete-feed freshness](contracts/bindings/truss-feed-freshness-v0.1.d.ts) observes confirmed source progress and all required fact kinds under a qualified original fact-clock profile. Timing metadata/producer coverage and coherent native observation remain unqualified.

[Downstream seed activation](contracts/bindings/truss-seed-downstream-adapter-v0.1.d.ts) and [source confirmation](contracts/bindings/truss-seed-confirmation-v0.1.d.ts) are separate host/tooling calls. Consumer witnesses distinguish protected versus staged seeds, downstream uncertain outcomes and pending source durability. Extraction/staging APIs and exact native custody/activation/confirmation profiles remain open.

[Initial seed extraction](contracts/bindings/truss-seed-extraction-v0.1.d.ts) and [staging](contracts/bindings/truss-seed-staging-v0.1.d.ts) are explicit tooling/host calls. Failed or unresolved extraction exposes no partial baseline/classifier/inventory; stage success requires confirmed complete custody. Replacement extraction admission is authored in the extraction declaration; exact artifact wire/native profiles and fresh-attempt restart native admission/observation profiles remain open.

[Seed abandonment](contracts/bindings/truss-seed-abandonment-v0.1.d.ts) separates pending invalidation from verified containment/cleanup and pending source finish. Consumer witnesses prohibit active-seed invalidation, missing containment and premature durable finish. Native races and fresh-attempt restart native admission/observation profiles remain open.

[Seed restart](contracts/bindings/truss-seed-restart-v0.1.d.ts) separates pending fresh-attempt registration from independently observed committed admission; the extraction tooling consumes that exact successor. Native admission/archive/protection qualification remains open.

[Journal-only paging](contracts/bindings/truss-journal-page-v0.1.d.ts) is exposed through the history facade with exact xid/seq continuation and qualified snapshot context. Its consumer checks establish type distinctions; native watermark/retention/authority and cursor/page wire qualification remain open.

[Seed baseline/inventory declarations](contracts/bindings/truss-seed-baseline-v0.1.d.ts), [baseline schema](contracts/seed-baseline-v0.1.schema.json), [inventory schema](contracts/seed-baseline-inventory-v0.1.schema.json), [snapshot schema](contracts/seed-snapshot-evidence-v0.1.schema.json) and [retained history archive](contracts/retained-history-archive-v0.1.schema.json) now define the extraction payload inventory. Published composition fixtures pass wire/content-link checks; original native truth, complete retained membership and current authority remain profile gates.

[Host feed application adapter](contracts/bindings/truss-feed-application-adapter-v0.1.d.ts) applies complete transactions with native fence/dedup/boundary atomicity and produces submitted evidence for separate verification. Retained installation-time boundaries cannot reset current progress; native profile qualification remains open.

The [archived application evidence envelope](contracts/bindings/truss-feed-application-evidence-v0.1.d.ts) names complete original transition content and acyclic commit/verification linkage. The [closed wire schema](contracts/feed-committed-application-v0.1.schema.json) has fourteen structural probes; registered native evidence admission remains open.

The [interval coverage wire](contracts/feed-interval-coverage-v0.1.schema.json) preserves complete producer disposition evidence; semantic/native admission remains separate from its fifteen structural probes.

The [feed lifecycle tooling projection](contracts/bindings/truss-feed-tooling-v0.1.d.ts) binds the authored source registration/worker/seed methods to an existing assembly. Other tooling exports and native profile admission remain open.

The [bootstrap generation tooling](contracts/bindings/truss-bootstrap-generation-v0.1.d.ts) separates pure UMF-backed candidate generation from installation and qualified native observation. The [bundle wire](contracts/bootstrap-bundle-v0.1.schema.json) and [generation request wire](contracts/bootstrap-generation-v0.1.schema.json) have ten/eleven structural probes. The [installer/reconciliation declaration](contracts/bindings/truss-bootstrap-installation-v0.1.d.ts) includes inert construction, qualified input, original-attempt pins and explicit preflight/application/cleanup/commit uncertainty. [Namespace lock vectors](contracts/bindings/truss-bootstrap-namespace-lock-v0.1.vectors.json) and [complete bundle vectors](contracts/bindings/truss-bootstrap-bundle-v0.1.vectors.json) have four independent byte checks each. UMF is sufficient for the current scope. Truss owns complete source/composition/native correspondence using existing pinned APIs; exact native/inventory/runtime resource qualification remains open. CONTRACT-008 now defines PI01–PI07 installation ordering, a concrete generation resource proposal and bounded refusal diagnostics.

The [physical optimization](contracts/bindings/truss-physical-optimization-v0.1.d.ts), [retention maintenance](contracts/bindings/truss-retention-tooling-v0.1.d.ts) and [host conformance](contracts/bindings/truss-conformance-tooling-v0.1.d.ts) declarations expose explicit tooling boundaries. Their selected native/resource/custody profiles remain open; construction/type/wire checks do not establish runtime support. The architecture owns the consolidated package/export map, and the current decision queue distinguishes design definitions from later build qualification.

Installed-policy design now has explicit namespace/routine/relation/column/sequence grant provenance, closed privilege scopes and command-compatible tagged RLS policy carriers in [the installed-policy binding](contracts/bindings/truss-installed-policy-v0.1.d.ts). Raw ACLs and complete positive/negative native inquiries have source-preserved query proposals; [eleven independent fragments](contracts/bindings/installed-policy-comparison-v0.1.vectors.proposal.json) specify selected comparison outcomes. [CONTRACT-011](contracts/CONTRACT-011-support-evidence-receipts.md) separates native observations, stable resolved meaning, current caller authority and original evidence. The [implementation plan](../04-build/implementation-plan.md) IP01–IP07 handoff identifies remaining exact producer/decoder/encoder/administrative profiles and native qualification. No source/type/fixture check is an installed enforcement claim.
