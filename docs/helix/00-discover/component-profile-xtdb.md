---
ddx:
  id: truss.component-profile-xtdb
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

# Component Profile: XTDB

Desk research on XTDB 2.x as a candidate for the graph storage and query
layer truss would otherwise build, measured against the capabilities truss
needs from that role, and read for the history, time and provenance ideas
truss could borrow. This profile makes no choice among candidates; the
build-versus-adopt decision belongs to an ADR that cites the profiles, and
what reading cannot settle is routed below.

## Scope

- Component: XTDB, version 2 line: latest stable tag `v2.1.0` (1 December
  2025) and the `v2.2.0` pre-releases (latest tag `v2.2.0-beta2`, 17
  September 2026), read through the documentation source on the default
  branch at commit `6cd79ee` (23 September 2026), whose pages mark
  version-specific features "(v2.1+)" or "(v2.2+)"; self-hosted
- Kind: Technology (open-source database from a single maker)
- Would fill: the graph storage and query layer for connected, evolving,
  UMF-typed data, or, in part, the per-value history and provenance journal
  truss plans beside it
- Feeds: the owner's build-versus-adopt decision for truss; no ADR or
  [[tech-spike]] exists yet
- Incumbent: *None*. truss has no implementation; teams use hand-built
  per-type tables, JSONB documents or a separate graph database
  ([[truss.product-vision]] §Target Market). truss has no
  [[current-state-inventory]].
- Researched: 24 September 2026
- Excluded: hands-on testing of any kind; XTDB 1.x (a different engine and
  Datalog API); cloud-provider sizing and costs; the Kafka Connect source;
  ADBC and Flight SQL beyond a mention. docs.xtdb.com and xtdb.com were
  blocked by this session's network proxy, so the documentation was read
  from its source in the maker's repository at the commit above, and a few
  behaviours were read in the maker's source code at the same commit
  (labelled "read at commit"; nothing was built or run).

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
hand-designed schema's latency. On the public record XTDB 2.x meets the
concurrency, unrecognised-data and SQL-readability capabilities, leaves
exact scalar storage, null handling, the TypeScript path and latency
unknown, and fails the rest, starting with the first: it is its own
database server on object storage and a transaction log that speaks the
PostgreSQL wire protocol, has no schema enforcement, no user-defined indexes
and no recursive queries, so the verdict is No fit, while its bitemporal
columns, transaction-metadata table and PostgreSQL change-data-capture
source are direct prior art for truss's history and provenance design.

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

XTDB is an open-source immutable SQL database that keeps the full history of
every table and lets queries travel in two time dimensions: system time,
when the database learned a fact, and valid time, when the fact holds in the
business domain [1][5]. It is written and supported by JUXT Ltd, which holds
the copyright [1]. Version 2 is a new engine: a columnar store built on
Apache Arrow, designed for object storage, with all writes serialised
through a totally ordered log and a single writer, and with a SQL dialect
(plus the XTQL language) served over the PostgreSQL wire protocol [1][5][7].
Its documentation positions it as "a bitemporal and dynamic relational
database for regulated data", built to implement the SQL:2011 temporal
features in a first-class way [6], and it draws on the epochal time model
of Rich Hickey's talk "The Database as a Value" [7].

- Category and purpose: bitemporal, schemaless relational database with SQL
  and XTQL, for auditable, time-versioned records [1][5][6]
- Maker or governing body: JUXT Ltd, a single company; contributions need a
  signed Contributor License Agreement [1][3]
- Adoption, from an independent source: Not published (searched
  "XTDB 2.0 review", DB-Engines and "XTDB adoption", 24 Sep 2026)
- Release cadence and support window: `v2.0.0` tagged 11 June 2025, `v2.1.0`
  on 1 December 2025, `v2.2.0-rc0` on 21 July 2026, `v2.2.0-rc1` on 6
  August 2026 and `v2.2.0-beta2` on 17 September 2026 (tag commit dates)
  [23]; the security policy supports 2.x and 1.24.x, as of 24 Sep 2026 [4]
- Licence: Mozilla Public License 2.0, or at the user's option any later
  version [1][2]
- Built-for use cases: regulated data, audit history without custom audit
  tables, backfills and corrections in valid time, and point-in-time
  analysis, per the maker [6][8]

## Capability Alignment

### C1. Runs inside the user's own PostgreSQL

Interpretation: XTDB speaks PostgreSQL's wire protocol, but the question is
where the data and the engine live. An XTDB node is its own JVM server with
a transaction log (Kafka, or a local or in-memory log for a single node)
and a storage module (in memory, local disk, or a remote object store with
a local cache), and it serves SQL through its own PostgreSQL
wire-compatible server, on port 5432 in the maker's Docker images [18].
Nothing in the record runs XTDB inside a PostgreSQL database or ships it as an extension (searched [1][18] and the
documentation tree for "extension", 24 Sep 2026). The closest link to an
existing PostgreSQL is the v2.2 external source, which subscribes to a
PostgreSQL 17 or later database by logical replication (`wal_level=logical`,
a publication and a replication slot) and keeps a read-only bitemporal
mirror of its tables inside XTDB [19]; the data still lives in XTDB's own
storage.

**Settled by**: a supported-version matrix for running inside PostgreSQL not found; the maker's deployment model found in [1][18], contradicting the capability; the PostgreSQL external source found in [19]
**Status**: Unmet

### C2. Stores UMF's nine scalar families exactly

The documented types cover every family: `BOOLEAN`; `SMALLINT`, `INT` and
64-bit `BIGINT`; fixed-point `DECIMAL(p, s)`; 32- and 64-bit IEEE floats;
`VARCHAR`/`TEXT`; `VARBINARY`; `DATE`; `TIME`; `TIMESTAMP` without a zone and
`TIMESTAMP WITH TIMEZONE`, whose literals may carry an offset and a zone
name such as `[Europe/London]` [9]; whether a stored value keeps that
offset or zone name is not stated (searched [9], 24 Sep 2026). Overflow in
temporal arithmetic raises an exception [9]. Decimals are bounded: the maker recommends precision 32
or 64 because other precisions are still stored at 128 or 256 bits; a
precision-32 result that would overflow raises an exception, and
`::DECIMAL` with no arguments means `DECIMAL(64, 9)` [9]. What happens to a
decimal with more than 64 significant digits is Not published (searched
[9], 24 Sep 2026). Mixing a decimal with a float converts to floating point
[9]. At commit `6cd79ee` the SQL grammar parses a numeric literal with a
decimal point as a double (`visitFloatLiteral` calls `parse-double`) while
integer literals outside the 64-bit range are an error [13]; a decimal
therefore needs a cast or a typed parameter, a difference from PostgreSQL
the documentation does not state. The type set fits; exactness at the
precision bound and at the literal boundary is not settled by the
documentation.

**Settled by**: type-system documentation found in [9]; behaviour beyond precision 64 not found (searched [9], 24 Sep 2026); literal parsing read at commit [13]
**Status**: Unknown

### C3. Absent versus null; ordered lists and maps

`ARRAY` values are ordered lists (sets are a separate type), and `OBJECT` or
`RECORD` values map keys to values, nested to any depth [9]. Whether a
stored row or object distinguishes an absent key from an explicit `NULL` is
not documented: the standard library speaks of "non-absent" fields in a
struct and of values that are "false, null or absent" [17], `obj->field`
returns `NULL` when the field does not exist [17], and `PATCH` preserves the
stored key "if a key is absent or null" in the patch document, so a patch
cannot set a key to null [11]. At commit `6cd79ee` the struct reader drops
null-valued fields from the maps it returns (`filterValues { it != null }`
in `StructVector.getObject0`), and keyword keys are normalised to lower case
with `-` replaced by `_` before storage, while string keys are kept as given
[16]. Read together these suggest a nested explicit null may come back
absent, but that is a reading of code, not a documented rule or an observed
result.

**Settled by**: list and map types found in [9]; null handling not documented (searched [9][11][17] and the documentation tree for "absent" and "null", 24 Sep 2026); source behaviour read at commit [16]
**Status**: Unknown

### C4. Declared rules enforced by the database

Interpretation: "graph writes" are SQL or XTQL DML (`INSERT`, `UPDATE`,
`PATCH`, `DELETE`). The Node.js driver page states that XTDB "learns your DB
schema as you enter data" and "doesn't provide a way for specifying and
enforcing a schema in advance" [14]. `CREATE TABLE` (v2.2+) only declares
column names and does not yet accept types [10]. XTDB has no foreign keys
and "no concept of uniqueness beyond the ID"; other schema-dependent
features are "not available within XTDB currently", while "gradual schema"
work is under way [5]. What the record offers instead is `ASSERT`, which
rolls a transaction back when a predicate is false, for example `ASSERT NOT
EXISTS (SELECT 1 FROM users WHERE email = ...)` before an insert [11];
because write transactions are serialised [7], such checks are free of
races, but each writer has to include them, so they are not declared rules.

**Settled by**: constraint documentation found in [5][10][14], which states the capability is absent; the per-transaction `ASSERT` alternative found in [11]
**Status**: Unmet

### C5. Property indexes used by queries

Interpretation: SQL and XTQL queries stand in for Cypher. The documentation
lists indexes among the schema-dependent features "not available within
XTDB currently" [5], and no `CREATE INDEX` statement appears in the SQL
reference (searched [10][11][12], 24 Sep 2026). XTDB does maintain a
dedicated temporal index [5][6], an LSM tree whose deeper levels are
partitioned by a hash of the primary key (IID), and per-block and per-page
metadata that lets the engine skip data that cannot match temporal or
content conditions [22]; the maker's 2024 internal note on index strategies
treats unique-key and selective-attribute lookups as cases metadata must
rule out, not as user-declared indexes [22]. No independent report of query
plans was found (searched "XTDB query performance index", 24 Sep 2026).
Equality and range lookups on arbitrary properties therefore rest on data
skipping, which the user cannot declare.

**Settled by**: indexing documentation found in [5][22], which states user-defined indexes are unavailable; independent reports not found (searched, 24 Sep 2026)
**Status**: Unmet

### C6. Traversal, writes and composition with SQL

Interpretation: XTDB SQL and XTQL stand in for openCypher; composition means
joins with, and use inside, SQL statements in the user's PostgreSQL. XTDB
SQL supports joins, lateral subqueries, window functions, parameters (`?`
and `$n`), aggregates and nested subqueries [12], and XTQL unifies across
relations with logic variables [5]. Multi-hop traversal is written as
self-joins; variable-length traversal is not available: "`WITH RECURSIVE` is
not yet supported in XTDB" [12], the SQL front end at commit `6cd79ee`
raises "Recursive CTEs are not supported yet" [13], and the issue asking for
common table expressions (§7.13) has been open since 6 April 2022 [25].
Writes cover `INSERT` (an upsert over the valid-time range), `UPDATE ... SET`
of chosen columns, `PATCH` (a key-level merge), `DELETE` and `ERASE` [11].
Queries run in XTDB, so they cannot join tables in the user's PostgreSQL or
appear inside its SQL statements. Shortest-path queries are Not published
(searched [12] and the XTQL reference, 24 Sep 2026).

**Settled by**: SQL coverage found in [12]; variable-length traversal stated absent in [12][13][25]; composition with the user's SQL contradicted by the deployment model [18]
**Status**: Unmet

### C7. Transactional writes under concurrency

Interpretation: XTDB's serial log stands in for PostgreSQL's isolation
levels. Write transactions are non-interactive: they may contain only DML
and `ASSERT`, statements inside run in order and see earlier effects, and
mixing `SELECT` into a write transaction is an error [7][11]. All write
transactions are serialised through a totally ordered durable log and
indexed one at a time, which the maker calls "trivially consistent to the
highest isolation level - 'serializable'" [7]; a single writer processes
transaction logic serially and deterministically on each database's leader
[5], and since v2.2 other nodes follow the leader's resolved results [21]. `UPDATE t SET version = version + 1 WHERE _id = ?` reads current state
inside the transaction [7], so single-property updates are atomic;
concurrent merges are ordered by the log, with `INSERT` overwriting the
document and `PATCH` merging key by key [11]. Reads across connections may
lag writes unless an `AWAIT_TOKEN` is passed [7]. No independent analysis
of XTDB 2.x consistency was found (searched "XTDB Jepsen", "XTDB 2
consistency analysis", 24 Sep 2026).

**Settled by**: concurrency and merge semantics found in [5][7][11]; independent analysis not found (searched, 24 Sep 2026)
**Status**: Met

### C8. Retains data that matches no schema definition

XTDB is schemaless: new tables and columns can be asserted on the fly, and
rows are recorded with "dynamic, self-describing type information",
including nested sets, structs, maps and vectors [5]; the maker contrasts
this with JSONB by claiming it keeps "data type fidelity" [6]. Every row
needs an `_id` [5][11]. Values of unrecognised properties are therefore
stored as typed values rather than dropped. The caveats are the ones in C2
(decimal bound, float literals) and C3 (null fields in nested maps, and
normalisation of keyword keys [16]).

**Settled by**: maker documentation that arbitrary nested data is stored with its types found in [5][6]
**Status**: Met

### C9. Usable from TypeScript without precision loss

The maker's JavaScript page uses the `postgres` package over the wire
protocol and notes that the `pg` package could not, when written, specify
parameter type OIDs, which XTDB needs because it has no declared schema
[14]. It states that int64 values are handled as text by default, and its
example parser converts them to numbers only when `Number.isSafeInteger`
holds and throws otherwise [14]. At commit `6cd79ee` the wire server maps
Arrow decimals to PostgreSQL `numeric` (OID 1700) [15], which `postgres`
delivers as text. Nested values come back through a fallback output format
(`json` by default, or `transit`) [14], and the page does not say how large
integers or decimals inside nested objects survive `json`; Bun is not
mentioned (searched [14], 24 Sep 2026). Top-level integers and decimals can
travel without loss; nested values and timestamps are not documented.

**Settled by**: driver documentation found in [14], with the decimal mapping read at commit [15]; nested-value precision not found (searched [14], 24 Sep 2026)
**Status**: Unknown

### C10. Stored data readable through plain SQL

Interpretation: C10 does not name PostgreSQL, so XTDB's own SQL counts.
XTDB serves a full SQL dialect over the PostgreSQL wire protocol [1], and
PostgreSQL clients connect to it [14][18]; a read-only wire port can be
opened that rejects all DML and DDL [18]. Values convert with `CAST`
between temporal, numeric, interval and text types, and any value can be
cast to `TEXT` (v2.2+) [9]; the wire server reports Arrow types as
PostgreSQL types such as `numeric` [15], and v2.2 exposes role membership
through `pg_roles` and `pg_auth_members` [20]. The stored data itself is
Arrow files in XTDB's object store, read through the XTDB server [6][18].

**Settled by**: casts and SQL access found in [1][9][18], with type mapping read at commit [15]
**Status**: Met

### C11. Sustainable dependency

Releases are active: two stable tags in the twelve months to 24 September
2026 and three `v2.2.0` pre-release tags since July 2026 [23]. The licence,
MPL 2.0, permits commercial use [2]. On the default branch, 2,199 commits
were made in those twelve months by 13 author names, 10 of them human; one
author made 1,189 of the commits [24]. Governance sits with one company:
JUXT writes and supports XTDB and holds the copyright [1], contributions
require a signed CLA [3], and work in progress is planned on the xtdb
organisation's GitHub project board [3]. Interpretation: "open governance" means decisions and code
open to parties other than one company; the record contradicts it, while
the other three conditions are met.

**Settled by**: release history found in [23], contributor statistics in [24], licence text in [2], governance in [1][3]
**Status**: Unmet

### C12. Latency within twice a hand-designed schema

No independent benchmark comparing XTDB 2.x with a relational or
native-graph baseline on single-object fetches and one-to-three-hop
traversals was found (searched "XTDB benchmark PostgreSQL", "XTDB 2
performance comparison", 24 Sep 2026).

**Settled by**: not found (searched, 24 Sep 2026)
**Status**: Unknown

Other notable capabilities the record documents and no criterion requires:

| Capability | What the record says | Source |
|------------|----------------------|--------|
| Bitemporal columns | Every table carries `_system_from`, `_system_to`, `_valid_from` and `_valid_to`, closed-open periods kept automatically; a built-in `WITHOUT OVERLAPS` constraint keeps versions from overlapping; Allen-algebra operators such as `OVERLAPS` and `PRECEDES` | [5] |
| Temporal queries | `FOR VALID_TIME` or `FOR SYSTEM_TIME` with `AS OF`, `FROM ... TO`, `BETWEEN` or `ALL`; `FOR VALID_TIME ONLY FROM X TO Y` (v2.2+) clamps projected periods; valid time defaults to now and system time to the latest indexed transaction | [12] |
| Valid-time writes | `UPDATE` and `DELETE` without a period apply from now to end of time, an acknowledged deviation from SQL:2011, which applies them to all valid time | [11] |
| Transaction provenance | `xt.txs` records each transaction's id, commit flag, error and system time; `BEGIN READ WRITE WITH (METADATA = ...)` (v2.1+) adds arbitrary metadata, such as request or correlation ids, in `user_metadata` | [11] |
| Backfill | A write transaction may set `SYSTEM_TIME`, which must be strictly later than the latest completed transaction | [11] |
| Legal erasure | `ERASE` removes documents for all valid and system time | [11] |
| Repeatable reads | Snapshot tokens and `CLOCK_TIME` fix a query's basis; `SNAPSHOT_TIME` is only an approximation | [7] |
| PostgreSQL change-data capture | A secondary database can mirror a PostgreSQL 17+ database by logical replication, read-only; tables added to the publication after attaching are not snapshotted | [19] |
| Roles | `GRANT` and `REVOKE` of roles (v2.2+), stored as bitemporal rows in `xt.role_membership` | [20] |
| Row-level security (nice to have) | Not published (searched [20] and the documentation tree, 24 Sep 2026) | none |
| Shortest path and ISO GQL (nice to have) | Not published (searched [12] and the XTQL reference, 24 Sep 2026) | none |

Design prior art for truss that the record above documents (inputs for
truss's own design, not a recommendation among candidates): a pair of
closed-open periods per version, system time kept by the database and
valid time by the user, with SQL:2011 query syntax to read them [5][12]; a
transactions table that carries commit status, errors and caller-supplied
metadata, which is the shape of the provenance truss's journal needs [11];
an explicit, monotonic system-time override for backfilling legacy history
[11]; snapshot tokens that make an audited query repeatable [7]; and an
erase operation that removes a value from all history for legal deletion
[11]. The record also shows semantics truss should decide explicitly rather
than inherit: history kept per row version rather than per property value
[5]; `PATCH` treating null as "leave unchanged" [11]; identifier
normalisation that can merge distinct keys [16]; and float parsing of
decimal literals [13]. The PostgreSQL external source [19] is a
build-versus-adopt option in its own right: bitemporal history of
PostgreSQL tables kept outside PostgreSQL, which the ADR can weigh against
an in-database journal.

**Verdict**: No fit. C1, C4, C5, C6 and C11 are Unmet on the public record,
starting with C1: XTDB is its own server and storage engine, reached over
the PostgreSQL wire protocol, not a layer inside PostgreSQL.

## Technology and Operations

| Aspect | What the record says | Source |
|--------|----------------------|--------|
| Hosting model | Self-hosted nodes (Docker images; guides for AWS, Azure and Google Cloud) with a transaction log (Kafka, or local or in-memory for one node) and storage (in memory, local disk, or a remote object store with local caches); no managed offering is described in the documentation source (searched the documentation tree for "managed" and "hosted", 24 Sep 2026) | [18] |
| Integrations | PostgreSQL wire protocol (read-write and optional read-only ports), Flight SQL and ADBC, drivers documented for Java, Kotlin, Clojure, Python, Node.js, Go, Ruby, PHP, C#, Elixir and C; change-data capture from PostgreSQL 17+ and Kafka Connect | [14][18][19] |
| Data handling | Designed for trusted environments behind firewalls; users secure the object store and log; authentication applies to the wire listener only, and the Flight SQL listener has no TLS or authentication, so the maker advises a TLS-terminating proxy | [4][26] |
| Certifications | Not published (searched [4][6] and "XTDB SOC 2", 24 Sep 2026) | none |
| Maturity and cadence | `v2.0.0` June 2025, `v2.1.0` December 2025, `v2.2.0` pre-releases from July 2026 (tag commit dates) | [23] |
| Governance | Single vendor, JUXT Ltd; CLA required for contributions; 10 human commit authors in the twelve months to 24 Sep 2026 | [1][3][24] |
| Security process | Private reports to security@xtdb.com or GitHub security advisories; acknowledgement within 48 hours and resolution or mitigation within 90 days as aims; coordinated disclosure; 2.x and 1.24.x supported | [4] |

## Pricing and Licensing

| Item | Figure | Label | Source |
|------|--------|-------|--------|
| Licence | Mozilla Public License 2.0 or any later version; permits commercial use with file-level copyleft; CLA for contributors | Published | [1][2][3] |
| Software cost | None, as of 24 Sep 2026 | Published | [2] |
| Commercial support or hosting | Not published (searched [1][4] and "XTDB pricing support", 24 Sep 2026; xtdb.com blocked) | Not published | none |

## Competitive Landscape

Cells for the rows researched in this session (XTDB, Datomic, SurrealDB)
come from each system's own record; the Datomic and SurrealDB rows summarise
their sibling profiles. Every other row is left to its sibling profile.

| Candidate | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | Profile |
|-----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|---------|
| XTDB 2.x | Unmet: own server on object storage and a log [18] | Unknown: nine families typed; decimal bound and literal parsing unsettled [9][13] | Unknown: absent vs null undocumented [11][16][17] | Unmet: no schema enforcement; uniqueness only on `_id` [5][14] | Unmet: no user-defined indexes [5][22] | Unmet: `WITH RECURSIVE` unsupported [12][13] | Met: serial single-writer log [7] | Met: schemaless typed storage [5] | Unknown: int64 as text by default; nested values undocumented [14] | Met: SQL over the PostgreSQL wire protocol [1][9] | Unmet: single vendor with CLA [1][3] | Unknown: no benchmark found | this profile |
| Datomic Pro 1.0.7705 | Unmet: own transactor; PostgreSQL holds opaque `bytea` segments [27] | Unmet: no date or time type; millisecond instants [28] | Unmet: no nil; cardinality-many is a set; no maps [28] | Unmet: specs opt-in via `:db/ensure` [28] | Met: AVET, VAET, range predicates [29] | Unmet: Datalog recursion, but no composition with the user's SQL [27][31][34] | Met: serialised transactor; Jepsen Serializable [30] | Unmet: attributes must be installed first [28] | Unknown: community JS client only [32] | Unmet: segments not SQL-readable [27][34] | Unmet: closed source, single vendor [33] | Unknown: no benchmark found | [[component-profile-datomic]] |
| SurrealDB 3.x | Unmet: own server on key-value engines [35] | Unmet: no date or time type; datetimes converted to UTC [37][42] | Met: `NONE` vs `NULL`; arrays; objects [36] | Unknown: rules documented; exact-equality semantics of `UNIQUE` not published [41][45] | Met: B-tree and unique indexes [45] | Unmet: no ANSI SQL [40][43] | Met: snapshot isolation with write-conflict checks [38] | Met: `SCHEMALESS` and `FLEXIBLE` [41] | Met: SDK decodes decimals and 64-bit integers exactly [44] | Unmet: SurrealQL or GQL only over its wire listener [40] | Unmet: BSL 1.1, single vendor [39] | Unknown: no independent benchmark found | [[component-profile-surrealdb]] |
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

- Datomic Pro shares XTDB's immutable, single-writer, time-travelling design
  [7][30]; it diverges by versioning individual facts rather than rows,
  querying in Datalog rather than SQL, and requiring every attribute to be
  declared [28][31].
- SurrealDB 3.x shares the flexible, nested-record model and adds graph
  relations and field-level schema enforcement [41]; it diverges by
  offering no SQL [40] and only engine-dependent record versioning rather
  than bitemporal history [35].
- Apache AGE, Palantir OSv2, Sqlg, PuppyGraph, Gel, Neo4j, Memgraph and
  LadybugDB: shared ground and divergence Not researched here; each named
  sibling profile fills its row.
- UMF-generated per-type PostgreSQL tables and JSONB plus expression
  indexes: Not researched; no sibling profile exists yet. Both keep data in
  the user's PostgreSQL, where XTDB's PostgreSQL external source [19] could
  at most mirror them for history.

## Confidence

| Grade | Means |
|-------|-------|
| **High** | Every design-defining claim is corroborated by the maker's material *and* at least one independent source, and no design-defining capability is Unknown. |
| **Medium** | Design-defining claims rest on the maker alone, or a design-defining capability is Unknown, or the independent coverage is older than two major versions. |
| **Low** | Thin public footprint; claims rest on one source or on none. |

**Grade**: Medium. Every XTDB claim rests on the maker alone: its
documentation source, source code and repository history read directly at
commit `6cd79ee` [1]–[25], which makes the documentary record strong and
version-pinned but uncorroborated; no independent analysis, benchmark or
review of XTDB 2.x was found. C2, C3, C9 and C12 are Unknown, and C3 and C12
are design-defining. The C2 and C3 findings that go beyond the documentation
(float literal parsing, null fields dropped from nested maps, key
normalisation) come from reading code, not from documentation or observed
behaviour [13][16]. The Datomic sibling cells rest partly on search
summaries [28]–[32][34]. Weakest area: null and nested-value fidelity (C3,
C9), where the documentation is silent.

## Open Questions

| # | Question | Design-defining because | Route |
|---|----------|-------------------------|-------|
| 1 | Does XTDB 2.x return an explicit null inside a nested object as null or as absent, and does a map key such as `fooBar` or `foo-bar` survive a round trip unchanged? | It decides whether XTDB could hold truss's property values, or only its history, without silent loss | [[tech-spike]] |
| 2 | What happens to a decimal with more than 64 significant digits, and to a decimal literal written without a cast? | It bounds C2 and truss's exact-decimal claims | [[tech-spike]]; ask maker |
| 3 | Should truss's journal version whole objects in bitemporal periods, as XTDB versions rows, or individual property values? | It fixes the journal's granularity and the cost of per-value provenance | ADR in truss's design activity, informed by [5][11] |
| 4 | Could the PostgreSQL external source keep bitemporal history of truss's own tables well enough to replace an in-database journal? | It is a build-versus-adopt option for history alone, outside C1 | [[tech-spike]] (requires PostgreSQL 17+, logical replication) |
| 5 | Will recursive queries and "gradual schema" constraints arrive in the 2.x line? | They would move C4 and C6, though not C1 | ask maker |

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
a search engine's summary of it was available. XTDB sources 1–22 are files
in [github.com/xtdb/xtdb](https://github.com/xtdb/xtdb) at commit
`6cd79ee2f5df500c3112c309e21a9a9870484d93` (23 Sep 2026), the source of the
docs.xtdb.com pages.

1. [`README.adoc`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/README.adoc), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
2. [`LICENSE` (Mozilla Public License 2.0)](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/LICENSE), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
3. [`CONTRIBUTING.adoc`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/CONTRIBUTING.adoc), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
4. [`SECURITY.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/SECURITY.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
5. [Key concepts, `docs/src/content/docs/concepts/key-concepts.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/concepts/key-concepts.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
6. [What is XTDB?, `docs/src/content/docs/concepts/what-is-xtdb.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/concepts/what-is-xtdb.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
7. [Transactions/Consistency in XTDB, `docs/src/content/docs/about/txs-in-xtdb.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/about/txs-in-xtdb.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
8. [Time in XTDB, `docs/src/content/docs/about/time-in-xtdb.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/about/time-in-xtdb.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
9. [XTDB Data Types, `docs/src/content/docs/reference/main/data-types.md`, and temporal functions, `reference/main/stdlib/temporal.mdx`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/reference/main/data-types.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
10. [SQL Schema, `docs/src/content/docs/reference/main/sql/schema.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/reference/main/sql/schema.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
11. [SQL Transactions, `docs/src/content/docs/reference/main/sql/txs.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/reference/main/sql/txs.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
12. [SQL Queries, `docs/src/content/docs/reference/main/sql/queries.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/reference/main/sql/queries.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
13. [SQL front end, `core/src/main/clojure/xtdb/sql.clj` (lines 259–260 reject recursive CTEs; line 1313 parses float literals as doubles) and grammar `core/src/main/antlr/xtdb/antlr/Sql.g4` (line 103)](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/core/src/main/clojure/xtdb/sql.clj), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
14. [Using XTDB from JavaScript, `docs/src/content/docs/drivers/nodejs.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/drivers/nodejs.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
15. [Wire-protocol types, `core/src/main/kotlin/xtdb/pgwire/PgType.kt` (Arrow decimal to `numeric`, OID 1700)](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/core/src/main/kotlin/xtdb/pgwire/PgType.kt), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
16. [Struct storage, `core/src/main/kotlin/xtdb/arrow/StructVector.kt` (lines 98–110), and key normalisation, `api/src/main/kotlin/xtdb/util/NormalForm.kt` with its test](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/core/src/main/kotlin/xtdb/arrow/StructVector.kt), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
17. [Other functions, `docs/src/content/docs/reference/main/stdlib/other.md`, and XTQL standard library, `reference/main/xtql/stdlib.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/reference/main/stdlib/other.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
18. [Configuration, `docs/src/content/docs/ops/config.md`, with `ops/config/storage.md`, `ops/config/log.md` and the `ops/guides/` pages for AWS, Azure and Google Cloud](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/ops/config.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
19. [External Sources, `docs/src/content/docs/ops/external-sources/overview.md`, and Postgres external source setup, `ops/external-sources/postgres/setup.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/ops/external-sources/postgres/setup.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
20. [Authorization, `docs/src/content/docs/ops/config/authorization.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/ops/config/authorization.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
21. [Databases in XTDB, `docs/src/content/docs/about/dbs-in-xtdb.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/about/dbs-in-xtdb.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
22. [Evaluating index strategies, `dev/doc/evaluating-index-strategies.adoc` (written 29 Oct 2024), and `dev/GLOSSARY.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/dev/doc/evaluating-index-strategies.adoc), maker, JUXT Ltd, published 29 Oct 2024, read at commit, accessed 24 Sep 2026
23. [XTDB release tags (`git ls-remote --tags`; tag commit dates for `v2.0.0`, `v2.1.0`, `v2.2.0-rc0`, `v2.2.0-rc1`, `v2.2.0-beta2`)](https://github.com/xtdb/xtdb/tags), maker, JUXT Ltd, accessed 24 Sep 2026
24. [XTDB commit history on the default branch, 24 Sep 2025 to 24 Sep 2026 (2,199 commits; 13 author names, of which 3 are bots)](https://github.com/xtdb/xtdb/commits/main), maker, JUXT Ltd, counted from a partial clone, accessed 24 Sep 2026
25. [Support CTEs, §7.13 (issue #2087, open, opened 6 Apr 2022)](https://github.com/xtdb/xtdb/issues/2087), maker, JUXT Ltd, found through the GitHub search API, accessed 24 Sep 2026
26. [ADBC reference, `docs/src/content/docs/adbc/reference.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/adbc/reference.md), maker, JUXT Ltd, read at commit, accessed 24 Sep 2026
27. [Datomic Pro 1.0.7705 distribution, `bin/sql/postgres-table.sql` and `config/samples/sql-transactor-template.properties`](https://datomic-pro-downloads.s3.amazonaws.com/1.0.7705/datomic-pro-1.0.7705.zip), maker (Datomic), Nu North America, Inc., published 10 Jul 2026, accessed 24 Sep 2026 (read by HTTP range requests)
28. [Datomic Schema Data Reference](https://docs.datomic.com/schema/schema-reference.html), maker (Datomic), accessed 24 Sep 2026 (search summary)
29. [Datomic Indexes](https://docs.datomic.com/indexes/index-model.html) and [Executing Queries](https://docs.datomic.com/query/query-executing.html), maker (Datomic), accessed 24 Sep 2026 (search summary)
30. [Jepsen: Datomic Pro 1.0.7075](https://jepsen.io/analyses/datomic-pro-1.0.7075), independent, Jepsen (Kyle Kingsbury), published 15 May 2024, accessed 24 Sep 2026 (search summary)
31. [Datomic Query Reference](https://docs.datomic.com/query/query-data-reference.html), maker (Datomic), accessed 24 Sep 2026 (search summary)
32. [Datomic Peer Language Support](https://docs.datomic.com/operation/languages.html) (search summary) and [datomic-client-js](https://github.com/csm/datomic-client-js) (community, Casey Marshall, read at commit `59c03a7`, 25 Feb 2026), accessed 24 Sep 2026
33. [Maven Central, `com.datomic/peer` POM 1.0.7705](https://repo1.maven.org/maven2/com/datomic/peer/1.0.7705/peer-1.0.7705.pom) and the [Datomic GitHub organisation](https://github.com/Datomic), maker (Datomic), Nu North America, Inc., accessed 24 Sep 2026
34. [Datomic Analytics Support](https://docs.datomic.com/analytics/analytics-concepts.html) and [JDBC](https://docs.datomic.com/analytics/analytics-jdbc.html), maker (Datomic), accessed 24 Sep 2026 (search summary)
35. [SurrealDB documentation source, `learn/data-models/architecture.mdx`, and `SELECT` reference (`VERSION` clause)](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/learn/data-models/architecture.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7` (23 Sep 2026), accessed 24 Sep 2026
36. [SurrealDB documentation source, `data-types/none-and-null.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/data-types/none-and-null.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
37. [SurrealDB documentation source, `build/migrating/from-other-databases/from-postgresql.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/build/migrating/from-other-databases/from-postgresql.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
38. [SurrealDB documentation source, `learn/querying/concepts-and-guides/transactions.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/learn/querying/concepts-and-guides/transactions.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
39. [SurrealDB `LICENSE` (Business Source License 1.1)](https://raw.githubusercontent.com/surrealdb/surrealdb/main/LICENSE), maker (SurrealDB), SurrealDB Ltd, accessed 24 Sep 2026
40. [SurrealDB documentation source, `reference/rest-api/postgres-protocol.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/rest-api/postgres-protocol.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
41. [SurrealDB documentation source, `statements/define/table.mdx` and `statements/define/field.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/statements/define/table.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
42. [SurrealDB documentation source, `data-types/numbers.mdx` and `data-types/datetimes.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/data-types/numbers.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
43. [SurrealDB documentation source, `language-primitives/idioms.mdx` (recursive paths)](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/idioms.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
44. [SurrealDB JavaScript SDK documentation source, `reference/javascript/api/types/index.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/javascript/api/types/index.mdx) and [SDK source, `packages/sqon/src/codec/cbor/codec.ts`](https://github.com/surrealdb/surrealdb.js/blob/69129d7d3109c22f55f94954510c392a3e1ebc8e/packages/sqon/src/codec/cbor/codec.ts), maker (SurrealDB), SurrealDB Ltd, read at commits `47139e7` and `69129d7` (10 Sep 2026), accessed 24 Sep 2026
45. [SurrealDB documentation source, `statements/define/indexes.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/statements/define/indexes.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026

**Searched**: Network access: docs.xtdb.com and xtdb.com answered 403 at
this session's proxy on 24 Sep 2026, as did docs.datomic.com, jepsen.io and
db-engines.com; github.com (git clones and the GitHub search API),
raw.githubusercontent.com and the npm registry were readable. The XTDB
documentation tree at commit `6cd79ee` was searched for "extension" (no
in-PostgreSQL deployment, hence C1), "absent", "null" and "normali[sz]"
(no documented null rule, hence C3 Unknown), "index", "CREATE INDEX",
"bloom" and "secondary index" (no user-defined indexes, hence C5),
"recursive" and "rule" (hence C6; issue #2087 found through the GitHub
search API with "recursive CTE WITH RECURSIVE support graph traversal"),
"precision", "nanosecond" and "microsecond" (no statement beyond precision
64, hence C2's Not published clause), "managed", "hosted", "TLS", "SSL"
and "encrypt" (hence the hosting and data-handling cells), "row" in the
authorization page (no row-level security, hence the nice-to-have row),
and "Bun" in the JavaScript page (not mentioned). Web searches (24 Sep
2026): "XTDB 2.0 review bitemporal SQL database independent article 2025"
(only maker pages and a directory listing, hence Adoption Not published and
no independent corroboration); "DB-Engines ranking SurrealDB Datomic XTDB"
(no scores; pages blocked); "XTDB Jepsen" and "XTDB 2 consistency
analysis" (nothing, hence C7 rests on the maker); "XTDB benchmark
PostgreSQL" and "XTDB 2 performance comparison" (nothing comparable, hence
C12 Unknown); "XTDB SOC 2" (nothing, hence Certifications Not published);
"XTDB pricing support" (nothing readable, hence the commercial support row).
Apache AGE, Palantir OSv2, Sqlg, PuppyGraph, Gel, Neo4j, Memgraph,
LadybugDB, UMF-generated per-type tables and JSONB plus expression indexes
were not searched in this profile, hence Not researched.

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
