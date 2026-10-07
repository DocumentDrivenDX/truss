---
ddx:
  id: TD-016
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-016
      kind: informed_by
    - id: SD-004
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
---

# TD-016: Journal plain SQL changes

**Story:** [[US-016]]. **Parent:** [[SD-004]]. **Feature:** FEAT-004.

## Technical Approach

Implement CONTRACT-002's exclusive engine/trigger writer selection. Trigger mode makes native object/edge changes produce journal effects and maintain version/time; the engine supplies scoped origin and omits its own event/version writes. Engine mode retains its narrower bypass guarantee and reports it explicitly. Journal triggers are separate from unavoidable endpoint/multiplicity integrity guards.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/tooling/src/journal/triggers.ts` | Versioned trigger installation/inventory and trusted origin handling | US-016-AC1 |
| `packages/postgresql/src/journal/mode.ts` | Pin configured mode through write transaction and dispatch one writer path | US-016-AC2 |
| `packages/core/src/reports/enforcement.ts` | Report engine-mode raw-SQL audit gap | US-016-AC3 |
| `tests/journal/modes.test.ts` | Real bypass/engine mutations and mode transition races | All criteria |

All runtime components are new. Trigger bodies and administrative transition protocol must be specified in the governing contract before implementation.

## API/Interface Design

CONTRACT-002 owns mode/version/event behavior; CONTRACT-007 owns transaction-local origin restoration; CONTRACT-004 owns engine writes. Administrative mode transition needs an exact mutually exclusive protocol and privilege model in the shared contract. A mere setting read cannot prevent a simultaneous administrator update.

## Data Model and Integration

Use existing journal/configuration tables. Native triggers compare old/new exact maps, emit property and whole-record events under finalized envelopes, and maintain record version once. Pure no-op SQL updates cannot create false semantic changes. Engine reads trigger-maintained results rather than guessing returned version. Mode pin must cover caller transaction lifetime, including several calls before host commit.

## Security and Performance

Qualified writers cannot disable triggers, alter mode or tamper with journal. Definer functions use fixed search path and trusted acting-role capture. Caller origin role fields are ignored. Revoke direct version manipulation or define/prove trigger overwrite behavior. Measure native trigger cost and journal failure rollback; do not bypass triggers through bulk paths advertised as supported.

## Testing

STP-016 owns primary allocation. Supplement with raw insert/update/delete, no-op update, retained changes, endpoint metadata changes, bulk SQL, caller rollback and two distinct call origins in one transaction. Mode transition must wait/refuse while old-mode transactions are active, preventing gaps or duplicates. Existing journal envelope/role gates apply.

## Migration and Rollback

Fresh installation first. A live mode switch needs explicit exclusion, trigger/grant readiness and evidence; this story does not silently install over active writers. Failed trigger/journal write rolls back canonical changes. Removing triggers withdraws bypass auditing and requires an atomic switch to qualified engine mode, not a period with no writer.

## Implementation Sequence

1. Specify trigger bodies, privileges and mode-transition exclusion in CONTRACT-002.
2. Create red native mode/bypass cases and transition interleavings.
3. Implement trigger writer, engine dispatch and returned version integration.
4. Qualify complete operation matrix and report limitations per mode.

## Risks and Gates

CONTRACT-002 now authors transaction-wide shared writer/exclusive administrator admission and separates mode-only switch from dispatcher DDL. Exact native mechanism/current-setting custody, trigger admission timing and writer/admin wait matrix remain incomplete. Exact diff/envelope and trusted role capture depend on D-05/D-07. Trigger recursion, caller-set version fields and trigger order require native tests. A sequential mode switch cannot prove transaction-wide writer exclusivity.
