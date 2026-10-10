---
ddx:
  id: STP-028
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-028
      kind: informed_by
    - id: TD-028
      kind: informed_by
    - id: SD-007
      kind: informed_by
    - id: CONTRACT-011
      kind: informed_by
---

# STP-028: Corpus and interchange

## Story Reference

US-028, TD-028, SD-007, TP-001 and CONTRACT-004. Tests are planned; no second implementation is claimed.

## Scope and Objective

Prove complete corpus aggregation and independently witnessed bidirectional native interoperability.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-028-AC1 | `required_corpus_pass_is_complete` | Every required normative observation matches; exact versions/digests reported; missing/skipped required case prevents pass | `@covers US-028-AC1` | Contract | `tests/conformance/interchange.test.ts`; independent manifest/results |
| US-028-AC2 | `independent_implementations_cross_read` | A-write/B-read and reverse match independent state/journal expectations on actual shared layout | `@covers US-028-AC2` | Native integration | Same file; two genuinely independent implementations and disposable database |
| US-028-AC3 | `divergence_retains_evidence_and_attribution` | Deliberate mismatch retains both outputs/oracle and reviewed implementation/contract attribution; unresolved attribution is explicit | `@covers US-028-AC3` | Contract | Same file; known adapter defect and known fixture defect |

## Executable Proof

Future command `bun test tests/conformance/interchange.test.ts` requires harness/adapter schema. Full AC2 evidence additionally requires independent implementation builds and native matrix receipts. Mock adapters qualify runner behavior only, not interchange support.

## Data and Setup

Use independent expected fixtures, identity aliases and fresh state per direction. Native observer checks canonical/derived/journal and reports independently. Exact environment and required-case counts are recorded. Two wrappers sharing the same core are not independent implementations.

## Edge Cases and Failure Modes

Newer required corpus refuses full pass; selected host-extension exclusion is explicit. Asymmetric value decoding, journal omission and wrong identities fail. Two implementations agreeing on a wrong result still fail independent expectations. Attribution review does not erase observed mismatch.

## Build Handoff

Select exact registered case-adapter/corpus manifest, original producer/custody/native environment/resource profiles; consume the authored runner result/divergence/receipt/assessment wires, write red tests, implement orchestration/native observers, then obtain independent bidirectional evidence. All criteria block full-profile closeout; unavailable second implementation remains unverified, not a skipped success.

## Complete resource and interruption evidence

CONTRACT-011 governs these runner/assessor cases. Select exact quantitative resource, original producer/custody and containment profiles before executing; fixtures cannot define their own passing qualification manifest. Complete receipt means complete required outcome inventory, not every case passed.

| Planned case | Independent assertion |
| --- | --- |
| `run_capacity_refuses_before_environment_effects` | Oversized input or unqualified worst-case outcome/evidence bound returns unavailable(resource), creates no native/environment resource and emits no recorded receipt |
| `complete_stopped_receipt_is_not_qualification` | Confirmed contained resource stop records every actual failed/skipped/not_run outcome and required evidence; the assessor cannot qualify when mandatory criteria remain unfulfilled |
| `unknown_case_remains_original_recovery` | Lost worker/cleanup reply retains original run/environment/progress as interrupted; an active unknown case is not relabeled failed/not_run and reconciliation launches no replacement run |
| `evidence_overflow_cannot_suppress_divergence` | Complete mismatched outputs/oracle attribution and raw performance samples survive in original custody; no truncation/digest substitution or case omission produces a pass |
| `assessment_resource_is_unavailable` | Complete artifact/manifest resolution overflow yields unavailable(resource), with no partial assessment or cached qualified verdict and no invented integrity/criteria failure |
| `exact_limits_include_simultaneous_buffers` | Exactly-at/one-over case/count/byte limits use complete escaped envelope and actual raw/decoded/archive reservations; independent counters detect concealed copies and uncertain refunds |
| `original_recovery_survives_saturated_admission` | Full new-run capacity cannot evict an existing unresolved run or its original evidence; cleanup/reconciliation retains its reserved capacity and exact issuer |

Faulted runner/assessor components qualify only honest aggregation and resource/recovery behavior. Native observer receipts, independent implementation provenance and the complete declared matrix remain required for US-028-AC2. Retained false/unknown results remain evidence even if later runs pass; a rerun has a separate identity. Never infer rollback from timeout or silence. All scenarios remain planned until original native/host adapters and exact resource profiles exist.

Divergence wire scenarios distinguish observed unresolved mismatch from reviewed original attribution. Reject claimed closeout without recognized reviewer/original full evidence; preserve original observations after correction; independently detect two agreeing wrong implementations. Forged attribution enum or fixture-generator agreement cannot establish implementation/contract blame. US-028-AC3 stays open until actual reviewed evidence exists.

Single-run divergence scenarios require exactly one original implementation/observation and independent expected/native evidence, with no invented second implementation. Reviewed single implementation attribution cannot substitute interchange A/B blame; converse mismatches similarly reject generic single attribution. Verify original mode through actual referenced mismatch bytes, not the review enum alone. A single corpus pass/mismatch cannot close bidirectional interoperability.

Divergence wrapper check: `bun docs/helix/04-build/evidence/design-audit/check-conformance-divergence.ts <Ajv Draft 2020-12 module path>` passes 12 envelope cases. It rejects fabricated second-implementation fields, observed blame, missing reviewer recognition, rewritten observation fields and majority attribution. Wrong mode attribution, forged recognition and equally wrong observed outputs intentionally pass shape; original mismatch/issuer/oracle/review evidence must independently refuse them. No case in this command establishes actual mismatch, review or native support.

Receipt-capacity tests charge both complete required-case entries and complete outcomes, including escaped UTF-8 coverage/ID/reason text, artifact references, delimiters/separators and remaining context. Maximum candidate reserve is 1048576 + 1000×(4096+16384) = 21528576 bytes. Reject unbounded manifest-entry producers before effects; optional extra outcomes require separate proven reservation. Source-manifest size or average diagnostic size cannot replace complete receipt accounting.

Conformance capacity witnesses: `bun docs/helix/04-build/evidence/design-audit/check-conformance-capacity.ts` reads the actual candidate and passes seven independently expected exact cases (empty, one, maximum, one-over, count alias, host number and huge exact count). Maximum reserve is 21528576 bytes. This checks conditional arithmetic/formula identity, not lossless producer ceilings, complete artifact/archive inventory or physical allocation.

Conformance result check: `bun docs/helix/04-build/evidence/design-audit/check-conformance-results.ts <Ajv Draft 2020-12 module path>` passes 13 run/assessment wrapper cases. It rejects unavailable receipts/cached pass, empty recovery, recorded-to-qualified promotion and qualification without assessment evidence. False original receipt/run claims deliberately pass shape and require actual issuer/run/manifest/assessor/native admission. This command executes no corpus or native runner.

Observer-layer cases allow an explicitly approved component-only control without fabricating a native observer, but refuse component substitution for required native state/journal/bypass/interchange/performance evidence. The exact approved qualification manifest fixes each evidence layer; caller manifest edits cannot downgrade it. Aggregate component passes qualify only their named scope and cannot fill a missing native matrix receipt.

Manifest check: `bun docs/helix/04-build/evidence/design-audit/check-conformance-manifest.ts <Ajv Draft 2020-12 module path>` passes 12 field/variant cases, refusing empty manifest, executable command, missing expected artifact, fabricated single-case second implementation and unknown observer layer. Duplicate IDs, unproven same implementation pair, component interchange and false coverage deliberately pass shape and require original approved manifest/independence/native admission refusal. No actual corpus or native observer is run.

Runner preparation cases retain the original returned recovery reference before run, lose run replies before/after original claim and reconcile without duplicate case/environment execution. A raw request or recovery string cannot replace prepared-run custody. Lost prepare reply proves no native/environment work was started, while lost run reply proves no outcome by itself. Strict consumers reject request-as-run and forged recovery-only prepared handles; native claim/containment still needs independent evidence.

Prepared-run cleanup/capacity cases race run claim with abandon, repeat original abandonment, fill prepared/active/retained/byte limits and reconcile saturated original work. Verify no acquired native run is freed by cleanup, lost replies never imply abandonment, definitive resource refusal does not later start when capacity frees, closed/unresolved records remain charged and stale reclaimed handles cannot recreate claims. Actual store/native/environment/allocator evidence is required beyond declaration shape.

Reconciliation-state cases observe prepared work without native/environment effects, explicitly start only the returned original handle, abandon it then prove observation/retained handles cannot reopen it. Missing/conflicting registry state cannot be guessed prepared/abandoned. Original run elapsed counters continue across lost replies/reconciliation; idle preparation stays charged in registry without automatic time expiry. Observe after asynchronous state changes must recheck original lineage before returning prepared authority.

Reconciliation evidence consumer controls reject abandoned observation with preparation alone and prepared observation carrying a receipt. Native/store schedules additionally substitute a closure from another request/generation and race closure observation with original run claim; exact original inventory/transition custody must detect them despite plausible artifact metadata.

Progress/finalization schedules fail between native registration and reply, observer completion and cleanup, and archive/receipt publication and delivery. Verify original ordered directions/fresh state, no duplicate native work, exact not_started versus unknown distinctions and complete surface projection. A callback return without observer/termination cannot pass; unknown native activity cannot become failed/not_run; lost receipt reply resolves original bytes without rerun. Compare exact lexical/presence/source/journal expectations after only admitted identity aliases.

Independence provenance scenarios reject two wrappers around one Truss core and a shared Truss codec reused as its own oracle. Record shared UMF/Weft/driver/runtime components without duplicating their owner implementations; qualify only their existing supported subsets and obtain independent native expectations for Truss-owned observations. A second language/process or high code-difference percentage cannot close provenance. Missing independent coverage for any mandatory selected observation blocks full interchange support.

## Original runner factory and retained tooling

| Planned case | Independent assertion |
| --- | --- |
| `runner_construction_is_inert` | A qualified original service/configuration constructs with zero prepare/run/reconcile/cleanup calls, artifact resolution, environment/native acquisition or worker start; importing tooling has the same zero-effect boundary |
| `runner_profile_correspondence_refuses` | Wrong original runner/resource/composition pins or missing original service recognition refuses construction before any service method, even when caller metadata claims trust |
| `runner_approvals_are_host_owned` | Empty/conflicting manifests/environment references refuse; claimant receipt/case cannot expand host-approved qualification inventory or select another executable/environment |
| `prepared_run_rechecks_actual_original_state` | Retained tooling repeats original generation/profile/authorization and exact approved request correspondence; a replacement service with matching names cannot acquire the old prepared run |
| `recovery_does_not_retarget_after_reconfiguration` | Original active/unresolved run reconciliation and cleanup remain in original issuer custody; new host setup cannot claim it or turn lost custody into abandonment |
| `tooling_preserves_host_lifetime` | No construction/assessment/disposal-like caller action shuts down the original runner/pool/environment or frees unknown native work; explicit original host shutdown follows admitted containment |

Strict consumer checks cover empty approvals, forged host runner, request-as-prepared-run, recovery-only forged handle, preparation-only abandonment and prepared receipt claims. Native/service scenarios still require actual original producer/recognition/store/resource profiles; function-shaped mocks establish only callback-count/declaration behavior. No runner factory pass qualifies corpus/native/interchange correctness.

Cancellation schedules abort before prepare, during artifact admission, before run claim, during writer/observer work and after receipt publication. Independently confirm no early native acquisition, exact stopped manifest projection, no active-unknown→not_run conversion, original committed evidence preservation and cleanup/reconciliation despite the still-aborted original signal. Wait cancellation cannot release original native resources or produce a passing receipt. Recorded all-not_run cancellation is a contained procedure receipt, not executed-case qualification.
