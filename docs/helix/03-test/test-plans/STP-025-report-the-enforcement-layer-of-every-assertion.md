---
ddx:
  id: STP-025
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-025
      kind: informed_by
    - id: TD-025
      kind: informed_by
    - id: SD-006
      kind: informed_by
---

# STP-025: Evidence-qualified enforcement reports

## Story Reference

US-025, TD-025, SD-006, TP-001 and CONTRACT-001/003/004. Tests are planned.

## Scope and Objective

Prove complete assertion classification and native evidence for every advertised database guarantee.

## Acceptance Criteria Test Mapping

Additional qualification matrix under CONTRACT-004: enumerate actual ordinary-writer grants and test canonical DML, missing/forged derived keys and limit markers, direct derived-row DML, callable functions and engine writes independently. Tamper with trigger enablement, function body/search path, role grant and FORCE RLS inventory after a qualifying run; a current support check must refuse stale qualification while retaining the historical receipt unchanged. Run attacks as the actual writer, with independent administrative state observation; superuser success is an explicit exclusion rather than ordinary-role evidence. Missing inventory verification cannot produce database classification.

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-025-AC1 | `every_assertion_has_qualified_status` | Independent sales assertion inventory matches every rule identity/status with no omission | `@covers US-025-AC1` | Contract | `tests/reports/enforcement.test.ts`; authored matrix and profile |
| US-025-AC2 | `authored_key_cannot_be_bypassed` | Plain SQL duplicate key properties cannot evade database guarantee by omitting/forging derived rows; report matches proved scope | `@covers US-025-AC2` | Native integration | `tests/enforcement/bypass.test.ts`; finalized unavoidable guard/role contract |
| US-025-AC3 | `engine_only_never_becomes_database` | Engine rule stays engine classification even with a declared but unqualified trigger | `@covers US-025-AC3` | Contract | `tests/reports/enforcement.test.ts`; independent path/evidence fixtures |
| US-025-AC4 | `opaque_text_is_retained_and_none` | Opaque rule remains recoverable with stable source identity and none status | `@covers US-025-AC4` | Contract | Same file; unknown text assertion fixture |

## Executable Proof

Future commands `bun test tests/reports/enforcement.test.ts` and `bun test tests/enforcement/bypass.test.ts` require harness/files. Every criterion cites its ID; native evidence pins actual versions, roles, guards and layout. AC2 remains blocked under current engine-only key derivation.

## Data and Setup

Source-kind inventory controls contain both a portable UMF Key and a Truss sparse/timestamp storage binding with equal display text/IDs. They remain distinct assertions with exact accepted source artifacts/pointers. Missing or forged sourceKind/definition resolution refuses report admission; a Truss binding cannot claim source-authored UMF portable identity. Database classification for the selected large-key profile requires actual bucket generation/derivation guards and every advertised writer path, not merely a digest index or successful engine precheck. Removing a guard makes current qualification unavailable while historical reports remain immutable.

Pin current UMF interpretation separately from Truss enforcement evidence. DDD invariant expression fixtures remain none/opaque despite valid structural references; unknown facet members/units retain source without borrowing known facet enforcement. An arbitrary extension member named constraint cannot execute code or gain engine/database status. Known key/facet ideals need independent supported semantic extraction and Truss validator/native proof; UMF validation success alone is insufficient.

Include opaque unnamed assertions and equal rule text at two source pointers: both retain distinct source identities and original bytes, with none status. Display rule names cannot merge them. Authored IDs and profile-derived source identities are distinct variants; a new revision cannot imply continuity for an unnamed rule. A restricted projection is labeled explicitly and cannot disclose hidden global rule counts or satisfy complete inventory qualification.

Expected assertion list/classification is independent of production extractor. Include missing/stale evidence, mismatched server/role/mode and unsupported assertion meaning. Bypass attacks operate as qualified ordinary writer, with independent canonical/derived state observations. Owner powers are separately scoped.

## Edge Cases and Failure Modes

Unknown selected semantics cannot disappear from report. Guard/grant changes invalidate claim eligibility. Duplicate object props without marker expose false key guarantees. Report cannot equate successful sequential validation with concurrent/bypass safety. Version-dependent outcomes remain separately qualified.

## Build Handoff

Installed-policy inventory probes enumerate PUBLIC/inherited/SET ROLE paths, column grants, partitions, overloaded routine identities, definer owners/configuration and body changes, disabled triggers, policy composition and sequence rights. Empty/missing dependent surfaces cannot pass against an independently selected guard closure. Interleave an administrative role/policy change during capture; without qualified serialization require unstable_observation rather than a match assembled from incompatible observations. Native tests establish actual writer/observer identities separately. Same SQL file with changed installed grants must invalidate current database classification while preserving the historical receipt.

Resolve key/report contract gaps, write red inventory/bypass tests, implement classification and receipt matching, then qualify installed guarantees. All four criteria block closeout; evidence-free capabilities never count as enforcement.
