# Weft integration iteration feedback

Observed from merged Weft 2744531735c2a771fbe7ed24a7f67e3afc851b25 through the actual Truss query API. This is a local review packet, not a delivered owner message or a request to alter compiler semantics without review.

## Native host parameter admission

The duplicate SUM join compiles and executes with the original SQL and exact shared parameter vector. Integrity SQL uses sparse positions from that vector. Bun's inferred extended-query path failed with PostgreSQL42P18 (could not determine parameter $2). This is a host parameter-type realization gap, not proof of invalid logical SQL or a compiler semantic failure.

The component harness now sends each original SQL statement through native Parse with an explicit text OID25 for every original parameter position, followed by Bind with exact UTF-8 bytes. This replaces the earlier SQL-level PREPARE/EXECUTE workaround. Sparse integrity vectors execute without SQL changes, added casts or slot renumbering. Original request/response frames, result descriptors, command tags/counts and ReadyForQuery state are retained. The local trust-auth-only probe refuses malformed frames, count mismatch and unsupported authentication; stored values remain text/null. TLS/password authentication, cancellation/pooling/recovery, complete preallocation accounting and production profile adoption remain unqualified.

## Actual semantics exercised

The independent fixture uses logical customer key 9007199254740993 while physical object ID is 100. Two separate Orders values of 12.50 must both contribute; the actual join returns Ada plus exact decimal token 25.00. COUNT returns exact integer token 2. Empty Orders returns SQL null for global SUM under the aggregate descriptor; this is distinct from the excluded logical native-null field capability. Complete emitted integrity SQL runs first. A stored invalid-decimal field refuses before any data SQL and publishes no result.

Retained [receipt](../../04-build/evidence/weft-integration-native-component.json). Six scenarios have eleven context checks (two per successful scenario, one before refused execution), six successful integrity checks and a forged identity-digest refusal. Additional cases page from logical key 9007199254740993 to 9007199254740994 and bind injection text as an ordinary value returning no rows. Seven independent protocol tests cover exact numeric text/Unicode Bind, native count mismatch, authentication refusal and malformed completion order/shape (Bind before Parse, nonempty or duplicate Parse completion, command before description). Protocol faults close the original connection before reuse. Fixtures use a private temp object LIKE the owner 0.13 repair definition; they do not provide accepted catalog identity, protected graph writes or feed support.

## Explicit compiler subset refusal

`SELECT SUM(o.total) AS total FROM Orders o WHERE o.id < :cursor` with cursor integer token0 refuses WFT-UNSUPPORTED at the comparison in weft-sql0.2. Truss retains that result and does not rewrite the query, choose another dialect or fall back to physical SQL. The independent empty-dataset SUM test does not establish support for the refused filter. Future language support belongs in Weft with its own version/subset/evidence; this is a concrete use-derived case for that review.


## Revised consumer relationship-predicate feedback — 2026-10-09

[Fresh frontend receipt](../../04-build/evidence/design-audit/consumer-revised-frontend.json)
uses frozen Weftf05f2df and both revised owner-authored models, with no inserted
names or SQL rewriting. All original archive files compare byte-exactly before
execution; Cargo runs locked/offline with Rust1.90.0. Ninety query observations
resolve80 and refuse10: these are the following five original steps on each model.
All refusals are WFT-NAME-MISSING in resolve, reporting a property absent from
Record members. This is test-frontend evidence, not SQL lowering/native execution
or a public parsed-input ABI qualification.

| Original consumer step | Required logical predicate |
| --- | --- |
| `read.relationship-filter-both-directions:0` | `s.addresses = 'uc-1'` |
| `read.relationship-filter-both-directions:1` | `u.addressedBy = 'sol-1'` |
| `read.relationship-filter-both-directions:2` | `u.addressedBy = 'nobody'` |
| `read.repeated-relationship-predicates-mean-both:2` | `s.addresses = 'uc-1' AND s.addresses = 'uc-2'` |
| `read.repeated-relationship-predicates-mean-both:3` | `s.addresses = 'uc-1' AND s.addresses = 'nope'` |

The consumer expects directed relationship-key membership, including separate
members satisfying both conjuncts and empty output for the unmatched key. These
are not scalar Field equalities over a stored physical object ID. Adding core
Record/Field names closes the earlier naming-input mismatch but does not make
relationship endpoints scalar members. Full original SQL and expectations remain
in the frozen corpus; preserve its relationship/key selectors and exact parameter
meaning, multiplicity, authorization and disclosure semantics.

Weft owns selecting/resolving/lowering this logical capability and its parsed-input
boundary. Truss supplies accepted original model/binding and actual native mapping,
then qualifies original parameters/obligations/ordered output under the installed
security profile. Do not patch queries into joins in Truss, pretend incident-edge
reads satisfy arbitrary predicates, silently add fake scalar Fields or declare
R8 complete from the other80 frontend outcomes. A future owner composition needs
these positive/unmatched/repeated-predicate cases and backend/native bounds,
source validation and exact result evidence. This local packet is not a cross-chat
message or adoption of an unfinished Weft API.
