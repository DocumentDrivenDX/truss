# Qualified grant helper execution design

Companion to CONTRACT-005/008/009. Candidate native interface: `truss.grant_module_roles(document_id text, module text, writes boolean) RETURNS void`. This is an administrative installation/policy operation, not an application mutation or a role-creation API. The three-argument body is absent from review layout 0.7; the old two-argument interface is excluded from this profile.

## Inputs and captured authority

Reject SQL NULL in any argument, empty document/module, unsupported exact-text carrier and unresolved or ambiguous qualified grant. No implicit document, normalization, prefix matching or fallback is allowed. Capture original invocation authority before entering any definer body using CONTRACT-005/007's admitted acting-role/host protocol. A caller cannot supply a trusted actor, generation or installation identity as an argument. Security-definer current_user alone cannot recover original caller authority.

Resolve reader_role/writer_role to exact original native role identities under policy exclusion. The roles must be distinct and must not expose protected owners, administrative roles, BYPASSRLS/superuser authority or a disallowed membership/delegation path. Do not create roles or SET ROLE on behalf of the caller. Missing role or unsupported role inventory refuses the whole transaction.

## Ordered producer algorithm

1. Admit an exact live installation/profile and trusted administrative invocation. Acquire required catalog locks, then the policy-generation guard exclusively, following CONTRACT-009. Collect complete original grant/role/policy/dependency inventory at that admitted cut; do not discover an earlier lock after acquiring the guard.
2. Resolve exactly one `(document_id,module)` grant row and its two roles. A predeclared grant without definitions is allowed by CONTRACT-005; it does not establish later definition provenance. Validate the selected protected operation and current-role paths before any GRANT.
3. Construct the complete desired privilege delta from the selected installation's exact callable/relation/sequence identities. Reader receives schema usage and the qualified read surface only. With writes=true, writer additionally receives the admitted protected mutation surface. With writes=false, no write privileges are added. These calls do not silently revoke existing privileges; preexisting incompatible direct-DML or delegation exposure refuses profile admission rather than claiming it was repaired.
4. Apply only that reviewed delta with native identifier quoting and exact resolved identities. Never interpolate document/module as SQL or derive a routine from a display label. Grant no ownership, grant option, role membership, arbitrary sequence usage or blanket archive/recovery access. The helper cannot grant itself to application roles.
5. Recollect actual affected grants/effective authority and independently compare with the intended delta and complete protected profile. Verify current generation and owner/dependency correspondence. Update policy generation atomically if authority changed. An exact no-op remains a no-op; no generation is invented for bookkeeping alone.
6. Return only after complete native parity. Any failure rolls back grants and generation together. Supplied transaction durability remains pending until its owner commits; uncertain commit follows original executor recovery and must not submit a fresh grant attempt automatically.

## Callable family allocation

| Role | Permitted capability families | Required admission |
| --- | --- | --- |
| Reader | Catalog/direct/compiled/history/feed disclosure | Complete current owner union, retained-source correspondence and selected native read profile; no hidden evidence through helper internals |
| Writer | Canonical object/edge mutation and finalization | Current qualified owner union, original operation custody, codec/key/cardinality validation and mandatory commit guards |
| Worker | Registration/application acknowledgment and permitted seed progression | Exact registration/generation, host verifier custody and original committed proof; not granted merely because it is a module writer |
| Administrator | Qualified grants, reseed/removal, retention and installation | Separate trusted administrative profile, original request/evidence and retention/policy exclusion; not inherited from module read/write selection |

Worker and administrator capabilities are installed through separately admitted host setup. `writes=true` cannot grant them. Internal observer/guard/encoder/collector routines remain nonpublic and callable only through the selected protected paths. A shared callable's EXECUTE privilege never substitutes for its per-invocation qualified owner checks.

## Independent acceptance schedules

QG-01: same module name in two documents with different roles; each invocation affects only its qualified selection, and cross-document reads still refuse.

QG-02: NULL/empty/missing role, same reader/writer, malicious identifier spelling and unauthorized actor; refuse before any privilege or generation change.

QG-03: writes=false, then writes=true, then repeat; independently inventory each delta. Existing forbidden DML/member/definer access prevents qualification, never gets hidden by a successful helper response.

QG-04: force failure after first GRANT, during parity and around commit acknowledgment; rollback preserves originals, pending visibility stays pending and unknown commit uses original reconciliation.

QG-05: race grant/revoke, catalog owner change and active reader under the selected lock hierarchy. No stale owner/grant selection or inverted lock acquisition; later admissions observe new policy or refuse.

QG-06: attempt indirect protected-owner/delegation/wrapper access and blanket recovery-store disclosure. Reject effective escape paths, including role membership rather than only direct ACLs.

These are planned native tests. Exact callable names/signatures, selected role/security/driver/resource profile, bounded inventory collector and source bodies remain installation outputs. This design introduces no UMF interpretation or Weft lowering responsibility.
