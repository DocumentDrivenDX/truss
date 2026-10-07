---
ddx:
  id: STP-035
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-035
      kind: informed_by
    - id: TD-035
      kind: informed_by
    - id: SD-002
      kind: informed_by
---

# STP-035: Import provenance

## Story Reference and Scope

US-035, TD-035, SD-002, TP-001 and CONTRACT-001/004/005/007. Tests are planned. Prove source fact preservation independently of journal initiator.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-035-AC1 | `source_lookup_returns_original_load_author_time` | Imported record returns load id, seed-author and exact source time while journal identifies a different operator | `@covers US-035-AC1` | Native integration | `tests/import/source.test.ts`; object and edge fixtures |
| US-035-AC2 | `missing_source_author_stays_absent` | Missing author remains absent despite operator/role origin; unknown source members survive the qualified carrier | `@covers US-035-AC2` | Native integration | Same file; absent author and extension content |
| US-035-AC3 | `edit_and_repeat_load_do_not_rewrite_provenance` | Later edit and skipped repeat leave source row/load id unchanged | `@covers US-035-AC3` | Native integration | Same file; independently captured source row |
| US-035-AC4 | `direct_create_has_no_source_row` | Direct-created visible record has no provenance and no synthesized source facts | `@covers US-035-AC4` | Native integration | Same file; direct create and authorized lookup |

## Data and Failure Probes

Historical source supplements: delete an imported object and an imported edge plus endpoints, then query with complete retained original owner/creation inventories. Current authorization for the full original owner union returns exact immutable facts; losing either endpoint-owner grant yields non-disclosing not_found before gap details. Recreate the same business keys with new storage IDs/source facts and verify original requests cannot return replacement provenance. Prove absent only from a complete qualified direct-create inventory; removing a required source/creation/definition artifact yields unavailable for an authorized caller. Empty query output is not absence evidence. Compare independently authored missing/null/opaque source values and original typed endpoint pins; source author strings never authenticate the caller.

Compare raw native rows with independent expected source facts; never derive expected author from journal origin. Test absence versus explicit null per CONTRACT-004, exact source time text and nested unknown values within D-05's qualified profile. Force source insertion failure and verify canonical/journal rollback; caller transaction rollback also removes pending source rows. Attempt ordinary writer update/delete and unauthorized module lookup. Resolve deleted-record visibility before asserting historical access.

## Executable Proof and Handoff

Future command `bun test tests/import/source.test.ts` requires implemented harness, lookup envelope and exact source schema. Pin server/adapter/role-policy versions and retain independent row/privilege evidence. All four criteria block closeout. Source assertions remain unverified claims even when storage fidelity passes.

## Source assertion envelope examples

Input `{at:"2026-08-14"}` returns source with exactly that member and no author/system. Input `{author:null,at:"2026-08-14T09:00:00-04:00",system:""}` retains null, authored offset and empty string. Eligible new input `{author:42}` rejects known-field type; a skipped live identity does not validate replacement source under import precedence. A visible direct record yields absent; an inaccessible identity yields not_found without provenance disclosure. Historical deleted-source authorization is specified by the retained original owner union above; native access remains unqualified until its complete loader, current-authority and source profile are selected and tested.

## Bound history facade supplements

Use the history facade for exact historical source ownership, separate from live-source lookup. Missing creation/source evidence cannot become absent; a new same-key record cannot supply old provenance. Hidden results carry no request/fact. Foreign/dead/read-only-without-qualified-authority handles refuse before disclosure. Disposal preserves host transaction/snapshot ownership and blocks new native work.


## Retention dependency controls

Under a separately selected administrative retention profile, independently construct a deleted source fact still needed by a reservation, historical edge endpoint-owner check, retained feed/history artifact and unresolved recovery respectively. Each blocks isolated deletion. Remove a required creation/owner artifact or omit a dependency from the collector; require unavailable eligibility rather than a successful empty closure. Recreate the same business key with new identity and verify it cannot satisfy original ownership or replace the cleanup root.

For a fully eligible cohort, independently compare complete before/after membership and retained evidence; source deletion must not erase its own eligibility/result archive. Race a newly retained dependency against cleanup and require original exclusion/revalidation to prevent partial deletion. Lose cleanup completion and require original recovery with no automatic new cohort. Exercise resource exhaustion before deletion and after submission separately, preserving the governing containment/unknown-outcome distinction. These cases remain planned; they adopt no retention duration or native cleanup implementation.


## Provenance cleanup race schedule PC01

Use two independent native sessions under the selected retention/dependency profile, plus a fresh qualified after-state observer. Preserve an independently authored deleted source identity S and exact original source/owner/creation bytes. Select a profile-admitted dependency producer P; its actual source and locks are fixture prerequisites, not a fabricated public method.

| Barrier | Cleanup session A | Dependency session B | Required observation |
| --- | --- | --- | --- |
| PC01-1 | Collect a provisional eligible cohort containing S; pause before final exclusions/revalidation and before DELETE | Idle | No graph/source deletion or public cleanup success yet |
| PC01-2 | Paused | Admit and create a retained dependency on original S through P, then obtain confirmed native commit | Independent observer confirms exact dependency and unchanged S; lost commit acknowledgment makes the case unresolved |
| PC01-3 | Acquire selected original exclusions in governing order and revalidate complete dependency closure | Idle after confirmed commit | S is no longer independently deletable; no source DELETE is submitted |
| PC01-4 | Finish refusal/containment under original executor ownership | Idle | Fresh full after-state equals baseline plus B's dependency; source/owner/creation bytes remain exact |

Repeat with P targeting a recreated same-key identity S2: the original S closure must distinguish those identities rather than treating the display key as a dependency root. The selected policy independently determines whether S remains eligible; it must never replace S's source facts with S2's. Repeat PC01-2 with unknown B completion; absence in A's observation cannot settle the original dependency attempt or authorize cleanup until the profile's original termination/exclusion proof is complete. A may wait or refuse under the selected deadline, preserving source evidence.

Native barriers must observe actual submission/termination and lock participation. Timed sleeps, host flags or a stale fixed snapshot cannot establish the schedule. PC01 remains not_run and does not select retention duration, SQL routines or a deployment.
