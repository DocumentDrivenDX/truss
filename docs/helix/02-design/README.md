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
option C partitioned by type, with the constraints SPIKE-002 and the review
impose. Its storage-home thresholds, composition rule, edge ids and edge index
shape are provisional until validation measurements V1–V3, V5 and V7 report.

Status: ADR-002 accepted; no architecture document yet. Pending decisions that
design must record: [ADR-001](adr/ADR-001-language-and-portable-core.md)
(TypeScript on Bun first, a portable core free of I/O and host-specific APIs,
and the measurable triggers for a Rust core; **proposed**, awaiting the owner's
decision), supported PostgreSQL versions,
and the query language. The draft storage layers in
[discovery input](../00-discover/vision-input.md) are design input, not decisions.
