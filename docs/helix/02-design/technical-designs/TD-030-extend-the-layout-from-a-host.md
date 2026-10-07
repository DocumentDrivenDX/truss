---
ddx:
  id: TD-030
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-030
      kind: informed_by
    - id: SD-008
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
---

# TD-030: Host extension qualification

**Story:** [[US-030]]. **Parent:** [[SD-008]]. **Feature:** FEAT-008.

## Technical Approach

Qualify explicit host extension profiles around the fixed layout without altering canonical columns/constraints. Host schemas/functions/roles/triggers remain host-owned; their coexistence is evidenced against the required corpus. Forced RLS governs reads through the actual ordinary role and all selected access paths. Layout inventory detects forbidden alteration even when an administrative owner has power to perform it.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/conformance/src/host/extensions.ts` | Apply trusted disposable extension fixtures and run required corpus | US-030-AC1 |
| `packages/conformance/src/host/policy.ts` | Independent role/path visibility probes | US-030-AC2 |
| `packages/conformance/src/layout/catalog.ts` | Detect canonical column/constraint drift against independent inventory | US-030-AC3 |
| `tests/host/extensions.test.ts` | Native coexistence, forced-RLS and mutation-drift witnesses | All criteria |

New harness components reuse bootstrap/layout comparator. Runtime core does not install arbitrary host extension code.

## API/Interface Design

CONTRACT-001 owns extension rules; CONTRACT-002 owns exclusive journal modes; CONTRACT-005 owns qualified isolation; CONTRACT-007 owns role/transaction context; CONTRACT-008 owns inventory. Host extension content cannot alter Truss's public semantics silently. Exact profile registration/evidence shape belongs in shared contracts before support publication.

## Data Model and Integration

No canonical layout DDL. External tables/functions and allowed triggers are inventoried separately from required Truss objects. Journal triggers must respect configured single-writer behavior. RLS policy qualification includes object/key/edge direct and joined reads; host policies can narrow visibility, but integrity paths must not undercount hidden state. Forbidden changes are reported, not automatically repaired.

## Security and Performance

Host controls trusted DDL and administrative principals. Ordinary writer cannot disable policies/guards or tamper with evidence. Definer functions need acting-role and search-path qualification. Native FK/unique errors can reveal hidden existence; host reporting policy is explicit. Arbitrary host triggers may block or add locks, so no universal deadlock/performance guarantee applies outside a qualified profile.

## Testing

STP-030 allocates criteria. Trusted ledger/trigger fixture runs full selected corpus; induced trigger failure rolls back host and Truss effects. Forced-RLS read matrix uses reader/writer/no-access roles and direct child/key/join paths. Corrupt columns/constraints individually in disposable namespaces and require independent layout-check detection.

## Migration and Rollback

Initial fixture installation is disposable qualification only. Production host DDL requires its own authorization/runbook. Remove/revert host extensions only through host-owned migration; disabling policy cannot be presented as a harmless rollback. Canonical layout drift refuses support until explicit repair/migration, never blind automatic reinstall.

## Implementation Sequence

1. Define trusted extension/policy profile and inventory boundaries.
2. Create red coexistence/visibility/drift fixtures.
3. Reuse corpus/native comparator and qualify role/journal/lock behavior.
4. Publish only named tested profiles, not arbitrary host-extension safety.

## Risks and Gates

AC1 cannot prove every possible extension; exact profile scope and exclusions must be explicit while preserving required outcomes. RLS/guard authority and hidden-state counting remain shared design gates. Existing partial role benchmark does not qualify all read paths. Administrative ability to alter layout differs from contract permission to do so.


The STP-030 concrete host ledger proposal now supplies the trusted row-trigger source, separate physical observations/control, owner/ACL admission and complete-corpus/rollback schedules for the first named fixture. Harness extension setup consumes that source only in a disposable admitted layout/profile; it never installs implicitly or becomes an alternative journal producer. Actual native compilation, privilege isolation, complete normative corpus and journal-mode coexistence remain the implementation evidence. Physical ledger counts do not substitute for semantic event counts or exact authored-value fidelity.
