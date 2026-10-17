---
ddx:
  id: TD-049
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-049
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: CONTRACT-013
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
---

# TD-049: Qualify the bounded Python action gateway

## Consolidation scope amendment — 2026-10-16

This historical draft is preserved from the earlier authorized bulk-action work.
It does not claim that its planned tests or protected executor are complete.
Current owner amendments govern every requirement below: Python-first delivery,
basic functionality tests, stock PostgreSQL practical limits and the existing
native statement/operation deadlines. Receiver/exporter, custom tracing/metrics,
formal-model and elaborate qualification prescriptions below are historical
optional proposals, not required implementation or release gates. A proposed
upstream60-second allowance cannot widen current native10-second SQL or30-second
operation limits. Host connection/transaction ownership and no hidden retries
remain unchanged. Existing `bulk_action_gateway.py`, action-store and authority
components on main must be reused and qualified; planned paths or statements
that no gateway exists describe the historical checkpoint, not current main.
Any cited evidence absent from main is **unverified historical evidence**, not
completion. Current public capability claims require their actual scoped tests.


## Scope

Realize US-049 under SD-003 and CONTRACT-013. Original UMF action/value meaning and person-required attribution remain authoritative.

## Technical Approach

Implement the selected bounded Python set recipe gateway using original UMF schemas/owner preparation/conformance fixtures and existing native Truss value/Key/authority outputs. The owner-produced artifact is inspected for exact original byte/source/version/obligation correspondence; it is neither a native authority token nor a finite-corpus shortcut for arbitrary models. Host explicitly wires the original inspectors/current-policy/session issuer, registered action revisions and transaction capability. Qualify the concrete Python consumer independently; reference TypeScript evidence cannot establish adoption.

## Component Changes

Planned files: packages/python/src/truss/bulk_action_gateway.py, bulk_delegation.py, bulk_attempt.py; native counterparts in packages/postgresql/src/bulk-action-gateway.ts and packages/postgresql/native/bulk-action-control.sql. Pure metadata planning has separate driver-free modules; native acquisition stays in the configured adapter boundary. No packages/core is assumed.

| Criterion | Realization |
| --- | --- |
| US-049-AC1 | gateway_registration through original configured gateway/control/native witnesses |
| US-049-AC2 | delegated_human through original configured gateway/control/native witnesses |
| US-049-AC3 | outer_transaction_gateway through original configured gateway/control/native witnesses |
| US-049-AC4 | native_attempt_custody through original configured gateway/control/native witnesses |
| US-049-AC5 | gateway_native_conformance through original configured gateway/control/native witnesses |

## API/Interface Design

CONTRACT-013 owns registerBulkActions and configured gateway composition; CONTRACT-904 owns full bulk operations, delegation and original attempt phases. Internal gateway implements the original tx/1 semantic envelope/results under preheld outer-transaction custody, not a new external generic invoke endpoint. Reserved pap1 tokens are unavailable outside this registered gateway namespace.

## Data Model Changes

Original revision/registration, seal/delegation, attempt/admission marker and original outcome homes join a fixed versioned shipped migration/installer inventory. Add no table per action/job. Control pre-effect registration occurs before effect connection acquires job/business locks; independent native correspondence and control commit are verified before business dispatch.

## Integration Points

Original owner schemas/registry/preparation -> bounded Python gateway; shared authority issuer -> original human/service context; original transaction/driver custody -> protected attempt registry and preheld lock capability. Missing/incompatible original dependencies refuse; no default credential/privileged writer is inferred.

## Security

Independently authenticate human and worker service; job-scoped issued delegation is current-authorized at admission/commit. Original Registry callbacks and native ACL/dependency closure are preserved. Outsider/stale request denials cannot mutate another valid job. No raw connection is exposed to action handlers.

## Performance

Use the declared profile1 finite bounds and per-batch configured capacity/accounting; no throughput promise. Known capacity refusal preserves committed prefixes; it is not a storage-truncation license.

## Testing

STP-049 owns independent ordinary-role native cases and original owner corpus agreement. Boundary gate: python3 scripts/check-module-boundaries.py plus original TypeScript native map. The gateway/source/native inventory is part of complete installed admission; simple import shape is insufficient.

## Formal Specification

US-048-AC7 owns the shared nonvacuous three-target/two-batch model. Its pre-effect registration, original transaction and claim/effect-admitted/settled transitions map to US-049-AC4 and native controls. Complete the bounded model before dependent US-047 execution work; model success is no native issuer/transaction proof.

## Diagnostic Wiring

Reuse original safe diagnostics and protected audit correspondence; US-048-AC6 owns real receiver/privacy/outage integration. Never export raw human credentials/source/guard values.

## Migration & Rollback

New gateway/profile registration is explicit. Disable admission, retaining original delegation/attempt/outcome custody and namespace nonreuse; do not remove native homes while uncertain work exists.

## Implementation Sequence

1. Create cited red gateway tests and original issuer/attempt/native mutation controls.
2. Implement pure owner artifact matching and explicit registration/current authorization.
3. Compose original native transaction/preheld locks, instrumented action effects and complete outcomes.
4. Qualify original worker/human, authority/native inventory and uncertain control/rollback schedules before US-047 execution.

## Risks

No current Truss action gateway or delegated issuer is implied. Protected admission/native correspondence and complete installer resources remain concrete dependencies; missing producer implementations block effects, not independent metadata/red-test work.

## Registration custody component (2026-10-13)

Historical claim: original component evidence is now retained unchanged in main;
it was not rerun against current runtime and establishes no current completion:
[Original owner-artifact registration](../../04-build/evidence/bulk-update/gateway-registration.md) now retains exact model/action/preparation bytes behind opaque instance-owned tickets, with original UMF API witness and seven Python3.11 tests. This is inert custody only; full qualified owner/Python semantic adoption, native authorization/delegation/attempt/gateway execution remain open. No US-049 criterion is marked complete.


## First direct-action prerequisite — owned psycopg completion

Apply CONTRACT-013's owned-completion profile in a small private
`packages/python/src/truss/_engine_action_session.py` component. Reuse
`engine_import._EngineImportSession.control` and the existing SCRAM connection
adapter. Do not reuse the import session's begin/reopen/rollback-repair behavior
or the preparation session's REPEATABLE READ authority/capture machinery.
Keep native settlement and connection-health observations separate. Preserve
known acknowledgement through cleanup failure; enforce the remaining absolute
invocation deadline before settlement. No public capability is enabled by this
component.

Basic checks use the real public group path on the owned caller-authenticated
connection: create/commit/read, explicit rollback and deferred commit rejection.
Reuse existing preparation test patterns for unknown acknowledgement and known
acknowledgement followed by cleanup failure. Refuse repeated begin/completion
and non-idle/substituted connections. Run the existing Python module-boundary
check with explicit imports for the new private component. No new tracing,
accounting, formal model or performance campaign is required for this adapter.

The [component evidence](../../04-build/evidence/action-owned-completion-20261017/receipt.json)
records 17 unit controls and three native tests passing on PostgreSQL 18.6 /
psycopg 3.3.6, using the exact source-matching wheel. The native workflow commits
and reads a public mutation, rolls back another, and confirms deferred COMMIT
rejection; two existing import workflows also pass. This is settlement evidence
only and does not complete this story or enable a public action capability.

The following integration remains unfinished: native action registration/revision
issuance, independent replay discovery, protected Subject/ACTION-role admission,
closed set-effect/frame enforcement, durable complete tx/1 outcomes and the SDK
ReplayingActionExecutor. The private session must not be presented as any of
those capabilities. Frozen-manifest control and delegation follow that complete
single-action workflow.


### Owner-only native role cut

The fixed `acquire_owned_action_role_catalog_cut()` dependency has a separately
named superuser-owned body and EXECUTE granted only to the excluded NOLOGIN
Truss owner. The original LOGIN-only preparation issuer remains unchanged.
The private installer checks original source, signature, owner flags, settings
and exact ACL. The action boundary must take its mapping cuts before calling
this helper, check the original authenticated Subject afterward, and retain all
cuts through owned completion. It must verify this helper as part of its full
source dependency closure under the stated administrator-quiescence premise.
This component alone supplies neither action admission nor an executor.

The installed-wheel [native dependency check](../../04-build/evidence/action-owned-role-cut-20261017/receipt.json)
passes alongside the original Subject workflow on PostgreSQL 18.6. It checks
coexistence with the original preparation issuer, direct-human refusal, owner
composition, role-lock lifetime through outer COMMIT and leaked-grant refusal.
The composing test routine is a fixture, not the protected action provider.


### Next implementation: protected single-set invocation

Implement one native SD boundary for invoke, keyed lookup and preview, with a
Python `ReplayingActionExecutor` adapter using the owned SCRAM session. This is
planned work, not an enabled capability. Start with the original committed UMF
`bulk-update-owner-fixture` model (main source `b40e9a13`, model SHA-256
`6fdf2d51e6bd2f167f43dbb32a6ce07ecc504e81fbe969de8e93c5fe5b924594`)
and its owner-prepared one-entity, one-field set action. The implementation must
handle that closed shape generically; the fixture is evidence, not an allowlist.

- Register an engine-issued immutable revision bound to complete original model,
  action and preparation bytes and the exact accepted catalog. Validate every
  relevant obligation: one EntityInput Key, one required Boolean/String/Integer
  value, one input-Key write frame, one set effect, no rules/handlers/outputs or
  additional read/write/relationship obligations. Refuse unknown meaning.
- Install independent family discovery membership explicitly. It is not inferred
  from action roles. Native Subject, revision, discovery and role bindings remain
  private. No table per action or job is introduced.
- Within the owned RC transaction, acquire source/store/mapping cuts, then the
  owner-only native role cut. Authenticate genuine SCRAM `SESSION_USER`, resolve
  its current enrolled human Subject, and check current ACTION roles and
  ordinary module permissions. Keyed invoke/replay and lookup additionally
  require discovery membership; unkeyed invoke and preview do not. Retain cuts
  through actual completion.
- Serialize the complete store/principal/family/key namespace before lookup.
  Hashes only route; full bytes establish identity. Authorize discovery before
  reading tokens and authorize the retained original revision before disclosure.
  Preserve original revision/expiry/payload precedence and mathematical typed
  equality without requiring a replayed entity to still exist.
- Fresh execution resolves the declared Key inside the native invariant boundary.
  The first profile may conservatively exclude other business writers with
  NOWAIT relation locks. Check existence and expected version in declared order;
  missing-entity rejection and version conflict are durable terminal outcomes.
  Fresh existing targets must be rootless; refuse owned targets before effects.
  Retained replay does not recheck the target's current existence or ownership.
  Preview executes no effects and persists no outcome or reservation.
- Reuse the original group executor for the set effect. Force its deferred native
  constraints before finalization; verify exact selected object/field changes,
  no edge or additional object transitions, complete recipe verification and
  no-op correspondence. Store complete tx/1 result, original typed intent and
  terminal audit atomically with effects. Denial, unsupported input, ambiguous
  resolution and known failed execution create no terminal business outcome.
- Convert the original native outcome into SDK carriers only after actual owned
  COMMIT acknowledgement. Preserve original request/result bytes and keyed
  recovery. Unknown acknowledgement stays indeterminate; no automatic retry.

Result binding is explicit. `store-opaque` versions identify the qualified
primary canonical-state cut, not an object version or ordered counter. Changed
actions bind their version to their actual native commit; a no-op retains the
pre-effect canonical cut and allocates no business-change version or event.
The read-at-least receipt identifies the exact retained terminal commit in the
registered store/epoch and is backed by its original native writer XID and full
outcome. It is not a relabeled group receipt. The qualified projection is the
primary canonical Truss tables: a fresh primary RC read reports visible only
when native MVCC includes that original committed writer and therefore all
canonical effects committed with it. An in-flight writer is pending; an unknown,
foreign, fenced or unsupported receipt/projection refuses. No asynchronous
projection or maximum-observed-ID shortcut is included. Keep original keyed
outcomes for the entire namespace lifetime, with no visibility expiry, purge or
key reuse in this first profile. Original replay returns the same retained
version, verification and receipt, including no-op outcomes.

The supported initial administration boundary is explicit: installation and
registration start with no pending administrator/DDL transactions; administrators
make no DDL, grants or configuration changes during service. Maintenance stops
admission, drains owned transactions, requalifies exact native dependencies and
then reopens. This is an environment premise, not proof of concurrent privileged
DDL exclusion. Existing store-incarnation fencing remains in force; no restart,
restore or namespace-reset guarantee is added by this plan.

The first completion check is a genuine generated-SDK invoke, owned commit,
public readback and keyed replay, plus changed-payload refusal, independent
replay-discovery denial, current-role revocation and rollback containment. Keep
basic tests and original 10-second SQL / 30-second operation maxima. Manifest
control and delegated batches follow this complete direct workflow.
