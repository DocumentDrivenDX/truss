# Truss Python delivery

Truss owns the tested embeddable Python implementation. The complete engine
package is under implementation; current files provide the pinned local runtime
candidate, not released mutation/query/installation APIs.

For local PostgreSQL:

```sh
python3.11 -m venv .venv
.venv/bin/pip install -r packages/python/local-runtime-requirements.txt
.venv/bin/python scripts/local-postgres.py --data-dir .local/truss-postgres
```

Run from the repository root. Stop with Ctrl-C; data survives. `--probe` starts,
checks readiness and stops. This component uses pgserver0.1.4 with its actual
bundled PostgreSQL16.2 on the qualified macOS arm64 tuple. It performs no Truss
installation or migration. Use a host-supplied connection for external PostgreSQL;
pool configuration/operation belongs to the host.

See the [installation and migration execution plan](../../docs/helix/04-build/local-runtime-installation-migration-plan.md)
for the complete delivery scope and independent acceptance scenarios.

Rollback-only native profile checks (same environment):

```sh
.venv/bin/python scripts/check-pgserver-layout.py
.venv/bin/python scripts/check-pgserver-adjuncts.py
.venv/bin/python scripts/check-pgserver-umf-structure.py
```

Each creates its own disposable server and rolls back all review DDL. The last
compares the UMF schema-browser model with actual columns and FK mappings; it
is not a complete installer or migration verifier.
