---
ddx:
  id: STP-002
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-002
      kind: informed_by
    - id: TD-002
      kind: informed_by
    - id: SD-001
      kind: informed_by
---

# STP-002: Dependency ordering

## Story Reference and Scope

US-002, TD-002, SD-001, TP-001 and CONTRACT-003. Native acceptance tests remain planned; current UMF registry representation and private original supplied-source/graph components have scoped execution evidence.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-002-AC1 | `valid_dependency_package_orders_sales_before_orders` | Either submission order records sales then orders and resolves endpoint through qualified owning identity | `@covers US-002-AC1` | Native integration | `tests/catalog/dependencies.test.ts`; future upstream-valid pinned package |
| US-002-AC2 | `valid_mutual_dependency_component_accepts_in_byte_order` | Upstream-valid mutual dependency accepts atomically with component members in exact identifier byte order | `@covers US-002-AC2` | Native integration | Same file; upstream cycle-policy gate |
| US-002-AC3 | `submission_permutations_have_identical_recorded_order` | All tested permutations produce identical ord and phased catalog result | `@covers US-002-AC3` | Native integration | Same file; valid independent and future dependent sets |

## Supporting Algorithm and Failure Tests

Implemented private `tests/catalog-document-order.test.ts` covers disconnected components, cycles with outgoing dependencies, diamonds, Unicode byte ties, duplicate/missing identities and bounded graph limits using independently authored expected orders. These cannot substitute for native validity/acceptance criteria. Native fixtures pin upstream package schema/validator and retain exact document digests. No fabricated cross-document syntax or host resolver may make tests green.

Compare catalog endpoint ownership and ord directly; an algorithm returning the expected vector while persisting another order fails. Missing required dependencies block upstream validity; optional Truss unknown policy applies only to valid input. Failure leaves no partial component revisions.

## Executable Proof and Handoff

Current command `bun test tests/catalog-document-order.test.ts` runs ten tests/541 assertions against all small vector permutations and a nonrecursive 4,096-document chain. With `TRUSS_UMF_PRODUCER` pointing to the exact pinned original producer, `bun test tests/catalog-endpoint-intent-basis.test.ts tests/catalog-endpoint-source-references.test.ts tests/catalog-document-order.test.ts` runs 30 tests/609 assertions across original supplied sources, Records/keys and ordering. Future native `tests/catalog/dependencies.test.ts` still requires adopted complete original package/cycle/accepted-source semantics and installed protected acceptance. All three criteria block closeout. Report algorithm-only evidence separately from blocked native package cases.

## Independent component ordering vectors

Abstract validated graph notation is `dependent -> dependency`; these are pure algorithm cases, not invented UMF wire syntax. For A->B and B->A plus C->A, expected order is A,B,C. For that same cycle plus unrelated D, ready-component vector [A,B] sorts before [D], yielding A,B,C,D because C becomes ready and C sorts before D. For A->C, B->C and unrelated D, expected order is C,A,B,D. Each input permutation must preserve these exact vectors. Native acceptance remains separately gated on upstream-valid representation.


The [eight authored graph vectors](../document-order-v0.1.proposal.vectors.json) make the component and byte-order expectations concrete. Enumerate every node and edge ordering for each valid small graph; compare the complete independently authored order. The U+E000/U+10000 case detects default JavaScript UTF-16 sorting, and the NFC/NFD case detects normalization. The A/Z cyclic component must finish before unrelated B even though B sorts before Z individually. Duplicate document and missing dependency cases refuse rather than manufacturing graph vertices. The original vector artifact retains its authored_not_run source label; the current private runner executes all small node/edge permutations as reported above. Its execution does not supply complete adopted cross-document semantics or native acceptance evidence.
