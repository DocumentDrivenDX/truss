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

Catalog mismatch, uniqueness/endpoint refusal, deadlock, serialization, cancellation before/after effects, cleanup failure, lost connection and uncertain commit. No-op equality covers absence/null and exact numeric policy; undeclared retained content is not automatically an error. The shared failure precedence is authored; original driver error/cause/termination and scope-containment producer adoption remains a gate. Native supplements verify database failures beyond synthetic shape assertions.

## Build Handoff

Consume the existing failure-order inventory/red tests, select exact equality and original failure/containment producers, then implement the shared pipeline. All four criteria and ownership/fault supplements block closeout. A complete error enum without observed state/retry behavior is insufficient.


## Complete diagnostics and original transaction outcome

Author two independent invalid properties whose expected rule/path/layer facts do not come from the production validator. Establish complete observation of both under the selected profile and expect one invalid result with both diagnostics and no operation effects. Separately exhaust the selected work/byte/deadline bound after the first violation but before the second is examined: no complete invalid result or success can be inferred from that prefix. Preserve original failure classification and confirm containment before any resource-unavailable outcome; unresolved native cancellation remains the original executor outcome. No automatic smaller request or callback replay supplies missing validation.

Run the valid and invalid requests inside a caller-owned transaction containing an earlier independently observed host sentinel. Valid application returns pending, with no driver COMMIT and no externally durable receipt/ID claim. Confirmed operation-local refusal preserves the sentinel and removes only this operation's effects. A host-requested outer rollback then removes the sentinel and valid pending effects together. Independently fault savepoint rollback/connection termination and assert no healthy transaction handle, fabricated no-change verdict or blind retry. Engine-owned execution separately requires confirmed outer settlement before a committed response. These are planned native/driver schedules, not runtime evidence.


## Shared failure-order handoff

Consume [the existing failure-order vectors](../../02-design/contracts/bindings/failure-order-v0.1.vectors.proposal.json) and CONTRACT-007’s native failure classification procedure, retaining their original scope. Expected outcomes come from the contract and independently authored observations, not a SQLSTATE-only switch. Bind every error, cancellation cause, command submission and termination/containment observation to the original issuer/epoch/ordinal/cycle before classification.

Planned boundary controls preserve confirmed commit through later bookkeeping failure; retain commit_unknown when original COMMIT submission is possible but confirmation is missing; retain transaction_unusable when submitted work or cleanup is unresolved; and permit whole_transaction retry for qualified serialization/deadlock only after the required original state/termination evidence exists. Caller ownership never authorizes Truss to restart the host transaction or invoke its callback again. A known cancellation code without admitted cause and containment cannot become cancelled. Unknown/malformed error evidence cannot manufacture business absence or authorization refusal. These native controls remain not_run, and shape-valid failure objects alone cannot satisfy AC4.
