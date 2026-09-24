# Working in truss

This repository uses HELIX. Read `.helix.yml` and engage the installed
`helix` skill for governed planning and documentation work.

- Keep project artifacts under `docs/helix/` in the matching activity.
- Resolve the graph, templates, and prompts from the installed HELIX plugin;
  do not copy the methodology catalog into this repository.
- Read governing upstream artifacts before authoring downstream documents.
- Preserve artifact IDs, frontmatter, and deliberate `ddx.links` traceability.
- Record unknowns explicitly as open questions, assumptions or risks.

Start with `docs/helix/README.md`. truss is in discovery: the product vision,
competitive analysis, naming research and discovery input exist; no
requirements, design or implementation exist yet. The next HELIX action is
`frame`. Owner direction: PostgreSQL is the initial backing SQL engine, and
truss is implemented in TypeScript first (Bun for development and testing),
moving to Rust only if a measured need arises. ADR-001 must confirm this, and
the portable-core split, before any code lands.

## Boundaries

- truss consumes UMF ([DocumentDrivenDX/umf](https://github.com/DocumentDrivenDX/umf))
  and never defines UMF semantics. When truss needs a concept UMF lacks, carry
  it in a truss-owned UMF extension vocabulary and propose it upstream; do not
  fork UMF meaning. truss is a UMF consumer, not UMF's reference implementation.
- truss is property-oriented: the individual property value and edge are the
  canonical unit of storage, identity and mutation. Document-shaped views are
  derived. truss is distinct from Axon, which is document-oriented; do not
  describe truss as part of Axon, and do not rule out Axon using truss.
- Never silently lose meaning. Retain UMF documents verbatim, retain data that
  binds to no known field, and report for every UMF assertion whether the
  database, the engine, or nothing enforces it.
- Qualify every support claim with the database engine and version, UMF core
  version, supported subset and evidence.
