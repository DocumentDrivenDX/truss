---
ddx:
  id: STP-019
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-019
      kind: informed_by
    - id: TD-019
      kind: informed_by
    - id: SD-004
      kind: informed_by
---

# STP-019: Partition-only journal retention

## Story Reference

US-019, TD-019, SD-004, TP-001 and CONTRACT-002/006/008. Tests are planned.

## Scope and Objective

Prove partition routing, fail-closed audit writes, recognized-writer immutability and isolated eligible retention. No live application maintenance is authorized by this test plan.

## Acceptance Criteria Test Mapping

Retention arbitration probes under CONTRACT-006 pause between eligibility scan and drop, then race consumer registration/reset/removal and qualified acknowledgment. Require serialized revalidation so a newly protected boundary cannot be lost. Compare partition event positions rather than timestamp cutoff alone. Failure leaves inventory/horizon unchanged; success updates horizon atomically and preserves neighbors. Registration at an already trimmed boundary cannot promise replay. Recreating an empty dropped partition cannot certify restored history. Exact maintenance/profile APIs remain prerequisites for these planned native cases.

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-019-AC1 | `event_routes_to_exact_partition` | Actual native tableoid and range match expected partition at interior/boundary times | `@covers US-019-AC1` | Native integration | `tests/journal/retention.test.ts`; explicit month/timezone fixtures |
| US-019-AC2 | `missing_range_rolls_back_change` | Native check violation from uncovered journal time leaves canonical/derived/journal effects absent | `@covers US-019-AC2` | Native integration | Same file; disposable uncovered range |
| US-019-AC3 | `writer_cannot_edit_audit_rows` | Every qualified recognized writer cannot UPDATE/DELETE/TRUNCATE through parent or direct child; protection cannot be disabled | `@covers US-019-AC3` | Native integration | Same file; finalized writer/admin role matrix |
| US-019-AC4 | `eligible_drop_preserves_other_months` | Eligible old partition removed; neighbor row/content/catalog digests unchanged and retained horizon updated | `@covers US-019-AC4` | Native integration | Same file; disposable partitions and finalized eligibility profile |

## Executable Proof

Future command `bun test tests/journal/retention.test.ts` requires native harness/files. Every criterion cites its ID and pins server/layout/grant/timezone/retention profile. Recognized-role policy and mandatory append-only protection must be resolved before AC3 passes.

## Data and Setup

Use disposable databases and independent partition catalog/row observers. Verify no default partition. Compare neighboring content, not just counts. Journal failure occurs after canonical write inside the same transaction. Administrative test principal differs from ordinary writer.

## Edge Cases and Failure Modes

Overlapping ranges, exact month boundary, clock anomalies, direct child access, attempted detach/drop by writer and active transaction locks. Protected feed/history/request horizons refuse premature retention. Recreating an empty dropped partition does not recover history; restore tests need explicit archive/recovery policy.

## Build Handoff

Resolve role/protection/horizon conflicts, write red native tests, implement inventory/protection/planning and qualify disposable retention. All four criteria block closeout. Operational production procedures and destructive-action authorization are separate work.

## Retention public tooling supplements

Verify inert constructor with zero queries/timers/deletion. Reject arbitrary candidate relation/foreign installation/epoch, changed expected horizon and timestamp-only input before effects. Barrier a new registration/seed protection against eligibility observation and drop; lifecycle exclusion plus qualified current observation must preserve required dependencies. Repeat under held REPEATABLE READ: snapshot-old consumer absence cannot authorize drop after new protection commits. Either use the selected independent authority/protection observation protocol or refuse honestly without altering the host transaction. Inject failure between partition drop and horizon write and between later drops: confirmed operation rollback preserves all original objects/horizon and earlier host work; uncertain rollback remains recovery. Test exact complete catalog/configuration/receipt/history/seed dependencies independently, not journal position alone. Native profile and executable cases remain pending.

### Mutation groups spanning retained partition boundaries

Independently author one complete mutation with a property sibling in partition P and another property plus metadata witness in neighboring Q. Keep reconstruction of that version advertised. Propose removal of P while feed acknowledgments are already past both: removal still refuses without a qualified replacement baseline/definition/provenance closure. Observe that Q's unchanged rows/count/digest do not make the remaining partial group complete. Neither the metadata after image nor current canonical record can act as an implicit checkpoint.

Supply an explicitly qualified checkpoint at that version with independently retained original definition/owner/source and committed evidence. Under the selected administrative protocol, publish the restricted horizon and remove P atomically; requests before that checkpoint become unavailable and cannot inherit newer support. Interrupt or fault checkpoint admission, native drop and horizon publication; assert prescribed unchanged or original uncertain outcome, not a fabricated successful transition. New dependency discovery during administrative exclusion, missing sibling partition and exhausted closure budget refuse retention. These planned schedules do not authorize live retention or prove a checkpoint producer exists.
