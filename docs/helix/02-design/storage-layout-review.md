---
ddx:
  id: truss.storage-layout-review
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.vision-input
      kind: informed_by
    - id: SPIKE-001
      kind: informed_by
    - id: SPIKE-002
      kind: informed_by
    - id: truss.concerns
      kind: informed_by
    - id: ADR-002
      kind: informed_by
    - id: ADR-003
      kind: informed_by
    - id: ADR-006
      kind: informed_by
    - id: ADR-007
      kind: informed_by
---

# Storage Layout Review: generic catalog storage against graph-storage practice

**Updated 2026-10-13** against `main` at `097bd38c` (v0.0.2), rechecked at
`e948dee5` (v0.0.3); see the update section first.

Design input for [ADR-002](adr/ADR-002-storage-strategy.md), accepted on
2026-10-03 with provisional points. The review evaluates the draft storage
layers in [discovery input](../00-discover/vision-input.md) §Draft Storage
Layers, as built for [SPIKE-002](spikes/SPIKE-002-storage-bake-off.md) option C
(`spikes/SPIKE-002-storage-bake-off/sql/c_schema.sql`), against published
graph-on-SQL practice. The candidate positions below preserve the review's
recommendations; ADR-002 owns the accepted decision and V1–V7 follow-up checks.
Written 2026-10-03. Nothing here has been run beyond what SPIKE-002 reports. Claims marked
"inferred" come from PostgreSQL documentation or source and were not executed
in this project.

Terminology: UMF is DocumentDrivenDX's machine-readable metamodel and schema
interchange fabric. SQL is Structured Query Language; PostgreSQL JSONB is its
binary JSON storage type. EAV means entity-attribute-value storage, FK means
foreign key, and p95 is the 95th percentile. TAO is Facebook's distributed
object and association store [1].

Concern 3 (a shared objects table growing with type count) is settled by
[SPIKE-003](spikes/SPIKE-003-partitioning-locks-and-prepared-statements.md): the
layout in [ADR-002](adr/ADR-002-storage-strategy.md) D2 is one table with a key
table, not a partition per type, and the partitioning proposals below are not
adopted.

## Update 2026-10-13: vision, specifications and the v0.0.2 implementation

This update reviews `main` at `097bd38c` (tag v0.0.2), where the Python reference
implementation now exists. It was rechecked against v0.0.3 (`e948dee5`), released
the same day. That release adds exact typed business keys (integer, decimal,
Boolean and binary key components), which settles concern 6. It leaves
`layout.sql` unchanged and does not affect the other findings: key buckets
still have no unique index, object rows are still locked `FOR UPDATE NOWAIT`,
the catalog replay remains, and the report still forces `unqualified`. The
probes below ran on v0.0.2. The sections after it are the original review of
2026-10-03, kept for its reasoning.

The update compares three things:

- the vision: [product vision](../00-discover/product-vision.md), PRD Goals, the
  `AGENTS.md` boundaries;
- the specifications: the PRD's functional requirements, ADR-001 to ADR-008,
  CONTRACT-001 to CONTRACT-012;
- the implementation: `packages/python`, release v0.0.2.

Features the README marks unfinished are excluded: multi-hop queries,
structured values, broader imports and managed-service qualification.

**Method.** All observations come from one Linux x86_64 machine, using
Python 3.11, Bun 1.4.2 and PostgreSQL 18.6 from `pgserver-pg18` 18.6.1.

- **Install:** truss 0.0.2 was installed from its release wheels.
- **Adopter workflow:** `packages/python/examples/adopter_workflow.py` ran end
  to end. It covered catalog acceptance, mutation, receipt replay, a key
  lookup, a relationship query, a dry run, an import and feed
  acknowledgement.
- **Probes:** the public Python API was probed directly.
- **Test suite:** 1,601 passed, 376 failed and 489 errored. Nearly all
  failures were environmental: hard-coded `/private/tmp` and
  `/opt/homebrew` paths, an undocumented `TRUSS_CENSUS_POSTGRES_BIN`, and a
  missing `pg8000`. Continuous integration runs only a smoke check.
- **Source:** findings marked *source* were read from the installed SQL under
  `packages/python/src/truss/_catalog_runtime/` and were not executed.

### Verdict

The storage idea at the centre of the vision has held up in code:

- a catalog revision adds rows, not DDL;
- values round-trip exactly;
- unknown data is retained;
- the database enforces edge endpoint types;
- the journal records per-property changes with a database-derived role.

The gaps are elsewhere:

1. **The specification and the build have split.** The normative layout
   (CONTRACT-001, `storage-layout.sql`, "layout 0.2") no longer describes what
   is installed. The installed layout calls itself
   `source-epoch-0.16 REVIEW ONLY - unqualified`. Superseding ADRs or contract
   revisions do not record the split.
2. **Two headline promises are not delivered, and nothing tracks that.** The
   vision's primary KPI, an enforcement status per assertion, is structurally
   empty. "Readable with plain SQL" has no requirement behind it.
3. **The write path has grown expensive and unbounded.** The cost of one write
   grows with catalog history. Every write keeps several permanent full
   copies of the object. The journal has a fixed 14-month horizon.
4. **The documents contradict each other** on the implementation language,
   ADR status, supported PostgreSQL versions and counts.
5. **Specification volume now hides the specification.** The PRD has 56 FRs.
   There are 12 contracts of about 12,100 lines, about 700 proposal files under
   `02-design`, and 485 evidence directories. There is no glossary and no
   short, readable statement of the layout and write protocol.

### Vision promises against the implementation

| Vision promise | State in v0.0.2 | Evidence |
|---|---|---|
| A new entity or relationship is a UMF revision, not a migration | **Delivered.** A revision adding a type and a property left `pg_class`, column and index counts unchanged | Observed |
| Values stay exact | **Delivered.** int64 overflow values, 2^53+1, `10.10`, timestamps with offset, binary, and null versus absent all round-trip. U+0000 is refused, but with a misleading message | Observed |
| Nothing silently dropped | **Partly.** Unknown fields are kept in `retained` but are not reported in the write result. A later revision that defines a retained name is refused (`property.retained_name_collision`) instead of re-binding it (FR-11) | Observed |
| Every value carries its type, revision and origin | **Partly.** Journal rows carry definition pins and an origin with a database-derived role. `old_value` is always NULL, and `new_value` is a base64 envelope, so history cannot be read as JSON in SQL | Observed; `layout.sql` |
| Enforcement report: database, engine or none per assertion (primary KPI) | **Not delivered.** Every assertion is reported `enforcement: none, reason: unqualified`, including rules the engine and database do enforce. The report assembler rejects any other value until native qualification (`_catalog_report_assembly.py:129`). STP-025 still names Bun tests that do not exist | Observed; source |
| The database enforces keys | **Not delivered.** `object_key` was replaced by `object_key_bucket` with only a non-unique route index. Two raw inserts with the same key both committed. Uniqueness is now engine-only, through advisory locks and a guard row (FR-12, FR-35) | Observed; `layout.sql` |
| Readable with plain SQL | **Not delivered.** `props` is keyed by opaque property id, values are tagged cells, keys are byte strings, and no views exist. Typed views are P2, and no requirement covers plain-SQL readability | Observed |
| Tightening a rule lists every violator before acceptance (FR-5) | **Partly.** It is refused with a count (`affected_object_count=7`), not with object ids | Observed |

### Specifications against the implementation

| Point | Specification | As built | Severity |
|---|---|---|---|
| Layout | CONTRACT-001 layout 0.2, 19 tables; `storage-layout.sql` (its own header says 0.1) | 63 tables, layout profile 0.16, marked unqualified, on PostgreSQL 18.6, which the contract check never ran on | High |
| Value encoding | ADR-002 D3: JSON numbers in lexical form, JSON `null`. ADR-006: catalog-directed untagged token strings | Tagged cells, `{"kind":"decimal","text":"10.10"}` and `{"kind":"null"}` (`scalars.sql`). This matches neither ADR | Medium |
| Journal | ADR-002 D7 and CONTRACT-002: old and new value per property | `old_value` always NULL. `new_value` and `origin` are exact-byte envelopes. An undocumented `op='metadata'` row holds full before and after records (ADR-007 direction, not reflected in CONTRACT-002) | Medium |
| Row locking | ADR-002 D9: `FOR NO KEY UPDATE`, waits | `FOR UPDATE NOWAIT` on object rows (`operations.sql:240,608,845`). Concurrent writers fail fast with 55P03 instead of queueing, and the lock conflicts with the key-share locks taken by edge foreign keys | Medium |
| Error kinds | CONTRACT-004: `endpoint_violation`, `edge_exists`, `has_edges`, `key_reserved`, `invalid` with violations | Returns `invalid_input`, `key_conflict` and `dependencies`. `invalid` carries no rule, path or layer | Medium |
| Edge properties | ADR-002 D6: `edge.props` keyed by property id | Typed edge properties are refused; values go to `edge.retained` | Medium |
| Interchange | ADR-003 body: "interchange check against the TypeScript engine" | The ADR-003 amendment (2026-10-13) removes mandatory interchange, but the body still requires it. No TypeScript engine exists | Low |
| Core isolation | ADR-001 D2: host-neutral core | Python core modules import psycopg directly | Low |

### Vision against the specifications

- **Implementation language.** The vision input, ADR-001's status row,
  `AGENTS.md`, the PRD Summary (line 58, "TypeScript reference implementation"), PRD Platform Targets (line 282, "Bun first") and the
  design README ("embeddable TypeScript toolkit") all say TypeScript. Accepted
  ADR-003, the README and PRD line 278 say Python. ADR-001 needs an explicit
  amendment or a superseding note in its status row, and the other documents
  must follow it.
- **Persona and scope.** The vision's user is a data platform engineer with
  UMF schemas. The specifications are now driven by one embedding
  application: a trusted embedding host (ADR-008), authority and membership,
  disclosure, receipts, feeds and managed-service targets. The PRD's
  non-goals still say truss does not authenticate people. Either bring this
  scope into the vision and PRD as owner-approved requirements, or park it.
  Technical design TD-020 cites US-056 and US-057, which do not exist; the
  stories stop at US-045.
- **Support claims.** FR-34, ENF-03 and the README's PostgreSQL 18.6 claim
  dropped the "subset" qualifier the vision requires, and the README claim
  links no evidence.
- **PostgreSQL versions.** The README and PRD line 327 say 18.6. PRD line 280
  says 16 and 17 were tested and 18 is unverified. `AGENTS.md` says "18
  untested". The PRD open question is still unchecked.
- **Query language.** The PRD has settled on Weft's query surface, but
  `AGENTS.md` and the vision input still list the query language as open.
- **Performance.** The PRD deferred the latency targets, so the vision's
  performance measure has no owner. No figure exists for the as-built layout;
  the only numbers are SPIKE-003's, from the prototype layout.

### Status of this review's original concerns

| # | Concern (2026-10-03) | Now |
|---|---|---|
| 1 | Every write is an object-level write | **Worse.** A one-property update also writes two journal rows (one with full before and after records), an attempt row with two or three updates, and a transition row with full images. Receipt rows are added when a request id is given. All of these are immutable and never pruned (*source*) |
| 2 | Nested records as child objects; `root_id` | Open. `root_id` exists, but the runtime refuses rooted objects; structured values are unfinished |
| 3 | Shared table and type count | Settled by SPIKE-003, with one object table |
| 4 | Canonical store | Object row is canonical; the journal changed shape (ADR-007) |
| 5 | Property identity across revisions | Settled: definition pins appear in every event |
| 6 | Numeric kinds colliding in keys | Settled in v0.0.3: typed key components, and decimal-equivalent tokens identify the same key |
| 7 | `jsonb_set` NULL | Settled (`props NOT NULL`) |
| 8 | Endpoint types enforced by the database | Settled; foreign keys observed refusing a raw insert |
| 9 | Edge properties | Open; typed edge properties are refused |
| 10 | Ordered edges | Partly done: free-text order keys, with no generator |
| 11 | Planner statistics | Open; no `CREATE STATISTICS` anywhere |
| 12 | Disk footprint | Worse (see 1). V1–V7 have not been measured |

Two more storage risks, both from *source*:

- **Write cost grows with catalog history.**
  `truss.catalog_all_expected_records` rebuilds the expected catalog by
  replaying every registration request from genesis. The write and read paths
  call it (`operations.sql:308`, `runtime.sql:105-138`). This works against
  the PRD's catalog-independence goal.
- **The journal has a fixed horizon.** The installer creates one journal
  partition covering 14 months and no default partition (`groups.sql:146-151`).
  Without a partition-maintenance job, writes will fail once that horizon
  passes.

### Documents that contradict each other

- **ADR status.** All eight ADR files say `accepted`. `AGENTS.md`, the design
  README ("ADR-003–007 remain proposed") and `architecture.md:62` say
  otherwise.
- **`AGENTS.md` counts and state.** It says 50 FRs, 39 stories, five
  contracts, layout 0.2 and "no implementation exists". The actual figures are
  56, 45 and 12, layout profile 0.16, and a shipped Python runtime. It also
  points to `docs/helix/parking-lot.md`, which does not exist. The commit that
  created the file was never merged.
- **PRD Technical Context.** It says "APIs: none yet", "pre-build" and "Bun
  first".
- **Helix README.** Its "Next action" line conflicts with its own list of
  available operations.

### Recommendations, in order

1. **Record the as-built layout as the contract, or name the gap.** Publish
   layout 0.16 as CONTRACT-001's normative DDL, or add an ADR that supersedes
   ADR-002 D3, D7 and D9 and CONTRACT-001/002 where the build deliberately
   differs. Run the layout check on PostgreSQL 18.6.
2. **Make the primary KPI real.** Report `database` or `engine` for the rules
   that are enforced today: endpoint foreign keys, `edge_limit`, required
   properties and scalar types. Keep `none` only where nothing enforces.
   Re-home STP-025 to the Python harness.
3. **Restore database key uniqueness,** for example with a unique index on
   `(type_id, key_num, key_sha256)` plus a byte comparison. Otherwise change
   FR-12 and FR-35 and report keys as engine-enforced.
4. **Bound the write path.** Replace the genesis replay with a cached,
   revision-keyed expected catalog. Decide retention for the transition and
   attempt tables. Add journal partition maintenance or a documented operator
   job. Then measure V1 and the 3 ms write target on the as-built layout.
5. **Plain SQL.** Add catalog-driven read views, or a function that returns
   name-keyed JSON, with no per-type DDL. Alternatively, change the vision
   statement.
6. **Align the documents** listed above in one pass. Add a glossary and a
   short "truss in one read" document covering the layout, write protocol,
   enforcement report and journal.
7. **Make the tests portable.** Parameterize the machine paths, document the
   environment variables, add `pg8000` to an extra, and run the full suite in
   CI.

## Summary (original review, 2026-10-03)

Option C is a well-established shape: a typed object table plus a typed
association table, with a catalog that holds the schema. Facebook's TAO used the
same split, with one object table and one association table per MySQL shard and
custom tables for types that needed them [1]. It also matches the hybrid
entity-attribute-value designs that Dinu and Nadkarni recommend (cited in the
[competitive analysis](../00-discover/competitive-analysis.md)). Packing values
into one JSONB map per object avoids the classic EAV cost of joining many rows
to rebuild one object. Relational engines are competitive on 1–3 hop
transactional traversals when edges are well indexed [2], and SPIKE-002 agrees:
p95 within 2× of per-type tables for fetch, one hop, range and update, with two
hops at the boundary.

The review finds no reason to reverse SPIKE-002's recommendation. It finds five
points the ADR should settle explicitly, because the layout either leaves them
undecided or makes a costly default:

1. Per-property storage is logical only. PostgreSQL versions, locks and logs
   whole rows, so every write is an object-level write.
2. Nested records always become child objects, which multiplies rows, edges and
   joins for aggregate-shaped reads.
3. One shared objects table scales badly with the number of types. SPIKE-002
   measured this, and partitioning by type is the evident mitigation.
4. Which store is canonical, the object row or the journal, is not decided.
5. Property identity across schema revisions is implied by the spike but not
   stated.

## Concerns and their status after SPIKE-002

| # | Concern | SPIKE-002 status | Proposed ADR position |
|---|---------|------------------|------------------------|
| 1 | Per-property storage is logical only: object-level write physics | **Open** (not measured) | State it; bound map size; measure |
| 2 | Nested records always become child objects | **Open** (kept, not costed) | Separate value records from entities; add `root_id` |
| 3 | One shared objects table grows with type count | **Confirmed** | Partition objects by `type_id` |
| 4 | Canonical store: object row or journal | **Open** | Decide; record it |
| 5 | Property identity across revisions | **Implied** (R4 kept the id) | State the rule |
| 6 | Numbers of different kinds colliding in keys | **Resolved for typed keys** | Keep typed key expressions |
| 7 | `jsonb_set` with SQL NULL nulls the whole map | **Guarded** by `props NOT NULL` | Keep the constraint |
| 8 | Endpoint types enforced by the database | **Confirmed** (`rel_endpoint` FKs) | Adopt; use `FOR NO KEY UPDATE` |
| 9 | Edge properties (relationship attributes) | **Open** (edges carry none) | Decide where they live |
| 10 | Ordered edges | **Open** (`ordinal int`) | Use fractional order keys |
| 11 | Planner statistics for JSONB filters | **Open** (key-driven queries only) | Declared statistics; measure |
| 12 | 4.8× disk footprint | **Confirmed** | Decide edge identity; measure compression |

### 1. Per-property storage is logical only

The vision makes the property value the unit of identity, typing, indexing,
mutation and enforcement. Physically, every write goes through the object row:

- **Whole-value rewrite.** `jsonb_set` produces a new JSONB value. Once a map
  passes the TOAST threshold (about 2 KB), each single-property update
  decompresses, rewrites, recompresses and logs the whole value [3][4].
- **No cheap in-place (HOT) updates.** An update is heap-only only when no
  indexed column changes. Option C's generated key indexes are expression
  indexes on `props`, so every update of any property in any object with such
  an index takes the non-HOT path and touches every index on the table
  (inferred from PostgreSQL's HOT rules). A patch that evaluates expression
  indexes to allow HOT was moved from the PostgreSQL 19 to the PostgreSQL 20
  commitfest [5].
- **Row-lock contention.** Two transactions updating different properties of
  the same object queue on one row lock. The vision input names contention as
  the reason for `row` storage homes; object size and write rate are reasons
  too.

SPIKE-002's update shape set one property (`Order.status`) on 20 hot rows from
two writers, on small maps. It did not measure log volume, HOT ratio,
different-property contention or growth with map size.

Proposed ADR position: say plainly that the journal, not the storage row, is the
per-property record. Give the binding a rule that moves a property to a `row`
home when it is large or written often, not only when it is contended. Add the
measurements in §Follow-up measurements.

### 2. Nested records always become child objects

The layout rule "nested records become child objects, never nested JSON" holds
in the spike: `Customer.address` is a child object linked by a composition edge.
That keeps every nested value individually addressable, but:

- An Order with 50 lines is 51 objects and 50 edges. Reading it as a document
  needs a traversal per level.
- Part of the 4.8× footprint is this rule. The edge table alone was 178.1 MB of
  C's 304.7 MB.
- The vision's performance target names "single-object fetch". Users will also
  fetch aggregates, and the spike did not measure that shape.

Proposed ADR position:

- Store a record type that has no identity of its own (a UMF value record such
  as Address or Money) as a structured value in the map. Its sub-fields are
  still typed and validated through the catalog. Only records with identity
  become objects. This needs a binding rule and a statement of what is lost:
  per-sub-field journal entries and edges into the value.
- Give every composed object a `root_id` (its aggregate root), indexed and
  co-partitioned with the root. A document view is then one index range scan,
  not a recursive query.
- Add aggregate fetch (root plus N children) to the benchmark shapes.

### 3. One shared objects table grows with type count (confirmed)

SPIKE-002 measured the costs:

- Planning grew from about 1.1–1.4 ms to 7.6–8.0 ms going from 5 to 105 types
  with partial indexes on one table (`out/53_planner_probe_pg17.txt`).
- Conditional CHECKs cost about 14 µs per constraint per statement, for every
  type's rules on every insert, and need `ACCESS EXCLUSIVE` on the table every
  type shares (FINDING 4).

Other costs of one shared table:

- `CREATE INDEX CONCURRENTLY` for a new index on one type scans the whole graph.
- Autovacuum and planner statistics are shared across all types (inferred).

LIST-partitioning by `type_id` kept planning at 1.0–1.9 ms with 105 types at
equal latency (`out/54_partition_probe_pg17.txt`). PostgreSQL requires unique
constraints on a partitioned table to include the partition key, so `id` is no
longer unique by constraint across partitions. Uniqueness then rests on the
shared sequence, and references must target `(id, type_id)`. Option C already
carries `(source_id, source_type)` and `(target_id, target_type)` on edges for
the typed endpoint FKs, so the fit is natural. The existing 16.3 MB `(id, type_id)`
unique index becomes the primary key rather than an extra index. Thousands of
partitions bring their own planning cost (inferred), so a default partition for
long-tail types is likely needed.

Proposed ADR position: partition objects by type in the first build, with
per-partition indexes and no per-type CHECKs on shared tables. Whether to
partition edges by relationship type follows from the traversal benchmarks.

### 4. Canonical store: object row or journal

Every journaled write adds a journal row with old and new values. This moved the
update shape's p95 from 0.383 to 0.463 ms in SPIKE-002. Two coherent positions:

- **Object row canonical.** The journal is an audit trail. As-of reads are
  best-effort, and losing journal rows does not lose current state.
- **Journal canonical** (Datomic/XTDB style). Current state is a rebuildable
  projection. As-of reads and provenance are exact, but the journal must be
  complete, ordered and replayable, and rebuild time becomes an operational
  limit.

The [OSv2 design lessons](../00-discover/design-lessons-palantir-osv2.md)
(rebuildable indexes from durable data) favour the second. The vision's
per-property history favours either. The ADR should choose. Either way, the
journal should be partitioned by time so retention is a partition drop.

### 5. Property identity across revisions

In the spike, `prop_def` carries `since_rev`, and R4 (`Customer.email` one →
array) kept the same `prop_id` and transformed stored values in place. That
implies a rule: a property keeps its id across revisions, and an incompatible
change rewrites the affected values. The ADR should state the rule and its
limits:

- which changes keep the id (facet changes, cardinality widening with a
  transform);
- which changes mint a new id (scalar family change without a total
  conversion?);
- how retained data is re-bound when a later revision defines a field it
  matches.

The earlier key-size concern is resolved: map keys are compact catalog integers
rendered as text (`'12'`), not qualified names.

### 6–8. Encoding and enforcement details

- **Numeric kinds in keys (6).** JSONB treats `1` and `1.0` as equal, so untyped
  JSONB keys would conflate integer, float and decimal. SPIKE-002's key indexes
  cast to the declared type (`((props->>'1')::bigint)`, text with
  `COLLATE "C"`), so typed keys do not collide. The hazard remains for keys over
  untyped or retained values, which should not be allowed.
- **`jsonb_set` and SQL NULL (7).** `jsonb_set` is strict, so a SQL NULL new
  value returns NULL for the whole map. `props jsonb NOT NULL` turns that into
  an error instead of silent loss, so the constraint should stay. The write path
  must still render explicit null as `'null'::jsonb`.
- **Endpoint types (8).** The `rel_endpoint` table with composite FKs gave
  database enforcement of endpoint types with no DDL per relationship
  (FINDING 4, R1). Its costs, also observed: three FK checks per edge made the
  bulk load slow, and `FOR UPDATE` on objects stalls edge inserts. The write path
  must use `FOR NO KEY UPDATE`, as SPIKE-002 recommends.

### 9–10. Edges

- **Edge properties (9).** Edges take ids from the object sequence but carry no
  properties. UMF's relationship work (attributes are one of the gaps handed to
  UMF) will need them. A separate object row per edge with properties adds a
  join per hop whenever a traversal filters on an edge property. A `props`
  column on the edge row, keyed by the same catalog ids, avoids that join.
- **Ordered edges (10).** An integer `ordinal` forces renumbering on insertion
  in the middle of a list, which rewrites many edge rows under contention. Use
  fractional (lexicographically sortable text) order keys so an insertion writes
  one row.
- **Traversal indexes.** The generic `(source_id, rel_type_id) INCLUDE
  (target_id)` and reverse indexes already gave index-only scans after VACUUM.
  SPIKE-002 proposes adding `target_type` to the covering columns for the
  two-hop tail. Index-only scans depend on the visibility map, so autovacuum on
  the edge table needs tuning for write-heavy graphs (inferred).

### 11. Planner statistics for filters on JSONB values

PostgreSQL keeps no per-key statistics inside a JSONB value. Predicates on
values without an expression index fall back to fixed selectivity estimates [6].
Expression indexes give `ANALYZE` statistics for the indexed expression, and
`CREATE STATISTICS` on expressions (PostgreSQL 14+) covers correlated
predicates. SPIKE-002's shapes all start from a key or an indexed range, so
estimate quality was not exercised. Multi-predicate filters and joins whose
estimates drive join order are where generic storage usually loses to typed
columns [7].

### 12. Disk footprint

C used 4.76× A's space at the plan's scale and 4.81× at 5×. The edge table and
its indexes dominate. Drivers the ADR can act on:

- the edge `id` primary key, which exists only because edges share the object id
  space;
- the `(id, type_id)` unique index, which partitioning turns into the primary
  key;
- the composition rule (§2);
- JSONB storage of keys per row and default compression. SPIKE-002 proposes
  measuring compression.

Whether edges need their own identity is a product question: it matters for
per-edge provenance, journal entries and edge properties.

## Candidate design rules

These rules follow from the evidence above and SPIKE-002's design constraints.
They are proposals for the ADR and the PRD's non-functional requirements.

| Rule | Basis |
|------|-------|
| **Versioned catalog cache.** Engines cache the compiled catalog, keyed by schema revision, and every write transaction verifies the revision it validated against (for example `FOR SHARE` on the current `schema_rev` row). | SPIKE-002 risk: engines enforcing a stale catalog after a revision |
| **Declared indexes only.** The engine creates only indexes declared by the binding, and never adds them in response to queries. Index count per partition is a reported budget. | Planning cost grows with index count (FINDING 7); every expression index on `props` blocks HOT updates (§1) |
| **Declared statistics.** Bindings may declare extended statistics for property combinations used together in filters, created per partition. | §11 |
| **Refuse rather than degrade.** The engine refuses work it cannot do within its guarantees: unprepared execution where the 2× target depends on preparation, a revision with violators, a write it cannot validate. It reports the refusal rather than silently running slower or unenforced. | C missed 2× by 2.8–6.6× unprepared (FINDING 7); the vision's no-silent-loss rule |
| **Bounded traversal first.** The query compiler supports fixed-depth patterns before variable-length paths, and variable-length paths carry an explicit depth bound. | SPIKE-002's fixed patterns met or approached 2×; SPIKE-001's variable-length cache cost 577 ms p95 under writes |
| **Parent lock for cross-row rules.** Minimum-multiplicity and aggregate rules lock the parent object (`FOR NO KEY UPDATE`) or run SERIALIZABLE. | Deferred triggers raced under READ COMMITTED in both options (FINDING 4) |

## Alternatives not covered by SPIKE-002

SPIKE-002 compared UMF-generated per-type tables (A) with generic catalog
storage (C). Three other layouts deserve a line in the ADR's alternatives
section:

| Alternative | Gains | Costs |
|-------------|-------|-------|
| One row per value with Datomic-style covering indexes (EAVT, AEVT, AVET, VAET) | The only layout where versioning, locking and logging are truly per property | Object fetch rebuilds rows; Apache Jena SDB's generic triple table lost to native storage. Open question 1 in the [Datomic profile](../00-discover/component-profile-datomic.md) |
| Typed columns for hot properties plus a JSONB overflow map per type | Most of A's read and write cost with C's long tail | Two value paths; covered by the planned `shaped` strategy and its differential tests |
| Adjacency lists stored on the node row (arrays of edge ids) | Fast neighbour reads | Write contention on high-degree nodes, no foreign keys, rewrite on every edge change; rejected |

## Follow-up measurements

Proposed additions to SPIKE-002's follow-up spike (C partitioned by type,
realistic type counts, data larger than memory, a pooler, Node `pg`):

1. Log volume (`pg_stat_wal`) and HOT ratio (`pg_stat_user_tables`) per
   single-property update, with maps of 0.5, 2, 8 and 32 KB.
2. Throughput with concurrent writers updating different properties of the same
   object, compared with the same properties in `row` homes.
3. Aggregate fetch: a root with 1, 10, 50 and 500 composed children, as child
   objects versus structured values, with and without `root_id`.
4. Planner estimate error (estimated versus actual rows) for filters on
   unindexed properties, indexed properties and two correlated properties, with
   and without extended statistics.
5. Index build time for a new per-type index on a shared table versus on a
   partition, at the larger dataset.
6. Fixed two- and three-hop patterns with a property filter on an intermediate
   node and on an edge property.
7. Disk footprint with and without edge ids, with `lz4` versus `pglz` TOAST
   compression.

## Decisions for the storage ADR

- Ratify or reject option C (SPIKE-002 recommendation).
- Partition objects by type in the first build (§3).
- Canonical store: object row or journal (§4).
- Property identity rule across revisions (§5).
- Value records as structured values or child objects; `root_id` (§2).
- Edge identity and edge properties (§9, §12).
- Storage-home rule beyond contention: size and write rate (§1).
- Adopt, amend or drop the candidate design rules above.

## Sources

1. Bronson et al., *TAO: Facebook's Distributed Data Store for the Social Graph*, USENIX ATC 2013; summary at <https://blog.acolyer.org/2015/05/19/tao-facebooks-distributed-data-store-for-the-social-graph/>
2. Pacaci, Zhou, Lin, Özsu, *Do We Need Specialized Graph Databases? Benchmarking Real-Time Social Networking Applications*, GRADES 2017, <https://cs.uwaterloo.ca/~jimmylin/publications/Pacaci_etal_2017.pdf>
3. pganalyze, *Postgres performance cliffs with large JSONB values and TOAST*, <https://pganalyze.com/blog/5mins-postgres-jsonb-toast>
4. Snowflake Engineering, *Postgres JSONB Columns and TOAST: A Performance Guide*, <https://www.snowflake.com/en/blog/engineering/postgres-jsonb-columns-and-toast/>
5. *Expanding HOT updates for expression and partial indexes*, pgsql-hackers thread <https://www.postgresql.org/message-id/78574B24-BE0A-42C5-8075-3FA9FA63B8FC@amazon.com> and commitfest entry <https://commitfest.postgresql.org/56/5556>
6. pganalyze, *How to fix bad JSONB selectivity estimates*, <https://pganalyze.com/blog/5mins-postgres-planner-jsonb-selectivity>; PostgreSQL 18 documentation, *Statistics Used by the Planner*, <https://www.postgresql.org/docs/current/planner-stats.html>
7. pgsql-hackers, *Collecting statistics about contents of JSONB columns*, <https://www.postgresql.org/message-id/c9c4bd20-996c-100e-25e7-27e27bb1da7c@enterprisedb.com>
