---
ddx:
  id: STP-040
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-040
      kind: informed_by
    - id: TD-040
      kind: informed_by
    - id: SD-003
      kind: informed_by
---

# STP-040: Atomic groups

## Story Reference and Scope

US-040, TD-040, SD-003, TP-001 and CONTRACT-004/007/009. Tests are planned. Request-free atomicity is independent of gated receipt replay.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | Setup |
| --- | --- | --- | --- | --- | --- |
| US-040-AC1 | `valid_alias_group_has_ordered_results_and_one_origin` | All effects commit together; result order matches input and journal shares xid/origin with exact version progression | `@covers US-040-AC1` | Native integration | `tests/mutation/groups.test.ts`; parent/child/edge aliases |
| US-040-AC2 | `invalid_third_operation_rolls_back_entire_group` | Error names index 2/inner kind; no canonical/key/marker/journal/tombstone/receipt effects survive | `@covers US-040-AC2` | Native integration | Same file; preflight and persistence-failure variants |
| US-040-AC3 | `opposed_order_groups_acquire_same_sorted_lock_order` | Both request-free groups complete without PostgreSQL deadlock, retaining their own result order | `@covers US-040-AC3` | Native concurrency | Same file; independent initially empty transactions and explicit barriers |
| US-040-AC4 | `catalog_acceptance_and_group_have_serialized_legal_schedules` | Acceptance-first makes old-revision group refuse; group-first blocks acceptance while original catalog custody remains; earlier host-savepoint rollback invalidates removed pending work | `@covers US-040-AC4` | Native concurrency | Same file; observed lock acquisition/acceptance barriers |

## Data and Additional Probes

Use independently expected rows/versions/journal and observer connections. Include owned-deletion closure expansion between discovery and lock, re-key swaps/collisions, stronger delete locks, single/group overlap, mixed no-op operations and final minimum participation. Forward/duplicate aliases and empty group refuse without effects. Barrier/lock-state observations establish actual overlap; timing sleeps alone cannot prove concurrency.

Opposed-order proof excludes arbitrary prior host locks. Include host-induced deadlock as a separate retry/rollback probe without pretending it satisfies AC3. For caller adoption, successful group is pending; caller rollback removes it and failed group preserves earlier host work. Final invariant errors retain last-affecting index and all violation paths.

## Executable Proof and Handoff

Future command `bun test tests/mutation/groups.test.ts` requires implemented harness and finalized shared protocols. Pin layout/lock/adapter/isolation/roles, retain barrier traces and native deadlock SQLSTATE outcomes. All four criteria block closeout. AC4 now explicitly follows head-lock exclusion; no mid-lock acceptance is a valid test schedule.

## Public facade supplements

Select group handles inertly; request-none must work with no receipt namespace/storage installed when the selected request-free profile is otherwise qualified. Apply in an active outer engine/caller scope and require pending new results, not committed. Confirm one ordered result per input including no-ops and exact profiled inner errors/index attribution on failure. Incomplete planning/resource observation returns no successful partial result. Operation-local rollback preserves earlier host work and all group graph/key/journal/source/receipt effects disappear together.

Combined strict declaration checking includes `truss-mutation-group-capability-v0.1.typecheck.ts`: independent consumers reject standalone aliases, premature in-transaction commit, same-transaction replay labeled committed and failure with success payload. These are type distinctions only; native context and effects require the cases above.

Complete result wire checks use `check-group-result.ts` and independently authored operation/replay fixtures. Twenty structural expectations cover create/change/no-op/delete and same-transaction versus committed-receipt replay, including empty group/event and false replay durability rejection. Wrong input order, duplicate native event and forged committed disposition intentionally remain shape-valid semantic/native controls. Verify original complete input/result/alias/deletion/event correspondence and actual original commit/authority separately; schema pass never authorizes replay.

Unified planner lock-order controls follow the current CONTRACT-009 table rather than the retired seven-level shorthand. Mix single writes, request-free/request-bearing groups, re-key, owned deletion and concurrent catalog/policy/namespace administration. Independently verify full earlier guard sets before business/root/row locks and contained restart on newly discovered earlier owner/root/bucket; request-free omission never skips required policy admission. Native writer coverage and the selected advisory versus bucket observation profiles are separate prerequisites. Existing declared wire/type checks prove shape only, not complete closure/final invariant or lock ordering.

Resource profile probes use the exact CONTRACT-009 reference artifact. For each counter independently expect exact-bound admission and one-over resource refusal; force depth/node/closure/guard/simulation exhaustion without treating result paging or SQL LIMIT as complete discovery. Exhaust after graph/key/journal effects and independently verify confirmed savepoint rollback of every effect; cancellation with unresolved native cleanup is an outer execution failure. A long host transaction after a successful pending call retains its guards, with no deadline-triggered commit/unlock. Native actual scan/buffer/cancellation evidence is separate from logical counter evidence.

Deadline/containment boundary: hold native work beyond the 30,000 ms candidate invocation budget, then permit rollback during the independent 5,000 ms containment observation. Confirm no effect survives and only then expect resource unavailable. In the alternate barrier schedule, withhold termination confirmation past containment allowance: expect outer unresolved execution, original recovery reference and quarantined unreleased connection, with no automatic reexecution or whole host transaction termination. Verify both schedules independently rather than treating cancellation acknowledgment as rollback.

Composed value/group resource tests use independently counted roots and canonical bytes. A value within its own limits exceeds whole-group depth only after envelope nesting; many individually valid values exceed aggregate input/result limits; one value exceeds its scalar/collection bound while aggregate group bytes fit. Require the named failing profile/counter and whole-operation refusal, without tag conversion, profile substitution or truncation. Envelope expansion is admitted before allocation/native submission and failure after effects is fully contained. Validity of an individual carrier never qualifies the containing operation's decoder/work profile.

### Request-free dispatch controls

Under an independently selected ordinary-group deployment without receipt storage, instrument the full admitted command/procedure path. A request-none invocation performs no request namespace lookup/lock, receipt read/write, replay digest or retention-clock work, while retaining all original policy/catalog/operation/touch/journal/finalization controls. A unavailable or hostile receipt-only service must not be invoked or cause ordinary readiness failure. This is not permission to bypass unknown installed-policy objects or an ordinary group producer failure.

Invoke identical request-none operations twice in separately confirmed transactions: independently expect each operation's normal second-invocation meaning, including unique-key conflict, stale-version refusal or valid new effect/no-op as appropriate. Never expect replayed solely from equal input. Inject lost completion after submission and lost commit acknowledgment; require original recovery custody and no automatic replacement invocation, receipt lookup, manufactured request identity or receipt_expired result. Also mutate the caller request envelope after admission and verify branch choice remains original. Cases compare original command traces and complete graph/key/journal/result state, not just the response discriminator. Request-present replay qualification remains STP-043 work.


## Concrete final-state relationship replacement

Start from the independently authored reference M03 graph: Account A has AB and AC, Item D is unlinked, the Account's target maximum is two, each Item's source maximum is one, and both lower bounds are zero. On a fresh isolated copy submit one request-free atomic group: first create A→D, then delete original AB. Independently expected final membership is exactly AC plus the newly assigned AD; A/B/C/D all remain live, B becomes unlinked and no independent-lifecycle target is deleted. The intermediate simulation has three targets for A, but the complete final graph satisfies the selected cross-row group invariant. Do not classify the first operation as the standalone M04 third-target refusal; CONTRACT-009 qualifies final cross-row checks for the group while each operation still has its complete field/type/key/endpoint/authority admission.

On a separate fresh original graph submit the reverse ordered group, deleting AB then creating AD. Both groups produce the same logical final membership, but retain their own original operation order, actual newly assigned edge identity, ordered semantic results, version/source/origin and complete journal/metadata references. Do not require equal generated IDs, sequence order or complete receipt bytes across independent executions. Original AC's edge identity and unchanged endpoint record state must remain exact. No provisional intermediate graph is published outside the original transaction.

Negative controls omit deletion of AB (invalid final third target), delete an unrelated edge (same final violation), use a missing or wrong-typed D, or create a second incoming source for an already linked Item. Require indexed failure according to the selected immediate-versus-final violation rule and confirmed complete group rollback, preserving original graph/key/reservation/source/journal state. An unknown containment/commit outcome retains original recovery rather than a rollback assertion. Inspect complete finalizer/touch participation: deleting AB cannot hide a required dirty A/D/B scope or omit one of the two operation results.

Hold the group pending under an adopted transaction: its original admitted scope sees the complete pending final graph, while an independent committed observer retains AB/AC until host settlement. Host rollback restores the original graph; host commit publishes only the final AC/AD membership. Native trigger firing/deferred constraint timing and protected producer orchestration must independently realize this result without changing caller transaction constraint mode. These planned cases supplement US-040 atomicity/rollback criteria and the existing lock/concurrency corpus; standalone max violations still refuse.


For the replacement case, distinguish original semantic order from admitted native dependency order. The fixed marker profile may remove AB before inserting AD; do not require a physically stored third marker as evidence of final-state support. Capture the complete preplanned native effect ordering and original semantic attribution independently. A forced implementation that cannot retain both ordered results and full original history correspondence refuses qualification; silently swapping public operation indices or dropping a deletion event fails. Plain-SQL caller flags or future-delete promises never grant a finalizer exemption.


Independently enumerate marker expectations for outgoing replacement: source_max=1 produces target-side B/C/D markers as applicable; target_max=2 produces no source-side A marker. Assert the larger maximum through its separately qualified final invariant producer, not marker PK success. Add an independently prepared Account E and the incoming replacement create E→B/delete AB: final AC/EB has target-side C/B markers, and native dependency ordering removes the original B slot before inserting EB. An omitted deletion refuses the complete group. Compare complete old/new marker tuples and canonical membership under target exclusion, original semantic indices/results/history and rollback baseline. These controls prevent a maximum-one-only receipt from claiming maximum-two native enforcement.


Qualify the selected maximum-two native count separately from EL marker equality. Hold A with one edge and synchronize A→C versus A→D writers on independent connections; exactly one may consume its last target slot. Hide the first edge from the application role and require protected counting to include it without disclosure. Force a stale held snapshot before lock contention and require refusal/retry rather than count-based overcommit. Parallel edges count as occurrences; zero-degree endpoints remain checked. Remove the protected count dependency or one ordinary-writer invocation path and require readiness/enforcement-claim refusal. The existing marker-only profile cannot pass maximum-two coverage through its own tests. These planned controls retain full original scope/guard/count/canonical/marker/history and settlement observations.


Maximum-guard evidence controls distinguish complete degree 0/1/2 from at-least-3 violation. Feed a two-row prefix of a larger degree and require refusal/unavailable rather than success; feed a third distinct edge and permit only bound violation, never an exact total or successful full-scope proof. Duplicate the same edge's transport row and require integrity refusal, not a fabricated degree. Vary user LIMIT/predicate/hidden-row visibility and reject scope narrowing. The existing complete canonical/marker/current-union observations remain required on successful finalization; an early violation witness cannot replace them or qualify native scan bounds.

### Concrete participation-query integration controls

Use the [private observation query](../../02-design/contracts/reference-participation-observation.proposal.sql) and [independent degree oracle](../reference-participation-expected.proposal.json) only after original protected scope/visibility/lock and producer admission. Resolve all five non-null native parameters from actual registry/endpoint observations. A guessed positive ID, NULL parameter, wrong type/relationship or stale scope must refuse before query invocation; a zero count from an unmatched parameter cannot establish an empty participation set.

PQ-01 executes both sides against independently installed zero/one/two/three/five-occurrence native cohorts, including parallel edges with different edge identities. Compare each returned saturated count with the independently declared oracle. Place additional edges on the same source with other targets and on the same target with other sources; verify that pair-only filtering cannot pass. Place irrelevant edges on other relationship/typed scopes and verify exact scope isolation. Native source visibility must include hidden required edges without revealing them in application output.

Current source-epoch0.16 qualification limit: the original unique `edge_out`
index excludes two canonical edges with the same `(source_id, rel_type_id,
target_id)`, even with different edge IDs and properties. The
[local native boundary receipt](../../04-build/evidence/design-audit/pgserver-edge-occurrence-profile.json)
records PostgreSQL16.2 SQLSTATE23505 from that exact index, preservation of the
first occurrence, and successful distinct-relationship/distinct-target controls.
Its administrative fixture is not admitted catalog or protected-writer evidence.
The same-tuple parallel part of PQ-01 is therefore unavailable on this profile,
not a skipped pass or proof that DISTINCT counting is sound. Keep the full planned
occurrence semantics and qualification gate. Dropping the index to seed a fixture
would change the installation and cannot qualify source-epoch0.16. A future
parallel-capable layout needs its own reviewed source/target migration,
uniqueness and association/key semantics, count enforcement and compiler/security
qualification. No such layout is selected by this receipt.

PQ-02 independently observes the statement's actual parameter types, one-row/two-column text descriptor, exact field names and complete completion/cycle. Accept only canonical count text outgoing 0,1,2,3 and incoming 0,1,2; NULL, leading zeros, signs, exponent text, out-of-range counts, wrong descriptor, duplicate/missing row or truncated transport refuses the whole observation. At saturation assert at-least semantics, never an exact larger degree. Original failed native execution follows containment/recovery rather than a fabricated count.

PQ-03 covers zero-degree surviving endpoints after delete, deletion of an endpoint after its incident edges, and catalog tightening across complete actual endpoint inventory. This query does not enumerate affected endpoints: omit one registry/enumeration scope and require operation/profile refusal even if all invoked counts pass. Retain complete typed scope custody and separate canonical/marker parity and current-union finalization. A caller cannot choose limits or replace the private query with a visible subset.

PQ-04 combines final-state replacement, last-slot contention and a lock-wait stale snapshot with the original count invocation. Independently observe producer/role/dependency and native work/peak/transport admission before effects. LIMIT bounds returned witness cardinality only; no native scan or allocation bound is inferred. Missing complete visibility, count dependency, ingress reserve or original actor correspondence refuses the affected capability. All cases remain planned; no native result is supplied by the mathematical oracle or source SQL.

PQ-05 exercises the selected independent [source](../../02-design/contracts/reference-outgoing-participation.proposal.sql) and [target](../../02-design/contracts/reference-incoming-participation.proposal.sql) observations, each with three admitted parameters and one canonical text result named saturated_count. Install Accounts with no Items, and Items with no Accounts; catalog tightening must still enumerate and check every actual zero-degree endpoint without a fabricated opposite endpoint. Reuse the corresponding degree oracle and full termination/descriptor controls. Give source and target scopes identical numeric endpoint IDs under distinct typed identities and require separate custody/deduplication. Deleting an endpoint through an admitted operation preserves its original finalization scope. The earlier paired-query PQ controls apply only when both scopes actually exist; they cannot substitute for these complete independent forms.

PQ-06 compares the [independent replacement-scope oracle](../reference-participation-scope-expected.proposal.json) with the actual protected extractor. From separately committed AB/AC, create AD then delete AB yields four original provenance occurrences and three distinct invocations: source A count two, target D count one, target B count zero. Resolve fixture labels to independently observed typed identities without inventing native IDs. Preserve both original A occurrences after deduplication; drop old B/new D, merge opposite typed sides or omit a finalized surviving operation and require complete refusal. Unchanged C belongs to the original committed baseline rather than an invented current-group effect; its separate canonical/marker/current-union obligations remain intact.


## Host-savepoint rollback and catalog acceptance

Create an earlier host savepoint S, then execute a successful adopted group and release its internal call savepoint. Hold its pending result privately and independently observe catalog share custody. Start catalog acceptance on another connection and prove its actual wait. Roll back the host to S: confirm complete group graph/key/journal/receipt/report effect removal and invalidation of its original capture. Where the selected native profile proves the catalog lock was first acquired after S, acceptance may now proceed even though the outer host transaction remains live. A later host COMMIT cannot settle the removed pending group or publish its provisional identifiers.

Repeat with catalog custody acquired by earlier host work before S: rollback removes the group but does not imply that earlier custody vanished; independently observe acceptance still waiting until that custody ends. Repeat with lost rollback acknowledgment and preserve original unknown/recovery classification rather than declaring lock release from client intent. A new group after confirmed rollback must obtain the current catalog/context and a fresh operation ordinal; no old result or cached lock pin supplies admission. These planned controls consume the existing TD-044/STP-044 lifetime protocol and do not authorize Truss to issue whole-host rollback or restart.
