# Reference type-page cost experiment — candidate 0.1

This execution procedure serves US-021-AC4 under TP-001 and STP-021. It is
an authored benchmark candidate, not a performance receipt or released profile.
The runner and exact environment/fixture registration remain unfinished.

Measure public `list_objects` elapsed time from entry into an already-created,
qualified read capability until its complete result is admitted for return.
Include native observation, lookahead, current-authority participation, complete
record decoding and result admission. Exclude installation, capability
construction, pool checkout and transaction creation; report those exclusions.
Use the same selected held-snapshot read mode, driver/transport and resource
profile in both arms. This measures page cost, not network service latency.

Prepare independently equivalent 10-type and 1,000-type installations. The
selected small type contains exactly three identical complete objects; limit
is 50 and continuation is absent. Freeze original source/value bytes and
independently expected complete results before execution. Other types have
zero objects. Catalog metadata count is the sole intended difference; record
complete table/index/statistics inventories and any unavoidable metadata-size
changes. A different query, cache policy, optional index or payload creates a
new experiment registration. No reduced decoding or authority bypass.

Run three registered blocks with 30 unmeasured paired warm-up calls and 1,000
measured pairs per block. Alternate arm order deterministically: 10 then
1,000 on odd pairs, reverse on even pairs. Use one caller at a time and
separately admitted original resources for each arm; refresh held snapshots
only between blocks under the same procedure. Retain all warm-up and measured
outcomes. Cancellation, refusal, missing sample or changed expected result
invalidates the block; do not delete that sample or replace the block to pass.

Capture monotonic elapsed durations as exact integer nanoseconds. For each
arm/block, sort all 1,000 durations and take the 950th as nearest-rank p95.
The denominator must be positive and independently above the qualified timer
resolution. The block passes only if candidate p95 <= 2 * baseline p95 using
exact integer comparison. Report each block separately; all three must pass
for this registered candidate. Report median, maximum, paired raw order and
native plans as supporting evidence, without substituting a favorable statistic.

Before running, seal server/build, hardware/runtime, transport, installation,
model/codec/security/resource/source pins, session settings, query/parameter
bytes, fixture expectations, timer producer/resolution and cache/statistics
policy. Record actual evidence and differences; missing pins leave registration
unavailable. Exercise deliberately failing ratio and missing/zero/incomparable
sample controls before trusting the runner. This result cannot qualify other
payload sizes, concurrent load, cold startup or different managed services.
