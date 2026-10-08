# Weft integration iteration feedback

Observed from merged Weft 2744531735c2a771fbe7ed24a7f67e3afc851b25 through the actual Truss query API. This is a local review packet, not a delivered owner message or a request to alter compiler semantics without review.

## Native host parameter admission

The duplicate SUM join compiles and executes with the original SQL and exact shared parameter vector. Integrity SQL uses sparse positions from that vector. Bun's inferred extended-query path failed with PostgreSQL42P18 (could not determine parameter $2). This is a host parameter-type realization gap, not proof of invalid logical SQL or a compiler semantic failure.

The component harness instead explicitly PREPAREs each original check/data SQL with text parameter types, then executes the exact scalar text values under observed standard_conforming_strings=on/UTF8. It does not patch compiler SQL or compact/renumber its parameter vector. The harness escapes text values for its native EXECUTE grammar and refuses NUL. This is not qualification of extended-protocol Bind, original transport/resource/cancellation or a production host. The real driver integration must retain complete vector/position/type correspondence and prove its original native parameter type/Bind behavior; no wrapper may add inferred placeholder casts to the compiler SQL.

## Actual semantics exercised

The independent fixture uses logical customer key 9007199254740993 while physical object ID is 100. Two separate Orders values of 12.50 must both contribute; the actual join returns Ada plus exact decimal token 25.00. COUNT returns exact integer token 2. Empty Orders returns SQL null for global SUM under the aggregate descriptor; this is distinct from the excluded logical native-null field capability. Complete emitted integrity SQL runs first. A stored invalid-decimal field refuses before any data SQL and publishes no result.

Retained [receipt](../../04-build/evidence/weft-integration-native-component.json). Four scenarios have seven context checks (two per successful scenario, one before refused execution), four successful integrity checks and a forged identity-digest refusal. Fixtures use a private temp object LIKE the owner 0.13 repair definition; they do not provide accepted catalog identity, protected graph writes or feed support.

## Explicit compiler subset refusal

`SELECT SUM(o.total) AS total FROM Orders o WHERE o.id < :cursor` with cursor integer token0 refuses WFT-UNSUPPORTED at the comparison in weft-sql0.2. Truss retains that result and does not rewrite the query, choose another dialect or fall back to physical SQL. The independent empty-dataset SUM test does not establish support for the refused filter. Future language support belongs in Weft with its own version/subset/evidence; this is a concrete use-derived case for that review.
