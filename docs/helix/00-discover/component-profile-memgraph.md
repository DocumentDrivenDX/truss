---
ddx:
  id: truss.component-profile-memgraph
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

# Component Profile: Memgraph

Desk research on Memgraph, the in-memory, Cypher-compatible property-graph
database, as a system teams adopt when they move connected data out of
PostgreSQL, measured against the capabilities truss needs from a graph
storage and query layer. This is research. The choice between building
truss and adopting an existing system lives in a later decision record
that cites the profiles; anything the public record cannot settle is a
[[tech-spike]].

## Scope

- Component: Memgraph 3.13 (latest release 3.13.1 of 14 September 2026),
  Community Edition under the Memgraph Business Source Licence and
  Enterprise Edition under the Memgraph Enterprise Licence; default
  `IN_MEMORY_TRANSACTIONAL` storage mode; accessed from JavaScript through
  `neo4j-driver`, the client Memgraph documents
- Kind: Technology (with a managed provider, Memgraph Cloud, and a separate
  federated query product, MemGQL, noted but not profiled)
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
- Excluded: hands-on testing of any kind; MAGE graph algorithms, streaming,
  high availability and multi-tenancy, which no required capability names;
  Memgraph Cloud pricing and regions beyond what could be read (memgraph.com
  was blocked by the research environment's egress proxy, see Sources)

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
hand-designed schema's latency. On the public record Memgraph 3.13 meets
property indexing, retention of arbitrary maps and lists, and lossless
TypeScript access through the Neo4j driver, but it runs as its own
in-memory server, has no exact decimal or binary type, treats null as an
absent property, cannot constrain relationships, offers no SQL surface, and
ships its Community Edition under a source-available licence from a single
vendor, so the verdict is No fit, with concurrent merge semantics and
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

Memgraph is an in-memory property-graph database written in C++ that
implements the openCypher query language; its repository describes it as a
"high-performance open-source in-memory graph database for GraphRAG, AI
memory, agentic AI, and real-time graph analytics" [22], and its
documentation says it "aims to be as close as possible to the most commonly
used openCypher implementations" [3]. It is made by Memgraph Ltd, the
licensor named in its Business Source Licence [20]. Its architecture "has
been built natively for in-memory data analysis and storage", with
write-ahead logs and snapshots for durability in the default transactional
mode [7]. The Community Edition is under the Memgraph Business Source
Licence 1.1, which states that it "is not an 'open source' license", and
Enterprise features are under the Memgraph Enterprise Licence [19][20].

- Category and purpose: in-memory property-graph database, openCypher,
  ACID in the transactional storage modes [3][7]
- Maker or governing body: Memgraph Ltd; no foundation [20]
- Adoption, from an independent source: Not published (searched DB-Engines
  and the 2025 Stack Overflow Developer Survey on 2026-09-24; both hosts
  were blocked and search summaries gave no figure). Descriptively, the
  repository shows 4.6k stars as of 2026-09-24 [22].
- Release cadence and support window: minor releases roughly monthly to
  bimonthly, most recently 3.13.0 on 9 September 2026 and 3.13.1 on
  14 September 2026 [10]; support window Not published (searched the
  documentation for "LTS", "end of life" and "supported versions",
  2026-09-24)
- Licence: Business Source Licence 1.1 as amended on 1 January 2026, with
  production use limited to internal business purposes and a change to
  Apache-2.0 on a stated change date [20]
- Built-for use cases: GraphRAG, AI memory, agentic AI, real-time graph
  analytics [22]; fast in-memory import and analysis [7]

## Capability Alignment

### C1. Runs inside the user's PostgreSQL

Interpretation: C1 asks for a component that runs inside the user's
PostgreSQL; the nearest equivalent for Memgraph would be a supported way to
keep the graph in PostgreSQL storage, and none exists. Memgraph is its own
in-memory database server with its own storage modes [7]. Its managed form,
Memgraph Cloud, is "a cloud service fully managed on AWS and available in 6
geographic regions" running Enterprise instances [9]. Memgraph's separate
MemGQL product queries PostgreSQL tables in place as a federated engine
that translates GQL into each backend's native language [14][15]; it runs outside
PostgreSQL and its PostgreSQL connector cannot `SET` or `REMOVE` properties
[15].

**Settled by**: a PostgreSQL version matrix or managed-provider listing, not found; the maker documents its own server, cloud service and a federated engine [7][9][14][15] (searched the documentation for "PostgreSQL" and "extension", 2026-09-24)
**Status**: Unmet

### C2. Exact storage of nine scalar families

Supported property types are Null, String, Boolean, Integer, Float, List,
Map, Duration, Date, LocalTime, LocalDateTime, ZonedDateTime, Enum and
Point [1]. The storage engine holds integers as `int64_t` and floats as
`double`, and its property-type enumeration has no decimal or byte-string
member [21]. There is no time-of-day type with a zone; LocalTime and
LocalDateTime carry no zone, and ZonedDateTime accepts offsets or IANA
names [1]. Temporal precision is microseconds: seconds take "up to 6
digits" and durations "internally hold microseconds" [1]. The maker warns
that `tzdata` 2024b or later "will break the timezone feature in Memgraph"
[1]. Exact decimals and binary data would have to be carried as strings or
lists, which C2 exists to prevent.

**Settled by**: type-system documentation found in [1] and storage source in [21]; no exact decimal or binary type
**Status**: Unmet

### C3. Absent versus null; lists and maps

The type table defines Null as "Property has no value, which is the same as
if the property doesn't exist" [1], and setting a property to `NULL`
removes it [6]. Lists may contain "any number of property values of any
supported type" and maps map "string keys to values of any supported type"
[1], so ordered, mixed lists and string-keyed maps are storable; list and
map properties can only be replaced whole, not edited in place [1]. Whether
a null inside a stored list or map is kept is Not published (searched [1]
and [6], 2026-09-24).

**Settled by**: null semantics found in [1][6]; the absent-versus-null distinction is contradicted
**Status**: Unmet

### C4. Database-enforced rules

Memgraph offers existence, uniqueness and data-type constraints on a node
label and property [2]; none of them is in the Enterprise-only feature list
[8]. Relationship uniqueness, existence and type constraints "are **not**
supported and will raise a `SemanticException`" [3], and no rule restricting
which node labels a relationship type may connect was found (searched [2]
and [3], 2026-09-24). No range, length or pattern constraint exists in the
documented list [2]. Constraint checking is optimistic: a multi-query
transaction commits if the database satisfies the constraints after its
final query [4], and a uniqueness violation fails the commit [2]. Triggers
can run openCypher `BEFORE COMMIT` inside the triggering transaction [31],
which could implement further checks, but that is application code, not a
declared constraint. How uniqueness compares an Integer and an equal Float
is Not published (searched [1][2], 2026-09-24).

**Settled by**: constraint documentation found in [2][3][4][8]; relationship and endpoint rules contradicted by [3]
**Status**: Unmet

### C5. Property indexes used by the planner

Label-property indexes speed up matches on a label and property, including
`WHERE` equality filters, though a complicated expression may keep the index
from being used [5]. Range predicates such as `WHERE n.age > 30` use
ascending or descending label-property indexes [5], and edge-type property
indexes, composite indexes, index hints and `ANALYZE GRAPH` statistics are
documented [5]. Indexes are not created automatically, and a uniqueness
constraint does not create one [5][2]. No independent source examining
Memgraph plans was found.

**Settled by**: indexing documentation found in [5]; independent plan reports not found (searched "Memgraph label property index query plan", 2026-09-24)
**Status**: Met

### C6. Graph reads and writes that compose with SQL

Interpretation: the Cypher half of C6 is judged on openCypher; the SQL half
asks for joins with relational tables and use inside SQL statements, whose
nearest equivalent for a non-SQL database would be a documented SQL
interface over the graph. Memgraph implements openCypher with `MERGE` [17],
variable-length and built-in deep-path traversals (BFS, DFS, weighted and
K shortest paths) [3][18], and documents differences from Neo4j: no
fixed-length quantified pattern (`--{2}`) and no `NOT` label expression,
each with a workaround [3]. No SQL interface to Memgraph data was found
(searched the documentation for "SQL", 2026-09-24); MemGQL runs GQL against
PostgreSQL tables from outside PostgreSQL, the opposite direction [15].

**Settled by**: openCypher coverage and differences found in [3][17][18]; SQL composition not found
**Status**: Unmet

### C7. Defined behaviour under concurrency

Interpretation: C7's "PostgreSQL's standard isolation levels" is read as
the candidate's documented isolation levels plus a documented way to
prevent lost updates. The default is snapshot isolation: a transaction
"will successfully commit only if no updates it has made conflict with any
concurrent updates made since that snapshot"; read committed and read
uncommitted are also offered, and the maker's own table shows write skew
(G2-item) is prevented at no level [4]. Write-write conflicts surface as
serialization errors that clients must retry [13]. The analytical storage
mode "offers no isolation levels and no ACID guarantees" [4][7]. Concurrent
`MERGE` of the same pattern is not described in the `MERGE` or transaction
pages (searched [4][13][17], 2026-09-24), so whether two concurrent merges
yield one node, one serialization error or two nodes without a uniqueness
constraint is not settled.

**Settled by**: isolation and conflict behaviour found in [4][13]; concurrent merge semantics not found
**Status**: Unknown

### C8. Retains unmodelled data unchanged

Memgraph has no required schema: "There are **no restrictions on the
number of properties**" on a graph element, and values need only be of a
supported type [1]. Maps of string keys to values of any supported type and
lists of any supported values are storable [1], and label-property indexes
can reach properties nested in map properties [5]. Exactness of the values
themselves is bounded by the type system assessed under C2.

**Settled by**: storage of arbitrary maps and lists found in [1][5]
**Status**: Met

### C9. TypeScript without precision loss

Memgraph's Node.js guide installs the Neo4j JavaScript driver
(`npm i neo4j-driver`) and requires "any LTS version of Node.js" [11]; its
JavaScript example output shows identities as driver `Integer` objects
(`Integer { low: 106, high: 0 }`) [12]. That driver represents 64-bit
integers with its own `Integer` type, treats JavaScript numbers passed as
parameters as floats, and writes large integers through `neo4j.int` from a
string [24]; its `useBigInt` option returns native `BigInt` [25]. Driver
6.2.0 is Apache-2.0 [26]. Memgraph publishes nothing about Bun (searched
[11][12], 2026-09-24).

**Settled by**: client documentation found in [11][12] and driver documentation in [24][25]
**Status**: Met

### C10. Readable through plain SQL

Interpretation: the nearest equivalent is a maker-supported SQL surface
with conversions from graph values to SQL types. Memgraph's query language
is openCypher [3], its data lives in its own in-memory storage [7], and no
SQL interface or cast layer to SQL types was found (searched the
documentation for "SQL", 2026-09-24).

**Settled by**: not found (searched [3][7] and the documentation tree, 2026-09-24)
**Status**: Unmet

### C11. Sustainable dependency

The Community Edition licence, amended 1 January 2026, grants production
use "solely for any Authorised Purpose": internal business purposes,
provided the user does not embed or distribute it to third parties, host
it for third parties as a database service, or "create a work or solution
which competes (or might reasonably be expected to compete)" with it; the
licence converts to Apache-2.0 on a change date written as "2030-14-09"
[20]. The licence text says it "is not an 'open source' license" [20],
while the repository description calls Memgraph "open-source" [22].
Enterprise features are under the Memgraph Enterprise Licence [19][8].
Releases are frequent [10]; the public repository shows 831 commits by 20
distinct author names in the twelve months to 2026-09-24 (Counted) [23].
Governance is a single vendor with no foundation found (searched [19][20][22],
2026-09-24).

**Settled by**: licence text [19][20], release history [10] and contributor count [23] found; an open licence and open governance are contradicted by [20]
**Status**: Unmet

### C12. Latency within twice a hand-designed schema

No independent benchmark comparing Memgraph with a hand-designed relational
schema at the 95th percentile on comparable workloads was found. The
community graph-bench harness, whose author also builds a rival engine,
reports Memgraph 3.10.0 medians of 528.7 µs for a point read and 776.5 µs
for a three-hop expansion on a 10,000-node grid, over Bolt on a host at
load average 37, and says those columns "mostly measure a round trip, a
driver and a planner" [27]. The same README prints no PostgreSQL figures
for that host and warns against comparing across tables [27].

**Settled by**: an independent comparable benchmark, not found (searched "experimental evaluation graph database systems Neo4j Memgraph Kuzu PostgreSQL VLDB paper 2024 2025 benchmark", 2026-09-24); community numbers in [27]
**Status**: Unknown

Other notable capabilities the record documents and no criterion requires:

| Capability | What the record says | Source |
|------------|----------------------|--------|
| Row-level security (nice to have) | Role-, label- and property-based access control are Enterprise Edition features | [8] |
| Shortest paths (nice to have) | Built-in BFS, weighted shortest path, all shortest paths and K shortest paths in pattern syntax | [3][18] |
| GQL alignment (nice to have) | Memgraph itself publishes no GQL conformance statement (searched [3], 2026-09-24); MemGQL, a separate product, accepts ISO-standard GQL and translates it for backends including PostgreSQL | [14][15] |
| Federated reads over PostgreSQL | MemGQL 0.12.0 (14 Sep 2026) supports `MATCH`, bounded quantified paths, aggregation, `INSERT` and `DELETE` against PostgreSQL, not `SET`, `REMOVE` or shortest paths; MemGQL Community is free of charge "without any official support obligations" | [15][16][32] |
| Triggers | openCypher triggers run before commit inside the transaction or asynchronously after commit | [31] |
| Storage modes | In-memory transactional (default), in-memory analytical (no ACID), and on-disk transactional, which is "still in the experimental phase" | [7] |
| Enterprise-only | High availability with automatic failover, multi-tenancy, audit log, time-to-live, parallel execution | [8] |

**Verdict**: No fit. C1 is Unmet because Memgraph is its own in-memory
server, and C2, C3, C4, C6, C10 and C11 are Unmet on the maker's own
statements; C7 and C12 are Unknown and would not change the verdict.

## Technology and Operations

| Aspect | What the record says | Source |
|--------|----------------------|--------|
| Hosting model | Self-hosted server; Memgraph Cloud is fully managed on AWS in 6 regions with Enterprise instances up to 32 GB RAM and 8 cores (as of 2026-09-24) | [9] |
| Integrations | Bolt protocol; Neo4j drivers (JavaScript through `neo4j-driver`); MemGQL federation to PostgreSQL and other stores | [11][14][15] |
| Data handling | In-memory storage persisted through write-ahead logs and snapshots in the transactional mode; encryption at rest Not published in pages read (searched [7][9], 2026-09-24) | [7] |
| Certifications | Not published (searched "Memgraph security vulnerability reporting policy SOC 2 certification", 2026-09-24; the summary named no certification) | none |
| Maturity and cadence | 3.0.0 on 29 Jan 2025; 3.13.1 on 14 Sep 2026; minor releases every one to two months | [10] |
| Governance | Single vendor, Memgraph Ltd | [20] |
| Security process | Search summary only: a disclosure policy asks for reports to security@memgraph.io with acknowledgement in 3 business days (page not read); no SECURITY.md in the repository (checked 2026-09-24) | [28] |

## Pricing and Licensing

| Item | Figure | Label | Source |
|------|--------|-------|--------|
| Licence, Community Edition | Memgraph BSL 1.1 as amended 1 Jan 2026: internal production use only; no embedding or distribution to third parties, no database service, no competing work; converts to Apache-2.0 on the change date | Published | [20] |
| Licence, Enterprise Edition | Memgraph Enterprise Licence | Published | [19] |
| Enterprise price | Not published in any page read (memgraph.com/pricing blocked, 2026-09-24); a search summary attributes a starting price of USD 25,000 per year for 16 GB of memory to that page, unverified | Not published | [29] |
| Memgraph Cloud price | Not published (searched [9] and "Memgraph Cloud pricing", 2026-09-24) | Not published | none |
| JavaScript driver | Apache-2.0 (the Neo4j driver) | Published | [26] |

## Competitive Landscape

Cells for Neo4j and LadybugDB come from this author's research for their
sibling profiles; other rows were not researched here. Sibling slugs other
than the three written with this profile are provisional.

| Candidate | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | Profile |
|-----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|---------|
| Memgraph 3.13 | Unmet: own server [7][9] | Unmet: no decimal or bytes [1][21] | Unmet: null equals absent [1] | Unmet: node-only constraints [2][3] | Met [5] | Unmet: no SQL composition [3] | Unknown: merge semantics undocumented [4] | Met [1] | Met [11][24] | Unmet [3] | Unmet: BSL 1.1 [20] | Unknown [27] | this profile |
| Apache AGE | Unknown† | Unmet† | Unmet† | Unknown† | Unknown† | Met† | Unknown† | Met† | Unknown† | Met† | Unknown† | Unknown† | [[component-profile-apache-age]] |
| Palantir OSv2 | Unmet† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-palantir-osv2]] |
| Sqlg | Unknown† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unknown† | Unmet† | Unmet† | Met† | Unmet† | Unknown† | [[component-profile-sqlg]] |
| PuppyGraph | Unmet† | Unknown† | Unknown† | Unmet† | Unknown† | Unmet† | Unmet† | Unmet† | Unknown† | Met† | Unmet† | Unknown† | [[component-profile-puppygraph]] |
| Gel | Unmet† | Unknown† | Unmet† | Met† | Met† | Unmet† | Met† | Unmet† | Met† | Met† | Unmet† | Unknown† | [[component-profile-gel]] |
| Neo4j 2026.09 (CE/EE) | Unmet: own server [37] | Unmet: no decimal [33] | Unmet: no null or map properties [33][34] | Unmet: limits absent; most rules EE-only [35][37] | Met [36] | Unmet: limited SQL translation only [39] | Met [38] | Unmet: maps not storable [33] | Met [24][25] | Unmet [39] | Unmet: single vendor, CLA [40] | Unknown [27] | [[component-profile-neo4j]] |
| LadybugDB 0.20 | Unmet: embedded engine; pg_ladybug reads only [41][47] | Unmet: no time type; offset dropped [42] | Unmet: missing values are NULL [43] | Unmet: primary key and endpoints only [43][44] | Unmet: no property indexes [44] | Unmet [44][47] | Met: single writer, serializable [45] | Unknown | Unmet: INT64 to JS Number [46] | Unmet [47] | Unmet: one dominant maintainer [48] | Unknown [27] | [[component-profile-ladybugdb]] |
| Datomic | Unmet† | Unmet† | Unmet† | Unmet† | Met† | Unmet† | Met† | Unmet† | Unknown† | Unmet† | Unmet† | Unknown† | [[component-profile-datomic]] |
| XTDB | Unmet† | Unknown† | Unknown† | Unmet† | Unmet† | Unmet† | Met† | Met† | Unknown† | Met† | Unmet† | Unknown† | [[component-profile-xtdb]] |
| SurrealDB | Unmet† | Unmet† | Met† | Unknown† | Met† | Unmet† | Met† | Met† | Met† | Unmet† | Unmet† | Unknown† | [[component-profile-surrealdb]] |
| UMF-generated per-type PostgreSQL tables | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | *none yet* |
| JSONB plus expression indexes | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | Not researched | *none yet* |

† Status copied on 2026-09-25 from the sibling profile named in the Profile column, where the evidence and sources are recorded.

- Apache AGE: shares openCypher; the divergence truss cares about is that
  AGE runs inside PostgreSQL. Not researched here; the project's
  competitive analysis records it as an openCypher PostgreSQL extension
  ([[truss.competitive-analysis]] Competitor Profiles).
- Palantir OSv2: Not researched here; see its sibling profile.
- Sqlg: Not researched here; the competitive analysis records a Gremlin
  layer over relational databases ([[truss.competitive-analysis]]).
- PuppyGraph: Not researched here; like MemGQL [14], the competitive
  analysis records graph reads over existing SQL tables
  ([[truss.competitive-analysis]]).
- Gel: Not researched here; see its sibling profile.
- Neo4j: shares Cypher, Bolt and the JavaScript driver [11][24]; it
  diverges by an Enterprise graph-type schema with relationship endpoint
  rules [49], read-committed isolation with lock-based merge guarantees
  [38], no map properties [33], and a GPLv3 Community Edition [40].
- LadybugDB: shares the Cypher family; it diverges by an embedded,
  schema-first engine with exact `DECIMAL` and declared relationship
  endpoints [42][43], and by an early PostgreSQL extension that reads
  PostgreSQL tables [47].
- Datomic, XTDB, SurrealDB: Not researched here; see their sibling profiles.
- UMF-generated per-type tables and JSONB with expression indexes: Not
  researched; no sibling profile exists yet.

## Confidence

| Grade | Means |
|-------|-------|
| **High** | Every design-defining claim is corroborated by the maker's material *and* at least one independent source, and no design-defining capability is Unknown. |
| **Medium** | Design-defining claims rest on the maker alone, or a design-defining capability is Unknown, or the independent coverage is older than two major versions. |
| **Low** | Thin public footprint; claims rest on one source or on none. |

**Grade**: Medium. The deciding claims, that Memgraph is its own server
(C1), lacks decimal and binary types and equates null with absence (C2,
C3), cannot constrain relationships (C4), and ships under a restrictive
BSL (C11), rest on the maker's documentation, source code and licence text
[1][2][3][7][20][21], read from version-pinned sources on GitHub because
memgraph.com was blocked. The type-system claim is corroborated within the
maker's record by both documentation [1] and storage source [21]; a search
summary of an ArcadeDB (rival vendor) article agrees on the BSL
restrictions but was not read [30]. Nothing independent measures C12; the only
cross-engine numbers are a community harness by a rival engine's author
[27]. Weakest area: concurrent merge semantics (C7) and anything on
memgraph.com (pricing, certifications, disclosure policy), which could not
be read.

## Open Questions

| # | Question | Design-defining because | Route |
|---|----------|-------------------------|-------|
| 1 | Under snapshot isolation, what do two concurrent `MERGE` statements for the same node pattern produce, with and without a uniqueness constraint? | Defined merge behaviour is part of C7; truss's `sql-exactness` concern requires an explicit isolation strategy for cross-row rules | ask maker, then [[tech-spike]] |
| 2 | On truss's benchmark corpus, what p95 does Memgraph reach for single-object fetch and one-to-three-hop traversal, relative to a hand-designed PostgreSQL schema? | The competitive analysis tells truss not to compete on raw traversal speed with native graph databases; a measured baseline shows the size of that gap | [[tech-spike]] (the benchmark [[truss.vision-input]] asks for) |
| 3 | Would the Business Source Licence's "competes (or might reasonably be expected to compete)" clause affect an organisation that runs truss beside Memgraph, or truss itself if it ever interoperates with Memgraph? | Licence terms decide whether Memgraph can even serve as a comparison or migration target in truss tooling | operator guidance (legal review) |

## Sources

Classes: **maker** (the component's maker or governing body), **vendor** (a
company selling hosting or support for the component or a rival),
**independent** (no commercial interest; named author or organisation and a
date), **community** (a project or forum around the component). Memgraph
documentation was read from the maker's documentation source on GitHub at
commit 7d85d48 (23 Sep 2026) because memgraph.com was blocked by the
research environment's egress proxy; the same applies to Neo4j sources.

1. [Data types, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/data-types.mdx), maker, Memgraph, commit of 23 Sep 2026, accessed 24 Sep 2026
2. [Constraints, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/constraints.mdx), maker, Memgraph, accessed 24 Sep 2026
3. [Differences in Cypher implementations, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/querying/differences-in-cypher-implementations.mdx), maker, Memgraph, accessed 24 Sep 2026
4. [Transactions (isolation levels, optimistic constraint checking), Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/transactions.mdx), maker, Memgraph, accessed 24 Sep 2026
5. [Indexes, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/indexes.mdx), maker, Memgraph, accessed 24 Sep 2026
6. [SET clause, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/querying/clauses/set.md), maker, Memgraph, accessed 24 Sep 2026
7. [Storage memory usage (storage modes), Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/storage-memory-usage.mdx), maker, Memgraph, accessed 24 Sep 2026
8. [Enabling Memgraph Enterprise (Enterprise-only features), Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/database-management/enabling-memgraph-enterprise.mdx), maker, Memgraph, accessed 24 Sep 2026
9. [Memgraph Cloud, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/getting-started/install-memgraph/memgraph-cloud.mdx), maker, Memgraph, accessed 24 Sep 2026
10. [Release notes, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/release-notes.mdx), maker, Memgraph, latest entry 3.13.1 of 14 Sep 2026, accessed 24 Sep 2026
11. [Node.js client, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/client-libraries/nodejs.mdx), maker, Memgraph, accessed 24 Sep 2026
12. [JavaScript client, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/client-libraries/javascript.mdx), maker, Memgraph, accessed 24 Sep 2026
13. [Transaction errors (conflicting transactions), Memgraph help center, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/help-center/errors/transactions.mdx), maker, Memgraph, accessed 24 Sep 2026
14. [Memgraph Zero (MemGQL overview), Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/memgraph-zero.mdx), maker, Memgraph, accessed 24 Sep 2026
15. [MemGQL: Connect to PostgreSQL (supported GQL features), Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/memgraph-zero/memgql/connect/postgres.mdx), maker, Memgraph, accessed 24 Sep 2026
16. [MemGQL licensing, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/memgraph-zero/memgql/licensing.mdx), maker, Memgraph, accessed 24 Sep 2026
17. [MERGE clause, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/querying/clauses/merge.mdx), maker, Memgraph, accessed 24 Sep 2026
18. [Deep-path traversal, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/advanced-algorithms/deep-path-traversal.mdx), maker, Memgraph, accessed 24 Sep 2026
19. [LICENSE, memgraph/memgraph at 6a80124](https://github.com/memgraph/memgraph/blob/6a80124060482583e72610fa268f8a442c0d830c/LICENSE), maker, Memgraph Ltd, commit of 24 Sep 2026, accessed 24 Sep 2026
20. [Memgraph Business Source License 1.1, as amended 1 Jan 2026, memgraph/memgraph at 6a80124](https://github.com/memgraph/memgraph/blob/6a80124060482583e72610fa268f8a442c0d830c/licenses/BSL.txt), maker, Memgraph Ltd, amended 1 Jan 2026, accessed 24 Sep 2026
21. [`src/storage/v2/property_value.cppm`, memgraph/memgraph at 6a80124](https://github.com/memgraph/memgraph/blob/6a80124060482583e72610fa268f8a442c0d830c/src/storage/v2/property_value.cppm), maker, Memgraph Ltd, accessed 24 Sep 2026
22. [memgraph/memgraph repository page](https://github.com/memgraph/memgraph), maker, Memgraph Ltd, 4.6k stars and repository description as shown, accessed 24 Sep 2026
23. [memgraph/memgraph commit history, branch master](https://github.com/memgraph/memgraph/commits/master), maker, Memgraph Ltd, Counted by the author from `git log --since=2025-09-24` on 24 Sep 2026 (831 commits, 20 distinct author names), accessed 24 Sep 2026
24. [neo4j-javascript-driver README, Numbers and the Integer type, 6.x at 6453219](https://github.com/neo4j/neo4j-javascript-driver/blob/6453219576098a71c8deaf1493a136f5230370c5/README.md), maker (of the driver), Neo4j, commit of 10 Sep 2026, accessed 24 Sep 2026
25. [neo4j-javascript-driver `packages/core/src/types.ts` (useBigInt), 6.x at 6453219](https://github.com/neo4j/neo4j-javascript-driver/blob/6453219576098a71c8deaf1493a136f5230370c5/packages/core/src/types.ts), maker (of the driver), Neo4j, accessed 24 Sep 2026
26. [neo4j-driver package metadata, npm registry](https://registry.npmjs.org/neo4j-driver), maker (of the driver), Neo4j, version 6.2.0 published 30 Jun 2026, accessed 24 Sep 2026
27. [graph-bench README at 89ff1c7](https://github.com/tamnd/graph-bench/blob/89ff1c7989e9cf401fcbbb70ca1c60fc4d6f2eaf/README.md), community, tamnd (who also develops the rival `zu` engine), measurements dated 12 to 22 Aug 2026, accessed 24 Sep 2026
28. [Memgraph vulnerability disclosure policy](https://memgraph.com/policies/disclosure), maker, Memgraph, Search summary only (host blocked; page not read), accessed 24 Sep 2026
29. [Memgraph pricing](https://memgraph.com/pricing), maker, Memgraph, host blocked; Search summary only, accessed 24 Sep 2026
30. [Neo4j Alternatives in 2026: A Fair Look at the Open-Source Options](https://arcadedb.com/blog/neo4j-alternatives-in-2026-a-fair-look-at-the-open-source-options/), vendor (rival database maker), ArcadeDB, Search summary only (host blocked; page not read), accessed 24 Sep 2026
31. [Triggers, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/fundamentals/triggers.mdx), maker, Memgraph, accessed 24 Sep 2026
32. [MemGQL changelog, Memgraph documentation, documentation@7d85d48](https://github.com/memgraph/documentation/blob/7d85d4838167b5193cfa402176f24d744745e5ae/pages/memgraph-zero/memgql/changelog.mdx), maker, Memgraph, v0.12.0 of 14 Sep 2026, accessed 24 Sep 2026
33. [Property, structural, and constructed values, Cypher Manual 25 (Neo4j 2026.09), docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/values-and-types/property-structural-constructed.adoc), maker, Neo4j, accessed 24 Sep 2026
34. [REMOVE, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/clauses/remove.adoc), maker, Neo4j, accessed 24 Sep 2026
35. [Constraints, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/schema/constraints/index.adoc), maker, Neo4j, accessed 24 Sep 2026
36. [The impact of indexes on query performance, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/indexes/search-performance-indexes/using-indexes.adoc), maker, Neo4j, accessed 24 Sep 2026
37. [Introduction (editions, key features per edition), Neo4j Operations Manual 2026.09, docs-operations@a4c8c47](https://github.com/neo4j/docs-operations/blob/a4c8c4785b0b9c3c81184ba6c742082430225a56/modules/ROOT/pages/introduction.adoc), maker, Neo4j, accessed 24 Sep 2026
38. [Concurrent data access, Neo4j Operations Manual 2026.09, docs-operations@a4c8c47](https://github.com/neo4j/docs-operations/blob/a4c8c4785b0b9c3c81184ba6c742082430225a56/modules/ROOT/pages/database-internals/concurrent-data-access.adoc), maker, Neo4j, accessed 24 Sep 2026
39. [Neo4j JDBC Driver README at 35ec862](https://github.com/neo4j/neo4j-jdbc/blob/35ec8625fa327ea5f85ed3dae847b47bb354ace7/README.adoc), maker, Neo4j, accessed 24 Sep 2026
40. [README.asciidoc (Licensing, Extending Neo4j), neo4j/neo4j at 54a7dcf](https://github.com/neo4j/neo4j/blob/54a7dcf7c2501b31866199143364c5332da8936f/README.asciidoc), maker, Neo4j, accessed 24 Sep 2026
41. [LadybugDB README at 2d69bd3](https://github.com/LadybugDB/ladybug/blob/2d69bd3d7e6dd84b8e1438d42553dddd437660b3/README.md), maker, LadybugDB Developers, commit of 23 Sep 2026, accessed 24 Sep 2026
42. [Data types, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/data-types/index.mdx), maker, LadybugDB Developers, commit of 15 Sep 2026, accessed 24 Sep 2026
43. [Create table, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/data-definition/create-table.md), maker, LadybugDB Developers, accessed 24 Sep 2026
44. [Differences between Ladybug and Neo4j, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/difference.md), maker, LadybugDB Developers, accessed 24 Sep 2026
45. [Transactions, LadybugDB documentation, ladybug-docs@74a8467](https://github.com/LadybugDB/ladybug-docs/blob/74a846735b127abd9fda635b377372a69dba3b25/src/content/docs/cypher/transaction.md), maker, LadybugDB Developers, accessed 24 Sep 2026
46. [ladybug-nodejs `src_cpp/node_util.cpp` at b62c549](https://github.com/LadybugDB/ladybug-nodejs/blob/b62c5499d266ca1af4053e3e2e61d999c11962d3/src_cpp/node_util.cpp), maker, LadybugDB Developers, commit of 29 Aug 2026, accessed 24 Sep 2026
47. [pg_ladybug README at 895cbdb](https://github.com/LadybugDB/pg_ladybug/blob/895cbdb5d1d0fb7db65e78ac7352795489b91f5d/README.md), maker, LadybugDB Developers, commit of 10 Aug 2026, accessed 24 Sep 2026
48. [LadybugDB commit history, branch main](https://github.com/LadybugDB/ladybug/commits/main), maker, LadybugDB Developers, Counted by the author on 24 Sep 2026 (1,219 commits since 10 Oct 2025, 948 by one author), accessed 24 Sep 2026
49. [Set graph types, Cypher Manual 25, docs-cypher@9fc37dc](https://github.com/neo4j/docs-cypher/blob/9fc37dc068a31e940dd4e1d6ccecabef4051554b/modules/ROOT/pages/schema/graph-types/set-graph-types.adoc), maker, Neo4j, accessed 24 Sep 2026

**Searched**: Memgraph documentation read from `memgraph/documentation`
(branch `main`, commit 7d85d48) because memgraph.com returned an egress
block on 2026-09-24. "decimal", "byte", "precision", "int64" in the data
types page and the storage source (no decimal or binary type: C2).
"null" in the data types and `SET` pages (null in nested lists and maps Not
published: C3). "relationship", "edge", endpoint rules in the constraints
and Cypher-differences pages (C4); Integer-versus-Float uniqueness equality
(Not published: C4). "Memgraph label property index query plan" (no
independent plan report: C5). "SQL" across the documentation tree (no SQL
surface: C6, C10). "concurren", "conflict", "serializ" in the `MERGE` and
transactions pages (concurrent merge semantics Not published: C7). "bun" in
the client pages (no statement: C9). "LTS", "long-term support", "end of
life", "supported versions" (support window Not published). "Memgraph
snapshot isolation write skew Jepsen test independent analysis" (no
independent isolation analysis found). "experimental evaluation graph
database systems Neo4j Memgraph Kuzu PostgreSQL VLDB paper 2024 2025
benchmark" (no independent p95 comparison against a hand-designed schema:
C12; found [27]). "Memgraph Business Source License change 2026 community
edition license" (found [20] and [30] as a search summary). "Memgraph
security vulnerability reporting policy SOC 2 certification" (found [28] as
a search summary; certifications Not published). "Memgraph Enterprise
pricing per GB memory 2026 Memgraph Cloud pricing" (memgraph.com/pricing
blocked; figure only in a search summary: Pricing Not published).
"DB-Engines ranking graph DBMS September 2026" (host blocked: Adoption Not
published). Blocked hosts: memgraph.com, neo4j.com, db-engines.com,
survey.stackoverflow.co, arxiv.org, arcadedb.com. Apache AGE, Palantir
OSv2, Sqlg, PuppyGraph, Gel, Datomic, XTDB, SurrealDB, UMF-generated
per-type tables and JSONB with expression indexes were not searched for
this profile, hence Not researched.

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
