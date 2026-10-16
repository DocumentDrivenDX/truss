# Captured graph cut transport

The disclosure evaluator previously replaced captured `graphs` and
`graphCoverage` with empty arrays. It now transports all four captured
populations byte-for-byte through `disclosure_fact_cut`. The helper requires
explicit strict JSON arrays and refuses metadata collisions; no completeness
or permission is inferred. Existing evaluation-frame bounds remain enforced.
The compiler integration fixture now supplies all four populations explicitly.

The focused run executes 20 tests: 17 pass and three required parallel cases
remain expected failures on the packaged UMF 206951/d333 cohort. The original
15-case attempt observed those same three refusals; the other 12 cases produced
the original expected resources. The expected-failure tests retain the desired
rendered behavior, rather than redefining refusal as acceptance. They must be
removed when an independently qualified packaged-cohort upgrade passes them.
The new strict transport control preserves exact large-integer, decimal and
escaped-string tokens and rejects malformed/missing populations and collisions.

`probe.json` retains six actual semantic-child observations with cleanup:
removing graph data and coverage makes all three base Subjects refuse in the
packaged cohort; current clean UMF source 11b412e4 produces the required parallel
results (Alice: RA, Bob: RB, Outsider: none). This isolates a packaged-cohort
qualification gap. It does not prove which source change causes the difference.
The production packaged cohort and Weft pins are unchanged by this patch.

This supports the US-056-AC6/AC7 complete-source and empty-population prerequisites
in UMF STP-056. It is supplied-cut semantic/transport evidence, with no SQL,
authenticated Subject/source custody, whole compiler/driver integration, native
admission, guarded release, or backend case promotion. The original 158 cases
and 34 criteria remain required (45 implemented, 113 missing at the governing
checkpoint); these component results do not change those totals.

Replay focused tests with the Python source/test directories on PYTHONPATH and
`TRUSS_GRAPH_TRANSPORT_COMPONENT_QUALIFICATION=1`. `probe.py UMF_ROOT` additionally
needs the named clean UMF source checkout and Bun 1.4.2. The source checks are
endpoint correspondence, not held-file/ABA or hermetic-build proof.

Bounded Astra review of the frozen 7c65ee10 diff completed within five minutes
with no findings, including an independent 15-packet packaged replay. Its
19-artifact manifest and complete packet are retained. No re-review was needed.
An additional actual exact-Weft-a944 compiler/child component replay passes all
66 vectors (46 rendered, 20 refused, six stale fixture generations replaced by
the simulated host generation), in 49.476s. SQL remains explicitly simulated.
The three parallel expected failures above remain open despite that replay.
