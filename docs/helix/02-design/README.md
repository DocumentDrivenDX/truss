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
than one implementation can share the tables. They are drafts: no PRD frames
truss yet. [ADR-003](adr/ADR-003-conforming-implementations-and-shared-contracts.md)
(proposed) records how implementations in other languages conform.

Status: ADR-001 and ADR-002 accepted; ADR-003 proposed; no architecture document yet. Pending
decisions that design must record: supported PostgreSQL versions,
and the query language. The draft storage layers in
[discovery input](../00-discover/vision-input.md) are design input, not decisions.
