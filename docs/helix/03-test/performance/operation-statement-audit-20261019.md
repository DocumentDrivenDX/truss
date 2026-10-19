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

The structural review is being completed against the current source; qualification remains pending. Earlier C83
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
| Deferred entity checks | Complete attempt and live authority at commit | Object and transition events each replay object/key/journal proof for the same owner | Consolidate engine-owned work at mandatory attempt settlement; issue current actor once there, retaining separately supported legacy paths |
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
receipt readers now select compiled historical dependencies by revision/type
rather than rebuilding and scanning the complete catalog for each object.
The stored compact-plan desired hash remains for historical hydration compatibility;
the ordinary producer does not serialize and hash the image again to prove its
own construction. This is a compatibility field, not a new admission transcript.


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

Canonical before/after metadata history is product data required by ADR-007.
Property deltas, exact original import bytes, actual source metadata, and ordered
wire hashes remain for their public meanings. They are not a license to keep
parallel expected copies or reread every private write to prove correspondence.
Fresh imports and imports retained by earlier releases both read the immutable
canonical source row; existing ledger copies need no rewrite during upgrade.

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
| Install / upgrade | One-time selected runtime DDL, source/index migration and owner/ACL inventory. Work follows runtime objects and retained schema revisions; never charge this to every record. Existing data is retained. |
| Accept catalog | Current revision/permission check, source publication and actual catalog deltas atomically. Cost follows source and definitions/effects; no table/index per user type. |
| Adopt / status / group context / schema revision | Constant command count, small current installation/transaction/catalog observations. No object scans. Host containment is separate from payload work. |
| Get object / exact key lookup | Typed primary-key or exact-byte key-bucket index probe, actual owner/root permission and bounded payload: O(log D + P), plus bounded collision-bucket evidence. |
| List / compiled query | Select immutable binding, lower once, read bounded complete source bags, current authorization before/after, and decode returned data. Scalar scan follows selected bag rows; joins/sorts follow query semantics. Complete-entity attribution resolves indexed creation/latest transition and actor without semantic/history replay. Descriptor lookup is a dictionary built once per query. |
| Create / changed update | Admit supplied values once against loaded schema. Write selected objects, changed key routes/reservations, history and results atomically. Work follows supplied/affected bytes, affected key rows and required history; table/index operations add log D. No key-stage object-image multiplication. |
| No-op update | Validate supplied changes and expected version, retain the existing version/timestamps, produce no history delta. Group completion and current authorization still apply. |
| Edge create / retarget / unlink | Selected typed endpoints and distinct business-key routes, version/count DML, actual edge metadata/history. No full endpoint property copies. Edge pages collect payloads with an incremental byte total and deduplicate root dependencies once. |
| Reparent / delete cascade | Observe the bounded connected component once; traverse actual owned adjacency, update/remove A affected nodes/edges, produce required history. Repeating a reparent may necessarily touch the subtree again; copied work must follow those actual effects, not all unrelated G members. The mixed planner uses one invocation-local indexed working relation; each operation projects only its changed members and root/endpoint witnesses. The initial snapshot is retained once, and complete final graph projection occurs once. |
| Import | Identity/key preflight, one atomic admitted group, one batched source attachment. Original record bytes and one immutable source fact per created entity are retained. Decode the operation group once; source/field and primary-key component projections aggregate once. Original payload envelope validation and execution each decode record bytes, giving two linear passes rather than one. |
| Read history / source | Indexed retained coordinates, actual requested event/source bytes and their current historical readers. Returning H bytes necessarily costs O(H); historical event validation buffers semantic events and serializes each array once. Historical property readers use compiled revision/type/property metadata; a returned property does not reconstruct the full catalog. Full transition replay is removed, while original edge endpoint/root policy is checked once per group. Ordinary entity attribution must not read H just to return actor names. |
| Preconditions | Capture the actual selected object cut and acquire exact key routes, then evaluate current conditions in authored order. Predicate-key bytes are indexed by condition ordinal; ordered failures aggregate once. Preserve condition failure precedence and current dependency authority. |
| Receipt / reached | Exact retained receipt and transaction inclusion, distinct retained dependency readers. Modern receipt authority uses indexed results plus compiled revision/type dependencies once, rather than parsing the complete group for each operation. |
| Feed / acknowledge | Indexed writer position, whole transaction facts and actual required revision prerequisites within explicit caps. Preserve original facts; no per-property configuration discovery. Acknowledgement changes the selected consumer position atomically. |
| Traverse | Visit the selected bounded frontier and incident edges using typed indexes, bounded result bytes, current resource readers; no scan of unrelated types or reinterpretation of every stored property. |
| Finish / commit | Small current custody/version/receipt checks, one complete ordered result inventory, distinct actual dependency readers, applicable bounded graph constraints. No second engine execution or private event-by-event proof program. |

The mixed planner creates one temporary working relation and two adjacency indexes per
invocation, drops it on completion, and retains no cross-call state. Initialization
and final projection follow G; indexed point access and actual adjacency/effects
follow A (with index access costs). Shared scope discovery uses recursive set
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
