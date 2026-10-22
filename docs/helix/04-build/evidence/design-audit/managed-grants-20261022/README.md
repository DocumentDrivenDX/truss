# Managed platform grants: local qualification

The managed-grants implementation was qualified locally on 2026-10-22 with Sol planning/review and Luna implementation. Changes were confined to Truss and owned temporary qualification files; no Praxis or Arras source changes or publication were performed. Actual Lakebase acceptance remains a separate gate.

The [aggregate audit](local-qualification.json) binds the final candidate wheel `7a41a223033c1af0da4a2df2d377c672fcd3b3be1fcfc5b5bf8232d009725ed4` and native manifest `35fd797b5cf48dd888c68e53b9e599df20cffe00f8f3d33e1563820ea808d59f`. The [environment record](build/final-3-environment.json) records Python 3.11.17, macOS ARM64, PostgreSQL 18.6, psycopg 3.3.6 and Weft 0.4.51. These are bounded local results, not complete release qualification.

| Gate | Final observation | Evidence |
| --- | --- | --- |
| Selected installed components | 19 modules, 116 tests, zero skips | [Receipt](attempt-4/selected-components/qualification.json) |
| Concurrent HF corpus | All 61 cases passed, zero skips | [Receipt](attempt-5/hf-corpus/qualification.json) |
| Protected regression | Nine tests passed | [Log](attempt-5/protected-regression.log) |
| Published migration lineage and recovery | 80 tests, three published source populations, zero skips | [Receipt](attempt-5/migrations/qualification.json) |
| Original public workload | 1,000 objects and 1,000 edges; 1,000 reads; 200 committed updates; reopened values verified | [Report](attempt-5/public-workload/report.json) |
| Managed lifecycle supplement | Additive evolution and history preservation passed; unsupported retirement refused with no effects and caller work committed; later selected grant/revoke tolerated | [Result](supplemental/final-3/managed_grants_lifecycle_installed.json) |
| Module boundaries | 1,724 imports checked; all 20 allowed/forbidden boundary controls behaved as expected | [Imports](attempt-4/boundaries.log), [controls](attempt-4/boundary-controls.log) |
| Artifact custody | 459 package files verified; all 15 historical migration artifacts preserved byte-for-byte | [Payload](build/payload-verification-final-3.json), [capture receipt](runtime-migration-captures/receipt.json) |
| UMF model | Import/export native AST equality checked with the recorded parser/version | [Model evidence](managed-grants-model.json) |

The [remaining final gates](attempt-5/qualification.json) passed with unchanged input hashes. Qualification workers restored their inventories and stopped. The workload measured 26,121 SQL submissions including measurement overhead; it establishes neither a general latency budget nor a maximum capacity. Supported evolution passed; successful retirement is not claimed.

The [concurrent preservation audit](build/concurrent-preservation.json) records baseline custody and reviewed overlaps. The concurrent commit was retained, historical artifacts were not rewritten, and the final HF run qualifies the composed behavior. The [final corpus archive](hf61/final-cli-migration-35fd.zip) retains the final producer snapshot. Producers and environment records are retained under [build](build/); the independent [final audit producer](build/final-audit.py) binds the aggregate receipt.

The original [broad installed-suite attempt](attempt-1/installed-suite/installed-suite.json) remains **incomplete and unqualified**: it executed 1,262 tests with 35 opt-in skips on the first candidate, then stopped after fixture-cleanup failures. Its [original qualification](attempt-1/qualification.json) is retained. Later scoped passes do not turn that run into a full-suite pass. Intermediate failures and the stale-corpus preflight refusal remain in attempts 2–4; the positive attempt-4 claim above covers its selected-components receipt only.

Complete legacy-suite acceptance, hosted Linux qualification, publication, actual Lakebase/TLS/token acceptance, and Arras adoption remain open gates. No release tag or publication was created by this work.
