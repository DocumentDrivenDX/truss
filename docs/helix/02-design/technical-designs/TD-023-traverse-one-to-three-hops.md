---
ddx:
  id: TD-023
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-023
      kind: informed_by
    - id: SD-005
      kind: informed_by
---

# TD-023: Bounded one-to-three-hop traversal

**Story:** [[US-023]]. **Parent:** [[SD-005]]. **Feature:** FEAT-005.

## Technical Approach

Implement bounded explicit relationship-hop execution over the fixed typed edge layout, without authoring a traversal language. Resolve each hop through pinned catalog identity and recognized physical bindings. Preserve the story's object-unique/cycle rule as a direct traversal profile; do not transfer deduplication into Weft's bag-valued relational queries. Hop/request/result/continuation, release, host service and private state/ledger candidate contracts are authored; exact selected native/store evidence and resource profiles still gate implementation adoption.

## Component Changes

| Planned files | Change | Criteria |
| --- | --- | --- |
| `packages/core/src/reads/traversal-plan.ts` | Validate declared hop sequence, supported directions and resource bounds | US-023-AC1, US-023-AC2 |
| `packages/postgresql/src/reads/traverse.ts` | Qualified one/two/three-hop templates with typed filters and bounded result handling | US-023-AC1, US-023-AC2 |
| `tests/reads/traversal.test.ts` | Independent graph outcomes, cycles and high-degree refusal/truncation | Semantic prerequisites |
| `tests/benchmarks/traversal.ts` | Native p95 and planning comparisons against independent schema | US-023-AC1, US-023-AC2, US-023-AC3 |

Components are new. Weft retains source compiler ownership; these direct templates cannot grow into a duplicate parser/optimizer.

## API/Interface Design

CONTRACT-004 now proposes a concrete hop/work-limit/result declaration, path-local cycle exclusion and terminal object uniqueness. Consume it as a candidate rather than implementing global visited pruning or conflating output limit with expanded work. Owner cycle interpretation, staged work/result protocol and native budget enforcement remain review boundaries.

CONTRACT-001 owns edge access/indexes; CONTRACT-007 owns read context. Consume the existing direct-traversal request/resume/page/result/release and host-service candidates in CONTRACT-004. The human choice between unique terminal destinations and path output remains pending; do not adopt the proposed deduplication/cycle interpretation from wire shape or the independent candidate oracle. Exact original native/store/resource/authority realization must qualify before publication. A result limit alone cannot bound expanded intermediate work. Unsupported selected relationship variants refuse explicitly.

## Data Model and Integration

No default per-type DDL. Each hop retains relationship/source/target type filters. Visited identities are typed object identities, not display names; cycles terminate without losing required path evidence if the contract selects paths. Multiple paths to one object need an explicit deduplication policy. Catalog/profile and data share a qualified snapshot. High-degree expansion requires declared intermediate budget and explicit outcome; silent intermediate truncation can omit otherwise reachable results and is forbidden.

## Security and Performance

Apply source/edge/target authorization at every hop. Intermediate hidden objects cannot leak through count or truncation markers. Parameterize identities and filter values. Compare equivalent logical outcomes on independent hand-designed and Truss layouts with identical corpus/selectivity/output size, runtime/server settings and measured client overhead. Record p95 distributions, not a favorable single sample. ADR-002 V5 index qualification remains relevant.

## Testing

STP-023 allocates performance criteria; correctness prerequisites cover chains, cycles, diamonds, isolated nodes, opposite directions and high-degree objects. Hand-designed baseline is independently authored and must return equivalent results before latency ratios count. Vary metadata type count only for planning comparison. Weft bag semantics remain independently tested and are never deduplicated to pass this profile.

## Migration and Rollback

No implicit layout migration. Disable an unqualified traversal profile without rewriting storage. Optional index changes follow declared binding/administrative rollout and independent evidence. Changed deduplication/cursor behavior requires new profile version; no silent continuation reinterpretation.

## Implementation Sequence

1. Resolve the pending human output interpretation, consume existing traversal/service/state/ledger/resource candidates, select original realizable producer profiles and freeze the independent correctness corpus/baseline.
2. Write red native correctness tests and preregister benchmark sampling.
3. Implement bounded typed templates, then qualify native result equality and p95/planning ratios.
4. Review optional index changes separately if measured gaps require them.

## Risks and Gates

Traversal/service/state/ledger wires and finite budget candidates are authored. The output interpretation remains pending; exact original native expansion/store/physical accounting and supported process-lifetime realization remain unqualified. Cross-process or crash resumability is not supplied by the selected process-store candidate. SQL LIMIT after join expansion is not a work bound. Performance requirements remain unmet until native evidence proves equivalence and ratios. Broader relationship/association meaning and filtered multihop variants must not be silently removed to obtain green benchmarks.

Use CONTRACT-004's versioned initial/resume/sealed-page/result schemas. Preserve full original normalized query, frontier path state, terminal dedup, cumulative budgets and live host snapshot behind original registry custody; wire hashes alone are insufficient. Resume requires serialized expected work version and no budget reset. Emit records only after membership is sealed; limited results contain no partial frontier. Release declaration/result and malformed-input classification are now authored under CONTRACT-004; selected host storage/resource defaults and native budget enforcement remain design outputs.

Implement release as original-registry invalidation, worker containment and complete private resource cleanup with retained completion/recovery custody. The retained facade permits cleanup after snapshot end/disposal, without a transaction handle or graph/feed operation. Serialize against active resume and page disclosure; uncertain cleanup keeps the stage invalid and returns original recovery references. No missing registry entry or digest equality proves released. Malformed traversal input returns permitted invalid diagnostics without partial records.

The bounded reference candidate pins inclusive exact counters, request/page bytes, cumulative active work, per-stage and assembly-wide storage/stage reservations. Count repeated edge encounters and all admitted path states; terminal dedup never resets work. Atomic host reservations include quarantined stages until confirmed deletion; unavailable/resource covers new-stage/page capacity, limited/active_work covers cumulative expansion deadline. Native scanning/buffering and physical retained memory require independent host/native accounting evidence. No process-lifetime registry claims crash resume. See CONTRACT-004 for candidate values and unresolved service/storage integration.

The host stage-service/registration declaration now supplies inert existing-assembly setup and opaque issuer leases. Truss performs expansion; the host service atomically accounts/persists/version-controls private state. Successful publication advances version and replaces the old lease; conflict preserves prior state, uncertainty retains charged original recovery. No sealed membership mutation or disclosure after uncertain lease closure. Exact state/evidence codecs and qualified physical accounting/native authority remain selected-profile design outputs.

Private query/state schemas now define full query, FIFO path-local frontier frames with exclusive incident-edge scan position, cumulative counters and immutable sealed terminal identities. Checkpoint every processed edge with all enqueue/dedup consequences atomically; no prefetched boundary can skip unprocessed work. Seal only after complete frontier exhaustion and contained publishers. Canonical byte selection is authored; actual store publication/scan-completeness evidence and physical accounting remain design outputs.

Use separate resource-accounting and frontier-publication versions. Reserve opaque one-use work permits before effects; settle only independently confirmed actual usage, preserving uncertain maximum charges. Failed checkpoint publication cannot roll back cumulative budget. Resume reconciles the original latest ledger before fresh work; sealing/disclosure/confirmed release require no unresolved permits. Exact original permit/result ledger evidence and host atomicity remain selected-profile outputs.

Private ledger wire now separates initial creation charge, outstanding maxima and settled actuals with complete original permit inventory. Verify independent sum/uniqueness/version equations and issuer registry correspondence; physical retained bytes include ledger/tombstone overhead. Historical permit byte ceilings are not additive charges. Canonical byte selection is authored; original store/completion/cleanup evidence profiles remain open.

Traversal canonical byte selection now reuses truss-canonical/0.1.0 with separate query/private-state/ledger domains. Handle query digest differs from raw archived artifact SHA; verify both with full original custody. Published three-vector corpus binds schema trees/preimages/hashes, including Unicode. Complete production encoder/parser/browser and native/store evidence remain qualification outputs.

Publication performs atomic expected frontier + expected accounting-version admission, and private state names its original accounting cut. Concurrent ledger settlement forces candidate conflict/revalidation before checkpoint replacement. Later deletion/settlement may advance the independent ledger while sealed membership stays immutable; open reconciles original state against latest accounting without rollback/reset. Replacement-state allocation is precharged.

Publication evidence now has a closed private wire binding original attempt/store observation, old/new state, exact ledger cut and version+1. Produce only after confirmed actual atomic replacement; unknown reply reconciles original attempt without blind republish. This evidence supplies neither graph durability nor terminal completeness/cleanup. Actual-store observation profile/producer remains open.

The process-lifetime reference store now has a concrete synchronous immutable-root replacement model under CONTRACT-004. Original attempt records and stage/ledger/lease/permit custody transition atomically with the root; no callback/await occurs in the critical section. Actual async native workers and physical buffers retain separate original containment/accounting obligations. This candidate supports one original JavaScript service instance, not cross-process/crash resumability.

Process-store observation record and observePublication recovery call now have exact original-root/attempt semantics. Reconcile historical replacement without minting a new lease or current-stage permission; copied records cannot restore dead process custody. Completion/cleanup evidence and host physical/native qualification remain pending.

Work-completion metadata now binds original permit/worker and actual counters/bytes to original termination/usage/clock-span records before settlement. Missing producer custody cannot become zero usage or a refund. Exact native termination, monotonic-clock rounding and allocator usage profiles remain unresolved design outputs.

Cleanup evidence now binds invalidation, complete worker/permit/resource inventory, deletion and resulting charged tombstone/ledger. Retained completion metadata must not retain old roots/private buffers. For the process-store candidate, logical ownership release does not prove GC/RSS reclamation; select and qualify an explicit live-storage or physical allocator accounting profile. Actual producer/retention evidence remains pending.
