---
ddx:
  id: STP-009
  type: story-test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: US-009
      kind: informed_by
    - id: TD-009
      kind: informed_by
    - id: SD-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-006
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
    - id: CONTRACT-010
      kind: informed_by
    - id: CONTRACT-011
      kind: informed_by
    - id: TP-001
      kind: informed_by

---

# STP-009: Find an object by its key

## Story Reference

US-009, TD-009, SD-002, CONTRACT-001/004/006/007/009/010/011 and TP-001. Test files and cases below are planned, not implemented or passing.

## Scope and Objective

Prove exact key identity and transactionally enforced canonical-row uniqueness. Plan native key-row uniqueness controls for each selected layout/profile. Arbitrary object SQL deriving correct keys is a separate advertised enforcement guarantee and must not be inferred from a key-row constraint or the protected-writer candidate.

## Acceptance Criteria Test Mapping

| AC ID | Planned failing test | Asserted behavior | Citation | Primary layer | File/setup |
| --- | --- | --- | --- | --- | --- |
| US-009-AC1 | `duplicate_customer_key_is_atomic` | Second create conflicts; first remains; second object/key/journal effects are absent; raw duplicate key-row SQL also fails | `@covers US-009-AC1` | Native integration | `tests/keys/native.test.ts`; accepted Customer key, two independent clients |
| US-009-AC2 | `decimal_key_lexemes_compare_equal` | `1.0` and `1.00` derive the same key bytes; second native insert conflicts without changing original stored value | `@covers US-009-AC2` | Native integration | Same file; independently expected canonical `1` |
| US-009-AC3 | `offset_distinct_keys_remain_distinct` | Same instant authored as `Z` and `+02:00` creates two distinct canonical rows; each lookup retrieves its own object | `@covers US-009-AC3` | Native integration | Same file; explicit RFC3339 equivalent-instant fixture |
| US-009-AC4 | `absent_component_has_no_key_row` | Missing composite component produces no key row; object persists and report identifies missing component | `@covers US-009-AC4` | Native integration | Same file; two-component key with one absent property |

## Executable Proof

Planned command: `bun test tests/keys/native.test.ts`. Supplementary `bun test tests/keys/canonical.test.ts` covers pure fixture bytes. Both are future commands until files and native harness exist. Every actual criterion test carries its citation. Run on every advertised adapter/server profile; unavailable targets remain unverified.

## Data and Setup

Binding admission cases independently check stable IDs/qualified Records, duplicate/reordered/foreign properties and wrong source definition pins. Portable bindings cannot alter upstream equality/nullability or replace source key IDs with binding IDs. Storage bindings exercise reject/participating/nonparticipating null separately from missing reject/omit_and_report, including present-null versus absent controls. A profile pin referencing an unavailable registration or artifact-supplied executable code refuses; declared enforcement/primary labels cannot manufacture total identity. Compare exact accepted binding provenance and missing/null report paths across revisions.

Mixed-component participation witnesses independently expect: allowed absent plus participating null omits the whole tuple; nonparticipating null plus rejected absence rejects; omitted absence plus invalid present value rejects; two participating null components produce a complete two-component key and collide with an equal complete tuple. Verify every omission reason in binding order, with no shortened key. Repeat the cases during backfill and an update from complete to omitted: old key removal, record change, journal and any selected reservation effects commit together or all roll back. An unavailable equality/null registration refuses before data effects even if the candidate key would be omitted.

Independently inspect held-to-omitted reservation bytes, omitted-to-omitted absence of reservation writes, omitted-to-held collision/refusal and held-to-different atomic replacement. For held-to-equal, change decimal spelling from 1.0 to 1.00: preserve one complete key row and no new tombstone while applying the qualified lexical value/version/journal change. Exercise both reuse configurations, removal-only bucket planning and injected failure after key removal but before journal insertion; no partial old-key loss may survive rollback.

Profile separation controls explicitly select portable_identity versus Truss storage_uniqueness. AC4 uses absent-allowed component definitions plus a sparse storage binding; the object persists with no key row/report, while the same absence on a required property rejects atomically. AC3 uses the storage binding's authored timestamp-text comparator, not portable tuple temporal admission. Portable core-Key fixtures reject absent/null/temporal input according to the upstream subset. A sparse binding cannot claim a total UMF target Key or satisfy an incomplete import identity; unsupported dependent operations refuse without rewriting source ideals.

Portable native transport fixtures independently use prefix `umf-key-tuple-v1:hex:` plus lowercase complete owner tuple bytes. Uppercase, odd-length hex, valid-hex/invalid-framing, changed receipt source/key/field order, digest-only truncation and different selected transport refuse. Boundary cases measure the actual prefix-plus-hex bytes at/over the selected maximum and leave no effects on refusal. Compare native equality/unique/index/lock/reservation paths with independent exact bytes; source text collation or decoded numeric spelling must not redefine this carrier. These are candidate-profile tests, not legacy-key qualification.

Candidate compact decimal profile controls use ADR-006's independently authored tuples, not expected values produced by the codec under test. Assert `1e2`/`100.00` collide mathematically while exact stored tokens remain distinct, signed-zero key equality, and `0.00120`/`1.20e-3` equality. Ordering witnesses include 2 versus 10, negative 10 versus negative 2, and adjacent coefficients above host-number precision. A huge exponent fixture must remain bounded or refuse under its selected profile without expanding zeros; it does not qualify native storage. Compare actual native key/reservation bytes only after the new component encoding and supported domain are selected. Lexical-only edits preserve the derived key while producing the declared value/version/journal change.

Use independently specified canonical outputs for decimal signs/zero/exponents, escaped composite strings, binary and timestamp offsets. Observe native object/key/journal rows through a separate connection after commit or refusal. Concurrent duplicate creates use barriers; require exactly one success and one constraint failure. Do not derive expected key text using production canonicalization.

## Edge Cases and Failure Modes

Lookup mapping controls pin the exact key encoding profile. Supply the same local number with a newer/different encoder digest and require unavailable before native lookup; no current-profile fallback or false not_found. Reorder/rename the authored key while preserving its stable identity and verify mapping continuity; use a held snapshot predating the accepted revision to verify one coherent catalog/key/object observation. An arbitrary historical revision applied to current native key rows cannot qualify this direct lookup. Historical business-key reconstruction would require a separate designed profile and is not inferred from snapshot or retained record carriers.

Decimal-byte profile cases manually specify the four-string component and outer composite escaping. Inner-array flattening, extra whitespace/BOM/newline, exponent `-0`/leading-zero aliases and raw token substitution refuse canonical admission. Distinguish a numeric-looking text component from the decimal equality component. Migration fixture has two previously distinct spellings becoming equal plus a retained reservation: activation reports the complete collision inventory and leaves original keys/reservations unchanged. Historical profiles remain recoverable; a profile toggle cannot silently rebuild keys or change lock identities.

Key-profile probes distinguish absent, explicit null and empty string; unsupported null/family semantics refuse without effects. Test one delimiter-containing component versus several components, exact quote/backslash/control/Unicode composite bytes, mathematical numeric equality with distinct retained spelling and authored timestamp offset inequality. A short exponent expanding beyond the output bound refuses atomically even if legal for scalar storage. Changed encoding/definition pins cannot reuse persisted keys/tombstones without the reviewed rebuild. Native null/collation behavior is independently qualified, not inferred from a pure-code fixture.

Key-changing update collision leaves old object/key/journal state; deleting object removes its keys; adding a key over duplicate existing values refuses the entire catalog revision with all affected objects reported. Parameter-injection text remains data. Restricted roles cannot discover hidden objects through lookup. Explicit null, unsupported scalar families, normalization and maximum length remain gated shared policy cases, not silently treated as missing.

## Build Handoff

Guard-statement spike controls distinguish a real no-value-change native guard UPDATE from an advisory lock/SELECT, and a separate post-exclusion observation from a pre-wait CTE snapshot. Exercise two operations in one adopted transaction and observe its own earlier key/guard changes. Force a first-guard insert identity collision and require safe retry without suppressing native conflict into empty membership. A skipped import/no-op may touch the internal guard but must not increment graph version, emit graph/feed facts, rewrite source or increment logical membership generation. Savepoint/transaction rollback restores actual membership/generation; host transaction lifetime remains host-owned.

Bucket identity supplements verify exact namespace array order/UTF-8/canonical strings, production built-in SHA-256 identity and 32-byte routing digests. Force both namespace and key digest collisions in a separate test profile: distinct full namespaces/keys coexist, while equal full identity conflicts. No full key appears in a B-tree key/include payload. Native generation at its maximum refuses a new mutation atomically without wrap; independently qualified reads remain possible. Test cumulative row/byte scan bounds with hidden integrity rows included; reaching a bound cannot yield not_found or prove uniqueness. Guard/internal-row IDs never become public graph IDs.

Bucket guard schedules use barriers: transaction A establishes a fixed snapshot before B creates the guard/key and commits; A waits/acquires exclusion and must retry rather than infer an empty bucket. Repeat with an existing guard whose generation changed, read-committed fresh reobservation, same-digest distinct full keys and equal full keys. Rollback restores guard generation and key/reservation membership. Guard creation races, administrative reset/trim, generation exhaustion and late trigger lock discovery cannot bypass the protocol. Independently assert committed full-key uniqueness across both transactions; no test may equate acquired advisory lock with refreshed MVCC visibility.

Native capacity controls compare incompressible full-key index entries at the selected server/block/index profile boundary; the 1 MiB codec ceiling cannot serve as expected native index capacity. The separate large-key bucket candidate needs forced same-digest/different-key fixtures, concurrent equal/different creators, exact-byte lookup, reservation/re-key/delete races and all advertised raw-SQL guard paths. A unique digest index, truncated bucket scan, wrong full-key result or caller-forged digest must fail qualification. Full retained keys remain recoverable after migration/retention; no checksum replaces them. Select DDL, digest/dependency, row identity and guard/migration procedures before implementing this profile.

Portable-key consumer probes use the qualified UMF public encoder/receipt admission path and independent owner byte vectors. A private source import or copied encoder cannot satisfy the package dependency gate. Refuse mismatched source/Record/key ID, field order, receipt version/profile or byte inventory before native lookup. Native carrier and unavoidable derivation probes must compare independent expected bytes for every selected family and resource boundary. Unsupported null/absent/float/temporal components cannot borrow the compact-decimal candidate to pass the portable profile.

Start with independent fixtures and red native cases, then codec/extractor, maintenance and lookup. Block closeout on all four criteria, concurrency/rollback supplements and resolved family/null policy for the claimed profile. A passing bounded key corpus cannot claim every UMF key family.

### Independent migration controls

Binding-source provenance controls for the proposed source-home profile accept a storage key from an original archived binding with independent owning Record document provenance. Later acceptance changes the source projection while preserving authored identity/key_num/since_rev and prior historical envelope. Substitute current head/report, another equal-named key, wrong pointer, mismatched original binding bytes or the owning Record's document as the key's authored source: each must refuse source admission. Mixed document/binding fields, partial tuples and missing original archive cannot pass merely because a native FK exists. Exact repeat preserves original source; failed revision preserves prior projection. These are planned native/semantic controls and do not qualify the unadopted columns or decoder.

Plan `tests/keys/migration.native.test.ts` with two clients and pre-authored source/target inventories, independent of the conversion under test. The native fixture must pin the exclusion, DDL, encoding/installation profiles and existing journal/feed transition classification before it runs.

| Case | Independently expected observation |
| --- | --- |
| Deleted reservation has only irreversible old canonical text | Migration refuses representability; original bytes, reservation identity and selected binding remain intact |
| Two live spellings plus a deleted reservation convert to one forbidden target identity | Assessment includes all three originals; no target binding or partial target membership commits |
| Distinct namespaces and keys route to identical test digests | Exact identities coexist; no digest-only collision report |
| Writer, catalog acceptance or reservation purge waits across migration | Native admission establishes one ordered source/target decision; no writer executes under a half-switched binding |
| Inject failure after target rows/policy creation and before binding switch | Confirmed rollback restores old membership/policy/binding; no graph version/source/history mutation is fabricated |
| Lose acknowledgment after committed switch | Original-attempt reconcile finds its exact committed receipt/inventory; conversion is not reissued |
| Same target installed by another original attempt | Target equality alone cannot resolve the lost attempt as committed |
| After migration, create a key beyond old native index capacity and request reversal | New reversal refuses, preserves subsequent write and current binding; stale old tables do not replace it |
| Hold an old snapshot/cursor and attempt old-store cleanup | Cleanup obeys active/retained-context exclusion; current profile switch does not reinterpret the old context |
| Exhaust inventory/report bounds after discovering a conflict | Incomplete assessment cannot authorize activation or return collision-free; original installation remains selected |

These cases are planned; no native migration or runtime test is implemented or passing. Exact receipt, transition wire and procedure inventory remain implementation prerequisites, not fixture-defined substitutes.

Migration failure-stage controls inject lost application acknowledgment during target staging, unconfirmed cleanup after binding-switch failure, and lost commit acknowledgment separately. Assert application_unknown versus cleanup_unknown with original stage for the first two, commit_unknown for the third, and no committed payload in any unresolved result. Reconciliation must preserve original evidence and cannot replace cleanup uncertainty with collision refusal merely because no target rows are visible.

Migration tooling consumer/lifetime controls count host calls during constructor/import (zero), reject separately supported but unregistered transition pairs, retain a handle across disposal and require admission failure, and verify committed migration does not rewrite old assembly selection/readiness. Dispose after lost commit reply, then use a newly authorized matching recovery tool: original evidence remains, target-active state may resolve original commit, and no source-matching check causes blind replacement or blocks original-only recovery. Caller credentials/registry/pool remain host owned. These are future runtime/package tests; declaration compilation cannot prove them.

Inventory admission controls reject duplicate source IDs, missing/extra/reordered target references, live/reservation coalescing, a reservation mapped to omitted, count-only empty-scope evidence and a blocked report with no actual blocker. Forced digest-collision classes remain separate by full bytes. Include a hidden participant in a forbidden equality class and require complete authorized report or unavailable, never a collision-free prefix. Target derivation controls distinguish preserved-component owner encoding, exact registered conversion and unchanged-byte reuse; no missing-component reservation may be synthesized from an opaque old key.

Resource classification controls distinguish one completely assessed over-limit key from total-work exhaustion before remaining entries are visited. The former may be a complete per-entry unrepresentable result; the latter requires incomplete overall assessment, with no synthesized suffix correspondence or complete blocked report. Empty native inventory still requires nonempty independent collector observations and complete scope proof. Five declaration rejection controls cover missing reservation bytes, missing preserved components, target derivation evidence, empty raw observation and singleton conflicts.

Receipt custody controls observe the receipt before commit in its own transaction (pending only), after committed switch from an independent authorized observer, and after a later migration (original committed result remains recoverable while current binding stays newer). Substitute another attempt's equal target receipt, remove original receipt without independent termination proof, or attempt overwrite under the same attempt ID with different request bytes: none may produce original committed success. Verify request/inventory/transition/receipt/commit dependency graph is acyclic, and dynamic receipt bytes do not enter an installed-inventory self hash. Ordinary writers cannot fabricate native switch evidence or edit receipts under the claimed administrative profile.

Archive closure controls distinguish an upstream-valid cyclic authored model from a forbidden migration proof back-reference. The first retains exact definitions and terminates bounded artifact enumeration; the second refuses before replacement. Test repeated references to one admitted original artifact, equal bytes under distinct owners, substituted same-digest bytes, conflicting immutable-identity bytes, missing required archive, unknown dependency grammar and arbitrary URI-looking opaque content. Repeated references count as edges and actual repeated work, without becoming fresh graph expansion; distinct ownership cannot be merged. Opaque content remains exact and never triggers network fetch. Independent inventories at 10,000/10,001 artifacts and 100,000/100,001 reference occurrences prove whole-closure boundary behavior under the selected candidate, separately from source/native row limits. Missing or oversized closure leaves all original memberships/binding intact after confirmed containment, or preserves original recovery custody if termination is unresolved. These tests are planned; the limits and closure procedure remain unadopted and unqualified.

Complete-feed migration controls require a migration-only transaction to be independently discoverable with its exact required transition member and original receipt/configuration/archive context. A configuration prerequisite without a member, fabricated object change/revision/reservation, or omitted completeness transaction fails. Missing selected transition capability refuses migration before effects. Changed layout/interpretation context requires the designed explicit compatibility/replacement lifecycle; no implicit reseed/epoch reset/dedup clear may pass. These native tests await the versioned Truss transition contract, not a UMF/Weft parser change.

Bounded scan controls independently populate 10,000 and 10,001 combined live/reservation candidates across forced colliding namespaces, including hidden rows. Metadata lookahead must prove completeness before full-byte fetch; no truncated absence/uniqueness success. Test cumulative byte bounds across old/new buckets with exact integer length transport, duplicate planned bucket dedup and missing/changed metadata-to-full-fetch correspondence. Observe query plans and cancellation/rollback independently; LIMIT cannot stand for bounded native work. Full routing index contains only digest pair/internal ID, never large key or original context.

Artifact-budget controls use small exact keys with independently large original context/reservation bytes. Metadata reports original artifact octet lengths and rejects cumulative over-budget originals before fetch. Qualified bytea wire/decoder/base64/hex expansion bounds include whole envelope overhead; an unknown expansion profile refuses rather than fetch unbounded output. Exact-bound/one-byte-over fixtures and changed metadata/full-fetch lengths require complete output accounting or safe rollback/recovery, never partial conflict disclosure/not_found. These are native/runtime tests to implement, not pure length checks that qualify a driver.

Privilege controls enumerate every ordinary inherited role and granted writer entrypoint against guard/key/reservation/sequence/receipt stores. Attempt direct DML, truncate, sequence reset, forged internal IDs/digests, trigger disable and procedure invocation with caller-supplied acting role: protected profile must establish no unauthorized effects and current-role authority. Separately exercise hidden candidates with bounded native observer visibility and require exact uniqueness plus no payload/count/size disclosure. These controls qualify the named protected-procedure profile only; direct-table writer enforcement remains a distinct required schedule/design output, never passed solely by privilege denial.

Migration entry-address cases accept ordinals 1 and bigint maximum with nineteen-digit padding, and reject zero/overflow/sign/short padding/whitespace. Independently enumerate two same-byte source instances and prove they remain distinct entries and target results. Reuse a correspondence against another original inventory with identical local entry IDs: refuse original-artifact mismatch. Duplicate or ambiguous native locator, missing applicable omitted instance and incomplete stream exhaustion prevent complete inventory; report-budget failure cannot publish a complete prefix. Native locator ordering is a selected collector prerequisite, not inferred from ordinal syntax.

Bucket-source collector schedules independently list live applicability tuples with IDs 2 and 10 to prove native numeric order, include one omitted sparse instance with no bucket row, and include equal-byte reservations with distinct storage rows. Missing expected projection, extra unmatched row, wrong definition/version and duplicate native locator block complete scope. Preserve hidden reservation and deleted original components in the private integrity inventory; unauthorized public assessment must refuse disclosure. A legacy source presented under the bucket locator profile refuses. Stream work exhaustion after the live phase cannot report complete scope before reservation exhaustion.

Original collector artifact custody controls reject a reverse dependency on the later source inventory, mismatched source entry kind/held classification, substituted native store definition, missing applicability-domain proof and either missing stream-exhaustion witness. Positive empty-scope collection retains both independent exhaustion artifacts. Exact source-entry bytes, not entry count or digest alone, must correspond to each native locator and ordinal. Four declaration rejection controls establish required shape only; native original-cut/full-byte/visibility checks remain planned.

Head-exclusion schedules hold a pre-admitted writer share lock, begin migration and prove inventory collection waits until writer termination; begin a later writer and prove it cannot mutate before migration termination. Commit a key change before exclusive acquisition and require the separate post-lock source observation to include it or reject the stale basis. Hold a purge/backfill/retention operation and check the same exclusion. Missing/replaced head, nonparticipating granted writer, wrong isolation and lower-lock-first admission refuse qualification. Cancel during lock wait and separately during conversion: establish original native termination before releasing recovery obligations. A qualified retained reader must preserve its original snapshot; exclusive migration admission alone cannot authorize old-store cleanup.

Migration authority schedules use the owned connection and independently capture original acting role, administrative grant, disclosure grant and sorted owner guards. A pure policy revocation commits before admission: migration refuses under the new authority. Revocation after guarded admission waits until migration termination, with no claim of immediate revocation. Catalog-policy admin must acquire head before policy guard. Inject a separate coordinator trying to reacquire migration-held head and require profile rejection rather than entering that cross-connection wait. Discover an unplanned reservation owner after lower locks: no prefix disclosure or lock-set growth; contain/reconcile original work. Integrity definer visibility without admin/disclosure permission cannot produce a successful migration or complete public report.

Public migration authority controls grant administrative execution but deny complete inventory/result disclosure: refuse before conversion/staging/switch and return no assessment/report/source-inventory reference. Integrity observer access cannot satisfy disclosure. Native containment/recovery custody remains separately authorized and an unresolved original transaction cannot be mislabeled clean pre-native refusal. Two result wire controls cover authorized refusal shape and assessment leakage rejection.

Installed admission-state controls test absent row, forged generation, scalar/configuration byte mismatch, unchanged catalog with changed binding and unexpected conditional-update row count. Generation bigint maximum refuses before switch; successful migration increments once while preserving epoch/installation/reuse/journal. Rollback preserves all original state and protected archive bytes. Mutate legacy setting rows through any granted writer and require profile invalidation/refusal rather than split policy admission. Native generated artifact hashes remain observations, not full-byte parity proof.

Admission statement controls substitute one original artifact byte while retaining generation/digest claim, forge target encoded generation/policies, exceed metadata/output budget and return zero rows at maximum generation. No partial switch/receipt/feed commit follows. Lost UPDATE response preserves application-unknown custody until actual native termination/transaction outcome is established. A RETURNING row cannot qualify commit or complete feed. Two fetch statements must have exact original metadata correspondence under the retained head exclusion.

Fixed migration receipt controls inject equal routing digests with unequal full installation/epoch/attempt bytes, identical identity with changed original request, duplicate exact-identity rows, generation pair gaps and receipt insertion followed by switch/finalizer failure. Full identity collision serializes without conflation; conflicting/duplicate original evidence refuses; confirmed rollback leaves no receipt/switch/feed member. Ordinary update/delete/truncate/sequence-reset attempts must fail under the qualified profile. Recover an old receipt after a newer binding: classify the original attempt without overwriting current state. Missing original archives or exhausted complete routing budget blocks successful reconciliation.

Receipt lookup controls exercise 10,000/10,001 routing rows with unrelated full identities, exact identity hidden among collisions, oversized original request/receipt bytes and driver output expansion at/above its selected bound. Inject missing/extra/reordered/changed fetched rows after metadata and require integrity refusal. Zero exact receipt rows while the original transaction remains unresolved cannot authorize a new migration. Concurrent receipt purge must wait behind the admitted lookup head; native timeout/termination remains independently observed.

Head privilege qualification tests run admission through the actual ordinary EXECUTE-only caller and prove retained FOR SHARE exclusion without direct UPDATE authority over schema_head. Raw revision mutation, inherited role/role-switch grants and definer helper argument abuse must not bypass protection. A helper invoked on another connection cannot satisfy same-transaction admission. Capture original acting role separately from procedure owner and verify migration admin/disclosure remains independently checked. Exact function/body/search-path/profile is a preimplementation design dependency.

Head routine controls test no-argument invocation through the actual EXECUTE whitelist, revoked PUBLIC access, read-only/missing-head/missing-state refusal and temporary relation/function shadowing. Role capture remains the original SET ROLE/session caller under a distinct function owner. Roll back a savepoint containing lock acquisition and ensure cached metadata is not reusable as retained admission; on another connection it proves nothing. Compare READ COMMITTED and fixed-snapshot head-change behavior under exact adapter/server profiles. Return values alone cannot bypass policy/full selected binding admission.


## Admission routine native qualification handoff

Proposed harness command: `bun test tests/native/write-head-admission.test.ts`. This test file/harness is not implemented. Setup uses the exact installed candidate routine/body and admitted head/state DDL, a controlled routine owner, ordinary EXECUTE-only caller, unrelated non-whitelisted caller and independent privileged observer. Credentials remain injected by the host. Use three separately identified connections for caller, competing administrator and observer; controlled barriers establish lock schedules without inferring acquisition from sleep. Pin PostgreSQL/adapter versions, role membership and complete installed-policy inventory before each case.

| Case | Independently required result |
| --- | --- |
| `ordinary_execute_retains_original_head_share` | Exactly one row reports original revision/generation/caller. Competing native head update cannot finish until caller transaction ends; later writer admission observes the updated head under its qualified isolation rule. |
| `ordinary_cannot_mutate_head` | Raw UPDATE/DELETE/TRUNCATE and reachable helper attempts leave original head and admission state unchanged. Caller is neither owner nor member of owner/admin roles. |
| `nonwhitelisted_public_execution_refuses` | Role with no direct/inherited qualified EXECUTE cannot invoke the routine; PUBLIC grants do not reopen it. |
| `definer_preserves_actual_acting_role` | Session caller and explicit SET ROLE variants report their database-derived acting role, distinct from native routine owner. |
| `read_only_refuses_before_lock` | Explicitly read-only caller scope receives the candidate 25006 failure and changes no state; independently prove competing administrator is not left blocked by a leaked owned attempt. |
| `missing_native_home_refuses` | Missing head or admission row returns candidate 55000 failure, with original transaction containment observed separately. |
| `temporary_shadow_cannot_retarget` | Temporary same-name relations/functions and caller-writable namespace objects cannot replace qualified native dependencies or reported values. |
| `savepoint_rollback_releases_acquired_lock` | Lock acquired inside a rolled-back savepoint is no longer accepted as retained admission; subsequent operation refreshes original native state. |
| `fixed_snapshot_change_requires_retry` | A fixed snapshot predating head advancement cannot report stale successful current admission; exact native retry/refusal follows the selected profile. |
| `metadata_does_not_grant_policy_or_binding` | Correct returned revision/generation/caller does not authorize an inaccessible owner or incompatible selected binding/configuration. Public effect count stays zero. |

Observe actual native function qualified signature, language, definer/volatility/configuration flags, owner, body bytes/dependencies and complete effective role/schema/table/column/sequence/EXECUTE rights. Retain native raw observations and original case results, including all rows/column order/error state and confirmed transaction termination. No password/session secret is an artifact. Record whether each lock was acquired/released using independent native evidence and barrier completion. A transport timeout or test assertion failure does not itself prove the native transaction ended; use the qualified containment/recovery protocol.

A pass closes only this exact routine/adapter/server/role/namespace/isolation tuple. It cannot qualify native writer derivation, complete migration, read-only historical coordinator, generated UMF installation or other callable helpers. Mutation on absence/malformed outputs, wrong native role, broken PUBLIC grants or leaked lock must fail the qualifier itself; a fixture owner calling the routine is insufficient evidence for the ordinary caller path.

Head adapter result vectors accept revision/generation zero and native maxima as exact text, plus mixed-case/quoted-name role meaning. Reject missing/extra/reordered/duplicate columns, zero/two rows, null cells, leading zero/sign/overflow numbers and implicit host-number conversion. Expected native 25006/55000 must still classify aborted/unknown transaction state correctly; confirmed savepoint containment may expose domain refusal without ending a host-owned transaction. Inject transport loss after lock acquisition and malformed driver success: no cached admission or assumed lock release/reuse follows.


## Protected native operation closure controls

For CONTRACT-001's protected migration operation inventory, independently enumerate all actual executable routines and transitive privilege paths under each tested application, migration, maintenance, recovery and installation role. Compare exact signatures, owners, bodies/search paths, helper dependencies, inherited/SET ROLE/default/PUBLIC privileges and store access with the installed operation map. An extra callable helper or owner-role path fails qualification; a manifest supplied by the implementation is not the oracle.

Run role-separation controls: mutation-only caller attempts stage/switch/retention/initialization; migration admin lacking disclosure attempts collection/result delivery; observer attempts mutation; recovery-only service attempts a new migration; installer attempts initialized/populated namespace changes. Require zero forbidden effects and no hidden identity/count/byte disclosure. Exercise helper execution rather than only direct table denial.

Cascade schedules delete an object with several key memberships while another writer holds an earlier sorted bucket. Require the protected delete to wait before canonical-row effects, retain complete old/new guards, increment actual affected generations, and roll back canonical/membership/journal changes together on finalizer failure. Reservations retain original deleted evidence; neither FK cascade nor an internal privileged trigger may remove them implicitly. Repeat through every granted public mutation/import/catalog path that can cause deletion. A missing granted path fails inventory closure, not merely this individual test.

All controls are planned native tests. They do not close direct-table writer support or qualify the currently unapplied statement fragments.


## Internal metadata helper controls

For key_bucket_integrity_metadata_v01, planned native tests cover NULL/31/33-byte inputs, all-live/all-reservation/mixed routing members, numeric IDs 2 versus 10, exactly 10,000 combined rows and a 10,001st lookahead. Require one complete global numeric order, exact decimal length text and no full hidden identity/artifact output. Two kinds with fewer than 10,000 each but more than 10,000 combined must refuse full admission. Across multiple buckets, aggregate ceilings remain cumulative.

Use a qualified test-only collision source separately from production digest qualification. Query independent native tables under a harness-only complete observer to establish expected membership and lengths; the helper cannot generate its own expected output. Missing RLS visibility, lost original guard, same route on another connection, unexpected full-read correspondence and original resource/timeout uncertainty must block mutation/completeness. Verify actual helper owner/signature/body/settings and no PUBLIC/application EXECUTE or indirect role path. No native tests have run for this draft.


## Metadata-to-full-read admission schedules

Planned controls for the ordered extraction procedure independently alter metadata kind, locator uniqueness/order, canonical length spelling, namespace/key physical limits and original-context size. Require refusal before any full-byte read for every malformed/resource-unadmitted metadata result. A repeated shared-sequence locator under different kinds is integrity failure. Exercise exactly-at/one-over aggregate namespace/key, artifact and expanded driver/private-buffer bounds across multiple buckets; resetting a per-call budget must fail the qualifier.

After full-read admission, inject extra/missing/reordered/changed-length rows, substituted same-length original context, released guard, changed snapshot, cancelled read and unknown driver termination. No partial identity, hidden participant prefix, conflict/absence verdict or mutation may escape. A qualified internal streaming profile must preserve complete exact original bytes and charge simultaneously live chunks/reconstruction/decoded buffers; no truncation/partial digest substitutes for the original artifact. Original native recovery stays unresolved when termination or cleanup is unknown. These tests remain planned until exact full-read/decoder profiles exist.


## Lossless extraction chunk boundaries

Planned chunk-helper tests use independently authored original byte carriers of lengths 1, 65,535, 65,536, 65,537 and multiple chunks, including zero bytes and incompressible TOASTed artifacts. Require exact independent reconstruction with final short chunk and no lexical/source normalization. NULL/unknown selectors, zero/negative/overflow locator or length, negative/equal-total/greater offsets and mismatched expected length fail before any public result. Force missing/multiple row faults under a separate corruption fixture; no alternative row/store can satisfy the original selector.

Inject duplicated/out-of-order chunks, partial transport, changed metadata length, lost guard/savepoint and timeout while a native chunk remains active. Require original failure/recovery without resumed extraction on another snapshot. Measure actual server detoast/work and adapter/owned reconstruction allocation independently: a small returned chunk with excessive native allocation must fail resource qualification. These tests are planned; no native helper behavior is claimed.


## Typed locator/context parity

Planned locator-helper tests independently read original live object/type/local-key tuples and reserved original artifacts. Assert exact native scalar text, original metadata kind/locator and same-guard/snapshot correspondence. Wrong route/kind, missing row, NULL live tuple, same key under another object/type/local key, stale authored-key/local-number mapping and same-length substituted context must fail admission before mutation or public disclosure.

For reservations, assert three absent native live-tuple fields while complete original historical typed identity remains required in the artifact. Delete the former live object and prove qualification does not reconstruct provenance from a new object's equal key or current catalog numeric IDs. Missing original identity cannot become a sparse/omitted success. Exercise native scalar extremes without JavaScript number conversion and cumulative framing/resource limits. These remain planned native tests.


## Observer harness implementation sequence

Implement the observer tests in planned `tests/keys/observer-native.test.ts` after exact server/adapter/role/resource profiles and native setup have been admitted. `bun test tests/keys/observer-native.test.ts` is a future command, not current runnable evidence. The harness owns scratch namespace and roles explicitly; it never alters an existing deployment role/schema or installs the drafts automatically from library construction.

| Step | Harness deliverable / independent observation | Stop/refusal condition |
| --- | --- | --- |
| O1: capture deployment | Record actual server patch, adapter build, native layout/helper source pins, role identities/attributes/membership graph, policies/grants and selected resource/caller/snapshot tuple. Inspect native catalogs through a separately authorized harness observer. | Unknown profiles, preexisting target objects/roles, unresolved owner installation correspondence or unauthorized setup: unverified, zero helper test invocation. |
| O2: install and compile | Compile exact selected helpers in the admitted scratch deployment transaction; assign approved owners, revoke PUBLIC, grant only exact internal callers, commit only after independent installed body/signature/settings/privilege parity. | Native compilation/parity/role setup fails: record exact failure and confirmed rollback/cleanup; source parser success cannot override it. |
| O3: independent fixtures | Construct immutable expected native tuple/byte records separately from tested helpers/UMF exporter; install visible/hidden live and reserved members plus numeric-order/length boundaries. Retain full original expected bytes and archived provenance. | The fixture cannot supply required native homes/provenance/complete expected members: case unverified, never generate expectations from helper output. |
| O4: role/custody invocation | Invoke helpers through the exact internally granted protected caller path; separately attempt ordinary/public/inherited/SET ROLE bypasses. Use distinct native connections with barriers for retained guard, savepoint rollback and policy change schedules. | Using the fixture admin as the actual caller, absent outer guard/caller capture or an unobserved barrier invalidates the case. |
| O5: results and resources | Independently compare complete metadata order/tuple and every reconstructed byte; capture actual native execution/detoast/work, adapter buffering, simultaneously owned buffers and elapsed/containment observations under approved measurement profile. | Missing measurement cannot qualify a quantitative resource claim; small result/chunk size is not a native memory/work measurement. Preserve mismatches and unknown active work. |
| O6: evidence and cleanup | Archive original request/native observations/expected-versus-actual comparison, profile pins and per-case status; independently establish original transaction/resource termination and exact scratch ownership before cleanup. | Unknown termination stays interrupted with original recovery; no name-only deletion, guessed rollback or success based on disconnect. |

Concurrency barriers identify the exact original transaction and native statement phase: after outer guard admission, after complete metadata, before each locator/chunk, after native reply before delivery, and before cleanup. Independent blocker/query/transaction observations plus released harness barriers establish the schedule; elapsed sleeps alone cannot prove a lock was held or a native operation ended. Corruption/forced-collision/transport fault fixtures carry separate test-only profiles and cannot change the production helper/digest definition whose behavior is claimed.

Qualification records distinguish helper-body compilation, role-policy completeness, metadata/typed-context parity, full-byte reconstruction, original guard/snapshot custody and quantitative resource/containment evidence. Each required component must pass for the selected composed observer claim; an aggregate count cannot hide an unverified component. These helper tests do not qualify the protected bucket writer, migration switch, direct-table coverage or shared UMF/Weft interfaces.


## Exclusive migration head callable schedules

Planned native cases hold ordinary writer FOR SHARE, invoke the internal migration helper and independently observe its wait; commit/rollback the original writer and verify fresh revision/admission text after exclusive acquisition. Start a later writer and prove it waits until original migration termination. Missing head/admission state, read-only, REPEATABLE READ and SERIALIZABLE refuse this selected READ COMMITTED profile without implicit mode/snapshot change or public successful admission. If head acquisition precedes missing admission failure, independently establish rollback/lock release before reuse.

Invoke through exact qualified internal caller, not fixture administrator or ordinary share-admission role. Exercise PUBLIC/inherited/helper-role bypass, temporary shadowing, original SET ROLE/session role versus definer owner, savepoint rollback and lost reply/cancel while lock wait is active. Cached metadata from another connection/released savepoint cannot authorize collection; missing current admin/disclosure/binding admission remains refusal after a syntactically successful head result. Native observation confirms original termination; disconnect alone cannot prove lock release. All cases are planned, with no native qualification claimed.


Same-store migration schedules exercise the actual object/type/key uniqueness constraint. Attempt side-by-side insertion as a negative control. Inject faults after exact source deletion, after a subset of target insertions, before target parity, after conditional switch and during receipt/feed finalization; independently verify original memberships/binding/generation/receipts remain durable after confirmed rollback. Include omissions changing applicability, unchanged memberships, reservation preservation, source/target digest collisions, sequence gaps and fresh locator correspondence. A missing original archive or insufficient candidate/evidence reservation must refuse before deletion. Lost commit replies reconcile the original attempt rather than repeating replacement; a later migration/re-key cannot be overwritten from old retained source evidence. Native schedules remain planned.


The [six guard-generation expectations](../../02-design/contracts/bindings/migration-guard-generation-v0.1.vectors.json) distinguish actual delete/insert counts from net cardinality and target initialization. Planned native controls force source/target route collision, preexisting near-exhausted guard, absent guard creation and unexpected cascade effects. Capacity refusal precedes any membership mutation across all guards; rollback restores actual rows and transactional deltas. Existing colliding guards cannot be reset merely because target full namespaces differ. Fixture arithmetic is not native evidence.


Converted reservation controls preserve an original A-profile artifact while admitting its B-profile lookup bytes through complete source/target derivation and actual native locator correspondence. Reject new bytes without derivation custody, sourceEntryId/hash-only matching, changed original typed identity and a staged future receipt used as its own authority. In A-to-B-to-C schedules remove B's required evidence and require unavailable/refusal rather than an absent reservation or guessed A-to-C equivalence. Complete retained archive dependency exclusion precedes cleanup. These are native/semantic implementation schedules, not passing evidence from receipt shape.


Signed catalog namespace schedules exercise type IDs -2147483648, -1, 0 and 2147483647 and key numbers -32768, -1, 0 and 32767 with independently valid original definitions. Reject out-of-range, plus-prefixed, negative-zero, padded/exponent and rounded forms. Compare positive-ID v0.1/v0.2 namespaces as distinct domains; retained old lookup/history cannot silently switch domains. A missing object-key definition cannot be fabricated from an edge's special zero reservation. Native migration preserves source numeric identities and full history while changing namespace projection through the complete conversion/switch protocol. Current v0.1 admission refuses unsupported nonpositive components honestly; signed v0.2 remains a candidate awaiting byte/native/profile qualification.


The [signed namespace byte examples](../../02-design/contracts/bindings/signed-key-namespace-v0.2.vectors.json) contain six complete canonical array/preimage/routing expectations and nine lexical/range refusals. The profile hash is synthetic fixture context, not an admitted UMF encoder receipt. Compare actual native namespace bytes and routing with these examples only after separately admitting each original owner/profile/definition. The positive v0.1/v0.2 pair must differ; native minima/maxima and valid zero/negative identities retain exact spelling. Encoder tuple output is deliberately outside this namespace fixture's claim.


Phase classification schedules stop at pure admission, after native head acquisition without row changes, after guard insertion, after membership deletion, after switch/receipt finalization, after COMMIT submission and after independently confirmed commit. Require the exact existing result/containment classification from actual original termination/durability, not last returned phase. Lost head reply cannot be pre-native refusal; failed staging cannot be rolled_back until all-store termination is observed; postcommit result/cleanup loss cannot become rollback or replacement migration. Check original recovery remains reachable after disposal and retains committed truth. Native schedules remain planned.


Whole-migration resource schedules use exact proposed profile units and request/profile composition. Smaller caller limits tighten; larger limits cannot enlarge; missing registration or incompatible units refuse before native work. Count hidden/colliding/omitted/reserved entries and all repeated stages globally. Force receipt/report/candidate/owned-buffer shortage before deletion and full collision report overflow before activation. Deadline/containment stops follow actual original native phase evidence; no per-stage reset or replacement attempt repairs unknown work. Default numeric values await feasibility/native qualification.


Chunk-call planning controls compare exact per-carrier counts: lengths 1, 65536 and 65537 require respectively 1, 1 and 2 calls; ten thousand one-byte carriers require ten thousand calls, not one. Independently budget source/post-state metadata/locator calls and complete guard/persistence/finalization/containment allowances. A plan fitting entry/byte ceilings but exceeding remaining statements must refuse before deletion. Actual repeated calls remain charged, and reserved containment cannot be spent on extra normal work. Producer batching requires separately admitted observation semantics. These are protocol/resource expectations, not executed native throughput evidence.


Receipt-backed archive controls remove original source bucket rows after confirmed migration and require complete original interpretation from the retained admitted receipt closure. Reject a top-level complete receipt whose nested component/definition/derivation dependency is missing; embedding caller bytes cannot repair provenance. Verify old/new locator correspondence against actual replacement and prevent pending receipt/future commit self-authorization. Nested base64 expansion and decoded copies exceed the proper resource ceilings honestly; no implicit compression/externalization repairs it. Retention is blocked by later projections/conversion chains/feed/active contexts/recovery even when the migrated receipt is old. Native/archive tests remain planned.


Locator correspondence grammar has fifteen shape expectations, including all five actions, reservation preservation, positive textual locators, mandatory row/coverage evidence and exclusion of a future receipt. Duplicate source entries, same-locator replacement and native bigint overflow intentionally pass shape and must fail semantic/native admission. Independently compare complete actual old/new sets and full row bytes under original custody; IDs/counts or an unchanged action label cannot prove parity. No test result above establishes deployed replacement behavior.


Precommit switch evidence has twelve shape expectations, excluding future receipt/commit members and requiring original exclusion/locator/guard evidence. Duplicate routed guards, incorrect generation sums, deletion from a created guard and native bigint overflow remain shape-valid semantic refusals. Actual finalizer schedules compare complete native pre/post effects with each admitted guard and one-step admission before receipt persistence; a supplied evidence tree or returned row cannot establish original custody or commit.


Admission snapshot has twelve shape expectations, including generation/policy/full-artifact/observation requirements and exclusion of future commit evidence. Bigint overflow, duplicated scalar/configuration mismatch and historical-current-authority confusion intentionally pass shape and require semantic/native refusal. Independently corrupt metadata versus full-fetch lengths/scalars/bytes under original exclusion and require no switch. Original prior/resulting snapshots must share installation/epoch/policies and exact one-step generation; shape-valid copied snapshots cannot repair original custody.


### Adopted lexical numeric held-to-equal key controls

Use an explicitly adopted lexical numeric property/home/codec and an independently qualified mathematical decimal key definition admitting both 1.0 and 1.00. Retain original full qualified old/new derivation receipts from existing UMF operations where applicable; NX witnesses alone cannot issue key bytes. Independently expect the same key membership/locator after the property token update, no synthetic old-key reservation, a genuine property version/history transition and successful exact-key lookup resolving the same instance. Distinct Record/key contexts remain distinct even with equal component bytes.

A concurrent same-qualified-key creator with an alternate admitted lexical token must encounter the existing current conflict, not obtain a second instance because stored token spelling differs. Establish actual overlapping original guard/exclusion and current revalidation; selected serialization retry remains separately reported. Host rollback of the lexical update restores original property/version/history while preserving the same valid key membership. A hidden or resource-incomplete key observation cannot pass equality/conflict correspondence. Scope these controls to US-009's uniqueness/lookup obligations and cross-reference STP-007/015 for exact property/event behavior; no portable domain or profile adoption is inferred from this planned fixture.

### Equal-membership native guard controls

For an adopted lexical-preserving numeric value and independently selected mathematical key profile, replace 1.0 with 1.00. Independently expect a real property/version/history/journal change, identical full key membership and original key locator, no synthetic removal/reservation/reinsert and no membership-generation increment unless another actual admitted membership mutation occurs. Require original affected-key guard admission and canonical/key finalization despite zero key-row changes. These expectations do not select a decimal key profile or broaden UMF portable encoding.

Use barrier-driven competing key/reservation writers and original lock traces to show a prelock equal comparison cannot skip guarded revalidation. Corrupt or omit the surviving derived row, swap owner/source/encoding correspondence, or bypass a property write through a selected ordinary raw SQL path while key-table triggers remain silent: complete native enforcement must refuse or honestly classify the profile unqualified. A passing engine precheck is insufficient. Compare full original before/after graph/key/source/version/journal inventory and actual operation/current-union observations; unchanged row counts or native numeric equality cannot supply that evidence.
