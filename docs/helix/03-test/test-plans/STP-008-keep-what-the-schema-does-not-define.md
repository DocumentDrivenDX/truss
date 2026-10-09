---
ddx:
  id: STP-008
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-008
      kind: informed_by
    - id: TD-008
      kind: informed_by
    - id: SD-002
      kind: informed_by
---

# STP-008: Keep what the schema does not define

## Story Reference

US-008, TD-008, SD-002 and TP-001; CONTRACT-001–004/007. Cases below are planned, not implemented.

## Scope and Objective

Prove unknown accepted content survives import and later definition without silent loss or coercion. Rejected records retain explicit source/error evidence and are not counted as successfully stored records.

## Acceptance Criteria Test Mapping

Existing-retained mutation probes: a new unknown name is retained; an exact identical repeated set is a no-op; different set and unset refuse with source path and preserve all prior state/version/journal. Lexically different equal numbers are not representation-identical. Combine a valid defined-property edit with a retained collision and require whole-operation/group rollback. Setting a newly defined same-name property cannot bypass an unresolved retained collision. Unrelated mutations continue reporting the surviving entry; skipped imports do not overwrite it.

Rebind collision vectors under CONTRACT-003: absent destination permits a valid candidate move; present null, equal value and unequal value destinations each refuse without merging homes. Ambiguous authored-name matching refuses without case folding or cross-owner lookup. Incompatible candidates preserve the retained source and old head; qualified transform candidates must validate final keys/invariants before persistence. Force journal/report failure after one attempted move and require rollback of every map/head/event effect. Independently compare exact source/destination presence, empty collections and historical definition contexts. Complete rebind event encoding and selected name-mapping profile remain prerequisites.

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-008-AC1 | `unknown_name_and_value_survive` | Native retained map has original authored name and exact recursive content; report names the retained entry | `@covers US-008-AC1` | Native integration | `tests/retained/native.test.ts`; Order with undeclared giftWrap and nested exact-value fixture |
| US-008-AC2 | `three_retained_values_rebind_atomically` | Defining revision moves three matching entries to their property home, yields exactly three rebind journal events and lists all three; unmatched content stays retained | `@covers US-008-AC2` | Native integration | Same file; three Orders plus one unmatched retained name |
| US-008-AC3 | `import_corpus_recovers_every_value` | Independent recovery from defined/retained homes matches all accepted source values; no missing name, presence or numeric content | `@covers US-008-AC3` | Native integration | Same file; committed corpus and independent expected recovery |

## Executable Proof

Planned command `bun test tests/retained/native.test.ts` requires the future native harness and test files. Actual tests carry criterion citations and run on every claimed adapter/server/value profile. No pass is inferred from source fixture counts alone.

## Data and Setup

Independent fixtures include nested unknown names, numeric values beyond host-double precision, explicit null, empty arrays/records, Unicode names and binary content. Observe maps, revision head, journal and reports separately. Expected recovery uses authored fixture bytes/meaning under the qualified profile, not production classification.

## Edge Cases and Failure Modes

The authored CONTRACT-003/004 candidate supplies refusal/no-op precedence for incompatible definitions, occupied destinations and retained mutation collisions. Consume that exact candidate interpretation rather than reopening an unspecified overwrite policy; original name/owner mapping, value/event/codec and native producer profiles still require admission before execution. In every refusal case, old head/maps/journal remain unchanged and source content survives. Fault after the first planned move must not commit partial rebinds. Restricted roles cannot enumerate hidden rows through retained reports. Unknown values matching nothing remain retained after revision.

## Build Handoff

Begin with retention/rebind red cases using the authored collision/no-op/incompatibility rules, admit the complete name/owner/value/event/native profile, then implement classification/planning/persistence. Block closeout on all three criteria and independent recovery/rollback observations. No claim of arbitrary lexical retention until D-05 is resolved.
