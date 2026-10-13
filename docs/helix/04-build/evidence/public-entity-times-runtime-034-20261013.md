# Public entity timestamps, runtime0.34 — 2026-10-13

Whole-object SQL with read_profile=complete-entity now includes _created_at/_updated_at as exact six-fraction UTC strings. The new Weft entity read profile0.2, compile/IR/backend2.3 and backend0.4.7 select installed Truss runtime0.34. Old schemas2.2 and old five-field entity profile0.1 stay unchanged. SQL paging admits the new transport without changing authored-key or continuation semantics.

The additive owned query_object_times helper invokes original verified attribution, then uses the same STABLE statement snapshot/current after-image for object timestamps. It refuses nonfinite/out-of-range dates; journal insertion time is not used. PUBLIC execute is revoked and current module reader/writer roles receive the helper through the installation/access/upgrade paths. Exact archive033 bytes are retained. Upgrade captures all existing .33 query/feed/entity routine OIDs, owners and ACLs before replacement; the physical layout is unchanged.

Installed basic evidence on DocumentDrivenDX pgserver-pg18 18.6.1/PostgreSQL18.6, psycopg3.3.6 binary/libpq18.6:

- Public create/update/no-op/import and fresh read-only whole-object query: one test,9.476seconds. Query timestamps exactly match public ScalarObject timestamps; no-op leaves the whole entity unchanged.
- Seven unchanged original consumer SQL/output variants plus populated .33-to-.34 upgrade/rollback/receipt replay/feed preservation: two tests,18.136seconds. The required whole-object metadata fields are present. Consumer answer-position/time and replica invariants remain outside these scoped observations.
- Existing public preview workflows pinned in new corpus0.8: two tests,18.242seconds (basic22 and exact-scalar10 observations); original .1–.7 and UMF fixture bytes are preserved.
- Python type fixtures: five,20 expected negative diagnostics. Import boundaries877; Weft workspace boundaries11. The new standard-library datetime dependency is explicit.

Astra Ultra reviewed the plan and final source. It found missing timestamp schema alternatives and missing .33 routine-preservation coverage; both were corrected before the passing installed results. Old schema files remain byte-identical. Protected security activation, full original consumer harness/corpus and independent bidirectional native interchange remain open.
