---
ddx:
  id: STP-003
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-003
      kind: informed_by
    - id: TD-003
      kind: informed_by
    - id: SD-001
      kind: informed_by
---

# STP-003: Unknown endpoints

### Definition source pointer candidate

For future fully admitted endpoint-intent US-003-AC4 cases, create a provisional type in revision 1 and define it from a document archived in revision 3 at a different ordinal. Under CONTRACT-001's proposed independent definition-source profile, type_id and since_rev remain unchanged while the complete source tuple identifies revision 3's actual document/bytes. Include a revision-1 row at the same later ordinal with unrelated content: native FK existence must not falsely qualify it. Independently verify all-null provisional source, full defined source, partial-null rejection, wrong document ID and changed source bytes; failed promotion preserves original provisional state and graph/history atomically. These cases remain upstream-gated and planned, not evidence of currently valid unresolved UMF endpoints or installed pointer columns.

## Story Reference and Scope

US-003, TD-003, SD-001, TP-001 and CONTRACT-003. Native policy tests remain planned; the endpoint-intent representation is experimentally available, with full native/profile adoption still D-04-gated.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-003-AC1 | `default_reject_names_every_unknown_endpoint` | Valid unresolved input rejects with each qualified endpoint/relationship and no persisted effects | `@covers US-003-AC1` | Native integration | `tests/catalog/unknown.test.ts`; future fully admitted endpoint-intent representation |
| US-003-AC2 | `provisional_type_has_no_fields_and_stays_reported` | Stable provisional type/no properties or keys, derived relationship and repeated unresolved report entries | `@covers US-003-AC2` | Native integration | Same file; several relationships sharing exact unknown identity |
| US-003-AC3 | `skip_omits_whole_relationship_and_records_source_loss` | No partial relationship/endpoints persist; exact source-qualified loss appears | `@covers US-003-AC3` | Native integration | Same file; selected skip policy |
| US-003-AC4 | `authoritative_definition_preserves_provisional_identifier` | Later exact owning definition clears flag/provenance and preserves type_id/since_rev atomically | `@covers US-003-AC4` | Native integration | Same file; later pinned definition and retained data |

## Additional Probes and Evidence

Pure `tests/core/unknown-policy.test.ts` covers reject/provisional/skip classification on abstract validated identities. It cannot prove invalid UMF becomes acceptable. Test upstream-invalid local endpoint rejection before policy and prohibit synthetic stubs/name-based global lookup. Distinct document-qualified identities with equal presentation names must not collapse.

The validity-boundary regression matrix uses pinned real UMF fixtures for a missing source endpoint, missing target endpoint and missing endpoint key. Run each fixture under reject, provisional and skip; require the same reference-validator validity and diagnostics (severity, code, path), unchanged head and graph/catalog state, and no placeholder allocation. Include valid self-reference and valid mutual local-reference controls so a blanket cycle rejection cannot masquerade as correct validation. These cases establish the upstream boundary only; they cannot close AC2–AC4 or substitute for future valid unresolved-reference acceptance tests. A package lookup returning incomplete must not be treated as a resolved relationship or an empty valid definition.

Native expected state covers placeholders, endpoints, reports and retained/rebound data. Failed definition/transform undoes all effects. Keyless provisional imports reject; no accidental authored key inference. Orphan placeholder lifecycle and incompatible retained values require shared resolution before assertions.

## Executable Proof and Handoff

Future command `bun test tests/core/unknown-policy.test.ts tests/catalog/unknown.test.ts` requires actual files and valid upstream unresolved representation. All four criteria block closeout. Algorithm-only tests remain separate from gated acceptance evidence.


## Candidate-language versus native policy evidence

The full original UMF registry experiment has 17 controls; the original supplied-
source/Record/key/graph suite has 30 tests/609 assertions. These execute preparation,
not US-003's native policy criteria. Follow the representation handoff's E4 matrix
with independently encoded native expectations. Under reject, provisional and skip,
a missing required key on a known Record must not allocate a substitute provisional
type or become a key-free relationship. Wrong selected source, missing required
dependency and unsupported required modifiers likewise refuse before effects.

For valid pending type intent, compare complete reject diagnostics, whole-intent
skip/loss membership and actual provisional type/relationship cross-products.
Hold native target_key NULL fixed while changing only absent versus unresolved
interpretation; require full original profile/source correspondence to detect it.
An orphan retains original ID/objects and remains reported until an explicit
admitted lifecycle transition. Promotion preserves stable authored key IDs and
current security-owner admission. Fault after late endpoint allocation and at
commit acknowledgment; compare confirmed rollback separately from original
unknown-attempt recovery. None of these native schedules has passed yet.
