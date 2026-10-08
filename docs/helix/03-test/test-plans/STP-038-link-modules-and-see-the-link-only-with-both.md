---
ddx:
  id: STP-038
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-038
      kind: informed_by
    - id: TD-038
      kind: informed_by
    - id: SD-008
      kind: informed_by
---

# STP-038: Cross-module edges

## Story Reference and Scope

US-038, TD-038, SD-008, TP-001 and CONTRACT-003/005/007. Tests are planned. Initial valid model has both modules in one owning UMF document; external-document semantics remain upstream-dependent.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-038-AC1 | `relationship_retains_billing_declaring_module` | Valid cross-module relationship accepts and rel_def ownership is billing with sales source type | `@covers US-038-AC1` | Native integration | `tests/host/cross-module-edges.test.ts`; pinned valid model |
| US-038-AC2 | `sales_only_role_cannot_observe_cross_module_edge` | Direct/list/inverse/id reads omit edge and expose no target through declared read paths | `@covers US-038-AC2` | Native integration | Same file; sales-only role |
| US-038-AC3 | `authorized_intersection_role_sees_edge` | Role reading relationship and both endpoints sees exactly expected edge/endpoints | `@covers US-038-AC3` | Native integration | Same file; dual-module and three-module fixtures |
| US-038-AC4 | `relationship_writer_without_source_read_cannot_create` | Native edge creation refuses with no edge/marker/journal/source effects | `@covers US-038-AC4` | Native integration | Same file; billing writer lacking sales read |

## Data and Additional Probes

Coordinator lifecycle vectors forge capture/lease markers, change data SET ROLE/connection between capture and disclosure, omit a required before/after owner and discover an additional scope after admission. Refuse without out-of-order lock growth or payload disclosure. Disconnect coordinator after private buffering; discard/withhold complete payload and preserve data transaction ownership. Unresolved release quarantines coordinator resources, never silently reuses the handle. Force catalog/policy/DDL cross-connection waits to establish the qualified wait matrix; a second connection is not itself deadlock proof. Streaming needs separate evidence.

Guard-adoption probes force catalog-versus-policy administration and request replay interleavings under the proposed order. Explicit READ ONLY RR keeps its original snapshot/access mode and requires the qualified authority coordinator, not a row lock on the data connection. Coordinator verifies the actual caller's complete historical owner context rather than its own elevated access. Coordinator loss/refusal cannot commit/rollback host data work or disclose staged payload. Wrong cross-connection lock order/unguarded privilege changes cannot qualify current authority.

Current-authority vectors start a held snapshot, commit a participating module-grant revocation elsewhere, then attempt live/historical/source/replay/staged disclosure. Require guarded new generation or retry/refusal, not stale application-grant rows. Force both read-before-revoke and revoke-before-read orderings. Long caller transactions may delay participating revocation under the proposed guard profile; no hidden commit is allowed. Uncontrolled native role/policy changes invalidate the installed authority qualification; a module_access-only counter is insufficient. SERIALIZABLE alone cannot close these probes.

Historical matrix: create an edge with three distinct owning modules, update a property, delete the edge and endpoints, then read its journal, tombstone, source and retained replay result. Remove each module grant independently; every required historical context must still be checked, with no relationship-only or live-row-join fallback. Regrant access and require the original exact payload when all retained contexts resolve. Include ownership/endpoint-context changes whose before/after union is unauthorized, missing retained provenance, retired catalog definitions and equal module names in different documents. An unauthorized feed consumer cannot advance its applied checkpoint past withheld required events. These planned cases require qualified historical provenance and do not certify the existing policy SQL.

Use separate declaring/source/target modules and independently expected visibility sets. Remove each grant in turn, test incoming/outgoing directions and self-module controls. Ordinary writer UPDATE that retargets a visible edge to hidden endpoints must not succeed. Definer read must retain caller intersection. Actual Weft queries are secondary integration evidence only after production backend registration; no synthetic compiler fixture substitutes for native policy behavior.

Invalid local references must match pinned UMF refusal; proposed external references remain explicitly unimplemented. Unknown-endpoint behavior is not a workaround for upstream-invalid input. Complete historical edge isolation requires shared journal/tombstone/source policy resolution and additional TD-037 tests.

## Recovery custody/disclosure supplements

Retain a cross-module edge obligation, revoke either endpoint grant and attempt diagnostic disclosure. Current relationship-only or original historical grants are insufficient: use retained relationship and both historical endpoint owners under current authority. Registry/admin inspection cannot bypass the union. Missing endpoint ownership remains unavailable even if a new record or rebound definition has the same business name.

## Executable Proof and Handoff

Future command `bun test tests/host/cross-module-edges.test.ts` requires implemented harness/catalog/policy bundle. Pin model bytes, validator, layout, policies, roles and native target. All four criteria block closeout. Preserve FK/unique side-channel limitations in the receipt.


## Complete independent effective-authority matrix

The [authority oracle](../cross-module-authority-expected.proposal.json) enumerates all eight relationship/source/target read intersections and both relationship-write states. Instantiate coherent cases under an independently pinned valid in-document model, with distinct declaring/source/target modules and original acting-role/current-policy evidence. Relationship writer authority includes relationship read; inconsistent write-true/read-false rows are admission-corruption controls and must refuse before execution. Do not invent a native grant arrangement to make those inconsistent rows appear valid.

Compare every declared direct/id/outgoing/incoming/compiled read path against the authored intersection, independently checking each endpoint's object-read visibility. A hidden edge does not revoke separately authorized source objects; it also cannot reveal an unauthorized target through traversal, counts or diagnostics. Creation additionally needs relationship write, with endpoint reads checked independently; endpoint write is not added as an unrequested requirement. Mutation refusal must retain complete independent canonical/marker/source/journal baseline and original containment evidence. This matrix supplements all four existing criteria, historical before/after owner unions and revocation schedules; it does not qualify cross-document UMF resolution or replace them.


## Entry and disclosure closure (planned)

PAC-02/04/06 from the [protected access composition](../../02-design/contracts/reference-protected-access-composition.proposal.md#native-closure-acceptance) supplement existing authority controls. Independently inspect direct/private/inherited/SET/owner paths and public error/result disclosure for every selected ordinary and administrative route. WCB-06 requires withholding compiled results if current authority changes after integrity checks. No private observer fact may become an absent public value or a disclosed count. All cases remain not_run; method inventories are design evidence, not effective native rights.
