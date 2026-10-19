---
ddx:
  id: truss-practical-performance-matrix
  type: test-plan
  activity: test
  status: draft
  owner: Erik LaBianca
  updated: 2026-10-18
  links:
    - id: truss.prd
      kind: informed_by
    - id: TP-001
      kind: informed_by
---

# Practical functionality and performance

## 2026-10-18: bounded journal successor under qualification

The C80 hosted run exposed wide-update timeouts and native capacity failures;
it is not a release qualification. The successor retains the complete original
workloads and deadlines. Its independent update producer writes history in
internal sets of at most 64 objects, with the original exact journal proof for
each set and the original four transition fingerprints afterward. All sets
execute within one protected native call and its single 10s SQL deadline.
An error in a later set rolls back the whole operation, preserving caller work.
For 1,000 changed objects, statement observers see 16 journal INSERTs; the
object UPDATE and transition INSERT remain set based. Frontend guard submissions
are unchanged. This bounds the number of objects in journal intermediates;
server peak memory has not been measured.

Permanent native controls cover 63/64/65-operation boundaries, mixed no-ops,
complete metadata, global event order, ordered digests and compact references,
an all-no-op group, and suppression in the second journal set. Separate graph
cleanup avoids edge counts for unrestricted multiplicity sides while retaining
bounded checks, both permission phases and marker verification. No timing gain
is claimed for that cleanup. Final installed-wheel and hosted evidence is pending.

## 2026-10-18: C80 real schemas pass; hosted failures retained

The [installed-wheel real-schema run](results/2026-10-18-c80-real-schemas.json)
passes Pizza, Northwind and catalog in 101.105 seconds. Each original schema
registers, creates 1,000 objects of its selected benchmark record type, lists
51 complete entities, performs 1,000 ID reads and 100 key reads, commits 200
individual updates and verifies values after reopening. These are public API
workflows, not browser UI or synthetic stress qualification. Separate native
embedder tests exercise every original record and relationship.

Median committed-update times are 20.88/19.34/18.37ms for
Pizza/Northwind/catalog; p95 is 34.38/21.32/24.10ms. Each fresh-transaction update
makes ten frontend SQL submissions, including BEGIN, transaction adoption,
context acquisition and apply; COMMIT is recorded separately. Fresh registration
uses three submissions. Schema preparation takes 512/368/309ms and registration
116/183/187ms. External Bun/Node processes are forbidden during the run. Python
peak RSS is 201,064,448 bytes, including embedded libraries; the retained schema
cache estimate is 332,056 bytes in two entries. These are distinct measures.

All 528 runtime payloads match committed source
`109d474a3df68fa8de2d29f87557b020c2d70486` independently. The full unchanged
eleven-case/two-platform run
[39176421417](https://github.com/DocumentDrivenDX/truss/actions/runs/39176421417)
exposed wide-update timeouts and native-gate failures. It does not qualify the
release. No full matrix or publication success is claimed by this local receipt.

## Dense relationship source boundary

Query ABI 1.1 admits complete source bags of at most 10,000 rows per record or
relationship type before caller predicates. The unchanged dense workload has
500,000 edges across ten relationship types: 50,000 per relationship. Its
complete-entity list therefore receives a whole-query resource refusal even
though each object's 50 outgoing keys fit the separate 100-key bound. A list
limit does not qualify a smaller source bag under this ABI.

The driver records this exact source-bound negative, checks the native reason,
and requires a successful 51-row scalar list with exact original values. It
still loads and verifies all 10,000 objects and 500,000 edges, and runs every
declared ID/key read, committed single write and five repetitions of each
supported atomic update size. This does not qualify complete-entity dense
lists. Selected-endpoint source pushdown needs a separately qualified compiler
and provider ABI; raising the bound or returning partial relationship keys is
not part of this change. The million-node object-source and skewed per-object
relationship-cardinality boundary tests remain separate.

The [isolated boundary control](results/2026-10-18-query-source-boundary-control.json)
passes on the C79 installed wheel with 102 objects and 10,001 edges in one
relationship, at most 99 outgoing keys per object. It verifies the source-bound
refusal and the exact 51-row scalar list under the unchanged deadlines. This
small boundary control is not the declared 500,000-edge stress qualification.

## 2026-10-18: C77 focused controls; hosted qualification pending

The [C77 controls](results/2026-10-18-c77-local-controls.json) pass twelve
focused native regressions across two invocations, retaining the exact command and original test output.
They cover a single 1,000-distinct-type create batch through deferred checks and
commit, exact values and history for 1,000 updates, source-admission boundaries,
the retained edge-planner oracle, feed delivery, the eight-key capacity case and
protected-query activation with the selected compiler cohort.
Original schema bytes are compared once per document within each admission call;
the current owner and writer checks still run for every admitted operation.
Relation lookup starts from the affected type's endpoints in both planning and
native graph validation. This is local evidence, not a passing hosted matrix.

The earlier [C76 index-heavy diagnostic](results/2026-10-18-c76-index-heavy-diagnostic.json)
loads the full 10,000 objects and 20,000 edges, then commits all five repetitions
of each 1/100/1,000/1,024 update size. Median 1,024-update apply time is 4,350ms,
with a separate 1,327–2,165ms commit. It uses 1,000-row load batches instead of
the declared hosted case's 100 and enables function profiling. Its bulk-100
speedup of 4.710 is below the initial 5× triage threshold. Preserve those
differences and that signal; this diagnostic does not replace hosted qualification.

## 2026-10-18: C75 successor failures and graph diagnostic

[C75 run 39167394688](https://github.com/DocumentDrivenDX/truss/actions/runs/39167394688)
uses source `d40e5570ed78136ed6e91060d22f4271303dd260`. Its
[immutable package comparison](results/2026-10-18-c75-hosted-package.json)
checks all 528 runtime payloads, including the Python host. The macOS native
job still times out on the eight-key, 1,024-operation batch. The Linux native
job exposes a stale oracle test that clones the old two-argument planner wrapper
instead of its application-aware implementation. Neither is a passing release gate.

A separate [1,000-distinct-type diagnostic](results/2026-10-18-c75-graph-diagnostic.json)
also times out while creating all 1,000 objects in one atomic group, before any
update is attempted. Loading the fixture in ten groups and successfully updating
1,000 objects does not establish this create capacity. The graph validator scans
unrelated relationship definitions for each object. A selected-endpoint lookup
reduces the standalone authorization query from 2.512ms/9,046 buffer hits to
0.175ms/32 hits; the successor must still pass the complete create operation,
deferred checks and caller commit under the original deadlines.

## 2026-10-18: C73 hosted failures; successor under test

[Run 39164763845](https://github.com/DocumentDrivenDX/truss/actions/runs/39164763845)
tests source `7fcb4c5a9719c1a9a86468e1a2a05510cbf8c80b` against all eleven
unchanged workloads on Linux x86_64 and macOS ARM64, alongside both complete
native release jobs. The [failure snapshot](results/2026-10-18-c73-hosted-failures.json)
records container-oracle, wide, many-type and eight-key/index-heavy SQL timeouts.
The run was cancelled after preserving its failures when its replacement was ready.
This candidate cannot be published.
Its replacement is under test with unchanged deadlines and workloads.

The [C73 controls](results/2026-10-18-c73-local-controls.json) identify the exact
installed wheel and native runtime. Production writes reuse one compiled schema
across records, facades and transactions, with current native permissions checked
on each call. Separate controls cover disjoint writer selections, newly granted
modules, independent scalar/container parity and the genuine 1,000-type workflow.
The 12,000-property application schema occupies an estimated 8,124,944 bytes;
the shared retained cache totals 58,274,659 bytes within its 128MiB budget. These
are object-graph estimates, distinct from measured process RSS.

Independent updates retain one shared original snapshot and compact per-operation
patches rather than duplicated value maps. Full before/after history and all four
transition intent fingerprints remain. A local 1,024-object, 128-field update
passes in 9,533ms plus 2,181ms commit, with 1,024 exact history witnesses and zero
mismatches. Its SQL margin is narrow; this is not a hosted capacity claim or the
full 10,000-node/20,000-edge wide workload. The unchanged eleven-case matrix must
still pass on both platforms before publication, with 10s SQL/30s operation
deadlines.

## 2026-10-18: superseded C64 local controls

The [C64 record](results/2026-10-18-c64-local-qualification.json) identifies the
exact installed wheel and native manifest. Its 26 focused controls pass, including
all three real schema workflows, a populated upgrade, conditional writes and a
complete-entity list over the original 1,000-type catalog. The 1,024-object wide
diagnostic also passes, with every before/after history record matching the
retained reference helper. It has no edges and does not replace the full wide
workload.

The successor removes repeated finalization history reconstruction, initializes
native catalog indexes in set-based stages and resolves condition definition pins
before reading their sources. Weft 0.4.42 fixes the actual 1,000-type compiler
request within the existing byte limits and indexes original element coordinates.
Its scale diagnostic stopped at a completed batch boundary after 379,000 nodes
and zero edges when this candidate was superseded. No failed operation was
observed; the run did not complete the declared workload. The final production
application-cache candidate must repeat the unchanged full hosted matrix. SQL
and operation deadlines remain 10s and 30s. These local passes are not a release
or full qualification receipt.

The [C65 compatibility record](results/2026-10-18-c65-compiler-compatibility.json)
retains the same native SQL and enrolls exact hosted Weft 0.4.42 wheel identities
for the existing protected-query flow. Five native permission/activation controls
and the public policy example pass; the latter uses an explicitly missing Bun
executable. This enrollment adds no new query ABI or protected capability.

The embedder's captured findings are covered by the
[original-schema workflows](../../../../packages/python/tests/test_embedder_workflows_native.py)
and [condition precedence regressions](../../../../packages/python/tests/test_condition_precedence_native.py).
Whole-entity lists use `SELECT x.*`; repeating a relationship's existing output
name remains a `WFT-OUTPUT-NAME` refusal. Original unnamed definitions retain
stable-ID lookup rather than acquiring invented names. First writes, committed
lists, open/modify/reopen and failed-condition precedence are exercised through
the public toolkit. The C65 registration/precedence subset passes all six tests.

## 2026-10-18: superseded C61 qualification

The candidate's [local qualification record](results/2026-10-18-c61-local-qualification.json)
identifies the exact runtime and wheel. All three original sample schemas pass
registration, seed, list, open, modify, commit and reopen. A separate public
benchmark performs 1,000 ID reads, 100 key reads and 200 committed single updates
per sample with external JavaScript forbidden. Median committed updates were
20.7–22.7ms; 51-row complete-entity lists took 290–367ms. These are local
observations, not service-level guarantees.

The added 1,000-type regression creates and reopens 100 distinct object types
and 100 distinct relationship types. Indexed pin resolution avoids catalog-wide
source scans. Eligible key codecs compile once per revision; decoded property
definitions are reused during initialization. The unchanged eight-key,
1,024-operation capacity, populated native71 upgrade, permission revocation,
history and original-intent tamper controls pass locally.

[Targeted hosted qualification](https://github.com/DocumentDrivenDX/truss/actions/runs/39153969605)
failed. The [full 11-case/two-platform matrix](https://github.com/DocumentDrivenDX/truss/actions/runs/39154235495)
exposed many-type compilation, wide-update and eight-key update failures. The
local million-node workload stopped after 173,000 committed creates when the
next 1,000-create group exceeded its SQL deadline. This candidate was not
released. Its successor must repeat the complete matrix; these local passes
are historical evidence, not a release receipt. SQL and operation deadlines
remain 10s and 30s.

## 2026-10-17: both complete hosted release jobs pass

[Run 39084247653](https://github.com/DocumentDrivenDX/truss/actions/runs/39084247653)
passed packaging and both complete native jobs on exact runtime source
`47416d511926901c10954e8640e31a5dcbaeba98`. Both platforms passed original
1,024-operation capacity, overflow and late rollback controls, the analyzed
1,000-key custom/generic caller-mode regression, and the unchanged full small
public workload. Every subsequent release regression also passed. SQL 10s and
operation 30s budgets were unchanged. The separate clean local run passed all
31 focused native controls in 101.145 seconds.

The [qualification record](results/2026-10-17-final-hosted-qualification.json)
retains exact wheel identity, measurements and limitations. Linux's 1,000 creates
applied in 2.053 seconds and committed in 1.367 seconds; macOS's applied in 2.999
seconds and committed in 2.777 seconds. Five changed 1,000-object update groups
applied in 3.515–3.938 seconds on Linux and 6.475–7.798 seconds on macOS. Each
platform also committed and read back every group. These are observations from
one original workload campaign, not stress or p95 certification.

The compressed full reports retain their checkout-dirty flags and explicitly
unevaluated performance qualification. Independent verification matched all 90
catalog wheel payloads including the manifest, host/activation code and
embedded delivery manifest to the pushed source. The public workload recorded
no external process executable; its external-JavaScript prohibition flag was off.
The separate missing-Bun adopter and embedded-runtime controls cover deployment.
Native71 and package 0.0.39.dev0 remain unreleased. Stable Bun-free 0.0.38 is
unchanged; this campaign does not publish a new version.

## 2026-10-17: reuse plans inside private point lookups

[Run 39083626733](https://github.com/DocumentDrivenDX/truss/actions/runs/39083626733)
again passed the original capacity controls but failed the analyzed 1,000-key
update with forced custom plans on both platforms. Metadata reuse alone was
insufficient. All 89 expanded local regressions passed, including original
catalog key backfill, keyed rebind and typed-key workflows.

Four repeatedly invoked private lookup functions now declare function-local
`plan_cache_mode=force_generic_plan`: reader authorization, key bucket locking,
final object row validation and final graph object validation. This amortizes
planning for their repeated indexed lookups. It does not cache query results,
authorization decisions, key observations or physical images. All queries still
execute. PostgreSQL restores the caller policy on function exit; outer batch
queries retain the caller setting and the analyzed-history test still exercises
both caller modes. This is an explicit internal plan policy, not an assertion
that each nested query uses the caller's forced mode. The original deadlines,
checks and independent commit triggers remain unchanged.

A serial instrumented disposable-fixture comparison reduced custom-mode apply
from 4,912 to 3,674ms and commit from 5,068 to 3,006ms. Generic-mode apply remained
approximately 2.7 seconds and commit 2.0 seconds. These are single local diagnostic
observations, not hosted or p95 qualification. The [raw function counters](results/2026-10-17-reusable-point-plans-profile.json)
retain this scope. Full hosted scale and integrity gates are still required.
Twenty-one native scale/authority/rollback controls passed, followed separately
by all ten collision-bucket controls in 13.160 seconds. The latter fixture
previously reinstalled a predecessor helper and supplied pre-feed reservation
bytes; it now uses the installed helper and current writer-XID fixture bytes.
Those ten controls are added to the existing hosted typed-key gate. No native
guard is disabled. Native71 remains unreleased.

## 2026-10-17: compile native key metadata once per phase

[Hosted run 39082059330](https://github.com/DocumentDrivenDX/truss/actions/runs/39082059330)
passed the original capacity controls but failed the added analyzed-history,
forced-plan 1,000-key update on both platforms. Full public workloads were skipped.
Profiling showed thousands of identical source-definition walks alongside
per-value checks. Each read-only preflight and batch phase now compiles the
original native key metadata once per type/key. Every value retains the original
source-domain validator and encoder. The cache is invocation-local, bounded at
4 MiB, and falls back to fresh compilation without imposing a new source limit.
The public derivation wrapper retains source validation and refusal ordering;
planned catalog basis derivation is preserved. Complete membership coordinates
also constrain each existing-key lookup independently of row estimates.

The analyzed-history test and four independent native key derivation controls
passed in 32.865 seconds. A separate instrumented comparison measured custom-plan
apply at 4,912ms versus 5,574ms before compilation reuse; generic-plan apply was
2,635ms versus 2,909ms. Commit remained approximately 5.1/2.0 seconds respectively.
These single local diagnostic observations establish neither hosted qualification
nor p95 performance. The original SQL/operation budgets, caller optimizer settings,
independent finish/commit guards and full hosted release gates remain unchanged.
Native71 remains unreleased.

## 2026-10-17: stable plans as attempt history grows

The full hosted workload exposed a statistics-dependent regression: repeated
1,000-update calls grew until macOS exceeded the original SQL budget. Actual
EXPLAIN ANALYZE showed current-attempt cardinality estimated as one row and
nested loops discarding nearly two million event/digest join pairs. Switching
between generic and custom plans did not remove the structural problem.

Ordered window aggregates now carry event context and compute each group digest
once. Complete-key parameterized lookups close physical plans, transitions and
journals; ordinal maps seal results without a history-sensitive UPDATE join.
All original comparisons and independent commit guards remain. The engine
preserves caller optimizer settings and both original deadlines.

The [focused native checks and actual-plan evidence](results/2026-10-17-planner-stable-batches-qualification.json)
cover custom and generic plans after ANALYZE, retained key reservations, no-ops,
late rollback and both retained semantic oracles. Across five repeated updates,
with 200 preceding small writes and explicit statistics refreshes, journal
history grew from 5,410 to 13,410 rows while both plans discarded zero join
pairs. Public update calls remained between 2.72 and 2.97 seconds on the local
machine. Extra diagnostic queries ran separately; these are not p95 or hosted
qualification. The full original hosted gates remain required before native71
publication.

## 2026-10-17: relational update closure and buffered graph scope

Distinct stored rootless updates under the captured current catalog now close
plans, native transitions, public results and physical journals as SQL relations.
Expected event meaning and ordered digests are reconstructed independently from
original source metadata and transition images. Full final-graph checks and
independent row/journal/commit guards remain. Historical catalog heads and other
operation shapes retain the general validator. Source/type compilation shares
only exact bindings within each read-only phase; original per-reference scope
and planner admission still runs.

Graph observation buffers incident edge images and assembles its map once,
preserving discovery order, bytes, bounds and both required observations.
The [66 native checks and incremental diagnostics](results/2026-10-17-relational-update-closure-qualification.json)
include comparisons with the retained general update validator and retained
graph observer, a stored 1,000-edge graph, key-changing updates, no-ops, later
groups in one transaction, late rollback and all preceding integrity checks.
The previous hosted run passed both capacity gates and the complete macOS
workload; Linux still timed out in general update closure. The unchanged scale
gates now run earlier in CI, followed by every existing regression gate.
Native71 remains unreleased; full final hosted qualification is still required.

## 2026-10-17: set-based stored-object updates

Distinct stored-object updates without ownership changes now use one object
UPDATE and batched key, journal and transition writes. The complete ordered
key preflight remains, including forbid-reuse simulation and original bucket
locks. Unchanged memberships keep their original bytes and old reservations
survive. Duplicate targets, aliases, mixed groups and ownership changes keep
ordered execution. Final stored identities use the same exact reference check
as the identity helper directly in SQL; genuine creates retain its sealed-slot checks.

The [serial local comparison and native qualification](results/2026-10-17-set-based-update-summary.json)
measured a 1,000-update call at 5,468 → 4,483 ms; commit was 2,445 → 2,471 ms.
This is one shortened diagnostic repetition on the original 1,000-object/edge
model, with complete readback and external JavaScript launches forbidden.
All 64 affected native tests passed, including key-changing batch statement
counts, old reservation retention, no-op preservation, late rollback, replay,
corrupt slots/journals, authority revocation and protected activation. The
original full hosted Linux/macOS gates remain required; their preceding run
passed creates but exposed the update bottlenecks recorded in the comparison.
Native71 remains unreleased and both deadlines remain unchanged.

## 2026-10-17: set-based independent creates

Independent rootless object creates and independent stored-endpoint edge creates
now use one INSERT per physical home. Plans insert as a set; pure edge planning
buffers new states instead of repeatedly copying/counting a growing JSONB map.
Definition/source admission is shared per exact CREATE pin within its read-only
phase. Mixed and ownership-changing groups retain ordered execution.

The [serial local comparison](results/2026-10-17-set-based-create-summary.json)
measured 1,000 objects at 5,375 → 2,133 ms plus commit 2,477 → 1,132 ms;
1,000 edges at 5,685 → 3,605 ms plus commit 3,196 → 2,663 ms.
These are single macOS ARM64 observations on PostgreSQL18.6/Python3.11,
not hosted-runner or broader workload qualification. Both deadlines remain unchanged.
The [native checks and statement budgets](results/2026-10-17-set-based-create-qualification.json)
cover capacity, replay, revocation, corrupt plans/results/journals and late rollback.
The [original three example schemas](results/2026-10-17-set-based-create-real-samples.json)
each registered and committed 1,000 representative objects with external JavaScript
launches forbidden. Main's existing compact registration was used; this does not
claim that published v0.0.38 contains that path or changes host guard counts.


First run the unmodified pizza, northwind and catalog examples through public
registration, data loading, reads, updates and database reopen. Verify actual
returned and persisted values. A failure stops that workflow and is a product
failure, not a performance result. Do not replace the examples with smaller
fixtures, add missing optional names, or remove their actions to get a pass.

Use `workloads.json` for a small set of contrasting workloads. It varies type
count, field count/complexity, node count, edge density/skew and indexed
properties. The current scalar generator uses strings. Mixed adds integers,
booleans and exact decimals; wide workloads also include absent properties.
Nominal and index-heavy keep all potential key fields required. Mixed-nested adds a
map → array → decimal property. Keys are independent single-property unique
business keys. Explicit nulls, bounded strings and composite keys are not yet
represented. Equal field counts do not imply equal complexity.

| Point | Types | Properties/type | Shape | Nodes | Edges | Key properties/type |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| Small | 1 | 4 | Strings | 1,000 | 1,000 | 1 |
| Nominal | 10 | 12 | Mixed | 10,000 | 20,000 | 2 |
| Type-heavy | 100 | 12 | Mixed | 10,000 | 20,000 | 2 |
| Many-types capacity | 1,000 | 12 | Mixed | 10,000 | 20,000 | 2 |
| Wide | 10 | 128 | Mixed | 10,000 | 20,000 | 2 |
| Nested | 10 | 12 | Map/array/decimal | 10,000 | 20,000 | 2 |
| Dense | 10 | 12 | Mixed | 10,000 | 500,000 | 2 |
| Index-heavy | 10 | 12 | Mixed | 10,000 | 20,000 | 8 |
| Skewed | 10 | 12 | Mixed | 10,000 | 20,000, concentrated | 2 |
| Large | 10 | 12 | Mixed | 1,000,000 | 2,000,000 | 2 |

All points are planned until an actual result is recorded. Type-heavy tests a
runnable increase in catalog size; many-types additionally exposes the current
input-size capacity bound. Keep the nominal dataset identical when changing one
axis. Skew concentrates 95% of edge sources on 1% of nodes.

Start with smoke, then standard; run million-node and thousand-type cases
explicitly as extended runs. Generate deterministic data. Load every measured
case through public APIs and commit it. Never populate private tables to hide
loading overhead. Report unsupported data shapes, rejected declared indexes,
capacity limits, setup time and setup failures rather than skipping them.

An indexed property counts only when the database actually maintains a usable
index for it. Record declared versus installed indexes, index size and readiness.
A key's uniqueness index is distinct from an optional lookup index. An index
that is merely declared or pending does not count. Compare identical datasets
before/after indexes, including the cost of index creation and maintenance.

Measure these operations on each runnable workload:

- Cold process/database start, schema preparation and committed registration,
  separately. Include schema bytes and peak temporary preparation bytes.
- Warm point reads by ID and business key; bounded type pages; indexed and
  unindexed predicate queries; one-, two- and three-hop traversals. Verify results
  against known generated identities and values before timing repeated calls.
- Committed single-record create/update/delete, including journal and key/index
  maintenance. Separate changed updates from no-ops. Do not call replay a write.
- Bulk load/update at 1, 100, 1,000 and 10,000 records per request where supported.
  Include serialization, validation, execution, journal maintenance and commit.
  Confirm row counts and values after reopen. Report both latency and rows/s.
- Edge creation/removal and indexed-property updates, so edge guards and index
  write amplification appear in the results. Compare skewed and uniform graphs.

Use a quiet local PostgreSQL socket and record machine, runtime, library version,
connection mode, durability settings and initial database size. Separate one-time
setup from warm work, but do not subtract it from an end-to-end number. Run the
same useful operations against a straightforward PostgreSQL baseline on the same
machine with equivalent keys, indexes, journal and durability; a bare unjournaled
INSERT is not an equivalent write. Keep preparation/Bun calls and SQL round trips
visible. Do not silently warm away a subprocess launched on every operation.

Retain one ordinary CSV/JSON result file and a short comparison table, not full
inspection transcripts. Include requested/attempted/completed/failed operation
counts, sample count, p50/p95/p99, max, rows/s, input/result bytes, peak memory,
database/index/WAL growth and round trips where measurable. Use monotonic wall
time around the public call and caller commit; show database statement/commit
time separately. Never drop timeouts or failures from the result. No p95 claim
from five bulk repeats: report all five and their median/range instead.

## Napkin math

Fit a simple cost budget from measurements rather than assuming every operation
is cheap:

`batch time ≈ fixed request cost + rows × row work + changed properties × journal work + changed keys/indexes × index work + changed edges × edge work + commit`

Read time should mostly follow index depth, rows returned and bytes decoded.
Increasing unrelated types must not trigger a full-catalog walk per point read.
Unchanged schema validation/compilation should be paid at registration, rather
than repeated for each record. Compare batches of 100 and 1,000 with individually
committed writes; genuine bulk work should amortize fixed costs. Compare predicted
and observed values and investigate a 2× nominal regression or a bulk speedup
below 5× as initial triage signals, not achieved guarantees or contractual limits.

The PRD's proposed p95 budgets (1 ms point read, 3 ms single write and 20 ms type
enumeration) remain provisional. Report full public-call-plus-commit measurements
against them without relabeling SQL-only microbenchmarks as application latency.
The million-node/thousand-type PRD scale is a measured target only after that
specific workload actually runs. Replace provisional budgets with explicit
measured and owner-agreed budgets as results arrive.

## Run the real-sample baseline

```sh
python scripts/benchmark-public-workflows.py \
  --truss-root /path/to/truss \
  --examples-root /path/to/hohfeld/examples \
  --output /tmp/truss-public-performance.json
```

Use the normal native-test dependencies and the selected PostgreSQL package.
The runner creates and cleans up its own isolated local database. Existing native
fixture helpers perform installation/role setup only; all measured business work
uses public assembly calls. Its default is 100 created records per example,
1,000 warm ID reads and 200 committed updates, followed by fresh-connection value
checks. The initial data slice uses Country in pizza, Category in northwind and
UseCase in catalog. It registers the complete unmodified schema but does not yet
replay all Hohfeld seed actions or exercise every application type. The generated
matrix creates data across all of its declared record types. Single update timing includes BEGIN/adoption, the public update and COMMIT.
An initial read obtains its version; subsequent writes use the returned version.
No extra application read is inserted into every timed write. Database-enforced
validation, key maintenance and journal work remain inside the timed operation.
Run a selected synthetic case with `--matrix-case small` or `--matrix-case nominal`
instead of `--examples-root`. The executable matrix currently uses unique business
keys to vary actually maintained indexed properties; it does not pretend those
are optional nonunique lookup indexes. It creates the requested types, fields,
nodes and edges through public APIs, verifies values/counts, and measures bulk
updates at the selected sizes. Synthetic execution remains pending the real
registration repair; declaring the matrix does not establish a performance result.

Initial run against the current development source, before simplification:
PostgreSQL installation succeeded for all three samples; preparation refused
pizza in 2.47 seconds, northwind in 2.37 seconds and catalog in 2.06 seconds.
All three workflows failed, so bulk/read/update throughput remains unmeasured.
These are single observations, not p95 results. The raw result is a temporary
benchmark output, not required registration metadata.

The current executable driver measures registration, catalog views, committed
bulk creation, ID/key reads, committed single updates, bulk updates and edge
loading, with value/count checks after reopening connections. Traversal, delete,
optional lookup-index creation and WAL/memory instrumentation remain additional
work; no result for those operations is implied by the current driver.

Modern owned groups now admit 1,024 operations; legacy rootless groups retain
128. The runner expects 1,024 by default. Use `--expected-group-limit 128` only
to reproduce the old baseline. Configuration alone does not qualify execution.
Measure 1/100/1,000/1,024 atomic updates where enough nodes exist; record 10,000 as
outside the configured capacity. A multi-transaction 10,000-row load is a separate
throughput workload, never one atomic group. Verify 1,025 receives a typed refusal
in the engine boundary test. Other byte/value limits still apply.
The thousand-type schema exceeds the current 1 MiB preparation bound; report that
capacity refusal. All host adoptions use 10 s statement / 30 s operation budgets.
The runner performs the configured 20 warmup ID reads after value verification;
bulk sizes and repeats come from the matrix configuration.

## First real workflow measurements

The [raw native baseline](results/2026-10-15-native-baseline.json) ran on the local
development source after the registration summary repair. This is an initial
diagnostic run on a shared development machine, not a quiet-machine release budget.
All three complete schemas registered and loaded 100 objects. Pizza and catalog
completed 200 committed updates and connection-reopen checks. Northwind failed
on update 84 with `GroupUnavailable(reason='observation')`; 83 succeeded.

| Sample | 100-row create + commit | Commit alone | ID-read p95, 1,000 calls | Single update + commit p50 / p95 |
| --- | ---: | ---: | ---: | ---: |
| Pizza | 70.51 s | 50.72 s | 208.53 ms | 434.26 / 693.97 ms |
| Northwind | 66.75 s | 46.08 s | 133.41 ms | 728.97 ms / insufficient successful samples |
| Catalog | 184.47 s | 161.27 s | 92.96 ms | 897.78 / 1,451.76 ms |

These results fail the provisional nominal latency expectations by large margins.
Fix and profile ordinary request/commit work before spending hours on large stress
points. No synthetic matrix pass or 1,024-operation support is established here.

The first [small matrix execution](results/2026-10-15-small-before-fix.json)
also failed: one type with four string properties loaded 1,000 objects in
767.39 seconds across ten committed groups. Group execution consumed 191.89 s;
commit consumed 575.48 s. The first 100-edge group was cancelled with SQLSTATE
57014 after 22.88 s. No point-read, single-update or bulk-update result was
obtained for this matrix point. This is a failed practical baseline, not a
qualified throughput claim.

The isolated [graph-check comparison](results/2026-10-15-catalog-graph-fix.json)
passed the same catalog 100-object / 1,000-ID-read / 200-committed-update workflow.
Commit fell from 161.27 s to 12.06 s; complete load fell from 184.47 s to 40.91 s.
Single-update p95 remained 976.97 ms. This is a meaningful improvement and still
a failed nominal performance result. The shared machine was quieter in this run;
do not attribute unrelated point-read latency differences to the graph change.

Actual 1,024-create boundary attempts on isolated reviewed candidates still failed
under the unchanged 10-second statement / 30-second operation budgets. After
fixing a native SQL CASE syntax error, repeated CREATE type resolution timed out
in capture. Distinct-type resolution moved the timeout into whole-graph planner
work. The focused CREATE delta/counter fast path moved it into another per-operation
owner/type/reader authorization loop in `object_group_begin`. The last test ran
28.44 s and returned cancellation SQLSTATE 57014; it did not reach a successful
1,024-row commit. The 1,025 admission refusal worked. No capacity pass is claimed.
Further local optimization patches are paused for a short review of which
duplicate planning and validation layers should be removed from ordinary writes.

## Simplify the ordinary write path

Astra's source review traced a structural cause: ordinary writer roles can call
separate native begin/metadata/step/finish functions. Persisted graph plans,
completion witnesses and nested create groups then try to prove that the client
finished this protocol. CONTRACT-009 requires complete affected sets, lock
revalidation and ordered final-state semantics; it does not require this protocol
or durable per-operation graph snapshots.

The next implementation slice is one protected native atomic batch entry and
private helpers, with transient ordered state, one actor/dependency admission
pass, ordinary key/graph checks, actual journal/results and optional request
receipt. Keep current authorization at the operation/commit boundary. Remove
duplicate execution-proof writes as their consumers are redirected. Preserve
existing history and replay: current history readers use transition validators
and creation leaf-group data, so those consumers must move before new duplicate
records stop. Current accepted definitions should not be reconstructed from
entire original documents on every property read.

This records the proposal at that point in the investigation, not a performance
qualification. The atomic public entry was subsequently integrated; unused
context/resolver-wrapper and transient-planning prototypes were shelved. Current
work targets measured costs in the actual public apply and commit path.

### Bounded diagnostic after create-storage removal (2026-10-16)

The full unmodified Catalog schema registered and a one-record public workflow
passed on runtime manifest `fe8f4bde7ed2ff4bcbfb5829621fa9d84fdde1380fb220549158a37823e05da2`.
One create including commit took 1,538.92 ms. Five single updates including commit
had median 452.15 ms (range 440.28–473.37 ms); this sample does not establish p95.
Twenty ID reads had median 18.11 ms; twenty key reads had median 50.14 ms.
Native profiling was enabled, so this is a diagnostic run on the shared machine,
not a release benchmark or a comparison with different-sized prior workloads.

Across the complete workflow, `runtime_person` ran 1,074 times and consumed
2,199.42 ms self time. Historical catalog reconstruction still ran 120 times.
The remaining work is shared per-operation authorization/metadata context and
transient planning, followed by the requested 1,024-operation and stress runs.
The observed costs remain a performance violation. Raw measurements:
[diagnostic result](results/2026-10-16-direct-storage-small-profile.json).

### Isolated actor-scan experiment (2026-10-16)

Moving the reachable-role ACL scan to the final authorization predicate and
removing its duplicate actor scan passed source review and three existing native
privilege-path controls. On the same small Catalog workload, candidate update
median was 496.61 ms versus 560.87 ms in an immediately following original-code
control (five updates each). Create including commit was 1,116.79 versus
1,457.85 ms. Shared-machine timings varied; this does not establish nominal
performance or p95. The experiment remains isolated and is not integrated.
A concurrent upstream statement-overhead change takes precedence for merge
verification. Raw candidate and control JSON are retained in `results/`.

### Corrected statement-overhead merge diagnostic (2026-10-16)

The same small Catalog workflow passed on runtime `a9806ff6f8e6bb04e27a06769871fd9a1465f0fb1c6b3bf6e7f4d5b02409d905`,
with a real final host observation retained after callback execution. One create
including commit took 992.85 ms. Five updates had median 427.65 ms, range
420.69–438.32 ms; this does not establish p95. Twenty ID reads had median
25.05 ms and twenty key reads 48.69 ms. Native profiling was enabled on the
shared development machine. Actor qualification still consumed 2,216.90 ms self
time across 1,060 reported calls. These costs remain a performance violation.
No 1,024-operation support or nominal budget pass is established by this run.
Raw data: [merged host diagnostic](results/2026-10-16-merged-host-small-profile.json).

### One-update attribution and current history basis (2026-10-16)

The profiling runner now flushes consumer counters before and after the last
committed update, outside its timing, and records `lastCommittedUpdateNativeFunctions`.
The original implementation performed 102 actor qualifications, 17 catalog
reconstructions and 12 history renders for that one update.

The isolated reviewed patch `387194d1` uses accepted native rows only when
head/schema revision and selected rows share one published SQL snapshot; older
or partially published revisions retain reconstruction. It adds no cache or
helper. Rebind, same-transaction registration and history workflows passed.
An old-catalog refusal classification mismatch also reproduces on the unmodified
baseline; it remains a separate open issue.

Final candidate manifest `7f20fdd663b50d92fa58ddaaa1a9210190b0995d745ab42fee79f77dc0f4dd99`
reduced reconstructions from 17 to 5 per update. Five update timings had median
309.58 ms (range 303.65–315.84 ms). These shared-machine diagnostic timings do
not establish p95 or nominal readiness. Actor qualification remained 102 calls
and approximately 192.62 ms self time for the last update. Performance and
1,024-operation acceptance remain open. Raw baseline and candidate profiles
are retained under `results/2026-10-16-*-profile.json`.

### Final settlement diagnostic (2026-10-16)

Reviewed candidate `e1b90c8c` retains current row authorization and moves full
immutable transition validation to final settlement and mandatory commit.
The selective constraint-flush then writer-revocation workflow passes: final
commit refuses and the original row remains. One committed UPDATE now performs
75 actor qualifications, two catalog reconstructions, two transition semantic
validations and six history renders. Actor qualification alone consumes
163.48 ms self time. Five updates have median 252.19 ms, range
239.76–254.75 ms; create including commit takes 680.03 ms. These diagnostic
measurements remain a major performance violation, establish no p95, and do not
qualify the required 1,024-operation path. Manifest:
`5d5bdd6dca8cb242c3206a96d959eb661abe61367ee98588efc2bb8939698959`.
Raw data: [final settlement diagnostic](results/semantic-settlement-single-update-20261016.json).

### Composed main and browser diagnostics (2026-10-16)

Composed native source `6a05a254` plus reviewed final-settlement changes,
manifest `83b1912f03d8fcad814c7e5ea388601f3b109bd771e9e5f8bbb48b64d54a6736`,
passes the real small Catalog workflow. Five committed updates have median
218.07 ms (215.30–231.34 ms); a create including commit takes 743.08 ms.
One update still qualifies the caller 75 times (122.92 ms self). This is not
a nominal performance pass. [Native result](results/main-composed-semantic-20261016.json).

The separate existing frozen browser provider also passes the real static-page
Foo/bar UPDATE with three unchanged rows. Passive worker RPC timing separates
execution (130 ms) from job review (28 ms) and row readback (20.8 ms); the full
page execute action takes 266.7 ms. Cold store opening takes 3.34 s. This is one
local diagnostic sample and overlaps owner native correctness work; it establishes
no percentile, causal improvement or public deployment. No external requests or
write HTTP requests occurred. [Browser diagnostic](results/browser-update-rpc-diagnostic-20261016.json).

### Distinct value-owner checks diagnostic (2026-10-16)

Candidate `18e66fb4` unions the record owner with all property and nested-item
module owners within each value-reader invocation. One committed update performs
61 caller qualifications versus 75 before this change; every distinct owner
and the separate settlement/commit invocations remain. Actor self time is
112.29 ms in this run. Five update timings range from 209.91 to 437.22 ms
(median 255.29 ms), so the variable shared-machine result does not establish
an end-to-end latency improvement. Performance remains failing.
[Raw diagnostic](results/value-owner-dedup-20261016.json).

The distinct-owner candidate also passes the existing public cross-module read
refusal, nested create/commit/read/history/query/import/reopen, and selective
constraint-flush/writer-revocation workflows. The first nested run stopped at
`QueryUnavailable(compiler)` because the test environment lacked Weft; rerunning
with the candidate's required published Weft 0.4.35 target passes. No query
assertion or model bytes were changed.

### Isolated settlement actor candidate (2026-10-16)

Candidate `0891551b` freshly qualifies each group/row settlement invocation and
passes that local actor through private permission/value/transition helpers.
Module policy locks and membership checks remain at their existing points.
No actor is retained in data, a caller flag or a cross-invocation cache.
Four focused native workflows pass, including denied direct helper execution,
cross-module reader denial, nested values and later writer revocation after an
earlier attempt-constraint flush. Astra source review is clear for this bounded candidate; integration remains
pending. The populated published 0.0.35/native68 upgrade also
passes, preserving original objects, edges and receipt replay before new
create/delete/update; all four new helpers remain owner-only after upgrade.

Adjacent shared-machine runs on the same public Catalog workflow show candidate
median 135.94 ms (134.11–143.68) versus current-main control 161.42 ms
(158.96–166.10), five updates each. Caller qualifications drop from 61 to 43;
actor self time is 62.63 versus 88.51 ms on the last committed update. Creates
including commit are 628.47 versus 619.40 ms. This is a diagnostic comparison,
not p95 or nominal readiness; performance and 1,024 operations remain failing
or unqualified. [Candidate](results/settlement-actor-qualified-20261016.json),
[control](results/settlement-actor-control-20261016.json).

### Harness accounting corrections (2026-10-16)

Failed atomic bulk updates now retain the whole BEGIN/apply/commit elapsed time
as well as phase failures. A final partial edge batch contributes public endpoint
readback samples. Nominal and index-heavy cases keep the same potential indexed
fields required and populated; only their key declarations differ. Outside
timing, each generated record type reports declared keys, objects and maintained
key rows, and mismatches fail the workflow. These are unique business keys,
not separately installed optional lookup indexes.

Machine reports now state `functionalPassed` (`passed` remains its compatibility
alias), `performanceQualification: not_evaluated`, and configured versus actually
attempted/committed atomic group sizes. A successful workflow establishes neither
the latency budget nor a maximum supported batch size. Older retained raw results
keep their original report format and measurement/generator scope.

The reviewed settlement change `0891551b` is now integrated and pushed as
`cefa8044`, including matching authoritative owner sources and persistent private
helper/upgrade checks. Its diagnostic measurements do not establish nominal
performance or successful1024-operation execution.

### Preparation and cumulative-plan diagnostic (2026-10-16)

The bounded caller-qualification change is integrated as `2bf54c59`. It retains
fresh qualification at preparation, effect, settlement and commit boundaries,
and current module policy and membership checks. The one-record diagnostic
reports 33 full caller qualifications per committed UPDATE, versus 43 before
this change. Its median of 121.55 ms across five samples overlapped another correctness run;
it does not establish a quiet comparison, percentile or nominal performance.
See the [preparation diagnostic](results/preflight-actor-qualified-20261016.json).

The same runtime then committed 16 records from the unmodified Catalog
schema (87,445 bytes) in 7,260.20 ms: 4,145.34 ms applying and 3,114.82 ms
committing, about 2.20 rows/s.
The retained 16 operation plans contain 120 before-node references and 136
after-node references: 256 total, or 16 squared. They occupy 122,297 logical JSON
bytes and 20,249 stored datum bytes; the largest logical plan is 14,151 bytes.
These measurements were read outside the timed load on PostgreSQL 18.6 with
fsync, full-page writes and synchronous commit enabled. The raw report's runtime
manifest matches the integrated native sources. Functional success is distinct
from performance qualification, which remains `not_evaluated` in this bounded
report. No 1,024-operation result is implied.

This confirms cumulative snapshot retention as an actual scaling problem.
The next change must address both its producer work and the consumers that
validate or reconstruct state from those snapshots, preserving exact transition
history, replay, current authorization and final graph checks. It must not
substitute a higher operation cap or a cache for that work. Raw measurements:
[16-record diagnostic](results/preflight-bulk16-planning-20261016.json).


### Current main, unmodified consumer workflows (2026-10-16)

Main `0dd148c0` passes all three original consumer schemas through the existing
public workflow runner. Each registers the complete source, commits 100 objects,
performs 1,000 ID reads and 100 key reads, commits 200 real changed updates and
verifies selected and unselected values on a fresh connection. These cases use
Country, Category and UseCase respectively; they do not exercise every record or
action in those schemas. The run takes 47.34 seconds on the local macOS ARM64
PostgreSQL 18.6 host with fsync, full-page writes and synchronous commit enabled.
Statement and operation deadlines remain 10 and 30 seconds.

| Original sample | 100 creates + commit | Commit alone | ID-read p95 | Update + commit p50 / p95 |
| --- | ---: | ---: | ---: | ---: |
| Pizza | 1,429.67 ms | 273.49 ms | 5.28 ms | 22.90 / 25.57 ms |
| Northwind | 2,656.32 ms | 390.30 ms | 4.57 ms | 29.21 / 31.41 ms |
| Catalog | 2,898.43 ms | 451.52 ms | 4.64 ms | 32.54 / 34.88 ms |

All sampled operations succeed. The point-read and write results still exceed
the provisional 1 ms and 3 ms p95 budgets. This is a shared-machine observation,
not a controlled causal comparison or a release performance pass. The configured
limit remains 128; actual committed group sizes are 1 and 100, with no 1,024-operation
claim. The report marks the working tree dirty because of unrelated untracked
build/evidence files; tracked runtime sources were clean at the recorded commit.
The [existing runner's complete report](results/main-real-schemas-20261016.json.gz)
retains individual samples, source/runtime identity and settings without adding a
runtime observation protocol.

### Main atomic capacity increment (2026-10-16)

The basic native capacity suite passes real 1,024-object creation, a second
one-object group in the same caller transaction, caller COMMIT, 1,024 changed
updates and COMMIT, original update receipt replay, and complete ordered public
ID/value/version readback with selected alternate-key reads. The second test
injects an error at operation index 1,023, preserves earlier caller work and
verifies zero durable group effects after the caller commits. Both pass together
in 42.676 seconds on PostgreSQL 18.6 with unchanged 10-second statement and
30-second operation deadlines. These are functional checks, not per-operation
latency measurements or qualification of every schema/action.

A separate two-test run passes published v0.0.35 upgrade followed by 129 real
creates, and modern 1,025/legacy 129 host/native refusal checks (13.254 seconds).
Source review independently verifies the retained legacy size guard; its native
refusal also encounters the unsupported legacy profile and therefore does not
isolate that guard. The initial run exposed an installation syntax error in the
CASE upper-bound expression; the parenthesized correction was regenerated and
all four checks rerun successfully. Astra Ultra clears corrected source and
basic tests. The previous 128-operation results above remain historical.

Installed-wheel CI run38879576731 subsequently fails both macOS ARM64 and Linux
x64 at the original statement deadline (`57014`) during 1,024-create execution.
The late-fault test also times out before reaching its final trigger. The local
functional pass above remains valid for that host, but capacity within the
existing deadlines is not qualified on the release runners. Keep the complete
workload and deadlines while improving the creation path; no release pass follows
from the larger admitted bound.

The next creation-path change removes a discarded `UPDATE RETURNING` progress
image: the code immediately overwrote it with a stored-row reread. The reread,
full expected progress comparison, transition reread and affected-row check stay
in place. Three existing creation-custody/progress controls and the full local
1,024-operation positive/final-fault workflows pass together (five tests,
49.921 seconds). Suite elapsed time is not a causal performance comparison;
installed-runner deadline qualification still requires its own successful run.

The following scoped change compares the stored six progress fields directly
as native SQL row values, instead of packing actual and expected progress into
temporary JSON objects. It retains full result/alias equality and the same
post-trigger reread and check order. Astra Ultra clears the source; the same
five local native workflows pass (51.733 seconds). This is another allocation
reduction, not a measured latency improvement or release-runner clearance.

A buffered preparation path now handles only empty existing graph scopes whose
operations are all exact rootless object creations. It accumulates states and
assembles the complete node map once; every other graph shape uses the original
path. The validation loop, ordered operation plans, final forest/multiplicity
checks and byte limits remain. Basic native tests compare complete inventories
against the retained general branch for singleton and mixed-type batches, reject
missing mandatory relationships without durable effects, and run the existing
owned subtree/reparent/cascade/history/retry workflow (three passes,12.591s).
The unchanged full1,024-create/update/commit/replay/readback and final-operation
fault checks also pass locally (two passes,41.764s). Astra Ultra clears source
and tests. These elapsed suite times do not establish a causal speedup. Earlier
installed-runner failures remain open pending the new exact wheel check.

Transient built-in PostgreSQL function statistics on main7ac63209 identify
row settlement as a remaining cost: 1,024 real requested creates take9,328.10ms
in application and5,064.01ms in caller COMMIT on the local host. The row validator
runs3,072 times with3,161.57ms self time; the creation leaf runs1,024 times with
2,960.13ms self time. These instrumented shared-host observations exclude
individual attribution of inlined SQL and are not a causal comparison. The
statistics are confined to a disposable fixture; no runtime instrumentation is
installed. CI38881630345 still fails the complete creation deadline on both
release platforms.

The row validator now projects the result-array count it actually consumes,
instead of transferring the complete growing result array into its loop record.
The original actor/writer/ordinal guards still control evaluation, and every
current authority, root, row, key, journal and group check remains. Five existing
local custody/full-capacity/final-fault workflows pass (51.685s); Astra Ultra
clears the source. Runner qualification and measured benefit remain pending.

### Write-once operation results

Modern owned execution now stores each original operation's complete result once
in its existing operation row. Pending attempts advance only scalar progress;
finish assembles and retains ordered results/aliases together with completion.
Both finish and mandatory commit compare the full arrays with every sealed
ordinal, including no-op and cascade results. The UMF owner exporter generates
the nullable fifth column. An AFTER UPDATE guard preserves source/plan fields
through all BEFORE triggers and refuses any later result replacement. Legacy
execution and published receipt/history/import carriers retain their formats.

Ten basic native workflows pass in33.344s: created/changed/no-op results and
replay, result/late-plan tamper containment, existing creation custody controls,
owned graphs/queries/cascades/history, populated published35 upgrade, and import
provenance/retry. The unchanged complete1,024-create/update/commit/replay/readback
and final-operation-fault tests pass separately in40.659s. Astra Ultra clears the
corrected source. Initial qualification failed on PL/pgSQL local-variable names;
explicit block labels corrected it before both successful runs. Local suite
elapsed times do not prove speedup; installed-wheel deadline qualification remains
open. No deadline extension or no-op workload substitution is used.

Installed-wheel run 38884918533 on main 4b596d8f still fails both Linux and macOS
with 57014 during the complete 1,024-create call; the final-operation fault test
also expires before reaching its injected P9999. Packaging passes. A disposable
local built-in-statistics run of that same commit completes all 1,024 requested
creates in 7,847.54 ms and caller COMMIT in 4,803.29 ms. Row validation accounts
for 3,022.87 ms self time over 3,072 calls; creation-leaf self time is 1,928.43 ms
over 1,024 calls. These shared-host instrumented observations do not establish a
causal improvement or release-runner qualification. The original statement and
whole-operation deadlines and the complete positive/final-fault workloads remain.

### Actual edge-phase profile

Main 430b77b9 still times out on the complete 1,000-edge group after committing
1,000 objects. A disposable diagnostic repeats that workload with the original
10-second statement and 30-second operation limits, flushing function statistics
and resetting them between the object and edge phases. Its completed edge-phase
calls include 19,966 actor qualifications (2,188.43 ms self time), 1,000 edge
effects (1,852.56 ms self time), 1,000 owned steps (1,141.35 ms self time), and
one graph preparation (1,138.67 ms self time). The cancelled statement stops in
finish-time endpoint authorization. Repeated identity and plan reads remain, but
the measured actor checks and effect/preparation work warrant priority over
additional image-helper micro-optimizations.

The [phase profile](results/main-small-edge-phase-20261016.json.gz) retains the
failed full workload and completed function counters. Cancelled active callers
may be absent from those counters; inlined SQL is not separately attributed.
Unrelated untracked files make the harness dirty flag true; tracked runtime and
harness sources match the named main commit throughout the run. No causal speedup
or release qualification follows, and no instrumentation is installed in Truss.


## Original small matrix on main7a3b — 2026-10-16

The [original result](results/2026-10-16-main7a3b-small.json) passes the unchanged
1,000-node/1,000-edge public workload on local PostgreSQL18.6 at main
`7a3b847d2a6ba77dd3a8fe3e3f4b9cdec3b7d4e8`, with 10-second SQL and
30-second operation limits. The run includes 1,000 ID reads,100 key reads,
200 committed changed updates, five repeated changed batches at sizes1/100/1,000,
independent persisted counts/keys/endpoints, fresh-connection values and successful
server cleanup. Total suite time is135.286s. Creation plus commit takes12.362s;
edge loading plus commit13.895s; median1,000-row update plus commit12.549s.

This is one local functional pass, not hosted release qualification or the larger
scale matrix. The result's dirty-tree flag includes only untracked build/cache
products; tracked source matched that commit. Bulk100 speedup3.93x remains a
triage signal, not a separate release gate. The provisional latency targets are
not achieved: ID-read p95 is6.30ms and committed single-update p95 is37.97ms.
Full Linux/macOS release validation run38970215099 is still pending.


The subsequent full [release validation38970215099](https://github.com/DocumentDrivenDX/truss/actions/runs/38970215099)
failed on both Linux x64 and macOS ARM64 at the original1,024-create statement
deadline (57014). The [original failure log](results/2026-10-16-release38970215099-failed.log)
locates macOS cancellation in final row validation and Linux cancellation in
final graph validation/current-reader checks. Each runner passes the other17
owned-workflow tests, including final-operation fault rollback. Publication was
skipped; no tag was created. This contradicts hosted readiness, not the narrower
local1,000-node/edge result above. A local diagnostic narrowing row-authority
projection showed no benefit (row-validation self1077ms versus1070ms); the
candidate was discarded, leaving all tracked runtime sources unchanged.


## Journal entity lookup correction — 2026-10-16

The history predicates now cast their CASE result to the indexed column's
`char(1)` type. Both branches remain the exact same `o`/`e` values; sequence
ordering, limits, validation and authorization remain unchanged. The
[original 1,024-create diagnostic](results/2026-10-16-journal-entity-kind.json)
records journal heap fetches falling from1,051,648 to4,096. History validation
self time falls from228.6ms to52.0ms; whole CREATE SQL from8,044ms to7,179ms.
This is one sequential local comparison, not an isolated timing qualification.

Ten original PostgreSQL18.6 tests pass in53.256s: full1,024 create/update/commit/
replay/readback,1,025 refusal, final-operation rollback, owned history/reparenting,
immutable result slots and final edge/future-slot controls. No deadline, source
census, guard, layout or routine inventory changes. The alternative ordered-slot
mechanism was not implemented:100 complete1,024-slot counts took only19.069ms.
Hosted Linux/macOS release validation remains required after this correction.

### Hosted release validation on 0ca19c23

[Run 38974408702](https://github.com/DocumentDrivenDX/truss/actions/runs/38974408702)
failed the unchanged original 1,024-operation workflow on both platforms. Linux
reached CREATE finalization and timed out in qualified row validation; macOS
completed CREATE and timed out during UPDATE finalization. Both returned SQLSTATE
57014 under the existing deadline. The other 17 tests in this step passed on each
platform. [Original failed-step logs](results/2026-10-16-release38974408702-failed.log)
retain the precise stacks. No tag was created; publication was skipped. Removing
the redundant CREATE leaf exception boundary does not establish release readiness.

### Original CREATE and UPDATE component costs on main23c5

[Stock function counters](results/2026-10-16-main23c5-function-costs.json)
record separate original1,024-CREATE and changed-UPDATE statements, each followed
by rollback and cleanup. CREATE apply_group measured4,536.7ms; UPDATE5,443.2ms
after committed original creates and the original following group. UPDATE
finalization measured1,308.7ms and original definition resolution593.1ms over
17,413 calls. These are local diagnostic observations, not hosted or isolated
performance qualification, and omit full commit/replay/readback acceptance.

An Astra-cleared candidate removed a redundant inner full-input byte comparison
while preserving its sole caller's exact comparison. The same UPDATE diagnostic
measured5,655.6ms and showed no improvement; the candidate was discarded and
source restored. No new runtime mechanism or relaxed check was retained.

### Initial-scope definition reuse — 2026-10-16

Preparation's existing type-sorted object/edge loops now resolve immutable
metadata once per consecutive type. Separate first-lookup guards preserve NULL
refusals; operation resolution and live authority checks are unchanged. This
avoids rescanning original schema text for every object of the same type.
Owner `execute.sql` and packaged `owned.sql` agree; generator `--check` passes.

The same original1,024 changed-UPDATE diagnostic passed and reduced definition
resolutions from17,413 to16,390 (1,023 fewer). Its single local apply observation
was5,353.5ms versus5,443.2ms previously; this is not an isolated speedup or hosted
qualification. Ten existing PostgreSQL18 cases passed in51.796s: original
capacity/commit/replay/readback, preparation correspondence and mandatory-edge
refusal, plan-rewrite refusal, mixed owned graphs and ordered batch updates.
Astra Ultra cleared the plan and final owner/generated source.

### Original thousand-node/edge workflow on main1a12

[The original small workload](results/2026-10-16-main1a12-small.json) passed on
main1a12f40c with1,000 objects,1,000 edges,1,000IDreads,100keyreads,200committed
changed updates and fresh-connection value/count/key/endpoint checks. Five
observations each exercised atomic1/100/1,000 changed-update groups. It used the
unchanged10sSQL/30soperation limits, fsync/full-page-writes and synchronous commit.
Total elapsed107.774s; CREATE plus commit5,349.6ms; edge load plus commit7,103.4ms;
median1,000-update plus commit11,643.6ms. This is functional evidence with local
timings, not hosted performance qualification or proof of provisional latency
targets. The exact committed runtime manifest matches the result. Its dirty-tree
flag reflects untracked build/cache files; tracked source matched main1a12.

### Full Linux release job passes; macOS capacity still open

[Run38976295079](https://github.com/DocumentDrivenDX/truss/actions/runs/38976295079)
on committed main1a12f40c passed packaging and the complete Linux installed-wheel
native job, including the original1,024-operation workflow, upgrades, current-policy
and numeric/query checks. macOS passed17 of18 owned-graph-step cases but the
original1,024-CREATE statement timed out in group-finalization identity resolution
with SQLSTATE57014. [The original failed-step log](results/2026-10-16-release38976295079-failed.log)
retains the stack. Publication was skipped; no tag was created.

A subsequent local progress-only composite projection trial passed but showed no
material whole-operation benefit: CREATE apply4,369.8ms versus4,391.6ms after
restoring committed source. That trial was discarded.

### Reuse the checked actor during metadata capture

The affected-type collection now calls its existing qualified type resolver with
capture's freshly checked actor. It previously called a wrapper that repeated the
full person/unsafe-role-graph check for each operation. No writes intervene; every
operation's source/identity/property-reader checks and later effect, settlement and
commit actor checks remain unchanged. The original1,024-CREATE diagnostic passes
and person-check calls fall from2,059 to1,035. Whole apply measured4,403.7ms versus
a recent restored-source4,391.6ms; no whole-operation speedup is established.
Ten existing capacity, actor/role/reader, owner-only helper, revoked-writer, owned
graph and plan-corruption checks pass in48.318s. Astra Ultra clears the plan and
owner/generated source, and generator `--check` verifies all manifest hashes.

### Reuse the checked attempt in creation image validation

[Release validation 38977948015](https://github.com/DocumentDrivenDX/truss/actions/runs/38977948015)
failed the original 1,024-CREATE statement at the unchanged 10-second SQL
deadline on both Linux and macOS; publication was skipped. Linux stopped in
creation image validation while reloading the attempt; macOS stopped in the
final physical-row key check. Each owned-graph step passed its other 17 cases.

Both creation image checks now pass their already-loaded and identity-checked
attempt to the existing helper. Independent plan loading, sealed create-result
checks, root identity resolution, full member uniqueness scans, authority and
image comparisons remain intact. Astra Ultra cleared the plan and source.
The proposed reference-discovery shortcut was rejected and was not implemented.
This change does not establish a timing improvement or hosted qualification.
Seven existing PostgreSQL 18 tests passed in 42.857 seconds: original
1,024-operation create/update/commit/replay/readback and capacity refusals,
owned graphs, immutable plan capture and journal-row guards. Runtime generator
`--check` verifies the packaged source hashes.

### Discarded unused-array argument trial

Astra Ultra cleared a one-call trial passing an empty operations array only for
CREATE's finishing owner lookup, whose helper does not read that argument. The
original 1,024-CREATE diagnostic passed on both committed baseline and candidate.
Whole apply measured 4,443.4 ms versus 4,336.2 ms; finish measured 1,500.8 ms versus
1,465.0 ms. A single comparison does not establish a material improvement. The
candidate was discarded and both runtime files restored exactly to main. No
new helper, cache, relaxed check or deadline change was retained.

[The subsequent installed-wheel run 38978591272](https://github.com/DocumentDrivenDX/truss/actions/runs/38978591272)
on main 5bd7569c also failed original 1,024-CREATE at the unchanged SQL deadline
on both platforms. Linux stopped in final row custody validation; macOS stopped
in creation-history property definition resolution. Both passed the other 17
owned-graph-step cases. The checked-attempt reuse has not resolved the release
blocker; no tag or publication followed.

A subsequent two-read direct-path extraction trial also passed original CREATE:
whole apply 4,278.0 ms and finish 1,448.4 ms against the same committed-runtime
baseline above. That single observation does not establish a material gain;
the trial was discarded, with runtime and manifest restored exactly. Further
release attempts await a substantive change rather than another micro-optimization.

### Creation history uses the existing settlement metadata

Settlement now includes created objects' original live after-images in its
existing per-revision/type history metadata, including objects deleted by later
operations. Creation verification uses the existing metadata renderer; standalone
validation keeps its generic fallback. The private unpublished qualified helper
adds an optional argument; the published wrapper and 223-routine inventory remain
unchanged. Source pins are rebuilt independently at each finish/commit, while
authority, ownership, journal, identity and complete-effect checks remain live.

The original 1,024-CREATE diagnostic passes. Definition resolutions decrease
from 20,484 to 17,415 and generic history renders from 2,048 to 1,024. One local
apply observation was 4,084.4 ms versus the recent identical-runtime baseline
4,443.4 ms; finish was 1,337.1 ms versus 1,500.8 ms. This establishes reduced
repeated work, not isolated timing improvement or hosted release qualification.
The first installation attempt exposed a missing CASE-expression grouping; it
was corrected before the successful native run.
Twelve existing/basic PostgreSQL 18 cases pass in 57.912 seconds: original
capacity/commit/replay/readback, ordered batches, owned graphs, immutable capture,
published native68 upgrade routes and a same-group create/delete followed by
committed historical reconstruction. Astra Ultra cleared the plan and final
source; generator `--check` verifies owner assembly and all runtime hashes.

### Full functional release steps pass; original capacity remains open

[Run 38980177061](https://github.com/DocumentDrivenDX/truss/actions/runs/38980177061)
on main 8d4f341c passed packaging and every preceding installed functional,
query, catalog-evolution and predecessor-upgrade step on Linux and macOS. The
final unchanged capacity suite passed its two refusal/rollback cases but timed
out original 1,024-CREATE on both platforms. Linux stopped in final physical-row
attempt custody; macOS stopped in creation-transition validation's prepared
attempt check. Publication was skipped; no tag followed. This does not establish
hosted coverage of native export sources added later in 21346602. Their two
source cases are now selected by the existing installed owned-graph release step;
protection and populated-upgrade assertions remain in their existing selectors.

### Optional release-runner capacity diagnosis

The existing release workflow has a default-off `capacity_statistics` manual
input. It enables only PostgreSQL's built-in function counters on the capacity
fixture's consumer role; no production runtime instrumentation is added. The
original workloads, assertions, 10-second statements, 30-second operations and
publication dependencies remain unchanged. Run a diagnostic validation with
`gh workflow run release.yml --ref main -f capacity_statistics=true`.

Observations use the same consumer connection immediately after each apply
returns and before assertions or commit. They are cumulative within that
transaction, exclude later deferred COMMIT work, and omit unfinished calls.
A disposable PostgreSQL 18.6 cancellation/savepoint probe retained both completed
child calls while the cancelled outer call had zero completed calls. These are
partial cost observations, not complete cancellation timings. Unsafe connections
are reported unavailable without changing host containment. Always-uploaded,
platform-specific artifacts identify captured, unavailable and missing phases.

On local PostgreSQL 18.6/psycopg 3.3.6/Bun 1.4.2, all three original capacity cases
pass with collection enabled (30.417 seconds), producing five tracked phase
observations including the final-operation rollback. The original full
create/update/commit/replay/readback case also passes with collection disabled
(23.498 seconds). Static comparisons preserve all six original fixture methods
apart from capture calls and preserve the original workflow after removing its
optional diagnostics. Astra Ultra cleared the plan and source. Instrumented
runs provide functional evidence, not clean timing qualification. Remove this
temporary diagnostic plumbing after the release-runner bottleneck is resolved.

### Avoid deriving identical preflight key cells twice

[Diagnostic run 38990946071](https://github.com/DocumentDrivenDX/truss/actions/runs/38990946071)
on 4661b290 passed every installed functional, query, evolution and upgrade step
on Linux and macOS, including native export-source checks. Original capacity
still failed: Linux cancelled CREATE during final row settlement; macOS completed
CREATE and its following commit, then cancelled UPDATE during final settlement.
Both platforms passed the original overflow and late-fault rollback controls.
The partial counters show the immutable attempt guard is about one percent of
completed work; removing that guard is not justified.

Preflight now reuses its already-derived tuple when an existing before-image has
exactly equal key cells. Unequal cells retain the original derivation, including
canonical equivalence and invalid-value behavior. Live membership, namespace,
reservation, locking, mutation and final validation are unchanged. A broader
non-key-update shortcut was rejected because it could miss membership changes
after preflight.

Six original capacity and ordered-batch cases pass locally in 33.483 seconds.
The original capacity case plus real-key-change/dry-run/retry workflow pass in
28.163 seconds with optional collection enabled. UPDATE tuple-derivation calls
fall from 8,192 to 7,168 for the same 1,024-operation workload. This is reduced
repeated work, not an isolated timing improvement or a hosted release pass.
Astra Ultra cleared the bounded plan, source and exact-token precision behavior.
Owner SQL/hash and module-boundary checks pass. The hosted capacity blocker
remains open; neither deadlines nor workloads changed.

### Exercise the original public workload against release wheels

Release tags now select the existing `small` public workload on both Linux and
macOS, after original capacity passes. Manual validation selects it with
`gh workflow run release.yml --ref main -f public_workflows=true`.
The unchanged driver loads 1,000 nodes and 1,000 edges, performs 1,000 sampled
reads and 200 committed writes, and retains all original batch sizes/repetitions,
including five changed 1,000-object UPDATE groups with commit and readback.
Failure blocks the existing native job and publication. The 25-minute job budget,
10-second SQL and 30-second operation limits remain unchanged. Stress work waits
for original workflows to pass on both platforms.

The new `--installed-package` mode omits checkout library imports and refuses a
resolved checkout package. Reports hash the imported package's actual runtime
manifest and record its path/version separately from the harness commit.
Always-retained status/log/report artifacts distinguish skipped or missing runs.
Astra Ultra cleared the plan and source. Static AST comparison confirms every
existing workload function/class is unchanged; workflow comparison preserves all
prior steps and publication dependencies. A built current wheel passes import,
manifest and version checks, while checkout injection refuses before database
startup. Collection scripts handle both present and missing reports. Actual
hosted workload completion remains pending; these checks are not a workload pass.

### Original installed workload still blocks release

On local PostgreSQL 18.6 with the current wheel, the unchanged `small` workflow
created and committed 1,000 objects (5,579 ms apply), then refused the 1,000-edge
group with 57014 during final edge-transition validation at the original 10s SQL
limit. The report correctly records functional failure, not a partial pass.
A source/wheel inventory check found no wheel payloads absent from source.

A bounded instrumented repeat completed the edge apply in 9,597 ms and completed
three changed 1,000-object UPDATE groups with commit/readback; the fourth UPDATE
cancelled during final graph settlement. The full run failed in 112.640 seconds.
Its retained completed-call counters show 1,652 ms self time in 1,000 owned steps,
688 ms in row validation, 685 ms in object effects and 658 ms in 19,007 definition
resolutions. Cancelled calls and later COMMIT work may be absent. The temporary,
Astra-reviewed failure observer left the original workload/assertions/cleanup
unchanged and is not committed or installed. These are diagnostic observations,
not clean timing qualification. A proposed creation-identity lookup microchange
was discarded: it did not address the measured changed-UPDATE blocker. No stress
qualification or release tag follows these failures.

### Reuse each step's immutable before-map

`runtime_owned_step` now extracts `beforeEdges` and `beforeNodes` once into local
JSONB variables. The last slot can carry the full graph; repeated extraction
inside its existing loops copied the large map while selecting actual effects.
Filters, ordering, null/deleted semantics, effects, authority, progress and final
settlement remain unchanged. No helper, schema, cache protocol or public API was
added. An inverse substitution check reproduces the original function exactly.

The full original installed-wheel `small` workload passes locally in 126.123
seconds with counters off: 1,000 nodes, 1,000 edges, 1,000 sampled reads, 200
committed single writes and all five changed 1,000-object UPDATE groups with
commit and persisted readback. CREATE apply was 5,114 ms (7,607 ms including
commit); edge apply was 8,660 ms (13,714 ms including commit). Five UPDATE applies
were 7,610–8,238 ms, median 7,905 ms; all commits and readbacks succeeded. This
is one functional run under unchanged 10s SQL/30s operation limits, not an
isolated speedup or hosted qualification. The report correctly identifies a dirty
candidate checkout and the actual installed manifest. Wheel SHA-256:
`6d47537a9d192f57b04ca32bb6b990d5f2f2733d0758b9171b8a5904d525f614`.
All 509 packaged payloads match source. Original capacity/overflow/late-fault and
owned reparent/cascade/history/retry/query controls also pass: five cases in
34.116 seconds. Owner/hash, module-boundary and whitespace checks pass. Astra
Ultra cleared the plan, source and completed small-workload evidence.

The preceding [baseline run 38992684003](https://github.com/DocumentDrivenDX/truss/actions/runs/38992684003)
on 8cbe8fb3 passed all preceding installed functional steps on both platforms.
Linux passed original capacity but cancelled the 1,000-edge public group during
final validation; macOS cancelled the 1,024-UPDATE capacity group during final
validation and skipped the public workload. Publication was skipped. The new
map-reuse increment still requires both hosted original workloads before stress
qualification or tagging.

### Selected stress comparisons after both original workloads

The release workflow's manual `stress_case` choice defaults to `none`. Selecting
one case forces the full original `small` workload in both native platform legs;
the stress job needs both legs to succeed before it can start. Tags or absent
inputs do not select stress. The stress job uses the same built wheel and exact
checksum-verified compiler/PG18 installation, separately on Linux and macOS.

The declared comparison tranche is `nominal`, `type-heavy`, `wide`, `complex`,
`node-heavy`, `dense-edges`, `index-heavy` and `skewed`. All existing cases retain
their exact sizes. The new `node-heavy` point has 20,000 nodes and 40,000 edges,
with nominal's 10 types, 12 mixed fields, two indexed properties per type and
uniform distribution; it changes node count at fixed average degree. The
extended `large` point remains 1,000,000 nodes/2,000,000 edges and is not silently
substituted by this new point. The 1,000-type extended case is also unchanged.

All selected stress comparisons load with the existing driver's batch size 100;
wide 128-field objects can exceed the ordinary input-byte limit in a 1,000-create
group. This explicit load profile does not reduce original capacity acceptance:
the original 1,024-operation/full-small gates still run, and the stress driver's
five repetitions at each supported update size through 1,024 remain unchanged.
Its 10,000-operation point stays explicitly unsupported. Each run retains the
exact case, installed asset identity, actual object/edge counts, physical indexes
and maintained business-key inventory. SQL 10s/operation 30s limits are unchanged.
A 180-minute stress-job ceiling is not a completion promise; timeout or a missing
report is incomplete evidence. Report/log/status artifacts are retained when
collection can run, with platform/case-specific names.

Example after original qualification:
`gh workflow run release.yml --ref main -f stress_case=nominal`.
Only one selected case is dispatched per run. Workflow/schema/static controls
are not a stress pass; none is claimed before actual execution.

### Assemble the ownership projection once

The [map-reuse run 38993545762](https://github.com/DocumentDrivenDX/truss/actions/runs/38993545762)
on b9f6eaf2 passed the preceding installed functional checks on both platforms,
but both original 1,024-CREATE groups reached the unchanged SQL deadline. Linux
cancelled in final row custody validation; macOS cancelled in the final forest
projection. The overflow and final-operation rollback controls passed. The full
public workload and publication were skipped; this is not hosted qualification.

A disposable input-storage experiment was rejected. Both original capacity
workflows completed locally, but uncompressed EXTERNAL storage increased CREATE
apply from 5,419 to 6,852 ms and added about 623 KB of table storage. Logical
input lengths and stored/retrieved hashes matched across the two modes. This
single instrumented comparison does not establish an isolated speedup; no
production storage or authority change was retained.

The forest projection now retains its existing edge validation and per-node
cycle/root walk, then groups incoming edges once and assembles the complete
ordered result with one aggregate. This removes growing JSONB concatenation
and a full incoming-edge scan for each node. Parallel incoming edges retain
numeric ID order, and rootless nodes retain null parent/root values. The final
byte bound, authority checks, public interfaces and deadlines are unchanged.
Deep-chain traversal is unchanged. No new helper, table or cache was added.

Against baseline 2299de37, a disposable PostgreSQL 18.6 comparison returned exact
old/new JSONB values or identical SQLSTATE/message for 12 empty, rootless, chain,
branching, parallel-edge and refusal cases, including 1,024-node rootless/star
inputs. Client-call observations were 72.354/9.904 ms for the rootless case and
169.546/4.985 ms for the star, before/after; they include result decoding and are
component observations, not end-to-end qualification. Original capacity, overflow,
late-fault rollback and owned reparent/cascade/history/query workflows, plus one
basic projection regression case, pass: six cases in 41.278 seconds. PostgreSQL
cleanup completed. The wheel's 509 payload files match source; SHA-256:
`65acd50e215c1fbfaa4c5e2507aeffc326407e4c6cdc693cdfb4c162d3dc58e4`.

The candidate's full original installed-wheel `small` workload still **fails**:
1,000 CREATEs committed, then the 1,000-edge apply cancelled with `57014` during
final validation. Reads and changed updates were not reached; cleanup completed.
The [original report](results/forest-output-small-20261016.json) and
[run log](results/forest-output-small-20261016.log) retain this failed attempt.
No end-to-end improvement, non-regression or release qualification is established.
Astra Ultra cleared the component plan/source, differential evidence and bounded
increment with this failure explicitly recorded. Both hosted original workloads
remain prerequisites for stress and tagging; no unchanged hosted rerun follows.

### Reuse immutable operation arrays and count simulated edges once

Group admission, owned preparation/capture and finish now extract the unchanged
operations array once per invocation. Previously their loops repeatedly copied
the complete array while resolving each operation or checking its length. Inverse
substitution reproduced all four original bodies before the following count
change; guards, helper calls, validation order and null/non-array behavior remain
unchanged.

After the existing final forest/root checks, owned preparation now counts the
immutable simulated live edges once by relationship and endpoint. The existing
node/relation traversal still checks outgoing before incoming multiplicity with
the same rules and `P1005` refusals. Parallel edges each contribute one count;
missing entries mean zero. Keys retain the original text type IDs and references.
This removes a full edge scan for every node/relation without caching current
authority or adding a table, helper, protocol or deadline exception.

Astra Ultra cleared both plans and the combined source. Original capacity,
overflow/final-fault rollback, owned subtree/history/query, batch and parallel-edge
workflows pass: ten tests in 68.452 seconds. The composed Subject-cut regression
also passes in 7.945 seconds with fixture cleanup. The exact installed wheel has
509 source-matching payloads and SHA-256
`367e1034e2f02a8cf95d459fd25573b13fa2d4db848d426e2372d199ad18d1e8`.
These basic controls do not establish full workload or hosted qualification.

The full original installed-wheel `small` workload now passes locally in 124.576
seconds with counters off and unchanged 10s SQL/30s operation limits: 1,000 nodes,
1,000 edges, 1,000 sampled reads, 200 committed single writes and all five changed
1,000-object UPDATE groups with commit and persisted readback. CREATE apply was
5,090 ms (7,411 ms including commit); edge apply was 8,690 ms (13,264 ms including
commit). Five UPDATE applies were 6,975–8,577 ms, median 7,028 ms; all five commits
and readbacks passed. The database maintained all 1,000 declared business-key
rows and retained the actual physical index inventory. Cleanup completed.

The [original report](results/operation-counts-small-20261016.json) records the
actual installed package, manifest and dirty candidate on source parent d2f88c38.
This is one functional run, not an isolated speedup, broader scale result or
hosted qualification. Both hosted original workloads must still pass before
stress or tagging.
Astra Ultra cleared the completed iteration, retained result and source-matching
wheel for commit and the subsequent hosted original-workload run.


### Reuse immutable graph maps during final validation

Hosted gate [38996959566](https://github.com/DocumentDrivenDX/truss/actions/runs/38996959566)
on dc948aeb failed the unchanged deadlines: Linux passed the original three
capacity tests, then cancelled the 1,000-edge apply; macOS cancelled the
1,024-CREATE final validation, so its small workload was not reached. Stress
and publishing remained skipped. These failures are not superseded by local
passes.

Final validation now extracts each operation's immutable before/after node and
edge maps once, and extracts the original input operations array once. The full
plans, extraction semantics, validation predicates/order, result-slot census,
history and fresh authority checks are unchanged. Exact inverse substitution
reproduces the original owner source. Astra Ultra cleared the plan and source;
the generated SQL and manifest agree.

The installed candidate wheel has 509 source-matching payloads, SHA-256
`750628e463afc5c7568fa75a8e6218fa23d7d12ace894e31d937ba8666876a3d`.
Seven original capacity/overflow/late-fault, owned and parallel-edge tests pass
in 59.199 seconds. The [full original small report](results/finalize-map-hoist-small-20261016.json)
passes in 161.558 seconds, counters off, with the unchanged 10s SQL/30s operation
limits: 1,000 nodes, 1,000 edges, 1,000 sampled reads, 200 committed writes and all
five changed 1,000-object UPDATE groups, commits and persisted readbacks. CREATE
apply was 5,969 ms; edge apply 8,609 ms; five UPDATE applies had median 7,106 ms
and maximum 8,054 ms. All 1,000 business-key rows were maintained; cleanup
completed. This is a bounded correctness increment, not an isolated speedup
or hosted qualification. Both hosted original workloads remain release gates.


### Reuse the primary reference and exact edge member

Gate [38998774190](https://github.com/DocumentDrivenDX/truss/actions/runs/38998774190)
on b76a983c passed the complete Linux native gate, including original capacity
and full small workload. macOS passed capacity (three tests, 41.110s) but its
1,000-edge apply cancelled with `57014` inside `runtime_owned_step`; later small
reads/updates were not reached. Stress and publishing stayed skipped.

The next bounded change extracts the immutable primary reference once per owned
step. Edge identity discovery passes the exact selected member in a narrow plan,
following existing final validation, while retaining the full plan for subsequent
image/context checks. Every candidate is still resolved and counted; original
creation-result proofs, current authority, history and result-slot census remain
unchanged. No helper, signature, table or deadline changed. Astra Ultra cleared
the plan and source; primary-reference inverse substitution is exact.

Seven capacity/overflow/late-fault, owned and parallel-edge controls pass in
109.971s. The [compressed original small report](results/edge-member-projection-small-20261017.json.gz)
passes in 165.132s with counters off, unchanged 10s SQL/30s operation limits,
1,000 nodes/edges/reads, 200 committed writes and all five changed 1,000-object
UPDATE groups with commits and persisted readbacks. CREATE apply was 6,819ms,
edge apply 8,247ms; five UPDATE applies had median 6,662ms and maximum 6,821ms.
All 1,000 business-key rows were maintained; cleanup completed. These observations
do not establish an isolated speedup or hosted qualification.

The installed wheel has 509 source-matching payloads and SHA256
`36d61bb9362d1cb22f462eb31bab812d351c6f7374c5b3351d0f70e8d144fb3a`.
The report records dirty candidate source parent 4202cbed; its raw SHA256 is
`916c6772651f4f887b46403b566afd12046f62ef4ccceb9535e6c9e76a2fdd3f`.
Both hosted original workloads remain release prerequisites.


### Hosted capacity failure and preserved atomic call boundary

Run [39000427135](https://github.com/DocumentDrivenDX/truss/actions/runs/39000427135)
on fa28145c failed the unchanged capacity gate on both hosts. macOS cancelled
changed UPDATE at object transition validation; Linux cancelled CREATE at the
module-writer check in finalization. Both returned `57014`. The full small
workload, stress and publishing were skipped. Cancellation locations do not
isolate a regression or justify removing authority checks.

A two-call execution/finalization split was considered and is not adopted.
Astra Ultra identified that CONTRACT-009 requires one protected ordinary group
call with private continuation helpers. Incomplete-attempt commit rejection alone
would not preserve that boundary; two separate SQL calls would also introduce two
10s statement budgets instead of the current group-spanning one. Keep the current
single-call contract, 10s SQL/30s operation limits and original workloads. The next
performance change must preserve that boundary and be supported by measurement;
no authorization check is removed on the basis of a cancellation stack alone.


### Project only the creation attempt fields used by the leaf

An unchanged original capacity diagnostic on the prior wheel passed in 43.414s
with stock PostgreSQL function counters. CREATE showed 2,060ms self time in
1,024 `apply_create_group_qualified` calls; module-writer checks accounted for
149ms across 6,144 calls (177ms across 7,170 UPDATE calls). These instrumented
observations do not qualify clean timing or justify removing authority checks.

The creation leaf now selects the six attempt fields it actually uses: ID,
next index, actor, writer transaction, results and aliases. It no longer copies
unused input, document and context fields into its local record. Every query
predicate, `INTO STRICT`, row lock and downstream check remains unchanged.
Astra Ultra cleared the corrected six-field plan and source; the complete
function field inventory matches that projection. No call boundary, helper,
signature, grant or deadline changed.

Five original capacity/overflow/late-fault and basic create/replay/caller-work
controls pass in 96.801s. The [full original small report](results/attempt-projection-small-20261017.json.gz)
passes in 169.770s with counters off, unchanged 10s SQL/30s operation limits,
1,000 nodes/edges/reads, 200 committed writes and all five changed 1,000-object
UPDATE groups, commits and persisted readbacks. CREATE apply was 6,116ms and edge
apply 7,856ms; the five UPDATE applies ranged from 6,444ms to 7,378ms. All 1,000
business-key rows were maintained and cleanup completed. This establishes local
functionality, not an isolated speedup or hosted release qualification.

The wheel has 509 source-matching payloads and SHA256
`0817060ef088ce22024f5e0580a9fa39a2fd0bde568ff6d4316206e8ae72feea`;
manifest SHA256 is `7c74f01d54684f76dd68b5da537f2a2dc71a08812db00ae05b859aaaf4e8084a`.
The report records dirty candidate source parent 7e941507; raw report SHA256 is
`85072405d3d7be798c66686f045071b656f73b990d00daf3952a2bab5db58749`.
Both hosted original workloads remain release prerequisites.

### Reuse closed edge settlement context within the current attempt

[Hosted run 39002622579](https://github.com/DocumentDrivenDX/truss/actions/runs/39002622579)
failed both original-workload jobs. Linux timed out during CREATE 1,024 at the
final operation-owner/type-reader check; full small was not reached. macOS
passed original capacity, then timed out during 1,000-edge finalization. These
are separate blockers; the edge change below does not qualify Linux CREATE.

Edge finalization now passes the already checked current-attempt input and
closed result-slot context to the existing qualified transition validator.
This avoids repeated attempt loads and full result-slot counts for each edge.
A fresh progress and completed-slot count follows trigger-capable marker writes.
Each edge retains its fresh actor and module-writer check, physical edge and
journal correspondence checks. Earlier attempts in the same transaction use
the existing standalone validation path. The old private entry point and its
attributes remain; the new helper is owner-only. Routine inventories are 227.
The single protected call and 10s SQL/30s operation limits remain unchanged.

Four focused final-wheel controls pass in 69.638s: same-transaction edge groups
with commit/readback, future-slot and unplanned-edge refusals, and populated
upgrade from the checksum-verified published v0.0.37 wheel. The final wheel has
509 source-matching payloads, SHA256
`99f169aea5347676fdbb55994c4a282970f12ae5f9b232a3e9ed69a41142a8ce`;
manifest SHA256 is `cdf56b3682c32c270253adc3ace51d3ef851d6d1847dfc6dc7b2d1193aa703df`.

The [final full original small report](results/edge-context-small-20261017.json.gz)
passes in 177.460s with counters off: 1,000 nodes, 1,000 edges, 1,000 reads,
200 committed writes and all five changed 1,000-object UPDATE groups with
commits and persisted readbacks. CREATE apply was 5,872ms, edge apply 7,375ms,
and the five UPDATE applies ranged from 6,347ms to 6,822ms. Cleanup completed.
Raw report SHA256 is
`bca3ba1a333b66a01d7255ae34b34ecb329b2d8449947766e299d4cca2d32037`;
it records dirty candidate source parent 2675a77a. Astra Ultra cleared the source
and its freshness guard. This is local functionality evidence, not an isolated
speedup or hosted qualification; both hosted original workloads remain required.

### Project only archived definition fields used by pin resolution

The retained Linux capacity observation recorded 11,268 completed
`runtime_definition_in_basis` calls and 1,257ms self time. It does not record
archived-column sizes or establish the cost of unused fields. The resolver now
selects only its four used archive fields: original document text, revision,
ordinal and content digest. The exact `INTO STRICT` predicates, original source
parsing, fragment bytes and pin recipe remain unchanged; no helper, signature,
authority check or deadline changed. Astra Ultra cleared the plan and source.

The candidate wheel has 509 source-matching payloads and SHA256
`437d43d74f030594046864073807b1a0de456ea691d5180dad2279397b3e6557`;
manifest SHA256 is `eb60e3d38a799a9fe60191f108ac22ff2929bca66dd7073363dd9b8d40a37533`.

The [three original capacity controls](results/definition-projection-capacity-20261017.log.gz)
pass in 76.983s with counters off: 1,024 real creates, changed updates, commits,
replay and ordered reads; 1,025 refusal; and operation-1,024 late-fault rollback.
SQL and operation limits remain 10s and 30s. Cleanup completed. This records
local correctness, not an isolated speedup or a resolved Linux timeout. Both
hosted original-workload gates still need to pass before a release tag.

### Current hosted CREATE blocker and bounded diagnostic

[Run 39005153026](https://github.com/DocumentDrivenDX/truss/actions/runs/39005153026)
tested exact main `a5f41d79264ab8d75d01fff2eca37f614d979b5b`. Both platforms
passed the preceding functional checks but failed CREATE 1,024 with `57014`
at the unchanged 10s SQL deadline. Linux cancelled in final owner/type source
resolution; macOS cancelled later in owned-group transition validation. Both
full-small workloads, stress and publishing were skipped. No tag was created.
The local projection result did not establish a hosted performance fix.

One unchanged original capacity diagnostic passes locally in 41.883s with the
existing stock PostgreSQL counters enabled. Its [CREATE observation](results/create-capacity-functions-20261017.json.gz)
records 5,444ms in `apply_group`: the creation leaf totals 2,571ms across 1,024
calls, with 1,350ms self time; source-definition resolution totals 709ms across
17,415 calls. The cancellation-site identity helper totals only 155ms across
8,191 calls. The entire creation metadata helper totals 255ms, so bypassing its
fresh authority/source checks is not justified by these measurements. Captured
owned values are already reused. The next diagnostic must locate the leaf's
own SQL/CPU cost before another admission-path change. These observations cover
completed calls through apply return, exclude later commit work, and do not
qualify clean timing or isolate the benefit of either preceding projection.


A final disposable stock `pg_stat_statements` diagnostic enabled nested tracking
only for the post-registration consumer connection. The unchanged CREATE test
failed with `57014` at its original 10s deadline after 756 completed steps;
182 [normalized statement aggregates](results/create-capacity-statements-20261017.json.gz)
were captured before the original assertion. No later update, commit, replay or
readback ran. The test finished in 17.070s and cluster cleanup completed.

This is diagnostic evidence, not a workload pass or clean performance result.
Tracking materially changed costs: capture/preflight recorded 3,584/1,668ms,
versus 754/249ms in the preceding function-counter observation. Nested totals
overlap, failed statements are omitted, and normalized entries can combine
calls from different functions. The completed leaf attempt selection recorded
131ms across 757 calls; journal insertion recorded 273ms across 756 calls.
These observations do not establish a dominant scan or justify weakening the
completed-slot census, exact source checks or authority checks. No further
profiler revisions are planned; the next runtime candidate needs a concrete
source equivalence and clean measurement. No production instrumentation was
added. Raw observation SHA256 is `a48c84a1077274cfa83824bb00c09a9279552c3c7d855dfcd0a05363e8b17cae`.


### Resolve repeated CREATE pins once when collecting affected types

Owned capture constructs an affected-type set before graph exclusion. It now
selects the first complete original CREATE operation and ordinal for each exact
definition pin, under `COLLATE "C"`, before calling the unchanged type resolver.
A 1,024-operation batch using one CREATE pin therefore performs one resolution
in this scope query instead of 1,024. Update/delete resolution, outer type order,
property/relationship/endpoint reader checks, and per-operation admission,
execution and settlement remain on their original paths. No helper, table,
public signature, write order or deadline changed. Routine inventory remains 227.
Astra Ultra cleared the plan and source; owner and generated SQL match.

The [five installed-wheel controls](results/create-scope-dedup-controls-20261017.log.gz)
pass in 37.623s with counters off and unchanged 10s SQL/30s operation limits:
original 1,024 creates/changed updates/commits/replay/ordered reads, 1,025 refusal,
operation-1,024 fault rollback, mixed A/B/A create order/pins/committed values,
and same-group create/delete retained history. Fixture cleanup completed.
This is correctness evidence, not an isolated speedup: the full original small
workload subsequently passed locally, as recorded below; both hosted original-workload gates remain release blockers.
The earlier diagnostic's 104.54ms affected-type aggregate was perturbed and does
not establish the clean saving.

The candidate wheel has 509 source-matching payloads and SHA256
`7fdee3ba01c1547fcb0f0157302c88c50b14b61741f5da9859680fc251ff392e`;
manifest SHA256 is `f0fe32fac6389964c83fba0fbd7d4ea8170bd67437a166f8d77ce88c33a4fe7f`.
The tested candidate was the working tree over main `2c546981`. Raw control-log
SHA256 is `a0146e1aeb683b01cdaa9830f4f0f37f7ac0b0e8a0d6d778d0bf6130e007df55`.


### Hosted 4070181b workload result

[Run 39011067743](https://github.com/DocumentDrivenDX/truss/actions/runs/39011067743) tested exact main `4070181bb20769af37ddc4b29c87d2c462826723`, once, with capacity statistics off and the original workloads and 10s SQL/30s operation limits. Packaging and preceding functional workflows passed. Linux failed the original positive 1,024-CREATE capacity case with `57014` during final readable-value validation; overflow and final-operation rollback controls passed. Linux did not reach full-small. macOS passed the original capacity tests, then failed full-small while applying 1,000 edges with `57014` during final graph validation. Its 1,000-object create and commit completed; later reads, 200 writes and five changed 1,000-object update groups did not run. macOS workload server cleanup completed. Cancellation locations alone do not establish dominant costs.

The campaign failed overall. Stress and publishing were skipped. Neither platform is qualified for release by this run, and no unchanged rerun is scheduled.

The [terminal hosted failure log](results/hosted-39011067743-failed.log.gz) and [macOS full-small report](results/hosted-39011067743-macos-small.json.gz) retain these failures.

The subsequent [unchanged local full-small run](results/create-scope-dedup-small-20261017.json.gz) passed in 97.337s on PostgreSQL 18.6 with the exact installed wheel above and counters off. It completed 1,000 nodes, 1,000 edges, 1,000 reads, 200 committed writes, and all five changed 1,000-object UPDATE groups with commits and readbacks. CREATE applied in 4,125ms; edges in 5,982ms; median 1,000-object UPDATE applied in 5,484ms and committed in 3,052ms. Server cleanup completed in 369ms. The report's dirty flag reflects only preexisting untracked build/cache/egg-info directories; tracked source was clean at 4070181b. This local pass does not supersede either hosted failure or establish an isolated speedup.


### Resolve current-revision relationship pins without catalog replay

Explicit relationship pin requests now select the native relationship row only when the requested revision equals schema_head and no newer schema_rev exists, with both predicates and row selection in one SQL snapshot. Older or in-flight revision requests retain the original strict historical reconstruction. The NULL-revision path still excludes retired definitions; explicit historical resolution retains retired rows. Archive selection, original source fragment bytes and exact pin construction are unchanged. No helper, cache, public signature, authority check or deadline changed.

Astra Ultra cleared the plan, source and four assertions exercised across both existing UMF 0.7/0.8 relationship evolution workflows. The assertions compare current public pins and retained older pins after compatible acceptance. The retired-row branch is source-reviewed; no public retirement fixture was added and no administrative guard was bypassed. The [two installed-wheel public evolution controls](results/relationship-pin-controls-20261017.log.gz) passed in 11.823s with fixture cleanup and unchanged 10s SQL/30s operation limits. This establishes these basic correctness cases; the [unchanged three original capacity controls](results/relationship-pin-capacity-20261017.log.gz) also passed in 23.713s with fixture cleanup. The [unchanged local full-small workload](results/relationship-pin-small-20261017.json.gz) then passed in 96.017s: 1,000 nodes, 1,000 edges, 1,000 reads, 200 committed writes and all five changed 1,000-object UPDATE groups with commits and readbacks. Cleanup completed in 592ms. Counters were off and the 10s SQL/30s operation limits were unchanged. Both hosted original workloads remain release blockers; this sequential local result establishes no isolated speedup. No speedup or release qualification is claimed.

The wheel has 509 source-matching payloads and SHA256 `e4235fd521e6be318b8decbfd3f69e712f879515e236a645b494f745aae95d97`; manifest SHA256 is `7cd731fb936ac0b10ab7c27719f26d33b9f2df512a73d431f2be1e1ed25d9d25`. Raw native control-log SHA256 is `5264dba30eb397352d9aebbf2026dcc2f971179fcb4d2c01b8e4b81affc3f0a7`. Routine inventory remains 227. The tested candidate was the working tree over main `acc5e19f`, with the SQL and manifest changes in this increment.


### Hosted a8d21ebb original capacity gates

[Run 39013147807](https://github.com/DocumentDrivenDX/truss/actions/runs/39013147807) tested exact main `a8d21ebb6572fcc4d01ec38151866209218867aa` once, with counters off, original workloads and unchanged 10s SQL/30s operation limits. Packaging and preceding functional/upgrade workflows passed on Linux and macOS. The [terminal capacity failure traces](results/hosted-39013147807-failed.log.gz) retain both failures. Linux timed out with `57014` during CREATE final settlement, in `runtime_owned_identity` called by `runtime_owned_group_validate`; its three controls finished in 24.530s. macOS completed CREATE but timed out during changed UPDATE final settlement, in `runtime_exact_wrapper` called by the object-transition validator; its controls finished in 37.290s. Both platforms passed the overflow and final-operation rollback controls. Cancellation sites alone do not identify dominant costs.

Both original full-small workloads were skipped because capacity failed. Stress and publishing were skipped. No hosted release qualification or performance fix is established, and no unchanged rerun follows. The earlier complete local passes remain scoped local evidence. Main runtime remains unchanged while the next specific repeated-work candidate is investigated.


### Current-main stock function counters

One unchanged positive 1,024-operation capacity test on tracked-clean main `b78427ac` passed in 21.243s, including both commits, durable replay, ordered readback and fixture cleanup. All 509 source payloads matched the installed `e4235fd521e6be318b8decbfd3f69e712f879515e236a645b494f745aae95d97` wheel. This used only the existing opt-in `TRUSS_CAPACITY_FUNCTION_STATS` hook and stock PostgreSQL 18.6 transaction function counters; no new instrumentation code or native extension was added. The [test log](results/main-b784-capacity-counters-20261017.log.gz) and [CREATE](results/main-b784-capacity-create-20261017.json.gz), [following group](results/main-b784-capacity-following-20261017.json.gz), [UPDATE](results/main-b784-capacity-update-20261017.json.gz) and [replay](results/main-b784-capacity-replay-20261017.json.gz) observations are retained.

These are completed calls through each capture in its current transaction, not clean timing or COMMIT measurements. The following-group capture includes CREATE; nested totals overlap and incomplete calls are excluded. Original 10s SQL/30s operation limits remained unchanged. CREATE recorded `runtime_definition_in_basis` at 15,369 calls/593ms self time, and UPDATE at 16,390/643ms. Write-side `runtime_object_history` recorded 1,024/208ms total for CREATE and 2,048/410ms for UPDATE. The scalar validator recorded about 49ms in each phase, supporting cancellation of the uncommitted scalar exception-boundary experiment without another native campaign. The temporary candidate remains outside main. Pin/history reconstruction is the next source-analysis target; these observations establish no isolated speedup or hosted release qualification.

### Exact settlement property-pin reuse — 2026-10-17

The clean [hosted run 39018524151](https://github.com/DocumentDrivenDX/truss/actions/runs/39018524151) tested runtime `8ab6d504` with counters off and original limits. Linux CREATE and macOS changed UPDATE timed out (`57014`) during final settlement; overflow and final-operation rollback controls passed. Both full-small workloads, stress and publishing were skipped. The [failure traces](results/hosted-39018524151-failed.log.gz) do not establish a dominant cost.

The next increment reuses an already resolved property pin only when the current settlement invocation's metadata matches the exact type, catalog revision and string-valued property pin. Otherwise it retains the original STRICT lookup. No helper signature, cache, authority check, event validation or deadline changed; finish and commit independently rebuild their metadata.

The exact installed wheel (`b42f8ceabc46a4dcf0bb4ff0d36ada7bfa8657f9afa7a08e62bf9b9d85e24faa`, all 509 payloads source-matching) passed [two existing history/evolution controls](results/property-pin-reuse-controls-20261017.log.gz), the [UMF 0.8 cross-revision removal fallback](results/property-pin-reuse-removal-20261017.log.gz), and the [three original capacity controls](results/property-pin-reuse-capacity-20261017.log.gz) in 24.631s. The removal case commits, reconstructs both versions and compares the event pin to independent historical resolution. The [original full-small workload](results/property-pin-reuse-small-20261017.json.gz) passed in 105.807s (report elapsed), including 1,000 objects/edges/reads, 200 committed writes and all five changed 1,000-object UPDATE groups with commits/readbacks. Owned server cleanup completed in 382ms. Counters were off; SQL 10s/operation 30s limits were unchanged. These local results establish no isolated speedup, Linux CREATE fix or hosted release qualification.
