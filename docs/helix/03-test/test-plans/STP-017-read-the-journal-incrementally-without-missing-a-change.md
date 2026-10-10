---
ddx:
  id: STP-017
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-017
      kind: informed_by
    - id: TD-017
      kind: informed_by
    - id: SD-004
      kind: informed_by
---

# STP-017: Safe incremental journal reads

## Story Reference

US-017, TD-017, SD-004, TP-001 and CONTRACT-002/006/007. Tests are planned.

## Scope and Objective

Prove stable complete eligible-row ordering despite late commits. Downstream delivery/application and retention recovery are separate obligations.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-017-AC1 | `open_old_xid_withholds_new_commit` | B committed after A assigned older xid remains absent while A is open; observed safe boundary excludes it | `@covers US-017-AC1` | Native integration | `tests/journal/watermark.test.ts`; three clients and explicit barriers |
| US-017-AC2 | `late_commit_releases_ordered_rows` | After A commits, A/B rows return in exact xid/seq order without missing events or duplicated continuation | `@covers US-017-AC2` | Native integration | Same file; independently expected positions |
| US-017-AC3 | `ahead_position_waits_for_safe_boundary` | Position ahead of safe boundary yields no rows; subsequent reads return only eligible rows after boundary advances | `@covers US-017-AC3` | Native integration | Same file; controlled position/boundary fixture |

## Executable Proof

Future command `bun test tests/journal/watermark.test.ts` requires native harness/files. Actual tests cite criteria and pin server/isolation/feed profile. Missing native environments remain unverified.

## Data and Setup

Assert A/B xid assignment and commits directly, never infer from sleep order. Include multiple events in each transaction and exact high-valued positions. Independent observer compares committed rows to returned eligible subset and saved continuation. One qualified snapshot determines both boundary and selected rows.

## Edge Cases and Failure Modes

A rollback releases B without a phantom event. Long-running unrelated transaction may delay watermark. Same-xid page continuation preserves seq order; complete transaction batching follows CONTRACT-006. Role-filtered reads cannot claim global completeness. Retention gap, database restoration and position-version mismatch must receive explicit recovery/refusal policy before full feed support.

## Build Handoff

Write late-commit/rollback red tests, implement exact position and snapshot-bound query, then integrate complete-batch/retention contracts. All three criteria block closeout; sequence/time-based cursors must fail qualification.

## Local-to-archive continuation schedules (planned)

These supplement US-017-AC1/2 under CONTRACT-006's short/zero local-retention and original offload procedures, paired with STP-019 AH-01–06. All are `not_run`. Use independently authored complete transactions, their full original prerequisites and exact numeric positions; select the actual native retention, archive retrieval and reader profiles before execution. Archive admission for reconstruction alone does not establish support for journal or feed continuation.

| Case | Independent schedule | Required observation |
| --- | --- | --- |
| JR-A01 paused reader crosses local removal | Return the first page of a multi-member transaction, pause the reader, durably offload the complete original cohort, then attempt qualified local cleanup. Resume under the original reader context. | Outstanding consumer/reader protection prevents removal where required. If the selected continuation profile permits archive-backed resumption, return the exact remaining original positions and bytes once in that scan; otherwise report unavailable history without page/cursor advancement. Never silently switch a held snapshot's cut or infer a new cursor from the oldest surviving local row. |
| JR-A02 duplicate and incomplete sources | Retain both local and archived copies after cleanup failure; separately remove one required archived sibling or definition after local removal in a fault environment. | Complete duplicate copies do not duplicate logical rows. Conflicting originals refuse; missing required content cannot be repaired from current canonical rows, current definitions or the surviving copy's count/digest. No partial page or complete-transaction claim is published on refusal. |
| JR-A03 later local rows do not bridge a gap | Make a later transaction available locally while an earlier required archived transaction is unavailable, unauthorized or exceeds the original retrieval budget. | Visible later rows do not establish a gap-free scan, caught-up/reached proof or eligible acknowledgment. Withhold advancement over the missing transaction; classify availability and authorized diagnostics under the selected profile without leaking hidden event content. Restore qualified access and resume from the unchanged boundary. |
| JR-A04 cleanup uncertainty and restart | Lose the original cleanup COMMIT acknowledgment; restart the reader while provider durability remains separately confirmed. Exercise independently confirmed cleanup commit and rollback outcomes. | Resolve the original native maintenance attempt under its recovery protocol; archive success cannot classify native settlement. A fresh reader admits its own current source epoch, horizon, authority and exact retrieval profile. It cannot reuse a dead observation handle or replace unresolved original context with a fabricated successful continuation. |

Retain complete original source/page/archive bytes, native partition/horizon/protection observations and separate provider/native outcomes. Row continuation is not durable downstream application: complete feed membership, application, acknowledgment and reached-proof checks remain separate CONTRACT-006 obligations. Request receipts retain their independent lifetime and retry protection after journal removal. A mocked archive or shape-valid locator cannot pass these native/provider schedules.

## Journal facade supplements

Exercise exact epoch/profile/scope/snapshot context and exclusive numeric (xid,seq) cursors. Late older-transaction commit must not appear behind an admitted safe boundary. Split a multi-row version and prohibit reconstruction-completeness claims. Retention/authority gap refuses rather than skipping hidden rows; oversized event returns no partial page/advance. End is observation-local, not complete feed acknowledgment. Held snapshot replay must reject foreign/dead handles; statement continuation can later discover newly eligible rows. Disposal submits no SQL and preserves host snapshot lifetime.

### Metadata sibling and nonconsecutive position paging

Independently author a selected complete group with property positions 41 and 43 and metadata position 48 under one eligible producing xid. With one-row pages, require exact continuations 41, 43 and 48; the first two pages are valid row fragments and cannot advertise complete reconstruction or feed acknowledgment. A different producer's interleaved allocations do not require synthetic gap rows or cursor rewinds. Finish group membership through independently checked original count/digest, not final page size or consecutive arithmetic. Subject these conditional controls to the exact adopted producer profile and unresolved US-015 row-count reconciliation.

Include a later metadata sibling with unsupported required meaning: decoder refusal withholds that page and its advance; earlier transport receipt is not complete mutation proof. Native watermark/cut/current-authority and full feed membership remain separate qualification gates.

## Preallocated-position and out-of-order settlement schedules

Use independent writer connections and native barriers. Writer A obtains the earlier full xid and reserves original positions, then pauses before append/outer settlement. Writer B obtains a later xid, publishes and commits its complete group. Independently observe visible higher rows and the qualified safe watermark. Paging must not advance past A using MAX(seq), timestamp, B's commit or a pending/application-finalized stage. It may return no eligible rows; end is not permanent catch-up or feed acknowledgment.

Release A first with commit and separately with rollback. A fresh qualified observation after commit must retain original lower-xid group before B under numeric (xid,seq) ordering without omission or duplication. Rollback emits no placeholder event for consumed seq gaps and does not claim a missing committed record version. Verify complete original group membership independently of split row pages.

Keep a held observation open while A settles. Continue only under its original snapshot/watermark/context; changing cut behind the same cursor refuses. Start the separately qualified new observation and verify its own source epoch/horizon/current authority. Repeat with unavailable original watermark evidence, changed epoch, retained-definition gap and resource exhaustion; no partial cursor or visible-max fallback is admitted. These are planned native schedules, not source/schema support, and remain not_run until actual selected allocator/watermark/adapter/authority profiles exist.

## Split-page manifest current-authority controls

Independently author a complete original mutation group spanning distinct historical owners, then page one sibling under a caller authorized for only that sibling's live owner. Full count/digest/continuation/lookahead disclosure refuses without partial events/cursor or protected sibling-count/gap details. Grant the complete original retained union and require valid split row delivery, still without complete-group/application claim. Missing original membership/owner evidence or a filtered private observer remains unavailable; matching manifest count/hash cannot repair it.

Revoke a required original owner between pages while holding the same data snapshot. Fresh current-union admission must withhold later disclosure; prior-page authority and unchanged snapshot are not permits. Exhaust private unreturned-sibling/lookahead closure work despite a small delivered-row limit and require no partial cursor. Test historical old/new endpoint/definition owners and source ownership separately from current live ownership. All cases remain planned native controls under the selected original guard/coordinator/retention/event profile.

Manifest owner-admission tests independently distinguish same numeric entity ID across kinds/types/source epochs, separate versions in one producing xid and copied count/digest across foreign boundaries. Every attempted merge refuses original membership. Start a page cursor inside a group and retain protected siblings on both sides; complete authorization must include both original sides, not just the returned slice. Substitute an owner-union artifact omitting a historical endpoint/property/source owner and require refusal despite valid group digest and current live-record permission. All native profile/collector/coordinator schedules remain not_run.
