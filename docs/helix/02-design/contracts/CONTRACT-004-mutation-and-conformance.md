---
ddx:
  id: CONTRACT-004
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: ADR-001
      kind: informed_by
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: SPIKE-002
      kind: informed_by
---

# Contract: Mutation protocol and conformance corpus

**Contract ID**: CONTRACT-004
**Type**: library
**Version**: 0.1 (draft)
**Status**: draft
**Related**: ADR-001 D5 (conformance corpus as data), ADR-002 D3, D7, D9, D10, D11, CONTRACT-001, CONTRACT-002, CONTRACT-003, SPIKE-002 (`harness/`, `loader/engine.ts`)

## Purpose

Defines, in a way that does not depend on a programming language, what each read and write operation must do against the tables of CONTRACT-001, and the language-neutral corpus that proves an implementation does it. Two implementations that pass the corpus are interchangeable over one database: either can read what the other wrote.

## Scope and Boundaries

- In scope: the operations and their effects, validation, locking, the version check, error kinds, and the conformance corpus format and pass rule.
- Out of scope: any language's method names or types (each implementation binds these operations idiomatically), the query language, the HTTP or GraphQL surface, how a host authenticates a caller.
- Owning project: truss. Implementations: truss's TypeScript engine, and any other (for example a Python implementation embedded in an application).

## Normative Surface

**Operations.** Inputs and outputs are abstract. `ref` is `(id, type)` of an object or an id of an edge.

| Operation | Effect |
|-----------|--------|
| `create_object(type, props, origin)` | Inserts an object and one `object_key` row for each key whose components are all present, returns its `ref` and `ver` 1. A key already held by another object fails as `key_conflict`; a key in `key_tombstone` fails as `key_reserved` when `setting.key_reuse` is `"forbid"`. Writes a `create` journal row. |
| `update_object(ref, set, unset, expected_ver?, origin)` | Changes the named properties, returns the new `ver`. A change to a key component also updates that key's `object_key` row, or inserts or deletes it when a component becomes present or absent; a conflict fails as `key_conflict` or `key_reserved`, and the old value is written to `key_tombstone`. A change that alters no value writes nothing and does not raise `ver`. |
| `delete_object(ref, expected_ver?, origin)` | Deletes the object and its composed children and owned objects, in one transaction; their key rows go with them by the foreign key, and each key value is written to `key_tombstone`. Refuses when any other edge refers to it. |
| `create_edge(rel_type, source, target, props, order_key?, origin)` | Inserts an edge between two existing objects of allowed types. |
| `update_edge(id, set, unset, expected_ver?, origin)` | As `update_object`, for an edge. |
| `delete_edge(id, expected_ver?, origin)` | Deletes an edge. |
| `get_object(ref)`, `get_edge(id)` | Returns the record with its `ver`, or `not_found`. Values are read as text and parsed exactly (CONTRACT-001). |
| `find_by_key(type, key_id, values)` | Returns the object holding that key value, or `not_found`: the canonical key text is built from `values` (CONTRACT-001, Key identity) and looked up in `object_key`. An incomplete key is `invalid`. |
| `list_objects(type, limit, after?)` | Keyset pages ordered by `id`, served by the `(type_id, id)` index; `limit` required. Returns the items and a marker that says whether more remain. |
| `list_edges(object, direction, rel_type?, limit, after?)` | As above, for the edges of one object, ordered by `order_key` (NULLs last) then `id`; the paging marker is the pair `(order_key, id)`. An ordered relationship's binding declares the index that serves this order. |
| `import_batch(records, load_id, origin)` | Applies imported records so that repeating the same import changes nothing. An object record is identified by its type and primary key, an edge record by its relationship and the two endpoint ids. A record whose identity is held by a live record, or is in `key_tombstone`, is skipped and reported. Any other record is created as `create_object` or `create_edge` would, and a `record_source` row is written with the `load_id` and the record's `source` facts. A record that fails validation or names a missing endpoint is rejected and stored nowhere. Objects are applied before edges across the whole input. Each record commits with its journal rows, in batches, so an interrupted import is completed by running it again. Returns counts of created, skipped and rejected records. A type with no primary key cannot be imported idempotently; its records are rejected as `invalid` with that reason. |

A deployment sets the maximum `limit`. A call above it is refused as `invalid`.

**Write protocol.** Every write operation MUST follow these steps in one transaction.

1. Read the catalog head as the first statement, `SELECT rev FROM schema_head WHERE id = 1 FOR SHARE`, and compare it with the revision being validated against. If they differ, fail as `catalog_changed` (MAY be retried). The share lock is held to the end of the transaction, so no revision is accepted while the write runs. Under REPEATABLE READ or SERIALIZABLE a head changed since the snapshot fails as `retry`. *(CONTRACT-001; ADR-002 D10)*
2. Lock the target row `FOR NO KEY UPDATE`; for `delete_object` and `delete_edge` lock it `FOR UPDATE`. Lock composed children after their parent, in ascending `(type_id, id)`. *(ADR-002 D9; delete lock Proposed)*
3. If `expected_ver` is given and differs from the row's `ver`, fail as `version_conflict` with no change.
4. Validate the whole proposed record against the catalog and report **every** violation, each with the UMF `rule`, a `path` and a `message`, and the `layer` that enforces it. Fail as `invalid` if there is any. *(ADR-002 D9)*
5. Apply the change. Values the catalog does not define go to `retained` and are reported, never dropped. A property set to explicit null is stored as `'null'::jsonb`; a property in `unset` is removed.
6. In `engine` journal mode, increase `ver` by 1, set `updated_at`, and set `rev` to the validated revision. In `trigger` mode, set `rev` and pass `origin` with `set_config('truss.origin', ..., true)`; the triggers maintain `ver` and `updated_at`.
7. In `engine` mode write the journal rows (CONTRACT-002) with the `origin` the caller gave and `db_role` from the database. In `trigger` mode write none: the triggers do, and writing them here would duplicate them. Read `setting.journal_mode` before step 1 and do not change behavior mid-transaction.
8. Commit. If any step fails the transaction rolls back and nothing is visible.

An operation SHOULD use prepared statements and MUST give the same results without them. *(ADR-002 D11)*

**Cross-row rules.** Minimum multiplicity and aggregate invariants are checked in step 4 under the parent lock (`FOR NO KEY UPDATE`) or in a SERIALIZABLE transaction. A deferred trigger under READ COMMITTED alone is never reported as database enforcement. *(ADR-002 D9)*

**Error kinds.** Every implementation MUST distinguish these, with these meanings.

| Kind | Meaning | Retry |
|------|---------|-------|
| `invalid` | One or more violations; each has `rule`, `path`, `message`, `layer` | no |
| `endpoint_violation` | The relationship does not allow these endpoint types, or an endpoint does not exist | no |
| `has_edges` | The object is still referred to by an edge that is not owned by it | after removing the edges |
| `key_conflict` | The key value already belongs to another object of the type (a unique violation on `object_key`) | no |
| `edge_exists` | An edge with this relationship, source and target already exists (a unique violation on `edge`) | no |
| `key_reserved` | The key value is in `key_tombstone` and `setting.key_reuse` is `"forbid"` | no |
| `version_conflict` | `expected_ver` differs from the stored `ver` | after re-reading |
| `catalog_changed` | The head revision differs from the one the write validated against | yes |
| `retry` | The database reported `deadlock_detected` or `serialization_failure`; no change was made | yes, the whole operation |
| `not_found` | No such object, edge or key value | no |
| `unavailable` | The database cannot be reached | when it recovers |

**Conformance corpus.** The corpus is data, not code. Its shape:

| Element | Rules |
|---------|-------|
| `manifest.json` | `corpus_version`, the `layout_version` and `umf_version` it targets, and the list of case files. |
| `models/` | UMF documents and truss bindings the cases import. |
| Case file | `id`, `description`, `tags`, `setup` (import sets to accept and prior data), `operations` (each `{op, args, alias?}`), and `expected`. |
| Aliases | Cases name records symbolically (`$a`, `$b`); real ids are assigned by the database and are never compared. |
| `expected.results` | The result or error kind, and for `invalid` the full set of violations, of each operation. **Normative.** |
| `expected.state` | The objects and edges after the case, in canonical form (properties by UMF element name, exact values as source tokens). **Normative.** |
| `expected.journal` | The journal rows per record in `(entity alias, ver)` order: `op`, `prop`, `old`, `new`, and the defined `origin` keys. `seq`, `at` and `xid` are not compared. **Normative.** |
| `expected.report` | For catalog acceptance cases, the acceptance and enforcement report (CONTRACT-003). **Normative.** |
| `expected.sql` | Informative only. An implementation may generate different, equivalent SQL. |

*Pass rule.* An implementation passes a corpus version on one engine version when every case yields the expected results, state, journal and report. A pass is reported with the engine, the layout and UMF versions and the corpus version, and no claim is made beyond them.

*Interchange check.* For each case, implementation A runs it against one database and implementation B reads the resulting state and journal, then the reverse. The two must agree. A divergence is a defect in one implementation or in this contract.

*Seed corpus.* SPIKE-002's harness inputs are the seed: the sales model and its revisions R1 to R5 (`model/`, `harness/revisions.ts`), the value corpus (`harness/fidelity.ts`), and the enforcement matrix (`harness/enforcement.ts`). Cases added later cover catalog acceptance (CONTRACT-003: ordering, unknown endpoints, rebinding) and the journal (CONTRACT-002: watermark, as-of).

*Host cases.* A host MAY add cases tagged `x-<host>` that exercise its extensions (CONTRACT-001). They are not part of the pass rule.

## Precedence and Compatibility

- Versioning: this contract and the corpus are versioned together as `0.x`. Adding an operation or a case is minor. Changing an operation's effect, an error kind or a normative expectation is major.
- Precedence: ADR-002 (accepted) governs; the DDL governs CONTRACT-001, which governs this document; the corpus states the expected behavior this document and CONTRACT-001 to CONTRACT-003 require, and a case that contradicts the ADR is a defect in the case.
- Backward compatibility: an implementation MUST treat an unknown error kind or case tag as not applicable, not as a failure.
- Deprecation: as CONTRACT-001.

## Error Semantics

| Condition | Outcome |
|-----------|---------|
| A revision is accepted while a write waits for the catalog lock | `catalog_changed` after the write reads the new head |
| Two writers update one object | One waits on the row lock; the second sees the new `ver` and, if it passed `expected_ver`, gets `version_conflict` |
| A journal row cannot be written | The write rolls back; the caller sees `unavailable` |
| An unknown value in `set` | Stored in `retained` and reported; not an error |
| A key listed in `find_by_key` is incomplete | `invalid` |

## Examples

```text
update_object($a, set={coverage:"substantial"}, expected_ver=1, origin={actor:"jsmith"})
  -> ver 2; journal: op=update prop=coverage old="partial" new="substantial" ver=2
update_object($a, set={coverage:"x"}, expected_ver=1)
  -> version_conflict
create_object(Solution, {coverage: 7})
  -> invalid [ {rule:"Solution.coverage:value", path:"coverage", message:"not a string", layer:"engine"} ]
delete_object($u)   where an Order edge refers to $u
  -> has_edges
```

## Non-Normative Notes

SPIKE-002's engine validated in client code before the insert, with the database round trip dominating the write cost (7.8 to 19.3 µs per record in Bun 1.3.11). The write protocol's order matters because the version check and the parent lock must come before validation, so validation never runs against a row another writer is changing. The corpus is what makes a second implementation possible without a second reading of the ADRs; ADR-001 D5 already records that expected results and reports are normative and expected SQL is informative.
