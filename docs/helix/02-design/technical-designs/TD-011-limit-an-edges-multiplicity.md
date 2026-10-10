---
ddx:
  id: TD-011
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-011
      kind: informed_by
    - id: SD-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
---

# TD-011: Limit edge multiplicity

**Story:** [[US-011]]. **Parent:** [[SD-002]]. **Feature:** FEAT-002.

## Technical Approach

Use fixed `edge_limit` uniqueness for maximum-one, with unavoidable catalog-driven marker maintenance at the qualified database writer boundary. Merely inserting a marker in the engine is insufficient: a raw edge insert can otherwise omit it. The shared integrity-guard contract must define deployment, privileges, insert/update/delete and catalog-change behavior before this story is ready. It remains distinct from optional journal triggers.

For larger maxima, the engine acquires the relevant endpoint parent lock under CONTRACT-009, checks final group participation and refuses excess. Report this as engine enforcement. Never substitute per-relationship indexes to obtain the native maximum-one guarantee; index count remains bounded independently of relationship count.

## Component Changes

| Planned files | Change | Criteria |
| --- | --- | --- |
| `packages/tooling/src/guards/multiplicity.ts` | Install/check the versioned unavoidable integrity guard and privileges | US-011-AC1, US-011-AC2 |
| `packages/core/src/edges/limits.ts` | Derive endpoint-side limits and final participation checks | US-011-AC4 |
| `packages/postgresql/src/edges/limits.ts` | Parent lock/check wiring in complete group plan | US-011-AC4 |
| `packages/postgresql/src/operations/context.ts` | OC01–OC07 original transaction/admission/observer/commit context wiring; shared with row-home finalization | US-011-AC1, US-011-AC2, US-011-AC4 |
| `tests/edges/multiplicity.test.ts` | Engine/bypass/concurrent maximum-one and larger-limit cases | US-011-AC1, US-011-AC2, US-011-AC4 |
| `tests/benchmarks/relationship-planning.ts` | Controlled 10/1,000-relationship native planning comparison | US-011-AC3 |

Components are new. CONTRACT-001 EL01–EL07 now defines complete canonical/marker correspondence and protected final-state maintenance ordering. Exact native guard SQL/body/registration and installation remain unfinished; planned file names do not constitute implementation evidence.

## API/Interface Design

CONTRACT-001 owns derived limit rows; CONTRACT-004 owns write/report semantics; CONTRACT-009 owns lock order and final group validation. Consume CONTRACT-001 EL01–EL12 and OC01–OC07 for complete marker/context/final-state integrity; select and implement the original native bodies, dependencies, privilege and resource profiles before activating a guard. The authored protocol does not need a second public integrity surface. No new public command or payload is defined here.

## Data Model and Integration

Keep one fixed marker table and its generic uniqueness constraint. Marker derivation uses accepted catalog identity and source/target side, never caller-selected limit data. Edge deletion removes exactly its marker; updates that move endpoints or change relationships maintain old/new markers atomically. Tightening a relationship limit must scan/backfill and reject existing violations atomically with revision acceptance. Two-sided limits require both markers without partial effects.

## Security and Performance

The qualified writer cannot delete markers independently, disable guards or alter catalog limits. Definer functions need fixed search path, bounded authority and acting-role checks. Owner/superuser administrative bypass is outside the writer profile. AC3 measures identical query shape/data distribution and server settings with only relationship-count metadata changed; record planning distributions and native plans. No 2× claim follows from index counts alone.

## Testing

STP-011 owns four primary allocations. Test raw insert without marker, forged marker, marker-only deletion, endpoint-changing update, both sides, self-edge, deletion/replacement and simultaneous contenders. Larger maxima tests force both clients to compete at the parent lock and assert at most three committed edges. Group edge replacement validates final state under the shared protocol.

## Migration and Rollback

Initial qualification installs guard with fresh bootstrap. Existing populated installations require separately reviewed validation/backfill/grant transition, not this fresh bootstrap story. Failed edge or catalog changes roll back all markers and journals. Removing a guard withdraws database enforcement support; disabling engine checks is not a safe rollback for a claimed larger-max profile.

## Implementation Sequence

1. Select the complete native installation/role/adapter/context/codec/resource inventory and original producer bodies under CONTRACT-001/005/007/008. Refuse candidate execution while installable=false; selection is a design prerequisite, not a test skip.
2. Build the STP-011 original-transaction/barrier/state harness and independently authored expected graph/marker/version/history fixtures. Add ordinary-role bypass tests and planning benchmark fixtures.
3. Implement OC01 admission and OC02–OC04 observer resolution, registering actual native relation/event/function identities and complete original custody. If the unfinished-operation index is selected, include its complete original identity/dependency/security inventory and immediate uniqueness containment before registry insertion; qualify real finalization/savepoint membership restoration. Establish zero/ambiguous/forged/finalized-operation refusal before canonical marker maintenance. Index at-most-one membership does not establish the required exactly-one authentic observer context.
4. Implement complete old/new lock planning, EL04 remove-old/apply-final/insert-final maintenance and separately classified larger-limit checks. Use the final-group simulation; intermediate occupancy cannot replace final validation.
5. Implement OC05 complete row/non-row finalization and OC06–OC07 full-transaction current-union commit checks. The same dispatcher serves row-home and EL; no second registry or maximum-one-only completion path.
6. Execute all seven final-state schedules plus existing side/mode/bypass/resource matrix and preregistered planning benchmark. Keep original commit/rollback/unknown evidence; only independent native results can qualify support.

## Risks and Gates

Current layout uniqueness alone does not satisfy AC1. Native guard ownership and role design are unresolved enforcement dependencies in the coordination findings (D-07 concerns history/feed). Catalog-wide guard scans may harm write latency; measure without weakening integrity. Benchmark thresholds are story requirements, not existing evidence. Broader UMF relationship variants remain explicitly gated.


EL01–EL07 preserves source_max as sources per target and target_max as targets per source; source-side s markers derive from target_max=1 and target-side t markers from source_max=1. Complete actual marker multiset must equal canonical-edge derivation, including self-edge/both sides, updates and full catalog tightening scope. Protected remove-old/apply-final/insert-final ordering retains existing immediate PK and full endpoint/root exclusions, with final native seal/commit checks. Body/privilege/profile adoption remains open; marker uniqueness alone is not canonical graph enforcement.


EL01/EL05 now supplies three read-only legacy-layout definition/edge/marker query candidates with same-batch and original-cut/guard obligations. Complete marker closure includes rows naming selected relationships or linking selected canonical edges even when stored marker relationship/endpoint/side is wrong. Source-only UMF roundtrip evidence exists; actual bounded native collectors, token/descriptor/profile admission and protected maintenance/commit routines remain unfinished.


EL08–EL12 binds edge/marker observations and complete current-scope proof into the existing protected operation generations/finalization and transaction commit dispatcher. Edge-only/no-row-home effects still require EL obligations. Later distinct caller operations preserve earlier immutable results while final commit rechecks the complete current union; no cached historical marker proof or invented property tuple is admitted. The candidate registry kind CHECK now includes pure catalog-acceptance; actual native kind/context/phase registration remains required, and catalog-transform cannot substitute for acceptance authority. Exact observer/verifier bodies and registered privilege/resource/context profiles remain open.


The earlier missing pure-acceptance operation-kind finding is superseded by the candidate SQL/custody schema correction. Original operation/trigger-parent/index allocations and guard-inclusive composition/mapping are refreshed; native registration, full non-row catalog/EL finalization, private observer/verifier bodies and report policy remain unfinished. Merely admitting the label cannot permit bypass or an artificial row-home touch.


Three exact EL observer declarations and original baseline-parent trigger allocations are preserved as individual source artifacts and included in the selected 23-statement guard candidate; the older twenty-statement candidate retains its separate scope. Source/AST checks pin after-row all-events/no-filter/function/parent correspondence only. Actual native bodies, enablement/replication state, catalog versus ordinary operation context, privileges/resource producer and complete combined inventory still gate support.


The three EL observers are now included in a separately scoped 23-statement/142-effect selected-source candidate, preserving all twenty older statements and final initialization ordering. Exact delta/mapping checks pass; complete baseline/native routines/security/grants/registry source is still missing and installable=false. The older candidate remains separately versioned by original content pins.


STP-011 now supplies seven concrete native final-state schedules with independently authored E0/L0 and E1/L1 graph/marker multisets. Implement protected harness barriers only after original source/context/privilege/resource adoption; preserve immediate marker uniqueness, final-group semantics and distinct later-operation results. Swap rollback, early constraint checking, shared-target and larger-bound contenders, and pure catalog tightening each have explicit committed/pending/containment observations. These planned schedules require native implementation and execution before closing US-011.


### Separate enforcement observations

| Native guarantee | Selected source/design handoff | Independent qualification |
| --- | --- | --- |
| At most one unfinished stored operation per xid, if selected | Original partial unique-index identity and 24-statement/143-identity composition variant | Actual index parent/key/predicate/dependencies and unique/immediate/valid/ready/live state; controlled second-admission refusal and genuine finalization/savepoint restoration. Does not establish actual xid/role/context authority. |
| Exactly one authentic unfinished context per observer | OC02–OC04 full original registry collection, actual xid and original admission/producer/role/scope correspondence | Zero, ambiguous, substituted/stale/foreign context and ordinary helper/DML refusal. Retain full decoder and resource proof even with a unique index. |
| Maximum-one canonical/marker correspondence | EL01–EL07 complete old/new scope and remove-old/apply-final/insert-final under immediate marker PK | Full independently expected marker multiset, swap/self-edge/two-sided/catalog tightening and bypass cases. Registry uniqueness is unrelated to marker derivation correctness. |
| Complete transaction commitment | OC05–OC07 and EL08–EL12 original operation generations/current union, including finalized earlier operations | No unfinished survivors, complete current row/non-row/capacity correspondence and actual host commit/rollback/unknown outcome. A partial index excludes finalized rows and cannot be the commit collector. |

The prior 23-statement/142-identity source candidate remains preserved; the 24-statement variant is a separate unadopted choice with exact retained-source delta evidence. Do not infer any guarantee in this table from another row's pass, source object counts or a startup index-name check. These profiles must compose with host constraint timing and original savepoint/cancellation rules, with no missing earlier exclusion acquired inside an observer.

### Owning UMF participation versus Truss occurrence caps

The [fresh upstream review](../../04-build/evidence/design-audit/weft-b8867c9-participation-review.json)
records UMF main322b193 and Weft mainb8867c9. UMF's committed relationship contract
counts distinct associated endpoint Record instances. Weft's new Databricks
degree guards deduplicate source/target pairs while preserving edge occurrence
bags in result SQL. No Truss PostgreSQL lowering changes in that upstream range,
and Truss's adopted f05f2df compiler is unchanged.

US-011's existing second/fourth-edge refusal and marker correspondence describe
an occurrence cap. They must not be advertised as equivalent enforcement of an
owning UMF participation assertion: two edges to the same target give two
occurrences but one associated Record. Keep the existing occurrence-cap meaning
and its evidence separately named. A separately explicit cap may coexist with
participation, but cannot be silently inferred from the UMF assertion or hide
the stronger restriction in a fidelity report.

Before admitting UMF participation on Truss, select and version the distinct
typed-neighbor native mapping, complete writer/marker/catalog-change algorithms,
locking/accounting and independent tests. Distinct endpoint pairs are admissible
only after exact relationship/revision scope, typed original Record identity,
endpoint existence and complete integrity visibility are established; display
keys or projected tuples are not Record identity. Minimum checks include owners
with zero neighbors. Deleting one parallel occurrence preserves participation
while another survives; deleting the last removes it. Degree deduplication must
never deduplicate read bags, edge IDs, ordering or exact lookahead/truncation.

The current edge-marker profile cannot qualify that distinct-neighbor mapping
merely by changing a count query. Its full expected marker multiset and bypass/
concurrency/deletion procedures require reconciliation first. Until then refuse
the unqualified equivalent mapping rather than changing existing guards or
adopting the Databricks realization as PostgreSQL evidence. This is a concrete
shared semantic integration gap, not a new traversal or edge-cap product vote.
