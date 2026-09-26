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

Status: no architecture or ADRs yet. Pending decisions: a storage ADR
ratifying or rejecting SPIKE-002's recommendation, and that design must record: ADR-001
(TypeScript on Bun first, a portable core free of I/O and host-specific APIs,
and the measurable triggers for a Rust core), supported PostgreSQL versions,
and the query language. The draft storage layers in
[discovery input](../00-discover/vision-input.md) are design input, not decisions.
