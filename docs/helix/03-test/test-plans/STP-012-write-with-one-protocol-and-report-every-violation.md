---
ddx:
  id: STP-012
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-012
      kind: informed_by
    - id: TD-012
      kind: informed_by
    - id: SD-003
      kind: informed_by
---

# STP-012: Shared write protocol

## Story Reference

US-012, TD-012, SD-003, TP-001 and CONTRACT-004/007/009. Planned tests are not runtime evidence.

## Scope and Objective

Prove common mutation behavior, complete applicable diagnostics and defined retry advice without loss of transaction ownership.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-012-AC1 | `two_independent_violations_leave_no_effect` | Both rule/path diagnostics appear; canonical/derived/journal rows stay unchanged | `@covers US-012-AC1` | Native integration | `tests/mutations/protocol.test.ts`; accepted catalog, independent invalid properties |
| US-012-AC2 | `stale_expected_version_is_refused` | Defined conflict kind; stored row/version/journal unchanged, including otherwise-no-op request | `@covers US-012-AC2` | Native integration | Same file; stored v3 and expected v2 |
| US-012-AC3 | `exact_noop_does_not_advance` | No changed rows, derived effects or journal events; version unchanged | `@covers US-012-AC3` | Native integration | Same file; exact presence/value fixtures |
| US-012-AC4 | `failure_inventory_matches_retry_contract` | Each finalized contract failure maps to its expected kind/scope/retry advice; fatal/unknown commit does not trigger blind retry | `@covers US-012-AC4` | Contract | `tests/mutations/failures.test.ts`; contract-derived inventory and named native/transport fault supplements |

## Executable Proof

Future commands: `bun test tests/mutations/protocol.test.ts` and `bun test tests/mutations/failures.test.ts`. Actual files/harness do not exist. Tests carry criterion citations and receipts identify adapter/server/journal/ownership profiles. Missing required failure cases prevent full support.

## Data and Setup

Independent observer snapshots canonical, key, marker, journal and version state. Caller-scope cases include an earlier host sentinel write: ordinary refusal preserves it while removing call effects. Engine-owned cases prove rollback/commit behavior. Fault inventory is derived from finalized contract definitions, not implementation branches.

## Edge Cases and Failure Modes

Catalog mismatch, uniqueness/endpoint refusal, deadlock, serialization, cancellation before/after effects, cleanup failure, lost connection and uncertain commit. No-op equality covers absence/null and exact numeric policy; undeclared retained content is not automatically an error. Full error precedence remains a design gate. Native supplements verify database failures beyond synthetic shape assertions.

## Build Handoff

Create contract failure inventory/red tests, resolve precedence and equality gates, then implement the shared pipeline. All four criteria and ownership/fault supplements block closeout. A complete error enum without observed state/retry behavior is insufficient.
