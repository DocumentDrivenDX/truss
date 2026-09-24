---
ddx:
  id: truss.component-profile-surrealdb
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

# Component Profile: SurrealDB

Desk research on SurrealDB 3.x as a candidate for the graph storage and
query layer truss would otherwise build, measured against the capabilities
truss needs from that role, and read for the typed-record, schema-mode and
graph-relation ideas truss could borrow. This profile makes no choice among
candidates; the build-versus-adopt decision belongs to an ADR that cites the
profiles, and what reading cannot settle is routed below.

## Scope

- Component: SurrealDB, version 3 line: latest stable tag `v3.2.4` (3
  August 2026) and the 3.3.0 pre-releases (latest tag `v3.3.0-beta.3`, 19
  August 2026), read through the documentation source at commit `47139e7`
  (23 September 2026), whose pages mark features with the version that
  introduced them; features first shipped in 3.3.0 are pre-release as of 24
  September 2026 and are flagged below; self-hosted server or embedded
  library, with the managed service noted
- Kind: Technology (source-available database from a single maker)
- Would fill: the graph storage and query layer for connected, evolving,
  UMF-typed data: typed records, record links and graph relations, schema
  rules on writes, traversal queries
- Feeds: the owner's build-versus-adopt decision for truss; no ADR or
  [[tech-spike]] exists yet
- Incumbent: *None*. truss has no implementation; teams use hand-built
  per-type tables, JSONB documents or a separate graph database
  ([[truss.product-vision]] §Target Market). truss has no
  [[current-state-inventory]].
- Researched: 24 September 2026
- Excluded: hands-on testing of any kind; SurrealDB 1.x and 2.x except
  where the 3.x documentation describes a change; vector, full-text,
  file-storage and Agent Memory features; managed-service pricing, which was
  unreadable. surrealdb.com was blocked by this session's network proxy, so
  the documentation was read from its source repository at the commit
  above, and SDK behaviour was read in the maker's source code (labelled
  "read at commit"; nothing was built or run).

## Summary

truss needs a graph storage and query layer that runs inside an
organisation's existing PostgreSQL for connected domain data described by
UMF schemas, so that teams can store, traverse, update and constrain that
data in place, see which rules are actually enforced, and never lose data
silently. The layer must run inside PostgreSQL 17 and 18 including managed
services, store UMF's nine scalar families exactly, tell an absent property
from an explicit null and keep ordered lists and maps, enforce declared
rules on graph writes, index property values and use those indexes, traverse
and compose with SQL, write safely under concurrency, retain unrecognised
properties, work from TypeScript without precision loss, stay readable
through plain SQL, be a sustainable dependency, and stay within twice a
hand-designed schema's latency. On the public record SurrealDB 3.x meets
the null-handling, indexing, concurrency, unrecognised-data and TypeScript
capabilities, leaves rule enforcement under exact equality and latency
unknown, and fails five, starting with the first: it is its own database on
embedded key-value engines, with no date or time-of-day type, no SQL and a
Business Source Licence, so the verdict is No fit, while its distinction
between `NONE` and `NULL`, its per-table and per-field schema modes and its
typed, endpoint-enforced relations are close prior art for truss's catalog
and binding design.

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
| **Search summary** | Sources | The page was blocked by this session's network proxy; the claim rests on a search engine's summary of the page, not on a reading of it. The Confidence section names every status that rests mainly on such sources. |
| **Read at commit** | Sources | A maker's source repository (code or documentation source) read from a git clone at the named commit; nothing was built or run. |

Capabilities worded in PostgreSQL or Cypher terms (C1, C4, C5, C6, C7, C10, C12) are assessed against the candidate's nearest equivalent, stated in each subsection. A system that needs its own server or storage engine instead of running inside the user's PostgreSQL does not meet C1, whatever else it offers.

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

SurrealDB is a multi-model database written in Rust: one engine stores
documents, graph relations, vectors, full text, time series, geospatial
values and relational tables, and one query language, SurrealQL, reads and
writes across them in a single transaction [6]. At its core it is a document
database: each record is a document held on a transactional key-value
engine (RocksDB, SurrealKV, the in-memory SurrealMX, browser IndexedDB, or
distributed storage in the managed and Enterprise offerings) [7]. It is made
by SurrealDB Ltd [1]. Its schema strictness is set per table, from
schemaless tables that accept any record to schemafull tables that store
only defined fields with types and assertions enforced on write [6][14].
Records link to each other by record id, and graph edges are records in
relation tables created with `RELATE` [14][17].

- Category and purpose: multi-model document and graph database with
  SurrealQL, record links, typed relations and optional schemas [6][7]
- Maker or governing body: SurrealDB Ltd, a single company [1][2]
- Adoption, from an independent source: Not published (searched "SurrealDB
  adoption" and DB-Engines, 24 Sep 2026); a VentureBeat article on the 3.0
  release reports a $23 million Series A extension bringing total funding to
  $44 million, as of February 2026 (search summary) [37]
- Release cadence and support window: `v3.0.0` tagged 17 February 2026,
  `v3.1.0` on 26 May 2026, `v3.2.0` on 2 July 2026, `v3.2.4` on 3 August
  2026 and `v3.3.0-beta.3` on 19 August 2026 (tag commit dates); the 2.x line
  ended at `v2.6.5` [29]; the security policy supports versions 2.0.0 and
  later, as of 24 Sep 2026 [3]
- Licence: Business Source License 1.1 for the core database, with an
  Additional Use Grant that allows any use except offering it as a Database
  Service, converting to Apache 2.0 on 1 January 2030 for SurrealDB 3.0 [1];
  SDKs and some components are Apache-2.0 or MIT [2]
- Built-for use cases: applications that mix document, graph, search and
  relational data in one store, and a memory layer for AI agents built on
  the same engine [6]

## Capability Alignment

### C1. Runs inside the user's own PostgreSQL

Interpretation: the question is whether SurrealDB can live inside the
user's PostgreSQL database. It runs embedded (SurrealMX in memory, RocksDB
or SurrealKV on disk, IndexedDB in the browser), as a single-node server on
RocksDB or SurrealKV, as a multi-node deployment on Kubernetes, or as a
managed instance; each storage engine must support transactional reads and
writes of keys and key ranges, "the whole contract" [7]. PostgreSQL is not
among the storage engines [4][7]; the documentation treats PostgreSQL as a
source to migrate from, with the Surreal Sync tool copying data in [13].
From 3.3.0 (pre-release) SurrealDB can listen on the PostgreSQL wire
protocol, but it runs SurrealQL or ISO GQL there, not SQL, and the data
stays in SurrealDB [22].

**Settled by**: a supported-version matrix for running inside PostgreSQL not found; the maker's storage and deployment models found in [4][7], contradicting the capability
**Status**: Unmet

### C2. Stores UMF's nine scalar families exactly

SurrealQL has `bool`, 64-bit `int`, 64-bit `float`, 128-bit `decimal`,
`string` (any Unicode text), `bytes` and `datetime` [8][9][12]. A numeric
literal without a decimal point that lies outside the 64-bit range is
"parsed, stored, and treated as a 64-bit floating point value", as is any
literal with a decimal point unless it carries the `dec` suffix; casting a
float literal to `decimal` keeps the float's imprecision [9]. Decimals are
implemented with the `rust_decimal` crate 1.41 [4], whose values are a
96-bit integer coefficient, a scale and a sign, with trailing zeros
preserved [5], so roughly 28 to 29 significant digits fit. Datetimes carry
nanosecond precision, but a datetime written with an offset "will be
converted and stored as a UTC date" [10], so the original offset is lost.
There is no date-only type and no time-of-day type: the maker's PostgreSQL
mapping turns `DATE` into a datetime at midnight UTC and `TIME` into a
string because "SurrealDB has no pure time type" [13].

**Settled by**: type-system documentation found in [8][9][10][12]; date and time storage contradicted by [13]; silent integer-to-float parsing stated in [9]
**Status**: Unmet

### C3. Absent versus null; ordered lists and maps

SurrealDB separates `NONE`, meaning a field is not present (setting a field
to `NONE` removes it, like `UNSET`), from `NULL`, which is stored and means
the field exists with no value [11]. Arrays are ordered collections
addressed by index [12], sets are a separate, deduplicated type [8], and
objects hold fields of any type nested to any depth [12]; since 3.0 `NONE`
can also be used as a type, so `string | NONE` is the same as
`option<string>` [11]. One community report, open since March 2026, says a
`NONE` value is not considered by a unique compound index in 3.0.4 [33].

**Settled by**: null, list and map handling found in [8][11][12]
**Status**: Met

### C4. Declared rules enforced by the database

Interpretation: "graph writes" are `CREATE`, `UPDATE`, `UPSERT`, `INSERT`
and `RELATE`. On a `SCHEMAFULL` table, fields must be declared with
`DEFINE FIELD`, and since 3.0 an undefined field makes the write fail
(before 3.0 it was silently dropped) [14]. A field's `TYPE` is checked on
every write, a non-`option` type rules out `NONE` so the field is required,
and literal, union and length-bounded array types narrow values further
[8][12][15]. `ASSERT` evaluates any boolean expression over `$value` on write,
and `READONLY`, `DEFAULT` and `VALUE` control how values are set [15]. A
`UNIQUE` index makes a duplicate value an error [16]. A relation table
declared `TYPE RELATION IN city OUT city` restricts edge endpoints, and
`ENFORCED` rejects a `RELATE` whose endpoints do not exist; before 3.3.0,
restoring an export silently dropped the edges of such tables when the
relation table sorted before its endpoint tables [14]. What the record does
not settle is exact equality: whether a `UNIQUE` index compares strings by
exact bytes and treats `1`, `1.0f` and `1dec` as distinct keys is Not
published (searched [9][16] and the operators page, 24 Sep 2026), and
numbers of different types are documented as comparable with one another
[9]. A community report opened on 23 September 2026 describes a blocking
`DEFINE INDEX` that misses updates committed during the build, leaving a
`UNIQUE` index unenforced for those values on 3.2.4 and 3.3.0-beta.4; it is
open and unconfirmed by the maker, and it cites an earlier issue about
unique values under concurrent creates that was closed after a storage-engine
fix [31].

**Settled by**: constraint documentation found in [8][14][15][16]; exact-equality semantics of unique keys not found (searched [9][16], 24 Sep 2026); issue-tracker evidence in [31]
**Status**: Unknown

### C5. Property indexes used by queries

Interpretation: SurrealQL stands in for Cypher. `DEFINE INDEX` builds
standard (B-tree) indexes on one or more fields, `UNIQUE` indexes, `COUNT`
indexes, full-text indexes and HNSW or DiskANN vector indexes; the planner
uses standard indexes for filtered queries and count scans, and `WITH
NOINDEX` exists to compare plans [16]. `SELECT` accepts `WITH INDEX` hints
and `EXPLAIN` [18]. For traversals, 3.3.0 (pre-release) adds `INLINE` fields
on relation tables, copied into the adjacency entries so a filter inside the
graph path is tested during the scan [15]. Two open community reports, both
unconfirmed by the maker, describe index paths returning wrong results:
the index-build race above [31], and `UPDATE` or `DELETE` with `IN` on the
leading field of a compound index silently matching nothing on 3.1.5, 3.2.4
and 3.3.0-beta.3 [32]. No independent study of plans was found (searched
"SurrealDB index query planner", 24 Sep 2026).

**Settled by**: indexing documentation found in [15][16][18]; issue-tracker reports in [31][32]
**Status**: Met

### C6. Traversal, writes and composition with SQL

Interpretation: SurrealQL (and ISO GQL where offered) stands in for
openCypher; composition means joins with, and use inside, SQL statements in
the user's PostgreSQL. SurrealQL navigates record links and graph edges
with arrow paths (`->friends_with->person`), and since 2.1 recursive paths
with depth ranges such as `.{2}` or `.{1..3}`; since 2.2 the `+path`,
`+collect` and `+shortest=record` modifiers collect paths, collect unique
nodes and find shortest paths [17]. `SELECT` groups, orders and filters,
and statements take parameters [18][24]. Writes include `CREATE`, `UPDATE
... SET` of one field, `UPSERT`, `INSERT`, `DELETE` and `RELATE` [24].
ISO GQL pattern matching and data modification (`MATCH ... RETURN`,
`INSERT`, `SET`, `REMOVE`, `DELETE`) arrived in 3.2.0 behind an experimental
flag and is on by default from 3.3.0 [23]. SQL is not available: "ANSI SQL
is not yet supported over the Postgres wire protocol" [22], and queries run
inside SurrealDB, so they cannot join relational tables in the user's
PostgreSQL or appear inside its statements.

**Settled by**: SurrealQL traversal and write coverage found in [17][18][23][24]; composition with ordinary SQL stated absent in [22]
**Status**: Unmet

### C7. Transactional writes under concurrency

Interpretation: SurrealDB's own isolation contract stands in for
PostgreSQL's levels. Each statement runs in its own transaction unless
grouped with `BEGIN` and `COMMIT` [20]. Every transaction runs under
snapshot isolation on every storage engine; there are no weaker levels and
no serialisable level [19]. On commit the engine checks write conflicts, so
of two transactions writing the same key the later commit fails and must be
retried, with "no silent last-writer-wins merge"; the maker's table marks
dirty reads, non-repeatable reads and same-key lost updates as prevented and
write skew as prevented only for records read with `SELECT ... FOR UPDATE`,
new in 3.3.0 (pre-release), and compares the whole to PostgreSQL's
`REPEATABLE READ` [19]. `UPDATE ... SET balance += 300` updates one field in
place [20], and a concurrent merge on the same record conflicts and retries
[19]. Asynchronous events run after commit in a separate transaction [19].
Community reports describe conflict errors from events and a concurrent
`INSERT IGNORE` that does not ignore an existing record (both open) [34].
No independent consistency analysis was found (searched "SurrealDB Jepsen",
24 Sep 2026).

**Settled by**: concurrency and merge semantics found in [19][20]; issue-tracker reports in [34]; independent analysis not found (searched, 24 Sep 2026)
**Status**: Met

### C8. Retains data that matches no schema definition

A `SCHEMALESS` table accepts any fields [14], and on a `SCHEMAFULL` table
the `FLEXIBLE` clause lets an `object` field (including objects inside
arrays, options and unions) accept keys that are not declared, while
declared subfields keep their types and assertions [15]. Since 3.0 a
schemafull table rejects an undeclared field rather than silently dropping
it [14]. Unrecognised values are therefore kept, within the value domain in
C2 (for example, an integer literal beyond 64 bits becomes a float [9]).

**Settled by**: maker documentation that arbitrary fields and nested keys are stored found in [14][15]
**Status**: Met

### C9. Usable from TypeScript without precision loss

The JavaScript SDK (npm `surrealdb`, latest 2.0.8 published 21 July 2026
[28]) installs with Bun or npm, and the maker's Node.js engine package runs
an embedded database in Node.js, Bun or Deno [25][39]. The SDK
documentation describes a `Decimal` value type compared with arbitrary
precision, `bigint` alongside `number` in record ids and comparisons, and a
`useNativeDates` option that "loses nanosecond precision" when enabled
[25]. At commit `69129d7` the SDK's CBOR codec sends and receives decimals
as tagged strings (tag 10) mapped to its `Decimal` class, and its text
parser returns a `bigint` for integers beyond JavaScript's safe range [26];
the `@surrealdb/cbor` 2.0.0-alpha.4 decoder it depends on returns a
`bigint` for 64-bit integers above 2^53 [27]. Integers, decimals and
datetimes can therefore cross the wire without loss when the defaults are
kept.

**Settled by**: client documentation found in [25], with the wire format read at commit [26][27]
**Status**: Met

### C10. Stored data readable through plain SQL

Interpretation: C10 does not name PostgreSQL, so any SQL interface would
count. SurrealDB offers none: its interfaces are SurrealQL over HTTP and
WebSocket RPC, GraphQL, ISO GQL, and from 3.3.0 (pre-release) a PostgreSQL
wire listener whose query language is SurrealQL or GQL, with "ANSI SQL
translation" and `pg_catalog` emulation listed as not yet included [22][23].
Over that listener, results map to PostgreSQL types where possible (`int8`,
`float8`, `numeric`, `timestamptz`, `bytea`, `jsonb`), record ids become
text, and a column mixing `int` and `float` across rows is widened to
`float8` or `numeric` [22]. Other tools can connect, but they must speak
SurrealQL.

**Settled by**: SQL access and casts to SQL types not found; the maker states ANSI SQL is not supported [22]
**Status**: Unmet

### C11. Sustainable dependency

Releases are frequent: three minor releases and several patches between
February and August 2026 [29]. On the default branch, 793 commits were made
in the twelve months to 24 September 2026 by 48 author names, 45 of them
human [30]. The licence is the Business Source License 1.1, which the maker
states "is not an Open Source license"; it allows production use, including
embedding and internal services, except offering SurrealDB as a commercial
Database Service, and each version converts to Apache 2.0 four years after
release (1 January 2030 for 3.0) [1][2]. Governance sits with SurrealDB Ltd
[1][2]. Interpretation: "open governance" means decisions and code open to
parties other than one company; the record contradicts it, and the licence
permits commercial use only within the grant's limit.

**Settled by**: release history found in [29], contributor statistics in [30], licence text in [1][2]
**Status**: Unmet

### C12. Latency within twice a hand-designed schema

The maker publishes its own benchmarks against PostgreSQL, MongoDB, Neo4j
and Redis with durability enabled (search summary) [36]; they are maker
material, not independent, and no independent benchmark comparing
SurrealDB with a hand-designed relational schema on single-object fetches
and one-to-three-hop traversals was found (searched "SurrealDB benchmark
PostgreSQL independent", "SurrealDB graph traversal performance
comparison", 24 Sep 2026).

**Settled by**: independent benchmark not found (searched, 24 Sep 2026)
**Status**: Unknown

Other notable capabilities the record documents and no criterion requires:

| Capability | What the record says | Source |
|------------|----------------------|--------|
| Record references | `DEFINE FIELD ... REFERENCE` with `ON DELETE REJECT`, `CASCADE`, `IGNORE`, `UNSET` or a custom expression | [15] |
| Lightweight edges (3.3.0, pre-release) | A `LIGHTWEIGHT` relation stores no edge record; its id is the pair of endpoints, so `RELATE` is idempotent and the edge carries no properties | [14] |
| Change feeds | `CHANGEFEED` on a table or database keeps changes for a duration; `INCLUDE ORIGINAL` stores reverse diffs; `SHOW CHANGES FOR TABLE ... SINCE` a timestamp or versionstamp replays them | [14][21] |
| Time travel | With a versioned engine (SurrealMX, RocksDB where supported, or SurrealKV in beta) started with `versioned=true`, `SELECT ... VERSION` reads a table as of a past time | [18] |
| Computed fields (3.0+) | Read-only computed field bodies, capped at the definer's permissions | [15] |
| Permissions (row-level security, nice to have) | Table and field `PERMISSIONS` per `select`, `create`, `update` and `delete`, evaluated against `$auth`, documented as row-level security | [14] |
| Shortest path (nice to have) | `{..+shortest=record:id}` since 2.2; GQL `SHORTEST` and `ALL SHORTEST` | [17][23] |
| ISO GQL (nice to have) | ISO/IEC 39075 reads and writes over tables and `RELATE` edges; experimental in 3.2.x, default from 3.3.0 | [23] |

Design prior art for truss that the record above documents (inputs for
truss's own design, not a recommendation among candidates): a stored `NULL`
distinct from an absent `NONE`, which is the same line truss's draft storage
layers draw between an explicit-null row and no row [11]; schema strictness
chosen per table (`SCHEMAFULL` or `SCHEMALESS`) and relaxed per field
(`FLEXIBLE`), which maps onto truss's strict and report loss modes and its
retained-value table [14][15]; `option<T>`, union and literal types for
field typing [8][15]; relation tables that declare their endpoint tables and
can enforce that endpoints exist [14]; assertions as expressions over the
incoming value [15]; change feeds that keep reverse diffs [21], a journal
shape; depth-ranged recursive paths with shortest-path modifiers [17]; and
edge properties copied into adjacency entries to filter traversals [15].
The record also carries warnings that bear directly on truss's
never-silently-lose rule: undeclared fields were silently dropped before
3.0 [14], enforced relations lost their edges on restore before 3.3.0 [14],
and open community reports describe unique indexes left unenforced and
writes that silently match nothing [31][32]; its documentation's table of
which anomalies snapshot isolation prevents [19] is a model for how truss's
enforcement report could state its isolation assumptions.

**Verdict**: No fit. C1, C2, C6, C10 and C11 are Unmet on the public
record, starting with C1: SurrealDB is its own database on embedded
key-value engines, not a layer inside PostgreSQL.

## Technology and Operations

| Aspect | What the record says | Source |
|--------|----------------------|--------|
| Hosting model | Embedded (in memory, RocksDB, SurrealKV in beta, IndexedDB in browsers), single-node server, multi-node on managed Kubernetes, or managed instances ("Start" single-node and "Scale" multi-node), as of 24 Sep 2026 | [7] |
| Integrations | SDKs for Go, Python, Rust, C, Java, .NET, Node.js and PHP; HTTP, WebSocket RPC, GraphQL and ISO GQL endpoints; PostgreSQL wire listener from 3.3.0 (pre-release) | [7][22][23] |
| Data handling | The managed service applies encryption in transit and at rest and audit logging; 3.x enables disk sync by default while 2.x did not (maker blog, search summary), after an August 2025 independent post criticised durability defaults in the maker's benchmarks (search summary; author not named) | [6][35][36] |
| Certifications | ISO 27001, SOC 2 Type 2 and Cyber Essentials Plus for the managed service; HIPAA and PCI DSS planned, as of 24 Sep 2026 | [38] |
| Maturity and cadence | 3.0.0 February 2026; 3.1 May 2026; 3.2 July 2026; 3.3 in beta from August 2026 (tag commit dates) | [29] |
| Governance | Single vendor, SurrealDB Ltd; 45 human commit authors in the twelve months to 24 Sep 2026 | [1][2][30] |
| Security process | Reports through GitHub security advisories or security@surrealdb.com; acknowledgement within 3 business days; coordinated disclosure; versions 2.0.0 and later supported | [3][38] |

## Pricing and Licensing

| Item | Figure | Label | Source |
|------|--------|-------|--------|
| Licence | Business Source License 1.1 for the core; Additional Use Grant excludes offering a Database Service; converts to Apache 2.0 on 1 January 2030 for SurrealDB 3.0; SDKs Apache-2.0 or MIT | Published | [1][2] |
| Self-hosted use, including production | No licence fee, as of 24 Sep 2026 | Published | [2] |
| Managed instances and Enterprise licence | Not published (searched [2][38] and "SurrealDB pricing"; surrealdb.com/pricing blocked, 24 Sep 2026) | Not published | none |

## Competitive Landscape

Cells for the rows researched in this session (SurrealDB, Datomic, XTDB)
come from each system's own record; the Datomic and XTDB rows summarise
their sibling profiles. Every other row is left to its sibling profile.

| Candidate | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | Profile |
|-----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|---------|
| SurrealDB 3.x | Unmet: own database on key-value engines [7] | Unmet: no date or time type; datetimes converted to UTC; big integers parse as floats [9][10][13] | Met: `NONE` vs `NULL`; arrays; objects [11][12] | Unknown: rules documented; exact-equality semantics of `UNIQUE` not published [14][15][16] | Met: B-tree, unique and composite indexes [16] | Unmet: rich traversal, no ANSI SQL [17][22] | Met: snapshot isolation with write-conflict checks [19] | Met: `SCHEMALESS` and `FLEXIBLE` [14][15] | Met: SDK decodes decimals and 64-bit integers exactly [25][26][27] | Unmet: SurrealQL or GQL only over its wire listener [22] | Unmet: BSL 1.1, single vendor [1][2] | Unknown: no independent benchmark found | this profile |
| Datomic Pro 1.0.7705 | Unmet: own transactor; PostgreSQL holds opaque `bytea` segments [40] | Unmet: no date or time type; millisecond instants [41] | Unmet: no nil; cardinality-many is a set; no maps [41] | Unmet: specs opt-in via `:db/ensure` [41] | Met: AVET, VAET, range predicates [42] | Unmet: Datalog recursion, but no composition with the user's SQL [40][44][47] | Met: serialised transactor; Jepsen Serializable [43] | Unmet: attributes must be installed first [41] | Unknown: community JS client only [45] | Unmet: segments not SQL-readable [40][47] | Unmet: closed source, single vendor [46] | Unknown: no benchmark found | [[component-profile-datomic]] |
| XTDB 2.x | Unmet: own server on object storage and a log [49] | Unknown: nine families typed; decimals capped at precision 64 [53] | Unknown: absent vs null undocumented [53] | Unmet: no schema enforcement; uniqueness only on `_id` [48][52] | Unmet: no user-defined indexes [48] | Unmet: `WITH RECURSIVE` unsupported [51] | Met: serial single-writer log [50] | Met: schemaless dynamic tables [48] | Unknown: int64 as text by default; nested values undocumented [52] | Met: SQL over the PostgreSQL wire protocol [49] | Unmet: single vendor with CLA [49][54] | Unknown: no benchmark found | [[component-profile-xtdb]] |
| Apache AGE | Unknown† | Unmet† | Unmet† | Unknown† | Unknown† | Met† | Unknown† | Met† | Unknown† | Met† | Unknown† | Unknown† | [[component-profile-apache-age]] |
| Palantir OSv2 | Unmet† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-palantir-osv2]] |
| Sqlg | Unknown† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unknown† | Unmet† | Unmet† | Met† | Unmet† | Unknown† | [[component-profile-sqlg]] |
| PuppyGraph | Unmet† | Unknown† | Unknown† | Unmet† | Unknown† | Unmet† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unknown† | [[component-profile-puppygraph]] |
| Gel | Unmet† | Unknown† | Unmet† | Met† | Met† | Unmet† | Met† | Unmet† | Met† | Met† | Unmet† | Unknown† | [[component-profile-gel]] |
| Neo4j | Unmet† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Met† | Unmet† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-neo4j]] |
| Memgraph | Unmet† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Unknown† | Met† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-memgraph]] |
| LadybugDB | Unmet† | Unmet† | Unmet† | Unmet† | Unmet† | Unmet† | Met† | Unknown† | Unmet† | Unmet† | Unmet† | Unknown† | [[component-profile-ladybugdb]] |
| UMF-generated per-type PostgreSQL tables | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | *none yet* |
| JSONB plus expression indexes | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | *none yet* |

† Status copied on 2026-09-25 from the sibling profile named in the Profile column, where the evidence and sources are recorded.

- Datomic Pro shares SurrealDB's schema-as-declarations approach, with
  typed attributes and uniqueness [41]; it diverges by storing immutable
  facts with full history, having no null or map values, and querying in
  Datalog [41][44].
- XTDB 2.x shares the nested, dynamic record model [48]; it diverges by
  keeping bitemporal history of every row and speaking SQL over the
  PostgreSQL wire protocol, while enforcing no schema [48][49][52].
- Apache AGE, Palantir OSv2, Sqlg, PuppyGraph, Gel, Neo4j, Memgraph and
  LadybugDB: shared ground and divergence Not researched here; each named
  sibling profile fills its row.
- UMF-generated per-type PostgreSQL tables and JSONB plus expression
  indexes: Not researched; no sibling profile exists yet. Both keep data in
  the user's PostgreSQL, which SurrealDB can only import from [13].

## Confidence

| Grade | Means |
|-------|-------|
| **High** | Every design-defining claim is corroborated by the maker's material *and* at least one independent source, and no design-defining capability is Unknown. |
| **Medium** | Design-defining claims rest on the maker alone, or a design-defining capability is Unknown, or the independent coverage is older than two major versions. |
| **Low** | Thin public footprint; claims rest on one source or on none. |

**Grade**: Medium. The design-defining claims (storage engines, types,
null handling, schema modes, isolation, SQL absence, licence) rest on the
maker's documentation source, licence files and SDK source read directly at
pinned commits [1]–[30]; the SDK precision finding goes beyond the
documentation by reading code [26][27]. Independent material is thin: a
press article and an unnamed author's durability post, both read as search
summaries [35][37], and community issue reports, which are unconfirmed by
the maker [31][32][33][34]. C4 and C12 are Unknown, and both are
design-defining. Features first shipped in 3.3.0 (the PostgreSQL wire
listener, `FOR UPDATE`, `INLINE`, `LIGHTWEIGHT`) are pre-release as of 24
Sep 2026. The Datomic sibling cells rest partly on search summaries
[41]–[45][47]. Weakest area: unique-key semantics under exact equality and
under concurrent index builds (C4).

## Open Questions

| # | Question | Design-defining because | Route |
|---|----------|-------------------------|-------|
| 1 | Does a `UNIQUE` index compare strings byte for byte, and does it treat `1`, `1.0f` and `1dec` as the same key? | It decides whether SurrealDB could enforce UMF keys under exact equality (C4) | ask maker; [[tech-spike]] |
| 2 | Are the open reports of unique indexes left unenforced after a blocking index build, and of `UPDATE` or `DELETE` silently matching nothing, confirmed and fixed in a stable release? | Silent loss is what truss's concerns forbid | maker's issue tracker (issues 7533 and 7534) |
| 3 | Should truss's catalog adopt SurrealDB's split of per-table strictness and per-field flexibility, and its `NONE`/`NULL` distinction, as the binding-catalog vocabulary for loss modes? | It shapes truss's binding catalog and retained-value report | ADR in truss's design activity, informed by [11][14][15] |
| 4 | Should truss's journal record reverse diffs, as SurrealDB's change feeds do with `INCLUDE ORIGINAL`, or full values per change? | It fixes the journal's format and replay cost | ADR in truss's design activity, informed by [21] |

## Sources

Classes:

- **maker**: the component's maker or governing body
- **vendor**: a company that sells hosting or support for the component or a rival
- **independent**: no commercial interest in the component; a named author or organisation and a date
- **community**: a project or forum around the component

A source with no named author or organisation and no date supports a
descriptive claim only, never a design-defining one. "Read at commit" means
a git clone at the named commit was read and nothing was built or run;
"search summary" means the page was blocked by this session's proxy and only
a search engine's summary of it was available. SurrealDB documentation
sources are files in
[github.com/surrealdb/docs.surrealdb.com](https://github.com/surrealdb/docs.surrealdb.com)
at commit `47139e737a8d17cbdd274322c85bb75dba42cc81` (23 Sep 2026), the
source of the surrealdb.com/docs pages; paths below are relative to
`src/content/`.

1. [SurrealDB `LICENSE` (Business Source License 1.1; Licensed Work SurrealDB 3.0; Change Date 2030-01-01)](https://raw.githubusercontent.com/surrealdb/surrealdb/main/LICENSE), maker, SurrealDB Ltd, accessed 24 Sep 2026
2. [SurrealDB Licensing, `README.md` in surrealdb/license](https://raw.githubusercontent.com/surrealdb/license/main/README.md), maker, SurrealDB Ltd, accessed 24 Sep 2026
3. [SurrealDB `SECURITY.md`](https://raw.githubusercontent.com/surrealdb/surrealdb/main/SECURITY.md), maker, SurrealDB Ltd, accessed 24 Sep 2026
4. [SurrealDB workspace `Cargo.toml` (version 3.3.0-nightly; `rust_decimal` 1.41.0; `surrealkv`, `surrealdb-rocksdb`, `surrealdb-tikv-client` and `indxdb` dependencies)](https://raw.githubusercontent.com/surrealdb/surrealdb/main/Cargo.toml), maker, SurrealDB Ltd, accessed 24 Sep 2026
5. [rust-decimal `README.md`](https://raw.githubusercontent.com/paupino/rust-decimal/master/README.md), community, rust-decimal project (repository `paupino/rust-decimal`), accessed 24 Sep 2026
6. [What is SurrealDB, `index/what-is-surrealdb.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/index/what-is-surrealdb.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
7. [Architecture, `learn/data-models/architecture.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/learn/data-models/architecture.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
8. [Data types, `reference/query-language/language-primitives/data-types/index.mdx`, and sets, `data-types/sets.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/data-types/index.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
9. [Numbers, `data-types/numbers.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/data-types/numbers.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
10. [Datetimes, `data-types/datetimes.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/data-types/datetimes.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
11. [None and null, `data-types/none-and-null.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/data-types/none-and-null.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
12. [Arrays, objects, strings and bytes, `data-types/arrays.mdx`, `objects.mdx`, `strings.mdx`, `bytes.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/data-types/arrays.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
13. [Migrating from PostgreSQL, `build/migrating/from-other-databases/from-postgresql.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/build/migrating/from-other-databases/from-postgresql.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
14. [`DEFINE TABLE` statement, `reference/query-language/statements/define/table.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/statements/define/table.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
15. [`DEFINE FIELD` statement, `statements/define/field.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/statements/define/field.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
16. [`DEFINE INDEX` statement, `statements/define/indexes.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/statements/define/indexes.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
17. [Idioms (graph navigation, recursive paths, shortest path), `language-primitives/idioms.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/idioms.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
18. [`SELECT` statement, `statements/select.mdx` (index hints, `EXPLAIN`, `COLLATE`, `FOR UPDATE`, `VERSION`)](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/statements/select.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
19. [Transactions (concepts and guides), `learn/querying/concepts-and-guides/transactions.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/learn/querying/concepts-and-guides/transactions.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
20. [Transactions, `language-primitives/transactions.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/transactions.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
21. [`SHOW` statement (change feeds), `statements/show.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/statements/show.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
22. [Postgres wire protocol, `reference/rest-api/postgres-protocol.mdx` (since 3.3.0)](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/rest-api/postgres-protocol.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
23. [GQL (ISO graph query language), `learn/querying/gql/overview.mdx` (since 3.2.0)](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/learn/querying/gql/overview.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
24. [SurrealQL statements reference, `reference/query-language/statements/` (`create`, `update`, `upsert`, `insert`, `delete`, `relate`) and parameters, `language-primitives/parameters.mdx`](https://github.com/surrealdb/docs.surrealdb.com/tree/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/statements), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
25. [JavaScript SDK documentation: installation, types (`api/types/index.mdx`) and equality (`api/utilities/equals.mdx`)](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/javascript/api/types/index.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
26. [JavaScript SDK source, `packages/sqon/src/codec/cbor/codec.ts`, `value/decimal.ts` and `codec/text/parser.ts`](https://github.com/surrealdb/surrealdb.js/blob/69129d7d3109c22f55f94954510c392a3e1ebc8e/packages/sqon/src/codec/cbor/codec.ts), maker, SurrealDB Ltd, read at commit `69129d7` (10 Sep 2026), accessed 24 Sep 2026
27. [`@surrealdb/cbor` 2.0.0-alpha.4 package (`dist`, `readMajorLength`)](https://registry.npmjs.org/@surrealdb/cbor/-/cbor-2.0.0-alpha.4.tgz), maker, SurrealDB Ltd, read from the npm tarball, accessed 24 Sep 2026
28. [npm registry metadata for `surrealdb` (latest 2.0.8, published 21 Jul 2026)](https://registry.npmjs.org/surrealdb), maker, SurrealDB Ltd, accessed 24 Sep 2026
29. [SurrealDB release tags (`git ls-remote --tags`; tag commit dates for `v3.0.0`, `v3.0.5`, `v3.1.0`, `v3.2.0`, `v3.2.4`, `v3.3.0-beta.3`; last 2.x tag `v2.6.5`)](https://github.com/surrealdb/surrealdb/tags), maker, SurrealDB Ltd, accessed 24 Sep 2026
30. [SurrealDB commit history on `main`, 24 Sep 2025 to 24 Sep 2026 (793 commits; 48 author names, of which 3 are bots)](https://github.com/surrealdb/surrealdb/commits/main), maker, SurrealDB Ltd, counted from a partial clone, accessed 24 Sep 2026
31. [Blocking `DEFINE INDEX` silently misses UPDATEs committed during the build (issue #7533, open)](https://github.com/surrealdb/surrealdb/issues/7533), community, GitHub user omer9564, published 23 Sep 2026, accessed 24 Sep 2026
32. [UPDATE/DELETE silently match nothing when WHERE uses IN on the leading field of a compound index (issue #7534, open)](https://github.com/surrealdb/surrealdb/issues/7534), community, GitHub user aurorasmartxai, published 24 Sep 2026, accessed 24 Sep 2026
33. [none value is not considered in unique compound index in 3.0.4 (issue #7128, open)](https://github.com/surrealdb/surrealdb/issues/7128), community, published 19 Mar 2026, accessed 24 Sep 2026 (title and status only, from the GitHub search API)
34. [Events that target the same property throw a read or write conflict (issue #6246, open, 18 Aug 2025)](https://github.com/surrealdb/surrealdb/issues/6246) and [`INSERT IGNORE` won't silently ignore the record already existing during a concurrent write (issue #5518, open, 10 Feb 2025)](https://github.com/surrealdb/surrealdb/issues/5518), community, accessed 24 Sep 2026 (titles and status only, from the GitHub search API)
35. [SurrealDB is sacrificing data durability to make benchmarks look better](https://blog.cf8.gg/surrealdbs-ch/), independent, author not named, published around August 2025 (per linked discussion threads), accessed 24 Sep 2026 (search summary; descriptive use only)
36. [SurrealDB 3.x by the numbers](https://surrealdb.com/blog/surrealdb-3-x-by-the-numbers), maker, SurrealDB Ltd, accessed 24 Sep 2026 (search summary)
37. [SurrealDB 3.0 wants to replace your five-database RAG stack with one](https://venturebeat.com/data/surrealdb-3-0-wants-to-replace-your-five-database-rag-stack-with-one), independent, VentureBeat, published February 2026 (per the summary), accessed 24 Sep 2026 (search summary)
38. [Organisations FAQs, `manage/organisations/faqs.mdx` (certifications, security reporting)](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/manage/organisations/faqs.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
39. [Node.js engine, `reference/javascript/engines/node.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/javascript/engines/node.mdx), maker, SurrealDB Ltd, read at commit, accessed 24 Sep 2026
40. [Datomic Pro 1.0.7705 distribution, `bin/sql/postgres-table.sql` and `config/samples/sql-transactor-template.properties`](https://datomic-pro-downloads.s3.amazonaws.com/1.0.7705/datomic-pro-1.0.7705.zip), maker (Datomic), Nu North America, Inc., published 10 Jul 2026, accessed 24 Sep 2026 (read by HTTP range requests)
41. [Datomic Schema Data Reference](https://docs.datomic.com/schema/schema-reference.html), maker (Datomic), accessed 24 Sep 2026 (search summary)
42. [Datomic Indexes](https://docs.datomic.com/indexes/index-model.html) and [Executing Queries](https://docs.datomic.com/query/query-executing.html), maker (Datomic), accessed 24 Sep 2026 (search summary)
43. [Jepsen: Datomic Pro 1.0.7075](https://jepsen.io/analyses/datomic-pro-1.0.7075), independent, Jepsen (Kyle Kingsbury), published 15 May 2024, accessed 24 Sep 2026 (search summary)
44. [Datomic Query Reference](https://docs.datomic.com/query/query-data-reference.html), maker (Datomic), accessed 24 Sep 2026 (search summary)
45. [Datomic Peer Language Support](https://docs.datomic.com/operation/languages.html) (search summary) and [datomic-client-js](https://github.com/csm/datomic-client-js) (community, Casey Marshall, read at commit `59c03a7`, 25 Feb 2026), accessed 24 Sep 2026
46. [Maven Central, `com.datomic/peer` POM 1.0.7705](https://repo1.maven.org/maven2/com/datomic/peer/1.0.7705/peer-1.0.7705.pom) and the [Datomic GitHub organisation](https://github.com/Datomic), maker (Datomic), Nu North America, Inc., accessed 24 Sep 2026
47. [Datomic Analytics Support](https://docs.datomic.com/analytics/analytics-concepts.html) and [JDBC](https://docs.datomic.com/analytics/analytics-jdbc.html), maker (Datomic), accessed 24 Sep 2026 (search summary)
48. [XTDB documentation source, `concepts/key-concepts.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/concepts/key-concepts.md), maker (XTDB), JUXT Ltd, read at commit `6cd79ee` (23 Sep 2026), accessed 24 Sep 2026
49. [XTDB `README.adoc` and `LICENSE`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/README.adoc), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026
50. [XTDB documentation source, `about/txs-in-xtdb.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/about/txs-in-xtdb.md), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026
51. [XTDB `core/src/main/clojure/xtdb/sql.clj` (recursive CTEs rejected) and `reference/main/sql/queries.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/core/src/main/clojure/xtdb/sql.clj), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026
52. [XTDB documentation source, `drivers/nodejs.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/drivers/nodejs.md), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026
53. [XTDB documentation source, `reference/main/data-types.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/reference/main/data-types.md), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026
54. [XTDB `CONTRIBUTING.adoc`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/CONTRIBUTING.adoc), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026

**Searched**: Network access: surrealdb.com (documentation, blog, pricing,
releases), blog.cf8.gg, venturebeat.com and db-engines.com answered 403 at
this session's proxy on 24 Sep 2026; github.com (git clones and the GitHub
search API), raw.githubusercontent.com and the npm registry were readable.
The documentation tree at commit `47139e7` was searched for "postgres"
(PostgreSQL appears only as a migration source and a wire protocol, hence
C1 and C10), "coerc" (type checks on write, C4), "collat",
"case-sensitiv" and "normali" in the index, numbers, strings and operators
pages (no exact-equality statement for unique keys, hence C4 Unknown and
Open Question 1), "rust_decimal", "significant digits" and "Decimal128"
(no stated decimal precision, hence the crate-based bound in C2),
"isolation", "serializ" and "conflict" (found [19]), "wire protocol",
"JDBC" and "ODBC" (found [22]), "SOC 2" and "ISO 27001" (found [38]),
"security@" and "disclos" (found [38]), "SYNC_DATA" and "fsync" (no
storage durability default in the documentation; audit-log settings only),
and "bigint", "Decimal" and "precision" in the JavaScript reference (found
[25]). GitHub issue searches in surrealdb/surrealdb: "transaction isolation
lost update concurrent write conflict bug data loss" (found [34]) and
"unique index concurrent insert duplicate values race" (found [31][33]);
"UNIQUE not enforced under concurrent CREATE" did not surface the closed
issue that [31] cites. Web searches (24 Sep 2026): "SurrealDB durability
SURREAL_SYNC_DATA default fsync benchmarks" and the post title (found
[35][36]); "SurrealDB license BSL 1.1 change 3.0 Database Service" (found
[1][2]); "SurrealDB 3.0 release review independent analysis graph database
2026" (found [37] and maker pages only); "DB-Engines ranking SurrealDB
Datomic XTDB" (no scores; pages blocked, hence Adoption Not published);
"SurrealDB Jepsen" (nothing, hence C7 rests on the maker);
"SurrealDB benchmark PostgreSQL independent" and "SurrealDB graph
traversal performance comparison" (maker benchmarks only, hence C12
Unknown); "SurrealDB index query planner" (nothing independent);
"SurrealDB pricing" (page blocked, hence the managed-pricing row). Apache
AGE, Palantir OSv2, Sqlg, PuppyGraph, Gel, Neo4j, Memgraph, LadybugDB,
UMF-generated per-type tables and JSONB plus expression indexes were not
searched in this profile, hence Not researched.

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
