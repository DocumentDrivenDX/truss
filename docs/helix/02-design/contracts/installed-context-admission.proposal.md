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
