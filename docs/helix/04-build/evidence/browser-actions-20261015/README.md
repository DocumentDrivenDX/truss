# Browser action and separate selection-read issuance

The worker now derives the original local action preparation from the exact
registered catalog document using UMF's unchanged public producer633f8. It
reuses the existing closed core-catalog admission and original membership
observations. The original Products sourceb8ce produces preparation6f5e exactly.

`registerAction(owner,{module,action})` issues an opaque per-open action handle
and returns separate copies of the original model/pins/preparation metadata.
`grantSelectionRead(owner,action)` separately issues an opaque read grant for
local-store-read/1, the original target Key and every original Record member in
declaration order, complete-canonical-target-population/original. Private custody
binds both handles to the issued owner/open instance, store/incarnation and full
catalog/source cut. No serialized ID, declaration or metadata copy issues a
handle. Every later internal grant use rechecks action/grant identity, current
catalog and lifecycle state. Closing prevents further issuance or use.

The actual Chromium153 case exercises this exact owned bundle under a Pages
prefix: original preparation and complete grant, forged action refusal, previous
open action refusal despite persisted store/incarnation equality, fresh issuance,
and the existing catalog/lifecycle checks. Strict worker TypeScript passes.
Two fresh builds from different working directories yield the same provider
and manifest digests, matching the retained final receipt.

The owned source archive contains original UMF40f011 public ESM9d26a51a,
compressed losslessly; the emitted ESM bytes remain unchanged and hash-checked.
Original provenance and the 56-package inventory with 51 existing notice files
are retained. Five package entries contain no installed notice file; no missing
license text or licensing-closure claim is invented. The builder checks every
inventoried notice hash and rechecks all captured build inputs before emitting
its manifest. No mutable UMF checkout is required to build or run this provider.

UMF's separate typed-access proposal at branchdd7b81f6 (CONTRACT069/071/072/073)
was read for alignment. Its ManifestBulkPlan leaves execution to host workers;
native-sql/0.1 is a raw-table proposal and does not replace local CONTRACT905.
No generated target adapter, structural-digest catalog admission, null/wider SET
domain or new Python/managed-database qualification is claimed here.

Selection SQL, helper installation, materialization, sealing, effects, replay
and recovery remain the next provider integration. This checkpoint issues local
handles; it does not execute actions or establish native person/security claims.
