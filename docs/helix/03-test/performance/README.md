---
ddx:
  id: truss-practical-performance-matrix
  type: test-plan
  activity: test
  status: draft
  owner: Erik LaBianca
  updated: 2026-10-17
  links:
    - id: truss.prd
      kind: informed_by
    - id: TP-001
      kind: informed_by
---

# Practical functionality and performance

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
