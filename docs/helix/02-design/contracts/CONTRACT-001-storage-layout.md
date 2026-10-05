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
    - id: SPIKE-003
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
**Version**: layout 0.2 (draft)
**Status**: draft
**Related**: ADR-002 (storage strategy), ADR-001 (language and portable core), SPIKE-002, SPIKE-003, the storage layout review, CONTRACT-002 (journal), CONTRACT-003 (catalog), CONTRACT-004 (mutation and conformance)

## Purpose

Defines the fixed set of PostgreSQL tables truss stores UMF-described property-graph data in, so that any implementation, in any language, reads and writes the same tables. The executable form is [`storage-layout.sql`](storage-layout.sql), checked by [`storage-layout.check.sql`](storage-layout.check.sql). A conforming implementation is interchangeable with another over the same database.

No PRD frames truss yet. This contract implements ADR-002 and is a draft until framed requirements confirm it.

## Scope and Boundaries

- In scope: tables, columns, constraints, sequences, indexes, identity, key identity, value encoding, deletion, locking, enforcement layering, host roles and extension rules, supported PostgreSQL versions.
- Out of scope: how a UMF document becomes catalog rows (CONTRACT-003), the journal's content and ordering (CONTRACT-002), the mutation operations and the conformance corpus (CONTRACT-004), the query language, generated per-type tables.
- Owning project: truss. Consumers: truss's own engine, and any other implementation (for example a Python implementation embedded in an application).
- Every element carries a source: **ADR-002** (with its decision number), **SPIKE-002** or **SPIKE-003** (a measurement), or **Proposed** (set by this contract and not yet in an ADR). Points that ADR-002 marks provisional are marked so here.

## Normative Surface

MUST, MUST NOT, SHOULD and MAY are used as in RFC 2119. The schema name is a deployment parameter, `truss` by default; `COMMENT ON SCHEMA` carries `truss-layout 0.1`.

**Tables**

| Table | Rules | Source |
|-------|-------|--------|
| `setting` | Key/value deployment settings. `journal_mode` is `"engine"` or `"trigger"` (CONTRACT-002); `key_reuse` is `"forbid"` or `"allow"` (CONTRACT-004). | Proposed |
| `module_access` | Optional. The reader and writer role of each UMF module, `module` the primary key. Empty by default and used only by the isolation layer (CONTRACT-005). | Proposed |
| `schema_rev` | One row per accepted catalog revision: `rev` (primary key), `accepted_at`, `report`, and `origin`, a JSON object that records who or what accepted it, with the keys and rules of the journal's `origin` (CONTRACT-002). Revision 0 is the empty catalog and exists from the start. Immutable. | ADR-002 D1; Proposed |
| `schema_head` | One row (`id` = 1) holding the current revision. Updated in place by every acceptance. | ADR-002 D10; SPIKE-003 |
| `schema_doc` | The UMF documents of a revision, verbatim: `(rev, ord)`, `doc_id`, `doc_revision`, `umf_version`, `content_sha256`, `document`, `validation`. A revision MAY hold several documents. Immutable. | ADR-002 D1; Proposed |
| `schema_change` | The prior and new form of a catalog row that a revision changed in place (CONTRACT-003). Append-only. | Proposed |
| `type_def` | `type_id`, `module`, `element` (unique together), `kind`, `provisional`, `since_rev`, `doc_ord` (the defining document, NULL for a provisional type), `retired_rev`. A retired type is never deleted. | SPIKE-002; Proposed |
| `prop_def` | `prop_id`, `type_id`, `element`, `name`, `scalar_type`, `nullability`, `cardinality`, `facets`, `item`, `home` (`json` or `row`), `since_rev`, `doc_ord`, `retired_rev`. `(type_id, name)` and `(type_id, element)` are unique. | SPIKE-002; ADR-002 D4 |
| `key_def` | `(type_id, key_id)`, `key_num` (a compact number, unique per type, never reused), `prop_ids` (components in order), `is_primary`, `since_rev`, `retired_rev`. | SPIKE-002; Proposed (`key_num`) |
| `rel_def` | Relationship identity, `source_min/max`, `target_min/max` (NULL maximum means unbounded), `lifecycle`, `directed`, `target_key`, `composition`, `assoc_type_id`, `inverse`, `since_rev`, `doc_ord`, `retired_rev`. | SPIKE-002; Proposed |
| `rel_endpoint` | The allowed `(rel_type_id, source_type, target_type)` triples. Adding a relationship is an INSERT. | ADR-002 D6 |
| `object` | One table for every type. Primary key `(id, type_id)`. `props`, `retained`, `root_id` and `root_type`, `rev`, `ver`, `created_at`, `updated_at`. Index `(type_id, id)` serves keyset listing of one type. | ADR-002 D2, D3; D5 (provisional); Proposed |
| `object_key` | One row per object per key: `(type_id, key_num, k)` is the primary key, `(object_id, type_id, key_num)` is unique, and `(object_id, type_id)` references `object` with `ON DELETE CASCADE`. | ADR-002 D2, D9; SPIKE-003 |
| `edge` | `id`, `rel_type_id`, `(source_id, source_type)`, `(target_id, target_type)`, `props`, `order_key` (text, `COLLATE "C"`), `rev`, `ver`, `created_at`, `updated_at`. | ADR-002 D6; Proposed |
| `key_tombstone` | A key value an object has held, or the endpoints of a deleted imported edge, written in the transaction that deletes or re-keys the record and never changed. `(entity_kind, type_id, key_num, k)` is the primary key. | Proposed |
| `record_source` | One row per imported record: `(entity_kind, entity_id)` is the primary key, with the `load_id` and a `source` JSON object whose defined optional keys are `author`, `at` and `system`. Written by the import that created the record, never changed. | Proposed |
| `feed_consumer` | One row per registered consumer of the journal: `consumer` (primary key) and the position `(xid, seq)` it has delivered through, with `updated_at`. Written by the consumer. | Proposed |
| `journal` | RANGE-partitioned by `at`, with no default partition. See CONTRACT-002. | ADR-002 D7; Proposed |
| `id_seq` | One sequence for object and edge ids. | ADR-002 D6 (edge ids provisional, V7) |
| `journal_seq` | The sequence for `journal.seq`. An explicit sequence, not an identity column. | Proposed |

No table other than `journal` is partitioned, and no operation adds a table, partition, column or per-type index. Accepting a type is catalog INSERTs. *(ADR-002 D1, D2; SPIKE-003)*

**Constraints**

| Rule | Source |
|------|--------|
| `edge` source and target MUST reference `object (id, type_id)` with `ON DELETE RESTRICT`. | ADR-002 D6; Proposed (RESTRICT) |
| `edge.(rel_type_id, source_type, target_type)` MUST reference `rel_endpoint`. | ADR-002 D6 |
| `object.(root_id, root_type)` MUST reference `object (id, type_id)` with `ON DELETE RESTRICT`; `root_id` and `root_type` are both set or both NULL. Every reference carries both columns. | ADR-002 D2, D5 (provisional); Proposed (`root_type`) |
| `object_key.(type_id, key_num)` MUST reference `key_def`. | Proposed |
| A `key_tombstone` for an edge has `key_num` 0; `source` of a `record_source` row is a JSON object. | Proposed |
| `props`, `edge.props` and `journal.origin` MUST be JSON objects; `retained` MUST be a JSON object or NULL. `props` is NOT NULL, so a SQL NULL from `jsonb_set` fails instead of erasing the map. | ADR-002 D3 |
| No per-type CHECK constraints on `object`. | ADR-002 D9 |
| `rev` columns of `object`, `edge` and the catalog tables reference `schema_rev`. `journal.rev` is not enforced. | Proposed |

**Identity**

- An `id` comes from `id_seq`, shared by objects and edges. A caller MUST NOT supply one. Within `object` the primary key `(id, type_id)` is unique; global uniqueness of `id` across objects and edges rests on the sequence. An id is never reused. *(ADR-002 D2; edge ids from the shared sequence are provisional, V7)*
- Catalog ids (`type_id`, `prop_id`, `rel_type_id`) are allocated as the current maximum plus 1 under the catalog lock and are never reused, including after retirement. *(Proposed)*
- Business identity is a named UMF key (`key_def`), held in `object_key`.

**Key identity.** An object's key value for key `K` is the canonical key text `k`, stored in `object_key` with `(type_id, key_num)`.

- A key with one component uses that component's canonical text. A key with several uses the compact JSON array of the components' canonical texts, in component order, for example `["a","b"]`. The arity of a key is fixed by its definition, so the two forms cannot be confused.
- Canonical text of a component by scalar family: a string is its text; binary is base64 text; a timestamp is its RFC 3339 text exactly as authored (two timestamps that differ only in offset are different keys); an integer is its decimal digits with an optional leading `-`, no leading zeros, and `0` for any zero; a decimal is a plain decimal with trailing fractional zeros removed, no exponent, and `0` for any zero. So integers and decimals are equal when equal in value (`1.0` and `1.00` are one key), and every other family is equal when equal as text.
- Comparison uses `COLLATE "C"`, so equality is exact bytes.
- An object that lacks a key component has no `object_key` row for that key. It is not reachable by that key and the engine reports it.
- `object_key` rows are written, updated and deleted by the same operation, in the same transaction, as the object (the engine, or a host's trigger). A change to a key component changes `k`. Deleting an object deletes its key rows by the foreign key. *(ADR-002 D9; SPIKE-003)*
- A key lookup is `object_key` joined to `object` on `(object_id, type_id)`.
- A key value an object has held is written to `key_tombstone` in the same transaction as the delete, and also when a change of key component frees the old value. With `setting.key_reuse` `"forbid"` the value then stays reserved: an import skips it and a direct create is refused (CONTRACT-004). With `"allow"` the tombstone is still written and a create may reuse the value. The database cannot enforce a reservation by a constraint, so it is engine enforcement, and a delete by plain SQL without a host trigger leaves no tombstone, which the enforcement report lists. *(Proposed)*

**Values**

- `props` is keyed by `prop_id` rendered as text. A missing key means absent; JSON `null` means an explicit null. Meaning always comes from the catalog, never from the JSON type. *(ADR-002 D3)*
- Data matching no definition goes in `retained`, keyed by the author's field name as received, is reported, and is never dropped. *(ADR-002 D3; key format Proposed)*
- Canonical encodings: integers and decimals are JSON numbers in the author's lexical form; binary is base64 text; timestamps are RFC 3339 text with the author's offset; U+0000 is rejected with a reported rule. *(ADR-002 D3)*
- A reader MUST read JSONB, `numeric`, `bigint` and temporal values as text and parse them exactly. *(ADR-001 D3; ADR-002 D3)*
- A write renders an explicit null as `'null'::jsonb`. *(ADR-002 D3)*
- Records without identity are stored as structured values inside the owner's `props`, typed through the catalog; records with identity are objects, and composition with them is an edge with owned lifecycle, carrying `root_id` and `root_type`. *(ADR-002 D5, provisional on V3)*

**Indexes**

- Indexes other than those in `storage-layout.sql` exist only where the binding declares them; the engine never creates them in response to queries. A declared index on `object` is a partial expression index on one type. *(ADR-002 D11)*
- Planning cost grows with the number of indexes on `object`. Measured on PostgreSQL 16.2 and 17.9 with one partial index per type: planning a key lookup took about 0.1 ms with 111 indexes and about 90 to 105 ms with 1011, while a layout with no per-type indexes planned in 0.02 ms at every size (SPIKE-003). The deployment sets a budget for declared indexes per table; the default is 100, and the report lists the count. *(Proposed; default from SPIKE-003)*
- A declared index MUST be built with `CREATE INDEX CONCURRENTLY`, outside the acceptance transaction. The implementation MUST then check that the index is valid and drop and report it if not; the acceptance report lists indexes still pending. *(Proposed)*
- `edge` carries two traversal indexes: `(source_id, rel_type_id, target_id) INCLUDE (target_type)`, which is unique, and `(target_id, rel_type_id) INCLUDE (source_id, source_type)`. The unique index makes an edge unique by relationship, source and target: a second kind of link between the same two objects is a second relationship, and a repeated link of one kind needs an association object. A traversal from a source uses the index by its first two columns, and no table or index is added for the rule. *(ADR-002 D6; SPIKE-003 F9; the `target_type` include is provisional)*
- A maximum multiplicity of one is enforced by `edge_limit`, whose primary key `(rel_type_id, side, endpoint_id)` refuses a second edge: side `s` holds one row per edge of a relationship that allows one edge per source, side `t` one per target. The engine writes the row in the same transaction as the edge; the row goes with the edge by the foreign key. A maximum above one is enforced by the engine under the parent lock. No index is created per relationship, because that costs a table-wide index per relationship: at 1,000 relationships, 1,003 edge indexes made planning take about 110 ms and inserts 5 times slower, while `edge_limit` kept both at the baseline. *(ADR-002 D9; SPIKE-003 E1b)*

**Concurrency**

- **Catalog lock.** Every write transaction MUST read the current revision as its first statement, `SELECT rev FROM schema_head WHERE id = 1 FOR SHARE`, compare it with the revision it validated against, and fail as `catalog_changed` if they differ. A catalog acceptance updates `schema_head` in place, which waits for the writers holding the share lock and blocks new ones while it holds the row. Because the row is updated in place, a waiting writer locks the current version and sees the new revision. Under REPEATABLE READ or SERIALIZABLE a writer whose snapshot predates the acceptance gets `serialization_failure` instead, which is `retry`. *(ADR-002 D10; SPIKE-003: an in-place head row detected the stale writer under READ COMMITTED and failed it with a serialization failure under REPEATABLE READ; a new head row per revision accepted the stale write under both, and advisory locks accepted it under REPEATABLE READ)*
- An acceptance waits for the current writers' share locks. Under sixteen continuous writers it waited 0.5 s at the median and over 5 s at the worst (SPIKE-003), because new writers can join the lock while it waits. An acceptance therefore sets a `lock_timeout` and retries later; acceptances are rare.
- A deployment MAY add an advisory queue in front of the head row (ADR-002 D10): writers take `pg_advisory_xact_lock_shared(hashtextextended('truss.catalog', 0))` first, an acceptance takes the exclusive form first. It never replaces the head-row lock, which alone gives correct behavior under REPEATABLE READ. *(SPIKE-003)*
- A write to an object locks it `FOR NO KEY UPDATE`; a delete locks it `FOR UPDATE`, so the lock does not escalate. Composed children are locked after their parent, then in ascending `(type_id, id)` order. *(ADR-002 D9; delete lock Proposed)*
- `ver` starts at 1 and increases by 1 on every change. A writer MAY pass an expected `ver` and MUST then refuse to write if it differs. *(Proposed)*
- Cross-row rules lock the parent or run SERIALIZABLE; a deferred trigger alone under READ COMMITTED is never reported as database enforcement. *(ADR-002 D9)*
- An adapter SHOULD use prepared statements or an equivalent plan cache and MUST work without them; it reports whether it is prepared. Unprepared point reads cost about 0.01 to 0.03 ms more at 1,000 types. *(ADR-002 D11; SPIKE-003 E3)*

**Deletion.** An object is deleted by deleting its row once it has no edges; its key rows go with it by the foreign key, and the journal keeps its history. Composition and owned lifecycle are enforced by the engine, which deletes edges and owned objects first. *(ADR-002 D5, D7)*

**Enforcement layers**

| Layer | Enforces |
|-------|----------|
| Database | Typed endpoint foreign keys; no object deleted while it has edges; uniqueness of key rows per `(type, key, value)` and removal of an object's key rows with it; maximum multiplicity of one through `edge_limit`; the JSON-object checks |
| Engine | Every assertion in the UMF model, validated before the write, naming the rule; that each object's key rows match its `props`; minimum multiplicity and aggregate invariants under the locks above |
| None | Assertions UMF carries that no layer can enforce; each is listed in the report |

The database cannot check that `object_key.k` matches the object's key components, because that needs the catalog and the canonicalization above. A write by plain SQL that bypasses the engine or a host trigger can leave the two inconsistent, and the report says so.

**Roles and extension rules for a host**

A host that builds on these tables names four roles. The roles are a convention; truss creates none.

| Role | Holds |
|------|-------|
| Owner | Owns every truss object. SHOULD be `NOLOGIN`. Creates the declared indexes. The application's login identity MUST NOT be the owner. |
| Acceptance | May run catalog acceptance (CONTRACT-003) by assuming the owner's rights through an owner-owned function. |
| Writer | Writes objects and edges, through the engine or host write functions. |
| Reader | Reads. |

- A host MAY add its own tables, functions, roles and privileges in its own schema; MAY `ENABLE` and `FORCE ROW LEVEL SECURITY` and add policies on any truss table, including the catalog tables and the journal, which can decide from the `module` that `type_def` and `rel_def` record (CONTRACT-005 is one such set, shipped as `module-isolation.sql`); and MAY add triggers on truss tables, including triggers that write the journal (CONTRACT-002) and keep `object_key` current. `FORCE` is needed because the owner and `SECURITY DEFINER` functions it owns bypass row-level security otherwise.
- A host MUST NOT add, drop or alter columns, change a primary key, foreign key or check constraint, or write the catalog tables except through a catalog revision.
- Foreign-key and unique checks run regardless of row-level security, so a key conflict or an object that still has edges can reveal that a hidden row exists. A host that must hide this decides how to report it.
- Keys in `origin` that begin `x-` are reserved for hosts.
- A host MUST declare the layout version it was built against and MUST refuse a database of a different major version.

**Supported PostgreSQL versions** *(the minimum of 16 is Proposed)*

| Version | Status |
|---------|--------|
| 16.2, 17.9 | The layout and the check pass (embedded servers) |
| 17.11, 18.6 | SPIKE-002 ran generic catalog storage on these; this exact DDL is untested there |
| 18, and managed PostgreSQL services | Unverified for this DDL |

The layout uses `xid8`, `INCLUDE` indexes and explicit sequences, and no extension.

## Precedence and Compatibility

- Precedence: ADR-002 governs. Where ADR-002 is silent, the DDL governs this document, and this document governs the other contracts. A point that ADR-002 marks provisional may change this contract by a layout version change.
- Versioning: the layout version is `major.minor`. Adding a nullable column or an index is minor. Removing or retyping a column, changing a key or constraint, or changing an encoding is major.
- Backward compatibility: a reader built for 0.x MUST ignore columns it does not know. A writer MUST refuse a different major version.
- Deprecation: an element is deprecated for one minor version before removal.

## Error Semantics

Errors are classified by SQLSTATE and the relation concerned, never by constraint name.

| Condition | SQLSTATE | Meaning to the engine |
|-----------|----------|------------------------|
| A second edge with the same relationship, source and target | `unique_violation` on `edge` | `edge_exists` |
| Edge to a disallowed endpoint type or a missing object | `foreign_key_violation` on `edge` | `endpoint_violation` |
| Delete of an object that has an edge | `foreign_key_violation` on `object` | `has_edges` |
| Key value already held by another object of the type | `unique_violation` on `object_key` | `key_conflict` |
| Key row for a missing object or an undefined key | `foreign_key_violation` on `object_key` | Engine defect |
| `props`, `origin` or `retained` not an object; `root_id` without `root_type` | `check_violation` | Engine defect |
| SQL NULL assigned to `props` | `not_null_violation` | Engine defect |
| No journal partition covers `at` | `check_violation` | Deployment must create partitions (CONTRACT-002) |
| Deadlock, a serialization failure, or a lock timeout on acceptance | `deadlock_detected`, `serialization_failure`, `lock_not_available` | `retry`: repeat the whole operation |
| Statement cannot be prepared | adapter runs unprepared and reports it | None required |

## Examples

```sql
-- a write: read the head first, under the share lock
SELECT rev FROM truss.schema_head WHERE id = 1 FOR SHARE;       -- must equal the revision validated against
INSERT INTO truss.object (type_id, props, rev) VALUES (1, '{"10":"lease"}', 1) RETURNING id;
INSERT INTO truss.object_key VALUES (1, 1, 'lease', 42);        -- type, key_num, canonical key text, object id

-- a key lookup
SELECT o.id, o.props::text
FROM truss.object_key k JOIN truss.object o ON o.id = k.object_id AND o.type_id = k.type_id
WHERE k.type_id = 1 AND k.key_num = 1 AND k.k = 'lease';

-- keyset listing of one type
SELECT id, props::text FROM truss.object WHERE type_id = 1 AND id > 100 ORDER BY id LIMIT 50;
```

## Non-Normative Notes

SPIKE-003 compared four layouts at 10, 100 and 1000 types on PostgreSQL 16.2 and 17.9 (200,000 objects, 400,000 edges): one table with a partial unique index per type, one partition per type, one table with a generic key table (this layout), and hot-type partitions plus a default partition. At 1000 types the first planned a key lookup in about 100 ms, the partitioned layouts planned a one-hop traversal in 88 to 330 ms, and this layout planned every shape in 0.02 to 0.04 ms with a fresh-connection first query of about 2 ms. It costs about 57 MB more disk (70%) than the partitioned layouts, because each key is stored twice. Not measured: declared secondary indexes on non-key properties (they remain partial indexes per type, subject to the budget above), filters on JSONB values and planner statistics (layout review concern 11), data larger than memory, and concurrent write throughput beyond the catalog-lock test. The measurements were taken on a shared laptop with other load; the differences cited are two orders of magnitude, well outside that noise.
