# PostgreSQL17.11 cluster reuse timing

One local sample per configuration using the same cached pinned wheels. All 15 groups passed. No source build or wheel installation is included.

| Configuration | 12 reusable native checks, including startup and cleanup | Full 15-group comparison |
| --- | ---: | ---: |
| Previous cluster per experiment | 77.8 s | 105.8 s |
| Shared, one worker | 22.1 s | 50.2 s |
| Shared, two workers | 20.3 s | 48.4 s |

The three isolated lifecycle groups took 28.0 s, measured once and added equally to each native configuration. These full totals are composed comparisons, not three separately timed full-suite invocations. The previous total sums successful subprocess durations. Nine durations were retained at millisecond precision after an instrumentation import-path failure; that failed attempt is excluded.

Previous cluster startup totaled 52.7 s and pgserver cleanup totaled 5.4 s. One shared worker took 4.39 s to initialize and 0.42 s to stop/remove; its 12 fresh database/role creations totaled 1.98 s and fixture cleanup totaled 3.14 s. Two workers took 3.59/7.76 s to become ready (including serialized startup lock wait), and 0.74/0.84 s to stop/remove. Concurrent durations must not be added to infer wall time.

Single samples in fixed order; workstation load/cache may affect results. Shared baselines were verified after every case, workers stopped and owned directories removed. See benchmark.json for raw timings. Run benchmark-driver.py with the existing pinned qualification Python environment to generate a fresh comparison directory; benchmark-child.py adds timing instrumentation only.
