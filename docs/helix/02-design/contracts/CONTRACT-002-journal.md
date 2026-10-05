---
ddx:
  id: CONTRACT-002
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-003
      kind: informs
    - id: CONTRACT-004
      kind: informs
---

# Contract: Journal

**Contract ID**: CONTRACT-002
**Type**: schema
**Version**: layout 0.1 (draft)
**Status**: draft
**Related**: ADR-002 D7, CONTRACT-001 (storage layout), CONTRACT-004 (mutation)

## Purpose

Defines the journal: the append-only record of every change to an object or an edge, written in the same transaction as the change. It is the audit trail, the source of as-of reads, and the feed that carries changes to a warehouse. Every implementation writes it the same way so any reader can use it.

## Scope and Boundaries

- In scope: the row shape per operation, the `origin` object, ordering, the consumer watermark, as-of reads, append-only rules, retention.
- Out of scope: the table's DDL (CONTRACT-001), who is allowed to write (a host), the Delta publication job.
- Owning project: truss. Source tags as in CONTRACT-001: ADR-002 (accepted), SPIKE-002, or Proposed.

## Normative Surface

**Row shape.** One row records one property change, or one whole-record create or delete. Columns are in `storage-layout.sql`.

| Column | Rules | Source |
|--------|-------|--------|
| `seq` | From `journal_seq`; unique with `at`. Assigned at insert. Not commit order. | SPIKE-002; Proposed |
| `at` | The database clock when the statement ran (`clock_timestamp()`). Not a commit time. The partition key. | SPIKE-002 |
| `xid` | The writing transaction (`pg_current_xact_id()`). | SPIKE-002 |
| `entity_kind` | `o` for an object, `e` for an edge. | Proposed |
| `entity_id`, `entity_type` | The record's id, and its `type_id` (object) or `rel_type_id` (edge). | Proposed |
| `ver` | The record's `ver` after the change. | Proposed |
| `op` | `create`, `update`, `delete`, `retain` or `rebind`. | ADR-002 D7; Proposed (values) |
| `prop_id` | The property changed, or NULL for a whole-record row. | SPIKE-002 |
| `old_value`, `new_value` | The property's old and new value as JSONB, in the encodings of CONTRACT-001. | SPIKE-002 |
| `rev` | The catalog revision in force. | SPIKE-002 |
| `origin` | A JSON object; see below. | SPIKE-002 (text); Proposed (object) |

**Rows per operation**

| Operation | Rows written |
|-----------|--------------|
| `create` | One row with `prop_id` NULL and `new_value` the object `{"props": <the props map>, "retained": <the retained map or null>}`. `ver` is 1. |
| `update` | One row per property whose value changed, with `old_value` and `new_value`. All rows of one change share `entity_*`, `ver` and `xid`. A write that changes nothing writes no row and does not raise `ver`. |
| `delete` | One row with `prop_id` NULL and `old_value` the object `{"props": ..., "retained": ...}` as it was. `ver` is the version it had plus 1. |
| `retain` | One row when data that matched no definition is stored in `retained`. |
| `rebind` | One row when retained data is re-bound to a newly defined property at catalog acceptance (CONTRACT-003). |

A record's history is ordered by `ver`, then `seq`.

**`origin`.** A JSON object that records who or what caused the change. Defined keys:

| Key | Meaning |
|-----|---------|
| `actor` | The person or service the caller asserts. Not authenticated by truss. |
| `db_role` | The database role the change ran as, taken from the database, never from the caller. |
| `load` | For a bulk load, `{id, initiated_by}`. When present, `actor` SHOULD be absent. |
| `reason` | Free text. |
| `x-*` | Reserved for hosts. truss preserves and ignores them. |

An implementation MUST NOT set `db_role` from a value the caller supplied.

**Atomicity.** A change and its journal rows MUST commit in one transaction. If a journal row cannot be written the change MUST NOT commit. *(ADR-002 D7)*

**Append-only.** The journal MUST NOT be updated or deleted by a role truss or a host recognizes. A trigger that refuses UPDATE, DELETE and TRUNCATE is RECOMMENDED; a host MAY require it. Retention removes whole partitions, never rows. *(Proposed)*

**Bypass.** A change made by plain SQL that does not go through an implementation, or a host's trigger, is not journaled, and the enforcement report says so. A host that must journal every change MUST add triggers or write functions (CONTRACT-001, extension rules). *(ADR-002 D7)*

**Ordering and the consumer watermark.** `seq` and `at` are assigned when a row is inserted, not when its transaction commits, so a row with a higher `seq` can become visible before a row with a lower one. A consumer that reads the journal incrementally MUST NOT use `seq` or `at` as a watermark. It MUST read only rows whose `xid` is below the snapshot's minimum, in `(xid, seq)` order:

```sql
SELECT * FROM truss.journal
WHERE xid < pg_snapshot_xmin(pg_current_snapshot())
  AND (xid, seq) > ($last_xid, $last_seq)
ORDER BY xid, seq;
```

Every transaction with a lower `xid` has then finished, so no row below the watermark can appear later. The order is stable and complete, and it is the order transactions began, not committed. *(Proposed; verified on PostgreSQL 16.2 and 17.9 on 4 Oct 2026: a committed row is withheld while an older transaction is still open, and both appear in order once it commits.)*

**As-of reads.** The state of a record at version `v` is its `create` row's `new_value.props` with every `update` row of versions up to `v` applied in order. As-of reads are derived from the journal; the object row stays canonical. *(ADR-002 D7)*

**Retention.** `journal` is RANGE-partitioned by `at`. The deployment chooses the partition interval and the retention period; truss defines neither.

## Precedence and Compatibility

- Versioning: with the layout version (CONTRACT-001).
- Precedence: a row's columns govern; `origin` keys not listed here are preserved untouched.
- Backward compatibility: a reader MUST ignore unknown `origin` keys and unknown `op` values and MUST NOT fail on them.
- Deprecation: as CONTRACT-001.

## Error Semantics

| Condition | Outcome | Retry | Recovery |
|-----------|---------|-------|----------|
| A journal row cannot be written | The whole change rolls back; the caller is told it failed | After the database recovers | None; no partial change exists |
| A reader asks for a version that was never written | No rows; the reader reports an empty history, not an error | no | |
| A consumer's saved watermark is ahead of the snapshot minimum | The consumer reads nothing until the minimum passes it | wait | |
| A partition for `at` does not exist | The row goes to `journal_default` | no | Create partitions ahead of time |

## Examples

```text
create:  op=create  prop_id=NULL  new_value={"props":{"10":"lease"},"retained":null}  ver=1  origin={"actor":"jsmith","db_role":"app_w"}
update:  op=update  prop_id=11    old_value="partial" new_value="substantial"  ver=2
delete:  op=delete  prop_id=NULL  old_value={"props":{"10":"lease","11":"substantial"},"retained":null}  ver=3
load:    op=create  ...  origin={"load":{"id":"load-2026-10-05-01","initiated_by":"ops"},"db_role":"app_w"}
```

## Non-Normative Notes

The bake-off's journal had one row per property with no entity kind and a text `origin`. This contract adds the entity kind, the version, whole-record rows for create and delete (so a create does not write one row per property), and a JSON `origin`. Whether the journal or the object row is canonical was left open by the layout review; ADR-002 chose the object row, and a journal-canonical design can be adopted later without changing the table set.
