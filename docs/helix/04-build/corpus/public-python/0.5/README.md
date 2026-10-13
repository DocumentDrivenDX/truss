# Public Python preview corpus 0.5

Two portable JSON cases exercise the public Python interface using installed
Truss and Weft packages on DocumentDrivenDX pgserver-pg18==18.6.1/PostgreSQL18.6
and psycopg3.3.6. The selected runtime is0.31, layout0.16 candidate and Weft
backend0.4.4. Inputs carry their original UMF fixture digest; native identities
come from public results. Caller phases explicitly commit, roll back or read only.

`adopter-basic.json` retains the prior 22-observation workflow: catalog,
object/edge writes, original-request replay, key/query reads, refusals, dry-run,
imports, durable feed/ACK and receipt comparison. `exact-scalars.json` adds ten
observations covering public creation and import followed by key and complete
SQL reads of string, integer, decimal, boolean, timestamp and binary properties.
An omitted optional field and an imported explicit null remain distinct.

Run either case with a new or empty directory:

```sh
python packages/python/examples/run_corpus.py \
  docs/helix/04-build/corpus/public-python/0.5/exact-scalars.json \
  /tmp/truss-exact-scalars --bun bun
```

Authored integer/decimal/time/binary values use exact text; booleans require JSON
booleans, and explicit null uses `{kind:"null"}`. Unknown kinds or extra members
refuse. Direct reads retain original `TextValue` spelling. Query integers use
exact Python integers; decimal observations use `str(Decimal)` without floating
point conversion. Timestamp and binary queries retain their `TextValue` tokens.
Optional query absence is `{kind:"absent"}`, separate from `{kind:"null"}`.
The cases explicitly compare every returned scalar property and output column.

Success is `passed_preview` for one Python implementation. These cases do not
complete the [original required corpus](../../../evidence/consumer-revision-2026-10-09/corpus.json)
or independent bidirectional native interchange. Earlier0.1–0.4 datasets retain
their original versions and bytes; the current runner selects0.5 explicitly.
The physical layout, runtime, protected security profile and public API are unchanged.
