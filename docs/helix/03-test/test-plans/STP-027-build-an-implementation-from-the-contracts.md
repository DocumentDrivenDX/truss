---
ddx:
  id: STP-027
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-027
      kind: informed_by
    - id: TD-027
      kind: informed_by
    - id: SD-007
      kind: informed_by
---

# STP-027: Language-neutral corpus

## Story Reference

US-027, TD-027, SD-007, TP-001 and CONTRACT-004. Tests/review procedures are planned.

## Scope and Objective

Prove case completeness and meaningful alias comparison, plus contract-only implementability review.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-027-AC1 | `contract_only_operation_walkthrough` | Independent reviewer derives operation behavior/error/state obligations without reference code; missing decisions fail readiness | `@covers US-027-AC1` | Contract review | `tests/conformance/contract-walkthrough.md`; recorded evidence and unresolved findings |
| US-027-AC2 | `case_requires_all_normative_expectations` | Setup/operations/results/state/journal/report required; SQL marked informative; missing section refuses | `@covers US-027-AC2` | Contract | `tests/conformance/corpus.test.ts`; independent valid/corrupt cases |
| US-027-AC3 | `alias_comparison_ignores_only_allocations` | Different opaque ID allocations compare equal; wrong endpoint/alias relationship still fails | `@covers US-027-AC3` | Contract | Same file; two allocator permutations and deliberate identity defect |

## Executable Proof

Future command `bun test tests/conformance/corpus.test.ts` validates executable cases. AC1 additionally requires its documented review procedure/evidence; no unit test substitutes for implementability. All cases cite criteria and pin corpus/contract/profile digests.

## Data and Setup

Independently authored expectations include objects, edges, journal and reports. Preserve meaningful authored keys, ordering/version relationships and exact values. Alias normalization never compares allocator-specific IDs but must check their graph relationships. Missing required case semantics fail full-profile support.

## Edge Cases and Failure Modes

Unknown unselected optional tags may be outside a profile; unknown required semantics cannot be skipped. This policy is now aligned in the story and feature; executable schema/evidence still remain. Reference-code-generated expected outcomes fail independence review. Fixture contradiction with accepted ADR is a fixture defect, not permission to modify accepted meaning silently.

## Build Handoff

Resolve case policy and exact schemas, author red fixtures, implement normalizer/runner and execute contract-only walkthrough. All criteria block closeout. No second-language implementation support is claimed until its own independent corpus/native evidence exists.

Compiled bridge boundary plan under CONTRACT-007: independently test ASCII components at 63/64 bytes and multibyte `é` at 31/32 repetitions (62/64 UTF-8 bytes), mixed case, literal dot and embedded quote. Inspect exact compiler SQL/component provenance and actual server setting; no truncation fallback. Slots 1..1024 preserve values/origins and order; 1025, missing/duplicate/out-of-order positions or unknown native type refuse before native preparation. Two equal values retain separate original positions; unsigned-64 maximum remains exact lexical typed input through actual prepared binding without host Number rounding. Instrument driver submission counts to detect hidden splitting/interpolation/callback rerun. Missing backend registration/profile/transport obligations produce refusal rather than a primitive-only support claim. These are future native/packed bridge cases; upstream primitive unit-test source is not their execution evidence.
