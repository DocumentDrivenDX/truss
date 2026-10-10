---
ddx:
  id: STP-033
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-033
      kind: informed_by
    - id: TD-033
      kind: informed_by
    - id: SD-008
      kind: informed_by
---

# STP-033: Embedded PostgreSQL

## Story Reference and Scope

US-033, TD-033, SD-008, TP-001, CONTRACT-008 and SPIKE-003. Tests are planned. Qualify exact local instance and adapter profiles with the same bundle as the server.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-033-AC1 | `fresh_embedded_bundle_installs_and_checks` | Exact generated DDL installs and independent inventory/behavior check passes without separately provisioned server | `@covers US-033-AC1` | Native integration | `tests/host/embedded.test.ts`; owned fresh local instance |
| US-033-AC2 | `identical_bundle_has_same_semantic_objects_on_server` | Same bundle bytes produce equivalent complete required inventory on embedded and server targets; missing constraint/function is detected | `@covers US-033-AC2` | Native integration | Same file; external disposable test server and independent comparator |
| US-033-AC3 | `parallel_embedded_runs_remain_isolated` | Two concurrent instances have distinct state/paths; each excludes the other's sentinels and one teardown leaves the other usable | `@covers US-033-AC3` | Native integration | Same file; separate owned processes/data/socket directories |

## Data and Failure Probes

Pin server/runtime/platform/adapter, bundle hash and inventory manifest. Record versions even when embedded/production majors differ. Test startup and teardown failure, cancellation and concurrent repeated runs. Inject missing function/constraint and require comparator rejection; normalization must not hide drift. Observe owned process handles rather than assuming unique schema names imply independent instances. Run selected protocol corpus separately before broader feature support claims.

## Executable Proof and Build Handoff

Future command `bun test tests/host/embedded.test.ts` requires harness and files. Native receipts include full inventory differences, behavior outcomes and process lifecycle evidence. Missing target is unverified. Finalize distributions/targets and comparator before implementing; all three criteria block story closeout. No browser or managed-service qualification follows from local process evidence.
