---
ddx:
  id: truss.component-profile-gel
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

# Component Profile: Gel

Desk research on Gel (formerly EdgeDB), an open-source "graph-relational"
database whose server compiles its own schema and query language to
PostgreSQL, as a candidate for the graph storage and query layer that truss
would otherwise build on PostgreSQL. It is one of several profiles for the
build-or-adopt decision; the choice among candidates belongs to a later ADR,
and what the public record cannot settle is routed below. No hands-on testing
was done. The documentation was read from its sources in the Gel repository,
because docs.geldata.com and geldata.com were blocked by this session's egress
proxy.

## Scope

- Component: Gel server 7.1 (tagged 3 December 2025), self-hosted with an
  external PostgreSQL backend; documentation read from the repository at
  commit `8519106` (23 December 2025, the latest commit on `master`); the
  TypeScript client `gel` 2.2.1 (published 13 September 2026)
- Kind: Technology (open-source database server)
- Would fill: the graph storage and query layer inside an organization's
  existing PostgreSQL (store, traverse, update and constrain connected data
  described by UMF schemas)
- Feeds: the truss build-or-adopt ADR (not yet written)
- Incumbent: *None*. truss has no implementation; teams use hand-built
  per-type tables, JSONB documents or a separate graph database
  ([[truss.product-vision]] §Target Market). truss has no
  current-state inventory.
- Researched: 24 September 2026
- Excluded: Gel Cloud (closed at the end of January 2026); the auth, AI and
  GraphQL extensions; the Python client; hands-on verification of any claim

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
Gel 7.1 enforces declared constraints in PostgreSQL, indexes properties,
defaults to serializable transactions and has a TypeScript client that can
read 64-bit integers and decimals losslessly, but it runs as its own server
that needs a PostgreSQL superuser, has no null to distinguish from absence,
no variable-length traversal, a strictly typed schema that rejects unknown
data, and a maker that shut down in December 2025, so the verdict is No fit.

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

Gel is an open-source database that its maker calls "graph-relational": a
schema of object types with properties and links, queried in EdgeQL, taking
"the best parts of relational databases, graph databases, and ORMs" [1]. Its
server compiles EdgeQL schemas and queries into PostgreSQL queries, according
to a search-engine summary of a 2025 paper by the maker's engineers [45]. It
was made by Gel Data Inc., formerly EdgeDB; the product took the Gel name with
version 6 on 23 February 2025, the v5 release notes being titled "EdgeDB v5"
and the v6 notes "Gel v6" [3][48][8]. On 2 December 2025 the company
announced it was shutting down, with the team joining Vercel, according to
search-engine summaries of the announcement and of Vercel's post [39][40].
The documentation states that Gel Cloud "is sunsetting at the end of January
2026" [38]. Version 1.0 shipped on 9 February 2022 and 7.1 on 3 December 2025
[3]; the licence is Apache-2.0 [2]. The repository shows 14.2k stars and 450
forks as of 24 September 2026 [44], a descriptive figure rather than an
adoption survey.

- Category and purpose: a database server with its own schema language,
  query language and protocols, storing data in PostgreSQL [1][5][6]
- Maker or governing body: Gel Data Inc., which has shut down; no foundation
  or successor steward named in the repository [1][39]
- Adoption, from an independent source: Not published (searched as recorded
  under Sources, 24 Sep 2026)
- Release cadence and support window: one or two major versions a year from
  2022 to 2025 (1.0 February 2022, 2.0 July 2022, 3.0 June 2023, 4.0 October
  2023, 5.0 April 2024, 6.0 February 2025, 7.0 November 2025) [3]; no
  server commit on `master` after 23 December 2025 [4]; no support window
  published (searched [7][8], 24 Sep 2026)
- Licence: Apache License 2.0 [2]
- Built-for use cases: application back ends that want a typed object
  schema, nested queries and migrations, with SQL access through a
  PostgreSQL-protocol adapter [1][8][26]

## Capability Alignment

### C1. Runs inside the user's own PostgreSQL, 17 and 18, on managed services

Interpretation: Gel stores its data in PostgreSQL, but a Gel server process
sits in front of it; applications talk to that server, not to PostgreSQL.
Under the rule that a system requiring its own server does not meet C1, it is
not Met. The server uses a bundled PostgreSQL unless given a backend DSN, in
which case "the PostgreSQL cluster specified by the URI is used instead of the
builtin PostgreSQL server" [6]. The deployment guide adds that the Gel
container needs about 1 GB of RAM and that "when using an external PostgreSQL
instance Gel must connect with the PostgreSQL superuser" [5]. Several Gel
instances can share one PostgreSQL cluster only with distinct tenant IDs [6].
On versions, Gel 7.0 "supports PostgreSQL 14 or above" [7], the server refuses
older backends [9], and Gel 6.5 bundled PostgreSQL 17.4 [8]; PostgreSQL 18 is
not named anywhere in the documentation (searched [5][6][7][8]). The maker
publishes self-hosting guides for AWS Aurora with ECS, Azure Database for
PostgreSQL Flexible Server, Google Cloud SQL, DigitalOcean and Fly.io [5][42]; the
Google guide provisions `POSTGRES_17` [10], and the Azure guide provisions
version 14 and enables the `uuid-ossp` extension that Gel requires [11].

**Settled by**: version floor found in [7][9]; managed-provider guides found in [5][10][11][42]; deployment as its own server with a superuser found in [5][6]
**Status**: Unmet

### C2. UMF's nine scalar families stored exactly

Gel documents `bool`, `int16`, `int32` and `int64` with the full signed 64-bit
range, `float32` and `float64`, arbitrary-precision `bigint` and `decimal`,
`str`, `bytes`, and date and time types [12][13]. Its "philosophy" is that
`decimal` and `bigint` are explicit opt-ins and "should not be accidentally
cast to a different numerical type that could lead to a loss of precision"
[12]. In PostgreSQL these become `int8`, `numeric`, `float8`, `text`, `bytea`,
and Gel-defined domains for dates and timestamps [14]. For time, Gel keeps a
strict separation between the timezone-aware `datetime` and the local
`cal::local_datetime`, `cal::local_date` and `cal::local_time`; it "stores and
outputs timezone-aware values in UTC format", and all date and time types are
limited to years 1 to 9999 [13]. A timestamp's original UTC offset is
therefore not kept, the same hazard [[truss.vision-input]] §Draft Storage
Layers records for `timestamptz`. Whether that loses UMF meaning depends on
UMF's temporal semantics (instant versus civil value, offset retention), which
[[truss.vision-input]] §UMF Gaps lists as not yet designed. The other eight
families have exact documented types.

**Settled by**: type documentation found in [12][13], storage mapping in source [14]; timestamp exactness depends on UMF temporal semantics not yet defined
**Status**: Unknown

### C3. Absent versus null; ordered lists and string-keyed maps

EdgeQL has no null: "the reason EdgeQL introduced the concept of *sets* is to
eliminate the concept of `null`"; in Gel "the absence of data is just an empty
set" [15]. An optional property that was never set and one set to empty are
the same state, so an explicit null cannot be distinguished from absence in a
typed property. Arrays store values of one type "in an ordered list" [16], but
"cannot contain object types or other arrays" [16]; `multi` properties are
unordered sets [17]. There is no map type; string-keyed maps can live only in
a `json` value, where a JSON `null` "can be cast to an empty set" [18].

**Settled by**: null semantics found in [15]; list and map support found in [16][17][18]
**Status**: Unmet

### C4. Rules enforced by the database, honoured by graph writes

Interpretation: EdgeQL `insert`, `update` and `insert ... unless conflict`
stand in for Cypher `CREATE`, `SET` and `MERGE`, and link target types for
allowed edge endpoints. Properties and links are `required` or `optional`
[17][21]; each property has a declared scalar type [17]; built-in constraints
include `exclusive`, `min_value`, `max_value`, `min_len_value`,
`max_len_value`, `regexp`, `one_of` and `expression on (...)` over single
properties and links of one object type [19]. A link has a declared target
type, cardinality and delete policy, `restrict` by default [21]. Writes are
checked against these constraints, and `unless conflict` exists precisely to
catch "exclusivity constraint violations" in an insert [22]. On exact
equality, Gel creates its databases with `LC_COLLATE='C'` [20], so `exclusive`
on `str` compares by code-point order rather than a linguistic collation.

**Settled by**: constraints and their interaction with writes found in [19][21][22]; exact collation found in source [20]
**Status**: Met

### C5. Property indexes used by the planner for graph queries

Interpretation: EdgeQL `filter` stands in for Cypher `WHERE`. Gel supports
`index on (.property)` and expression indexes; ids, links and properties with
an `exclusive` constraint are indexed automatically [23]. The documentation
says indexes speed up filtering, ordering and grouping, and that "the Postgres
query planner decides when to use indexes for a query", with `analyze` to
compare plans [23]. No independent plan evidence was found.

**Settled by**: maker's indexing documentation found in [23]; independent plans not found (searched as recorded under Sources, 24 Sep 2026)
**Status**: Met

### C6. Traversal, pattern matching, aggregation, writes, and SQL composition

Interpretation: EdgeQL coverage stands in for openCypher coverage. Fixed
multi-hop traversal is a path expression, aggregation uses the `group`
statement and aggregate functions [50][12], queries take typed `$` parameters
[49], and writes cover `insert`, `update`, `delete` and upsert through
`unless conflict ... else (update ...)` [22]. Variable-length traversal is absent: an issue asking
for recursive EdgeQL for graph queries, opened on 29 July 2022, remains open
with no maintainer response [24], as does a request for recursive functions
opened on 11 February 2023 [25]. Gel's SQL adapter lets PostgreSQL clients
query Gel types as tables through the Gel server, with a subset of DML since
6.0, but not DDL [26]; EdgeQL cannot be used inside a statement on the user's
own PostgreSQL, and nothing documents joining Gel data with other tables in
that database.

**Settled by**: EdgeQL coverage found in [12][22][49][50]; variable-length traversal absent per open issues [24][25]; SQL composition limited to Gel's own endpoint [26]
**Status**: Unmet

### C7. Transactional writes with defined concurrent behaviour

The default isolation is `serializable`: if concurrent transactions produce
a result no serial order could, "one of them will be rolled back with a
serialization failure" [27]. Every query runs in a transaction, explicit or
implicit [6]. Since 6.0 the default can be set to `RepeatableRead`, which the
documentation warns can allow serialization anomalies [6][27]; the `sys`
reference page still says the isolation enum accepts only `Serializable` [28],
so the maker's pages disagree on whether the weaker level is available, but
none offers anything weaker than repeatable read, and PostgreSQL's Read
Committed level is not offered [6][28]. The TypeScript client's
`transaction()` re-runs the body on transient errors, including serialization
errors, with configurable retries [32]. A single `update ... set { prop :=
... }` statement runs in its own implicit transaction [6], and an upsert is
one `insert ... unless conflict ... else (update ...)` statement [22].
Concurrent `unless conflict` queries once raised spurious constraint errors,
fixed in 2021 [29]; conflicting inserts inside the same query still raise an
error by design, an issue open since 5 February 2021 [30].

**Settled by**: isolation and retry semantics found in [6][27][28][32]; merge behaviour found in [22][29][30]
**Status**: Met

### C8. Data that matches no schema definition is retained unchanged

"Gel schema is strictly typed" [31]; data enters through declared types,
properties and links. No mechanism for keeping undeclared properties is
documented. The documented home for arbitrary data is a declared property of
type `json`, "arbitrary JSON data" [18], which Gel stores as PostgreSQL `jsonb`
[14].

**Settled by**: strict typing found in [31]; `json` catch-all found in [18][14]; retention of undeclared properties not found (searched [17][18][31], 24 Sep 2026)
**Status**: Unmet

### C9. Usable from TypeScript on Bun or Node without numeric loss

The `gel` client installs with npm, Yarn, pnpm or Bun [36]. By default it maps
`int64` and the float types to JavaScript `number`, `bigint` to `BigInt`, and
`datetime` to `Date`, and it has no default JavaScript type for `decimal`;
the documentation advises casting to `str` "for an exact decimal
representation" [32]. In the 2.2.1 source, the default `int64` decoder throws
"cannot unpack ... without losing precision" for values beyond JavaScript's
safe range rather than rounding, the decimal codec yields a string, and the
default `datetime` decoder rounds microseconds to milliseconds [33].
`Client.withCodecs`, added in 2.0.0 [34], lets an application decode `int64`,
`datetime`, `local_time` and `duration` as `bigint` and `decimal` as a string
[33]. A lossless configuration therefore exists, but only when the
application sets those codecs.

**Settled by**: client documentation found in [32][36]; number decoding and custom codecs found in source [33] and release notes [34]
**Status**: Met

### C10. Stored data readable through plain SQL with ordinary types

Interpretation: C10 asks whether other tools can read the data with plain
SQL. Through the SQL adapter, Gel "implements PostgreSQL wire protocol as well
as SQL query language", and "object types in your Gel schema are exposed as
regular SQL tables" to any PostgreSQL-compatible client [26]. That reading
goes through the Gel server; the adapter does not support PostgreSQL logical
replication and lists unsupported statements and functions [26]. In the
backend database itself, user types live in the `edgedbpub` schema in tables
named by object UUID [37], and several scalar types are Gel-defined domains
[14], so direct reading is possible but not in ordinary names.

**Settled by**: SQL access and its limits found in [26]; backend naming found in source [37]
**Status**: Met

### C11. Maintained well enough to be a long-lived dependency

The licence is Apache-2.0 [2]. The maker, Gel Data Inc., announced its
shutdown on 2 December 2025, and Vercel stated it was not commercializing Gel
as a database platform, according to search-engine summaries of the two
announcements [39][40]; the repository documentation confirms Gel Cloud's
end-of-January-2026 sunset and data deletion [38]. The last server release is
7.1 on 3 December 2025 [3]; the last commit on `master` is a migration guide
dated 23 December 2025 [4]; the last Docker image was pushed on 25 December
2025 [43]. Between 24 September and 23 December 2025, 13 people committed to
`master`, dropping to 3 after 3 December [4]. The TypeScript client had a
2.2.1 release on 13 September 2026 [35]. No foundation or successor steward is
named [1].

**Settled by**: licence text found in [2]; release history found in [3][43]; contributor statistics found in [4]; foundation status not found (searched [1][38], 24 Sep 2026)
**Status**: Unmet

### C12. Single-object fetch and 1–3 hop traversal within 2× of a hand-designed schema

Interpretation: the row names AGE; for Gel the equivalent evidence is an
independent benchmark against hand-written SQL on PostgreSQL. The maker's
IMDBench (Rev. 1.0, last changed 6 October 2024) compares ORMs and EdgeDB with
a "tuned PostgreSQL implementation" executed through asyncpg and node-postgres,
under a simulated 1 ms network latency, but publishes its results as charts
whose values the text does not state [46]. No independent benchmark was
found.

**Settled by**: maker benchmark found in [46] without readable figures; independent benchmark not found (searched as recorded under Sources, 24 Sep 2026)
**Status**: Unknown

Other notable capabilities the record documents and no criterion requires:

| Capability | What the record says | Source |
|------------|----------------------|--------|
| Row-level security (nice to have) | Access policies, which the documentation compares to SQL row-level security | [47] |
| Shortest path (nice to have) | Not published; no graph path functions found (searched [12][24], 24 Sep 2026) | none |
| ISO GQL alignment (nice to have) | Not published; the query language is EdgeQL (searched [1][26], 24 Sep 2026) | none |
| Link properties | Links can carry their own properties | [21] |
| Schema migrations | Schema changes are applied as generated DDL migrations | [31] |
| Extensions | PostGIS support added in 6.0 | [8] |

**Verdict**: No fit. C1, C3, C6, C8 and C11 are Unmet: Gel runs as its own
server needing a PostgreSQL superuser, has no null distinct from absence and
no maps, has no variable-length traversal, rejects data outside its strictly
typed schema, and its maker has shut down.

## Technology and Operations

| Aspect | What the record says | Source |
|--------|----------------------|--------|
| Hosting model | Self-hosted server with bundled or external PostgreSQL 14 or later; Gel Cloud closed at the end of January 2026 | [5][7][38] |
| Integrations | Gel binary protocol, HTTP and GraphQL endpoints, PostgreSQL wire protocol (SQL adapter); TypeScript and Python clients | [26][32][36] |
| Data handling | Stored in PostgreSQL databases the Gel server creates from its own template; TLS required by default on the server's endpoints | [20][26] |
| Certifications | Not published for the self-hosted software (searched [1][5], 24 Sep 2026) | none |
| Maturity and cadence | 1.0 February 2022 to 7.1 December 2025; no server commits after 23 December 2025 | [3][4] |
| Governance | Single company, now shut down; no foundation | [1][39] |
| Security process | Not published: no security policy found in the repository root (searched [1], 24 Sep 2026) | none |

## Pricing and Licensing

| Item | Figure | Label | Source |
|------|--------|-------|--------|
| Licence | Apache License 2.0: use, modify and distribute, including commercially, with patent grant | Published | [2] |
| Software cost | None | Published | [2] |
| Gel Cloud | Closed; data deleted after the January 2026 deadline | Published | [38] |
| Commercial support | Not published after the shutdown (searched [38][39], 24 Sep 2026) | Not published | none |

## Competitive Landscape

Columns are the Required Capabilities: C1 in the user's PostgreSQL; C2 exact
scalars; C3 absent/null, lists, maps; C4 database-enforced rules; C5 indexes
used; C6 traversal, writes and SQL composition; C7 concurrency; C8 unknown data
retained; C9 TypeScript without loss; C10 plain-SQL readable; C11 sustainable
maintenance; C12 latency within 2×.

| Candidate | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | Profile |
|-----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|---------|
| Gel 7.1 | Unmet: own server, superuser [5][6] | Unknown: exact types; datetime kept in UTC [12][13] | Unmet: no null; no maps [15][16] | Met: constraints, C collation [19][20] | Met, maker only [23] | Unmet: no variable-length traversal [24] | Met: serializable default, retries [27][32] | Unmet: strict schema [31] | Met with custom codecs [33][34] | Met via Gel's SQL endpoint [26] | Unmet: maker shut down [39][4] | Unknown: maker charts only [46] | this profile |
| Sqlg 3.1.6 | Unknown (plain tables, no version matrix) | Unmet (decimal as double) | Unmet (absent = null; no maps) | Unknown (collation undocumented) | Met | Unmet (no SQL-callable traversal) | Unknown | Unmet | Unmet (JVM only; JS client floats large longs) | Met | Unmet (single maintainer) | Unknown | [[component-profile-sqlg]] |
| PuppyGraph 1.11 | Unmet (own server) | Unknown | Unknown | Unmet (read-only) | Unknown | Unmet (read-only) | Unmet (no writes) | Unmet | Unknown | Met (reads tables in place) | Unmet (proprietary) | Unknown | [[component-profile-puppygraph]] |
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

The Sqlg and PuppyGraph rows carry the statuses from their sibling profiles,
researched in the same session; the evidence and sources for those cells are
in those profiles and are not repeated here.

- Sqlg shares Gel's typed tables in PostgreSQL; it diverges by being a JVM
  library over plain per-label tables with no server of its own, and by
  weaker type fidelity ([[component-profile-sqlg]]).
- PuppyGraph shares a separate server beside PostgreSQL; it diverges by
  owning no tables and having no write path
  ([[component-profile-puppygraph]]).
- Apache AGE shares the aim of graph queries over data in PostgreSQL; it runs
  as an extension inside PostgreSQL; not researched here
  ([[component-profile-apache-age]]).
- Palantir OSv2 is not researched here ([[component-profile-palantir-osv2]]).
- Neo4j, Memgraph and LadybugDB are native graph engines; not researched here
  ([[component-profile-neo4j]], [[component-profile-memgraph]],
  [[component-profile-ladybugdb]]).
- Datomic, XTDB and SurrealDB are not researched here
  ([[component-profile-datomic]], [[component-profile-xtdb]],
  [[component-profile-surrealdb]]).
- UMF-generated per-type tables share Gel's declared, typed, constraint-backed
  tables; the divergence (no separate server, schema from UMF) is not
  researched here.
- JSONB plus expression indexes is not researched here.

## Confidence

| Grade | Means |
|-------|-------|
| **High** | Every design-defining claim is corroborated by the maker's material *and* at least one independent source, and no design-defining capability is Unknown. |
| **Medium** | Design-defining claims rest on the maker alone, or a design-defining capability is Unknown, or the independent coverage is older than two major versions. |
| **Low** | Thin public footprint; claims rest on one source or on none. |

**Grade**: Medium. The technical findings rest on the maker's documentation
sources, read directly at a pinned commit, and on its source code: the server
requirement and superuser [5][6], null semantics [15], constraints and
collation [19][20], isolation [27], strict typing [31], the missing recursion
[24][25] and the client codecs [33]. None is corroborated by an independent
source. The shutdown is corroborated by the maker's own documentation [38] and
the commit and image history [4][43], but the announcement itself was read
only through search-engine summaries [39][40][41]. C2 and C12 are Unknown.
Weakest area: performance (C12), where only a maker benchmark with unreadable
figures exists.

## Open Questions

| # | Question | Design-defining because | Route |
|---|----------|-------------------------|-------|
| 1 | Does UMF require a timestamp to keep its original UTC offset, and does it need years outside 1–9999? | Decides whether Gel's UTC-normalised `datetime` meets C2; the same question applies to every PostgreSQL candidate using `timestamptz` | UMF gap 5 (temporal semantics) in [[truss.vision-input]] §UMF Gaps |
| 2 | Does Gel 7.1 run against PostgreSQL 18, and on managed services that grant no true superuser? | C1 version and managed-service clauses | ask maintainers; [[tech-spike]] |
| 3 | Is anyone maintaining the Gel server after December 2025, and will security fixes ship? | C11 for any long-lived dependency | ask maintainers; watch the repository |
| 4 | How does EdgeQL compare with hand-written SQL on the same data for single-object fetch and 1–3 hop reads? | C12 is truss's proposed performance target | [[tech-spike]] |

## Sources

Classes: **maker** (the component's maker or governing body), **vendor** (a
company selling hosting or support for the component or a rival),
**independent** (no commercial interest; named author or organisation and a
date), **community** (a project or forum around the component). Documentation
files were read from the Gel repository at commit `8519106` (the published
site docs.geldata.com was blocked); sources marked "search-engine summary"
were not read directly.

1. [Gel README](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/README.md), maker, Gel Data Inc., commit of 23 Dec 2025, accessed 24 Sep 2026
2. [Gel LICENSE (Apache-2.0)](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/LICENSE), maker, Gel Data Inc., accessed 24 Sep 2026
3. [Gel release tags](https://github.com/geldata/gel/tags), maker, Gel Data Inc., dates from the tagged commits (v1.0 9 Feb 2022; v2.0 27 Jul 2022; v3.0 21 Jun 2023; v4.0 31 Oct 2023; v5.0 19 Apr 2024; v6.0 23 Feb 2025; v6.11 23 Sep 2025; v7.0 4 Nov 2025; v7.1 3 Dec 2025), accessed 24 Sep 2026
4. [Gel commit history, master](https://github.com/geldata/gel/commits/master), maker, Gel Data Inc., read from a clone with `git log` and `git shortlog`, last commit 23 Dec 2025, accessed 24 Sep 2026
5. [Gel docs: Deployment](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/running/deployment/index.rst), maker, Gel Data Inc., accessed 24 Sep 2026
6. [Gel docs: Server configuration](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/running/configuration.rst), maker, Gel Data Inc., accessed 24 Sep 2026
7. [Gel v7 changelog](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/resources/changelog/7_x.rst), maker, Gel Data Inc., accessed 24 Sep 2026
8. [Gel v6 changelog](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/resources/changelog/6_x.rst), maker, Gel Data Inc., accessed 24 Sep 2026
9. [Gel server source: `MIN_POSTGRES_VERSION`](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/edb/server/defines.py#L46), maker, Gel Data Inc., accessed 24 Sep 2026
10. [Gel docs: Deploying on Google Cloud](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/running/deployment/gcp.rst), maker, Gel Data Inc., accessed 24 Sep 2026
11. [Gel docs: Deploying on Azure Flexible Server](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/running/deployment/azure_flexibleserver.rst), maker, Gel Data Inc., accessed 24 Sep 2026
12. [Gel docs: Numbers](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/stdlib/numbers.rst), maker, Gel Data Inc., accessed 24 Sep 2026
13. [Gel docs: Dates and Times](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/stdlib/datetime.rst), maker, Gel Data Inc., accessed 24 Sep 2026
14. [Gel source: scalar-to-PostgreSQL type map](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/edb/pgsql/types.py#L43-L73), maker, Gel Data Inc., accessed 24 Sep 2026
15. [Gel docs: Sets, "Empty sets"](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/edgeql/sets.rst), maker, Gel Data Inc., accessed 24 Sep 2026
16. [Gel docs: Primitives](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/datamodel/primitives.rst) and [Arrays](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/stdlib/array.rst), maker, Gel Data Inc., accessed 24 Sep 2026
17. [Gel docs: Properties](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/datamodel/properties.rst), maker, Gel Data Inc., accessed 24 Sep 2026
18. [Gel docs: JSON](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/stdlib/json.rst), maker, Gel Data Inc., accessed 24 Sep 2026
19. [Gel docs: Constraints](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/datamodel/constraints.rst), maker, Gel Data Inc., accessed 24 Sep 2026
20. [Gel server source: template database created with `LC_COLLATE='C'`](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/edb/server/bootstrap.py#L477), maker, Gel Data Inc., accessed 24 Sep 2026
21. [Gel docs: Links](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/datamodel/links.rst), maker, Gel Data Inc., accessed 24 Sep 2026
22. [Gel docs: Insert, "Conflicts" and "Upserts"](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/edgeql/insert.rst), maker, Gel Data Inc., accessed 24 Sep 2026
23. [Gel docs: Indexes](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/datamodel/indexes.rst), maker, Gel Data Inc., accessed 24 Sep 2026
24. [Issue #4168: Graph Queries - recursive EdgeQL](https://github.com/geldata/gel/issues/4168), community, kerimcharfi, opened 29 Jul 2022, open, accessed 24 Sep 2026
25. [Gel issues matching "recursive query"](https://github.com/geldata/gel/issues?q=is%3Aissue+recursive+query), community, listing including #5016 "Support recursive functions" (opened 11 Feb 2023, open); title only, accessed 24 Sep 2026
26. [Gel docs: SQL adapter](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/using/sql_adapter.rst), maker, Gel Data Inc., accessed 24 Sep 2026
27. [Gel docs: start transaction](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/reference/edgeql/tx_start.rst), maker, Gel Data Inc., accessed 24 Sep 2026
28. [Gel docs: sys, `TransactionIsolation`](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/stdlib/sys.rst), maker, Gel Data Inc., accessed 24 Sep 2026
29. [Issue #2876: Concurrent complex UNLESS CONFLICT queries can spuriously raise ConstraintViolationError](https://github.com/geldata/gel/issues/2876), maker, Michael J. Sullivan, opened Sep 2021, closed as completed, accessed 24 Sep 2026
30. [Issue #2193: Rethink behavior of INSERT UNLESS CONFLICT inserting two conflicting rows in the same query](https://github.com/geldata/gel/issues/2193), maker, Michael J. Sullivan, opened 5 Feb 2021, open, accessed 24 Sep 2026
31. [Gel docs: Schema (data model index)](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/datamodel/index.rst), maker, Gel Data Inc., accessed 24 Sep 2026
32. [Gel docs: JavaScript client data types](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/using/js/datatypes.rst) and [client transactions](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/using/js/client.rst), maker, Gel Data Inc., accessed 24 Sep 2026
33. [gel-js source at 2.2.1: `buffer.ts`, `codecs/numbers.ts`, `codecs/numerics.ts`, `codecs/datetime.ts`, `codecs/codecs.ts`](https://github.com/geldata/gel-js/tree/2cb25dbb313dfd056efd2fcc3356c6f9b7f01249/packages/gel/src), maker, Gel Data Inc., commit of 13 Sep 2026, accessed 24 Sep 2026
34. [gel-js release v2.0.0](https://github.com/geldata/gel-js/releases?q=withCodecs&expanded=true), maker, Gel Data Inc., npm publication 23 Feb 2025, accessed 24 Sep 2026
35. [`gel` on npm](https://www.npmjs.com/package/gel), maker, Gel Data Inc., 2.2.1 published 13 Sep 2026, read from the registry metadata, accessed 24 Sep 2026
36. [Gel docs: JavaScript client](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/using/js/index.rst), maker, Gel Data Inc., accessed 24 Sep 2026
37. [Gel source: backend schema and table naming](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/edb/pgsql/common.py#L161), maker, Gel Data Inc., accessed 24 Sep 2026
38. [Gel docs: Migrating from Gel Cloud to Self-Hosted](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/cloud/migrate_from.rst), maker, Gel Data Inc., added 23 Dec 2025, accessed 24 Sep 2026
39. [Gel joins Vercel](https://www.geldata.com/blog/gel-joins-vercel), maker, Gel Data Inc., 2 Dec 2025 per summary; page blocked; search-engine summaries only, accessed 24 Sep 2026
40. [Investing in the Python ecosystem](https://vercel.com/blog/investing-in-the-python-ecosystem), vendor, Vercel, date not shown in the summary; page blocked; search-engine summary only, accessed 24 Sep 2026
41. [Gel (ex EdgeDB) shutting down, team joins Vercel](https://news.ycombinator.com/item?id=46168814), community, Hacker News thread; page blocked; title from search results only, accessed 24 Sep 2026
42. [Gel docs: Deploying on AWS Aurora and ECS](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/running/deployment/aws_aurora_ecs.rst), maker, Gel Data Inc., accessed 24 Sep 2026
43. [geldata/gel on Docker Hub](https://hub.docker.com/r/geldata/gel), maker, Gel Data Inc., last updated 25 Dec 2025, tags 7.1 and `latest` 5 Dec 2025, read through the Docker Hub API, accessed 24 Sep 2026
44. [geldata/gel repository page](https://github.com/geldata/gel), community (GitHub), star, fork and issue counts as shown, accessed 24 Sep 2026
45. [Sullivan et al.: Querying Graph-Relational Data](https://arxiv.org/abs/2507.16089), maker, Gel Data engineers (M. J. Sullivan, Z. Chen, E. Pranskevichus, R. J. Simmons, V. Petrovykh, A. Mur Eržen, Y. Selivanov), 23 Jul 2025; page blocked; search-engine summary only, accessed 24 Sep 2026
46. [IMDBench README](https://github.com/geldata/imdbench/blob/88e5eb6a8af39963338eeee513d6e4b39d2396cd/README.rst), maker, Gel Data Inc. (EdgeDB), Rev. 1.0, last commit 6 Oct 2024, accessed 24 Sep 2026
47. [Gel docs: Access Policies](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/datamodel/access_policies.rst), maker, Gel Data Inc., accessed 24 Sep 2026
48. [EdgeDB v5 changelog](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/resources/changelog/5_x.rst), maker, Gel Data Inc. (then EdgeDB), accessed 24 Sep 2026
49. [Gel docs: Parameters](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/edgeql/parameters.rst), maker, Gel Data Inc., accessed 24 Sep 2026
50. [Gel docs: Group](https://github.com/geldata/gel/blob/85191063b4db8b87caf26499de40f8a9d90c8146/docs/reference/edgeql/group.rst), maker, Gel Data Inc., accessed 24 Sep 2026

**Searched**: Gel repository documentation sources (all of `docs/reference`, `docs/cloud` and `docs/resources/changelog`) at commit `8519106` for "postgres" with version numbers, "superuser", "tenant", "isolation", "serializable", "recursive", "null", "strictly typed", "codec", "bun", "shortest", "gql" and "row-level" (24 Sep 2026): PostgreSQL 18 not named (C1), no recursion construct (C6), no undeclared-property retention (C8), no shortest-path or GQL statement; server source (`edb/server/defines.py`, `bootstrap.py`, `pgcluster.py`, `edb/pgsql/types.py`, `common.py`) for version checks, collation and storage mapping; gel-js source and git log for `withCodecs` (added in PR #1161, 10 Jan 2025); GitHub issues for "unless conflict concurrent" and "recursive query"; Docker Hub and npm registry metadata. Web searches (24 Sep 2026): "Gel Data EdgeDB joins Vercel shutting down Gel Cloud January 31 2026 announcement" and "Gel database open source future after Vercel acquisition maintenance community fork 2026" (found [39][40][41]; no successor steward, hence Commercial support Not published); "arXiv 2507.16089 \"Querying Graph-Relational Data\" authors EdgeQL" (found [45]). No independent benchmark or adoption survey was found in any of these searches, hence C12 Unknown and Adoption Not published. Blocked by the egress proxy: geldata.com, docs.geldata.com, vercel.com, news.ycombinator.com, arxiv.org, and the edgedb.github.io benchmark report. Competitive Landscape rows other than Sqlg and PuppyGraph were not searched in this profile, hence Not researched.

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
