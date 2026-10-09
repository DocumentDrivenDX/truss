# Protected source epoch lifecycle candidate

Status: proposed implementation selection, not an installed profile.
Governing sources: CONTRACT-003 report producer context; CONTRACT-006 immutable
change identity; CONTRACT-007 installed recovery context; CONTRACT-008 committed
installation and trusted deployment identity. This is Truss-owned installation
custody, independent of UMF interpretation and Weft lowering.

## Identity and storage

Use an opaque producer-issued epoch token, retained as exact UTF-8 text. It is
not a counter, timestamp, catalog revision, xid, installation ID or caller
request token. An installation can have successive epochs. Allocate through
the registered installation lifecycle producer; collisions refuse under a
native unique constraint and retry issuance before publication. Entropy source
and exact token grammar belong to that immutable producer profile and require
qualification before installation. No arbitrary epoch argument is accepted by
ordinary operations.

Add a fixed immutable epoch registry and one installation-local current-epoch
pointer to the UMF layout source before generating DDL. Registry entries bind
installation ID, trusted target incarnation, token, predecessor (absent for
initial issuance), transition reason, exact lifecycle profile and original
transition evidence. Preserve exact artifact bytes and direct SHA-256, with
full-byte comparison; a digest alone is not original authority. The pointer
references the full registry identity. Reuse the existing installation marker
and archive rather than introducing another installation identity authority.
A profile must provide bounded token/evidence size and transition work.

## Admission and transitions

Initial issuance belongs to the installation transaction. Its registry row and
pointer are provisional until independent committed installation admission;
bootstrap-attempt observation never qualifies an installed epoch. Registry and
pointer publication roll back together. Ordinary roles have no direct DML,
allocator or transition privileges; complete installed entry/role closure is
part of adoption, not established by this document.

Ordinary restart, connection replacement and retention changes preserve the
current epoch and original event identities. Restore, fork or source replacement
requires trusted deployment incarnation evidence and an explicit transition
before new protected writes. A clone cannot prove its identity using copied
marker/registry bytes. Truss cannot detect an unreported byte-identical restore
from SQL state alone: the trusted deployment admission producer must fence it.
If that evidence is unavailable, installed admission refuses.

For a continuity-preserving restore, retain installation identity and historical
epoch rows, issue a fresh current epoch, and label older event/report origins
with their original epoch. For an independently installed fork/replacement,
use its independently admitted installation identity and fresh initial epoch;
imported history remains original source evidence and is not relabeled as new
local history. No automatic cross-epoch checkpoint translation is provided.

Writer admission holds a shared lock on the current-epoch pointer through the
surrounding native transaction, captures its original registry/evidence and
executor affinity, and uses that same epoch for acceptance, mutation, journal
and feed prerequisites. Transition obtains the exclusive pointer lock, waits
for preceding admitted writers to end, verifies current predecessor and target
incarnation, inserts the immutable successor and switches the pointer atomically.
No role-only context, caller JSON, current setting or later connection can
replace this captured installed basis. A transition retry with its original
request identity returns the original result only after complete evidence
correspondence; changed evidence conflicts. Commit uncertainty follows original
attempt recovery, without issuing an uncorrelated second transition.

## Required native test schedule

1. Fresh installation: provisional reads refuse installed admission; commit
   produces one independently admitted epoch; rollback leaves no epoch/pointer.
2. Restart and retention: same epoch; identical historical event identity and
   original report context.
3. Concurrent writer/transition: transition waits for the held shared pointer
   lock; next writer sees the successor; one operation cannot straddle epochs.
4. Restore/clone: copied SQL metadata under different or unavailable trusted
   target-incarnation evidence refuses; explicit admitted transition succeeds.
5. Stale/copy attacks: old installed basis, changed executor, forged epoch,
   registry update/delete and direct pointer DML refuse under ordinary roles.
6. Retry/uncertainty: unchanged original request/evidence returns original epoch;
   changed evidence conflicts; uncertain commit reconciles original attempt.
7. Historical reads/ACK: old epoch remains original history; old checkpoint
   cannot acknowledge a new epoch; no checkpoint rewriting or guessed baseline.
8. Resource and authority: bound exhaustion leaves no transition effects;
   qualified installer alone can transition; role recreation/definer calls do
   not inherit authority solely from matching role text.

Exit requires generated layout correspondence, complete installation/profile
adoption, native schedules and complete report-context composition. This design
selects storage/lifecycle structure; it does not claim issuer implementation,
managed deployment fencing, accepted IDs or a working feed.

## Storage candidate generation

[source-epoch-storage-v0.1.proposal.umf.json](source-epoch-storage-v0.1.proposal.umf.json)
retains the fixed native registry/pointer declarations through UMF's PostgreSQL
adapter. Reproduce with `bun scripts/build-source-epoch-layout.ts`; saved model
reload exports identical [owner DDL](../../04-build/evidence/source-epoch-storage.owner-export.sql).
The [receipt](../../04-build/evidence/design-audit/source-epoch-storage.json)
records exact output hashes and owner checkout revision. This native extension
candidate is not a core ER projection, installed profile or immutable owner
bundle qualification. It must be composed with the installation marker model,
qualified native guards and selected lifecycle issuer before adoption.
