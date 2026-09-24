# Discover

Research the problem, audience, and existing solutions; use that evidence
to write `product-vision.md`.

- [Product vision](product-vision.md): draft direction for a property-oriented
  graph engine on SQL databases, typed by UMF schemas.
- [Competitive analysis](competitive-analysis.md): prior-art survey of graph
  engines on relational databases, property and fact stores, and graph query
  standards.
- [Discovery input](vision-input.md): the owner's direction, proposals not yet
  approved, the draft storage layers, the language analysis, the UMF gaps
  handed to UMF, and open decisions.
- [Naming research](naming-research.md): criteria, candidates and checks behind
  the name `truss`.
- Component profiles, all scored against the same Need and required
  capabilities C1–C12, all **No fit**:
  - PostgreSQL-based graph layers: [Apache AGE](component-profile-apache-age.md)
    (with executed evidence in [SPIKE-001](../02-design/spikes/SPIKE-001-apache-age.md)),
    [Sqlg](component-profile-sqlg.md), [PuppyGraph](component-profile-puppygraph.md),
    [Gel](component-profile-gel.md).
  - Native property-graph databases: [Neo4j](component-profile-neo4j.md),
    [Memgraph](component-profile-memgraph.md), [LadybugDB](component-profile-ladybugdb.md).
  - Fact, temporal and multi-model stores: [Datomic](component-profile-datomic.md),
    [XTDB](component-profile-xtdb.md), [SurrealDB](component-profile-surrealdb.md).
  - Reference system: [Palantir Foundry OSv2](component-profile-palantir-osv2.md),
    with [design lessons for truss](design-lessons-palantir-osv2.md).

Status: drafts from discovery sessions on 2026-09-24 and 2026-09-25. Profile
review checklists are unticked (no named reviewer yet). Audience validation,
business case and opportunity canvas have not started.
