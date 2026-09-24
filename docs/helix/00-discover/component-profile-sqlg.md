---
ddx:
  id: truss.component-profile-sqlg
  type: component-profile
  activity: discover
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.product-vision
      kind: informed_by
    - id: truss.concerns
      kind: informed_by
    - id: truss.competitive-analysis
      kind: informed_by
---

# Component Profile: Sqlg

Desk research on Sqlg, an Apache TinkerPop (Gremlin) implementation over
relational databases, as a candidate for the graph storage and query layer
that truss would otherwise build on PostgreSQL. It is one of several profiles
for the build-or-adopt decision; the choice among candidates belongs to a
later ADR, and what the public record cannot settle is routed below. No
hands-on testing was done.

## Scope

- Component: Sqlg 3.1.6 (released 1 February 2026), the `sqlg-postgres`
  dialect, running on TinkerPop 3.7.4; documentation read from the 3.1.6
  documentation sources in the repository at commit `d769024` (31 July 2026)
- Kind: Technology (open-source Java library)
- Would fill: the graph storage and query layer inside an organization's
  existing PostgreSQL (store, traverse, update and constrain connected data
  described by UMF schemas)
- Feeds: the truss build-or-adopt ADR (not yet written); the Follow-up
  research item in [[truss.competitive-analysis]] §Strategic Implications
- Incumbent: *None*. truss has no implementation; teams use hand-built
  per-type tables, JSONB documents or a separate graph database
  ([[truss.product-vision]] §Target Market). truss has no
  current-state inventory.
- Researched: 24 September 2026
- Excluded: the H2, HSQLDB, MariaDB and MySQL dialects (truss targets
  PostgreSQL); Sqlg's graphical UI; PostgreSQL's own behaviour beyond what
  Sqlg's documentation states (postgresql.org was unreachable from this
  session); hands-on verification of any claim

## Summary

We need a graph storage and query layer that runs inside an organization's
existing PostgreSQL, for connected domain data whose shape evolves and is
described by UMF schemas, so that teams can store, traverse, update and
constrain that data without moving it, see which rules are enforced, and never
lose data silently. It must run on the PostgreSQL versions and managed services
teams use, store UMF's scalar types exactly, tell an absent property from a
null and keep lists and maps, let the database enforce declared rules, index
and traverse efficiently while composing with SQL, behave predictably under
concurrent writes, keep unrecognised data, work from TypeScript without
numeric loss, stay readable with plain SQL, be sustainably maintained, and
stay within twice the latency of a hand-designed schema. On the public record
Sqlg 3.1.6 keeps its graph as ordinary per-label tables that plain SQL can read
and uses PostgreSQL indexes, but it stores exact decimals as binary floating
point, cannot tell an absent property from a null, has no map values, is
reachable from TypeScript only through a JVM Gremlin Server whose JavaScript
client turns large 64-bit integers into floats, and has a single maintainer,
so the verdict is No fit.

## How to Read This Profile

| Word | Where | Means |
|------|-------|-------|
| **Met** | Capability Alignment status | The public record documents the capability as its Required Capabilities row defines it. |
| **Unmet** | Capability Alignment status | The public record contradicts it, or the maker states it is absent. |
| **Unknown** | Capability Alignment status | The record does not settle it; the Open Questions table routes it. |
| **Fit** | Verdict | Every required capability is Met. |
| **Conditional fit** | Verdict | Every required capability is Met or Unknown, and no Unknown is design-defining; each Unknown is an Open Question with a route. |
| **Undetermined** | Verdict | At least one design-defining capability is Unknown; the spike that would settle it is named. |
| **No fit** | Verdict | At least one required capability is Unmet. |
| **Published** | Figures | The maker states it, with source and date. |
| **Third-party estimate** | Figures | Someone other than the maker estimated it; the estimator is named. |
| **Not published** | Figures and claims | Searched and absent; the search is recorded (which pages, which date). |
| **Not researched** | Competitive Landscape cells | Nobody has looked; the sibling profile that would fill the cell is named. |
| **High / Medium / Low** | Confidence | Defined in the Confidence section. |
| **maker / vendor / independent / community** | Sources | Defined in the Sources section. |

## Need

We need a graph storage and query layer that runs inside an organization's existing PostgreSQL, for connected domain data whose shape evolves and is described by UMF schemas, so that teams can store, traverse, update and constrain that data without moving it to another database, see which rules are actually enforced, and never lose data silently. Nothing fills the role today: truss has no implementation, and teams use hand-built per-type tables, JSONB documents or a separate graph database instead. [[truss.product-vision]] §Mission Statement, §Positioning, §Target Market; [[truss.concerns]] §Active Concerns; [[truss.vision-input]] §Owner Direction.

## Required Capabilities

| # | Capability | Serves | Comes from | Settled by |
|---|------------|--------|------------|------------|
| C1 | Runs inside the user's own PostgreSQL on current major versions (17 and 18), with a path to 19, including on the managed PostgreSQL services teams commonly use. | Keep data in existing PostgreSQL | [[truss.product-vision]] §Mission Statement; [[truss.concerns]] `postgresql` | Supported-version matrix in the maker's docs or release notes; managed-provider documentation listing the extension |
| C2 | Stores values for UMF's nine scalar families exactly: boolean, integer across the signed 64-bit range, exact decimal, binary floating point, Unicode string, binary data, date, time and timestamp, without silent coercion or rounding. | Never lose data silently | [[truss.concerns]] `sql-exactness`, `umf-fidelity` | Maker's type-system documentation for property values; documented conversion and precision rules |
| C3 | Distinguishes an absent property from an explicit null, and preserves ordered lists (with duplicates) and string-keyed maps as property values. | Never lose data silently | [[truss.vision-input]] §Draft Storage Layers; [[truss.concerns]] `umf-fidelity` | Maker's documentation of null handling in properties, lists and maps |
| C4 | Lets declared rules be enforced by the database: required properties, value types and limits, unique keys under exact (binary) equality, and allowed edge endpoints, with graph writes (create, merge, set) honouring those rules. | See which rules are enforced | [[truss.product-vision]] §Key Value Propositions; [[truss.concerns]] `umf-fidelity`, `sql-exactness` | Maker's documentation or issue-tracker evidence of constraints, unique indexes or triggers on graph storage and their interaction with Cypher writes |
| C5 | Indexes property values for equality and range lookups, and the planner uses those indexes for graph queries. | Store and traverse efficiently | [[truss.product-vision]] §Success Definition (performance) | Maker's indexing documentation; independent reports or plans showing index use from Cypher |
| C6 | Supports multi-hop and variable-length traversal, pattern matching, aggregation and parameters for reads, and create, update-one-property, delete and merge for writes, and composes with ordinary SQL (joins with relational tables, use inside SQL statements). | Traverse and update connected data | [[truss.product-vision]] §User Experience | Maker's openCypher coverage and limitation lists; independent coverage |
| C7 | Provides transactional writes with defined behaviour under concurrency: atomic single-property updates, defined concurrent merge behaviour, and no lost updates at PostgreSQL's standard isolation levels. | Constrain data correctly | [[truss.concerns]] `sql-exactness` (cross-row constraints under an explicit isolation strategy) | Maker's documentation or issue-tracker evidence on concurrency and merge semantics |
| C8 | Retains property data that matches no schema definition, with values unchanged. | Never lose data silently | [[truss.concerns]] `umf-fidelity` | Maker's documentation that arbitrary maps are stored and returned with exact values |
| C9 | Is usable from TypeScript on Bun or Node without numeric precision loss when reading and writing property values. | Fit the chosen implementation language | [[truss.concerns]] `typescript-bun` | Maker's client or driver documentation; the text format of returned values |
| C10 | Keeps stored data readable by other tools through plain SQL, including conversion of property values to ordinary SQL types. | Store data where other systems can read it | [[truss.product-vision]] §Key Value Propositions | Maker's documentation of casts and functions from graph values to SQL types |
| C11 | Is maintained well enough to be a long-lived dependency: active releases, open governance, more than a handful of maintainers, and a licence that permits commercial use. | Avoid dependency risk | [[truss.competitive-analysis]] §Strategic Implications (sustainability risk) | Foundation status, release history, contributor statistics and licence text |
| C12 | Fetches single objects and traverses one to three hops with 95th-percentile latency within twice that of a hand-designed schema for the same data. | Store and traverse efficiently | [[truss.product-vision]] §Success Definition (proposed target) | Independent benchmark comparing AGE with relational or native-graph baselines on comparable workloads |

Nice to have: row-level security on graph data; shortest-path queries; ISO GQL alignment.

## What It Is

Sqlg is an open-source Java implementation of the Apache TinkerPop 3 graph
API on a relational database, supporting H2, HSQLDB, PostgreSQL, MariaDB and
MySQL [1]. It is written and maintained by Pieter Martin, whose commits make up
all non-automated changes to the main branch since September 2024 [6]. Its
stated primary challenge is to reduce latency by combining TinkerPop traversal
steps into as few database calls as possible [2]. The repository's first
commit is dated 12 July 2014 [6]; the 3.x line began with 3.0.0 on 1 March
2023 and reached 3.1.6 on 1 February 2026 [5]. It is licensed under the MIT
License [3]. On GitHub the repository shows 260 stars and 52 forks as of
24 September 2026 [7], a descriptive figure rather than an adoption survey.

- Category and purpose: a TinkerPop 3 (Gremlin) graph implementation that
  maps each vertex label to a `V_<label>` table and each edge label to an
  `E_<label>` table [8], translating traversals to SQL [2][12]
- Maker or governing body: Pieter Martin, as sole active maintainer; no
  foundation or governance document in the repository [1][6]
- Adoption, from an independent source: Not published (searched as recorded
  under Sources, 24 Sep 2026)
- Release cadence and support window: irregular tagged releases, two in
  2024 (3.1.0 on 27 April, 3.1.1 on 8 December), four in 2025 (3.1.2 on
  17 June, 3.1.3 to 3.1.5 between 14 and 18 August) and one so far in 2026
  (3.1.6 on 1 February) [5]; no support window published (searched [1][4],
  24 Sep 2026)
- Licence: MIT, permitting use, modification and redistribution, including
  commercial use, without fee [3]
- Built-for use cases: Gremlin traversals over relational storage with
  reduced round trips [2]; bulk loading through PostgreSQL `COPY` in batch
  modes [18]; horizontally split graphs through `postgres_fdw` [19]

## Capability Alignment

### C1. Runs inside the user's own PostgreSQL, 17 and 18, on managed services

Interpretation: Sqlg is neither a PostgreSQL extension nor a database server.
It is a Java library (the build requires JDK 17 or later [30]) that runs in the
application's JVM and keeps the graph as ordinary tables, `V_<label>` and
`E_<label>`, in the database it connects to over JDBC [8]. For C1 that means
the data does stay in the user's own PostgreSQL and nothing has to be
installed in PostgreSQL, so managed-provider extension allow-lists do not gate
it; what C1 then asks is which PostgreSQL versions and managed services the
maker supports. The record does not say. Neither the README, the 3.1.6
documentation nor the changelog carries a supported-version matrix [1][4][8];
the repository's test-database Dockerfile still builds from
`postgres:9.6-alpine` [21]; the only version-specific changelog entries concern
partitioning and Citus sharding on PostgreSQL 10 [4]; and an open maker issue
from 3 February 2023 proposes using the `MERGE` statement "introduced in
postgresql 15" [22]. No managed provider documents Sqlg. Two operational
caveats bear on managed services: with the default unlocked topology, writes
create tables and columns at run time, so the connecting role needs DDL
rights [11]; and several JVMs sharing one database use PostgreSQL `NOTIFY` to
distribute the schema cache [17]. A TypeScript application would also need a
separate JVM Gremlin Server process (see C9).

**Settled by**: supported-version matrix not found (searched [1][4][8][21], 24 Sep 2026); managed-provider documentation not found (searched as recorded under Sources, 24 Sep 2026)
**Status**: Unknown

### C2. UMF's nine scalar families stored exactly

Sqlg's 3.1.6 type table maps Java `Boolean` to `BOOLEAN`, `Long` to `BIGINT`,
`Double` to `DOUBLE PRECISION`, `String` to `TEXT`, `byte[]` to `BYTEA`,
`LocalDate` to `DATE`, `LocalTime` to `TIME`, `LocalDateTime` to `TIMESTAMP`,
and `ZonedDateTime` to a `TIMESTAMP` column plus a `TEXT` column [9]. It maps
`BigDecimal` to `DOUBLE PRECISION` on PostgreSQL [9], and the PostgreSQL
dialect source at the 3.1.6 tag does the same [10]: an exact decimal is stored
as binary floating point, which rounds any value that a double cannot hold.
The same table notes that `java.time.LocalTime` "drops the nanosecond
precision" [9]. Since 2.1.0 Sqlg stores timestamps without time zone and
keeps the zone separately, having removed `timestamp with time zone` columns
[4]. Integer, float, string, binary, date and boolean map to native columns;
the decimal mapping alone contradicts C2.

**Settled by**: maker's type documentation found in [9], confirmed in source [10]; exact decimal is stored as `DOUBLE PRECISION`
**Status**: Unmet

### C3. Absent versus null; ordered lists and string-keyed maps

Since 3.0.0 Sqlg supports TinkerPop's `supportsNullPropertyValues`, and the
changelog states that `isPresent` "will now return `true` if the property
exist in the schema, regardless of the value", so a null check needs
`property.isPresent() && property.value() != null` [4]. The topology
documentation's own example creates a vertex without a property and reads it
back as null [11]. Because a property is a column on the label's table [8], a
never-set property and an explicitly null one are the same stored state.
Ordered collections are supported only as typed arrays (`Boolean[]`,
`Integer[]`, `Long[]`, `String[]` and others, stored as PostgreSQL arrays) [9];
the feature list names `MapValues`, `MixedListValues` and `UniformListValues`
as not implemented for vertex and edge properties [14]. The only map-shaped
value is a Jackson `JsonNode` stored as `JSONB` [9].

**Settled by**: null handling found in [4][11]; list and map support found in [9][14]
**Status**: Unmet

### C4. Rules enforced by the database, honoured by graph writes

Interpretation: Gremlin writes (`addV`, `addE`, `property`, `mergeV`,
`mergeE`) stand in for Cypher `CREATE`, `SET` and `MERGE`. A
`PropertyDefinition` carries a type, a multiplicity, a default literal and a
check constraint; a lower multiplicity of 1 generates `NOT NULL`, an upper
bound on an array generates a `CHECK`, and any property can carry a `CHECK`
expression; the documented violations are raised by PostgreSQL itself [11].
Each property is a typed column [8][9]. Unique and non-unique indexes can be
added on any property or set of properties [12]; globally unique indexes
across labels were removed in 2.1.5 [4]. Edge tables carry one column per
adjacent vertex label with a foreign key by default, which can be switched
off for performance [8]; an `EdgeDefinition` enforces one-to-one and unique
many-to-many edges through unique indexes, while other multiplicities are not
checked automatically and are left to a `checkMultiplicity` helper [11].
Locking the topology prevents any new label, edge label or property from being
created, raising `IllegalStateException` [11]; an issue report shows that the
first edge between a new pair of labels issues `ALTER TABLE ... ADD COLUMN`
[23], so allowed endpoints hold only while the topology is locked. What the
record leaves open is exact equality: Sqlg's documentation states no collation
for its `TEXT` columns or unique indexes [9][12], so whether a unique key
compares strings byte for byte depends on a database setting Sqlg does not
document.

**Settled by**: constraints, unique indexes and their interaction with writes found in [11][12]; exact (binary) equality not found (searched [9][11][12][13], 24 Sep 2026)
**Status**: Unknown

### C5. Property indexes used by the planner for graph queries

Interpretation: Gremlin `has()` steps and `P` predicates stand in for Cypher
`WHERE`. Indexes (unique, non-unique, composite and PostgreSQL full-text GIN)
are created through the topology API and can be added at any time [12]. The
maker states that a `HasStep` on an indexed property translates to a SQL
`where` clause and that "the underlying RDBMS will utilize the index" [12];
comparison predicates resolve on the database as SQL `where` clauses, and
`within` predicates become a join onto a `VALUES` expression [13]. No
independent plan or report was found.

**Settled by**: maker's indexing documentation found in [12][13]; independent plans not found (searched as recorded under Sources, 24 Sep 2026)
**Status**: Met

### C6. Traversal, pattern matching, aggregation, writes, and SQL composition

Interpretation: Gremlin coverage stands in for openCypher coverage, and "use
inside SQL statements" means a traversal callable from a SQL statement.
Sqlg 3.1.6 runs on TinkerPop 3.7.4 [30] and states that it passes TinkerPop's
`StructureStandardSuite`, `ProcessStandardSuite` and Gherkin feature tests
[14]; the tests it opts out of are mostly null-handling cases and a few
boolean-logic error cases [15]. Graph computer, threaded transactions,
variables, multi- and meta-properties are not implemented [14]. The recursive
`repeat` step was optimised in 3.1.1 [4], and `mergeV` and `mergeE` are
exercised by the maker's tests [31], while the maker's own issue to implement
merge through SQL `MERGE` has been open since 3 February 2023 [22]. On
composition, the graph tables are ordinary tables other SQL can join [8], and
Sqlg can import existing and foreign schemas and tables into its topology
[4][19]. But the maker documents two entry points only, the embedded JVM API
and Gremlin Server, and states that none of Sqlg's custom features are
available through Gremlin Server [16]; no SQL-callable traversal is
documented.

**Settled by**: Gremlin coverage and limitations found in [14][15]; SQL composition found partly in [8][19], use inside SQL statements not found (searched [1][8][16][19], 24 Sep 2026)
**Status**: Unmet

### C7. Transactional writes with defined concurrent behaviour

Sqlg runs graph changes inside database transactions committed or rolled back
through `tx()` [11], and schema changes are transactional on PostgreSQL [11].
Since 2.1.0 it takes no locks during schema creation; the changelog calls its
earlier locking "a bad idea from the start", makes preventing deadlocks "the
responsibility of the client", and suggests retrying the transaction [4].
Because the first edge between a new pair of labels alters the edge table [23],
schema changes can occur inside ordinary writes unless the topology is locked
[11]. The issue tracker lists fixed reports of deadlocks between writing
threads and of exceptions under concurrent schema creation [24]. The
documentation states no isolation level, no atomicity rule for single-property
updates and no behaviour for concurrent `mergeV` [11][14]; merge still runs as
TinkerPop's step rather than SQL `MERGE` [22].

**Settled by**: concurrency guidance found in [4]; isolation level, single-property atomicity and concurrent merge semantics not found (searched [4][11][14][22][24], 24 Sep 2026)
**Status**: Unknown

### C8. Data that matches no schema definition is retained unchanged

With the topology unlocked, Sqlg follows TinkerPop semantics: every graph
modification checks whether the element's label and properties exist and
creates them if not [11], so an unrecognised property becomes a new typed
column in the same transaction. That column takes the type mapping of C2, so
an unrecognised decimal is stored as `DOUBLE PRECISION` [9], and map values
are not supported at all [14]. With the topology locked, an unrecognised label
or property is refused with `IllegalStateException` [11]. Retention therefore
either rewrites the schema and can change values, or is refused; the only
home for an arbitrary map is a declared `JSONB` property [9].

**Settled by**: schema-on-write and locked-topology behaviour found in [11]; value mapping found in [9][14]
**Status**: Unmet

### C9. Usable from TypeScript on Bun or Node without numeric loss

Sqlg is a JVM library [1][30]; a Node application reaches it through Gremlin
Server with TinkerPop's Gremlin-JavaScript driver [16][25], and the maker
warns that none of Sqlg's custom features (batch mode, partitions) are
available through Gremlin Server [16]. TinkerPop's documentation says
Gremlin-JavaScript "targets Node.js runtime" and does not mention Bun [25].
In the 3.7.4 driver source, the GraphBinary long deserializer converts any
value outside ±(2^53 − 1) with `parseFloat`, a documented TODO that keeps the
GraphSON contract [26]; the 3.8.2 source is unchanged [27]. Large 64-bit
integers therefore arrive in JavaScript rounded, and decimals are already
stored as doubles (C2).

**Settled by**: client documentation found in [16][25]; number decoding found in driver source [26][27]
**Status**: Unmet

### C10. Stored data readable through plain SQL with ordinary types

Interpretation: Sqlg has no graph value type to cast; the question is whether
its tables are ordinary SQL. Each vertex label is a `V_<label>` table and each
edge label an `E_<label>` table holding its properties and the adjacent
vertex ids, and the edge table is described as the classic many-to-many join
table [8]. Property values are native column types [9]; some Java types span
several columns (`ZonedDateTime` as `TIMESTAMP` plus `TEXT`, `Period` as
three `INTEGER` columns, `Duration` as `BIGINT` plus `INTEGER`) [9]. The
topology itself is stored in the `sqlg_schema` schema as a graph [11]. Values
that C2 already coerced (decimals) are read back as stored.

**Settled by**: storage layout and native column types found in [8][9][11]
**Status**: Met

### C11. Maintained well enough to be a long-lived dependency

Sqlg is MIT-licensed, which permits commercial use [3]. Releases continue:
3.1.0 on 27 April 2024 through 3.1.6 on 1 February 2026 [5], with the latest
main-branch commit on 31 July 2026 [6]. Since 24 September 2024 every
non-automated commit on the main branch, 199 in all across three e-mail
identities, is Pieter Martin's; the rest are 8 Dependabot updates [6]. The
repository carries no foundation affiliation or governance document [1], and
[[truss.competitive-analysis]] recorded the single-maintainer point as
unverified; the commit history now supports it.

**Settled by**: licence text found in [3]; release history found in [5]; contributor statistics found in [6]; foundation status not found (searched [1], 24 Sep 2026)
**Status**: Unmet

### C12. Single-object fetch and 1–3 hop traversal within 2× of a hand-designed schema

Interpretation: the row names AGE; for Sqlg the equivalent evidence is an
independent benchmark of Sqlg against a relational or native-graph baseline.
Pacaci, Zhou, Lin and Özsu (GRADES 2017) ran the LDBC Social Network Benchmark
interactive workload against several systems including Sqlg through Gremlin
Server; according to a search-engine summary of the paper, "Postgres (SQL)
significantly outperforms Sqlg (Gremlin) even though both systems have the
same underlying data model and storage engine", and the TinkerPop and Gremlin
Server integration "incur significant overhead" [28]. The paper itself was
unreachable, the Sqlg version predates the 2.x and 3.x lines, and no latency
ratio against the 2× target is available from the summary. A 2018 PVLDB
microbenchmark by Lissandrini, Brugnara and Velegrakis included Sqlg,
according to a search-engine summary; its findings could not be read [29].
No current benchmark was found.

**Settled by**: independent benchmark found only in summary form for a pre-2.x version [28]; no current benchmark found (searched as recorded under Sources, 24 Sep 2026)
**Status**: Unknown

Other notable capabilities the record documents and no criterion requires:

| Capability | What the record says | Source |
|------------|----------------------|--------|
| Shortest path (nice to have) | Partial pgRouting support, including `pgr_bdDijkstra`, on self-referencing edge labels only | [4][32] |
| Bulk loading | Normal, streaming and streaming-with-lock batch modes on PostgreSQL through `COPY` | [18] |
| Partitioning and sharding | PostgreSQL partitioning; Citus sharding added for PostgreSQL 10 | [4] |
| Foreign data wrappers | Import foreign graph schemas through `postgres_fdw`; no distributed transactions | [19] |
| Vector and GIS types | pgvector, PostGIS, `ltree`, `inet` and `cidr` property types on PostgreSQL | [4][9] |
| Identifier limit | Schema, table and column names limited to 63 characters on PostgreSQL | [20] |
| Row-level security (nice to have) | Not published (searched [8][11][20], 24 Sep 2026) | none |
| ISO GQL alignment (nice to have) | Not published; the query language is Gremlin (searched [1][14], 24 Sep 2026) | none |

**Verdict**: No fit. C2, C3, C6, C8, C9 and C11 are Unmet on the public
record: exact decimals become doubles, absent and null are indistinguishable,
maps are unsupported, there is no SQL-callable traversal, the only
TypeScript path rounds large integers, and one person maintains the project.

## Technology and Operations

| Aspect | What the record says | Source |
|--------|----------------------|--------|
| Hosting model | Embedded Java library in the application's JVM, or behind Gremlin Server for non-JVM clients; data in the user's relational database | [1][16] |
| Integrations | TinkerPop 3.7.4 Gremlin API; Gremlin Server with GraphBinary and GraphSON serializers; JDBC to PostgreSQL, MariaDB, MySQL, H2, HSQLDB | [1][16][30] |
| Data handling | Stored in the user's database as per-label tables; encryption and residency are the database operator's | [8] |
| Certifications | Not published (searched [1][3], 24 Sep 2026) | none |
| Maturity and cadence | First commit July 2014; 3.x since March 2023; 3.1.6 on 1 February 2026; no support window published | [5][6] |
| Governance | Single maintainer; no foundation; MIT licence | [3][6] |
| Security process | Not published: no security policy found in the repository root (searched [1], 24 Sep 2026) | none |

## Pricing and Licensing

| Item | Figure | Label | Source |
|------|--------|-------|--------|
| Licence | MIT: use, copy, modify, merge, publish, distribute, sublicense and sell, without fee | Published | [3] |
| Software cost | None | Published | [3] |
| Commercial support | Not published (searched [1][7], 24 Sep 2026) | Not published | none |

## Competitive Landscape

Columns are the Required Capabilities: C1 in the user's PostgreSQL; C2 exact
scalars; C3 absent/null, lists, maps; C4 database-enforced rules; C5 indexes
used; C6 traversal, writes and SQL composition; C7 concurrency; C8 unknown data
retained; C9 TypeScript without loss; C10 plain-SQL readable; C11 sustainable
maintenance; C12 latency within 2×.

| Candidate | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | Profile |
|-----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|---------|
| Sqlg 3.1.6 | Unknown: plain tables in user's PG, no version matrix [8][21] | Unmet: decimal stored as double [9][10] | Unmet: absent = null; no maps [4][14] | Unknown: NOT NULL, CHECK, unique, FK; collation undocumented [11][12] | Met, maker only [12][13] | Unmet: no SQL-callable traversal [16] | Unknown: isolation and merge undocumented [4][22] | Unmet: DDL on write or refusal [11] | Unmet: JVM only; JS client floats large longs [16][26] | Met: per-label tables, native types [8][9] | Unmet: single maintainer [6] | Unknown: 2017 study, summary only [28] | this profile |
| PuppyGraph 1.11 | Unmet (own server) | Unknown | Unknown | Unmet (read-only) | Unknown | Unmet (read-only) | Unmet (no writes) | Unmet | Unknown | Met (reads tables in place) | Unmet (proprietary) | Unknown | [[component-profile-puppygraph]] |
| Gel 7.1 | Unmet (own server) | Unknown (UTC-normalised datetime) | Unmet (no null; no maps) | Met | Met | Unmet (no variable-length traversal) | Met | Unmet (strict schema) | Met (with custom codecs) | Met (via Gel's SQL endpoint) | Unmet (maker shut down) | Unknown | [[component-profile-gel]] |
| Apache AGE | Unknown† | Unmet† | Unmet† | Unknown† | Unknown† | Met† | Unknown† | Met† | Unknown† | Met† | Unknown† | Unknown† | [[component-profile-apache-age]] |
| Palantir OSv2 | Unmet† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-palantir-osv2]] |
| Neo4j | Unmet† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Met† | Unmet† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-neo4j]] |
| Memgraph | Unmet† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Unknown† | Met† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-memgraph]] |
| LadybugDB | Unmet† | Unmet† | Unmet† | Unmet† | Unmet† | Unmet† | Met† | Unknown† | Unmet† | Unmet† | Unmet† | Unknown† | [[component-profile-ladybugdb]] |
| Datomic | Unmet† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Met† | Unmet† | Unknown† | Unmet† | Unmet† | Unknown† | [[component-profile-datomic]] |
| XTDB | Unmet† | Unknown† | Unknown† | Unmet† | Unmet† | Unmet† | Met† | Met† | Unknown† | Met† | Unmet† | Unknown† | [[component-profile-xtdb]] |
| SurrealDB | Unmet† | Unmet† | Met† | Unknown† | Met† | Unmet† | Met† | Met† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-surrealdb]] |
| UMF-generated per-type PostgreSQL tables | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | *none yet* |
| JSONB plus expression indexes | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | *none yet* |

† Status copied on 2026-09-25 from the sibling profile named in the Profile column, where the evidence and sources are recorded.

The PuppyGraph and Gel rows carry the statuses from their sibling profiles,
researched in the same session; the evidence and sources for those cells are
in those profiles and are not repeated here.

- PuppyGraph shares Sqlg's Gremlin support and its reading of relational
  tables as a graph; it diverges by running as its own server over existing
  tables with no write path ([[component-profile-puppygraph]]).
- Gel shares the idea of a typed schema compiled to PostgreSQL tables; it
  diverges by requiring its own server in front of PostgreSQL, by enforcing
  constraints declaratively, and by its maker having shut down
  ([[component-profile-gel]]).
- Apache AGE shares the goal of graph queries inside the user's PostgreSQL;
  not researched here ([[component-profile-apache-age]]).
- Palantir OSv2 is not researched here ([[component-profile-palantir-osv2]]).
- Neo4j, Memgraph and LadybugDB are native graph engines outside PostgreSQL;
  not researched here ([[component-profile-neo4j]],
  [[component-profile-memgraph]], [[component-profile-ladybugdb]]).
- Datomic, XTDB and SurrealDB are fact, bitemporal or multi-model stores; not
  researched here ([[component-profile-datomic]], [[component-profile-xtdb]],
  [[component-profile-surrealdb]]).
- UMF-generated per-type tables share Sqlg's one-table-per-type layout; the
  divergence (schema from UMF, exact types) is not researched here.
- JSONB plus expression indexes is not researched here.

## Confidence

| Grade | Means |
|-------|-------|
| **High** | Every design-defining claim is corroborated by the maker's material *and* at least one independent source, and no design-defining capability is Unknown. |
| **Medium** | Design-defining claims rest on the maker alone, or a design-defining capability is Unknown, or the independent coverage is older than two major versions. |
| **Low** | Thin public footprint; claims rest on one source or on none. |

**Grade**: Medium. The decisive Unmet findings rest on the maker's own
documentation and source: the decimal mapping [9][10], null semantics [4][11],
list and map support [14], entry points [16], topology behaviour [11], and the
commit history [6]; the TypeScript finding rests on TinkerPop's driver source
[26][27]. None of these is corroborated by an independent source, and C1, C4,
C7 and C12 are Unknown. The only independent coverage [28][29] is from 2017 and
2018, older than two major versions, and was read only through search-engine
summaries. Weakest area: performance (C12) and concurrency (C7), where the
record is silent.

## Open Questions

| # | Question | Design-defining because | Route |
|---|----------|-------------------------|-------|
| 1 | Which PostgreSQL major versions, including 17 and 18, does Sqlg 3.1.6 support, and does it run on managed services that restrict DDL or `NOTIFY`? | C1 decides whether the candidate can live in teams' existing databases | ask maker; [[tech-spike]] if the answer matters after the Unmet findings |
| 2 | Under what collation are Sqlg's `TEXT` unique indexes created, and do they compare byte for byte? | C4 exact-equality keys are part of truss's `sql-exactness` concern | ask maker |
| 3 | What isolation level does Sqlg use, and what happens when two transactions run `mergeV` for the same key concurrently? | C7 decides whether merges and cross-row rules are safe without application locking | ask maker; [[tech-spike]] |
| 4 | How does Sqlg 3.x latency compare with hand-written SQL on the same per-label tables for single-object fetch and 1–3 hop traversal? | C12 is truss's proposed performance target; the only study is from 2017 | [[tech-spike]] |

## Sources

Classes: **maker** (the component's maker or governing body), **vendor** (a
company selling hosting or support for the component or a rival),
**independent** (no commercial interest; named author or organisation and a
date), **community** (a project or forum around the component). All GitHub
files were read from the repository at the commit or tag in the URL; the
rendered documentation at sqlg.org was blocked by this session's egress proxy.

1. [Sqlg README](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/README.md), maker, Pieter Martin, commit of 31 Jul 2026, accessed 24 Sep 2026
2. [Sqlg 3.1.6 documentation: Introduction](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/introduction.adoc), maker, Pieter Martin, docs added 4 Feb 2026, accessed 24 Sep 2026 (rendered at https://sqlg.org/docs/3.1.6/, blocked)
3. [Sqlg LICENSE (MIT)](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/LICENSE), maker, Pieter Martin, copyright 2022, accessed 24 Sep 2026
4. [Sqlg CHANGELOG](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/CHANGELOG.md), maker, Pieter Martin, entries through 3.1.6, accessed 24 Sep 2026
5. [Sqlg releases](https://github.com/pietermartin/sqlg/releases), maker, Pieter Martin, release dates confirmed from the tagged commits (3.0.0 1 Mar 2023; 3.1.0 27 Apr 2024; 3.1.1 8 Dec 2024; 3.1.2 17 Jun 2025; 3.1.3 14 Aug 2025; 3.1.4 17 Aug 2025; 3.1.5 18 Aug 2025; 3.1.6 1 Feb 2026), accessed 24 Sep 2026
6. [Sqlg commit history, master](https://github.com/pietermartin/sqlg/commits/master), maker, Pieter Martin, 3,022 commits from 12 Jul 2014 to 31 Jul 2026, counted from a clone with `git shortlog`, accessed 24 Sep 2026
7. [pietermartin/sqlg repository page](https://github.com/pietermartin/sqlg), community (GitHub), star, fork and open-issue counts as shown, accessed 24 Sep 2026
8. [Sqlg 3.1.6 documentation: Architecture](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/architecture.adoc), maker, Pieter Martin, accessed 24 Sep 2026
9. [Sqlg 3.1.6 documentation: Data types](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/dataTypes.adoc), maker, Pieter Martin, accessed 24 Sep 2026
10. [PostgresDialect.java at tag 3.1.6, `BIG_DECIMAL` column type](https://github.com/pietermartin/sqlg/blob/3.1.6/sqlg-postgres-parent/sqlg-postgres-dialect/src/main/java/org/umlg/sqlg/dialect/impl/PostgresDialect.java#L1721), maker, Pieter Martin, tagged 1 Feb 2026, accessed 24 Sep 2026
11. [Sqlg 3.1.6 documentation: Topology](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/topology.adoc), maker, Pieter Martin, accessed 24 Sep 2026
12. [Sqlg 3.1.6 documentation: Indexes](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/indexes.adoc), maker, Pieter Martin, accessed 24 Sep 2026
13. [Sqlg 3.1.6 documentation: Predicates](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/gremlin/predicates.adoc), maker, Pieter Martin, accessed 24 Sep 2026
14. [Sqlg 3.1.6 documentation: TinkerPop supported features](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/supportedFeatures.adoc), maker, Pieter Martin, accessed 24 Sep 2026
15. [SqlgGraph.java test opt-outs](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-core/src/main/java/org/umlg/sqlg/structure/SqlgGraph.java), maker, Pieter Martin, accessed 24 Sep 2026
16. [Sqlg 3.1.6 documentation: Gremlin server](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/gremlinServer.adoc), maker, Pieter Martin, accessed 24 Sep 2026
17. [Sqlg 3.1.6 documentation: Multiple JVMs](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/multipleJvm.adoc), maker, Pieter Martin, accessed 24 Sep 2026
18. [Sqlg 3.1.6 documentation: Batch mode](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/batchMode.adoc), maker, Pieter Martin, accessed 24 Sep 2026
19. [Sqlg 3.1.6 documentation: PostgreSQL foreign data wrappers](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/postgresqlForeignDataWrappers.adoc), maker, Pieter Martin, accessed 24 Sep 2026
20. [Sqlg 3.1.6 documentation: Limitations](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/limitations.adoc), maker, Pieter Martin, accessed 24 Sep 2026
21. [sqlg-testdb-postgres Dockerfile](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-testdb-postgres/Dockerfile), maker, Pieter Martin, accessed 24 Sep 2026
22. [Issue #478: Implement merge step](https://github.com/pietermartin/sqlg/issues/478), maker, Pieter Martin, opened 3 Feb 2023, open, accessed 24 Sep 2026
23. [Issue #464: Table Locking issue with SQLG](https://github.com/pietermartin/sqlg/issues/464), community, amitbhoyar, opened 19 Sep 2022, closed, accessed 24 Sep 2026
24. [Sqlg issues matching "concurrent OR deadlock OR lock"](https://github.com/pietermartin/sqlg/issues?q=is%3Aissue+concurrent+OR+deadlock+OR+lock), community, listing including #329 "Deadlocks between writing threads" (closed, Feb 2019) and #477 "ConcurrentModificationException on concurrent schema creations" (closed, Feb 2023); titles only, accessed 24 Sep 2026
25. [TinkerPop 3.7.4 reference: Gremlin-JavaScript](https://github.com/apache/tinkerpop/blob/3.7.4/docs/src/reference/gremlin-variants.asciidoc), maker (TinkerPop), Apache TinkerPop, tag 3.7.4, accessed 24 Sep 2026 (rendered at tinkerpop.apache.org, blocked)
26. [Gremlin-JavaScript 3.7.4 LongSerializer.js](https://github.com/apache/tinkerpop/blob/3.7.4/gremlin-javascript/src/main/javascript/gremlin-javascript/lib/structure/io/binary/internals/LongSerializer.js#L95-L102), maker (TinkerPop), Apache TinkerPop, tag 3.7.4, accessed 24 Sep 2026
27. [Gremlin-JavaScript 3.8.2 LongSerializer.js](https://github.com/apache/tinkerpop/blob/3.8.2/gremlin-javascript/src/main/javascript/gremlin-javascript/lib/structure/io/binary/internals/LongSerializer.js#L95-L102), maker (TinkerPop), Apache TinkerPop, tag 3.8.2 (npm `gremlin` 3.8.2 published 8 Sep 2026), accessed 24 Sep 2026
28. [Pacaci, Zhou, Lin, Özsu: Do We Need Specialized Graph Databases? Benchmarking Real-Time Social Networking Applications](https://cs.uwaterloo.ca/~jimmylin/publications/Pacaci_etal_2017.pdf), independent, University of Waterloo authors, GRADES 2017 (SIGMOD workshop); page blocked, content taken from search-engine summaries, accessed 24 Sep 2026
29. [Lissandrini, Brugnara, Velegrakis: Beyond Macrobenchmarks: Microbenchmark-based Graph Database Evaluation](https://doi.org/10.14778/3297753.3297759), independent, PVLDB 12(4), December 2018; page blocked, content taken from a search-engine summary, accessed 24 Sep 2026
30. [Sqlg pom.xml](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/pom.xml), maker, Pieter Martin, `tinkerpop.version` 3.7.4 and Java `[17,)`, accessed 24 Sep 2026
31. [TestMerge.java](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-test/src/main/java/org/umlg/sqlg/test/mergestep/TestMerge.java), maker, Pieter Martin, accessed 24 Sep 2026
32. [Sqlg 3.1.6 documentation: PostgreSQL pgRouting](https://github.com/pietermartin/sqlg/blob/d769024bf84fe060a6ddf2e0df06b7a92b6581bc/sqlg-doc/docs/3.1.6/include/postgresqlPgRouting.adoc), maker, Pieter Martin, accessed 24 Sep 2026

**Searched**: Sqlg repository files README, CHANGELOG, `release.md`, `.travis.yml`, `sqlg-testdb-postgres/` and the 3.1.6 documentation sources (all include files) for "postgres" with version numbers, "isolation", "row level", "gql", "collat" and "support" (24 Sep 2026): no supported-version matrix, managed-provider statement, isolation level, collation, row-level security, GQL or support window, hence the C1 and C7 Unknowns and the Not published cells; source files `PostgresDialect.java`, `SqlgGraph.java` and `SqlgStartupManager.java` for "BIG_DECIMAL", "OptOut" and "isolation" (the only isolation setting found is serializable during Sqlg's own start-up, not for user transactions). GitHub issues searched for "postgres" and "concurrent OR deadlock OR lock" (titles only; no PostgreSQL 16–18 or managed-service issue found). Web searches: "Sqlg TinkerPop PostgreSQL benchmark performance evaluation"; "\"sqlg\" gremlin postgresql vertex table per label review OR comparison 2024 OR 2025"; "Pacaci Zhou Lin Özsu \"Do we need specialized graph databases\" GRADES 2017 Sqlg results"; "\"Sqlg\" LDBC social network benchmark Postgres Neo4j Titan Virtuoso throughput latency interactive workload"; "Lissandrini Brugnara Velegrakis \"Beyond Macrobenchmarks\" Sqlg PostgreSQL results" (found [28][29] only as summaries; no current benchmark, no independent adoption figure, hence C12 Unknown and Adoption Not published). Blocked by the egress proxy: sqlg.org, tinkerpop.apache.org, cs.uwaterloo.ca, blog.acolyer.org (The Morning Paper, 7 Jul 2017), vldb.org, velgias.github.io, people.cs.aau.dk, and repo1.maven.org (HTTP 429). Competitive Landscape rows other than PuppyGraph and Gel were not searched in this profile, hence Not researched.

## Review Checklist

Ticked by a named reviewer, recorded on the line; an author ticking their own
boxes is a draft.

Reviewed by: *unreviewed*

- [ ] Need and Required Capabilities cite project artifacts only; no `[n]` appears in them
- [ ] Every required capability has a "Settled by" line and a status from How to Read This Profile
- [ ] Every claim cites at the clause or is marked Not published (with the search) or Not researched (with the sibling profile)
- [ ] Every figure carries a label, and every mutable fact an as-of date
- [ ] The verdict follows the definitions in How to Read This Profile
- [ ] The Competitive Landscape scores every named alternative on the same capabilities
- [ ] The confidence grade follows the rubric; a design-defining Unknown caps it at Medium
- [ ] Every source carries class, author or organisation, publication date where shown, and access date; scoped-version docs are version-pinned
- [ ] No benchmark, prototype, or integration result is claimed
- [ ] No owner, date, duration, or figure appears that a project artifact does not state
- [ ] No choice among candidates is made here
