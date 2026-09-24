---
ddx:
  id: truss.component-profile-neo4j
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

# Component Profile: Neo4j

Desk research on Neo4j, the native property-graph database, as the system
teams adopt when they move connected data out of PostgreSQL, measured
against the capabilities truss needs from a graph storage and query layer.
This is research. The choice between building truss and adopting an
existing system lives in a later decision record that cites the profiles;
anything the public record cannot settle is a [[tech-spike]].

## Scope

- Component: Neo4j server, Community Edition (CE) and Enterprise Edition
  (EE), calendar-versioned line 2026.09 (Cypher 25), with the 5.26 LTS line
  noted where support windows matter; the official JavaScript driver 6.x
- Kind: Technology (with a managed provider, Neo4j Aura, noted but not
  profiled)
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
- Excluded: hands-on testing of any kind; Neo4j Aura regions, pricing and
  certifications beyond what could be read (the maker's website was blocked
  by the research environment's egress proxy, see Sources); Graph Data
  Science, Bloom, Infinigraph and clustering, which no required capability
  names

## Summary

We need a graph storage and query layer that runs inside an organisation's
existing PostgreSQL, so that teams can store, traverse, update and
constrain connected data described by UMF schemas without moving it,
see which rules are enforced, and never lose data silently. It must run in
the user's PostgreSQL 17 and 18 including managed services, store nine
scalar families exactly, distinguish absent from null and keep lists and
maps, enforce declared rules, index property values for the planner,
traverse and write while composing with SQL, behave predictably under
concurrency, keep unknown data, work from TypeScript without precision
loss, stay readable through SQL, be a sustainable dependency, and stay
within twice a hand-designed schema's latency. On the public record Neo4j
2026.09 meets indexing, concurrency and TypeScript access, but it runs as
its own server rather than inside PostgreSQL, has no exact decimal type,
cannot store null or map property values, reserves existence, type, key
and endpoint rules for the Enterprise Edition, offers no SQL composition,
and is governed by a single vendor, so the verdict is No fit, with
comparative latency left unknown.

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
measurement of the software.

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

Neo4j is a native property-graph database: its maker describes an
architecture "designed for optimal management, storage, and traversal of
nodes and relationships", with ACID-compliant transactions and the Cypher
query language, deployable as a standalone server or a fault-tolerant
cluster [17]. The software is developed and owned by Neo4j Sweden AB [20];
outside contributions require a Contributor License Agreement [21]. It
exists to let applications work with "a flexible network structure of nodes
and relationships rather than static tables" [21]. The Community Edition is
open source under GPLv3, and the Enterprise Edition adds closed-source
components under a commercial licence [21][17].

- Category and purpose: native property-graph database with native graph
  storage and processing, a cost-based Cypher optimiser and ACID
  transactions [17]
- Maker or governing body: Neo4j (Neo4j Sweden AB owns the software) [20];
  no foundation; contributions under a CLA [21]
- Adoption, from an independent source: Not published (searched DB-Engines
  and the 2025 Stack Overflow Developer Survey on 2026-09-24; both hosts
  were blocked and search summaries gave no figure). Descriptively, the
  maker's GitHub repository shows 17.3k stars as of 2026-09-24 [22].
- Release cadence and support window: calendar versioning (YYYY.MM.Patch)
  since 2025.01, with some releases designated long-term support [17];
  2026.09.0 is the newest tag and 5.26 LTS still receives patches (5.26.31)
  as of 2026-09-24 [22]; the maker's notes refer to "the next LTS release
  in 2026" [19]; a search summary of the maker's blog states 5.26 LTS is
  supported until June 2028 (page not read) [34]
- Licence: Community Edition GPLv3; a commercial agreement supersedes GPLv3
  for its licensees [20]; Enterprise Edition components are closed source
  and need a commercial licence [21]
- Built-for use cases: CE for "single-instance deployments", learning and
  small workgroups; EE for "production systems with requirements for scale
  and availability" [17]

## Capability Alignment

### C1. Runs inside the user's PostgreSQL

Interpretation: C1 asks for a component that runs inside the user's
PostgreSQL; the nearest equivalent for Neo4j would be a supported way to
keep the graph in PostgreSQL storage, and none exists. Neo4j is its own
database server with its own store formats, deployed standalone or as a
cluster [17]. The managed form is Neo4j Aura, which "always uses the latest
version of the Neo4j server" [17]; it is a Neo4j service, not a PostgreSQL
extension. Adopting Neo4j therefore means moving graph data out of the
PostgreSQL estate, which is the substitute behaviour the Need names.

**Settled by**: a PostgreSQL version matrix or managed-provider listing, not found; the maker documents a standalone server and cluster [17] (searched the Operations Manual 2026.09 [17] and the Cypher Manual 25, 2026-09-24)
**Status**: Unmet

### C2. Exact storage of nine scalar families

Storable property types are `BOOLEAN`, `DATE`, `DURATION`, `FLOAT`,
`INTEGER`, `LIST`, `LOCAL DATETIME`, `LOCAL TIME`, `POINT`, `STRING`,
`UUID`, `VECTOR`, `ZONED DATETIME` and `ZONED TIME` [1]. `INTEGER` is
always a 64-bit integer and `FLOAT` a 64-bit double-precision number [2].
There is no decimal type in the property-type list or in the type-synonym
table [1]. Byte arrays can be stored as property values but are
"pass-through", with no literal form, and are "not considered a first
class data type by Cypher" [1]. Temporal types cover dates, local and zoned
times, and local and zoned datetimes [6]; a zone is an offset or an IANA
name, the instant is stored as UTC and the offset "is only applied when the
time is presented" [6], and sub-second values reach nanosecond precision
through the JavaScript driver [26]. Strings are Unicode, with the Unicode
version set by the JVM (Unicode 15 on Java 21) [2]. A 2020 feature request
on the Java driver asked for BigDecimal support and was closed [32]. Exact
decimals would have to be carried as strings or scaled integers, which is
the silent change of type C2 exists to prevent.

**Settled by**: property type documentation found in [1][2][6]; no exact decimal type (searched [1][2] and the GQL analogous-feature pages, 2026-09-24)
**Status**: Unmet

### C3. Absent versus null; lists and maps

The maker states that "Neo4j doesn't allow storing `null` in properties.
Instead, if no value exists, the property is just not there" [4]; setting a
property to null through a map removes it [5]. Lists stored as properties
must be homogeneous lists of simple types and "cannot contain `null`
values", and maps "cannot be stored as properties" [1]. Ordered lists with
duplicates survive only when they are homogeneous and null-free [1].

**Settled by**: null, list and map handling found in [1][4][5]
**Status**: Unmet

### C4. Database-enforced rules

Neo4j offers property uniqueness, property existence, property type and
key constraints; existence, type and key constraints carry the Enterprise
Edition label [8][9], and the edition table lists only uniqueness
constraints for Community [17]. Uniqueness and key constraints are backed
by range indexes, and creating data that violates an existing constraint
fails [9]. Graph types, an Enterprise feature for Cypher 25 that became
generally available in Neo4j 2026.06 [10], add node element types (required
labels, required properties, property types) and relationship element types
that fix the source and target labels of a relationship type [11]; setting
a graph type replaces previously defined constraints [11]. The enumerated
constraint kinds include no range, length or pattern limits [8]. Cypher
treats values of the same type as equal only when identical [7]; whether a
uniqueness constraint treats an `INTEGER` and an equal `FLOAT` as duplicates
is Not published (searched [7][9], 2026-09-24). Under concurrent `MERGE`,
constraints on identifying properties "protect against duplicate creation"
[13].

**Settled by**: constraint kinds, editions and write interaction found in [8][9][10][11][13][17]; value limits not found (searched [8][9][11], 2026-09-24)
**Status**: Unmet

### C5. Property indexes used by the planner

Range indexes support equality checks, range comparisons and prefix
searches, among other predicates [12]. Search-performance indexes "are used
automatically by the Cypher planner in `MATCH` clauses", and the maker's
plans show `NodeIndexSeek` and `NodeIndexSeekByRange` operators replacing a
label scan [14]. Composite indexes are listed for both editions [17]. No
independent source examining Neo4j plans was found; the evidence is the
maker's own.

**Settled by**: indexing documentation and example plans found in [12][14][17]; independent plan reports not found (searched "neo4j range index planner NodeIndexSeek", 2026-09-24)
**Status**: Met

### C6. Graph reads and writes that compose with SQL

Interpretation: the Cypher half of C6 is judged on Cypher; the SQL half
asks for joins with relational tables and use inside SQL statements, whose
nearest equivalent for a non-SQL database would be a documented SQL
interface over the graph. Cypher covers variable-length and quantified path
patterns [15], shortest paths [16], `MERGE` [13], `SET` and `REMOVE` [5][4],
and parameters for all property types [1]; the maker states Cypher supports
"the majority of mandatory GQL features" [2]. The SQL half is not met:
Neo4j has no SQL engine, and its JDBC driver "has limited support for using
SQL", translating SQL text into Cypher [31]. No documented way exists to
join Neo4j data with PostgreSQL tables or call Cypher inside a SQL
statement (searched [17][31], 2026-09-24).

**Settled by**: Cypher coverage found in [1][2][4][5][13][15][16]; SQL composition not found beyond the translation layer in [31]
**Status**: Unmet

### C7. Defined behaviour under concurrency

Interpretation: C7's "PostgreSQL's standard isolation levels" is read as
the candidate's documented isolation levels plus a documented way to
prevent lost updates. Neo4j's default is read committed; serializable
behaviour is obtained by taking write locks explicitly [18]. When `SET`
reads the property it writes (`SET n.prop = n.prop + 1`), Cypher acquires a
write lock first, "thus preventing lost updates"; without that direct
dependency, concurrent read-then-write queries can lose updates [18].
Concurrent `MERGE` of a relationship between bound nodes locks both end
nodes and re-matches after locking, a guarantee that "does not rely on a
uniqueness constraint" [13]; for nodes, `MERGE` alone "only guarantees the
existence of the pattern, not its uniqueness", and a uniqueness constraint
closes that gap [13]. `MERGE` takes locks out of order, which can cause
deadlocks [18]. The behaviour is defined and documented, with lost-update
protection depending on query shape or explicit locks.

**Settled by**: isolation, locking and merge semantics found in [13][18]
**Status**: Met

### C8. Retains unmodelled data unchanged

A graph type is open: it "does not impose any constraints on nodes,
relationships, and properties not included by the graph type" [10], and a
database without a graph type accepts any property. What cannot be kept
unchanged is the value shape: maps cannot be stored as properties, and
stored lists must be homogeneous and null-free [1]. Arbitrary nested data
that fits no schema therefore has to be flattened or serialised to a string
before Neo4j will store it.

**Settled by**: open-schema behaviour found in [10]; storage of arbitrary maps contradicted by [1]
**Status**: Unmet

### C9. TypeScript without precision loss

The official driver, `neo4j-driver` 6.2.0 (Apache-2.0, published
2026-06-30) [28], returns integers as its own `Integer` type because
JavaScript numbers cannot hold the full 64-bit range, and it treats any
JavaScript number passed as a parameter as a `Float`; large integers are
written with `neo4j.int` from a string [24]. A `useBigInt` option returns
native `BigInt` values [25], while `disableLosslessIntegers` trades
precision for plain numbers [24][26]. Temporal values keep nanoseconds, and
converting to a JavaScript `Date` drops them [26]. The maker requires "any
LTS version of node.js" [27] and says nothing about Bun; two Bun issues from
2024 reported connections hanging under Bun with driver 5.18 and 5.22, and
both are closed without a visible resolution in the pages read [29][30].

**Settled by**: integer and temporal handling found in [24][25][26]; Node support in [27]; Bun behaviour not published by the maker (searched [24][27], 2026-09-24)
**Status**: Met

### C10. Readable through plain SQL

Interpretation: the nearest equivalent is a maker-supported SQL surface
with conversions from graph values to SQL types. Data lives in Neo4j's own
store, not in SQL tables [17], and the only SQL surface found is the JDBC
driver's limited SQL-to-Cypher translation [31]; no cast layer from Cypher
values to SQL types was found.

**Settled by**: not found beyond [31] (searched [17][31], 2026-09-24)
**Status**: Unmet

### C11. Sustainable dependency

Releases are monthly: tags 2025.01.0 through 2026.09.0, alongside 5.26 LTS
patches [22]. The Community Edition's GPLv3 permits commercial use under
its terms, and a commercial agreement supersedes it for licensees [20];
Enterprise components are closed source [21]. The public branch 2026.09
shows 2,702 commits by 100 distinct author names in the twelve months to
2026-09-24 (Counted) [23]. Governance is a single vendor: contributions
require a CLA [21], Enterprise features are developed outside the public
repository [21], and no foundation or published governance document was
found (searched [21][17], 2026-09-24).

**Settled by**: release history [22], licence text [20][21] and contributor count [23] found; open governance contradicted by single-vendor control and a closed Enterprise edition [21]
**Status**: Unmet

### C12. Latency within twice a hand-designed schema

No independent benchmark comparing Neo4j with a hand-designed relational
schema at the 95th percentile on comparable workloads was found. The only
cross-engine numbers found come from graph-bench, a community harness whose
author also builds a rival engine: on a 10,000-node grid, Neo4j 2026.06.0
answered a point read at a median of 4.33 ms and a three-hop expansion at
2.46 ms over Bolt on a host at load average 37, which the author says
"mostly measure[s] a round trip, a driver and a planner" [33]. An earlier
desktop run reports medians of 608.4 µs and 672.1 µs and 99th percentiles
of 973.5 µs and 1311.9 µs for the same two queries [33]. PostgreSQL 18.6
ran on the same host, but the README prints no PostgreSQL figures for that
run and warns against comparing across tables [33]. None of this settles a
p95 ratio against a hand-designed schema.

**Settled by**: an independent comparable benchmark, not found (searched "benchmark Neo4j versus PostgreSQL recursive CTE graph traversal latency paper 2024 2025", "experimental evaluation graph database systems Neo4j Memgraph Kuzu PostgreSQL", 2026-09-24); community numbers in [33]
**Status**: Unknown

Other notable capabilities the record documents and no criterion requires:

| Capability | What the record says | Source |
|------------|----------------------|--------|
| Row-level security (nice to have) | Property-based and sub-graph access control and role-based access control are Enterprise Edition features | [17] |
| Shortest paths (nice to have) | `SHORTEST` path patterns and shortest-path functions in Cypher 25 | [16] |
| GQL alignment (nice to have) | Conformance statement last updated 1 June 2026 for Neo4j 2026.06; unsupported mandatory features are session and transaction commands, graph and schema references, and reserved words | [2][3] |
| Vector values | Storing `VECTOR` properties needs Enterprise Edition block format or Aura | [1] |
| Change Data Capture | Enterprise Edition only | [17] |
| Scale | Aligned store format supports 34 billion nodes and relationships; sharded property databases, new in 2025.12, are listed only for Enterprise Edition with Infinigraph | [17] |
| Relational read path | The JDBC driver's `sql2cypher` translation lets JDBC tools send limited SQL | [31] |

**Verdict**: No fit. C1 is Unmet because Neo4j is its own server, and C2,
C3, C4, C6, C8, C10 and C11 are Unmet on the maker's own statements; C12 is
Unknown and would not change the verdict.

## Technology and Operations

| Aspect | What the record says | Source |
|--------|----------------------|--------|
| Hosting model | Self-managed CE or EE, standalone or clustered; Neo4j Aura is the managed service and runs the latest server version; Aura regions Not published in pages read (neo4j.com blocked, 2026-09-24) | [17] |
| Integrations | Bolt protocol; official drivers for .NET, Go, Java, JavaScript and Python; APOC procedures; JDBC driver 6.15.0 with limited SQL translation | [17][31] |
| Data handling | Not published in pages read (searched [17]; maker security pages blocked, 2026-09-24) | none |
| Certifications | Search summary only: the Neo4j Trust Center lists SOC 2 Type II and ISO 27001 among others (page not read) | [35] |
| Maturity and cadence | Calendar versioning since 2025.01; monthly releases; 5.26 is the current LTS and a new LTS is expected in 2026 | [17][19][22] |
| Governance | Single vendor; CLA for contributions; Enterprise source not public | [20][21] |
| Security process | No SECURITY.md in the public repository (checked 2026-09-24); a search summary names a responsible-disclosure page on neo4j.com (not read) | [35] |

## Pricing and Licensing

| Item | Figure | Label | Source |
|------|--------|-------|--------|
| Licence, Community Edition | GPLv3; a commercial agreement supersedes it for licensees | Published | [20][21] |
| Licence, Enterprise Edition | Commercial licence required; closed-source components | Published | [21] |
| Enterprise Edition price | Not published in any page read (neo4j.com/pricing blocked, 2026-09-24) | Not published | [36] |
| Aura price | Not published in any page read; a search summary attributes USD 65 per GB-month (Professional) and USD 146 per GB-month (Business Critical) to the maker's pricing page, unverified | Not published | [36] |
| JavaScript driver | Apache-2.0 | Published | [28] |

## Competitive Landscape

Cells for Memgraph and LadybugDB come from this author's research for their
sibling profiles; other rows were not researched here. Sibling slugs other
than the three written with this profile are provisional.

| Candidate | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | Profile |
|-----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|---------|
| Neo4j 2026.09 (CE/EE) | Unmet: own server [17] | Unmet: no decimal [1] | Unmet: no null or map properties [1][4] | Unmet: limits absent; most rules EE-only [8][17] | Met [12][14] | Unmet: no SQL composition [31] | Met [13][18] | Unmet: maps not storable [1] | Met [24][25] | Unmet [31] | Unmet: single vendor [21] | Unknown [33] | this profile |
| Apache AGE | Unknown† | Unmet† | Unmet† | Unknown† | Unknown† | Met† | Unknown† | Met† | Unknown† | Met† | Unknown† | Unknown† | [[component-profile-apache-age]] |
| Palantir OSv2 | Unmet† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-palantir-osv2]] |
| Sqlg | Unknown† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unknown† | Unmet† | Unmet† | Met† | Unmet† | Unknown† | [[component-profile-sqlg]] |
| PuppyGraph | Unmet† | Unknown† | Unknown† | Unmet† | Unknown† | Unmet† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unknown† | [[component-profile-puppygraph]] |
| Gel | Unmet† | Unknown† | Unmet† | Met† | Met† | Unmet† | Met† | Unmet† | Met† | Met† | Unmet† | Unknown† | [[component-profile-gel]] |
| Memgraph 3.13 | Unmet: own server [37] | Unmet: no decimal or bytes [37] | Unmet: null equals absent [37] | Unmet: node-only constraints; none on relationships [38][39] | Met [41] | Unmet: no SQL composition [39] | Unknown: merge semantics undocumented [40] | Met: maps and lists of any type [37] | Met: uses neo4j-driver [43] | Unmet: openCypher only [39] | Unmet: BSL 1.1 [42] | Unknown [33] | [[component-profile-memgraph]] |
| LadybugDB 0.20 | Unmet: embedded engine; pg_ladybug reads only [44][50] | Unmet: no time type; offset dropped [45] | Unmet: missing values are NULL [46] | Unmet: primary key and endpoints only [46][47] | Unmet: no property indexes [47] | Unmet [47][50] | Met: single writer, serializable [48] | Unknown | Unmet: INT64 to JS Number [49] | Unmet [50] | Unmet: one dominant maintainer [51] | Unknown [33] | [[component-profile-ladybugdb]] |
| Datomic | Unmet† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Met† | Unmet† | Unknown† | Unmet† | Unmet† | Unknown† | [[component-profile-datomic]] |
| XTDB | Unmet† | Unknown† | Unknown† | Unmet† | Unmet† | Unmet† | Met† | Met† | Unknown† | Met† | Unmet† | Unknown† | [[component-profile-xtdb]] |
| SurrealDB | Unmet† | Unmet† | Met† | Unknown† | Met† | Unmet† | Met† | Met† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-surrealdb]] |
| UMF-generated per-type PostgreSQL tables | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | *none yet* |
| JSONB plus expression indexes | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | *none yet* |

† Status copied on 2026-09-25 from the sibling profile named in the Profile column, where the evidence and sources are recorded.

- Apache AGE: shares Cypher; the divergence truss cares about is that AGE
  runs inside PostgreSQL. Not researched here; the project's competitive
  analysis records it as an openCypher PostgreSQL extension
  ([[truss.competitive-analysis]] Competitor Profiles).
- Palantir OSv2: Not researched here; see its sibling profile.
- Sqlg: Not researched here; the competitive analysis records a Gremlin
  layer over relational databases ([[truss.competitive-analysis]]).
- PuppyGraph: Not researched here; the competitive analysis records graph
  reads over existing SQL tables with no write path found.
- Gel: Not researched here; see its sibling profile.
- Memgraph: shares Cypher, Bolt and the Neo4j driver with Neo4j [43]; it
  diverges by storing maps and mixed lists as properties [37] and by
  snapshot isolation [40], and by a source-available licence [42].
- LadybugDB: shares the Cypher family; it diverges by an embedded,
  schema-first engine with typed tables, exact `DECIMAL` and declared
  relationship endpoints [45][46], and by an early PostgreSQL extension
  that reads PostgreSQL tables [50].
- Datomic, XTDB, SurrealDB: Not researched here; see their sibling profiles.
- UMF-generated per-type tables and JSONB with expression indexes: Not
  researched; no sibling profile exists yet.

## Confidence

| Grade | Means |
|-------|-------|
| **High** | Every design-defining claim is corroborated by the maker's material *and* at least one independent source, and no design-defining capability is Unknown. |
| **Medium** | Design-defining claims rest on the maker alone, or a design-defining capability is Unknown, or the independent coverage is older than two major versions. |
| **Low** | Thin public footprint; claims rest on one source or on none. |

**Grade**: Medium. The deciding claims, that Neo4j is its own server (C1),
has no decimal type and cannot store null or map properties (C2, C3), and
keeps existence, type and key constraints for the Enterprise Edition (C4),
rest on the maker's documentation alone [1][4][8][17], read from the
version-pinned documentation sources on GitHub because the maker's website
was blocked; a search summary of third-party material agrees on the
Enterprise-only constraints but was not read. The licence is stated
consistently in two maker sources [17][20][21]. Bun behaviour rests on two
community issues [29][30]. Nothing independent measures C12; the only
cross-engine numbers are a community harness by a rival engine's author
[33]. Weakest area: comparative latency and anything on neo4j.com (pricing,
certifications, security process), which could not be read.

## Open Questions

| # | Question | Design-defining because | Route |
|---|----------|-------------------------|-------|
| 1 | On truss's benchmark corpus, what p95 does Neo4j reach for single-object fetch and one-to-three-hop traversal, relative to a hand-designed PostgreSQL schema? | The competitive analysis tells truss not to compete on raw traversal speed with native graph databases; a measured baseline shows how large that gap is for the workloads truss targets | [[tech-spike]] (the benchmark [[truss.vision-input]] asks for before the layout is committed) |
| 2 | Does a Neo4j uniqueness or key constraint treat an `INTEGER` and an equal `FLOAT`, or two canonically equivalent Unicode strings, as the same key? | truss's `sql-exactness` concern requires exact binary key equality; if truss exchanges data with Neo4j, key semantics must round-trip | ask maker, then [[tech-spike]] |
| 3 | Does `neo4j-driver` 6.x run reliably on current Bun? | Matters only if truss or its users move data between truss and Neo4j from Bun (`typescript-bun`) | [[tech-spike]] |

## Sources

Classes: **maker** (the component's maker or governing body), **vendor** (a
company selling hosting or support for the component or a rival),
**independent** (no commercial interest; named author or organisation and a
date), **community** (a project or forum around the component). Documentation
was read from the maker's version-pinned documentation sources on GitHub
because neo4j.com and memgraph.com were blocked by the research
environment's egress proxy; each commit is named.

1. [Property, structural, and constructed values, Cypher Manual 25 (Neo4j 2026.09), docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/values-and-types/property-structural-constructed.adoc), maker, Neo4j, commit of 23 Sep 2026, accessed 24 Sep 2026
2. [GQL conformance, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/appendix/gql-conformance/index.adoc), maker, Neo4j, page last updated 1 Jun 2026 (Neo4j 2026.06), accessed 24 Sep 2026
3. [Currently unsupported mandatory GQL features, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/appendix/gql-conformance/unsupported-mandatory.adoc), maker, Neo4j, accessed 24 Sep 2026
4. [REMOVE, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/clauses/remove.adoc), maker, Neo4j, accessed 24 Sep 2026
5. [SET, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/clauses/set.adoc), maker, Neo4j, accessed 24 Sep 2026
6. [Temporal values, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/values-and-types/temporal.adoc), maker, Neo4j, accessed 24 Sep 2026
7. [Equality, ordering, and comparison of value types, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/values-and-types/ordering-equality-comparison.adoc), maker, Neo4j, accessed 24 Sep 2026
8. [Constraints, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/schema/constraints/index.adoc), maker, Neo4j, accessed 24 Sep 2026
9. [Create constraints, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/schema/constraints/create-constraints.adoc), maker, Neo4j, accessed 24 Sep 2026
10. [Graph types, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/schema/graph-types/index.adoc), maker, Neo4j, accessed 24 Sep 2026
11. [Set graph types, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/schema/graph-types/set-graph-types.adoc), maker, Neo4j, accessed 24 Sep 2026
12. [Create indexes, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/indexes/search-performance-indexes/create-indexes.adoc), maker, Neo4j, accessed 24 Sep 2026
13. [MERGE, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/clauses/merge.adoc), maker, Neo4j, accessed 24 Sep 2026
14. [The impact of indexes on query performance, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/indexes/search-performance-indexes/using-indexes.adoc), maker, Neo4j, accessed 24 Sep 2026
15. [Variable-length paths (syntax and semantics), Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/patterns/reference/variable-length-paths.adoc), maker, Neo4j, accessed 24 Sep 2026
16. [Shortest paths (syntax and semantics), Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/patterns/reference/shortest-paths.adoc), maker, Neo4j, accessed 24 Sep 2026
17. [Introduction (editions, key features per edition, server versions), Operations Manual 2026.09, docs-operations@a4c8c47](https://github.com/neo4j/docs-operations/blob/a4c8c4785b0b9c3c81184ba6c742082430225a56/modules/ROOT/pages/introduction.adoc), maker, Neo4j, commit of 23 Sep 2026, accessed 24 Sep 2026
18. [Concurrent data access, Operations Manual 2026.09, docs-operations@a4c8c47](https://github.com/neo4j/docs-operations/blob/a4c8c4785b0b9c3c81184ba6c742082430225a56/modules/ROOT/pages/database-internals/concurrent-data-access.adoc), maker, Neo4j, accessed 24 Sep 2026
19. [Deprecations, Operations Manual 2026.09, docs-operations@a4c8c47](https://github.com/neo4j/docs-operations/blob/a4c8c4785b0b9c3c81184ba6c742082430225a56/modules/ROOT/pages/deprecations.adoc), maker, Neo4j, accessed 24 Sep 2026
20. [LICENSE.txt, neo4j/neo4j branch 2026.09 at 54a7dcf](https://github.com/neo4j/neo4j/blob/54a7dcf7c2501b31866199143364c5332da8936f/LICENSE.txt), maker, Neo4j Sweden AB, accessed 24 Sep 2026
21. [README.asciidoc (Licensing, Extending Neo4j), neo4j/neo4j at 54a7dcf](https://github.com/neo4j/neo4j/blob/54a7dcf7c2501b31866199143364c5332da8936f/README.asciidoc), maker, Neo4j, accessed 24 Sep 2026
22. [neo4j/neo4j repository and tags](https://github.com/neo4j/neo4j/tags), maker, Neo4j, tags 2025.01.0 to 2026.09.0 and 5.26.31; 17.3k stars shown on the repository page, accessed 24 Sep 2026
23. [neo4j/neo4j commit history, branch 2026.09](https://github.com/neo4j/neo4j/commits/2026.09), maker, Neo4j, Counted by the author from `git log --since=2025-09-24` on 24 Sep 2026 (2,702 commits, 100 distinct author names), accessed 24 Sep 2026
24. [neo4j-javascript-driver README, Numbers and the Integer type, 6.x at 6453219](https://github.com/neo4j/neo4j-javascript-driver/blob/6453219576098a71c8deaf1493a136f5230370c5/README.md), maker, Neo4j, commit of 10 Sep 2026, accessed 24 Sep 2026
25. [neo4j-javascript-driver `packages/core/src/types.ts` (useBigInt), 6.x at 6453219](https://github.com/neo4j/neo4j-javascript-driver/blob/6453219576098a71c8deaf1493a136f5230370c5/packages/core/src/types.ts), maker, Neo4j, accessed 24 Sep 2026
26. [Data types and mapping to Cypher types, JavaScript Driver Manual, docs-drivers@f0bd7ad](https://github.com/neo4j/docs-drivers/blob/f0bd7ad02144e4eb6e19287da9085d411ec9204d/javascript-manual/modules/ROOT/pages/data-types.adoc), maker, Neo4j, commit of 22 Sep 2026, accessed 24 Sep 2026
27. [Installation, JavaScript Driver Manual, docs-drivers@f0bd7ad](https://github.com/neo4j/docs-drivers/blob/f0bd7ad02144e4eb6e19287da9085d411ec9204d/javascript-manual/modules/ROOT/pages/install.adoc), maker, Neo4j, accessed 24 Sep 2026
28. [neo4j-driver package metadata, npm registry](https://registry.npmjs.org/neo4j-driver), maker, Neo4j, version 6.2.0 published 30 Jun 2026, accessed 24 Sep 2026
29. [Support for neo4j-driver, oven-sh/bun issue #9914](https://github.com/oven-sh/bun/issues/9914), community, reporter gramliu, opened 4 Apr 2024, closed, accessed 24 Sep 2026
30. [Different behavior between node and bun when using the Neo4J driver, oven-sh/bun issue #12772](https://github.com/oven-sh/bun/issues/12772), community, reporter nicholasoxford, opened 24 Jul 2024, closed, accessed 24 Sep 2026
31. [Neo4j JDBC Driver README (latest 6.15.0) at 35ec862](https://github.com/neo4j/neo4j-jdbc/blob/35ec8625fa327ea5f85ed3dae847b47bb354ace7/README.adoc), maker, Neo4j (Michael Simons), accessed 24 Sep 2026
32. [BigInteger and BigDecimal values support, neo4j-java-driver issue #727](https://github.com/neo4j/neo4j-java-driver/issues/727), community, reporter nryanov, opened 3 Jun 2020, closed, accessed 24 Sep 2026
33. [graph-bench README at 89ff1c7](https://github.com/tamnd/graph-bench/blob/89ff1c7989e9cf401fcbbb70ca1c60fc4d6f2eaf/README.md), community, tamnd (who also develops the rival `zu` engine), measurements dated 12 to 22 Aug 2026, accessed 24 Sep 2026
34. [Neo4j v5 long-term support and the continued evolution](https://neo4j.com/blog/developer/neo4j-v5-lts-evolution/), maker, Neo4j, Search summary only (host blocked; page not read), accessed 24 Sep 2026
35. [Neo4j Trust Center](https://trust.neo4j.com/), maker, Neo4j, Search summary only (page not read), accessed 24 Sep 2026
36. [Neo4j pricing](https://neo4j.com/pricing/), maker, Neo4j, host blocked; Search summary only, accessed 24 Sep 2026
37. [Data types, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/data-types.mdx), maker, Memgraph, commit of 23 Sep 2026, accessed 24 Sep 2026
38. [Constraints, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/constraints.mdx), maker, Memgraph, accessed 24 Sep 2026
39. [Differences in Cypher implementations, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/querying/differences-in-cypher-implementations.mdx), maker, Memgraph, accessed 24 Sep 2026
40. [Transactions, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/transactions.mdx), maker, Memgraph, accessed 24 Sep 2026
41. [Indexes, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/indexes.mdx), maker, Memgraph, accessed 24 Sep 2026
42. [Memgraph Business Source License 1.1 (as amended 1 Jan 2026), memgraph@6a80124](https://github.com/memgraph/memgraph/blob/6a80124060482583e72610fa268f8a442c0d830c/licenses/BSL.txt), maker, Memgraph Ltd, accessed 24 Sep 2026
43. [Node.js client, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/client-libraries/nodejs.mdx), maker, Memgraph, accessed 24 Sep 2026
44. [LadybugDB README at 2d69bd3](https://github.com/LadybugDB/ladybug/blob/2d69bd3d7e6dd84b8e1438d42553dddd437660b3/README.md), maker, LadybugDB Developers, commit of 23 Sep 2026, accessed 24 Sep 2026
45. [Data types, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/data-types/index.mdx), maker, LadybugDB Developers, commit of 15 Sep 2026, accessed 24 Sep 2026
46. [Create table, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/data-definition/create-table.md), maker, LadybugDB Developers, accessed 24 Sep 2026
47. [Differences between Ladybug and Neo4j, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/difference.md), maker, LadybugDB Developers, accessed 24 Sep 2026
48. [Transactions, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/transaction.md), maker, LadybugDB Developers, accessed 24 Sep 2026
49. [ladybug-nodejs `src_cpp/node_util.cpp` at b62c549](https://github.com/LadybugDB/ladybug-nodejs/blob/b62c5499d266ca1af4053e3e2e61d999c11962d3/src_cpp/node_util.cpp), maker, LadybugDB Developers, commit of 29 Aug 2026, accessed 24 Sep 2026
50. [pg_ladybug README at 895cbdb](https://github.com/LadybugDB/pg_ladybug/blob/895cbdb5d1d0fb7db65e78ac7352795489b91f5d/README.md), maker, LadybugDB Developers, commit of 10 Aug 2026, accessed 24 Sep 2026
51. [LadybugDB commit history, branch main](https://github.com/LadybugDB/ladybug/commits/main), maker, LadybugDB Developers, Counted by the author on 24 Sep 2026 (1,219 commits since 10 Oct 2025, 948 by one author), accessed 24 Sep 2026

**Searched**: Neo4j documentation read from `neo4j/docs-cypher` (branch
`cypher-25`, the published 2026.09 manual) and `neo4j/docs-operations`
(branch `main`, 2026.09) because neo4j.com returned an egress block on
2026-09-24. "decimal", "BigDecimal", "exact decimal" in the Cypher Manual
(no decimal type: C2). "value range", "length", "CHECK" in the constraint
and graph-type pages (no value limits: C4). Uniqueness equality across
`INTEGER` and `FLOAT` in [7][9] (Not published: C4). "neo4j range index
planner NodeIndexSeek" (no independent plan report: C5). "Bun" in the
driver repository and manual (no maker statement: C9); "neo4j-driver Bun
runtime support issue" (found [29][30]). "SQL", "sql2cypher" in [17][31]
(C6, C10). "Neo4j 2026 LTS release long-term support" (found [34] as a
search summary). "benchmark Neo4j versus PostgreSQL recursive CTE graph
traversal latency paper 2024 2025" and "experimental evaluation graph
database systems Neo4j Memgraph Kuzu PostgreSQL VLDB paper 2024 2025
benchmark" (no independent p95 comparison against a hand-designed schema:
C12; found [33]). "DB-Engines ranking graph DBMS September 2026" and
"Stack Overflow Developer Survey 2025 databases Neo4j" (db-engines.com and
survey.stackoverflow.co blocked; no figure in summaries: Adoption Not
published). "Neo4j security advisories vulnerability disclosure policy Aura
SOC 2 ISO 27001" (found [35] as a search summary; data handling Not
published). "Neo4j AuraDB pricing 2026" (neo4j.com/pricing blocked; figures
only in search summaries: Pricing Not published). Blocked hosts:
neo4j.com, memgraph.com, endoflife.date, db-engines.com,
survey.stackoverflow.co, arxiv.org, gdotv.com, arcadedb.com. Apache AGE,
Palantir OSv2, Sqlg, PuppyGraph, Gel, Datomic, XTDB, SurrealDB,
UMF-generated per-type tables and JSONB with expression indexes were not
searched for this profile, hence Not researched.

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
