# Bulk job-control core — evidence (2026-11-10)

Scope: `packages/python/src/truss/_bulk_job_control.py`, a pure port of the UMF CONTRACT-904 control rules plus the CONTRACT-013 capacity check. No I/O, no PostgreSQL, no locks, no connection custody.

Command: `PYTHONPATH=packages/python/src python3.11 -m unittest discover -s packages/python/tests -p test_bulk_job_control.py` — 13 tests pass. Expectations come only from the pinned UMF owner fixture (`packages/python/tests/fixtures/bulk-update/transitions.json`, sha256 `ad94f478…396e`, upstream `status: planned`, owner review pending) and the CONTRACT-013 numbers (R = 2 MiB, C = 256 MiB, 100 batches + 16 MiB manifest leaves 40 MiB; R = 8 MiB refuses).

Negative controls (each made the suite fail, then restored): ambiguous reconcile evidence stopping the job; capacity check off by one at the boundary; confirmed-no-execution expiry requeuing admitted work.

What this does not show: any US-046/047/048/049 acceptance criterion. Those are native-integration criteria and stay `planned`. Residuals: the fixture needs owner review; the module is not yet called by any executor; durable persistence under the job lock, original attempt custody, authorization and tx/1 composition remain unimplemented.

## Addendum (control layout)

`control-layout-results.json` records `check_control_layout.py` against PostgreSQL 18.6: 79 cases pass. A final-batch cancel now yields `completed` in `_bulk_job_control.py` (3 added tests); the pinned UMF fixture does not cover that case and the UMF model still says `cancelled` there.
