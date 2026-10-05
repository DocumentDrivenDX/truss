---
ddx:
  id: CONTRACT-005
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
    - id: SPIKE-003
      kind: informed_by
---

# Contract: Module isolation

**Contract ID**: CONTRACT-005
**Type**: schema
**Version**: layout 0.2 (draft)
**Status**: draft
**Related**: ADR-002 D14, CONTRACT-001 (tables, extension rules), CONTRACT-002 (`db_role`), SPIKE-003 F8, `module-isolation.sql`, `module-isolation.check.sql`

## Purpose

Defines an optional layer that lets a deployment give database roles read or write access to some UMF modules and none to others, enforced by the database. A module is the unit of ownership, because a UMF module is a bounded context and every type and relationship records its module.

## Scope and Boundaries

- In scope: the `module_access` table, the row-level security policies, the privileges the policies assume, which rows a role sees, cross-module edges, and how the acting role is determined.
- Out of scope: authenticating people, choosing which role a person gets, the write path (an engine, or functions a host writes), and the catalog revision itself, which is administrative.
- Owning project: truss. The layer is optional: with `module_access` empty and the policies not applied, truss behaves as in CONTRACT-001.

## Normative Surface

**`module_access`**

| Column | Rules |
|--------|-------|
| `module` | Primary key. The UMF module identifier as recorded on `type_def` and `rel_def`. A row MAY exist before the module has types. |
| `reader_role`, `writer_role` | Database role names. They MUST differ in a row. A role MAY appear in several rows, which is how one role reads several modules. A writer can always read its module. |

**Acting role.** The role that decides access is the one the database reports, as for the journal's `db_role` (CONTRACT-002): `current_setting('role')` when it is not `none`, otherwise `session_user`. It is not `current_user`, which inside a function owned by another role is that owner. `truss.acting_role()` returns it.

**What a role sees.** Policies apply to the roles' acting role. A superuser and a role with `BYPASSRLS` bypass them.

| Table | A role may read a row when | A role may write a row when |
|-------|----------------------------|------------------------------|
| `module_access` | it is the row's reader or writer | never through the layer |
| `type_def`, `rel_def` | it can read the row's module | never through the layer |
| `prop_def`, `key_def`, `rel_endpoint` | it can read the row's type or relationship | never through the layer |
| `object`, `object_key` | it can read the module of the row's type | it is the writer of that module |
| `edge` | it can read the relationship's module and the modules of both endpoint types | it is the writer of the relationship's module and can read both endpoint types' modules |
| `edge_limit` | not granted | the edge it refers to is visible to it |
| `journal`, `key_tombstone` | it can read the module of the type (entity kind `o`) or relationship (`e`) the row names | it is the writer of that module |
| `record_source` | the record it describes is visible to it | the record is visible to it |
| `schema_rev`, `schema_doc`, `schema_change`, `setting` | not granted | not granted |

A catalog revision is written by the owner, and the catalog tables are enabled but not forced, so acceptance is not subject to these policies. The data tables are forced, so the owner and functions it owns obey the policies as the acting role.

**Cross-module edges.** UMF allows a relationship in one module to name a type in another. Under this layer such an edge is visible only to a role that can read the relationship's module and both endpoint types' modules, so a role that reads only the source's module does not learn that an edge, or its target, exists. A role that writes the relationship's module can create it only if it can also read both endpoint types' modules. A deployment gives a role access to several modules by naming it as the reader of each.

**Privileges.** Policies only narrow what a granted privilege reaches. `truss.grant_module_roles(module, writes)` grants a module's roles `USAGE` on the schema and `SELECT` on the tables above that they may read, which includes `module_access`, `type_def` and `rel_def` because the policies read them as the role. With `writes` true it also grants the writer `INSERT`, `UPDATE` and `DELETE` on `object`, `object_key`, `edge` and `edge_limit`, `INSERT` on `journal`, `key_tombstone` and `record_source`, and `USAGE` on the id and journal sequences. A host that writes only through functions it owns can pass `writes` false.

**Policy cost.** Measured on PostgreSQL 16.2 and 17.9 at 1,000 types and 10 modules (SPIKE-003 F8), with the role already granted and set: the set-based policies used here added 0.006 to 0.007 ms to a read by id, 0.012 to 0.021 ms to a one-hop read and 0.06 to 0.07 ms to a page of 50, on top of about 0.02 ms for assuming the role. Policies built from row-by-row function calls cost about twice as much on a page of 50, and a `SECURITY DEFINER` function 2 to 3 times as much, so neither is used. The measured edge policy checked the endpoint types only; the shipped one also checks the relationship's module, which was not measured.

## Precedence and Compatibility

- Versioning: with the layout version (CONTRACT-001). `module_access` is part of the layout; the policies are a separate file that a deployment applies and that carries the same version.
- Precedence: CONTRACT-001 governs the tables. This contract adds policies and privileges and changes no column or constraint.
- Backward compatibility: adding a policy that narrows access is a breaking change for a deployment that applied the layer.
- Deprecation: as CONTRACT-001.

## Error Semantics

| Condition | Outcome | Retry | Recovery |
|-----------|---------|-------|----------|
| A role reads a row it may not | the row is absent, no error | no | Grant access in `module_access` |
| A role writes a row it may not | `insufficient_privilege` (a row-level security violation) | no | Use the module's writer role |
| A role lacks the privilege on a table | `insufficient_privilege` | no | Call `grant_module_roles` |
| A policy needs a table the role cannot select (`module_access`, `type_def`, `rel_def`) | `insufficient_privilege` | no | Call `grant_module_roles` |
| A foreign-key or unique check against a row the role cannot see | the check runs regardless of the policies and can reveal that the row exists | no | The host decides how to report it |

## Examples

```text
INSERT INTO truss.module_access VALUES ('sales', 'sales_ro', 'sales_rw'), ('billing', 'sales_ro', 'billing_rw');
SELECT truss.grant_module_roles('sales', true), truss.grant_module_roles('billing', true);
-- sales_ro reads both modules and any edge between them; sales_rw writes sales only and sees no billing row.
```

## Non-Normative Notes

The check script (`module-isolation.check.sql`) builds two modules and checks each rule above as non-superuser roles on PostgreSQL 16.2 and 17.9. It does not run the policies under a `SECURITY DEFINER` function owned by a non-superuser, where `FORCE ROW LEVEL SECURITY` and the acting role interact; that case is unverified. Writing a module's types and relationships through a catalog revision is not governed by this layer; a host that accepts revisions on behalf of a role checks that the role may define the module.
