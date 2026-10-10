# Reference protected access composition

Status: authored responsibility and route plan; native roles, routine bodies, grants and support remain unqualified. This composes CONTRACT-001 and CONTRACT-005 with the original 0.12 store and sixteen-selector worklists. It does not replace their immutable source pins or fill native evidence fields with design labels.

## Responsibility boundaries

The table assigns responsibility labels, not SQL role names. Installation binds each label to exact native identities and effective privileges. The ordinary application actor has no canonical DML in this protected-procedure candidate. It receives only the exact admitted public entry signatures and independently qualified read surfaces. Baseline direct DML is a separate profile under CONTRACT-005; this candidate cannot remove or claim that profile's requirements.

The installation administrator owns protected objects and performs installation/conversion. Routine responsibilities receive only the relation/column/sequence rights required by their complete bodies; assigning a family never grants all its stores or all commands. They are not application-inheritable or SET-accessible roles. A producer requiring another responsibility calls an exact private entry under original custody rather than acquiring that role in its caller session. Native role coalescing must preserve every prohibition and undergo the complete transitive-path review; it is not an automatic optimization.

The integrity observer remains the separate non-login read-only responsibility selected in CONTRACT-005. It observes complete admitted hidden scope privately and cannot mutate, allocate IDs, publish, administer policies or authorize outer disclosure. Read surfaces must use the original actor/current authority and cannot borrow observer visibility. Administrative access is explicitly separate from ordinary enforcement claims.

## Complete declared-store route plan

Every original declared store occurs exactly once below. Read routes describe allowed logical surfaces, not raw SELECT grants. Complete column/row/payload disclosure must be derived separately; private auxiliary stores cannot be exposed by an automatically generated view. Writer routes require original operation or administrative custody, resource admission, authority and final native integrity checks.

| Original relation | Writer responsibility | Ordinary/public read route | Protected write route |
| --- | --- | --- | --- |
| setting | Installation administrator | Qualified configuration inspection | Installation/configuration admission |
| module_access | Policy administrator | Qualified grant administration and permitted authority inspection | Qualified policy transition |
| schema_rev | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| schema_head | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| schema_doc | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| schema_change | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| type_def | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| prop_def | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| key_def | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| rel_def | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| rel_endpoint | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| object | Graph mutation producer | Qualified graph read; edge_limit remains private integrity state | Atomic graph mutation and private integrity maintenance |
| edge | Graph mutation producer | Qualified graph read; edge_limit remains private integrity state | Atomic graph mutation and private integrity maintenance |
| edge_limit | Graph mutation producer | Qualified graph read; edge_limit remains private integrity state | Atomic graph mutation and private integrity maintenance |
| key_tombstone | Key mutation producer | Exact full-context key lookup only; guards/reservations remain private | Original key allocation/reservation/lifecycle procedure |
| record_source | Graph mutation producer | Qualified graph read; edge_limit remains private integrity state | Atomic graph mutation and private integrity maintenance |
| feed_consumer | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| journal | Journal publisher | Qualified complete history reconstruction/feed read | Journal publication; separately admitted retention |
| row_home_operation | Operation coordinator | No ordinary raw disclosure; public result/settlement only | Original operation/phase/touch/capacity procedure |
| row_home_journal_stage | Operation coordinator | No ordinary raw disclosure; public result/settlement only | Original operation/phase/touch/capacity procedure |
| row_home_state | Graph mutation producer | Qualified complete value read through admitted definition/decoder | Original complete row-home mutation |
| row_home_node | Graph mutation producer | Qualified complete value read through admitted definition/decoder | Original complete row-home mutation |
| row_home_scalar | Graph mutation producer | Qualified complete value read through admitted definition/decoder | Original complete row-home mutation |
| relationship_lineage | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| row_home_touch | Operation coordinator | No ordinary raw disclosure; public result/settlement only | Original operation/phase/touch/capacity procedure |
| row_home_capacity | Operation coordinator | No ordinary raw disclosure; public result/settlement only | Original operation/phase/touch/capacity procedure |
| key_bucket_guard | Key mutation producer | Exact full-context key lookup only; guards/reservations remain private | Original key allocation/reservation/lifecycle procedure |
| object_key_bucket | Key mutation producer | Exact full-context key lookup only; guards/reservations remain private | Original key allocation/reservation/lifecycle procedure |
| object_key_reservation_bucket | Key mutation producer | Exact full-context key lookup only; guards/reservations remain private | Original key allocation/reservation/lifecycle procedure |
| catalog_acceptance_report | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| installation_marker | Installation administrator | Admitted readiness/report inspection; archive internals private | Atomic installation/conversion admission |
| installation_archive | Installation administrator | Admitted readiness/report inspection; archive internals private | Atomic installation/conversion admission |
| feed_tx | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| feed_member | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| feed_prerequisite | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| feed_configuration_prerequisite | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| complete_feed_consumer | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| complete_feed_administration_receipt | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| complete_feed_seed_attempt | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| complete_feed_seed_artifact | Feed coordinator | Admitted consumer feed/status; administration and seed state remain private | Registered feed/consumer/seed/administrative procedure |
| key_lifecycle_history | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| installation_admission | Installation administrator | Admitted readiness/report inspection; archive internals private | Atomic installation/conversion admission |
| key_migration_receipt | Catalog producer | Accepted definition/report/lifecycle read with complete current owner authority | Catalog acceptance/evolution/migration |
| request_receipt_route_guard | Receipt coordinator | Original request lookup/replay with fresh owner-union authority; guards/protections private | Original arbitration/publication/protection/expiry procedure |
| request_receipt | Receipt coordinator | Original request lookup/replay with fresh owner-union authority; guards/protections private | Original arbitration/publication/protection/expiry procedure |
| request_receipt_protection | Receipt coordinator | Original request lookup/replay with fresh owner-union authority; guards/protections private | Original arbitration/publication/protection/expiry procedure |

For graph reads, object/edge/record_source each retain original qualified owner intersections; row_home_state/node/scalar require complete owned state/root/payload and the admitted four-Field definition bundle. The graph family label does not admit edge_limit disclosure. Catalog reports, original source and retired/deleted history require their complete retained owner union, not merely visibility of the current schema head. Receipt guards and protections and feed prerequisite/configuration/seed state are internal even when an admitted status API exists.

## Original private entry routing

| Existing selector cohort | Permitted invocation boundary | Prohibited shortcut |
| --- | --- | --- |
| row_touch_observe; edge_limit_observe; edge_limit_catalog_observe | Installed original triggers under admitted writer/catalog operation, with original actor and generation | Ordinary direct EXECUTE, synthetic trigger invocation or actor supplied as a trusted argument |
| row_touch_commit_check; feed_current_union_check | Installed original deferred/current-union check paths under the same transaction's surviving operation cohort | Treating an earlier seal or filtered unfinished-operation set as commit proof |
| feed_union_validate_current_scope; edge_limit_verify_current_scope | Exact internal finalization/commit caller with complete original scope and exclusion | Arbitrary SQL/table/scope selection or exposed private count result |
| journal_capture_start; journal_observe_transition; journal_prepare_final; journal_reserve_positions; journal_append_group | Original journal coordinator following H1–H7 and exact phase/capture custody | Caller-created phase bytes, precommit publication, or reservation as commit evidence |
| row_touch_reserve; row_touch_seal | Original canonical admission/finalization caller, exact operation/generation and whole integrity scope | Capacity reset, sealing only visible rows, caller-chosen owner identity as authority |
| row_touch_cleanup; row_journal_stage_cleanup | Separately admitted retention administrator, complete original selected cohort and native termination | Application cleanup rights, partial returned cohort as completion or cleanup as rollback proof |

These routes cover sixteen existing selectors, not the entire future callable closure. Public mutation/read/import/catalog/report/receipt/feed/retention/recovery entry bodies must be enumerated with their complete private dependencies before installer readiness. No public entry is licensed merely because this document names its logical responsibility.

## Composition and failure order

1. Retain original native actor before elevated work; admit complete requested input, authority and resource context. Resolve the exact public entry and original transaction/operation identity.
2. Bind every reached store/column/sequence and helper to the intended responsibility and exact native definition. Check effective ACL, ownership, PUBLIC/default grants, inherited/SET/grant-option paths, policy applicability, resolution namespaces and transitive wrappers.
3. Execute only the admitted producer route. Internal observations preserve complete hidden scope but return facts only to original protected custody. Public errors, tracing and callbacks cannot disclose private IDs/counts/bytes.
4. Before publication recheck current actor/authority, definition/profile generation, complete original operation effects and native final integrity. Apply the existing outer-commit and original recovery rules; this access plan does not settle a transaction.
5. Installation compares its complete intended inventory against actual installed bodies, dependencies, roles, grants, policies, triggers and administrative/restore/replication paths before readiness. Missing, additional or changed access invalidates the affected capability. Unknown installation settlement retains original recovery custody.

This selects the responsibility and routing composition while preserving unresolved physical names, exact body-specific rights and native evidence. It does not grant unrestricted administrator escape paths ordinary-writer qualification, infer absence from inaccessible rows, or assert database isolation/resource behavior from source text.


## Public and administrative caller closure

The canonical method-to-route design is the [public native route map](reference-public-native-route-map.proposal.md), including direct/compiled reads, transaction-owned facade routes, inert construction/readiness/disposal and bootstrap pure/owned/read-only boundaries. Its [administrative method inventory](reference-administrative-method-routes.proposal.json) retains 35 exact signatures across fourteen selected interfaces. Preserve that inventory rather than maintaining a second method matrix here. Those TypeScript selectors are not proposed SQL grants or actual native identities.

This access composition supplies store/private-helper responsibility and the independent acceptance controls below. The installer expands each canonical route into its actual callable/statement/dependency/store/column/sequence/actor/resource/publication closure. Ordinary callers receive only admitted public methods, never implicit rights to private helpers or administrative role paths. Keep feed0.1/0.2 selections distinct; construction/registration confers no native readiness or authority.

Initial compiled logical reads advertise no standalone SQL view. Any separately selected direct-DML or SQL-client read profile retains CONTRACT-005 obligations and its explicit original exposure inventory; this candidate cannot silently replace it.

### Native closure acceptance

PAC-01: invoke every declared public capability through its original admitted caller and independently inspect reached objects/roles; refuse any unregistered transitive callable or widened right before readiness. A positive public result alone is insufficient.

PAC-02: attempt direct invocation of private trigger/finalizer/journal/cleanup helpers and direct canonical DML/sequence manipulation as ordinary actor, including inherited/SET-capable roles and function-owner paths. Refuse all prohibited routes without effects; independently inspect actual effective rights.

PAC-03: inject an additional callable/operator/cast or advertised read surface into the installation while retaining the old inventory. Native correspondence/readiness must refuse rather than ignore the new entry.

PAC-04: use a permitted facade to reach hidden staging, guard, receipt protection, observer count or another owner's source/report through errors/results. Require full original disclosure enforcement, including after authority changes before publication.

PAC-05: exercise owned versus adopted transaction failure, savepoint rollback and outer commit for mutation/import/catalog/feed ACK; inspect complete surviving journal/feed cohort and earlier caller sentinel work. A shared private helper must not change settlement ownership.

These schedules remain not_run. Exact body-specific rights and transitive native closure are implementation outputs. The canonical route map specifies caller/dependency design; complete native method/body inventory and security qualification remain required.


## Administrative closure acceptance

PAC-06 extends the existing planned closure controls: independently invoke every selected administrative method in the canonical route/inventory as its correct original administrator, then as an ordinary application actor, a stale generation and a foreign issuer. Permit only its declared authority/effect boundary. Include rolled-back pending job/registration tokens, unknown bootstrap/migration/downstream acknowledgment and cleanup faults; inspect source and downstream effects independently. All schedules remain not_run. Native method-to-body identity, grants/dependencies and production evidence remain implementation outputs.

## Native callable closure construction and exit rule

Use the canonical public route map and administrative inventory as the root
set. Classify each root as pure/inert, ordinary disclosure, protected
transaction participant, owned installation/administration, or recovery-only
observation. Pure/inert roots have no native call edge; a constructor cannot
acquire authority through a hidden readiness query. Record actual body
selectors and full argument/result signatures only when those bodies exist.
A logical capability name is not a callable SQL identity.

For each native root, expand a work queue of actual reached statements and
callables until no new dependency remains. Each edge retains the original
source/body identity, invoker/elevated actor transition, exact command and
store/column/sequence access, native definition-resolution dependency, trigger
firing/timing, disclosure/error/callback destination, resource account and
transaction settlement owner. Include indirect trigger/default/generated
expression/policy/operator/cast/wrapper calls, deferred commit paths and
restore/replication firing differences. Catalog dependency introspection is
one input, not proof that dynamic statements or trusted wrapper behavior
were enumerated. Dynamic identifier/statement selection must be confined to
a finite admitted original inventory; unresolved selection marks the affected
capability unavailable rather than assuming the static dependency graph is
complete. Recursion cycles require explicit admitted termination/work bounds.

Compare the intended closure with independently collected installed identities
and effective rights in both directions. Missing dependencies refuse; extra
reachable routes or grants refuse even when all intended functions exist.
Exercise each ordinary invocation route under the actual actor/inheritance/SET
ROLE context, including direct helper calls, trigger bypass and wrapper
substitution. Check original source/profile and installation generation again
before publication. A changed body or grant invalidates the affected closure
without transferring settlement or disclosure ownership to its helper.

The design exit is this authored construction algorithm plus each canonical
root's selected responsibility and caller boundary. The implementation exit
is the complete actual root/edge inventory, independent native reconciliation
and PAC/STP controls; sixteen named private routines or a source AST pass
cannot satisfy it. New root capability semantics require design reconciliation;
new body/OID/dependency identities implementing an existing route are
implementation outputs, not an unmade product decision.


## Security-owner graph-source candidate integration boundary

The current owner work includes private `security-graph-source.ts`, which constructs
object/association-edge projections and a separate validity query from fixed native
relations and validated required string/boolean metadata. It is uncommitted review
input, not a selected compiler ABI, installed view, accepted definition or permit.
Consume the original owner-produced source and version/profile evidence before
adopting it; do not build a competing policy graph or ACL resolver.

1. Bind construction inputs to original accepted type/relationship/property and
   namespace/key/context custody. Retain exact native installation/layout and
   current security-owner registration. The candidate's local WeakSet recognition
   only proves local construction; neither copied SQL nor the issued object proves
   source completeness, installation or authority.
2. Reserve original driver ingress/result, validity, complete projection and final
   freshness/custody capacity in the containing operation. Execute validity and
   projection under the same independently qualified source/membership cut. Separate
   READ COMMITTED statement snapshots cannot be assumed equivalent; use the owner's
   selected original-cut/guard protocol rather than introducing another lock order.
3. Admit validity's actual ordered raw metadata/text result through the original
   physical lease and owner protocol. NULL, malformed/false, lost response, missing
   catalog metadata or an invalid selected row refuse projection/publication.
   A true result is not proof of complete visible roots or current authority: apply
   the existing source-completeness and disclosure procedures independently.
4. Collect every required object/edge and typed endpoint under that same admitted
   context, preserving original identity/key buckets and graph-source membership.
   Recheck the original source/security context before evaluation/publication.
   Missing buckets, omitted roots, duplicate/mismatched rows or a changed context
   refuse the complete result; inner joins and empty projections cannot prove absence.
   Consume the owner's buffered-publication custody and backend-loss quarantine;
   no host callback or fresh replacement connection settles original obligations.

This candidate's required single string/boolean JSON-home subset does not qualify
optional/null values, decimals, row-home storage, arbitrary UMF types or general
consumer logical SQL. In particular it does not replace Weft's Item.note presence
mapping or authorize the Python adapter to coerce projected NULL into absence.
Current owner work also tightens array descriptor custody and qualifies native
JSON operators; original rerun receipts are required before adoption. Truss retains
its independent complete callable/privilege/native-source qualification gates.

Independent integration schedules alter one required property/catalog fact,
omit a root or key bucket, return malformed validity metadata, substitute a copied
candidate, change graph/catalog/security context between validity and projection,
and lose the original backend after collection. Each must refuse protected
publication with original quarantine/recovery intact. A full positive source uses
independently expected complete object/association-edge/typed endpoint membership;
row counts alone cannot qualify it. These are authored integration exits, not
execution of the owner's native or browser tests.
