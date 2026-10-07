---
ddx:
  id: TD-018
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-018
      kind: informed_by
    - id: SD-004
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
---

# TD-018: Version-qualified reconstruction

**Story:** [[US-018]]. **Parent:** [[SD-004]]. **Feature:** FEAT-004.

## Technical Approach

Load complete retained event history and historical catalog definitions in one consistent read context. Admit complete mutation groups in version order, retaining original source sequence within each group. Reduce all admitted deltas in that source order; standalone retained additions require the separately selected later event profile and cannot enter the unchanged event/0.1.0 decoder; complete metadata snapshots are group-boundary witnesses under the proposed CONTRACT-002 procedure, not sequential replacement instructions. Resolve each event under its recorded revision, not today's property definition. Verify the requested version exists before returning its state; a genuinely unwritten version returns the contract's empty outcome.

Retention loss is not evidence that a version never existed. Missing create/definition/event prerequisites require explicit history-unavailable handling in CONTRACT-002 rather than fabricating empty history or reconstructing from the current canonical row.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/postgresql/src/history/load.ts` | Consistent event/definition reads and completeness checks | US-018-AC1, US-018-AC2, US-018-AC3 |
| `packages/core/src/history/reduce.ts` | Exact presence-aware event replay | US-018-AC1 |
| `packages/core/src/history/definitions.ts` | Revision-qualified definition selection | US-018-AC2 |
| `tests/history/reconstruct.test.ts` | Independent expected states, definition evolution and absence outcomes | All criteria |

All runtime components are new; pure replay has no database imports.

## API/Interface Design

CONTRACT-002 owns event/reconstruction semantics; CONTRACT-003 owns schema_change history; CONTRACT-007 owns read context. CONTRACT-002 now distinguishes complete state, qualified deletion, provably unwritten version and unavailable/unsupported history. The [reconstruction declaration](../contracts/bindings/truss-history-reconstruction-v0.1.d.ts), [complete record schema](../contracts/history-record-v0.1.schema.json), [event schema](../contracts/history-event-v0.1.schema.json) and [retained archive schema](../contracts/retained-history-archive-v0.1.schema.json) are authored candidates. API exposure still requires their selected interpretation, exact native horizon/completeness producers and runtime admission; declaration/schema existence does not establish retained evidence. No wall-clock as-of API is inferred from event timestamps.

## Data Model and Integration

The legacy baseline is unchanged by this draft. Complete-profile adoption must select snapshot/staging and manifest persistence, generation/privilege effects and any required migration explicitly; this design cannot promise zero new tables for that unadopted composition. Complete envelopes must include enough state for objects and edges, including retained content and presence. Rebind changes homes explicitly; unset removes a property rather than writing null. Historical type/field meaning must remain resolvable after later catalog changes. Legacy partial envelopes remain insufficient. Complete envelope and group-boundary semantics are authored; D-07 still requires profile adoption, native producers, retained historical definitions and qualified horizon/retention procedures.

## Security and Performance

Host policy governs historical visibility; access to a currently visible object does not automatically authorize all past content. Apply CONTRACT-005 and CONTRACT-002's complete retained-owner/current-authority procedure across the baseline, both snapshot images, intermediate deltas and historical definitions; preserve the original data caller through private collection. Parameterize IDs/versions and avoid leaking hidden histories through distinguishable errors. Read only relevant indexed entity events, but never truncate necessary history to meet latency. Reserve complete original inventories and cumulative decode/comparison/publication work before materialization; resource refusal withholds the requested state rather than publishing a valid prefix.

## Testing

STP-018 owns criteria. Independently author states at every version and compare public reconstructed output to expected values without production reducer reuse. Include definition change, unset/null, retained/rebind/transform and deletion. Pure replay supplements native event/definition loading. Deliberately missing history must expose incompleteness, not a false unwritten outcome.

## Migration and Rollback

Select complete-profile migration and an independently qualified seed/horizon where legacy evidence is partial. Reserved-position publication is a recommended unadopted candidate and changes insertion-assigned baseline allocation timing; record exact layout/source/profile compatibility before activation. Preserve historical event/definition versions through schema evolution. Unsupported new event semantics block reconstruction rather than ignore required events. Retention requires an explicit horizon/checkpoint recovery policy; rollback cannot recreate removed evidence. A previous qualified reducer remains usable only for its supported event versions.

## Implementation Sequence

1. Review and adopt the authored complete envelopes, snapshot interpretation and result outcomes; select exact native capture/staging/sequence/manifest and current-authority procedures, installation effects and historical migration horizon.
2. Create red independent multi-version and historical-definition fixtures.
3. Implement pure reducer and consistent native loader with completeness checks.
4. Qualify recovery, policy and unsupported-event refusals before broad history claims.

## Risks and Gates

D-07 remains open: complete payload/result/group interpretation is proposed, while exact native producers and selected persistence/allocation/resource profiles, retained baseline/definition/horizon evidence and owner adoption remain incomplete. Do not replace those concrete outputs with a generic missing-schema task. US-018-AC3 applies to genuinely unwritten versions, not missing retained evidence. Current canonical values cannot repair unknown historical state. This design does not assert time-based reconstruction or arbitrary graph snapshots from a single-record pass.

### Mutation-group reducer and producer handoff

For the proposed complete historical profile, the loader supplies complete original sibling inventory, definitions and group manifest before the reducer processes a version. A non-create/delete group supplies exactly one complete metadata before/after pair. Preserve an immutable group-start record and a separate staged property/retained inventory. Compare metadata.before to the full start; apply every admitted delta with its own before-state check; compare the full staged inventory to metadata.after before applying independently admitted metadata differences. Snapshot sequence position does not change these group-boundary comparisons. Preserve its actual position in the ordered digest.

The native writer must capture the start before the first effect and the final record after all group effects, under the same original operation custody. It cannot sample an intermediate record and label it group-final, emit one metadata pair per property, or omit a pair because only a property changed. Create/delete follow their complete-envelope procedures separately. This is a conditional producer requirement for the proposed profile, not evidence that an existing trigger or writer implements it. Exact entrypoints, snapshot capture, full sibling publication and finite accounting remain B-007/B-011 delivery outputs.

Pure reducer inputs retain original exact values and source meaning; hashing or canonicalizing a snapshot cannot erase token/presence/retained differences. Reserve group-start, staging, snapshots and definition/comparison work together before materialization. An interrupted or mismatched group returns no requested state. STP-018's independently authored metadata-before/between/after cases and missing-delta controls qualify the proposed reducer procedure separately from native producer/cut/current-authority evidence.
