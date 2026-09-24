---
ddx:
  id: truss.component-profile-datomic
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

# Component Profile: Datomic

Desk research on Datomic Pro as a candidate for the graph storage and query
layer truss would otherwise build, measured against the capabilities truss
needs from that role, and read for the fact-level identity, history and
schema-as-data ideas truss could borrow. This profile makes no choice among
candidates; the build-versus-adopt decision belongs to an ADR that cites the
profiles, and what reading cannot settle is routed below.

## Scope

- Component: Datomic Pro, release 1.0.7705 (published 10 July 2026), with
  its SQL storage protocol pointed at PostgreSQL; Datomic Cloud (the AWS
  edition) and Datomic Local (the in-process development library) are noted
  where they differ
- Kind: Product (free binaries from a single maker; source not published)
- Would fill: the graph storage and query layer for connected, evolving,
  UMF-typed data: fact-level storage of property values and edges, their
  history and provenance, schema-constrained writes, and traversal queries
- Feeds: the owner's build-versus-adopt decision for truss; no ADR or
  [[tech-spike]] exists yet
- Incumbent: *None*. truss has no implementation; teams use hand-built
  per-type tables, JSONB documents or a separate graph database
  ([[truss.product-vision]] §Target Market). truss has no
  [[current-state-inventory]].
- Researched: 24 September 2026
- Excluded: hands-on testing of any kind; Datomic Cloud's AWS topology,
  Ions and AWS running costs; Datomic Analytics beyond what bears on C6 and
  C10; client libraries other than the JVM peer and JavaScript. The maker's
  documentation site (docs.datomic.com), its blog (blog.datomic.com),
  www.datomic.com and jepsen.io were blocked by this session's network
  proxy; claims from those pages rest on search-engine summaries and are
  labelled as such in Sources. The maker's own distribution archive and
  Maven Central were readable and carry the design-defining C1 evidence.

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
hand-designed schema's latency. On the public record Datomic Pro meets the
indexing and concurrency capabilities, is unknown on a TypeScript client and
on latency, and fails the other eight, starting with the first: it runs its
own transactor and JVM peers and uses PostgreSQL only as a key-value table
of opaque binary segments, so the verdict is No fit, while its datom, index,
transaction-as-entity and schema-as-data models remain the closest prior art
for truss's catalog and journal.

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

Datomic is a transactional database that records information as immutable
facts, called datoms, each carrying an entity id, an attribute, a value, the
transaction that asserted or retracted it and an added flag, and it answers
queries in Datalog [15][16]. Writes go through a transactor process, which
runs transaction functions against the preceding database value [14];
applications use the JVM peer library [5] or a client API [19], and the
transactor and peers share a storage service [4][7]. It is
made by Nu North America, Inc. (Nubank), which took over its original maker
Cognitect [3][5][29]. Datomic Free and Datomic Pro were first released
publicly as version 0.8.3335 [2]; since release 1.0.6726 the peer and
transactor binaries are licensed under the Apache License 2.0 and need no
licence key [2], while the source code is not published [5][6]. The maker
positions it for keeping every past state queryable: databases can be read
as of a past transaction, since a transaction, or as a full history of
assertions and retractions [11], and transactions are themselves entities
that can carry provenance [12].

- Category and purpose: immutable fact database with Datalog queries,
  indexes over datoms, and time-filtered database values [11][15][16]
- Maker or governing body: Nu North America, Inc. (Nubank); the peer POM
  lists ten developers, all with Nubank addresses [5]; a Nubank post
  says Stuart Halloway and Rich Hickey continue to set the roadmap after the
  Cognitect acquisition (search summary) [29]
- Adoption, from an independent source: Not published (searched DB-Engines
  and "companies using Datomic", 24 Sep 2026); the maker says Datomic is
  developed at Nubank, where it is a critical piece of infrastructure
  (search summary) [22]
- Release cadence and support window: five peer releases on Maven Central
  between 23 October 2025 and 10 July 2026 (1.0.7469, 1.0.7491, 1.0.7556,
  1.0.7622, 1.0.7705) [5]; the change log asks users to take the
  highest-numbered bugfix release in a family [2]; a support window is Not
  published (searched the change log [2] and the free-licensing post [22],
  24 Sep 2026); 1.0.7705 requires Java 17 or later [2]
- Licence: binaries under the Apache License 2.0 [2][3][5]; no source
  repository for the database is published (the POM's `scm` element points
  at the product website, and the maker's GitHub organisation holds samples
  and libraries only) [5][6]
- Built-for use cases: history and audit through as-of, since and history
  database values [11]; attaching provenance (purpose, application, user,
  source of the data) to transaction entities [12]; SQL analytics through a
  Trino connector [18]

## Capability Alignment

### C1. Runs inside the user's own PostgreSQL

Interpretation: Datomic is a separate database system; the question is what
its SQL storage option puts inside PostgreSQL. The Datomic Pro 1.0.7705
distribution's PostgreSQL script creates a single table, `datomic_kvs`, with
columns `id text NOT NULL` (primary key), `rev integer`, `map text` and
`val bytea` [1]. The SQL transactor template connects to that database over
JDBC (`protocol=sql`, `sql-url=jdbc:postgresql://localhost:5432/datomic`),
and the distribution bundles the PostgreSQL JDBC driver 42.7.11 [4]. The
maker's storage page describes storage services as a key-value store of
index segments written as binary blobs (search summary) [7]. PostgreSQL
therefore holds opaque, keyed segments, not datoms as rows: it cannot query,
index or constrain Datomic's facts, and the transactor and JVM peers (Java 17
or later for 1.0.7705 [2]) still have to run beside it [4]. A supported
PostgreSQL version range for storage and any managed-provider listing are
Not published (searched the change log [2], the transactor template [4] and
the storage page summary [7], 24 Sep 2026). Datomic Cloud runs on AWS
storage, recording transactions with compare-and-swap against DynamoDB
(search summary) [28]; Datomic Local is a no-cost development and test
library (search summary) [24]. Neither runs inside PostgreSQL.

**Settled by**: an in-PostgreSQL runtime or extension not found; the storage table definition found in [1], the JDBC transactor configuration in [4]; version matrix and managed-provider listing not found (searched [2][4][7], 24 Sep 2026)
**Status**: Unmet

### C2. Stores UMF's nine scalar families exactly

The value types are `bigdec`, `bigint`, `boolean`, `bytes`, `double`,
`float`, `instant`, `keyword`, `long`, `ref`, `string`, `symbol`, `tuple`,
`uuid` and `uri` (search summary) [8]. `bigint` is arbitrary-precision up to
a bit length of 8192 and `bigdec` is an exact `java.math.BigDecimal` limited
to 1024 digits (search summary) [8]; release 1.0.6222 added changing the
scale of a BigDecimal attribute in a transaction [2]. The type list has no
date-only and no time-of-day type, and instants are stored as milliseconds
since the epoch (search summary) [8], so a UMF date or time value has no
native home and a timestamp loses sub-millisecond precision and its original
offset. `:db.type/bytes` maps to Java byte arrays, which lack value
semantics; the maker has deprecated it, and bytes attributes cannot be
unique or used as lookup refs (search summary) [8][10]; the change log
records that its limitations were documented and enforced in 0.9.5206 [2].

**Settled by**: type-system documentation found in [8][10] (search summaries) with change-log corroboration in [2]; date, time and sub-millisecond timestamp storage contradicted by the type list [8]
**Status**: Unmet

### C3. Absent versus null; ordered lists and maps

Independent coverage reports that Datomic accepts no nil attribute values:
an entity either has a datom for an attribute or it does not, and a value is
removed by retracting it (Matthew Boston, undated; search summary) [26]. The
maker's record found in this session does not state the rule directly, but
it is consistent with the datom model, in which a fact is an assertion or a
retraction of a value [15]. A `:db.cardinality/many` attribute returns a set
of values (search summary) [8], so order and duplicates are not kept; tuples
hold two to eight scalar values (search summary) [8]; the type list has no
map type [8]. An explicit null, an ordered list with duplicates, and a
string-keyed map therefore have no direct representation as one property
value.

**Settled by**: null handling found in independent coverage [26] (search summary, descriptive only); list and map handling found in [8] (search summary), which contradicts the capability
**Status**: Unmet

### C4. Declared rules enforced by the database

Interpretation: "graph writes" are Datomic transactions (list and map forms,
upserts, retractions). Each attribute declares a value type and cardinality
that transactions must satisfy [8], and `:db/unique` (value or identity)
makes the database reject or unify duplicate values [9]; bytes attributes
cannot be unique [8]. Attribute predicates are enforced on assertions from
the transaction after they are asserted and must be on the classpath of the
transacting process (search summary) [8]; since 1.0.6242 they apply to
assertions only [2]. Required attributes are declared in entity specs
(`:db.entity/attrs`), but a spec is enforced only when a transaction asks for it with `:db/ensure`, and
the page states, in the search summary, that enforcement is never
automatic or retroactive [8]. Reference attributes declare no target entity type in
the record found (Not published; searched [8][9], 24 Sep 2026), so allowed
edge endpoints are not a declarable rule on that record. Whether unique
string values compare by exact code units is Not published (searched [8][9],
24 Sep 2026). A write that omits `:db/ensure` bypasses required-attribute
rules, which contradicts the "writes honouring those rules" half of the
row.

**Settled by**: type, uniqueness and predicate enforcement found in [2][8][9]; required-attribute enforcement found to be opt-in per transaction [8]; endpoint rules and exact-equality semantics not found (searched [8][9], 24 Sep 2026)
**Status**: Unmet

### C5. Property indexes used by queries

Interpretation: Datalog queries stand in for Cypher. The EAVT and AEVT
indexes contain all datoms; AVET contains datoms of attributes declared with
`:db/index true` or `:db/unique` in Datomic Pro, while Datomic Cloud keeps
every attribute in AVET; VAET indexes reference attributes for reverse
navigation (search summary) [15]. The comparison predicates `=`, `!=`, `<`,
`<=`, `>` and `>=` use AVET directly (search summary) [17], and the index
range API returns an attribute's datoms between bounds [15]; the change log
records range requests on `Database.index` since 0.8.3372 and reverse index
iteration (`rseek-datoms`) in 1.0.7622 [2]. Datomic evaluates `:where`
clauses in the order written, apart from a few guaranteed reorderings such as
pushing predicates, and `query-stats` reports clause selectivity so authors
can reorder (search summary) [17]; the change log shows the in-order rule
dates from 0.8.3372 [2]. Index use is therefore documented, but the query
author, not a cost-based planner, chooses the join order. No independent
report of index use was found (searched "Datomic query performance AVET",
24 Sep 2026).

**Settled by**: indexing documentation found in [15][17] (search summaries) with change-log corroboration in [2]; independent reports not found (searched, 24 Sep 2026)
**Status**: Met

### C6. Traversal, writes and composition with SQL

Interpretation: Datalog stands in for openCypher, and "composes with ordinary
SQL" means joining with, and appearing inside, SQL statements in the user's
PostgreSQL. Datomic Datalog supports rules with recursion (so variable-length
traversal is written as a recursive rule), negation, aggregates and pull
expressions in `:find`, and query inputs declared in `:in` (search summary)
[16]; pull patterns navigate forward and reverse references recursively with
limits and defaults [16]. Writes assert and retract values, upsert through
`:db.unique/identity` [9], compare-and-swap one cardinality-one attribute
with `:db/cas` [14], and retract all values of an attribute with
`[:db/retract e a]` since 0.9.6045 [2]. SQL access exists only through
Analytics Support, a Trino connector whose metaschema files map attributes
to SQL tables; its JDBC connection is read-only and not low latency (search
summary) [18], and the distribution bundles Presto server 348 for it [2][4].
Because the PostgreSQL storage holds opaque segments [1], no SQL statement in
the user's PostgreSQL can join Datomic data with relational tables.
Shortest-path queries are Not published (searched [16], 24 Sep 2026).

**Settled by**: Datalog coverage found in [16] and write forms in [2][9][14]; composition with the user's SQL contradicted by the storage format [1] and the read-only analytics path [18]
**Status**: Unmet

### C7. Transactional writes under concurrency

Interpretation: Datomic's serialised transactor stands in for PostgreSQL's
isolation levels. Every write is an ACID transaction [28], defined as the
addition of a set of datoms to the preceding database value rather than as
a batch of smaller updates [13], and transaction functions run on the
transactor against that value [14] (all three search summaries). `:db/cas` gives optimistic
single-attribute updates [14], and the change log records it rejecting
cardinality-many attributes [2]; upsert unifies a temporary id with an
existing entity through a unique identity [9], and the change log records
improved intra-transaction unique-identity handling [2]. Jepsen's 2024
analysis of Datomic Pro 1.0.7075 found every history Serializable, sessions
bound to one peer Strong Session Serializable, and write transactions with
`d/sync` reads Strong Serializable; it also found that operations inside one
transaction behave as if concurrent rather than in order, so invariants kept
by separate transaction functions can break when combined in one
transaction, which Nubank intends to keep and Jepsen judged consistent with
the documentation (independent, Jepsen, 15 May 2024; search summary) [25].

**Settled by**: concurrency and merge semantics found in [9][13][14] (search summaries), corroborated by the change log [2] and independent analysis [25] (search summary)
**Status**: Met

### C8. Retains data that matches no schema definition

Attributes are entities that must be installed with a transaction before
data can use them (search summary) [8]; there is no schemaless attribute or
catch-all map type in the type list [8]. A property with no installed
attribute therefore cannot be stored as itself. Because schema is data, a
client could install a new attribute for each unrecognised property before
writing it, but the value would then match a definition the client
generated, and its type would have to fit the type list in C2.

**Settled by**: maker documentation found in [8] (search summary), which contradicts the capability
**Status**: Unmet

### C9. Usable from TypeScript without precision loss

The maker's peer APIs are Java and Clojure; non-JVM languages are directed
to the REST service, in which a peer runs as an HTTP server (search summary)
[19], and the 1.0.7705 distribution still ships a `bin/rest` launcher [4].
No maker JavaScript or TypeScript client was found (searched [19] and
"Datomic client JavaScript TypeScript", 24 Sep 2026). The community package
`datomic-client-js` (npm 0.1.13; Apache-2.0) targets Peer Server and Datomic
Cloud, describes itself as "Work in progress!", and decodes responses with
transit-js 0.8.861 [27]; its change log fixed handling of `goog.math.Long`
values in 0.1.8, and at commit `59c03a7` its `BigDec` wrapper accepts only
strings matching `^[0-9]+(\.[0-9]+)?$`, which excludes negative decimals
[27]. No published guarantee covers 64-bit integers, big decimals or
instants end to end.

**Settled by**: maker client documentation found in [19] (search summary) and [4]; a TypeScript path without precision loss not found; community client read at commit [27]
**Status**: Unknown

### C10. Stored data readable through plain SQL

The rows Datomic writes to PostgreSQL are `id`, `rev`, `map` and a `bytea`
segment [1][7], so other tools reading PostgreSQL see keys and binary blobs,
not property values, and no cast turns a segment into SQL types. SQL access
to Datomic data is through the Trino connector, configured by metaschema
files that name the SQL tables and columns, over a read-only JDBC connection
(search summary) [18]. That is a separate server reading through Datomic,
not plain SQL over the stored data.

**Settled by**: casts or functions from stored values to SQL types not found; storage format found in [1], analytics path in [18] (search summary)
**Status**: Unmet

### C11. Sustainable dependency

Releases are active: five peer releases in the twelve months to 24
September 2026 [5]. The binaries are Apache-2.0 and free of licence fees,
which permits commercial use [3][22]; Datomic Cloud has carried no licence
fee since June 2023 (search summary) [23]. Governance is a single company:
the maker is Nubank [3][5], the roadmap is set by its Datomic leads (search
summary) [29], the source is not published [5][6], and no public issue
tracker or contribution process for the database was found (searched [6],
24 Sep 2026). The POM lists ten developers [5]. Interpretation: "open
governance" means decisions and code open to parties other than one
company; the record contradicts it.

**Settled by**: release history found in [5], licence text in [3], governance and source availability in [5][6][29]
**Status**: Unmet

### C12. Latency within twice a hand-designed schema

No independent benchmark comparing Datomic with a relational or
native-graph baseline on single-object fetches and one-to-three-hop
traversals was found (searched "Datomic benchmark PostgreSQL", "Datomic
performance comparison graph traversal", 24 Sep 2026).

**Settled by**: not found (searched, 24 Sep 2026)
**Status**: Unknown

Other notable capabilities the record documents and no criterion requires:

| Capability | What the record says | Source |
|------------|----------------------|--------|
| Time-filtered database values | `as-of` ignores transactions after a point, `since` keeps only later ones (and may miss identifying facts asserted earlier), `history` holds every assertion and retraction (search summary) | [11] |
| Reified transactions and provenance | Transactions are entities; extra attributes on a transaction can record purpose, application, provenance of the data and the user, and every datom leads to its transaction (search summary) | [12] |
| Backdated imports | Since 0.8.3435 a transaction may set `:db/txInstant` explicitly to backdate imported data; the transactor keeps `:db/txInstant` monotonic | [2] |
| Opting out of history | `:db/noHistory` stops keeping past values of an attribute; excision cannot guarantee full removal of such datoms (search summary) | [20] |
| Excision | Permanent removal of datoms, including from history; 1.0.7469 fixed excisions that were not fully applied to as-of and history values and added a repair tool | [2][20] |
| Schema evolution | Schema changes are transactions and visible immediately; the maker's best practice is to plan for accretion (search summary) | [12][20] |
| Composite keys | Composite tuples of two to eight scalars; 1.0.7705 can permanently discontinue a composite tuple's maintenance | [2][8] |
| Read-only access | 1.0.7622 added read-only connections to storage and backups | [2] |
| Row-level security (nice to have) | Not published (searched [7][18], 24 Sep 2026) | none |
| ISO GQL (nice to have) | None found; the query language is Datalog (searched [16], 24 Sep 2026) | none |

Design prior art for truss that the record above documents (inputs for
truss's own design, not a recommendation among candidates): the datom as the
unit of storage, identified by entity, attribute, value and transaction,
with an added/retracted flag [15]; four index orders (EAVT, AEVT, AVET for
declared attributes, VAET for references), which [[truss.vision-input]]
already names as the model for covering indexes on truss's property table
[15]; the transaction as an entity carrying provenance attributes [12] and
an explicit, monotonic transaction instant that imports can backdate [2];
schema as data, with attributes installed and evolved by ordinary
transactions [8][20]; and time-filtered reads (`as-of`, `since`,
`history`) [11]. The record also shows three gaps truss's concerns forbid
repeating: no explicit null [26], millisecond instants with no date or time
types [8], and byte arrays without value semantics [10]; and two semantics
truss should decide explicitly: rule enforcement that is opt-in per
transaction [8], and operations inside one transaction applied as if
concurrent [25].

**Verdict**: No fit. C1, C2, C3, C4, C6, C8, C10 and C11 are Unmet on the
public record, starting with C1: Datomic runs outside PostgreSQL and stores
only opaque segments there.

## Technology and Operations

| Aspect | What the record says | Source |
|--------|----------------------|--------|
| Hosting model | Self-hosted transactor and JVM peers on a storage service: SQL databases (scripts for PostgreSQL, MySQL and Oracle ship in the distribution), DynamoDB, Cassandra and others; Datomic Cloud runs on AWS; Datomic Local runs in-process for development and CI (search summaries for Cloud and Local) | [1][4][24][28] |
| Integrations | Java and Clojure peer APIs; a Client API; a REST server launcher; Trino/Presto SQL analytics over read-only JDBC; JavaScript only through a community client | [4][18][19][27] |
| Data handling | Peer-to-transactor channel encrypted by default (`encrypt-channel=true`); excision for permanent removal; encryption at rest is left to the storage service, and no maker statement on it was found (searched [4][7], 24 Sep 2026) | [4][20] |
| Certifications | Not published (searched [21][22] and "Datomic SOC 2", 24 Sep 2026) | none |
| Maturity and cadence | First public release 0.8.3335; five peer releases from October 2025 to July 2026; Java 17 or later from 1.0.7705 | [2][5] |
| Governance | Single vendor, Nubank; source not published; ten Nubank developers named in the POM | [3][5][6][29] |
| Security process | A disclosure policy is Not published (searched "Datomic security vulnerability reporting", 24 Sep 2026); the change log records dependency upgrades for published CVEs, such as the REST server's bootstrap.js for CVE-2016-10735 in 1.0.7180 | [2] |

## Pricing and Licensing

| Item | Figure | Label | Source |
|------|--------|-------|--------|
| Licence | Apache License 2.0 for the peer and transactor binaries since 1.0.6726; source not published | Published | [2][3][5] |
| Datomic Pro licence fee | None, as of 24 Sep 2026 (free of licensing fees since April 2023; search summary) | Published | [22] |
| Datomic Cloud licence fee | None; the user pays for the AWS resources it runs on, as of 24 Sep 2026 (search summaries) | Published | [21][23] |
| Paid support | Not published (searched [21][22], 24 Sep 2026) | Not published | none |

## Competitive Landscape

Cells for the rows researched in this session (Datomic, XTDB, SurrealDB)
come from each system's own record; the XTDB and SurrealDB rows summarise
their sibling profiles. Every other row is left to its sibling profile.

| Candidate | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | Profile |
|-----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|---------|
| Datomic Pro 1.0.7705 | Unmet: own transactor; PostgreSQL holds opaque `bytea` segments [1][4] | Unmet: no date or time type; millisecond instants [8] | Unmet: no nil; cardinality-many is a set; no maps [8][26] | Unmet: specs opt-in via `:db/ensure` [8] | Met: AVET, VAET, range predicates [15][17] | Unmet: Datalog recursion, but no composition with the user's SQL [1][16][18] | Met: serialised transactor; Jepsen Serializable [13][25] | Unmet: attributes must be installed first [8] | Unknown: community JS client only [19][27] | Unmet: segments not SQL-readable [1][18] | Unmet: closed source, single vendor [5][6] | Unknown: no benchmark found | this profile |
| XTDB 2.x | Unmet: own server on object storage and a log [31] | Unknown: nine families typed; decimals capped at precision 64 [35] | Unknown: absent vs null undocumented [35] | Unmet: no schema enforcement; uniqueness only on `_id` [30][34] | Unmet: no user-defined indexes [30] | Unmet: `WITH RECURSIVE` unsupported [33] | Met: serial single-writer log [32] | Met: schemaless dynamic tables [30] | Unknown: int64 as text by default; nested values undocumented [34] | Met: SQL over the PostgreSQL wire protocol [31] | Unmet: single vendor with CLA [31][36] | Unknown: no benchmark found | [[component-profile-xtdb]] |
| SurrealDB 3.x | Unmet: own server on key-value engines [37] | Unmet: no date or time type; datetimes converted to UTC [39][44] | Met: `NONE` vs `NULL`; arrays; objects [38] | Unknown: rules documented; exact-equality semantics of `UNIQUE` not published [43][47] | Met: B-tree and unique indexes [47] | Unmet: no ANSI SQL [42][45] | Met: snapshot isolation with write-conflict checks [40] | Met: `SCHEMALESS` and `FLEXIBLE` [43] | Met: SDK decodes decimals and 64-bit integers exactly [46] | Unmet: SurrealQL or GQL only over its wire listener [42] | Unmet: BSL 1.1, single vendor [41] | Unknown: no independent benchmark found | [[component-profile-surrealdb]] |
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

- XTDB 2.x shares Datomic's immutable, single-writer, time-travelling design
  (its documentation credits Datomic's epochal time model [32]); it diverges
  by speaking SQL over the PostgreSQL wire protocol and versioning whole rows
  bitemporally rather than individual facts [31][32].
- SurrealDB 3.x shares the flexible typed-record goal and adds graph
  relations as first-class edges; it diverges by distinguishing `NONE` from
  `NULL` [38] and enforcing field types on write, at the cost of an
  embedded key-value storage engine and a source-available licence
  [37][41].
- Apache AGE, Palantir OSv2, Sqlg, PuppyGraph, Gel, Neo4j, Memgraph and
  LadybugDB: shared ground and divergence Not researched here; each named
  sibling profile fills its row.
- UMF-generated per-type PostgreSQL tables and JSONB plus expression
  indexes: Not researched; no sibling profile exists yet. Both keep data in
  the user's PostgreSQL, which is exactly where Datomic diverges (C1).

## Confidence

| Grade | Means |
|-------|-------|
| **High** | Every design-defining claim is corroborated by the maker's material *and* at least one independent source, and no design-defining capability is Unknown. |
| **Medium** | Design-defining claims rest on the maker alone, or a design-defining capability is Unknown, or the independent coverage is older than two major versions. |
| **Low** | Thin public footprint; claims rest on one source or on none. |

**Grade**: Medium. The deciding claim, C1, rests on the maker's own
distribution files (the `datomic_kvs` definition and the JDBC transactor
template) read directly [1][4], with the storage page's summary agreeing
[7]; the licence, release history and governance claims rest on the
distribution, Maven Central and the maker's GitHub listing [2][3][5][6]. The
statuses for C2, C3, C4, C5, C7, C8 and C10 rest mainly on search-engine
summaries of maker pages, because docs.datomic.com was blocked; C2, C4, C5
and C7 are partly corroborated by the change log [2]. The only independent
sources are Jepsen's 2024 analysis [25], read as a summary, which tested
1.0.7075, an earlier release of the same 1.0 line, and an undated blog post
[26] used descriptively.
C9 and C12 are Unknown, and C12 is design-defining. Weakest area: C3 and C8,
whose rules (no nil values; attributes installed before use) were not read
on a maker page directly.

## Open Questions

| # | Question | Design-defining because | Route |
|---|----------|-------------------------|-------|
| 1 | Can truss reproduce Datomic's datom model and its EAVT, AEVT, AVET and VAET orders as rows and covering indexes in PostgreSQL within twice a hand-designed schema's latency? | It decides whether truss's per-value storage borrows Datomic's layout; [[truss.competitive-analysis]] already names the benchmark as follow-up research | [[tech-spike]] (the benchmark named in [[truss.competitive-analysis]]) |
| 2 | Should truss apply the operations of one mutation in order, or as if concurrent as Datomic does, and how should composed transaction functions see each other's effects? | It fixes the semantics of truss's mutation engine and journal | ADR in truss's design activity, informed by [25] |
| 3 | Should required-property and endpoint rules be enforced on every write, or opt-in per transaction as Datomic's entity specs are? | It decides what truss's enforcement report can claim as "engine enforced" | ADR in truss's design activity, informed by [8] |
| 4 | Does any maker-supported path exist from TypeScript to Datomic that preserves 64-bit integers, big decimals and instants? | Only if Datomic were adopted; it would bound C9 | ask maker |
| 5 | Which PostgreSQL versions and managed services does the maker support for SQL storage? | Only if Datomic were adopted with PostgreSQL storage; C1 stays Unmet either way | ask maker |

## Sources

Classes:

- **maker**: the component's maker or governing body
- **vendor**: a company that sells hosting or support for the component or a rival
- **independent**: no commercial interest in the component; a named author or organisation and a date
- **community**: a project or forum around the component

A source with no named author or organisation and no date supports a
descriptive claim only, never a design-defining one. "Search summary" means
the page was blocked by this session's proxy and only a search engine's
summary of it was available; "read at commit" means a git clone at the named
commit was read and nothing was run.

1. [Datomic Pro 1.0.7705 distribution, `bin/sql/postgres-table.sql` and `bin/sql/postgres-db.sql`](https://datomic-pro-downloads.s3.amazonaws.com/1.0.7705/datomic-pro-1.0.7705.zip), maker, Nu North America, Inc., published 10 Jul 2026 (archive Last-Modified), accessed 24 Sep 2026 (files read from the archive by HTTP range requests; nothing was run)
2. [Datomic Pro 1.0.7705 distribution, `CHANGES.md` (change log for all releases)](https://datomic-pro-downloads.s3.amazonaws.com/1.0.7705/datomic-pro-1.0.7705.zip), maker, Nu North America, Inc., published 10 Jul 2026, accessed 24 Sep 2026
3. [Datomic Pro 1.0.7705 distribution, `LICENSE` (Apache License 2.0) and `COPYRIGHT`](https://datomic-pro-downloads.s3.amazonaws.com/1.0.7705/datomic-pro-1.0.7705.zip), maker, Nu North America, Inc., published 10 Jul 2026, accessed 24 Sep 2026
4. [Datomic Pro 1.0.7705 distribution, `config/samples/sql-transactor-template.properties` and the `config/samples/`, `bin/` and `lib/` listings (transactor templates for SQL, DynamoDB, Cassandra, Infinispan and dev storage; `transactor`, `rest`, `postgresql-42.7.11.jar`, bundled Presto server)](https://datomic-pro-downloads.s3.amazonaws.com/1.0.7705/datomic-pro-1.0.7705.zip), maker, Nu North America, Inc., published 10 Jul 2026, accessed 24 Sep 2026
5. [Maven Central, `com.datomic/peer` POM 1.0.7705 and `maven-metadata.xml`](https://repo1.maven.org/maven2/com/datomic/peer/), maker, Nu North America, Inc., release dates from each POM's Last-Modified header (1.0.7469 23 Oct 2025; 1.0.7491 26 Jan 2026; 1.0.7556 13 Mar 2026; 1.0.7622 28 Apr 2026; 1.0.7705 10 Jul 2026), accessed 24 Sep 2026
6. [Datomic organisation on GitHub (18 public repositories: samples, Fressian, codeq, Simulant and tutorials; no database source)](https://github.com/Datomic), maker, Nu North America, Inc., listed through the GitHub search API, accessed 24 Sep 2026
7. [Setting up Storage Services](https://docs.datomic.com/operation/storage.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
8. [Schema Data Reference](https://docs.datomic.com/schema/schema-reference.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
9. [Identity and Uniqueness](https://docs.datomic.com/schema/identity.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
10. [Querying on Byte Array Attributes (tech note)](https://docs.datomic.com/tech-notes/querying-byte-array.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
11. [Database Filters](https://docs.datomic.com/reference/filters.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
12. [Best Practices](https://docs.datomic.com/reference/best.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
13. [Transaction Model](https://docs.datomic.com/transactions/model.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
14. [Transaction Functions](https://docs.datomic.com/transactions/transaction-functions.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
15. [Indexes](https://docs.datomic.com/indexes/index-model.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
16. [Query Reference](https://docs.datomic.com/query/query-data-reference.html) and [Pull](https://docs.datomic.com/query/query-pull.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
17. [Executing Queries](https://docs.datomic.com/query/query-executing.html) and [Query Stats](https://docs.datomic.com/reference/query-stats.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
18. [Analytics Support](https://docs.datomic.com/analytics/analytics-concepts.html), [Metaschema Reference](https://docs.datomic.com/analytics/analytics-metaschema.html) and [JDBC](https://docs.datomic.com/analytics/analytics-jdbc.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
19. [Peer Language Support](https://docs.datomic.com/operation/languages.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
20. [Excision](https://docs.datomic.com/operation/excision.html) and [Changing Schema](https://docs.datomic.com/schema/schema-change.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
21. [Configurations and Pricing](https://docs.datomic.com/whatis/configurations-and-pricing.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
22. [Datomic is Free](https://blog.datomic.com/2023/04/datomic-is-free.html), maker, Datomic team, published Apr 2023, accessed 24 Sep 2026 (search summary)
23. [Datomic Cloud is Free](https://blog.datomic.com/2023/06/datomic-cloud-is-free.html), maker, Datomic team, published Jun 2023, accessed 24 Sep 2026 (search summary)
24. [Datomic: Our Products](https://www.datomic.com/products.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
25. [Jepsen: Datomic Pro 1.0.7075](https://jepsen.io/analyses/datomic-pro-1.0.7075), independent, Jepsen (Kyle Kingsbury), published 15 May 2024, accessed 24 Sep 2026 (search summary)
26. [Setting Null Values in Datomic](https://matthewboston.com/blog/setting-null-values-in-datomic/), independent, Matthew Boston, publication date not shown, accessed 24 Sep 2026 (search summary; descriptive use only)
27. [datomic-client-js](https://github.com/csm/datomic-client-js) (README, CHANGELOG, `src/shared.js`) and [npm registry metadata](https://registry.npmjs.org/datomic-client-js), community, Casey Marshall (repository owner `csm`), version 0.1.13, read at commit `59c03a7` (25 Feb 2026), accessed 24 Sep 2026
28. [Datomic Cloud Architecture](https://docs.datomic.com/cloud/whatis/architecture.html), maker, Datomic, accessed 24 Sep 2026 (search summary)
29. [Cognitect, creator of Clojure and Datomic, is now part of Nubank](https://building.nubank.com/nubank-acquires-cognitect/), maker, Nubank, publication date not seen, accessed 24 Sep 2026 (search summary)
30. [XTDB documentation source, `docs/src/content/docs/concepts/key-concepts.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/concepts/key-concepts.md), maker (XTDB), JUXT Ltd, read at commit `6cd79ee` (23 Sep 2026), accessed 24 Sep 2026
31. [XTDB `README.adoc` and `LICENSE`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/README.adoc), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026
32. [XTDB documentation source, `about/txs-in-xtdb.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/about/txs-in-xtdb.md), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026
33. [XTDB `core/src/main/clojure/xtdb/sql.clj` (recursive CTEs rejected) and `reference/main/sql/queries.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/core/src/main/clojure/xtdb/sql.clj), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026
34. [XTDB documentation source, `drivers/nodejs.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/drivers/nodejs.md), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026
35. [XTDB documentation source, `reference/main/data-types.md`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/docs/src/content/docs/reference/main/data-types.md), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026
36. [XTDB `CONTRIBUTING.adoc`](https://github.com/xtdb/xtdb/blob/6cd79ee2f5df500c3112c309e21a9a9870484d93/CONTRIBUTING.adoc), maker (XTDB), JUXT Ltd, read at commit `6cd79ee`, accessed 24 Sep 2026
37. [SurrealDB documentation source, `learn/data-models/architecture.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/learn/data-models/architecture.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7` (23 Sep 2026), accessed 24 Sep 2026
38. [SurrealDB documentation source, `data-types/none-and-null.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/data-types/none-and-null.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
39. [SurrealDB documentation source, `build/migrating/from-other-databases/from-postgresql.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/build/migrating/from-other-databases/from-postgresql.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
40. [SurrealDB documentation source, `learn/querying/concepts-and-guides/transactions.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/learn/querying/concepts-and-guides/transactions.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
41. [SurrealDB `LICENSE` (Business Source License 1.1)](https://raw.githubusercontent.com/surrealdb/surrealdb/main/LICENSE), maker (SurrealDB), SurrealDB Ltd, accessed 24 Sep 2026
42. [SurrealDB documentation source, `reference/rest-api/postgres-protocol.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/rest-api/postgres-protocol.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
43. [SurrealDB documentation source, `statements/define/table.mdx` and `statements/define/field.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/statements/define/table.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
44. [SurrealDB documentation source, `data-types/numbers.mdx` and `data-types/datetimes.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/data-types/numbers.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
45. [SurrealDB documentation source, `language-primitives/idioms.mdx` (recursive paths)](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/language-primitives/idioms.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026
46. [SurrealDB JavaScript SDK documentation source, `reference/javascript/api/types/index.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/javascript/api/types/index.mdx) and [SDK source, `packages/sqon/src/codec/cbor/codec.ts`](https://github.com/surrealdb/surrealdb.js/blob/69129d7d3109c22f55f94954510c392a3e1ebc8e/packages/sqon/src/codec/cbor/codec.ts), maker (SurrealDB), SurrealDB Ltd, read at commits `47139e7` and `69129d7` (10 Sep 2026), accessed 24 Sep 2026
47. [SurrealDB documentation source, `statements/define/indexes.mdx`](https://github.com/surrealdb/docs.surrealdb.com/blob/47139e737a8d17cbdd274322c85bb75dba42cc81/src/content/reference/query-language/statements/define/indexes.mdx), maker (SurrealDB), SurrealDB Ltd, read at commit `47139e7`, accessed 24 Sep 2026

**Searched**: Network access: docs.datomic.com, blog.datomic.com,
www.datomic.com, jepsen.io, tonsky.me, clojure.org, db-engines.com and
most non-GitHub hosts answered 403 at this session's proxy on 24 Sep 2026;
github.com (git and the GitHub search API), raw.githubusercontent.com, the
Datomic download bucket, Maven Central and the npm registry were readable.
Search strings (24 Sep 2026): "Datomic schema reference value types bigdec
bigint bytes instant tuple" (found [8]); "Datomic storage services SQL
database PostgreSQL datomic_kvs" (found [7]; no supported-version matrix or
managed-provider list, hence the C1 Not published clause); "Datomic entity
specs required attributes :db.entity/attrs :db/ensure attribute predicates"
(found [8]); "Datomic as-of since history database filters reified
transactions provenance" (found [11][12]); "Datomic indexes EAVT AEVT AVET
VAET index-range" (found [15]); "Datomic Datalog rules recursion aggregates
query inputs pull" (found [16]; no shortest-path construct, hence C6's Not
published clause and the nice-to-have row); "Datomic query best practices
most selective clauses first" and "Datomic query hints query-stats" (found
[17]); "Datomic transactions :db/cas upsert unique identity transactor
ACID" (found [9][13][14][28]); "Datomic nil values not allowed cardinality
many set" and "Datomic transaction data nil value not allowed" (found [26];
no maker statement surfaced, hence C3's weaker footing); "Datomic
:db.cardinality/many set of values" (found [8]); "Datomic transact
attribute not defined must be installed before use" (found [8]); "Datomic
Analytics Support Trino Presto SQL metaschema read-only" (found [18]);
"Datomic client JavaScript TypeScript Node.js library REST API" (found
[19][27]; no maker JavaScript client, hence C9 Unknown); "Datomic is free
Apache 2.0 binaries Nubank" (found [22][23]); "Datomic Local Datomic Cloud
pricing" (found [21][24]); "Datomic bytes limitations value equality"
(found [10]); "Datomic peer language support JVM" (found [19]); "Datomic
schema is data attributes are entities noHistory excision" (found [20]);
"Datomic security vulnerability reporting policy" (no maker policy, hence
the Security process Not published cell); "Datomic Nubank adoption
companies using Datomic" and "DB-Engines ranking SurrealDB Datomic XTDB"
(no independent adoption figure, hence Adoption Not published; the
DB-Engines pages were blocked); "Jepsen Datomic Pro 1.0.7075" (found
[25]); "Datomic benchmark PostgreSQL" and "Datomic performance comparison
graph traversal" (nothing comparable, hence C12 Unknown); "Datomic SOC 2"
(nothing, hence Certifications Not published); "Datomic row level
security" (nothing, hence the nice-to-have row). Apache AGE, Palantir
OSv2, Sqlg, PuppyGraph, Gel, Neo4j, Memgraph, LadybugDB, UMF-generated
per-type tables and JSONB plus expression indexes were not searched in this
profile, hence Not researched.

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
