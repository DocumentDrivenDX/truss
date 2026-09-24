---
ddx:
  id: truss.design-lessons-palantir-osv2
  activity: discover
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.component-profile-palantir-osv2
      kind: informed_by
    - id: truss.vision-input
      kind: informed_by
---

# Design Lessons for truss from Palantir Foundry Object Storage V2

Status: draft research note, 2026-09-25. Companion to
[component-profile-palantir-osv2.md](component-profile-palantir-osv2.md), which scores OSv2 against
truss's required capabilities; OSv2 scored No fit as a component. This note
extracts design lessons. Nothing here was run: no benchmark, prototype or
integration result is claimed.

**Citations.** `[Pn]` refers to source *n* in the Sources list of
`component-profile-palantir-osv2.md`. Palantir documentation pages were blocked
by the egress proxy and were read from a community mirror of palantir.com/docs
[P81] (capture date not shown). The Foundry API reference was read from
Palantir's `foundry-platform-python` repository at tag 1.107.0 [P54]–[P71], and
the TypeScript OSDK from its npm packages [P72][P73]. Items marked "(search
summary)" come from a search engine's summary of a page that was not read. All
Palantir pages are living pages, so every limit and feature status below is as
of 2026-09-24. truss artifacts are cited as `[[truss.*]]`.

**Recommendation words.** *Borrow*: take the idea largely as is. *Adapt*: take
the idea, change it for truss's setting (inside PostgreSQL, UMF-typed,
per-value). *Avoid*: a documented OSv2 behaviour truss should not reproduce.
*Not applicable*: outside truss's role.

## Lessons at a glance

| # | Lesson | Recommendation |
|---|--------|----------------|
| 1 | Keep definitions, bindings and values separate, and treat every derived structure (index, per-type projection) as rebuildable, with a live/replacement swap | Adapt |
| 2 | Bind each property to exactly one source, and make ingestion semantics explicit (duplicate keys, ordering, deletes) | Borrow |
| 3 | Make the conflict policy between imported data and user edits a declared, per-source setting | Borrow |
| 4 | All writes go through the engine; plain-SQL access is read-only by contract | Borrow |
| 5 | Detect concurrency conflicts at property granularity: OSv1 had false conflicts, OSv2 has weaker guarantees | Adapt |
| 6 | Classify schema changes by whether affected data (especially edited data) exists, and ship a finite, explicit migration set with a cast table that fails instead of coercing | Borrow |
| 7 | Fail loudly, never coerce silently, and never drop (OSv2 still drops bad streaming records) | Borrow strictness, avoid dropping |
| 8 | Do not conflate absent, null, missing-source-row and redacted values (OSv2 shows all four as null) | Avoid |
| 9 | Bounded 1–3 hop traversal serves OSv2's operational workloads; flag approximate results | Adapt |
| 10 | First-class edges with identity and properties remove the need for OSv2's "object-backed link" workaround, and multiplicity enforcement must be reported | Adapt |

## 1. Object model: types, keys, links, interfaces, value types, property types

### 1.1 Object types, primary keys and title keys

**What OSv2 does.** An object type has one primary-key property, one title
property, API names, a status and a visibility [P57]. OSv2 forbids real numbers
(decimal, double, float), geopoints, geoshapes, arrays and time series as primary
keys [P3]. Palantir discourages time-based keys because the storage format can
differ from the display format, and Long keys because "Long has representational
issues in Javascript" [P13]. Actions cannot edit a primary key; "Modifying the
primary key is equivalent to deleting an object and then adding a new object"
[P32]. The migration framework "does not support applying migration
instructions on the primary key property" [P5]. A consultancy explainer is
summarised as calling the wrong primary key "the most common reason an ontology
gets rebuilt" (search summary) [P78].

**Why it matters for truss.** UMF's key work (TD-044, alternate keys,
referenceable keys, equality edge cases) was handed to UMF on 2026-09-24
([[truss.vision-input]] §UMF Gaps Handed to UMF). truss already plans a key table
with canonical byte encodings ([[truss.vision-input]] §Draft Storage Layers).
OSv2's rules show what a mature system does when key equality is unclear: it
bans the types whose equality is ambiguous (binary floating point) and treats a
key change as a new identity.

**Recommendation: Adapt.** Accept only key families with exact equality under
truss's canonical encoding, and report any other key as not enforceable rather
than silently accepting it. Unlike OSv2, keep an internal object identity
separate from the business key, as the draft layer design already does (graph
objects share one id space). A key change can then be recorded as a change
rather than a delete and create, and history survives it. Support alternate and
composite keys once UMF specifies them. OSv2 publishes neither [P57].

### 1.2 Link types and many-to-many representation

**What OSv2 does.** There are three bindings [P20]:
- **Foreign key** for one-to-one and many-to-one: a property on one type refers
  to the other type's primary key.
- **Join table** for many-to-many: a dataset of primary-key pairs, one column
  mapped to each side. It "is required to enable users to edit or write back to
  the link type", and a join table can be generated automatically.
- **Object-backed**: an intermediary object type linked many-to-one to both
  sides, which is the only way to put properties on a link.

Cardinality is ONE or MANY per side [P58]. "The one-to-one cardinality serves as
an indicator of the intended relationship, but ... is not enforced" [P20]. Link
reads warn that returned "primary keys ... may not exist anymore" [P61]. Links
across ontologies are "not supported" [P18]. Foreign-key links are created by
editing the foreign-key property, many-to-many links by dedicated rules [P31].
The edit-history API returns object edits only: "link edits are not included"
[P64]. Ontology SQL exposes many-to-many link tables with generated column
names such as `person_vehicles` [P37].

**Why it matters for truss.** truss's draft design makes edges first-class,
sharing the object id space, with endpoints and order ([[truss.vision-input]]
§Draft Storage Layers), and UMF's relationship work (association, multiplicity
at each end, lifecycle, relationship attributes, inverse names) is open
([[truss.vision-input]] §UMF Gaps). OSv2 shows the cost of not having first-class
edges: link attributes need a whole extra object type, link history is missing,
and multiplicity is advisory.

**Recommendation: Adapt.** Keep first-class edges with properties and history.
Offer OSv2's three physical shapes as *bindings* of one logical edge: a
foreign-key column in a `shaped` table, an edge table in `generic` storage, and
a reified edge object. Differential tests should show the three answer the same
queries ([[truss.concerns]] `umf-fidelity` vs. performance conflict). Report
multiplicity and dangling-reference enforcement per link in the binding report
instead of leaving them advisory. OSv2's sentence "is not enforced" is a prose
enforcement report; truss's version should be machine-readable
([[truss.product-vision]] §Key Value Propositions).

### 1.3 Interfaces and shared properties

**What OSv2 does.** Interfaces are abstract shapes with properties (defined on
the interface or via shared properties), multiple inheritance and link-type
constraints (target interface or object type, ONE or MANY, required or optional).
Object types may implement several interfaces [P21][P22][P69]. Support is
partial: the Object Set Service can search and sort by interface, but
aggregation and interface link types are "in development" [P21]. The Ontology
SQL page says interfaces are queryable in its introduction but "Not supported"
in its feature table [P37]. Shared properties share *metadata* across object
types; "the underlying object data is not" shared [P23].

**Why it matters for truss.** Polymorphic queries ("all Facilities") are a common
reason to use a graph. OSv2 shows that interfaces are cheap to define and slow
to support end to end.

**Recommendation: Adapt.** Wait for UMF to define abstract types before truss
implements polymorphic storage. When it does, compile interface queries to
unions over implementing types and publish per-surface support (query,
aggregate, write) with evidence, rather than a blanket "interfaces supported".

### 1.4 Value types

**What OSv2 does.** Value types are "semantic wrappers around a field type" with
constraints: enum; range (for strings, length; for arrays, size); regex with an
optional partial match; RID; UUID; array uniqueness and element constraints;
struct-field constraints [P24][P25]. The base type and constraints are
immutable per version, changing constraints creates a new version, and
non-breaking versions "automatically propagate to the Ontology" [P26]. Value
types are scoped to a space, not available in the Default ontology [P24], and
enforced at indexing: data that fails validation makes the object type "fail to
index" [P53]. A community feedback post dated 2026-02-05 asks to "Make Value
Type constraints more useful in action types" (search summary; the thread was
not read) [L1].

**Why it matters for truss.** UMF facets are the analogue. truss's enforcement
report needs to say *where* each facet is enforced. OSv2 enforces value types
when it indexes datasource data; whether Actions enforce them is not clearly
documented.

**Recommendation: Borrow** versioned, immutable constraint sets (a schema
revision pins facet versions), and record the enforcement point per write path
(import, engine write, raw SQL) in the binding report.

### 1.5 Property types and their limits

**What OSv2 does** (as of 2026-09-24):
- Base types: boolean, byte, short, integer, long, float, double, decimal,
  string, date, timestamp, geopoint, geoshape, attachment, media reference,
  time series, vector, cipher text, marking, struct and array [P55].
- "All field types are valid base types except for Map and Binary types" [P14],
  and there is no time-of-day type [P49][P55].
- Timestamps travel as ISO 8601 in UTC [P54].
- Decimal precision and scale are at most 38 [P56]. Palantir's pages conflict on
  whether Decimal works in OSv2 and in Actions [P12][P15][P17][P32].
- Structs have "a depth of one", at least one field, 12 allowed field types, and
  no array fields [P13][P15]. Arrays of structs match fields independently:
  `firstName = Harvey AND lastName = Face` matches two different elements,
  because structs "are indexed similarly to ElasticSearch object field types"
  [P15].
- Arrays: no null elements, no nesting, at most 100,000 elements; strings at
  most 12 MB [P3].
- Vectors: KNN search only, at most 2048 dimensions [P17][P34].
- At most 2000 properties per object type [P1]; streaming object types allow at
  most 250 properties and 1 MB records [P9].

**Why it matters for truss.** UMF's nine scalar families include binary data and
time of day, and truss must keep maps and absent-versus-null
([[truss.concerns]] `umf-fidelity`, `sql-exactness`). Many OSv2 limits come from
its search-index design, for example the struct-array cross-matching. They are
not general truths about typed property storage.

**Recommendation: Avoid** importing OSv2's type restrictions. **Borrow** two
things: string wire encoding for 64-bit integers and decimals (the OSDK returns
`long` and `decimal` as strings and compares them with big.js "covering longs
beyond Number.MAX_SAFE_INTEGER" [P72][P73]), and the habit of publishing every
limit with an as-of date. For arrays of structured values, make per-element
matching the default so truss never matches across elements, as OSv2's index
does.

## 2. Backing datasources versus the object layer

**What OSv2 does.**
- **Separate services.** The Ontology Metadata Service holds definitions,
  object databases hold indexes, the Object Set Service serves reads, Actions
  applies writes, and the Object Data Funnel orchestrates indexing [P1].
- **Indexes are disposable.** "All indexed data in object databases are
  considered ephemeral"; durability comes from Foundry datasets and
  Funnel-owned merged datasets [P4].
- **The pipeline.** Changelog (Funnel computes the diff of each datasource
  transaction), then merge (source changes and recent user edits joined by
  primary key), then indexing "per object database", then hydration (index
  files copied to search nodes) [P8].
- **Live and replacement pipelines.** Schema changes build a replacement
  pipeline in the background while the live one keeps serving, then swap [P8].
- **Incremental by default.** Full reindex happens when more than 80% of rows
  change in one transaction, on schema changes that need a replacement
  pipeline, or on request [P8].
- **Precise ingestion rules.** For incremental datasets "the row in the most
  recent transaction will be present in the Ontology". "You may not have
  duplicate primary keys within a single transaction" [P8]. Streams are "most
  recent update wins", and out-of-order events give "incorrect data" [P9].
- **Explicit property bindings.** Each property maps to a column, a struct
  (with nested field mappings) or an "edit-only" slot [P68][P52]. A type can
  instead be "edits only", with no backing dataset at all [P68].
- **Multi-datasource object types.** These are column-wise only: "a specific
  property of an object type must come from one—and only one—of the input
  datasources", the primary key must exist in every datasource, and there are
  at most 70 datasources per type. If one datasource has no row for a key, the
  properties it maps are "displayed as null" [P28].
- **Refined data only.** Palantir advises that the Ontology "is best used with
  highly refined data that is synthesized from a larger data asset", and notes
  that "Ontology data cannot be compressed" [P40].

**Why it matters for truss.** truss's idea is to lift property definitions out
of the data, store values in a generic form, and create value rows only where
needed ([[truss.vision-input]] §Draft Storage Layers: schema catalog, binding
catalog, instance graph, `shaped` projections for hot types). OSv2 is a working
example of the first half: definitions in a metadata service, values bound
through explicit per-property mappings, and a derived, denormalised per-object
index built from the canonical data. Where OSv2 differs, truss's plan is the
stronger one: OSv2's canonical store is a wide table per source, and its
per-object index is the only object-shaped copy. truss makes the property value
canonical and every document or per-type shape derived.

**Recommendation: Adapt.**
- Keep the binding catalog as the single place where a property meets its
  storage, with OSv2's invariant that each property has exactly one source of
  truth.
- Treat every `shaped` projection and every value index the way OSv2 treats
  object-database indexes: disposable, rebuilt by a replacement build while the
  old one serves, and switched only when "hydrated" (ready and verified).
- Write down ingestion semantics as precisely as OSv2 does (duplicate keys in
  one batch fail; later batches win; how deletes are signalled) and include them
  in the enforcement report.
- Do not reproduce null for a missing source row; that is exactly the
  absent-versus-null distinction truss promises ([[truss.concerns]]
  `umf-fidelity`).
- *Not applicable*: Spark indexing, hydration onto search nodes and streaming
  ingestion. truss stays inside PostgreSQL ([[truss.competitive-analysis]]
  §Strategic Implications: avoid building a storage engine).

## 3. Edits and writeback

**What OSv2 does.**
- **One write path.** "OSv2 only supports user edits via Actions", and direct
  OSv1 edit APIs had to be refactored away [P2]. An Action is "a single
  transaction" [P30]. Its rules compile "to generate a single edit per object",
  include "Create or modify object(s)", and can trigger webhooks, notifications
  and schedule builds [P31]. Limits: 50 object types and 10,000 objects per
  submission, 3 MB per object edit in OSv2 (32 KB in OSv1) [P32]. A community
  post reports a real ceiling of 25,001 objects (search summary) [P75].
- **How edits land.** Edits go to the index immediately, through "a
  Funnel-managed queue that has offset tracking to support simultaneous user
  edits", and a later read "is guaranteed to contain the user edits" [P4]. They
  are made durable in a Funnel-owned merged dataset, built when datasources
  change or "every 6 hours" when edits exist [P4][P8].
- **Conflict policy.** Each datasource chooses "Apply user edits" (default: edits
  win against later source updates) or "Apply most recent value" (an edit
  applies only if newer than a UTC timestamp column in the source, compared
  against the source value and never the edited one). Edit-only properties
  always apply. "Deletions are not considered an edit", and a recreated object
  "will not inherit the previous edits" [P4]. Under "most recent value", a newer
  source timestamp can revert a user's edit back to null (Q&A, 2024-06-13) [P50].
- **Undo.** There is none: "no mechanism to directly undo a single user edit ...
  other than to make additional user edits"; the only reset is "drop all edits"
  [P4].
- **History.** Edit history is opt-in per object type and records only changes
  after it is enabled. "Disabling Track user edit history permanently deletes
  all existing edit histories" [P7]. The history API lists object edits with
  user, timestamp and action, but not link edits [P64]. Materialised copies keep
  only the latest snapshot, with retention "not customizable" [P6]. The OSv1 to
  OSv2 migration kept full history only when "preserve edit history" was chosen
  [P2][P12].
- **Concurrency.**
  - OSv1 checked every loaded object's version and threw `StaleObject` even for
    "user edits on irrelevant properties".
  - OSv2 checks only objects "directly used to generate edits", which "reduces
    the frequency of StaleObject conflicts, with a consequence of weaker
    guarantees".
  - Front-end reads are sent to `/apply` without versions [P4], and the apply
    endpoint takes no expected-version parameter [P63].
  - A 2026 community question asks how to stop concurrent Actions from
    overwriting each other (search summary) [P76].
  - Multi-call Ontology transactions exist only as a Private Beta [P65].

**Why it matters for truss.** truss plans a mutation journal and per-value origin
([[truss.vision-input]] §Draft Storage Layers; [[truss.product-vision]] §Vision)
and "cross-row constraints under an explicit isolation strategy"
([[truss.concerns]] `sql-exactness`). OSv2 is the clearest public example of
imported data and human edits living side by side, and of the choices that
arrangement forces.

**Recommendations.**
- **Borrow: an explicit, declared conflict policy per source**, stored in the
  binding catalog and shown in reports. truss's per-value origin makes this
  cheaper than in OSv2, because it can record which source won for each value.
- **Borrow: writes only through the engine.** OSv2 removed the low-level edit
  APIs because they bypassed its semantics [P2]. truss's promise that data stays
  readable with plain SQL ([[truss.product-vision]] §Key Value Propositions)
  should be read-only by contract. Writes that bypass truss cannot be journalled
  or enforced, so truss should detect such drift and report it rather than
  support it.
- **Adapt: property-granular optimistic concurrency.** OSv1 shows that
  object-level version checks produce false conflicts; OSv2 shows that dropping
  them produces lost updates. Inside PostgreSQL, truss can let a write state the
  values or versions it depends on (compare-and-set per property value) and
  rely on the database's isolation for the rest. Any claim about this needs
  evidence from real PostgreSQL ([[truss.concerns]] `verification`).
- **Avoid:** history that one toggle can delete, history without link edits,
  derived copies whose retention cannot be configured, and "no undo". A
  per-value journal makes a targeted revert a normal operation.
- *Not applicable*: webhooks, notifications, schedule triggers and other Action
  side effects. These are orchestration, not storage.

## 4. Schema evolution

**What OSv2 does.**
- **What counts as breaking.** Changing input datasources, the primary key or a
  property's data type; changing the ID of, or deleting, a property that has
  received user edits; deleting a struct field with edits; changing a struct
  field's type [P5].
- **What does not.** Display name, title key, render hints, type classes and
  visibility changes, and any change to properties that have "never received
  user edits" [P5].
- **The migration set.** Ontology Manager "will block the user from saving
  changes until they define a migration". The allowed migrations are drop
  property edits, drop struct-field edits, drop all edits, move edits, move
  struct-field edits, cast (a fixed matrix such as String→Timestamp,
  Double→Integer and Long→Integer) and revert [P5].
- **Casts fail rather than coerce.** "All existing values ... must be strictly
  compatible with the target type ... the migration process cannot
  automatically clean or coerce these values" [P3].
- **Limits.** At most 500 migrations per save, and none on the primary key [P5].
- **Serving during the change.** A saved change creates "a new schema version",
  a replacement pipeline rebuilds the index, and the new version becomes
  queryable once "fully hydrated" [P5][P8].
- **The contrast with OSv1.** In OSv1 breaking changes "will result in the loss
  of existing user edits" [P5].

**Why it matters for truss.** truss's user-experience scenario already has a
schema revision that shortens a text limit, with truss listing violating values
before accepting it ([[truss.product-vision]] §User Experience). UMF's schema
evolution requirements (FR-17 to FR-19) are stated but not designed
([[truss.vision-input]] §UMF Gaps, item 4).

**Recommendation: Borrow.**
- Classify each change by whether affected data exists. OSv2 keys on "has
  received user edits"; truss can key on "has stored values from this origin".
- Offer a finite, named migration set with an explicit cast table in which
  every lossy-looking cast (Double→Integer) fails on the first incompatible
  value.
- Record migrations in history so they can be reverted.
- Keep serving the old schema revision until the new projection is verified.
- Hand OSv2's breaking and non-breaking lists to UMF as a concrete starting
  catalogue for FR-17 to FR-19.

## 5. Indexing and query

**What OSv2 does** (as of 2026-09-24):
- **Filters and indexing.** Equality, range, `in`, `isNull`, text, regex, geo and
  interval filters [P60]. Per-property "searchable and sortable" render hints
  decide what is indexed and affect reindex cost [P17].
- **Search Around.** A default limit of 100,000 objects, with higher scale on a
  Spark-based layer by support request [P1]. Functions allow at most 3
  search-arounds on in-memory object sets and a 10-million-object result in
  OSv2, against 100,000 in OSv1 [P34]. Derived properties traverse "up to 3
  levels" [P51]. No variable-length traversal or pattern language is documented
  (profile, C6).
- **Aggregations.** Object Explorer and Workshop use `PREFER_SPEED` and "may not
  display results with full accuracy", while the OSDK and Functions request
  accuracy [P33]. Responses say ACCURATE or APPROXIMATE, and callers can require
  accuracy [P70]. Limits: 10,000 buckets, and `topValues` is approximate above
  1,000 distinct values [P34].
- **Paging.** OSv2 removed OSv1's 10,000-object paging limit ("Limitless
  paging") [P10][P61]. Snapshot paging is optional [P48]. `loadLinks` returns
  partial results beyond 100,000 links per page of 1,000 objects [P61].
- **Ontology SQL** (Beta). Spark SQL, SELECT only, 10,000 rows, a 20-second
  timeout, no struct columns, and no mixing of objects and datasets. Filters on
  computed expressions lose index use [P37].
- **Cost.** Every query type has a minimum compute-second cost, from 2 for a
  base query to 18 for Actions [P38].

**Why it matters for truss.** truss's proposed performance target covers
single-object fetch and 1–3 hop traversal ([[truss.product-vision]] §Success
Definition). The vision prefers ISO GQL or SQL/PGQ semantics
([[truss.vision-input]] §Proposed in Discussion).

**Recommendations.**
- **Adapt: bounded traversal first.** Palantir's operational applications run on
  a store with a three-search-around limit in Functions and no documented
  variable-length paths. That is evidence, though not proof, that a
  well-implemented 1–3 hop subset delivers most operational value. It supports
  truss's target and argues for putting variable-length GQL patterns after
  correctness work, in line with [[truss.concerns]] `scope-discipline`.
- **Borrow: exactness flags on results.** Where truss approximates (it should
  rarely need to), say so in the result, as OSv2's ACCURATE and APPROXIMATE
  markers do. This fits truss's enforcement-transparency stance.
- **Borrow: snapshot paging** as an explicit option.
- **Adapt: per-property indexing opt-in.** This matches "value rows only where
  needed": the binding catalog decides which properties get typed value rows or
  indexes, and says so.
- **Avoid:** approximate-by-default aggregation in general-purpose surfaces, and
  element-independent matching inside arrays of structs (section 1.5).
- *Not applicable*: Spark offload for searches beyond 100,000 objects.

## 6. Permissions and governance

**What OSv2 does.**
- **Security policies.** Object security policies give row-level security,
  property security policies give column-level security, and together they
  give cell-level security. A user who fails a property policy sees "a null
  value in place of the property value". The primary key cannot be in a
  property policy, and a property can be in at most one [P27].
- **Mandatory control properties.** These hold markings, organisations or
  classifications as data. They must be required and non-null, are validated
  "on the object storage level", and cause invalid edits to be rejected [P29].
- **Security in multi-datasource types.** Each datasource can carry its own
  mandatory control. A user without access to a datasource sees its properties
  as null [P28].
- **Materialisations** carry "the most restrictive permissions", combining source
  and policy markings [P27][P6].

**Why it matters for truss.** Row-level security on graph data is a nice-to-have
in the shared capability list. Per-property security is natural in a
property-row store, where each value is a row that PostgreSQL row-level security
could guard, and awkward in per-type tables.

**Recommendation: Adapt.** If truss ever exposes per-property security, return a
distinct "redacted" marker rather than null; OSv2's conflation is lesson 8.
Treat security labels stored as data (mandatory control) as an interesting
pattern for UMF policy metadata. *Not applicable*: a markings or classification
system, or a policy engine of truss's own.

## 7. Published scale and limits

All figures are Published by Palantir and are as of 2026-09-24 (living pages)
unless marked otherwise. None was measured here.

| Figure | Value | Context | Source |
|--------|-------|---------|--------|
| Objects per object type | "on the order of tens of billions" | Indexing scale claim; in the GA announcement of 2023-05-26 and the current overview | [P1][P10] |
| Properties per object type | 2,000 | OSv2 maximum | [P1] |
| Properties per streaming object type | 250; records at most 1 MB | Streaming datasources | [P9] |
| Datasources per object type | 70 | Multi-datasource object types | [P28] |
| Objects edited per Action | 10,000 (raisable by support request) | A community post reports a real ceiling of 25,001 (search summary) | [P1][P32][P75] |
| Object types edited per Action | 50 | | [P32] |
| Size of one object edit | 3 MB (OSv2); 32 KB (OSv1) | | [P32] |
| Batch Action calls | 10,000 per batch; 20 if function-backed without batched execution | The API `applyBatch` says "Up to 20 actions" per call, more for OSv2-only non-function Actions | [P32][P63] |
| String property size | 12 MB | Larger values should use media references | [P3] |
| Array property size | 100,000 elements | Larger sets should be links | [P3] |
| Search Around | 100,000 objects by default; 10 million result objects in OSv2 Functions (100,000 in OSv1); at most 3 search-arounds on in-memory object sets | | [P1][P34] |
| Aggregation buckets | 10,000; `topValues` approximate above 1,000 distinct values | | [P34][P70] |
| Ontology SQL | 10,000 rows; 20-second timeout; up to 6 seconds of queueing | Beta | [P37] |
| Schema migrations per save | 500 | | [P5] |
| API rate limits | 5,000 requests per minute and 30 concurrent per user; 800 concurrent for service users | | [P47] |
| Vector search | 0 < k ≤ 100; at most 2048 dimensions | KNN only, OSv2 only | [P34] |
| Streaming latency | "on the order of seconds or minutes" | No numeric service-level target found | [P9] |
| Edit throughput (edits per second) | Not published | Searched [P1][P4][P10][P32], 2026-09-24 | none |
| Links per object type, links per object | Not published beyond the `loadLinks` paging caveat (100,000 links per 1,000 objects) | | [P61] |

**Lesson for truss.** Publish limits in this form from the start, with the
PostgreSQL version and the evidence behind each figure
([[truss.product-vision]] §Success Definition, "Evidence-backed claims"). Do not
set targets from OSv2's numbers: they describe a distributed index service, not
a library inside one PostgreSQL database.

## 8. OSv1 to OSv2: what changed and why

Palantir's own account of the rewrite points to what failed in OSv1.

| OSv1 (Phonograph) | OSv2 | Stated reason or effect | Source |
|-------------------|------|-------------------------|--------|
| "a large API surface area, exposing significant amounts of low-level database functionality directly" | Objects synced "through the Object Data Funnel service into specialized object databases"; edits only via Actions; the Object Set Service has no query-string support | "scale, performance, flexibility, and security improvements"; separating concerns required refactoring queries | [P2] |
| Indexing and querying consolidated in one system | "separating the subsystems responsible for indexing and querying data" | "can scale horizontally more easily" | [P1] |
| Full reindex on every SNAPSHOT transaction | Incremental indexing by default, with Funnel computing the changelog | Faster indexing; the "changelog python decorator" became obsolete | [P2][P8][P11] |
| Breaking schema changes lost user edits | Schema migration framework for edits | "flexible and iterative workflow building" | [P5] |
| Empty strings "silently converted to nulls"; looser validation | Strict data restrictions; indexing fails on violations | "improve the quality of data going into the Ontology, ensure more deterministic behavior" | [P2][P3] |
| Object-level version checks; `StaleObject` on irrelevant property edits | Checks only objects used to generate edits | Fewer conflicts, "weaker guarantees" | [P4] |
| 10,000-object paging limit | "Limitless paging" | API consumers can load more than 10,000 objects | [P10][P61] |
| Writeback datasets required, schema copied from the source | Optional materialisations; schema from Ontology API names; multiple materialisations | "increase the legibility of the Foundry Ontology" | [P6] |
| One sync job with health checks | Live and replacement pipelines; monitoring views | Schema changes without downtime | [P8] |
| Search Around result limit 100,000 | 10 million (Functions) | | [P34] |
| Edit size 32 KB | 3 MB | | [P32] |

The move was mandatory for every object type. Edits were disabled while an
object type migrated, full history was kept only if chosen, and OSv1 is "unavailable after June 30,
2026" [P11][P12].

**Lessons for truss.**
- **Design derived structures to be incremental and rebuildable from day one.**
  OSv1's full reindex is the scaling failure OSv2 had to fix. Adapt.
- **Do not publish a low-level storage API you will have to withdraw.** OSv2 had
  to break customers to narrow OSv1's surface. truss should expose a typed
  mutation API and a read-only SQL contract, never "write your own rows into our
  tables". Borrow.
- **Strictness is much cheaper at the start than later.** OSv1's silent
  conversions became a published list of breaking changes. truss's `strict` and
  `report` loss modes ([[truss.concerns]] `umf-fidelity`) are the right default.
  Borrow.
- **Plan how edits and the journal survive schema changes before the first
  release.** Adapt.
- **State concurrency trade-offs explicitly.** OSv2 bought fewer conflicts with
  weaker guarantees and documented it; truss should document its choice at least
  as clearly. Borrow.
- **Keep the physical layout behind a stable logical contract.** A storage
  rewrite forced a mandatory, customer-visible migration. truss's
  `generic`→`shaped` moves should be invisible to readers and writers. Adapt.

## 9. Implications for representing Ontology concepts in UMF

Palantir's Ontology is a planned UMF interchange target; UMF's architecture lists
"object types, properties, links, interfaces, value types, actions, datasource
mappings, and policy/capability metadata" as preservation candidates (UMF
architecture). The findings above suggest where UMF has a home and where it does
not yet (UMF status as recorded in [[truss.vision-input]] §UMF Gaps and the
product vision's Why Now).

| Ontology concept | UMF home today | Note |
|------------------|----------------|------|
| Object type, property, primary key | Records, fields, keys (key work TD-044 pending) | Single-property primary key only [P57] |
| Title key, render hints, visibility, status, type classes | No home; annotation or extension metadata | Display metadata affects reindex cost [P17] |
| Link type (foreign key, join table, object-backed; ONE or MANY per side) | Relationships and physical bindings are open (FEAT-006, TD-045 to TD-049) | Join-table and object-backed shapes need binding vocabulary; one-to-one is advisory [P20] |
| Interface, interface link constraints, multiple inheritance | No home (abstract types, polymorphism) | [P21][P22] |
| Shared property (shared metadata, not data) | No home (field reuse across records) | [P23] |
| Value type (space-scoped, versioned, immutable constraints) | Partly facets; versioning and scoping have no home | [P24][P25][P26] |
| Action type (parameters, rules, submission criteria, side effects) | No home; UMF places operations in consumers, and the UMF architecture maps "selected operations as Actions" as a candidate only | [P30][P31] |
| Datasource mapping (column, struct, edit-only), multi-datasource types, edits-only types | Physical bindings (open) | [P28][P52][P68] |
| Conflict-resolution strategy per datasource | No home | [P4] |
| Object and property security policies, mandatory control, markings | Policy and capability metadata (candidate) | [P27][P29] |
| Derived properties, property reducers | No home (computed and derived fields) | [P51] |
| Geopoint, geoshape, attachment, media reference, time series, vector, cipher text, marking types | No scalar family; extension vocabularies | [P55] |

In the UMF-to-Palantir direction, loss must be reported for binary data, maps,
time of day, timestamps with offsets, absent versus null, nested arrays, arrays
containing nulls, decimals above 38 digits (and decimals at all until Palantir's
pages agree), empty strings, NaN and ±infinity [P3][P14][P17][P54][P56]. UMF's
competitive analysis already notes that the Ontology JSON export format can
change; Palantir's page says "You should not depend on the exported JSON schema
as it may change over time" [P43]. The versioned API reference at a pinned SDK tag [P54]–[P70] is the
steadier surface to target.

## What this means for the build-versus-adopt question

**Differentiators OSv2 already demonstrates, which validates them as valuable:**
- Definitions separated from stored values, with an explicit per-property binding
  catalog and multi-source bindings [P1][P28][P68].
- Explicit, documented semantics for imports, duplicate keys and conflicts
  between imported data and user edits [P4][P8].
- A write path with an edit history and migrations that carry edited data across
  schema changes [P5][P7].
- Strict validation replacing OSv1's silent coercion [P3].
- Documented enforcement points (required properties and value types at indexing
  and apply time) and documented non-enforcement (one-to-one cardinality)
  [P16][P20][P53]. This is a prose version of truss's enforcement report.
- A typed TypeScript SDK that keeps 64-bit integers and decimals lossless by
  encoding them as strings [P72][P73].

A company operating at this scale chose to build and keep these features, which
strengthens the case that truss's corresponding differentiators are worth having.

**What OSv2 lacks that truss plans** (so it neither validates nor refutes them):
- Deployment inside the customer's own PostgreSQL, with canonical data readable
  through plain SQL.
- Absent versus null, maps, binary data and time of day.
- Retention of content that matches no schema.
- Per-value provenance.
- A machine-readable, per-assertion enforcement report.
- Property-granular concurrency guarantees.
- Open governance.
- Variable-length traversal and ISO GQL alignment.

For each of these, the Palantir record shows the gap (profile C1 to C3, C6 to C8,
C10 and C11). No surveyed system combines them ([[truss.competitive-analysis]]
§Feature Comparison). Whether users want the combination is still the owner's
unvalidated hypothesis ([[truss.product-vision]] §Target Market).

**What OSv2 suggests truss should not attempt:**
- A separate search-index serving tier with hydration, Spark offload for large
  traversals, or streaming ingestion. These are the parts of OSv2 that need a
  platform team and a cluster; [[truss.competitive-analysis]] already says to
  avoid building a storage engine.
- Scale claims of Palantir's kind: tens of billions of objects per type. truss's
  claims should be named PostgreSQL versions, corpora and measured ratios.
- Action orchestration (webhooks, notifications, schedules), markings and
  classification systems, and application-layer features.
- Serving as the ingestion layer from a data lake. OSv2 is "best used with highly
  refined data that is synthesized from a larger data asset" [P40]; truss's role
  is the operational store inside PostgreSQL.

In short, OSv2 confirms that the *model* truss proposes (typed definitions,
explicit bindings, edits with history and migrations, enforcement stated per
rule) is what a mature operational graph system ends up needing. It does not
test truss's *deployment* bet (inside the user's PostgreSQL, readable as plain
SQL, lossless for UMF). That bet still rests on the benchmark and user research
the truss artifacts already call for ([[truss.competitive-analysis]] §Follow-up
research; [[truss.product-vision]] §Target Market).

## Additional source

Sources not in the component profile's list. Class vocabulary and access
conditions are as in the profile.

- L1. [Palantir Developer Community: "Make Value Type constraints more useful in action types"](https://community.palantir.com/t/make-value-type-constraints-more-useful-in-action-types/5961) (search summary), community, posted 2026-02-05 per summary, accessed 2026-09-24
