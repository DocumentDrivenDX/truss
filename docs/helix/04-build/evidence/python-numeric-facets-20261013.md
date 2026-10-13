# Python numeric facets — 2026-10-13

Runtime 0.39 candidate adds signed64 and decimal(18,4) to original UMF 0.7/0.8
catalog preparation and native public operations. Weft backend 0.4.9 admits
these exact facet maps; older backend contracts are retained. Original owner
assertion evidence is unchanged. A separately scoped runtimeFacetEnforcement
report adjunct is gated by the original request support profile.

Basic installed-wheel tests cover public acceptance, create, update, import,
read-only reads, parameterized Weft queries, integer overflow, decimal overflow
and refusal of rounding. The populated upgrade test uses the actual published
v0.0.1 wheel and preserves original reports, receipts, routine custody and
caller rollback behavior across runtime 0.38 → 0.39.

Final installed-wheel run after Astra’s native profile-gate fix passed all three
tests in 24.764s. Both UMF 0.7 and 0.8 public workflows passed.
The two initial tests passed in 16.806s on macOS arm64, PostgreSQL 18.6,
psycopg 3.3.6, pgserver-pg18 18.6.1 and the production Rust ABI3 wheel.
The broad Rust lib-test build hit an existing unrelated nonexhaustive
Shape::ExactScalar match in property_definition.rs; production release builds
and the actual compiled-query workflow passed. No second implementation or
managed-database qualification is claimed.

Truss v0.0.1 release Actions run 38416525880 passed package build, Linux/macOS
native tests and publication. Published assets and SHA256SUMS were downloaded
and verified. Weft v0.4.3 recovery run 38414272945 built and smoke-tested all five
platform wheels without retagging the source. Numeric facets are the subsequent
unpublished iteration, not a v0.0.1 release claim.

Astra Ultra reviewed the plan and completed iteration. Its native admission
profile-gate finding was fixed and tested; final source approved, with release
and unpublished-main upgrade instructions separated.
