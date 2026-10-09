# Interactive read execution schedule

Independent planned native cases for [consumer read integration](../02-design/contracts/consumer-read-integration.proposal.md), R8 and SD-005/STP-009/020/021/022/039. None is an executed native receipt. Supply the original consumer UMF model, exact native homes and current-person policies; don't replace it with a sales fixture to avoid unsupported domains.

| Case | Original fixture/action | Required result and native observation |
| --- | --- | --- |
| IR-01 typed ID/key parity | Two types with distinct business identities and overlapping local key numbers; ID and complete-key lookup | Same exact logical record only in the correct type/namespace; signed catalog IDs and large object IDs preserved; native lookup/index/domain identity independently checked |
| IR-02 equality/collision | Full-key equality, partial composite filter, digest-collision fixture and indexed property equality | Full-byte comparison prevents wrong match; partial key uses declared compiled page path; missing/incompatible index refuses interactive profile; no unauthorized key-existence disclosure |
| IR-03 composite keyset | Key (a,b) with (1,1),(1,2),(2,1); page after (1,2), plus equal-key/Unicode/decimal boundaries | Next includes (2,1), proving tuple seek rather than independent > predicates; exact ordering/collation and complete unique key native evidence; no offset or rounded cursor |
| IR-04 direct versus logical order | Object ID order intentionally differs from business-key order | Direct page uses ID continuation; logical Weft page follows declared complete key. A cursor from one domain cannot resume the other |
| IR-05 snapshot/catalog change | Page under held snapshot; concurrently mutate order key and accept a new catalog; resume held and live contexts | Held pages match original snapshot; incompatible live context refuses or follows explicitly selected live semantics. No snapshot promise from ORDER BY alone |
| IR-06 complete projection | Absent/null/empty, large integer, decimal, structured field and retained unknown data; one unsupported required member | Full exact descriptors/presence/values retained; selected unsupported member refuses whole query. No scalar or JSON numeric float conversion; complete field publication obeys policy |
| IR-07 relationship existential | Multiple edges to same target plus empty relation and inverse direction | HAS_RELATED never duplicates source row; RELATED_KEYS preserves declared multiplicity/order; cap/lookahead truncation exact; endpoints/type/direction/key checked |
| IR-08 relationship publication | Over-cap list/columns, unauthorized target and malformed or oversized lookahead | No prefix/result/cursor leaks before full validation; no hidden-target existence or count via predicate/related projection; selected security semantics govern |
| IR-09 grouped count | Grouped empty input, global empty input, join duplicates, >2^53 exact expected count oracle and missing-value grouping domain | Exact bag semantics, integer text, complete group ordering and no partial count. Native count range/absence/null equality profile explicitly qualified; independent large-count oracle supplements actual smaller native fixture |
| IR-10 access-plan scale | Representative type count, object count, equality selectivity, high fan-out, groups and skew with actual index/statistics versions | Retain original EXPLAIN ANALYZE/buffer/candidate/sort/aggregate observations and baseline; result LIMIT alone cannot certify bounded work or latency |
| IR-11 compiler/driver admission | Unknown obligation, stale mapping, reordered parameters, caller SQL artifact, wrong role/transaction and read-only write attempt | Refuse before artifact submission/publication; native traces show original affinity and denied effects; no hidden reparsing or fallback compiler |
| IR-12 external consumer/parsing | Clean Python/TypeScript query consumers; source SQL and eventual owner parsed-input adapter over same original query/model/parameters | Exact ordered parameters/descriptors/results/diagnostics/obligations agree; current SQL-text route documented as interim until owner parsed ABI exists; no qualification from an invented AST entry point |

Record exact compiler/frontend/backend, model/layout/codec, index/statistics, database/driver, policy/current-principal, snapshot and controlled-work profiles. Native execution and full public-result publication are required for Truss support. Unsupported required case or absent original input is unavailable, not skipped into success. Performance evidence applies to its measured cardinality/role/profile only. Python/TypeScript interoperability does not replace independent expected results.

## IR-12 parsed-input admission schedule

These are planned subcases of IR-12, not new executed checks. The owner must
supply the actual parsed-input grammar/API and approved parser profile before
fixture serialization; do not invent plausible tree bytes to fill that gap.

| Subcase | Original action | Independent expectation |
| --- | --- | --- |
| PI-01 route parity | Compile one supported query as original SQL and admitted parser data against identical model/binding/parameters | Same complete logical results, descriptors and parameter/obligation meaning under the owner's declared compatibility rule; independently expected result, not SQL-text equality alone |
| PI-02 name resolution | Ambiguous/unresolved qualified name, duplicate alias/output label and wrong dependency identity in host input | Owner semantic refusal; a host's claimed identity/type cannot bypass resolution |
| PI-03 exact parameters | Large integer/decimal/Unicode literals, repeated named parameter and missing/surplus/wrong-family binding | Exact text/domain preserved and ordered native slots correct; rounded numeric input or inconsistent domain refuses |
| PI-04 forged lowering | Supply target SQL fragment, caller-created resolved plan, removed integrity obligation or executable/unknown node | Refuse before native submission; no artifact from a trusted compiler registration |
| PI-05 original correspondence | Change tree/model/binding after preparation; supply conflicting original SQL when required by the owner profile | Original-input/profile correspondence refusal; no borrowed prior artifact or guessed equivalence |
| PI-06 grammar/resources | Unknown/newer parser profile, unsupported construct, duplicate-member input, invalid Unicode, excessive byte/node/depth/work boundary | Whole-input refusal with retained original failure category; no partial plan/public result or silent SQL-text fallback |
| PI-07 native publication | Execute admitted parsed-input artifact through Python and TypeScript on original read-only transactions; race authority/mapping change | Same complete native/logical result on authorized cuts; stale/denied context publishes nothing; compiler success alone is insufficient |
| PI-08 compatibility | Existing SQL-text and old backend profiles encounter newly supported parsed/null semantics | Old supported behavior remains unchanged; excluded meaning still refuses unless its own new registration is selected |

Retain original parser/input/compiler/model/binding/profile artifacts, actual
compile outcomes and native/public observations separately. Source interface
inspection closes none of these execution cases.

## IR-11 backend-loss publication control

Hold an authorized read result in the live host before its declared final
release, then terminate only that fixture's reader backend and concurrently
request the relevant revocation. The independent observer must distinguish
native termination from host-buffer drain. The selected security protocol must
prevent acknowledgment until admitted final release/cleanup, or return its
explicit unresolved/unavailable outcome. Detecting the lost connection later
cannot turn an already acknowledged revocation into a successful drain case.

Retain the original buffer/lease/authority identities and ordered termination,
revocation and final-release observations. Do not publish unauthorized data to
exercise the control. Repeat through applicable scalar/entity, report/receipt,
feed and reached publishers under their own profiles; a SQL-reader lock test
cannot qualify every host publication path. This is planned integration
qualification against the security owner's observed counterexample, not a rerun
or acceptance of its unsafe mechanism.


## Publication sibling and stale-retirement controls

Plan two concurrently enrolled publications for one admitted actor with separate original identities/generations and independently retained buffers. Terminate the original native backends as specified by the qualified assessor, then close only publication A: B’s registration, recovery/capacity and buffer-drain obligation remain live. A revocation acknowledgment cannot treat actor-wide deletion as B’s drain. No unauthorized payload is delivered by this negative control.

Separately retain an old repeatable-read snapshot that observed an enrolled pending publication; complete original buffer discard and terminal retirement through the selected security-owned protocol. Attempt new admission using that old snapshot/identity. Refuse before buffer acquisition or disclosure unless the owner’s exact freshness/current-generation evidence independently authorizes a new original enrollment. Rollback/lost cleanup reply cannot resurrect the old identity. Native PID, UUID equality or a snapshot row alone is insufficient. Repeat across direct and compiled host publication integration; reports/replay/feed/reached require their own applicable native schedules. These controls are planned, consume owner evidence and do not qualify the complete security profile.
