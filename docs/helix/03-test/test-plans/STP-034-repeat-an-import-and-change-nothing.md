---
ddx:
  id: STP-034
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-034
      kind: informed_by
    - id: TD-034
      kind: informed_by
    - id: SD-002
      kind: informed_by
---

# STP-034: Repeat-safe imports

## Story Reference and Scope

US-034, TD-034, SD-002, TP-001 and CONTRACT-001/004/007. Tests are planned. Assert identity-based create/skip and durable reservation effects independently of request replay.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-034-AC1 | `second_load_skips_all_existing_identities` | First load creates 51; second load id reports 51 skipped with identical rows/versions/journal/source facts | `@covers US-034-AC1` | Native integration | `tests/import/replay.test.ts`; keyed objects and relationships |
| US-034-AC2 | `repeat_import_preserves_user_correction` | Corrected payload/version remain unchanged by original source repeat | `@covers US-034-AC2` | Native integration | Same file; user edit between loads |
| US-034-AC3 | `forbid_tombstone_prevents_object_resurrection` | Deleted object remains absent, key remains reserved and repeat skips without new journal effects | `@covers US-034-AC3` | Native integration | Same file; forbid profile |
| US-034-AC4 | `deleted_imported_edge_remains_reserved` | Same relationship/endpoints remain absent after repeat, with durable edge reservation | `@covers US-034-AC4` | Native integration | Same file; live endpoints, deleted imported edge |
| US-034-AC5 | `keyless_type_import_rejects_without_effects` | Specific no-primary-key rejection has no canonical/source/journal/reservation effects | `@covers US-034-AC5` | Native integration | Same file; accepted keyless type |
| US-034-AC6 | `allow_recreates_object_without_erasing_tombstone` | Reused absent key creates a new object and original tombstone remains | `@covers US-034-AC6` | Native integration | Same file; allow profile |

## Data and Additional Failure Probes

Configuration schedules: hold a mutation's shared catalog-head exclusion while an authorized `key_reuse` change waits; prove all records in that transaction use its admitted generation. Commit engine batch one, change forbid to allow before batch two, then require refusal before batch-two writer submission, earlier confirmed effects retained and remaining original indices unprocessed. A new explicitly admitted attempt may use allow. Repeat under an adopted transaction without library commit and under a snapshot predating the generation change; stale configuration cannot qualify current admission. Fail an administrative journal-mode transition and require no available partially installed producer profile. Verify exact attempted configuration provenance independently, not just final setting contents.

Lose the writer reply before any created result is observed: that index is attempt_unknown and untouched later indices are unprocessed. Fail rollback cleanup before any commit was sent: the batch is transaction_unresolved, not rolled_back or commit_unknown. Repeat under a host-adopted transaction and verify the library never manufactures a host commit observation. A later confirmed rollback proves no surviving effects but does not recover the lost application verdict. Require original-context resolution before a potentially overlapping retry.

Validate the [draft import report](../../02-design/contracts/bindings/truss-import-report-v0.1.d.ts) independently: duplicate/missing indices, overlapping batches, mismatched counts and a host-adopted committed disposition refuse. In an engine-owned two-batch attempt, retain the first confirmed batch and classify second-batch observed creations as commit-unknown after a lost commit reply. Confirmed rollback moves observed creations into the rolled-back bucket; later skips in that batch cannot certify surviving data. Object-before-edge execution still reports original input order. Processed with pending, unknown or rejected entries is not full-load success.

Progress-report probes distinguish original submitted order from execution phases, rejected from unprocessed and committed from pending/unknown. Inject one record-local validation failure and require confirmed savepoint rollback before continuation; inject serialization, cleanup failure and commit acknowledgment loss and require attempt stop without false rejected counts. Earlier confirmed engine batches survive, while adopted scopes never commit. Qualified identity repeat may create/skip but cannot report recovered original results or rewrite source facts. Full success requires every index resolved with qualified durability.

Use independently authored expected keys, raw SQL observer snapshots and unequal repeated payloads. Assert no hidden version/source/journal changes on skip. Include composite exact decimal keys, duplicate input identities, key change reserving old value, direct reserved-key create, concurrent import/delete and RLS-hidden identity. Lock revalidation must prevent two creators or resurrection under forbid.

Edge reservation fixtures independently distinguish: original deleted edge with live historical endpoints (forbid skips; allow may create); original reserved tuple with a now-deleted endpoint (forbid skips after authorization; allow rejects missing endpoint); missing endpoint without a reservation (reject); object recreated under the same business key with a fresh storage ID (new edge identity, old reservation retained); reversed source/target; same numeric endpoint ID under a different type; and same tuple under a different relationship/profile/epoch. Assert original source facts are never inherited by a new edge. Compare native reservations and lock identities to manually authored typed tuples, not the import/deletion encoder's own output. Profile changes cannot silently reinterpret old reservations or erase forbid history.

Interrupt an engine-owned import after a confirmed committed batch; repeat creates only missing records. Caller-owned import returns pending and full rollback removes canonical/journal/source/reservation effects while preserving earlier host work through savepoints. Transaction-fatal errors stop the import rather than count as ordinary rejected records.

## Executable Proof and Handoff

Report-wire configuration controls refuse a missing selectedConfiguration, numeric generation and unknown reuse policy. A digest-shaped inventory pin passes shape but requires independent installed/attempt/batch correspondence. Verify that an interrupted report retains the original selected policy after administration changes it; the same report cannot be relabeled with the new current policy. Zero submitted batches cannot manufacture successful configuration admission evidence.

Future command `bun test tests/import/replay.test.ts` requires implementation/harness and finalized identity, skip-validation and batch policy. Retain complete counts, per-record outcomes and independent state receipts. All six criteria block closeout; concurrency and interrupted progress probes support the protocol, not new acceptance criteria.

## Skip precedence regression cases

Add independently expected controls to `tests/import/replay.test.ts`: a live identity with now-invalid replacement nonidentity payload still skips and preserves correction/source/journal; malformed primary-key components reject before lookup; unauthorized identity rejects without exposing hidden contents; an absent identity with the same invalid payload rejects full validation. Duplicate input records with unequal payload create the first and skip later entries in declared phase order while reports retain original submitted indices. Under allow, a retained tombstone alone does not force skip when the live record is absent. These support existing replay criteria and do not add or narrow acceptance scope.

## Identity-separated payload supplements

Use an authorized live identity with integrity-valid payload bytes containing invalid replacement values/source members: skip without decoding/applying those members. The same payload for an eligible absent identity rejects after full creation admission. Forged payload digest or malformed required identity fails earlier envelope/identity admission. Identity-bearing payload disagreement cannot choose a different key/endpoint. Inspect original indexed object-before-edge execution and exact retained payload/source provenance. Unsupported declared payload format cannot execute artifact code or imply UMF invalidity.

## Decoded payload witnesses

Eligible object payloads require complete key values and profile-equality agreement with explicit identity: 1.0/1.00 equality preserves stored spelling; changed key value or missing required key value rejects without implicit fill. Duplicate authored values/source keys, wrong payload kind/version, ownership alias and malformed known source value reject creation. Empty map supplies no author/time/system; absent/null/empty known source states remain distinct. Unknown exact source values preserve meaning or explicitly refuse unsupported native encoding. Live-identity skip does not apply these replacement-payload checks.

## Import facade ownership supplements

runBatches owns its bounded engine commits and preserves earlier committed progress on later failure. applyInTransaction reports caller host_adopted or outer_engine_scope matching the actual handle; neither commits supplied scopes, and pending counts cannot become committed from a callback return. Inject failure after writer submission and require exact execution error plus interrupted indexed report, never null progress. Null report is permitted only for verified no-submission failures. Invalid envelopes fail before any writer. A surrounding engine rollback removes its pending effects just like caller rollback. Older report profile/digest selection cannot silently admit the new execution variant.

Import report shape receipt now has 18 cases including outer_engine_scope pending and a shape-valid committed-disposition forgery requiring semantic refusal. Combined declaration checking includes three import-facade negative consumer witnesses (read-only batch writer, invalid envelope plus progress, execution failure dropping explicit report/null). Runtime tests must additionally prove null means no submission, exact handle ownership matches the report and outer rollback clears pending records/source/journal/receipts. Type/schema success proves none of those native facts.

## Empty load and exact input digest supplements

After coherent admission, empty records reports processed with all zero counts and empty inventories, no writer calls/artificial batch or graph/source/journal effects, and unchanged supplied transaction lifetime. Context-observation failure is not empty success. Independently vary load/origin/pins, record order, identity components and complete payload bytes/profile: submitted digest changes while attempt/batch/runtime configuration changes do not rewrite it. Missing source versus explicit empty map creates the declared same empty source fact but preserves different original evidence; no unrelated required fields receive defaults. Digest collision/equality cannot authorize skip/replay or replace full retained input/identity verification.

Run `bun docs/helix/04-build/evidence/design-audit/check-import-payload.ts <installed-Ajv-2020-module-path>` for eleven decoded shape witnesses. They do not establish source/key/value semantics or the writer's validation order. Instrument decoding in native skip/creation scenarios to prove live/reserved skips never eagerly validate replacement payloads.

Run `bun docs/helix/04-build/evidence/design-audit/check-import-input.ts <installed-Ajv-2020-module-path>` for eight envelope cases. An undecodable payload is intentionally shape-valid here: with verified byte integrity and qualified profile, live/reserved identity skip avoids decode, while eligible creation rejects it. Unsupported key-number/total-primary/owner semantics need independent refusal.

Bounded import candidate now selects complete pre-writer envelope/artifact limits and stable objects-then-edges greedy batches constrained by record count and exact canonical record bytes. Skipped records still bypass deferred payload semantics; transport integrity/byte admission remains mandatory. Preserve original indices and prior batch durability on exhaustion. Exact resource-interruption result/diagnostic wire and native accounting remain design outputs.

Independent partition cases must cover interleaved objects/edges, exact count/byte boundary, one-record overflow, empty input, corrupt-but-skipped semantic payload versus invalid artifact integrity and mid-batch resource exhaustion. Assert fixed original-index partition, no writer on globally inadmissible envelope, no semantic payload decode on authorized skip, prior committed batches retained and no verdict on never-submitted records. Native bounds remain unqualified.

Import now has resource_limited with mandatory coherent interrupted progress and selected resource profile; unresolved application/commit/cleanup uses execution_failed instead. Pre-reserve complete bounded report storage before writers and preserve exact prior batch durability. Seven resource-result shape cases and strict consumers pass; schema-valid unresolved/false index inventories require semantic refusal. Native/report-memory/savepoint/cancellation qualification remains pending.

Run `bun docs/helix/04-build/evidence/design-audit/check-import-partition.ts`: seven independent synthetic-capacity witnesses pass for empty input, global phase order, exact byte/count boundaries, no reordering for packing, single-record global refusal and legal mixed-phase chunk. Input bytes here are declared synthetic sizes; qualify actual canonical tree measurement separately. Preserve original-index reporting despite processing order.

Report-capacity witnesses must verify 0/1/1,000 input bounds and independently compute 13,344,576 bytes at the reference maximum. Test maximum identity/definition/recovery/diagnostic alternatives and one-byte-over slot before writer admission; no truncation/hash substitution. Force producer overrun after writer submission and require preserved original progress/integrity recovery rather than incomplete public report. Canonical report reservation alone does not prove physical allocation bounds.

Reference-capacity command: `bun docs/helix/04-build/evidence/design-audit/check-import-report-capacity.ts` reads the original resource artifact and passes six independent expected capacities: empty context, one record, 1,000-record maximum, count-limit refusal even when bytes fit, noncanonical count and extreme exact-integer count. This verifies formula/profile agreement only; worst-case lossless producer and physical allocation evidence remain required.


## Original-index interruption and settlement schedules

Supplement the existing replay criteria with an independently authored five-record request in submitted order [edge 0, object 1, edge 2, object 3, object 4]. Select a fixture batch profile allowing two records with every exact byte ceiling independently satisfied; the objects-before-edges execution order is [1,3,4,0,2], with batches [1,3], [4,0], [2]. Author valid original endpoint dependencies and complete expected canonical/source/journal state before execution. Input/report indices remain original submitted indices, never execution offsets or positions in a sorted report.

Run each fault separately under engine-owned and supplied-scope execution. After the first batch completes, interrupt before any second-batch writer, after its first writer, during the second record's savepoint containment, during batch rollback and around actual engine commit acknowledgment. Observe native command termination, local containment and enclosing settlement independently. No-submission remainder, confirmed rolled-back submitted outcomes and unknown attempted outcomes must remain distinct. Prior engine batches retain only independently observed committed durability; supplied-scope completed batches remain pending unless the actual containment profile rolled them back. A lost reply cannot promote pending state to committed or trigger automatic replay.

For confirmed resource containment, independently reconcile all five original indices exactly once between outcomes and never-submitted remainder, derive counters and reject any unresolved outcome/batch in resource_limited. For unavailable rollback/commit/termination evidence, require execution_failed with retained original interrupted report and recovery custody; report null is invalid after any writer submission. Inject a false original index, execution-order index relabeling, omitted prior batch, duplicate outcome, fabricated rejected never-submitted record and stale successful creation after actual rollback. Each must fail report admission without repeating writers or repairing from current live records. The native harness must record the exact selected savepoint/adapter/resource profile and original batch boundaries; these schedules remain not_run and do not select a deployment profile.


## Repeat while original settlement is unknown

Lose the original engine commit response while independently retaining attempt and native recovery identity. In separate schedules, pre-create the same business identity with another writer, let a competing writer create it, and commit the original creation then independently delete it before a later invocation. A newly admitted attempt's live/reserved create-or-skip result must not settle the original attempt; neither presence nor absence is a recovery oracle. Repeat exact load ID/input bytes on a separately admitted resource and verify distinct attempt custody, current configuration/authorization and immutable source/journal association. Current hidden identity cannot be disclosed through either report.

Attempt the same invocation on the original quarantined connection and require executor admission refusal; a newly admitted unrelated resource cannot clear the original obligation. Withhold original settlement evidence and preserve unknown recovery even if the later attempt succeeds. Supply qualified original committed/rolled-back/termination evidence separately and verify only the original obligation gains qualified appended resolution evidence; the exact originally returned report stays unchanged. No automatic retry, host transaction termination or provenance rewrite is permitted. These independent schedules supplement existing replay/atomicity criteria and remain not_run.


Retain and compare the original interrupted report bytes before and after each recovery observation. Append committed/rolled-back/termination evidence separately, verify exact original attempt/batch/index association, and reject foreign/newer-attempt evidence. Include host commit after a record-local savepoint rollback, confirmed native termination with unknown commit and one settled batch alongside another unresolved batch. No derived view may relabel rolled-back savepoint effects as committed or mutate the original report; unresolved membership stays explicit. These checks exercise selected host recovery tooling without assuming a new import recovery method or report wire.


The [import interruption/recovery case inventory](../../04-build/evidence/design-audit/import-interruption-recovery-case-inventory.proposal.json) assigns IR-01–IR-06 to the supplemental schedules above. It is an unselected native test allocation, not the complete US-034 corpus. Before running the existing planned command, the harness must provide the listed original profile, byte, state, authority, termination and settlement observations; absent observations cannot produce a passed receipt. All six primary criterion tests remain separately required.


Plan NI-01/02 for a selected network host: lose acknowledgment after one runBatches batch commits and another becomes unknown, then invoke a new identity-based import and prove it cannot replace the original report or settle its native recovery; invoke applyInTransaction with successful and failed records, then lose outer commit acknowledgment and preserve original pending/unknown report until qualified original outcome observation, without presenting an atomic group receipt or treating loadId as exact-report idempotency. Compare independent original/later reports and native committed state. These are planned integration cases; no import receipt or new wire field is selected.
