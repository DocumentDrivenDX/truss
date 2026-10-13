# Original repeated relationship predicates — 2026-10-13

The public original-consumer adapter now runs read.repeated-relationship-predicates-mean-both unchanged. Its added edge uses actual identities returned by public fixture creation, public CreateEdge/group apply, caller commit, durable original request replay and read-only reached. The original two AND predicates select sol-1 for both real targets and no rows when one target is absent. No SQL/expectation rewrite or administrative data seed is used.

Installed runtime0.33 / Weft backend0.4.6 / DocumentDrivenDX PostgreSQL18.6: the five original authority cases (eight SQL steps) pass in one native test10.216s. The extra fixture mutation runs last and does not alter the four earlier cases. This is not full corpus or replica evidence. Astra Ultra reviewed the adapter.

The next verified gap is the public SQL-page wrapper; explicit keyset SQL is supported, while native-ID object pages cannot substitute for business-key ordering.
