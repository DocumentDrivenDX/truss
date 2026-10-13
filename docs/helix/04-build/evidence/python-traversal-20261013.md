# Public bounded traversal iteration — 2026-10-13

Implements FEAT-005 RD04 / US-023 and CONTRACT-004's separately qualified
one-call live traversal subset. It follows the feature-first release ordering
in `../release-tranches.md`, without claiming staged snapshot resumability.

`ReferenceAssembly` and its direct-read provider expose `traverse_in_transaction`
with a typed start and1–3 qualified relationship/direction hops. Supported
independent directed relationships return unique terminal scalar objects after
all hops, ordered by exact numeric type/id. Cycles exclude repeated typed objects
within each path, including the start. Diamond paths deduplicate terminal objects
without a global visited-node shortcut.

A materialized recursive stream caps all attempted states before terminal
filtering/dedup/order; cycle attempts consume the limit. Complete results have no
continuation. A state/result/byte limit returns limited/not-established/restart
with no objects. Logical state/output bounds and ordinary PostgreSQL deadlines
are the practical stock-PostgreSQL profile; this makes no exact physical scan,
allocation, rollback-resistant accounting or stable multi-call membership claim.

Start existence, edge expansion, terminal rows and row-home facts share one
native statement snapshot. Scalar rendering consumes frozen row/catalog inputs
without current data-table reads. The full declared endpoint/property/relationship
scope is authorized before observation and rechecked with catalog head before
handback, including byte-limit outcomes. Existing object reads now also require
property declaration owners; identity/key/pages inherit that correction.

Runtime0.41-candidate preserves layout0.16 and upgrades exact0.40 installations
additively. The old manifest is retained byte-exact. Existing typed-key helper
OIDs/ownership/ACLs are included in preservation checks; the new traversal facade
starts owner-only and grants only configured reader/writer roles. Weft0.4.6 /
backend0.4.11 admits the new release while preserving0.4.10→0.40 compatibility.

Basic installed-wheel PostgreSQL18.6 evidence:

- Create→commit→read→original durable replay:1 test6.353s PASS.
- Diamond/cycle1/2/3 hops, incoming/both, state/result limits, read-only call;
  cross-module declaration-owner refusal; actual public0.0.3→new runtime upgrade,
  rollback/preservation/replay/feed/next write:3 tests19.632s PASS.
- Original UMF0.7/0.8 exact numeric write/read/import/Weft query:2 tests18.212s PASS.
- Python module boundaries:932 imports PASS. Production Weft ABI3 wheel built.

Astra Ultra reviewed the plan, implementation and matching Weft delta. Concrete
findings fixed: JSONB operator precedence, public identity encoding, old helper
custody, non-PUBLIC default ACLs, final authority checks for resource outcomes,
and manifest/capability version alignment. No broader campaign was added.

An accidental module-level test invocation also discovered legacy create tests
with outdated failure/profile assertions; these are recorded for the final
verification/fix phase. The focused current public workflow above passes.
