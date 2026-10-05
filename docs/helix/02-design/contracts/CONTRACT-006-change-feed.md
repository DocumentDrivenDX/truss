---
ddx:
  id: CONTRACT-006
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
    - id: CONTRACT-002
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
---

# Contract: Change feed

**Contract ID**: CONTRACT-006
**Type**: schema
**Version**: layout 0.2 (draft)
**Status**: draft
**Related**: ADR-002 D7, D15, CONTRACT-001 (`feed_consumer`), CONTRACT-002 (journal, consumer watermark), CONTRACT-003 (catalog revision)

## Purpose

Defines what any publisher of truss's changes to a downstream copy (a warehouse, a search index, another database) must preserve, so that the copy is complete, correctly ordered, repeatable after a failure, and honest about how current it is. It states content and ordering. It does not choose a transport: a custom reader of the journal and a database-native synchronization are both allowed, provided they preserve what is stated here.

## Scope and Boundaries

- In scope: the records a feed carries, ordering, completeness, replay, the delivery guarantee, consumer positions, freshness evidence, and how retention interacts with consumers.
- Out of scope: the transport, the downstream table design, and what a consumer does with a record.
- Owning project: truss.

## Normative Surface

**Records.** A feed carries these record kinds, each defined by tables of CONTRACT-001.

| Kind | Source | Content |
|------|--------|---------|
| `change` | a `journal` row | entity kind, id and type, `ver`, `op`, `prop_id`, old and new value, `rev`, `origin` (CONTRACT-002), and its `(xid, seq)` position |
| `revision` | a `schema_rev` row with its `schema_doc` rows | `rev`, `accepted_at`, `origin`, and each document's identity, revision token, UMF version, `content_sha256` and bytes |
| `source` | a `record_source` row | entity kind and id, `load_id`, `source` |
| `reservation` | a `key_tombstone` row | entity kind, type, key number and key text, the entity that held it, and its `ver` |

A delete is a `change` with `op` `delete` that carries the record as it was, so a consumer needs no other record to remove it.

**Order.** `change` records are delivered in `(xid, seq)` order and only below the safe watermark of CONTRACT-002 (`xid < pg_snapshot_xmin(pg_current_snapshot())`), so no change that commits later can have a position before one already delivered. A `revision` record `N` is delivered before the first `change` whose `rev` is `N` or later. `source` and `reservation` records are delivered with, or after, the `change` of the transaction that wrote them.

**Completeness.** Every committed journal row is delivered, exactly once in position order, unless the consumer's retention has removed it by consent (below). Nothing is delivered for a change that rolled back.

**Repeatability.** A consumer MAY restart from any earlier position and receive the same records in the same order. A consumer MUST treat delivery as at-least-once and apply idempotently by the key `(entity kind, entity id, ver, prop id)` for a `change`, `rev` for a `revision`, and `(entity kind, entity id)` for a `source`.

**Consumer positions.** A consumer registers a name in `feed_consumer` and updates its row with the `(xid, seq)` of the last record it has durably applied, in the same transaction or step that applied it where the downstream allows. A position ahead of the safe watermark is not an error: the consumer reads nothing until the watermark passes it.

**Freshness evidence.** For one consumer, the age of the feed is the time since the earliest change that the consumer has not yet applied was written:

```sql
SELECT now() - min(at) AS lag
FROM truss.journal j, truss.feed_consumer c
WHERE c.consumer = $1 AND (j.xid, j.seq) > (c.xid, c.seq) AND j.xid < pg_snapshot_xmin(pg_current_snapshot());
```

A change written but still above the safe watermark counts as not yet publishable and is reported separately. A publisher MUST make the consumer's position and its own `updated_at` readable by whoever relies on the copy, so a reader of the copy can say "reflects the source through position P".

**Retention.** A journal partition MUST NOT be dropped while it holds a row past the lowest position of any registered consumer, unless that consumer has been removed from `feed_consumer` by an operator. A deployment with no registered consumer retains by its own policy.

**Schema changes.** The `revision` records give the consumer every document of every revision in order, so a consumer can learn new types before the first change that uses them. A consumer that does not support a document's UMF version stops at that revision and reports it; it does not skip it.

## Precedence and Compatibility

- Versioning: with the layout version (CONTRACT-001).
- Precedence: the journal governs content (CONTRACT-002); this contract adds ordering across record kinds, delivery, positions and retention.
- Backward compatibility: a consumer MUST ignore unknown record kinds and unknown fields. Adding a record kind is compatible.
- Deprecation: as CONTRACT-001.

## Error Semantics

| Condition | Outcome | Retry | Recovery |
|-----------|---------|-------|----------|
| A consumer's position is older than the retained journal | the consumer cannot resume and reports it | no | Re-seed the copy from a snapshot, then resume from the snapshot's position |
| A document's UMF version is unsupported by the consumer | the consumer stops at that revision | after upgrade | Upgrade the consumer |
| A publisher delivers a record out of order | the consumer must detect it by position and stop | no | Fix the publisher |
| A long-running transaction holds the safe watermark back | later changes are delayed; lag grows | wait | End or cancel the transaction |

## Examples

```text
position (1042, 7):  change  o 1043 type 7 ver 2 update prop 12 "partial" -> "substantial" rev 3 origin {actor:"a", db_role:"w"}
position (1042, 8):  source  o 1043 load "load-1" {author:"x"}
revision 3 is delivered before the first change with rev 3.
```

## Non-Normative Notes

The feed's end-to-end freshness depends on the transport. A database-native synchronization to a warehouse may deliver changes within seconds; that figure is the transport's to establish and measure, and this contract only requires that the lag be observable. The consumer watermark's cost is that one slow transaction delays everything behind it.
