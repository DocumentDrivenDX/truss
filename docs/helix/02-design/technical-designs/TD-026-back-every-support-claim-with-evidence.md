---
ddx:
  id: TD-026
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-026
      kind: informed_by
    - id: SD-006
      kind: informed_by
---

# TD-026: Versioned support evidence

**Story:** [[US-026]]. **Parent:** [[SD-006]]. **Feature:** FEAT-006.

## Technical Approach

Build support statements from immutable run receipts and exact contract/profile/source digests. A statement is qualified by actual PostgreSQL patch version, implementation/adapter, UMF version/subset, layout, role/mode and relevant Weft pins. Missing runs are unverified; mismatch with governing contract is stale; failed runs remain visible. Regeneration adds a new run reference without rewriting historical receipts.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/conformance/src/evidence/receipt.ts` | Validate version/digest/case/result/command evidence shape | US-026-AC1 |
| `packages/conformance/src/evidence/support.ts` | Assemble qualified support, stale/unverified/failure states | US-026-AC1, US-026-AC2, US-026-AC3 |
| `tests/evidence/support.test.ts` | Independent missing/stale/failed/regenerated fixtures | All criteria |

New tooling components do not enter the pure runtime core.

## API/Interface Design

CONTRACT-004 owns conformance evidence/pass rules. CONTRACT-011 now defines receipt/support semantics, required inventory and exact digest matching; executable wire schema and trust bindings remain gates. Weft evidence declarations are references, not transferred Truss native qualification.

## Data Model and Integration

No database DDL. Evidence files are immutable addressed artifacts with complete required-case inventory and actual command/environment outcomes. Source/contract hashes bind the run; a new contract makes old evidence stale for that claim, not historically false. Links must resolve to executable procedure and retained results, not merely design prose. Unsigned/externally supplied receipts require declared trust provenance.

## Security and Performance

Receipts cannot select executable imports or expose connection secrets. Host chooses trusted runners. Validate bounded receipt content and references before rendering support. Cache by exact digest only; never reuse stale qualification by matching a friendly version label. Report assembly scales with manifest size and must preserve failures rather than omit them for compactness.

## Testing

STP-026 allocates criteria. Independently author receipt fixtures with exact versions/hashes and missing/stale/failed cases. Change contract bytes without changing its display name and require stale outcome. New run must bind new hash, while old run remains accessible. Native runner authenticity is separately qualified; schema validity alone cannot prove a test ran.

## Migration and Rollback

Version evidence/support schema separately. Retain original receipts and explicit adapters for old schemas, refusing unknown required fields. Roll back support publication to an earlier profile only with its matching contracts/implementation; never relabel old evidence as current. Regeneration failures do not erase the prior run or hide new failure.

## Implementation Sequence

1. Contract receipt/support/trust schema and create red missing/stale/regeneration cases.
2. Implement bounded validation and statement assembly.
3. Integrate real runner outputs, digest/link verification and immutable retention.
4. Review every support claim against required-case matrix before publication.

## Risks and Gates

Exact receipt schema, trusted runner provenance and support profile selection remain shared-contract work. Time recency is weaker than digest identity. Missing targets or skipped required cases cannot become full support. A historical spike's environment cannot qualify a newly changed contract by citation alone.

Index/statistics readiness wires now preserve separate original declaration/attempt, installed definition versus collection and unknown failure outcomes under CONTRACT-003. They are native observation inputs, not performance/integrity evidence. Exact inventory/current-attempt/collection producer admission remains mandatory.

Explicit physical-job tooling now separates supplied-transaction pending admission from actual admission-commit observation and explicit original index/statistics execution. Accepted catalog commit alone cannot start a pending queue attempt. Original issuer/fence/native inventory and uncertain termination remain mandatory.
