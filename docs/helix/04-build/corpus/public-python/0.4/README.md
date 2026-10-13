# Public Python preview corpus 0.3

This directory publishes one language-neutral JSON case, its exact UMF fixture,
and explicit result/feed projections. `adopter-basic.json` is the input to the
public Python runner; its values, SQL, actor roles, caller transaction boundaries
and expected results drive execution. Native IDs, original request objects,
receipt tokens and feed cursors are captured from public results, not supplied as
fixture IDs. The report identifies the exact case digest and selected versions.

Run from the repository root with the installed Truss package, Bun and Weft
runtime backend0.4.4 (feature `truss-postgresql-pg18`):

```sh
python packages/python/examples/run_corpus.py \
  docs/helix/04-build/corpus/public-python/0.4/adopter-basic.json \
  /tmp/truss-public-preview --bun bun
```

Use a new or empty runtime directory. The fixture is resolved relative to the
case, confined to that directory, and checked against its SHA256. Copy this
whole corpus directory when using it elsewhere. The case cannot select code or
an executable; the trusted caller supplies the installed runner and Bun path.
Unknown formats, profiles, operations, fields and projections fail execution.
A newer required corpus cannot be reported as this version's successful preview.

The case checks accepted catalog registration, atomic object/edge writes,
committed original-request replay, source and consumer receipt comparison,
business-key and Weft relationship reads, reader/outsider refusals, precondition
refusal, caller rollback, and a mixed created/skipped/rejected import. Canonical
post-import reads check three objects and no invalid import. Feed assertions
compare all four mutation events, their actual identity aliases, values, versions,
authenticated database actors and edge endpoints/order key, plus import provenance
and original document bytes. Exact feed pages remain in the durable sink before
separate committed source ACKs. Declared projections identify metadata retained
but not compared; they do not make that metadata a passing observation.

Success is `passed_preview`. This is one Python implementation executing shared
data on DocumentDrivenDX pgserver-pg18==18.6.1/PostgreSQL18.6/psycopg3.3.6, layout
0.16 candidate and runtime0.31. It does not qualify a stable layout, TypeScript
engine, complete required corpus or bidirectional interchange. The original
[41-case consumer corpus](../../../evidence/consumer-revision-2026-10-09/corpus.json)
and [STP-028](../../../../03-test/test-plans/STP-028-pass-the-corpus-and-the-interchange-check.md)
remain open. Two callers or two wrappers around this Python implementation would
not supply the required independent second implementation.

Versions 0.1, 0.2 and 0.3 remain retained for their original runtime/backend pins.
Version 0.4 selects runtime0.31/backend0.4.4; the case and fixture meaning remain
unchanged. Mixed-scalar source reads have separate native workflow evidence.
