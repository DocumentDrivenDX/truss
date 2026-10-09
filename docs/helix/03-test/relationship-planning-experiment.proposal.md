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
