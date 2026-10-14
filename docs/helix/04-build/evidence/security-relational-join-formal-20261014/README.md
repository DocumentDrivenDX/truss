# Conditional bag join eligibility

Run `/private/tmp/umf-write-comparison-proof-env-20261013/bin/python scripts/prove-security-relational-join.py` using Z3 4.15.4. Four original SMT-LIB queries and fresh-context replays match their expected outcomes. Arbitrary nonnegative integer multiplicities are retained; this is not a bounded enumerated fixture.

Three unsatisfiable counterexample queries establish that joining two independently eligible bags equals the original join predicate with both eligibility predicates, and neither hidden input contributes a result occurrence. The satisfiable one-sided-filter query demonstrates a leak when the right input is hidden but only left eligibility is applied.

US-056-AC2 and Truss B03/B08 linkage is conditional logical evidence. Eligibility correctness, native identities, source completeness, original predicate interpretation and compiler mapping are premises. No PostgreSQL optimizer, SQL, parser, driver or release refinement is proved. Outer joins, NULL/absence and cursor semantics require separate laws and native controls. This does not promote any original acceptance case.
