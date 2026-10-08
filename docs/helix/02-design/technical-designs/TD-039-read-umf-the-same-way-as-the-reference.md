---
ddx:
  id: TD-039
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-039
      kind: informed_by
    - id: SD-007
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
---

# TD-039: Pinned UMF validation parity

## Technical Approach

Reference TypeScript composition invokes the pinned UMF library for validity and diagnostics. Truss then assesses its declared storage/semantic subset separately. Another-language implementation may use its own reader but must pass the pinned validity/diagnostic corpus. A valid supported document accepts; a valid unsupported selected feature refuses explicitly without relabeling it UMF-invalid. Unknown uninterpreted content remains preserved according to upstream meaning, not automatically rejected or silently understood.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/umf/validation.ts` | Browser-compatible pinned validator adapter and separate support assessment | US-039-AC1, US-039-AC2, US-039-AC3 |
| `packages/conformance/src/umf/parity.ts` | Language-neutral diagnostic comparison and version-scoped receipts | US-039-AC1, US-039-AC2, US-039-AC4 |
| `packages/conformance/corpus/umf/manifest.json` | Immutable source bytes, oracle pins and expected cases | US-039-AC4 |
| `tests/conformance/umf-parity.test.ts` | Positive/negative/support/version corpus gates | All criteria |

## Shared Interface

CONTRACT-003 step 1 owns validity; CONTRACT-004 owns corpus packaging. Record source byte digest, UMF core version, validator package/commit, schema/extension subset and result. Compare diagnostics as severity/code/path with multiplicity, not message text or presentation order. Define path normalization explicitly from upstream published semantics; do not discard pointer escaping, root location or document identity. Preserve reference warnings on accepted input. Truss support diagnostics have a separate namespace/stage so they cannot hide missing validator diagnostics.

## Corpus and Integration

Expected validity/diagnostics are frozen from a pinned reference run and reviewed against independently authored invalid conditions. Running the same current library on both sides without retained expected cases only proves adapter agreement. Include duplicate JSON members, malformed UTF-8, exact large numbers, ambiguous identities, local missing references, warning-only cases and unknown extensions as permitted by the upstream profile. Byte parsing behavior must be part of the declared validation pipeline rather than host JSON coercion. No network schema/model fetching.

UMF CONTRACT-045 is proposed: version tags or matching unknown keys cannot activate successor semantics. New core/extension/validator revisions receive a new corpus/evidence scope; never overwrite previous expectations to make drift green. Native PostgreSQL source model qualification remains separate from logical catalog validity. Weft's model checks are a compiler participation subset and cannot replace full pinned UMF validation.

## Testing, Sequence and Rollback

STP-039 allocates four criteria. Finalize validator API/pins and diagnostic normalization; author versioned expected cases; implement adapter and parity runner; qualify pure core in Bun and a real browser. Native acceptance tests assert invalid/unsupported documents have no persisted effects. Pin downgrade requires declared compatible scope and retained cases; no automatic newest-version fallback.

## Gates

Public validator result shape, exact parsing ownership, warning/path semantics, complete required corpus manifest and supported subset remain explicit integration decisions. AC1 applies to supported valid input; AC3 mandates explicit refusal outside that subset. Neither an empty fixture set nor a second-language promise qualifies parity.


### Recursive numeric owner boundary

The owner review at Weft 8de43d0 distinguishes exhaustive scalar decimal SUM evidence from missing recursive signed/decimal native procedures. B-012 must retain signed and exact decimal fields through record/sequence/map native homes; it cannot qualify that requirement through nonnegative integer fixtures, JSONB fallback or scalar aggregates. STP-039 RN-01–06 allocates exact signed bounds, decimal scale/token preservation, selected zero meaning, malformed unprojected siblings, original domain/codec substitution and fresh embedding/native parity. Requesting an unavailable original procedure refuses explicitly while the broader required integration remains open. Compiler procedure implementation stays Weft-owned; no additional UMF capability is commissioned.
