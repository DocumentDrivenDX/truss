---
ddx:
  id: truss.component-profile-puppygraph
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

# Component Profile: PuppyGraph

Desk research on PuppyGraph, a proprietary graph query engine that reads
existing SQL and lakehouse tables in place, as a candidate for the graph
storage and query layer that truss would otherwise build on PostgreSQL. It is
one of several profiles for the build-or-adopt decision; the choice among
candidates belongs to a later ADR, and what the public record cannot settle
is routed below. No hands-on testing was done. PuppyGraph's documentation,
website and pricing pages were blocked by this session's egress proxy, so
several findings rest on the maker's GitHub repositories and Docker Hub
listing, and others on search-engine summaries, each labelled where used.

## Scope

- Component: PuppyGraph 1.x (image `puppygraph/puppygraph`, 1.0.0 released
  30 June 2026, 1.11.1 current on 18 September 2026), Developer and
  Enterprise editions, self-hosted, with a PostgreSQL catalog as the data
  source
- Kind: Product (proprietary software)
- Would fill: the graph storage and query layer inside an organization's
  existing PostgreSQL (store, traverse, update and constrain connected data
  described by UMF schemas)
- Feeds: the truss build-or-adopt ADR (not yet written); the Follow-up
  research item "confirm whether PuppyGraph supports writes" in
  [[truss.competitive-analysis]] §Strategic Implications
- Incumbent: *None*. truss has no implementation; teams use hand-built
  per-type tables, JSONB documents or a separate graph database
  ([[truss.product-vision]] §Target Market). truss has no
  current-state inventory.
- Researched: 24 September 2026
- Excluded: lakehouse, warehouse and non-PostgreSQL sources; the Graph RAG
  and MCP tooling beyond what bears on client access; the PuppyGraph 0.x line;
  hands-on verification of any claim

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
PuppyGraph 1.x leaves PostgreSQL data where it is and answers openCypher and
Gremlin reads over it, but it runs as its own server beside PostgreSQL, offers
no graph write path, and is proprietary software from one company, so the
verdict is No fit.

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

PuppyGraph is a proprietary graph query engine that maps existing relational,
warehouse and lakehouse tables to a graph schema and answers openCypher and
Gremlin queries over them without copying data into a graph database [4][9].
It is made by PuppyQuery Inc, which holds the copyright and licenses the
software under its own end-user agreement [1]. Its maker's material describes
the problem it solves as querying data "directly over raw PostgreSQL tables
with no ETL required" [4], and its Python client lists zero-ETL access,
dynamic schema changes and Cypher and Gremlin support among its features [9].
The Docker image was registered in May 2022 and had 251,882 pulls as of
24 September 2026 [1]; version 1.0.0 shipped on 30 June 2026 and 1.11.1 on
18 September 2026 [2]. According to a search-engine summary of a press
release, the company raised a $5 million seed round led by Defy.vc in
October 2024 [18].

- Category and purpose: a graph query engine over existing SQL and
  lakehouse tables, deployed as its own service [4][5]
- Maker or governing body: PuppyQuery Inc [1]
- Adoption, from an independent source: Not published; a review aggregator
  listed no reviews (searched as recorded under Sources, 24 Sep 2026)
- Release cadence and support window: roughly weekly image releases in
  August and September 2026 (1.5.0 on 9 August through 1.11.1 on
  18 September) [2]; no support window found (searched [1][2], 24 Sep 2026;
  documentation blocked)
- Licence: proprietary, "All Rights Reserved", used under the PuppyQuery
  Software License Agreement [1]; the agreement itself was blocked
- Built-for use cases: graph analytics over existing data such as supply
  chain dependency and risk tracing, cybersecurity and fraud-style multi-hop
  queries, from the maker's demos [4][7][23]

## Capability Alignment

### C1. Runs inside the user's own PostgreSQL, 17 and 18, on managed services

Interpretation: PuppyGraph leaves PostgreSQL data where it is, but it does
not run inside PostgreSQL; it is a separate server that connects to
PostgreSQL over JDBC. The maker's PostgreSQL demo starts PostgreSQL and
PuppyGraph as two containers, with PuppyGraph serving its web interface,
Gremlin and Bolt on ports 8081, 8182 and 7687 [5], and the graph schema
declares a `postgresql` catalog reached through a JDBC URI and driver class
[6]. Under the rule that a system requiring its own server does not meet C1,
it is not Met. Which PostgreSQL versions it reads from is also unsettled: the
maker's demos use PostgreSQL 14.1, 15 and untagged `postgres` images [23], and a search-engine
summary of the "Connecting to PostgreSQL" page did not include versions [14].

**Settled by**: deployment as its own server found in [5][6]; supported-version matrix not found (searched [14][23], 24 Sep 2026; documentation blocked)
**Status**: Unmet

### C2. UMF's nine scalar families stored exactly

PuppyGraph stores nothing in the user's PostgreSQL; the question is whether
values pass through its type system exactly. According to a search-engine
summary of the maker's "Attribute Types" page, attributes may be Boolean,
Byte, Short, Int, Long, HugeInt, Float, Double, Decimal(P, S), String, Date
and DateTime [10]. The maker's demo schemas corroborate `DECIMAL(3,1)`,
`DECIMAL(5,2)`, `Long`, `Int`, `Double`, `String`, `Date`, `DateTime`,
`Boolean` and `HUGEINT` attributes [6][23]. No time-of-day or binary type
appears in either, and no conversion or precision rules were readable.

**Settled by**: type list found only as a search-engine summary [10] and in demo schemas [6][23]; conversion and precision rules not found (searched [10][23], 24 Sep 2026; documentation blocked)
**Status**: Unknown

### C3. Absent versus null; ordered lists and string-keyed maps

No statement on null handling was found. The summarised attribute-type list
names no list or map type [10], while another summary of the same
documentation mentions "collections" among the documented data types [10];
the two summaries do not agree, and the page could not be read. The maker's
demo schemas use scalar attributes only [23].

**Settled by**: not found (searched [10][23], 24 Sep 2026; documentation blocked)
**Status**: Unknown

### C4. Rules enforced by the database, honoured by graph writes

Interpretation: the graph writes in C4 would be openCypher or Gremlin
`CREATE`, `MERGE` and `SET` (Gremlin `addV`, `mergeV`, `property`).
PuppyGraph's schema is a mapping from source columns to graph attributes and
identifiers [6], not a set of constraints it enforces. No graph write path
appears in any maker demo, all of which upload a schema and run read queries
[4][7][23]. A search-engine summary of a Redpanda post says PuppyGraph "is
read-only on the lakehouse storage" [16], and another search-engine summary,
whose source page was not identified, states that you "read through it" and
"write through your existing databases using their normal clients". The 1.x
documentation, per a search-engine summary, offers manual row insertion into
PuppyGraph-managed local tables from its web interface only [13]; that is
data in PuppyGraph's own storage, not graph writes into PostgreSQL. Rules on
the source tables are whatever PostgreSQL enforces on writes made outside
PuppyGraph.

**Settled by**: absence of graph writes found in summaries [13][16] and the maker's demos [4][7][23]; no constraint mechanism found (searched [6][10][13], 24 Sep 2026)
**Status**: Unmet

### C5. Property indexes used by the planner for graph queries

According to search-engine summaries of maker blog posts, PuppyGraph issues
only simple projection and filter queries to a SQL store such as PostgreSQL
and performs the multi-hop work in its own engine, which uses columnar,
vectorised execution, predicate pushdown and min/max statistics [17]. Version
1.x adds local tables, called "local cache" in 0.x, "for better query
performance", and the maker's demo loads them before querying [7]. Whether
PostgreSQL indexes serve the pushed-down filters, and how traversal steps use
any index, was not found.

**Settled by**: pushdown found only in search-engine summaries [17]; index use not found (searched [7][17], 24 Sep 2026; documentation blocked)
**Status**: Unknown

### C6. Traversal, pattern matching, aggregation, writes, and SQL composition

Reads are well covered: the maker's demos run multi-hop openCypher `MATCH`
patterns and Gremlin traversals with `count()` aggregation [4], and bounded
variable-length patterns such as `*1..3` [7]. According to a search-engine
summary, PuppyGraph supports openCypher version 9 and its release notes
improved the error for unbounded variable-length relationships (`[*]`,
`[*1..]`) to "suggest a bounded alternative" [11][12], which indicates that
unbounded patterns are rejected. Writes are absent (C4). Graph queries run
in PuppyGraph's own engine [17] and no way to use them inside a PostgreSQL
statement was found.

**Settled by**: read coverage found in [4][7] and summaries [11][12]; write support contradicted as in C4; SQL composition not found (searched [4][11][17], 24 Sep 2026)
**Status**: Unmet

### C7. Transactional writes with defined concurrent behaviour

There is no graph write path to be transactional (C4). The read-only design
means concurrency and merge semantics for graph writes do not arise.

**Settled by**: absence of writes found as in C4 [13][16]
**Status**: Unmet

### C8. Data that matches no schema definition is retained unchanged

PuppyGraph exposes only the attributes a schema maps, each declared with a
source field, a target name and a type [6]. It has no write path through
which unrecognised data could be stored (C4); columns left out of the mapping
stay in the source table but are not part of the graph.

**Settled by**: mapping-only exposure found in [6]; no retention mechanism found (searched [6][10][13], 24 Sep 2026)
**Status**: Unmet

### C9. Usable from TypeScript on Bun or Node without numeric loss

The maker's TypeScript MCP server connects to PuppyGraph with `neo4j-driver`
over Bolt for Cypher and the `gremlin` package over WebSocket for Gremlin,
on Node.js 18 or later [8]. The Neo4j JavaScript driver returns 64-bit
integers as its own lossless `Integer` type unless configured otherwise [21];
TinkerPop's JavaScript driver converts longs beyond ±(2^53 − 1) with
`parseFloat` [22]. How PuppyGraph encodes `Decimal(P, S)` and `HugeInt`
values over Bolt or Gremlin, and whether Bun is supported, was not found.

**Settled by**: client libraries found in [8]; driver number handling found in [21][22]; decimal and 128-bit encoding not found (searched [8][9][10], 24 Sep 2026)
**Status**: Unknown

### C10. Stored data readable through plain SQL with ordinary types

Interpretation: PuppyGraph has no stored graph values of its own in
PostgreSQL. Its design reads source tables in place [4], through a schema
that points at existing tables and columns [6], so the stored data remains
ordinary PostgreSQL rows readable by any SQL tool. The 1.x local tables are
copies held by PuppyGraph for performance [7][13] and are not part of the
user's PostgreSQL.

**Settled by**: in-place reads found in [4][6]
**Status**: Met

### C11. Maintained well enough to be a long-lived dependency

Releases are frequent: sixteen numbered images from 1.0.0 on 30 June 2026 to
1.11.1 on 18 September 2026 [2]. Governance is one company's: the image is
"Copyright © 2023-2026 PuppyQuery Inc - All Rights Reserved" and use is
subject to the PuppyQuery Software License Agreement [1]. No engine source
repository appears among the maker's public repositories, which are demos,
clients and tools under Apache-2.0 [3]. According to a search-engine summary of Tracxn, the
company had 22 employees as of 30 April 2026 [19]. Whether the free
Developer Edition permits commercial use could not be checked because the
agreement and the pricing page were blocked [1][15].

**Settled by**: licence notice found in [1]; release history found in [2]; foundation status not applicable (single vendor) [1]; contributor statistics not available for closed source
**Status**: Unmet

### C12. Single-object fetch and 1–3 hop traversal within 2× of a hand-designed schema

Interpretation: the row names AGE; for PuppyGraph the equivalent evidence is
an independent benchmark against a relational or native-graph baseline. None
was found. The maker's own material claims "sub-second multi-hop queries" on
petabyte-scale data, according to a search-engine summary [17]; that is a
vendor claim, not a measurement against the 2× target.

**Settled by**: independent benchmark not found (searched as recorded under Sources, 24 Sep 2026)
**Status**: Unknown

Other notable capabilities the record documents and no criterion requires:

| Capability | What the record says | Source |
|------------|----------------------|--------|
| Two query languages | openCypher and Gremlin over the same schema | [4] |
| Many source types | Demo schemas use PostgreSQL, Iceberg, Delta Lake, Hudi, Trino, Glue, Unity, Snowflake, Redshift and MongoDB catalogs | [23] |
| Local tables | 1.x keeps optional local copies of mapped tables for performance; renamed from "local cache" in 0.x | [7][13] |
| Schema format change | 1.x uses a v2 schema format and converts v1 schemas on upload | [7] |
| Row-level security (nice to have) | Not published (searched [10][13][14], 24 Sep 2026; documentation blocked) | none |
| Shortest path (nice to have) | Not published (searched [11][12], 24 Sep 2026) | none |
| ISO GQL alignment (nice to have) | Not published; openCypher version 9 per summary | [11] |

**Verdict**: No fit. C1 is Unmet because PuppyGraph runs as its own server
beside PostgreSQL, C11 because it is proprietary software from one company,
and C4, C6, C7 and C8 because no graph write path exists on the record as it
could be read.

## Technology and Operations

| Aspect | What the record says | Source |
|--------|----------------------|--------|
| Hosting model | Self-hosted Docker container; per a search-engine summary of the pricing page, a single-node Developer Edition and an Enterprise Edition with clustering, deployable by AWS AMI or Docker | [5][15] |
| Integrations | JDBC sources; Bolt on 7687 for Cypher; Gremlin over WebSocket on 8182; web interface on 8081; Python client; MCP server | [5][8][9] |
| Data handling | Reads source tables in place; optional local tables copy data into PuppyGraph's storage | [4][7][13] |
| Certifications | Not published (searched [1][3]; puppygraph.com blocked, 24 Sep 2026) | none |
| Maturity and cadence | Image registered May 2022; 1.0.0 on 30 June 2026; 1.11.1 on 18 September 2026 | [1][2] |
| Governance | Single vendor, PuppyQuery Inc; proprietary licence | [1] |
| Security process | Not published (searched [3], 24 Sep 2026; website blocked) | none |

## Pricing and Licensing

| Item | Figure | Label | Source |
|------|--------|-------|--------|
| Licence | PuppyQuery Software License Agreement; "All Rights Reserved" | Published | [1] |
| Developer Edition | Free: single-node Docker, up to 2 data sources and 8 vCores, community support (read through a search-engine summary of the pricing page, as of 24 Sep 2026) | Published | [15] |
| Enterprise Edition | Custom pricing based on CPU and memory used; 30-day free trial (read through a search-engine summary, as of 24 Sep 2026) | Not published (no figure; searched [15], 24 Sep 2026) | [15] |

## Competitive Landscape

Columns are the Required Capabilities: C1 in the user's PostgreSQL; C2 exact
scalars; C3 absent/null, lists, maps; C4 database-enforced rules; C5 indexes
used; C6 traversal, writes and SQL composition; C7 concurrency; C8 unknown data
retained; C9 TypeScript without loss; C10 plain-SQL readable; C11 sustainable
maintenance; C12 latency within 2×.

| Candidate | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | Profile |
|-----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|---------|
| PuppyGraph 1.11 | Unmet: own server over JDBC [5][6] | Unknown: Decimal(P,S) listed; no time or binary type [10] | Unknown: null handling not found [10] | Unmet: no graph writes [13][16] | Unknown: pushdown only [17] | Unmet: reads only, bounded paths [7][12] | Unmet: no writes [16] | Unmet: mapped attributes only [6] | Unknown: Bolt and Gremlin drivers; decimal encoding not found [8][21] | Met: tables read in place [4][6] | Unmet: proprietary, single vendor [1] | Unknown: no benchmark found | this profile |
| Sqlg 3.1.6 | Unknown (plain tables, no version matrix) | Unmet (decimal as double) | Unmet (absent = null; no maps) | Unknown (collation undocumented) | Met | Unmet (no SQL-callable traversal) | Unknown | Unmet | Unmet (JVM only; JS client floats large longs) | Met | Unmet (single maintainer) | Unknown | [[component-profile-sqlg]] |
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

The Sqlg and Gel rows carry the statuses from their sibling profiles,
researched in the same session; the evidence and sources for those cells are
in those profiles and are not repeated here.

- Sqlg shares PuppyGraph's Gremlin interface and its reading of relational
  tables as a graph; it diverges by storing and writing the graph in the
  user's PostgreSQL through a JVM library ([[component-profile-sqlg]]).
- Gel shares nothing of PuppyGraph's zero-copy approach; it owns its tables in
  PostgreSQL and enforces a declared schema, through its own server
  ([[component-profile-gel]]).
- Apache AGE shares the goal of Cypher over PostgreSQL data; it runs inside
  PostgreSQL rather than beside it; not researched here
  ([[component-profile-apache-age]]).
- Palantir OSv2 is not researched here ([[component-profile-palantir-osv2]]).
- Neo4j, Memgraph and LadybugDB are native graph engines that hold their own
  data; not researched here ([[component-profile-neo4j]],
  [[component-profile-memgraph]], [[component-profile-ladybugdb]]).
- Datomic, XTDB and SurrealDB are not researched here
  ([[component-profile-datomic]], [[component-profile-xtdb]],
  [[component-profile-surrealdb]]).
- UMF-generated per-type tables and JSONB plus expression indexes are not
  researched here; either could in principle be the tables PuppyGraph reads.

## Confidence

| Grade | Means |
|-------|-------|
| **High** | Every design-defining claim is corroborated by the maker's material *and* at least one independent source, and no design-defining capability is Unknown. |
| **Medium** | Design-defining claims rest on the maker alone, or a design-defining capability is Unknown, or the independent coverage is older than two major versions. |
| **Low** | Thin public footprint; claims rest on one source or on none. |

**Grade**: Low. The C1 finding (its own server over JDBC) rests on the
maker's demo configuration [5][6], and the C11 finding on the maker's licence
notice [1]; both are direct reads of maker material. The read-only finding
behind C4, C6, C7 and C8 rests on search-engine summaries [13][16] and on the
absence of writes in the maker's demos, not on a maker statement read in
full. C2, C3, C5 and C9 rest on single summaries or on nothing. No
independent source was read in full; the one independent article found [20]
was blocked. Weakest area: the type system and null handling (C2, C3),
because the maker's documentation site could not be reached.

## Open Questions

| # | Question | Design-defining because | Route |
|---|----------|-------------------------|-------|
| 1 | Does PuppyGraph 1.x offer any openCypher or Gremlin write (`CREATE`, `MERGE`, `SET`, `addV`) against a PostgreSQL source? | Confirms the read-only finding behind C4, C6, C7 and C8, which [[truss.competitive-analysis]] listed as follow-up research | ask maker |
| 2 | What attribute types, null handling and collection types does PuppyGraph support, and how are `Decimal(P, S)` and `HugeInt` encoded over Bolt and Gremlin? | Decides C2, C3 and C9 should PuppyGraph be considered as a read path over truss-managed tables | ask maker; read the documentation from an unrestricted network |
| 3 | Do filters pushed down to PostgreSQL use its indexes, and how do local tables affect freshness? | C5 and C12 for any read-path role | [[tech-spike]] |
| 4 | Does the Developer Edition licence permit commercial production use? | C11 licence clause | ask maker (the PuppyQuery Software License Agreement) |

## Sources

Classes: **maker** (the component's maker or governing body), **vendor** (a
company selling hosting or support for the component or a rival),
**independent** (no commercial interest; named author or organisation and a
date), **community** (a project or forum around the component). The egress
proxy blocked puppygraph.com, docs.puppygraph.com and every third-party page
tried except GitHub, Docker Hub and the npm registry; sources marked
"search-engine summary" were not read directly.

1. [puppygraph/puppygraph on Docker Hub](https://hub.docker.com/r/puppygraph/puppygraph), maker, PuppyQuery Inc, description with copyright and licence notice, registered 9 May 2022, last updated 18 Sep 2026, read through the Docker Hub API, accessed 24 Sep 2026
2. [puppygraph/puppygraph tags on Docker Hub](https://hub.docker.com/r/puppygraph/puppygraph/tags), maker, PuppyQuery Inc, 190 tags including 1.0.0 (30 Jun 2026) to 1.11.1 (18 Sep 2026) and `stable` (11 Feb 2026), accessed 24 Sep 2026
3. [PuppyGraph GitHub organization](https://github.com/puppygraph), maker, PuppyQuery Inc, public repositories and licences, accessed 24 Sep 2026
4. [Supply Chain Graph Analytics Demo README](https://github.com/puppygraph/puppygraph-getting-started/blob/be8cf64197f28f731609d423c38ec7b357e21b46/use-case-demos/supply-chain-demo/README.md), maker, PuppyQuery Inc, commit of 22 Sep 2026, accessed 24 Sep 2026
5. [Supply Chain demo docker-compose.yaml](https://github.com/puppygraph/puppygraph-getting-started/blob/be8cf64197f28f731609d423c38ec7b357e21b46/use-case-demos/supply-chain-demo/docker-compose.yaml), maker, PuppyQuery Inc, commit of 22 Sep 2026, accessed 24 Sep 2026
6. [Supply Chain demo schema.json](https://github.com/puppygraph/puppygraph-getting-started/blob/be8cf64197f28f731609d423c38ec7b357e21b46/use-case-demos/supply-chain-demo/schema.json), maker, PuppyQuery Inc, commit of 22 Sep 2026, accessed 24 Sep 2026
7. [Finance Trino demo README](https://github.com/puppygraph/puppygraph-getting-started/blob/be8cf64197f28f731609d423c38ec7b357e21b46/use-case-demos/finance-trino-demo/README.md), maker, PuppyQuery Inc, commit of 22 Sep 2026, accessed 24 Sep 2026
8. [PuppyGraph MCP Server README and package.json](https://github.com/puppygraph/puppygraph-mcp-server/blob/0c6b2b2c7fcba6b4742af404280e2b4c2b5e707c/README.md), maker, PuppyQuery Inc, version 1.1.0, commit of 26 Aug 2026, accessed 24 Sep 2026
9. [puppygraph-python README](https://github.com/puppygraph/puppygraph-python/blob/4268b2b525e0255c358a31cde0e37b1b0b04f5e1/README.md), maker, PuppyQuery Inc, client 0.1.6, commit of 27 Aug 2026, accessed 24 Sep 2026
10. [PuppyGraph Docs: Attribute Types](https://docs.puppygraph.com/reference/schema/attribute-types/), maker, PuppyQuery Inc, page blocked; search-engine summaries only, accessed 24 Sep 2026
11. [PuppyGraph Docs: Querying using openCypher](https://docs.puppygraph.com/querying/querying-using-opencypher/) and [Cypher Query Language](https://docs.puppygraph.com/reference/cypher-query-language/), maker, PuppyQuery Inc, pages blocked; search-engine summary only, accessed 24 Sep 2026
12. [PuppyGraph Docs: Releases](https://docs.puppygraph.com/releases/), maker, PuppyQuery Inc, page blocked; search-engine summaries only, accessed 24 Sep 2026
13. [PuppyGraph Docs: Managing the Graph](https://docs.puppygraph.com/modeling/managing-the-graph/), maker, PuppyQuery Inc, page blocked; search-engine summary only, accessed 24 Sep 2026
14. [PuppyGraph Docs: Connecting to PostgreSQL](https://docs.puppygraph.com/connecting/connecting-to-postgresql/), maker, PuppyQuery Inc, page blocked; search-engine summary without version information, accessed 24 Sep 2026
15. [PuppyGraph Pricing](https://www.puppygraph.com/pricing), maker, PuppyQuery Inc, page blocked; search-engine summary only, accessed 24 Sep 2026
16. [Real-time graph analytics with Redpanda Iceberg Topics and PuppyGraph](https://www.redpanda.com/blog/real-time-graph-analytics-iceberg-puppygraph), vendor, Redpanda (a streaming-platform company and PuppyGraph integration partner), author and date not shown in the summary; page blocked; search-engine summary only, accessed 24 Sep 2026
17. [PostgreSQL Graph Database: Everything You Need To Know](https://www.puppygraph.com/blog/postgresql-graph-database) and other PuppyGraph blog pages returned for "PuppyGraph predicate pushdown PostgreSQL", maker, PuppyQuery Inc, pages blocked; search-engine summaries only, accessed 24 Sep 2026
18. [PuppyGraph Raises $5 Million in Seed Funding Led by Defy.vc](https://www.businesswire.com/news/home/20241023866174/en/PuppyGraph-Raises-$5-Million-in-Seed-Funding-Led-by-Defy.vc-to-Bring-Zero-ETL-GraphRAG-and-Real-Time-Graph-Analytics-To-Market), maker (press release), PuppyGraph, 23 Oct 2024; page blocked; search-engine summary only, accessed 24 Sep 2026
19. [PuppyGraph company profile](https://tracxn.com/d/companies/puppygraph/__tGLpP3iI2fkqC05e4JRCdzyhDOs68QGdAVF8ujO9dNg), independent, Tracxn, employee count as of 30 Apr 2026; page blocked; search-engine summary only, accessed 24 Sep 2026
20. [PuppyGraph: Graph Queries on SQL Database Without Migration](https://dgg32.medium.com/puppygraph-graph-queries-on-sql-database-without-migration-96c63fc932b3), independent, Sixing Huang, 2 Jan 2026; page blocked; search-engine summary only, accessed 24 Sep 2026
21. [Neo4j JavaScript driver README, "Numbers and the Integer type"](https://github.com/neo4j/neo4j-javascript-driver/blob/6.0/README.md), vendor, Neo4j (maker of the Bolt driver PuppyGraph's own client uses), 6.0 branch, accessed 24 Sep 2026
22. [Gremlin-JavaScript 3.8.2 LongSerializer.js](https://github.com/apache/tinkerpop/blob/3.8.2/gremlin-javascript/src/main/javascript/gremlin-javascript/lib/structure/io/binary/internals/LongSerializer.js#L95-L102), independent, Apache TinkerPop (no commercial interest in PuppyGraph), tag 3.8.2, accessed 24 Sep 2026
23. [puppygraph-getting-started use-case and integration demos](https://github.com/puppygraph/puppygraph-getting-started/tree/be8cf64197f28f731609d423c38ec7b357e21b46), maker, PuppyQuery Inc, all demo schemas and compose files at the commit of 22 Sep 2026, accessed 24 Sep 2026

**Searched**: Docker Hub API for the image description, pulls and tags; GitHub organization and clones of `puppygraph-getting-started`, `puppygraph-python` and `puppygraph-mcp-server`, grepping schema types, `localDataSource`, "postgres" images, and Cypher and Gremlin write keywords (`MERGE`, `CREATE (`, `SET`, `addV(`, `addE(`, `mergeV`, `.property(`, `DETACH DELETE`) in every demo README and script (24 Sep 2026): no write statement, no PostgreSQL 16–18 image, no time, binary, list or map attribute. Web searches (24 Sep 2026): "PuppyGraph docs PostgreSQL data source supported versions connect" (no versions, hence C1 version matrix not found); "PuppyGraph read-only graph query engine write support mutations CREATE MERGE" and "\"PuppyGraph\" FAQ \"does not support\" writes OR \"write operations\" OR \"read-only\" graph query engine" (found [16] and an unattributed summary); "docs.puppygraph.com FAQ \"write\" data through PuppyGraph insert update graph" and "PuppyGraph \"standalone local table\" OR \"local tables\" \"Insert Rows\" managing the graph" (found [13]); "PuppyGraph schema attribute data types Decimal DateTime supported types documentation" and "\"PuppyGraph\" \"Attribute Types\" Int Long Float Double String Boolean Date DateTime Decimal List Map" (found [10]; null handling not found, hence C3 Unknown); "PuppyGraph openCypher support limitations variable length path shortestPath unsupported clauses" (found [11][12]; shortest path not found); "PuppyGraph predicate pushdown PostgreSQL index query performance JDBC data source local tables columnar" (found [17]; index use not found, hence C5 Unknown); "PuppyGraph pricing developer edition free enterprise edition license terms" (found [15]); "PuppyGraph company founded funding seed round investors employees" (found [18][19]); "PuppyGraph independent review OR evaluation OR benchmark 2025 2026 graph query engine relational" (no independent benchmark; PeerSpot listed no reviews, hence C12 Unknown and Adoption Not published); "Sixing Huang \"PuppyGraph: Graph Queries on SQL Database Without Migration\" medium" (found [20]). Blocked by the egress proxy: puppygraph.com, docs.puppygraph.com, redpanda.com, polaris.apache.org, medium.com, businesswire.com, tracxn.com. Competitive Landscape rows other than Sqlg and Gel were not searched in this profile, hence Not researched.

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
