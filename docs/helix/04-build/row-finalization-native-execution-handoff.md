# Native row finalization execution handoff

This packet applies CONTRACT-001 RF01–RF06, original operation/context/group
custody, and its reserve/observe/seal/commit-check ordering. It supplies the next
native implementation and test sequence; it does not select missing security
APIs, qualify a complete install, or modify original private routine signatures.

## Phase ownership

| Phase | Required original producer | Mutation permitted |
| --- | --- | --- |
| Admission/reservation | Original four-family writer with admitted subject/connection/attempt, head/capacity exclusion and current context | Reserve before graph effects; no caller-issued authority |
| Write observation | Registered unavoidable actual state/node/scalar event under complete OLD/NEW/cascade prestate custody | Consume reservation, retain all contributors, advance dirty generation |
| Nonsealing final capture | Complete independently admitted state/definition/candidate observation under retained exclusions | Capture exact journal inputs; no seal or effects-ready assertion |
| Effects readiness | Native group producer after actual canonical/key/history/report effects and independent invariants | Original transaction-local group readiness; no commit acknowledgement |
| RF01–RF06 finalization | Protected finalizer with complete original contributor/group context and admitted codec | Seal the actual current generation only after all RF steps pass |
| Application finalization | Registered operation producer after all required scope seals | Record complete pending operation result; no externally committed success |
| Deferred commit closure | Installed `row_touch_commit_check` trigger | Verify complete current touch coverage, dirty/sealed equality, application finalization, reservations and selected validators; never create a missing seal |
| Settlement/publication | Original connection/attempt and qualified acknowledgement/reconciliation path | Publish committed result only with actual commit evidence; retain unknown outcomes |

Sealing cannot depend on seal-dependent application-finalized status. Journal
capture cannot require effects readiness before producing the journal input.
A failed/uncertain transaction cannot become committed from visible finalized
rows. Setting constraints immediate while unfinished must refuse; invocation
order and repeated checks cannot bypass closure or reset shared accounting.

## Implementation and independently expected tests

| Step | Implementation output | Required native evidence |
| --- | --- | --- |
| RF01 | Original subject/cut/owner/property association and expected version recheck | Wrong document/property/edge association, foreign context or stale generation refuses with no published effects |
| RF02 | Complete bounded collection by original owner/property tuple, then all state/node/payload membership; reserve before lookup/traversal allocation | Zero state under unavailable observation is not absence; duplicate owner/property state, extra/disconnected node, mixed identity and overflow refuse. A root-only walk is insufficient |
| RF03 | Full-ID lookup and bounded explicit reachability; exactly one parentless root equal to declared root; all same-state parents, every node visited once | Actual FK-admitted disconnected cycle from native67 refuses before seal; self-parent, orphan, extra root and depth/stack exhaustion refuse; original bytes restored by rollback |
| RF04 | Original definition graph/member ordering, required fields, allowed parent slots, collection bounds and complete unknown content | Duplicate literal keys/full field identities, sequence gap, missing required field, wrong child kind and dropped opaque/open content refuse |
| RF05 | Scalar/node parity plus original native codec/domain/source proof | All seven native families; selected physical columns; token/native numeric equality, finite/integral/facet boundaries; qualified timestamp precision/instant and original spelling; unsupported profile refuses |
| RF06 | Independent bidirectional complete reconstruction against admitted candidate and all key/history/report/group effects | Missing extra candidate/member/key/journal/report content refuses; equality of counts/digests alone cannot pass; failure restores full old value and dependent effects |

The existing Python tree check covers physical RF03 and parts of RF04/RF05.
The scalar-shape check covers only family-exclusive columns and retained carrier
presence. They are host components, not admitted original/native proof and not
complete logical reconstruction. Native69 retains their actual capture/cascade
composition; no all-RF native finalizer exists.

Implement each native body against the same admitted complete profile. Do not
wrap the private host checks in a boolean that grants native seal authority.
Resolve original codec guarantees with UMF semantics; missing native guarantees
retain engine-enforcement classification or refuse the affected capability.
Weft supplies lowering/comparator obligations, not row-finalization authority.

## Deferred check acceptance exit

After finalizer qualification, implement the registered deferred closure using
one complete actual-transaction operation/touch/reservation cohort. Preserve
noncontributors, deleted owners and every contributing operation; empty touched
scope still requires full cohort/context admission. Check original generation,
current dirty/sealed equality, complete application finalization and settled
reservations, then dispatch selected edge/feed validators under original custody.

Qualify unfinished admission, missing observer, dirty-after-seal, earlier-generation
seal, missing contributor, stale context, wrong target/event/OID/ACL/dependency,
early constraints, repeated invocation, overflow/cancellation and late failure.
Prove transaction containment with original driver settlement rather than treating
an exception as rollback. Full canonical/key/journal/feed/receipt state must agree
in the same transaction. Native table counts or private component tests cannot
establish this exit.

## Dependencies and delivery

PA01–PA04 require the security owner's closed authenticated-person/connection,
complete authority/context and freshness/publication contracts. The handoff
request remains unsent pending explicit destination/payload approval. Truss can
prepare original source/expected-negative fixtures and implementation algorithms
without inventing those interfaces. All seven original semantic routines still
need exact native body, identity, role/ACL, dependency and qualification artifacts.

Package these original inputs through the complete installer and independent
verifier. The corrected private pgserver16.15 tuple remains unpublished; Aurora
and Lakebase require their own exact installed qualification. Complete migration
source/target qualification and preservation/recovery preparation runs alongside
installation, not as a prerequisite for first usable Python operations.


## Actual RLS valid-prefix counterexample

[Native70](evidence/design-audit/row-image-visibility-native.json) installs two
explicit fixture SELECT policies on original node/scalar tables. A separate
connecting role has schema/table rights and fixture-only helper EXECUTE. The
policies hide node614 and its decimal payload from state501. The administrator's
original snapshot contains8 images; the reader's actual repeatable-read capture
contains6 images with original native descriptor/completion. Capture framing,
physical tree validation and scalar carrier shape all pass. The omitted sequence
member was last, so visible ordinals remain contiguous. The receipt retains the
two exact hidden original images and confirms completeScopeQualified=false.
The existing nested/cycle/cascade restoration checks also pass.

RF02 must therefore consume original complete-scope integrity observation under
the qualified native role/security profile, independently of caller disclosure.
Count/byte preflight over visible rows and SELECT completion prove only that
returned set. Even a valid visible tree can omit canonical members. No host
visible result may become full replacement, journal image or seal authority from
these checks alone. Full scope cannot be inferred from root existence, remaining
contiguous ordinals or caller claims that the SELECT succeeded.

Qualification must exercise RLS-enabled and selected FORCE-RLS/role profiles,
hidden last/interior members and complete absent-state observation under the
original policy/cut. The owner must supply authenticated-person/current-authority
and integrity/disclosure separation; Truss binds actual native roles/dependencies
and same-transaction custody. Do not grant blanket helper EXECUTE or disable RLS
for application reads as a fix. This probe's broad grants/policies are solely
fixture inputs, not an adopted security resolver or R4/R5 implementation.
