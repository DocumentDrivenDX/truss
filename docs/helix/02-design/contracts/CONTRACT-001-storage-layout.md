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

Defines the fixed set of PostgreSQL tables truss stores UMF-described property-graph data in, so that any implementation, in any language, reads and writes the same tables. The executable form is [`storage-layout.sql`](storage-layout.sql), checked by [`storage-layout.check.sql`](storage-layout.check.sql). A conforming implementation is interchangeable with another over the same database.

No PRD frames truss yet. This contract implements the accepted ADR-002 and is a draft until framed requirements confirm it.

## Scope and Boundaries

- In scope: tables, columns, constraints, partitions, sequences, indexes, identity, value encoding, deletion, locking, enforcement layering, host roles and extension rules, supported PostgreSQL versions.
- Out of scope: how a UMF document becomes catalog rows (CONTRACT-003), the journal's content and ordering (CONTRACT-002), the mutation operations and the conformance corpus (CONTRACT-004), the query language, generated per-type tables.
- Owning project: truss. Consumers: truss's own engine, and any other implementation (for example a Python implementation embedded in an application).
- Every element carries a source: **ADR-002** (accepted, with its decision number), **SPIKE-002** (from the bake-off's option C schema, `sql/c_schema.sql`), or **Proposed** (added by this contract and not yet in an ADR). Points that ADR-002 marks provisional are marked so here.

## Normative Surface

MUST, MUST NOT, SHOULD and MAY are used as in RFC 2119. The schema name is a deployment parameter, `truss` by default; `COMMENT ON SCHEMA` carries `truss-layout 0.1`.

**Tables**

| Table | Rules | Source |
|-------|-------|--------|
| `setting` | Key/value deployment settings. `journal_mode` is `"engine"` or `"trigger"` (CONTRACT-002). | Proposed |
| `schema_rev` | One row per accepted catalog revision: `rev` (primary key), `accepted_at`, `report`. Immutable. | ADR-002 D1; Proposed |
| `schema_doc` | The UMF documents of a revision, verbatim: `(rev, ord)`, `doc_id`, `doc_revision`, `umf_version`, `content_sha256`, `document`, `validation`. A revision MAY hold several documents. Immutable. | ADR-002 D1; Proposed |
| `schema_change` | The prior and new form of a catalog row that a revision changed in place (CONTRACT-003). Append-only. | Proposed |
| `type_def` | `type_id`, `module`, `element` (unique together), `kind`, `provisional`, `placement` (`own` or `default`), `since_rev`, `doc_ord` (the defining document, NULL for a provisional type), `retired_rev`. A retired type is never deleted. | SPIKE-002; Proposed |
| `prop_def` | `prop_id`, `type_id`, `element`, `name`, `scalar_type`, `nullability`, `cardinality`, `facets`, `item`, `home` (`json` or `row`), `since_rev`, `doc_ord`, `retired_rev`. `(type_id, name)` and `(type_id, element)` are unique. | SPIKE-002; ADR-002 D4 |
| `key_def` | `(type_id, key_id)`, `prop_ids` (components in order), `is_primary`. | SPIKE-002 |
| `rel_def` | Relationship identity, `source_min/max`, `target_min/max` (NULL maximum means unbounded), `lifecycle`, `directed`, `target_key`, `composition`, `assoc_type_id`, `inverse`, `since_rev`, `doc_ord`, `retired_rev`. | SPIKE-002; Proposed |
| `rel_endpoint` | The allowed `(rel_type_id, source_type, target_type)` triples. Adding a relationship is an INSERT. | ADR-002 D6 |
| `object` | LIST-partitioned by `type_id`; primary key `(id, type_id)`. `props`, `retained`, `root_id` and `root_type`, `rev`, `ver`, `created_at`, `updated_at`. | ADR-002 D2, D3; D5 (provisional); Proposed |
| `edge` | `id`, `rel_type_id`, `(source_id, source_type)`, `(target_id, target_type)`, `props`, `order_key` (text, `COLLATE "C"`), `rev`, `ver`, `created_at`, `updated_at`. | ADR-002 D6; Proposed |
| `journal` | RANGE-partitioned by `at`, with no default partition. See CONTRACT-002. | ADR-002 D7; Proposed |
| `id_seq` | One sequence for object and edge ids. | ADR-002 D6 (edge ids provisional, V7) |
| `journal_seq` | The sequence for `journal.seq`. Explicit sequences, not identity columns. | Proposed |

**Constraints**

| Rule | Source |
|------|--------|
| `edge` source and target MUST reference `object (id, type_id)` with `ON DELETE RESTRICT`. | ADR-002 D6; Proposed (RESTRICT) |
| `edge.(rel_type_id, source_type, target_type)` MUST reference `rel_endpoint`. | ADR-002 D6 |
| `object.(root_id, root_type)` MUST reference `object (id, type_id)` with `ON DELETE RESTRICT`; `root_id` and `root_type` are both set or both NULL. Every reference carries both columns. | ADR-002 D2, D5 (provisional); Proposed (`root_type`) |
| `props`, `edge.props` and `journal.origin` MUST be JSON objects; `retained` MUST be a JSON object or NULL. `props` is NOT NULL, so a SQL NULL from `jsonb_set` fails instead of erasing the map. | ADR-002 D3 |
| No per-type CHECK constraints on `object`. | ADR-002 D9 |
| `rev` columns of `object`, `edge` and the catalog tables reference `schema_rev`. `journal.rev` is not enforced. | Proposed |

**Identity**

- An `id` comes from `id_seq`, shared by objects and edges. A caller MUST NOT supply one. Global uniqueness rests on the sequence, because PostgreSQL cannot enforce it across partitions. An id is never reused. *(ADR-002 D2; edge ids from the shared sequence are provisional, V7)*
- Catalog ids (`type_id`, `prop_id`, `rel_type_id`) are allocated as the current maximum plus 1 under the catalog lock and are never reused, including after retirement. *(Proposed)*
- Business identity is a named UMF key (`key_def`).

**Key indexes.** Each declared key MUST be enforced by a unique index on the type's partition (a type with `placement` `default` uses a partial index on `object_default` with `WHERE type_id = <id>`). The expression per component is fixed, so a lookup uses the same expression and reaches the index:

| Component's scalar family | Index expression | Equality |
|---------------------------|------------------|----------|
| integer, signed, at most 64 bits | `((props ->> '<prop_id>')::bigint)` | by value |
| integer otherwise, decimal | `((props ->> '<prop_id>')::numeric)` | by value; `1.0` and `1.00` are equal |
| string, binary, timestamp | `((props ->> '<prop_id>') COLLATE "C")` | exact text; timestamps that differ only in offset are different keys |

The index name is `key_<type_id>_<key_id>` with non-word characters replaced by `_`. A composite key lists its components in order. NULLs are distinct, so an object with an absent key component is not indexed, is not reachable by key, and the engine reports it. A key lookup or write MUST use these expressions. A value that cannot be cast fails with `invalid_text_representation`, which is an engine defect because the engine validates first. *(ADR-002 D9; expressions from SPIKE-002 `valueExpr`)*

**Values**

- `props` is keyed by `prop_id` rendered as text. A missing key means absent; JSON `null` means an explicit null. Meaning always comes from the catalog, never from the JSON type. *(ADR-002 D3)*
- Data matching no definition goes in `retained`, keyed by the author's field name as received, is reported, and is never dropped. *(ADR-002 D3; key format Proposed)*
- Canonical encodings: integers and decimals are JSON numbers in the author's lexical form; binary is base64 text; timestamps are RFC 3339 text with the author's offset; U+0000 is rejected with a reported rule. *(ADR-002 D3)*
- A reader MUST read JSONB, `numeric`, `bigint` and temporal values as text and parse them exactly. *(ADR-001 D3; ADR-002 D3)*
- A write renders an explicit null as `'null'::jsonb`. *(ADR-002 D3)*
- Records without identity are stored as structured values inside the owner's `props`, typed through the catalog; records with identity are objects, and composition with them is an edge with owned lifecycle, carrying `root_id` and `root_type`. *(ADR-002 D5, provisional on V3)*

**Partitions and placement**

- Each type has a `placement`, fixed when the type is accepted. `own` creates the partition `object_t<type_id>` at acceptance, before any object of the type exists. `default` puts the type in `object_default`, for long-tail types. *(ADR-002 D2; `placement` Proposed)*
- Placement cannot change in layout 0.1. PostgreSQL refuses to create a partition for a type while the default partition holds rows of it, and moving those rows is impossible once edges refer to them (`DELETE` from the default partition and `DETACH` both fail on the foreign keys). Both were observed on 16.2 and 17.9, 4 Oct 2026.
- Creating a partition is DDL. It takes `ACCESS EXCLUSIVE` locks on `object` and `object_default` and share-row-exclusive locks on `schema_rev` and `type_def` (observed). It MUST run inside the catalog acceptance transaction, after the exclusive catalog lock, under a `lock_timeout`; on timeout the acceptance rolls back and MAY be retried. Writers are excluded by the catalog lock, so only readers can delay it. *(Proposed; this contradicts ADR-002's statement that revisions need no table locks above ROW EXCLUSIVE, and is raised in the notes)*
- Indexes and extended statistics exist only where the binding declares them; the engine never creates them in response to queries; the per-partition index count is reported. *(ADR-002 D11)*
- `edge` carries two traversal indexes: `(source_id, rel_type_id) INCLUDE (target_id, target_type)` and the reverse. *(ADR-002 D6; the `target_type` include is provisional)*
- Maximum-multiplicity indexes are partial unique indexes on `edge` per relationship: `(source_id) WHERE rel_type_id = <id>` when the target maximum is 1, and `(target_id) WHERE rel_type_id = <id>` when the source maximum is 1. If built `CONCURRENTLY` after the revision commits, the implementation MUST verify the index is valid and drop and report it if not; the report lists indexes still pending. *(ADR-002 D9; SPIKE-002; timing Proposed)*

**Concurrency**

- **Catalog lock.** The lock key is `hashtextextended('truss.catalog', 0)`. Every write transaction MUST take `pg_advisory_xact_lock_shared(key)` as its first statement, then read the head revision (`SELECT max(rev) FROM schema_rev`) and compare it with the revision it validated against; if they differ it fails as `catalog_changed`. A catalog acceptance MUST take `pg_advisory_xact_lock(key)` as its first statement, re-read the head, then derive, check and write. This replaces a `FOR SHARE` lock on the head row, which was verified to lock a stale row under READ COMMITTED (a waiting writer gets the lock on the old head and does not notice the new one) and to create MultiXacts on a hot row. Verified on 16.2 and 17.9: a writer that waited on an acceptance saw the new head, and a second acceptance took the next revision number without a conflict. *(ADR-002 D10 allows "for example" `FOR SHARE`; the mechanism here is Proposed)*
- A write to an object locks it `FOR NO KEY UPDATE`; a delete locks it `FOR UPDATE`, so the lock does not escalate. Composed children are locked after their parent, then in ascending `(type_id, id)` order. *(ADR-002 D9; delete lock Proposed)*
- `ver` starts at 1 and increases by 1 on every change. A writer MAY pass an expected `ver` and MUST then refuse to write if it differs. *(Proposed)*
- Cross-row rules lock the parent or run SERIALIZABLE; a deferred trigger alone under READ COMMITTED is never reported as database enforcement. *(ADR-002 D9)*
- Every adapter MUST use prepared statements or an equivalent plan cache and MUST refuse to run where it cannot. *(ADR-002 D11)*

**Deletion.** An object is deleted by deleting its row once it has no edges; the journal keeps its history. Composition and owned lifecycle are enforced by the engine, which deletes edges and owned objects first. *(ADR-002 D5, D7)*

**Enforcement layers**

| Layer | Enforces |
|-------|----------|
| Database | Typed endpoint foreign keys, no object deleted while it has edges, key uniqueness, maximum multiplicity indexes, the JSON-object checks |
| Engine | Every assertion in the UMF model, validated before the write, naming the rule; minimum multiplicity and aggregate invariants under the locks above |
| None | Assertions UMF carries that no layer can enforce; each is listed in the report |

**Roles and extension rules for a host**

A host that builds on these tables names four roles. The roles are a convention; truss creates none.

| Role | Holds |
|------|-------|
| Owner | Owns every truss object. SHOULD be `NOLOGIN`. Creates partitions and indexes. The application's login identity MUST NOT be the owner. |
| Acceptance | May run catalog acceptance (CONTRACT-003) by assuming the owner's rights through an owner-owned function. |
| Writer | Writes objects and edges, through the engine or host write functions. |
| Reader | Reads. Reads of a type's partition happen through the parent. |

- Partitions are created by the owner and given no grants; a host MUST NOT grant privileges on a partition, because row-level security on the parent does not apply to a query that names the partition.
- A host MAY add its own tables, functions, roles and privileges in its own schema; MAY `ENABLE` and `FORCE ROW LEVEL SECURITY` and add policies on the parent tables `object` and `edge`; and MAY add triggers on truss tables, including triggers that write the journal (CONTRACT-002). `FORCE` is needed because the owner and `SECURITY DEFINER` functions it owns bypass row-level security otherwise.
- A host MUST NOT add, drop or alter columns, change a primary key, foreign key or check constraint, or write the catalog tables except through a catalog revision.
- Foreign-key and unique checks run regardless of row-level security, so `key_conflict` and `has_edges` can reveal that a hidden row exists. A host that must hide this decides how to report it.
- Keys in `origin` that begin `x-` are reserved for hosts.
- A host MUST declare the layout version it was built against and MUST refuse a database of a different major version.

**Supported PostgreSQL versions** *(the minimum of 16 is Proposed)*

| Version | Status |
|---------|--------|
| 16.2, 17.9 | The layout and the check pass (embedded servers, 4 Oct 2026) |
| 17.11, 18.6 | SPIKE-002 ran option C on these; this exact DDL is untested there |
| 18 on Databricks Lakebase | Unverified for this DDL |

The layout uses `xid8`, `INCLUDE` indexes, foreign keys to a partitioned table (including a self-reference) and explicit sequences, and no extension.

## Precedence and Compatibility

- Precedence: ADR-002 (accepted) governs. Where ADR-002 is silent, the DDL governs this document, and this document governs the other contracts. A point that ADR-002 marks provisional may change this contract by a layout version change. A statement here that differs from ADR-002 is tagged Proposed and raised in the notes.
- Versioning: the layout version is `major.minor`. Adding a nullable column or an index is minor. Removing or retyping a column, changing a key or constraint, or changing an encoding is major.
- Backward compatibility: a reader built for 0.x MUST ignore columns it does not know. A writer MUST refuse a different major version.
- Deprecation: an element is deprecated for one minor version before removal.

## Error Semantics

Errors are classified by SQLSTATE and the relation concerned, never by constraint name: constraint names differ on partitions (observed: `edge_target_id_target_type_fkey` in place of `edge_target_fk`).

| Condition | SQLSTATE | Meaning to the engine |
|-----------|----------|------------------------|
| Edge to a disallowed endpoint type or a missing object | `foreign_key_violation` on `edge` | `endpoint_violation` |
| Delete of an object that has an edge | `foreign_key_violation` on `object` | `has_edges` |
| Second object with the same key | `unique_violation` on a `key_` index | `key_conflict` |
| Value that cannot be cast in a key index | `invalid_text_representation` | Engine defect, reported as `invalid` |
| `props`, `origin` or `retained` not an object; `root_id` without `root_type` | `check_violation` | Engine defect |
| SQL NULL assigned to `props` | `not_null_violation` | Engine defect |
| Partition created for a type that has default-partition rows | `check_violation` | Placement was wrong at acceptance |
| No journal partition covers `at` | `check_violation` | Deployment must create partitions (CONTRACT-002) |
| Deadlock, or a serialization failure | `deadlock_detected`, `serialization_failure` | `retry`: repeat the whole operation |
| Statement cannot be prepared | adapter refuses to start | Deployment unsupported |

## Examples

```sql
-- a type is accepted under the catalog lock: partition and key index first, then objects
SELECT pg_advisory_xact_lock(hashtextextended('truss.catalog', 0));
CREATE TABLE truss.object_t1 PARTITION OF truss.object FOR VALUES IN (1);
CREATE UNIQUE INDEX key_1_primary ON truss.object_t1 (((props ->> '10') COLLATE "C"));

-- a write: shared catalog lock first, then compare heads
SELECT pg_advisory_xact_lock_shared(hashtextextended('truss.catalog', 0));
SELECT max(rev) FROM truss.schema_rev;          -- must equal the revision validated against
INSERT INTO truss.object (type_id, props, rev) VALUES (1, '{"10":"lease"}', 1) RETURNING id;
```

## Non-Normative Notes

SPIKE-002 measured generic catalog storage within 2× of per-type tables for fetch, one hop, range and update with prepared statements, two hops at 1.70 to 2.32×, and 4.8× the disk, on PostgreSQL 17.11. Those figures do not describe this exact DDL on 16.2 or Lakebase.

**Raised for the owner.** (1) ADR-002 states that revisions need no DDL or table locks above ROW EXCLUSIVE, but adding an `own` type creates a partition, which takes `ACCESS EXCLUSIVE` locks (observed). (2) ADR-002 D2 includes a default partition; this contract keeps it but fixes each type's placement at acceptance, because a type cannot be promoted out of it once rows exist. (3) The journal has no default partition for the same reason (CONTRACT-002). (4) ADR-002 D10's `FOR SHARE` mechanism is replaced by advisory locks. The layout review's open concerns (object-level write cost, the cost of structured value records, planner statistics for JSONB filters) are not settled here, and a limit on the number of types would need a measurement that does not exist yet.
