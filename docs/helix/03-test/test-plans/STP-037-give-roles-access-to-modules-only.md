---
ddx:
  id: STP-037
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-037
      kind: informed_by
    - id: TD-037
      kind: informed_by
    - id: SD-008
      kind: informed_by
---

# STP-037: Module isolation

## Story Reference and Scope

US-037, TD-037, SD-008, TP-001 and CONTRACT-005/007. Tests are planned. Direct native attacks and complete visibility sets qualify a concrete policy profile.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-037-AC1 | `sales_writer_reads_exact_authorized_sets` | Only authorized objects/edges/keys/journal/tombstones/catalog appear through direct SQL; source lookup obeys policy | `@covers US-037-AC1` | Native integration | protected relation matrix |
| US-037-AC2 | `cross_module_write_cannot_change_billing` | Unauthorized INSERT/UPDATE/DELETE has no effects and returns qualified refusal/hidden-row outcome | `@covers US-037-AC2` | Native integration | cross-module native writes |
| US-037-AC3 | `module_reader_cannot_mutate` | Reader cannot mutate canonical/derived/audit data under declared grants/policies | `@covers US-037-AC3` | Native integration | reader role matrix |
| US-037-AC4 | `unassigned_role_reads_empty_sets` | SELECT-capable no-module principal sees no protected rows | `@covers US-037-AC4` | Native integration | granted SELECT with no module assignment |
| US-037-AC5 | `non_superuser_definer_uses_acting_role` | Definer reads preserve caller module view despite a different owner role | `@covers US-037-AC5` | Native integration | FORCE RLS, fixed search path and local role |
| US-037-AC6 | `paired_policy_read_cost_meets_bound` | At 1,000 types/10 modules incremental agreed policy statistic is at most 0.01 ms | `@covers US-037-AC6` | Performance integration | matched reads with role already set |

## Data and Failure Probes

### Document-qualified policy candidate

For CONTRACT-005's proposed `truss-qualified-module-policy/0.1.0`, build independent documents A and B with the same module `sales` and distinct retained ownership. Give one ordinary role A-only read/write authority. Under US-037-AC1/AC2/AC4, prove B's objects/keys/catalog/history/source facts remain hidden or denied through direct, joined and public toolkit paths, despite equal module/element display names. A relationship declared in a third document and endpoints in A/B requires all three qualified owner permissions; adding only its module-name grant must not disclose the edge. Give A and B separate readers/writers and compare complete expected sets after individual grant changes.

The qualified helper must select only its exact document/module row. Wrong/missing document, old two-argument helper path, substituted owner mapping and ambiguous legacy grant conversion cannot broaden access or create an inferred grant. Test full-byte identity distinctions under the selected native collation profile, including case and NFC/NFD spellings admitted by the original source profile. Populated conversion failure/rollback preserves original grants and policies; successful atomic activation does not expose an intermediate mixed-owner policy. Revoke one qualified grant while a retained snapshot/replay/old historical context exists and require the existing current-authority protocol. These are planned candidate tests with the same criterion citations as their primary tests, not evidence that baseline 0.2 supports qualified grants. Exact owner-home/policy DDL and migration/native authority profiles remain gates.

Use independent expected sets over all protected tables. Native command file planned as `tests/host/module-policy.test.ts`; performance file `tests/performance/module-policy.test.ts`. Include relationship module distinct from endpoint modules, historical deleted edge/source facts, hidden keys, direct type/endpoint reassignment and rollback. Verify table owners and bypass flags; superuser is a control outside the promised boundary. AC4 must return empty results rather than fail SELECT privilege. Definer test uses non-superuser owner and proves effective caller role independently.

## Recovery custody/disclosure supplements

Retain an unresolved obligation, revoke the original module grant, then reconcile through the host registry without disclosing archived input/result to that caller. A reference or administrator inspection is not a grant. Check retained owner-union admission for deleted/rebound records; missing ownership refuses disclosure. Reject executor authentication/reusable resource handles in portable envelope fields. A permitted authored string resembling a connection URI or token must retain exact bytes in protected evidence without heuristic redaction; disclosure still needs current grants. A retention profile unable to preserve required exact evidence refuses before native submission. Independently prove internal containment can finish without revealing original data.

## Executable Proof and Handoff

Future commands `bun test tests/host/module-policy.test.ts` and `bun test tests/performance/module-policy.test.ts` require implemented harness and finalized policy matrix. Pin bundle/server/adapter/grants/FORCE/search-path, retain raw visibility/refusal and timing evidence. Hidden-write outcomes now follow CONTRACT-005; resolve indirect history disclosure and timing statistic before acceptance. All six criteria block closeout. FK/unique existence disclosure is separately reported, not claimed eliminated.

## Native denial controls

For an unauthorized billing INSERT, assert the applicable grant/WITH CHECK refusal and zero effects. For UPDATE/DELETE selecting a hidden billing row, assert zero RETURNING rows and unchanged independent observer state; library outcome is not_found without an elevated existence probe. For visible sales row retargeted to billing, assert WITH CHECK refusal. Distinguish these paths from stale-version handling on an authorized visible row. Native SQLSTATE alone cannot establish no mutation or satisfy the complete denied-write matrix.


## Protected integrity observer qualification

Planned native controls for CONTRACT-005's observer-role candidate use independently installed hidden and visible collision members, exact original acting roles and separately inspected native role/policy/helper catalogs. The ordinary application cannot read hidden records, call an observer helper or inherit/SET ROLE to the observer through direct or indirect membership. The registered protected procedure sees every required hidden integrity member privately, but exposes only the authorized public outcome. Observer SELECT authority cannot authorize writes or migration inventory/result disclosure.

Add a restrictive policy that filters one hidden member: preparation/admission must reject the incomplete observer composition, rather than claim no conflict or silently change the host policy. Test FORCE RLS with a non-superuser/non-BYPASSRLS observer and actual nested definer owners. Verify original acting role survives the chain and current_user changes only for internal execution; supplying another role name never grants authority.

Inject PUBLIC/default helper grants, an inherited owner/helper execution path, SET ROLE membership, writable resolution schema, temporary relation/type shadowing and replaced helper body/owner. Each invalidates exact composition before new effects/disclosure. Inspect publication from another ordinary session across deployment commit/rollback; no callable PUBLIC exposure may exist. Withhold observer SELECT on one required store and require unavailable complete inspection, not a partial pass. Native observer output faults must retain original containment/recovery custody without hidden payload in public diagnostics.

These are additional planned tests, not baseline policy-check evidence. Exact physical helpers and native implementation are still missing; this test plan does not qualify the candidate.

## Acting-role reset and version qualification

For US-037-AC5, pin the exact server patch release and vendor build. PostgreSQL's [CVE-2024-10978 advisory](https://www.postgresql.org/support/security/CVE-2024-10978/) documents incorrect identity after SET ROLE or SET SESSION AUTHORIZATION, including queries using current_setting('role'); upstream PostgreSQL 17.0 is affected and 17.1 contains the correction. A vendor backport needs its own documented provenance. This prerequisite does not qualify a complete server/adapter/policy profile or select support for older major versions.

The planned `acting_role_reset_matrix_preserves_caller` test cites `@covers US-037-AC5`. Independently establish expected caller identity and exact visible row sets for no SET ROLE, SET LOCAL ROLE, session SET ROLE, RESET ROLE and separately authorized SET SESSION AUTHORIZATION. Repeat role changes around savepoint rollback, whole-transaction rollback and commit, using prepared and unprepared statements through the admitted connection/pool profile. Include nested non-superuser definer owners, quoted mixed-case role names and two consecutive invocations with different callers. Each helper return must match the independently established current caller; no prior return or inner definer owner may supply authority for a later call. Unsupported or empty native role context must refuse before effects or disclosure. Session-setting cases are explicit test fixtures, not permission for the toolkit to alter host session state.

Retain the original role and unresolved attempt evidence when a later caller reconciles recovery. Prove current authorization governs disclosure without rewriting the original attempt's identity. Record server patch/build, role transitions, statement preparation mode, actual helper owner/search path and independent observer results. These schedules remain planned; source inspection and the advisory establish neither native caller correctness nor pooler support.


## Installed raw role-graph controls (planned)

Run CONTRACT-011's proposed role-graph capture through the independently admitted administrative observer. Seed inheritance-only, SET-only, ADMIN-only and independently granted memberships; retain each grantor and option separately. A graph edge cannot certify all three capabilities. Independently establish writer/observer identities and effective native rights; the observer's session/current role must never replace the data caller inside a definer helper. Prove no password/configuration content is captured or logged, and no private role graph reaches public read/error callbacks.

Exact role/member ceilings succeed only when all other independent bounds fit; one-over produces whole-graph unavailability with charged overflow rows. Truncated JSON/native completion, duplicate IDs, unresolved role/member/grantor references and unregistered server catalog versions cannot normalize into empty or partial closure. Independently inspect raw carrier/parser/tree/correlation copies and native aggregation/work limits. Race role changes between this statement and relation/routine/ACL capture, including ABA changes with equal pre/post digests; absent complete administrative serialization, the inventory is unstable_observation. These tests are planned; source parsing does not qualify effective privileges or cluster-wide coherence.


Role normalization controls seed distinct grantors for the same member/granted role. The normalized inventory retains one entry per original membership, unchanged admin/inherit/set booleans and exact grantor names; an OR-merged or grantor-less representation refuses the proposed profile. Native OID reassignment with identical resolved names/facts must leave the existing bootstrap policy-meaning basis equal, while a grantor-only change is drift. Independently count raw-to-normalized correspondence and reject duplicate/omitted entries, unresolved grantors, name collisions and later-snapshot name resolution. Vary raw row order and non-ASCII/case-distinct names; expected normalized order is unsigned UTF-8 byte order without Unicode normalization. Raw source custody remains required despite exclusion of volatile OIDs/observer evidence from the stable basis. These are planned semantic/native controls, not qualification from declaration compilation.


Conditional separate-report privilege controls use an acceptance touching two independently owned documents, relationship endpoints and a previously retained rebind owner. A caller with only one document's authority cannot read raw report bytes, discover hidden event/owner counts or obtain a trimmed report labeled complete. Independently inspect direct column grants, inherited/SET paths, PUBLIC execution and overloaded helper identities. Attempt report insertion/rewrite/delete/TRUNCATE, positive parent without report, arbitrary-byte helper writes and head publication before completeness. Each advertised database guarantee requires its actual unavoidable native denial; missing guard remains engine/none. Protected read-owner authority cannot be used as acting-caller authority or integrity-observer access. Revocation/held-snapshot and missing original owner/source tests follow the existing coordinator/recovery protocols. These are planned tests for the unadopted storage option.


Baseline report disclosure controls grant table SELECT while revoking report-column SELECT as an intentionally unsafe negative setup. Independent effective-privilege inspection must still detect raw report access; column ACL appearance cannot qualify protection. Repeat through inherited/SET/PUBLIC and view/helper paths. Qualified metadata-only access must not disclose schema_rev.report or sensitive original origin/source content, and one visible document/revision cannot authorize the complete affected owner union. Test both baseline and any separately adopted report home without treating old JSONB rendering as exact original report-byte custody. These planned native controls qualify the selected actual grant/policy paths, not source SQL alone.

Embedding role-state controls use a host connection whose current role differs from session_user and whose connection-time RESET role differs from both. Ordinary Truss success/failure must preserve the original role/settings without emitting role-switch/reset commands. Independently verify qualified native definer return, cancellation, savepoint rollback and uncertain containment. Host role change during a call invalidates custody and disclosure. A successful RESET ROLE or SET ROLE NONE with the wrong final role cannot prove restoration. SET ROLE must not be assumed to load target login settings. Direct and transaction-pooler profiles require separate native evidence; cases remain planned.

Consume CONTRACT-011’s eleven independent installed-policy comparison fragments as literal expectations; do not generate their expected outcomes by the production comparator. Supplement each fragment with a complete independently selected native inventory/cut and original callers before claiming installed qualification. Reordered grants preserve multiset meaning; repeated tuples retain multiplicity. Missing denied pairs are unavailable, whereas a complete all-false matrix admits an empty positive projection. Changed native OIDs alone are not stable meaning changes but require original coherence; same OID with renamed schema is drift. Cases are planned.

RLS policy role normalization distinguishes native polroles zero from a real role named public. Reject the old string-only projection, unresolved native roles and unsupported empty applicability. Compare reordered applicability principals as tagged sets while retaining original native array order/multiplicity privately; grant tuple multiset semantics do not apply to RLS applicability. Independently exercise actual RLS combination/actor behavior and policy expression meaning. Native tests remain planned.

RLS command/expression controls independently map all five original polcmd codes and refuse unknown codes. Preserve NULL versus explicit true and absent WITH CHECK versus explicit USING copy. Exercise ALL/UPDATE fallback, INSERT without USING, SELECT/DELETE without WITH CHECK, no applicable policy, restrictive-only policy sets and changed rowSecurity/forceRowSecurity. Same policy names on different relations stay distinct. Actual native expected rows/write rejection are authored independently; deparse/text or declaration checks cannot qualify expression semantics. Cases remain planned.

Policy expression capture controls seed NULL, explicit true, column Vars, external functions/operators, quoted identifiers and collation-sensitive expressions. Native tree/deparse must share the exact original relation/cut; wrong relation context, failed/truncated deparse or unresolved dependency refuses. Change observer search_path and referenced definition while retaining similar display text; equal text cannot certify unchanged native meaning. No captured expression is executed by the observer. Complete bounded native deparse/tree admission remains planned.

Policy definition-artifact tests refuse text-only projections and shape-valid unknown definition profiles. Independently vary referenced function/operator/type meaning while retaining equal deparse text, and require complete definition/current-cut refusal or drift. Bootstrap policy rows and physical entries require bidirectional exact relation/name/profile/definition correspondence; a producer-generated self-hash without original native evidence cannot admit. Standalone policy comparison uses the same native definition admission. These are planned semantic/native tests.

### Feed authority separation acceptance

Use CONTRACT-005's six feed responsibilities under an independently selected installed role/grant/helper profile. Native actor IDs, effective membership/SET ROLE paths, routine security/search_path/dependencies and relation/column grants are inspected independently; labels below are fixture roles, not production names or serialized authority. Capture every public output/log/progress callback and keep original helper observation private.

| Case | Actor and independently attempted path | Required result |
| --- | --- | --- |
| FP01 | Ordinary application caller attempts direct INSERT/UPDATE/DELETE on each of four feed stores, including column-specific counter/ordinal/manifest access | Protected profile denies each bypass; no admitted graph/feed effect or hidden original payload is disclosed |
| FP02 | Writer attempts finalization or deletion of a committed predecessor using matching context/identity text | Native original producing-context/role admission refuses; ordinary module grants and same names cannot authorize historical mutation |
| FP03 | Validation actor attempts registration/finalization/retention or a repair write through a nested helper | Native separation refuses; independently observe attempted repair and dependency call paths, not only rolled-back final state |
| FP04 | Retention actor attempts current producer registration/finalization; producer actor attempts settled deletion | Cross-responsibility calls refuse; legitimate original protected cohort cleanup remains a separate positive control |
| FP05 | Ordinary caller reaches a private validator/observer through indirect role membership, SET ROLE, broad function execution or alias routine | Any effective bypass invalidates profile adoption; hiding the named primary entrypoint alone is insufficient |
| FP06 | Internal validator sees complete hidden/deleted-owner evidence while the actual data caller lacks the full retained owner union | Integrity proof remains complete, but no provisional originals/counts/digests or fabricated complete feed reach caller output/log/callback; downstream acknowledgment is withheld |
| FP07 | Ordinary caller attempts trigger disabling, routine owner/dependency replacement or admitted replication-setting bypass | Profile denies or invalidates the changed native authority before subsequent support/publication; privileged administration follows separate original coordination |
| FP08 | Independently qualified registration, finalization, validation, public read and retention paths under their rightful original contexts | Each permitted action succeeds with its exact expected effects/disclosure and original caller capture; a configuration that denies every path cannot pass functional qualification |

All refusal cases preserve actual native submission/completion and original containment classification. Native error/unknown completion cannot be flattened into proven effect-free refusal, and read-only integrity visibility does not prove public disclosure authority. Repeat effective grant tests after original role/policy change through the admitted current-authority coordinator. These eight cases supplement US-037's existing criteria and STP-041 feed semantics; they remain not_run until the native helper/role/profile and independent fixture instrumentation are implemented.

### Observer reachability and wrapper controls

Independently author ordinary/observer/writer/intermediate-role graphs. Vary INHERIT, SET and ADMIN options separately, including cycles, a non-login intermediate, a denied direct edge with an admitted indirect path, and delegation that can grant observer access after initially clean membership. Original complete admission must reject every effective ordinary-role escape under the selected native semantics; a missing edge or unknown option cannot become no path. Pin actual native option behavior rather than treating all edges identically.

Grant observer-helper EXECUTE through PUBLIC, an inherited intermediate role, a grant option or a public wrapper that returns hidden facts: each invalidates the protected profile. Include wrong overload/body/dependency substitution and ownership/policy changes after a retained readiness observation. A positive graph preserves only exact private writer-helper invocation and complete current-authority closure. Overbound/truncated role or helper fanout refuses before observer data collection; no-path results require complete original membership, not equal counts. Native bypass/disclosure and original bounded producers remain mandatory qualifications.

For the PG17 static closure controls, switch login→intermediate via SET TRUE, then inherit intermediate→observer via INHERIT TRUE/SET FALSE: observer object privileges remain an escape. Reverse the options to distinguish role-switch permission from inherited privilege. A mixed INHERIT-then-SET path cannot independently authorize SET from a different current role; original session-user SET closure stays authoritative. Validate actual active-role correspondence separately. Synthetic cyclic membership or PUBLIC membership refuses the PG17 candidate before protected observation; use these only as corrupt input controls, since native PG17 disallows them. Special role attributes require active/switchable-role inspection and are not added by ordinary INHERIT closure.

Protected-owner controls grant an ordinary actor INHERIT TRUE/SET FALSE membership in a helper-owner role, or access to the owner of a required dependency. Despite no direct observer path and revoked EXECUTE, the selected profile must reject inherited definition/implicit grant authority. Separately exercise actual native role ADMIN and object grant-option permissions, grantor provenance and membership-option modification under isolated administrative fixtures. A later grant to self or wrapper dependency replacement cannot be reported as a safe unchanged observer profile. Positive admission contains complete original owners/grantors/options and no ordinary mutation/delegation path. The static graph experiment is not expected to certify these ownership/delegation cases.

## Combined private routine security boundary

SG-01–SG-05 consume CONTRACT-005’s eight-field binding and the [known routine worklist](../../02-design/contracts/reference-routine-security-worklist.proposal.json). All are `not_run`. The sixteen known entries seed the fixture; the independent native installer inventory must additionally include all admitted operation/public/administrative/transitive callables. A successful sixteen-entry check cannot establish complete coverage.

| Case | Independent setup and observations | Required behavior |
| --- | --- | --- |
| SG-01 / `effective_membership_cannot_reach_private_surface` | Separate actual application and internal roles; independently collect direct, inherited, SET and admin membership paths plus exact overload EXECUTE rights. Inject broad role membership, PUBLIC/default helper grants and a same-name alternate overload one at a time. | Selected admission refuses the incompatible role/callable tuple before application work. Private reserve/seal/phase/cleanup entrypoints cannot be reached through direct calls or elevated arbitrary-byte wrappers. A nonlogin owner alone does not prove separation. |
| SG-02 / `complete_transitive_body_privileges` | Inspect the complete selected body call graph and relation/column/sequence/operator/type/collation dependencies. Add one reachable helper outside the allowed responsibility, and separately omit its dependency from the claimed inventory. | Both actual privilege expansion and missing inventory prevent readiness. No body may gain reset, canonical mutation, private disclosure or stage deletion authority merely through an indirect helper. Exact native dependency/effective-right observations are required; a manifest label is not proof. |
| SG-03 / `original_actor_survives_nested_definers` | Use an application actor lacking one required module grant while nested definer owners have broad integrity visibility. Trace original actor custody through admission, transition/final observation, append and read/report disclosure. | Private integrity collection may use admitted scope, but cannot substitute routine owner authority for the original actor or disclose forbidden facts. A copied context with a different actor refuses; authorized integrity observation cannot turn hidden data into public absence or success. |
| SG-04 / `cleanup_and_publication_cannot_repair_each_other` | At a frozen phase and during unresolved host settlement, attempt stage deletion through producer authority, phase re-execution through cleanup authority, parent sealing through journal authority and sequence reset through reservation authority. | Each path refuses without clearing original obligations, replaying publication or changing the original unknown outcome. Confirmed qualified cleanup remains possible after full settlement/retention discharge under its separate original administrative path. |
| SG-05 / `administrative_drift_invalidates_complete_readiness` | Under explicit isolated administrator custody, change an owner, grant, membership, namespace resolution or transitive callable after a coherent installation observation. Invoke a retained facade and independently inspect the new native facts. | Affected readiness is invalidated and dependent work refuses until a fresh complete profile is admitted. No automatic repair, cached role-name comparison or source hash alone restores readiness. Existing committed receipts/history and unresolved operation custody retain original meaning. |

Record actual role attributes/memberships, exact callable identities/signatures, body hashes, transitive dependency observations and denied effect traces. Keep raw private facts confined to the conformance assessor; application diagnostics obey current disclosure. Role/DDL administrative bypass is separately classified and cannot be counted as ordinary writer enforcement. Native evidence must retain the original selected tuple and independent expected access decisions for every source owner.
