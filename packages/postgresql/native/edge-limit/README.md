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

`event-frame.sql` and `observe.sql` add private event correspondence components.
Install the original row-touch custody decoders and capacity hooks first. The
three ALWAYS AFTER ROW triggers cover every INSERT, UPDATE and DELETE on edge,
edge_limit and rel_def. The relationship trigger explicitly replaces the earlier
catalog generation trigger; its route retains catalog-acceptance and exclusive
head requirements. The two parameter-free routines bind exact relation/trigger
registrations, retain invoker checks and revoke PUBLIC execution.

The versioned `truss-native-edge-event-frames/0.1` projection occupies existing
immutable effect_obligation_bytes. Its frames have unique canonical decimal
`effectGeneration`, a closed event and an exact scope artifact. Sparse generations
address the global operation frontier; they do not establish complete schedule
consumption. Each event retains complete native JSONB OLD/NEW row images. Capture
and comparison require UTC, ISO YMD and hex bytea rendering. Integers remain exact
JSONB numbers; Python fixtures never pass them through floating point.

Each `truss-native-edge-event-scope/0.1` scope has old/new sides, absent exactly
when the corresponding image is absent. A present side retains its complete
relationship definition, parent edge (null for definition events) and exact
originalGuard artifact. Marker attribution checks relationship, edge identity,
endpoint side and the relevant maximum-one bound, including deleted parent facts
without querying the removed row. These retained artifacts do not prove acquired
native guards or protected family/allocator authority.

Actual events compare full OLD/NEW images before advancing generation. Original
registry/active actor, retained reservation and native capacity hooks are required.
The full expected operation row is checked in UPDATE RETURNING and independent
readback; earlier readiness/seal/application evidence is cleared. The unconditional
commit barrier remains installed. Administrative replica-mode fixtures exercise
these ALWAYS observers, but do not establish ordinary-person admission or an
installed EL09 body. Whole-catalog verification, genuine guard/allocation producers,
complete schedule consumption, source/privilege closure and finalization remain
integration requirements. No public Python write capability is enabled here.
