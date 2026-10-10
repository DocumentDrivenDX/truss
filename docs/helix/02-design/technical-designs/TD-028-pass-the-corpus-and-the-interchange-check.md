---
ddx:
  id: TD-028
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-028
      kind: informed_by
    - id: SD-007
      kind: informed_by
    - id: CONTRACT-011
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
---

# TD-028: Corpus and bidirectional interchange

**Story:** [[US-028]]. **Parent:** [[SD-007]]. **Feature:** FEAT-007.

## Technical Approach

Run the complete required corpus on a qualified implementation/server/profile and compare all normative observations. Interchange separately runs A writes/B reads and B writes/A reads against the same fixed-layout database. Independent expected fixtures arbitrate agreement: two implementations sharing one bug cannot qualify by agreeing with each other. Unsupported newer required semantics refuse full pass.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/conformance/src/runner/pass.ts` | Required-case aggregation and exact profile receipt | US-028-AC1 |
| `packages/conformance/src/runner/interchange.ts` | Bidirectional execution/read orchestration and native observers | US-028-AC2 |
| `packages/conformance/src/runner/divergence.ts` | Structured mismatch evidence and triage status | US-028-AC3 |
| `tests/conformance/interchange.test.ts` | Deliberate wrong adapters and fixture defects | All criteria |

Harness components are new and outside runtime core. Real independent second implementation remains a future dependency under proposed ADR-003.

## API/Interface Design

CONTRACT-004 owns pass/interchange rules and adapter/corpus schema. TD-026's receipt work supplies exact evidence pins. Shared divergence schema must distinguish observed mismatch from reviewed attribution; the runner cannot automatically prove which implementation or contract is wrong without an independent oracle/review.

## Data Model and Integration

No DDL. Each direction uses fresh isolated case state and declared identity aliases. Readers must independently decode actual canonical rows/journal, not reuse writer serialization. Required result/state/report/journal expectations remain normative; host extensions are explicitly outside the selected pass profile. Exact implementation build, adapter, server, layout, UMF and corpus/contract digests are recorded.

## Security and Performance

Trusted host selects adapters; case input cannot choose executable paths. Disposable database principals and cleanup prevent cross-case contamination. Bound evidence output without truncating mismatches. Sharding is allowed only with complete manifest accounting; retry-to-green cannot hide a failure. Performance benchmarks remain separate from interchange correctness.

## Testing

STP-028 allocates criteria. Test missing/skipped/newer required cases, asymmetric decoding, wrong endpoint alias and deliberate journal/report divergence. Preserve both observed outputs and independent expectations. Full AC2 native evidence requires two independently implemented readers/writers, not two wrapper names around the same core.

## Migration and Rollback

Version profiles/receipts; preserve prior runs. An incompatible layout or corpus pin refuses rather than mutates a shared database. Failed cases retain diagnostic evidence and clean their isolated resources. Withdraw an invalid support statement without rewriting historical results.

## Implementation Sequence

1. Admit the complete selected case-adapter/corpus manifest and original producer/resource profiles; consume authored receipt/divergence/run/assessment wires and create red aggregation/asymmetry fixtures.
2. Implement orchestration and independent native observations.
3. Run the first implementation corpus; qualify bidirectional native interchange when a truly independent implementation exists.
4. Review mismatch attribution and publish exact scoped receipts.

## Risks and Gates

Independent implementation availability gates full interchange evidence. Agreement alone is insufficient; shared codec/expected generator bugs require independent oracle checks. US-028-AC3 attribution may need human review; preserve unresolved status instead of inventing blame. Unknown required cases must never count as not-applicable success.

CONTRACT-011 now separates runner pre-effect resource refusal, post-effect original interruption, complete honestly recorded stopped receipts and assessor resource unavailability. STP-028 supplies seven independent scenarios. Select exact complete evidence producer/allocator/custody/containment profiles before implementing orchestration; average outcome sizing, case omission and cached qualification are forbidden. No second implementation/native interchange evidence follows from these authored procedures.

The divergence wire in CONTRACT-011 now separates complete immutable observed evidence and original reviewed attribution. Unresolved triage preserves honesty during investigation but leaves US-028-AC3 incomplete; closeout requires recognized original review identifying implementation A/B/both or contract with complete governing/oracle evidence. Actual independent implementation/native evidence remains required for AC2.

Runner tooling now has explicit inert original-service construction, host-approved manifest/environment/configuration capture and prepared/original-run/reconciliation/cleanup boundaries under CONTRACT-011. STP-028 adds six factory/retained-lifetime scenarios; exact runtime original service/producer/store recognition remains selected design/adoption work. This tooling stays outside browser-compatible runtime core and construction cannot start native tests or terminate host resources.
