---
ddx:
  id: STP-030
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-030
      kind: informed_by
    - id: TD-030
      kind: informed_by
    - id: SD-008
      kind: informed_by
---

# STP-030: Host extensions

## Story Reference

US-030, TD-030, SD-008, TP-001 and CONTRACT-001/002/005/007/008. Tests are planned.

## Scope and Objective

Prove named host-extension coexistence, actual policy visibility and forbidden layout drift detection.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-030-AC1 | `host_extension_preserves_required_corpus` | Trusted ledger/function/role/trigger profile preserves all selected normative corpus outcomes and atomic host effects | `@covers US-030-AC1` | Native integration | `tests/host/extensions.test.ts`; disposable extension profile |
| US-030-AC2 | `forced_rls_covers_direct_and_joined_reads` | Ordinary roles see only policy-allowed object/key/edge state through every qualified read path | `@covers US-030-AC2` | Native integration | Same file; explicit role/path matrix |
| US-030-AC3 | `canonical_layout_alteration_is_detected` | Add/drop/alter column or constraint causes contract/layout mismatch; no automatic repair | `@covers US-030-AC3` | Native integration | Same file; independent inventory and isolated corruptions |

## Executable Proof

Future command `bun test tests/host/extensions.test.ts` requires harness/files. Each test cites ID and pins server/layout/extension/role/journal profile. Full corpus case counts are retained; missing required cases prevent coexistence claim.

## Data and Setup

Host and canonical inventories are separate. Independent observer checks ledger, canonical/derived/journal and policy-filtered results. Run as ordinary roles, not owner. Trigger failure and caller rollback prove atomicity. Corruption fixtures use disposable namespaces.

## Edge Cases and Failure Modes

Reference assembly construction/lifetime supplements: instrument a host executor and prove construction makes zero native calls; malformed/duplicate/contradictory selections refuse before I/O. Mutating the caller's configuration object afterward cannot retarget the assembly. Undeclared readiness selection refuses, and disposal closes new admission before awaiting in-flight work. Cancel disposal waiting, reconcile through the same recovery registry and repeat disposal without reopening admission. Unknown native completion/release yields quarantined with nonempty references; confirmed owned cleanup yields disposed. Independent host observers prove no host connection/pool/adopted transaction/exported snapshot was ended by either path. Readiness after disposal initiates no native work. These supplement B-014's assembly contract and do not replace US-030's extension criteria.

Readiness admission must reject a qualification receipt for a different installation/profile tuple, missing required cases or a forged current-inventory reference. Test bootstrap against a coherently observed fresh namespace separately from mutation against an installed namespace; fresh readiness cannot authorize writes. Change one guarded dependency and require all affected capabilities unavailable, retaining unrelated independent observations only when the dependency profile proves separation. A readiness record cannot replace current-authority or transaction-liveness checks.

Reference-assembly lifetime probes: construction emits no SQL or service startup; missing installation stays unverified/unavailable rather than auto-bootstrap; drift withdraws only affected named capability readiness. Dispose during an adopted transaction and verify host connection/transaction remain usable and uncommitted. Dispose during uncertain owned native work and require quarantine rather than resource reuse. Run a packaged independent consumer without Weft registration, then add a registered backend separately. Host shutdown policy cannot become an implicit library commit/rollback path.

Definer identity/search path, hidden FK/unique errors, direct key access, trigger ordering and arbitrary host locks. Policy bypass powers are excluded from ordinary-role qualification. Unknown extensions require explicit new evidence; supported named profile never implies universal trigger safety.

Namespace-observation recovery witnesses run readiness against an empty namespace with no fabricated installation/epoch, then interrupt an in-flight metadata query and require a resolvable quarantine obligation. A matching marker observed later leaves the original namespace-observation context immutable. Reject mutation/DDL through that context and cross-schema executor substitution before SQL. A subsequent write needs a separately admitted installed context and current authority. A read-only intent or cancelled Promise cannot itself confirm native termination.

Assembly-identity witnesses use two simultaneously active instances against one target: distinct IDs preserve independent obligation inventories, and a deliberately reused attempt ID with changed evidence refuses before the second submission. Repeated identical registration may return the same reference but cannot cause repeated native execution. Mutating the caller's assemblyId afterward cannot change captured identity. New-instance disposal cannot resolve, release or erase the old instance's quarantine by sharing a target or configuration digest. Restart reconciliation resolves original evidence independently of recreating an assembly.

## Bound direct-read facade supplements

Obtain a configured handle with zero registry/SQL calls, then independently test unsupported selection and closed admission. Retain a handle across disposal and require execution_obligation without native submission. Use foreign executor transactions, stale profiles, unverified installation and expired snapshot/stage contexts: each refuses before payload disclosure. An adopted successful read does not commit its transaction. Direct lookup/pages/catalog/traversal work without compiler registration. A structurally matching handle or readiness result cannot discharge native/authority obligations.

## Build Handoff

Observation-admission fixtures preserve a registry record while independently forging its confirmed flags, evidence digest, profile digest, attempt/resource identity or predecessor. Each remains unresolved and cannot release quarantine. A genuine commit receipt without exact native termination/release evidence also stays quarantined. Check a valid complete termination/release witness separately, then remove its verifier registration and require unavailable rather than accepting stored flags. A storage-success result cannot qualify native evidence authenticity.

Ownership-inventory fixtures instrument each CONTRACT-007 resource class independently. An inert assembly disposes with no native resources. After native submission, dropping bookkeeping cannot produce an empty inventory/disposed result while termination remains unknown. Retire private undisclosed buffers without publishing them, preserve host pools/transactions/registry/compiler and apply creator-specific snapshot/authority/stage release protocols. An extension introducing an unregistered resource refuses activation. For each assembly-owned resource, independently observe confirmed release or an exact retained unresolved obligation; a generic cancellation/cache-clear counter is insufficient.

Registry negotiation fixtures vary one of identity/version/digest/retention at a time and require incompatible_selection with zero registry/native calls. A declared restart-durable configuration paired with a process-lifetime registry refuses. Mutate host metadata after construction: the assembly cannot adopt replacement pins or rewrite existing obligations. Metadata agreement followed by registration unavailable remains unavailable, never a durability pass.

Registry identity/concurrency witnesses: identical registration returns the original reference, changed target/evidence conflicts, two appends against the same prior observation permit at most one distinct successor, and changed evidence under a reused observation ID conflicts. Confirmed native termination cannot regress to unknown; a host-owned resource label with unknown termination stays quarantined. Construction calls none of the host registry methods, and disposal never clears it.

Recovery-registry supplements: reject work before native submission when obligation registration fails; destroy the assembly's local cache and independently resolve its quarantine reference through the host registry. Substitute another target/installation reference and refuse it. Simulate registry outage after submission, cancelled disposal waiting and expiry pressure: retain unresolved evidence and quarantine in all three cases. A durability-only observation cannot release a resource with unknown native termination. Check immutable original evidence plus appended observations, authority-filtered lookup and the exact declared process-local/restart retention subset. The host remains the sole authority for ending adopted transactions. These cases qualify the selected registry profile rather than asserting every registry is durable.

Assembly shutdown controls distinguish a completed adopted operation with pending host durability (disposal may finish while the host transaction remains active) from an in-flight native statement with unconfirmed termination (quarantine/reconcile). Verify both through an independent host observer. Retain original-attempt evidence/recovery registry ownership after disposal; dropping an assembly cache cannot erase uncertain work. Construction error fixtures use invalid configuration/profile/selection diagnostics and never execution retry/commit-unknown codes. Negative declaration examples establish only these type distinctions; native host lifetime remains qualification work.

Define exact profiles, write red native cases, reuse corpus/comparator and qualify role/transaction behavior. All criteria block named-profile closeout. Production DDL and policy migrations remain separately authorized work.

## Bound compiled-execution facade supplements

Select a retained compiled-execution handle without loading or invoking a compiler. Pass a registered exact artifact through the pinned bridge and independently verify decoded ordered aliases, exact numerics and absent/null distinctions. Wrong family, blocked/untrusted artifact, stale model/mapping/codec, unknown required obligation, foreign/ended scope and disposal must submit no artifact SQL. Repeat on a qualified read-only held snapshot with current-authority checks. Host commit/rollback and compiler lifetime remain host-owned. Oversized/malformed outputs cannot return partial success; native cancellation must preserve quarantine rather than claim a semantic refusal proved termination. Diagnostic probes check hidden-context disclosure independently of artifact shape.


## Concrete host ledger fixture proposal

[host-ledger-extension-v0.1.proposal.sql](host-ledger-extension-v0.1.proposal.sql) supplies the named test-only extension for US-030-AC1. It targets the exact disposable truss-layout 0.2 object/edge homes; other layouts require separate source correspondence, not textual SQL replacement. A dedicated non-superuser host owner owns the schema, ledger/control tables, identity sequence and definer function. The admitted fixture installer obtains separately authorized trigger-creation rights. Independently capture actual owners, effective ordinary-role rights, PUBLIC/default grants, inherited/SET paths, trusted search path and trigger inventory; source REVOKEs alone do not establish that the ordinary writer cannot read/tamper with the ledger or enable failure. Fixture setup is an explicit harness operation, never toolkit construction or mutation-side installation.

The AFTER row triggers insert one physical-change observation for every actual object/edge INSERT/UPDATE/DELETE. Before/after native JSONB is diagnostic native row content, not an exact authored-value transport, HistoricalRecord or Truss event. Physical effects and semantic events have independently expected counts; do not assume a single graph operation, group or catalog acceptance produces one ledger entry. producing_xid is native transaction correlation only, not a commit receipt or caller identity. Ledger identity gaps after rollback are allowed and are not committed host effects. No trigger increments canonical ver/updated_at, writes the Truss journal, creates canonical keys or changes current policy. Engine/trigger journal profiles retain their existing single-producer requirements.

Run the complete selected normative corpus before and after installation with independent expected canonical/journal/source/read results. Separately inspect committed ledger before/after rows as the private independent observer. Test create/update/delete for both homes, multi-record groups and caller-owned pending transactions. Before host commit, successful trigger execution proves only pending rows; after confirmed commit the independent observer checks actual durability. Caller rollback and injected trigger failure must leave both canonical effects and ledger inserts absent. Read/public error paths expose neither hidden ledger content nor control state. Missing/corrupted singleton control refuses by trigger failure rather than silently disabling capture.

Enable fail_writes through an explicit fixture-administrator transaction completed before the tested call. Record that control state as the test input; do not change it concurrently and assume a deterministic injection point. Test a mutation/group that would otherwise pass and independently verify original rollback/recovery, journal mode and host effects. For unresolved transport/commit, preserve CONTRACT-007 uncertainty until the actual independent observer/original recovery protocol resolves it; lack of a reply is not rollback evidence. Restore the control only through harness administration.

Coexistence qualification covers only this exact installed extension/profile and complete selected corpus. The ledger stores private native row images and must remain under host-owned retention/access controls; the toolkit neither discovers nor manages it. The fixture has no universal bounded retention/performance guarantee. Disposal cannot remove its triggers or tables; explicit authorized harness teardown occurs after all original transactions/recovery contexts are resolved. No production installation, native function compilation or coexistence run has occurred from authoring this source.


The fixture's AFTER-trigger NULL return and raised-error behavior follow [PostgreSQL 17 trigger-function semantics](https://www.postgresql.org/docs/17/plpgsql-trigger.html). The [separate source receipt](../../04-build/evidence/design-audit/host-ledger-extension-source.json) passes owner parsing/archive/document reload/stable export; it does not compile the PLpgSQL body or execute native fixtures, and does not change the seventeen-draft receipt scope.


Fixture invocation controls attach the same function as an unauthorized BEFORE row trigger, statement trigger or argument-bearing trigger in separate disposable negative setups. The function must raise unsupported invocation before any ledger write; a BEFORE NULL return must never silently suppress canonical changes. Inventory comparison independently rejects these altered trigger definitions. The supported fixture remains exactly AFTER ROW, zero arguments, object/edge and INSERT/UPDATE/DELETE. Each negative run restores the original independently inspected trigger inventory before coexistence tests resume.

TRUNCATE is outside this row-ledger projection: zero ledger rows cannot prove it caused no changes. Independently test actual ordinary-writer TRUNCATE rights and denial through every admitted role path against the canonical profile. Host row-trigger qualification does not fill a missing canonical guard or authorize an unaudited relation-wide mutation. Administrative teardown remains separate from ordinary mutation/journal semantics.


Compiled execution custody supplements: pause an independently controlled provenance callback after bounded original request capture. Mutate the caller's artifact/profile containers and separately replace SQL/descriptors/obligations in a caller-owned decoded cache before callback completion and before native submission. Require exact originally admitted bytes throughout or refusal; substituted content cannot execute. Return valid provenance evidence for a different artifact with identical SQL text and require refusal before submission. Exhaust original capture/copy limits and inspect zero SQL submissions. Independently change current catalog/authority while paused and exercise the existing native context admission separately from byte custody. Original executed result identity, decoding and scan-obligation evidence must reference the admitted artifact, not the later caller value. These planned native/packed-consumer controls add no Weft API and remain not_run.


Compiled refusal-stage controls: compare invalid provenance before SQL submission with malformed carrier/output descriptor after confirmed command completion, and with a lost command-termination observation. Independently count original submissions and observe executor/transaction state; the same domain reason cannot imply zero submissions. Confirmed post-command publication refusal returns no partial result and never ends an adopted host transaction. Unknown termination/containment follows the original outer execution failure/recovery protocol and retains quarantine, without arbitrary commit_unknown classification or automatic retry. A transaction-fatal decoder/transport case follows the selected executor containment evidence. Successful decoding of an early prefix cannot produce executed while later rows, descriptors or obligations remain unadmitted. These native controls remain not_run.


Backend replacement schedules: pause an admitted compiled operation before native submission and separately after submission but before decoding. Replace the host registration with a different decoder/obligation implementation, including a deliberately reused profile identifier/version with changed evidence. Require original exact implementation/evidence correspondence or the existing stage-correct refusal/recovery; never decode original rows through the replacement. A subsequent independently admitted artifact uses its own exact selected registration and cannot repair the prior operation. Remove the original required service while command termination is unknown and retain recovery/quarantine. Independently revoke current authority while original decoder custody remains available; retained services cannot authorize stale disclosure. Hosts without a qualified replacement mechanism must refuse that capability rather than claim these races passed. These supplements remain not_run.


The [compiled consumer case inventory](../../04-build/evidence/design-audit/compiled-consumer-case-inventory.proposal.json) assigns CE-01–CE-06 to these Truss execution supplements. It does not claim Weft compiler conformance or replace any primary story test. Native/packed-consumer execution requires independently selected bridge/backend/decoder/authority/executor/resource evidence, with retained original artifact bytes and actual submission/termination observations. An unsupported optional registration-replacement mechanism is explicitly unavailable; it cannot yield a passed replacement-race receipt.


### Configuration capture controls

Plan CC-01–04 alongside the assembly construction cases: (01) mutate the original selections array, every nested profile pin, namespace and assembly ID after construction and independently compare the exposed captured configuration and later target admission; (02) ordinary-data accessor/toJSON inputs refuse with counters proving no getter or toJSON invocation, while cyclic/over-limit data refuses before publication; (03) replace each hostServices container property after construction and prove the original admitted service remains selected, with no host object freeze/disposal and no service calls during capture; (04) alter actual service/native custody after capture and require per-operation refusal rather than trusting unchanged metadata. Keep hostile Proxy behavior outside the ordinary-data guarantee unless an independently qualified input profile admits it. Repeat packed-consumer checks in the selected Bun and browser-compatible construction environments. These are planned, not executed runtime evidence; existing static readonly declarations cannot satisfy them.
