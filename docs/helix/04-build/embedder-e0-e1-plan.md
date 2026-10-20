---
ddx:
  id: PLAN-EMBEDDER-E0-E1-001
  type: implementation-plan
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-005
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
    - id: STP-040
      kind: informed_by
---

# Embedder E0/E1 execution

## Scope

Deliver the Truss-owned E0/E1 subset of UMF's
`docs/helix/04-build/truss-embedder-feedback-plan.md`: owned-profile condition
capacity, typed permission/operation diagnostics, correct original collision
ordinal, registration regression qualification, and alias/limit documentation.
The upstream plan is a consumer request; Truss contracts own adopted semantics.
The owner authorized implementation. Bulk import, cache validators, catalog
evolution, lifecycle, preview and audit work remain separate slices.

Governing artifacts: [architecture](../02-design/architecture.md),
[CONTRACT-003](../02-design/contracts/CONTRACT-003-catalog-revision.md),
[CONTRACT-004](../02-design/contracts/CONTRACT-004-mutation-and-conformance.md),
[CONTRACT-005](../02-design/contracts/CONTRACT-005-module-isolation.md),
[CONTRACT-007](../02-design/contracts/CONTRACT-007-embedding-and-execution.md),
[CONTRACT-009](../02-design/contracts/CONTRACT-009-group-planning-and-locks.md),
[STP-040](../03-test/test-plans/STP-040-apply-operations-as-one-atomic-group.md).

## Shared Constraints

- Preserve locked prestate, unique condition IDs, authored failure order and
  predicate failure precedence. A higher count never overrides bytes, complete
  owner/scope/lock/key footprint, result limits or deadlines.
- Preserve original caller authority, full original error/replay artifacts and
  native failure/recovery context. No postfailure key reread, hidden-key
  disclosure, implicit transaction settlement, retry or group splitting.
- Valid nameless Records/Fields already have ID-based selected-profile behavior;
  retain and qualify it. The reported blanket nameless refusal is superseded by
  the current regression intent. Do not add an authored-name requirement.
- Preserve the Python boundary map and protected native paths. Truss composes
  UMF metadata and Weft SQL meaning; no new semantic resolver or compiler facade.

## Implementation Slices

| Slice | Area / dependency | Validation gate |
| --- | --- | --- |
| E0a | Source map and baseline, before E1 | Run `python3 scripts/check-module-boundaries.py` and `python3 scripts/check-module-boundaries-controls.py`; review explicit import additions. The current control producer defines 18 cases. CI runs both in `.github/workflows/python-boundaries.yml`. No active pre-commit hook was found; do not claim pre-commit wiring. |
| E0b | Reproduction and exact installed cohort | Retain test/fixture/source and native asset hashes, Python/psycopg/libpq/Weft/UMF/runtime versions, transport and limits. Run selected regressions against installed wheel; distinguish reports from reproduced failures. |
| E1a | CONTRACT-004 condition selection, after E0a/design | Owned 1,024 profile admits 3,072 predicates subject to unchanged limits; the retired inventory component retains 128 without reactivating legacy execution. Prove 51×3, count bound/one-over, byte/resource bound, failure precedence and complete rollback. |
| E1b | CONTRACT-007 typed family refusals | Group context/apply, metadata references/preparation and key/edge/object reads distinguish denied authority from missing entities and execution failure. Negative authority results contain no hidden identifiers or native prose. |
| E1c | CONTRACT-004 operation diagnostics | Add stable operation code and preserve full artifact; propagate trusted native key-preflight ordinal through admission. Prove first/middle/last, multiple conflicts, tombstones, within-group duplicate and unindexed whole-group finalization. |
| E1d | CONTRACT-003 registration and consumer docs | Existing ID-only scalar registration/create/update/query/reopen regressions pass; unsupported executable shape refuses before head publication. Document selected condition/operation/import/input/result limits and safe explicit relationship alias after `x.*`. |
| E1e | Source-bound integration/review | Boundary controls, focused native suites, fresh installed-wheel tests and changed-code review pass; original replay/rollback/disclosure gates remain green. |

### Local condition metadata optimization

Retain the current condition/source-validation and pre/post-evaluation passes.
Within one `runtime_condition_inventory` invocation, reuse a resolved type row
only when the full object target exactly equals the last successfully validated
target. A separate validity flag prevents missing/SQL-null input from matching
uninitialized memo state. Catalog-head share custody makes the accepted
definition stable; the memo neither stores predicate truth nor suppresses any
per-condition authority check. It has one entry and ends with the invocation.

Qualify both the repeated-target ceiling and a mixed ObjectExists/PropertyEquals
ceiling with distinct A/B targets, unique condition IDs and original-value
assertions. Preserve the heterogeneous 153-condition ObjectExists/property/key
case and malformed identity controls. The current statement/operation limits
remain 10,000/30,000 ms. A timeout remains failure to qualify that workload.
Broader structural-inventory consolidation is deferred while this smaller
change satisfies the selected gates; it requires separate ordered-authority,
source-precedence and private-helper closure review if reopened.

### E2 continuation design boundary

E2 is subsequent design/implementation work. Legacy `ImportInput` retains
per-record outcomes and partial progress, with settlement determined by its
selected caller-owned or engine-owned route. The existing atomic
`OwnedImportInput` route has a different whole-aggregate failure boundary.
Batching MUST NOT silently turn legacy partial progress into an all-or-nothing
atomic group, or treat the owned route as evidence for legacy semantics.

Qualify batching at the existing 128-record bound first. Preserve original
record indices, object-before-edge order, existing/reserved identity skips
before payload decoding, exact retained source and complete tagged reports.
Within-chunk duplicate identities must preserve original create/skip/error
ordering. Adopt explicit per-record containment, relationship validation and
failure/report behavior before selecting a set-based executor; an atomic group
failure cannot erase previously accepted legacy records by convenience.

Qualify 1,024 records as a separate resource profile after batching parity.
Bound cumulative transaction work, input/payload/report bytes, complete source
and authority checks, memory and deadlines. Establish the actual fixed client
statement budget per homogeneous bounded run, including builder and provenance
work. Measure 32/64/128/1,024 on the same cohort, fixture and transport; separately
count server work and transaction boundaries. No E1 result establishes larger
import capacity or a speedup. CONTRACT-004/007/009 and import story test plans
must adopt the selected E2 failure/settlement design before its execution.

## Execution Contract

Planning/review uses the installed HELIX catalog and preserves existing artifact
frontmatter. Implementation uses the available Python environment and the
existing native fixture worker lifecycle; one process owns any native cluster
management. Reuse owned Unix-socket workers with fresh databases/roles and
explicit cleanup verification. No shared TCP listener or worker reuse after
cleanup drift. Lifecycle tests stay isolated.

Runtime reference cohort is package 0.0.41, native `0.72-candidate`,
PostgreSQL 18.6 / `pgserver-pg18==18.6.1`, psycopg 3.3.6 and Weft 0.4.48.
Retain exact installed identities when executing; package versions alone do not
qualify bytes. A changed native release requires manifest/hash correspondence
and the normal supported installation/upgrade qualification before release.

Use supported Python 3.11 or later for source-map and test commands. In this
execution the available interpreter is
`/private/tmp/truss041-final-env-20261020/bin/python`; activate that environment
so `python3` resolves to its supported runtime. The system Python 3.9 cannot
parse current variadic tuple syntax and cannot establish the boundary gate.

Token cost and duration estimates are unknown: no comparable metered execution
is available. The initial probe is bounded to E0 inventory, focused reproduction
and these design amendments. No enforced spending ceiling or runtime usage meter
is available here. Native verification and review remain required for delivery.

## Validation Plan

Use [STP-040's Python supplement](../03-test/test-plans/STP-040-apply-operations-as-one-atomic-group.md#python-embedder-e1-supplement).
Run `python3 scripts/build-owned-runtime.py --check` to verify owner SQL assembly
and complete runtime manifest correspondence after regeneration. Apply owned
runtime changes to `packages/postgresql/owned-groups/` owner sources before
regenerating packaged SQL. Run focused native tests with the active installed test environment and existing
worker harness, including `test_group_preconditions_native`,
`test_group_create_native`, `test_owned_group_batch_native`,
`test_object_mutations_native`, `test_consumer_northwind_numeric_native`,
`test_edge_mutations_native`, `test_typed_keys_native` and
`test_embedder_workflows_native`. Confirm actual available selectors before use.
Retain original commands, exit statuses, logs, source/asset pins and cleanup.

Measure client statements, network round trips, transaction count, elapsed work
and server-internal work separately for the actual admitted workload. The
[original installed E0 baseline](evidence/design-audit/embedder-e0-e1-20261020/e0-measured.json)
and its [measurements](evidence/design-audit/embedder-e0-e1-20261020/e0-measured-measurements.json)
record three client statements each for group context, reader catalog and point
object read, and four for one cold update apply. These are single observations
inside an already adopted caller transaction; setup/BEGIN/COMMIT, round trips
and server-internal statements are excluded. No latency distribution, speedup
or universal write-count promise is adopted. This slice raises no import ceiling and establishes no bulk-import
performance claim. Native and installed evidence qualify only their exact
versions, selected subset, platform and transport.

## Continuation Evidence

Read-only design review found the original condition cap at native inventory
and original operation ordinals available during serialized native key planning.
The wrapper defaulted admission failures to index zero. E1 carries the trusted
ordinal through conflict DETAIL and the existing outer failure artifact.
Existing tests explicitly preserve nameless
Fields and all nameless elements through stable IDs. The source-map update
explicitly admits `functools` for four static installed-asset
cache modules; these cache immutable package bytes/digests, not live authority.
Implementation and native outcomes require separate recorded execution evidence.

The [local-memo ceiling gate](evidence/design-audit/embedder-e0-e1-20261020/e1-opt1-ceiling.json)
passes its repeated-target 3,072-condition case and native malformed/count
controls against the [unpublished wheel](evidence/design-audit/embedder-e0-e1-20261020/opt1-wheel.json)
with 412 exact source/wheel/installed file matches. This follows retained
statement-timeout failures; limits were not raised. The retired inventory's
corrected synthetic original-caller case has separate evidence in the
[corrective log](evidence/design-audit/embedder-e0-e1-20261020/e1-installed-corrective.log);
that earlier combined run also retains an owned-capacity failure.

The [broad installed gate](evidence/design-audit/embedder-e0-e1-20261020/e1-opt1-regression.json)
passes all 65 selected tests with unchanged inputs. Its exact preconditions test
source is retained in
[the tested snapshot](evidence/design-audit/embedder-e0-e1-20261020/opt1-regression-test_group_preconditions_native.txt).
After the test-only mixed-ceiling and unique-condition-ID correction, the
[final targeted gate](evidence/design-audit/embedder-e0-e1-20261020/e1-opt1-mixed-final.json)
passes both current cases with unchanged inputs: mixed 3,072 conditions over A/B
identities and native count/malformed/full-identity controls. These workloads
retain the 10s SQL/30s operation limits. They do not establish every possible
3,072-condition key/relationship workload.

[Static gates](evidence/design-audit/embedder-e0-e1-20261020/opt1-static-gates.json)
pass generated runtime correspondence, 1,526 Python import edges, 18 boundary
controls and installed positive/exact-negative consumer type checks.
[Final verification](evidence/design-audit/embedder-e0-e1-20261020/final-verification.json)
binds the same 412 runtime files across broad and targeted runs to final source,
the current test file to the targeted receipt, and the retained prior test file
to the broad receipt. The [final test delta](evidence/design-audit/embedder-e0-e1-20261020/final-test-delta.json)
confirms that imports, helpers and other methods match the broad snapshot;
only the two requalified methods differ. Governing frontmatter remains unchanged.

E0/E1 implementation, focused review and local qualification are complete for
the exact [cohort](evidence/design-audit/embedder-e0-e1-20261020/cohort.json)
and unpublished development wheel: macOS ARM64, PostgreSQL 18.6, Python
3.11.17, psycopg 3.3.6 and Weft 0.4.48. Original failed receipts remain retained.
This is selected-subset qualification, not full-suite, platform, managed-service,
upgrade or published-release qualification. E2 and later slices remain unfinished.

## Risks and Rollbacks

| Risk | Response / rollback |
| --- | --- |
| Larger condition inventory exceeds other bounds | Refuse the whole group at the governing bound; retain documented lower profile if qualification fails. |
| Permission mapping masks uncertain transaction state | Translate only contained `execution_obligation` / `42501`; retain other original execution errors. |
| Wrong conflict index or hidden-key disclosure | Consume only trusted closed ordinal DETAIL; retain exact original artifact; never query after failure. |
| Added error accessors alter historical replay | Keep retained native bytes and old outer `group_failed` tag; test original replay equality. |

## Exit Criteria

Design readiness requires owner contracts, scoped tests, source map and exact
commands. E0/E1 execution completes only after focused native and installed-wheel
gates, consumer documentation, measured actual baseline, recorded cleanup and
focused code review. Planning amendments do not establish implementation success.

The continuation evidence above meets these execution criteria for the selected
local E0/E1 subset. E2 continuation design does not establish E2 implementation
or larger-import/performance completion.
