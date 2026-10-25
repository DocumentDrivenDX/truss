---
ddx:
  id: truss.pws03-temporal-engine-plan
  type: implementation-plan
  activity: build
  authoring:
    home: repo
  links:
    - id: truss.temporal-query-source-guard
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
    - id: truss.typed-sdk-adoption
      kind: informed_by
---

# PWS-03 temporal engine extension

## Scope

The owner selects extending PWS-03 with a versioned Truss local carrier/query
ABI in an isolated worktree. Complete genuine installed DATE/instant/local
read/filter/order/page execution and exact UMF/Truss codec composition.
Sol plans/reviews; Luna implements. Praxis stays unchanged and read-only.
No PWS-04 action expansion, publication or consumer port is authorized.

The [source/guard contract](../02-design/contracts/temporal-query-source-guard.md)
freezes exact interfaces before feature edits. Existing UMF CONTRACT-082 and
the PWS-03 raw/safe-compiler checkpoint remain historical evidence, not permission
to relabel old native support. The installed HELIX0.19.1 catalog governs planning.

## Shared Constraints

- Truss base: clean `14e16ce852381fd376da1d2187fc941683903ab2`, isolated
  `/private/tmp/truss-pws03-20261023`; never edit the primary checkout.
- Weft base: exact Truss-qualified public0.4.51 source
  `557153731e9f5d0583193a1189a07c6ed485d3d3`, isolated
  `/private/tmp/weft-pws03-truss-20261023`. Port bounded temporal changes onto
  that base; retain its person shims, ABI1.2 selective sources and existing
  capabilities. Never copy the older truss_runtime.rs wholesale.
- Preserve `/private/tmp/weft-pws01-20261022` raw-final/source checkpoints and
  previous UMF evidence unchanged. New captures belong under PWS-03
  `truss-extension/`; Truss evidence belongs in its matching HELIX build tree.
- UMF owns access admission through existing `inspectAccessViews` and its
  `ResolvedField.temporal`. Native declarations derive a separate local family;
  exact original core declarations and unknown content remain retained.
- Local acceptance selects new support/capability profiles and preparation2.1;
  DATE10_PROFILE/preparation2.0 remain exact. The native descriptor records the
  original source hash/FieldView pointer separately from the declaration.
  Existing timestamp properties never change family when retained metadata
  becomes understood; conflicting existing source/local/native meaning refuses.
- No automatic upgrade or startup migration. An explicit installation migration,
  if qualified, must preserve old property/cell meanings and source bytes;
  fresh candidate acceptance is not migration evidence.
- Supporting typed-target I/O remains Truss-owned. UMF inert catalog work is
  limited to descriptor/decoder/profile custody and refusal. Qualify a fresh
  exact UMF access dev6 source/wheel cohort; older dev5 or historical dev6
  receipts do not qualify this extension.
- Current-person READ COMMITTED, native role/owner/ACL/dependency checks and
  final authorization remain intact. The new complete buffered STABLE source
  supplies the single data snapshot; separate preflight statements are forbidden.

## Implementation Slices

| Slice | Owner and source scope | Depends on | Gate |
| --- | --- | --- | --- |
| TX-0 | Root/Luna: record all three source heads/hashes; adopt current source-owner maps and real module gates before porting. | Frozen contract | No primary/Praxis changes; exact imported delta inventory; old raw-final unchanged. |
| TX-1 | UMF owner bridge + Truss preparation/support: consume `inspectAccessViews` through the pinned issued producer; retain original Field declaration and derive native family/selector/presence separately. | TX-0 | Full source-native correspondence; wrong vocabulary/FieldView, unknown selected meaning, duplicate/foreign refs and Key refusal. No Truss semantic fork. |
| TX-2 | Truss scalar contract/schema/value owners: distinct Python local carrier, native local cell and source-derived property/cache support. Touch `_record_schema.py`, `_catalog_support.py`, native `containers.sql`, `plan.sql`, scalar/property/value validators and bounded data ingress only as needed. | TX-1 | Public accept/apply/data creation/read of actual local property; original `scalarType:timestamp` unchanged; no synthetic direct-SQL local seed. Legacy timestamp exact retention; local Keys/containers/refinements refuse. |
| TX-3 | Truss native query/runtime owners: native0.75, additive temporal ABI1.3 capture and STABLE person guarded sources; exact manifest, invocation inventory/grants and pure helper pins. | TX-2 | Actual installer observes every new function owner/ACL/dependency; invalid value outside user filter aborts before any row; data snapshot concurrency and resource caps. ABI1.2 ordinary paths remain valid for existing schemas under fresh actual runtime capture. |
| TX-4 | Weft compiler/PG backend + runtime custody: port bounded PWS-03 semantics onto public0.4.51; add frontend0.2.10/backend0.4.47/engine0.4/profile0.2 and ABI1.3 source-guard composition. | TX-1/3 | All three kinds compile/check; exact scalar/Key/cursor/source/ABI closure; final SQL uses guarded complete source, no selective prefilter or raw fallback; native ordered bags match independent tuples. |
| TX-5 | Truss query/typed target + UMF catalog/codec adapter: explicit fresh temporal source capture, original engine comparison, guarded statement dispatch and exact result/cursor decoding. | TX-3/4 | Actual public installed target all-three native reads/pages; current/final authority and transaction/deadline/cleanup preserved; generic/unqualified target refuses before dispatch. |
| TX-6 | Root/Luna artifact qualification; Sol independent semantic/evidence review. | TX-0–5 | Fresh installed Truss/Weft/UMF tuple and real Chromium parity; all required tests below pass; immutable receipt/source manifests; no phantom native/release claims. |

## Execution Contract

The owner authorizes the above implementation. Each owner may resolve routine
source layout and native implementation details within the frozen interface.
Any interface change must be reconciled across the three owners before dependent
code uses it. A missing native capability remains an explicit refusal until fixed.
No token estimate or aggregate hard metering is available; include testing and
review in continuation evidence. No tracker is selected.

### TX-2 transport decision and verification gate

Use the contract's prep2.1 noncompact route while preserving the original
acceptance-input0.2.0 bytes. Change producer arguments, native route selection,
mandatory owner-local descriptor coverage, request storage and replay together.
The exact temporal support profile plus summary2.1 selects this route; the
legacy summary2.0 compact route retains its original meaning.

Before another installed carrier qualification, prove that removing a genuine
local descriptor, stripping its declaration owner entry, or sending empty
prep2.1 declarations refuses before publication. Check retained request and
replayed request bytes keep summary2.1, owner admission and descriptors; verify
the persisted local family and original timestamp source declaration. Then run
public create/read with the separate local carrier and ordinary date/instant
siblings, followed by original-request replay and a legacy2.0 regression on the
fresh candidate. Record exact source/wheel/native manifest pins and refusal
atomicity. Passing parser or property component checks alone does not close TX-2.

### Paging Key qualification

The current temporal engine page profile retains complete required-string
selected Keys. Preserve numeric selected-Key attempts as explicit refusal
evidence; numeric-Key paging remains unsupported and unqualified. Backend-only
numeric cursor vectors do not expand public support. Native full-tuple paging
must still cover repeated string-Key prefixes, duplicate temporal sort values,
missing/null equivalence, both directions and null placements. Exact instant
numeric order across epoch9/10 and negative epochs remains a required native
gate. Record this Key subset in the final qualification claim.

## Validation Plan

1. Pure/native shared vectors: all finite year boundaries, leap dates, pre-epoch
   instants, exact offsets/DST boundaries, unknown offsets, leap seconds, nonzero
   residue,128/129 character boundary, malformed Unicode, local offsets and
   instant/local cross-kind comparisons. Preserve original offset/fraction text.
2. Real public source acceptance/apply creates a local typed property using the
   owner-selected access meaning; existing public data API creates values. Verify
   native property definition/cache/family, direct reads and source bytes.
3. Native PG18.6 ordinary authenticated person: all three kinds project/filter/
   order/page; duplicate temporal sorts, missing versus null, both directions/
   null placements, repeated first composite-Key components and full tuple
   continuation. Independent expected rows; no client-side row repair.
4. Security/snapshot: wrong roles, denied module/root, drifted owner/ACL/ABI/
   source/context; revoked authority before final handoff; invalid stored value
   excluded by user filter; a later invalid source row; scan/byte/time caps;
   concurrent writer between source validation and predicate consumption. Prove
   one statement snapshot and no early row publication; do not relax guards.
5. Legacy regression: ordinary ABI1.2 default/query/stream captures and exact
   timestamp fidelity remain intact on fresh candidate runtime bindings. Old
   runtime/program pins refuse rather than being rewritten. Source migration/
   release support is not inferred from a fresh candidate installation.
6. Exact current wheels: actual site-packages origins equal built archives and
   reviewed source; fresh Truss installer and native release/ABI observations;
   no dependency downgrade to old PWS-03 Weft0.4.48 or stale UMF dev5 receipts.
7. Bun/native/WASM in real Chromium replay all changed portable accepts/refusals
   and complete request/program/cursor metadata. Run adopted real module gates,
   focused native and package regressions/typechecks. Qualify local Darwin only;
   Linux hosted and managed qualification are not claimed without their own run.

## Risks and Rollbacks

ABI1.3 must remain additive; default ABI replacement would break current public
compiler captures. Native local adoption reaches catalog/value ingress, not just
query SQL. Buffering complete sources costs bounded memory and must preserve
the existing cap checks. Keep new capability unavailable until native tests pass.
Revert/disable only the isolated candidate profile on failure; retain all original
documents, old carrier meaning and historical evidence.

## Exit Criteria

Every TX slice and native/installed/browser/security gate passes with Sol review.
The fresh source/installation/compiler tuple is exact, all three genuine engine
kinds execute through the actual public target and code never bypasses current
person guards. PWS-03 stays incomplete while any of those gates remains open.
