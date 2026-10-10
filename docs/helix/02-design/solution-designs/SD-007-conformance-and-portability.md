---
ddx:
  id: SD-007
  type: solution-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: FEAT-007
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
    - id: CONTRACT-011
      kind: informed_by
---

# SD-007: Conformance and portability

**Feature:** FEAT-007. **Status:** draft. **Parent:** Truss architecture.

## Scope

Publish language-neutral cases with independent expected data and qualify implementations per model/layout/engine/profile. Bootstrap the internal layout through UMF-native representation and parity gates.

## Requirements Mapping

The table also owns feature-level traceability; exact per-criterion tests belong in story test plans.

| Requirement | Design capability | Verification strategy |
| --- | --- | --- |
| CNF-01 | Contract inventory and language binding mapping | Independent implementer can find every normative surface and compatibility rule |
| CNF-02 | Versioned case schemas, required tags and independently authored expectations | Malformed/unknown required case refuses certification; host cases separate |
| CNF-03 | Same corpus on each implementation and bidirectional interchange | Read/write across both implementations; narrower profile never reported full pass |
| CNF-04 | Layout/capability check before operations | Different major refused; compatible minor checked for required components |
| CNF-05 | Disposable native install plus full catalog and behavior checks | Actual selected layout passes on each qualified server |
| CNF-06 | Pinned UMF validity and diagnostic corpus | Same severity/code/path; no host-specific semantic reinterpretation |
| CNF-07 | UMF native model/export and independent baseline candidate oracle | US-045 determinism, complete inventory, edited model and refusal cases |

## Solution Approaches

Data corpus plus native oracle is selected over SQL-text snapshots as the semantic authority. Generated SQL remains informative; reference implementation code cannot define expected behavior by itself.

## Domain Model

A corpus manifest identifies required cases and pins; each case carries setup, operations, expected results/state/journal/report. Bootstrap coverage inventories every physical object; evidence records claims separately from execution outcomes.

## System Decomposition

Corpus package owns declarative cases and expected data. Native runner owns fixture install/cleanup and evidence; browser runner checks pure core. Tooling owns model generation/bootstrap. Story test plans allocate each acceptance criterion and implementation slices name their exact gate.

Exact shared surfaces belong to the referenced contracts. Story technical designs inherit these component boundaries and add files, per-criterion wiring and rollback steps without duplicating interface definitions.

## Quality Attributes and Concern Alignment

ADR-001 governs separate TypeScript core/adapters, Bun development and provisional Node support. ADR-002 governs fixed storage and measured/provisional choices. Values and documents remain exact within the explicitly qualified profile; unknown content is retained. Database claims require native evidence at the actual bypass/role boundary. Performance targets remain proposed and measured independently from correctness. Package changes keep PostgreSQL-specific I/O outside the pure core.

## Traceability and Gaps

Every functional feature requirement is assigned above. Governing story criteria remain in their US artifacts. These gaps are design/qualification dependencies, not permission to omit requirements:

D-02 covers actual native layout-model generation and parity evidence; the design contract is not the model artifact. Second-language qualification waits for proposed ADR-003 and an actual independent implementation; current design must not promise its tests already pass. Bun/Node/browser claims stay separate.

## Constraints, Risks and Rollback

A new layout/encoding/profile is explicit and versioned. An unsupported combination refuses before mutations or SQL emission. Keep the previous model/layout/profile artifacts for rollback; do not rewrite an installed database implicitly. New implementation code can be disabled/unregistered independently of stored data; a deployed breaking schema change needs its own reviewed migration. Before building, reconcile these references against current UMF/Weft interfaces and resolve the affected gates in the design coordination record.

### Required manifest and qualification evidence

CONTRACT-011 governs the complete approved case manifest, registered procedures, independent original input/expected artifacts, implementation and observer profiles, isolation, cleanup and receipt aggregation. Coverage counts and a reference-host checkpoint sequence do not establish complete required membership. Select the full supported scope before execution; unavailable preparation cannot become a skipped passing case, and a failure cannot authorize excluding a required profile.

Keep component/source checks separate from native database, bypass, performance and independent interchange evidence. Each case retains its original evidence layer. Completed case outcomes use passed, failed, skipped, blocked or not_run under the contract; interrupted or unknown native/cleanup activity remains recoverable run evidence rather than a fabricated completed receipt. Support requires every required case to pass with complete original evidence and the separately admitted current installed-policy observation.

Existing UMF capabilities are sufficient for the consumer design. Source capture, guarded statement composition and mapping candidates already exist; D-02 now requires complete Truss-owned authored effect inventory, selected collector interpretation and independent installed/native parity. Do not replace these concrete outputs with a generic request for upstream exporter work, or treat source/model equality as native installation qualification.
