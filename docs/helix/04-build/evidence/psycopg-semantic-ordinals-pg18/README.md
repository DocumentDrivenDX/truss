# Psycopg semantic operation ordinal evidence

37 tests pass: six native semantic-issuer controls, 26 existing native host
controls, and five shared ordinal corpus/reservation controls. The semantic
fixture asserts actual PostgreSQL `server_version_num=180006`, registers owned
cleanup before startup, and preserves the directory if shutdown is unconfirmed.

Run from the repository root with psycopg 3.3.6 binary installed:

```sh
TRUSS_CENSUS_POSTGRES_BIN=/absolute/path/to/pginstall/bin \
PYTHONPATH=packages/python/src:packages/python/tests:scripts \
python -m unittest test_psycopg_semantic_ordinals_native test_psycopg_host_native test_operation_ordinal -v
```

The production caps are 256 transaction bindings per physical connection and
256 attempts per native transaction. The capacity tests inject the counter/map
at those boundaries; they do not claim execution of 256 native transactions.
The failed-SAVEPOINT test submits a malformed SAVEPOINT and confirms retention
of the consumed ordinal and conservative quarantine. The reservation-publication
fault is a local injected exception after authoritative counter publication.

This qualifies the private host ordinal seam. It does not qualify public catalog
acceptance, a protected native facade, or the complete installation profile.
