---
ddx:
  id: truss.vision-input
  activity: discover
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.naming-research
      kind: informed_by
---

# Discovery Input

Source: the owner's direction on 2026-09-24, given in a design discussion held
in the UMF repository. This note separates what the owner stated from what was
proposed in that discussion and not yet approved. It is source material for the
[product vision](product-vision.md), not an approved requirements document or
evidence of implemented capabilities.

## Owner Direction

- truss is a sister project to UMF, the DocumentDrivenDX machine-readable
  metamodel and schema interchange fabric
  ([DocumentDrivenDX/umf](https://github.com/DocumentDrivenDX/umf)).
- truss is a graph engine that runs on SQL databases. It starts as a universal
  set of table structures and relationships that store and retrieve data
  efficiently from SQL. It later gains a query engine, a mutation engine and a
  constraints engine based on UMF.
- truss lives in its own repository, `DocumentDrivenDX/truss`, bootstrapped as
  a HELIX project. The name is recorded in [naming research](naming-research.md).
- truss must be differentiated from Axon
  ([DocumentDrivenDX/axon](https://github.com/DocumentDrivenDX/axon)). Axon is
  not a graph engine; it is primarily document-oriented, whereas truss is
  property-oriented. Axon may evolve to be more graph-like, and that outcome
  must not be ruled out.
- PostgreSQL is the initial backing SQL implementation.
- Implement in TypeScript first, and extend into Rust only if that is
  determined to be necessary. The owner first raised Rust with Python and Node
  bindings, because the query compiler must be fast and memory-safe and Rust
  embeds more easily than Go, then chose TypeScript first.
- The repository was created with the Apache License 2.0.

## Proposed in Discussion (not yet approved)

| Topic | Proposal | Rationale |
| --- | --- | --- |
| Relationship to UMF | truss is a **reference consumer** of UMF, not UMF's reference implementation. It depends on UMF; UMF never depends on truss. | UMF NFR-50 and its PRD non-goals place query execution and storage services in consuming systems. FR-30 and NFR-48 forbid a runtime from becoming UMF's semantic authority. |
| Claims | truss may claim bounded conformance, such as enforcing named UMF core ideals on named PostgreSQL versions, backed by fixture evidence. | Matches UMF's rule that every support claim names versions, subset and evidence. |
| Unit of storage | The individual property value and edge are canonical. Anything shaped like a document (per-object JSON caches, "document views") is derived. | Property orientation is the boundary with Axon. |
| Document view | A root object plus its composition-edge subtree can be materialized as a document view. | Leaves room for Axon, if it grows graph features, to use truss as its property and edge layer instead of duplicating one. |
| Aggregate consistency | truss reports aggregate consistency boundaries as unenforced unless explicitly modeled. | Foreign keys and edges do not enforce DDD aggregates; honest reporting is a reason to choose Axon for aggregate-shaped workloads. |
| Query language | Adopt ISO GQL (ISO/IEC 39075:2024) or SQL/PGQ (ISO/IEC 9075-16:2023) semantics and compile to SQL, using UMF for typing. | UMF defines no query semantics; inventing a language adds risk. |
| Language | TypeScript on Bun first, with a core free of I/O and host-specific APIs and a language-neutral conformance corpus, so a later Rust core can be verified against the same corpus. ADR-001 records the choice and the measurable triggers for Rust. | See the language analysis below. |

## Draft Storage Layers (design input)

Three layers were sketched. Table names, columns and indexes are design input
for `02-design`, not decisions.

1. **Schema catalog** — UMF documents stored verbatim and immutable per revision
   (content hash, exact core version, validation result), plus derived,
   rebuildable rows for elements and references. Type identity is
   (document, module, element), never a display name or namespace.
2. **Binding catalog** — per UMF element: what it binds as (node type, edge type,
   property, composition), the storage strategy (`generic` or `shaped`), loss
   mode (`strict` or `report`), and a report giving each assertion's outcome
   (exact, approximated, not-expressible, unknown) and who enforces it
   (database, engine, none).
3. **Instance graph** — a fixed table set: graph objects (nodes and edges share
   one id space), edges with endpoints and order, one row per property value
   with typed value columns (absent = no row; explicit null = a flagged row;
   array position and map key as slots), a key table using canonical byte
   encodings for exact equality, a table retaining values with no bound field,
   and a mutation journal.

Hot types can later move to a `shaped` strategy: a generated typed table with
native NOT NULL, CHECK and UNIQUE constraints. Differential tests must show both
strategies answer the same queries identically.

Prior-art input for design (see [competitive analysis](competitive-analysis.md)):
covering indexes on the property table in the style of Datomic's index orders
(entity-attribute-value and attribute-value-entity), per-type projections as in
Sqlg, and a benchmark against a hand-designed schema before the layout is
committed, since Apache Jena SDB's generic triple table lost to native storage
on performance.

Known hazards: collation-sensitive equality (SQL Server's common
case-insensitive collations), `timestamptz` dropping the original offset,
unsigned 64-bit integers exceeding `bigint`, SQL Server decimal precision capped
at 38 digits, SQLite lacking an exact decimal type, and cross-row constraints
(edge multiplicity, aggregate invariants) needing serializable transactions or
deferred checks.

## Language Analysis

Owner direction: TypeScript first; Rust only if determined necessary. The table
records the options weighed.

| Option | For | Against |
| --- | --- | --- |
| Rust core, Python and Node bindings | No runtime or garbage collector; C ABI; mature bindings (PyO3 and maturin for Python, napi-rs for Node and Bun's Node-API, wasm-bindgen for browsers); memory and data-race safety | Cannot reuse UMF's TypeScript library, so truss needs its own UMF reader built from UMF's JSON Schemas and fixtures; community-maintained SQL Server driver (tiberius); per-platform binary builds |
| Go | Simple language; good concurrency | Embedding ships a Go runtime per shared library; cgo overhead and signal-handling conflicts; awkward Python and Node bindings |
| TypeScript on Bun (HELIX shipped default) — **chosen first** | Reuses `@umf/core` directly; same language and toolchain as UMF; Bun has a built-in PostgreSQL client and `pg` covers Node; PostgreSQL does the heavy execution, so compile speed only needs to be adequate | No native Python embedding; single-threaded runtime; slower compile path |

Proposed triggers for moving the core to Rust (to confirm in ADR-001): a named
consumer requires in-process Python use, or query-compile latency or memory
misses a benchmark target that profiling cannot fix in TypeScript.

Keeping that move cheap:

- Keep the compiler and catalog core free of I/O and of Bun- or Node-specific
  APIs; database access sits behind an adapter. UMF's ADR-002 uses the same
  split (Bun for development and testing, portable library code).
- Express the conformance corpus as data: UMF documents, graph data, queries,
  expected SQL and expected results. A Rust core must pass the same corpus.

Conflict to settle in ADR-001: the HELIX `typescript-bun` concern prefers
Bun-native APIs, while a library embedded by Node applications cannot depend
on them.

## UMF Gaps Handed to UMF (2026-09-24)

The owner passed prompts for these gaps to the agent owning UMF:

1. Key: deliver TD-044, allow alternate keys per record, make keys referenceable,
   and pin equality edge cases in fixtures.
2. Relationships: association between independently identified records,
   multiplicity at each end, owned vs. independent lifecycle, relationship
   attributes, inverse names.
3. Cross-document references and revision identity (UMF FR-15 and FR-16 are
   stated; CONTRACT-001 excludes them in its bootstrap surface).
4. Schema evolution between revisions (UMF FR-17 to FR-19 are stated but not
   designed).
5. Temporal semantics: instant vs. civil values, precision, offset retention.
6. Value constraints: enumerations, ranges, minimum length, patterns with a
   declared dialect, record-level invariants.
7. Documentation: correct UMF's Axon description and add truss as a planned
   consumer.

As of 2026-09-24, UMF's tracker (`.ddx/beads.jsonl`) holds open work items for
authored relationships and physical bindings (FEAT-006, TD-045 to TD-049). No
items were observed for gaps 3 to 6.

## Open Decisions

- ADR-001: confirm TypeScript on Bun, the portable-core split, and the
  measurable triggers for a Rust core.
- PostgreSQL versions to support first. Whether and when to add SQL Server,
  which UMF already has qualified bindings for.
- Query language: GQL, SQL/PGQ, or a subset.
- Whether truss reads UMF through its own implementation or through
  pre-validated artifacts produced by UMF tooling.
- First users and workloads; audience validation has not started.
- Work tracker: the DDx tracker workspace has not been initialized in this
  repository.
