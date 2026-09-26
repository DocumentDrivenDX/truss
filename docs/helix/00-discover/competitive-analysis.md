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
2026-09-24; revised 2026-09-25 with eleven component profiles and one
executed spike. Confidence per claim: **primary** (read directly on GitHub, in
a maker's package, or in the PostgreSQL git history), **executed** (observed in
[SPIKE-001](../02-design/spikes/SPIKE-001-apache-age.md)), **secondary**
(search-engine summaries of the cited page) or **unverified**. Each component
profile carries its own numbered sources; this analysis cites the profile.

Terms: **GQL** is ISO/IEC 39075:2024, the ISO graph query language.
**SQL/PGQ** is ISO/IEC 9075-16:2023, the SQL:2023 part that defines property
graphs over tables and the read-only `GRAPH_TABLE` operator. **openCypher** is
the open specification of Neo4j's Cypher language. **EAV** (entity-attribute-value)
is the relational pattern that stores one row per attribute value. **BSL** is
the Business Source License, a source-available licence that restricts some
production uses until a change date.

## Market Landscape

| Attribute | Assessment |
|-----------|------------|
| Market Maturity | Native graph databases: mature. Graph on an existing relational database: emerging. |
| Growth Rate | Not measured; no market sizing was performed (open question for the business case). |
| Key Trends | Standardization (GQL 2024; SQL/PGQ 2023, Technical Corrigendum 1 in 2026). Read-only graph queries over data already in SQL: Oracle SQL/PGQ, PuppyGraph, and in 2026 Memgraph's MemGQL and LadybugDB's `pg_ladybug`. Native SQL/PGQ reverted from PostgreSQL on 2026-09-07. Consolidation and exits: Kuzu archived 2025-10-10; Gel's company shut down 2025-12-02; Memgraph and SurrealDB under BSL. |
| Entry Barriers | Medium: engineering effort and correctness evidence, not capital (assumption). |
| Buyer Power | High: capable open-source alternatives and free tiers exist (assumption). |

## Competitive Forces

| Force | Pressure | Evidence / Confidence | Implication |
|-------|----------|-----------------------|-------------|
| Direct Rivalry | Low–Medium | Apache AGE is the only active open-source graph layer inside PostgreSQL; SPIKE-001 shows it loses decimal precision, drops null-valued properties and fails concurrent writes to one vertex (executed). Sqlg stores decimals as double precision and has one active author (primary). | Rivals are weak on exactness and enforcement, the ground truss would stand on. |
| Substitutes | High | Hand-designed per-type schemas with recursive queries, JSONB documents, native graph databases, and UMF's own PostgreSQL DDL generation (UMF tracker item TD-048, open 2026-09-24; primary). UMF's projection reports already state which assertions generated DDL enforces. | truss must justify itself against "generate the tables from UMF" on schema evolution and runtime enforcement, not on raw speed. |
| New Entrants | Medium | PostgreSQL native SQL/PGQ was reverted from PostgreSQL 19 on 2026-09-07 (primary: commits `b1f106c` and `2b9e1af`). MemGQL and `pg_ladybug` read PostgreSQL tables as graphs, read-only (primary, per profiles). | The read path over PostgreSQL is commoditizing; truss should emit compatible views rather than compete on reads alone. |
| Buyer Power | High | Free alternatives; teams can hand-build or generate schemas (assumption). | Adoption depends on low integration cost and visible correctness evidence. |

## Competitor Profiles

Every system below scored **No fit** against truss's required capabilities;
the reasons are the evidence for truss's gap, not a ranking.

| Competitor | Type | Positioning | Target Segment | Strengths | Weaknesses | Source / Confidence |
|------------|------|-------------|----------------|-----------|------------|---------------------|
| Apache AGE 1.8 | Direct | openCypher inside PostgreSQL through an extension | PostgreSQL users wanting Cypher | Apache-2.0; PostgreSQL 11–18 with a PostgreSQL 19 branch; B-tree and GIN property indexes used by Cypher; Cypher writes honour unique indexes and CHECK | No temporal or binary types; decimal literals lose precision and scale; null-valued properties dropped; concurrent writes to one vertex fail with SQLSTATE XX000; triggers and foreign keys bypassed; Azure the only large cloud offering it (secondary) | [profile](component-profile-apache-age.md): primary; [SPIKE-001](../02-design/spikes/SPIKE-001-apache-age.md): executed |
| Sqlg 3.1.6 | Direct | Apache TinkerPop (Gremlin) on relational databases | JVM teams using Gremlin | Plain per-label tables in the user's PostgreSQL, readable with SQL; MIT | Decimals stored as `DOUBLE PRECISION`; absent equals null; no map values; unknown properties trigger `ALTER TABLE` or are refused; JVM only; one active author since September 2024 | [profile](component-profile-sqlg.md): primary |
| PuppyGraph 1.11 | Direct (reads) | Graph queries over existing SQL and lakehouse tables without copying data | Analytics teams | No ETL; openCypher and Gremlin | Separate proprietary server; no graph write path found; could only be a read layer over tables truss writes | [profile](component-profile-puppygraph.md): primary for licence and deployment, secondary for read-only status |
| UMF-generated per-type tables | Substitute | UMF projects its schema to PostgreSQL DDL and reports what the DDL enforces | Teams already using UMF | Native constraints, types and planner statistics; no new runtime | Every schema change is a migration; no graph query layer; runtime enforcement of rules DDL cannot express is out of UMF's scope | UMF tracker TD-048 (primary); no profile yet |
| PostgreSQL native SQL/PGQ | Future substitute | Standard property graphs over tables, built into PostgreSQL | All PostgreSQL users | Standard syntax; no extension needed | Reverted from PostgreSQL 19; read-only by standard | PostgreSQL git history: primary |
| Gel 7.1 (formerly EdgeDB) | Substitute | "Graph-relational" object types and links compiled to PostgreSQL | Application developers | Constraints enforced by PostgreSQL; `C` collation; serializable by default; lossless TypeScript client with custom codecs | Own server connecting as superuser; no null; no variable-length traversal; maker shut down 2025-12-02; no server commits since 2025-12-23 | [profile](component-profile-gel.md): primary |
| Neo4j 2026.09 | Substitute | The reference native property-graph database | Teams moving graph data out of SQL | Mature model; graph types and documented concurrency rules | No null or map properties; no decimal type; existence, type and key constraints Enterprise-only; Community GPLv3 with CLA | [profile](component-profile-neo4j.md): primary |
| Memgraph 3.13 | Substitute | In-memory Cypher graph database | Real-time analytics teams | Fast in-memory traversal; Neo4j driver compatibility | No decimal or binary type; null equals absent; BSL 1.1 bars embedding and competing works | [profile](component-profile-memgraph.md): primary |
| Datomic Pro | Substitute (concept) | Immutable facts ("datoms") queried with Datalog | Teams wanting history and fact-level modeling | Fact identity, four index orders, transactions carrying provenance, schema as data | PostgreSQL storage is one table of opaque segments (`datomic_kvs`); no null; closed source | [profile](component-profile-datomic.md): primary for storage and licence |
| XTDB 2.x | Substitute | Bitemporal SQL database on its own storage | Teams needing history and time travel | Valid and system time; PostgreSQL wire protocol; v2.2 mirrors a PostgreSQL 17+ database read-only via logical replication | Own storage engine; no schema enforcement; decimals capped at 64 digits; history per row, not per value | [profile](component-profile-xtdb.md): primary |
| SurrealDB 3.x | Substitute | Multi-model database with record links and graph relations | Application developers | `NONE` versus `NULL`; per-table strictness; relation tables with declared endpoints | Own storage engines; datetimes converted to UTC; BSL 1.1; history of silent drops fixed in 3.0 and 3.3 | [profile](component-profile-surrealdb.md): primary |
| Palantir Foundry OSv2 | Reference system | Canonical data store behind the Foundry Ontology | Foundry customers | One source per property; declared conflict policy; rebuildable indexes; migration catalogue | Foundry-only and proprietary; no binary or map type; four states returned as null; version checks admitted weak | [profile](component-profile-palantir-osv2.md), [design lessons](design-lessons-palantir-osv2.md): primary via SDKs, docs via a community mirror |

**Indirect competitors:** LadybugDB (the main Kuzu fork; embedded, one main
author; `pg_ladybug` reads PostgreSQL tables only; [profile](component-profile-ladybugdb.md)).
SQL Server SQL Graph and Oracle SQL/PGQ (relevant only if another engine
becomes a target; secondary). DuckPGQ (SQL/PGQ research extension for DuckDB;
primary). Cayley (dormant since 2019; primary). Apache Jena SDB (RDF in SQL,
retired because native storage was faster; secondary).

## Feature Comparison

| Feature | Us | Apache AGE | Sqlg | UMF-generated tables | Gel | Neo4j |
|---------|----|------------|------|----------------------|-----|-------|
| Graph data stored in the user's PostgreSQL | Planned | Full | Full | Full | Partial (own server over PostgreSQL) | None |
| Graph traversal and writes | Planned | Full | Full | None (hand-written recursive SQL) | Partial (no variable-length traversal) | Full |
| Exact values: decimals, explicit null, temporal, binary | Planned | None | None | Full (by column choice) | Partial (no null; UTC datetimes) | None |
| Schema changes without table migrations | Planned | Full (schemaless) | Partial (`ALTER TABLE` on write) | None | None | Full (schema optional) |
| Schema supplied by an external metamodel | Planned (UMF) | None | None | Full (UMF) | Partial (own SDL) | None |
| Rules enforced by the database (required, types, unique keys, endpoints) | Planned | Partial (unique and CHECK on label tables; triggers and foreign keys bypassed) | Partial (plain-table constraints; collation undocumented) | Full (native DDL where expressible) | Full | Partial (most constraints Enterprise-only) |
| Runtime enforcement of rules DDL cannot express, with a per-rule report | Planned | None | None | None (design-time report only) | None | None |
| Data with no matching definition retained | Planned | Full (subject to value losses) | Partial (adds a column or refuses) | None | None | Partial (scalars kept; maps not storable) |
| Open-source licence | Full (Apache-2.0) | Full | Full | Full | Full (maker defunct) | Partial (GPLv3 Community) |

**Legend**: Full | Partial | Planned | None. Every truss cell is Planned: no
truss code exists. Cells cite the profiles above and SPIKE-001.

## Differentiation Strategy

| Differentiator | Why It Matters | Defensibility |
|----------------|----------------|---------------|
| Exact, typed property values in the user's PostgreSQL, with schema changes that need no table migrations | Every PostgreSQL graph layer surveyed loses precision, nulls or types; generated per-type tables stay exact but migrate on every change | M: the storage idea is replicable; doing it exactly is where rivals fail |
| Runtime enforcement of UMF rules that DDL cannot express, with a report on stored data | UMF's projection reports cover what generated DDL enforces at design time; nothing enforces and reports the remainder at runtime | M: depends on UMF's fidelity model and on getting concurrency right |
| Nothing silently dropped, including data that fits no definition | Rivals drop nulls (AGE, Neo4j, Memgraph, Gel), refuse unknown fields (Gel, Sqlg) or have dropped data silently in past releases (SurrealDB) | M |

Removed on 2026-09-25: "writable graph with standards-aligned reads" (Apache
AGE already writes through openCypher) and the claim that the per-assertion
enforcement report is unique (UMF already reports design-time enforcement for
generated DDL).

**Positioning**: For PostgreSQL teams who model connected, evolving data with
UMF schemas, truss is a property-oriented graph engine that stores and queries
that data exactly in their own PostgreSQL database. Unlike Apache AGE, Sqlg or
tables generated from UMF, truss keeps every value exact without per-type
migrations and enforces, at runtime, the UMF rules that PostgreSQL cannot.

## Strategic Implications

- **Attack**: PostgreSQL estates with connected data whose shape changes often
  and that already maintain UMF or TableSpec schemas; exactness and runtime
  enforcement as the lead story.
- **Defend**: UMF integration and fidelity reporting; publish evidence on named
  PostgreSQL versions.
- **Avoid**: competing on raw traversal speed with native graph databases or on
  read-only graph views, which are commoditizing; building a storage engine,
  search tier, clustering or graph-algorithm library; document-store
  positioning, which is Axon's space.

Risks (to carry into the risk register during `frame`): generic property
storage compiles graph patterns into many self-joins that SQL planners estimate
poorly (Jena SDB's retirement; Bill Karwin's *SQL Antipatterns*); per-property
integrity rules cannot use declarative constraints, so enforcement moves into
truss and faces concurrency races; small teams stall (Kuzu, Gel, Cayley, and
single-author Sqlg and LadybugDB). Dinu and Nadkarni (2007) recommend hybrid
EAV-plus-conventional designs and warn that the metadata sub-schema becomes the
complex part; in truss, UMF supplies that metadata. Their paper has not been
read directly; this rests on a search summary.

**Follow-up research:**
- Done 2026-09-25: the bake-off between UMF-generated per-type tables and a
  minimal truss ran as [SPIKE-002](../02-design/spikes/SPIKE-002-storage-bake-off.md)
  and recommends generic catalog storage; SPIKE-001 had already answered the
  AGE option.
- Read managed providers' extension lists from an unblocked network.
- Validate the target segment and name the first consumer.

## Sources

- Component profiles in this directory: [Apache AGE](component-profile-apache-age.md),
  [Sqlg](component-profile-sqlg.md), [PuppyGraph](component-profile-puppygraph.md),
  [Gel](component-profile-gel.md), [Neo4j](component-profile-neo4j.md),
  [Memgraph](component-profile-memgraph.md), [LadybugDB](component-profile-ladybugdb.md),
  [Datomic](component-profile-datomic.md), [XTDB](component-profile-xtdb.md),
  [SurrealDB](component-profile-surrealdb.md), [Palantir OSv2](component-profile-palantir-osv2.md);
  [OSv2 design lessons](design-lessons-palantir-osv2.md).
- [SPIKE-001: Apache AGE on PostgreSQL 18](../02-design/spikes/SPIKE-001-apache-age.md).
- PostgreSQL SQL/PGQ revert: commits `b1f106c` (master) and `2b9e1af`
  (`REL_19_STABLE`), 2026-09-07, in the [PostgreSQL GitHub mirror](https://github.com/postgres/postgres);
  context in [pgEdge](https://www.pgedge.com/blog/looking-forward-to-postgres-19-epilogue).
- UMF tracker: `.ddx/beads.jsonl` in [DocumentDrivenDX/umf](https://github.com/DocumentDrivenDX/umf)
  (TD-048, PostgreSQL DDL generation), read 2026-09-24.
- [Kuzu archived (The Register)](https://www.theregister.com/software/2025/10/14/kuzudb-graph-database-abandoned-community-mulls-options/1142229)
- [Cayley](https://github.com/cayleygraph/cayley), [DuckPGQ](https://github.com/cwida/duckpgq-extension)
- [Jena SDB archive](https://jena.apache.org/documentation/archive/sdb/sdb_index.html), [Jena TDB](https://jena.apache.org/documentation/tdb/)
- [Karwin, SQL Antipatterns (slides)](https://www.slideshare.net/billkarwin/sql-antipatterns-strike-back)
- [Dinu and Nadkarni 2007, Int. J. Med. Inform.](https://www.sciencedirect.com/science/article/abs/pii/S1386505606002371)
- [ISO/IEC 39075:2024 GQL](https://www.iso.org/standard/79473.html), [ISO/IEC 9075-16 TC1:2026](https://www.iso.org/standard/93698.html), [openCypher](https://opencypher.org/)
