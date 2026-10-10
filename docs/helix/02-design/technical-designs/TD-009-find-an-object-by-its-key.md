---
ddx:
  id: TD-009
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-009
      kind: informed_by
    - id: SD-002
      kind: informed_by
    - id: CONTRACT-001
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
    - id: ADR-006
      kind: informed_by

---

# TD-009: Find an object by its key

**User Story:** [[US-009]]. **Feature:** FEAT-002. **Parent:** [[SD-002]].

## Scope

For UMF's portable authored-key subset, reuse CONTRACT-040's `umf-key-tuple-v1` and qualified package/API instead of implementing Truss's own competing portable normalizer. Resolve stable authored key identity explicitly to the Truss local key binding, retain ordered field/source pins and select an injective native byte carrier. UMF's internal encoder evidence is not Truss native guard/lookup qualification. The separate compact-decimal candidate cannot broaden the portable subset or silently replace its byte profile.

Consume ADR-006's proposed compact decimal equality tuple only through an explicitly selected key component profile. Original lexical value remains separate; mathematical order does not follow encoded tuple bytes. Pure normalization/comparator, native derivation and lookup/reservation encoding are separate implementation boundaries. Pin admitted source grammar/native domain and resource limits before selecting support. Independently authored rational fixtures in the design audit establish the proposed example meanings only, not a production codec or SQL comparison path.

Implement catalog-derived business-key encoding, transactional key-row maintenance and lookup. Inherit fixed storage from SD-002; do not create per-type unique indexes. Prerequisites are US-007 exact storage, accepted key catalog derivation and the executor transaction protocol. This is a draft design; exact original key binding, scalar/null participation, native transport/guard and resource profile admission remain prerequisites. Consume the authored policies below rather than introducing a second normalizer or reopening the selected storage-versus-portable identity distinction.

## Technical Approach

Compile each catalog key definition into an ordered component extractor and the canonicalization prescribed by CONTRACT-001. Read components by property identity, distinguish missing from explicit null, and build key text using exact decimal parsing rather than host numbers. The baseline database unique constraint arbitrates competing canonical rows within its qualified capacity; the large-key profile instead requires the unavoidable native bucket-generation/exact-comparison procedure below. Application prechecks alone cannot qualify either native guarantee.

US-009-AC1 uses the selected qualified native uniqueness protocol in the same transaction as the object. AC2 uses numeric equality canonicalization independent of stored lexical form. AC3 retains authored timestamp text, including offsets; do not use timestamp-to-instant conversion for key identity. AC4 omits the derived key row when a component is absent and records the missing-component report. These behaviors do not imply that arbitrary raw object SQL derives valid keys: CONTRACT-001 explicitly classifies property-to-key consistency as engine/host-trigger enforcement.

## Component Changes

| Planned component/files | Change | Criteria |
| --- | --- | --- |
| `packages/core/src/keys/canonical.ts` | Qualified UMF portable encoder consumption; separate selected family-specific storage transport/composite encoding | US-009-AC2, US-009-AC3 |
| `packages/core/src/keys/derive.ts` | Ordered component extraction and absent-component diagnostics from pinned catalog | US-009-AC4 |
| `packages/postgresql/src/keys/write.ts` | Maintain old/new key rows atomically with object effects and map unique violations | US-009-AC1, US-009-AC2 |
| `packages/postgresql/src/keys/read.ts` | Parameterized type/key/value lookup, object retrieval in one qualified read context | Story walkthrough |
| `tests/keys/canonical.test.ts`, `tests/keys/native.test.ts` | Corpus, collision, missing component, bypass and concurrent-client observations | All criteria |

All components are new; no runtime implementation exists yet. Pure derivation imports no database/driver APIs.

## API/Interface Design

CONTRACT-001 now distinguishes UMF portable total identity from authored Truss storage uniqueness. US-009-AC3/AC4 use explicit timestamp-text/sparse storage bindings; they cannot be tested as successful portable core-Key cases. Required property validation remains independent. Catalog extraction and enforcement reports preserve binding source kind/provenance, and Weft/relationship/import identity admission cannot upgrade sparse uniqueness into total authored identity. Exact binding wire/profile selection remains open.

Implement membership transitions from CONTRACT-004 after complete component admission: held-to-omitted reserves the old full key; omitted-to-omitted writes no key/reservation; omitted-to-held performs ordinary complete conflict/reservation checks; held-to-equal preserves membership despite a lexical change; held-to-different reserves/replaces atomically. Plan old/new buckets before effects, including removal-only transitions. A failed key transition rolls back record/version/journal effects. Catalog remapping is a separate migration boundary, not a synthetic sequence of object updates.

CONTRACT-001 owns canonical text, fixed constraints and database error mapping. CONTRACT-004 owns mutations and reports; CONTRACT-007 owns transaction and exact transport. This story uses those surfaces rather than defining another lookup payload. Consume the existing [direct lookup request](../contracts/direct-lookup-request-v0.1.schema.json), [result](../contracts/direct-lookup-result-v0.1.schema.json) and [key binding wire](../contracts/key-bindings-v0.1.schema.json) under their exact versions. Qualify original codec, visibility, full correspondence and public error/disclosure behavior before package API publication; a shape-valid lookup result cannot establish native absence or uniqueness. No parallel lookup envelope is needed.

## Data Model Changes

Use the existing `object_key` and catalog key/component definitions only for the qualified baseline profile; the separately selected transport/bucket candidate has explicit new layout inventory below. Key addition to an existing populated type builds rows in catalog acceptance: list duplicate objects and roll back the entire revision on collisions. Component updates remove obsolete rows and insert new rows atomically; deletion relies on the existing object FK cascade. Do not leave an intermediate key state visible outside the transaction.

## Integration Points

Catalog supplies key/component identity and scalar family. Core supplies canonical values and ordered lock identities; PostgreSQL executes under CONTRACT-009's shared lock hierarchy. Changing several keys acquires the complete old/new key lock set before effects. Weft receives qualified authored-key mapping only after key completeness/uniqueness obligations are met; storage identifiers are not a substitute for an authored key. Unsupported families refuse rather than stringify into a false equality policy.

## Security

Host supplies authentication and allowed type/module context. Parameterize canonical values; never interpolate user key text. Lookup must use the same role policy as object reads and must not expose a hidden object's identity through a separate key lookup. Unique-error diagnostics must respect visibility. Bypass tests distinguish key-row uniqueness from object-property consistency honestly.

## Performance

The baseline uses `(type_id,key_num,k)` lookup/uniqueness only within a qualified native index-capacity profile. It cannot qualify all keys below the codec ceiling. CONTRACT-001's separate large-key candidate routes through a nonunique fixed-size digest index, retains complete key bytes and guards exact comparison with bucket generation admission. Record latency/plan evidence for the actual selected native profile; collision-bucket/resource cost is part of that evidence. No new numeric SLA is invented here.

## Testing

Consume CONTRACT-001's explicit key-profile boundary: no generic text fallback for unknown families; null is present and needs qualified participation/encoding; scalar storage does not imply key support. Independent fixtures cover quote/backslash/control escaping, Unicode bytes, delimiter/arity distinction, zero/exponent equivalence and expansion bounds. Version changes require reviewed rebuild/reservation migration, not implicit reinterpretation.

STP-009 owns criterion allocation. Supplement with decimal zero/exponent/sign equivalence, escaped composite strings, binary canonicalization, concurrent duplicate creates, update collision rollback, key addition with existing duplicates and lookup under restricted roles. Expected canonical bytes come from committed independent fixtures, not the codec under test.

## Migration and Rollback

The baseline requires no extra key-layout migration; selecting portable transport or the large-key bucket profile requires an explicit new physical encoding/layout and reviewed rebuild/collision/rollback procedure. Failed key writes or catalog backfills roll back objects, key rows, bucket generations, reservations and journals together. Retain the previous accepted catalog after collision refusal. Disable an unqualified family before accepting values; never change canonicalization for existing keys silently.

### B-004/B-008 native large-key selection spike

Candidate stores: fixed-size unique `key_bucket_guard` namespace/digest identity with generation; key rows with stable internal row identity, full exact `k`, selected profile/context and nonunique bucket index; retained reservation rows using the same bucket derivation and complete historical context. Preserve object/type/key uniqueness and typed object/key-definition foreign keys. Full `k` must not remain in a B-tree unique/include entry that defeats large-value support. Internal key-row IDs are storage bookkeeping, not authored record identity or feed reservation identity.

Prototype only in a disposable native fixture when implementation work is authorized. Admission sequence: verify catalog/configuration/owner tuple and transport; preplan/sort all old/new buckets; establish each native guard under business-level exclusion; prove current observation or whole-transaction retry; compare exact full current/reserved keys under the policy; validate/persist atomic key/canonical/history effects and generation changes. Native procedure and direct-writer coverage must preserve the same hierarchy. Choose exact namespace/digest dependencies, row identity, generation range and guard DDL before the spike; do not infer them from pseudocode.

Selection evidence must independently decide equal-key concurrency, forced digest collision coexistence/lookup, stale fixed-snapshot retry, first-guard race, atomic re-key/deletion/reservation, incompressible large carrier, rollback and ordinary-writer bypass. A candidate failing any required invariant is not activated; retain its failure evidence and refine the design without narrowing full exact-key requirements. This spike selects a native procedure, not qualification from a pure encoder pass.

### Candidate native guard statement sequence

1. Within the operation savepoint and catalog/configuration/business hierarchy, resolve the complete planned sorted routing-bucket set from independently admitted full namespace/key bytes.
2. For each bucket, issue a native guarded row touch that writes its existing generation unchanged and returns its identity/generation. This proposes a real native row-version/write-conflict fence, not a SELECT/advisory-lock-only observation. Its privileges and own-transaction behavior must be qualified.
3. If no visible guard exists, attempt a protected insert at generation zero. A native identity collision means the attempt cannot establish fresh absence; roll back its savepoint and report whole-transaction retry under the adapter protocol. Do not suppress the collision and continue from an empty old-snapshot SELECT. A fixed-snapshot write conflict likewise retries; never change host isolation or end its transaction implicitly.
4. After all guards are established, observe/revalidate complete matching full namespace/key rows and reservations through a separate qualified native statement observation. A single CTE whose snapshot preceded a lock wait cannot inherit this freshness proof. For read-committed, the procedure must prove the second observation is fresh after exclusion; for fixed snapshots, its earlier guard touch must prove no prior committed membership change is missing or produce the native retry outcome.
5. Apply admitted canonical/key/reservation effects only after exact comparison and full validation. Increment the logical generation for each actual bucket membership/reservation mutation, with checked bigint exhaustion, atomically with those effects. The guard touch itself preserves logical generation; it is exclusion bookkeeping, not a graph mutation or feed event. A create-or-skip/no-op may touch exclusion without fabricating graph version/history/source facts.
6. All failures restore prior candidate state through the qualified savepoint/whole-transaction protocol. Locks may remain under caller transaction lifetime; the library never claims a released savepoint refreshed its snapshot or ended its exclusion. Existing original-attempt unknown outcomes follow CONTRACT-007 rather than blind retry.

This is the selected statement-order candidate for the disposable spike, not evidence that these native observations work on every adapter/server/isolation combination. Prove it with independent clients/barriers and exact native SQLSTATE/outcome capture before accepting the profile. Raw canonical SQL with only a late row trigger cannot advertise this preplanned protocol unless separately shown to satisfy its hierarchy and conflict coverage.

## Implementation Sequence

1. Create canonical fixtures and native failing tests in the planned test files.
2. Implement pure canonicalization/extraction, then transactional key maintenance and constraint error mapping.
3. Wire parameterized lookup with visibility and read pinning; exercise update/backfill and concurrent races.
4. Publish evidence only after the complete qualified family matrix passes.

## Risks and Gates

CONTRACT-001 defines string, binary, timestamp, integer and decimal key policies but does not fully specify every UMF family, explicit-null components, collation/normalization or size limits. Resolve those shared policies before claiming general key support. AC4 covers absence, not permission to equate null with absence. D-05's stored numeric lexical preservation decision does not change decimal key equality. Accepted ADR-004 supplies document-qualified catalog identity. Export to Weft still requires original authored key/source correspondence and the complete selected installed mapping; no identity product vote remains pending.

### Migration design handoff

Consume CONTRACT-001's `truss-key-profile-migration/0.1.0` ordering: original request capture, exclusive admission before lower locks, complete live/reserved inventory, qualified exact conversion, full collision assessment, transactional target staging/policy verification, atomic binding/receipt switch and original-attempt reconciliation. Do not implement conversion from key text when deleted reservations lack preserved components. Postcommit reversal is a new complete migration; retained old tables cannot overwrite later writes. B-004/B-008/B-010 and B-003 must jointly supply the exact native exclusion, DDL, installed-policy/receipt inventory and feed transition before execution.

### Candidate bounded native bucket observation

The draft route indexes now include internal storage_row_id after the two fixed digests. This is fixed-width ordering for bounded candidate inspection; full namespace/key/context artifacts remain outside indexes. After the already specified guard touch and qualified fresh observation, query each live/reservation store separately for at most 10,001 matching routing rows ordered by storage_row_id. First return only store discriminator, internal ID and native octet lengths of namespace/key, with exact canonical integer transport. A combined candidate total above 10,000 rejects before full-byte fetch; do not call the first 10,000 a complete bucket. Account both stores and all hidden integrity candidates, including digest-colliding distinct namespaces.

Accumulate admitted metadata lengths with exact integers against the 16 MiB full namespace/key byte budget across every planned bucket in the operation, including old/new removal-only buckets. A candidate reaching the permitted row/byte bound is allowed only when the independently bounded lookahead proves no further required candidate and the full fetch correspondence is exact; over-limit or unknown completeness refuses before effects. Repeated occurrences of a bucket are deduplicated in the complete sorted operation plan, not silently scanned twice into inconsistent limits. Native statement/work timeout and cancellation/termination/savepoint procedures remain the selected execution-profile obligations; LIMIT alone cannot qualify bounded native work or a query plan.

Only after complete metadata admission fetch those exact internal IDs under the same guarded observation, then verify row identity/count, full namespace/key octet lengths and original encoding/owner context. A missing/extra/changed row invalidates the observation; never turn it into absence. Compare full bytea namespace and key against admitted original candidate bytes. Distinct full identity sharing routing digests remains legal; equal full identity follows actual live/reservation policy. Postmetadata effects, RLS filtering and later guard acquisition cannot alter completeness. The native profile must establish one coherent guarded metadata/full-byte observation, including own earlier operations and fixed-snapshot retry behavior; an integrity observer cannot expose hidden candidate payloads to the ordinary caller.

This is an authored query/admission procedure candidate, not a native plan/capacity pass. Actual statement templates, privileged integrity observer/ordinary result disclosure, generation mutation triggers, context codec, direct-writer coverage and native profile qualification remain open.

[Draft native statement templates](../contracts/key-bucket-observation-v0.1.draft.sql) now explicitly separate guard touch/insertion, per-store 10,001 metadata lookahead, bounded exact-ID full fetch and checked actual-effect generation advance. Do not execute them as one CTE or concatenate them into a single pre-wait observation. Complete planned guard admission precedes both metadata statements. Parameter identities/digests/arrays/effect count originate from the admitted procedure, not user SQL. Full fetch verifies exact admitted IDs/lengths and original context; zero-row generation advance restores the operation or enters recovery, never reports applied. Exact ordinary/privileged role procedure and failure mapping remain open.

Full fetch also returns original context/reservation bytes, whose selected archive resource budget is separate from the 16 MiB namespace/key comparison budget. Metadata now includes original_artifact_bytes_length for both stores; admit these exact lengths and whole encoded output before fetching. This closes the earlier missing metadata projection, while native metering/decoder/profile adoption remains open. A small key cannot bypass a large original artifact budget. Native bytea/array parameter/decoder and output/work/cancellation profiles remain explicit dependencies.

The native bucket invocation resource profile must register positive exact `originalArtifactBytes`, `encodedOutputBytes`, `workUnits` and statement/cancellation limits in addition to namespace/key comparison rows/bytes. No absent resource profile means unlimited. Accumulate original artifact lengths across all admitted live/reserved rows and planned buckets before full fetch, even when originals later resolve to the same catalog archive. Admit exact driver wire/decoder expansion and bounded envelope overhead independently before fetching; bytea/base64/hex modes require their own qualified output accounting and cannot share an unverified factor. Whole decoded/encoded buffers and archive verification work remain charged through completion. Boundary equality is permitted only with complete candidate/output accounting; unknown output bound refuses before full fetch.

After fetch, independently measure exact returned native byte lengths and original artifact/decoded/encoded output against admitted metadata and actual limits. Any mismatch or exhaustion restores the operation before clean refusal or enters native recovery if cleanup cannot be established. Never disclose a partial collision candidate, rewrite original reservation context, or report not_found from a budget-exhausted fetch. Metadata sizes and actual output admission are integrity observations, not ordinary caller-accessible row information.


## Candidate bucket-source migration collector ordering and locators

For an already admitted bucket installation, the source collector enumerates the live record/binding domain before the reservation domain. Live stream ordering is native numeric `(type_id, object_id, key_num)` ascending, never text ordering of decimal IDs. Enumerate every original applicable object/binding from the accepted source catalog under the migration exclusion, including sparse omitted instances; enumerating only `object_key_bucket` cannot establish this domain. Join held rows back to exactly that original object/binding. Missing expected held row, duplicate holder projection, unexpected key row, wrong type/definition or missing omission report makes the inventory incomplete/invalid. Original graph version and envelope/component evidence must agree with this same source cut.

The live locator is the complete native typed object identity plus local key number and original binding/definition artifacts. It identifies the applicability instance even when there is no held key row. A held projection additionally records its bucket storage row ID in raw evidence; that row ID cannot replace the live applicability locator. Reservation stream ordering is native positive `storage_row_id` ascending from the admitted reservation store. Its locator binds the original installation/store definition, exact row ID and original reservation bytes. Equal namespace/key bytes across locators do not merge them. Internal row IDs are not exported as authored identities or replay authority.

The complete collector first validates native source store/definition/policy inventory against the selected source basis; then captures both ordered streams and their complete exhaustion witnesses under the original exclusion/cut; then assigns the ordinal entry profile across the concatenated streams. Every entry's original locator witness remains in `collection.rawEvidence` with complete entry-to-locator correspondence. Hidden rows participate under the integrity observer without disclosing their artifacts in an unauthorized public result. Row/byte/work/report exhaustion prevents a complete source inventory rather than publishing an apparently complete prefix.

This candidate governs bucket sources only. Legacy reservation sources without these native row identities require their own original locator/ordering/capture profile; a reconstructed current graph row is not an acceptable substitute for a deleted reservation. Source profile mismatch refuses before collecting under the wrong grammar. These rules close ordering and locator meaning for the candidate, while exact native catalog applicability/component decoding, exclusion procedure, raw evidence wire and privilege/resource profiles remain design outputs. No native collector has been implemented or executed.

[Bucket collection evidence declaration](../contracts/bindings/truss-key-migration-collection-v0.1.d.ts) represents the original attempt/source/installation/exclusion/cut, complete applicability evidence, exact ordered entry-to-locator/source-entry correspondence and separate live/reservation exhaustion witnesses. This artifact is captured before composing the source inventory; it must not reference the later inventory digest. Native evidence admission checks locator kind and held/omitted classification against the corresponding source entry, exact ordinal/order and complete scope. Empty entries do not waive either exhaustion proof. Hashes or public projections cannot substitute for original raw bytes.

[Closed bucket collection wire](../contracts/key-migration-bucket-collection-v0.1.schema.json) supplies original locator and applicability/exhaustion grammar. Ten structural controls cover held/omitted/reserved/empty variants, missing domain/exhaustion, count substitution and zero row identity. Mismatched cuts and duplicate locators intentionally remain shape-valid semantic counterexamples. Native bigint range, ordinal profile, original artifact bytes and complete correspondence require admitted native/profile evidence.


## Candidate admission-state observation and switch

[Three separate unapplied admission templates](../contracts/migration-admission-statements-v0.1.draft.sql) observe metadata, fetch original bytes and conditionally switch exactly one row. Metadata lengths include original identity and all artifact bytes; admit full driver/output expansion before fetch and independently compare fetched lengths/scalars/bytes. Head exclusion must remain held between these separate statements. A same hash or prior generation alone cannot substitute for complete original configuration/binding/inventory comparison.

Switch requires the independently admitted original and target artifacts, unchanged epoch/installation/reuse/journal policy, exact original generation and remaining bigint capacity. Verify target configuration decodes to original generation plus one and preserved policies before submission; SQL cannot infer its contents. Exactly one RETURNING row denotes pending update only. Zero rows refuses/rolls back under the original containment protocol; transport loss cannot determine whether update happened. Original returned evidence and receipt are captured in the same transaction; later qualified commit observation establishes durability. Retry never invokes switch again solely because returned hashes match a current installation. Original initialization inserts the admission row only with full independently verified bootstrap artifacts; recovery uses original archives rather than constructing old state from the current row.


## Candidate bounded original migration receipt lookup

[Receipt observation templates](../contracts/migration-receipt-statements-v0.1.draft.sql) use the full original identity's independently derived three SHA-256 routes. The selected owned administrative READ COMMITTED lookup holds the original head exclusively until its coherent receipt inspection terminates; participating receipt insert/purge cannot race its two statements. This is a selected migration/recovery lookup profile, not an implied read-only historical client protocol. Actual native termination/custody and original producing transaction evidence remain separate from row inspection.

The candidate admits at most 10,000 complete route rows and uses 10,001 lookahead. Count every row, including unequal full identities sharing the route; overflow refuses without proving absence. Before fetching bytes, sum all original installation/epoch/attempt identity, request, original attempt and receipt lengths under selected positive artifact/input/output/work limits. Driver expansion and result envelope/metadata overhead also count. An unknown bound cannot mean unlimited. Native query work/cancellation limits remain necessary because SQL LIMIT alone cannot prove bounded CPU.

Fetch only the complete admitted storage-ID list and require exact original ID/order/count/length/scalar correspondence. Compare complete installation/epoch/attempt bytes privately; zero matching full identities means only no receipt visible under this admitted lookup. It does not prove an uncertain original transaction rolled back, release original recovery custody, or permit replacement migration. One exact match requires original request/attempt byte parity, receipt/profile/archive/transaction admission; multiple matches are integrity failure. A current binding equal to the target cannot replace these observations, and an old committed receipt cannot overwrite newer current state. Metadata/fetch mismatch or incomplete native observation refuses/requires original recovery, never false absence.


## Same-store migration staging

CONTRACT-001's truss-key-same-store-migration/0.1.0 explicitly accounts for the live bucket's unique object/type/key tuple: retain complete converted candidates privately, revalidate source correspondence, replace exact admitted memberships inside the original owned exclusive-head transaction, independently observe pending target parity, then switch/finalize. Old/new memberships cannot coexist in that store, and private staging cannot claim native parity. Full original archive/locator correspondence survives replacement; any failure rolls back every store. Shadow stores require a separate admitted layout, not an unstated generation column or weakened uniqueness.


## Migration evidence component handoff

| Planned component | Owned responsibility and boundary |
| --- | --- |
| packages/core/src/migrations/evidence.ts | Pure bounded decoding/structural/byte/profile correspondence and exact integer/action checks for source, target, locator, switch and admission candidates. No SQL, native lock/role/commit observation, ambient clock or producer authority is minted from a valid tree. Consume UMF's admitted encoder; do not implement a competing portable encoder. |
| packages/core/src/migrations/archive-plan.ts | Pure iterative declared-dependency enumeration, exact identity/conflict/visited bookkeeping and original whole-ledger node/edge/byte/work reservation. Separate static original prerequisites from bounded later native evidence; semantic model cycles do not imply proof cycles. No archive fetch or trusted capture occurs here. |
| packages/postgresql/src/migrations/archive.ts | Resolve original retained homes through the admitted custody service, verify exact profile/owner/context/bytes and complete static closure before replacement. After native effects, admit actual dynamic artifacts within the original reserved domains/budgets before receipt publication. Failed post-effect closure uses original rollback/recovery, never a fabricated pre-native refusal. |
| packages/postgresql/src/migrations/admission.ts | Original owned transaction/exclusion, metadata-before-fetch singleton and complete source collection with native scalar/full-artifact parity. Actual executor/native context remains private and is not reconstructed from snapshot strings. |
| packages/postgresql/src/migrations/replace.ts | Complete private target candidates, original source revalidation, capacity/guard preplanning and exact same-store row effects. Capture actual old/new locator and guard correspondence; no binding publication or commit proof here. |
| packages/postgresql/src/migrations/switch.ts | Independently compare pending native target state, decode complete prior/resulting admission, build original precommit switch evidence, persist receipt-backed closure and transition/finalizer effects in the same transaction. Original commit/recovery comes from the executor, never receipt presence. |
| packages/tooling/src/migrations/keys.ts | Existing inert administrative tooling entrypoint, explicit migrate/reconcile orchestration and phase/resource/containment classification. No import-time connection, worker, automatic retry or mutation of captured assembly selections. |
| packages/conformance/fixtures/migrations | Independent expected byte/shape/semantic/native schedules, keeping fixture producer separate from actual original native evidence. Host/runtime adapters enter through the harness; browser core consumers remain independent. |

Implementation order is pure evidence admission, original native collection, private conversion/complete assessment, protected replacement, pending target/switch finalization, then original commit/recovery/disclosure. A pure valid snapshot or correspondence object cannot skip any later actual-native step. Scope-qualified browser/package checks apply to pure core; Bun/Node connection/decoder behavior and PostgreSQL native roles/resources/faults require their separate checks. These paths are planned implementation boundaries, not code already present.

### Shared lookup implementation boundary

TD-020/CONTRACT-004 now author baseline and full-byte read-only lookup templates plus native record/context projection and a named finite lookup resource candidate. keys/read.ts delegates to the shared reads/lookup.ts binding and decode-record.ts layer; it does not maintain a parallel lookup algorithm. Mutation guard-touch/insert/high-water/resource procedures remain writer/migration boundaries, never a required write inside a read-only lookup. Exact selected full-byte integrity/snapshot/policy/protected-entrypoint/canonical transport and decoder adoption remain open, separately from portable UMF encoder validity and Weft mapping/compiled execution.


### Conditional lexical change with equal qualified key

Apply CONTRACT-004's adopted lexical-profile update semantics and CONTRACT-010 NX correspondence without using NX as a key encoder. Derive old/new full key bytes through the exact selected existing UMF portable operation when applicable, or the separately adopted Truss storage-key profile. Full owning document/Record/key definition, encoding/epoch and component order remain part of identity; equal mathematical tuples or equal payload bytes across different keys cannot establish equal membership.

When complete original derivation proves held-to-equal membership, preserve that membership and its original locator under the selected key profile. The genuine token/source property change still advances owner version and selected journal/history; no artificial old-key reservation, replacement namespace or migration is warranted by lexical spelling alone. Existing required bucket exclusion/freshness fences still execute under CONTRACT-009 and charge real work; unchanged membership does not permit skipping current conflict/canonical correspondence or forging a generation observation. Native maintenance effects are checked against complete original effect scope.

Do not mutate the source token to obtain canonical key bytes. Equal key identity cannot make the property update a no-op, and property lexical inequality cannot choose a different key profile. If old/new key derivation or codec/context/facet correspondence is unavailable, refuse the complete update with existing original containment; no guessed identity can authorize reuse. STP-009 supplies lookup/contender/rollback controls after exact profile adoption.

### Equal-membership guard and finalization procedure

A held-to-equal result is established only after full original old/new derivation under the admitted current catalog, key encoding and source/codec profiles. Keep the complete affected key namespace/bucket/owner guard in the original group plan even if the eventual key bytes match. Acquire/revalidate that guard through the ordinary hierarchy before canonical replacement; a prelock mathematical comparison cannot remove it from the plan. If locked observations change the required owner/bucket set, follow contained discovery restart rather than writing under the earlier set.

For a complete held-to-equal result, preserve the original key row/locator and avoid synthetic removal, reservation or reinsertion. Increment a bucket generation only for the actual membership/reservation mutations its original profile specifies, not merely because a source token changed. The property mutation still contributes its original source/token/node touch and version/history/journal effects to the protected operation registry. Equal key bytes do not waive full key derivation, complete current membership/duplicate/reservation observation or independent canonical-to-key finalization. Finalizer coverage identifies the original affected key even when no key row changed; observing only key-table trigger activity is insufficient.

Before pending success and again under the selected unavoidable commit proof, compare complete current canonical components and the surviving derived key against the admitted expected original definition/encoding. A missing/extra/wrong owner key row, unsupported facet or changed original source/profile refuses the operation/profile under the governing containment rules. Preserve complete earlier operation/current-union custody; a key from a different owner or stale source cannot corroborate this operation. Engine checks alone remain engine evidence until the selected direct-writer/native producer and privilege closure makes these checks unavoidable.
