---
ddx:
  id: BUILD-ROW-TOUCH-OBSERVER-001
  type: evidence
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: PLAN-PYTHON-CONSUMER-001
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
---

# Native row-touch observer implementation

`packages/postgresql/native/row-touch/observe.sql` implements the argument-free
AFTER ROW observer on the source-epoch layout 0.16 state, node and scalar tables.
The component is private and grants no consumer privileges. It is not an
installed Truss capability or a complete PA05/RT2 implementation.

The observer requires exactly one unfinished operation in the actual xid,
original nine-artifact context/group correspondence, the current actor,
retained catalog lock and original capacity reservation. It checks the exact
relation family, INSERT/UPDATE/DELETE opcode and complete OLD/NEW binary images
before changing proof state. Retained side images supply parents after cascade
deletion; current-table parent lookup does not establish attribution. A single
event deduplicates full owner/property tuples, including both old and new owners.
Object and edge IDs occupy distinct tuple namespaces even when numbers match.

All touch and operation growth is checked against the remaining reservation
before effects. Existing capacity hooks perform the actual transfers. Actual
INSERT/UPDATE results and final operation/touch readback must match complete
planned composites. A later event in admitted, effects_ready or row_sealed
increments generations, clears proofs and returns to admitted. Historical
contributors retain their own actor captures; only the current selected
operation must match the current acting role. Contributor original bytes,
artifact identities, owner/property membership, installation, xid and profile
remain checked. The existing unconditional deferred commit barrier remains.

## Component input projections

These Truss-owned draft projections preserve native binary cells. Their strings
or hashes establish correspondence, not protected admission or UMF semantics:

- `truss-native-row-image-scope/0.1`: closed `interfaceVersion` and `images`;
  each image has `kind` and `imageHex`. Full native images have exact type OIDs,
  nullability, framing and lengths. Members are unique, node identity belongs
  to one state, and retained parents are required.
- `truss-native-row-image-frames/0.1`: closed `interfaceVersion` and `frames`;
  each frame has `effectGeneration`, original-artifact `scope` and `event`.
  An event contains `kind`, `opcode`, `oldImageHex` and `newImageHex`, with JSON
  null representing the absent side. Both prestate and candidate frame plans
  retain the same exact event descriptor.
- `truss-row-owner-property-union/0.1`: closed `interfaceVersion` and `members`;
  each member contains ownerKind, ownerId, discriminatorId,
  propertyOwnerTypeId, propertyId, originalHome and originalOwnerProperty.
  Native integer identities use canonical decimal strings. Every member,
  including unused members, must satisfy the complete grammar.

The native tests place these frames in administrative fixture registry columns.
This does **not** turn frames into the six registered family prestate/candidate
schemas. The original family producer must still derive an admitted event
projection from each retained family input/prestate/candidate/effect artifact,
retain the original artifacts, and prove complete event membership/order.
A total generation schedule is currently required. One-child cascade evidence
does not qualify multi-child ordering or mixed catalog/row schedules. A qualified
original producer or counted event inventory with per-identity order remains
required; no caller-supplied scope becomes authority.

## Evidence and remaining work

The selected local evidence uses CPython 3.11, pg8000 1.31.5 and the corrected
pgserver PostgreSQL 16.15 runtime. Administrative fixtures skip unrelated catalog
FK admission for setup, keep ALWAYS observers and the commit barrier, and use
ordinary native FK cascade behavior for the cascade test. The role-change test
uses two actual administrative acting roles. None proves authenticated-person
origin, ordinary-role isolation, accepted catalog identities or installation.

Twenty native tests cover all nine event combinations, equal-value updates,
retained deleted parents, object/edge ownership change, insufficient second-owner
capacity, generation overflow, invalid unused union members, substituted event
images, wrong-event substitution, suppressed touch effects, AFTER-operation
rewrites, phase invalidation, multiple contributors and actual role changes.
Independent Python context/group/manifest decoders check original correspondence;
a Python calculation over full native operation/touch rows checks the capacity
ledger after each event in the explicit action loop. The separate cascade
statement and second-operation insert have generation/custody checks; this
checkpoint does not claim a ledger-oracle call after those separate statements. All six operation kind labels exercise the
generic bookkeeping, not their distinct family semantics.

Still required: node reparenting across retained states, later historical capture
and foreign-installation substitution, exact decimal generation 9-to-10 capacity
boundary, broader mixed/multi-child schedules, immutable-original trigger closure,
complete native work/allocation and dependency qualification, original family
producers, protected admission/installation, cohort finalization including
zero-touch operations, and the first public Python workflow. This checkpoint
must not flip executable installation or readiness flags.
