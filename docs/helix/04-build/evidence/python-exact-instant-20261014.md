# Public exact timestamp query increment — 2026-10-14

SDK23/native59 and Weft24/backend29 select committed UMF
`umf-rfc3339-exact-instant/1.0.0` under compile/IR/backend0.2.6. Generic timestamp,
temporal facets and temporal business keys remain unchanged. Original tokens
stay in scalar cells, public reads/projections and typed parameter slots.
Both stored fields and query operands normalize to exact UTC whole seconds and
fraction digits; no timestamp cast or fractional rounding is used.

The basic installed PostgreSQL18.6 workflow covers original UMF0.7 and0.8 catalogs,
public creates/readback, offset equality, differing seventh fractional digits,
unknown local offset, required/optional equality, absent/null nonmatches, literals,
joins, pages and read-only transactions. Invalid leap-second parameters refuse
even against an empty source. The original binary workflows remain passing.

Final installed SDK23v4 + original Weft24 wheel: five sequential native tests pass
in48.058s, including populated native58→59 upgrade, rollback, immutable old facts,
receipts/feed state and continued operations. The exact native58 predecessor
manifest equals the retained upgrade-source-058 bytes. All packaged manifest
hashes match; Python1031 imports and Weft11-package boundaries pass. Workspace
Rust checking and one targeted exact-instant Rust test pass.

Astra Ultra source review found and corrected exact compiler version admission,
the new helper's exclusion from predecessor routine custody, and archive058
hash verification. The first installed test attempt failed solely at the unavailable
compiled selector after successful timestamp writes/reads; corrected workflows
pass. No broader performance/conformance or Ashlar native support is claimed.
The existing release workflow publishes matching wheels after its native checks.
