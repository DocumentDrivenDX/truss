---
ddx:
  id: truss.concerns
  type: concerns
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.product-vision
      kind: informed_by
    - id: truss.vision-input
      kind: informed_by
---

# Project Concerns

Project Concerns declare active cross-cutting context for downstream work. They
are not principles, requirements, ADRs, test plans, or implementation tasks.
These are the initial selections implied by the [product vision](../00-discover/product-vision.md)
and [discovery input](../00-discover/vision-input.md); `frame` refines them.

## Active Concerns

| Concern | Source | Areas | Why Active | Key Practices |
|---------|--------|-------|------------|---------------|
| `typescript-bun` | library; slot `language-runtime`; source `shipped-default`, matching owner direction 2026-09-24 (TypeScript first, Rust only if necessary) | `area:*` | truss reuses UMF's TypeScript library and toolchain. | Library practices, with the portable-core override below. ADR-001 confirms the choice and the triggers for a Rust core. |
| `postgresql` | project-local; slot `datastore`; source `operator-override` (owner direction 2026-09-24) | `area:storage`, `area:catalog`, `area:query`, `area:mutation`, `area:constraints`, `area:dialects` | PostgreSQL is the initial backing SQL implementation; the library has no `datastore` members. | Supported PostgreSQL versions named in every claim; evidence from real PostgreSQL instances; PostgreSQL-specific SQL confined to `area:dialects`. |
| `relational-data-modeling` | library | `area:storage`, `area:catalog` | truss's own fixed table set and any generated per-type tables are relational schemas that must stay correct across releases. | Keys, constraints, indexing strategy and migration discipline for truss's own tables. |
| `scope-discipline` | library | `area:*` | "Universal tables" invites gold-plating ahead of framed requirements. | Build only what governing acceptance criteria request; no hollow placeholders. |
| `testing` | library | `area:*` | Every storage, query and constraint behavior needs executable evidence. | Tests trace to acceptance criteria; never skip failing tests. |
| `verification` | library | `area:*` | Claims about database behavior must come from running real engines. | Observed evidence against real PostgreSQL instances before a claim. |
| `umf-fidelity` | project-local | `area:catalog`, `area:storage`, `area:constraints`, `area:query` | truss inherits UMF's rule that meaning is never silently lost. | Retain UMF documents verbatim per revision; retain data with no bound field; record per assertion whether the database, the engine, or nothing enforces it; support `strict` and `report` loss modes; carry gaps upstream to UMF instead of forking semantics. |
| `sql-exactness` | project-local | `area:storage`, `area:query`, `area:constraints`, `area:dialects` | SQL defaults silently change values and comparisons unless storage is chosen deliberately. | Exact equality through `COLLATE "C"` or canonical byte encodings for keys; exact decimals; explicit temporal bindings (`timestamptz` discards the original offset); integer range checks; cross-row constraints under an explicit isolation strategy; differential tests between `generic` and `shaped` storage. |

Slots not filled: `architecture-style` (no signal yet). `frontend-framework`,
`e2e-framework`, `auth-provider` and `deploy-target` do not apply to a library
with no UI or hosted service. Not active yet: a Rust core with Python and Node
bindings (`rust-cargo`), which becomes a candidate only when an ADR-001 trigger
fires; SQL Server as a second backing engine.

## Project Overrides

| Concern | Practice | Override | Authority |
|---------|----------|----------|-----------|
| `typescript-bun` | Use Bun-native APIs (`Bun.sql`, `Bun.file`, …) | The compiler and catalog core stay free of I/O and of Bun- or Node-specific APIs so Node applications can embed truss; Bun-native APIs are allowed in database adapters, tooling and tests. Follows the split in UMF's ADR-002. | Needs ADR (ADR-001) |

## Area Labels

This project uses the following area labels for concern scoping:

- `area:catalog` — UMF schema storage, revisions and derived catalog rows
- `area:storage` — the fixed instance tables and generated per-type tables
- `area:query` — query compilation and result shaping
- `area:mutation` — writes, transactions and the mutation journal
- `area:constraints` — enforcement of UMF assertions and enforcement reporting
- `area:dialects` — engine-specific SQL generation and behavior
- `area:tooling` — build, CI, packaging and test infrastructure

## Concern Conflicts

| Conflict | Resolution |
|----------|------------|
| `umf-fidelity` vs. performance work (per-type tables, caches) | Optimizations must not change observable results; differential tests compare optimized and generic paths on the same corpus. |
| `postgresql` vs. portable "universal" tables | Build and prove on PostgreSQL first; keep engine-specific SQL behind `area:dialects` so a second engine is additive, without claiming portability before it is tested. |
| `scope-discipline` vs. a "universal" storage ambition | Universality is a design constraint on the table set, not licence to build unframed engines early. |
