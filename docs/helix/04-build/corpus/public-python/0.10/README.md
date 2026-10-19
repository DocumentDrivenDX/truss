# Public Python preview 0.10

This directory preserves a historical preview case, not the current Truss
v0.0.40 owned workflow. Its model fixtures use UMF 0.7.0 and its recorded
runtime is 0.38-candidate; both are incompatible with the current UMF 0.10-only
v0.0.40 source path. Keep this corpus for its historical observations only.

Two portable JSON examples run through the installed public Python API on
truss-toolkit0.1.0.dev38/native runtime0.38-candidate, layout0.16 candidate,
Weft runtime backend0.4.8, DocumentDrivenDX pgserver-pg18==18.6.1/PostgreSQL18.6
and psycopg3.3.6. Follow the current Python package README for installation.

From the Truss repository root, with a new or empty runtime directory:

```sh
python packages/python/examples/run_corpus.py \
  docs/helix/04-build/corpus/public-python/0.10/adopter-basic.json \
  /tmp/truss-preview-basic --bun bun
python packages/python/examples/run_corpus.py \
  docs/helix/04-build/corpus/public-python/0.10/exact-scalars.json \
  /tmp/truss-preview-scalars --bun bun
```

The basic example retains22 observations covering catalog, object/edge mutation,
committed replay, key/query reads, refusals, dry-run, import and durable feed/ACK.
The exact scalar example retains10 observations for string, integer, decimal,
boolean, timestamp and binary properties, including absence versus explicit null.
Caller phases explicitly commit, roll back or read only. Native identities come
from public results; exact values never pass through floating point conversions.

Only the preview format and runtime pins/expected install release change from0.9.
All other inputs and expected observations remain identical; both original UMF
fixtures are byte-identical. The runner explicitly selects0.10 and refuses other
profiles. Success is `passed_preview` for one Python implementation, not complete
consumer conformance, stable layout or independent interchange. Prior datasets
remain unchanged and need their historical runner/package for reproduction.
