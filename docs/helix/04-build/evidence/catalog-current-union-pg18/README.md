# Current catalog union native checks

Run from the Truss repository root in a Python 3.11 environment with the
published `pgserver-pg18==18.6.0`, psycopg and the Python test dependencies.
Set `TRUSS_CENSUS_POSTGRES_BIN` to that distribution's `pginstall/bin` directory.

```sh
PYTHONPATH=packages/python/src:packages/python/tests:scripts python docs/helix/04-build/evidence/catalog-current-union-pg18/check.py
python scripts/build-catalog-finalization-reference.py --profile catalog-current-union --selection docs/helix/04-build/evidence/catalog-current-union-pg18/selection.json --postgres-bin "$TRUSS_CENSUS_POSTGRES_BIN" --output /private/tmp/truss-current-union-reference-new
```

The compiler output directory must not already exist. It owns its temporary
PostgreSQL server, stops it and retains the original inputs in the explicit
output directory. Expected reference SHA-256:
`fd634fa397414bcfab753f58f9f64b28daf7ea85ad3c091931400f4f44b551a0`.

`initial-native.log` records three passing methods and one failed fixture: a
readiness-only update violated the native phase constraint before validation.
`tamper-native.log` records the passing corrected generation and legal
`effects_ready`/readiness control. `cleanup.json` belongs to that corrected
replay. `portable-native.log` and `portable-cleanup.json` record the passing
repeat/write-free control from the integrated checkout. The source/reference
compilation and its cleanup are recorded in `reference-compilation.json`.

This validates a private administrative first-revision catalog composition.
The validator derives the scope from the actual transaction and verifies
already-finalized feed rows without publication or repair. Business refusal
triggers exist before admission; full composition validation runs before
capture/registration. Public acceptance, ordinary-role installation and the
conditional commit dispatcher remain unfinished; the unconditional commit
barrier is unchanged.
