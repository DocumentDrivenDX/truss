# Design

Record architecture, decisions, contracts, and technical designs grounded
in the project's requirements.

[SPIKE-001](spikes/SPIKE-001-apache-age.md) ran Apache AGE 1.8.0 on
PostgreSQL 18.6 against truss's required capabilities; scripts and raw outputs
are in [`spikes/SPIKE-001-apache-age/`](spikes/SPIKE-001-apache-age/).

Status: no architecture or ADRs yet. Pending decisions that design must record: ADR-001
(TypeScript on Bun first, a portable core free of I/O and host-specific APIs,
and the measurable triggers for a Rust core), supported PostgreSQL versions,
and the query language. The draft storage layers in
[discovery input](../00-discover/vision-input.md) are design input, not decisions.
