# Source-F installed Truss qualification

This packet binds the actual rebuilt Weft source-F module to the installed Truss
candidate. The final macOS campaign passes 80 migration cases, 62 independent
archive cases, 6 cohort controls, 14 policy executions (10 distinct controls; four
imported query tests repeat) and the original 1,000-object/1,000-edge workload.
All final tests pass without skips. All 455 runtime payloads still match the exact
source, wheel and sdist built at `22ed3335`.

Original raw outputs remain unchanged. The earlier skipped policy run, enabled
policy timeout and sandboxed migration refusal are retained separately and are
not qualification passes. The timeout cause remains unproven; the serialized
policy retry uses the same 2-second statement and 30-second operation limits.
The public workload separately retains its 10-second statement deadline.

The independent corpus producer-pin correction and original c08 refusal are in
the [producer-pin repair packet](../../arras-source557-producer-pin-repair-20261022/README.md).
The previous source-86 packet remains historical. No native evidence transfers
between the differing compiler modules. Public Weft adoption, Truss Linux tag
gates and fresh public artifact verification remain mandatory.
