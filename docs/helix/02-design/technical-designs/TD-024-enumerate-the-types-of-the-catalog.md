---
ddx:
  id: TD-024
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-024
      kind: informed_by
    - id: SD-005
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
---

# TD-024: Consistent catalog enumeration

**Story:** [[US-024]]. **Parent:** [[SD-005]]. **Feature:** FEAT-005.

## Technical Approach

Enumerate complete catalog definitions under one qualified snapshot or head-lock context. A transaction alone at READ COMMITTED does not guarantee several statements see one revision; use CONTRACT-007's consistent context explicitly. Retain exact logical/storage identities, retired/provisional flags and revision. This operation feeds mapping consumers, not a source compiler.

## Component Changes

| Planned files | Change | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/catalog/enumerate.ts` | Complete type/property/key/endpoint reads in one context | US-024-AC1, US-024-AC2 |
| `packages/core/src/catalog/view.ts` | Deterministic identity-preserving assembly, no omitted definitions | US-024-AC1 |
| `tests/catalog/enumerate.test.ts` | Independent inventory and concurrent acceptance | US-024-AC1, US-024-AC2 |
| `tests/benchmarks/catalog-enumeration.ts` | 100-call native latency distribution | US-024-AC3 |

Components are new; assembly stays I/O-free.

## API/Interface Design

Consume the [draft catalog view binding](../contracts/bindings/truss-catalog-view-v0.1.d.ts) and CONTRACT-003 enumeration rules. The view preserves exact definitions and distinguishes full inventory from an authorized closed projection. Native loading and pure reference/inventory validation are separate components; no mapper may promote a projection or provisional entry into full validated model support.

CONTRACT-001/003 own catalog storage and acceptance; CONTRACT-007 owns context. The existing catalog-view binding and CONTRACT-003 enumeration rules define completeness, deterministic ordering, identity, flags and qualified role projection. Select exact original loader/assembly/resource/context producers and qualify their complete correspondence before publication; do not commission a parallel view contract. Do not expose mixed revision results as a valid mapping bundle.

## Data Model and Integration

No DDL. Read every required definition/member/endpoint for the selected catalog; do not confuse retired with absent or provisional with fully defined. Empty initial catalog returns revision zero and no types. A historical selection requires historical definitions, not filtering current rows by a guessed revision. Weft mapping export adds its own binding/pin obligations after this complete view exists.

## Security and Performance

Host supplies acting role. Module-filtered enumeration is explicitly a projection, not proof of full catalog availability; cross-module endpoint references need an authorized closure or refusal. Avoid N+1 reads using fixed catalog queries within the same context. Capture end-to-end decode/assembly time in the proposed 20 ms p95 benchmark, not server-only time masquerading as public latency.

## Testing

STP-024 owns allocation. Independent 1,000-type inventory includes properties, composite keys, endpoints and flags. Pause between component reads while another client accepts a distinguishable revision; answer must match exactly one expected inventory. Test empty and visibility-qualified catalogs separately. Benchmark pins dataset, server/runtime and measurement boundary.

## Migration and Rollback

No schema migration. Incompatible view/profile versions refuse. Missing meaning or resource overflow yields explicit incomplete/refusal policy rather than truncating success. Read failures change no database state. Preserve prior profile for consumers while qualifying new document identity.

## Implementation Sequence

1. Consume the authored complete enumeration result/context rules, select original loader/resource/authority profiles and create red inventory/race tests.
2. Implement fixed native reads and pure assembly.
3. Qualify role/identity closure and preregistered 100-call p95 measurement.

## Risks and Gates

D-04 document identity and authorized reference closure remain dependencies. READ COMMITTED multi-statement reads can mix revisions without lock/snapshot protection. The 20 ms target remains proposed, not measured. Completeness cannot be inferred from type count alone.


The STP-024 concrete experiment now specifies the proposed 1,000-type/four-property/two-key/ring-relationship fixture, complete expected memberships, selected context/cache/setup boundaries and exact 100-sample assessment/refusal controls. The benchmark runner consumes independently authored fixture/expected inventory and the registered experiment before invocation; it cannot derive the expected membership from enumeration output. Public decode/assembly stays inside timing while independent result comparison follows clock stop and still gates the whole series. Exact source/profile admission and server/adapter/cache/context selections remain prerequisites; authored cardinalities and synthetic assessor controls are not native latency evidence.
