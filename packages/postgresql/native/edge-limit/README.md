# Private whole-catalog limit correspondence

`verify-current-scope.sql` implements the first selected EL semantic body. It
accepts no parameters and performs no writes. The initial profile is catalog-only
native test custody: superuser session equals the definer owner, an actual assigned
transaction has one unfinished catalog-acceptance operation, and that backend
already holds exclusive schema-head exclusion. PUBLIC execution is revoked.
These administrative fixtures do not authenticate an ordinary person or qualify
an installed production profile.

The scope is every relationship ID observed in definitions, canonical edges or
markers. Every referenced identity must have one native definition. Input columns
must have the selected exact native types, nullability and character width;
definition and edge identity duplication refuses. Retired definitions are included.
The profile bounds definitions and distinct relationship scope to256, canonical
edges to16384 and markers to32768. These are logical row bounds; executor memory,
whole-operation work/resource reservations and protected owner/installation source
closure remain separate integration gates.

For each canonical edge, derive a source-side marker when `target_max=1` and a
target-side marker when `source_max=1`. A self-edge with both bounds one requires
two different sides. Independently reject duplicate required `(relationship,
side,endpoint)` keys, then compare required and actual four-column multisets with
EXCEPT ALL in both directions. A wrong relationship, side, endpoint or edge cannot
be hidden by an expected-only join. Unknown definitions, unsupported bounds and
native source drift refuse. The all-empty case is checked under the same custody.

This proves maximum-one occurrence marker correspondence only. Correct markers
can coexist with larger maximum/minimum or distinct-neighbor participation
violations; those require their selected enforcement. It does not seal an
operation, publish a report/head, replace the unconditional commit barrier or
supply commit-union routing. Future ordinary-role composition must admit the
actual original caller, registered owner/source/ACL/dependency closure and complete
current-cut/resource custody before selecting this body.

The native tests use the current retained qualified-property owner export,
explicit synthetic rows and the eleven authored correspondence vectors. Replica
mode is used only for administrative fixture/corruption setup and restored before
the measured verifier. Isolated PK/index/constraint removal probes exercise
multiset, ambiguity and drift detection; they do not qualify those altered layouts.
Every test rolls back. Native tests also cover tightening without property writes,
retirement, orphan markers, signed IDs, exact source type/width/nullability, row
bounds, ordinary direct-call denial and concurrent catalog exclusion.
