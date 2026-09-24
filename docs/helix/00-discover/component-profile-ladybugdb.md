---
ddx:
  id: truss.component-profile-ladybugdb
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

# Component Profile: LadybugDB

Desk research on LadybugDB, the most active fork of the archived Kuzu
embedded property-graph database, and on its young PostgreSQL extension
`pg_ladybug`, measured against the capabilities truss needs from a graph
storage and query layer. This is research. The choice between building
truss and adopting an existing system lives in a later decision record
that cites the profiles; anything the public record cannot settle is a
[[tech-spike]].

## Scope

- Component: LadybugDB (repository `LadybugDB/ladybug`, engine library
  `liblbug`), release 0.20.4 of 10 September 2026, with 0.21.0 in
  development; the Node.js binding `@ladybugdb/core` 0.20.4; and the
  PostgreSQL extension `pg_ladybug` (repository `LadybugDB/pg_ladybug`,
  last commit 10 August 2026)
- Fork confirmation: Kuzu's repository `kuzudb/kuzu` was archived on
  10 October 2025 [9]; LadybugDB states "The database was formerly known as
  Kuzu" [1] and is, by public commit activity, the most active of the Kuzu
  forks found (see What It Is) [7][10][11][12]
- Kind: Technology
- Would fill: the graph storage and query layer truss is planned to be,
  that is, the substitute a team chooses instead of building or adopting a
  graph layer inside its own PostgreSQL
- Feeds: the owner's build-versus-adopt decision for truss; no decision
  record exists yet
- Incumbent: none; truss has no implementation, and teams use hand-built
  per-type tables, JSONB documents or a separate graph database
  ([[truss.product-vision]] Target Market). truss has no
  current-state inventory.
- Researched: 24 September 2026 (mutable facts are as of 2026-09-24)
- Excluded: hands-on testing of any kind; the other Kuzu forks beyond
  confirming their activity; graph algorithms, vector and full-text search,
  lakehouse and LLM extensions, which no required capability names

## Summary

We need a graph storage and query layer that runs inside an organisation's
existing PostgreSQL, so that teams can store, traverse, update and
constrain connected data described by UMF schemas without moving it, see
which rules are enforced, and never lose data silently. It must run in the
user's PostgreSQL 17 and 18 including managed services, store nine scalar
families exactly, distinguish absent from null and keep lists and maps,
enforce declared rules, index property values for the planner, traverse
and write while composing with SQL, behave predictably under concurrency,
keep unknown data, work from TypeScript without precision loss, stay
readable through SQL, be a sustainable dependency, and stay within twice a
hand-designed schema's latency. On the public record LadybugDB 0.20 meets
defined concurrency through a single serializable writer and brings an
exact `DECIMAL`, typed columns and declared relationship endpoints, but it
is an embedded engine whose two-month-old PostgreSQL extension only reads
PostgreSQL tables, lacks a time-of-day type and secondary property indexes,
treats missing values as `NULL`, returns 64-bit integers to JavaScript as
floating-point numbers, and depends on one dominant maintainer, so the
verdict is No fit, with retention of unmodelled data and comparative
latency left unknown.

## How to Read This Profile

The vocabularies used below, in one place.

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

Two further labels appear in this profile. **Search summary** marks a claim
taken from a search engine's summary of a page that could not be opened;
it is never presented as a page read, and it supports descriptive claims
only. **Counted** marks a figure the author counted from a public git
history on the access date; it is a reading of the public record, not a
measurement of the software. Source code cited here was read, not run.

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

LadybugDB is an embedded property-graph database, "a library you embed
inside an application process" rather than a server [21], optimised for
"complex analytical workloads on very large databases", with columnar
disk-based storage, CSR adjacency indices, a vectorised and factorised
query processor, serializable ACID transactions, and full-text and vector
indices [1]. It continues Kuzu: the README says "The database was formerly
known as Kuzu" [1], and the Kuzu repository was archived by its owner on
10 October 2025 with a note that Kuzu is "working on something new" [9]. A
2025 report in The Register, available here only as a search summary,
describes Kuzu as abandoned by Kùzu Inc after its acquisition by Apple
[13]. LadybugDB is developed by "LadybugDB Developers" [1], and its licence
names Ladybug Memory Inc. as copyright holder from 2025 [2].

- Category and purpose: embedded, columnar property-graph database with
  Cypher, built for analytical graph workloads [1]
- Maker or governing body: LadybugDB Developers; copyright Ladybug Memory
  Inc. [1][2]; no foundation or governance document found (searched the
  repository root and `.github`, 2026-09-24)
- Fork status: of the Kuzu forks found, LadybugDB has 1,219 commits by 48
  distinct author names since 10 October 2025, against 110 by 5 for
  RyuGraph (last commit 7 December 2025), 67 by 3 for Bighorn (last commit
  8 August 2026) and 40 by 4 for Vela Partners' fork (last commit
  14 June 2026) (Counted) [7][10][11][12]; a gdotv post, seen only as a
  search summary, calls it "the definitive fork of Kuzu" [14]
- Adoption, from an independent source: Not published (searched
  "LadybugDB production readiness review 2026" and DB-Engines, 2026-09-24).
  Descriptively, the repository shows 1,778 stars and 148 forks as of
  2026-09-24 [8].
- Release cadence and support window: first post-Kuzu tag v0.12.0 on
  3 November 2025 [6]; releases 0.20.0 to 0.20.4 between 29 August and
  10 September 2026 [5]; main branch declares 0.21.0 [4]. The security
  policy still lists only 0.15.x and 0.14.x as supported [3], so the
  support window is Not published in current form.
- Licence: MIT [2]
- Built-for use cases: analytical graph queries embedded in applications,
  knowledge graphs, and browser use through WebAssembly bindings [1]; a
  Data Quarry post (search summary) describes a "graph lakehouse" goal
  [35]

## Capability Alignment

### C1. Runs inside the user's PostgreSQL

Interpretation: C1 asks for a component that runs inside the user's
PostgreSQL. LadybugDB itself is an embedded library with its own database
files, allowing one read-write `Database` object per database [21]. The
nearest candidate is `pg_ladybug`, which "embeds the Ladybug graph engine
via its C API" in PostgreSQL and "lets you run Cypher queries that read
your Postgres tables": the embedded planner rewrites a pattern over
registered tables into "a single SQL JOIN query" that PostgreSQL executes
[27]. It requires PostgreSQL 17 or later, "tested on 17 and 18", plus the
`liblbug` shared library and a `pg_client` extension [27]. Its second mode
creates Ladybug tables whose data "lives in `$PGDATA/storage.lbdb`", a
separate file outside PostgreSQL's tables, and "mixed mode execution" is
not supported [27]. The extension's history is 38 commits by one author
between 24 July and 10 August 2026 (Counted) [29], and its own review file
records reproduced backend crashes on NULL input and silent truncation of
results to 64 rows; the current SQL declares the functions `STRICT` and the
64-row cap no longer appears in the source [28][30]. No managed PostgreSQL
provider lists `pg_ladybug` (searched "pg_ladybug PostgreSQL extension",
2026-09-24). Graph storage and writes therefore do not live in PostgreSQL.

**Settled by**: version statement found in [27] (17 and 18 tested; no statement on 19); managed-provider listing not found; graph writes and storage outside PostgreSQL per [21][27]
**Status**: Unmet

### C2. Exact storage of nine scalar families

LadybugDB has signed integers from `INT8` to `INT128`, unsigned integers to
`UINT64`, `FLOAT` and `DOUBLE`, `BOOLEAN`, `UUID`, UTF-8 `STRING`, `DATE`,
`TIMESTAMP`, `INTERVAL`, `BLOB` and nested types [15]. `DECIMAL(precision,
scale)` is exact up to 38 digits, stored as integers, and a cast that does
not fit raises an overflow error rather than rounding [15]. Three gaps
remain: no time-of-day type is listed [15]; `TIMESTAMP` accepts an offset
but "stores the timestamp based on the timezone offset relative to UTC", so
the original offset is not kept [15]; and `BLOB` holds "up to 4KB" [15].
The maker says it "follows the Postgres typing system" [19].

**Settled by**: type-system documentation found in [15][19]; time-of-day type absent, timestamp offset dropped and binary size capped
**Status**: Unmet

### C3. Absent versus null; lists and maps

Every property belongs to a declared table column whose default "is
`NULL`" when not specified [17], and there is no `REMOVE`; the maker says to
"Use `SET n.prop = NULL` instead" [19], so an absent property and an
explicit null are the same state. `LIST` values keep order but "must all be
of the same type" [16], and `MAP` values need "a single type for all keys,
and a single type for all values" [15]. A `JSON` column stores nested
objects with mixed values and nulls inside lists [37].

**Settled by**: null and nested-type documentation found in [15][16][17][19]; the absent-versus-null distinction is contradicted
**Status**: Unmet

### C4. Database-enforced rules

The default schema is strict: node and relationship tables declare typed
properties before data is inserted [19][17]. Node tables require a primary
key, backed by an index that "also guarantees non-null and uniqueness"
[19][17]. Relationship tables declare their allowed `FROM`/`TO` node-table
pairs and may cap multiplicity at "at most 1" per direction, while
"exactly 1" semantics are not yet supported [17]. The maker states it "does
not currently support manually creating indexes or constraints on custom
properties" [19], so non-key properties cannot be required or made unique,
and no range, length or pattern rule exists beyond a `DECIMAL`'s declared
precision [15]. Whether primary-key equality is exact for strings (no
collation) is Not published (searched [15][17][19], 2026-09-24).

**Settled by**: schema and constraint documentation found in [17][19]; required non-key properties, alternate unique keys and value limits contradicted by [19]
**Status**: Unmet

### C5. Property indexes used by the planner

Apart from the primary-key index, the maker states that manual indexes on
custom properties are not supported [19]; full-text and vector indices are
provided for search [1]. Equality and range lookups on other properties
therefore have no property index to use.

**Settled by**: indexing statement found in [19]
**Status**: Unmet

### C6. Graph reads and writes that compose with SQL

Interpretation: the Cypher half is judged on LadybugDB's Cypher; the SQL
half asks for joins with relational tables and use inside SQL statements.
Reads cover pattern matching and recursive relationships with walk
semantics by default, `TRAIL` and `ACYCLIC` options [24], shortest and all
shortest paths, and a default upper bound of 30 hops when none is given
[19]. Writes cover `CREATE`, `SET`, `DELETE` and `MERGE` with `ON CREATE`
and `ON MATCH` [22][23], but `REMOVE`, `FOREACH`, `CALL` subqueries and
`SET +=` are not supported [19]. In PostgreSQL, `pg_ladybug` exposes
`ladybug.cypher(text)` as a set-returning function over registered
PostgreSQL tables, so read results can be used inside SQL [27]; writing to
PostgreSQL tables through Cypher is not documented, and Ladybug-native
tables cannot be mixed with PostgreSQL tables in one query [27].

**Settled by**: Cypher coverage and limits found in [19][22][23][24]; SQL composition limited to reads in [27]
**Status**: Unmet

### C7. Defined behaviour under concurrency

Interpretation: C7's "PostgreSQL's standard isolation levels" is read as
the candidate's documented isolation plus a documented way to prevent lost
updates. Every statement runs in a transaction; "there can be multiple read
transactions but only **one** write transaction" at a time, and
auto-committed statements execute "in a serializable manner" [20]. Only one
read-write `Database` object may open a database, in or across processes
[21]. With one writer at a time, single-property updates and merges are
serialised and lost updates cannot occur; the cost is no concurrent
writers.

**Settled by**: transaction and concurrency model found in [20][21]
**Status**: Met

### C8. Retains unmodelled data unchanged

The record is inconsistent. The differences page says LadybugDB "requires a
schema to be defined before any data can be inserted" [19], while the
`CREATE GRAPH` page documents open type graphs (`CREATE GRAPH g ANY`) that
"allow you to create nodes with labels without first defining the node
table" [18]. How undeclared properties are typed and stored in an open
graph is not documented (searched [17][18][19], 2026-09-24). A declared
`JSON` column keeps arbitrary nested objects, including nulls in lists
[37], but whether JSON numbers beyond double precision or long decimals are
returned unchanged is Not published (searched [37], 2026-09-24).

**Settled by**: open-type behaviour partly documented in [18]; exact retention not found
**Status**: Unknown

### C9. TypeScript without precision loss

The Node.js package `@ladybugdb/core` 0.20.4 is MIT-licensed and was
published on 10 September 2026 [32]. Its native conversion code returns
`INT64`, `SERIAL` and `UINT64` values as JavaScript numbers
(`Napi::Number`), and returns `DECIMAL` by parsing its string form to a
number, so integers beyond 2^53 and long decimals lose precision; only
`INT128` is returned as a `BigInt` [31]. No option for lossless 64-bit
integers and no Bun statement were found (searched [31] and the Node.js
API page, 2026-09-24).

**Settled by**: value conversion found in the maker's binding source [31]; lossless handling contradicted
**Status**: Unmet

### C10. Readable through plain SQL

Interpretation: the nearest equivalent is a maker-supported SQL surface
with conversions from graph values to SQL types. Ladybug-native data lives
in LadybugDB's own database files [21], including under `pg_ladybug`, where
it sits in `$PGDATA/storage.lbdb` rather than in PostgreSQL tables [27].
Query results can be exported to CSV, Parquet and JSON [36], and
`pg_ladybug`'s read mode leaves data in ordinary PostgreSQL tables because
those tables were already the user's [27]; neither is SQL access to graph
storage.

**Settled by**: not found for Ladybug storage (searched [21][27][36], 2026-09-24)
**Status**: Unmet

### C11. Sustainable dependency

The licence is MIT [2]. Releases are frequent, from v0.12.0 on
3 November 2025 to 0.20.4 on 10 September 2026 [5][6]. Maintenance is
concentrated: one author wrote 948 of the 1,219 commits since
10 October 2025, and the releases page shows the same account publishing
each recent release (Counted) [7][5]; `pg_ladybug` has a single author
[29]. The copyright holder is a company, Ladybug Memory Inc. [2], and no
foundation, governance document or maintainer list was found (searched the
repository root, `.github` and CONTRIBUTING, 2026-09-24). A gdotv interview,
seen only as a search summary, calls it "transparently governed" [14].

**Settled by**: licence [2] and release history [5][6] found; more than a handful of maintainers and open governance contradicted by commit concentration [7] and no governance record
**Status**: Unmet

### C12. Latency within twice a hand-designed schema

No independent benchmark comparing LadybugDB with a hand-designed
relational schema at the 95th percentile was found. The community
graph-bench harness, whose author builds a rival engine, ran LadybugDB
0.19.1 in-process and PostgreSQL 18.6 over a network driver in one
invocation on one laptop on a 10,000-node grid: medians of 54.2 µs versus
160.2 µs for a point read and 1.06 ms versus 170.8 µs for a three-hop
expansion [33]. The author notes that PostgreSQL's numbers are dominated by
the round trip, that LadybugDB was "the slowest of them on three hops", and
that nothing was tuned [33]; the PostgreSQL schema is not described in the
README and the figures are medians, not p95. A May 2026 post by John Nevin
at The Consensus, seen only as a search summary, compared LadybugDB 0.16.1,
DuckDB and a PostgreSQL 19 development build on baseball data and reports
DuckDB fastest throughout [34].

**Settled by**: an independent comparable benchmark, not found (searched "experimental evaluation graph database systems Neo4j Memgraph Kuzu PostgreSQL VLDB paper 2024 2025 benchmark", "theconsensus.dev Graph database-ball LadybugDB DuckDB PostgreSQL", 2026-09-24); community numbers in [33]
**Status**: Unknown

Other notable capabilities the record documents and no criterion requires:

| Capability | What the record says | Source |
|------------|----------------------|--------|
| Row-level security (nice to have) | Not published (searched the documentation for "security", "privilege", "role", 2026-09-24) | none |
| Shortest paths (nice to have) | `SHORTEST` and `ALL SHORTEST` in recursive patterns | [19] |
| GQL alignment (nice to have) | No conformance statement; open type graphs are offered "for users migrating from GQL or Neo4j", and GQL's `FINISH` is not supported | [18][19] |
| Reading PostgreSQL from LadybugDB | A `postgres` extension attaches a PostgreSQL database to a standalone LadybugDB for scanning and import | [25] |
| Wide integers | `INT128` and `UINT64` property types, beyond PostgreSQL's `bigint` | [15] |
| Browser | WebAssembly bindings | [1] |
| Declarative replication design | A `pg_ladybug` design note proposes trigger-based capture of PostgreSQL changes replayed into Ladybug storage as Cypher | [26] |

**Verdict**: No fit. C1 is Unmet because LadybugDB is an embedded engine
and `pg_ladybug` only reads PostgreSQL tables, and C2, C3, C4, C5, C6, C9,
C10 and C11 are Unmet on the maker's own documentation and source; C8 and
C12 are Unknown and would not change the verdict.

## Technology and Operations

| Aspect | What the record says | Source |
|--------|----------------------|--------|
| Hosting model | Embedded library in on-disk or in-memory mode; no managed service found (searched the documentation and organisation repositories, 2026-09-24); `pg_ladybug` runs inside a self-managed PostgreSQL 17 or 18 | [21][27] |
| Integrations | Python, Node.js, Rust, Go, Swift, Java, C/C++, CLI and WebAssembly; PostgreSQL attach extension; `pg_ladybug` | [1][25][27] |
| Data handling | Local database files; WAL with `CHECKPOINT`; encryption at rest Not published (searched [20][21], 2026-09-24) | [20][21] |
| Certifications | Not published (searched the repository and documentation, 2026-09-24) | none |
| Maturity and cadence | Fork of Kuzu; first LadybugDB tag 3 Nov 2025; nine minor versions to 0.20 by Sep 2026; pre-1.0 | [5][6] |
| Governance | Company copyright holder (Ladybug Memory Inc.); one dominant committer; no governance document found | [2][7] |
| Security process | Reports to security@ladybugdb.com, response within 7 working days, 90-day disclosure; the supported-versions table is stale (0.14.x, 0.15.x) | [3] |

## Pricing and Licensing

| Item | Figure | Label | Source |
|------|--------|-------|--------|
| Licence, LadybugDB | MIT | Published | [2] |
| Licence, `pg_ladybug` | PostgreSQL Licence | Published | [27] |
| Licence, Node.js binding | MIT | Published | [32] |
| Commercial support or hosted offer | Not published (searched the repositories and documentation, 2026-09-24) | Not published | none |

## Competitive Landscape

Cells for Neo4j and Memgraph come from this author's research for their
sibling profiles; other rows were not researched here. Sibling slugs other
than the three written with this profile are provisional.

| Candidate | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | Profile |
|-----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|---------|
| LadybugDB 0.20 | Unmet: embedded engine; pg_ladybug reads only [21][27] | Unmet: no time type; offset dropped; BLOB 4 KB [15] | Unmet: missing values are NULL [17][19] | Unmet: primary key and endpoints only [17][19] | Unmet: no property indexes [19] | Unmet: SQL composition read-only [27] | Met: single writer, serializable [20] | Unknown [18][19] | Unmet: INT64 to JS Number [31] | Unmet [27] | Unmet: one dominant maintainer [7] | Unknown [33] | this profile |
| Apache AGE | Unknown† | Unmet† | Unmet† | Unknown† | Unknown† | Met† | Unknown† | Met† | Unknown† | Met† | Unknown† | Unknown† | [[component-profile-apache-age]] |
| Palantir OSv2 | Unmet† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-palantir-osv2]] |
| Sqlg | Unknown† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unknown† | Unmet† | Unmet† | Met† | Unmet† | Unknown† | [[component-profile-sqlg]] |
| PuppyGraph | Unmet† | Unknown† | Unknown† | Unmet† | Unknown† | Unmet† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unknown† | [[component-profile-puppygraph]] |
| Gel | Unmet† | Unknown† | Unmet† | Met† | Met† | Unmet† | Met† | Unmet† | Met† | Met† | Unmet† | Unknown† | [[component-profile-gel]] |
| Neo4j 2026.09 (CE/EE) | Unmet: own server [42] | Unmet: no decimal [38] | Unmet: no null or map properties [38][39] | Unmet: limits absent; most rules EE-only [40][42] | Met [41] | Unmet: limited SQL translation only [44] | Met [43] | Unmet: maps not storable [38] | Met [45] | Unmet [44] | Unmet: single vendor, CLA [46] | Unknown [33] | [[component-profile-neo4j]] |
| Memgraph 3.13 | Unmet: own server [53] | Unmet: no decimal or bytes [47] | Unmet: null equals absent [47] | Unmet: node-only constraints [48][49] | Met [51] | Unmet: no SQL composition [49] | Unknown: merge semantics undocumented [50] | Met [47] | Met: uses neo4j-driver [54] | Unmet: openCypher only [49] | Unmet: BSL 1.1 [52] | Unknown [33] | [[component-profile-memgraph]] |
| Datomic | Unmet† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Met† | Unmet† | Unknown† | Unmet† | Unmet† | Unknown† | [[component-profile-datomic]] |
| XTDB | Unmet† | Unknown† | Unknown† | Unmet† | Unmet† | Unmet† | Met† | Met† | Unknown† | Met† | Unmet† | Unknown† | [[component-profile-xtdb]] |
| SurrealDB | Unmet† | Unmet† | Met† | Unknown† | Met† | Unmet† | Met† | Met† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-surrealdb]] |
| UMF-generated per-type PostgreSQL tables | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | *none yet* |
| JSONB plus expression indexes | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | *none yet* |

† Status copied on 2026-09-25 from the sibling profile named in the Profile column, where the evidence and sources are recorded.

- Apache AGE: shares Cypher and, with `pg_ladybug`, the idea of Cypher
  inside PostgreSQL; the divergence truss cares about is that AGE stores
  graph data in PostgreSQL. Not researched here; the project's competitive
  analysis records AGE as an openCypher PostgreSQL extension
  ([[truss.competitive-analysis]] Competitor Profiles).
- Palantir OSv2: Not researched here; see its sibling profile.
- Sqlg: Not researched here; the competitive analysis records a Gremlin
  layer with one table per label ([[truss.competitive-analysis]]).
- PuppyGraph: Not researched here; like `pg_ladybug`'s read mode [27], the
  competitive analysis records graph reads over existing SQL tables
  ([[truss.competitive-analysis]]).
- Gel: Not researched here; see its sibling profile.
- Neo4j: shares the Cypher family; it diverges by a server with lock-based
  concurrent writers [43], an Enterprise graph-type schema [40], no decimal
  type [38] and a lossless JavaScript driver [45].
- Memgraph: shares the Cypher family; it diverges by an in-memory server
  with snapshot isolation [50], schema-free map properties [47], and a
  source-available licence [52].
- Datomic, XTDB, SurrealDB: Not researched here; see their sibling profiles.
- UMF-generated per-type tables and JSONB with expression indexes: Not
  researched; no sibling profile exists yet. LadybugDB's typed node and
  relationship tables with declared endpoints [17] resemble the `shaped`
  strategy in [[truss.vision-input]] Draft Storage Layers.

## Confidence

| Grade | Means |
|-------|-------|
| **High** | Every design-defining claim is corroborated by the maker's material *and* at least one independent source, and no design-defining capability is Unknown. |
| **Medium** | Design-defining claims rest on the maker alone, or a design-defining capability is Unknown, or the independent coverage is older than two major versions. |
| **Low** | Thin public footprint; claims rest on one source or on none. |

**Grade**: Medium. The deciding claims, that LadybugDB is embedded and
`pg_ladybug` only reads PostgreSQL tables (C1), that it lacks a time type
and property indexes (C2, C5), that missing values are `NULL` (C3), and
that the Node.js binding returns 64-bit integers as JavaScript numbers
(C9), rest on the maker's documentation and source code alone
[15][17][19][21][27][31]. The fork's status is corroborated by the archived
Kuzu repository [9] and by commit histories [7][10][11][12], with press and
community accounts available only as search summaries [13][14][35].
Parts of the documentation are inherited from Kuzu and disagree with newer
pages (strict schema [19] against open type graphs [18]; a supported-versions
table stuck at 0.15 [3]). Weakest area: retention of unmodelled data (C8)
and comparative latency (C12), which no source settles.

## Open Questions

| # | Question | Design-defining because | Route |
|---|----------|-------------------------|-------|
| 1 | In an open type graph, how are undeclared properties typed and stored, and do `JSON` columns return long decimals and integers beyond 2^53 unchanged? | Decides whether LadybugDB could keep unmodelled data without loss (C8, `umf-fidelity`) | ask maker, then [[tech-spike]] |
| 2 | Will `pg_ladybug` gain a write path into PostgreSQL tables and support mixed PostgreSQL and Ladybug queries, and under what maintenance model? | A Cypher-to-single-SQL read path over PostgreSQL tables overlaps the query layer truss plans; its trajectory changes what truss must build versus reuse | ask maker; revisit this profile |
| 3 | On truss's benchmark corpus, what p95 does LadybugDB reach for single-object fetch and one-to-three-hop traversal, relative to a hand-designed PostgreSQL schema? | The competitive analysis tells truss not to compete on raw traversal speed; a measured baseline shows the size of that gap | [[tech-spike]] (the benchmark [[truss.vision-input]] asks for) |

## Sources

Classes: **maker** (the component's maker or governing body), **vendor** (a
company selling hosting or support for the component or a rival),
**independent** (no commercial interest; named author or organisation and a
date), **community** (a project or forum around the component). LadybugDB
documentation was read from its source repository `LadybugDB/ladybug-docs`
at commit 74a8467 (15 Sep 2026); ladybugdb.com and docs.ladybugdb.com did
not respond through the research environment's proxy, and neo4j.com and
memgraph.com were blocked.

1. [LadybugDB README at 2d69bd3](https://github.com/LadybugDB/ladybug/blob/2d69bd3d7e6dd84b8e1438d42553dddd437660b3/README.md), maker, LadybugDB Developers, commit of 23 Sep 2026, accessed 24 Sep 2026
2. [LICENSE at 2d69bd3](https://github.com/LadybugDB/ladybug/blob/2d69bd3d7e6dd84b8e1438d42553dddd437660b3/LICENSE), maker, Kùzu Inc. (2022–2025) and Ladybug Memory Inc. (2025–2026), accessed 24 Sep 2026
3. [SECURITY.md at 2d69bd3](https://github.com/LadybugDB/ladybug/blob/2d69bd3d7e6dd84b8e1438d42553dddd437660b3/SECURITY.md), maker, LadybugDB Developers, accessed 24 Sep 2026
4. [CMakeLists.txt at 2d69bd3 (project version 0.21.0)](https://github.com/LadybugDB/ladybug/blob/2d69bd3d7e6dd84b8e1438d42553dddd437660b3/CMakeLists.txt), maker, LadybugDB Developers, accessed 24 Sep 2026
5. [LadybugDB releases](https://github.com/LadybugDB/ladybug/releases), maker, LadybugDB Developers, releases 0.19.0 to 0.20.4 published by @adsharma, latest 10 Sep 2026, accessed 24 Sep 2026
6. [LadybugDB tags](https://github.com/LadybugDB/ladybug/tags), maker, LadybugDB Developers, v0.12.0 tagged 3 Nov 2025 through v0.20.4 on 10 Sep 2026, accessed 24 Sep 2026
7. [LadybugDB commit history, branch main](https://github.com/LadybugDB/ladybug/commits/main), maker, LadybugDB Developers, Counted by the author from `git log --since=2025-10-10` on 24 Sep 2026 (1,219 commits, 48 distinct author names, 948 by Arun Sharma), accessed 24 Sep 2026
8. [LadybugDB organisation repositories](https://github.com/LadybugDB), maker, LadybugDB Developers, 1,778 stars and 148 forks for `ladybug`, `pg_ladybug` created 25 Jul 2026, accessed 24 Sep 2026
9. [kuzudb/kuzu repository (archived)](https://github.com/kuzudb/kuzu), maker (of Kuzu), Kùzu Inc., archived 10 Oct 2025, accessed 24 Sep 2026
10. [predictable-labs/ryugraph commit history](https://github.com/predictable-labs/ryugraph), community, Predictable Labs, Counted on 24 Sep 2026 (110 commits by 5 authors since 10 Oct 2025; last 7 Dec 2025), accessed 24 Sep 2026
11. [Kineviz/bighorn commit history](https://github.com/Kineviz/bighorn), community, Kineviz, Counted on 24 Sep 2026 (67 commits by 3 authors since 10 Oct 2025; last 8 Aug 2026), accessed 24 Sep 2026
12. [Vela-Engineering/kuzu commit history](https://github.com/Vela-Engineering/kuzu), community, Vela Partners, Counted on 24 Sep 2026 (40 commits by 4 authors since 10 Oct 2025; last 14 Jun 2026), accessed 24 Sep 2026
13. [KuzuDB graph database abandoned, community mulls options](https://www.theregister.com/software/2025/10/14/kuzudb-graph-database-abandoned-community-mulls-options/1142229), independent, The Register, published 14 Oct 2025, Search summary only (page not read), accessed 24 Sep 2026
14. [Kuzu's Legacy and the New Wave of Embedded Graph Databases](https://gdotv.com/blog/kuzu-legacy-embedded-graph-database-landscape/), vendor (graph tooling company), gdotv, Search summary only (host blocked; page not read), accessed 24 Sep 2026
15. [Data types, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/data-types/index.mdx), maker, LadybugDB Developers, commit of 15 Sep 2026, accessed 24 Sep 2026
16. [LIST and ARRAY, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/data-types/list-and-array.md), maker, LadybugDB Developers, accessed 24 Sep 2026
17. [Create table, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/data-definition/create-table.md), maker, LadybugDB Developers, accessed 24 Sep 2026
18. [CREATE GRAPH (open type graphs), LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/data-definition/create-graph.md), maker, LadybugDB Developers, accessed 24 Sep 2026
19. [Differences between Ladybug and Neo4j, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/difference.md), maker, LadybugDB Developers, accessed 24 Sep 2026
20. [Transactions, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/transaction.md), maker, LadybugDB Developers, accessed 24 Sep 2026
21. [Connections and Concurrency, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/concurrency.md), maker, LadybugDB Developers, accessed 24 Sep 2026
22. [MERGE, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/data-manipulation-clauses/merge.md), maker, LadybugDB Developers, accessed 24 Sep 2026
23. [SET, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/data-manipulation-clauses/set.md), maker, LadybugDB Developers, accessed 24 Sep 2026
24. [MATCH (recursive relationships, walk, trail, acyclic), LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/query-clauses/match.md), maker, LadybugDB Developers, accessed 24 Sep 2026
25. [PostgreSQL extension (attach), LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/extensions/attach/postgres.mdx), maker, LadybugDB Developers, accessed 24 Sep 2026
26. [pg_ladybug replication design note at 895cbdb](https://github.com/LadybugDB/pg_ladybug/blob/895cbdb5d1d0fb7db65e78ac7352795489b91f5d/replication_design.md), maker, LadybugDB Developers, accessed 24 Sep 2026
27. [pg_ladybug README at 895cbdb](https://github.com/LadybugDB/pg_ladybug/blob/895cbdb5d1d0fb7db65e78ac7352795489b91f5d/README.md), maker, LadybugDB Developers, commit of 10 Aug 2026, accessed 24 Sep 2026
28. [pg_ladybug security and correctness review (issues.md) at 895cbdb](https://github.com/LadybugDB/pg_ladybug/blob/895cbdb5d1d0fb7db65e78ac7352795489b91f5d/issues.md), maker, LadybugDB Developers, accessed 24 Sep 2026
29. [pg_ladybug commit history](https://github.com/LadybugDB/pg_ladybug/commits/main), maker, LadybugDB Developers, Counted on 24 Sep 2026 (38 commits, all by Arun Sharma, 24 Jul to 10 Aug 2026), accessed 24 Sep 2026
30. [pg_ladybug--1.0.sql at 895cbdb](https://github.com/LadybugDB/pg_ladybug/blob/895cbdb5d1d0fb7db65e78ac7352795489b91f5d/pg_ladybug--1.0.sql), maker, LadybugDB Developers, accessed 24 Sep 2026
31. [ladybug-nodejs `src_cpp/node_util.cpp` at b62c549](https://github.com/LadybugDB/ladybug-nodejs/blob/b62c5499d266ca1af4053e3e2e61d999c11962d3/src_cpp/node_util.cpp), maker, LadybugDB Developers, commit of 29 Aug 2026, accessed 24 Sep 2026
32. [@ladybugdb/core package metadata, npm registry](https://registry.npmjs.org/@ladybugdb/core), maker, LadybugDB Developers, version 0.20.4 published 10 Sep 2026, MIT, accessed 24 Sep 2026
33. [graph-bench README at 89ff1c7](https://github.com/tamnd/graph-bench/blob/89ff1c7989e9cf401fcbbb70ca1c60fc4d6f2eaf/README.md), community, tamnd (who also develops the rival `zu` engine), seven-engine run dated 19 Aug 2026, accessed 24 Sep 2026
34. [Graph database-ball! Exploring the Game with the graph capabilities of LadybugDB, DuckDB and PostgreSQL](https://theconsensus.dev/p/2026/05/29/ladybug-duckdb-and-postgresql.html), independent, John Nevin, The Consensus, published 29 May 2026, Search summary only (host blocked; page not read), accessed 24 Sep 2026
35. [From Kuzu to Ladybug: The embedded graph ecosystem powers onward](https://thedataquarry.com/blog/from-kuzu-to-ladybug/), community, The Data Quarry (Prashanth Rao), Search summary only (host blocked; page not read), accessed 24 Sep 2026
36. [Export data, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/export/index.mdx), maker, LadybugDB Developers, accessed 24 Sep 2026
37. [JSON extension and JSON data type, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/extensions/json.mdx), maker, LadybugDB Developers, accessed 24 Sep 2026
38. [Property, structural, and constructed values, Cypher Manual 25 (Neo4j 2026.09), docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/values-and-types/property-structural-constructed.adoc), maker, Neo4j, accessed 24 Sep 2026
39. [REMOVE, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/clauses/remove.adoc), maker, Neo4j, accessed 24 Sep 2026
40. [Constraints, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/schema/constraints/index.adoc), maker, Neo4j, accessed 24 Sep 2026
41. [The impact of indexes on query performance, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/indexes/search-performance-indexes/using-indexes.adoc), maker, Neo4j, accessed 24 Sep 2026
42. [Introduction (editions, key features per edition), Neo4j Operations Manual 2026.09, docs-operations@a4c8c47](https://github.com/neo4j/docs-operations/blob/a4c8c4785b0b9c3c81184ba6c742082430225a56/modules/ROOT/pages/introduction.adoc), maker, Neo4j, accessed 24 Sep 2026
43. [Concurrent data access, Neo4j Operations Manual 2026.09, docs-operations@a4c8c47](https://github.com/neo4j/docs-operations/blob/a4c8c4785b0b9c3c81184ba6c742082430225a56/modules/ROOT/pages/database-internals/concurrent-data-access.adoc), maker, Neo4j, accessed 24 Sep 2026
44. [Neo4j JDBC Driver README at 35ec862](https://github.com/neo4j/neo4j-jdbc/blob/35ec8625fa327ea5f85ed3dae847b47bb354ace7/README.adoc), maker, Neo4j, accessed 24 Sep 2026
45. [neo4j-javascript-driver README, Numbers and the Integer type, 6.x at 6453219](https://github.com/neo4j/neo4j-javascript-driver/blob/6453219576098a71c8deaf1493a136f5230370c5/README.md), maker, Neo4j, accessed 24 Sep 2026
46. [README.asciidoc (Licensing, Extending Neo4j), neo4j/neo4j at 54a7dcf](https://github.com/neo4j/neo4j/blob/54a7dcf7c2501b31866199143364c5332da8936f/README.asciidoc), maker, Neo4j, accessed 24 Sep 2026
47. [Data types, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/data-types.mdx), maker, Memgraph, commit of 23 Sep 2026, accessed 24 Sep 2026
48. [Constraints, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/constraints.mdx), maker, Memgraph, accessed 24 Sep 2026
49. [Differences in Cypher implementations, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/querying/differences-in-cypher-implementations.mdx), maker, Memgraph, accessed 24 Sep 2026
50. [Transactions, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/transactions.mdx), maker, Memgraph, accessed 24 Sep 2026
51. [Indexes, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/indexes.mdx), maker, Memgraph, accessed 24 Sep 2026
52. [Memgraph Business Source License 1.1, as amended 1 Jan 2026, memgraph@6a80124](https://github.com/memgraph/memgraph/blob/6a80124060482583e72610fa268f8a442c0d830c/licenses/BSL.txt), maker, Memgraph Ltd, accessed 24 Sep 2026
53. [Storage memory usage (storage modes), Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/storage-memory-usage.mdx), maker, Memgraph, accessed 24 Sep 2026
54. [Node.js client, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/client-libraries/nodejs.mdx), maker, Memgraph, accessed 24 Sep 2026

**Searched**: "LadybugDB Kuzu fork embedded graph database GitHub" (found
[1][8]; fork name and repository confirmed). "Kuzu archived October 2025
Apple acquisition LadybugDB fork Arun Sharma" and "gdotv Kuzu's Legacy
embedded graph database forks LadybugDB RyuGraph Bighorn" (found [13][14]
[35] as search summaries; fork activity then Counted in [7][10][11][12]).
The Register, gdotv, The Data Quarry, szarnyasg.org (Gábor Szárnyas, "Kùzu
forks"), The Consensus and arcadedb.com were blocked or unreachable, so
their content is known only from search summaries. "TIME", "time zone",
"offset", "BLOB", "DECIMAL" in the data-types page (C2). "NULL", "REMOVE"
in the data-types, create-table and differences pages (C3). "NOT NULL",
"UNIQUE", "CHECK" in the data-definition pages (C4: no manual constraints;
string key equality Not published). "index" in the differences page (C5).
"pg_ladybug PostgreSQL extension" (no managed-provider listing: C1).
"BigInt", "INT64", "DECIMAL" in the Node.js binding source and API page
(C9); "bun" in the binding repository and documentation (no statement:
C9). Open type graph property typing and JSON number exactness in [17][18]
[37] (Not published: C8). Repository root and `.github` for GOVERNANCE,
MAINTAINERS and CODEOWNERS (no governance document: C11). "LadybugDB
production readiness review 2026 embedded graph database Kuzu successor
benchmark" and "experimental evaluation graph database systems Neo4j
Memgraph Kuzu PostgreSQL VLDB paper 2024 2025 benchmark" (no independent
p95 comparison: C12; found [33] and [34] as a search summary). "security",
"privilege", "role" in the documentation (row-level security Not
published). Apache AGE, Palantir OSv2, Sqlg, PuppyGraph, Gel, Datomic,
XTDB, SurrealDB, UMF-generated per-type tables and JSONB with expression
indexes were not searched for this profile, hence Not researched.

## Review Checklist

Ticked by a named reviewer, recorded on the line; an author ticking their
own boxes is a draft.

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
