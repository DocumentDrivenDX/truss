---
ddx:
  id: CONTRACT-001
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: ADR-002
      kind: informed_by
    - id: ADR-001
      kind: informed_by
    - id: SPIKE-002
      kind: informed_by
    - id: truss.storage-layout-review
      kind: informed_by
    - id: CONTRACT-002
      kind: informs
    - id: CONTRACT-003
      kind: informs
    - id: CONTRACT-004
      kind: informs
---

# Contract: Storage layout

**Contract ID**: CONTRACT-001
**Type**: schema
**Version**: layout 0.1 (draft)
**Status**: draft
**Related**: ADR-002 (storage strategy), ADR-001 (language and portable core), SPIKE-002, the storage layout review, CONTRACT-002 (journal), CONTRACT-003 (catalog), CONTRACT-004 (mutation and conformance)

## Purpose

Defines the fixed set of PostgreSQL tables truss stores UMF-described property-graph data in, so that any implementation, in any language, reads and writes the same tables. A conforming implementation is interchangeable with another over the same database. The executable form of this contract is [`storage-layout.sql`](storage-layout.sql), checked by [`storage-layout.check.sql`](storage-layout.check.sql). Where this document and the DDL disagree, the DDL governs and the disagreement is a defect in this document.

No PRD frames truss yet. This contract implements the accepted ADR-002 and is a draft until framed requirements confirm it.

## Scope and Boundaries

- In scope: tables, columns, constraints, partitions, sequences, indexes, identity, value encoding, deletion, locking, enforcement layering, extension rules, supported PostgreSQL versions.
- Out of scope: how a UMF document becomes catalog rows (CONTRACT-003), the journal's content and ordering rules (CONTRACT-002), the mutation operations and the conformance corpus (CONTRACT-004), the query language, generated per-type tables.
- Owning project: truss. Consumers: truss's own engine, and any other implementation (for example a Python implementation embedded in an application).
- Every element carries a source: **ADR-002** (accepted), **SPIKE-002** (taken from the bake-off's option C schema, `sql/c_schema.sql`), or **Proposed** (added by this contract, not yet in an ADR).

## Normative Surface

The words MUST, MUST NOT, SHOULD and MAY are used as in RFC 2119. The schema name is a deployment parameter, `truss` by default, and `COMMENT ON SCHEMA` carries the layout version string `truss-layout 0.1`.

**Tables**

| Table | Rules | Source |
|-------|-------|--------|
| `schema_rev` | One row per accepted catalog revision: `rev` (primary key), `accepted_at`, `report` (the acceptance and enforcement report, CONTRACT-003). Rows are immutable. | ADR-002 D1; Proposed (split from the documents) |
| `schema_doc` | The UMF documents of a revision, verbatim: `(rev, ord)` key, `doc_id`, `doc_revision`, `umf_version` (exact), `content_sha256`, `document` (the bytes as received), `validation`. A revision MAY hold several documents. Rows are immutable. | ADR-002 D1; Proposed (several documents per revision) |
| `type_def` | One row per entity type: `type_id`, `module`, `element` (unique together), `kind`, `provisional`, `since_rev`, `retired_rev`. A type retired is never deleted. | SPIKE-002; Proposed (`provisional`, `retired_rev`) |
| `prop_def` | One row per property: `prop_id`, `type_id`, `element`, `name`, `scalar_type`, `nullability`, `cardinality`, `facets`, `item`, `home` (`json` or `row`), `since_rev`, `retired_rev`. `(type_id, name)` and `element` are unique. | SPIKE-002; ADR-002 D4 |
| `key_def` | The named keys of a type: `(type_id, key_id)`, `prop_ids` (the component properties in order), `is_primary`. | SPIKE-002 |
| `rel_def` | One row per relationship: identity, `source_min/max`, `target_min/max` (NULL maximum means unbounded), `lifecycle`, `directed`, `target_key`, `composition`, `assoc_type_id` (the type whose properties an edge carries), `inverse`, `since_rev`, `retired_rev`. | SPIKE-002; Proposed (`assoc_type_id`, `retired_rev`) |
| `rel_endpoint` | The allowed `(rel_type_id, source_type, target_type)` triples. Adding a relationship is an INSERT, not DDL. | ADR-002 D6 |
| `object` | LIST-partitioned by `type_id`. Primary key `(id, type_id)`. Columns: `props` (JSONB object keyed by `prop_id` rendered as text), `retained` (JSONB object or NULL), `root_id`, `rev` (catalog revision of the last write), `ver`, `created_at`, `updated_at`. One partition per type, plus `object_default`. | ADR-002 D2, D3, D5; Proposed (`ver`, timestamps) |
| `edge` | Not partitioned. Columns: `id`, `rel_type_id`, `(source_id, source_type)`, `(target_id, target_type)`, `props` (JSONB object, relationship attributes), `order_key` (text, fractional, `COLLATE "C"`), `rev`, `ver`, `created_at`, `updated_at`. | ADR-002 D6; Proposed (`ver`, timestamps) |
| `journal` | RANGE-partitioned by `at`. See CONTRACT-002. | ADR-002 D7 |
| `id_seq` | One sequence for the ids of objects and edges. | ADR-002 D6 |
| `journal_seq` | The sequence for `journal.seq`. Explicit sequences are used, not identity columns. | Proposed |

**Constraints**

| Rule | Source |
|------|--------|
| `edge.(source_id, source_type)` and `edge.(target_id, target_type)` MUST reference `object (id, type_id)` with `ON DELETE RESTRICT`. An object that has an edge cannot be deleted. | ADR-002 D6; Proposed (RESTRICT stated) |
| `edge.(rel_type_id, source_type, target_type)` MUST reference `rel_endpoint`. Endpoint types are enforced by the database with no DDL per relationship. | ADR-002 D6 |
| `object.props`, `object.retained` (when not NULL), `edge.props` and `journal.origin` MUST be JSON objects. `props` is NOT NULL, so a SQL NULL from `jsonb_set` fails instead of erasing the map. | ADR-002 D3 |
| No per-type CHECK constraints on `object`. | ADR-002 D9 |
| `rev` columns reference `schema_rev`. | Proposed |

**Identity**

- An `id` comes from `id_seq`, shared by objects and edges. A caller MUST NOT supply an id. *(ADR-002 D2 consequence)*
- Global uniqueness of `id` rests on the sequence, not a constraint, because PostgreSQL cannot enforce it across partitions. An id is never reused. *(ADR-002 D2)*
- Business identity is a named UMF key (`key_def`). Each declared key is enforced by a unique partial expression index on the type's partition, cast to the declared type, with text keys `COLLATE "C"`. Keys of different types do not interact. *(ADR-002 D9)*

**Values**

- `props` is keyed by `prop_id` rendered as text, for example `'12'`. A missing key means the property is absent. JSON `null` means an explicit null. Meaning always comes from the catalog, never from the JSON type. *(ADR-002 D3)*
- Data that matches no definition goes in `retained`, is reported, and is never dropped. *(ADR-002 D3)*
- Canonical encodings: integers and decimals are JSON numbers in the author's lexical form; binary is base64 text; timestamps are RFC 3339 text with the author's offset; the character U+0000 is rejected with a reported rule. *(ADR-002 D3)*
- A reader MUST read JSONB, `numeric`, `bigint` and temporal values as text and parse them exactly. Default driver decoding is forbidden: it rounds integers beyond 2^53 and drops decimal trailing zeros. *(ADR-001 D3; ADR-002 D3)*
- A write renders an explicit null as `'null'::jsonb`. *(ADR-002 D3)*

**Partitions and indexes**

- A type's partition (`object_t<type_id>`) MUST be created when the type is accepted, **before any object of that type exists**. PostgreSQL refuses to create it while the default partition holds rows of that type (observed on 16.2 and 17.9, 4 Oct 2026). An implementation that must accept a type with data already in the default partition MUST first move those rows. *(Proposed; evidence in the check)*
- The default partition holds long-tail types. *(ADR-002 D2)*
- Indexes and extended statistics exist only where the binding declares them. The engine never creates them in response to queries. The per-partition index count is reported. *(ADR-002 D11)*
- `edge` carries two traversal indexes: `(source_id, rel_type_id) INCLUDE (target_id, target_type)` and the reverse. *(ADR-002 D6; the `target_type` include is provisional)*
- Indexes MAY be built after the revision commits, outside its transaction (for example `CREATE INDEX CONCURRENTLY`); a revision's report MUST list indexes still pending. *(Proposed)*

**Concurrency**

- A write to an object MUST lock it with `FOR NO KEY UPDATE`, never `FOR UPDATE`. *(ADR-002 D9)*
- A write transaction MUST confirm the catalog revision it validated against, for example with `FOR SHARE` on the current `schema_rev` row, so a revision cannot be accepted while a writer uses the previous one. *(ADR-002 D10)*
- `ver` starts at 1 and increases by 1 on every change to an object or edge. A writer MAY pass an expected `ver` and MUST then refuse to write if it differs. *(Proposed)*
- Cross-row rules, such as minimum multiplicity and aggregate invariants, lock the parent or run SERIALIZABLE. A deferred trigger alone under READ COMMITTED is never reported as database enforcement. *(ADR-002 D9)*
- Every adapter MUST use prepared statements or an equivalent plan cache and MUST refuse to run where it cannot. A transaction-mode pooler without prepared-statement support is such a place. *(ADR-002 D11)*

**Deletion**

An object is deleted by deleting its row once it has no edges. The journal keeps its history. Composition and owned lifecycle are enforced by the engine, which deletes the edges and owned objects first. *(ADR-002 D5, D7; Proposed for the RESTRICT consequence)*

**Enforcement layers**

| Layer | Enforces |
|-------|----------|
| Database | Typed endpoint foreign keys, no object deleted while it has edges, key uniqueness per partition, maximum multiplicity by partial unique edge indexes, the JSON-object checks |
| Engine | Every assertion in the UMF model, validated before the write, naming the rule; minimum multiplicity and aggregate invariants under the locks above |
| None | Assertions UMF carries that no layer can enforce; each is listed in the report |

**Extension rules (for a host that builds on these tables)**

- A host MAY add its own tables, functions, roles and privileges in its own schema.
- A host MAY add row-level security policies and triggers on truss tables, including triggers that write the journal.
- A host MUST NOT add, drop or alter columns of truss tables, change a primary key, foreign key or check constraint, or write the catalog tables except through a catalog revision (CONTRACT-003).
- Keys in `origin` that begin `x-` are reserved for hosts (CONTRACT-002).
- A host MUST declare the layout version it was built against and MUST refuse to run against a different major version.

**Supported PostgreSQL versions**

| Version | Status |
|---------|--------|
| 16.2 | The layout and check pass (embedded server, 4 Oct 2026) |
| 17.9 | The layout and check pass (embedded server, 4 Oct 2026) |
| 17.11, 18.6 | SPIKE-002 ran option C on these; this exact DDL is untested there |
| 18 on Databricks Lakebase | Unverified for this DDL |

The minimum supported version is 16. The layout uses `xid8`, `INCLUDE` indexes, foreign keys to a partitioned table, and partitioned tables with explicit sequences; it uses no extension.

## Precedence and Compatibility

- Versioning: the layout version is `major.minor`. Adding a nullable column or an index is minor. Removing or retyping a column, changing a key or constraint, or changing an encoding is major.
- Precedence: the DDL file, then this document, then ADR-002. ADR-002 points it marks provisional (storage-home thresholds, composition, edge identity, the `target_type` include) may change this contract by a layout version change.
- Backward compatibility: a reader built for layout 0.x MUST ignore columns it does not know. A writer MUST refuse a database whose layout major version differs.
- Deprecation: an element is deprecated for one minor version before removal.

## Error Semantics

| Condition | Database outcome | Meaning to the engine |
|-----------|------------------|------------------------|
| Edge names a disallowed endpoint type or a missing object | `foreign_key_violation` | Reported as an endpoint-type or missing-endpoint rule |
| Delete of an object that has an edge | `foreign_key_violation` | Reported as an object-has-edges refusal |
| Second object with the same key in a partition | `unique_violation` | Reported as a key conflict |
| `props` is not an object, or `origin` is not an object | `check_violation` | Engine defect; never user data |
| SQL NULL assigned to `props` | `not_null_violation` | Engine defect |
| Partition for a type created over default-partition rows | `check_violation` | Move the rows first |
| Statement cannot be prepared | adapter refuses to start | Deployment unsupported |

## Examples

```sql
-- a type is accepted: its partition and key index first, then objects
CREATE TABLE truss.object_t1 PARTITION OF truss.object FOR VALUES IN (1);
CREATE UNIQUE INDEX object_t1_key ON truss.object_t1 (((props ->> '10') COLLATE "C"));

INSERT INTO truss.object (type_id, props, rev) VALUES (1, '{"10":"lease"}', 1) RETURNING id;
-- explicit null, preserved; an absent key means the property is absent
UPDATE truss.object SET props = jsonb_set(props, '{10}', 'null'::jsonb) WHERE id = 1 AND type_id = 1;
```

## Non-Normative Notes

SPIKE-002 measured generic catalog storage within 2× of per-type tables for fetch, one hop, range and update with prepared statements, two hops at 1.70 to 2.32×, and 4.8× the disk, on PostgreSQL 17.11. Those figures do not describe this exact DDL on 16.2 or on Lakebase. The layout review lists open concerns this contract does not settle: object-level write cost, the cost of structured value records, and planner statistics for filters on JSONB values. Planning cost grows with the number of types on a shared table (7.6 to 8.0 ms at 105 types) and a limit on the number of types would need a measurement that does not exist yet (the layout review's follow-up list has none for type count).
