---
ddx:
  id: STP-014
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-014
      kind: informed_by
    - id: TD-014
      kind: informed_by
    - id: SD-003
      kind: informed_by
---

# STP-014: Cross-row enforcement honesty

## Story Reference

US-014, TD-014, SD-003, TP-001 and CONTRACT-004/007/009. Cases are planned, not passing evidence.

## Scope and Objective

Prove bounded minimum participation safety through the qualified engine path and honest guarantee reporting.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-014-AC1 | `two_removals_preserve_minimum` | Two competing removals commit at most one; final native participation is at least one and refused effects/journals are absent | `@covers US-014-AC1` | Native integration | `tests/mutations/cross-row.test.ts`; two clients, two lines, barriers/post-lock reads |
| US-014-AC2 | `trigger_alone_is_not_database_guarantee` | Deferred-trigger-only READ COMMITTED profile is not classified database-enforced; unverified/bypass limits remain explicit | `@covers US-014-AC2` | Contract | `tests/reports/enforcement.test.ts`; independently authored profile/evidence fixture |
| US-014-AC3 | `parent_lock_is_engine_classification` | Qualified parent-lock path reports engine enforcement, not unavoidable database enforcement | `@covers US-014-AC3` | Contract | Same file; exact rule/profile evidence identity |

## Executable Proof

Future commands `bun test tests/mutations/cross-row.test.ts` and `bun test tests/reports/enforcement.test.ts` require files/harness. Actual tests cite their criteria and pin server/adapter/isolation/role context. Native bypass supplements establish the declared boundary.

## Data and Setup

Use observed locks and post-lock native counts; sleeps alone do not establish overlap. Independent observer checks graph/journal and report separately. Add inverse/target-side minimum and group replacement fixtures. Role-restricted checks must demonstrate complete integrity counts without leaking hidden data.

## Edge Cases and Failure Modes

Direct SQL can violate an engine-only rule and must not invalidate an honestly scoped report. Snapshot isolation variants need separate concurrency evidence. A stale pre-lock count fixture should expose an incorrect implementation. Timeout/cancellation and group refusal leave no partial effects. Aggregate rules outside declared lock scope refuse support.

## Build Handoff

Create forced-race/report red cases, implement post-lock checks and classification, then qualify native bypass/visibility variants. All three criteria block bounded-profile closeout; general cross-row safety requires additional scoped designs and evidence.


K03/K04 reference schedules require full outgoing and incoming bound arbitration with distinct source parents. Independently inspect actual ordinary-role direct-DML/helper/derived-marker paths and the installed guard/privilege inventory. Missing shared target-side exclusion or an omitted canonical contribution must fail even if engine operations and derived-row uniqueness pass. Unknown native outcome is unresolved original work, not rollback evidence. No new lock hierarchy or fixture-only bypass is allowed.


## Parent-lock wait versus count snapshot (planned)

Start with one parent and two independently enumerated participating edges,
minimum one. Transaction A acquires the selected parent exclusion and stages
removal of edge a. Transaction B submits its lock acquisition while A remains
open. Independently observe B actually blocked before permitting A to commit.
After B confirms the lock, issue the complete participation observation as a
subsequent admitted native command. Its baseline contains only edge b;
removing b would violate the final-state minimum and must refuse with confirmed
local containment. Independently committed state remains one edge, with only
A's original version/journal effects.

Retain exact command submission/completion order and actual native lock/state
barriers. As a deliberately defective comparator, place lock acquisition and
ordinary participation collection in one statement whose snapshot began before
A committed. Demonstrate its stale count where the selected query permits
that schedule; it cannot qualify the engine path even though the parent lock
was ultimately acquired. A mock post-lock count or sleeps cannot establish
snapshot freshness. No production guarantee is inferred from a locking CTE or
sequential source lines inside a callable.

Repeat the supported post-lock schedule with target-side participation and a
valid remove/add final-state replacement. Separately retain an earlier fixed
snapshot under REPEATABLE READ: a new command alone does not refresh it. Apply
only the selected conflict/retry/refusal protocol; Truss cannot restart an
adopted transaction or silently change its isolation. These cases remain
`not_run`, consuming the original shared hierarchy without adding another lock
or bypass guarantee.
