---
ddx:
  id: STP-010
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-010
      kind: informed_by
    - id: TD-010
      kind: informed_by
    - id: SD-002
      kind: informed_by
---

# STP-010: Refuse bad edges and protect connected objects

Reference Account/Item qualification consumes the [relationship binding](../../02-design/contracts/reference-relationship-binding.proposal.md). Under an independently seeded M03 graph, attempt A deletion with AB/AC present, then B and C deletion with their respective edges present: each must refuse under `@covers US-010-AC3`, including qualified plain-SQL attempts. Preserve complete original graph/key/value/source/journal state after confirmed containment; an uncertain native result stays unresolved. Separately delete AB/AC through protected edge mutations, then delete A under `@covers US-010-AC4`. B/C/D and their complete original values/keys survive; independent lifecycle cannot become target cascade. Verify actual original source/target RESTRICT constraints, complete journal contributions and outer settlement. Use separate fixtures for each destructive schedule; no production maintenance is authorized. These reference refinements remain not_run and do not replace the existing wrong-type, missing-endpoint, self-edge or concurrent create/delete cases.

## Story Reference

US-010, TD-010, SD-002, TP-001 and CONTRACT-001/004/007/009. Tests are planned, not executable evidence.

## Scope and Objective

Prove native endpoint integrity and object protection for the qualified writer role, including engine bypass. Composition and multiplicity remain separate story scopes.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-010-AC1 | `wrong_endpoint_type_is_native_refusal` | Customer-to-OrderLine insert fails through engine and plain SQL, including forged Order discriminator on Customer ID; no row/journal effect | `@covers US-010-AC1` | Native integration | `tests/edges/integrity.test.ts`; accepted endpoint catalog and ordinary writer |
| US-010-AC2 | `missing_endpoint_is_native_refusal` | Nonexistent source or target fails native FK and leaves no edge | `@covers US-010-AC2` | Native integration | Same file; reserved nonexistent IDs |
| US-010-AC3 | `connected_object_cannot_be_deleted` | Source and target delete each fail through plain SQL/engine while edge exists; object and edge remain | `@covers US-010-AC3` | Native integration | Same file; independent clients and committed connected rows |
| US-010-AC4 | `edge_first_delete_releases_object` | Delete edge then object succeeds; neither remains and selected journal mode records effects once | `@covers US-010-AC4` | Native integration | Same file; unowned relationship |

## Executable Proof

Planned command `bun test tests/edges/integrity.test.ts` requires future harness/files. Every actual test carries its criterion citation. Run on each advertised server/adapter/journal profile; missing targets remain unverified.

## Data and Setup

Install baseline/generated layout independently, then seed allowed and disallowed typed endpoints. Execute bypass SQL with the qualified writer principal, not schema owner. Inspect native state from a separate observer after commit/refusal. Corrupt expectations deliberately during harness development to prove refusal tests can fail.

## Edge Cases and Failure Modes

Force concurrent insert versus object delete with explicit barriers and bounded lock observations: one operation fails or waits then refuses; no dangling edge survives. Exercise self-edge, wrong target discriminator and missing source. Constraint refusal in a caller transaction preserves earlier host writes after call-savepoint rollback. Admin disabling constraints is outside qualified writer privileges and must be impossible for that role.

## Build Handoff

Write red bypass/engine cases, qualify bootstrap constraints, implement writes/deletes/error mapping, then concurrency/savepoint evidence. All four criteria and supplemental race observations block closeout. These passes do not establish maximum multiplicity or owned lifecycle.
