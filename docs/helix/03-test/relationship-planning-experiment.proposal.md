# Reference relationship-planning experiment — candidate 0.1

This procedure serves US-011-AC3 under TP-001/STP-011. It is an authored
candidate, not executed evidence or released support. Installation, actual
one-hop query/profile selection and runner qualification remain prerequisites.

Use independently equivalent 10-relationship and 1,000-relationship catalogs
on the same qualified server/build/settings. Keep canonical object/edge rows,
selected one-hop relationship, endpoint, result cardinality, payloads, query
shape, complete parameter types/values, role policy and native index inventory
constant. Additional relationship definitions have no edges. Preserve all
fixed native guard/helper obligations; do not substitute a query that bypasses
the selected production read path or install per-relationship indexes only in
one arm. Record inevitable catalog/statistics size differences explicitly.

## Reference workload packet

The candidate fixture has two required-string-field object types, `Source` and
`Target`, each containing 100 objects with independently expected ordinal labels
`source-000` through `source-099` and `target-000` through `target-099`. Create the
selected independent directed relationship first. Add one edge per Source to
the Target with the same ordinal, giving exactly 100 edges with no parallel
edges, duplicates or cycles. The measured request follows that relationship
outward once from `source-050`; the complete expected result is `target-050`
with its authored string value. This fixture has the same result under the
pending unique-terminal versus path-valued traversal choice, so it does not
select that product behavior implicitly.

The 10-definition arm has the selected relationship plus nine unused
relationships between the same types. The 1,000-definition arm preserves those
ten and adds 990 unused relationships with the same independent lifecycle and
multiplicity declaration. All additional relationships have zero edges. Preserve
100 Source objects, 100 Target objects and the same complete 100-edge logical
inventory in both arms. No optional/numeric/retained values, cascades or changed
policy workload may differ between arms.

Use original accepted identities bound to fixture aliases, not invented numeric
IDs. The registered fixture producer must specify how two isolated catalog arms
share the qualified server while retaining equivalent object/edge/index/native
statistics state. Different physical namespaces and original accepted revisions
are explicit packet differences; any identifier/parameter changes they require
are retained in each original statement packet rather than hidden by rewriting
observed SQL. Do not alternate a single growing catalog and call retirement an
independent 10-definition arm: retained definitions still affect its inventory.

This fixes logical workload and expected membership. Exact installation, fixture
producer, original public method/compiled mapping and all native statement bytes
remain registration outputs before execution. Capture and review them once for
each arm; a refusal does not authorize an easier handwritten query. The fixture
is not an independently installed/native-qualified benchmark packet yet.

## Measurement and registration

Freeze the actual selected one-hop statement and all required native query
prerequisites from the admitted direct-read or Weft-produced execution packet.
No alternate handwritten SQL can replace an unsupported owner query. Verify
independent expected complete results through the ordinary public execution
route before benchmarking and after each block. Pin query/parameter/original
binding bytes and complete native dependency/authority/resource correspondence.
Compilation is separately owned by Weft and excluded from native planning time.

Measure server-reported Planning Time using the same qualified
EXPLAIN (ANALYZE, FORMAT JSON, TIMING OFF) instrumentation for both arms.
It executes the query: admit every required operation and resource under the
original qualified context. Freeze the uncached/custom-plan instrumentation
route before execution; reused prepared/generic plans are a separate experiment,
not zero planning cost. Missing instrumentation of required nested planning
makes that scope unavailable; an outer wrapper plan cannot stand in for it.
Retain complete raw EXPLAIN bytes and native plan tree for every statement.

PostgreSQL's [EXPLAIN documentation](https://www.postgresql.org/docs/17/using-explain.html)
defines planning time separately from parsing, rewriting and execution, and
explains that EXPLAIN ANALYZE executes the query. This metric proves neither
public-call latency nor native enforcement. Estimated plan cost is not elapsed
planning time. Parse reported numeric tokens losslessly as exact milliseconds;
retain their original spelling and timing resolution without JS number rounding.

Run three blocks, each with 30 unmeasured warm-up pairs followed by 1,000
measured pairs. Alternate 10/1,000 and 1,000/10 arm order. Sum all required
statement planning durations for one complete admitted one-hop request, then
use the 950th sorted duration as nearest-rank p95 per arm/block. Each positive
baseline must be above the qualified reporting resolution. Require candidate
p95 <= 2 * baseline p95 in every block using exact arithmetic; preserve median,
maximum and complete paired raw order as supporting evidence. Missing samples,
errors, incorrect results or changed configuration invalidate the block rather
than being discarded. No replacement block, best-run selection or retry-to-green.

Seal original fixture expectations, target/adapter/driver/transport, installation,
layout/codec/security/resource, query source, planner/cache/statistics, hardware,
clock/reporting-resolution and session profile pins before running. Independently
exercise failing-ratio and missing/zero/incomparable-sample controls. Report each
block and every limitation; the runner is not yet implemented and no performance
claim follows from this procedure or from bounded index count alone.
