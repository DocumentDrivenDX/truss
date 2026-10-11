# Catalog-only business statement refusal — released PostgreSQL18.6

Three native controls pass in10.233seconds on the published pgserver-pg18 18.6.0
wheel, SHA2568abba22528fc6f35ca1bf2d7d7638ca4515101d6830909a432e524b05d488ae8.
The runtime replaces the preliminary same-version wheel explicitly. Owned cleanup
confirms stop0/status3/socket absent.

The26real Truss business relations each refuse zero-row INSERT, UPDATE, DELETE
and TRUNCATE CASCADE before any operation is admitted:104checked statements.
INSERT controls omit generated columns so they reach the intended guard. Object
COPY with an empty stream, MERGE with a DELETE action and no source rows, and
DELETE in replica mode also refuse. Prior external caller work survives rollback.
Exact trigger mask62, ENABLE ALWAYS, no arguments/WHEN/transition tables, full
footprint and native relation topology are checked; disabling a guard refuses.
The early-sorted trigger name ensures legacy refusal does not mask this control.

This is a separately installable private catalog-only component. It adds no
instrumentation, logs/metrics exporter or allocation meter. It neither limits
Weft SQL coverage nor qualifies Truss mutation operations: this action profile
refuses business writes and has no released write capabilities.

Present trigger state is not uninterrupted history authority. Ordinary-role
protection against DDL/disable/owner bypass, metadata transition closure and the
shared current-union validator remain unfinished. The unconditional commit barrier
is unchanged; no public acceptance or commit activation follows.

Use the selected PG18 environment from repository root with
PYTHONPATH=packages/python/src:packages/python/tests:scripts and
TRUSS_CENSUS_POSTGRES_BIN pointing at that runtime's pginstall/bin. The default
suite selects only these three controls; imported connected baseline tests do not run.
