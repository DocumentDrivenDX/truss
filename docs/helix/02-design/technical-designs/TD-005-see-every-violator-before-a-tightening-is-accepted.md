---
ddx:
  id: TD-005
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-005
      kind: informed_by
    - id: SD-001
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
---

# TD-005: Tightening and total transforms

## Technical Approach

Compute candidate assertion changes, then scan all affected current data under catalog-head exclusion using administratively complete visibility. Report every violator by typed record identity/source assertion/path. Accept only if all required checks complete and succeed. A type/cardinality change requires an explicit qualified total transform; apply and validate its candidate results atomically with definitions/history/journal/head.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/catalog/diff.ts` | Tightening/type-change classification and required transform detection | US-005-AC1, US-005-AC4 |
| `packages/postgresql/src/catalog/violators.ts` | Complete locked data scan and stable diagnostic identities | US-005-AC1, US-005-AC2 |
| `packages/core/src/catalog/transforms.ts` | Versioned trusted transform descriptor and exact result validation | US-005-AC3, US-005-AC4 |
| `packages/postgresql/src/catalog/accept.ts` | Atomic transformed effects, history and journal ownership | US-005-AC2, US-005-AC3 |

## Transform Boundary and Semantics

Transform descriptors/callbacks must be explicit trusted host registration, never executable source from UMF bytes. Define portable operation/profile semantics, deterministic exact value inputs/outputs, null/absence/cardinality handling, resource limits and error locations in the shared contract before implementation. No network or arbitrary database mutation in pure transform evaluation. Declared totality is verified over every affected stored value, not assumed from a label; broader mathematical totality is not claimed without a stronger contract.

Validate final transformed graph including keys, uniqueness, endpoints/participation and retained binding. Build replacement derived rows using shared canonicalization; collision after transform rejects atomically. Historical definitions must interpret prior values; transform journal includes each actual changed value with correct old/new definition revisions and one journal owner. Identity/no-op values need explicit journal/version policy.

## Completeness, Ordering and Security

Scan every violating row, including hidden modules under qualified administrative acceptance role. Bounded internal pages are allowed, but the complete required scan and final report must fit the selected containing work/storage/disclosure profile. Exhaustion returns explicit incomplete/resource refusal, never a truncated complete rejection or acceptance. No spill/export handle is required by the current contract; any future such profile needs its own exact snapshot, byte custody, authority, resource and lifecycle qualification before use. Failed or interrupted scan is incomplete and rejects rather than accepting partial evidence. Text-length semantics must match UMF facets exactly (code points/units/normalization), not host string length guessed from a name.

CONTRACT-003 now evaluates declared transforms without persistence, validates complete candidate state, and persists those same checked outputs. It never reinvokes a stateful transform during persistence. The exact transform profile, bounds and no-op/version attribution remain gates. Catalog lock excludes conforming writes throughout revalidation/persistence; bypass writers require the advertised enforcement profile.

## Testing and Handoff

STP-005 allocates four criteria. Finalize transform profile/check order/completeness carrier; author red multiviolator/no-transform/late-failure tests; implement scans then atomic migration. Failed transform removes catalog/data/keys/journal/report/head changes. Caller transaction rollback remains authoritative. Code rollback cannot reverse an already committed transform without a separate lossless reviewed migration. All runtime files/tests are planned.

Transform callback input/result wires are authored under CONTRACT-003, preserving exact absence/null and prior-state dependency boundaries. Original registration/dependency/profile admission and complete candidate-state validation remain mandatory; callback shape cannot establish purity or totality.

Transform registration now uses the original assembly/callback custody API. Resolve exact catalog selection, unique definition/dependency inventory and qualified execution before invocation. The synchronous callback cannot silently become an async worker; trusted cooperation does not establish interruptible hard deadlines. Retain each exact result once for candidate validation/persistence. Execution/isolation/resource profiles remain design outputs.

Transform registration now requires canonical immutable manifest provenance binding implementation/environment, resource/execution/value/dependency profiles and definition pairs. Registration pin hashes exact manifest bytes; duplicate runtime fields must match, and original host recognition binds the actual function. Names/function.toString cannot qualify closure identity. Changed semantics cannot reuse the old accepted transform pin. Retained exact repeat never reruns the callback.

Acceptance report retains complete original transform registration manifests and implementation recognition in a required inventory. Verify exact set equality against distinct accepted-input pins and persist atomically before head advance. Retained exact repeats do not invoke callbacks or substitute current manifests.
