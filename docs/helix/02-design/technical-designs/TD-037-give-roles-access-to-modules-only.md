---
ddx:
  id: TD-037
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-037
      kind: informed_by
    - id: SD-008
      kind: informed_by
    - id: CONTRACT-005
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
---

# TD-037: Database module isolation

## Technical Approach

Install the optional version-pinned policy bundle without changing canonical columns/constraints. Apply both grants and row policies: grants authorize operations, policies narrow rows. Use database-derived transaction acting role rather than definer current_user. Native direct SQL tests establish the boundary; library filtering is insufficient. Core accepts an explicit qualified policy profile and does not create roles or change host grants at startup.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/tooling/src/policy/bundle.ts` | Pin policy/grant inventory and administrative installation manifest | US-037-AC1, US-037-AC2, US-037-AC3, US-037-AC4 |
| `packages/conformance/src/policy/native.ts` | Protected relation/operation and definer matrix | US-037-AC1, US-037-AC2, US-037-AC3, US-037-AC4, US-037-AC5 |
| `tests/performance/module-policy.test.ts` | Matched 1,000-type/10-module read cost | US-037-AC6 |

## Shared Boundary and Model

CONTRACT-005 now separately proposes `truss-qualified-module-policy/0.1.0`: fixed document/module grant key and explicit three-argument administrative helper, with no default or name-inferred document. The candidate changes the fixed layout/policy inventory under ADR-004; it cannot use this design's baseline no-column-change extension route. Plan qualified owner-home resolution, complete explicit legacy grant mapping, guarded atomic activation and policy generation as one reviewed migration boundary. Reuse existing UMF-described layout generation with Truss-owned complete source/composition/native correspondence; do not create an alternate policy/table generator or wait for an additional upstream exporter API. STP-037's equal-name cross-document cases supplement the original ordinary-role matrix. Exact DDL/native predicates/privilege producer and review remain open.

CONTRACT-005 owns module_access, grants, acting_role and policy predicates. Reuse the native UMF policy bundle from bootstrap work; no alternate hand-maintained policy generator. Inventory every protected table, function, sequence, owner, FORCE setting, privilege and search path. Include keys, journal, tombstones and source facts, not only object. The historical baseline’s relationship-only edge-derived journal/tombstone policy is insufficient for the selected complete profile. Consume CONTRACT-005’s authored declaring-owner plus both original endpoint-owner union under current grants, including before/after contexts; missing retained provenance refuses disclosure. Exact native protected loaders/predicates and security-owner protocol composition remain implementation/adoption gates.

A no-module role must have enough SELECT privilege to exercise empty RLS results; mere permission denial cannot establish AC4. Reader refusal must reach the declared grant/policy boundary. Test cross-module UPDATE including changing type/endpoints, INSERT and DELETE. CONTRACT-005 now distinguishes hidden zero-row UPDATE/DELETE from WITH CHECK/grant refusal; library maps inaccessible/no-match to not_found without elevated existence probing.

## Security and Integration

Data tables FORCE RLS but superuser/BYPASSRLS remain outside guarantees. Catalog tables' non-forced owner access is administrative, not ordinary caller authority. Qualify non-superuser definer owner, transaction-local acting role, fixed search path and hostile role/setting attempts. Deletion-surviving provenance and cross-module historical edge exposure need explicit retained ownership facts or a restricted policy; do not weaken requirements by assuming live rows always exist. Read consistency and Weft host authorization obligations use actual role/profile, not compiler qualification alone.

## Testing and Performance

STP-037 allocates six criteria. Native fixtures contain sales/billing data and distinct modules/roles for relationship endpoints, with independently expected visibility. Compare exact set contents and absence of hidden ids/keys/source facts. Cost target is incremental policy cost with role already set, not role-assumption/pool/network overhead. Predefine timing statistic, randomized paired samples and environment; historical predicate variants do not qualify the complete current bundle.

## Sequence, Rollback and Gates

Consume the authored historical ownership/disclosure union and independently owned security protocol, select exact native definer/loader/predicate realization, and write red native matrix; verify generated bundle and run profile-specific corpus/performance. Removing policy broadens access and is not a safe rollback. Withdraw support and fail closed for an incompatible profile; host-admin policy migration must preserve authorization. No claim of eliminating FK/unique existence side channels: host diagnostic policy remains explicit.
