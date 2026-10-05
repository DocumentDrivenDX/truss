# Working in truss

This repository uses HELIX. Read `.helix.yml` and engage the installed
`helix` skill for governed planning and documentation work.

- Keep project artifacts under `docs/helix/` in the matching activity.
- Resolve the graph, templates, and prompts from the installed HELIX plugin;
  do not copy the methodology catalog into this repository.
- Read governing upstream artifacts before authoring downstream documents.
- Preserve artifact IDs, frontmatter, and deliberate `ddx.links` traceability.
- Record unknowns explicitly as open questions, assumptions or risks.

Start with `docs/helix/README.md`. truss has discovery artifacts (product
vision, competitive analysis, naming research, discovery input, component
profiles), a storage research plan, two spikes, a storage layout review, two
accepted ADRs, one proposed ADR and four draft contracts. No PRD, feature
specifications or implementation exist yet. The
next HELIX action is `frame`: write the PRD and feature specifications.
Implementation must trace to framed requirements.

## Accepted decisions

Follow these unless a later ADR supersedes them. Points an ADR marks
provisional may change when its validation measurements report.

- [ADR-001](docs/helix/02-design/adr/ADR-001-language-and-portable-core.md):
  TypeScript (strict, ES modules), with Bun for development, tests and tooling.
  The library supports Bun and Node 22 and later LTS lines (Node provisional
  until check L1).
  - The core is its own package with no I/O, no `node:*` or `bun` imports and
    no host globals. Database adapters (`Bun.sql`, `pg`) and tooling are
    separate packages and may use host APIs.
  - Never hold a stored integer, decimal or timestamp in a JavaScript `number`
    or `Date`. Adapters return text that the core parses exactly. Decimal
    arithmetic uses truss's `bigint`-based implementation.
  - Consume UMF through its TypeScript library at a pinned version.
  - The conformance corpus is language-neutral data. Expected results and
    enforcement reports are normative; expected SQL is informative.
  - Move the core to Rust only when an ADR-001 D6 trigger fires and a new ADR
    records the evidence.
- [ADR-002](docs/helix/02-design/adr/ADR-002-storage-strategy.md): generic
  catalog storage on PostgreSQL. Adding a type, property, key or relationship
  adds catalog rows, never columns, tables, partitions or per-type indexes.
  - Objects are one table keyed on `(id, type_id)`; business identity (UMF keys)
    is in a key table, `object_key`. Values sit in one flat JSONB map per object
    keyed by catalog property id: a missing key is absent, JSON `null` is
    explicit null. Unknown data goes in the `retained` map. SPIKE-003 measured
    a partition per type and a partial index per type against this layout.
  - Edges carry typed endpoints, enforced by foreign keys against
    `rel_endpoint`, and their own properties column.
  - The object row is canonical; the journal records per-property history in
    the same transaction.
  - Database enforcement only in forms that need no DDL per revision. No
    per-type CHECK constraints on shared tables. Cross-row rules lock the
    parent (`FOR NO KEY UPDATE`) or run SERIALIZABLE; a delete uses
    `FOR UPDATE`. Writers read the catalog head row `FOR SHARE` first.
  - Prepared statements are recommended, not required. Indexes and statistics exist only where
    the binding declares them.
  - Provisional until measured: storage-home thresholds, value records stored
    as structured values with `root_id` on composed objects, edge ids, and the
    `target_type` edge-index include.

Draft contracts (layout 0.1) specify the storage layout and DDL
([CONTRACT-001](docs/helix/02-design/contracts/CONTRACT-001-storage-layout.md),
`storage-layout.sql` and its check), the journal (CONTRACT-002), catalog revision
and unknown entity types (CONTRACT-003), and the mutation protocol and
conformance corpus (CONTRACT-004). [ADR-003](docs/helix/02-design/adr/ADR-003-conforming-implementations-and-shared-contracts.md)
(proposed) lets implementations in other languages conform to them. The layout DDL
and its check pass on PostgreSQL 16.2 and 17.9; PostgreSQL 18 is untested for it.

Still open: supported PostgreSQL versions (16 and 17 verified for the layout DDL), the query language, how a future
Rust core would read UMF, and first users.

## Boundaries

- truss consumes UMF ([DocumentDrivenDX/umf](https://github.com/DocumentDrivenDX/umf))
  and never defines UMF semantics. When truss needs a concept UMF lacks, carry
  it in a truss-owned UMF extension vocabulary and propose it upstream; do not
  fork UMF meaning. truss is a UMF consumer, not UMF's reference implementation.
- truss is property-oriented: the individual property value and edge are the
  canonical unit of storage, identity and mutation. Document-shaped views are
  derived. This is the logical model; ADR-002 packs a property's value into
  its object's JSONB map, and the journal keeps per-property history. truss is distinct from Axon, which is document-oriented; do not
  describe truss as part of Axon, and do not rule out Axon using truss.
- Never silently lose meaning. Retain UMF documents verbatim, retain data that
  binds to no known field, and report for every UMF assertion whether the
  database, the engine, or nothing enforces it.
- Qualify every support claim with the database engine and version, UMF core
  version, supported subset and evidence.
