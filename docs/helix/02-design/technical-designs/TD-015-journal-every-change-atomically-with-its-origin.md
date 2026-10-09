---
ddx:
  id: TD-015
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-015
      kind: informed_by
    - id: SD-004
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
---

# TD-015: Atomic journal and origin

**Story:** [[US-015]]. **Parent:** [[SD-004]]. **Feature:** FEAT-004.

## Technical Approach

Generate journal effects from the validated mutation diff and persist them in the same transaction as canonical/derived effects. Exactly one configured journal writer owns each event: engine mode and trigger mode cannot both emit the same change. Database role comes from the qualified session/acting-role mechanism, never a caller origin field; actor remains an explicitly asserted fact. Restore transaction-local origin context at call boundaries under CONTRACT-007.

## Component Changes

| Planned files | Change | Criteria |
| --- | --- | --- |
| `packages/core/src/journal/events.ts` | Produce per-property and whole-record events from exact diffs | US-015-AC1, US-015-AC4 |
| `packages/postgresql/src/journal/write.ts` | Complete staged sibling/manifest admission and atomic event persistence with original version/revision/transaction/position identity | US-015-AC1, US-015-AC3 |
| `packages/postgresql/src/journal/origin.ts` | Trusted role capture and scoped asserted origin | US-015-AC2 |
| `tests/journal/atomic.test.ts` | Independent row/origin/rollback observations | All criteria |

All runtime components are new. Core event planning stays I/O-free.

## API/Interface Design

CONTRACT-002 owns event/origin schemas and operation payloads; CONTRACT-004 owns mutation diff semantics; CONTRACT-007 owns transaction-local context and durability. Complete historical envelope schemas and snapshot procedures are authored candidates in CONTRACT-002; adoption and native producer realization under the selected two-delta/one-witness group remain prerequisites for AC4; this TD does not invent an alternate event format.

## Data Model and Integration

Preserve legacy journal partition/order meaning. The proposed complete profile additionally needs explicit snapshot/staging/manifest persistence and allocation reconciliation; CONTRACT-002 recommends protected prepublication sequence reservation for review, which changes baseline insertion-assigned timing. Two changed properties share entity version and transaction, with separate old/new presence-aware values. Create/delete envelopes must preserve all reconstructible object/edge state, including endpoints/order/composition and retained content where relevant. Exact native capture, operation-end scheduling, original sibling/position/digest publication, profile adoption and historical migration remain D-07 outputs. Capture schema revision at the locked mutation context, not a later head read. Caller-owned events become durable only with host commit.

## Security and Performance

Origin input cannot overwrite trusted role fields. Definer execution needs explicit acting-role propagation and fixed trusted capture; current_user alone may identify the function owner. Privileges must prevent ordinary writers altering audit rows or forging session context. Host authentication determines asserted actor trust; journal must not upgrade assertion to verified identity. Measure event volume/WAL separately from canonical writes and retain atomicity under partition failure.

## Testing

STP-015 owns criteria. Independently read journal rows and canonical state, including same transaction/version and trusted role. Force journal failure after canonical effects but before commit; assert full rollback. Exercise multiple calls in one caller transaction to expose origin leakage and both journal modes for duplicate/missing events.

## Migration and Rollback

No implicit layout migration. Missing partitions or failed journal writes refuse mutation and roll back effects. A changed event schema gets explicit version/compatibility and reader qualification; never rewrite old rows to resemble a new envelope without migration evidence. Journal mode transitions require exclusive configuration control and zero duplicate/gap evidence.

## Implementation Sequence

1. Finalize complete event envelopes and trusted role capture/privilege contract.
2. Add red row/origin/fault fixtures, then pure event planning.
3. Implement atomic persistence and scoped context; qualify engine/trigger mode independently.
4. Verify reconstruction prerequisites before publishing history/feed guarantees.

## Risks and Gates

D-07 whole-record/presence completeness and role/session authenticity remain shared-contract gates. Journal failure injection must occur inside the real transaction; throwing before any write is insufficient. Sequence position is not commit order by itself. This story does not qualify watermark/feed ordering merely by writing audit rows.


For explicitly adopted lexical numeric profiles, event planning consumes CONTRACT-004 stored-value equality and CONTRACT-002 exact old/new correspondence; mathematical NX equality or unchanged key identity cannot suppress a token change. Implement the same selected codec/event meaning in the exclusive engine or trigger writer, with original source reconstruction and atomic rollback. STP-015 supplies conditional lexical-change/no-op/engine-versus-trigger/failure cases. Carrier/envelope/codec adoption and native producer qualification remain prerequisites.

### Selected metadata witness row count

The owner resolved this interpretation on 2026-10-07: US-015-AC1 counts two property-delta rows and includes one additional complete record-boundary metadata witness in the same group. Consume the amended story and CONTRACT-002 selection; do not remove or hide the witness to obtain a two-total-row result. Keep the legacy two-row baseline separate from the selected complete profile. Exact three-event sibling membership, digest, original native producer and reader/migration qualification remain implementation obligations, not a pending product vote.

### Snapshot reuse implementation handoff

Before journal persistence, map the selected protected operation artifacts to a complete typed entity/version boundary inventory under CONTRACT-002's reuse procedure. Keep expected candidate and independently collected final state separate. Event planning consumes admitted exact deltas and observed full boundaries; it cannot create native custody through an I/O-free constructor. B-007/B-011 must supply original-artifact decoders, native capture/final collectors and exact position/publication entrypoints. STP-015's multi-entity collision, rollback, substitution and cumulative-budget cases qualify this boundary separately from STP-018's pure reconstruction experiment. No extra store or producer grammar is selected by this handoff.

### Complete snapshot collector composition

Plan the private collector in `packages/postgresql/src/journal/collect-record.ts`; it consumes CONTRACT-001/004/007's selected original home, native transport and guarded operation context, not a public read result. Bind one immutable collector specification before effects: exact layout/home/value/temporal/definition profiles, typed identity and kind, expected complete property and retained-home inventory, owner union, native descriptor signatures and cumulative resource account. Reject unsupported or ambiguous home composition before claiming capture readiness. Current metadata SELECT source preservation is evidenced, but no selected native collector is implemented.

1. Under the original operation's protection and coherent cut, observe the canonical header using the admitted object or edge metadata route. Admit exactly one complete header with matching typed identity/kind, native numeric domains, version/revision, ownership/endpoints/order and exact temporal/session descriptors. Zero rows is absence only under complete visibility and the selected create/delete boundary; two rows or invalid descriptors refuse. A LIMIT 2 result does not prove complete properties or retained inventory.
2. Collect every required property home using the selected complete owner enumeration and complete tree/scalar procedures. Compare expected-to-observed and observed-to-expected membership before decoding a full image. A canonical props carrier and row-home state cannot both supply the same property unless the original profile explicitly defines and independently verifies their relationship. Select no home by whichever query returns first, and omit no unclassified state.
3. Collect the independently selected complete retained home. Baseline objects use their admitted retained carrier; baseline edges without a selected retained home cannot produce a complete snapshot merely because the metadata query omits that column. The proposed edge column needs its own selected layout, complete query/descriptor and value/presence correspondence. Preserve literal member names, absence/null and original source meaning under the exact profile; no JSONB text-to-authored-source equivalence.
4. Resolve original definition/kind and the complete historical owner union, with current authority admitted separately. Assemble the full image only after all header/property/retained/source completions match the same operation, phase and original cut. Do not substitute later current definitions or public visibility for private integrity completeness. Charge every input, materialization, traversal, comparison, output and retained recovery artifact under the existing account before publication.
5. Freeze the start image before effects. Collect final state independently after canonical and derived effects have quiesced, while the original operation remains admitted and before full effects readiness or RF row sealing; compare complete candidate-to-final parity and the staged ordered delta-to-final correspondence before producing the witness. This is nonsealing native observation, not the full RF finalizer that already requires complete history/report effects. Start/candidate/observed-final remain distinct artifacts. A second operation in the host transaction captures the first operation's actual final state as its new start. Deletion proves complete original start and selected final absence; creation proves selected original absence and complete final inventory.

Collector success is private preparation, not commit acknowledgment, group digest authority or permission to overwrite immutable operation-registry byte slots. Original phase custody and bounded final/envelope/position staging still require the selected native realization. On interruption, invalid authority, changed home/profile, incomplete inventory or resource exhaustion, preserve the existing contained/unknown outcome and recovery custody; never publish a partial image or repair it from the current canonical table.

The collector's baseline-plus-retained-column branch now has a separate [object/edge metadata observation source](../contracts/private-record-metadata-retained-observation-v0.1.proposal.sql) with twelve object and fifteen edge projections, including retained_text on both routes. Its [UMF capture receipt](../../04-build/evidence/design-audit/private-record-metadata-retained-observation-source.json) proves original SQL archival and reload/export equality only: zero DDL declarations, two unhandled SELECTs and complete=false. The baseline query remains unchanged and lacks edge retained_text. Bind the exact query/descriptor signature to the selected original physical layout; a baseline-only database must refuse this branch before effects rather than catching undefined-column errors and falling back to an empty retained image. Root/endpoints/order, temporal settings and JSONB text carriers retain the existing decoder and source-correspondence obligations. This variant changes no compiler ABI and does not replace full property/home collection.


## Producer boundary correspondence handoff

The complete operation inventory uses global sibling ordinals; historical manifests use the narrower CONTRACT-002/ADR-007 typed entity/event-version boundary. `entities[].siblingOrdinals`, `siblings[].ordinal`, reserved `mapping[].ordinal` and pending `rows[].ordinal` must form independently verified one-to-one correspondence. Every mapping preserves the original sibling's exact typed identity, resolved kind and event mutation version; positions are native allocations, not derived from ordinal arithmetic. `completeGroupInventory` in the pending body denotes original evidence for all historical groups in the operation, not one operation-wide historical manifest.

Use this independently expected allocation schedule in JP-03–JP-05. A and B denote independently resolved original typed identities under the same admitted source epoch/profile; C is an unchanged captured entity. Versions and sequences are exact decimal text. The gaps deliberately prevent a contiguous-position shortcut.

| Global sibling ordinal | Original boundary | Reserved sequence | Boundary-local digest order |
| --- | --- | --- | --- |
| 0 | A, event version 7 | 101 | A member 1 |
| 1 | B, event version 3 | 104 | B member 1 |
| 2 | A, event version 7 | 109 | A member 2 |
| 3 | B, event version 3 | 113 | B member 2 |
| 4 | B, event version 3 | 120 | B member 3 |

Original final preparation assigns A ordinals [0,2], B [1,3,4] and C []; native publication must retain A count 2 and B count 3, with independently computed digests over the actual complete original event payloads at their assigned positions. C emits no group. These symbolic positions are fixture expectations, not an allocator guarantee or authentic digest vector. The selected native test harness must pin original payload/origin/codec bytes and independently expected digests before execution; substituting hashes produced by the writer under test cannot establish correspondence.

Compare full original boundary inventory and global membership before reservation, full returned allocation membership before encoding, and actual stored row/event/origin membership before pending evidence. Reject missing, duplicate, extra or foreign members at each boundary without returning a successful subset. Original same-cut authority, generations, resource budgets and rollback/unknown-settlement handling remain required. The frozen preparation cannot be rewritten to accommodate a mismatched mapping or append. Source/profile declaration and schema assignability do not establish this native bijection.


Owner decision, 2026-10-07: US-015 counts two property-delta rows and permits the additional complete record-boundary metadata witness. The story now states the complete three-event group explicitly. The row-count requirement conflict above is resolved; complete manifest/native producer/profile qualification remains open.
