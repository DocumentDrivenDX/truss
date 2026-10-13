# Scalar requiredness evolution tranche — 2026-10-13

Native0.48/layout0.16, SDK0.0.11, Weft0.4.13/backend0.4.18. Planner admits only
existing non-key singular supported scalars absent-allowed→required, checking
both old/new known facet maps even when unchanged. Existing compatibility
counts remain in locked acceptance before planning/allocation. Historical plan
replay does not scan current data. Key/container/new required field guards and
legacy widening stay unchanged. No custom tracing/accounting added.

Astra Ultra approved plan/source conditional on these basic checks. Both UMF
public workflows pass2 tests31.838s, covering missing-value refusal/count,
public repair, acceptance, exact unchanged object rows, read/query and retries.
Immediate .47→.48 upgrade passes1 test19.631s including rollback/commit, original
facts, receipt/feed and continued mutation. Prior .47 archive is byte-exact.
Python933-import and ordinary Cargo boundaries pass. Initial fixture reused a
request key for different mutations and expected TextValue for a direct-read
string; corrected without runtime changes. Concurrent local-server startup
failed in macOS psutil process enumeration; sequential rerun passes. No broader
platform/corpus qualification claim.
