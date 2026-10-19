---
ddx:
  id: truss-operation-statement-audit-20261019
  type: test-report
  activity: test
  status: draft
  links:
    - id: ADR-008
      kind: informed_by
    - id: ADR-007
      kind: informed_by
    - id: truss-practical-performance-matrix
      kind: informed_by
---

# Operation statement audit

The owner requires each statement to justify its purpose, cardinality and cost
against the trusted application/adapter design. Administrator-installed callbacks
that forge private engine plans and effects are outside ADR-008's ordinary caller
boundary. A test simulating those callbacks does not create a requirement to
reconstruct the engine's semantics independently at every database layer.

The structural review covers the selected current write profile and its public read/replay paths; qualification remains pending. The canceled 089dbf14 run never started stress: final review found the mixed CREATE leaf still recounting completed slots and replaying inserted rows. The corrected leaf uses indexed ordinal custody and mandatory group settlement. Earlier C83
failed macOS eight-key capacity, macOS index-heavy updates and Ubuntu wide updates.
Cancellation frames identify the active statement, not the dominant cost.

| Operation / layer | Required purpose | Observed or structural work | Disposition |
| --- | --- | --- | --- |
| Preparation | Preserve source meaning; compile immutable schema once per revision | C80 real-schema measurement: zero SQL submissions; application schema indexes reused on warm writes | Retain; do not create owner transcripts or per-record schema reconstructions |
| Registration | Publish selected schema atomically with live authority | C80 fresh registration: savepoint, accept payload, release | Retain atomic publication; audit acceptance internals separately from ordinary mutation |
| ID / key reads | Current authorized data and exact identity | C80: three frontend submissions per call | One payload plus containment; no measured case for caching authorization |
| List / compiled query | Correct lowering, complete bounded results, current scope | C80: twelve submissions per list; several current-scope/path observations | Fuse path capture/pinning and final scope/actor observations; retain source-time and post-query scope checks |
| Single update frontend | Current custody, context and one atomic apply | C80: ten submissions including BEGIN; COMMIT separate | Explain adoption/context/containment separately; do not mislabel all ten as native guard queries |
| Batch key preflight | Exact uniqueness/reservations and concurrent writer exclusion | Installed C83 scalar helper repeats the same global advisory gate and indexed observations for each route | Replace owned batch observation with a distinct route relation; retain scalar API for other callers |
| CREATE / UPDATE key expansion | Derive canonical key bytes and native row identities | Full authored operation / object images carried per key through materialized stages | Replace with operation index, native object/type IDs and necessary key bytes |
| UPDATE key/object DML | Atomic version-matched rows and relational constraints | Producer serializes full expected and RETURNING rows, compares, then rereads physical rows | Replace verification-only image aggregates/readbacks with expected-version predicates and affected-row counts; reuse the locked captured before snapshot, without a second full object read |
| UPDATE history | Required property deltas, complete metadata history, ordered wire digests | Additional paired hashes compare generated INSERT payloads against RETURNING payloads | Keep actual history/wire digests; remove administrator-trigger rewrite proofs |
| Group finish | Return complete ordered results, resolve conflicts, check current policy | Result slots assembled, then immediately reaggregated and compared again | Assemble once; retain one mandatory commit inventory check |
| Query stored values | Return admitted engine-valid values; enforce native numeric representability | A prop_def scan plus full property semantics replay for every object | Read numeric metadata once per type; compute numeric validity in the source query; retain root authority, header and complete-bag caps |
| UPDATE settlement | Current actor, transaction, revision, owner/read dependencies and effect count | Private immutable plan interpreted and checked again at finish and commit | Remove semantic replay; retain cheap live context/count checks; resolve dependency authority once per distinct type |
| Deferred entity checks | Complete attempt and live authority at commit | Object and transition events each replay object/key/journal proof for the same owner | Consolidate engine-owned work at mandatory attempt settlement; issue current actor once there, retaining separately supported direct-SQL routes |
| Deferred journal checks | Produce history atomically through private writers | Another callback per property event rereads journal and immutable claims | Private table ACLs and canonical producers define the boundary; remove unsupported administrator-forgery oracle |
| Feed capture | Preserve complete reservation facts and transaction configuration | One nested INSERT per reservation plus configuration query per reservation and journal row | Bulk transition-table capture; configuration once per nonempty carrier statement; refuse actual cross-statement drift |
| Installation | Select compatible runtime, owner and facade privileges | Diagnostic trace saw >1,800 frontend submissions per schema installation, including repeated per-object dependency and ACL observations | Retain one-time installation owner/privilege inventory; these observations are outside ordinary record execution and are not repeated per record |

Counts above are C80 scoped frontend observations or explicitly identified source
multiplicities. They are not C83 per-operation latency attribution. In the exact
1,024-object/eight-key changed update, seven fields change: 7,168 new reservations
and 8,192 history rows. The old feed configuration path therefore executes 15,360
row callbacks for those two carriers alone. Removing these repeated callbacks
is a structural reduction; its latency effect still requires qualification.

The opt-in benchmark `--trace-sql PATH` records ordered SQL text, workflow scope,
call duration and SQLSTATE without bind values. Native work inside a function is
included in its outer duration, not falsely counted as a single server statement.
The first C83 instrumented diagnostic exceeded installation's 30-second operation
allowance for all three schemas before exercising reads/writes. It is failure
evidence, not a functional or timing pass. Keep unchanged stress workloads and
10-second SQL / 30-second operation limits for release qualification.

Privileged trigger-rewrite tests must not gate this ordinary deployment profile.
Replace those requirements with consumer ACL denial, independent exact-history
readbacks, actual late SQL errors/rollback, permissions/revocation, expected-version
conflicts, uniqueness, FK and complete result/receipt tests. No stress workload or
capacity is removed by this change of threat boundary.


Final source review also removed the second key-membership/reservation observation
in each batch producer: preflight holds the global writer gate until transaction
end, and no ordinary caller interleaves private DML inside the protected call.
The final object/key snapshot oracle is retained for legacy execution profiles;
canonical rootless creates and prepared rootless updates use their canonical
writes and expected-version/count checks. Legacy and historical paths retain their public meaning checks. Their retained
receipt readers select compiled historical dependencies by revision/type rather
than rebuilding and scanning the complete catalog for each object. For compact
prepared updates, the before image is projected directly from the operation-zero
`initialScope` snapshot; it is not regenerated by replaying the historical plan.
When a historical frame needs the after image, the reader hydrates it from the
retained transition and checks the compatibility hash. The stored compact-plan
desired hash remains for that lazy hydration; the ordinary producer does not
serialize and hash the image again to prove its own construction. This is a
compatibility field, not a new admission transcript.


## Resource analysis, 2026-10-18

Timing is a capacity observation, not the justification for this design. Let n be
operation count, b the total request bytes, k the affected key bytes/rows, d the
history event bytes/rows, and e the actual incident edge count. Database index
access additionally depends logarithmically on stored table/index size; no claim
of constant-time SQL or strict linear PostgreSQL allocation follows from these
formulas.

| Path | Required work and retained data | Removed amplification |
| --- | --- | --- |
| Rootless batch create/update | Admit the request once using revision-scoped application dictionaries; set-based object/key DML; store canonical history and ordered result slots. Work follows n, k and d, plus indexed conflicts/locks. | Object images carried once per key; expected/RETURNING/reread image aggregates; second locked key observation; per-event proof callbacks. |
| Generic ordered progress | One small ordinal update per operation; one ordered result assembly at finish. Private request and document bytes stay unchanged. | Comparing b-sized request/documents/context on each progress update, a potential n*b path. |
| Edge mutation | Resolve actual selected endpoint identities/readers; capture the actual edge before image once; version-matched DML and canonical history. Lock distinct old/new business keys. | Full endpoint object rereads/comparisons; repeated transition derivation; expected/RETURNING/physical image proof sets. |
| Cascade deletion | Work over affected nodes and incident edges; retain actual deletion/history output. Collect event chunks and aggregate in order once. | Repeatedly appending complete growing JSON result arrays and reading unrelated relationship endpoint schemas on unbounded paths. |
| Import source attachment | Decode group input once per batch; indexed operation/result linkage per record; preserve original record bytes and one canonical immutable source row. | Whole group decode per record, per-key physical object replay, growing source map concatenation, duplicate full source image in ledger and deferred per-source reproof. The compatibility ledger column remains empty for new records. |
| Settlement | Check current custody, result completeness and distinct actual owner/reader dependencies; apply bounded relationship constraints. | A second semantic/history execution over private plans and transitions, including repeat final object/key snapshots for owned execution. |
| Feed | Publish required original facts; capture transaction configuration once per nonempty carrier statement. | Configuration discovery per journal/reservation row. |

New owned transitions leave the compatibility `after_keys` carrier empty. The
physical key tables already hold the canonical memberships; neither public
history, provenance, feed nor receipt interpretation needs another complete
expected copy. Older stored copies remain readable without a data rewrite.

Canonical before/after metadata history is product data required by ADR-007.
Property deltas, exact original import bytes, actual source metadata, and ordered
wire hashes remain for their public meanings. They are not a license to keep
parallel expected copies or reread every private write to prove correspondence.
Imports read their immutable canonical source row. No installation upgrade or
rewrite of an earlier release is supported.

Schema dictionaries are application memory indexed by immutable revision, type
and property identifiers. Their cost follows the number and size of definitions,
not record count. The two-revision/128 MiB cache budget bounds retention; 1,000
types alone is not a byte estimate without property counts and definition sizes.
Database dependency metadata supports live policy and historical interpretation;
it is not a per-record substitute for the application dictionaries.

### Per-operation cost ledger

These are work bounds, not elapsed-time predictions. Let S be selected schema
bytes, G the scoped graph, A the sum of actually affected members across ordered
operations, P returned payload bytes, H requested history bytes, and D stored
index cardinality. Costs include the required output and PostgreSQL index access;
ordinary SQL planner choices remain subject to correctness/capacity qualification.

| Operation | Purpose and resource cost |
| --- | --- |
| Prepare catalog | Parse/validate/compile S once, retain original source and immutable schema indexes; no database statements and no mandatory transcript. |
| Fresh install | One-time selected runtime DDL and owner/ACL inventory. Work follows runtime objects, never record count. An existing installation refuses before changes; installation upgrades are unsupported. |
| Accept catalog | Current revision/permission check, source publication and actual catalog deltas atomically. Cost follows source and definitions/effects; no table/index per user type. |
| Adopt / status / group context / schema revision | Constant command count, small current installation/transaction/catalog observations. No object scans. Host containment is separate from payload work. |
| Get object / exact key lookup | Typed primary-key or exact-byte key-bucket index probe, actual owner/root permission and bounded payload: O(log D + P), plus bounded collision-bucket evidence. |
| List / compiled query | Select immutable binding, lower once, read bounded complete source bags, current authorization before/after, and decode returned data. Scalar scan follows selected bag rows; joins/sorts follow query semantics. Complete-entity attribution resolves indexed creation/latest transition and actor without semantic/history replay. Descriptor lookup is a dictionary built once per query. |
| Create / changed update | Admit supplied values once against loaded schema. Write selected objects, changed key routes/reservations, history and results atomically. Work follows supplied/affected bytes, affected key rows and required history; table/index operations add log D. No key-stage object-image multiplication. Mixed/owned CREATE leaves reuse the already admitted source and prepared values; they do not recount prior results, compare whole group bytes, replay physical inserts, or observe the same protected key routes again. |
| No-op update | Validate supplied changes and expected version, retain the existing version/timestamps, produce no history delta. Group completion and current authorization still apply. |
| Edge create / retarget / unlink | Selected typed endpoints and distinct business-key routes, version/count DML, actual edge metadata/history. No full endpoint property copies. Edge pages collect payloads with an incremental byte total and deduplicate root dependencies once. |
| Reparent / delete cascade | Observe the bounded connected component once; traverse actual owned adjacency, update/remove A affected nodes/edges, produce required history. Repeating a reparent may necessarily touch the subtree again; copied work must follow those actual effects, not all unrelated G members. The mixed planner uses one invocation-local indexed working relation; each operation projects only its changed members and root/endpoint witnesses. The initial snapshot is retained once, and complete final graph projection occurs once. |
| Import | Identity/key preflight, one atomic admitted group, one batched source attachment. Original record bytes and one immutable source fact per created entity are retained. Decode the operation group once; source/field and primary-key component projections aggregate once. Original payload envelope validation and execution each decode record bytes, giving two linear passes rather than one. |
| Read history / source | Indexed retained coordinates, actual requested event/source bytes and their current historical readers. Returning H bytes necessarily costs O(H); historical event validation buffers semantic events and serializes each array once. Historical property readers load compiled revision/type metadata once per returned group or complete image, then use local property lookups; a returned property neither reconstructs the full catalog nor decompresses the same schema row again. Full transition replay is removed, while original edge endpoint/root policy is checked once per group. Ordinary entity attribution must not read H just to return actor names. |
| Preconditions | Capture the actual selected object cut and acquire exact key routes, then evaluate current conditions in authored order. Predicate-key bytes are indexed by condition ordinal; ordered failures aggregate once. Preserve condition failure precedence and current dependency authority. |
| Receipt / reached | Exact retained receipt and transaction inclusion, distinct retained dependency readers. Modern receipt authority uses indexed results plus compiled revision/type dependencies once, rather than parsing the complete group for each operation. |
| Feed / acknowledge | Indexed writer position, whole transaction facts and actual required revision prerequisites within explicit caps. Preserve original facts; no per-property configuration discovery. Acknowledgement changes the selected consumer position atomically. |
| Traverse | Visit the selected bounded frontier and incident edges using typed indexes, bounded result bytes, current resource readers; no scan of unrelated types or reinterpretation of every stored property. |
| Finish / commit | Small current custody/version/receipt checks, one complete ordered result inventory, distinct actual dependency readers, applicable bounded graph constraints. No second engine execution or private event-by-event proof program. |

The mixed planner creates one temporary working relation and two adjacency indexes per
invocation, drops it on completion, and retains no cross-call state. Initialization
and final projection follow G; indexed point access and actual adjacency/effects
follow A (with index access costs). Unchanged root and endpoint witnesses use small header columns in the invocation
working relation, initialized once and refreshed only on actual state changes.
Their reads and plan aggregation do not repeatedly detoast a shared property map.
Shared scope discovery uses recursive set
membership, and forest root resolution marks each node once. It does not walk
every ancestor chain afresh or copy G for each of n operations. Positive minimum
relationship constraints still inspect applicable node/relationship pairs: those
are actual constraints, not a scan across every unrelated relationship.

No latency improvement is claimed from these formulas. The real-schema and unchanged stress campaigns validate
correctness and supported capacity once on the final package; repeated local
timing runs are not an optimization acceptance criterion.


Buffer implementation note: PostgreSQL18's `array_append_support` explicitly
supports modifying the assigned array in place; `array_append` works with expanded
array storage. The retained local buffers use that form (or indexed assignments),
then serialize their payload once. This is different from concatenating an entire
flat JSONB array/map at each iteration. See the pinned-major
[PostgreSQL18 implementation](https://github.com/postgres/postgres/blob/REL_18_STABLE/src/backend/utils/adt/array_userfuncs.c)
and [PL/pgSQL array regression cases](https://github.com/postgres/postgres/blob/REL_18_STABLE/src/pl/plpgsql/src/sql/plpgsql_array.sql).
This does not assert that arbitrary SQL `array_cat` or arrays passed through
serialization have the same in-place behavior.


### Reachability of retained compatibility code

The installed `runtime_group_profiles` selects the owned profile. On a new request,
`object_group_begin_prepared` rejects any other mutation profile before effects.
Older scalar step implementations remain installed for compatibility references;
their growing result carriers are not selected for new public writes. Older
committed receipts replay before that gate, using the retained-receipt readers
covered above. This is a call-path fact, not a claim that every dormant historical
implementation has a linear algorithm. New CREATE, UPDATE, edge, mixed and owned
execution all use the selected profile and are included in this review.


### Canonical write statement families

These counts describe producer DML, not the entire protected frontend call or all
PostgreSQL-internal statements. Native revision/current-permission observations,
key preflight, transaction containment and group settlement are separate ledger
entries above. Empty sets can still submit a statement affecting zero rows.

| Producer | Canonical writes and justification |
| --- | --- |
| Rootless CREATE batch | One set INSERT each for objects, key memberships, retained reservations, journal and transitions; one grouped key-guard UPDATE; one result-slot UPDATE and one ordinal UPDATE. Each writes actual required state or completes its native operation slot. No INSERT/RETURNING/physical-image equality program follows it. |
| Distinct stored UPDATE batch | One changed-key DELETE, membership INSERT, reservation INSERT and grouped guard UPDATE; one version-matched object UPDATE; at most ceil(n/64) journal INSERTs; one transition INSERT, one result-slot UPDATE and one ordinal UPDATE. Journal sets bound formatting intermediates while the whole group remains atomic. |
| Mixed or owned CREATE leaf | One actual object INSERT; actual membership/reservation INSERTs and guard advancement per affected key; one create journal INSERT and one transition INSERT; one once-only indexed result-slot UPDATE and scalar ordinal UPDATE. It uses captured immutable schema/values and the group's held key gate, without rescanning prior slots or reobserving protected routes. |
| Generic object/edge effect | Typed indexed current-state/version access, DML for actual changed/deleted members and keys, canonical event production, and one transition per actual affected entity. Required cascades scale with their effects, while unchanged endpoint/root witnesses carry headers. |

Every producer checks affected-row counts for its selected actual writes. Native
PK/FK/unique constraints, the held writer/key gates and expected-version predicates
supply their independent relational/concurrency guarantees. Full private row
images are not read back merely to demonstrate that their producer worked.

## Current-only installation and source boundary

The owner decision on 2026-10-18 removes all pre-0.10 UMF source admission and all
predecessor Truss installation upgrades from this release. Preparation and key
encoding accept UMF 0.10.0; the ordinary preparation route selects the complete
current policy. Historical catalog revisions within a live installation remain
part of reads, history, and schema evolution. They are not installation upgrades.

Fresh installation now writes one immutable installation identity. Resolving the
active runtime reads that singleton directly: there is no release generation
sequence, release ledger lookup, overlay, or predecessor configuration rewrite.
The installer refuses an existing namespace; it never resets user data. The
compatibility upgrade method refuses before submitting SQL. Packaged predecessor
manifests, migration-only SQL, historical-wheel downloads and upgrade fixtures
are removed. The qualification campaign exercises the current format and fresh
installation, with unchanged real-schema and stress dimensions.

The three bundled Hohfeld fixtures were authored with a UMF 0.7 envelope. The
current-format fixtures change only the top-level `umf` declaration to 0.10.0;
original source hashes and source commits are retained as fixture provenance.
This qualifies the same real schema shapes under the supported current format,
not an automatic legacy import or a runtime migration feature.

Current-format registration no longer calls the field/member/key correspondence
replay helper, rebuilds the accepted report on every view, or installs a deferred
full-catalog reconstruction and graph scan on every changed definition. The
ordinary head snapshot aggregates each native metadata table once: O(D+B) for D
definitions and B metadata bytes. The no-argument current-acceptance working
basis is compacted to current definitions plus only the archives and latest
document it needs; it leaves `schema_change` empty and does not rewrite or trim
original history. Catalog views read accepted typed rows directly under the
current actor and revision lock. Historical reconstruction remains for actual
historical metadata requests, not current initialization or every changed
definition.

`_security_catalog_assessment` checks the current maximum head, report presence,
indexed inexpensive conditions, latest-source correspondence, and current
inventory. It does not count every historical receipt, rebuild reports across
history, or replay source validation. Explicit historical expected-record
projection uses the first future change's `before` value as the definition
overlay; it does not replay the historical planner to reconstruct each state.

The private `expected::text` serialization and its 16 MiB cap were removed, along
with the lifetime cap of 512 retained `schema_doc` rows. Actual caller bounds
remain: at most 512 input documents, 4 MiB source bytes, and 16 MiB request bytes;
the materialized view remains bounded at 16 MiB and 65,536 definitions. These
input and view limits are distinct from the removed verification serialization
and retained-row cap.

The sole current policy is UMF 0.10.0. Its actual document validator supplies the
validation result; Truss projects declarations directly. Earlier inspector
transcripts, configured provisional-catalog candidate/report staging, predecessor
profiles and their Python proposal adapters are removed. Key encoding uses the
pinned version-neutral UMFK1 framing primitive after validating/indexing current
source once per batch. Each key carrier contains its source hash and actual key
bytes instead of a repeated full source image: retained bytes are O(schema +
key payload), rather than O(keys × schema). This does not claim that an older
UMF public key-receipt API supports 0.10.

## Final catalog cost correction

Catalog evolution now builds identity, source-coordinate and existing-key indexes
once for the invocation. Ordered loops make the actual compatibility decisions;
they append changed rows and required history into expanded arrays. Each family
merges its retained prior rows and replacements once. ID allocation and new
owner-local key numbers are computed in authored order. Native metadata IDs are
normalized consistently in lookup keys. No per-definition full-array removal,
full source reparse, or growing JSONB map concatenation remains in that planner.

Normalized source evolution matches definitions by native primary IDs and
affected-row counts rather than full-row anti-joins between expected and
returned copies. The unchanged-registration hash index remains a lookup
accelerator; exact original bytes are still compared before a registration is
treated as unchanged. Current-basis construction uses the `(doc_id, rev DESC)`
latest-document index and retains only current definitions, required source
archives and the latest document set. Historical projection uses the
first-future `before` overlay described above.

Original container definitions use one index per document. It retains the exact
original JSON fragment text, ordinal pointer and source hash; item chains resolve
through that index within the existing depth32 bound. Registration and evolution
do not reparse/hash the whole document for each container field.

Stored-value compatibility checks collect only changed existing constraints and
names. Unchanged engine-valid fields require no data census. For each affected
type, one query materializes its objects, expands property cells once, joins the
changed property metadata only where required/family/facet checks apply and
aggregates diagnostics in authored field order.
Retained-name collisions use one retained-key expansion. Required missing counts
come from object count minus present nonnull cells. New-field rebind/backfill
remains responsible for its actual values. String maximum length counts Unicode
scalar values; binary maximum length counts bytes. Tightening checks existing
stored values before publication. Finite relationship maxima trigger applicable
count checks; unbounded sides skip multiplicity scans while endpoint/permission,
positive-minimum and marker checks remain.

The planner's metadata work follows selected source bytes and definition/key/
endpoint counts, plus dictionary lookups and ordered merges. Changed-field
compatibility work follows the affected types' actual property/retained bytes
and changed-cell checks; it does not multiply full-object decompression by the
number of declared fields. Historical expected-record projections use the
explicit revision index and first-future `before` overlays; they do not replay the
historical planner. Current initialization takes the direct published-metadata
path.

The in-memory PGlite differential suite now covers 57 cases across current
planner/evolution data behavior, bookkeeping indexes, acceptance SQL parsing,
and length/budget boundaries. It does not execute PostgreSQL authority, trigger,
or concurrency behavior and is not a native release gate.

For scale intuition, 1,000 types with 10 fields each means about 11,000 type/field
definitions before keys and relationships. At 100–500 bytes of encoded metadata
per definition, that is roughly 1.1–5.5 MiB of payload before runtime object and
index overhead. This is a planning example, not a measured heap bound. The
16 MiB catalog wire cap, 65,536-definition cap and 128 MiB estimated application
cache budget apply independently. A 100-field type mix costs much more than a
10-field mix; type count alone cannot justify retaining repeated schemas or
object images. Original source and required history are retained once in their
canonical homes.

The final native and unchanged real-schema/stress qualification is still pending;
source analysis and in-memory SQL differential checks do not replace it.


### Native qualification correction: key-route observations

The first current candidate's native gate canceled inside key preflight. Source
inspection identified a retained JSON-array join between every distinct route
and every captured guard, followed by further route/observation array joins.
Those representations allowed a route-count squared comparison path despite
sharing the initial guard acquisition.

EXPLAIN also showed the planner reexecuting each globally grouped membership
and reservation subquery for every outer route, because the JSON input was
estimated at 100 rows and its joined aggregate at one row. Those subqueries are
now correlated aggregates over this route's existing hash index, with exact-byte
filters and the collision-budget gate before payload aggregation.

The corrected implementation reads canonical guard generations through the
existing composite primary key. The admitted entry already holds the shared
transaction-wide graph-writer gate, used by scalar and catalog key writers too.
Preflight therefore removes its repeated advisory-lock call and separate row-lock
pass; actual guard updates acquire their own row locks.
It builds exact-route observations once in a JSON object keyed by the complete
namespace and transport bytes; each ordered operation looks up its observation
by that exact key. Hash-collision budgets, original membership, reservation
conflicts, generation exhaustion and authored error order remain enforced.
The guard JSON copy and two inventory recounts are removed. Work follows
distinct routes, actual collision candidates and ordered uses, with indexed
physical-row probes and dictionary lookups; no route/guard array cross product
is needed. The unchanged eight-key 1,024-operation create/update and 1,024
disjoint-endpoint edge cases pass locally after this change. Both custom/generic
plan modes and the remaining full matrix still require the final campaign.

Capture has the same upstream exclusion: `object_group_begin_prepared` acquires
the writer gate and object/edge table locks before conditions and capture. The
private capture helper no longer reacquires those three locks or reads the
complete input scope twice to compare it with itself. One captured scope supplies
reader checks and planning. This removes a second full graph/object read while
retaining the original current reader and writer checks. Final native
qualification must exercise this consolidated path.

Capture retains its bounded plan array directly as `jsonb[]` after computing the
existing sum of original plan UTF-8 bytes. Publication inserts each plan with
scalar attempt/index/transaction columns. It no longer wraps all plans in a
second JSON array of SQL rows and reparses that array with
`jsonb_populate_recordset`. The same 32MiB retained-plan budget and affected-row
count check remain; there is no new payload readback.

### Catalog item source indexing

The complete native gate passed 66 cases and found five failures sharing the
1,000-type registration path. The raw-JSON source index extracted the module ID
from the complete module for every definition. PostgreSQL JSON extraction parses
that raw module again, producing work proportional to definitions times module
bytes. Module identity, ordinal and raw element array are now materialized once
per module before expanding definitions. Original element fragment text, source
hash and ordinals retain their exact meaning.

Scalar catalog preparation does not need an item-source lookup at all. The
expected-record builder and stored-value compatibility scan now select distinct
documents referenced by actual array/map fields and build one index only for
those documents. The compatibility scan parses its declaration and document
carriers once; scalar-only catalogs skip item-source indexing. Property projection
uses the already selected field rows without a second join to their source documents. This is a removal of unused work, not an increase in statement
time limits. Final native qualification must verify container interpretation and
the unchanged 1,000-type cases.

Focused native qualification after the lazy-index change passed both recursive
container cases and the unchanged 1,000-type complete-view case: 16,000
definitions and 12,456,454 wire bytes. The three distinct-type write cases now
reach a separate timeout in `runtime_owned_prepare_application`, during the
requested-definition-pin join. That query remains under analysis; the write
qualification and complete final campaign are still pending. This result does
not close the operation audit.

### Requested type-definition pins

The next native failure exposed a separate multiplicative join. A request with
1,000 distinct CREATE pins faced 1,000 current record types and 16,000 indexed
source definitions. The fresh-catalog plan estimated both the request and current
types at one row. Its requested-pin outer loop repeated the full type/source
mapping. Source identity columns used default text collation while native type
identity used `C`, preventing module/element index conditions; the explicit
`C` pin predicate also did not match the original default-collation pin index.

Source identity and pin columns now use the existing native byte-exact `C`
semantics. One partial current-record source-coordinate index supplies the
five-column native lookup; it changes schema-metadata storage, not object-write
index maintenance. The existing pin index is reused, without a duplicate index.
The first revised plan still scanned all current types for each requested pin,
so merely adding indexes was insufficient. Two correlated LATERAL projections
with `OFFSET 0` keep the planner from moving the complete mapping back inside
the request loop. This is a planning boundary, not a result limit or another
semantic verification layer.

Both forced custom and generic plans now perform the requested pin's source
index lookup followed by the five-coordinate native type lookup. Work follows
actual distinct requested pins and indexed matches (plus index access and the
existing ambiguity grouping), rather than requested pins times all types times
source definitions. An empty CREATE-pin set enters neither lookup. Original
source bytes, pin construction, all matching rows, ambiguity refusal and current
record filters remain unchanged. The three previously failing native cases now
pass: a 1,000-type single-create group, a 1,000-type update batch and a
catalog-first distinct-type create batch. Their retained log SHA-256 is
`1363e70e4704fa5bbad20385e6bafd263b460a6bef5b7d6ec657e4ff2adc29f3`;
the custom/generic JSON plan receipt SHA-256 is
`80749c28489e4604df976abb50a6f946ac8b39338d505328f6a141c5dd595a18`.
These focused checks used the installed local Weft 0.4.46 candidate and current
Truss source. Final installed-package qualification on both platforms and the
unchanged complete stress campaign remain pending. The plan analysis establishes
the access pattern, not a latency claim.
