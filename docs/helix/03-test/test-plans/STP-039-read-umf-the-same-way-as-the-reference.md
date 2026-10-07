---
ddx:
  id: STP-039
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-039
      kind: informed_by
    - id: TD-039
      kind: informed_by
    - id: SD-007
      kind: informed_by
---

# STP-039: UMF reference parity

## Story Reference and Scope

US-039, TD-039, SD-007, TP-001 and CONTRACT-003/004. Tests are planned. Pin exact oracle/version/subset and distinguish validity from Truss support.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-039-AC1 | `supported_reference_valid_cases_accept` | Every required supported valid case accepts, including warning-only input retaining warnings | `@covers US-039-AC1` | Contract | `tests/conformance/umf-parity.test.ts`; frozen valid cases |
| US-039-AC2 | `invalid_cases_match_diagnostic_multiset` | Rejected cases match every severity/code/path with multiplicity; dropped/extra/wrong-path diagnostics fail | `@covers US-039-AC2` | Contract | Same file; independently authored invalid conditions and pinned reference receipt |
| US-039-AC3 | `valid_unsupported_selected_semantics_refuse_explicitly` | Valid but unsupported selected feature produces Truss support refusal without silent acceptance or rewritten validity | `@covers US-039-AC3` | Contract | Same file; declared subset and supported/unsupported controls |
| US-039-AC4 | `version_scoped_manifest_cannot_reuse_stale_pass` | Cases name target versions; receipt reports only complete passed version/subset scopes and blocks stale/missing pins | `@covers US-039-AC4` | Contract | Same file; two immutable version manifests |

## Data and Additional Probes

Portable-key envelope controls pin UMF public validator and tuple API separately. An evidenced 0.6.0/0.7.0 key envelope exercises qualified encoding; a validator-valid newer envelope without an evidenced tuple dispatch produces unsupported selected-profile refusal, preserving validity diagnostics and exact bytes with no catalog/data/history effects. Silent envelope-version substitution, dropped keys, names/ordinals replacing stable IDs and stale tuple receipts fail. A metadata-preservation profile explicitly leaves dependent capabilities unavailable and cannot count as writable-profile acceptance. Any explicit conversion retains original source/loss evidence and independently validates the target key subset.

Freeze byte digests, validator/schema/extension pins, validity and diagnostic multisets. Intentionally remove a required case or alter path/severity/code and require failure. Message wording alone is not compared. Test pointer escaping, root/document qualification and warning propagation once upstream normalization is pinned. Unknown unselected extensions must retain content within the declared profile; proposed envelope keys do not activate future semantics.

Run the same required pure-core corpus in Bun and real Chromium with no Node globals/network. Native acceptance integration separately proves invalid/unsupported inputs do not alter head/catalog/data. Second-language implementations must supply their own complete receipt; reference-only execution cannot claim interchange.

## Executable Proof and Handoff

Future command `bun test tests/conformance/umf-parity.test.ts` plus planned browser harness requires actual files and complete manifests. Finalize API/pins/path normalization and supported subset, author expected cases, then implement. All four criteria block closeout; version coverage is never inferred from shared names.
