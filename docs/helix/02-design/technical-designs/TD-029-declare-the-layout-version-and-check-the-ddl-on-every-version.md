---
ddx:
  id: TD-029
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-029
      kind: informed_by
    - id: SD-007
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
---

# TD-029: Layout compatibility and native checks

**Story:** [[US-029]]. **Parent:** [[SD-007]]. **Feature:** FEAT-007.

## Technical Approach

Read the normative installed schema marker before runtime writes and compare explicit layout compatibility. SQL comments are documentation, not the sole installed-version authority. Refuse incompatible major layouts without mutation. Run independent layout behavior/inventory checks on every advertised native target; unsupported server versions remain unverified rather than assumed compatible.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/layout/verify.ts` | Installed marker and required-surface compatibility preflight | US-029-AC1 |
| `packages/conformance/src/layout/native.ts` | Matrix installation/check receipts and independent physical inventory | US-029-AC2, US-029-AC3 |
| `tests/layout/compatibility.test.ts` | Major mismatch, missing marker and native behavior probes | All criteria |

Reuse US-045 bootstrap comparator; do not create a second layout authority.

## API/Interface Design

CONTRACT-001 owns marker/version compatibility; CONTRACT-008 owns generated bootstrap/parity and authority transition; CONTRACT-004 owns qualification evidence. Resolve blanket minor-version acceptance versus required capability inventory in governing contracts before publication. A compatible version label cannot excuse missing selected physical meaning.

## Data Model and Integration

No new runtime DDL. Fixed layout marker, SQL comment, native UMF model and generated artifact must name a consistent candidate version. Current SQL header/comment drift is explicit bootstrap cleanup. Behavioral probes cover key uniqueness, typed endpoints, restrictive deletion, exact values, journal coverage and no default partition. Checks cannot infer original lexical numeric preservation from mathematical equality.

## Security and Performance

Host owns connection and allowed namespace; validate names and use read-only compatibility inspection before effects. Writer cannot alter installed marker to bypass verification. Test installer uses disposable administrative principal, then runs behavior attacks as ordinary writer. Cache verification only with explicit invalidation/immutability assumptions; a stale cache must not ignore incompatible alteration.

## Testing

STP-029 owns criteria. Native baseline/generated layouts are checked independently. Corrupt marker, remove constraint or add default partition in disposable fixtures and require refusal/failure. Retain actual server patch/runtime/profile digests and all probe outcomes. Historical 16.2/17.9 evidence does not qualify changed layout automatically.

## Migration and Rollback

Startup never repairs an incompatible namespace. Fresh installation is separate from existing-data migration. Breaking layout changes require new major contract and reviewed migration; minor additions must preserve prior required behavior. Rollback cannot reinterpret an incompatible marker as supported or destructively reinstall over data.

## Implementation Sequence

1. Reconcile marker/comment and minor compatibility policy.
2. Write red mismatch/missing-surface fixtures and complete probe manifest.
3. Implement preflight and reuse independent bootstrap native runner.
4. Run required target matrix and publish scoped compatibility receipt.

## Risks and Gates

The story's comment-based version language is stale relative to installed schema marker. Blanket minor acceptance requires explicit compatibility guarantees; layout 0.x is draft, not a stable universal ABI. Exact-value and guard gaps remain independent probe gates. DDL parser success is not native behavior evidence.
