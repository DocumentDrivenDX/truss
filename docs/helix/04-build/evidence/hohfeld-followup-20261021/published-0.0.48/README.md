# Public Truss 0.0.48 verification

[Validation](validation.json) binds all 15 published assets to source `8e89a068bcb68f1e631388ddc59bc97da748563d`, the mandatory Linux tag release gates and independent fresh public-wheel macOS gates. [Producer custody](producer-custody.json) records commands, source hashes and the installation/test timeline.

- Linux and macOS each pass 80 migration cases and 62 independent conformance cases, without failures, errors or skips.
- macOS also passes the exact 30 declared psycopg driver tests, 21 worker cleanup controls, and the published isolated `uvx` command from an empty cache with two independent instances retaining data and installation identity across restart. All 455 installed Truss runtime files match the public wheel and tagged source.
- The original Linux 1,000-object/1,000-edge workload passes with SQL10s/op30s; optional capacity/stress jobs and general p95 targets remain unqualified.

Previous application runtimes are unsupported. Admitted UMF0.10 databases migrate forward to the latest runtime without a release-age cutoff. This includes the actual v0.0.46 → v0.0.47 → v0.0.48 route and preservation of prior published receipts. Pre0.10 and protected-profile migration remain outside this release.

Public report assets are copied as original bytes under `public-assets/`; four large public archives are referenced by immutable URL, size and SHA in [external archives](external-archives.json). Raw local reports retain null CI fields. Installation-stage pending snapshots and the unqualified missing-test-dependency refusal are preserved as historical observations. Original native snapshots are retained with deterministic compression and raw-byte hashes. [Handoff](handoff.json) is the earlier publication-stage snapshot; its then-pending Mac field is superseded by this final validation, without rewriting history.
