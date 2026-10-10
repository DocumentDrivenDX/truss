# Working in truss

This repository uses HELIX. Read `.helix.yml` and engage the installed
`helix` skill for governed planning and documentation work.

- Keep project artifacts under `docs/helix/` in the matching activity.
- Resolve the graph, templates, and prompts from the installed HELIX plugin;
  do not copy the methodology catalog into this repository.
- Read governing upstream artifacts before authoring downstream documents.
- Preserve artifact IDs, frontmatter, and deliberate `ddx.links` traceability.
- Record unknowns explicitly as open questions, assumptions or risks.

Start with `docs/helix/README.md`, then
`docs/helix/04-build/design-decision-queue.md` and
`docs/helix/04-build/remaining-design-handoff-audit.md`. The PRD, eight feature
specifications, 45 stories, architecture, contracts, implementation plan and
story test plans exist as governed drafts. Experimental Weft integration and
private PostgreSQL catalog/report components exist; they do not establish a
complete protected engine or accepted catalog. The user has authorized runtime
implementation. Trace changes to framed requirements rather than restarting
framing or requesting that authorization again.

Follow the audit's current acceptance implementation exit sequence. Preserve
original producer evidence and independently qualify native effects before
publishing an accepted revision. Never replace missing report fields with
fixture identities or empty inventories. Component checks cannot establish the
full acceptance → mutation → journal → feed → acknowledgement contract.

## Accepted decisions

Follow these unless a later ADR supersedes them. Points an ADR marks
provisional may change when its validation measurements report.

- Accepted ADR-003 amends ADR-001's Python restriction. Prioritize the Truss-owned,
  tested embeddable Python 3.11 implementation; do not wait for a Rust port or a
  complete TypeScript engine. Consume Weft's Rust Python bridge and the existing
  authorization boundary without implementing competing compiler/resolver semantics.
  Qualify both implementations against the shared corpus and native interchange.
- The owner-selected local runtime is pgserver, with explicit installation and
  infrequent migrations. The host supplies the PostgreSQL connection and operates
  any pool. Stale admission returns one refusal without internal retries. Catalog
  identity is document-qualified. Consult the current installation/migration plan
  for the observed PostgreSQL16.2 component scope and remaining complete-runtime gates.

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

CONTRACT-001 through CONTRACT-012 describe the storage, journal, catalog,
mutation, embedding, bootstrap and Weft handoff boundaries. Start physical
layout work with CONTRACT-012 and its installation gap matrix. The current
reviewed source-epoch native component model is 0.16; the separate core structural
projection is 0.6 and includes uncomposed configuration/migration adjuncts. These
are component review inputs, not a complete installed profile. Earlier layout and
compiler packets remain historical evidence and must
not be silently combined into an installed profile.

PostgreSQL 17.9 has component evidence. Supported deployment versions, complete
installation/security/resource profile adoption and full runtime qualification
remain open; consult the current decision queue for the precise scope. UMF owns
metadata semantics and reusable SQL generation; Weft owns logical SQL lowering.
Truss owns their composition, retained evidence and protected publication.

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
