---
ddx:
  id: truss.component-profile-palantir-osv2
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

# Component Profile: Palantir Foundry Object Storage V2 (OSv2)

Desk research on Palantir Foundry's Object Storage V2, the backend that stores,
indexes and serves the Foundry Ontology, measured against the capabilities truss
needs from a graph storage and query layer. OSv2 is profiled as a reference
system and an alternative to building truss, not as something truss could run
on. The build-versus-adopt decision this informs has no ADR yet; what the record
cannot settle is routed below.

## Scope

- Component: Palantir Foundry Object Storage V2 ("OSv2"), as publicly documented
  on 2026-09-24. Palantir's documentation uses "Object Storage V2 (OSv2)" for
  "the next-generation canonical data store for backing the Ontology" and
  "Object Storage V1 (Phonograph)" for "Foundry's legacy Ontology backend
  component" [1]. OSv2 reached general availability on 2023-05-26 as "a total
  re-architecting of the backend infrastructure that powers the Foundry
  Ontology" meant "to replace the Object Storage V1 (Phonograph) architecture"
  [10]. The term therefore means what the brief assumed. The profile covers the
  services Palantir groups as the Ontology backend (Ontology Metadata Service,
  object databases, Object Set Service, Actions, Object Data Funnel) [1] and the
  public access surfaces: Foundry API v2 as documented in the Python Platform SDK
  1.107.0 [71], the TypeScript Ontology SDK (OSDK) 2.72.0 [72][73], and Ontology
  SQL [37].
- Kind: Product (a proprietary component of a managed platform)
- Would fill: evaluated as a **reference system and alternative** to building
  truss, not as a substrate truss could embed. OSv2 runs only as part of Palantir
  Foundry [1][8] and cannot run inside a user's PostgreSQL. Two purposes: scoring
  it on the same capabilities used for the other candidates, and extracting
  design lessons for truss (the lessons are in a companion note,
  `design-lessons-palantir-osv2.md`). Palantir's Ontology is also a planned
  future UMF interchange target (UMF architecture, "Palantir Ontology | Later
  native operational-model interchange").
- Feeds: the owner's build-versus-adopt decision for truss (no ADR exists yet);
  secondarily, UMF's Foundry export and API study (UMF competitive analysis,
  Research Follow-up).
- Incumbent: none. truss has no implementation; teams use hand-built per-type
  tables, JSONB documents or a separate graph database
  ([[truss.product-vision]] §Target Market). truss has no current-state
  inventory.
- Researched: 2026-09-24 to 2026-09-25
- Excluded: Gotham, AIP and LLM features, the Workshop and Slate application
  layer, Foundry pipelines except where they feed OSv2, contract pricing, and
  anything non-public about how the object databases work inside (see Open
  Questions). No hands-on testing was possible and no result here comes from
  running anything.
- Access conditions: the egress proxy blocked www.palantir.com (including
  palantir.com/docs), blog.palantir.com, community.palantir.com,
  learn.palantir.com, web.archive.org and archive.ph, as well as most
  independent sites. Palantir documentation pages were therefore read from a
  community mirror of the documentation (JeremyMeissner/palantir-docs [81]); the
  mirror does not show its capture date. Where a search-engine summary of the
  live page on 2026-09-24 repeats the mirrored text, that is noted as
  corroboration of currency. Content known only from search-engine summaries is
  labelled "(search summary)" and was not read directly. The Foundry API
  reference and OSDK were read from Palantir's own published packages [71][72][73].

## Summary

truss needs a graph storage and query layer that runs inside an organization's
existing PostgreSQL, so that teams can store, traverse, update and constrain
connected data described by UMF schemas without moving it, see which rules are
enforced, and never lose data silently. The layer must run on current
PostgreSQL, store UMF's nine scalar families exactly, keep absent separate from
null along with lists and maps, enforce declared rules on writes, index property
values, support multi-hop traversal and writes that compose with SQL, give
defined concurrent-write behaviour, retain data that fits no schema, work from
TypeScript without numeric loss, stay readable through plain SQL, be a
sustainable dependency, and meet a latency target relative to a hand-designed
schema. On the public record Palantir's Object Storage V2 meets two of these
(property indexing and lossless TypeScript access), leaves two open (rule
enforcement and latency), and fails the other eight, starting with the fact that
it runs only inside Palantir Foundry; it is No fit as a component, and its value
to truss is as the most mature documented example of typed objects, links and
edits at scale.

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
| **(search summary)** | Any claim | Taken from a search engine's summary of a page the proxy blocked; the page itself was not read. |
| **Interpreted** | Capability Alignment | The capability's wording is PostgreSQL- or Cypher-specific; the subsection states the OSv2 equivalent it was measured against. Status stays strict. |

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

Object Storage V2 is the storage and indexing backend of the Palantir Foundry
Ontology: a set of Palantir services that index data from Foundry datasources
and user edits into "specialized object databases" and serve searches,
aggregations, traversals ("Search Arounds") and writes over typed objects,
properties and links [1][2]. It is made and operated by Palantir Technologies as
part of Foundry [1]. Palantir built it "from first principles" because "Foundry
gained more capabilities and evolved to meet the complex operational needs and
growing scale of Palantir's customers"; the new design "separates dimensions of
concern that had been consolidated in Object Storage V1 (Phonograph)" so that
indexing and querying "can scale horizontally" [1]. It became generally
available on 2023-05-26 [10]; migration from OSv1 "is mandatory for all object
types" [12], and OSv1 "will be unavailable after June 30, 2026" [11] (a living
page; the search summary of the live page on 2026-09-24 still showed this date).
Palantir describes the data it holds as ephemeral indexes over durable Foundry
datasets: "All indexed data in object databases are considered ephemeral" [4].

- Category and purpose: managed object store and index behind an operational
  ontology; typed objects, properties and links, edits through governed Actions,
  queries through object sets, search-arounds, aggregations, the OSDK and SQL
  [1][30][37][44]
- Maker or governing body: Palantir Technologies, single vendor [1][80]
- Adoption, from an independent source: Not published for OSv2 as a
  component. Company-level only: a 2026-08-03 CNBC report on Palantir's second
  quarter of 2026 is summarised as giving a U.S. commercial customer count of 653
  (search summary) [79]. Because OSv1 migration is mandatory [12], OSv2 is the
  Ontology backend for every Foundry ontology going forward (maker statement,
  not an adoption measure).
- Release cadence and support window: Not published for OSv2 (searched the
  overview, migration and announcement pages [1][10][12], 2026-09-24). The public
  SDKs release often: `@osdk/api` was first published 2023-09-29 and its 2.72.0
  release on 2026-09-23 [72]; `foundry-platform-sdk` 1.107.0 was published
  2026-09-23 [71].
- Licence: proprietary Foundry platform; contract terms Not published (searched
  [42][74], 2026-09-24). The client SDKs are Apache-2.0 [71][72][73].
- Built-for use cases: an "operational layer for the organization" that serves
  as "a digital twin" with semantic elements (objects, properties, links) and
  kinetic elements (actions, functions, dynamic security) [1]; high-scale reads,
  "atomic and durable transactional updates, high-scale batch mutations,
  high-scale streams, and mechanisms like Change Data Capture" [41]. Palantir
  advises that the Ontology "is best used with highly refined data that is
  synthesized from a larger data asset" [40].

## Capability Alignment

### C1. Runs inside the user's own PostgreSQL

OSv2 is not a database a customer installs. Palantir describes it as services
inside Foundry: the Ontology Metadata Service, object databases, the Object Set
Service, Actions and the Object Data Funnel [1]. Indexing runs as Foundry build
jobs on "a parallelized Spark backend" [39], and the last step, "hydration",
downloads index files "into the disks of the OSv2 database search nodes" [8].
Durable state lives in Foundry datasets that Funnel owns [4][8]. A 2026 analysis
by Pankaj Kumar is summarised as saying "you can't adopt the Ontology without
adopting Foundry" and that the Ontology "doesn't query your operational
database or lakehouse in place" (search summary) [77]. No Palantir page offers a
form that runs inside a customer's PostgreSQL, and the capability needs no
interpretation.

**Settled by**: a supported-version matrix or managed-provider listing does not
apply; the maker documents OSv2 only as Foundry services [1][8][39]
**Status**: Unmet

### C2. Stores UMF's nine scalar families exactly

The property types are boolean, byte, short, integer, long, float, double,
decimal, string, date and timestamp, plus geopoint, geoshape, attachment, media
reference, time series, vector, cipher text, marking, struct and array [54][55].
Palantir states that "All field types are valid base types except for Map and
Binary types" [14], so **binary data has no property type**. Neither the
property types [55] nor the dataset field types [49] include a **time-of-day**
type. Timestamps travel as an "ISO 8601 extended offset date-time string in UTC
zone" [54], and the timestamp used by the "Apply most recent value" strategy
"must be in Coordinated Universal Time (UTC)" [4]; whether storage keeps the
original offset is Not published. Long values travel as JSON strings [54], but
Palantir warns that "Long has representational issues in Javascript" above
1e15 [13], and a Functions `Long` is limited to "-(2^53 - 1) to (2^53 - 1)"
[36]. Decimal precision and scale are capped at 38 [56]. Palantir's own pages
disagree on decimals: the property metadata page says decimals "cannot be used
within action types as the precision cannot be guaranteed ... due to the
conversion between JSON and Java" and that the type "is also not supported in
Object Storage V2" [17] (the search summary of the live page on 2026-09-24
repeats this). Other pages list Decimal as supported in actions [32], allow
DECIMAL struct fields [15], and explain how to set decimal precision and scale
when migrating to OSv2 [12]. OSv2 **rejects rather than coerces** bad data:
"NaN or ±infinity" and empty strings are disallowed (OSv1 "silently converted"
empty strings "to nulls"), a string may be at most 12 MB, and violations make
batch indexing fail [3]. Type-changing migrations fail rather than "clean or
coerce" incompatible values [3]. The exception is streaming, where violating
records "are dropped" [3].

**Settled by**: type-system documentation found in [14][49][54][55][56]; precision
rules in [3][13][36]; conflicting decimal statements in [12][15][17][32]
**Status**: Unmet (Palantir states binary is not a property base type [14], there
is no time-of-day type, timestamps travel in UTC, and decimal support is stated
inconsistently)

### C3. Absent versus null, ordered lists, string-keyed maps

An object is a map from property API name to value [57]. The null filter
"Returns objects based on the existence of the specified field" [60], and the
nullability constraint notes that "Null values may still be observed for objects
that are not present in the datasource mapping" [67]. Three different
situations all appear as null. A property from a datasource that has no row for
the object shows null [28]. A property the user may not see shows "a null value
in place of the property value" [27]. And so does a genuinely null value. No
page documents a way to tell an absent property from an explicit null (Not
published; searched [3][13][16][54][57][60][67], 2026-09-24). Arrays exist for
every base type except vector and time series [14]. They cannot contain null
elements or nested arrays, and they hold at most 100,000 elements [3].
Duplicates are allowed unless a value type adds a uniqueness constraint [25].
Whether element order is preserved is Not published. **Maps are not a property
type** [14]. Structs have a fixed schema, "a depth of one", and "fields cannot
be arrays" [13][15].

**Settled by**: null handling found in [27][28][60][67]; list rules in [3][14][25];
maps stated absent in [14]
**Status**: Unmet

### C4. Rules enforced by the store on writes

*Interpreted*: rules that OSv2 enforces when it indexes datasource data and when
Actions (its write path) are applied, in place of database constraints and
Cypher writes.

Required properties exist only in OSv2. They are checked "as backing datasources
are indexed" and at Action apply time, where writing a null makes "the action
fail to execute" [16]. Value types add enum, range (including string length and
array size), regex, RID, UUID, array-uniqueness and struct-field constraints
[25]. They "enforce their validation constraints on data in Builder pipelines and
the ontology" [24], and a value type whose constraints existing values fail
makes the object type "fail to index" [53]. Mandatory-control values are checked
"on the object storage level", and invalid edits "will be rejected" [29].
Primary keys must be unique within a datasource transaction; a duplicate "within
a single transaction" fails indexing, and "across transactions, the version in
the later transaction will be used" [3][8]. Each object type declares a single
primary-key property [57], and real-number, geo, array and time-series types
cannot be keys [3]. Alternate unique keys are Not published, and so is whether
key equality is binary or normalised (searched [3][13][16][17][25][57],
2026-09-24). Link endpoints are fixed by the link type definition: a foreign key
on one object type refers to the primary key of the other, or a join table maps
columns to both primary keys [19][20]. But "the one-to-one cardinality is not
enforced" [20], and link reads warn that returned "primary keys ... may not exist
anymore" [61]. Enforcement depends on the source: batch violations fail the
indexing job, while "for object types backed by streaming datasources, records
that violate these restrictions are dropped" [3].

**Settled by**: constraint behaviour found in [3][16][20][24][25][29][53];
key-equality semantics and alternate keys not found (searched as above)
**Status**: Unknown (required and value constraints are Met; key-equality
semantics and alternate unique keys are unpublished; cardinality is documented as
not enforced)

### C5. Property indexes used by queries

*Interpreted*: indexing of property values for equality and range filters and
their use by OSv2's own query surfaces (object-set filters, search-arounds,
aggregations and Ontology SQL) in place of a Cypher planner.

OSv2 builds everything as index files [8]. The query filter union includes
`eq`, `gt`, `gte`, `lt`, `lte`, `in`, `isNull`, range, text, regex, geo and
interval predicates [60], and `eq` applies to "number, string, date, timestamp"
[62]. Indexing is controlled per property: deselecting the "searchable and
sortable render hints" improves reindex performance [17]. Ontology SQL states
that when functions are applied to columns in filters "the query engine cannot
leverage indices", which implies that filters on unmodified columns do use them
[37]. How query planning works inside the object databases is Not published, and
no independent query plans exist.

**Settled by**: indexing documentation found in [8][17][37][60][62]; independent
plan evidence not found (searched "palantir osv2 query plan index", 2026-09-24)
**Status**: Met (maker documentation only)

### C6. Traversal, pattern matching, aggregation, writes, SQL composition

*Interpreted*: object-set algebra, Search Around, aggregations, Action rules and
Ontology SQL in place of openCypher.

Reads compose object sets with `filter`, `union`, `intersect`, `subtract`,
`searchAround`, `nearestNeighbors` and `withProperties` [59]; the OSDK exposes
the same operations as `where`, `pivotTo` and `aggregate` [72]. Traversal hops
one link type at a time. Functions allow "a maximum of 3 search arounds" on
object sets loaded into memory, and in OSv2 a search-around result may not exceed
10 million objects [34]. The Ontology architecture page sets a default "Search
Around limit" of 100,000 objects, runs larger ones on a Spark-based execution
layer, and asks customers to contact support to raise it [1]. Derived properties
traverse "up to 3 levels" [51]. Variable-length traversal and a pattern-matching
language are Not published (searched [34][37][59][72], 2026-09-24).
Aggregations exist but may be approximate: Object Explorer and Workshop default
to `PREFER_SPEED`, while the OSDK and Functions request accuracy [33], and exact
grouping defaults to 10,000 groups [70]. Writes are Action rules: create, modify,
"create or modify" (the nearest thing to merge), delete, and many-to-many link
create and delete. Rules compile "to generate a single edit per object", and
foreign-key links change by editing the foreign-key property [31]. Actions
cannot edit primary keys [32]. SQL composition goes through Ontology SQL, which
is Beta, SELECT-only, single-statement, returns at most 10,000 rows, times out
at 20 seconds, fails on struct columns, and allows "No mixing of objects and
datasets" in one query [37]. It is exposed as a Public Beta API returning Apache
Arrow [66].

**Settled by**: query and write surfaces found in [1][31][33][34][37][59][66][72];
variable-length traversal not found (searched as above)
**Status**: Unmet (no documented variable-length traversal or pattern language;
Palantir states that objects cannot be joined with relational datasets in one SQL
query [37])

### C7. Transactional writes under concurrency

*Interpreted*: the transactional semantics of Actions and the Funnel edit queue
in place of PostgreSQL isolation levels.

"An action is a single transaction that changes the properties of one or more
objects" [30], and Functions that generate edits pass them to "the actions
service executing the atomic transaction" [35]. In OSv2, edits "will be visible
immediately after the action completes" (OSv1 was "eventually consistent") [63].
Edits enter "a Funnel-managed queue that has offset tracking to support
simultaneous user edits", and a later read "is guaranteed to contain the user
edits" [4]. Version checking is deliberately partial. Front-end values are sent
to `/apply` without versions, and "there is no guarantee" that they match what
the server loads. In OSv2 the Actions server checks only the versions "of objects
that are directly used to generate edits", which "reduces the frequency of
StaleObject conflicts, with a consequence of weaker guarantees" [4]. OSv1
instead failed whole Actions on any object change, "user edits on irrelevant
properties" included [4]. The apply endpoint takes no expected-version parameter
[63]. A community question from 2026, "Enforce idempotency and prevent
concurrent Ontology Actions from overwriting each other", asks how to stop two
Actions that read the same state from overwriting each other (search summary;
the answer was not visible) [76]. Concurrent "create or modify" on the same
primary key is Not published. A multi-call Ontology transaction API exists only
as a Private Beta [65].

**Settled by**: concurrency documentation found in [4][30][35][63][65]; community
evidence in [76]; concurrent merge behaviour not found (searched [4][31][63],
"palantir action concurrent create same primary key", 2026-09-24)
**Status**: Unmet (Actions are atomic, but Palantir documents that
read-modify-write through the front end is not version-checked, so lost updates
are possible by design)

### C8. Retains data that matches no schema definition

Object types have a fixed schema. Properties are bound to datasource columns,
struct columns or "edit-only" slots [68], and a datasource property mapping
lists only modelled properties ("Properties whose mapping info cannot be
modeled are omitted") [68]. Maps are not a property type [14], so no property
can hold arbitrary keys. Unmapped columns stay in the backing Foundry dataset
[4][8] but are not part of any object. OSDK code generation "will skip" a
property whose type it does not support "and log the error" [45]. Streaming
records that break the data restrictions are dropped [3].

**Settled by**: documentation that arbitrary maps are stored: not found; maps
stated absent in [14]; schema binding in [68]
**Status**: Unmet

### C9. TypeScript on Bun or Node without numeric loss

The TypeScript OSDK is an npm package, `@osdk/client` 2.72.0 (Apache-2.0,
2026-09-23) [73]. It maps `long` and `decimal` properties to TypeScript `string`
on read [72], and the client source describes "numeric strings (the wire
encoding for `decimal` and `long`)" compared with big.js to cover "longs beyond
Number.MAX_SAFE_INTEGER" [73]. The REST API also encodes Long and Decimal as JSON
strings [54]. There are caveats. Writes accept `long: string | number` and
`decimal: string | number` [72], so a caller who passes a number can lose
precision. TypeScript v1 Functions treat `Long` as a `number` bounded at
±(2^53−1), while TypeScript v2 uses `string`, and TypeScript Functions do not
support Decimal [36]. The TypeScript OSDK skips cipher, marking and vector
properties [45]. Palantir names NPM as the TypeScript channel [44]; Bun support
is Not published (searched [44][46][73], 2026-09-24).

**Settled by**: client documentation and wire format found in [36][44][54][72][73]
**Status**: Met (reads and string-typed writes through the OSDK; no Bun statement)

### C10. Readable by other tools through plain SQL

*Interpreted*: whether other tools can read OSv2 data with SQL and get ordinary
SQL types, through Ontology SQL, materialised datasets and Foundry's
JDBC/ODBC drivers.

Ontology SQL runs Spark SQL "directly against object storage", and "all other
ontology column types are supported and automatically converted to
SQL-compatible types", but "Including a struct-type column will cause the query
to fail". It is Beta, capped at 10,000 rows, main branch only, and OSv2 only
[37]. Full-fidelity bulk access means materialising objects into a Foundry
dataset, which is a derived copy with "a latency of a few minutes". Only its
"latest snapshot is guaranteed", and its `__`-prefixed metadata columns "could
be renamed or removed ... without prior warning" [6]. Foundry's JDBC and ODBC
drivers give "a read-only SQL-based interface" to Foundry datasets (search
summary of the live page) [49]. Palantir states that platform data is kept in
open formats such as Parquet and Iceberg [42]. None of this puts the data in a
database the customer runs.

**Settled by**: SQL access and type conversion found in [6][37][42]; Palantir
states that struct columns fail in the direct SQL path [37]
**Status**: Unmet (the direct SQL path is Beta, capped at 10,000 rows and cannot
read struct properties; complete SQL access needs a materialised copy)

### C11. Long-lived dependency

Palantir Technologies alone controls OSv2 as part of a proprietary platform
[1][80]. Releases are active: the OSDK shipped 2.72.0 on 2026-09-23 [72], and the
second-quarter 2026 filing is listed on SEC EDGAR (search summary) [80]. Commercial
use is by contract; the licence terms are not public (searched [42][74],
2026-09-24). There is no open governance or foundation, and the public
contributor base covers only the Apache-2.0 SDKs [71][72][73]. Kumar's 2026
analysis is summarised as saying that migrating away "is extremely expensive"
and that "you can't easily export an Ontology model and run it elsewhere"
(search summary) [77]. Palantir's Ontology JSON export carries the warning "You
should not depend on the exported JSON schema as it may change over time" [43].

**Settled by**: governance and licence evidence found in [43][71][77][80]; no
foundation, open governance or public licence text exists for the backend
**Status**: Unmet (the open-governance clause fails for a single-vendor
proprietary platform)

### C12. Latency within twice a hand-designed schema

Palantir publishes scale figures, not latency comparisons. It claims indexing
"on the order of tens of billions of objects for a single object type" [1][10],
streaming indexing "on the order of seconds or minutes" [9], and minimum
compute-second costs per query type [38]. No independent benchmark compares OSv2
with a relational or native-graph baseline (Not published; searched "palantir
osv2 benchmark latency", "palantir ontology performance p95", "object storage v2
query latency", 2026-09-24).

**Settled by**: independent benchmark not found (searched as above)
**Status**: Unknown

Other notable capabilities the record documents and no criterion requires:

| Capability | What the record says | Source |
|------------|----------------------|--------|
| Multi-datasource object types | Column-wise only; each property from exactly one datasource ("Property multiplicity is currently not supported"); up to 70 datasources per object type; not for streaming | [28] |
| Conflict resolution between edits and source data | Per datasource: "Apply user edits" (default) or "Apply most recent value" (needs a UTC timestamp column); deletions are not edits; a recreated object "will not inherit the previous edits" | [4] |
| Edit history | Opt-in per object type; only records changes after enabling; "Disabling Track user edit history permanently deletes all existing edit histories"; API returns object edits only ("link edits are not included"), each with user, timestamp and action | [7][64] |
| Schema migrations of edited data | Predefined migrations (drop, move, cast, revert); up to 500 at once; none on primary keys | [5] |
| Streaming indexing | "Most recent update wins"; out-of-order events give "incorrect data"; no user edits; records at most 1 MB; at most 250 properties; exactly-once by default | [9] |
| Row, column and cell security | Object and property security policies; a user who fails a property policy sees null; mandatory-control (marking) properties | [27][29] |
| Interfaces and shared properties | Interfaces with inheritance and link-type constraints; shared properties share metadata, not data | [21][22][23] |
| Vector search | KNN only; 0 < k ≤ 100; at most 2048 dimensions; OSv2 only | [34] |
| Change data capture | Named as an Ontology engine capability; no detail found | [41] |
| Snapshot paging | Optional `snapshot` flag for consistent paging on object-set loads | [48][59] |
| Edit-only properties | Properties with no backing column, populated only by Actions; OSv2 only | [52] |
| Value type versioning | Base type and constraints are immutable per version; changing constraints creates a new version; non-breaking versions "automatically propagate to the Ontology" | [26] |
| Cross-ontology links | "links between object types across different Ontologies is not supported" | [18] |
| Conflict strategy edge case | Under "Apply most recent value", a newer source timestamp reverts a user's edit of a null field back to null (Q&A dated 2024-06-13) | [50] |
| API limits | Per user: 5,000 requests per minute and 30 concurrent; service users: 800 concurrent (as of 2026-09-24) | [47] |

**Verdict**: No fit. C1, C2, C3, C6, C7, C8, C10 and C11 are Unmet on the public
record, starting with C1: OSv2 runs only inside Palantir Foundry. That is
expected for a system profiled as a reference, and it does not reduce the value
of its design record to truss.

## Technology and Operations

| Aspect | What the record says | Source |
|--------|----------------------|--------|
| Hosting model | Part of Palantir Foundry; services plus Spark indexing jobs and search nodes run by Palantir; no customer-installable form found (as of 2026-09-24) | [1][8][39] |
| Integrations | REST API v2 and generated OSDKs for TypeScript (npm), Python and Java, plus OpenAPI for other languages; Ontology SQL (Beta); webhooks; JSON Ontology export and import | [42][43][44][66] |
| Data handling | Indexes are "ephemeral"; durability comes from Funnel-owned Foundry datasets; merged edits persisted when datasources update or every 6 hours when edits exist; materialisation retention not customisable. Encryption and residency not researched (outside the role) | [4][6][8] |
| Certifications | Palantir's Trust and Security Portal is summarised as listing SOC 2 Type 2, ISO/IEC 27001, FedRAMP High and DoD IL6 among others (search summary; portal blocked) | [74] |
| Maturity and cadence | GA 2023-05-26; OSv1 unavailable after 2026-06-30; OSv2 release cadence Not published; SDK releases frequent (2026-09-23) | [10][11][71][72] |
| Governance | Single vendor (Palantir Technologies) | [1][80] |
| Security process | Disclosure policy and patch cadence for OSv2: Not published (searched [74], "palantir vulnerability disclosure foundry", 2026-09-24) | none |

## Pricing and Licensing

| Item | Figure | Label | Source |
|------|--------|-------|--------|
| Licence | Proprietary Foundry subscription; terms not public. SDKs are Apache-2.0 | Published (SDKs); Not published (platform terms; searched [42][74], "palantir foundry pricing", 2026-09-24) | [71][72][73] |
| Query compute (model effective 2026-01-01) | Minimum compute-seconds per query: base 2, Search Around 5, aggregation 5, Ontology SQL 5, advanced 10, derived property 10, Actions 18 plus 1 per extra object edited; OSv1 queries 16 | Published (as of 2026-09-24) | [38] |
| Indexing compute | Spark compute-seconds = max(vCPU, GiB/7.5) × runtime, for driver and executors | Published | [39] |
| Storage | Ontology volume in GB-month; "Ontology data cannot be compressed" | Published | [40] |
| Price per compute-second or GB-month | Not published | Not published (searched [38][39][40], "palantir compute-second price", 2026-09-24) | none |

## Competitive Landscape

Split into two tables (C1–C6, C7–C12) for width; the rows are the same.
Options A and C are PostgreSQL itself, so their cells cite PostgreSQL 18
documentation.

| Candidate | C1 In user's PostgreSQL | C2 Nine scalar families | C3 Absent vs null, lists, maps | C4 Enforced rules | C5 Property indexes | C6 Traversal and SQL | Profile |
|-----------|----|----|----|----|----|----|---------|
| Palantir OSv2 | Unmet: Foundry services only [1][8] | Unmet: no binary or time type; UTC timestamps [14][54] | Unmet: no map type; null conflated [14][27][28] | Unknown: required and value checks; 1:1 not enforced [16][20][53] | Met (interpreted) [8][37][60] | Unmet: no variable-length traversal; SQL cannot mix objects and datasets [34][37] | this profile |
| Apache AGE | Unknown† | Unmet† | Unmet† | Unknown† | Unknown† | Met† | [[component-profile-apache-age]] |
| Sqlg | Stores graph data in the user's PostgreSQL (also H2, HSQLDB, MariaDB, MySQL) [98]; version matrix Not researched | Timestamp types without time zone since 2.1.0 [99]; exact decimal Not researched | `isPresent()` true whenever the property is in the schema, regardless of value (3.0.0), so absent and null are not told apart [99] | Multiplicity on properties and edges; one-to-many and unique many-to-many enforced (3.0.0) [99] | Met† | Gremlin on TinkerPop 3.7.4 [99]; one table per label [[truss.competitive-analysis]]; SQL composition Not researched | [[component-profile-sqlg]] |
| UMF-generated per-type tables (option A) | It is PostgreSQL; 18 documented [83]; managed-provider matrix Not researched | bigint covers the signed 64-bit range; numeric exact; bytea; date and time types; timestamptz keeps UTC and drops the original zone [83] | Not researched (depends on the generator's null and list mapping) | NOT NULL, CHECK, UNIQUE and foreign-key constraints [100]; deterministic collations compare by byte sequence [84] | B-tree and expression indexes [88] | WITH RECURSIVE for variable-length paths [87]; native SQL; no graph pattern language (SQL/PGQ reverted from PostgreSQL 19) [[truss.competitive-analysis]] | *none yet* |
| JSONB plus expression indexes (option C) | It is PostgreSQL [83]; managed-provider matrix Not researched | JSON numbers map to numeric (exact; NaN and infinity disallowed); no binary, date or time JSON types; `\u0000` rejected [82] | JSON null differs from an absent key; arrays ordered with duplicates; objects are maps, but jsonb keeps only the last duplicate key and not key order [82] | Unique indexes on expressions [88]; foreign keys into JSON Not researched | GIN for containment and existence; expression indexes for extracted values [82][88] | As option A [87] | *none yet* |
| Neo4j | Unmet: separate database; data leaves the PostgreSQL estate [[truss.competitive-analysis]] | Unmet: no exact decimal type; byte arrays pass-through only [91] | Unmet: setting a property to null removes it; maps not storable; stored lists homogeneous without nulls [91][92] | Uniqueness in all editions; existence, type and key constraints Enterprise-only; no endpoint constraint among listed types [93] | Range, text, point and token-lookup indexes [95]; planner use Not researched | Cypher reads and writes including MERGE [94]; separate database, so no joins with PostgreSQL tables [[truss.competitive-analysis]] | [[component-profile-neo4j]] |

| Candidate | C7 Concurrency | C8 Retains unmatched data | C9 TypeScript without loss | C10 Plain-SQL readable | C11 Sustainable dependency | C12 Latency within 2× | Profile |
|-----------|----|----|----|----|----|----|---------|
| Palantir OSv2 | Unmet: atomic Actions but limited version checks [4][63] | Unmet: fixed schema; no map type [14][68] | Met: OSDK returns long and decimal as strings [72][73] | Unmet: Beta SQL, 10,000 rows, no structs [37] | Unmet: proprietary single vendor [1][77] | Unknown: no benchmark | this profile |
| Apache AGE | Unknown† | Met† | Unknown† | Met† | Unknown† | Unknown† | [[component-profile-apache-age]] |
| Sqlg | Unknown† | Unmet† | Unmet: JVM library (built with Java 17) [99]; "JVM only" [[truss.competitive-analysis]] | Per-label tables readable by SQL [[truss.competitive-analysis]]; casts Not researched | MIT [98]; 3.1.6 released 2026-02-01 [[truss.competitive-analysis]]; maintainer count unverified | Unknown† | [[component-profile-sqlg]] |
| UMF-generated per-type tables (option A) | `ON CONFLICT DO UPDATE` "guarantees an atomic INSERT or UPDATE outcome ... even under high concurrency"; serialization failures documented [85][86] | Not researched (needs a generator-defined side store) | node-postgres returns int8 as strings by default [90] | Native SQL types | PostgreSQL Licence; PostgreSQL Global Development Group [89] | Closest to the baseline by construction; no benchmark (truss follow-up) [[truss.competitive-analysis]] | *none yet* |
| JSONB plus expression indexes (option C) | Row-level as option A [85][86]; per-key concurrent updates Not researched | Arbitrary keys kept, but jsonb drops duplicate keys, key order, whitespace and E-notation [82] | node-postgres parses json and jsonb with `JSON.parse` by default, so large numbers lose precision unless overridden [90] | Needs casts from extracted values; details Not researched | As option A [89] | Not researched | *none yet* |
| Neo4j | Node MERGE "only guarantees the existence of the pattern, not its uniqueness" without constraints; concurrent relationship MERGE serialised by locks [94] | Maps cannot be stored as property values [91]; schema-optional storage Not researched | Driver represents integers losslessly by default [96] | Unmet for the role: data leaves the PostgreSQL estate [[truss.competitive-analysis]]; SQL access to Neo4j Not researched | Community Edition GPLv3; single vendor, Neo4j Sweden AB [97] | Unknown† | [[component-profile-neo4j]] |

† Status copied on 2026-09-25 from the sibling profile named in the Profile column, where the evidence and sources are recorded.

- Apache AGE shares truss's premise (graph storage inside PostgreSQL); a
  sibling agent is writing its profile, and these cells are left for it.
- Sqlg shares truss's premise of graph storage in the user's PostgreSQL with
  enforced multiplicity [99]. It diverges on language (JVM and Gremlin) and on
  storage (one table per label, not per value) [[truss.competitive-analysis]].
- Option A shares OSv2's model of typed columns per object type and native
  constraints [83][88]. It diverges from truss's `generic` strategy on schema
  churn: every type change is DDL ([[truss.vision-input]] §Draft Storage Layers).
- Option C shares truss's goal of evolving shape without DDL. It diverges on
  fidelity: jsonb normalises keys and numbers and has no binary or temporal
  types [82].
- Neo4j shares the typed property-graph model and constraints [91][93]. It
  diverges on C1 and C10 (data leaves PostgreSQL) and on C3 (null removes a
  property) [92].
- OSv2 shares truss's separation of schema from stored values, explicit edit
  semantics and multi-source bindings [1][4][28]. It diverges on deployment
  (Foundry only), fidelity (no binary, map or time type; null conflated) and
  governance.

## Confidence

| Grade | Means |
|-------|-------|
| **High** | Every design-defining claim is corroborated by the maker's material *and* at least one independent source, and no design-defining capability is Unknown. |
| **Medium** | Design-defining claims rest on the maker alone, or a design-defining capability is Unknown, or the independent coverage is older than two major versions. |
| **Low** | Thin public footprint; claims rest on one source or on none. |

**Grade**: Medium. The verdict rests on C1 and C11. Palantir's architecture
pages [1][8] support both, and so does one independent 2026 analysis, known only
from a search summary [77]. The type, null, constraint, concurrency and SQL
findings (C2, C3, C4, C6, C7, C10) rest on Palantir alone. They come from
documentation read through a community mirror of unknown capture date [81],
cross-checked against Palantir's own versioned API reference and SDK packages
[54]–[73] and against search summaries of the live pages. No independent source
covers OSv2 internals, and C12 has no benchmark. Palantir's pages contradict
each other on decimal support [12][15][17][32] and on interface support in
Ontology SQL [37]. Weakest area: concurrency semantics (C7), where the only
non-maker evidence is a community question whose answers were not visible [76].

## Open Questions

None of these changes the verdict, which C1 and C11 settle. They matter for
truss's design lessons and for UMF's Palantir interchange.

| # | Question | Design-defining because | Route |
|---|----------|-------------------------|-------|
| 1 | Does OSv2 store an explicit null differently from an absent property, or are they one state? | Decides whether a UMF-to-Palantir mapping must report absent-versus-null loss | ask maker; UMF Foundry export and API study |
| 2 | Is Decimal a supported OSv2 property type, and is precision exact end to end? | Palantir's pages conflict [12][15][17][32]; decides the loss report for UMF's exact decimal family | ask maker |
| 3 | What equality do primary keys use (binary, case-folded, Unicode-normalised), and are array element order and duplicates preserved? | Decides whether UMF key and list semantics map losslessly | ask maker |
| 4 | What happens when two Actions concurrently "create or modify" the same primary key, and is there any compare-and-set? | Informs truss's concurrency lessons; unpublished [4][31][63] | ask maker |
| 5 | How does OSv2 latency compare with a hand-designed schema? | C12; cannot be measured without a Foundry enrollment | none for OSv2; truss's own benchmark spike ([[truss.competitive-analysis]] follow-up research) covers the baseline question |

## Sources

Classes: **maker** (the component's maker or governing body), **vendor** (a
company selling hosting or support for the component or a rival),
**independent** (no commercial interest; named author or organisation and a
date), **community** (a project or forum around the component).

Reading notes. **(M)**: a Palantir documentation page whose live URL was blocked
on 2026-09-24. Its text was read from the community mirror [81] at
`https://raw.githubusercontent.com/JeremyMeissner/palantir-docs/main/foundry/<same path>.md`;
the capture date is not shown. **(A)**: Palantir's API reference as shipped in the
`foundry-platform-python` repository at tag `1.107.0` (the PyPI release of
2026-09-23 [71]). All 83 downloaded files were byte-identical to the `develop`
branch on 2026-09-24. **(S)**: known only from a search engine's summary; the
page was not read. Palantir documentation pages are living pages without
per-page dates; every mutable fact is as of 2026-09-24.

1. [Ontology architecture](https://www.palantir.com/docs/foundry/object-backend/overview/) (M), maker, Palantir Technologies, accessed 2026-09-24
2. [Breaking changes between Object Storage V1 and Object Storage V2](https://www.palantir.com/docs/foundry/object-backend/object-storage-v2-breaking-changes/) (M), maker, Palantir Technologies, accessed 2026-09-24
3. [Data restrictions](https://www.palantir.com/docs/foundry/object-indexing/data-restrictions/) (M), maker, Palantir Technologies, accessed 2026-09-24
4. [How user edits are applied](https://www.palantir.com/docs/foundry/object-edits/how-edits-applied/) (M), maker, Palantir Technologies, accessed 2026-09-24
5. [Manage schema changes](https://www.palantir.com/docs/foundry/object-edits/schema-migrations/) (M), maker, Palantir Technologies, accessed 2026-09-24
6. [Materializations](https://www.palantir.com/docs/foundry/object-edits/materializations/) (M), maker, Palantir Technologies, accessed 2026-09-24
7. [Enable user edit history](https://www.palantir.com/docs/foundry/object-edits/user-edit-history/) (M), maker, Palantir Technologies, accessed 2026-09-24
8. [Funnel batch pipelines](https://www.palantir.com/docs/foundry/object-indexing/funnel-batch-pipelines/) (M), maker, Palantir Technologies, accessed 2026-09-24
9. [Funnel streaming pipelines](https://www.palantir.com/docs/foundry/object-indexing/funnel-streaming-pipelines/) (M), maker, Palantir Technologies, accessed 2026-09-24
10. [Announcements, May 2023: "Object Storage v2 is Generally Available"](https://www.palantir.com/docs/foundry/announcements/2023-05/) (M), maker, Palantir Technologies, published 2023-05-26, accessed 2026-09-24
11. [Object Storage V1 (Phonograph) [Planned deprecation]](https://www.palantir.com/docs/foundry/object-databases/object-storage-v1/) (M), maker, Palantir Technologies, accessed 2026-09-24
12. [Migrate from Object Storage V1 (Phonograph) to Object Storage V2](https://www.palantir.com/docs/foundry/object-backend/osv1-osv2-migration/) (M), maker, Palantir Technologies, accessed 2026-09-24
13. [Properties](https://www.palantir.com/docs/foundry/object-link-types/properties-overview/) (M), maker, Palantir Technologies, accessed 2026-09-24
14. [Base types](https://www.palantir.com/docs/foundry/object-link-types/base-types/) (M), maker, Palantir Technologies, accessed 2026-09-24
15. [Structs](https://www.palantir.com/docs/foundry/object-link-types/structs-overview/) (M), maker, Palantir Technologies, accessed 2026-09-24
16. [Required properties](https://www.palantir.com/docs/foundry/object-link-types/required-properties/) (M), maker, Palantir Technologies, accessed 2026-09-24
17. [Properties: Metadata reference](https://www.palantir.com/docs/foundry/object-link-types/property-metadata/) (M), maker, Palantir Technologies, accessed 2026-09-24
18. [Link types](https://www.palantir.com/docs/foundry/object-link-types/link-types-overview/) (M), maker, Palantir Technologies, accessed 2026-09-24
19. [Link types: Metadata reference](https://www.palantir.com/docs/foundry/object-link-types/link-type-metadata/) (M), maker, Palantir Technologies, accessed 2026-09-24
20. [Create a link type](https://www.palantir.com/docs/foundry/object-link-types/create-link-type/) (M), maker, Palantir Technologies, accessed 2026-09-24
21. [Interfaces](https://www.palantir.com/docs/foundry/interfaces/interface-overview/) (M), maker, Palantir Technologies, accessed 2026-09-24
22. [Interface link type constraints](https://www.palantir.com/docs/foundry/interfaces/interface-link-types-overview/) (M), maker, Palantir Technologies, accessed 2026-09-24
23. [Shared properties](https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview/) (M), maker, Palantir Technologies, accessed 2026-09-24
24. [Value types](https://www.palantir.com/docs/foundry/object-link-types/value-types-overview/) (M), maker, Palantir Technologies, accessed 2026-09-24
25. [Value type constraints](https://www.palantir.com/docs/foundry/object-link-types/value-type-constraints/) (M), maker, Palantir Technologies, accessed 2026-09-24
26. [Value type versions](https://www.palantir.com/docs/foundry/object-link-types/value-types-versions/) (M), maker, Palantir Technologies, accessed 2026-09-24
27. [Object and property security policies](https://www.palantir.com/docs/foundry/object-permissioning/object-security-policies/) (M), maker, Palantir Technologies, accessed 2026-09-24
28. [Multi-datasource object types (MDOs)](https://www.palantir.com/docs/foundry/object-permissioning/multi-datasource-objects/) (M), maker, Palantir Technologies, accessed 2026-09-24
29. [Mandatory control properties](https://www.palantir.com/docs/foundry/object-link-types/mandatory-control-properties/) (M), maker, Palantir Technologies, accessed 2026-09-24
30. [Action types](https://www.palantir.com/docs/foundry/action-types/overview/) (M), maker, Palantir Technologies, accessed 2026-09-24
31. [Action types: Rules](https://www.palantir.com/docs/foundry/action-types/rules/) (M), maker, Palantir Technologies, accessed 2026-09-24
32. [Action types: Scale and property limits](https://www.palantir.com/docs/foundry/action-types/scale-property-limits/) (M), maker, Palantir Technologies, accessed 2026-09-24
33. [Aggregation considerations](https://www.palantir.com/docs/foundry/object-backend/aggregation-considerations/) (M), maker, Palantir Technologies, accessed 2026-09-24
34. [Functions on objects: Object sets](https://www.palantir.com/docs/foundry/functions/api-object-sets/) (M), maker, Palantir Technologies, accessed 2026-09-24
35. [Functions (TypeScript v1): Ontology edits](https://www.palantir.com/docs/foundry/functions/api-ontology-edits/) (M), maker, Palantir Technologies, accessed 2026-09-24
36. [Functions: Types reference](https://www.palantir.com/docs/foundry/functions/types-reference/) (M), maker, Palantir Technologies, accessed 2026-09-24
37. [Ontology SQL [Beta]](https://www.palantir.com/docs/foundry/sql-warehousing/ontology-sql/) (M), maker, Palantir Technologies, accessed 2026-09-24
38. [Compute usage with Ontology queries](https://www.palantir.com/docs/foundry/ontologies/query-compute-usage/) (M), maker, Palantir Technologies, model effective 2026-01-01, accessed 2026-09-24
39. [Compute usage: Ontology indexing](https://www.palantir.com/docs/foundry/ontologies/compute-usage/) (M), maker, Palantir Technologies, accessed 2026-09-24
40. [Ontology volume usage](https://www.palantir.com/docs/foundry/ontologies/volume-usage/) (M), maker, Palantir Technologies, accessed 2026-09-24
41. [The Ontology system (Architecture center)](https://www.palantir.com/docs/foundry/architecture-center/ontology-system/) (M), maker, Palantir Technologies, accessed 2026-09-24
42. [Interoperability (Architecture center)](https://www.palantir.com/docs/foundry/architecture-center/interoperability/) (M), maker, Palantir Technologies, accessed 2026-09-24
43. [Export, edit, and import an Ontology](https://www.palantir.com/docs/foundry/ontology-manager/export-import/) (M), maker, Palantir Technologies, accessed 2026-09-24
44. [Ontology SDK (OSDK)](https://www.palantir.com/docs/foundry/ontology-sdk/overview/) (M), maker, Palantir Technologies, accessed 2026-09-24
45. [Unsupported types in OSDK](https://www.palantir.com/docs/foundry/ontology-sdk/unsupported-types/) (M), maker, Palantir Technologies, accessed 2026-09-24
46. [TypeScript OSDK](https://www.palantir.com/docs/foundry/ontology-sdk/typescript-osdk/) (M), maker, Palantir Technologies, accessed 2026-09-24
47. [API: Rate and concurrency limits](https://www.palantir.com/docs/foundry/api/general/overview/limits/) (M), maker, Palantir Technologies, accessed 2026-09-24
48. [API: Paging](https://www.palantir.com/docs/foundry/api/general/overview/paging/) (M), maker, Palantir Technologies, accessed 2026-09-24
49. [Datasets (core concepts; field types)](https://www.palantir.com/docs/foundry/data-integration/datasets/) (M), maker, Palantir Technologies, accessed 2026-09-24; the JDBC/ODBC statement in C10 is from a search summary of [ODBC and JDBC drivers for Foundry datasets](https://www.palantir.com/docs/foundry/analytics-connectivity/odbc-jdbc-drivers/) (S)
50. [Product Q&A: Ontology](https://www.palantir.com/docs/foundry/questions-answers/ontology/) (M), maker, Palantir Technologies, entries timestamped 2024-03-07 to 2025-05-13, accessed 2026-09-24
51. [Configure derived properties [Beta]](https://www.palantir.com/docs/foundry/object-link-types/derived-properties/) (M), maker, Palantir Technologies, accessed 2026-09-24
52. [Edit-only properties](https://www.palantir.com/docs/foundry/object-link-types/edit-only-properties/) (M), maker, Palantir Technologies, accessed 2026-09-24
53. [Use value types](https://www.palantir.com/docs/foundry/object-link-types/use-value-type/) (M), maker, Palantir Technologies, accessed 2026-09-24
54. [PropertyValue (API model)](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/PropertyValue.md) (A), maker, Palantir Technologies, accessed 2026-09-24
55. [ObjectPropertyType (API model)](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/ObjectPropertyType.md) (A), maker, Palantir Technologies, accessed 2026-09-24
56. [DecimalType (API model)](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Core/models/DecimalType.md) (A), maker, Palantir Technologies, accessed 2026-09-24
57. API models [ObjectTypeV2](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/ObjectTypeV2.md), [PropertyV2](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/PropertyV2.md), [OntologyObjectV2](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/OntologyObjectV2.md) (A), maker, Palantir Technologies, accessed 2026-09-24
58. API models [LinkTypeSideV2](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/LinkTypeSideV2.md), [LinkTypeSideCardinality](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/LinkTypeSideCardinality.md) (A), maker, Palantir Technologies, accessed 2026-09-24
59. API models [ObjectSet](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/ObjectSet.md), [ObjectSetSearchAroundType](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/ObjectSetSearchAroundType.md), [LoadObjectSetRequestV2](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/LoadObjectSetRequestV2.md) (A), maker, Palantir Technologies, accessed 2026-09-24
60. API models [SearchJsonQueryV2](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/SearchJsonQueryV2.md), [IsNullQueryV2](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/IsNullQueryV2.md) (A), maker, Palantir Technologies, accessed 2026-09-24
61. [OntologyObjectSet endpoints (load, loadLinks, aggregate)](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/OntologyObjectSet.md) (A), maker, Palantir Technologies, accessed 2026-09-24
62. [OntologyObject endpoints (list, search, aggregate)](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/OntologyObject.md) (A), maker, Palantir Technologies, accessed 2026-09-24
63. [Action endpoints (apply, applyBatch)](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/Action.md) (A), maker, Palantir Technologies, accessed 2026-09-24
64. [ObjectType endpoints (editsHistory)](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/ObjectType.md) and [ObjectTypeEditsHistoryResponse](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/ObjectTypeEditsHistoryResponse.md) (A), maker, Palantir Technologies, accessed 2026-09-24
65. [OntologyTransaction endpoint (Private Beta)](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/OntologyTransaction.md) (A), maker, Palantir Technologies, accessed 2026-09-24
66. [SqlQuery endpoints (execute, executeOntology)](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/SqlQueries/SqlQuery.md) (A), maker, Palantir Technologies, accessed 2026-09-24
67. API models [NullabilityPropertyTypeDataConstraint](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/NullabilityPropertyTypeDataConstraint.md), [PropertyTypeDataConstraints](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/PropertyTypeDataConstraints.md) (A), maker, Palantir Technologies, accessed 2026-09-24
68. API models [ObjectTypeDatasource](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/ObjectTypeDatasource.md), [ObjectTypeDatasetDatasource](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/ObjectTypeDatasetDatasource.md), [PropertyTypeMappingInfo](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/PropertyTypeMappingInfo.md), [ObjectTypeEditsOnlyDatasource](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/ObjectTypeEditsOnlyDatasource.md) (A), maker, Palantir Technologies, accessed 2026-09-24
69. API models [InterfaceType](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/InterfaceType.md), [SharedPropertyType](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/SharedPropertyType.md), [OntologyValueType](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/OntologyValueType.md), [ValueTypeConstraint](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/ValueTypeConstraint.md) (A), maker, Palantir Technologies, accessed 2026-09-24
70. API models [AggregationExactGroupingV2](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/AggregationExactGroupingV2.md), [AggregationAccuracyRequest](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/docs/v2/Ontologies/models/AggregationAccuracyRequest.md) (A), maker, Palantir Technologies, accessed 2026-09-24
71. [foundry-platform-sdk 1.107.0 on PyPI](https://pypi.org/project/foundry-platform-sdk/) (licence Apache-2.0; uploaded 2026-09-23) and [README at tag 1.107.0](https://raw.githubusercontent.com/palantir/foundry-platform-python/1.107.0/README.md), maker, Palantir Technologies, accessed 2026-09-24
72. [`@osdk/api` 2.72.0 package (`build/types/mapping/PropertyValueMapping.d.ts`, `objectSet/ObjectSet.d.ts`)](https://registry.npmjs.org/@osdk/api/-/api-2.72.0.tgz), maker, Palantir Technologies, published 2026-09-23 (first version 2023-09-29), licence Apache-2.0, accessed 2026-09-24
73. [`@osdk/client` 2.72.0 package (`build/esm/observable/internal/compareNumericStrings.js`, `package.json`)](https://registry.npmjs.org/@osdk/client/-/client-2.72.0.tgz), maker, Palantir Technologies, published 2026-09-23, licence Apache-2.0, accessed 2026-09-24
74. [Palantir Trust and Security Portal](https://palantir.safebase.us/) (S), maker, Palantir Technologies, date not shown, accessed 2026-09-24
75. [Palantir Developer Community: "Action edit limit appears to be 25,001 objects, not the documented 10,000"](https://community.palantir.com/t/action-edit-limit-appears-to-be-25-001-objects-not-the-documented-10-000/7105) (S), community, author not shown in summary, date not shown, accessed 2026-09-24
76. [Palantir Developer Community: "Enforce idempotency and prevent concurrent Ontology Actions from overwriting each other"](https://community.palantir.com/t/enforce-idempotency-and-prevent-concurrent-ontology-actions-from-overwriting-each-other/7249) (S), community, date not shown, accessed 2026-09-24
77. [Pankaj Kumar, "Palantir Foundry Ontology: How It Works, What Problems It Solves, and Where It Falls Short"](https://badalaiworld.substack.com/p/palantir-foundry-ontology-how-it) (S), independent, Badal AI World (also in Towards AI), May 2026 per summary, accessed 2026-09-24
78. [BD Emerson, "The Palantir Ontology, Explained: Objects, Links, and Actions"](https://www.bdemerson.com/article/palantir-ontology-explained) (S), vendor (a consultancy that also publishes Palantir FedStart advisory material), August 2026 per summary, accessed 2026-09-24
79. [CNBC, "Palantir (PLTR) earnings Q2 2026"](https://www.cnbc.com/2026/08/03/palantir-pltr-earnings-q2-2026.html) (S), independent, CNBC, published 2026-08-03, accessed 2026-09-24
80. [Palantir Technologies Inc., Form 10-Q for the quarter ended 2026-06-30](https://www.sec.gov/Archives/edgar/data/0001321655/000132165526000041/pltr-20260630.htm) (S), maker, Palantir Technologies, accessed 2026-09-24
81. [JeremyMeissner/palantir-docs](https://github.com/JeremyMeissner/palantir-docs), community (an unaffiliated mirror of palantir.com/docs as Markdown with `source_url` front matter; `urls.txt` lists 5,000 crawled URLs; capture date not shown), read at `https://raw.githubusercontent.com/JeremyMeissner/palantir-docs/main/`, accessed 2026-09-24
82. [PostgreSQL 18 documentation source: JSON Types (`doc/src/sgml/json.sgml`)](https://raw.githubusercontent.com/postgres/postgres/REL_18_STABLE/doc/src/sgml/json.sgml), maker (of PostgreSQL), PostgreSQL Global Development Group, branch REL_18_STABLE, accessed 2026-09-24
83. [PostgreSQL 18 documentation source: Data Types (`datatype.sgml`)](https://raw.githubusercontent.com/postgres/postgres/REL_18_STABLE/doc/src/sgml/datatype.sgml), maker (of PostgreSQL), PostgreSQL Global Development Group, accessed 2026-09-24
84. [PostgreSQL 18 documentation source: Collation Support (`charset.sgml`)](https://raw.githubusercontent.com/postgres/postgres/REL_18_STABLE/doc/src/sgml/charset.sgml), maker (of PostgreSQL), PostgreSQL Global Development Group, accessed 2026-09-24
85. [PostgreSQL 18 documentation source: INSERT (`ref/insert.sgml`)](https://raw.githubusercontent.com/postgres/postgres/REL_18_STABLE/doc/src/sgml/ref/insert.sgml), maker (of PostgreSQL), PostgreSQL Global Development Group, accessed 2026-09-24
86. [PostgreSQL 18 documentation source: Concurrency Control (`mvcc.sgml`)](https://raw.githubusercontent.com/postgres/postgres/REL_18_STABLE/doc/src/sgml/mvcc.sgml), maker (of PostgreSQL), PostgreSQL Global Development Group, accessed 2026-09-24
87. [PostgreSQL 18 documentation source: Queries, WITH RECURSIVE (`queries.sgml`)](https://raw.githubusercontent.com/postgres/postgres/REL_18_STABLE/doc/src/sgml/queries.sgml), maker (of PostgreSQL), PostgreSQL Global Development Group, accessed 2026-09-24
88. [PostgreSQL 18 documentation source: Indexes (`indices.sgml`)](https://raw.githubusercontent.com/postgres/postgres/REL_18_STABLE/doc/src/sgml/indices.sgml), maker (of PostgreSQL), PostgreSQL Global Development Group, accessed 2026-09-24
89. [PostgreSQL COPYRIGHT (licence text)](https://raw.githubusercontent.com/postgres/postgres/REL_18_STABLE/COPYRIGHT), maker (of PostgreSQL), PostgreSQL Global Development Group, accessed 2026-09-24
90. [node-pg-types README](https://raw.githubusercontent.com/brianc/node-pg-types/master/README.md) and [`lib/textParsers.js`](https://raw.githubusercontent.com/brianc/node-pg-types/master/lib/textParsers.js), community (node-postgres driver project), master branch (version not pinned), accessed 2026-09-24
91. [Neo4j Cypher Manual source: Property, structural, and constructed values](https://raw.githubusercontent.com/neo4j/docs-cypher/dev/modules/ROOT/pages/values-and-types/property-structural-constructed.adoc), maker (of Neo4j), Neo4j, dev branch (version not pinned), accessed 2026-09-24
92. [Neo4j Cypher Manual source: SET (remove a property)](https://raw.githubusercontent.com/neo4j/docs-cypher/dev/modules/ROOT/pages/clauses/set.adoc), maker (of Neo4j), Neo4j, dev branch, accessed 2026-09-24
93. [Neo4j Cypher Manual source: Constraints](https://raw.githubusercontent.com/neo4j/docs-cypher/dev/modules/ROOT/pages/schema/constraints/index.adoc), maker (of Neo4j), Neo4j, dev branch, accessed 2026-09-24
94. [Neo4j Cypher Manual source: MERGE](https://raw.githubusercontent.com/neo4j/docs-cypher/dev/modules/ROOT/pages/clauses/merge.adoc), maker (of Neo4j), Neo4j, dev branch, accessed 2026-09-24
95. [Neo4j Cypher Manual source: Indexes](https://raw.githubusercontent.com/neo4j/docs-cypher/dev/modules/ROOT/pages/indexes/index.adoc), maker (of Neo4j), Neo4j, dev branch, accessed 2026-09-24
96. [Neo4j JavaScript driver README](https://raw.githubusercontent.com/neo4j/neo4j-javascript-driver/5.0/README.md), maker (of Neo4j), Neo4j, 5.0 branch, accessed 2026-09-24
97. [Neo4j LICENSE.txt](https://raw.githubusercontent.com/neo4j/neo4j/dev/LICENSE.txt), maker (of Neo4j), Neo4j Sweden AB, accessed 2026-09-24
98. [Sqlg README](https://raw.githubusercontent.com/pietermartin/sqlg/master/README.md), maker (of Sqlg), Pieter Martin / Sqlg project, master branch, accessed 2026-09-24
99. [Sqlg CHANGELOG](https://raw.githubusercontent.com/pietermartin/sqlg/master/CHANGELOG.md), maker (of Sqlg), Sqlg project, master branch (latest entry 3.1.6), accessed 2026-09-24
100. [PostgreSQL 18 documentation source: Data Definition, Constraints (`ddl.sgml`)](https://raw.githubusercontent.com/postgres/postgres/REL_18_STABLE/doc/src/sgml/ddl.sgml), maker (of PostgreSQL), PostgreSQL Global Development Group, accessed 2026-09-24

**Searched**: All on 2026-09-24 and 2026-09-25. Hosts blocked by the egress proxy
(403 on CONNECT, or `EGRESS_BLOCKED` in the fetch tool): www.palantir.com,
palantir.com, blog.palantir.com, community.palantir.com, learn.palantir.com,
palantir.safebase.us, web.archive.org, archive.ph, r.jina.ai, github.com (HTML),
gist.githubusercontent.com, medium.com, substack.com hosts, bdemerson.com,
puppygraph.com, labhub.hopto.org, elementum.ai, engineering.fyi, CNBC, Yahoo
Finance, qz.com, sec.gov, arxiv.org, en.wikipedia.org, neo4j.com, sqlg.org and
www.postgresql.org. Reachable: raw.githubusercontent.com, registry.npmjs.org and
pypi.org. The GitHub MCP tools were scoped to the umf and truss repositories and
were not used for Palantir repositories. Web searches: "Palantir Foundry
'Object Storage V2' OSv2 Phonograph" and "palantir.com docs foundry
object-backend overview" (terminology, OSv1 deprecation; confirmed from [1][10]);
"Breaking changes between OSv1 and OSv2 primary key duplicate"; "Object Data
Funnel indexing pipelines"; "object-indexing data-restrictions"; "property base
types decimal byte struct vector"; "how user edits are applied conflict
resolution"; "action types scale and property limits" (found [75]); "OSv2
maximum number of properties per object type 2000"; "search around limit
100,000"; "Object Storage v2 tens of billions"; "multi-datasource object types
column-level permissions"; "Manage schema changes"; "actions concurrent edits
atomic optimistic"; "architecture center ontology system Change Data Capture";
"Ontology SQL"; "Ontology query compute usage"; "link types many-to-many join
table"; "interfaces shared property types"; "value types constraints"; "Make
Value Type constraints more useful in action types"; "value type constraints
enforced indexing"; "structs struct property limits"; "object security policies
property security policies"; "Funnel streaming pipelines latency";
"materializations"; "Enable user edit history"; "Phonograph limitations full
reindex"; "Managing Elasticsearch Reindex at Scale Phonograph" and "Phonograph
Elasticsearch" (no maker statement ties OSv1 or OSv2 to a named engine, so the
object database engine is Not published); "Q2 2026 earnings customer count"
(found [79][80]); "Foundry FedRAMP SOC 2 ISO 27001 IL6" (found [74]); "Foundry
pricing compute-seconds AWS Marketplace" (no maker price list, so the price is
Not published); "blog.palantir.com Ontology Object Storage"; "Ontology-Oriented
Software Development"; "OSv2 independent review" and "ontology criticism hacker
news reddit" (no independent OSv2-specific critique found beyond [77]);
"'Palantir Foundry Ontology ... Where It Falls Short'" (found [77]);
"bdemerson palantir ontology explained" (found [78]); "size limits on individual
properties"; "cannot be used as primary keys"; "property metadata limited support
decimal" (the live page repeats the decimal statement in [17]); "palantir
ontology decimal OSv2 precision scale"; "StaleObject concurrent edits OSv2"
(found [76]); "Enforce idempotency ... overwriting each other" (answers not
visible); "palantir osv2 benchmark latency", "palantir ontology performance
p95", "object storage v2 query latency" (nothing, so C12 is Unknown);
"palantir vulnerability disclosure foundry" (nothing, so Security process is Not
published); "sqlg.org supported data types" and "sqlg unique index constraint
multiplicity" (Sqlg C2, C5, C7 and C8 cells stay Not researched because sqlg.org
was blocked and the changelog does not settle them). Neo4j C5 planner use, C12,
and option A and C cells marked Not researched were not searched further. The
Apache AGE row was left to the sibling profile, as instructed.

## Review Checklist

Ticked by a named reviewer, recorded on the line; an author ticking their own
boxes is a draft.

Reviewed by: *unreviewed* (author self-check only)

- [x] Need and Required Capabilities cite project artifacts only; no `[n]` appears in them
- [x] Every required capability has a "Settled by" line and a status from How to Read This Profile
- [x] Every claim cites at the clause or is marked Not published (with the search) or Not researched (with the sibling profile)
- [x] Every figure carries a label, and every mutable fact an as-of date
- [x] The verdict follows the definitions in How to Read This Profile
- [x] The Competitive Landscape scores every named alternative on the same capabilities
- [x] The confidence grade follows the rubric; a design-defining Unknown caps it at Medium
- [x] Every source carries class, author or organisation, publication date where shown, and access date; scoped-version docs are version-pinned (Palantir docs are unversioned living pages; the API reference is pinned to tag 1.107.0; the Neo4j, Sqlg and node-pg-types sources are unpinned branches and flagged)
- [x] No benchmark, prototype, or integration result is claimed
- [x] No owner, date, duration, or figure appears that a project artifact does not state
- [x] No choice among candidates is made here
