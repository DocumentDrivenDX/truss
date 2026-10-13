# Public field-name evolution —2026-10-13

Installed SDK0.0.21/native57 and Weft0.4.22/backend0.4.27: both original UMF0.7/0.8 public workflows passed (2 tests,25.608s) on DDdx PostgreSQL18.6/psycopg3.3.6. Key and non-key names change while object rows, key rows and property IDs remain unchanged. Public lookup/query/update/history/committed replay succeed. A retained unknown-name value is written through the public mutation API; a colliding field rename refuses with rule/count. Rename-plus-new-member reuse of a prior name refuses in both authored member orders.

Astra Ultra reviewed the plan and completed source, including PostgreSQL expression precedence, exact capability definition hashes and the deterministic prestate collision check. Rust workspace/test-target compilation and11-package boundaries passed. Python1003-import boundaries passed. The retained native56 manifest byte-matches the predecessor wheel; no source archive was rewritten.

Corrected-wheel populated56→57 upgrade passed (1 test,7.438s), including caller rollback and continuation with original facts.
