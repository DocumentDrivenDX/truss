# truss project documentation

truss is a planned property-oriented graph engine that runs on SQL databases,
with its schemas supplied by [UMF](https://github.com/DocumentDrivenDX/umf).
It starts as a fixed, portable set of tables and later adds query, mutation and
constraint engines. It consumes UMF and never defines UMF semantics.

**Current state (2026-09-24):** bootstrapped with HELIX genesis. Discovery
drafts exist; requirements, design and implementation do not.

| Activity | State | Entry point |
| --- | --- | --- |
| 00 Discover | Drafts | [Product vision](00-discover/product-vision.md), [competitive analysis](00-discover/competitive-analysis.md), [discovery input](00-discover/vision-input.md), [naming research](00-discover/naming-research.md), 11 [component profiles](00-discover/README.md) |
| 01 Frame | In progress | [Concerns](01-frame/concerns.md), [research plan](01-frame/research-plan.md) (storage bake-off); PRD not started |
| 02 Design | ADR-002 accepted | [SPIKE-001](02-design/spikes/SPIKE-001-apache-age.md) (Apache AGE), [SPIKE-002](02-design/spikes/SPIKE-002-storage-bake-off.md) (storage bake-off), [storage layout review](02-design/storage-layout-review.md), [ADR-002](02-design/adr/ADR-002-storage-strategy.md) (storage, accepted 2026-10-03, some points provisional); ADR-001 pending |
| 03 Test | Not started | — |
| 04 Build | Not started | No work tracker initialized |
| 05 Deploy | Not started | — |
| 06 Iterate | Not started | — |

**Build-or-adopt, storage decided:** every profiled system scored No fit, and
SPIKE-001 shows building on Apache AGE would still require most of truss. The
storage bake-off ([SPIKE-002](02-design/spikes/SPIKE-002-storage-bake-off.md))
recommends generic catalog storage (option C) over a runtime on UMF-generated
per-type tables, conditional on prepared statements, bounded per-table indexes
and engine-side enforcement. The owner accepted it in
[ADR-002](02-design/adr/ADR-002-storage-strategy.md) on 2026-10-03, with objects
partitioned by type; some points stay provisional until the follow-up spike
measures them.

**Next action:** `frame` — turn the product vision into a PRD, feature
specifications and user stories. Settle ADR-001 before any implementation.

Owner direction: PostgreSQL is the initial backing engine; implementation is
TypeScript first, with Rust only if a measured need arises.

Key open decisions: ADR-001, supported PostgreSQL versions, query language,
how truss reads UMF, and first users.
