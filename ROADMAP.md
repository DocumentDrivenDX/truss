# Roadmap

Unbuilt work, in no committed order. Nothing here is supported today.

- **Query**: Weft relationship queries work with umf-weft 0.4.57. Widen the accepted range to
  umf-weft 0.4.58+ once it is published.
- **Typed SDK**: `truss.access` needs umf-access 0.10.11 (not yet published); the `typed-sdk` extra
  stays out of the default install until then.
- **PyPI-only install**: drop the pgserver `--find-links` line once `pgserver-pg18` is on PyPI.
- **Temporal values and bulk job control**: shipped as experimental; native coverage is partial.
- **Protected admission**: ordinary-person admission and the complete installed security profile
  (the former security prototype was removed; its design record is in git history).
- **Other PostgreSQL versions**: only 18.6 is supported.
- **Packaging**: move `docs/helix/02-design/contracts/bindings` (TypeScript source) into a package.
- **Managed services** (hosted PostgreSQL such as Lakebase) are not qualified.
