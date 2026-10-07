---
ddx:
  id: TD-025
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-025
      kind: informed_by
    - id: SD-006
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
---

# TD-025: Evidence-qualified enforcement reports

**Story:** [[US-025]]. **Parent:** [[SD-006]]. **Feature:** FEAT-006.

## Technical Approach

Enumerate every selected UMF assertion by stable rule/source identity, then classify its qualified implementation path as database, engine or none. Evidence is specific to server/version/layout/role/mode/model subset; a declared constraint or capability without tests does not establish enforcement. Opaque text remains carried but uninterpreted and classified none.

## Component Changes

| Planned files | Change | Criteria |
| --- | --- | --- |
| `packages/core/src/reports/assertions.ts` | Complete assertion inventory with source/rule identity and opaque retention | US-025-AC1, US-025-AC4 |
| `packages/core/src/reports/enforcement.ts` | Match exact path/profile evidence without upgrading engine checks | US-025-AC1, US-025-AC3 |
| `packages/conformance/src/enforcement/evidence.ts` | Bind native bypass receipts to qualified assertion scope | US-025-AC2 |
| `tests/reports/enforcement.test.ts`, `tests/enforcement/bypass.test.ts` | Independent report matrix and unavoidable-key attacks | All criteria |

New components reuse the shared report/classification work from US-014.

## API/Interface Design

Use the [draft enforcement report declaration](../contracts/bindings/truss-enforcement-report-v0.1.d.ts) and CONTRACT-004 inventory/evidence admission. Database/engine/none entries retain exact assertion source and distinct evidence obligations. Pure report generation does not confer native enforcement or observer authority.

CONTRACT-004 now defines the required ordinary-writer privilege inventory and materially distinct bypass paths. Bind report classification to the installed inventory and exact receipt pins; current support checks reject drift rather than reuse historical acceptance qualification. Administrative exclusions must be visible in the scope, and actual tested role grants accompany native evidence.

CONTRACT-003 owns acceptance report; CONTRACT-004 owns validation/corpus evidence; CONTRACT-001 owns actual storage guarantees. Add exact assertion/evidence profile semantics to the shared report contract before publication. Unknown assertion meaning cannot be silently omitted or classified enforced.

## Data Model and Integration

No default new storage tables. Qualified evidence manifests are explicit versioned artifacts; installed guard/grant inventory must match them before the report claims database enforcement. Canonical key-row uniqueness differs from authored key-property derivation: current plain object SQL can omit object_key. Full US-025-AC2 requires unavoidable derivation/privilege evidence or governing reconciliation, not a misleading duplicate-marker-only test.

## Security and Performance

Report permissions respect source/model and row policy without concealing guarantee limits. Evidence IDs cannot load code or select untrusted executable plugins. Host controls trusted registration. Pure report generation scales with assertion count and uses pinned manifest lookups; no live benchmark is inferred from the earlier 19-assertion spike.

## Testing

STP-025 owns all criteria. Independently authored expected matrix includes keys, property rules, cross-row rules and opaque text. Missing/mismatched evidence must not appear enforced. Native attacks include duplicate object props without key rows, wrong derived key, direct marker tampering and engine bypass. Qualify each advertised database version/role independently.

## Migration and Rollback

No layout migration. Removing a guard or changing role grants withdraws its evidence-qualified claim. Preserve prior receipts/profiles rather than rewriting them as current. Changed rule identities or report semantics require explicit versioning. Historical reports remain tied to the installation they describe.

## Implementation Sequence

1. Resolve report schema and authored-key unavoidable enforcement gap.
2. Create red complete-inventory/classification and native bypass cases.
3. Implement pure inventory/classification and trusted receipt binding.
4. Verify installed surfaces and all rule/profile evidence before support publication.

## Risks and Gates

US-025's full key guarantee conflicts with current engine-only derivation; D-04/D-05 identity/key meaning also apply. A successful implementation validation is not database enforcement. Opaque assertions remain recoverable even when classified none. Broader assertion coverage cannot be inferred from one fixture model.
