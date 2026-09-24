---
ddx:
  id: truss.component-profile-apache-age
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

# Component Profile: Apache AGE

Desk research on Apache AGE as the graph storage and query layer for truss,
measured against the capabilities truss needs from that role. The choice among
the bake-off options lives in a later ADR that cites this profile; what the
record cannot settle is routed below. Executed evidence is kept out of this
profile and recorded separately in [SPIKE-001](../02-design/spikes/SPIKE-001-apache-age.md).

## Scope

- Component: Apache AGE 1.8.0, the release line published for PostgreSQL 18
  (tag `PG18/v1.8.0-rc0`, release-feed timestamp 2026-08-06) and PostgreSQL 15
  (`PG15/v1.8.0-rc0`, 2026-09-19); the PostgreSQL 17 line at 1.7.0 and the
  `PG19` branch are covered where they bear on C1. Community source
  distribution, self-hosted or on a managed PostgreSQL service.
- Kind: Technology
- Would fill: the storage and traversal substrate under truss (bake-off option
  B, "UMF projected onto Apache AGE"), or the graph layer that makes truss
  unnecessary
- Feeds: the bake-off between option A (UMF-generated per-type tables),
  option B (UMF on AGE) and option C (minimal truss), and the ADR that follows
  it; the companion tech-spike file [SPIKE-001](../02-design/spikes/SPIKE-001-apache-age.md)
- Incumbent: *None*. truss has no implementation; teams use hand-built
  per-type tables, JSONB documents or a separate graph database
  ([[truss.product-vision]] §Target Market). truss has no
  [[current-state-inventory]].
- Researched: 2026-09-24
- Excluded: AGE Viewer and the Python, Go and JDBC drivers (not in the
  TypeScript path); AgensGraph (the fork AGE descends from); prices of managed
  services (AGE itself is free); the Azure performance guide
  (learn.microsoft.com was blocked by the research environment's egress
  proxy)

## Summary

We need a graph storage and query layer inside an organization's existing
PostgreSQL, for connected domain data described by UMF schemas, so that teams
can store, traverse, update and constrain that data in place, see which rules
are enforced, and never lose data silently. It must run on PostgreSQL 17 and 18
with a path to 19 including on common managed services, store UMF's nine
scalar families exactly, keep absent distinct from null, let the database
enforce declared rules under graph writes, index properties for the planner,
cover Cypher reads and writes and compose with SQL, behave predictably under
concurrency, retain unknown properties, work from TypeScript without precision
loss, stay readable through plain SQL, be sustainably maintained, and meet a
2× latency target against a hand-designed schema. On the public record AGE 1.8
meets the SQL-storage, Cypher-coverage, unknown-property and plain-SQL
capabilities, but its own documentation shows no date, time, timestamp or
binary property types and states that null cannot be stored as a property
value, so the verdict is No fit for truss's fidelity requirements; managed
availability, constraint behaviour, concurrency, maintainer depth and
performance stay open pending the spike and sources the research environment
could not reach.

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
| **Search summary** | Sources | The page was blocked by the research environment's egress proxy; the claim comes from a search engine's summary of that page, was not read first-hand, and supports descriptive claims only. |

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

Apache AGE ("A Graph Extension") is a PostgreSQL extension that adds a graph
data model and openCypher queries on top of existing relational databases, so
that SQL and Cypher can be used against one store [1]. It is governed by the
Apache Software Foundation, which announced it as a Top-Level Project on
2022-06-08 after it entered the Incubator in April 2020; it descends from
Bitnine's AgensGraph, a PostgreSQL fork [1][31]. Graph data lives in ordinary
PostgreSQL tables: each graph is a schema, each label a table inheriting from
`_ag_label_vertex` or `_ag_label_edge`, and each vertex or edge carries its
properties as one map [6]. The maker ships one release line per PostgreSQL
major; in the twelve months to 2026-09-24 it published 1.6.0, 1.7.0 and 1.8.0
across PostgreSQL 14, 15, 17 and 18 [2]. A community discussion records that
Bitnine/AGEDB dismissed its AGE development team in October 2024 and that
development slowed before resuming in 2025 [19].

- Category and purpose: PostgreSQL extension providing a property-graph model
  and openCypher over relational storage, queried through a `cypher()` set
  returning function inside SQL [1][6][11]
- Maker or governing body: the Apache Software Foundation (Apache AGE project
  management committee) [1][31]
- Adoption, from an independent source: Not published (searched for surveys
  and adoption figures, 2026-09-24; see Searched). A production migration from
  Neo4j at Trendyol is reported in an April 2026 post, available only as a
  search summary [33].
- Release cadence and support window: roughly one feature release a year per
  PostgreSQL line, staggered by line (release-feed timestamps: 1.7.0 for PG18
  on 2026-02-04 and PG17 on 2026-03-06; 1.8.0 for PG18 on 2026-08-06 and PG15
  on 2026-09-19) [2]; a
  support window is Not published (searched README, RELEASE and release
  notes, 2026-09-24)
- Licence: Apache License 2.0 [35]
- Built-for use cases: fraud detection, master data management, product
  recommendations, identity and relationship management, personalization and
  knowledge management, per the maker's README [1]

## Capability Alignment

### C1. Runs in the user's PostgreSQL 17 and 18, a path to 19, and on common managed services

As of 2026-09-24 the maker's README states that AGE "supports Postgres 11, 12,
13, 14, 15, 16, 17 & 18" and that supporting the latest versions is on the
roadmap [1]. The latest releases per line are 1.7.0 for PostgreSQL 17
(2026-03-06) and 1.8.0 for PostgreSQL 18 (2026-08-06); PostgreSQL 16 stops at
1.6.0 [2][4]. The repository carries a `PG19` branch and a tag
`PG19/v1.8.0-rc0`, "Advance PG19 branch to Apache AGE version 1.8.0", dated
2026-07-06, but no release for PostgreSQL 19 [2][4]. The manual's setup page
still says "versions 11, 12, 13, 14, and 15" (last changed 2024-04-23), so the
manual lags the README [14]. AGE is an extension loaded as a shared library,
so a managed service must ship and allow-list it. Azure Database for
PostgreSQL announced general availability of AGE in May 2025, with AGE 1.6.0
for PostgreSQL 16 added in January 2026 and PostgreSQL 18 support in April
2026, and Azure lists AGE as unsupported for in-place major version upgrades;
all Azure statements come from search summaries because Microsoft's pages were
blocked [23][24][25]. For Amazon RDS a feature request opened 2023-06-18 states
"Apache AGE is not directly supported on Amazon RDS" and is still open as of
2026-09-24 [20]; a 2025-11-09 Supabase discussion reports that Supabase does
not support AGE [22]; a 2024-06-15 issue asking which quality hosts allow AGE
was closed without an answer [21]. Postgres Professional's Enterprise
distribution documents an `apache_age` module (search summary) [50].

**Settled by**: self-hosted version matrix found in [1][2]; PostgreSQL 19 path
found only as an unreleased branch and tag [4]; managed-provider extension
lists not read (AWS, Google Cloud, Supabase, Neon, Crunchy Bridge and
Microsoft documentation pages blocked, 2026-09-24); community reports [20][22]
and search summaries [23][24] indicate Azure only among the large clouds
**Status**: Unknown

### C2. Stores UMF's nine scalar families exactly

The maker's type documentation lists null, integer, float, numeric, bool and
string as simple types, and list, map, vertex, edge and path as composite
types; it lists no date, time, timestamp or binary type [5]. Integer "is a
64-bit field that stores values from -9,223,372,036,854,775,808 to
9,223,372,036,854,775,807. Attempts to store values outside this range will
result in an error" [5]. Float is IEEE-754 and the manual warns that
"Rounding might take place if the precision of an input number is too high"
[5]. Numeric is arbitrary precision, and "When creating a numeric data type,
the `::numeric` data annotation is required", so an unannotated decimal
literal is a float [5]. Strings accept `\uXXXX` escapes [5]. An open-issue
trail confirms the temporal gap: `datetime()` was requested in January 2023
[26] and a January 2026 report lists "function datetime does not exist" among
unsupported standard features on AGE 1.6.0 and PostgreSQL 17.7 [27]. The
comparability page adds that integers, floats and numerics compare "as if both
numbers would have been coerced to arbitrary precision big decimals" [13],
which bears on key equality (C4).

**Settled by**: maker's type documentation found in [5]; no date, time,
timestamp or binary data type is documented, and the temporal gap is
confirmed by issues [26][27]
**Status**: Unmet

### C3. Absent distinct from explicit null; ordered lists with duplicates; string-keyed maps

The REMOVE page states: "Cypher does not allow storing `null` in properties.
Instead, if no value exists, the property is just not there" [7]. The SET page
shows `SET v.name = NULL` removing the property: "the name property is now
missing" [8]. A top-level property therefore cannot be explicitly null, and
reading a missing property "produces `null`" [5]. Inside values, lists can
hold null ("it will appear as the word 'null' in a list") and nested maps can
hold lists and maps [5]; the 1.8.0 release notes add "Preserve null-valued
keys in map literals (#2391)" [3]. Lists are literal ordered sequences with
index and slice access [5]; property keys are strings [5].

**Settled by**: maker's null-handling documentation found in [5][7][8]; the
maker states that null cannot be stored as a property value
**Status**: Unmet

### C4. Database-enforced required properties, types and limits, binary-unique keys and edge endpoints under Cypher writes

The maker's manual documents no constraint feature and no Cypher `CREATE
CONSTRAINT` [5][6][9]. A 2022 issue asking how to create a unique constraint
"like in AgensGraph" was closed without a documented answer [28]. Because
labels are ordinary tables [6], PostgreSQL DDL can in principle be applied to
them, but the manual recommends "that no DML or DDL commands are executed in
the namespace that is reserved for the graph" [6]. The 1.8.0 release notes fix
"segfault on CREATE/MERGE/SET with generated or extra label columns (#2458)",
which shows users adding columns to label tables [3]. The 1.8.0 source for
SET calls `ExecConstraints` and inserts index entries when updating an entity
[15], but whether CREATE and MERGE do the same, and whether row triggers and
foreign keys fire, is not documented. Edges have exactly one label and no
documented endpoint-label restriction [5]. Key equality under a unique index
would follow agtype comparison, which treats integer, float and numeric values
as numerically comparable [13].

**Settled by**: no maker documentation of constraints or of their interaction
with Cypher writes (searched manual pages [5][6][9], README [1], release notes
[3], issues [28], 2026-09-24); SET's constraint check found in source [15]
**Status**: Unknown

### C5. Property indexes used by the planner for graph queries

The README lists "Property Indexes: on both vertices(nodes) and edges" as a
feature [1], but the manual has no indexing page (searched the manual source
for `CREATE INDEX`, 2026-09-24). The 1.8.0 release notes add "automatic
vertex-ID and edge-endpoint indexes, with indexed lookups for entity
operations" and restore containment selectivity estimators for `@>` and key
existence (#2356) [3]. A MATCH property map is translated to the `@>`
operator by default, with a `age.enable_containment` setting to use `->`
instead [15]. Community issues from 2023 and 2024 report WHERE predicates
and ORDER BY not using property indexes on earlier releases [29][30]. No
independent report on 1.8.0 index use was reachable.

**Settled by**: maker indexing documentation not found (README claim only
[1]; release notes [3]); independent plans for 1.8.0 not found (searched,
2026-09-24); older community reports of non-use [29][30]
**Status**: Unknown

### C6. Traversal, pattern matching, aggregation, parameters; create, set, delete, merge; composition with SQL

The manual's contents list MATCH, WITH, RETURN, ORDER BY, SKIP, LIMIT,
CREATE, DELETE, SET, REMOVE, MERGE and UNWIND, plus aggregation, list, map
and user-defined functions [51]; MATCH covers variable-length edges [10]. Parameters are passed as an agtype map
through the third argument of `cypher()` in a prepared statement [12]. Cypher
composes with SQL inside CTEs and JOINs, but "Cypher queries using the CREATE,
SET, REMOVE clauses cannot be used in sql queries with JOINs" and "Cypher
cannot be used in an expression — the query must exist in the `FROM` clause"
[11]. Release 1.8.0 adds MERGE with ON CREATE SET and ON MATCH SET, reduce(),
list predicates and fixes for OPTIONAL MATCH [3]. Labels are single: "Edges
are required to have a label, but vertices do not" and a vertex "may be
assigned a label" [5]. A January 2026 independent report lists standard
features missing on 1.6.0 (MERGE ON CREATE SET, since added; `datetime()`;
`NOT (pattern)`) [27].

**Settled by**: maker's clause documentation and limitations found in
[5][10][11][12]; release notes [3]; independent coverage [27]
**Status**: Met

### C7. Transactional writes with defined concurrent behaviour

AGE writes run inside PostgreSQL transactions because Cypher executes within a
SQL statement [11], and the README explains that graph writes need a commit to
become visible to other sessions [1]. The manual documents no concurrency
semantics for SET or MERGE (searched manual source for concurrency, isolation,
serialization and lock, 2026-09-24). The 1.8.0 source shows SET locking the
originally read tuple with `heap_lock_tuple` and raising an internal error
("Entity failed to be updated") when the lock does not return `TM_Ok` [15];
the behaviour a client sees is not documented. Release notes record a
non-concurrent MERGE bug, "MERGE incorrectly creates multiple vertices"
(issue 1691), fixed in 1.6.0 [2], and a 1.8.0 fix for "visibility of changes
across CREATE, MATCH, and chained MERGE operations" [3].

**Settled by**: maker documentation of concurrency and merge semantics not
found (searched manual, README, release notes, 2026-09-24); SET's lock path
found in source [15]
**Status**: Unknown

### C8. Retains properties that match no schema, with values unchanged

AGE has no external schema: "each individual node and edge possesses a map of
properties" [6], and maps may contain simple and composite values, including
nested lists and maps [5]. Any key can therefore be stored without prior
declaration. Values are retained within the limits of C2 and C3: a value that
agtype cannot represent (a date, binary data) must be encoded first, and a
null-valued top-level key is not stored [5][7].

**Settled by**: maker documentation that arbitrary maps are stored found in
[5][6]
**Status**: Met

### C9. Usable from TypeScript on Bun or Node without numeric precision loss

The maker's Node.js driver lives in the main repository as `pg-age`, version
`1.0.0-alpha`, built on `pg` and an ANTLR agtype grammar [17]. Its source
parses integers as JavaScript numbers when safe and as `BigInt` otherwise
("Use BigInt for values that exceed Number.MAX_SAFE_INTEGER"), parses float
values with `parseFloat`, and its grammar accepts a `::` type annotation that
the listener does not act on, so an annotated numeric is parsed as a
JavaScript number [17]. agtype's text form is JSON-like but not JSON: numerics
print with a `::numeric` suffix and entities with `::vertex` or `::edge` [5].
A client that reads agtype as text and parses it itself can keep every value;
the maker's driver, on the record of its source, cannot keep exact decimals.

**Settled by**: maker's driver source found in [17]; driver documentation of
precision guarantees not found (searched `drivers/nodejs/README.md`,
2026-09-24); text format found in [5]
**Status**: Unknown

### C10. Readable through plain SQL, with conversion to ordinary SQL types

Graphs are stored in ordinary PostgreSQL schemas and tables (`graph."Label"`
with `id` and `properties` columns) visible in the catalog [6]. The manual
shows cypher() results typed by the column definition list, including
`AS (name varchar(50))` [11], and the 1.8.0 release notes add "agtype <->
jsonb bidirectional casts" [3]. The manual does not document which agtype
values convert to which SQL types or with what rounding (searched manual
source for cast and typecast, 2026-09-24).

**Settled by**: storage in plain tables found in [6]; conversion via column
definition lists [11] and jsonb casts [3]; a documented cast matrix not found
**Status**: Met

### C11. Maintained well enough to be a long-lived dependency

AGE is an ASF Top-Level Project since 2022-06-08 [31] under the Apache License
2.0 [35], with line releases on the feed in 2025-12, 2026-01, 2026-02,
2026-03, 2026-08 and 2026-09 [2]. The
public commit history of `master` shows 118 commits by 22 distinct authors
between 2025-09-24 and 2026-09-24, of which one author made 51 and the top
three 85; the preceding twelve months show 17 commits by 4 authors [18]. A
discussion opened 2025-02-08 states that "In early October 2024,
Bitnine/AGEDB dismissed the entire development team responsible for
contributing to Apache AGE", and a committer replied on 2025-09-23 that
"Apache AGE development is still ongoing" [19]. The size of the committer and
PMC roster, which is what "maintainers" means here, is Not published on any
page reachable from the research environment (projects.apache.org, whimsy and
age.apache.org blocked, 2026-09-24).

**Settled by**: foundation status [31], release history [2], licence [35]
and commit statistics [18] found; maintainer roster not found (blocked)
**Status**: Unknown

### C12. p95 within 2× of a hand-designed schema for fetch and one to three hops

The maker publishes no benchmark (searched README, manual, release notes,
2026-09-24). GRBench, an August 2026 arXiv paper, reports in a search summary
that "PostgreSQL with AGE remains below the break-even line for every H- and
G-series group" against relational equivalents, attributing the gap to
Cypher translation and graph-type handling over relational storage [32]. An
April 2026 Trendyol engineering post reports, in a search summary, that
variable-length path queries "bypass indexes entirely in AGE" and were
rewritten as iterative fixed-depth queries [33]; a post by Sanjeev Singh
reports a 40× difference in favour of recursive CTEs for one case (search
summary, undated) [34]. None of these could be read first-hand, and none
states p95 latency against the project's target.

**Settled by**: independent benchmark comparing AGE with a relational baseline
found only as search summaries [32][33][34]; p95 figures not found
**Status**: Unknown

Other notable capabilities the record documents and no criterion requires:

| Capability | What the record says | Source |
|------------|----------------------|--------|
| Row-level security | 1.8.0 "Adds row-level security enforcement and improves permission checks for graph reads and writes" | [2][3] |
| Shortest path | 1.8.0 adds `shortest_path` / `all_shortest_paths` set-returning functions (#2430) | [3] |
| ISO GQL alignment | Not published (searched README, manual and release notes for GQL, 2026-09-24) | none |
| Bulk load | CSV loaders `load_labels_from_file` and `load_edges_from_file`; 1.8.0 moves them to PostgreSQL's COPY parser; files must sit under the hard-coded directory `/tmp/age/` | [3][16] |
| Major-version upgrade | 1.8.0 adds helpers for PostgreSQL major-version upgrades; Azure lists AGE as unsupported for in-place major version upgrade (search summary) | [3][25] |
| Multiple graphs | Several graphs per database, one schema each | [6] |
| Preloading | 1.8.0 makes AGE usable from `shared_preload_libraries`; otherwise each session runs `LOAD 'age'` | [1][3] |

**Verdict**: No fit. C2 and C3 are Unmet on the maker's own documentation: agtype
has no date, time, timestamp or binary type, and null cannot be stored as a
property value, so truss could meet its fidelity rules on AGE only by encoding
those values itself; C1, C4, C5, C7, C9, C11 and C12 are Unknown and are routed
below.

## Technology and Operations

| Aspect | What the record says | Source |
|--------|----------------------|--------|
| Hosting model | Self-hosted from source or the `apache/age` Docker image; managed on Azure Database for PostgreSQL as of 2026-04 (search summary); not on Amazon RDS as of the open 2023 request; not on Supabase per a 2025 community reply | [1][20][22][23][24] |
| Integrations | SQL via `cypher()`; drivers for Python, Node.js, JDBC and Go in the main repository; 1.8.0 fixes in all four | [1][3][17] |
| Data handling | Data stays in the user's PostgreSQL tables; residency, encryption and retention are PostgreSQL's and the host's | [6] |
| Certifications | Not published (searched README and release notes, 2026-09-24); not applicable to an extension on its own | none |
| Maturity and cadence | First commits 2019; ASF TLP 2022-06-08; 1.6.0 to 1.8.0 released 2025-09 to 2026-09 across PG14–18 | [2][18][31] |
| Governance | Apache Software Foundation project; vendor-neutral model restated by the ASF chair in 2025 | [19][31] |
| Security process | Not published on reachable pages (the ASF security page and age.apache.org were blocked, 2026-09-24); 1.8.0 fixes memory-safety issues and CSV loader out-of-bounds reads | [3] |

## Pricing and Licensing

| Item | Figure | Label | Source |
|------|--------|-------|--------|
| Licence | Apache License 2.0: use, modification and redistribution, including commercial use, with notice and patent terms | Published | [35] |
| Software price | No charge | Published | [35] |
| Managed-service price | Not researched for this profile (excluded in Scope) | Not published | none |

## Competitive Landscape

Cells cite each alternative's own record. "Search summary" marks a claim
taken from a search engine's summary of a blocked page.

| Candidate | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | Profile |
|-----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|---------|
| Apache AGE 1.8 | Unknown: PG11–18 self-hosted, PG19 branch; Azure only among large clouds (search summary) [1][4][23] | Unmet: no date, time or binary type [5] | Unmet: null not storable [7] | Unknown [15][28] | Unknown [1][3][29] | Met [3][10][11] | Unknown [15] | Met [6] | Unknown [17] | Met [3][6] | Unknown: ASF, Apache-2.0, 22 commit authors in 12 months [18][31][35] | Unknown [32][33] | this profile |
| Sqlg 3.1.6 | JVM library over JDBC, no extension needed; supported PostgreSQL versions Not published (searched 3.1.6 docs) [36] | Unmet: `BigDecimal` maps to `DOUBLE PRECISION` on PostgreSQL; dates, times and `BYTEA` supported; `LocalTime` drops nanoseconds [36] | Unmet† | Unique and non-unique property indexes via the topology API [36]; other constraints Not researched | Indexes used by `has()` steps per docs example [36] | Gremlin (TinkerPop), not Cypher; plain tables per label [36] | Unknown† | New properties create columns on the fly [36] | Unmet: Java library [36] | Met: typed columns in `V_<label>` tables [36] | MIT; one human commit author (74 of 80 commits, the rest dependabot) in the 12 months to 2026-09-24 [37] | Unknown† | [[component-profile-sqlg]] |
| PuppyGraph | Runs as a separate query engine over existing databases, not inside PostgreSQL (search summary) [38] | Decimal(precision, scale) attribute type (search summary) [38] | Unknown† | Not applicable: read-only engine (search summary) [38] | Unknown† | Reads only: openCypher and Gremlin, no writes (search summary) [38] | Unmet† | Unmet† | Unknown† | Data stays in source tables (search summary) [38] | Proprietary per [[truss.competitive-analysis]]; Not researched here | Unknown† | [[component-profile-puppygraph]] |
| Option A: UMF-generated per-type PostgreSQL tables with recursive CTEs | Plain PostgreSQL DDL, no extension [39][41] | Met by column choice: `numeric` "user-specified precision, exact", `bytea`, date and time types [39] | Not researched (depends on the generated design) | Met: CHECK, NOT NULL, UNIQUE, foreign keys [41] | Met: B-tree and expression indexes [42] | SQL and recursive queries, no graph language [43] | Met: row-level MVCC; READ COMMITTED re-checks a concurrently updated row [44] | Not researched (depends on the generated design) | Not researched | Met: ordinary tables and columns [41] | PostgreSQL Licence [45] | Baseline by definition | *none yet* |
| JSONB plus expression indexes (truss option C storage idea) | Plain PostgreSQL [40] | Partial: JSON numbers map to `numeric` and keep trailing zeroes; no binary or temporal JSON types; `\u0000` rejected [40] | Met: JSON null distinct from a missing key; arrays ordered; but duplicate object keys are not kept [40] | Met: CHECK and unique expression indexes on JSONB expressions [41][42] | Met: GIN (`jsonb_path_ops`) and expression indexes [40][42] | Via SQL over an edge table and recursive queries [43] | Met: row-level MVCC [44] | Met: arbitrary keys [40] | Not researched | Met: `->>` and casts [40] | PostgreSQL Licence [45] | Not researched | *none yet* |
| Neo4j (2026.x) | Unmet: data leaves the PostgreSQL estate ([[truss.competitive-analysis]]) | Unmet: INTEGER, FLOAT, STRING, BOOLEAN, temporal types and pass-through byte arrays, but no exact decimal type [46] | Unmet: only homogeneous lists of simple types are storable; maps are not property types [46] | Uniqueness in all editions; existence, type and key constraints and graph types in Enterprise Edition [47][48] | Range, text, point and token lookup indexes [49] | Cypher with published GQL conformance ([[truss.competitive-analysis]]); SQL composition Not researched | Met† | Unmet† | Met† | Unmet: data held outside PostgreSQL ([[truss.competitive-analysis]]) | Unmet† | Unknown† | [[component-profile-neo4j]] |

† Status copied on 2026-09-25 from the sibling profile named in the Profile column, where the evidence and sources are recorded.

- Sqlg: shares the "graph on your relational database" position; diverges on
  exactness (decimals stored as double precision) and runtime (JVM only), and
  its record shows a single active author [36][37].
- PuppyGraph: shares "data stays where it is"; diverges by being read-only and
  running outside PostgreSQL (search summary) [38].
- Option A: shares storage, constraints and indexing with PostgreSQL itself
  [39][41][42]; diverges by needing DDL per type, and by leaving absence and
  unknown fields to the generated design.
- JSONB plus expression indexes: shares AGE's one-map-per-object storage idea;
  diverges on exact decimals (JSONB numbers are `numeric`), explicit null, and
  full PostgreSQL constraint and trigger semantics on plain SQL writes [40][41].
- Neo4j: shares Cypher and a mature constraint model [47]; diverges by moving
  data out of PostgreSQL ([[truss.competitive-analysis]]), lacking an exact
  decimal type and disallowing map properties [46].

## Confidence

| Grade | Means |
|-------|-------|
| **High** | Every design-defining claim is corroborated by the maker's material *and* at least one independent source, and no design-defining capability is Unknown. |
| **Medium** | Design-defining claims rest on the maker alone, or a design-defining capability is Unknown, or the independent coverage is older than two major versions. |
| **Low** | Thin public footprint; claims rest on one source or on none. |

**Grade**: Medium. The two Unmet findings that decide the verdict (C2, C3) rest
on the maker's own manual [5][7][8], which is the strongest source for an
absence, and C2's temporal gap is corroborated by a 2026 independent report
[27]. Design-defining capabilities C1, C4, C5, C7 and C12 are Unknown, which
caps the grade at Medium. Independent coverage of managed availability and
performance could be reached only as search summaries (Microsoft, AWS, Google,
Supabase, Neon, arXiv, Medium and dev.to pages were blocked by the research
environment's egress proxy), so those rest on no first-hand independent
source. Weakest area: C12 performance and C1 managed-provider availability.

## Open Questions

| # | Question | Design-defining because | Route |
|---|----------|-------------------------|-------|
| 1 | Which of the managed PostgreSQL services the project's users run (Amazon RDS and Aurora, Google Cloud SQL and AlloyDB, Supabase, Neon, Crunchy Bridge, Azure) list `age` for PostgreSQL 17 and 18, and at which AGE version? | Option B is unavailable to users whose provider does not ship AGE | operator guidance (read each provider's extension list from an unblocked network) |
| 2 | Do Cypher CREATE, MERGE and SET honour CHECK, NOT NULL, unique indexes, row triggers and foreign keys on label tables, and with what errors? | Decides whether truss's enforcement report can say "database" for any rule on AGE storage | [[tech-spike]] (see [SPIKE-001](../02-design/spikes/SPIKE-001-apache-age.md)) |
| 3 | Does the 1.8.0 planner use B-tree expression indexes and GIN for Cypher equality, range and parameterised predicates? | Performance of fetch-by-key and traversal starts | [[tech-spike]] |
| 4 | What happens when two transactions SET different properties of one vertex, or MERGE one key, concurrently, at READ COMMITTED and REPEATABLE READ? | truss's concurrency and retry strategy (`sql-exactness`) | [[tech-spike]]; ask maker to document |
| 5 | Can decimals and 64-bit integers round-trip through Bun and Node clients, and at what cost (custom agtype parser)? | Implementation language fit (`typescript-bun`) | [[tech-spike]] |
| 6 | How large is the AGE committer and PMC roster, and how many committers are active outside one employer? | Dependency risk over the project's support horizon | ask maker (ASF committee page, board reports) |
| 7 | Does AGE meet the 2× p95 target against a hand-designed schema on the project's benchmark corpus for fetch and one to three hops, including under concurrent writes? | The proposed performance success measure | [[tech-spike]] on the benchmark corpus the vision names |
| 8 | Is a PostgreSQL 19 release of AGE planned, and when? | C1's path to 19 | ask maker |
| 9 | Would a truss-side encoding of dates, times, binary data and explicit nulls inside agtype maps be acceptable to UMF's fidelity rules, and what would it cost in queryability and indexing? | Whether C2 and C3 can be worked around rather than blocking option B | [[tech-spike]]; ADR for the bake-off |

## Sources

Access date for every source: 2026-09-24. Pages marked *search summary* were
blocked by the research environment's egress proxy and were not read
first-hand. The AGE manual is published only as an unversioned `master`
manual at age.apache.org (blocked); its source files in `apache/age-website`
are cited with their last-change dates instead.

1. [Apache AGE README (master)](https://github.com/apache/age/blob/master/README.md), maker, Apache AGE project, last changed 2026-07-15 (commit on master as of 2026-09-18), accessed 2026-09-24
2. [Apache AGE releases feed](https://github.com/apache/age/releases.atom) and [releases page](https://github.com/apache/age/releases), maker, Apache AGE project, entries 2025-12-12 to 2026-09-19, accessed 2026-09-24
3. [RELEASE notes, Apache AGE 1.8.0 (tag PG18/v1.8.0-rc0)](https://github.com/apache/age/blob/PG18/v1.8.0-rc0/RELEASE), maker, Apache AGE project, 2026-07-07, accessed 2026-09-24
4. [Apache AGE branches and tags, including `PG19` and `PG19/v1.8.0-rc0`](https://github.com/apache/age/tree/PG19), maker, Apache AGE project, tag dated 2026-07-06, accessed 2026-09-24
5. [AGE manual: Data Types – agtype](https://github.com/apache/age-website/blob/master/docs/intro/types.md) (published at age.apache.org/age-manual/master/intro/types.html), maker, Apache AGE project, last changed 2023-10-09, accessed 2026-09-24
6. [AGE manual: Graphs](https://github.com/apache/age-website/blob/master/docs/intro/graphs.md), maker, Apache AGE project, last changed 2023-10-09, accessed 2026-09-24
7. [AGE manual: REMOVE](https://github.com/apache/age-website/blob/master/docs/clauses/remove.md), maker, Apache AGE project, last changed 2023-12-21, accessed 2026-09-24
8. [AGE manual: SET](https://github.com/apache/age-website/blob/master/docs/clauses/set.md), maker, Apache AGE project, last changed 2023-12-21, accessed 2026-09-24
9. [AGE manual: MERGE](https://github.com/apache/age-website/blob/master/docs/clauses/merge.md), maker, Apache AGE project, last changed 2023-11-22, accessed 2026-09-24
10. [AGE manual: MATCH (variable-length edges)](https://github.com/apache/age-website/blob/master/docs/clauses/match.md), maker, Apache AGE project, last changed 2023-12-21, accessed 2026-09-24
11. [AGE manual: Advanced – Cypher in CTEs, JOINs and SQL expressions](https://github.com/apache/age-website/blob/master/docs/advanced/advanced.md), maker, Apache AGE project, last changed 2025-09-07, accessed 2026-09-24
12. [AGE manual: Prepared Statements](https://github.com/apache/age-website/blob/master/docs/advanced/prepared_statements.md), maker, Apache AGE project, last changed 2025-09-07, accessed 2026-09-24
13. [AGE manual: Comparability, Equality, Orderability and Equivalence](https://github.com/apache/age-website/blob/master/docs/intro/comparability.md), maker, Apache AGE project, last changed 2023-10-09, accessed 2026-09-24
14. [AGE manual: Setup](https://github.com/apache/age-website/blob/master/docs/intro/setup.md), maker, Apache AGE project, last changed 2024-04-23, accessed 2026-09-24
15. [AGE source: `src/backend/executor/cypher_set.c` and `src/backend/utils/ag_guc.c` (tag PG18/v1.8.0-rc0)](https://github.com/apache/age/blob/PG18/v1.8.0-rc0/src/backend/executor/cypher_set.c), maker, Apache AGE project, 2026-07-07, accessed 2026-09-24
16. [AGE source: `src/backend/utils/load/age_load.c` (tag PG18/v1.8.0-rc0)](https://github.com/apache/age/blob/PG18/v1.8.0-rc0/src/backend/utils/load/age_load.c), maker, Apache AGE project, 2026-07-07, accessed 2026-09-24
17. [AGE Node.js driver `pg-age` source (`drivers/nodejs`, tag PG18/v1.8.0-rc0)](https://github.com/apache/age/tree/PG18/v1.8.0-rc0/drivers/nodejs), maker, Apache AGE project, 2026-07-07, accessed 2026-09-24
18. [Apache AGE commit history, master](https://github.com/apache/age/commits/master), maker, Apache AGE project, counted with `git log --since/--until` on 2026-09-24 (Published data; counts made by the profile author), accessed 2026-09-24
19. [Discussion #2150: What's the Status of Apache AGE?](https://github.com/apache/age/discussions/2150), community, opened by thomastthai 2025-02-08; replies by the ASF chair (2025-02-09) and committer jrgemignani (2025-02-22, 2025-09-23), accessed 2026-09-24
20. [Issue #998: Add Support for Apache AGE on Amazon RDS](https://github.com/apache/age/issues/998), community, Omar-Saad, opened 2023-06-18, open as of 2026-09-24, accessed 2026-09-24
21. [Issue #1917: Which quality Postgres hosts allow the AGE extension?](https://github.com/apache/age/issues/1917), community, incorvia, 2024-06-15, closed as not planned, accessed 2026-09-24
22. [Supabase discussion #40285: How to Install Apache AGE Extension?](https://github.com/orgs/supabase/discussions/40285), community, mohammed90 and replies, 2025-11-09, accessed 2026-09-24
23. [General Availability of Graph Database Support in Azure Database for PostgreSQL](https://techcommunity.microsoft.com/blog/adforpostgresql/general-availability-of-graph-database-support-in-azure-database-for-postgresql/4413894), vendor, Microsoft, May 2025, *search summary* (page blocked), accessed 2026-09-24
24. Azure Database for PostgreSQL maintenance release notes, [January 2026](https://github.com/MicrosoftDocs/azure-databases-docs/blob/main/articles/postgresql/release-notes-maintenance/2026-january.md) and [April 2026](https://github.com/MicrosoftDocs/azure-databases-docs/blob/main/articles/postgresql/release-notes-maintenance/2026-april.md), vendor, Microsoft, 2026, *search summary* (pages returned 404 to the fetcher), accessed 2026-09-24
25. [Azure: Considerations when using extensions (in-place major version upgrade)](https://github.com/MicrosoftDocs/azure-databases-docs/blob/main/articles/postgresql/extensions/concepts-extensions-considerations.md), vendor, Microsoft, date not shown, *search summary*, accessed 2026-09-24
26. [Issue #613: datetime() Function](https://github.com/apache/age/issues/613), community, January 2023 (search summary for date), accessed 2026-09-24
27. [Issue #2323: Multiple standard features not supported](https://github.com/apache/age/issues/2323), independent user report, e7nd7r, 2026-01-28, AGE 1.6.0 on PostgreSQL 17.7, accessed 2026-09-24
28. [Issue #200: How to create a unique constraint on a property, like in AgensGraph?](https://github.com/apache/age/issues/200), community, bravius, 2022-03-16, closed, accessed 2026-09-24
29. [Issue #1000: Index is not used in the WHERE clause](https://github.com/apache/age/issues/1000), community, vladiksun, 2023-06-20, closed, accessed 2026-09-24
30. [Issue #1522: Sorted queries do not utilise indices](https://github.com/apache/age/issues/1522), community, maximdvoynishnikov, 2024-01-25, closed as not planned, accessed 2026-09-24
31. [The Apache Software Foundation Announces Apache AGE as a Top-Level Project](https://news.apache.org/foundation/entry/the-apache-software-foundation-announces83) (also [GlobeNewswire, 2022-06-08](https://www.globenewswire.com/news-release/2022/06/08/2458799/0/en/The-Apache-Software-Foundation-Announces-Apache-AGE-as-a-Top-Level-Project.html)), maker (ASF), 2022-06-08, *search summary* (page blocked), accessed 2026-09-24
32. [GRBench: A Comprehensive Benchmark Evaluation for Graph-relational Data Management, arXiv 2608.31027](https://arxiv.org/abs/2608.31027), independent, authors not read, August 2026, *search summary* (page blocked), accessed 2026-09-24
33. [Migrating Graph Operations to Apache AGE: From Writes to Reads](https://medium.com/trendyol-tech/migrating-graph-operations-to-apache-age-from-writes-to-reads-3b8334628e1c), independent (user organisation), Tolunay Kandırmaz, Trendyol Tech, April 2026, *search summary* (page blocked), accessed 2026-09-24
34. [PostgreSQL Showdown: Complex Joins vs. Native Graph Traversals with Apache AGE](https://medium.com/@sjksingh/postgresql-showdown-complex-joins-vs-native-graph-traversals-with-apache-age-78d65f2fbdaa), independent, Sanjeev Singh, date not shown, *search summary*, accessed 2026-09-24
35. [Apache AGE LICENSE](https://github.com/apache/age/blob/master/LICENSE), maker, Apache AGE project, Apache License 2.0, accessed 2026-09-24
36. [Sqlg 3.1.6 documentation source (`sqlg-doc/docs/3.1.6`: dataTypes, indexes, topology, introduction)](https://github.com/pietermartin/sqlg/tree/master/sqlg-doc/docs/3.1.6), maker (Sqlg), Pieter Martin, repository head 2026-07-31, accessed 2026-09-24
37. [Sqlg repository and commit history](https://github.com/pietermartin/sqlg), maker (Sqlg), MIT licence; commit authors counted with `git log` on 2026-09-24, accessed 2026-09-24
38. [PuppyGraph documentation: Attribute Types](https://docs.puppygraph.com/reference/schema/attribute-types/) and [PuppyGraph home](https://www.puppygraph.com/), vendor, PuppyGraph, dates not shown, *search summary*, accessed 2026-09-24
39. [PostgreSQL 18.6 documentation source: Data Types (`datatype.sgml`)](https://github.com/postgres/postgres/blob/REL_18_6/doc/src/sgml/datatype.sgml), maker (PostgreSQL Global Development Group), tag REL_18_6 dated 2026-08-11, accessed 2026-09-24
40. [PostgreSQL 18.6 documentation source: JSON Types (`json.sgml`)](https://github.com/postgres/postgres/blob/REL_18_6/doc/src/sgml/json.sgml), maker (PGDG), 2026-08-11, accessed 2026-09-24
41. [PostgreSQL 18.6 documentation source: Constraints (`ddl.sgml`)](https://github.com/postgres/postgres/blob/REL_18_6/doc/src/sgml/ddl.sgml), maker (PGDG), 2026-08-11, accessed 2026-09-24
42. [PostgreSQL 18.6 documentation source: Indexes on Expressions (`indices.sgml`)](https://github.com/postgres/postgres/blob/REL_18_6/doc/src/sgml/indices.sgml), maker (PGDG), 2026-08-11, accessed 2026-09-24
43. [PostgreSQL 18.6 documentation source: Recursive Queries (`queries.sgml`)](https://github.com/postgres/postgres/blob/REL_18_6/doc/src/sgml/queries.sgml), maker (PGDG), 2026-08-11, accessed 2026-09-24
44. [PostgreSQL 18.6 documentation source: Read Committed isolation (`mvcc.sgml`)](https://github.com/postgres/postgres/blob/REL_18_6/doc/src/sgml/mvcc.sgml), maker (PGDG), 2026-08-11, accessed 2026-09-24
45. [PostgreSQL 18.6 documentation source: Legal Notice (`legal.sgml`)](https://github.com/postgres/postgres/blob/REL_18_6/doc/src/sgml/legal.sgml), maker (PGDG), 2026-08-11, accessed 2026-09-24
46. [Neo4j Cypher Manual source: Property, structural and constructed values](https://github.com/neo4j/docs-cypher/blob/dev/modules/ROOT/pages/values-and-types/property-structural-constructed.adoc), maker (Neo4j), branch head 2026-09-23, accessed 2026-09-24
47. [Neo4j Cypher Manual source: Constraints](https://github.com/neo4j/docs-cypher/blob/dev/modules/ROOT/pages/schema/constraints/index.adoc), maker (Neo4j), 2026-09-23, accessed 2026-09-24
48. [Neo4j Cypher Manual source: Graph types (GA in Neo4j 2026.06, Enterprise Edition)](https://github.com/neo4j/docs-cypher/blob/dev/modules/ROOT/pages/schema/graph-types/index.adoc), maker (Neo4j), 2026-09-23, accessed 2026-09-24
49. [Neo4j Cypher Manual source: Search-performance indexes](https://github.com/neo4j/docs-cypher/blob/dev/modules/ROOT/pages/indexes/search-performance-indexes/index.adoc), maker (Neo4j), 2026-09-23, accessed 2026-09-24
50. [Postgres Pro Enterprise 18: apache_age](https://postgrespro.com/docs/enterprise/current/apache-age), vendor, Postgres Professional, date not shown, *search summary*, accessed 2026-09-24
51. [AGE manual: contents (`docs/index.rst`)](https://github.com/apache/age-website/blob/master/docs/index.rst), maker, Apache AGE project, repository head 2026-06-11, accessed 2026-09-24

**Searched**: Blocked hosts on 2026-09-24 (egress proxy): age.apache.org,
postgresql.org, apt.postgresql.org, learn.microsoft.com,
techcommunity.microsoft.com, docs.aws.amazon.com, docs.cloud.google.com,
supabase.com, neon.com, gdotv.com, arxiv.org, medium.com, dev.to,
snowflake.com, news.apache.org, neo4j.com, github.io pages; MicrosoftDocs
files on github.com returned 404 to the fetcher and refused a git clone.
Searches and pages per cell:
C1 managed providers: "Azure Database for PostgreSQL flexible server Apache
AGE generally available supported versions", "Amazon RDS for PostgreSQL
Apache AGE extension support request not supported", "Apache AGE extension
support Google Cloud SQL AlloyDB Supabase Neon Crunchy Bridge managed
PostgreSQL"; provider pages for AWS, Google, Supabase, Neon, Microsoft
(blocked) → C1 Unknown; Crunchy Bridge, Neon, AlloyDB and Cloud SQL cells not
settled. C1 support window: README, RELEASE, releases feed → Not published.
C2/C3: manual source `docs/intro/types.md`, `clauses/remove.md`,
`clauses/set.md`; "github apache/age issue date datetime temporal type support
agtype". C4: manual source grep for constraint, unique, index; "github
apache/age unique constraint property index vertex label MERGE duplicate" →
Unknown. C5: manual source grep for `CREATE INDEX`, `USING gin` (no hits);
"Apache AGE create index on property agtype_access_operator GIN properties
index not used Cypher WHERE"; issues #1000, #1522 → Unknown. C7: manual
source grep for concurren, isolation, serializ, lock (no hits); "github
apache/age "Entity failed to be updated" concurrent" (no hits) → Unknown. C9:
`drivers/nodejs/README.md` and source → Unknown. C10: manual source grep for
cast, typecast. C11: projects.apache.org and whimsy (blocked); git history
counted locally → roster Not published. C12: "Apache AGE benchmark performance
comparison Neo4j PostgreSQL recursive CTE paper 2024 2025", ""Apache AGE"
performance evaluation arxiv graph database PostgreSQL extension traversal
latency", "GRBench graph-relational benchmark Apache AGE", "Trendyol Tech
Apache AGE migrating graph operations"; github.com/tamnd/graph-bench (lists
AGE but publishes no AGE results as of 2026-08-22) → Unknown. Adoption:
"Apache AGE adoption survey users" folded into the searches above; no survey
found → Not published. ISO GQL: README, manual and release notes → Not
published. Competitive Landscape: Sqlg docs source (3.1.6) and README; Neo4j
docs-cypher source; PuppyGraph "PuppyGraph write support read-only graph
query engine PostgreSQL openCypher Gremlin supported data types decimal";
PostgreSQL 18.6 documentation source. Cells marked Not researched had no page
read for that capability: Sqlg C3, C7, C12; PuppyGraph C3, C5, C7–C9, C12;
option A C9; JSONB C9, C12; Neo4j C7–C9, C11, C12. The sibling profile that
would fill each is *none yet*.

## Review Checklist

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
