# Published Truss v0.0.6 — 2026-10-13

Truss release workflow38450285520 succeeded: package, Linuxx86_64/macOSarm64
native consumer checks and publication. Source tag02fefb147d1cb9bba85c8e670d97afe8f2e359a7
publishes native0.43-candidate/layout0.16. Runtime manifest SHA256:
714b67b1455def530baa6fd7ee035df7856155e9655c2eaca6f00f024e0855e3.

Matching Weftv0.4.8/backend0.4.13 source008c636588732a551a6c3df7e9ca49b68bc2f761:
all five platforms passed workflow38448159500. Publication initially lacked the
release-notes file; an authorized draft supplied the notes and only the failed
publication job was rerun. Tag/source and built wheel artifacts stayed fixed.
Workflow publication then succeeded.

Actual public Truss and macOSarm64 Weft artifacts were downloaded, matched to
published SHA256SUMS and isolated from source packages. Both original UMF0.7/0.8
scalar container workflows passed25.354 seconds, including writes/imports/reads/
history/read-only/retry/rollback and explicit container query refusal. No managed
Aurora/Lakebase claim or full corpus claim. See the release pins for exact
PG18.6 pgserver18.6.1, psycopg3.3.6 and Bun1.4.2 dependencies.

[Truss release](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.6)
and [matching Weft release](https://github.com/DocumentDrivenDX/weft/releases/tag/v0.4.8).
