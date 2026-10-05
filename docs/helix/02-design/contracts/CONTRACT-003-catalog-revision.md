---
ddx:
  id: CONTRACT-003
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
    - id: SPIKE-002
      kind: informed_by
    - id: CONTRACT-004
      kind: informs
---

# Contract: Catalog revision

**Contract ID**: CONTRACT-003
**Type**: library
**Version**: 0.1 (draft)
**Status**: draft
**Related**: ADR-002 D1, D8, D9, D10, D12, CONTRACT-001, CONTRACT-002, SPIKE-002 (`loader/catalog.ts`, `loader/revise.ts`)

## Purpose

Defines how a set of UMF documents becomes an accepted catalog revision: the order documents are imported in, how catalog rows are derived, how ids stay stable, what happens to an entity type that a relationship names but no document defines, and the report every acceptance produces. Any implementation that accepts a revision does so the same way, so the resulting tables are the same.

## Scope and Boundaries

- In scope: the import set, validation, ordering, derivation phases, unknown entity types, identity stability, tightened-rule checks, atomic acceptance, the acceptance and enforcement report.
- Out of scope: UMF's own semantics (truss consumes UMF and never defines it; ADR-002 D12), conversion of other UMF dialects into core documents, the tables themselves (CONTRACT-001), the mutation operations (CONTRACT-004).
- Owning project: truss.
- UMF assumption: documents are UMF core 0.7.0 (records, fields, named keys, and `module.relationships` per UMF's draft CONTRACT-041), the version SPIKE-002 exercised. Each document's exact UMF version is recorded; the supported subset is declared in the report.

## Normative Surface

**Input: an import set**

| Element | Rules |
|---------|-------|
| `documents` | One or more UMF documents as received bytes. Each has an identity `doc_id` and an owner-issued `doc_revision`. |
| `binding` | Optional truss binding vocabulary (storage home, indexes, statistics). |
| `origin` | The caller's `actor` and `reason`, and any `x-*` keys, as for a journal row (CONTRACT-002). The implementation adds `db_role` from the database and ignores any `db_role` the caller sends. |
| `policy.unknown_endpoint` | What to do with a relationship endpoint that no document in the set and no earlier revision defines: `reject` (default), `provisional` or `skip`. |

**Acceptance steps.** An implementation MUST perform these in order. Acceptance is all-or-nothing: if any step rejects, nothing is written and the report says why.

0. **Lock.** Begin a transaction and take the catalog lock: `SELECT rev FROM schema_head WHERE id = 1 FOR UPDATE` (CONTRACT-001). This waits for the writers holding the share lock and blocks new ones while it is held, so no write runs between the checks below and the revision's insert. Set a `lock_timeout` first; on timeout the acceptance rolls back and MAY be retried later. The row read is the head; the new revision is head + 1. Steps 1 and 2 MAY run before the lock; everything from step 3 runs under it.
1. **Verify.** Compute `content_sha256` of each document's bytes, parse it exactly, and validate it with the pinned UMF validator. A document that fails validation rejects the set.
2. **Order.** Sort the documents so that a document comes after every document it declares as a dependency or references by element. Ties break by `doc_id`, in byte order. Documents that depend on each other in a cycle are accepted together and take consecutive positions ordered by `doc_id`. The resulting `ord` of each document is recorded in `schema_doc` and is deterministic for a given set.
3. **Derive in phases.** Over the whole sorted set, derive in this fixed order: all types, then all properties, then all keys, then all relationships and their endpoints. Because every type exists before any relationship is derived, an endpoint defined in a later document of the set is not unknown. Derivation follows SPIKE-002 and ADR-002 D5: a UMF record becomes a type; a field becomes a property; a record-valued field whose record has identity becomes a composition relationship to a child object with owned lifecycle, carrying `root_id` and `root_type`; a record-valued field whose record has no identity is stored as a structured value inside the owner's `props`, typed through the catalog (ADR-002 D5, provisional on V3); a named key becomes a `key_def`; an authored relationship becomes a `rel_def` with one endpoint triple per source and target pair.
4. **Resolve unknown endpoints** by `policy.unknown_endpoint` (below).
5. **Keep identity** (below). Two documents in one set that define the same `(module, element)` reject the set as `duplicate_definition`, unless their bytes are identical. Each catalog row records the document that defined it (`doc_ord`). A catalog id is the current maximum plus 1, never reused (CONTRACT-001).
6. **Check tightened rules.** For a rule a revision tightens or adds, run the generated violator queries over existing objects and list every violating object. If any violation exists the set is rejected. Nothing is accepted on the first violation alone.
7. **Persist** in the same transaction, still under the lock: insert `schema_rev` at head + 1 with its `origin` and the `schema_doc` rows; insert catalog rows, with new catalog ids and key numbers allocated as the current maximum plus 1 (CONTRACT-001); update in place only the rows this contract permits, recording the before and after in `schema_change`; apply declared total transforms and write `transform` journal rows; write `rebind` journal rows (CONTRACT-002); and update `schema_head` to the new revision. Accepting a type adds catalog rows only: no table, partition, column or index is created. Because the acceptance holds the lock, the revision number it inserts cannot conflict with another acceptance.
8. **Build indexes** declared by the binding after commit if they cannot run in the transaction. The report lists them as pending until built.
9. **Report** (below). The report is stored in `schema_rev.report`.

**Unknown entity types.** An endpoint is unknown when it names a `(module, element)` that no document in the set defines and no earlier revision defines.

| Policy | Result |
|--------|--------|
| `reject` | The set is rejected; the report names each unknown endpoint and the relationship that names it. |
| `provisional` | A `type_def` row is created with `provisional = true`, kind `record`, and no properties, and the relationship's endpoint triple is created as usual. It has no keys. Objects of the type are allowed, identified by id; all their data is held in `retained` and reported. |
| `skip` | The relationship is not derived; the report records it as a loss. |

When a later revision defines the element, the same `type_def` row is updated in place: `provisional` becomes false and `doc_ord` is set; `type_id` and `since_rev` do not change. Retained data that matches a newly defined property is re-bound, one `rebind` journal row each, and listed in the report; data that matches none stays retained. A type that remains provisional is listed in every later report.

**Identity stability** (ADR-002 D8). A type, property or relationship keeps its catalog id for as long as its UMF identity (document, module, element) is unchanged. A new element gets a new id. An id is never reused. A revision that changes a property's type or cardinality is accepted only with a declared total transform applied in the same acceptance step; otherwise it is rejected with every violating object listed. An element removed from the documents is retired (`retired_rev`), not deleted.

**Keys.** A key added to a type that already has objects gets its `object_key` rows built for those objects in the same acceptance. If two objects share a value, the set is rejected as a tightened-rule violation and every duplicate is listed (step 6). The acceptance holds the catalog lock while it builds the rows, so its duration grows with the number of objects of the type, and the report says how many rows were built. A key removed from the documents is retired (`retired_rev`): its `object_key` rows are deleted, and its `key_num` is never reused.

**In-place catalog changes.** Catalog rows are not immutable. A revision MAY update, in place and with the same id: the columns of a `prop_def` row (`scalar_type`, `nullability`, `cardinality`, `facets`, `item`, `home`), the multiplicity, lifecycle and direction columns of a `rel_def` row, a `type_def` row's `provisional` flag (true to false only) and `retired_rev`, and the `retired_rev` of a property or relationship. Each such change writes a `schema_change` row holding the definition before and after, so a journal value written under an earlier revision can be read with the definition in force then. Nothing else in a catalog row changes.

**Other UMF dialects.** A source that is not a core document (for example table specifications whose relationships name tables by string with a type, confidence and reasoning) is converted by an adapter into core documents plus a loss report before acceptance. The adapter's losses are appended to the acceptance report. Resolution of a loose reference to `(module, element)` is the adapter's, and an unresolved reference follows `policy.unknown_endpoint`.

**Report.** A JSON object with these members. It is the enforcement report ADR-002 requires.

| Member | Content |
|--------|---------|
| `rev` | The accepted revision number. |
| `umf` | The exact UMF versions seen and the supported subset. |
| `documents` | For each document: `doc_id`, `doc_revision`, `content_sha256`, `ord`. |
| `counts` | Types, properties, keys, relationships and endpoints added, and elements retired. |
| `provisional` | Every type still provisional, with the relationships that name it. |
| `rebinds` | Retained data re-bound at this revision. |
| `assertions` | For every UMF assertion: `rule`, `layer` (`database`, `engine` or `none`) and `outcome`. |
| `pending_indexes` | Declared indexes not yet built. |
| `losses` | Anything UMF carries that truss cannot hold, with its source. |

## Precedence and Compatibility

- Versioning: with CONTRACT-001's layout version for rows, and this contract's own version for the steps.
- Precedence: UMF validity governs step 1; this contract governs everything after. ADR-002 points marked provisional may change this contract.
- Backward compatibility: a reader of `schema_rev.report` MUST ignore unknown members. Adding a policy value is compatible; changing the meaning of one is breaking.
- Deprecation: as CONTRACT-001.

## Error Semantics

| Condition | Outcome | Retry | Recovery |
|-----------|---------|-------|----------|
| A document fails UMF validation | Set rejected; report lists the violations | After fixing the document | Correct the document |
| Unknown endpoint with `reject` | Set rejected, naming each | After adding the definition or changing policy | Add the missing document |
| A tightened rule has violating objects | Set rejected; every violator listed | After correcting data or adding a transform | Fix the data |
| A type or cardinality change has no total transform | Set rejected | After declaring a transform | Declare it |
| Two documents define the same `(module, element)` with different bytes | Set rejected as `duplicate_definition` | After fixing the documents | Remove one definition |
| The lock is not granted within `lock_timeout` | The acceptance rolls back | yes, later | Retry |
| Dependency cycle between documents | Accepted together, ordered by `doc_id` | n/a | None |
| A writer is running | Acceptance waits for the writers' share locks to be released | automatic | None |
| Two acceptances at once | The second waits on the head row, reads the new head when it is granted, and validates against it | automatic | None |
| The same document bytes accepted twice | A new revision is created only if the derived rows differ; otherwise the existing revision is returned | n/a | None |

## Examples

```text
import set: [ sales.rev3.umf.json, orders.rev1.umf.json ]
  orders.rev1 declares relationship order_line: Order -> Line; Line is defined in sales.rev3.
  order: sales.rev3, then orders.rev1 (dependency). Types are derived for both before relationships,
  so Line resolves. policy.unknown_endpoint = reject: nothing is unknown.

import set: [ orders.rev1.umf.json ]  with Line defined nowhere
  policy = reject       -> rejected: relationship order_line names unknown (sales, Line)
  policy = provisional  -> accepted: type_def (sales, Line) provisional=true; endpoint (order_line, Order, Line);
                           report.provisional = [ {sales.Line, via order_line} ]
  later revision defines sales.Line -> same type_id, provisional=false, retained data re-bound, rebinds reported
```

## Non-Normative Notes

SPIKE-002's loader derives one document (`modules[0]`), keeps ids stable by element identity, updates property and relationship rows in place on revision, and writes a `migrate` journal operation for transforms (named `transform` here). It never faced unknown endpoints or several documents, so the ordering and provisional-type rules above are new and untested. The in-place update rule, `schema_change`, and the catalog head row are Proposed. UMF's own relationship contract is a draft and requires endpoints to resolve exactly; unknown endpoints arise across documents (UMF's resolver stays within one document today) and from other dialects. A provisional type is a deliberate, reported hole, not a silent default.
