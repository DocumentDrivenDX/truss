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
