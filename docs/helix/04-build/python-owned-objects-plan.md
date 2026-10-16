---
ddx:
  id: PLAN-PYTHON-OWNED-001
  type: implementation-plan
  activity: build
  status: draft
  links:
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: PLAN-PYTHON-CONSUMER-001
      kind: informed_by
---

# Public owned objects and composition

Complete the existing Python ownership surface rather than adding a separate
administrative API. `OwnedOwnership.root` identifies the aggregate root, not the
immediate parent. ADR-002 D5 stores identity-bearing composed Records as objects
connected by owned-lifecycle edges; identity-free Records remain structured
property values, a separate unfinished feature.

Published SDK35/native68 providers refuse owned objects, ownership changes and owned edges.
`ScalarObject.ownership` now reports the rootless selection guaranteed by its
current read profile. Native65 adds multi-object transition storage. Neither
change enables owned execution; accepting the Python carrier alone does not close
that gap.

## Accepted retargeting decision — 2026-10-15

Retargeting an owned edge does not implicitly reparent its target subtree. The
caller must include an explicit `UpdateObject.ownership_change` alongside
`UpdateEdge.endpoint_change` in the same atomic group when reparenting is needed.
Truss preserves ordered operation results, updates descendant aggregate-root
references, and validates the final ownership graph before committing. An edge
change without the required explicit ownership change refuses if the final graph
is inconsistent. This accepted contract does not activate the unfinished provider.

## Implementation order

1. Finish reviewed semantics for aggregate membership and owned relationship
   edges together: original root and relationship definitions, old/new aggregate
   closure, one ownership parent, cycle refusal and final group validation.
   Derive aggregate roots from the final bounded acyclic ownership graph; moving
   a subtree updates every affected root reference. Preserve global type/key identity and reservations on root changes. No root
   key namespace is introduced. Direct-root membership versus composition-edge
   correspondence must be resolved against governing contracts before admission.
2. Version the native multi-object transition representation. One cascade must
   retain one exact before/after and journal inventory per affected typed object,
   preserving original transitions and report bytes. Capture any physical
   constraint change through UMF and use the owner SQL exporter; add a populated
   predecessor upgrade to the existing basic workflow. Edge transitions also
   retain closed operation-time endpoint ownership contexts with their own
   catalog revision/root pins, including unchanged transitions. Distinguish
   absent before/after edge sides from rootless endpoints. Legacy SQL NULL is
   admitted only through verified original pre-owned profiles; do not backfill
   synthetic roots or use these historical contexts for live ownership.
3. Implement owned creation through stored roots and earlier aliases, ordinary
   updates and ownership changes, owned edges, and complete atomic cascades.
   Lock/recheck the entire affected root/object/edge and module closure using the
   established order and NOWAIT refusal. Cascade deletes include every affected
   child and owned edge; any independent incident edge refuses before effects, including one entirely
   inside the cascade set, unless the original group explicitly deletes it. Return
   all deleted identities through the existing result carrier without fabricating
   child input operations. Ownership-only changes increment versions; equal
   ownership remains a no-op. Host commit,
   rollback, dry-run and receipt retry remain unchanged.
4. Publish a versioned complete object read with original root identity, and
   preserve ownership through identity/key/page reads, relationship reads,
   retained history, imports, actual Weft projections and catalog rebinding.
   Root provenance and all original old/new owners survive deletion. Replay
   authorizes every deleted identity and original root, not just the root result.
5. Release matching Truss/Weft wheels through the existing workflows after Astra
   Ultra review. One ordinary adopter workflow covers owned create/read/query,
   reparent, dry-run, cascade, history and idempotent replay; one refusal covers
   an independent incident edge. Keep tests basic; no performance campaign.

## Scope and unknowns

A direct-root-only provider is not the completed ownership feature. The next
implementation follows the existing CONTRACT-009 composition rules: the selected
Truss profile states its bounded acyclic forest, aggregate-root and cascade
realization explicitly. UMF owned lifecycle metadata alone does not grant those
semantics. Astra Ultra reviewed this direction and required the complete closure
and independent-edge rules above before implementation. Cyclic schema definitions, composed
value Records, general physical row homes, retained history offload and managed
service qualification remain in the full release goal. No support claim follows
from this plan or from an existing schema column.

## Storage implementation checkpoint — 2026-10-14

The native65 candidate installs the UMF-exported multi-member object/edge
transition uniqueness and nullable endpoint ownership context. The populated
published Truss0.0.29/native64 predecessor workflow passes (one test, 9.362s):
original rows and committed receipt replay survive, followed by an atomic
object update and edge replacement with retained before/after endpoint contexts.
Legacy edge contexts remain SQL NULL. Astra Ultra reviewed the implementation;
the original four-argument edge history call and owner-only upgrade helper ACL
check are corrected. Matching Weft backend0.4.35 admits this runtime namespace;
two ordinary recursive-container query workflows passed against its local wheel.

This checkpoint does not activate owned inputs, cascade, ownership reads or
historical context enforcement. SDK0.0.30 and Weft0.4.30 were development versions at this checkpoint.
Completed feature tranches ship independently under the owner release direction;
the later native66 standalone-scalar candidate is described in
[its release notes](releases/v0.0.30.md). Its matching compiler is pending.
Owned-object functionality remains unfinished and is not implied by that release.

## Next implementation realization — 2026-10-15

Use an additional common graph-write serialization gate to keep the first owned
provider practical: transaction-held `SHARE ROW EXCLUSIVE` locks on `object`, then
`edge`, both `NOWAIT`. Place this level after catalog/configuration/policy and
request exclusion, before key/root/object/edge guards. Every participating group,
ordinary single-operation and import writer follows it. The existing replay probe retains
request locks on a miss; acquiring the gate after that request level avoids an
inversion. Pure receipt replay preserves its original results and rechecks current
disclosure authority; it does not recheck live ownership or require the new
writer realization.

Privately discover the complete candidate owner/closure scope before acquiring
its ordered policy guards and the gate. Reobserve the closure under the gate; a
new earlier owner/guard requirement refuses before effects rather than acquiring
that guard late. The gate stabilizes this revalidation; it does not replace
complete affected-closure planning, authorization, ordered simulation or canonical
key/row locking before graph effects. Bound the complete closure and all planned effects; overflow
refuses the whole group. Do not enumerate unrelated graph data or turn a partial
scope into a complete closure. This is a serialization choice, not a performance
claim or a replacement for current authority checks.

Apply an explicit ownership selection at its own operation. A child created under
A and later moved to B retains both ordered states, results and version changes.
Only final forest/root-edge consistency is deferred. Omitted ownership changes
remain omitted; an equal explicit selection is that operation's no-op. Cascades
use the graph at their operation: earlier removal of an independent incident edge
may permit deletion, but a later removal cannot retroactively rescue it, nor can
a later operation restore an already-deleted child by referring to its old alias.
Astra Ultra reviewed these implementation constraints; they are not installed
ownership support.

## Value and forest implementation checkpoint — 2026-10-15

Uninstalled native components in `packages/postgresql/owned-groups/` now derive
exact value images and complete valid-forest roots for the future group executor.
Local ordinals represent existing identities and pending aliases without ID
allocation. The executor must retain their exact correspondence, discover and
authorize the complete affected closure, preserve ordered operation semantics
and invoke final forest validation at the agreed deferred point. Two basic
PostgreSQL18 tests pass (11.042s): exact numeric values/requiredness/no graph
effects and subtree reparenting with parallel edges/cycle refusal. These
components do not install a public owned-object provider.

## Operation persistence and adopter workflow — 2026-10-15

Keep one private immutable `runtime_owned_operation` row per original attempt
and operation index. It retains the complete affected inventory for a reparent
or cascade, including original before/after object and edge interpretations.
Existing transition keys connect each descendant's own journal to that original
operation. This also covers eventless no-ops without fabricating child inputs.
The existing attempt context stays immutable. The table's four columns and
attempt foreign key have saved UMF core/native models and owner-exported DDL in
`packages/postgresql/owned-groups/operation-storage.generated.sql`.

Astra Ultra approved keeping this proof private. Public events keep the existing
event0.2/wrapper0.2 shape, selecting an explicit owned history profile; they do
not embed the complete private inventory or new fields. History and query
attribution must interpret original roots from retained evidence after deletion.
At that source-only checkpoint, the public adopter target
`test_owned_objects_native.py` accepted its UMF0.8 catalog but refused its first
owned create as unavailable/profile.
The table and workflow are implementation inputs, not installed owned support.

## Native69 development integration — 2026-10-15

The development assembly now executes the ordinary public owned workflow:
create two roots, a child/grandchild and owned edges; read by identity/key/page;
explicitly retarget and reparent; dry-run/rollback; reject an independent-edge
cascade; explicitly unlink, cascade and replay original committed receipts.
Historical descendant versions retain their original roots after deletion.
Relationship reads/pages and two-hop/reverse traversal preserve the same root
semantics. Traversal freezes every bounded reached node and root in one data
observation, then renders terminals without resolving live roots again.

Basic owned and independent traversal workflows pass on PostgreSQL18.6, as do
independent edge read-only/pagination and populated native68 upgrade/key-byte
preservation. Astra Ultra reviewed the plans and implementation iterations.
The explicit logical query ABI has a reviewed Weft backend patch and a real Rust
CLI/public Python/native descendant-query workflow; matching published wheels
are still required before a release. Stock development query dependencies do
not yet provide that new backend. Native69 includes 194 installed routines.

This is an unreleased SDK0.0.36.dev0 integration checkpoint. Complete owned
imports, owned retained-value rebinding/key backfill, cyclic value definitions,
record-valued properties, general row homes, history offload and actual managed
service qualification remain in the full goal. Unsupported owned imports and
catalog transformations refuse rather than substituting rootless semantics.
