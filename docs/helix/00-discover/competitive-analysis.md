---
ddx:
  id: truss.competitive-analysis
  type: competitive-analysis
  activity: discover
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.vision-input
      kind: informed_by
---

# Competitive Analysis

Scope: graph storage and querying on PostgreSQL, the initial backing engine,
plus adjacent graph and fact stores that teams use instead. Survey date
2026-09-24. Confidence per claim: **primary** (read directly on GitHub or in
the PostgreSQL git history), **secondary** (search-engine summaries of the cited
page) or **unverified** (background knowledge, not re-checked).

Terms: **GQL** is ISO/IEC 39075:2024, the ISO graph query language.
**SQL/PGQ** is ISO/IEC 9075-16:2023, the SQL:2023 part that defines property
graphs over tables and the read-only `GRAPH_TABLE` operator. **openCypher** is
the open specification of Neo4j's Cypher language. **EAV** (entity-attribute-value)
is the relational pattern that stores one row per attribute value.

## Market Landscape

| Attribute | Assessment |
|-----------|------------|
| Market Maturity | Native graph databases: mature. Graph on an existing relational database: emerging. |
| Growth Rate | Not measured; no market sizing was performed (open question for the business case). |
| Key Trends | Standardization (GQL 2024; SQL/PGQ 2023, Technical Corrigendum 1 in 2026). Graph queries over data already in SQL (Oracle SQL/PGQ, PuppyGraph). Native SQL/PGQ reverted from PostgreSQL on 2026-09-07. Consolidation and exits (Kuzu archived 2025-10-10; Gel's company shut down in December 2025). |
| Entry Barriers | Medium: engineering effort and correctness evidence, not capital (assumption). |
| Buyer Power | High: capable open-source alternatives and free tiers exist (assumption). |

## Competitive Forces

| Force | Pressure | Evidence / Confidence | Implication |
|-------|----------|-----------------------|-------------|
| Direct Rivalry | Medium | Apache AGE and Sqlg are active open-source graph layers on PostgreSQL (primary). | truss must win on what they lack: property-level storage, an external schema and enforcement reporting. |
| Substitutes | High | Hand-designed per-type schemas with recursive CTEs, JSONB documents and native graph databases such as Neo4j are the status quo (assumption, widely observed). | truss must justify itself against "just write the tables" on correctness and evolution, not on raw speed. |
| New Entrants | Medium | PostgreSQL native SQL/PGQ was committed, then reverted from PostgreSQL 19 on 2026-09-07; the earliest return is PostgreSQL 20 (primary: commits `b1f106c` on master and `2b9e1af` on `REL_19_STABLE`). | A standard read path may arrive in PostgreSQL; truss should emit compatible views rather than compete with it. |
| Buyer Power | High | Free alternatives; teams can hand-build schemas (assumption). | Adoption depends on low integration cost and visible correctness evidence. |

## Competitor Profiles

| Competitor | Type | Positioning | Target Segment | Strengths | Weaknesses | Source / Confidence |
|------------|------|-------------|----------------|-----------|------------|---------------------|
| Apache AGE | Direct | openCypher inside PostgreSQL through an extension | PostgreSQL users wanting Cypher | Active releases (v1.8.0 for PostgreSQL 18 on 2026-08-06); Apache-2.0; supports PostgreSQL 11–18 | Extension not available on every managed service (unverified); properties stored per vertex as `agtype` documents, not per value (unverified); no external schema; small team by its lead developer's account | [repo](https://github.com/apache/age), [releases](https://github.com/apache/age/releases.atom): primary |
| Sqlg | Direct | Apache TinkerPop (Gremlin) on relational databases | JVM teams using Gremlin | Runs on PostgreSQL, MariaDB, MySQL, H2, HSQLDB; MIT; 3.1.6 on 2026-02-01 | One table per label (`V_<label>`, `E_<label>`), not per value; no SQL Server; JVM only | [repo](https://github.com/pietermartin/sqlg): primary; single maintainer: unverified |
| PuppyGraph | Direct (reads) | Graph queries over existing SQL and lakehouse tables without copying data | Analytics teams with data in PostgreSQL, MySQL, Iceberg, Delta | No ETL; openCypher and Gremlin; JSON schema mapping over existing tables | Proprietary (free developer edition); no write path found (unverified); separate engine | [zero-ETL post](https://www.puppygraph.com/blog/what-is-zero-etl): secondary |
| PostgreSQL native SQL/PGQ | Future substitute | Standard property graphs over tables, built into PostgreSQL | All PostgreSQL users | Standard syntax; no extension needed | Reverted from PostgreSQL 19; read-only by standard (graph DML is not in SQL/PGQ, unverified) | PostgreSQL git history: primary |
| Gel (formerly EdgeDB) | Substitute | "Graph-relational" object types and links compiled to PostgreSQL | Application developers | Rich schema language with constraints, link properties and computed properties; Apache-2.0 | Company shut down 2025-12-02 and joined Vercel; Gel Cloud closed 2026-01-31; code remains self-hostable | [repo](https://github.com/geldata/gel): primary; [shutdown post](https://www.geldata.com/blog/gel-joins-vercel): secondary |
| Datomic | Substitute (concept) | Immutable facts ("datoms": entity, attribute, value, transaction) queried with Datalog | Teams wanting history and fact-level modeling | Closest model to per-value storage; four index orders (EAVT, AEVT, AVET, VAET); free Apache-2.0 binaries since April 2023 | Closed source; SQL databases used only as opaque storage, not queryable rows (unverified) | [free announcement](https://blog.datomic.com/2023/04/datomic-is-free.html): secondary |
| XTDB v2 | Substitute | Bitemporal SQL database on its own columnar storage | Teams needing history and time travel | Speaks the PostgreSQL wire protocol; MPL-2.0; 2.0 GA 2025-06-12; v2.2.0-beta2 on 2026-09-17 | Own storage engine, document- and row-oriented | [releases](https://github.com/xtdb/xtdb/releases.atom): primary |
| Neo4j | Substitute | The reference native property-graph database | Teams willing to move graph data out of SQL | Mature model and constraints; Cypher with published GQL conformance | Data leaves the existing PostgreSQL estate; Community Edition is GPLv3 (unverified) | [GQL conformance](https://neo4j.com/docs/cypher-manual/current/appendix/gql-conformance/): secondary |

**Indirect competitors:** SQL Server SQL Graph (per-type `NODE`/`EDGE` tables
with `MATCH`; relevant if SQL Server becomes a later target; secondary). Oracle
SQL/PGQ (the most complete commercial SQL/PGQ implementation, Oracle-only;
secondary). DuckPGQ (SQL/PGQ research extension for DuckDB; analytics, not an
operational store; primary). Kuzu (embedded graph, archived 2025-10-10; fork
LadybugDB is active; secondary). Cayley (quad store with SQL backends; last
release 2019, dormant; primary). Apache Jena SDB (RDF in SQL; retired after
Jena 3.17.0 because native storage was faster; secondary). Hand-built
PostgreSQL schemas, JSONB documents and EAV tables are the most common
substitute (assumption).

## Feature Comparison

| Feature | Us | Apache AGE | Sqlg | PuppyGraph | Gel | Datomic |
|---------|----|------------|------|------------|-----|---------|
| Graph data stored in the user's PostgreSQL | Planned | Full | Full | None (queries existing tables) | Partial (own server over PostgreSQL) | Partial (opaque storage only) |
| Writes and mutations | Planned | Full | Full | None | Full | Full |
| One row per property value, readable with plain SQL | Planned | None | None | None | None | None |
| Schema supplied by an external metamodel | Planned (UMF) | None | None | Partial (JSON mapping) | Partial (own SDL) | None |
| Per-assertion report of database vs. engine vs. no enforcement | Planned | None | None | None | None | None |
| ISO-aligned query language (GQL or SQL/PGQ) | Planned (subset) | Partial (openCypher) | None (Gremlin) | Partial (openCypher) | None (EdgeQL) | None (Datalog) |
| Open-source license | Full (Apache-2.0) | Full | Full | None | Full | Partial (free binaries, closed source) |

**Legend**: Full | Partial | Planned | None. Every truss cell is Planned: no
truss code exists. The enforcement-report row reflects the survey finding that
no surveyed system reports, per rule, which layer enforces it.

## Differentiation Strategy

| Differentiator | Why It Matters | Defensibility |
|----------------|----------------|---------------|
| Property-level storage and mutation in the user's own PostgreSQL, readable with plain SQL | Per-value provenance, history and mutation without moving data to another engine; sparse and evolving types without DDL churn | M: the layout is replicable; pairing it with UMF is not |
| Schema from UMF with a per-assertion enforcement report (database, engine, none) | Teams see which rules are actually enforced; nothing is silently dropped | H: no surveyed system offers it, and it depends on UMF's fidelity model |
| Writable graph with standards-aligned reads | SQL/PGQ is read-only and absent from PostgreSQL until version 20 at the earliest | M |
| Typed storage alongside retained unknown content | Existing tools are either strict-schema (Gel, TypeDB) or schemaless documents (AGE `agtype`, XTDB) | M |

**Positioning**: For PostgreSQL teams who model connected, evolving data with
UMF schemas, truss is a property-oriented graph engine that stores and queries
that data in their own PostgreSQL database. Unlike Apache AGE, Sqlg or a
hand-built schema, truss types every property value from UMF and reports which
rules PostgreSQL enforces, which truss enforces and which nothing enforces.

## Strategic Implications

- **Attack**: PostgreSQL estates with sparse, connected, evolving data that
  already maintain UMF or TableSpec schemas; correctness and enforcement
  transparency as the lead story.
- **Defend**: UMF integration and fidelity reporting; publish evidence on named
  PostgreSQL versions.
- **Avoid**: competing on raw traversal speed with native graph databases or on
  fixed-schema analytics (DuckPGQ, PuppyGraph over lakehouses); building a
  storage engine; document-store positioning, which is Axon's space.

Risks the survey surfaced (to carry into the risk register during `frame`):
generic property tables compile graph patterns into many self-joins that SQL
planners estimate poorly (Jena SDB's retirement; Bill Karwin's *SQL
Antipatterns*); per-property integrity rules cannot use declarative
constraints, so enforcement moves into truss and faces concurrency races; the
2025–2026 exits (Kuzu, Gel, Cayley's dormancy) show how small teams stall.
Dinu and Nadkarni (2007) recommend hybrid EAV-plus-conventional designs and warn
that the metadata sub-schema becomes the complex part; in truss, UMF supplies
that metadata and optional per-type tables supply the conventional half.

**Follow-up research:** confirm AGE's storage internals and managed-service
availability; confirm whether PuppyGraph supports writes; benchmark a generic
property table against a per-type schema on PostgreSQL before design commits to
the layout; validate the target segment with prospective users.

## Sources

- PostgreSQL SQL/PGQ revert: commits `b1f106c` (master) and `2b9e1af`
  (`REL_19_STABLE`), 2026-09-07, in the [PostgreSQL GitHub mirror](https://github.com/postgres/postgres);
  context in [pgEdge](https://www.pgedge.com/blog/looking-forward-to-postgres-19-epilogue)
  and [daily.dev](https://daily.dev/posts/two-features-just-left-postgresql-v19-ezlmngmsi)
- [Apache AGE](https://github.com/apache/age), [AGE releases](https://github.com/apache/age/releases.atom)
- [Sqlg](https://github.com/pietermartin/sqlg), [Sqlg docs](https://sqlg.org/docs/3.1.0/)
- [PuppyGraph: what is zero-ETL](https://www.puppygraph.com/blog/what-is-zero-etl)
- [Gel repository](https://github.com/geldata/gel), [Gel joins Vercel](https://www.geldata.com/blog/gel-joins-vercel)
- [Datomic is free](https://blog.datomic.com/2023/04/datomic-is-free.html), [Datomic overview](https://docs.datomic.com/datomic-overview.html)
- [XTDB releases](https://github.com/xtdb/xtdb/releases.atom), [XTDB v2 launch](https://xtdb.com/blog/launching-xtdb-v2)
- [Neo4j GQL conformance](https://neo4j.com/docs/cypher-manual/current/appendix/gql-conformance/)
- [SQL Server SQL Graph overview](https://learn.microsoft.com/en-us/sql/relational-databases/graphs/sql-graph-overview?view=sql-server-ver17)
- [Oracle CREATE PROPERTY GRAPH](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/create-property-graph.html)
- [DuckPGQ](https://github.com/cwida/duckpgq-extension)
- [Kuzu archived (The Register)](https://www.theregister.com/software/2025/10/14/kuzudb-graph-database-abandoned-community-mulls-options/1142229), [Kuzu forks (gdotv)](https://gdotv.com/blog/kuzu-legacy-embedded-graph-database-landscape/)
- [Cayley](https://github.com/cayleygraph/cayley)
- [Jena SDB archive](https://jena.apache.org/documentation/archive/sdb/sdb_index.html), [Jena TDB](https://jena.apache.org/documentation/tdb/)
- [Karwin, SQL Antipatterns (slides)](https://www.slideshare.net/billkarwin/sql-antipatterns-strike-back)
- [Dinu and Nadkarni 2007, Int. J. Med. Inform.](https://www.sciencedirect.com/science/article/abs/pii/S1386505606002371)
- [ISO/IEC 39075:2024 GQL](https://www.iso.org/standard/79473.html), [ISO/IEC 9075-16 TC1:2026](https://www.iso.org/standard/93698.html), [openCypher](https://opencypher.org/)
