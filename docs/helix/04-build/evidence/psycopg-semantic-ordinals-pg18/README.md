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

## Retained semantic parameters

`retained-parameters-native.log` records 11 native controls passing against
actual PostgreSQL180006. The same module command above runs these expanded
controls. A separate regression run of the semantic, existing host and fresh
catalog dispatch suites passed42 tests before the final uncertainty control was
added; the corrected full semantic suite subsequently passed11 tests.

An optional trusted parameter producer runs only after original transaction
matching. The exact immutable tuple is retained on the existing attempt before
the effect callback. The logical bound includes every cell, including ordinal
text, using UTF-8 byte lengths for strings: at most64 parameters and4MiB total.
There is no transport allocation-accounting claim. The deadline is checked again
after production. Producer/validation failures execute no effect callback;
savepoint/observation and cleanup SQL still occur.

The actual original preparation and six catalog inputs are bound to a native
SELECT with inherited hostile text/byte dumpers on the host connection. Stock
text and binary dumpers are selected only on the toolkit cursor; native encoded
values equal every retained byte input, and the host's adapters remain unchanged.
Failure controls retain the tuple across SQL failure, expiry and an injected
unconfirmed deadline-completion reply. That injection first stops the real timer.

This verifies private custody and parameter transport. The generic callback does
not establish fixed-facade SQL/tuple correspondence. The protected catalog body,
its result grammar and public acceptance remain unimplemented.
