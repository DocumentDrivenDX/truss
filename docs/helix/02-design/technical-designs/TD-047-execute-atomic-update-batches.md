---
ddx:
  id: TD-047
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-047
      kind: informed_by
    - id: SD-003
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: CONTRACT-013
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
---

# TD-047: Execute guarded atomic UPDATE batches

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


**User Story:** [US-047](../../01-frame/user-stories/US-047-execute-atomic-update-batches.md). **Feature:** FEAT-003. **Solution Design:** SD-003.

## Scope

One vertical journey defined by US-047; inherit the [parent solution design](../solution-designs/SD-003-mutation-and-concurrency.md) and architecture's portable/compiler/native boundaries. Shared surfaces live in CONTRACT-013, CONTRACT-004, CONTRACT-007, CONTRACT-009, CONTRACT-012.

## Technical Approach

Reuse original UMF core/actions identity, input, declaration and assessment semantics. Select pinned artifacts/registries explicitly. Preserve original intent and use source-qualified refusal; never make a local dialect, key codec or authority substitute. Python-first protected adapter and engine-owned transactions; original current-authority and native admission remain prerequisites.

## Component Changes

Planned source files: `packages/python/src/truss/bulk_executor.py; packages/postgresql/src/bulk-executor.ts; packages/postgresql/native/bulk-action-control.sql`. These additions are not present implementations.

| AC | Component realization |
| --- | --- |
| US-047-AC1 | atomic effects through the governing contract and focused test below |
| US-047-AC2 | identity and version through the governing contract and focused test below |
| US-047-AC3 | stop with prefix through the governing contract and focused test below |
| US-047-AC4 | current authority through the governing contract and focused test below |
| US-047-AC5 | no op receipt through the governing contract and focused test below |
| US-047-AC6 | capacity and failure through the governing contract and focused test below |
| US-047-AC7 | namespace_token_collision through the governing contract and focused independent witness |

## API/Interface Design

CONTRACT-013, CONTRACT-004, CONTRACT-007, CONTRACT-009, CONTRACT-012 define the exact shared shapes and methods. New exports follow those contracts; no signatures are independently defined here. Upstream schemas/fixtures are original owner inputs. Construct adapters only in the host registration boundary. Core cannot import native I/O/credentials; compiler cannot import Truss storage.

### Boundary realization

Boundary gate: `python3 scripts/check-module-boundaries.py` plus the existing TypeScript boundary inspection. Add the new pure/native module distinction to the checker allowlist before source wiring. Concrete native writer dependencies, native homes and privileged entry ACLs join the original complete installer inventory. Diagnostic wire authority is `docs/helix/02-design/contracts/diagnostics.proposal.md`, consumed unchanged.

## Data Model Changes

Fixed job/manifest/fence/outcome native homes require a shipped versioned migration and complete installer/admission inventory, not per-action tables. Use original accepted identity/value codecs and complete-result custody.

## Integration Points

US-046 and prerequisite US-049; qualified protected writer/invariant/action gateway and new control/outcome homes through shipped installer/migration. Unsupported/unavailable original dependencies refuse, with no fallback to fixtures or another executor.

## Security

Artifacts never load code or authenticate principals. Current protected read/execution/discovery authority remains executor-owned. Raw source/inputs stay out of diagnostics; retained manifests/outcomes require separately enforced access. Unknown relevant meaning blocks eligibility.

## Performance

Use the exact finite item/byte/node/deadline/result-capacity bounds in the contracts. Test both exact boundary and first overflow. No throughput/latency claim is made from structural tests.

## Testing

[STP-047](../../03-test/test-plans/STP-047-execute-atomic-update-batches.md) allocates each criterion once to a planned test with canonical citation. Command: `python3 -m unittest discover -s packages/python/tests -p test_bulk_executor.py`. The command/test target is planned, not currently passing evidence. Independent exact effects/refusals are the oracle, not generated output snapshots alone.

## Formal Specification

US-047-AC1/2/7 consume US-048-AC7's shared three-target/two-batch model: one batch contains two writes, so partial-batch commit is observable. Map original held guard/Key/version, preheld item-token scope and final atomic outcome transitions to independent native tests. Model completion is an initial US-048-AC7 substep before execution, not a dependency on full US-048 native recovery completion; bounded properties do not establish native enforcement.

## Diagnostic Wiring

Reuse selected existing diagnostic/capture contracts and construction pipeline. US-048-AC6/STP-048 owns real receiver, traced/untraced correlation, pre-sink privacy and exporter failure proof. Other stories consume the same pipeline without inventing a wire format. Admission/refusal and native completion emit only safe attempt/result references.

## Migration & Rollback

New profiles are opt-in; existing action/read/group behavior remains intact. Disable new admission while retaining all original manifests, terminal outcomes/tombstones and unresolved recovery custody. Do not reverse committed batches or drop native homes to simulate rollback.

## Implementation Sequence

1. Create the planned red tests in `packages/python/tests/test_bulk_executor.py` with canonical citations.
2. Implement contract-owned pure/component behavior in the named source files.
3. Integrate original dependency boundaries and run portable/native witnesses.
4. Retain exact versions, failed attempts, residual gaps and verified source correspondence.

## Risks

Incomplete upstream/native admission must block dependent execution without blocking independent pure work. Namespace/guard changes require new reviewed intent; they cannot migrate pending work silently. Architecture boundary check and concrete dependency closure must be current before public source readiness.

Native mutation prerequisite: US-049 supplies original UMF set-action registry/inspection, person-required delegated human context, transaction gateway and complete outcomes; ordinary update_object is not an action gateway.
