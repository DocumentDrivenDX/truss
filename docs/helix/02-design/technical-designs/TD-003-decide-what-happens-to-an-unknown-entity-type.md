---
ddx:
  id: TD-003
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-003
      kind: informed_by
    - id: SD-001
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
---

# TD-003: Explicit unknown-endpoint policy

## Technical Approach

After upstream validity/support checks and whole-set type derivation, classify unresolved endpoint identities against supplied documents and qualified accepted definitions. Default reject names every unresolved endpoint and relationship. Provisional creates one stable catalog type per exact qualified identity, with no properties/keys and retained instance content. Skip omits the entire affected relationship and records source-qualified loss. No silent endpoint substitution or partial endpoint-triple derivation.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/catalog/unknown.ts` | Unknown identity classification, policy and loss/report entries | US-003-AC1, US-003-AC2, US-003-AC3 |
| `packages/postgresql/src/catalog/provisional.ts` | Atomic placeholder allocation and later same-id definition | US-003-AC2, US-003-AC4 |
| `packages/postgresql/src/catalog/derive.ts` | Whole-set phased relationships and existing identity lookup | US-003-AC1, US-003-AC2, US-003-AC3, US-003-AC4 |

## Upstream Gate and Identity

UMF's current relationship resolver rejects missing required local endpoints. Truss cannot convert that invalid document into valid input by selecting provisional/skip. Proposed package dependencies do not yet supply a valid unresolved-reference category. All three policy branches require an upstream-valid representation or an adapter whose own valid output carries the unresolved semantic content and explicit loss contract; do not fabricate a resolved stub merely to evade validation. D-04 must reconcile this requirement with upstream ownership before native acceptance is build-ready.

Committed UMF owner CONTRACT-045 at origin/master `1f7b5f5d2a355c4b476e3a96b289b9048f03f567` remains a design proposal with no implemented schema/API/migration. Its reference-bearing member table explicitly leaves current relationship endpoint rules unchanged; structurally preserved unresolved external references do not authorize operations requiring their meaning. Therefore adopting that proposal is neither an available dependency nor sufficient proof for these positive relationship-policy criteria. The owner’s direction that current UMF is sufficient remains in force: do not request or wait for generic upstream feature work. Truss must identify a concrete already-valid owner adapter/extension representation with qualified endpoint identity and loss semantics, or obtain an explicit product resolution of this demonstrated requirement conflict. Current invalid local input still refuses before every policy effect. Keep AC1–AC4 in the scope and mark positive provisional/skip/promotion unavailable until that exact representation is admitted.

Provisional identity needs owning document/module/element, not a name guess. Define how absent owner/revision pins are represented and how later authoritative definitions claim the placeholder without merging unrelated identities. Existing physical unique(module,element) is insufficient for competing owning documents. Preserve source references and never normalize names into identity. Multiple relationships to one exact unknown share one placeholder; differently qualified unknowns remain distinct.

## Definition and Stored Data

Use CONTRACT-001's independent document-source pointer candidate for future admitted promotion: preserve type_id/since_rev and set the actual later definition revision/ordinal/document tuple. Do not reuse the legacy creation-revision FK as current source evidence. Distinguish original referring-source custody from an absent provisional definition source; future catalog-view provenance must not invent a definition. Document and accepted-binding source categories remain separate native layout mappings, with an exact binding-source home proposal authored and its native decoder/producer/adoption still open. STP-003's different-revision/ordinal controls are conditional on the unresolved upstream-valid representation.

Later definition updates provisional false and document provenance while retaining type_id/since_rev. Validate retained values, rebind eligible content and journal under the same acceptance transaction; incompatible retained content must follow the shared explicit loss/refusal/transform policy. Provisional objects have no authored key, so identity-based imports remain rejected by US-034. Persistent reports list unresolved placeholders in every accepted revision. Removal/retirement of references and placeholder orphan policy require explicit lifecycle semantics.

## Tests, Sequence and Rollback

STP-003 allocates four criteria. Resolve valid unresolved representation, qualified identity and placeholder lifecycle; write pure policy tests and gated native cases; implement atomic allocation/definition/rebind. Failure leaves no placeholder/relationship/report/head effects. Skip is explicitly requested loss, not successful full semantic support; rollback cannot restore skipped meaning unless source bytes were retained. All runtime components are planned.
