---
ddx:
  id: PLAN-HOHFELD-FOLLOWUP-20261021
  type: implementation-plan
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.prd
      kind: informed_by
    - id: PLAN-EMBEDDER-E2-E8-001
      kind: informed_by
    - id: PLAN-RUNTIME-MIGRATIONS-001
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-005
      kind: informed_by
    - id: CONTRACT-006
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
    - id: TP-001
      kind: informed_by
---

# Hohfeld follow-up dispositions and execution order

The [pushback response](hohfeld-pushbacks-20261021.md) states the semantic and
evidence boundaries to preserve during the next release.

## Scope

The original request snapshot compares the four supplied Hohfeld documents with
Truss 0.0.45 and Weft 0.4.49 as observed on 2026-10-21. Execution starts from
released Truss 0.0.47 at `6c9365c8be60b55602fe4e7bd4e45b4b5040ec74` and main
`da677e40660b90bcd8f2a6309d40bd2ae90abaf0`; the historical source document hashes
are retained below. The active consumer is now Arras, as recorded in the current
source-custody amendment. Reproduce disputes using the verified public wheel, not historical
adapter wording.
This is the follow-up queue for requests left after the
[embedder delivery](embedder-e2-e8-plan.md) and
[performance delivery](evidence/hohfeld-performance-20261021/README.md).
It does not reopen their completed scope or replace the
[runtime migration plan](runtime-migration-restoration-plan.md).

Governing requirements: [PRD](../01-frame/prd.md) FR-8/11/16–29/36–55 and
RES-01–06; contracts linked above; [test plan](../03-test/test-plan.md).
The installed HELIX 0.18.0 `workflows/` catalog supplies the implementation-plan
shape. This is engineering sequencing, not a dated iteration commitment.

Disposition vocabulary: **delivered** means scoped released evidence exists;
**in flight** names an actual active chat; **verify** means source/consumer
evidence conflicts; **accept** is proposed follow-up work; **push back** retains
selected semantics; **defer** requires separately selected scope. Proposed
changes below must enter their governing contracts/tests before implementation.

## Existing chats and overlap — original planning snapshot

| Chat inspected | Actual state and consequence |
| --- | --- |
| Assess Truss and Weft performance (`01a15f67-aee4-7241-926e-205667eeeb4d`) | Archived/completed. Released Truss 0.0.45 and Weft 0.4.49, with caching, combined reads, eligible set-based import and names diagnostics. Its final handoff predates Hohfeld's latest combined-API measurements. Do not repeat the instruction to adopt an API Hohfeld now uses. |
| Plan truss embedder asks (`01a15a71-3d81-7f93-8bd5-9ce9a12758ee`) | Archived/completed. 0.0.44 delivery covers batching, conditional catalog, document CAS, registrar/person status, preview, combined preparation, audit and install/grant outcomes. Remaining query/replay limits were explicitly excluded. |
| Find Truss schema migrations (`01a16023-fabd-7fa3-9abf-44d42e7fd673`) | **Active implementation.** Owner explicitly requested restoration. Latest commentary reports both source cohorts passing 14 native cases and an expanded 30-check suite; source/target recipes, old-wheel refusal, populated preservation, rollback, contention, lost COMMIT response and release gates are being implemented. These are chat-reported progress, not independently certified publication. R21.4 belongs here. |
| Explain UMF schema migrations (`01a1605c-de92-72c0-afcd-0498b7422c1c`) | **Active upstream design review.** Physical-table migration compiler/runtime, with tracked conversion/recovery gaps and remaining blockers. Relevant expertise for R16.5, but not Truss generic-layout catalog evolution; do not claim it implements that ask. |
| Plan Rust-based UMF packages (`01a16073-ec34-78b0-8795-b6abd1c7f058`) | Plan completed; implementation not started. Shared Rust/Python/Node/browser work is upstream direction, not delivered removal of Truss's embedded V8. It need not block this queue. |
| Truss Impl (`01a10c68-3279-7310-9e05-1b216e469b79`) | Archived; latest turns concern protected action installation/control, binary reads and compiler qualification. Not an active owner for the remaining Hohfeld query/replay asks. |

No inspected active chat owns the new query-profile, identity-only replay or
residual import-scaling work. A file modification alone is not proof of an
active assignment. No chat was messaged or new chat created in this review.

The working Truss checkout has concurrent migration edits. This review creates
only this file; it does not modify those edits. The migration chat also identifies
v0.0.46 launcher-isolation fixes beyond this checkout's 0.0.45 base. Resolve the
exact target cohort there; do not mistake a shared native label for equal bytes.

## Requirement dispositions

### R1–R15: baseline outcomes

| Request | Disposition and next action |
| --- | --- |
| R1 Python embedding | Delivered. Preserve public Python 3.11 adoption path. |
| R2 shared corpus/runner | Partial. Host corpus 13 reports 63 passes, nine declared limits, seven replica exclusions. Publish the independently expected Python/native corpus and runner with release/profile manifest; TypeScript interchange remains explicitly deferred under current FR-38. Host-specific corpus expectations do not override Truss decisions. |
| R3 installable layout | Fresh installation and the scoped runtime upgrade are delivered in v0.0.47 under R21.4. Candidate naming alone is not an acceptance failure. Pin actual manifest and installed inventory. |
| R4 person isolation | Delivered for the selected local tuple. Keep revocation/current-membership regressions; managed Lakebase security is a separate gate. |
| R5 origin | Delivered: native person and asserted origin remain separate. |
| R6 dry run | Delivered apply-and-rollback path; accept completion-check qualification under R18.14. Preview alone is insufficient. |
| R7 receipt/reached | Partial; see receipt decisions below. Keep pending token, no-op replay, rollback and retention evidence separate from replica-applied progress. |
| R8 interactive reads | Partial. Direct key reads exist; accept selective compiled reads and explicit query-profile work under R17. Verify endpoint lookup/ambiguity behavior before adding another API. |
| R9 exact values | Delivered for selected scalar subset. Broader structured values are separate work; do not round timestamps or coerce exact values through floats. |
| R10 distribution | GitHub wheels/sdist/checksums delivered. Defer a coordinated package-index release until Truss/Weft/platform dependencies, names and publication gates are selected; no date is established. Vendored digest-pinned wheels remain viable. |
| R11 preconditions | Delivered five predicates on locked prestate, ordered disclosure-safe failures. Preserve concurrency and failed-condition precedence. |
| R12 transaction ownership | Delivered exact psycopg adoption; host owns pool and outer settlement. Do not restore older prose claiming no public adoption factory. |
| R13 typed refusals | **Verify then fix** no-membership calls across preparation/context/reference, read, group and import surfaces. Historical 0.0.1 evidence does not establish a 0.0.45 defect. Never map every 42501 to business denial and hide damaged installation privileges. |
| R14 reader catalog/source | Delivered with complete document-read authorization and exact original bytes. |
| R15 evolution/scalars | Delivered bounded compatible evolution and scalar families. R16.5 owns the required-field gap; arbitrary extension edits, retirement, rekeying and structured changes remain separate scoped changes. |

R7: accept clearer unavailable reasons when disclosure-safe, but **push back on
classifying every absent receipt row as an invalid token**. Another transaction's
uncommitted receipt, a rollback and an invented identity can be indistinguishable
to the supplied snapshot. Prove issuance independently before promising that
distinction; retain `not_yet` for the published pending/rolled-back lifecycle.
Separate authorization from timeout/integrity when safely knowable, without an
existence oracle. A source ACK remains caller-asserted progress, not independent
proof of Ashlar commit. A stronger applied-position protocol needs a separately
qualified downstream transaction/deduplication boundary. Do not compare opaque
positions lexically or turn the read frontier into a timestamp. Confirm the
requested 24-hour replay protection with the actual retention policy and tests;
do not infer it from journal retention alone.

### R16: registration

| Item | Disposition and acceptance |
| --- | --- |
| R16.1 document CAS | Delivered. Keep unrelated-document/stale-document/absent-zero/exact-replay controls. |
| R16.2 registrar probe | Delivered, advisory; acceptance reauthorizes. |
| R16.3 module revisions/conditional catalog | Delivered. Validator is an observation, not authority. |
| R16.4 unsupported input | Names refusal delivered with all `TRUSS-NAME-MISSING` diagnostics. **Verify** nonselected decimals and structured values on 0.0.45; accept typed preparation/catalog errors where they still collapse into `invalid_transaction`. No automatic numeric coercion or inferred names. |
| R16.5 paired required DDD field | **Accept bounded design**: under acceptance exclusion, allow a known paired core/DDD required scalar addition when the affected Record has no instances and dependencies remain valid; otherwise return a typed incompatible/unsupported outcome with authorized evidence. Test empty/nonempty and racing writer cases. Existing optional addition is delivered. Do not ignore arbitrary extension changes. Existing-record defaults/backfill require a later explicit conversion plan. |
| R16.6 head zero | Delivered for enrolled reader/writer/auditor via person status. R22 owns nonmember disclosure. |
| R16.7 in-process preparation | Delivered embedded V8, no deployment Bun/Node. Upstream Rust plan is not a prerequisite. |
| R16.8 evidence size | Delivered for measured 13–89 KB documents, evidence 706–2,341 bytes, 0.36–0.42 s. Add the unrun 500-KB boundary and one-over resource controls before claiming that capacity. |

### R17: query surface (Truss composition; Weft compilation)

| Item | Disposition and acceptance |
| --- | --- |
| R17.1 column descriptors | Accept compiler-owned family/nullability metadata carried through Truss, including empty/all-null results, aliases, computed values and aggregates. No value sampling or second SQL parser. |
| R17.2 facts/relationship projection | Accept a versioned profile allowing selectable facts, facts with paging and explicit relationship projection. Preserve current `complete-entity` shape. Duplicate output aliases should continue to refuse. Do not silently truncate a supposedly complete entity: bounded relationship pages or an explicitly partial result with continuation need a new contract. Keep 100-key cap until replaced with evidence. |
| R17.3 syntax vs unsupported | Accept distinct compiler diagnostic codes. Test malformed SQL and well-formed excluded syntax without parsing messages. |
| R17.4 unknown vs other module | Accept useful diagnostic categories where safe. Push back on revealing an unauthorized type/module's existence; unavailable/hidden source can intentionally share a code. Column diagnostics may be more specific within an authorized source. |
| R17.5 10,000 source cap | Accept indexed key/equality/keyset source selection with defined work budgets. First diagnose plans and source materialization; raising the ceiling alone increases work. Keep ABI 1.1 pre-predicate cap until a new bounded compiler/runtime contract and native plans pass. Include 10,001+ populations, selective keys, absent keys and sparse pages. |
| R17.6 position comparison | Defer a general comparator until a partial-order/coverage contract is selected. Offer receipt inclusion for its documented scope; no string/time ordering and no fabricated staleness duration. |
| R17.7 facts plus continuation | Accept with R17.2/5; one bounded page carrying facts must replace N singleton reads. Test stable continuation, exact key types, deleted rows, concurrent changes and cross-person cursor misuse. |
| R17.8 entity cost | First optimization delivered. Latest host still measures singleton p95 30–39 ms versus 20-ms target. Keep performance goal open under the second pass below. |

### R18: groups

| Item | Disposition and acceptance |
| --- | --- |
| R18.1 failure code field | **Already delivered**: released `GroupOperationFailure.operation_code`. Correct adapter mapping/docs; add a regression only for a concrete mismatch. `InvalidGroupInput` diagnostics remain a separate carrier. |
| R18.2 nonmember | Same verification/fix as R13; preserve installation-error distinction and no data disclosure. |
| R18.3 replay independent of current state | Accept a receipt recovery/probe design bound to original request identity and full canonical input digest, authorized against retained owner context. Freeze original request before state resolution. Keep ADR-005 unequal-input conflict. **Decline implicit cross-person replay**: another person is a distinct scope unless an explicit authorized shared namespace is designed. Test delete/unlink/later deletion/no-op/lost ACK/revocation/expiry and changed-input conflict. Four host cases must be split into supported recovery and incompatible scope expectations. |
| R18.4 incident-edge delete | Adopted restrictive delete and explicitly selected owned cascade. Decline unconditional cascade or disclosure of hidden dependencies. |
| R18.5 version rule | Document existing per-changing-operation increment and no-op preservation. Do not change to one increment per group without a separate history/concurrency contract. |
| R18.6 group id | Accept stable retained group-attempt identity in result/replay, distinct from XID and receipt position. First reconcile existing audit identity; do not mint another group identity. Test two groups in one outer transaction. |
| R18.7 names/keys | **Push back** on blanket unknown-property rejection: PRD FR-11 requires retention/reporting. Fix any loss. Enforce authored key facets and selected resource limits; do not invent a universal ban on empty/long keys. Test key updates against declared mutability and reservation semantics. A host may select a stricter declared profile. |
| R18.8 numeric/time equality | Document exact-token behavior and preserve originals. Defer value-equivalence comparisons to an explicit UMF-owned/profiled rule; no silent decimal/timestamp normalization. |
| R18.9 retired keys | Document that reserved is not absent. Accept typed live/reserved/unavailable distinction only where authorized; do not make a tombstone existence oracle. |
| R18.10 cost/capacity | Guard and 1,024 operations/3,072 conditions delivered; latest end-to-end latency remains open. Keep independent byte/deadline limits. |
| R18.11 rollback read basis | Accept a non-durable validation observation basis, distinct from receipt/committed position. Preview's basis covers conditions only; full dry run must still evaluate effects and completion checks. |
| R18.12 missing endpoints/count predicates | Document current missing-endpoint refusal/failure; do not make an invalid endpoint pass `RelationshipAbsent`. Defer disjoint/not-equal count predicates until selected; represent multiple admitted conditions where possible. |
| R18.13 lookup locks | Document lock lifetime, NOWAIT/busy behavior and retry rule. A nonlocking read is advisory and cannot replace apply-time version/lock checks. Verify actual per-call lock modes on the selected release. |
| R18.14 deferred completion | Accept a typed completion/validation operation with correct savepoint containment and caller ownership. Test actual deferred failure before dry-run rollback, preservation of prior caller work and outer COMMIT failure. Do not force unrelated host constraints globally without a declared scope. Preserve native SQLSTATE and uncertain termination. |
| R18.15 condition timing | Document locked-prestate semantics. Decline silently changing to sequential conditions; aliases/ordered operations and preconditions have distinct roles. A sequential action evaluator would require a new profile. |
| R18.16 multiplicity attribution | Accept distinct final-state graph/multiplicity diagnostics. Name offending entity/rule where authorized; final-state failures may have multiple causes, so retain an absent operation index instead of blaming the last delete. Remove adapter inference from operation kind. |
| R18.17 condition IDs | Document group-wide uniqueness. Keep adapter renaming as explicit reversible mapping; per-operation scope would need a new carrier/profile. |
| R18.18 precedence | Delivered; keep mixed failed-condition/failed-operation regression. |
| R18.19 conflict ordinal | **Verify consumer discrepancy**. Existing native group tests assert first/middle/last, tombstone and earliest-conflict ordinals, not just import indices. Reproduce the host's exact run before fixing; unattributable finalization retains no invented index. |
| R18.20 pending receipt | Delivered. Existing native lifecycle evidence covers pending/rollback/commit; repeat through the host because its checks were not run. No precommit success claim. |
| R18.21 guard | Delivered three statements for simple managed call; adoption separately three. Compiled read is eleven. |
| R18.22 preview | Delivered advisory read-only conditions, no reservation. Host correctly keeps apply-and-rollback for full validation. |
| R18.23 preparation | Delivered/adopted combined group preparation. |

### R19–R22: import, audit and lifecycle

| Item | Disposition and acceptance |
| --- | --- |
| R19.1 import validation | Verify apply/import parity for selected routes. Unknown values must be retained/reported, never dropped; declared facets must hold. New batched source timestamps are validated, legacy opaque strings are deliberately separate. Do not retrospectively claim legacy provenance is a parsed instant. |
| R19.2 reserved deleted edge | Delivered behavior; document `reserved_identity` and ambiguous endpoint selection. |
| R19.3 origin/zero-created load | Delivered private retained origin/outcomes and zero-created load; literal empty-load discovery has separate authorization. |
| R19.4 size | Delivered explicit 1,024/chunk-128 profile with byte/work/settlement bounds. |
| R19.5 scaling | **New residual work**, not unimplemented batching. Set-based eligible rootless writer is proven, but one 1,024-record call still takes 48–49 s versus 8–11 s in eight 128-record calls. Profile eligibility/fallback, cumulative JSON/report/schema work, subtransactions and finalization; remove super-linear growth without losing indices/provenance/partial progress. No universal tenfold or linear-time promise from client statement counts. |
| R19.6 result wrapper | Delivered; preserve complete tagged result and empty-load settlement, including unknown commit. |
| R19.7 multiplicity | Verify current selected route against the host claim. CONTRACT-009 already requires final relationship invariants. Distinguish legitimate incomplete partial-import semantics from a violated advertised invariant; fix a true gap or explicitly narrow the profile. Do not silently make partial import one atomic group. |
| R19.8 permissions | Clarify module writer import authority versus registrar/admin authority. Accept advisory typed capability discovery if needed, with execution reauthorization; registrar status is not the answer to every import permission question. |
| R20 baseline | Delivered separately granted whole-group/load audit. Feed remains a replication surface. Preserve current grants over complete retained owner union. |
| R20 residual discovery | Accept relationship-only load discovery, usable public key-filter reference resolution and authorized multi-module discovery; qualify cross-module/empty/deleted/legacy boundaries. Legacy backfill requires explicit migration or historical-unavailable result, never fabricated audits. |
| R20 payload/size | Design optional key/version projection only for separately authorized data readers; auditor membership alone must not disclose values. Support complete group pages within declared event/byte bounds or explicitly refuse. Test groups with more than 1,024 journal events; 1,024 operations is a different bound. |
| R20 ordering | Push back on commit timestamps/order invented from observation time/XID. Preserve newest-observed audit semantics. A real commit-order service would be a separate feature; feed order is not automatically an audit total commit order. |
| R21.1, R21.2, R21.3, R21.6 | Typed install/grant outcomes, transaction exclusion and administrator role recovery delivered. Verify tampered-marker/unsupported-source outcomes on current exact artifacts. Do not overwrite or reset damaged installations. |
| R21.4 runtime upgrade | **Delivered in v0.0.47**, owned by this chat and the linked restoration plan. Explicit populated UMF 0.10 forward migration, latest-only runtime, old-wheel fencing, preservation and release-blocking lineage tests. Export/import is not the default substitute for preserved identities/history/receipts/feed state. |
| R21.5 grant skipping | Keep atomic indexed batch behavior. Independent per-module calls already provide best-effort composition. Defer a new skip mode; it must never silently weaken atomicity. |
| R22 un-enrolled status | Enrolled person status delivered. Retain typed unauthorized for nonmembers by default. If needed, design an explicitly public minimal health/compatibility probe without installation/role/catalog disclosure; token possession alone is not enrollment. |

## Other three documents and open questions

| Source request | Disposition |
| --- | --- |
| Overhead A/B/C/D | Delivered lighter guard, pending token, bundled preparation/conditional catalog and scoped commit-cost improvement. Repeat unrun host pending/rollback token tests. |
| Overhead E1–E4 | Delivered conditional metadata, smaller binding transfer, once/process verification and exact-input compile caching. Older E2–E5-open heading is stale. Cache keys include complete model/binding/profile/limits/parameter inputs, not only SQL and document digest. |
| Overhead E5; question 3 | Read combination delivered and **already adopted**. Accept write/describe transaction consolidation and source-digest reuse only with original-source custody plus fresh authorization/stale checks. Inspect actual read-write support first; the read-only qualification is not proof every composite is supported in a write transaction. |
| Overhead questions 1/2 | Residual import growth R19.5; selective scan R17.5. Host measurements substantiate follow-up investigation, not the cause of every bottleneck. |
| Overhead question 4 | Current validator intentionally includes `maximum_bytes`, count limits, person, role/transaction context and release. Keep that contract; align caller limits to reuse. A content-only fingerprint could be separate, never reusable authority or a reason to bypass a smaller limit. |
| Latency targets | Enumeration and list meet latest reported local p95 targets; singleton/action do not. Retain 20/100/20/1,000-ms targets with controlled reproduction; noisy host figures do not establish quiet-host or Lakebase guarantees. |
| Registration E1/E2/E3/E5 | Linear compact evidence and typed preparation categories delivered for measured samples. Non-name unsupported-profile errors need rerun (R16.4); 500-KB case unrun. No new E4 was supplied. Registration 0.36–0.42 s is a measured baseline, not a new hard latency obligation. |
| Findings 1.1 | Duplicate wildcard/explicit relationship alias is documented compiler behavior. Keep refusal; broader projection/facts work under R17.2 addresses usability. Host underscore aliases are a workaround with duplicate work, not closure of its original corpus assertion. |
| Findings 1.2/2 | Historical nameless-source failure addressed in 0.0.45 registration. Preserve original inputs; explicitly author names in revised sources. |
| Findings 3 | Condition precedence delivered; collision index discrepancy goes to R18.19. |
| Findings 4 extension parsing | **Weft-owned verify/fix**: raw `compile_json` profile refusing UMF 0.10 extensions is distinct from Truss registration/compilation. Preserve original bytes and unknown extensions; do not strip extensions to claim original-document acceptance. Qualify the correct compiler entrypoint/profile and retain native/browser parity. |
| Findings 5 | Whole-entity optimization delivered; residual singleton scan remains open. |
| Requirements open questions 1–6 | Package index R10; document exact install/grant privileges and timeout/containment/retry outcomes; Bun-free deployment delivered; extra driver tuples require demand and separate qualification; applied progress R7; wider query operators/key domains belong to a Weft profile roadmap with no invented dates. |

## Implementation slices

The same chat now owns HF-01–HF-07 through the following release. Suggested
component roles identify boundaries, not delegated assignments to other chats.

| Slice | Work and owner | Dependencies | Validation gate |
| --- | --- | --- | --- |
| HF-01 | Reconcile adapter-facing disputes: R13, R16.4/5, R18.1/19, R19.1/7; Truss Python plus host adapter maintainer | Exact released cohort and original minimal inputs | Public wheel reproduction with native state, person/role, exact source hashes and complete result carriers. Correct stale asks; retain actual defects as fixtures. No message-based inference. |
| HF-02 | Typed error/diagnostic and receipt recovery design; Truss Python, with Weft owning compiler diagnostics | HF-01; CONTRACT-004/005/007/009 and ADR-005 amendments for new carriers | Nonmember vs broken grants; original digest replay after deletion; unequal-input conflict; revoked/historical owner; no cross-person leak; final-state failure without false index. |
| HF-03 | Empty-record paired required-field admission; Truss catalog | HF-01 and narrow R16.5 contract/test update | Empty vs populated, existing optional→required handled separately, concurrent writer/acceptance, DDD validation and unchanged unknown bytes. |
| HF-04 | Selectable facts/descriptors/relationship projection and facts paging; Weft plus Truss query composition | Versioned output/profile design, compiler metadata custody | Empty/all-null/aggregate columns, duplicate names, 100/101 fanout, continuation, exact values, native and actual browser compiler parity, current grants. Remove only corpus pins whose original assertions pass. |
| HF-05 | Indexed selective source path and remaining write/describe/import cost; Weft plus Truss runtime and host | HF-01; selective-read ABI design; HF-04 for combined facts/page path | Native plans on 10,001+ rows, counts and source-bound refusal; 128/256/512/1,024 imports with actual DML/fallback counts; schema/report work growth; end-to-end statement/time/CPU/wait measurements and rollback/revocation controls. |
| HF-06 | Completion check, dry-run observation basis and audit discovery/projection; Truss transaction/audit | HF-02; explicit constraint scope and disclosure contract | Actual deferred failure, prior caller work, no residue, two groups/transaction, relationship-only/zero/legacy loads, cross-module audit, >1,024 events and typed cursor bounds. |
| Existing RM-S1–S7 | Finish runtime upgrade and release gates in existing migration chat | Existing restoration plan; frozen target retains launcher isolation | Existing RM-T01–08 and exact installed-wheel lineage gate; do not fork this work into HF slices. |
| HF-07 | Publish corpus runner, docs and coordinated release; Truss release owner | Selected HF scope and migration gate for any changed runtime release | Clean installed packages, published hashes/cohort, Linux CI, native development-platform qualification, supported-source migration and old-runtime refusal. Package index/other drivers/managed Lakebase require separately selected gates. |

Priority: HF-01 first to remove stale/ambiguous demands. Then typed nonmember and
original-request recovery plus required-field admission, matching the host's
largest correctness blockers. Query profile and bounded selective source work
follow; residual import/write costs can be diagnosed independently. Finish audit
and corpus distribution in explicit release scope. The completed migration baseline stays immutable; a runtime-changing follow-up
release must satisfy its lineage gate.

## Shared constraints, validation and risks

- Preserve unknown data and extension content; assert retained/report behavior.
  Stronger input restrictions must be authored profiles, not accidental loss.
- Native PostgreSQL 18.6/psycopg 3.3.6, UMF 0.10.0 and Weft 0.4.49 scope the
  baseline. Lakebase is an intended deployment, not qualified by local Postgres.
- Use `python3 scripts/check-module-boundaries.py` and
  `python3 scripts/check-module-boundaries-controls.py`, including the existing
  Linux CI boundary workflow, before feature slices. Query/application modules
  must not import migration executors or implement competing UMF/SQL semantics.
- Before rollout, qualify only affected maintained native modules and selected
  corpus cases against the final installed artifacts; retain failures/skips.
  Existing release counts are historical evidence, not this review's test run.
- Performance acceptance uses at least 100 warm sequential calls after recorded
  warmup, nearest-rank p95, exact fixture/package hashes, connection policy,
  transaction/statement/wait/CPU categories and machine load. Compare the same
  adapter on matched conditions. Inspect algorithms/plans as well as timings.
- Preserve old APIs by explicit profiles or deliberate version changes. Do not
  reinterpret receipts, complete results or audit dates to satisfy host wording.
  Roll back candidate adoption on fidelity/authorization regressions; installed
  database changes use verified forward repair/backup recovery, not old-package
  execution against new runtime bytes.

## Execution contract and continuation evidence

Owner follow-up on 2026-10-21 authorizes the remaining accepted priorities as the
next release after the existing migration tranche finishes. Deliver the pushback
response first. Then hand HF-01–HF-07 to the existing Find Truss schema migrations
chat (`01a16023-fabd-7fa3-9abf-44d42e7fd673`), reconciled against its completed
baseline. That chat is authorized to implement, test, review, merge and publish
the next release; select the next available version at execution time. Preserve
the declined/deferred variants above and update governing contracts before
changing behavior. Do not interrupt or widen the current migration tranche.
Existing migration authorization remains with that chat.
Owner clarification: the migration tranche must pass final Linux CI, be merged,
be published and pass public-artifact/clean installed-package verification before
the following-release handoff. Explicit authorization includes commit/push, PR,
review/fixes, merge and migration-release publication. A green unmerged or
unpublished candidate is not completion. The same chat then owns HF-01–HF-07
for the following release, preserving the documented pushbacks and deferred scope.
Implementation estimate and spending ceiling are unknown; no comparable usage
evidence supports a precise token/time promise. Choose a bounded slice and record
its estimate/actual usage before sustained implementation, without a separate
estimation report. No tracker was selected or created.

Planning completed: all R1–R22 and numbered subrequests, overhead targets/questions,
registration asks and query/condition findings have dispositions above. Open
acceptance decisions remain explicitly proposals; no new supported capability is
claimed. Handoff state: **dispatched** on 2026-10-22 at approximately 01:33 UTC
(2026-10-21 21:33 America/New_York) to the same Find Truss schema migrations
chat (`01a16023-fabd-7fa3-9abf-44d42e7fd673`, host `local`). The send tool
confirmed successful delivery to that thread. The one-time message authorizes
HF-01–HF-07 through implementation, review, final Linux CI, merge, publication
and public-package verification, retaining all written pushbacks and explicit
deferred scope. Heartbeat `truss-next-release-handoff` was disabled after
this dispatch (tool-confirmed `PAUSED`); it must not send a duplicate handoff.
The destination chat is active and acknowledged that it is beginning HF-01–HF-07
against 0.0.47 and carrying the accepted work through the following release.

Migration prerequisite verified: public v0.0.47, merged source
`6c9365c8be60b55602fe4e7bd4e45b4b5040ec74`, successful final Linux tag workflow
`39702368076`, 52 migration cases without skips on Linux and clean public-wheel
macOS, 12 checksummed public assets and 445 matching runtime files. GitHub live
reads confirmed the published non-draft release and successful source-matching
workflow. [Public verification](evidence/runtime-migrations-20261021/published-0.0.47/validation.json)
retains the installed-package and artifact evidence. No new tests were rerun by
this handoff review. Future native multi-edge proof is required when the next
real native edge is introduced, as specified by the migration release.

Next action is HF-01 against the 0.0.47 baseline and clean public artifacts.
Record later commands, fixture hashes, observed defects,
adopted decisions and completed slice IDs here rather than adding another queue.

2026-10-21 23:03 UTC heartbeat: migration chat completed local implementation
and reported 43 migration checks, 78 regressions, 20 boundary controls and exact
wheel/sdist payload verification. Its plan still marks hosted Linux qualification
pending; candidate is unpublished. The next-release handoff remains unsent.
Sent a scope-preserving continuation to the same chat to finish the existing
blocking Linux gate and report evidence or a concrete access/approval blocker.
The send tool confirmed the target thread. This is not the HF release dispatch;
monitoring remains active. Future real multi-edge proof remains event-dependent,
not a requirement to fabricate a release before this handoff.

Owner clarification dispatched to the migration chat: finish Linux CI, review,
merge, publication and public-package verification before the next handoff.
The first Linux run has failed predecessor native-inventory admission and the
agent is investigating; no success or publication is claimed here. The send
tool confirmed delivery to the existing chat; no replacement chat was created.

## Execution progress — following v0.0.47

2026-10-21 (America/New_York): the same agent accepted the HF-01–HF-07
handoff after verified migration release completion. Working branch:
`codex/hohfeld-followup`, based on main `da677e40`. All four original Hohfeld
source files match the recorded SHA-256 snapshot. Current selected dependencies
remain Python3.11.17, PostgreSQL18.6, psycopg3.3.6, mini-racer0.14.1,
UMF0.10.0 and Weft0.4.49. The public 0.0.47 wheel/native/migration identities
are retained in the completed migration release evidence, not inferred from labels.

HF-01 is the first bounded slice: public-wheel controls for nonmembers versus
damaged grants, required paired core/DDD field evolution, first/middle/last key
collisions, selected import value/facet validation and final multiplicity.
Estimate from this checkpoint: 8,000–16,000 additional tokens including fixture,
verification and review work, with low confidence; this is not a spending ceiling.
No total ceiling was provided, and no per-slice token meter is available. Record
actual commands, case counts, elapsed measurements and findings here and in the
retained receipts; do not invent precise token usage. The rest of the release is
not estimated until these reproductions establish its actual defects.

Preflight: Python3.11 module boundaries pass at 1,693 imports and all 20 checker
controls complete. An initial invocation using the machine's older `python3`
failed to parse modern syntax; it is a tooling-version failure, corrected by the
selected Python3.11 interpreter, not a source defect. No behavior change is claimed.
No earlier performance target or skipped host corpus case is promoted by this
preflight. Runtime migration and `GroupOperationFailure.operation_code` are
already delivered; they will be retained rather than reimplemented.

### HF-01 public-artifact findings — 2026-10-21 21:48 EDT

[Original public-wheel observations](evidence/hohfeld-followup-20261021/baseline-public-0.0.47/qualification.json)
execute 12 methods and retain 31 complete case observations in 18.838s on
macOS ARM64/Python3.11.17/PostgreSQL18.6, without skips or probe failures. This is
successful reproduction, not a claim that every requested outcome passes. The
[artifact binding](evidence/hohfeld-followup-20261021/baseline-public-0.0.47/public-artifact-binding.json)
names the exact verified public wheel, native digest, source and still-unsatisfied
outcomes. All fixtures use synthetic non-PII data and actual public identities.

| Dispute | Observed 0.0.47 outcome | Execution consequence |
| --- | --- | --- |
| Nonmember group/context/reference/direct reads | Typed denials already delivered across nine selected surfaces | Correct stale adapter assumptions; retain regressions |
| Nonmember legacy/batched import context/build/execution | Four surfaces still return execution failures | HF-02 must add typed denial without masking damaged installation |
| Damaged group-context EXECUTE grant for an enrolled writer | Incorrectly returns UnauthorizedPerson | Genuine error-classification defect; test native membership and missing privilege independently |
| Required paired core/DDD field on empty/nonempty Record | Both refuse unsupported; source/head/data remain intact | HF-03 adds the narrow empty-record admission and typed populated refusal under writer exclusion |
| Collision on first/middle/last single-field primary key, labels zz-a/zz-b/zz-c | Exact original index 0/1/2 and public operation_code=key_conflict | Current reported discrepancy not reproduced; no adapter index inference needed |
| Apply, legacy import, batched import unknown property | Original name and exact scalar survive native retained map and public reads | Do not implement blanket rejection or claim data loss |
| Authored string facet and batched source timestamp | Apply/import refuse invalid length; batched garbage timestamp creates no object | No reproduced validation gap for this selected profile; legacy opaque-time policy remains distinct |
| Batched relationship min/max | Minimum-invalid object rejects; over-maximum import commits two edges and rejects the extra | No reproduced advertised invariant violation; preserve per-record partial import semantics |
| Final-state minimum failure | Correctly omits operation index but shares dependencies code with restrictive delete | HF-02 improves diagnostics; do not fabricate an operation index |
| Decimal18/scale2 and nested scalar containers | Register already | Qualify the selected subset; do not repeat stale unsupported-profile claims |
| Valid owner UUID source | Explicit unsupported_profile, unchanged head | Preserve closed native subset; no generic invalid_transaction translation |

Initial failed reproduction attempts are retained separately. One single-key
fixture initially retained a relationship reference to its removed old key; one
serializer initially omitted the explicit ABSENT carrier. Both harness defects
were corrected. The damaged-grant control's failed desired assertion established
the product finding above. No failed attempt is counted as a passing behavior.
Per-slice token usage is not exposed by the runtime; the retained command/test
and elapsed-time evidence is the available actual measurement. HF-01 baseline
reconciliation is complete; HF-02/03 contract amendments and desired-behavior tests
are next. Import scaling and the other accepted slices remain required.

### HF-02 selected implementation boundary

Native PostgreSQL18.6 controls show that dynamic CASE and MATERIALIZED/LATERAL
filters do not avoid EXECUTE checks on a referenced private function: both raise
42501 before a denial branch can produce its result. Do not claim an SQL guard
can classify that by inspecting prose. The chosen design is a finite set of
native public person-entrypoint shims: current native role-family admission,
then independent verification of the original caller's EXECUTE on the selected
original function, then its existing private implementation. No extra client SQL
roundtrip or alternate mutation engine is introduced. Private grants stay private.
Intentional native authorization is P1403; PostgreSQL42501 is not classified as
business denial. Governed contract amendments precede source changes.

The same slice adds an immutable original request frame and observation-only
recovery, stable retained audit attempt identity, and distinct final-state
multiplicity diagnostics. It preserves complete canonical comparison, retained
owner authorization, no cross-person replay, no execution on missing receipt,
no fabricated operation index and original transaction/uncertainty custody.
Low-confidence estimate for this larger correctness slice is 20,000–40,000
additional tokens including native controls and review; no overall ceiling or
per-slice token meter is available. Record actual case/elapsed evidence, and do
not treat this estimate as a release spending promise. HF-03 remains required
alongside it; no follow-up capability is claimed complete by this design.

HF-02 person invocation component: seven native desired controls pass in 11.135s,
covering all 13 nonmember surfaces, original/mutation/private dependency grant
damage, no private PUBLIC access, retained prior work and a three-statement normal
context call. Thirty-three additional source controls pass. Two census classes
initially lacked their binary environment; the corrected run passes all nine
native controls in 9.020s. Python boundaries pass at 1,697 imports and 20 checker
controls. Generated native signatures come from the original PostgreSQL metadata;
the generator explicitly handles void and TABLE results. The earlier void-result
DDL error is retained, not counted as a product pass. Recovery, graph diagnostics,
HF-03–HF-07, final native inventory/migration edge and publication remain unfinished.

### HF-02/03 implementation checkpoint — 2026-10-22

The source now implements original-frame receipt recovery, stable retained group
IDs, distinct final-state multiplicity diagnostics and empty-Record paired
required core/DDD additions. A first combined native source run passes 34 cases
in 67.771s, with exact source hashes in
`evidence/hohfeld-followup-20261021/hf02-hf03-source/qualification.json`.
Two added settlement controls pass in 5.957s: real in-flight contention and an
injected lost acknowledgement after actual server commit. The final combined
cohort passes all 36 cases without skips in 72.994s; its original receipt, exact
test producers and claim clarification are retained separately in
`evidence/hohfeld-followup-20261021/hf02-hf03-source-v2/`. Earlier run evidence
stays unchanged. The injected acknowledgement control proves the later native
receipt observation, not a general network-fault transport protocol.

Required-field controls cover both lock orders and populated refusal; three
existing compatible-evolution workflows also pass. The stale-pin race exposed
a preexisting low-level missing-row error. The native selected-type resolver now
raises its explicit invalid-input verdict on a missing current definition; the
optimization can fall back and the group facade returns a typed refusal.
The PL/pgSQL CASE syntax repair and the incorrect initial assumption that every
failed create is diagnosed before native allocation are retained as failed
attempts. Actual allocated IDs are reported without a persistence claim; proposed
objects use their original creation ordinal, never an invented native ID.

Python boundaries pass at 1,702 imports and all 20 checker controls. The root
exports only the public immutable request frame and pure freezer; the existing
group runtime owns serialization and recovery. No new compiler/parser boundary
is introduced. Per-slice token usage remains unavailable. These are component
claims; the selected expiry/protection disposition, HF-04–HF-07, frozen migration
edge, final Linux/installed cohort and publication are still required.

### HF-04 source component checkpoint — 2026-10-22

Compiler-owned immutable column descriptors now accompany buffered, streamed and
paged decoded rows, including empty/all-null results. Explicit entity selection
retains ordered facts and separately requests relationships; facts can accompany
continuation. The existing complete entity profile is preserved. The selected
public-Weft0.4.49-based development cohort is frozen at
`5b51e5ce0df2945fd2f90e8a53e081a6158a1bcb`; its wheel SHA-256 is
`0bcf3c81417df7be210e48f2876fc2473498f459fc3c3a7f27e751a883b16ddd`.
It passes355 core and199 backend tests,15 installed compiler cases and actual
Chromium151 byte parity. It excludes the separately gated managed UC tranche.
Development version0.4.51.dev1 is not a reserved publication number.

The first expanded Truss native run passed21/23 and exposed two revoked-reader
failures: compiled queries still invoked private binding functions before the
typed person gate. Three native-declared query shims extend the finite registry
to43 declarations. The combined catalog call also uses the existing guarded
reader shim. All24 native query/page cases then pass in50.877s, including a new
damaged original binding grant control retaining42501 and prior caller work.
Preserve the failed run and actual PostgreSQL declarations with the component
evidence. Python boundaries retain1,702 imports and20 checker controls.

ADR-005 now selects indefinite complete-receipt retention for ordinary runtime
operation. Two explicit administrative expired-header fixtures qualify observer
behavior only; direct writer mutation and original immutable-trigger bypass are
not supported APIs. They do not claim an elapsed24-hour protection experiment or
an expiry writer. No new release, indexed query support or completion/audit
extension is qualified by this checkpoint. The new native target remains
unfrozen until the remaining HF-05–HF-07 changes and migration gate pass.

### HF-05 selected implementation design — 2026-10-22

CONTRACT-007 selects compile/IR0.2.8 and query ABI1.2, with new backend43
(and44 for cursor delivery;42 already belongs to the existing cursor backend).
Move the unpublished entity-selector profile off the published0.2.7 schemas.
Start with exact string/boolean equality via generic property GIN and complete
bounded residual evaluation; numeric/temporal equality retains the old fallback.
Qualify authored single required string ordered seeks up to1,024 UTF-8 bytes,
with an indexed whole-key exception check; preserve valid larger/composite/exact
numeric keys through the existing bounded route. Global redundant uniqueness
and complete key inventory are explicit native proof obligations, not assumptions
in a support claim. Do not turn candidate limits into claimed index-node limits.
Typed resolution categories are emitted by Weft where known and disclosed only
after current native scope checks. Remaining import/write/describe performance
measurements and honest unmet targets remain part ofHF-05.

### HF-05 native source checkpoint — 2026-10-22

The native component creates/commits10,001 objects through public groups, retains
legacy full-source refusal, and admits exact candidate equality and eligible
ordered seeks. Generic JSONB path-ops GIN and short single-string key order/
exception indexes add no per-type DDL. Original native plans and actual source
index scan deltas qualify index use; the first asynchronous-maintenance GIN plan
instead scanned all10,001 rows and is retained as a failed optimization attempt.
The selected GIN uses synchronous maintenance; actual managed batch timings are
retained rather than claiming a universal speedup or physical work-node bound.
Valid1,025-byte keys remain writable and force complete bounded fallback; caller
rollback preserves the prior10,001 committed objects. Other key families remain
on the existing bounded route. Exact UMF encoder/decoder controls retain empty,
Unicode, length framing and1,024/1,025 boundaries.

The expanded registry has54 actual native declarations. An original ACL check
after a contained54000 source error incorrectly retained an old EXECUTE verdict;
a separate native probe reproduces it. A plain fixed SELECT also failed. A fresh
plan of the fixed parameterized native owner/ACL query passes the same sequence,
without interpolating caller SQL or changing client statement counts. Native
PostgreSQL internals were not independently traced. The final combined source
run passes51 cases without skips in95.221s, covering actual index use, long-key
fallback, original-grant damage after refusal, revocation, all query/page cases,
person admission and16 retained-request recovery cases. Original failed controls
and source hashes remain in
`evidence/hohfeld-followup-20261021/hf05-native-source/qualification.json`.

The new compile/IR0.2.8 and query ABI1.2 integration is still in progress. Backend
interface0.2.8 was already used by ordered-engine profiles, so this increment
uses fresh backend interface0.2.9. Candidate ABI bytes are governed in
`../02-design/contracts/query-abi1.2.proposal.json`; they are not yet selected by the installed runtime. This checkpoint
qualifies native source components only. Original native-index/model custody,
full new compiler/public composition, remaining HF-05 costs, HF-06/07, target
freeze, populated migration lineage and final release gates remain required.

### Snapshot and existing rebind regression checkpoint — 2026-10-22

Actual native metadata identifies11 STABLE data/fact sources. Their new public
wrappers now preserve that statement snapshot while the person/owner/ACL guard
remains independently current. Registry0.2 records the split; STABLE scalar fact
wrappers do not enter the VOLATILE managed-function optimization. A controlled
concurrent public writer proves the distinction: an intentionally VOLATILE data
wrapper sees the later committed value, while the selected STABLE wrapper returns
the original statement value. The fixture's initial transaction-scoped advisory
lock cleanup failure is retained and corrected; no modified fixture installation
is promoted as the released source profile.

Broader evolution testing exposed an HF-03 regression: an early new-property
required count blocked existing valid retained-value core rebinds. The shared
planned rebind validator now owns new-property requiredness after complete root
readership. Original admitted declarations distinguish the empty-only paired
DDD addition, which refuses every populated Record even when valid retained
values exist, from the existing qualified core-only rebind path. Existing-property
tightening retains its original canonical census. Six paired-addition controls
and original required/keyed rebind workflows pass. Stale42501 business-denial
assertions were corrected to nativeP1403; real damaged grants remain42501.

The final pre-ABI source run passes37 native cases, no skips,68.504s with the
exact PostgreSQL binary supplied to the managed guard fixture. It includes actual
10,001-object index use, exact/control-character operand byte bounds, true/false
cells, snapshot countercontrol, managed guards, person admission and the rebind
split. Original failed attempts, source hashes and test producers are retained in
`evidence/hohfeld-followup-20261021/hf05-snapshot-rebind/qualification.json`.
No final ABI/package/migration/release claim follows from this checkpoint.

### Next-release migration publication obligations

Minimal person status currently reads the genesis installation marker rather
than the effective migration overlay. Qualify and correct status after a populated
upgrade, including fresh47 genesis versus44-upgraded47 genesis.

The initial XID-tie concern was an incorrect inference from the SQL head helper.
Inspection of `_migration_execute.execute` confirms that a complete route appends
one final immutable receipt after all edge effects and intermediate structural
verifications. `RuntimeMigrations` requires an owned idle autocommit connection
and settles its own excluded administration transaction. A real44→73→74 route
therefore does not append two tied-XID receipts or publish its intermediate73
runtime. Keep that actual atomic publication contract and qualify exactly one
append per completed route, with all original edge recipes/step evidence retained
inside it. Writer XIDs are not a general commit-order service. Do not add a new
chain-head algorithm for the disproven tied-edge premise.

The next release still requires actual fresh47 and previously upgraded47
populations, the real multi-edge route from44 using only the latest tool,
unchanged prior receipt rows plus one new final append, no old-wheel execution,
rollback/lost-ack settlement and current person status. Published47 source
profiles and recipes stay immutable. No release-age eligibility cutoff is added.

### ABI1.2, completion and audit candidate checkpoint — 2026-10-22

HF-04/05 now consume the selected Weft0.4.51 compiler, compile/IR0.2.8,
backend43/44 and interface0.2.9. Exact descriptors and requested ordered entity
facts come from the compiler. Native indexed predicates bound the complete
candidate set before residual evaluation; supported ordered string keys use a
generic Btree and all other key domains retain the complete bounded fallback.
Actual 10,001-object public populations prove GIN/Btree use and refusal boundaries.
Unlimited cursor portals do not inherit a finite key-page optimization.

The import owner-union pass now deduplicates exact owners without skipping any
original input identity. Original 1,024-record build/import samples improve from
12.845s to8.316s; a later instrumented sample records8.281s through build/import,
0.0065s describe and0.1246s commit,8.415s end to end. The final sample attributes
7.544 native CPU seconds and0.654 Python CPU seconds, with30 client submissions,
eight set-based writes each to object/journal/owned-operation and active native
wait samples. These are synthetic macOS ARM64 observations, not p95, universal
10×,20ms, or cross-platform performance claims. Broader targets remain unmet.

HF-06 completion and dry-run execute under a host-owned savepoint, force only
installed Truss deferred constraints, and publish an observation only after
rollback and custody rechecks. They preserve prior caller work and unrelated
host constraints. They issue no durable receipt or stable created identity.
Audit discovery may span modules but omits entries lacking complete current
scope. Whole mutation metadata permits4,096 events within its separate byte
budget. Optional key/version data requires current data readership before and
after projection. Named entity-key filters are native resolved; they are not an
auditor-only value oracle.

A previously undiscovered relationship-only test exposed real endpoint JSON
casts, nullable association ownership and omitted actor-name detail defects.
The corrected test is now in the explicit shared corpus. Newly produced loads
have exact complete owner inventories; real public47 incomplete headers remain
byte-preserved and unavailable after upgrade. No historical ownership is invented.
Source component probes, failures, exact producers and captures are retained in
[evidence custody](evidence/hohfeld-followup-20261021/hf05-hf06-final/custody.json).
Unpublished b7/977 candidates remain separately archived, not admitted historical
releases.

HF-07 provides an independently extracted60-case corpus archive and an installed
runner requiring the exact toolkit/compiler/native cohort with zero skips.
The80-case lineage gate includes all three published source-wheel populations,
actual44→47→latest custody, unchanged prior receipts, real lost COMMIT response
and historical audit preservation. Both full installed local gates pass without skips:80 migration cases in
133.713s and60 independently extracted corpus cases in138.515s
([original receipts](evidence/hohfeld-followup-20261021/installed-048-native2f23/receipt.json)).
The final native target is `2f230a44571ceb5c6ea04d86770cfd3cd3adcf18a09c5f658d644d74e01ec9fb`.
Only current Weft51 consumers enter the runtime cohort; older consumer records
remain evidence. Hosted Linux, exact published package adoption, review, merge
and publication remain required before this checkpoint is delivery.

### Release regression review and dependency resolution — 2026-10-22

The broader installed release commands exposed stale42501/P1005 assertions,
a historical compiler-cohort inventory, and preview race instrumentation still
matching the private original function name. Corrected tests now require exact
P1403/P1405/multiplicity outcomes and observe the actual public preview command.
Both real snapshot/revocation races pass. Administrative installation recovery
still requires its actual private EXECUTE grant; ordinary callers receive native
42501 without installation names.

One actual person-surface gap was corrected: receipt inclusion now uses a55th
public guarded read invocation. No membership is distinct from a damaged original
receipt-function grant, which a new native countercontrol independently proves.
All27 affected native cases pass, no skips,89.874s. This refines only the unpublished
candidate to native `c4339ac7f09ab5a004c272ab00962107a970938004c1765ec4163e4d5ca9b6f0`;
the prior2f23 candidate is archived with its passing component evidence, not
admitted as a published source. Both native initializers and logical restore pass.
The explicit independent corpus now contains61 cases. The exact installed wheel passes the complete serial80-case lineage gate
(no skips,182.468s) and61-case extracted corpus (no skips,309.862s).
[Original final-candidate receipts](evidence/hohfeld-followup-20261021/installed-048-nativec433/receipt.json)
retain both successes and the invalidated concurrent run: two fixture clusters
received administrator shutdown during restore (cause unknown), producing15
errors. Isolated logical restore and the full serial rerun pass without relaxed
limits or assertions. All455 runtime payloads match the isolated release source. The original public
1,000-object/1,000-edge installed workload also passes in76.857s
([original report](evidence/hohfeld-followup-20261021/installed-048-nativec433/public-workload/receipt.json));
its latency budgets remain provisional and no prior-run nominal baseline was supplied.

The Weft dependency is implemented and compiler-frozen at f0039979, with selected
release ancestor770137be; main integration preserves separately gated managed UC
work and its unqualified status. Its actual31-case native/Chromium corpus now
includes an original document carrying document-level unknown content, Record
umf.ddd and Field hohfeld.view payloads. The artifact retains the exact original
source SHA in modelPins. Unknown selected Field extension meaning explicitly
refuses WFT-TYPE; no stripping or relabeling claims model acceptance. The selected
Truss runtime entrypoint owns this profile; generic compile_json lacks its backend
registration. Linux x86/ARM packaging run39743904917 passes, but Truss selects only
the x86 wheel for its upcoming native Linux gate. Exact public publication and
clean installed adoption remain required. Two main-integration stale workspace
controls (missing example feature and promotion of an old UMF0.7 success golden)
were fixed without compiler behavior changes; the next full hosted run is required.

### Final local upstream gate and engineering review — 2026-10-22

Committed Weft integration61c994b8 passes the complete fresh-host gate with5,451
source inputs reconciled after actual CLI, installed native-wheel and Chromium
execution. The original2,181 UMF0.7 requests are explicitly qualified as current
envelope refusals, with zero current compiled inputs credited. Historical success
proofs remain immutable. Separate current compilation evidence is the31-case
UMF0.10 native/Chromium corpus, including original extension-bearing source.
Seventeen resource/security cases retain exact cross-host parity. The initial
stale full-host gate and local setup failures were retained and repaired rather
than reviving old core execution. [Complete source-bound local host receipt](evidence/hohfeld-followup-20261021/weft-final-host-source61c/receipt.json).

Engineering review rechecked finite native grant/owner separation, stable data
snapshots versus current authorization, observer-only original request recovery,
empty-only paired DDD admission versus retained-value core rebind, complete
candidate bounds before residual query evaluation, host-owned constraint/rollback
custody, reader authorization for audit key data, immutable old audit headers,
and one final publication per complete migration route. The review's discovered
receipt visibility gap and stale race instrumentation are fixed with independent
native controls. No unresolved local behavior finding remains in the accepted
scope. Broader performance targets, managed support, additional driver/query
subsets and all written pushbacks remain explicit limits.

Weft PR27 and Truss PR29 still require final hosted gates, merge, exact selected
Weft publication/adoption, Truss tag qualification, public artifact verification
and documentation publication. Local success is not the release exit.

### Arras source and qualification amendment — 2026-10-22

The owner identifies Arras as the renamed Hohfeld consumer and requests that this
release target its active sources. The four documents now live under
`/Users/erik/Projects/arras/docs/helix/02-design/`. Registration is byte-identical;
query findings rename the consumer and `hohfeld.view` to `arras.view`.
Requirements and overhead documents also relabel six historical measurements
from51 Records to30 while retaining their original timings. Those timings retain
their original51-record scope; Arras owns the correction or a fresh30-record run.

| Current source | SHA-256 |
| --- | --- |
| truss-requirements.md | `0a7be408d15947382f0ab3a5af05a3ff0978c85e597db31ff6acb50caeabed60` |
| truss-statement-overhead-spec.md | `caeb0276935514aa05735772fd3653dd9fb6cefaf7145d8f3263d60b6ba4ff15` |
| truss-registration-evidence-spec.md | `1a60da1464be4d1b03b0877e27b497551b86782ef55c1776eeaa4c72a3742abf` |
| truss-query-and-conditions-findings.md | `d31e36a1fdfa47fb35a0999f22317b410ad22455fb343d80f3362aad3228e777` |

`arras.view` is a real source namespace change. The f003 compiler artifacts and
31-case historical corpus above remain valid component evidence but cannot
qualify it. Rebuild the unpublished Weft0.4.51 candidate from its selected release
source, admitting opaque Record/Field metadata only when the same exact original
owning document declares `arras.view` version0.1.0. Missing, malformed or unsupported
declarations and unknown selected semantics must refuse without SQL. One document's
declaration must not qualify another's payload. Preserve original bytes/pins and
unselected unknown content; do not interpret presentation metadata or broaden
raw-table relationship semantics.

Sol owns review and Luna implementation under the owner's explicit allocation.
The new native Truss fixture first reproduced ordinary acceptance/source custody
followed by the old compiler's WFT-TYPE refusal. Positive original-source query
and relationship composition, supported/unsupported declarations, native wheel
and Chromium parity, refreshed exact compiler cohorts and all final release gates
remain required. Truss nativec433 is unchanged by a compiler-only metadata fix.
Arras's coordinating chat owns its adapter, parse harness, dependency adoption and
consumer evidence after the exact public package pair is available. Its fixture
parse harness that strips extensions is not runtime acceptance evidence.

## Exit criteria

- [x] Disputed consumer failures are reproduced or corrected with exact artifacts (selected HF-01 scope above).
- [ ] Each selected behavior change has governing contract/test amendments and
  native disclosure/transaction/fidelity evidence; declined variants are explicit.
- [ ] Relevant original corpus assertions pass before their limits are removed.
- [ ] Selected performance targets are met on a declared workload/tuple, or remain
  explicitly unmet; neither API availability nor one timing closes them.
- [ ] Runtime-changing release passes the existing migration lineage gate and
  clean package qualification; broader index/platform/managed claims stay scoped.

## Source custody

Hohfeld source directory:
`/Users/erik/Projects/hohfeld/.claude/worktrees/helix-bootstrap-setup-f77e53/docs/helix/02-design/`.
These digests identify the read snapshot; source files were not edited.

| File | SHA-256 |
| --- | --- |
| truss-requirements.md | `82f62abe6b63720540663fe42fe210d632bb9d9a510f1a3d6727aabc50340ed7` |
| truss-statement-overhead-spec.md | `4cd51c5951e8732dcc85bd933130d50a4ff79a185ab98ac5b4b4bc968dd7db97` |
| truss-registration-evidence-spec.md | `1a60da1464be4d1b03b0877e27b497551b86782ef55c1776eeaa4c72a3742abf` |
| truss-query-and-conditions-findings.md | `f53648b10f839808b2e249f96f283596eaff991b71e1ff7dbe7b804858e0e9ac` |

Local evidence inspected: [0.0.45 release](releases/v0.0.45.md),
[performance receipts](evidence/hohfeld-performance-20261021/README.md),
[earlier embedder dispositions](evidence/embedder-e2-e8-20261020/review.md),
[Python guide](../../../packages/python/README.md),
[released failure carrier source](../../../packages/python/src/truss/groups.py),
[group collision controls](../../../packages/python/tests/test_group_create_native.py)
and [validator implementation](../../../packages/python/src/truss/_catalog_runtime/reader.sql).
Earlier embedder prose permitting nameless registration is superseded by the
0.0.45 contract/release. Older planning statements that upgrades are forbidden
are superseded by the restoration plan and actual v0.0.47 release evidence;
original older release claims remain historical.
