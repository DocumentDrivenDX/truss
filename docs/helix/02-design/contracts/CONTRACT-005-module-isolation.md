---
ddx:
  id: CONTRACT-005
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-002
      kind: informed_by
    - id: SPIKE-003
      kind: informed_by
---

# Contract: Module isolation

**Contract ID**: CONTRACT-005
**Type**: schema
**Version**: layout 0.2 (draft)
**Status**: draft
**Related**: ADR-002 D14, CONTRACT-001 (tables, extension rules), CONTRACT-002 (`db_role`), SPIKE-003 F8, `module-isolation.sql`, `module-isolation.check.sql`

## Purpose

Defines an optional layer that lets a deployment give database roles read or write access to some UMF modules and none to others, enforced by the database. Truss selects the UMF module as its policy unit because types and relationships carry module identity. This is a Truss deployment policy choice: UMF core module/namespace does not declare a DDD bounded context. A deployment may attach additional semantic extensions without changing core module meaning.

## Scope and Boundaries

- In scope: the `module_access` table, the row-level security policies, the privileges the policies assume, which rows a role sees, cross-module edges, and how the acting role is determined.
- Out of scope: authenticating people, choosing which role a person gets, the write path (an engine, or functions a host writes), and the catalog revision itself, which is administrative.
- Owning project: truss. The layer is optional: with `module_access` empty and the policies not applied, truss behaves as in CONTRACT-001.

## Normative Surface

**`module_access`**

| Column | Rules |
|--------|-------|
| `module` | Primary key. The UMF module identifier as recorded on `type_def` and `rel_def`. A row MAY exist before the module has types. |
| `reader_role`, `writer_role` | Database role names. They MUST differ in a row. A role MAY appear in several rows, which is how one role reads several modules. A writer can always read its module. |

### Proposed protected row-home privilege profile

For CONTRACT-001's unadopted fixed row-home/dirty-generation layout, propose `truss-row-protected-privileges/0.1.0`. The registered deployment assigns exact native roles to the responsibilities below and records full grant/membership/ownership/routine/policy inventory under CONTRACT-011. Responsibility labels are not caller-supplied role names or grants. No role inherits or can SET ROLE into a broader internal responsibility from ordinary application authority; native membership/admin/options and routine dependencies require independent observation.

| Responsibility | Permitted selected entrypoints/store access | Explicitly excluded authority |
| --- | --- | --- |
| Application reader/writer | Invoke admitted read or mutation/import/group procedures according to actual current module grants. Read output only through qualified disclosure/decoder admission. | Direct canonical state/node/scalar/touch DML, allocator control, touch/seal/commit helper execution, integrity-observer reads and internal-role adoption. |
| Public read procedure owner | Selected read-only value collection needed by its registered query/decoder; actual original caller capture and current disclosure policy apply. | Hidden complete-integrity scope, all store mutation, sequence allocation, generation/seal updates and transaction termination. |
| Canonical mutation procedure owner | Selected state/node/scalar DML and qualified node allocator use under original owner/catalog/policy exclusions; execute protected touch observation/finalization only through the registered operation protocol. | Direct touch-row update/delete, caller-authored transaction identity/generation/seal, allocator reset and independent bypass of RF01–RF06/group obligations. |
| Touch observation owner | Read original OLD/NEW owner/source custody; create/update exact actual-transaction touch entries and dirty generations from unavoidable admitted write observation. | Sealing, suppressing prior operation custody, erasing unsettled entries, caller output and allocator reset. |
| Integrity/finalization owner | Complete private state/node/scalar/touch and original catalog/group/archive observation required by RF01–RF06; protected seal update after independent original scope/effect parity. | Application disclosure from private observations, mutation of canonical values as a validation side effect, accepting caller completion flags and sealing foreign transactions. |
| Commit-check owner | Complete private touch/registry/generation/context observation and native unfinished-closure refusal. | Creating success receipts, changing dirty/sealed generations, deleting obligations and public invocation. |
| Retention administrator | Selected guarded cleanup of actually committed settled touch/archive custody after original retention/recovery obligations are discharged. | Cleanup of current/unsettled/unknown-outcome entries, public application role impersonation and clearing guards to force commit. |

Native table/routine owners and administrative DDL roles are outside ordinary-writer support; they cannot be included through broad inherited grants. Deployment must revoke default/public helper execution and table mutation as appropriate to the exact selected inventory, qualify trusted namespace/search-path dependencies and independently verify actual effective rights. A trigger label or SECURITY DEFINER label alone supplies none of these guarantees. CONTRACT-001 now authors the five private reservation/observation/seal/commit-check/cleanup signatures and caller boundaries. Actual native routine bodies, exact type/security/owner/grant/dependency identities and selected RLS implementation remain realization outputs, not installed privileges.

Integrity completeness and public disclosure use different entrypoints/custody. The private finalizer may need complete hidden state to reject broken values, but it returns only the governing authorized outcome/diagnostic projection; it cannot disclose hidden node counts, value bytes, group identity or provenance. The public read path cannot reuse that privilege to turn a hidden state into absence. Actual caller capture remains the original data caller through nested helpers, with fresh current-policy admission and complete retained owner union for history/deletion/report disclosure.

This candidate deliberately restricts canonical table writes to admitted protected procedures. A baseline deployment allowing direct ordinary table DML is a distinct profile and cannot acquire row-home database-enforcement support just by installing the new tables. Activation must reconcile complete old/new grants, triggers, owners, routines and participating producer paths under the governing layout/policy exclusion; failure preserves the original profile. Request-free operations remain request-free; internal touch/group custody does not create a replay request; accepted ADR-005 applies only when request-present is selected. Tests must separately report database versus engine enforcement when native codec/producer closure is unavailable.

### Concrete role and callable binding required for body authoring

For the SQL/PL/pgSQL reference candidate, author each protected routine together with its exact ownership/privilege binding rather than attaching grants after the body. The installation manifest must bind the following original fields before CH-02 can claim that routine ready for composition:

| Binding field | Required original evidence |
| --- | --- |
| Native owner role | Actual role identity and login/superuser/BYPASSRLS/CREATEROLE/replication attributes, ownership and complete inherited/SET/admin membership paths |
| Callable identity | Schema-qualified name, ordered argument type identities, result type, language, exact body/hash and security mode; name-only EXECUTE targets cannot choose an overload |
| Table/column/sequence rights | Exact readable/writable columns and allocator USAGE; exclude reset/ownership/DML paths outside the responsibility matrix |
| Current caller | Original native actor capture before definer entry and preserved custody through nested private calls; routine owner is never substituted as the application actor |
| Trusted resolution | Fixed qualified relation/routine/operator/type dependencies and secure search-path behavior, including pg_temp/public shadowing refusal |
| Reachable private calls | Complete transitive callable graph with role transitions and separate integrity versus disclosure rights; internal helper access is not permission for public invocation |
| Public entry | Exact authorized application procedure/read surface and current module/owner policy; PUBLIC/default grants and inherited broad rights are independently absent where excluded |
| Administrative exception | Explicit deployment/DDL/retention/recovery authority, invalidation and original change-control path; never counted as ordinary writer enforcement |

Nonlogin internal roles are the recommended realization where the managed target permits their creation and ownership; nonlogin alone does not prevent inheritance or SET ROLE escalation. Table ownership, RLS bypass and definer execution are separate native facts. If a managed target cannot realize the selected separation, refuse that profile or author an explicit alternative with complete disclosure/integrity evidence; do not grant application ownership to make installation succeed. This binding design does not select role names, provider accounts or live grants, and it cannot qualify bodies whose collector/codec/custody dependencies remain unresolved.

### Proposed document-qualified grant home

The [qualified helper execution design](qualified-grant-helper.proposal.md) defines original actor capture, six-step privilege-delta ordering, no-op/rollback behavior and QG-01–06 native schedules. Its body and installation-bound callable inventory remain unimplemented.

The table above describes baseline layout 0.2. Under proposed ADR-004, `truss-qualified-module-policy/0.1.0` instead selects a fixed generic `module_access` home with exact non-null text columns `document_id`, `module`, `reader_role`, `writer_role` and primary key `(document_id,module)`. All identity comparisons use the selected native exact-byte text/collation profile, with no case folding, Unicode normalization or locale-dependent equality. Reader and writer remain distinct exact native role names. Qualified document/module values must independently resolve under the admitted UMF/catalog context and PostgreSQL text carrier; this profile cannot truncate or rename unsupported identities. A predeclared grant may precede definitions in its exact document/module, as in the baseline, but cannot supply provenance for a later catalog definition.

This candidate changes fixed ownership columns/constraints and the optional policy bundle; it requires a new explicit layout/binding version and complete generated/native inventory. It is not an unchanged-column extension to baseline 0.2, and native predicates cannot assume the new catalog ownership homes already exist. CONTRACT-001/003 own those full original type/relationship ownership mappings. Missing or ambiguous owner mapping refuses qualification rather than falling back to the unqualified `module` string.

The proposed helper call is `grant_module_roles(document_id,module,writes)`, with no default document and no document derived from schema/search path, role name or first matching type. It selects exactly one qualified grant row and applies the requested native privileges under the selected administrative profile. Actual row access still requires qualified policy predicates; broad table SELECT privilege does not merge document scopes. A missing/ambiguous grant is an explicit administrative refusal, not a request to create or copy a grant. The old two-argument helper cannot be an application or administrative grant path for this candidate; its baseline meaning remains available only in an independently selected baseline installation/profile.

For live object/key rows, resolve the owning type's original admitted document/module. For edges, independently require authority over the relationship's declaring document/module and both endpoint types' document/modules; identical module names across documents do not coalesce those requirements. Property/key/endpoint catalog rows inherit the corresponding original catalog owner. Historical/source/replay/migration disclosure uses its complete retained qualified owner union under current grants, preserving historical owners after rename/deletion/rebinding. Display labels and current endpoint lookup cannot replace retained owner identity. The qualified policy-generation guard covers this complete grant/role/policy scope; revocation ordering and read-only coordinator admission retain their existing separate obligations.

Populated conversion requires a complete host-authorized mapping from every retained legacy grant to the intended exact qualified document/module rows and exact role values. Do not infer that mapping from matching labels, copy a grant to every same-named module or silently discard an unresolved row. Validate all retained catalog/history/source owner mappings and the resulting grant/privilege/policy inventory privately before activation. Publish the qualified grant home, owner mappings and policy/binding selection atomically under the reviewed catalog/policy lock hierarchy. Failure preserves the original installation; unresolved native termination preserves recovery custody. A later downgrade cannot collapse distinct qualified grants or owners into one baseline key. Exact DDL, guarded administrative producer/privilege closure, complete exporter correspondence and native policy evidence remain separate design/adoption outputs.

**Acting role.** The role that decides access is the one the database reports, as for the journal's `db_role` (CONTRACT-002): `current_setting('role')` when it is not `none`, otherwise `session_user`. It is not `current_user`, which inside a function owned by another role is that owner. `truss.acting_role()` returns it.

### Acting-role capture admission

The expression above is the native capture candidate, not an independently sufficient authorization grant. Each invocation MUST preserve the exact nonempty native role name and verify correspondence to the actual current data caller under the selected adapter/procedure profile. An unknown, empty or unsupported native role context MUST refuse before effects or disclosure; it MUST NOT fall back to the helper owner, a request-supplied name or an earlier invocation's capture. Nested definer execution MUST retain the originally admitted caller while internal `current_user` changes. Later caller changes require fresh admission; recovery retains original attempt identity while independently applying current disclosure authority.

The selected server profile MUST pin patch release and vendor build and exclude known incorrect role-reset behavior. PostgreSQL's [CVE-2024-10978 advisory](https://www.postgresql.org/support/security/CVE-2024-10978/) identifies incorrect identity after SET ROLE/SET SESSION AUTHORIZATION, including queries using current_setting('role'); upstream 17.0 is affected and 17.1 includes the fix. A vendor backport requires documented correction provenance plus the selected profile's independent reset/rollback/prepared-statement evidence. This prerequisite does not select supported PostgreSQL majors, establish that 17.1 is otherwise sufficient, or allow the toolkit to change host session state.

The exact lowercase `none` sentinel is not an ordinary role name in the reviewed [PostgreSQL 17 RoleSpec grammar](https://raw.githubusercontent.com/postgres/postgres/REL_17_STABLE/src/backend/parser/gram.y): role creation and rename use RoleId/RoleSpec, which rejects that name. Preserve case and quoted-role identity; do not normalize other names to the sentinel. This source observation justifies retaining the candidate expression; it does not prove its behavior for a deployed procedure, native special context, pooler or driver. STP-037 owns the planned original-caller, reset, rollback and nested-definer qualification matrix.

**What a role sees.** Policies apply to the roles' acting role. A superuser and a role with `BYPASSRLS` bypass them.

| Table | A role may read a row when | A role may write a row when |
|-------|----------------------------|------------------------------|
| `module_access` | it is the row's reader or writer | never through the layer |
| `type_def`, `rel_def` | it can read the row's module | never through the layer |
| `prop_def`, `key_def`, `rel_endpoint` | it can read the row's type or relationship | never through the layer |
| `object`, `object_key` | it can read the module of the row's type | it is the writer of that module |
| `edge` | it can read the relationship's module and the modules of both endpoint types | it is the writer of the relationship's module and can read both endpoint types' modules |
| `edge_limit` | not granted | the edge it refers to is visible to it |
| `journal`, `key_tombstone` | object evidence: current authority over its retained historical type ownership; edge evidence: current authority over its retained historical relationship and both endpoint type ownerships, as below | ordinary insertion only through qualified mutation/audit maintenance; no caller-selected historical authority |
| `record_source` | the record it describes is visible to it | the record is visible to it |
| `schema_rev`, `schema_doc`, `schema_change`, `setting` | not granted | not granted |

A catalog revision is written by the owner, and the catalog tables are enabled but not forced, so acceptance is not subject to these policies. The data tables are forced, so the owner and functions it owns obey the policies as the acting role.

**Cross-module edges.** UMF allows a relationship in one module to name a type in another. Under this layer such an edge is visible only to a role that can read the relationship's module and both endpoint types' modules, so a role that reads only the source's module does not learn that an edge, or its target, exists. A role that writes the relationship's module can create it only if it can also read both endpoint types' modules. A deployment gives a role access to several modules by naming it as the reader of each.

### Proposed current-authority observation boundary

Data snapshot and current authorization are separate. [PostgreSQL 17 isolation documentation](https://www.postgresql.org/docs/17/transaction-iso.html#XACT-REPEATABLE-READ) specifies retained snapshots across repeatable-read queries. Thus ordinary reads of application module_access rows can preserve old grants. This inference is not a universal assertion about native catalog privilege invalidation. SERIALIZABLE alone does not supply the required current-authority protocol.

Candidate native profile: a protected policy-generation guard covers the qualified authorization scope. Participating grant/role/policy changes increment it atomically under exclusive guard ownership. Reads take a share guard before payload disclosure and verify observed generation, acting role and profile. A fixed snapshot encountering a changed guard must retry/refuse rather than authorize old grant rows. Exact native row/lock/error behavior requires versioned storage/profile review and independent evidence.

Cover every claimed authority input: document-qualified grants, acting-role resolution and relevant native privilege/policy changes. Changes outside the protocol invalidate qualification; a module_access-only counter cannot hide them. CONTRACT-011 inventories controlled/excluded administrative paths. Caller generation/cursor text cannot nominate authority. Without the boundary, current-grant disclosure is unavailable rather than redefined as snapshot-old grants.

Authorization follows admitted operation order: a guarded read may finish before waiting revocation commits; afterward admission observes the new generation or refuses. Native share guards may last through the caller transaction and delay revocation. Disclose that property; no immediate wall-clock revocation or hidden caller commit is promised. Faster cancellation needs a separately qualified protocol. Direct/staged/history/replay/compiled execution consume the same reviewed boundary; previously captured data cannot evade required authority revalidation. Truss supplies Weft execution obligations after joint review, not a new compiler. Guard schema/lock order/adoption and native revocation evidence remain outputs.

### Guard lock/adoption refinement

The [installation-wide guard candidate](installation-policy-guard.proposal.md) allocates a fixed singleton home, checked generation/initialization, complete controlled authority paths and PG-01–06 schedules. It is a concrete optional realization; layout 0.9 does not yet contain the table. Fixed-snapshot/current-authority and read-only coordinator qualifications remain explicit prerequisites.

For the proposed row-guard profile on compatible read/write transactions, acquire catalog-head locks already required by the operation first, then policy-generation guard, then request/business/root/row locks in CONTRACT-009 order. Do not add a catalog write lock to a read-only snapshot or acquire a newly discovered catalog lock after the guard. Administrative authority updates that require catalog locking use the same order; pure policy updates may take only the guard provided they acquire no earlier lock afterward. Multiple scope guards use the profile's exact stable scope order. All participants need the same versioned hierarchy; enabling one guarded writer cannot qualify unguarded legacy paths.

An explicitly read-only adopted transaction cannot use this row-lock candidate by changing its access mode, committing it or moving its data query to another snapshot. PostgreSQL's [read-only access-mode rules](https://www.postgresql.org/docs/17/sql-set-transaction.html) and [17 executor permission checks](https://raw.githubusercontent.com/postgres/postgres/REL_17_STABLE/src/backend/executor/execMain.c) constrain non-temporary locking queries. Source inspection is design evidence, not a pinned native adapter pass. Preserve the read-only requirement as an unresolved authority-adoption boundary rather than silently withdrawing it.

Alternative candidate: the host supplies a separately qualified authority coordinator that obtains fresh acting-role/owner grants under a revocation exclusion protocol while the data connection retains its read-only snapshot. Coordinator authority is not its own administrative visibility; it verifies the actual data caller's qualified owner contexts. Keep that exclusion through every required disclosure, and verify whole result/prerequisite context before exposing payload. Old snapshot RLS rows alone cannot establish current permission. Exact trust, native exclusion, cross-connection lock order, permission scope and failure/release behavior must be contracted and independently tested; no implicit elevated connection is opened by core. Loss of coordinator authority makes current-grant disclosure unavailable without committing or rolling back the host data transaction.

### Proposed authority coordinator lifecycle

[Coordinator binding](bindings/truss-authority-coordinator-v0.1.d.ts) separates host-captured native data caller, admission over a complete owner union, disclosure validation and exclusion release. Opaque TypeScript markers prevent accidental construction only; forged JavaScript/JSON cannot become authority. Host runtime verifies adapter/installation/connection/transaction/caller identity and liveness, actual acting-role evidence and exact profile. Coordinator visibility does not replace the data caller's grants. No credentials or caller-supplied role string become capture authority.

Derive the required owner union from qualified catalog/retained provenance and whole result/prerequisite context. Discovery may be private under the data snapshot, but cannot publish payload/hidden existence before fresh admission. Acquire all scope exclusions in stable qualified order and verify grants at the resulting guarded observation. Missing ownership, unknown authority input or unsupported native closure refuses. A newly discovered owner outside the admitted union requires release/restart under the qualified profile, not lock growth out of order. Validate exact retained union/pins alongside its digest; digest equality alone cannot establish completeness.

Bind the lease to the captured data connection/transaction and coordinator native exclusion handle. Revalidate acting-role/context/liveness and complete owner union immediately before required disclosure while exclusion remains held. Host SET ROLE/connection swap, coordinator loss, stale generation or conflicting context invalidates admission. Buffer under bounded private resource rules; on invalidation discard/withhold payload rather than return a partial complete result. Feed/replay completeness and staged-read rules continue to apply. Streaming requires an independently qualified per-disclosure scope/lifetime protocol and cannot inherit buffered atomic authorization.

Release affects only coordinator exclusion/resources and records confirmed versus unresolved outcome. It cannot commit/rollback data work, retry the caller callback or transfer the caller snapshot. Unresolved coordinator release quarantines that coordinator handle and blocks reuse until qualified native observation; caller data transaction authority stays intact unless its own driver separately reports failure. Cleanup proves owned resource identity. The profile must declare the complete cross-connection wait/lock matrix, including catalog and policy/DDL administration, and avoid workflow deadlocks not detectable as one native transaction. A separate connection alone does not solve lock ordering.

#### Cross-connection authority wait matrix

The existing coordinator/guard candidate, rather than a second authority singleton/profile, owns fresh disclosure leases. Stage and completely decode the private result first; then admit its full owner union in the fresh coordinator context and retain exclusion through complete publication. A failed grant check withholds the whole page/cursor/lookahead, not a silently filtered complete page. Coordinator cleanup contains only its engine-owned work and never ends the original caller data transaction.

| Participant | Admitted catalog/policy ordering | Forbidden wait relationship |
| --- | --- | --- |
| Original data caller | Retains exactly the catalog/snapshot guards required by its selected data profile; read-only mode stays unchanged | Cannot release a caller guard through hidden commit/rollback to unblock its coordinator |
| Fresh authority coordinator | Uses original admitted data/catalog custody and takes only its registered policy exclusion; observes current authority in its qualified fresh context | Cannot acquire/reacquire a head behind an administrator waiting on its own data caller; cannot later discover an earlier-level catalog requirement |
| Policy-only grant administration | Exclusive policy exclusion, exact new generation/inventory, confirmed completion; no later catalog-head acquisition | Cannot take a head after holding the policy guard or use unregistered native grant/role changes |
| Catalog/layout administration | Required exclusive head before policy exclusion and later object/DDL work | Cannot hold policy exclusion while waiting to acquire the earlier head |
| Policy/helper DDL with conflicting native relation locks | Explicit original-context registry/drain admission before acquiring locks that can block caller data work; exact native lock set/order remains required | Cannot hold exclusive policy exclusion while waiting for a relation lock retained by a data caller that now needs shared policy admission |

A second connection does not make these waits independent: some cycles span different native transactions and host workflow waits. Before policy/helper replacement, the selected administration service must close new incompatible context admission and independently observe required original contexts ending under host ownership; a connection count, timeout or registry disposal is not termination evidence. Defer/refuse the DDL attempt before acquiring the conflicting lock set when drain cannot be established. Do not cancel or commit caller transactions implicitly. Ordinary participating policy-only changes remain a separate path and cannot inherit unqualified DDL drain semantics. Native role/privilege operations require their exact catalog-lock/dependency qualification rather than assuming the grant-row path covers them.

The guard/generation, original caller linkage, full native lock sets, context registry, finite drain/lease resource bounds and exact public administration/recovery behavior remain design/adoption outputs. This matrix states the required protocol and excluded inversions; it does not prove a native implementation deadlock-free.

Read-only correctness tests must show unchanged data access mode/snapshot, current caller grants, both revocation/read orderings, coordinator disconnect and context changes. Exact native guard/permission/exclusion implementation, capture/wire schema, buffered/streaming limits and owner review remain required outputs. This candidate does not qualify elevated observer access or ordinary stale-snapshot RLS as current authority.

### Historical and indirect disclosure

History, delete envelopes, edge tombstones, source provenance, feed payloads and retained request results must not broaden live module authority. Resolve ownership from the retained definition/provenance in force for the evidence, then apply the caller's **current** grants to those qualified owning modules. A past grant is not continuing access. A retired definition or deleted endpoint does not remove the ownership requirement; joining only to a live object is insufficient. Equal module names from distinct owning documents are not interchangeable authority (ADR-004 remains proposed).

An edge evidence payload requires read authority over its relationship's historical declaring module and both historical endpoint-type modules, including evidence whose property delta omits endpoint metadata. The referenced retained envelope/definition must supply those identities. Do not infer them from current endpoints, a reused key, a relationship name or a newly rebound definition. Missing, ambiguous or unqualified ownership makes the evidence unavailable under this profile; it must not fall back to relationship-only access or owner privileges. Object evidence requires its historical owning type module under the same rule.

For updates that move ownership or endpoint context, a full before/after payload requires authority over the union of both contexts. If the profile cannot safely expose that payload, withhold it; do not silently remove fields and call it a complete change. A consumer denied required feed events cannot acknowledge them as applied or claim a complete replica. A separately filtered feed needs its own explicit projection, checkpoint and completeness contract. Request replay may return retained data only after authorization of every result member's retained context; partial replay cannot satisfy CONTRACT-009.

Deleted-record source lookup uses retained ownership and current grants rather than an elevated existence probe. Administrative catalog/report access remains separate and is not automatically granted to ordinary module readers. These requirements expose a layout/policy gate: the present historical rows and policy SQL do not yet prove sufficient provenance or these predicates. Reconcile ADR-004/007, retained definitions, source lifecycle and receipt context before claiming historical isolation. The optional layer's no-column-change promise cannot be used to discard required provenance; any necessary layout change requires the normal versioned decision.

**Privileges.** Policies only narrow what a granted privilege reaches. `truss.grant_module_roles(module, writes)` grants a module's roles `USAGE` on the schema and `SELECT` on the tables above that they may read, which includes `module_access`, `type_def` and `rel_def` because the policies read them as the role. With `writes` true it also grants the writer `INSERT`, `UPDATE` and `DELETE` on `object`, `object_key`, `edge` and `edge_limit`, `INSERT` on `journal`, `key_tombstone` and `record_source`, and `USAGE` on the id and journal sequences. A host that writes only through functions it owns can pass `writes` false.

**Policy cost.** Measured on PostgreSQL 16.2 and 17.9 at 1,000 types and 10 modules (SPIKE-003 F8), with the role already granted and set: the set-based policies used here added 0.006 to 0.007 ms to a read by id, 0.012 to 0.021 ms to a one-hop read and 0.06 to 0.07 ms to a page of 50, on top of about 0.02 ms for assuming the role. Policies built from row-by-row function calls cost about twice as much on a page of 50, and a `SECURITY DEFINER` function 2 to 3 times as much, so neither is used. The measured edge policy checked the endpoint types only; the shipped one also checks the relationship's module, which was not measured.

## Precedence and Compatibility

- Versioning: with the layout version (CONTRACT-001). `module_access` is part of the layout; the policies are a separate file that a deployment applies and that carries the same version.
- Precedence: CONTRACT-001 governs the tables. This contract adds policies and privileges and changes no column or constraint.
- Backward compatibility: adding a policy that narrows access is a breaking change for a deployment that applied the layer.
- Deprecation: as CONTRACT-001.

## Error Semantics

| Condition | Outcome | Retry | Recovery |
|-----------|---------|-------|----------|
| A role reads a row it may not | the row is absent, no error | no | Grant access in `module_access` |
| INSERT or visible UPDATE produces a row failing WITH CHECK | Native `insufficient_privilege` / RLS violation; no effects | no | Use an authorized writer/context |
| UPDATE or DELETE targets a row hidden by USING | Native statement may affect zero rows without an exception; library reports `not_found` under disclosure policy, never successful mutation | no | Use an authorized context without revealing hidden existence |
| A role lacks the privilege on a table | `insufficient_privilege` | no | Call `grant_module_roles` |
| A policy needs a table the role cannot select (`module_access`, `type_def`, `rel_def`) | `insufficient_privilege` | no | Call `grant_module_roles` |
| A foreign-key or unique check against a row the role cannot see | the check runs regardless of the policies and can reveal that the row exists | no | The host decides how to report it |

### Mutation outcome interpretation

Native zero-row UPDATE/DELETE is not proof that a target never existed. The library must distinguish no matched authorized row from a successful mutation using statement status/RETURNING and qualified expected-version handling. It MUST NOT probe with elevated authority merely to convert hidden absence into an existence-revealing error. A visible stale-version target follows CONTRACT-004 version semantics; an inaccessible target follows the host non-disclosure policy. All refused/zero-effect paths leave canonical, derived, journal and source effects absent. A test asserting the database rejects unauthorized writes must accept the applicable native guard outcome while still proving no change, not require one SQLSTATE for every DML form.

## Examples

```text
INSERT INTO truss.module_access VALUES ('sales', 'sales_ro', 'sales_rw'), ('billing', 'sales_ro', 'billing_rw');
SELECT truss.grant_module_roles('sales', true), truss.grant_module_roles('billing', true);
-- sales_ro reads both modules and any edge between them; sales_rw writes sales only and sees no billing row.
```

## Non-Normative Notes

The check script (`module-isolation.check.sql`) builds two modules and checks each rule above as non-superuser roles on PostgreSQL 16.2 and 17.9. It does not run the policies under a `SECURITY DEFINER` function owned by a non-superuser, where `FORCE ROW LEVEL SECURITY` and the acting role interact; that case is unverified. Writing a module's types and relationships through a catalog revision is not governed by this layer; a host that accepts revisions on behalf of a role checks that the role may define the module.

The historical upstream 16.2 environment predates the advisory's 16.5 fix; its observed predicate checks cannot qualify the corrected acting-role reset boundary. Preserve those observations at their original scope and run the complete caller matrix on the selected corrected server/build before claiming this profile.

Bucket integrity observation is separate from ordinary module reads: CONTRACT-001's protected-writer candidate requires complete hidden candidate inspection for uniqueness while retaining original acting-role/current authority for disclosure. No privileged metadata row/count/byte-size result is a public lookup result. Module isolation must qualify actual procedure owner/extraction policy and authorized redaction; owner identity never replaces data caller grants. Protected-store denial and direct-table writer coverage are separately reported, preserving the latter's unresolved native planning/enforcement requirement.


### Candidate migration authority uses the owning native transaction

For `truss-migration-head-exclusion/0.1.0`, migration authority admission uses its own READ COMMITTED read/write connection after exclusive head acquisition. It does not acquire a separate read-only authority coordinator lease whose capture might wait on that same head. Trusted acting-role capture remains the original data caller's role under the selected definer procedure, never the procedure owner's effective role. Administrative permission to migrate and permission to disclose the complete inventory/report are independently admitted; integrity-observer visibility alone supplies neither.

After the head is held, derive the complete original owner union from admitted source catalog/binding and retained reservation/archive provenance under private integrity custody. Acquire policy guards in the selected stable scope order, then perform a fresh guarded grant/role/admin-policy observation on this same connection before releasing any inventory/report to the caller. The guards remain held through native finalization and termination. If source collection exposes an owner absent from the planned union, terminate/reconcile the original transaction and restart only after confirmed containment; do not grow the guard set after lower locks or disclose a partial authorized prefix. Missing retained ownership or uncontrolled role/privilege mutation makes this profile unavailable.

| Participant | Allowed acquisition order | Prohibited wait dependency |
| --- | --- | --- |
| Migration | Exclusive head, sorted policy guards, sorted lower source/key/native guards | Separate coordinator acquiring the head held by migration |
| Catalog/policy administration requiring catalog | Head, policy guards, lower effects | Policy guard followed by head acquisition |
| Pure policy change | Policy guard and its own lower effects | Later head/catalog acquisition within that transaction |
| Participating ordinary writer/maintenance | Shared head, policy guards when required, lower guards | Lower guard followed by head upgrade or newly discovered earlier guard |

Revocation that commits before guarded admission must be observed/refused. A revocation waiting behind migration's share policy guard commits afterward; the resulting delay is part of the selected profile, not immediate revocation. A policy administrator needing the head follows the same order and cannot hold a policy guard while waiting for migration's head. Native cleanup/recovery preserves original connection/role/resource custody; a disconnected or cancelled transport does not prove those guards released. Explicitly read-only historical clients continue using their separately qualified coordinator protocol, which must itself respect the complete cross-connection matrix; this migration candidate does not qualify that different deployment path.


## Direct bucket-read private context boundary

CONTRACT-004's read-only bucket lookup statement is a fixed internal observation template, not an ordinary application grant to read original_context_bytes. The private match/context carrier may contain complete source/definition dependencies beyond the public record projection. Application raw column grants and public helpers cannot expose it merely because the object itself is visible. The installation privilege inventory must identify any complete context owner union and its disclosure path independently of object/key row access.

Candidate realization uses a qualified protected read entrypoint with original data-caller capture, exact context/key/mapping/parameter admission and fixed query dispatch. Its native read owner has only the selected read-column privileges, no bucket mutation/sequence rights, and obeys FORCE RLS/current data-caller policy composition rather than the complete hidden integrity-observer policy. The function owner's effective role is not public disclosure authority. Revoke PUBLIC execution, admit only the registered reader operation path, use trusted qualified dependencies/search path and exclude independently callable context-returning subhelpers. Exact body/signature/capture/privilege/profile realization remains required; a definer label cannot establish this boundary.

The entrypoint/coordinator privately verifies complete returned full namespace/key/source correspondence and current authority over the required context/record owner union before returning the permitted DirectRecord. It never returns matched_context_bytes, digest candidates, hidden multiplicity or private decoder diagnostics through the public wire, tracing or callbacks. Native loss/cancellation follows original read/coordinator recovery; neither private receipt nor memory deletion proves containment. A deployment directly granting the complete context column to application readers must independently qualify that raw disclosure policy or refuse this protected-context claim.

This read owner must not inherit the protected integrity observer's broader hidden scope. Mutation/migration completeness helpers remain restricted to their original protected owners; direct lookup cannot call them to find a hidden key/object or convert hidden source failure into public absence. Baseline key lookup and full-byte bucket lookup retain separate selected physical inventories. No ordinary read procedure is licensed to touch/insert a key guard, inspect reservations, alter current caller role or end its data transaction.

## Protected integrity observer role candidate

Select proposed `truss-integrity-observer-role/0.1.0` as a concrete realization candidate for CONTRACT-001's complete hidden routing-candidate inspection. It supplements the optional module policies; the baseline module-isolation SQL does not install it. The observer is a dedicated non-login, non-superuser role without BYPASSRLS, role/database creation or replication capability. It has narrowly inventoried SELECT access to required original candidate/context stores and no mutation, sequence allocation/reset, object ownership or policy/trigger alteration privilege. Application roles cannot inherit or SET ROLE to it, including through intermediate memberships; NOLOGIN alone is insufficient. PostgreSQL 17 distinguishes membership inheritance from role switching in its [role-membership rules](https://www.postgresql.org/docs/17/role-membership.html).

Each required RLS-enabled input store receives an explicit qualified SELECT policy for the observer's effective native role. Its admitted effective policy must permit the complete integrity scope; every applicable restrictive policy is inventoried and must preserve that completeness. A permissive observer policy alone cannot overcome a filtering restrictive policy. Required stores without RLS retain explicit SELECT privilege and the same original scope/custody checks. Do not disable FORCE RLS, grant BYPASSRLS or replace host policies implicitly to get a complete scan. An incompatible host policy yields unavailable profile/complete observation. PostgreSQL's [row-security rules](https://www.postgresql.org/docs/17/ddl-rowsecurity.html) distinguish owner/bypass behavior and combined policy effects; this candidate uses explicit policy composition rather than presumed owner visibility.

Only registered internal observation helpers execute as this observer. Grant exact helper signatures exclusively to the admitted protected mutation/migration procedure owners; neither PUBLIC nor ordinary caller roles may invoke them or obtain observer membership. Their bounded inputs identify already admitted original scope, not arbitrary table names, SQL, caller-selected role or authority. They return complete privately held integrity facts to the original outer procedure under its retained exclusions. No exposed observer view, table function, public wrapper or diagnostic may disclose hidden IDs, values, counts or sizes. Collection/result delivery still requires independently checked original migration administration and current disclosure; the observer policy supplies completeness, not caller permission.

Preserve native original acting-role capture through nested definer calls while recording the distinct current_user at each helper boundary. Current_user inside the observer is useful only for its installed internal SELECT policy; it cannot authorize the outer mutation or public result. Every write remains under the separately admitted writer's current authority and native privileges. The observer cannot repair a missing outer owner union, stale grant observation or late lock discovery.

For each helper, pin its exact body, dependencies, argument/result types, owner, security mode and fixed trusted search path, with pg_temp last and explicit schema qualification of referenced deployment objects. Build/revoke/grant in one admitted deployment transaction so default PUBLIC execution is never exposed. The [PostgreSQL 17 function documentation](https://www.postgresql.org/docs/17/sql-createfunction.html) describes definer execution and these publication/search-path precautions. Ordinary callers must lack CREATE/ownership over all helper-resolution namespaces and the ability to replace selected helpers/types/operators. No arbitrary dynamic SQL or ambient caller search_path is admitted.

The candidate's qualification inventory binds actual role identities/attributes, transitive membership edges and grant options, all effective policies and helpers, native server/adapter/namespace and original caller capture profile. Role/policy/function/ownership changes participate in current-authority exclusion or invalidate the composition; a historical catalog hash is not fresh admission. Exact physical role/helper names, bounded native helper definitions and installation/export correspondence remain owned native design outputs. This candidate is not accepted/installed or native-qualified, and does not extend baseline module policy evidence to protected observation.


### Observer role reachability and helper exposure admission

Before admitting the observer candidate, collect the complete original selected role/membership, effective grant-option, helper EXECUTE, ownership and policy inventories under the same current-authority exclusion. Build a bounded registry keyed by native original role identities and resolved installed meaning. Display names, NOLOGIN or a stored role-attribute hash cannot establish isolation. Preserve each membership's native inheritance, role-switch and administrative options rather than reducing it to one generic member edge.

For every ordinary admitted caller/session identity, independently apply the selected native server's effective inheritance and SET ROLE rules to the full membership graph. A bounded visited-role/state registry prevents repeated traversal; any cycle retains its original evidence and must be interpreted under the selected server grammar, not assumed native-valid. Any effective path to observer privileges or observer-role switching rejects this candidate. Separately admit administrative/delegation capabilities: an ordinary caller able to confer observer membership, change an observer/helper owner, grant helper EXECUTE, replace a helper/dependency or modify its complete-scope policy cannot fit the protected ordinary-role guarantee. Do not assume current nonmembership prevents later self-grant. Unknown option semantics or incomplete role/grant fanout makes the profile unavailable.

Reconcile complete effective helper invocation rights, including PUBLIC, transitive inherited grants, grant options, overload signatures and any registered wrapper. An ordinary caller must have no direct or indirect data-disclosing path to an observer helper. A registered outer writer may invoke it only under the original private scope/current-authority procedure; a wrapper's elevated current_user does not grant its public caller the observer's result. Inventory exact bodies/dependency calls and independently admitted output/diagnostic disclosure, not just catalog EXECUTE flags. A helper returning hidden counts to a public wrapper violates the candidate even when its own direct ACL is restricted.

Reserve full role/edge/signature/body-call registry and traversal work before collecting/resolving. Require complete original inventory membership and native termination evidence; limit-plus-lookahead cannot turn truncation into no path. Apply current-authority revalidation before each actual outer operation and invalidate affected retained readiness on role/ACL/policy/body drift. This procedure defines the finite closure obligations; exact native option interpretation, collector/descriptor/resource producers and original helper/role deployment adoption remain selected profile outputs.

### PostgreSQL 17 observer privilege-state closure

For the PostgreSQL 17 candidate, interpret original membership options according to [role membership](https://www.postgresql.org/docs/17/role-membership.html) and [SET ROLE](https://www.postgresql.org/docs/17/sql-set-role.html). Construct switchable states from the original admitted current session user, following only membership paths whose every edge permits SET. Changing current role does not make a new role the source for subsequent SET permission. Separately construct effective ordinary object privileges for each admitted active/switchable role by following INHERIT edges; inheritance stops at a false option. Include the active original role and validate its actual session/caller correspondence before interpreting privileges.

An observer inherited after switching to an intermediate role is still an escape even if there is no all-SET path directly to the observer. Conversely an INHERIT-only path cannot establish permission to SET ROLE. Attributes such as SUPERUSER/CREATEROLE are not ordinary inherited object privileges; inspect actual admitted active/switchable role attributes and separately selected delegation/ownership capabilities. Never traverse SET and INHERIT as an arbitrary mixed-edge path and call that native role-switch permission. Preserve original grantors/options and all independently required administrative observations.

PostgreSQL 17 rejects circular role memberships. A synthetic or corrupt observed cycle must therefore refuse the PG17 candidate, with bounded termination and original evidence retained; it is not a valid positive role fixture. PUBLIC is a pseudo-grantee for object ACL interpretation and cannot be a role-membership endpoint. Keep ACL and membership registries separate. Native catalog/descriptor/cut integrity and complete original options remain prerequisites; an apparently acyclic graph cannot establish those facts by itself.

This fixes the graph algorithm for the candidate's static switching/inheritance surface. It does not qualify administrative delegation, privileged wrappers, native reset/rollback/prepared behavior or deployment role/collector profiles. Any unsupported session-authorization transition or host command path invalidates the original admission rather than being simulated as an ordinary graph edge.

[Nine independently authored PG17 graph cases](bindings/observer-role-reachability-pg17-v0.1.vectors.json) have [scoped experiment evidence](../../04-build/evidence/design-audit/observer-role-reachability-audit.json), including inherited-after-switch exposure, a mixed path that grants no SET permission, blocked edges and corrupt cycle/PUBLIC endpoints. Reproduce with normal/optimized `python3 docs/helix/04-build/evidence/design-audit/check-observer-role-reachability.py`. A not_exposed result means only this synthetic static SET/INHERIT graph has no observer path; it is not observer-profile admission. Actual native role identities/options, delegation, ACL/wrapper/RLS and original complete collection/resource evidence remain required. Local role/edge limits are experiment bounds only.

### Protected ownership and delegation closure

Derive the complete protected-role set from original observer identity and owners of every selected helper, policy input store, required type/operator, resolution namespace and mutable dependency. Reconcile it with the original creator/ownership inventory; no role-name prefix substitutes for membership. Under the admitted PG17 privilege-state closure, an ordinary actor must neither switch to nor exercise inherited ownership privileges of those owners. Missing current object ACL entries cannot prove safety: [PostgreSQL 17 GRANT](https://www.postgresql.org/docs/17/sql-grant.html) assigns owners implicit grant rights and reserves definition control to ownership; it also warns that inherited owner privileges without SET can still permit manipulation of owned functions. Revoking ordinary EXECUTE/SELECT alone does not remove ownership authority.

Independently inspect role ADMIN options and object grant options under the selected original native grantor rules. Reject an ordinary actor able to confer membership/privileges to itself or another ordinary actor on the observer or protected-owner/helper surfaces, even if its current static observer path is empty. Keep role ADMIN and object WITH GRANT OPTION distinct. A role is not its own implicit ADMIN grantee; PUBLIC membership and PUBLIC grant options are not invented from object PUBLIC privileges. Preserve original grantor and dependency/cascade facts for later current-authority admission and drift reporting.

The complete protected dependency inventory includes mutable owners and call paths, not only the immediate observer function. A private wrapper whose dependent function/type/operator can be replaced by an ordinary actor invalidates the profile before execution. Dependency changes or new actual ownership edges participate in selected authority exclusion; an immutable historical body hash cannot hide an unguarded current replacement path. Native grant/delegation/ownership producer interpretation and all original effective privilege probes remain separately qualified outputs. The synthetic SET/INHERIT experiment does not cover this closure.

## Optional admission prelude cross-connection composition

When CONTRACT-003's optional advisory prelude is selected, extend each participating native transaction's order to advisory admission, required catalog head, policy guards, then lower guards/effects. Pure policy administration that takes no catalog head may retain its separate policy-only order, but cannot later acquire advisory/head admission. The optional prelude grants no authority and does not change historical read-only data snapshot adoption.

A data/migration transaction holding original shared/exclusive admission cannot synchronously wait for a separate authority/receipt coordinator to acquire a fresh conflicting or behind-waiter admission/head position. Native shared compatibility alone is insufficient when an exclusive queue waiter may intervene. Qualify the entire cross-connection wait graph and original coordinator capture/admission/disclosure/release procedure; reject a cyclic composition before starting its dependent work. The existing prohibition on a coordinator waiting for migration-held head now also covers its advisory prelude.

Do not fix an unsafe composition by transferring serialized lock metadata, opening an implicit elevated connection, bypassing queue participation, unlocking original host admission or moving data to another snapshot. A separately selected observation procedure may avoid those acquisitions only when its actual exclusion/authority guarantees are independently defined and reviewed. No universal coordinator-first workaround is prescribed: earlier policy/lower guards on that connection must themselves obey the complete cross-connection hierarchy. If no admitted procedure can satisfy the graph, that optional combination is unavailable while the original transaction and required cleanup remain under their original custody.

Native test matrices must distinguish same-transaction retained admission, independent coordinator transaction, an exclusive waiter between them, and original cancellation/termination. Optional queue qualification and read-only coordinator qualification remain separate; passing either independently cannot qualify their composition.


## Selected separate acceptance-report protection

CONTRACT-003's separate immutable report home is owner-selected. Its report_bytes is protected complete acceptance content, not an application-readable blob merely because the corresponding revision or one document is visible. The complete original accepted input, affected assertion/catalog/source owners and every reported transform/rebind event's retained declaring/root/endpoint owners define the required disclosure union under the selected report profile. Resolve that union from original admitted report/definition/source custody; current live catalog labels, surviving endpoints and caller-supplied owner arrays cannot replace it. Missing/ambiguous original ownership makes complete report interpretation/disclosure unavailable.

| Principal / path | Proposed access boundary | Required independent evidence |
| --- | --- | --- |
| Ordinary data caller, PUBLIC and inherited/SET paths | No direct INSERT/UPDATE/DELETE/TRUNCATE or raw report_bytes SELECT; no partial-phase or arbitrary-byte writer | Complete effective relation/column/function/schema/ownership inventory and direct bypass probes |
| Protected acceptance producer | Insert one full admitted report for its actual pending positive revision after complete event/source parity; no ordinary rewrite/delete entrypoint | Exact original plan/caller/transaction admission, native report encoder and actual one-row insertion/parity |
| Protected report reader | Narrow selected report/archive reads privately, complete owner-union admission under the original acting caller and current-authority coordinator before disclosure | Definer ownership/search path and actual caller capture; bounded complete bytes/definition loader; native policy/coherence/trace probes |
| Administrative conversion/retention/recovery | Separately admitted profile/transaction/custody; cannot impersonate ordinary acceptance or silently repair missing history | Complete dependency/archive/held-context/authority inventory and exact authorized transition receipts |

The protected reader cannot inherit the integrity observer's hidden-scope callable powers. Its ability to read bytes privately grants no application disclosure. Decode/admit the complete bounded original artifact and required owner union under its registered private profile; then apply current authority before returning a complete report or revealing existence/content/gaps. Missing current authority must not leak report bytes, event counts, affected owners, hashes or producer diagnostics. Preserve the existing selected report lookup outcome/disclosure semantics; this proposal creates no new public report API or blanket visibility grant. Catalog-report projection requires its own explicit authorized-projection contract; trimming an AcceptanceReport cannot still claim complete acceptance evidence.

The report home and every reachable report/archive/helper path join CONTRACT-011's complete installed inventory and the existing policy/current-authority administrative change-control boundary. No standalone GRANT/REVOKE source fragment proves effective rights or immutable production. Parent FK and nonempty report CHECKs do not prevent missing positive-revision reports, arbitrary caller bytes, report replacement, deletion or a head switch before report completeness. A selected native profile must enforce those invariants for every claimed ordinary writer path, including inherited privileges, owner-role changes and helper entrypoints, or classify them as engine/none with the exact missing guarantee.

This access proposal preserves host ownership of administrative connections and original caller transactions. It adds no data-caller commit, connection replacement, hidden integrity query, new policy singleton or implicit maintenance worker. Separate report storage is selected; exact producer/reader/retention/native inventory profiles remain prerequisites.


### Complete-report protection in the baseline home

The complete original owner-union disclosure rule also applies to baseline schema_rev.report whenever the selected isolation profile claims protected catalog/report access. A visible revision or document is insufficient authority for the report's complete affected input/event/assertion scope. This is not contingent on adopting the separate-report option. Preserve each selected layout's original owner interpretation; baseline module-only grants cannot be silently interpreted as document-qualified grants. If complete original ownership is unavailable, refuse protected full-report disclosure rather than infer it from surviving live rows.

The selected native privilege inventory must distinguish permitted revision metadata columns from the protected report column and other complete sensitive origin/source content. A table-level SELECT grant already permits all columns; revoking only column SELECT does not neutralize it. Avoid that effective broad grant on every ordinary inherited/SET/PUBLIC path, and expose allowed metadata only through the exact selected column/private-view/helper profile. PostgreSQL 17's [GRANT documentation](https://www.postgresql.org/docs/17/sql-grant.html) describes this table-versus-column privilege interaction. A column ACL listing alone is not complete privilege evidence. Views/helpers must be inventoried for their actual owner/definer/current-caller behavior, reachable source columns and complete current-authority protocol; a renamed report column is not a disclosure boundary.

Native JSONB report rendering does not establish the new exact-report-byte profile or recover original artifact custody. A baseline reader independently admits its selected original report/encoding/ownership capability and either returns qualified complete content under current authority or reports its existing unavailable/projection outcome. Moving storage cannot retroactively certify old bytes. Keep report semantic fidelity, immutable production and current disclosure as separate guarantees in enforcement/support reports.

### Feed-store native authority responsibilities

CONTRACT-006's four-store candidate requires the following separate protected responsibilities. These are capability/ownership rules, not selected role names or deployable GRANT statements. The original installation profile must map each to actual routine owners, effective role paths, relation/column privileges, security/search-path/dependency and current-caller capture. Application module access does not grant direct feed-table DML or private integrity-helper execution.

| Responsibility | Permitted protected effects | Forbidden authority transfer |
| --- | --- | --- |
| Required-fact/closure registration | Original admitted producer creates transaction custody, reserves the correct counter/generation and inserts complete immutable original member/prerequisite rows through the pinned sources | Caller-selected xid/address/clock/profile authority; arbitrary original UPDATE/DELETE; direct ordinal/manifest publication; registration without independent actual effect |
| Explicit finalization | Under original producing context, clear/replace delivery ordinals and final tuple through admitted masks after complete independent effect/closure/order/canonical proof | Change original payload/key/profile/owner/time or registration counters; mutate a committed predecessor; create omitted semantic facts |
| Current-union validation | Complete protected reads of original producer/operation/feed/closure custody and selected resource-account charges | Feed/graph/counter/ordinal/hash repair, retention deletion or hidden data disclosure through public results/logs |
| Feed consumer/seed/application reads | Complete admitted public artifact/envelope projection after current authority for the entire retained owner union | Borrow validator visibility to disclose hidden originals; treat restricted scope as complete empty feed; acknowledge undisclosed required facts |
| Administrative retention | Exact original settled dependency/cohort deletion through the separate retained-evidence and consumer/seed/receipt/recovery exclusion procedure | Alter remaining originals or history; erase live/unknown producing custody; impersonate historical writer; inherit registration/finalization privileges by role membership |
| Installation/lifecycle administration | Explicitly reviewed native provisioning/change/restore/invalidation under CONTRACT-008 and current-authority coordination | Ordinary assembly provisioning; runtime data callers disabling guards/changing routine owners or replication behavior to bypass validation |

Keep original acting data caller distinct from native definer/installation owner. Registration and validation may need complete hidden evidence, but successful internal comparison cannot widen public disclosure. Preserve actual declared caller/owner custody through nested helpers and complete effective grant paths; shared source names do not prove privilege separation. A routine capable of both registration and retention must have separately admitted original modes with native evidence, not a caller mode string plus a broad owner grant. Missing qualified separation makes the complete profile unavailable.

Native review must enumerate all direct, inherited and routine-mediated paths to the four tables and proposed shared validator, including column-specific grants and administrative aliases. Independently test an ordinary public caller against direct INSERT/UPDATE/DELETE, finalization masks and private helper invocation; test a validator attempting repair; test a retention actor trying live registration and a writer trying retained deletion. With hidden/deleted owners, require complete internal proof but no provisional row/count/bytes in public output, trace or callback. Actual role/grant/function/source and bypass qualification remain open; this matrix selects no deployment or extension dependency.

Complete historical row pages additionally authorize original mutation manifest disclosure under CONTRACT-002: count/digest and lookahead facts require complete retained group membership and current authority over the original full owner/source/definition union, including unreturned siblings. Ordinary per-row access cannot qualify these facts. Native private collection remains bounded and complete; inaccessible or unavailable union evidence uses the governing hidden/unavailable projection with no partial cursor or protected gap diagnostic. Split delivery and held snapshots do not relax current-union authorization or turn the row page into projected feed semantics.


### Selected reference handler/validator security binding

The seven required orchestration routines in the installer matrix use SECURITY DEFINER under separate protected responsibility owners. This closes their security-mode choice; actual role identities, effective rights and complete body/dependency correspondence remain native profile inputs. Ordinary application roles cannot inherit, SET into, administer or replace these owners. Installation maps the responsibility labels to exact observed roles, with no ordinary login/superuser/BYPASSRLS/CREATEROLE/replication authority inferred.

| Required callable | Protected owner responsibility | Allowed invocation path |
| --- | --- | --- |
| row_touch_observe | Touch observation owner | Original installed row-home triggers |
| row_touch_commit_check | Commit-check owner | Original installed completion triggers |
| edge_limit_observe | Touch observation owner, with separately inventoried edge observation rights | Original installed edge/marker triggers |
| edge_limit_catalog_observe | Touch observation owner, with separately inventoried catalog observation rights | Original installed catalog trigger |
| feed_current_union_check | Commit-check owner, with separately inventoried feed validation dependencies | Original installed feed constraint triggers |
| feed_union_validate_current_scope | Integrity/finalization owner | Exact private producer/finalizer/commit-check dependencies only |
| edge_limit_verify_current_scope | Integrity/finalization owner | Exact private producer/finalizer/commit-check dependencies only |

Each body has an explicit function-local search_path containing pg_catalog, the exact trusted installation namespace, then pg_temp last. Quote namespace identifiers through the selected installer; exclude PUBLIC/user-writable schemas and never capture ambient SET FROM CURRENT. Fully qualify protected relations/callables/types and bind operator/cast dependencies; the search path does not substitute for exact dependency identity. Original data-caller capture occurs before definer entry under the governing producer protocol: current_user inside a definer is not the original acting role. No caller-supplied role string creates that custody.

Create the exact functions, revoke PUBLIC execution and grant only inventoried private callers within the same installer transaction, before readiness publication. No ordinary application SELECT of the two void validators is admitted. Required trigger installation and later body/owner/ACL changes remain privileged inventory events. Complete hidden observations return no application bytes/counts/diagnostics except through the governing authorized projection. No validator repairs canonical state.

This design follows PostgreSQL 17's [SECURITY DEFINER guidance](https://www.postgresql.org/docs/17/sql-createfunction.html#SQL-CREATEFUNCTION-SECURITY): trusted resolution with temporary schema last and atomic restriction of default PUBLIC execution. Actual managed-service role creation/ownership, RLS behavior, trigger invocation, transitive calls and drift/bypass schedules must be qualified before support; names and source REVOKEs alone are insufficient.


The reference journal-phase owner is a distinct protected responsibility: complete admitted original capture observation, immutable stage writes, journal_seq nextval and explicit journal event append only. CONTRACT-002 selects private SECURITY DEFINER phase invocation with trusted resolution. This owner cannot seal operations, alter canonical/catalog/report facts, reset sequence state or delete stage custody. Stage-aware administrative cleanup remains separately admitted; neither owner can use the other path to repair incomplete history. Actual native roles, exact rights and complete dependency/actor/RLS behavior require original installation inventory and qualification.

### Selected protected-profile grant-helper behavior

For the selected reference protected procedure profile, `grant_module_roles(document_id,module,writes)` applies only exact admitted public procedure rights for the existing qualified module_access row and its existing reader/writer native roles. Resolve the original explicit document/module and original administrative scope under the governing policy/catalog exclusion, reject missing/ambiguous scope or unsafe effective role paths, and derive grants from the complete selected callable inventory. Bind exact overload identities and required trusted namespace access; no caller-supplied routine list or namespace-wide grant is admitted.

The helper does not grant direct canonical DML, sequence allocation/reset, private reserve/seal/journal/cleanup execution or integrity-scope disclosure. The baseline two-argument helper's broad table/sequence grants are incompatible with this profile. Public EXECUTE remains access to a shared procedure surface: every actual operation separately validates original actor and current qualified document/module/owner authority. Native helper success is not profile readiness without independent full effective-right correspondence.

A false writes request does not revoke existing rights. Revocation and shared-role/cross-module policy changes require their complete original transition/reconciliation procedure; one module's change cannot silently remove shared procedure rights required elsewhere. Repeated identical native grants do not prove durable original administrative settlement or create a Truss replay receipt. Failures and unknown outer acknowledgment preserve original administrative attempt and policy/installation custody. The [installation procedure](weft-review-installation-gap-matrix.proposal.md#document-qualified-administrative-grant-procedure) records the concrete authoring sequence; exact native argument/result/body/security/role/dependency/account binding remains required.
