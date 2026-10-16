---
ddx:
  id: truss.typed-sdk-adoption
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
---

# Typed SDK original engine read adoption

**Version:** `weft.engine-read/0.1` and `umf.engine-catalog/0.1`.
**Status:** local implementation candidate; RC module ACL scope.

## Purpose and scope

Expose source-bound generated SDK reads through the original Truss public
catalog/transaction/query path. `truss.access.TrussTarget` takes an explicit
host-owned operation context; it opens no connection, interprets no storage,
lowers no native SQL and invents no table/Key/actor/receipt identity.

This initial path qualifies ordinary RC module-access reads only. It does not
route around protected current-query activation, mint action permits, issue bulk
manifests, or qualify protected security/temporal/managed semantics. A protected
installation must continue to refuse legacy read access. Separate original
current-policy/action source and native release gates remain mandatory.

## Original context capture and execution

`query_catalog_sources_in_transaction` obtains the complete real
`truss.query_binding` bundle, compiles the original request through the selected
Weft Truss compiler and executes native `truss.query_scope` admission before
returning inert original request JSON. The bytes grant no runtime permission.

An engine catalog preserves the complete model/module/SQL/backend/binding
request and original Weft artifact. Runtime `query_in_transaction` with
`engine_program` reacquires the actual native binding and invokes Weft's complete
original-program comparison before executing native SQL. Only parameter values
may change; source/model/binding/SQL/inventory/backend drift refuses. The returned
current artifact must equal the exact artifact about to execute. All original
Truss native scope, integrity, deadline, descriptor and final checks still run.
No field is removed from an original context to obtain equality.

The explicit local development compiler selections retain the existing ordinary
compiler profile. Engine catalog operations additionally select the new custody
API in the exact tested development Weft cohorts. Evidence must identify the
whole wheel/module/source hash; a development version alone is not a broad
qualification claim.

## Candidate constructor identity

The constructor requires an original `QueryCatalogSources` capture through
`catalog_sources`, or original `EngineRead` values in `catalog_entries`. Supplying
both requires one identical complete target. Each original binding text must
match its SHA-256 and the configured binding. Construction without either source,
with mixed targets or inconsistent binding bytes refuses before native dispatch.
This is a deliberate candidate constructor change; no backend version is guessed.

Identity/backend/profile come from the complete retained original target. Every
read compares its whole target before native dispatch. This metadata grants no
authority: native `query_binding`, `query_scope`, original compiler/current-artifact
correspondence and final transaction settlement remain authoritative. A native
ABI/profile update needs a fresh capture and newly compiled catalog; old programs
are never relabeled. Typed Date and other temporal selections remain HELD.

## Typed release and host responsibilities

The target revalidates strict generated parameters, submits original SQL through
the public assembly and requires complete ordered QueryRows. Native refusal or
unavailability remains an inspectable original outcome; it never becomes empty
rows. A selected absent ColumnSet raises ADOPTION_MISMATCH. DTO validators run
inside the host transaction interval and no rows escape failed final settlement.

The supplied `operation(timeout)` must own its adopted transaction and configure
native statement and operation deadlines no greater than the requested budget.
The target checks the whole elapsed budget before dispatch and release. The host
settles and releases the transaction; the target never borrows a foreign handle.
Eager verification uses the same complete native read/page path. Candidate pages
retain the complete original `weft.engine-page/0.1` artifact, exact page bound,
hidden authored Key outputs and owner cursor. Native execution recompiles and
compares the original program against the complete current binding and page
metadata before data SQL. Optional typed cursor values must match the owner's
original lexical cursor under its own Key codecs. `QueryPage.next_sort_values`
retains those native decoded values; the SDK never reconstructs a native cursor.

The subset is a single nonaggregated source with native authored primary-Key
ordering, size1..999, and supported non-temporal Key carriers. Native compiler
refusals remain original outcomes. Streams and protected current-query source
envelopes still require separately admitted profiles: the current catalog's RC
requirement does not establish the SDK snapshot stream contract.

## Validation

Actual owned PostgreSQL18.6 E2Es accept original core0.8 schemas, create instances
through public groups, capture original native binding/compiler inputs, build and
check the real CLI catalog, invoke generated typed queries and validate exact
DTOs. Bound-injection, valid-but-different original SQL and removal of every
native read-capable module role are refusal controls. Native source/instance
identities are observed from actual public acceptance, never fixture IDs.
Temporal qualification remains HELD.


[Original page evidence](../../04-build/evidence/typed-sdk-native-20261016/pages/README.md)
records the exact two-interpreter installed cohort and retained wrong-driver
refusal. The combined compiler is unpublished; native default/ABI recapture and
complete protected action/manifest bulk qualification remain open.
