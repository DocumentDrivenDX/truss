# Disposable native stage diagnosis

This run used two temporary CREATE OR REPLACE overlays in a disposable PostgreSQL database. Marker stripping restores the original product functions exactly. Runtime sources were unchanged; installed function bodies, the exact two changed definitions, OIDs, owners, ACLs and settings were checked. Timings use local clock assignments and RAISE LOG only, with no record content. Original workload sizes, repetitions and 10s statement / 30s operation deadlines were retained.

The instrumented run timed out with 57014 in final forest projection during a later changed 1,000-object group. Two prior changed groups committed. Cleanup passed. One incomplete validation has no forest end marker and does not establish its duration. These timings diagnose instrumented costs, not production performance.

For completed changed groups, preparation was about 2.28–2.29s (operation loop 1.83–1.85s; multiplicity about293ms). Final validation was about2.51–2.68s (transition loop1.71–1.86s; final identities538–558ms; node/incident check about6ms; forest239–241ms). Commit validation transition loops were about1.70–1.78s. History metadata took about8ms. The per-call analysis retains calls with observed total >=250ms; the raw compressed log contains all calls. Its aggregate includes create/edge phases and should not be described as update-only. Reproduce the analysis with `python analyze.py` in this directory; it reads the retained gzip log directly.

The separate uninstrumented development CI run38905362987 failed actual1,024-create workflows on Linux and macOS under the same deadline. PublishedSDK37 passed its own gates and is unaffected. No release-runner or latency qualification is asserted here.
