# Compatible numeric refinement tranche — 2026-10-13

Implements a bounded subset of FEAT-001 CAT05 / US-005 and the feature-first
release goal: existing non-key exact scalar properties can transition between
unfaceted and the supported signed64 or decimal(18,4) maps. Every field occurrence
retains identity/name/family/cardinality/storage semantics; any primary or
alternate-key participation refuses changes. Unknown maps remain unsupported.
Historical nullability-only catalog folds keep their original admission.

Before narrowing, the native exclusive catalog-head fence excludes supported
writers. Existing present/non-null/base-family-valid cells are checked against
the desired known facets. Violations return `property.facets` with exact affected
counts, document/module/record/declaration-owner identity and no accepted revision.
Missing/family failures retain their distinct rules and are not double-counted.
Current module and declaration-owner authority is required before counts and
rechecked before handback. Counts are the current Python subset; this does not
claim the full CAT05 per-object violation enumeration interface.

A successful transition changes the property definition/source pin and adds
catalog evidence without rewriting object values, IDs, versions, timestamps or
record revisions. Unchanged record fragments retain their type pin. Historical
reports use the original revision fold, and original committed group replay
precedes current-value validation. Removing known facets is widening.

Runtime0.42-candidate preserves layout0.16 and upgrades0.41 additively, including
prior traversal/key helper custody and current module facade grants. Weft0.4.7 /
backend0.4.12 selects0.42; older0.4.11 retains0.41 correspondence.

Installed Python wheels on PostgreSQL18.6/psycopg3.3.6:

- Both original UMF0.7/0.8 workflows: create valid/invalid unfaceted rows; refuse
  exact counts; public repair; accept narrowing; preserve identities/versions/
  record revisions/exact values and historical report; original group replay;
  exact Weft query; widening and catalog retry.
- Additive0.41→0.42 upgrade: original data/reports/receipts/feed/routines preserved,
  caller rollback, commit and a subsequent public write.
- Final3 tests28.565s PASS. Python boundaries932 imports PASS.

Astra Ultra approved the plan and completed iteration after a concrete guard
correction: both sides of actual facet changes must be known family-matching
maps; counts apply only to known desired maps. Existing historic nullability-only
folds stay unchanged. No performance/conformance campaign was added.
