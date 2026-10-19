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

The source review is complete for these release paths; functional and performance qualification remains pending. C83
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
writes and expected-version/count checks. Legacy and historical paths remain
separate because this qualification does not extend their supported boundary.
The stored compact-plan desired hash remains for historical hydration compatibility;
the ordinary producer does not serialize and hash the image again to prove its
own construction. This is a compatibility field, not a new admission transcript.
