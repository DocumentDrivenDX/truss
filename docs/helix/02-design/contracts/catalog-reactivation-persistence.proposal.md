# Selected reactivation persistence

The owner selected same-qualified-authored-identity reactivation on 2026-10-07 in ADR-004. CONTRACT-003's historical retirement-only masks and unresolved lifecycle wording do not override that decision. Distinct authored identities still allocate fresh identifiers; old grants are not restored automatically.

## Admission and target masks

Resolve the incoming original category/qualified lineage against the retained definition and original source history before allocation. A retired exact match retains its original storage identifier, category, owner, lineage preimage and creation revision. The selected lifecycle decoder admits clearing retired_rev only for an independently validated reactivation plan. It cannot clear retirement as a generic field update or silently allocate a substitute ID.

Validate current authorization, complete retained values, original codecs, required key memberships/reservations and relationship endpoint/ownership/cardinality against the admitted final graph. Rebuild required derived key memberships from retained original values under the selected bucket profile; do not restore obsolete object_key rows. Forbid-policy reservations remain binding. Unsupported edits while retired refuse under the selected semantic support profile; reactivation is not permission to mutate immutable identity or key encoding/components through ordinary acceptance.

## Atomic effect order

The [report 0.3 candidate](acceptance-report-v0.3.proposal.schema.json) composes the earlier reactivation inventory and complete-history rebind shapes under a distinct discriminator. The combined reference handoff selects this existing report v0.3 alongside history events, journal pages and retained-history archives v0.2 under CONTRACT-002 and CONTRACT-003. Selecting the composed wire shape does not qualify its native producer or consumer. Earlier report schemas remain separately versioned. Original bytes, complete actual-effect inventory and native semantic validation remain mandatory.

After original candidate admission and full reservations, insert the new revision origin/archive before dependent catalog/history rows. Apply exact permitted lifecycle changes and independently record original before/after definitions and retirement state. For type/property/relationship categories, preserve the admitted schema_change category/identity correspondence. Keys require the separate owner-local `(type_id,key_num)` lifecycle chain, not a global def_id surrogate.

The existing [key history SQL](key-lifecycle-history-v0.1.proposal.sql) and [UMF source](key-lifecycle-history-v0.1.proposal.umf.json) allocate that key chain. They remain outside historical profile 0.8 and are now composed into review profile 0.9; native producers and installation qualification remain required. Preserve positive actual revision and original sequence order, exact complete before/after bytes, creation basis and contiguous admitted history. Shape constraints alone cannot establish chain completeness. No-change repeat adds no history or new head.

Apply required graph/key/rebind/journal effects through protected producers. Independently compare all actual catalog, key-history, graph, journal and source effects to the retained plan. Only then finalize the immutable separate acceptance report with actual generated metadata, insert it and publish the head under CONTRACT-012's selected report home. A report generated before actual effect verification cannot claim complete reactivation. Failure at any phase rolls back the complete acceptance; uncertain outer commit retains original recovery custody.

The report must enumerate each reactivated category/qualified identity, retained storage ID, original prior retirement and resulting live state, full definition/source pins and actual key/history/rebind effects under its selected report profile. An additions-only report, opaque extension or cleared flag cannot substitute for that inventory. Exact repeat returns the original admitted report under current authority without new allocation or history.

## Independent planned acceptance

The [TypeScript 0.3 binding](bindings/truss-acceptance-report-v0.3.proposal.d.ts) matches the composed report discriminator and adds explicit owner-local reactivation entries. Its type controls reject unowned/global/numeric keys, missing original definitions and implicit old-report upgrade. Type success cannot validate canonical numeric ranges, artifact digests, complete transition membership or native authority.

The [composed report schema check](../../04-build/evidence/design-audit/check-composed-report-v0.3.ts) validates a complete synthetic report containing both rebind events and owner-local reactivation entries. Its [fourteen shape controls](../../04-build/evidence/design-audit/composed-report-v0.3-shapes.json) refuse omitted lifecycle/profile/original-execution evidence, an unowned key, old or mixed event versions, a retain event substituted into rebinds, an opaque lifecycle substitution, unknown root content and implicit old-report upgrade. An explicit empty reactivation inventory remains shape-valid; completeness against actual transitions is a semantic producer/admission obligation. Fixture digests are placeholders. These controls do not establish original artifact fidelity, native ranges, actual-effect membership or runtime qualification. Earlier v0.2 wrapper and lifecycle-fragment evidence keeps its original scope.

CP-01 retire then reactivate the same qualified identity: retained IDs and creation revisions match originals; current authority and full final invariants pass; complete report/history records the transition.

CP-02 same label with distinct document/authored identity: allocate fresh ID, preserve retired original and do not transfer its permissions or history.

CP-03 retain an incompatible value, reserved-key collision or invalid relationship endpoint/cardinality: reject reactivation without flag, graph, report or head effects.

CP-04 reactivate keys on two owners with equal local key numbers: history/lookup/report remain owner-local; global def_id substitution and omitted interval refuse.

CP-05 fail after retirement-state change, graph rebuilding, history insertion or report insertion; independent post-rollback inventory equals the original. Lost commit acknowledgment reconciles originals without allocating or reactivating again.

CP-06 exact repeat after later revisions or grant changes: no new history/allocation; original report is disclosed only under current complete owner authority.

These tests are planned. This design reconciles the chosen lifecycle behavior; it does not qualify native producer bodies or adopt unrelated ADR-005/006/007 capabilities.
