# truss project documentation

Current schema-browser projection: [core 0.6](02-design/models/truss-layout-core-structural-0.6.proposal.umf.json) includes the unchanged native 0.16 baseline plus the uncomposed operation-configuration and migration-receipt adjuncts: 50 Records and 481 Fields. Physical FK associations use core record/field references with retained native descriptors; portable xid8 key equality remains unavailable. All three native sources download byte-exactly. Chromium verifies 532 displayed definitions, configuration/migration columns and mobile layout. Private immutable guards have rollback-only component evidence; protected producers, complete cleanup and installed native parity remain unfinished.

Historical storage source handoff: [CONTRACT-012](02-design/contracts/CONTRACT-012-weft-storage-handoff.md) supplies the reconciled 0.12 reference-history review, its [column inventory](02-design/contracts/weft-review-columns-v0.12.proposal.md) and separate [0.12 source packet](04-build/evidence/weft-source-binding012/README.md). It retains 46 tables and 442 columns from the separately pinned 0.11 foundation; explicit journal allocator settings and the review marker change. Native installation, replay qualification and Weft mapping adoption are unfinished.


Current native component model: [0.15 qualified-property candidate](02-design/models/truss-layout-qualified-property-0.15.proposal.umf.json), generated through UMF's PostgreSQL adapter. It preserves the Field declaration module and qualifies property identity independently of the owning Record. [CONTRACT-012](02-design/contracts/CONTRACT-012-weft-storage-handoff.md) documents the exact transition from historical 0.13/0.14 and separate Weft fixture profiles. The [native component guide](../../packages/postgresql/README.md#private-native-catalog-components) gives pinned-owner build and isolated PostgreSQL reproduction commands. Complete protected installation, matching/validation/report/finalization and populated conversion remain unfinished; the core ER model retains its separate native equality/nullable-unique gaps.

Experimental runnable query integration lives in `packages/weft` with the pinned Rust compiler adapter in `packages/weft-bun`. Six native PostgreSQL17.9 scenarios use original SQL and native Parse/Bind. The current isolated f05f2df compiler build passes twenty-one compiler/host and loopback protocol tests with fifty-one assertions, plus strict TypeScript checking; native PostgreSQL evidence retains its separately pinned historical scope. See [iteration feedback](02-design/contracts/weft-integration-iteration-feedback.proposal.md) for reproduction scope and the filtered-SUM refusal. Fixtures do not establish accepted catalog identities, protected mutations/feed or a production executor.

truss is a planned property-oriented graph engine that runs on SQL databases,
with its schemas supplied by [UMF](https://github.com/DocumentDrivenDX/umf).
It starts as a fixed, portable set of tables with mutation, constraint and
direct-read tooling. Compiled logical queries use Weft. It consumes UMF and
never defines UMF semantics.

**Current state (2026-10-09):** requirements, architecture, contracts and
implementation/test sequencing are authored drafts for an embeddable toolkit
and TypeScript reference implementation. UMF owns metadata interpretation and
portable key encoding; Weft owns SQL compilation. UMF is sufficient for the current scope; Truss owns composing its existing APIs
and verifying the generated/native layout. Semantic closure and Weft binding
adoption remain open.
See [design coordination](04-build/design-coordination.md) for source baselines,
interface dependencies and unresolved gates.

**Storage handoff priority (2026-10-08):** start with [CONTRACT-012](02-design/contracts/CONTRACT-012-weft-storage-handoff.md), then its [installation gap matrix](02-design/contracts/weft-review-installation-gap-matrix.proposal.md). The 0.12 review supplies exact owner-export DDL and declaration custody; the 0.11 compiler packet and baseline 0.2 remain separately documented. The source packet exercises a synthetic required-string fixture and does not establish the Account/Item reference registration or an installed layout.

| Activity | State | Entry point |
| --- | --- | --- |
| 00 Discover | Drafts | [Product vision](00-discover/product-vision.md), [competitive analysis](00-discover/competitive-analysis.md), [discovery input](00-discover/vision-input.md), [naming research](00-discover/naming-research.md), 11 [component profiles](00-discover/README.md) |
| 01 Frame | In progress | [Concerns](01-frame/concerns.md), [research plan](01-frame/research-plan.md) (storage bake-off); [PRD](01-frame/prd.md), [feature registry](01-frame/feature-registry.md) (8 features, 45 stories) draft |
| 02 Design | ADR-001/002/005/006/007 accepted directions; ADR-003/004 proposed; CONTRACT-001–012 draft | [SPIKE-001](02-design/spikes/SPIKE-001-apache-age.md) (Apache AGE), [SPIKE-002](02-design/spikes/SPIKE-002-storage-bake-off.md) (storage bake-off), [storage layout review](02-design/storage-layout-review.md), [ADR-002](02-design/adr/ADR-002-storage-strategy.md) (storage, accepted 2026-10-03, some points provisional), [ADR-001](02-design/adr/ADR-001-language-and-portable-core.md) (TypeScript first, portable core, Rust triggers; accepted 2026-10-03, Node support provisional) |
| 03 Test | Draft strategy; all 45 story plans allocated | [TP-001](03-test/test-plan.md), [story coverage](04-build/design-coverage.md) |
| 04 Build | Experimental Weft integration implemented; protected runtime unfinished | [Implementation plan](04-build/implementation-plan.md), [coordination](04-build/design-coordination.md) |
| Current closure | Design selections and adoption remain open | [Consolidated design closure](04-build/current-design-closure.md) |
| 05 Deploy | Not started | — |
| 06 Iterate | Not started | — |

**Build-or-adopt, storage decided:** every profiled system scored No fit, and
SPIKE-001 shows building on Apache AGE would still require most of truss. The
storage bake-off ([SPIKE-002](02-design/spikes/SPIKE-002-storage-bake-off.md))
recommends generic catalog storage (option C) over a runtime on UMF-generated
per-type tables, conditional on qualified optional preparation, bounded per-table indexes
and engine-side enforcement. The owner accepted it in
[ADR-002](02-design/adr/ADR-002-storage-strategy.md) on 2026-10-03; its layout
(one object table with a key table, no per-type DDL) was decided on 2026-10-04
after [SPIKE-003](02-design/spikes/SPIKE-003-partitioning-locks-and-prepared-statements.md)
measured the alternatives. Some points stay provisional until the follow-up
spike measures them.

**Next action:** prepare the first complete PostgreSQL integration milestone in the
[implementation plan](04-build/implementation-plan.md#first-complete-postgresql-integration-milestone),
while resolving the affected choices in the [current decision queue](04-build/design-decision-queue.md). The PRD, eight feature
specifications and 45 user stories are drafts. [Architecture](02-design/architecture.md)
defines the package and sibling-project boundaries; [design coordination](04-build/design-coordination.md)
tracks the remaining work. [ADR-001](02-design/adr/ADR-001-language-and-portable-core.md) and
[ADR-002](02-design/adr/ADR-002-storage-strategy.md) are accepted, so the
AGENTS.md precondition for code is met; implementation should still trace to
framed requirements.

Owner direction: PostgreSQL is the initial backing engine. Accepted
[ADR-003](02-design/adr/ADR-003-conforming-implementations-and-shared-contracts.md)
selects a Truss-owned, tested Python 3.11 implementation as the immediate delivery
priority, without waiting for a Rust port or a complete TypeScript engine. Weft
owns the Rust SQL compiler; authorization stays with its existing workstream.
The TypeScript core/package split remains governed by ADR-001. Both implementations
must satisfy the shared contracts and language-neutral corpus, including interchange.
The [installation and migration plan](04-build/local-runtime-installation-migration-plan.md)
selects pgserver as the default local development/test runtime, explicit installation
and migrations, one stale refusal without retry loops, document-qualified identities
and host-supplied PostgreSQL connections. Pool operations belong to the host.

Key open decisions: supported PostgreSQL versions, backend distribution and shared-interface gates,
how a future Rust core would read UMF (the TypeScript core uses UMF's library, ADR-001 D4), and first users.

Design additions: eight [feature solution designs](02-design/solution-designs/),
[embedding contract](02-design/contracts/CONTRACT-007-embedding-and-execution.md),
[bootstrap contract](02-design/contracts/CONTRACT-008-layout-bootstrap.md),
[group planning](02-design/contracts/CONTRACT-009-group-planning-and-locks.md),
and [bootstrap experiment](04-build/evidence/native-layout-capture.md). These
are drafts/candidate evidence. All 45 story design/test pairs are allocated;
structural coverage does not establish semantic completeness or execution readiness.


The [decision queue](04-build/design-decision-queue.md) is the current closure
index for all eleven design gates. The implementation plan contains separate
ID01–ID05 catalog identity and M-01–M-07 migration handoffs alongside group,
read, import, transform, optimization, compiler bridge and conformance sequences.
Each distinguishes authored design, owner adoption and later native qualification.
Start implementation review from those handoffs rather than chronological evidence
notes or an isolated SQL draft.

Recent catalog/migration refinements cover complete retained-ID allocation,
bidirectional relationship mapping, atomic same-store key replacement, guard
generation capacity, converted-reservation archive custody and signed legacy
catalog-ID transport. Proposed signed bucket namespace v0.2 requires explicit
migration; it does not reinterpret v0.1 or renumber historical IDs. Retirement
reactivation follows the owner-selected same-authored-identity policy after full validation. Truss-owned composition and generated/native correspondence using existing UMF
capabilities remain open, alongside Weft mapping adoption and native parameter review.

Current checks establish scoped draft schema/type/source properties only. The
relationship physical labels have reproducible source-binding/refusal checks;
UMF source archives have scoped capture/reload/export receipts. The selected
guard composition has 23 statements/142 authored effects, including three
edge-limit observers; it remains noninstallable and lacks complete native inventory.
The [current enforcement handoff](04-build/design-decision-queue.md#row-home-handoff-audit)
connects operation resolution, final-state marker maintenance and native schedules.
These checks do not prove generated installation or database enforcement. The
SQL drafts remain unapplied; runtime, role, race, resource and performance
qualification follows the selected implementation/test prerequisites.

Recent acceptance work specifies protected native phases, fixed catalog update
masks, semantic effect inventories and complete exact-repeat byte comparison.
Separate immutable acceptance-report storage is selected: produce the complete
report after original events and before head publication, atomically with the
catalog and journal. Exact producer/security/conversion profiles and native
qualification remain open; the report-storage product decision is settled.

Direct-read work now includes fixed page/lookup SQL, native-to-record projection,
separate finite page/lookup budgets and protected private bucket-context rules.
Integral and JSONB columns project as text; native timestamp text includes
same-statement format settings, and private matched bytes use explicit hex.
The current-authority coordinator has a participant wait/drain matrix. These
are authored proposals and scoped source evidence, with exact decoder, native
entrypoint, original-context registry and deployed profile adoption still open.

Current feed handoff includes explicit registration/finalization sources, four-store trigger scheduling, distinct proposed physical/reference identity inventories and shared write-free validation/authority/test procedures. The decision queue now separates these authored inputs from still-unselected native helper/profile/producer/privilege composition. Weft’s committed original Record preparation and projection metadata bridge are reflected in coordination; executable codecs, public result integration and genuine Truss native qualification remain open. These refinements add no UMF work prerequisite or alternate SQL compiler.


Current implementation handoffs select SQL/PLpgSQL orchestration, explicit attributes and protected ownership for seven required routines, with [source-pinned routine design](02-design/contracts/reference-routine-design-v0.1.proposal.json) and thirteen original trigger links. The [package delivery design](02-design/package-delivery.proposal.md) maps all eighteen authored function exports and the selected core numeric carrier types. Exact native bodies/profiles and published package/dependency selection remain open.

Current TypeScript compiler integration pins committed Weft f05f2df after an isolated build and twenty-one Truss regression tests. See the [regression receipt](04-build/evidence/design-audit/weft-f05f2df-truss-regression.json) and [owning-core0.8 source review](04-build/design-coordination.md#additive-weft-owning-core08-admission--2026-10-09). The public TypeScript model type remains core0.7; Python and browser builds retain their separate historical pins. Original core0.8 source admission is available upstream, but Truss has not qualified its full consumer projection, native execution or security composition. Earlier [source synchronization](04-build/evidence/design-audit/weft-post-integration-source-sync.json) remains historical evidence.


Truss must ship explicit migration tooling in its first release, with infrequent use as the intended operating model. Ordinary UMF model evolution remains DDL-free; opening an application connection never upgrades the installation. The [migration deployment handoff](04-build/migration-consumer-deployment-handoff.md) defines source/target selection, transactional apply, original-attempt recovery and clean-package qualification. A complete populated route remains unselected, and the executor/recovery/package stages remain unimplemented; the metadata planner and immutable receipt guards do not establish the shipped system.
