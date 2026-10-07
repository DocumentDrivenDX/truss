---
ddx:
  id: TD-012
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-012
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
---

# TD-012: Shared write protocol and complete violations

**Story:** [[US-012]]. **Parent:** [[SD-003]]. **Feature:** FEAT-003.

## Technical Approach

Route every public mutation through one executor orchestration boundary. CONTRACT-004 owns the protocol; CONTRACT-007 qualifies ownership/savepoints and CONTRACT-009 supplies complete lock planning. Read/check catalog under the head gate, acquire planned locks, compare expected version, validate all applicable independent rules, simulate effects, persist/journal once and finalize according to transaction ownership. A caller-owned successful result is pending until host commit; never label it committed.

Collect independent validation failures without short-circuiting after the first. A prerequisite failure that makes a dependent rule unevaluable is not a fabricated second violation; preserve deterministic diagnostics and the governing rule/path. No-op comparison uses exact logical value/presence policy, not host JSON equality. Unknown accepted content is retained/reportable rather than invalid solely because it is undeclared.

## Component Changes

| Planned files | Change | Criteria |
| --- | --- | --- |
| `packages/core/src/mutations/validate.ts` | Deterministic complete applicable-rule collection | US-012-AC1 |
| `packages/core/src/mutations/diff.ts` | Catalog-directed effect/no-op classification | US-012-AC3 |
| `packages/postgresql/src/mutations/execute.ts` | Shared head/locks/version/effects/journal pipeline and call scope | US-012-AC1, US-012-AC2, US-012-AC3 |
| `packages/postgresql/src/mutations/errors.ts` | Contract error mapping without blind retries | US-012-AC4 |
| `tests/mutations/protocol.test.ts`, `tests/mutations/failures.test.ts` | Native state/refusal observations and boundary fault cases | All criteria |

Components are new. Pure validation/diffing remains browser-compatible; I/O/transaction control stays in the executor.

## API/Interface Design

CONTRACT-004 owns mutation signatures, violation reports and domain failure kinds. CONTRACT-007 adds cancellation, transaction_unusable and commit_unknown behavior and caller/owned durability. Resolve overlapping error precedence there before exposing a public union; this TD cannot invent a competing error vocabulary. CONTRACT-009 owns retries caused by stale preflight state.

## Data Model and Integration

No new tables. Object/edge versions and derived rows change only for actual effects. A no-op must not emit journal rows or advance the record version; internal locks are permitted. Check expected version at the specified protocol stage even if the supplied value would otherwise be unchanged. Each journal mode has one writer path. Validation failure rolls back the call scope and leaves canonical/derived/journal data unchanged.

## Security and Performance

Host supplies authenticated acting role and connection; derive no privilege from mutation input. Parameterize writes, constrain diagnostic disclosure and preserve host work outside the call savepoint. Validate bounded payloads before expensive scans under locks where semantically safe. Cache compiled validators by catalog/profile pin, never by display name. Measure lock duration without dropping required checks.

## Testing

STP-012 owns criteria. Observe old/new rows, keys, markers, journal and version independently. Force catalog staleness, version conflict, two violations, exact no-op, unknown retained content and each documented database/transport failure. Tests distinguish ordinary statement refusal from transaction-fatal failure and uncertain commit; retry advice never proves the original commit did not happen.

## Migration and Rollback

No layout migration. Failed owned calls roll back their transaction; caller calls roll back only their call savepoint when usable. Transaction-fatal outcomes require host whole-transaction recovery; never retry inside an unusable transaction. Rollback of an executor release restores the prior qualified package/profile, not stored-data rewriting.

## Implementation Sequence

1. Create red validation/version/no-op cases and a contract-derived failure inventory.
2. Finalize error precedence and exact no-op semantics in shared contracts.
3. Implement pure validation/diffing, then executor/version/journal wiring.
4. Exercise faults on owned and caller scopes, then confirm every public mutation reaches the same pipeline.

## Risks and Gates

D-05 exact equality/presence and D-06 replay may affect no-op results. CONTRACT-004/007 need one explicit error precedence/retry matrix before AC4 is complete. Failure tests require named injection points and observed state; generic thrown-error tests are insufficient. Completeness applies to evaluable rules under the selected supported profile, never a claim of all UMF semantics from a bounded validator.
