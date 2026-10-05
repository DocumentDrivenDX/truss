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
| `policy.unknown_endpoint` | What to do with a relationship endpoint that no document in the set and no earlier revision defines: `reject` (default), `provisional` or `skip`. |

**Acceptance steps.** An implementation MUST perform these in order. Acceptance is all-or-nothing: if any step rejects, nothing is written and the report says why.

1. **Verify.** Compute `content_sha256` of each document's bytes, parse it exactly, and validate it with the pinned UMF validator. A document that fails validation rejects the set.
2. **Order.** Sort the documents so that a document comes after every document it declares as a dependency or references by element. Ties break by `doc_id`. Documents that depend on each other in a cycle are accepted together. The import `ord` of each document is recorded in `schema_doc`.
3. **Derive in phases.** Over the whole sorted set, derive in this fixed order: all types, then all properties, then all keys, then all relationships and their endpoints. Because every type exists before any relationship is derived, an endpoint defined in a later document of the set is not unknown. Derivation follows SPIKE-002: a UMF record becomes a type; a field becomes a property; a record-valued field becomes a composition relationship to a child object, never nested JSON; a named key becomes a `key_def`; an authored relationship becomes a `rel_def` with one endpoint triple per source and target pair.
4. **Resolve unknown endpoints** by `policy.unknown_endpoint` (below).
5. **Keep identity** (below).
6. **Check tightened rules.** For a rule a revision tightens or adds, run the generated violator queries over existing objects and list every violating object. If any violation exists the set is rejected. Nothing is accepted on the first violation alone.
7. **Persist atomically** in one transaction: lock the head `schema_rev` row `FOR UPDATE` (this waits for writers holding `FOR SHARE`, CONTRACT-001), insert `schema_rev` at head + 1, the `schema_doc` rows, the catalog rows, and the partition of each new type; apply declared total transforms; write `rebind` journal rows (CONTRACT-002).
8. **Build indexes** declared by the binding after commit if they cannot run in the transaction. The report lists them as pending until built.
9. **Report** (below). The report is stored in `schema_rev.report`.

**Unknown entity types.** An endpoint is unknown when it names a `(module, element)` that no document in the set defines and no earlier revision defines.

| Policy | Result |
|--------|--------|
| `reject` | The set is rejected; the report names each unknown endpoint and the relationship that names it. |
| `provisional` | A `type_def` row is created with `provisional = true`, kind `record`, and no properties, and the relationship's endpoint triple is created as usual. The type has a partition. It has no keys. Objects of the type are allowed, identified by id; all their data is held in `retained` and reported. |
| `skip` | The relationship is not derived; the report records it as a loss. |

When a later revision defines the element, the same `type_def` row is updated in place: `provisional` becomes false, and `type_id` and `since_rev` do not change. This is the only update a catalog row receives other than setting `retired_rev`. Retained data that matches a newly defined property is re-bound, one `rebind` journal row each, and listed in the report; data that matches none stays retained. A type that remains provisional is listed in every later report.

**Identity stability** (ADR-002 D8). A type, property or relationship keeps its catalog id for as long as its UMF identity (document, module, element) is unchanged. A new element gets a new id. An id is never reused. A revision that changes a property's type or cardinality is accepted only with a declared total transform applied in the same acceptance step; otherwise it is rejected with every violating object listed. An element removed from the documents is retired (`retired_rev`), not deleted.

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
| Dependency cycle between documents | Accepted together | n/a | None |
| A writer holds the current revision | Acceptance waits for the writer to finish | automatic | None |
| Two acceptances at once | The second waits on the head lock and then validates against the new head | automatic | None |
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

SPIKE-002's loader derives one document (`modules[0]`) and keeps ids stable by element identity. It never faced unknown endpoints or several documents, so the ordering and provisional-type rules above are new and untested. UMF's own relationship contract is a draft and requires endpoints to resolve exactly; unknown endpoints arise across documents (UMF's resolver stays within one document today) and from other dialects. A provisional type is a deliberate, reported hole, not a silent default.
