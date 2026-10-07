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

TypeScript on Bun and PostgreSQL are the active language-runtime and datastore
selections. [ADR-001](../02-design/adr/ADR-001-language-and-portable-core.md)
and [ADR-002](../02-design/adr/ADR-002-storage-strategy.md) govern their practices.
The [product vision](../00-discover/product-vision.md) and
[discovery input](../00-discover/vision-input.md) supply the product context.

UMF is DocumentDrivenDX's metamodel and schema interchange fabric. SQL is
Structured Query Language; JSON is JavaScript Object Notation; JSONB is
PostgreSQL's binary JSON storage type. An architecture decision record (ADR)
records a technical choice. Input/output (I/O) and application programming
interfaces (APIs) mark the portable-core boundary below.

## Active Concerns

| Concern | Source | Areas | Why Active | Key Practices |
|---------|--------|-------|------------|---------------|
| `typescript-bun` | library; slot `language-runtime`; source `shipped-default`, matching owner direction 2026-09-24 (TypeScript first, Rust only if necessary) | `area:*` | truss reuses UMF's TypeScript library and toolchain. | Library practices, with the portable-core override below. [ADR-001](../02-design/adr/ADR-001-language-and-portable-core.md) (accepted 2026-10-03) confirms the choice, Node 22+ and Bun support, separate core and adapter packages, and the triggers for a Rust core. |
| `postgresql` | project-local; slot `datastore`; source `operator-override` (owner direction 2026-09-24) | `area:storage`, `area:catalog`, `area:query`, `area:mutation`, `area:constraints`, `area:dialects` | PostgreSQL is the initial backing SQL implementation; the library has no `datastore` members. | Supported PostgreSQL versions named in every claim; evidence from real PostgreSQL instances; PostgreSQL-specific SQL confined to `area:dialects`. Per [ADR-002](../02-design/adr/ADR-002-storage-strategy.md): prepared statements are recommended, with equivalent unprepared results required; one object table plus a key table, with no per-type DDL; indexes and extended statistics only where the binding declares them, with a reported index budget per table. |
| `relational-data-modeling` | library | `area:storage`, `area:catalog` | truss's fixed table set and any later shaped tables must preserve keys and integrity across releases. | Keys, constraints, indexing strategy and migration discipline for truss's own tables. |
| `scope-discipline` | library | `area:*` | "Universal tables" invites gold-plating ahead of framed requirements. | Build only what governing acceptance criteria request; no hollow placeholders. |
| `testing` | library | `area:*` | Every storage, query and constraint behavior needs executable evidence. | Tests trace to acceptance criteria; never skip failing tests. |
| `verification` | library | `area:*` | Claims about database behavior must come from running real engines. | Observed evidence against real PostgreSQL instances before a claim. |
| `umf-fidelity` | project-local | `area:catalog`, `area:storage`, `area:constraints`, `area:query` | truss inherits UMF's rule that meaning is never silently lost. | Retain UMF documents verbatim per revision; retain data with no bound field; record per assertion whether the database, the engine, or nothing enforces it; support `strict` and `report` loss modes; carry gaps upstream to UMF instead of forking semantics. Per ADR-002: unknown data kept in the `retained` map and re-bound, with a report, when a revision defines it; truss-owned binding vocabulary carried as a UMF extension and proposed upstream. |
| `sql-exactness` | project-local | `area:storage`, `area:query`, `area:constraints`, `area:dialects` | SQL defaults silently change values and comparisons unless storage is chosen deliberately. | Exact equality through `COLLATE "C"` or canonical byte encodings for keys; exact decimals; explicit temporal bindings (`timestamptz` discards the original offset); integer range checks; cross-row constraints under an explicit isolation strategy; differential tests between `generic` and `shaped` storage. Per ADR-002: JSONB read as text and parsed exactly (no default driver decoding); no implicit decimal rounding; key indexes cast to the declared type; `FOR NO KEY UPDATE` for ordinary mutations and `FOR UPDATE` for deletion; cross-row rules lock the parent or run SERIALIZABLE, and a deferred trigger alone under READ COMMITTED is not reported as database enforcement. |

Slots not filled: `architecture-style` (no signal yet). `frontend-framework`,
`e2e-framework`, `auth-provider` and `deploy-target` do not apply to a library
with no UI or hosted service. Not active yet: a Rust core with Python and Node
bindings (`rust-cargo`), which becomes a candidate only when an ADR-001 (D6) trigger
fires; SQL Server as a second backing engine.

## Project Overrides

| Concern | Practice | Override | Authority |
|---------|----------|----------|-----------|
| `typescript-bun` | Target Bun only and prefer Bun-native APIs (`Bun.sql`, `Bun.file`, …) | The catalog and operation-planning core stay free of I/O and of Bun- or Node-specific APIs so Node applications can embed truss; Bun-native APIs are allowed in database adapters, tooling and tests. The published library targets Bun and Node 22 and later LTS (long-term support) lines; Node support remains provisional until L1. | [ADR-001](../02-design/adr/ADR-001-language-and-portable-core.md) D1–D2 (accepted 2026-10-03) |
| `relational-data-modeling` | Normalize by default and enforce integrity with database constraints | Store values in an object JSONB map; enforce per-type rules through the engine or catalog-driven database validation. No per-type `CHECK` constraints on shared tables. Report the enforcement layer for each assertion. | [ADR-002](../02-design/adr/ADR-002-storage-strategy.md) D3, D9 |
| `testing` | Prefer generated data over static fixtures | Keep the language-neutral conformance corpus as data with normative expected results and enforcement reports. Seeded generated cases may supplement it. | [ADR-001](../02-design/adr/ADR-001-language-and-portable-core.md) D5 |

## Area Labels

This project uses the following area labels for concern scoping:

- `area:catalog` — UMF schema storage, revisions and derived catalog rows
- `area:storage` — the fixed instance tables and later shaped storage
- `area:query` — Weft storage mapping, read context and exact result decoding; Weft owns source compilation
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
