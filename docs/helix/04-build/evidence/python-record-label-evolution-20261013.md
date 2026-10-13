# Record name/member-order tranche — 2026-10-13

Native0.47/layout0.16, SDK0.0.10 and Weft0.4.12/backend0.4.17 allow Record
name changes and retained qualified-member reordering. Comparison excludes only
name/members; retained reference values and multiplicity remain required.
Property names, keys, relationships and other meaning remain guarded.
No existing object/key row, ID, value, version or timestamp is rewritten.
Current SQL resolves current names and member order. History remains committed
and revision-aware; original reports/documents/receipt replay remain retained.

Astra Ultra reviewed plan/source and approved with basic checks. Installed
UMF0.7/0.8 public workflows passed2 tests60.510 seconds: accept changed document,
exact row preservation, key lookup, complete query, mutation, committed object
and edge history, original receipt replay and restoration. Immediate .46→.47
upgrade passed1 test43.520 seconds, including rollback/commit, original facts,
read-only receipt/feed and continued mutation. Source .46 archive is byte-exact.
History check commits updates before reconstruction; no pending-history gate
was weakened. No managed target or full corpus claim.
