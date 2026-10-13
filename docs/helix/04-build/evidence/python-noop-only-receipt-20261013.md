# No-op-only writer receipt — 2026-10-13

The existing basic no-op receipt test previously created the object and applied the no-op in one writer transaction. That already provided durable no-op replay, stable token and fresh read-only reached evidence; it was not missing coverage entirely.

The same test now commits creation first, then applies only the unchanged update in a fresh caller transaction. Both later retries use the exact retained semantic input and request, return the original complete semantic result and the same nonempty committed receipt token. The unchanged native result has no mutation event references. After ending the retry transaction, the existing fresh read-only call confirms receipt inclusion; existing malformed/changed-token refusals remain.

One existing installed-package test (`test_receipt_visibility_native.ReceiptVisibilityTests.test_noop_token_is_stable_and_missing_evidence_is_unavailable`) passes in6.649seconds on truss-toolkit0.1.0.dev38/native0.38/layout0.16 candidate, DocumentDrivenDX pgserver-pg18==18.6.1/PostgreSQL18.6 and psycopg3.3.6. This is the R7 basic no-op-only writer workflow, not a new conformance or fault campaign. No runtime code, native semantics or package version changed.
