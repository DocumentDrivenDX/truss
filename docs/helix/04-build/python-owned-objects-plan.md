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

Current providers refuse owned objects, ownership changes and owned edges.
`ScalarObject` also omits ownership. Native storage already has the root pair,
but ordinary transitions permit only one object per operation. These are real
implementation gaps; accepting the Python carrier alone does not close them.

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
   predecessor upgrade to the existing basic workflow.
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
