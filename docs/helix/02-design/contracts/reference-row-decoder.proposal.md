# Account/Item row decoder procedure

This specifies the reference direct-read decision procedure for the [selected candidate homes](reference-row-home-binding.proposal.md) under CONTRACT-010. It does not supply SQL lowering or select Weft decoder registration. Original native/profile/authority qualification remains required. Consume the existing public presence/value carriers; introduce no parallel result shape.

## Complete original observation

Admit the original requested Record/Field definitions, applicable property ownership, installed home/value/codec profiles and protected current authority before collecting values. Collect the complete owner-scoped state/node/scalar observations under one qualified cut and cumulative resource account. Retain duplicate and unexpected rows. A LEFT JOIN row containing SQL NULLs cannot establish that no state exists; enumerate actual state membership and native descriptors separately.

For each expected original field, independently determine the exact complete state membership. Zero states is permissible only for Item.note and only with complete applicable authorized visibility. Required code/amount fields refuse zero states. More than one matching state refuses; no first-row or last-row choice. Foreign/misowned states, conflicting definition/profile/source bytes and unexpected payload facts refuse the complete Record result rather than omitting a field.

Use CONTRACT-010's existing selected-state batch source/manifest and TCA/RF admission procedures. Construct batches only from admitted complete original headers, retain the independently required state set, and verify disjoint full union and per-state ownership before submission. Reserve both streams plus remaining authority/context/containment capacity in the containing operation before collection. Both streams use the same original admitted state array; complete terminations and full state/node correlation precede interpretation. This procedure does not authorize a new collector wire, fresh snapshot per field or fresh resource budget. Complete header/home reconciliation remains required even when a batch returns every selected state.

### Reference complete-scope collection plan

Reuse the [typed-owner header SQL](private-owner-states-observation-v0.1.proposal.sql) and its [original manifest](bindings/private-owner-states-observation-v0.1.proposal.json). Select object statement ordinal zero for A/B/C/D and edge statement ordinal one for AB/AC, binding independently admitted exact positive owner ID and signed type/relationship discriminator. Do not query both statements for one owner, substitute a caller-selected property list, add an active-field predicate or use LIMIT. Original owner existence/type/relationship and complete applicability/visibility require their separate protected admission; the header query alone does not establish them.

For the complete M03–M06 graph assessment, collect all six original typed-owner headers, including the two edges that declare no reference properties. Unexpected edge state rows cannot disappear because the fixture expects zero. Preserve complete extra/retained facts and classify them through original home/definition reconciliation; unclassified extras refuse. Build one disjoint required present-state set from these admitted headers and original property expectations, then execute the existing two-stream batch for its nine or ten states. The selected batch ceiling of 256 is sufficient for this fixture's cardinality, but byte/work/heap admission remains independent.

This plan needs six header plus two tree stream data submissions. Original owner/key/relationship admission, context/profile/authority observations and containment require additional reserved submissions within the containing 64-command direct-read limit; eight is not the whole-operation cost. Reserve the complete actual plan before collection, and refuse if it cannot fit. A per-owner or per-field counter reset cannot make the plan admissible. No new batch query or weakened completeness rule is introduced to reduce command counts.

### Independent fixture inventory expectations

For the independently authored M03 graph, expect these row-home contents under the proposed all-field mapping. Bind actual identities from independent native observations; this table assigns none. Counts supplement full membership/content assertions and cannot prove completeness alone.

| Original owner / cut | Complete present fields and root/payload meaning |
| --- | --- |
| Account A, committed M03 | code: one string root/payload. |
| Item B, committed M03 | code: string; amount: decimal; note: zero states. |
| Item C, committed M03 | code: string; amount: decimal; note: null root with no scalar payload. |
| Item D, committed M03 | code: string; amount: decimal; note: string root with present empty-text payload. |
| Item B, original pending M05 or confirmed committed M06 | code and amount unchanged; note: one null root without scalar payload. Independent committed M05 remains the M03 observation. Confirmed M05 rollback restores the complete original M03 graph. |

The full M03 scope has nine states, nine scalar-or-null root nodes and eight scalar payloads. The pending M05 and committed M06 scopes each have ten states, ten root nodes and eight scalar payloads. These are exact proposed fixture expectations, not global row limits or native measurements. Any extra descendant, foreign state, payload on a null root or missing required payload refuses even if total counts match. Independently compare every original owner/property/source/profile association and exact token/text value. Relationship and key stores remain separately verified under their own complete original inventories.

The [row-shape expectations](../../03-test/reference-account-items-row-shape.proposal.json) retain these independently authored totals for all six original logical cuts, with the full logical oracle's exact hash. They were checked against each original present/null/scalar occurrence without changing that oracle. The assessor must bind and compare actual complete owner/property/node/payload membership first; totals are supplementary checks. No native identities, successful execution or count-only completeness claim is introduced.

## State decision table

| Complete admitted observation | Logical decision |
| --- | --- |
| Item.note has zero states and complete applicability/visibility | Emit the existing absent presence carrier. Do not fabricate a null root, default or empty text. |
| Exactly one state whose complete tree has one explicit null root and zero scalar rows | Emit present null only for Item.note. Required code/amount refuse. |
| Exactly one state whose complete tree has one scalar root and exactly one string payload | Emit present exact string for code/note after the scalar codec checks, including empty text. |
| Exactly one state whose complete tree has one scalar root and exactly one decimal payload | Emit present original decimal token only for Item.amount after lexical/domain and exact native-projection checks. |
| Any other cardinality, tree shape, dispatch or incomplete observation | Refuse the complete requested result. No fallback to props or native NULL interpretation. |

Verify the sole root's actual state/root/node correspondence, root slot, absent parent and unused root slot fields under the original native declaration and semantic profile. Enumerate the complete node set: a matching root with extra descendants does not pass this scalar fixture. Verify complete scalar membership, exact node linkage and all unused payload slots. A null root with any payload refuses; a scalar root with no payload refuses. Every original source/definition/codec component must resolve and agree with the admitted field meaning; matching digests alone cannot establish the correspondence.

The decoder stages the complete Record privately. It never publishes a successfully decoded code before discovering malformed amount/note. Exhaustion, unavailable codec or incomplete protected observation refuses the whole required result. Preserve original diagnostics privately under current disclosure authority; failure cannot leak hidden owner membership.

## Publication and lifetime

### Two-stream collector failure procedure

The node and scalar statements are separate native commands. Reserve original submission and containment capacity before the first command, and mediate both through the same admitted executor/transaction. Stage every complete original observation privately; a completed node stream is not a reconstructed value or permission to publish. Observe actual descriptor/framing/command termination independently for each stream.

| Original failure boundary | Required disposition |
| --- | --- |
| Node stream descriptor, framing, row bounds or original termination fails | Stop admission; preserve original command custody and apply the existing executor containment protocol. Do not issue the scalar stream merely to obtain a matching count. |
| Node stream completes but scalar submission cannot be admitted | Refuse the complete read before submission. Preserve already spent work and owned node buffers until actual release/containment; no fresh scalar budget. |
| Scalar stream fails or terminates ambiguously | Withhold all staged fields. Establish original native termination through the qualified executor boundary; unresolved termination retains recovery custody. Node success cannot classify scalar completion. |
| Both streams complete but membership/source/codec interpretation fails | Refuse the complete result under original integrity/domain diagnostics. Successful command completion does not make malformed values valid. |
| Both streams and reconstruction pass, but publication authority changes | Withhold staged content and follow original resource release/containment rules. Do not disclose partial fields, retry on a replacement cut or infer authority from earlier stream success. |

Owned and adopted transactions retain their existing distinct containment responsibilities. No decoder-triggered whole-host rollback, isolation change, callback replay or fresh transaction is permitted for an adopted read. A later explicit operation may collect a new cut only after the original operation is settled or contained through its existing recovery rules; it cannot be substituted as evidence that the failed original observation completed. Count retained node buffers, scalar framing/decoded copies, correspondence indexes and staged values together while simultaneously owned, including unresolved command lifetime.

Keep exact original lexical token/source bytes in the staged value. Native numeric rendering is used only for qualified mathematical agreement, not as the authored token. Revalidate authority, original binding/source epoch and execution profile through the existing same-transaction publication protocol before releasing the complete value. Adopted transactions expose pending values only through their admitted original live handle; independent committed reads cannot see them before confirmed outer commit. Driver termination alone does not settle the mutation that produced a value.

Apply the same full-owner prerequisites to compiled reads through Weft-owned obligations and result descriptors. A predicate excluding the corrupted owner cannot waive those prerequisites. Complete Item.note compiled projection remains unavailable until the exact absent/null/string registration is supported. Direct decoder success cannot certify that integration.

M03–M07, FS controls, RD-03 and LC-04 must independently exercise zero/one/duplicate states, missing/extra nodes and payloads, null versus empty string, wrong original definition/home/codec coupling, and authority change before publication. Exact collector queries/lock order, profile bytes, native bodies/security/dependencies/resource producers and actual driver/Weft qualification remain unfinished delivery outputs; this procedure fixes decision ordering and whole-result refusal behavior.
