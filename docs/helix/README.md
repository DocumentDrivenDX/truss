# truss project documentation

The current development checkpoint is Python SDK `0.0.39.dev0` / native
`0.71-candidate`; the latest published release is [v0.0.38](04-build/releases/v0.0.38.md)
(native `0.70-candidate`, Weft `0.4.41` / backend `0.4.40`). Development owned-graph
workflows cover creation, explicit subtree reparenting, cascade deletion,
read-only reads, history, receipt replay and explicit atomic owned imports with
indexed original provenance. Development compiled queries use
published Weft0.4.41 / backend0.4.41. Canonical dates and exact decimal facets
are supported by catalog acceptance, writes and reads; their broader SQL query
domains remain unfinished. Practical performance still blocks the next release,
and the integrated 1,024-operation path remains unqualified on the release
runners. See the
[unreleased tranche notes](04-build/releases/v0.0.39.md) and
[current Python interface](../../packages/python/README.md) for exact scope.

## First-release scope — owner direction, 2026-10-13

Python is the first-release public interface. Truss TypeScript implementation
maintenance and full bidirectional TypeScript/Python interchange are deferred
correctness/portability work, not first-release blocking gates. The accepted
ADR-003 amendment governs earlier contrary sequencing in this artifact.
Required Python behavioral cases, independently authored expectations, and
native state/journal/transaction evidence retain their meaning. Deferral does
not qualify interchange: an eventual claim still needs both real directions
and their original independent expectations. UMF TypeScript dependencies and
Weft's Rust compiler remain required where the Python API consumes them.

The [public Python runtime](../../packages/python/README.md) provides a concrete
embeddable interface with published Truss0.0.10/native0.47/layout0.16 candidate,
UMF0.7/0.8 and Weft0.4.12. New feature tranches are released independently;
see the package README and release notes for later exact pairings.
The tested local tuple is DocumentDrivenDX `pgserver-pg18==18.6.1`, PostgreSQL18.6
and psycopg3.3.6 binary/libpq18.6. The host supplies its authenticated connection
and owns outer transactions; Bun1.4.2 remains required for UMF preparation.

Available operations include installation/status and additive predecessor
upgrades, accepted catalogs/reports/original source, compatible scalar evolution,
exact object/key/edge reads, atomic groups/preconditions/dry-run/durable replay,
caller-owned imports, Weft queries, receipt visibility, committed feed/ACK and
retained scalar/edge history, bounded traversal, exact typed SQL pages and
compatible Record name/member-order evolution. Complete SQL projections
preserve all six scalar families, flat scalar arrays/maps and absent/null
distinctions. [Consumer handoff](04-build/consumer-readiness-handoff.md)
and [portable preview0.9](04-build/corpus/public-python/0.9/README.md) describe the
actual basic workflows and limits.

Full required corpus, stable layout, broader value/query domains and actual
managed-service qualification remain open. Independent interchange remains
deferred under the accepted owner amendment above. The separate
protected security profile is not activated by these ordinary-role workflows.
Historical component checkpoints below keep their original narrower claims.

[Query and execution ownership](01-frame/prd.md#query-and-execution-ownership--owner-direction-2026-10-11): Truss exposes the full Weft query surface. Weft owns evolving SQL coverage; Truss owns table layout, query execution, actions and other executions. Direct read/traversal APIs are convenience operations, not SQL coverage limits.

## Current Python driver and resource decision — 2026-10-11

[ADR-003](02-design/adr/ADR-003-conforming-implementations-and-shared-contracts.md#accepted-owner-amendment--python-driver-baseline-2026-10-11) selects maintained stock psycopg 3 through supported APIs as the Python baseline. [The PRD](01-frame/prd.md#owner-decision--proportional-resource-controls-2026-10-11) requires practical workload limits and transaction safety; strict transport allocation accounting is optional and cannot block baseline release. Custom PostgreSQL wire/private-hook/fork/replacement work requires hard documented proof of a necessary deficiency and an owner-approved ADR. Historical pg8000/strict-parser receipts remain scoped experiments. Driver/package/Lakebase qualification remains pending.

Current embedded target (owner direction2026-10-11): **PostgreSQL18.6**, using
reusable `pgserver-pg18==18.6.1` wheels from
[DocumentDrivenDX/pgserver](https://github.com/DocumentDrivenDX/pgserver).
Truss shares Unix-socket workers across ordinary psycopg and pg8000 tests, with
fresh databases/roles and isolated lifecycle tests. See the
[consumer checkpoint](04-build/local-runtime-installation-migration-plan.md#current-embedded-runtime-delivery--owner-decision-2026-10-11)
for exact wheel evidence and release availability. Earlier16.x/17.11 receipts
remain historical; complete runtime and managed-service acceptance remain open.

Current schema-browser projection: [core 0.8](02-design/models/truss-layout-core-structural-0.8.proposal.umf.json) includes the unchanged native 0.16 baseline plus uncomposed configuration, migration, capacity-reservation and commit-cache adjuncts: 51 Records, 491 Fields and 61 associations. The 60 prior physical FK associations are unchanged; the memo singleton PK/FK and four Fields come from UMF's original PostgreSQL declaration inventory. Native xid8 equality, SQL NULL and coupled CHECK meanings remain qualified separately. Chromium verifies 542 displayed definitions, all memo Fields, the singleton FK, exact core/cache downloads and 390px mobile layout against current UMF browser322b193. [Source correspondence](04-build/evidence/design-audit/capacity-cache-core-source.json) restores the original core0.7 exactly after removing the cache adjunct. All five native models are available separately. Protected producers, complete resource/security installation and native engine qualification remain unfinished.

Historical storage source handoff: [CONTRACT-012](02-design/contracts/CONTRACT-012-weft-storage-handoff.md) supplies the reconciled 0.12 reference-history review, its [column inventory](02-design/contracts/weft-review-columns-v0.12.proposal.md) and separate [0.12 source packet](04-build/evidence/weft-source-binding012/README.md). It retains 46 tables and 442 columns from the separately pinned 0.11 foundation; explicit journal allocator settings and the review marker change. Native installation, replay qualification and Weft mapping adoption are unfinished.


Current native component model: [source-epoch 0.16 candidate](02-design/models/truss-layout-source-epoch-0.16.proposal.umf.json), retained through UMF's PostgreSQL adapter. The earlier [qualified-property 0.15 candidate](02-design/models/truss-layout-qualified-property-0.15.proposal.umf.json) remains a historical foundation. [CONTRACT-012](02-design/contracts/CONTRACT-012-weft-storage-handoff.md) records source transitions and separate Weft fixture profiles. The browser's Truss projection 0.8 is a separate structural artifact with unadopted adjuncts, not a new UMF core version or an installed layout. Complete protected installation, semantic guards, acceptance and populated conversion remain unfinished.

Historical Python integration evidence composed all four issued native admission families on PostgreSQL16.15 with original one-use custody, shared nonrewinding issuer and confirmed savepoint/error containment. See the [92-observation receipt](04-build/evidence/design-audit/pg8000-four-family-original-admission-native.json). The [caller/elevation receipt](04-build/evidence/design-audit/admission-elevation-native.json) passes ten boundary checks, and the [joint helper inventory](04-build/evidence/design-audit/private-callable-inventory-native.json) passes 73 observations across 17 actual native routines. These administrative component receipts do not qualify ordinary protected admission, the seven missing semantic bodies, a public installation/mutation API or a published package. The private corrected pgserver wheel is an integration candidate; published pgserver0.1.4/PostgreSQL16.2 remains separately limited historical evidence.

Experimental runnable query integration lives in `packages/weft` with the pinned Rust compiler adapter in `packages/weft-bun`. Six native PostgreSQL17.9 scenarios use original SQL and native Parse/Bind. The current isolated f05f2df compiler build passes twenty-one compiler/host and loopback protocol tests with fifty-one assertions, plus strict TypeScript checking; native PostgreSQL evidence retains its separately pinned historical scope. See [iteration feedback](02-design/contracts/weft-integration-iteration-feedback.proposal.md) for reproduction scope and the filtered-SUM refusal. Fixtures do not establish accepted catalog identities, protected mutations/feed or a production executor.

truss is a planned property-oriented graph engine that runs on SQL databases,
with its schemas supplied by [UMF](https://github.com/DocumentDrivenDX/umf).
It starts as a fixed, portable set of tables with mutation, constraint and
direct-read tooling. Compiled logical queries use Weft. It consumes UMF and
never defines UMF semantics.

**Current state (2026-10-10):** requirements, architecture, contracts and
implementation/test sequencing are authored drafts for an embeddable toolkit
and Truss-owned Python/TypeScript implementations, with Python the immediate
delivery priority under accepted ADR-003. UMF owns metadata interpretation and
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
| 02 Design | ADR-001/002/003/004/005/006/007/008 accepted directions; CONTRACT-001–012 draft | [SPIKE-001](02-design/spikes/SPIKE-001-apache-age.md) (Apache AGE), [SPIKE-002](02-design/spikes/SPIKE-002-storage-bake-off.md) (storage bake-off), [storage layout review](02-design/storage-layout-review.md), [ADR-002](02-design/adr/ADR-002-storage-strategy.md) (storage, accepted 2026-10-03, some points provisional), [ADR-001](02-design/adr/ADR-001-language-and-portable-core.md) (TypeScript first, portable core, Rust triggers; accepted 2026-10-03, Node support provisional) |
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

**Next action:** implement the [protected admission execution packet](04-build/operation-ordinal-issuer-handoff.md#protected-admission-execution-packet--2026-10-10), then complete the semantic bodies and installation composition within the first PostgreSQL integration milestone in the
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


## Current delivery and HELIX adoption entrypoints

The [accelerated queue](04-build/local-runtime-installation-migration-plan.md#accelerated-capability-queue--owner-direction-2026-10-09)
prioritizes complete installation and usable Python catalog/apply/import/direct-read
operations, with R4 isolation and R5 origin in the same first slice. Feed/retry
receipts and populated migrations follow their explicit exits. The estimates are
conditional engineering targets, not delivery commitments or released capability.

| Work | Governing entrypoint / current evidence boundary |
| --- | --- |
| Python and migration integration | [Python design](02-design/python-integration.proposal.md), [installation/migration handoff](04-build/python-migration-installation-handoff.md); installed public operations remain unfinished. |
| Module boundaries | [Architecture](02-design/architecture.md#module-boundaries); Python AST gate and nine controls pass. TypeScript inventory identifies12 private cross-adapter imports; enforcement/remediation remains open. |
| Configuration | [Reference configuration contract](02-design/contracts/reference-configuration.proposal.md), [CFG test plan](03-test/reference-configuration-test-plan.md); twelve cases specified, no reference loader/composition qualification claimed. |
| Observability | [Diagnostic contract](02-design/contracts/diagnostics.proposal.md), [OBS test plan](03-test/diagnostics-test-plan.md); event/OTel/privacy/bounds defined, actual bridge/receiver/failure evidence remains open. |
| Formal analysis | [Ordinal/admission specification](02-design/python-integration.proposal.md#formal-specification--original-ordinal-and-admission-custody), [test plan](03-test/test-plan.md#formal-methods-adoption-python-original-ordinaladmission-slice); precise specification and eight component tests, no analyzer/proof or native authority claim. |
| Corrected local server | [Current17.11 runtime](04-build/local-runtime-installation-migration-plan.md#current-main-integration-of-the-embedded1711-tuple--2026-10-11);16.15 packages are retired and earlier receipts remain historical. Complete issuer/guard/ready installation remains open. |

[Project Concerns](01-frame/concerns.md#helix-guidance-adoption--2026-10-09)
records installed HELIX0.15.0 separately from the consulted committed0.15.4
modularity/configuration/observability/formal guidance. The method catalog remains
in HELIX. These documents do not add UMF semantics or a Truss SQL compiler.
See [current closure](04-build/current-design-closure.md) for the remaining native
integration gates and upstream ownership boundaries.
