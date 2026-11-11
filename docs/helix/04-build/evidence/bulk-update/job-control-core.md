# Bulk job-control core — evidence (2026-11-10)

Scope: `packages/python/src/truss/_bulk_job_control.py`, a pure port of the UMF CONTRACT-904 control rules plus the CONTRACT-013 capacity check. No I/O, no PostgreSQL, no locks, no connection custody.

Command: `PYTHONPATH=packages/python/src python3.11 -m unittest discover -s packages/python/tests -p test_bulk_job_control.py` — 13 tests pass. Expectations come only from the pinned UMF owner fixture (`packages/python/tests/fixtures/bulk-update/transitions.json`, sha256 `ad94f478…396e`, upstream `status: planned`, owner review pending) and the CONTRACT-013 numbers (R = 2 MiB, C = 256 MiB, 100 batches + 16 MiB manifest leaves 40 MiB; R = 8 MiB refuses).

Negative controls (each made the suite fail, then restored): ambiguous reconcile evidence stopping the job; capacity check off by one at the boundary; confirmed-no-execution expiry requeuing admitted work.

What this does not show: any US-046/047/048/049 acceptance criterion. Those are native-integration criteria and stay `planned`. Residuals: the fixture needs owner review; the module is not yet called by any executor; durable persistence under the job lock, original attempt custody, authorization and tx/1 composition remain unimplemented.

## Addendum (control layout)

`control-layout-results.json` records `check_control_layout.py` against PostgreSQL 18.6: 79 cases pass. A final-batch cancel now yields `completed` in `_bulk_job_control.py` (3 added tests); UMF PR 131 added the covering fixture cases and fixed its model; this repo now pins the corrected fixture (sha256 `3cbca1f1…474c`, 16 tests pass) and the TLA job table, TLC receipts (607,102 states), refinement and layout receipts were regenerated against it.

## Addendum (claim/fence/cancel functions)

`claim-fence-native-results.json`: 27 checks pass on PostgreSQL 18.6 (role `bulk-worker`, lock level 4a). Four deliberate breaks of the SQL were each detected. This is the first native run of the claim/fence/cancel rules, but only for the control row; it does not close US-048-AC2/AC3, which need the effect transaction, original custody and the real lock prefix.
