# Installed context admission composition candidate

Status: proposed implementation handoff. Governing artifacts: CONTRACT-008
committed installation/inventory, CONTRACT-007 executor/recovery custody,
CONTRACT-003 originalExecution and installation-admission-v0.1. The existing
InstallationAdmissionSnapshot is a projection, never an authority token.

## Producer composition

Register one immutable Truss installation-admission composition with the host
assembly before exposing protected capabilities. Reuse registered bootstrap
inventory collection/definition/integrity and executor services; do not create
a parallel namespace inspector or let UMF/Weft select deployment identity.
Registration captures original executable references and exact profiles for:

- Trusted deployment identity/incarnation admission, including declared
  restore/fork/replacement handling and original target evidence.
- Committed installation marker/archive admission and complete selected native
  definition, role/policy/entry closure and expected-inventory correspondence.
- Native current-epoch lock/readback and original actor/connection capture.
- Complete configuration and selected binding interpretation, original resource
  accounting and recovery evidence retention.

Construction is inert and rejects unknown/mismatched selected pins. It does not
acquire a connection, inspect a namespace, generate an epoch or call a producer.
Each protected operation performs native admission on its original issued
executor/transaction; matching labels or a previously returned snapshot cannot
replace that operation's live evidence. Changed service metadata closes new
admission; outstanding uncertain attempts retain their original composition.

## Admission order and exact evidence

1. Admit current assembly/executor affinity and trusted target incarnation.
   Bind actual database/schema observations to this target; names/OIDs and
   copied installation metadata alone cannot establish it. Refuse unavailable
   restore fencing before writes.
2. Establish committed installation evidence through the registered bootstrap
   procedure. Do not classify a marker inserted in the current transaction as
   a committed installation. Retain original complete marker/archive/inventory
   observations with their issuer, cut and original attempt correspondence.
3. Hold the current epoch pointer shared lock. Compare original independently
   admitted installation/incarnation with the native registry; retain exact
   epoch profile/evidence bytes. The private epoch helper proves comparison and
   lock behavior only. Missing/unsupported epoch evidence closes admission.
4. Admit complete installed definition/entry/policy/resource composition under
   its qualified coherence procedure. Compare expected original inventory,
   actual retained bytes and complete required dependencies. The marker hash
   is a route to retained evidence, not proof of current native parity.
5. Capture original configuration generation, exact configuration and selected
   binding bytes, keyReuse and journalMode from the admitted native producer.
   Unknown settings or inaccessible rows refuse; caller options, defaults and
   current catalog documents cannot supply these facts.
6. Capture the native original role names/OIDs/executor together with separately
   asserted operation origin. Retain complete installed-context evidence under
   the selected capture profile. The role-only native context remains a
   component and cannot serve as the complete installed artifact.
7. Issue an internal original-admission object bound to this exact assembly,
   executor, native transaction, composition and retained observation. Its
   snapshot projects the existing closed wire shape. Copies/serialization do
   not preserve internal issuance; even the original is rechecked at use.

Do not assume a shared epoch-pointer lock protects arbitrary DDL, role changes
or configuration changes. Those require the selected inventory/security/
configuration exclusion procedures independently. Recheck original epoch,
configuration and native operation cut before protected publication. A callback
must not transition the epoch on the same transaction behind its original
admission; the lifecycle procedure and writable operation composition must
exclude that case explicitly. Row locks alone cannot forbid a transaction
upgrading its own lock.

## Configuration capture time and immutable operation custody

Step 5 MUST finish before the operation's first catalog/business/journal effect. Collect generation, keyReuse, journalMode and exact configuration, selected-binding and installed-inventory bytes from the admitted installation under its original head/configuration exclusion. Validate bounded metadata before copying artifacts, retain all three full byte sequences, and charge retained bytes plus transport/encoding expansion to the complete operation resource ledger. Full-byte correspondence is required in addition to digest checks.

The native operation registration and retained configuration capsule form one atomic admission cohort. The capsule binds the original writer xid/operation ordinal, installation/epoch/incarnation, configuration generation/scalars, original artifacts and their selected interpretation/capture profiles. It is immutable for the operation. Current configuration remains a separately observed fact; a later same-transaction update cannot rewrite the capsule or retroactively alter originalExecution. A transaction can mutate data despite holding its own exclusion, so the qualified protected path must explicitly forbid or fence configuration/lifecycle changes while an affected operation remains live. Locks alone do not establish that rule.

Current `runtime_collect_catalog_original_configuration` and its host basis collect **current bytes under original operation custody**. They require a prepared report and therefore run after staging in the existing component. Their current native row may even have been inserted after operation admission. Original collector issuance and exact repeat rechecks prove byte/cut correspondence at collection; they do not prove historical admission-time capture. Their scope is current_configuration_byte_basis_under_original_operation_only, and they cannot supply the immutable original configuration capsule or complete originalExecution.

| Temporal boundary | Required comparison | Failure behavior |
| --- | --- | --- |
| Before operation registration/effects | Original committed installation plus current configuration, selected profiles and complete capture capacity | Missing/newly provisional configuration or unsupported meaning refuses before operation effects |
| Admission cohort persisted | Independently compare retained full capsule with native source observations and exact original operation identity | Partial/missing/copied capsule or mismatched identity prevents admission; no generation-only success |
| Use and publication | Compare live configuration/epoch and complete applicable authority with immutable admission capsule under the qualified current-state profile | Changed generation/scalars/artifacts or lifecycle closes that operation's publication; newly collecting current bytes cannot replace the original capsule |
| Savepoint rollback | Preserve the adopted caller's earlier work while independently resolving capsule/operation/effects and original retained recovery custody | Rolled-back rows cannot leave an issuable original object; unresolved native end remains recovery_required |
| Exact request replay | Retain original historical result/context while separately admitting the current invocation and disclosure | Current configuration cannot rewrite the old report; incompatible required interpretation or unavailable original custody refuses |
| Cleanup/retention | Retain required capsule/result correspondence through report/history/receipt and unknown-attempt protections | Stage absence is not proof of settlement or authority to discard recovery evidence |

Realization must author the snapshot home, its fixed operation parent/immutability/cleanup links and initializer in the UMF layout before installation. Existing context0.4's one-MiB inline context and the collector's sixteen-MiB aggregate configuration limit are distinct component limits: do not append oversized hex artifacts to that context or silently widen its profile. A separately retained capsule/archive reference still requires complete original byte custody and compound resource accounting. Existing installation_admission remains the current configuration authority; the capsule is historical operation evidence and introduces no independent installation identity or ACL resolver.

Required native schedules extend the existing negative matrix: change configuration before the first late collection and demonstrate that it sees later bytes; install the qualified pre-effect capture, then change configuration in the same transaction and verify original capsule retention plus publication refusal; corrupt/delete one capsule sibling; restore changes by savepoint rollback; race another writer with configuration transition; and retry a committed old request after a compatible current configuration change. Retain full expected old/new bytes and independently observed operation/report/effect outcomes. The current late-collection witness establishes the gap; only the qualified pre-effect producer and protected publication schedules close it.

## Operation configuration storage and initialization handoff

The [UMF adjunct](operation-configuration-storage-v0.1.proposal.umf.json) supplies the proposed fixed `operation_configuration` home. [Owner-generated DDL](../../04-build/evidence/operation-configuration-storage.owner-export.sql) has sixteen columns, a primary key `(original_writer_xid, operation_ordinal)`, the existing operation-parent FK and `(installation_id, source_epoch)` registry FK. Both FKs use default no-action behavior; parent deletion cannot cascade away historical custody. The adjunct leaves the existing 0.16 candidate unchanged and is not an installed layout version.

The remaining columns retain exact installation/epoch/incarnation, nonnegative bigint configuration generation, selected keyReuse/journalMode, original-context SHA-256, original admission profile bytes, three complete configuration/binding/inventory byte artifacts and their three generated SHA-256 columns. Text identity columns use native C collation. Individual artifacts are nonempty, the combined artifact limit is sixteen MiB, admission profile bytes are at most 65,536 bytes and context digest is exactly 32 bytes. Those checks constrain storage shape; native admission must reserve capacity before materialization and apply the combined operation/capsule/transport budget.

Initialization is one protected admission cohort: observe original configuration under the selected exclusions; allocate the operation identity under the existing native procedure; retain the operation and capsule atomically before effects; independently compare full bytes/scalars with the original source; and issue host custody only after complete native correspondence. Insert exactly one capsule per operation with no upsert/replace path. Registry FK membership alone does not validate target incarnation or admission profiles: compare the complete original epoch evidence and selected profile semantics. `original_context_sha256` must match the operation parent's complete retained context bytes, with full context custody retained separately. A caller cannot supply a digest to bypass that comparison.

The protected path must forbid capsule UPDATE and ordinary DELETE. Cleanup uses the existing qualified whole-operation settlement/retention procedure after complete historical report/receipt/recovery handoff; delete the capsule before its operation parent under independently observed complete cohort custody. Unknown settlement or missing retained historical artifacts prevents cleanup. Public/ordinary native callers receive no direct write path; actual owner/grant/helper policies come from the security workstream's complete inventory. A PUBLIC revoke in this adjunct does not prove that inventory.

UMF import and saved reload/export are exact. A rollback-only native check observes sixteen columns, two FKs and three generated digest columns; it also observes zero user triggers, making the missing immutability/admission/cleanup procedures explicit. Source pins and [native observations](../../04-build/evidence/design-audit/operation-configuration-native.json) retain their limited scope. The core structural column/parent/epoch projection is now available in model 0.5 and the local schema browser. It preserves the native xid8 key gap through full physical descriptors and core record/field references, matching the existing hybrid route; no portable equality is invented. Before composition, author complete native producer/guard/cleanup dependencies and independently qualify IC-T01–06. Source generation and successful DDL do not establish those semantics.

## Private pre-effect implementation checkpoint

`operation-configuration-context-admission.sql` derives a separate private admission routine from the original epoch admission source. It preserves epoch/catalog exclusion order, original actor/context checks, the four-MiB input-artifact and one-MiB context limits. Under the head exclusion it checks current configuration artifact sizes before copying, compares original installation/epoch, and inserts the operation parent plus immutable capsule in one native statement before catalog staging. It takes separate configuration admission profile bytes; the origin capture profile keeps its original meaning.

The new component limits retained configuration artifacts to sixteen MiB, profile bytes to 65,536 bytes and the combined original input/epoch/configuration/profile/encoded-context logical bytes to twenty MiB. These are explicit bounds for this new private producer, with no change to context0.4's wire or existing admission profiles. PostgreSQL work/memory, transport copies, enclosing group resources and semantic profile registration remain separately qualified composition outputs.

`operation-configuration-immutability.sql` installs ENABLE ALWAYS row UPDATE/DELETE and statement TRUNCATE refusals. Cleanup deliberately remains unavailable; a finalized phase or arbitrary caller flag cannot erase the capsule. `operation-configuration-current.sql` compares original native context/cut/epoch and complete current generation/scalars/full artifact bytes with the retained capsule, checking current sizes before copying. This callable component is not yet an unavoidable public finalizer guard.

The native staged cohort records 157 checks, including capture before any new type row, maximum bigint generation, exact original artifacts/profile/context association, missing/mismatched/oversized input refusal, failed sibling insertion rollback, changed generation/scalars/artifacts, oversized current bytes, immutable-store refusal and complete admission savepoint rollback. The implementation test uses synthetic installation/incarnation and unregistered component profile bytes. Complete committed installation/interpretation/security/driver/resource admission, host-issued capsule projection, protected cleanup and public report/head/finalization still remain required. IC-T01–06 retain their full public/historical/concurrency scope; component checks do not mark those whole cases passed.

## Original snapshot host projection and shared native wire

The private `runtime_collect_catalog_admission_configuration` method takes original writer xid, operation ordinal and effect generation as canonical decimal text, plus expected configuration profile bytes as nonempty lowercase even hex (at most 131,072 characters). It returns exactly one row with these ordered nonnull text columns: context_hex, configuration_generation, key_reuse, journal_mode, configuration_hex, selected_binding_hex, installed_inventory_hex, configuration_sha256, selected_binding_sha256, installed_inventory_sha256, configuration_profile_hex, configuration_profile_sha256. Missing/foreign original capsule, changed current state, wrong profile bytes or unavailable original cut refuses with native 55000; malformed profile transport refuses with 22023. It emits no partial successful row.

The three artifacts and separate profile are the immutable native admission bytes, with direct SHA-256 correspondence. context_hex is the exact original operation context. Generation is canonical nonnegative int64 text; key_reuse is forbid/allow and journal_mode is engine/trigger. Artifact hex remains byte transport, preserving original spelling and arbitrary bytes; selected registered profiles determine interpretation. Expected profile bytes establish byte correspondence only and do not authorize an unregistered meaning.

The TypeScript `catalog-admission-configuration-basis` collector requires original preparation/report/epoch/executor issuance, copies the expected profile before its first await, verifies exact columns/scalars/full context/profile/artifact hashes and bounds, then rechecks the original epoch/cut before issuing a frozen internal projection. The projection scope is original_pre_effect_configuration_byte_basis_only. Copied or serialized objects lose issuance; original objects still require native/current comparison at use. The older current-byte collector retains its distinct current-only scope.

Python may consume this same native wire through its qualified original adapter, using exact text, bytes.fromhex, direct SHA-256 and immutable byte ownership. It must retain original connection/transaction/cut/profile custody and reproduce the same pre/post rechecks; a dictionary with matching fields or int-converted xid cannot establish issuance. Preserve native error/outcome meaning and disclose results through the security workstream's admitted boundary. No Python UMF interpreter, ACL resolver or alternate configuration identity is introduced.

The staged cohort now passes 171 component checks, including mutation of the caller's profile array while collection is pending, exact profile/artifact projection, copied-object and wrong-profile refusal, current changes and ended-transaction refusal. Registered interpretation, committed installation/security/resource/driver profiles, historical recovery projection and unavoidable public finalization remain required; this live collector cannot substitute for retained historical request context during replay.

## Historical custody and cleanup dependency closure

The [private custody reference](bindings/truss-configuration-custody-reference-v0.1.proposal.d.ts) addresses one original installation/epoch/incarnation, full native writer xid, operation ordinal and configuration generation under an exact custody profile, with original capsule identity/hash/byte length. It is a lookup locator, never a read grant, settled outcome or deletion certificate. Xid is canonical unsigned native text and ordinal/generation are canonical nonnegative int64 text. Resolution admits original target/profile/authority and full original bytes, source membership and settlement evidence; source epoch or matching current configuration cannot replace that correspondence. The reference introduces no public report field, identity allocator or parallel archive envelope.

Keep the operation_configuration row and operation parent locally until complete dependency closure permits their removal. Preserve their original bytes as a cohort; generation-only matching, rewriting a historical row to the current incarnation or deleting its parent first cannot discharge custody. If a qualified durable handoff is selected, reuse the existing provider-neutral archive submission/retrieval/protection procedure. The selected archive composition must explicitly cover operation/configuration artifacts and their dependencies in addition to per-record history. The current per-record v0.2 archive and unadopted S3 candidate do not establish that coverage. Configuration bytes cannot be put into a definition slot merely to satisfy an existing shape.

| Dependency | Required retained correspondence | Cleanup condition |
| --- | --- | --- |
| Complete accepted report and catalog interpretation | Original report/context/capture/mapping profile, full configuration/binding/inventory interpretation and source archive | Original required context is retained/retrievable for the advertised report/history horizon; a locator or current row alone is insufficient |
| Committed request receipt, including all-no-op | Exact original request/result/context and original confirmed transaction outcome | Receipt/retry/expired-identity protections and disclosure remain satisfied independently of event history; no synthetic journal member is created |
| Complete feed transaction | Every producing operation's original configuration interpretation and full required prerequisite bytes | Complete manifest/prerequisite/application/ACK and admitted consumer protections cover the original transaction before source cleanup |
| Pending adopted transaction or unknown original attempt | Original operation/capsule/executor/profile/resource evidence and unresolved settlement | Remains locally protected until original settlement, mandatory cleanup and qualified retained recovery correspondence are established |
| Configuration/lifecycle transition | Original prior/resulting configuration and explicitly selected epoch/incarnation lineage | Both sides remain available wherever retained historical results or consumers require them; same-name restored state is not original evidence |
| External archive | Complete original artifacts, target/profile/coverage, confirmed durability and verified bounded retrieval/lifetime | Existing protected retention procedure freshly admits every current dependency; upload callback, provider digest or old cleanup permit is insufficient |

Feed registration derives selected mutation configuration and prerequisite artifacts from each producing operation's original capsule through the registered configuration interpretation. It never reads today's installation_admission to reconstruct old semantics. Deduplicate shared prerequisites only after exact semantic identity and full-byte/profile correspondence; retain operation-specific context/custody independently. Distinct actors/ordinals cannot borrow another operation's original authority by sharing a generation. Full private installed inventory and native actor observations are not automatically public feed payloads: the security workstream supplies the admitted disclosure/projection, and unavailable required disclosure prevents complete publication.

Per-record reconstruction cannot prove closure for a no-op receipt, revision-only operation or unresolved attempt. Those have explicit original receipt/catalog/recovery owners even with zero graph events. Global cleanup must inspect these owners and complete operation membership under the existing common exclusion/settlement procedure. If required archive coverage is unavailable, retain local evidence and report cleanup unavailable; short/zero journal retention does not shorten independent receipt or recovery protection.

The complete report codec's one-MiB wire and the capsule's sixteen-MiB artifact bound are different profiles. Inline base64/context packaging must fit the report's complete enclosing account before publication. A selected compact capture manifest may use the private locator only with registered original full-byte resolution/lifetime semantics; it cannot silently replace existing context0.4 bytes or upgrade a digest into evidence. Unknown/incompatible capture/archive/resource composition refuses or retains local custody. No report schema pin or historical accepted bytes are rewritten by this handoff.

Implementation schedule: original capsule→complete report/receipt/feed prerequisite correspondence; current-state-independent historical lookup; whole-operation/protection inventory; original export/provider retrieval coverage where selected; atomic protected cleanup and original unknown-outcome recovery. Required independent cases are old request retry after configuration change, all-no-op receipt without graph events, held/unknown operation protection, multiple operations sharing versus conflicting configuration, revision-only feed prerequisites, denied private evidence disclosure, undersized report encoding, archive omission/corruption and protection added between archive verification and cleanup. Native historical resolver/projection, selected operation-artifact archive coverage and exact finite accounts remain implementation/adoption outputs; stage DELETE remains refused until they exist.

## Decisive implementation schedule

Use packed public capability exports plus their registered original services.
First positive case: independently committed fresh installation and native-issued
epoch admit one complete original snapshot/context. Verify every field against
its original producer, not another projection of the same object. No fake
installation ID, epoch, inventory or configuration artifact is acceptable.

Negative schedules: provisional marker; copied/changed issuer object; different
connection/transaction; wrong namespace/incarnation; unreported restore;
unsupported profile; incomplete archive/dependency closure; current policy or
configuration change; actor role recreation/definer substitution; stale epoch;
same-transaction epoch transition after writer admission; materialized resource
exhaustion; native observation failure; lost commit response. Each retains the
original recovery outcome and refuses before new effects where admission has
not completed. Exact repeat keeps historical report context while admitting
current invocation independently.

Exit: complete registered procedure, actual installation/authority/resource
qualification and originalExecution parity. Native epoch component receipts
are prerequisites, not evidence that this entire composition exists. Adoption
remains unfinished; this handoff introduces no public callback, new snapshot
field or independently authoritative installation identity store.
