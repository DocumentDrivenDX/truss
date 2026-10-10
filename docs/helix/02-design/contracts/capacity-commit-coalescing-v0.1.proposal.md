# Capacity commit-check coalescing candidate

This Truss-owned invocation design refines the [installation plan](../../04-build/local-runtime-installation-migration-plan.md), CONTRACT-001 retained custody and [CONTRACT-009](CONTRACT-009-group-planning-and-locks.md) original account/exclusion requirements. It does not change UMF meaning, Weft compilation, authorization ownership or the seven mandatory semantic bodies. The [explicit capacity closeout](../../../../packages/postgresql/native/capacity-reservation/commit-check.sql) remains a component; this protocol has not been installed.

## Decision and counterexample

Reject a host Boolean or native “already checked once” flag as a commit-check cache. PostgreSQL permits a host to force deferred checks with `SET CONSTRAINTS ... IMMEDIATE`, return to deferred mode, and write again. A cached first success cannot cover the later state. Selecting only a first/last operation or highest ordinal also cannot substitute for complete retained membership and semantic cohorts.

Use a candidate transaction-native dirty-generation/proof-generation cache for **capacity parity only**, with original transaction/profile custody. Every original relevant inventory/reservation change invalidates the capacity proof before effects can escape containment. The first queued callback observing a dirty generation verifies the complete current inventory/release/closeout and records that generation only after success. Further callbacks may skip the full scan only while the exact original proof remains current. Later writes, including after early forced checks, create a different dirty generation and require another complete scan.

This is an invocation optimization, not new execution authority. The cache cannot stand in for definitions, effects, touch generations, journal/feed/contributions, current subject/security or the seven semantic guards. Security-owner freshness and publication cuts remain independently required.

## State and transitions

The logical memo contains original native transaction epoch, dirty generation, last successfully verified generation and exact registered layout/resource/invocation profile custody. Concrete fields/table/DDL placement and original identity/role/dependency inventory remain an implementation spike, not an adopted layout extension. No GUC, caller-selected token, temporary table by name, shared host Boolean or copied response can provide that original memo.

- Begin: bind one actual native transaction and immutable installed capacity profile; initially no cached proof.
- Operation entry: after original registered constraint/name/profile recognition and confirmed containment, reassert only Truss-owned deferrable commit constraints before capacity or lower-lock effects. Do not change host-owned constraint modes. Early forced checks require this reassertion on a later operation.
- Relevant native event: increment a nonreusable generation within that original transaction before recording the complete inventory/reservation change. Include inserts, updates that keep the same framed size, phase/result changes, release, and eventual admitted cleanup; numeric counter equality is insufficient invalidation.
- Deferred callback: validate original memo/profile correspondence and work/control admission. If dirty differs from verified, run the complete original capacity closeout under head/ledger custody. Record verified=dirty only after success. Cache writes must not themselves count as inventory invalidation or create an endless callback loop.
- Early forced callback: follow the same transition. Do not terminalize the transaction or suppress future invalidation.
- Confirmed savepoint rollback: native inventory and memo return to their same original snapshot. Cumulative original host/native work and issued ordinals do not refund or rewind. A database `scans` fixture counter is not that cumulative account.
- Generation exhaustion, missing/foreign memo, unregistered invocation/profile, unknown completion or budget exhaustion: refuse/quarantine under existing containment; no reset/recycling, scan skipping, automatic replay or counter repair.
- Commit: the unavoidable original native schedule must cover the final surviving dirty generation and every required semantic cohort. An explicit successful function call alone is insufficient.

## Formal specification — precise slice

Assurance is a precise conditional specification with scoped native scheduling experiments, **not** a deductive proof or exhaustive model analysis. State is `(epoch, profile, dirty, verified, inventory, reservation, work, health)` plus the original deferred event queue. Generations are finite monotonic integers in an original epoch; the implementation must freeze bounds and preflight increment exhaustion. Each successful capacity check must observe the complete native inventory and a released reservation under original exclusion. Safety does not assume eventual commit. No liveness/fairness claim is made; native scheduling, finite budgets and confirmed containment are explicit environmental requirements.

| Property | Governing requirement | Law and evidence obligation |
| --- | --- | --- |
| CC-01 | CONTRACT-001 complete retained parity; CONTRACT-009 original state | A cached proof covers only the exact original epoch/profile and dirty generation it checked. A later relevant write cannot commit using that earlier proof. |
| CC-02 | CONTRACT-009 complete effects and native exclusion | Every relevant original mutation invalidates even if aggregate rows/bytes remain equal. Qualify the full producer/trigger/dependency inventory; this fixture does not prove completeness. |
| CC-03 | CONTRACT-001 complete membership | A noncached scan enumerates every retained operation/touch member and validates complete release/closeout. Coalescing does not use an ordinal/subset as the authority set. |
| CC-04 | CONTRACT-009 native rollback and original account | Confirmed rollback restores inventory and proof state together; cumulative work remains spent. Unknown rollback grants no reusable proof. |
| CC-05 | CONTRACT-009 bounded original work | Repeated callbacks with unchanged original state may avoid redundant scans, but callback, comparison, copy, generation and scan work all remain charged. Generation/queue exhaustion refuses. |
| CC-06 | CONTRACT-009 complete native termination; installer inventory | Final surviving dirty state must reach an unavoidable registered callback before commit. Early `SET CONSTRAINTS` does not disable later checks. Operation entry defers only original Truss-owned named constraints before effects. Complete seven-body semantic checks remain independent. |

## Native experiment and test path

[The PostgreSQL16.15 scheduling receipt](../../04-build/evidence/design-audit/capacity-coalescing-native.json) passes12 observations in separate synthetic schemas. An intentionally broken first-only cache commits a negative fixture value after an early successful check. A generation cache instead refuses at actual COMMIT, with native inventory/memo rollback. Positive controls commit an early-check/later-valid-write schedule with two scans, coalesce three deferred writes into one additional full scan, and restore a failed forced-check child before checking its surviving follow-up.

Reproduction uses the pinned corrected pgserver environment and the existing pg8000 dependency directory:

```sh
/private/tmp/truss-pgserver-corrected-test-env/bin/python -c 'import sys,runpy; sys.path.append("/private/tmp/truss-pg8000-runtime-env/lib/python3.11/site-packages"); sys.path.insert(0,"docs/helix/04-build/evidence/design-audit"); sys.argv=["check_capacity_coalescing_native.py","fresh-coalescing-receipt.json"]; runpy.run_module("check_capacity_coalescing_native",run_name="__main__")'
```

Use a fresh receipt basename. These are actual deferred PostgreSQL events, but the fixture's inventory predicate, memo and scan counter are not original Truss bodies, original resource accounts or a faithful full-engine model. The counterexample establishes that first-only caching is unsafe under this supported native schedule; positive traces establish only their fixture behavior. Native Truss correspondence remains unreviewed.

Before adoption, implement and independently verify original native memo storage/field ownership and profile conversion through UMF, exact callable/trigger registration, complete invalidation (including same-size changes), forced-check/later-write schedules, deletion/reinsertion, actual ordinal gaps, child/ancestor rollback, generation overflow, queue/work exhaustion, concurrent original writers, cancellation/unknown containment and final commit settlement. Replay with the real capacity observer/inventory/closeout functions, actual ordinary-role effects and all seven semantic bodies. Show bounded total scans/callback work against the declared65536-row/512MiB resource profile. No release, installer readiness or acceptance promotion follows from this candidate.

## Original accounting constraint-mode correspondence — 2026-10-10

[The14-observation PostgreSQL16.15 probe](../../04-build/evidence/design-audit/capacity-constraint-modes-native.json) composes the unchanged original reserve/admission/event/sizing/inventory/closeout functions with a separate synthetic deferred callback. Finalized/released A passes an early forced named check. Leaving that callback immediate makes B's actual native reservation UPDATE invoke closeout while the reservation is active;55000 refuses and native containment preserves A. The failed attempt consumes fixture ordinal1. Deferring only the Truss-named constraint before B at2 permits full reservation/admission/finalization/release, then forced check and actual COMMIT. A distinct connection sees both original finalized rows and retained totals. A host-owned constraint remains immediate and independently refuses its invalid update.

The callback runs four complete scans per operation in this small probe. This verifies native mode interaction, not the generation cache, bounded callback work, original constraint registration or all seven guards. Its marker/profile values and phase transitions remain administrative. The original native source files are pinned; the probe callback and host table are test-only definitions, not additions to Truss's UMF layout or accepted installer inventory.

Operation entry must reassert only the original registered Truss-owned commit constraints after the recognized operation boundary and before reservation/effects. The installer must prove exact pg_constraint/trigger identities, qualified names and complete ownership/namespace closure; PostgreSQL name-based SET CONSTRAINTS is not an OID-based authority check, and a name collision must refuse rather than affect another constraint. Never issue SET CONSTRAINTS ALL DEFERRED. Record this ownership in the connection/native invocation profile: Truss owns its engine commit-constraint scheduling for the enclosing transaction; host-owned modes remain host-owned. No guessed prior-mode restoration, broad session rewrite, disabling a guard or internal retry fixes the issue. Native original control/account admission and unknown-mode containment must cover this additional command.

Same-size mutations and early forcing still require dirty-generation invalidation; deferral alone is not coalescing or final proof. Qualify ordinary-role entry, nested operation rollback, early/later checks, owned-name collisions, unexpected DDL/trigger modes, control completion uncertainty, callbacks with dirty/released versus dirty/active state and bounded complete scan counts before adoption. Actual cache storage and unavoidable registered commit invocation remain unimplemented.
