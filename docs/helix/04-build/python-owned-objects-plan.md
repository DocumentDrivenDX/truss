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
not yet provide that new backend. Native69 includes 198 installed routines.

This is an unreleased SDK0.0.37.dev0 integration checkpoint. Complete owned
imports, owned retained-value rebinding/key backfill, cyclic value definitions,
record-valued properties, general row homes, history offload and actual managed
service qualification remain in the full goal. Unsupported owned imports and
catalog transformations refuse rather than substituting rootless semantics.

## Owned import implementation boundary — 2026-10-16

Current imports cannot create a complete owned aggregate: they execute one
record per group, require stored endpoint IDs, and retain source evidence at
operation index zero with one source row per attempt. An owned child and its
ownership edge must instead validate together in one final forest. Removing
only the rootless checks would expose an unusable or incorrect interface.

The next tranche will add an explicit atomic owned-import selection while
preserving the released scalar import profile and its per-record behavior.
Use primary-key references for batch object endpoints and roots, resolving
already-live identities before decoding replacement payloads. Translate only
eligible creations to the existing group operations and private earlier-object
aliases; do not add a second graph executor. Original input indices, source
payloads, load ID and authenticated actor remain attached to their original
records. Existing identities still skip without applying replacement values.
The new selection must explicitly define dependent-record failure semantics;
it cannot silently change existing import batching or skip precedence.

Native source registration must identify the actual group operation rather than
assuming a single creation at index zero. Its storage and deferred checks must
preserve the exact original record and resulting typed identity for every
created object/edge. Any changed physical storage comes from UMF and includes a
published-predecessor upgrade. Ordinary module, endpoint and root disclosure
checks remain required for reports and source lookup. Existing rootless source
rows and their original receipts must remain readable.

Astra Ultra cleared the minimal separate atomic selection on2026-10-16, subject
to the implementation constraints below. This is plan review, not an available
provider or runtime qualification. The basic completion gate is one public owned aggregate import,
caller commit and fresh object/edge/source readback; repeated import with invalid
replacement payloads must skip and preserve originals. One failed dependent
record must leave no partial aggregate. The adopted host alone settles its
transaction; engine-owned execution settles only complete atomic batches.
This tranche remains unfinished and is not a release claim.

The new selection uses distinct owned-import input/object/edge carriers and a
closed profile/context. Ownership has one authoritative location. Dependencies
resolve to existing live objects or earlier eligible object records; forward
references and reserved-identity references refuse explicitly. Unlike legacy
object-before-edge processing, this opt-in atomic profile preserves original
record order. Endpoint-only ambiguous parallel edges continue to refuse.

Identity resolution precedes replacement payload decoding. A repeated identity
within the batch skips only if the earlier new creation succeeds. If the atomic
batch rolls back, it cannot report that provisional identity as live. Existing
live/reserved skips remain skips; every eligible creation is rejected on a known
atomic failure. All-skipped input returns without invoking an empty group.
Transaction/commit uncertainty retains the existing unknown dispositions.

One host operation/savepoint encloses identity resolution, the existing group
executor and all source registrations. A source-registration failure rolls back
the creations too. Bound original records and report bytes as well as generated
operations. The host remains the sole transaction owner in adopted execution.

Native provenance storage uses unique `(group_attempt_id, operation_index)` plus
existing entity uniqueness. Existing rows migrate to index zero. Source and
commit checks bind the indexed operation/result/transition, typed identity,
original primary key, ownership/endpoints, exact payload and load ID. Private
aliases alone do not establish correspondence. Keep legacy one-operation checks;
do not require historical legacy attempts to have owned-operation storage rows.

## Ordered result storage — 2026-10-16

The 1,024-operation workflow passes locally but still exceeds the unchanged
statement deadline in installed-wheel CI. Built-in PostgreSQL statistics identify
creation and settlement costs; the attempt's growing result array is rewritten
on every operation. Astra Ultra reviewed replacing that pending representation
with a nullable write-once result in each existing owned-operation row.

Keep the original plan, attempt, ordinal and writer immutable. Capture expects
an empty result slot. Both the create leaf and the general owned executor seal
and reread their exact result, then advance and reread scalar progress under the
original actor/writer/ordinal/incomplete guards. Pending attempts retain empty
arrays; prior-create and pre-finish transition readers consume sealed slots.
No-op and cascade operations each retain one original primary result.

Finish requires every original ordinal and result, assembles the full ordered
results and aliases once, and stores them together with completion. Finish and
mandatory commit independently compare those arrays with the sealed slots.
Existing receipt, replay, history, import and attribution carriers stay intact;
legacy profiles keep their original execution representation. The fifth column
and its nullable core projection come through the UMF owner SQL exporter. The
published native68 upgrade installs that new table and its guards; unpublished
native69 snapshots receive no compatibility adapter.

The implementation gate is the existing public owned/alias/no-op/cascade/replay
workflows, a rewritten-result refusal preserving prior caller work, populated
published-predecessor upgrade, and the complete actual1,024-create/update/commit/
replay/readback and final-operation-fault tests. Installed Linux/macOS wheels
must pass their original deadlines before release. This is an implementation
candidate until those checks and the completed Astra review pass.

## Stored result count — 2026-10-16

Keep the single protected native group call and private partial helpers. Astra
Ultra clears a narrower optimization: PostgreSQL stores the generated integer
`jsonb_array_length(results)` on each attempt. Row settlement reads that exact
derived count through its existing actor/writer/ordinal guard, avoiding repeated
loading of a completed results array. Local finish-time array checks stay intact;
the in-memory attempt has not yet persisted its final results at that point.

Append the column consistently in fresh and upgraded storage. Under the existing
exclusive upgrade cut, require the predecessor column absent and verify the
stored expression, integer type, private column ACL and populated counts. Adding
a STORED generated column physically backfills rows but preserves original
source, result and receipt values. Basic slot/replay and populated published35
upgrade tests cover the derived count and refusal of direct assignment; retain
the complete capacity/final-fault workflows and installed-runner deadlines.

## Edge validation identity reuse — 2026-10-16

The basic 1,000-edge public workflow still has a recorded finish-time statement
timeout. Astra Ultra clears a narrow first change: its edge transition validator
passes the plan and attempt it has already checked to the existing identity
helper at four direct call sites. Exact slot, writer, create ordinal, operation
and typed-identity checks remain in that helper. Image/endpoint helpers, current
authority, full settlement and deadlines remain unchanged. This removes repeated
reads within one invocation; it does not establish that the stress case passes.

## Edge invocation context — 2026-10-16

The isolated full edge-phase profile prioritizes repeated actor qualification
and effect work. Astra Ultra clears private optional arguments that carry the
already checked actor and parsed original input through one owned step's read
helpers. Every module-policy lock, membership and endpoint-reader check remains
at its existing point. The edge effect checks the original input bytes before
using prepared JSON and keeps its default parse for other callers.

Fresh actor qualification remains after the edge/journal/transition writes and
after result-slot/progress writes before closing edge validation. Authorization,
final group settlement and mandatory commit each qualify their own invocation;
no actor or permission result is cached across calls. Published step/authorize
signatures stay intact; new private optional arguments retain default call paths
and the 219-routine inventory. Basic owned/edge/refusal/upgrade workflows and the
complete 1,000-edge and 1,024-operation gates remain required.

The focused authority control also reproduced a pre-existing edge-only gap on
main 79a27c4a: after flushing the attempt constraint and revoking the writer while
retaining reader access, COMMIT succeeded with one durable edge. Edge row and
transition settlement now recheck the relationship module writer, so queued
events remain effective after that early flush. Two last-write actor controls
cover transition insertion and unfinished attempt progress updates. These checks
join the basic release workflow; they do not establish a performance pass.

The released-scope edge-writer hotfix uses SDK0.0.36/native70. The owned development
tranche advances to SDK0.0.37.dev0/native71, preserving the exact native68 and
native70 predecessor identities and supporting the populated68→70→71 chain.
Historical native69 evidence remains attached to its original source.

The native71 edge settlement filters now read the admitted immutable attempt
context instead of reparsing the complete original group just to select its
mutation profile. Original source bytes, fresh actor/writer checks and every
transition validator remain unchanged. Astra Ultra clears the exact two-filter
change; six basic edge/owned/authority workflows pass (22.411s). The unchanged
1,000-node/1,000-edge matrix still refuses with57014 during edge application
(26.245s total), so this is not performance qualification or release clearance.

Final incident-edge validation now resolves the live final edge identities once
per validation invocation, then checks the same actual per-object incident edges
against exact `(typeId,id)` membership. Parallel edge IDs remain distinct;
deleted edges are excluded. Actual object/edge images, complete effect inventory,
forest validation and fresh authorization remain checked. Astra Ultra clears the
source. Seven existing edge/owned/authority/parallel workflows pass; a focused
unplanned parallel-edge injection refuses with the original inventory error and
preserves prior caller work with zero durable edges after caller COMMIT (4.645s).
An initial ambiguous SQL projection and a max1 test fixture were corrected.
The unchanged1,000-edge matrix still times out during apply (10,026ms; create
7,310ms plus4,845ms COMMIT). No edge commit was reached or performance gate closed.

The edge-image helper now mirrors object-image context reuse: it accepts optional
checked plan/attempt values and passes its selected local plan into identity
resolution. Final actual-edge validation supplies its already checked final plan
and attempt. Four-argument callers retain lazy defaults, phase/deletion handling,
identity proofs and actual image comparison; no endpoint helper changed. Astra
Ultra clears the four runtime-source files, and all eight basic graph/authority/
parallel/inventory tests pass (29.103s). The original1,000-edge matrix still
refuses during apply with57014 (26.350s total); performance remains open.

SDK36's release run38891797388 failed both installed adopter workflows because
published Weft0.4.34/backend0.4.37 admits exact native68, not native70. No assets
were published and the tag is retained. A narrow new compiler backend will admit
exact native70; the replacement SDK37 release will retain native70's original
manifest. The owned tranche will then advance to SDK38/native71. Latest published
installation instructions continue to select SDK35 until that replacement ships.

The complete identified pure edge-helper chain now carries the already checked
plan/attempt through metadata, image and endpoint identity resolution; phase
selection uses direct JSONB path extraction. Live readers/writers, physical rows,
original creation-index source lookups and all closing guards remain unchanged.
Astra Ultra clears the generated219-routine implementation. Eight basic tests
pass (29.953s), but the unchanged diagnostic1,000-edge workload still hits57014
before edge COMMIT (28.101s total). Completed plan lookups fall from77,141 to
29,861; this does not establish a latency improvement. Final member identity/
image work and repeated initial-node map construction remain profiling targets.
