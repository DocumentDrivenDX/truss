# Original relationship SQL gap — 2026-10-13

Against installed runtime0.32-candidate / Weft backend0.4.5 / PostgreSQL18.6, unchanged `read.relationship-filter-both-directions` fails on its first query: `SELECT s.code FROM catalog.Solution s WHERE s.addresses = 'uc-1'`.

Public original catalog registration, fixture groups, commit, replay and read-only receipt inclusion succeeded before compilation. The result is `QueryRefused(code='invalid_query')` with `WFT-NAME-MISSING`, `Property not found among record members`. No forward/inverse/absent-key success or replica support is claimed. Original SQL and expected results are unchanged. Failed runtime retained at `/private/tmp/truss-original-relationship-r2-20261013`.

Next implementation belongs to Weft: resolve qualified single-key relationship equality into its existing relationship-existence IR, preserving actual forward/inverse endpoints and exact target-key typing. Scalar fields keep their existing semantics; composite keys and unsupported comparisons must not silently acquire shorthand meaning. Truss will exercise the original case through its public query API when that compiler behavior lands.

## Resolved implementation

The shared Weft application resolver now recognizes qualified single-key relationship equality with a literal or named parameter, only when the actual Record has no authored member match. It emits existing HAS_RELATED IR and keeps direction-specific typing and authorization. This is additive frontend support for existing application backend versions; transport/IR schemas and backend capability requirements are unchanged.

The unchanged three-query relationship case passes against the rebuilt extension (SHA256 `154674f561a04f362071988e1c1d4a0eb14343c09e0e53f8d030b63f8fecaebe`). Two basic native tests pass in17.018s: the original three-case consumer adapter and existing public relationship workflow, including scalar equality and composite-key shorthand refusal. Weft module boundaries pass11packages. Replica variants and the other original cases remain unqualified.
