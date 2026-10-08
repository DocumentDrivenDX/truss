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

## Durable archive handoff and zero-retention schedules (planned)

AH-01–06 exercise the [reference handoff](../../02-design/contracts/reference-history-archive-handoff.proposal.md) in `tests/journal/archive-retention.test.ts`, citing `@covers US-019-AC4`; writer/admin isolation also consumes US-019-AC3. All cases are `not_run`. Seed complete independently authored history groups, original definitions/baselines, provider namespace and protected consumer/request-receipt dependencies. Provider and database observations have separate original attempt identities and outcomes.

| Case / test identifier | Independent fault or schedule | Required observation |
| --- | --- | --- |
| AH-01 / `verified_archive_precedes_zero_local_retention` | With zero eligible local retention configured, export a complete committed cut, store its exact bytes in the qualified provider, independently retrieve them, then invoke protected retention and confirm outer commit. | Complete recovery still matches independent original state/history/definitions without current rows. Only the admitted local inventory is removed; neighbor contents and every protected consumer/receipt dependency remain intact. No open Truss transaction spans provider submission/retrieval. Zero retention does not skip journal production or durable receipts. |
| AH-02 / `unknown_provider_write_never_authorizes_drop` | Drop upload acknowledgment after a possibly durable write. Retry/observe only the same original export; separately present changed bytes under that identity or a same-digest unequal-byte fixture. | No local removal or horizon advancement while durability is unresolved. Same-original retry returns its admitted observation without new history capture; changed identity/bytes conflicts or refuses. A matching route digest never replaces full-byte equality. Provider settlement cannot classify native transaction outcome. |
| AH-03 / `retrieval_must_be_complete_original_recovery_content` | Independently inject truncation, corruption, wrong namespace/credentials, stale profile, missing group sibling or missing historical definition during retrieval. Also supply only a successful upload callback, listing or local cache as evidence. | Cleanup refuses and original local protection/horizon remain intact. No partial reconstruction, synthetic event repair or complete archive claim. Current authorization is evaluated before protected disclosure; private missing-source diagnostics do not leak to unauthorized callers. |
| AH-04 / `fresh_protection_recheck_invalidates_prior_export_permit` | After provider verification, register a new protecting consumer/receipt dependency or change source epoch/required horizon before native drop admission. Separately expire provider authority/lifetime coverage. | Recollected complete protection/coverage refuses the stale drop intent. Earlier provider evidence is not a reusable permit. No grant/owner filtering can erase required dependencies. The independently retained before-state is unchanged after confirmed containment. |
| AH-05 / `archive_and_native_settlement_stay_independent` | With durable verified archive, fail after native horizon mutation/removal staging, or lose original COMMIT acknowledgment. Observe separate confirmed-commit and confirmed-rollback schedules. | Failure rolls back complete native retention effects; unused external artifact may remain. Unknown COMMIT retains original attempt/custody and prevents replay/readiness. Confirmed rollback preserves original horizon; confirmed commit admits only the independently verified new horizon/inventory. Physical termination or external success alone proves neither. |
| AH-06 / `provider_retry_and_admin_paths_preserve_original_bounds` | Exhaust retrieval/copy/deadline budget across individually small retries; attempt overwrite/delete through every selected provider admin path while an admitted horizon still depends on the artifact. | No budget reset or partial success; unresolved writes/retrieval retain original custody and local protection. Qualified immutability/lifetime prevents destructive changes, or that provider profile refuses qualification. Orphan cleanup cannot delete required recovery evidence. Mock orchestration results alone cannot certify the actual provider's durability/privilege guarantees. |

The assessor retains original archive and full dependency bytes, actual provider write/retrieval/lifetime/authority evidence, complete native pre/post partition/horizon/protection inventories and original settlement traces. Expected recovery content is authored independently of export/reducer implementations. Missing provider preparation is blocked, not passed via an in-memory substitute; native retention eligibility and provider qualification are assessed separately.

## S3 candidate qualification schedules (planned)

These supplement AH-01–06 for the [S3 candidate profile](../../02-design/contracts/reference-history-s3-profile.proposal.md). Use `tests/journal/archive-s3-profile.test.ts` with `@covers US-019-AC4`; privilege isolation also cites `@covers US-019-AC3`. All are `not_run`; a disposable, explicitly authorized actual provider environment and exact policy/SDK/resource profile are prerequisites. Mocks may exercise orchestration but cannot pass provider qualification.

| Case / test identifier | Independent setup and fault | Required observation |
| --- | --- | --- |
| S3-01 / `locked_version_survives_current_delete_marker` | Upload archive A with confirmed compliance retention and retain its version ID. An authorized fault principal adds a delete marker; a later conditional write produces distinct version B at the same key. | Recovery uses A's exact version and bytes. Current-key retrieval and B cannot replace A's original locator or satisfy its coverage. If version custody was lost, refuse cleanup. Observe actual marker/version inventory separately from the adapter. |
| S3-02 / `conditional_conflict_is_not_an_upload_receipt` | Lose A's successful upload acknowledgment; subsequent original-key conditional submission returns 412. Separately inject 409 and inaccessible/ambiguous version observations. | Only bounded independent full-byte and retention observation establishes the original version locator. HTTP status alone never advances local horizon. Changed content conflicts; unresolved lookup retains original custody and local protection without replacement keys or reset budgets. |
| S3-03 / `recovery_credentials_read_exact_original_version` | Upload credentials succeed while future recovery credentials lack version-read access; separately return another version, truncated content or a cache-only response. | Admission fails before native cleanup. After correcting the qualified identity, full original-version retrieval and archive/dependency interpretation pass independently. Provider checksum/HEAD success does not replace full content. |
| S3-04 / `retention_deadline_covers_every_discharged_obligation` | Choose retention shorter than an independently required consumer/receipt/reconstruction lifetime; separately allow a previously admitted deadline to expire before fresh retention admission. | Refuse cleanup and preserve local horizon. A finite deadline cannot discharge an unbounded obligation. Any proposed renewal protocol requires its own confirmed version-specific extension evidence before relying on the extended lifetime. |
| S3-05 / `privileged_mutation_and_encryption_paths_are_qualified` | Exercise every selected overwrite, version-delete, retention-change, lifecycle, policy-administration and encryption-key path with distinct qualified principals. | Required locked version remains protected for its admitted lifetime; current-key markers cannot conceal custody. Loss of retrieval authority/key availability refuses recoverability claims. If profile assumptions permit destruction of required bytes or keys, record that limitation and refuse qualification under stronger promised guarantees. No mock denial substitutes for actual policy behavior. |

Retain request/response and original uncertainty traces with secrets excluded, independent version/retention/policy observations, exact recovery bytes and native pre/post horizon inventories. The assessor must distinguish an unavailable setup, an expected refusal, a confirmed provider operation and a confirmed native commit. These schedules do not authorize provisioning, privileged mutations or deletion against existing deployment data.
