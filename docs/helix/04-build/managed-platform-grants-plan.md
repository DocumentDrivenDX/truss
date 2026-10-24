---
ddx:
  id: PLAN-MANAGED-GRANTS-001
  type: implementation-plan
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.prd
      kind: informed_by
    - id: ADR-008
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
    - id: TP-001
      kind: informed_by
    - id: STP-045
      kind: informed_by
---

# Managed platform grants: assessment and delivery plan

## Installer round-trip repair — 2026-10-24

The owner authorized batching installer SQL and set-based verification, followed
by a new immutable Truss release and fresh Arras Mac and actual Lakebase
campaigns. The repair requires no additional authority, reduced checks or
increased deadline. The owner subsequently authorized a separately bounded
regional runner experiment for comparison. That experiment cannot replace the
full actual Lakebase acceptance campaign across the WAN or make regional
placement a deployment requirement. Arras must pass the WAN campaign with its
existing operation deadlines and checks.

The first public 0.0.49 diagnostic reached its original 60-second operation limit
after 1,272 client execute submissions. A separately frozen repeat recorded
1,203 submissions and 60.363352 seconds inside delegated `Cursor.execute` calls;
the installer returned cancelled after 63.557889125 seconds including containment.
Neither attempt reached the first or final verification phase, so neither is a
complete installation baseline or managed-service acceptance. Client execute
timing includes driver, network and server work and does not isolate their
individual contributions. Batched result draining in `Cursor.nextset` must be
reported separately; execute timing alone is not complete phase latency.

The implementation keeps the exact ordered captured SQL units and quoted
object-specific commands. A carrier contains at most 32 units and 128 KiB of
UTF-8 text including separators. An already captured larger source unit runs
alone, unchanged. Units may contain multiple native SQL statements; carrier
counts must never be reported as native statement counts. Use the passed guarded
stock psycopg cursor, no bind parameters, `prepare=False`, `binary=False`, and
drain every command result. Reject any row-producing result; propagate original
driver failures without retries or sequential fallback. The original host
savepoint, caller transaction and operation-wide cancellation remain in force.

Replace per-object extension and effective-privilege reads with bounded catalog
queries keyed by the captured catalog class and OID. Preserve exact overload
identities, unsupported-class refusals, inventory and owner checks, role flags,
relation/sequence/column/routine/type/schema predicates, private defaults and
tolerated-grantee identity and grant-option equality. Missing, duplicate or NULL
required observations fail closed. Both verification phases remain: after
ownership protection and after final installation grants/comments.

| Slice | Dependency | Required evidence |
| --- | --- | --- |
| IB-1 | Existing CONTRACT-007/008 and Python boundary gate | Explicit private helper map; allowed caller and forbidden host/runtime import controls; ordered source and carrier boundary controls |
| IB-2 | IB-1 | Native complete inventory/definition/owner/ACL comparison, overload/dependency/column/inherited-grant refusals, mid-batch error and original-deadline cancellation; caller work and settings preserved |
| IB-3 | IB-2 | Matched public 0.0.49 and candidate fixture measurements: exact artifacts, captured units/command inventory, actual execute submissions, separate result-drain calls, client call/wall time and installer-process CPU, plus independently confirmed rollback/worker cleanup |
| IB-4 | IB-3 | Independent review; full Linux release workflow and every admitted populated migration lineage; immutable publication and public clean-download verification |
| IB-5 | Published IB-4 tuple | New exact Arras wheel and freeze; complete fresh installed Mac and actual Lakebase WAN campaigns at original deadlines; final PR #9 review/merge/release and exact published-byte verification; optional regional comparison does not close the WAN gate |

The runtime remains latest-only. Databases from every admitted UMF 0.10 lineage
retain forward migration to latest without an age cutoff; historical tools are
not supported application runtimes. If native source identity is unchanged,
verify the existing-current path explicitly rather than inventing a migration
edge or rewriting historical manifests. No pre-0.10 compatibility is added.

Execution is authorized. Spending/token estimates and a numerical ceiling were
not supplied; runtime metering is unavailable here. Native fixtures own fresh
socket-only workers and disposable database/roles. Existing public artifacts and
failed diagnostics remain immutable. At this checkpoint implementation and
offline controls are in progress; native, release and consumer gates above are
open. A candidate code diff or local timing improvement cannot close IB-4/IB-5.

### Published IB-4 checkpoint — 2026-10-24

IB-4 is complete for [Truss v0.0.50](releases/v0.0.50.md), source
`a687d0a226dad5745cbd909377bf99c7c1cddc66`. The
[retained public proof](evidence/design-audit/installer-batching-050-20261024/published-0.0.50/receipt.json)
binds the immutable tag, all 17 downloaded assets, exact package payloads and
the successful final-tag Linux release workflow. It preserves original
107-case migration, HF62, 174-test/26-module managed and selected small-workload
evidence, with the file-only verification and Linux execution scopes distinct.
The source 0.0.49 tuple verifies as already current; no native migration edge or
receipt is fabricated. Earlier diagnostics and captured measurements below
retain their original versions and qualification limits.

IB-5 remains open. Arras PR #9 now selects the actual public 0.0.50 wheel and
requires one new canonical Arras 0.6.1 wheel for both full fresh-installed Mac
and twelve-case actual Lakebase WAN campaigns, independent cleanup, normal
review/merge, release and exact public-byte verification. Ordinary OAuth actor
setup is reusable. No VM has been provisioned, and regional execution cannot
replace the WAN gate or justify relaxing its checks or deadlines.

### Diagnostic checkpoint — 2026-10-24

The exact public 0.0.49 WAN repeat and independent fresh-process audit preserved
the caller, removed the Truss schema, and matched all 33 role records and 18
memberships to the pre-install baseline. The selected platform-role OIDs and all
16 ordinary-actor/platform-role closure checks also matched. These are cleanup
facts for a failed diagnostic, not a successful acceptance receipt.

The local controlled attempt on product source `dcebf072` did not produce a
usable matched measurement. Its paired test stopped before any test body when
fresh database creation exceeded the existing fixture deadline. A later baseline
child exceeded the diagnostic controller bound, and worker inventory verification
failed; the complete owned cluster was then stopped and removed. Source and Git
state remained unchanged. The failed receipt is retained with SHA-256
`86915948498ccd4e79ff95b4287291913c9937c23245e18b5b351b7cc28b694b`.
No reduction, speedup or native equivalence claim follows from that attempt.

The refusal-control test also exposed an assertion path that skipped caller
savepoint cleanup and contaminated the next case. Each control now fails fast,
attempts rollback and all caller/native residue checks in `finally`, and retains
the primary failure with safe callsite-only diagnostics. Both its original
one-second statement and five-second operation limits remain unchanged. A
cancelled column-grant check remains a failure requiring native reproduction;
it is never recast as an accepted third-party-grant refusal.

The corrected helper, set-fact, observer, measurement-profile and release-cohort
pure controls pass 29 tests. Independent review also passed the 13 observer and
measurement controls and injected a primary failure plus cleanup failure into
the actual control method to verify original-error preservation, complete
cleanup attempts and fail-fast behavior. These checks do not close native,
matched-measurement, Linux release or consumer acceptance gates.

The `dcebf072` Linux gate passed all five native batching controls, migration
qualification and independent HF assertions, then found an existing managed
grants regression: the empty-policy trigger test expected the public 0.0.49
schema-first refusal but received a column-first refusal. The set census now
preserves the strict empty pre-ownership path's legacy object/OID and native
ACL-entry ordering. Nonempty managed-policy and final-census ordering remain
unchanged. The existing regression assertion is retained; the corrected source
still requires its native rerun and complete final-source release gates.

The `c1464cfe` local campaign passed all five batching controls and the unchanged
schema-first managed-grant regression, with no skips and restored worker
inventory after each phase. Both complete installation calls returned successful
pending installations. The comparison harness then rejected both snapshots:
PostgreSQL serializes native OID fields as JSON strings, while the harness
incorrectly required integers. Its snapshot comparison also needs explicit
treatment of the source-generated validator secret. The failed comparison
(`d25b673df8f4587a80bd467059192118a300a47089b4118f14af5be24fff530d`)
and stopped/removed-worker receipt
(`ff7a7793a5e45cd61b1f867248f68a0515dc3d5e7d73ccc6ae3837c43d7a6a71`)
remain immutable. The observed 3,409 and 114 execute calls are provisional
measurements, not a completed equivalence or acceptance result.

### Fresh-install comparison profile

This one-off 0.0.50 repair comparison binds both phases to native manifest
`288801f7177338328441b5d3ce9328af31740ebf513f04ea45e30ae316a9f3a4` and
the original `runtime.sql` SHA-256
`383b2280e20b3dd6bd31f7edc7654f83ebd7fefc1670739e24c3cf72c85c86cb`.
Independent fresh installations contain per-install generated identities and
secrets. The comparison may normalize only these named fields after
validating their native meaning:

- `catalog_runtime_installation.installation_id`, `.source_epoch` and
  `.genesis_at`, plus the source-identical revision zero
  `schema_rev.accepted_at`. Retain original values as per-run evidence.
- `catalog_runtime_installation.owner_oid` and `.registrar_oid`. Require canonical nonzero unsigned
  32-bit OID text and bind each value to its exact observed native role name;
  retain the original OID/name evidence before comparing fixed role names.
- The single `reader_catalog_validator_secret.secret` value. Require exactly
  one row and the exact field set, native `bytea` length 32, canonical JSON hex,
  and agreement with an independent native hex/length observation. Retain a
  SHA-256 commitment to the original bytes and the source binding; never export
  the secret. Compare an explicit generated-value marker only for this field.

Both phases must pass these generation checks, and their validator-secret
commitments must differ. Distinct commitments establish a fresh-value
distinction, not an entropy-quality claim. Full canonical snapshot equality
alone cannot pass qualification. Every other row and cardinality, native
definition, ACL, role attribute, membership and sequence state remains exact;
UUID or time defaults on empty tables receive no blanket normalization. Any
additional difference fails closed and requires a separately justified profile
change. This diagnostic profile changes no installed format or runtime API.
Migration preservation checks remain unchanged and compare original data without
this fresh-database normalization.

The subsequent exact-source `c67997f7` attempt completed both installations,
captured both snapshots and passed caller rollback, fixture inventory and owned
worker shutdown. Its comparison remains failed: exactly 520 cells differ, the
names of 260 internally generated foreign-key triggers and the same names in
their rendered definitions. All other captured fields match. Retain the
original failed report (`83496508e8deb9c75427ef2ea006a5d1c56ec01abd0dfb5c8d37cf5418619723`)
and shutdown receipt (`949a7a981e4db132e96c960be125dfa2c8995adc0b7fa5e87a1d5bb9b7750b14`);
do not relabel that result.

For the fixed native-2888/PostgreSQL-18.6 profile, comparison profile
`truss-fresh-install-snapshot/2`
also handles this finite native identity class. PostgreSQL [appends the actual
trigger OID to an internally generated name](https://raw.githubusercontent.com/postgres/postgres/REL_18_STABLE/src/backend/commands/trigger.c).
Capture each trigger's actual native OID and foreign-key constraint linkage in
the same catalog observation. Normalize only an internal foreign-key trigger
whose exact `RI_ConstraintTrigger_a_` or `RI_ConstraintTrigger_c_` suffix equals
that canonical native OID. Retain its original name, definition, OID, linkage and
row position as closed evidence. Change only the exact initial quoted trigger
name token in its rendered definition and its name field. The replacement
retains the a/c prefix and the full SHA-256 of the canonical foreign-key identity
(owning schema, owning relation, constraint name and exact definition). Cross-check the native
constraint definition against its unique captured foreign-key constraint row;
the trigger's table need not be the constraint's owning relation. This preserves
the compared trigger-to-constraint association. Preserve all other definition
bytes, enabled state and original row order.
Require the complete 322-trigger inventory with exactly 260 such internal
triggers, rejecting duplicate, missing or out-of-range evidence. All 62 other
trigger rows remain exact. Collector and publication checks must validate the
same evidence and normalized correspondence. This permits no general OID mask,
sorting, row removal or additional generated-value class. A fresh source-bound
run must pass; the failed attempt does not become qualification evidence.

The finite trigger correction passes 40 focused pure controls, with independent
review passing all 19 measurement controls against unchanged reviewed hashes.
These include the actual collector path, native OID/FK-link failures, missing or
duplicate evidence, distinct FK identities, changed definition tails and exact
noninternal rows. A fresh actual comparison and complete Linux release workflow
remain required.

The repaired diagnostic passes 39 focused pure controls. Independent review also
passes all 18 measurement controls, including the actual snapshot collector with
native-shaped JSON OID strings and negative identity cases, original generation
evidence retention, secret redaction, exact public-0.0.49 helper absence and
candidate helper requirements. These controls clear the source for the hosted
campaign; they do not establish a successful native comparison or release gate.

If the developer machine cannot complete this comparison reliably, the same
driver and exact subjects may run serially on one owned worker in the existing
Linux release job. Retain original 60-second limits, complete snapshots and
explicit cleanup; bind the report to the candidate wheel/source payload and
publication checks. This fresh 0.0.49 performance fixture is specific to the
0.0.50 repair, not perpetual support for an old application runtime. All admitted
database forward-migration gates remain mandatory in future releases. Arras's
fresh installed Mac and actual Lakebase WAN acceptance remain separate gates.

## Scope

Address the Lakebase installation blocker reported by the consumer now named Arras with an explicit,
installation-scoped policy for existing platform grants, consistent subsequent
verification, and a structured refusal containing the offending role name.
Lakebase is Databricks's managed PostgreSQL service. ACL means access-control
list. The selected delivery accepts exact role names, defaults to no
tolerance, retains tolerated grants, and records the resulting trust boundary.
The local implementation and qualification below do not establish actual Lakebase support.

Source request: [Praxis ask](/private/tmp/claude-501/-Users-erik-Projects-praxis-harness--claude-worktrees-research-workflow-sql-queries-f5f5dd/ea7b1a5f-5eef-47c4-a21a-889e9967bcad/scratchpad/truss-requirements-from-praxis.md).
Read on 2026-10-22. Its durable requirements are captured below; the temporary
source path is not an execution dependency. The request describes deployed
0.0.45 and checkout 0.0.47. The inspected Truss package declares 0.0.48;
release qualification must select exact wheel and installed native manifests
instead of assuming the request's baseline remains current.

Governing artifacts: [PRD](../01-frame/prd.md), especially FR-41/43/44/48,
[ADR-008](../02-design/adr/ADR-008-trusted-embedding-host.md),
[embedding contract](../02-design/contracts/CONTRACT-007-embedding-and-execution.md),
[bootstrap contract](../02-design/contracts/CONTRACT-008-layout-bootstrap.md),
[installation plan](local-runtime-installation-migration-plan.md),
[forward migration plan](runtime-migration-restoration-plan.md),
[test strategy](../03-test/test-plan.md), and
[bootstrap tests](../03-test/test-plans/STP-045-bootstrap-the-internal-layout-from-umf.md).
The decision queue and remaining-design audit provide historical constraints;
their older unfinished-runtime summaries do not override later released scope.

## Original assessment

The following findings describe the pre-implementation assessment. Current
implementation and qualification status is recorded in Continuation evidence.

| Request / finding | Assessment | Proposed disposition |
| --- | --- | --- |
| Tolerate operator-named platform grantees | INCOMPLETE: fresh protection rejects any explicit grantee other than installer or PUBLIC, including column ACLs | Add an explicit opt-in deployment policy; preserve strict defaults and normal PUBLIC cleanup |
| Preserve tolerated ACLs | ALIGNED with the existing choice to refuse unrelated grants rather than erase them; broad native authority changes the deployment trust boundary | Preserve effective privilege, grant-option and delegation meaning; retain before/after native observations, including ownership-induced grantor changes |
| Apply policy after installation | INCOMPLETE: installation-only plumbing cannot satisfy later integrity checks | Carry the same stored policy through all reachable lifecycle and verification paths |
| Named refusal | INCOMPLETE: the ACL check raises ValueError, which the psycopg host reduces to invalid_transaction | Use a narrow typed refusal after confirmed operation rollback; retain outer transaction and transport failure meanings |
| Role-name patterns | UNDERSPECIFIED: matching, future roles and identity replacement have no proposed rules | Ship exact names first; resolve database-specific names after connecting. Do not require discovery before connection |
| Managed-service reproduction | Reported by Praxis, not independently executed in this assessment | Qualify a local event-trigger stand-in, then the actual managed consumer path separately |

The reported triggers grant schema USAGE/CREATE, relation SELECT/ALL, and sequence
privileges, sometimes WITH GRANT OPTION. Merely calling them platform roles does
not remove their authority. Toleration acknowledges their existing native access;
Truss must not claim those roles or their effective delegates are isolated by its
module policy. PostgreSQL grants and role inheritance have actual authorization
effects: [PostgreSQL 18 GRANT](https://www.postgresql.org/docs/18/sql-grant.html)
and [role membership](https://www.postgresql.org/docs/18/role-membership.html).
Whether every reported role is platform-controlled on the target remains a
consumer/operator fact, not something a name prefix proves.

Observed implementation anchors:

- `packages/python/src/truss/_installation_privileges.py`:
  `protect_installation_with_cursor` rejects third-party namespace, relation,
  routine, type and column ACL entries before ownership transfer. Its `_verify`
  also checks effective client authority and exact private defaults.
- `catalog_runtime.py`: `install_in_transaction` creates objects, protects them,
  persists installation metadata, then grants declared entrypoints. It currently
  accepts owner/registrar keywords; the request's `InstallOptions` is illustrative,
  not an existing public type in this checkout.
- `lifecycle.py` and `psycopg_host.py`: `InstallRefused` describes pre-DDL
  preflight; `_run_operation` contains failures but loses ValueError detail.
- `_migration_verify.py`: full object ACLs are compared to exact role profiles;
  unrecognized grantees and any column ACL refuse. A successful fresh install
  alone therefore cannot establish a supported upgrade path.
- `_current_query_protection.py`, `_security_home_installation.py`, preparation,
  action and subject installation helpers have additional closure checks; some
  paths revoke grants. Inventory both validators and mutators before changing
  them. A general ACL bypass would invalidate separately protected profiles.

No standalone public role-retirement API was established by this bounded review.
Map Arras's registration/retirement terms to the actual Python, CLI and SQL
routes in MG-1; require corresponding end-to-end coverage rather than inventing
an API or treating catalog element retirement as database-role retirement.

## Shared constraints and selected interface

1. Keep the existing installer, owner, registrar and caller custody requirements.
   An ordinary data caller cannot set or change the policy. No event-trigger
   disabling, session replication changes, superuser escalation, automatic retry
   or implicit installation is needed.
2. Use the additive `tolerated_grantees: tuple[str, ...] = ()` keyword on the
   existing fresh-install method, with matching explicit CLI/config plumbing.
   CONTRACT-008 records the exported shape. Validate a bounded
   typed list, literal PostgreSQL names, encoding/identifier limits and duplicates;
   never interpolate a name as SQL. Refuse PUBLIC and installation owner/registrar
   identities as tolerance entries. Resolve names to current native role object
   identifiers (OIDs) under the existing administrative exclusion.
3. Store a versioned canonical policy and resolved role names/OIDs with the
   installation, plus bounded observed ACL evidence: object/column identity,
   grantee, grantor, privilege and grant option. OIDs are database-local identities,
   not portable role IDs. Verify identity on later administration; renamed,
   missing or recreated roles require explicit administrative reconciliation.
   Restores must requalify/remap identities deliberately. Ordinary operations
   cannot widen the stored policy from a fresh host configuration.
4. The initial policy tolerates existing grants to each selected identity across
   supported installation objects, including later created objects. It does not
   issue grants or memberships to those identities, clone their grants to new
   objects, or remove their grants. Evidence states that privilege changes to
   tolerated identities remain within this trusted platform boundary. All other
   grants retain their existing exact checks. Unknown object kinds, foreign
   ownership, role membership leaks and effective client privileges still refuse.
5. Preserve the distinction between ordinary managed deployment and separately
   protected security profiles. For each affected protected feature, either prove
   its guarantees under the selected policy or return a named incompatibility
   before its effects. Do not filter platform rows out of every security query.
   Activation must never silently revoke tolerated grants.
6. Recommend exact names for this cut: Arras can resolve the database
   OID and actual names after connecting, then pass the typed list. Wildcards
   are deferred unless that integration proves exact resolution insufficient.
   Any later pattern design must define restricted syntax, bounded matching and
   an explicit resolved identity set; newly created matching roles cannot silently
   gain tolerated status. Never infer trust from `databricks_*` alone.
7. The `third_party_grant` refusal carries a bounded role-name field and
   safe object-class/phase context. Use a private typed marker through the host's
   established rollback boundary, then expose the public result only after
   containment succeeds. Do not catch it inside the install callback and return
   success while leaving newly created objects in the caller transaction.
   Unusable transactions, cancellation, retries and unknown settlement retain
   their outer failures; arbitrary ValueError text is never exposed.
8. Persisted policy/evidence and changed native routines require exact forward
   migration classification under ADR-008. Existing supported installations map
   to an empty strict policy; adding platform trust is explicit administration,
   not an automatic migration side effect. Immutable historical receipts stay
   unchanged. Arras owns consumer configuration, backend forwarding/error mapping
   and preview adoption. UMF/Weft semantics need no change.

## Implementation slices

| Slice | Output and ownership | Dependency | Validation gate |
| --- | --- | --- | --- |
| MG-1 | Truss: amend CONTRACT-008/007, relevant requirements and STP-045; map install/status/register/module-access/retirement/migration routes and all ACL checks, grant rewrites and effective-rights checks. Identify ordinary versus protected subsets. Adopt the source boundary map for the helper and carriers | None | Every reachable ACL predicate/mutator has a policy-aware behavior or explicit incompatibility; independently review trust/delegation, PUBLIC, source-role drift and refusal containment |
| MG-2 | Truss: bounded exact-name policy, shared classification helper, additive API and retained installation evidence; extend existing metadata rather than creating competing readiness authority | MG-1 | Empty-policy regressions; valid/invalid name tests; SQL quoting; missing/duplicate/reserved identities; no new grant/membership; module boundary checks |
| MG-3 | Truss: integrate fresh install and typed contained refusal, then status/catalog registration/module access/feed and actual retirement routes identified in MG-1. Qualify safe protected subsets or refuse activation before effects | MG-2 | Real native event-trigger install through registration/configuration, denied ordinary callers, grant preservation, rollback and subsequent-use checks; every planned lifecycle route exercised |
| MG-4 | Truss: policy-aware migration observation, explicit strict-policy source conversion and any required latest native recipe; include CLI/config and administrative policy reconciliation | MG-2, MG-3 | All currently supported lineage-to-latest paths, populated preservation, strict/tolerated profiles, drift and lost-acknowledgment recovery. No historical manifest relabeling |
| MG-5 | Truss: clean installed-wheel qualification, docs/example and release assets. Arras: exact version forwarding, named Unavailable detail and managed preview acceptance | MG-3, MG-4 | Original local negative controls and Linux release gates pass; actual Lakebase consumer receipt binds server/driver/library/wheel/native manifests and complete workflow. Local-only success remains labelled local |

Use `python3 scripts/check-module-boundaries.py` and
`python3 scripts/check-module-boundaries-controls.py`; preserve their actual
local/pre-commit/CI wiring. Review any new map entries explicitly. The policy
helper owns bounded classification and observation, not connection lifecycle,
policy authorization or security resolution. The runtime owns composition;
the host owns containment; migrations consume the same policy interpretation.
Do not add parallel private-client grant resolvers. Review native SQL and dynamic
imports separately from the Python checker's coverage.

## MG-1 implementation handoff and path inventory — 2026-10-22

MG-1's selected boundary is now recorded in CONTRACT-007/008, FR-41 and
STP-045 MG-T01–08. It is implementation-ready under the following explicit
inventory. MG-2 onward require source and native evidence; listing a path is
not qualification of its behavior.

All Python paths below are relative to `packages/python/src/truss/` and SQL
paths to `_catalog_runtime/` within that directory.

| Reachable route | Source and native anchors | Required managed-policy behavior |
| --- | --- | --- |
| Fresh installation / private privilege primitive | `catalog_runtime.py:install_in_transaction`, `_installation_privileges.py:protect_installation_with_cursor`, `_verify`; `runtime.sql:catalog_runtime_installation`, final `managed-grants.sql` | Validate at most 32 exact <=63-byte names; resolve native identities under exclusion, classify every object/column ACL, preserve selected permissions and original before/after evidence; publish post-DDL refusal only after rollback |
| Administrative and person status / role recovery | `catalog_runtime.py:status_in_transaction`, `person_runtime_status_in_transaction`, `admin_install_recovery_in_transaction`; `_lifecycle_runtime.py`; `lifecycle.sql`, `runtime.sql:runtime_person`, `migrations.sql:runtime_current_installation`, final replacement in `managed-grants.sql`, `person-entrypoints.sql` | Stored policy governs current identity; preserve original administrative/person disclosure split, exact manifest and ordinary effective-role denial |
| Catalog registration and retirement | `catalog_runtime.py:accept_in_transaction`; `catalog_preparation.py`, `_catalog_source_reference.py`, `_catalog_report_semantics.py`; `runtime.sql:catalog_accept_with_keys`, `evolution.sql`, `catalog-rebind.sql` | Catalog acceptance/evolution is the actual route for requested retirement changes; current record/relationship retirement may refuse as unsupported. Preserve platform ACLs and complete source/head/history on successful supported evolution and contained unsupported retirement; do not invent database-role retirement or native DROP ROLE administration |
| Module access and audit enrollment | `catalog_runtime.py:configure_module_access_in_transaction`, `grant_module_audit_access_in_transaction`; `runtime.sql:runtime_person`, `load-audit-reader.sql`, `load-audit-writer.sql`, `load-audit-storage.sql` | Keep recursive role/effective rights and raw table/column/sequence denial; a tolerated platform role or effective delegate cannot become an ordinary permission role |
| Feed enrollment / mutation / feed / ACK | `catalog_runtime.py:register_feed_consumer_in_transaction`; `feed.py`, `_group_runtime.py`; `feed.sql`, `groups.sql`, `operations.sql`, `person-entrypoints.sql` | Preserve stored identity and current ordinary authorization; no new platform grants or membership; qualify actual ordinary end-to-end mutation/history/feed/ACK |
| Migration status / prepare / apply / reconciliation | `migrations.py`, `_migration_recipe.py`, `_migration_verify.py:acl`, `roles`, `verify`, `installed_profile`; `_migration_execute.py`; `migrations.sql`, `_migrations/manifest.json` | Exclude only selected platform ACL identities from ordinary profile comparison; retain exact checks for everything else, including column ACLs, qualified grantor identities, role closure, defaults and native definitions. A validated selected grantor may issue only otherwise exact declared ordinary grant tuples. Add strict empty carrier to admitted predecessors in one reviewed forward recipe |
| Explicit local launcher and migration CLI | `cli.py:_installation`, `main`, `migrate_main` | Existing CLI installs an owned local pgserver; it is not a generic Lakebase connection CLI. Add explicit fresh-install forwarding where applicable; reconnect uses stored policy. Migration remains a separate administrative session |

The supported field bounds and retained carrier are CONTRACT-008's
`managed_grants` version `truss-managed-grants/0.1`: at most 16,384 initial
ACL observations for selected tolerated grantees only and 4 MiB total canonical
UTF-8. Empty strict policy retains no observation rows; full unrelated-grant and
effective-rights checks remain. Native capture uses bounded set-oriented queries,
not one query per installed object. The helper owns classification
and bounded observations; the host owns rollback, runtime owns composition and
migration consumes that same policy. Source ownership and release/manifest
coordination are explicit because concurrent HF edits change these entrypoints.

Protected ACL validation/mutation inventory, all requiring exact combined
qualification or a pre-effect incompatibility for nonempty policy:

- Activation and private home/grant rewrite: `_current_query_protection.py`
  (`activate_current_query_protection_in_transaction` currently revokes routine
  recipients with CASCADE), `_current_query_subjects.py`, `_current_query_stage.py`,
  `_security_home_installation.py` and `_security_mapping.py`.
- Security issuers and subject/role cuts: `_security_source_epoch_installation.py`,
  `_security_catalog_subject_installation.py`, `_security_catalog_subject_helpers.py`,
  `_security_graph_subject_installation.py`, `_security_catalog_read_cut_installation.py`,
  `_security_graph_epoch_read.py`, `_security_relationship_epoch_read.py`,
  `_security_data_writer_binding.py` and `_security_preparation_authority.py`.
- Preparation and action registration: `_preparation_catalog_cut.py`,
  `_preparation_source_epoch.py`, `_preparation_seal_installation.py`,
  `_preparation_sources.py`, `_preparation_program.py`, `_action_store.py`,
  `_action_subject_installation.py` and `_action_role_installation.py`;
  `_security_bootstrap/preparation-bridge-inventory.sql` and
  `_security_bootstrap/action-store-issuer.sql` retain exact native ACL checks.
- Generic installed observation and fact/epoch cuts: `_installed_admission_inventory.py`,
  `_psycopg_fact_cut.py`, `_psycopg_epoch_cut.py`; `_inventory_sql/namespace-acl.sql`,
  `relation-acl.sql`, `routine-acl.sql` and `column-acl.sql` retain original evidence.
  No managed-policy row filter may silently redefine protected inventory.

The inventory includes both ACL predicates and their grant/ownership mutators.
Implementation review must follow directly callable helper routes as well as
assembly entrypoints, and identify any newly added source path before claiming
MG-T06 complete. Existing PUBLIC cleanup remains distinct from tolerated grants;
ordinary later declared public person entrypoints retain their own exact profile.

### Native artifact generation and qualification

The inspected latest package is the unpublished `0.0.48` candidate. Concurrent HF
refinement selected native manifest `c4339ac7f09ab5a004c272ab00962107a970938004c1765ec4163e4d5ca9b6f0`.
This is a source snapshot, not a released promise; freeze the final combined native
and migration hashes after both workstreams settle. Preserve every published
source44/source46/source47 manifest/profile/recipe and original archived migration
manifest. The old unpublished `2f230a…` target is separately archived in the HF
regression evidence and must not become an admitted published lineage source.

Existing generation and qualification entrypoints:

```sh
python3 scripts/build-person-entrypoints.py --declarations ORIGINAL_NATIVE_DECLARATIONS.json
python3 scripts/check-module-boundaries.py
python3 scripts/check-module-boundaries-controls.py
UMF_NATIVE_ROOT=/Users/erik/Projects/umf bun scripts/check-runtime-migration-model.ts
bun scripts/check-catalog-runtime-owner.ts
python3 scripts/qualify-runtime-migrations.py --installed-package --wheelhouse /private/tmp/truss-runtime-migration-wheelhouse --output EVIDENCE/qualification.json
```

The migration-model command above is the historical full-file checker; its
fixed model and evidence output paths refer to original migration delivery.
A changed `migrations.sql` routine requires new current model/receipt identities
and output paths. Preserve the published packaged `receipt-model-0.1.umf.json`
and `receipt-model-0.1.evidence.json` byte-for-byte; both are immutable lineage
artifacts. Do not overwrite their original evidence while qualifying a new body.

The person-entrypoint generator requires original native metadata; do not invent
function signatures. `scripts/build-owned-runtime.py` is pinned to native72 and
cannot regenerate native74 as a generic hash refresher. Likewise,
`scripts/build-runtime-migration-baseline.py --source44-wheel WHEEL44
--source46-wheel WHEEL46 --output DIRECTORY` is the initial bounded baseline
builder: it hardcodes the initial receipt-table/routine delta and is not a
subsequent managed-policy migration generator. `scripts/build-managed-grants-migration.py`
now owns the bounded target capture and explicit forward edge for the authored
managed column/check/routine. It verifies the published source47 wheel and frozen
runtime manifest, captures both installations in disposable PG18.6 workers under
New York and UTC, checks the exact delta against the preceding HF candidate, and
retains the historical source profiles and edge bytes. Capture first into one
review directory, then finalize without starting another worker:

```sh
WHEEL=/private/tmp/truss-runtime-migration-wheelhouse/truss_toolkit-0.0.47-py3-none-any.whl
CAPTURE=/private/tmp/truss-mg4-managed-grants-20261022
TARGET=35fd797b5cf48dd888c68e53b9e599df20cffe00f8f3d33e1563820ea808d59f
python scripts/build-managed-grants-migration.py --source47-wheel "$WHEEL" \
  --expected-target-manifest-sha256 "$TARGET" --output "$CAPTURE" \
  --initialization-time-zone America/New_York
python scripts/build-managed-grants-migration.py --source47-wheel "$WHEEL" \
  --expected-target-manifest-sha256 "$TARGET" --output "$CAPTURE" \
  --initialization-time-zone UTC
python scripts/build-managed-grants-migration.py --source47-wheel "$WHEEL" \
  --expected-target-manifest-sha256 "$TARGET" --output "$CAPTURE" --peer "$CAPTURE" \
  --finalize-captures --check-only
python scripts/build-managed-grants-migration.py --source47-wheel "$WHEEL" \
  --expected-target-manifest-sha256 "$TARGET" --output "$CAPTURE" --peer "$CAPTURE" \
  --finalize-captures --package
```

The frozen local target is `35fd797b…`; its direct forward edge starts at the
published source47 digest. The model `truss-managed-grants-0.1.umf.json` and
`managed-grants-model.json` capture separate UMF import/export AST correspondence
for the new SQL fragment. That evidence does not replace native installation or
migration checks. Keep the published receipt-model-0.1 artifacts byte-identical.
Release packaging must recheck that 0.0.48 remains unpublished before freezing
these candidate artifacts.

Local qualification uses macOS ARM64, PostgreSQL 18.6,
`pgserver-pg18==18.6.1`, stock psycopg 3.3.6 and the selected Weft/UMF package
closure. The final execution environment is
`/private/tmp/truss-managed-grants-qualification/venv-final-3`; exact imported versions
and wheel hashes belong in its receipt. Store original new evidence under
`docs/helix/04-build/evidence/design-audit/managed-grants-20261022/`.
Hosted release CI remains Linux only. The existing migration gate uses real
wheel fixtures from the declared wheelhouse and must run from the clean installed
latest wheel, not the source tree. The selected installed regression, populated
migration and original public workload gates pass as recorded below. The legacy
complete-suite gate remains unresolved; actual Lakebase/consumer forwarding
and hosted release evidence remain external.

## Validation plan

Extend the existing native installation, managed-installation, install-preflight,
module-access and runtime-migration suites. First reproduce the refusal with a
privileged test-fixture event-trigger installer; execute Truss as a distinct
non-superuser CREATEROLE/database administrator that cannot disable those triggers.
Use the existing reusable PostgreSQL 18.6 Unix-socket workers and fresh roles and
databases; isolate cluster-changing tests and verify cleanup.

Required acceptance matrix:

- Empty policy reproduces named refusal for schema/table/sequence and authored
  routine/type/column cases. Tolerated-only grants pass; tolerated plus one
  unlisted grantee refuses and identifies that exact role.
- Independently read native ACLs before and after ownership transfer, installation,
  registration, access configuration, retirement and migration. Preserve platform
  privileges and grant options; distinguish grantor identity transformation from
  a deleted permission. No tolerance-issued access appears.
- Reconnect with a fresh assembly: stored policy still governs. Spoofed prefixes,
  missing/recreated/renamed identities, unauthorized policy widening and native
  object/owner/definition drift cannot establish readiness. Client inheritance of
  tolerated raw access remains a failure of the ordinary-client boundary.
- A post-DDL refusal rolls back schema/roles/grants/marker while preserving prior
  caller work and search path. Cancellation, native permission errors, deadlocks,
  cleanup failure and uncertain settlement keep their original outcome class.
- Protected activation either passes its actual allowed/denied controls or returns
  explicit incompatibility with no platform-grant rewrite. Ordinary end-to-end
  writes, journal, feed and ACK remain correct for authorized consumers.
- Qualify populated strict predecessor migration and managed-policy latest
  installation/migration. Preserve source bytes, identities, values/history,
  receipts/feed/ACK and frozen evidence under all required lineage paths.
- Clean wheel execution and Arras forwarding preserve the tuple and named
  refusal. Capture actual Lakebase TLS/token/transaction behavior separately;
  a stand-in trigger proves only the local PostgreSQL behavior.

Run new focused native cases, affected regression suites and boundary checks first;
then the existing installed-suite/migration/public-workload release gates on the
final source. Hosted CI runs Linux only; local native checks use the development
machine's platform. Focused managed native checks have run during implementation;
final installed-wheel gates are tracked separately below.

## Risks and rollbacks

| Risk | Response | Rollback / recovery |
| --- | --- | --- |
| Trusted platform roles have raw read/write/delegation authority | State the real trust boundary; test ordinary caller effective access and protected incompatibilities | Refuse the opt-in deployment if the operator cannot accept its authority; never silently revoke platform grants |
| Install passes but later verification or grant cleanup contradicts it | Complete the MG-1 inventory and use one stored policy interpretation | Keep failed operations contained; retain previous installation and caller work |
| Wildcard or role replacement broadens trust | Exact resolved identities in the first release; explicit policy reconciliation | Refuse identity drift until deliberate administrator action |
| Metadata change strands previous installations | Exact immutable source recognition and populated lineage qualification | Forward fix or tested backup restore under ADR-008; no old-runtime support promise |
| Typed error conversion hides transaction damage | Publish only after confirmed containment; outer failure takes precedence | Preserve existing quarantine/discard and original recovery custody |

## Execution contract

The owner has authorized implementation with Sol planning/review and Luna
implementation. This documentation slice owns only governing amendments and the
MG-1 inventory; runtime source, native qualification and review evidence have
separate owners. Implementation follows MG-1 through MG-5; planning readiness
is not managed deployment acceptance. Do not make unavailable Lakebase credentials a
blocker for local implementation or qualification; keep the actual managed gate
open until original consumer evidence is available.

No token ceiling was supplied and no hard meter is asserted. The authorized
implementation has proceeded through the MG-1 inventory, runtime changes and
MG-4 artifact generation; final qualification controls completion claims.
No tracker or publication is selected. The owner-selected Sol/Luna agent work
shares this checkout with explicit documentation/runtime source ownership.

## Continuation evidence

Plan revision 4, 2026-10-22: MG-1 governing amendments and inventory are complete.
MG-2/3 runtime changes implement bounded exact-name policy, immutable initial ACL
provenance, contained named refusal, native identity checks, ordinary lifecycle
paths and explicit pre-effect protected-profile incompatibility. The focused
managed native matrix passes all 13 cases in the final installed-wheel run.
[Supplemental final-wheel evidence](evidence/design-audit/managed-grants-20261022/supplemental/final-3/receipt.json)
qualifies supported optional-field evolution, unchanged source/history/data,
later selected-role INSERT addition/removal accepted by status/verification, and
an unchanged initial policy carrier. Current record and relationship retirement
remains unsupported: the actual record-retirement attempt returns the exact
`0A000`/`unsupported_profile` refusal, preserves prior caller work through COMMIT,
and leaves head/source/history/data/ACLs unchanged. This does not claim successful
retirement support.

MG-4 has a source-ordered final managed-grants SQL fragment, a separate current
UMF model, native captures for both qualified initializer timezones, and an
explicit source47-to-latest edge. Sol's final source review found the 15 existing
immutable migration artifacts byte-identical to their HEAD bytes and pinned
hashes. Initial observations remain historical provenance: later selected-role
object/column ACL changes are tolerated, while ordinary grants, exact private
defaults, native definitions and owners retain their checks. The native migration
control also proves a selected grantor's duplicate exact registrar EXECUTE is
admitted, while an extra ordinary grant option refuses; the selected platform
trust does not add an ordinary privilege tuple. All 80 final installed
lineage and recovery controls pass without skips, including original source-field
preservation and the explicit new empty strict carrier.

The final candidate-3 source selects native manifest
`35fd797b5cf48dd888c68e53b9e599df20cffe00f8f3d33e1563820ea808d59f`,
wheel SHA-256
`7a41a223033c1af0da4a2df2d377c672fcd3b3be1fcfc5b5bf8232d009725ed4`
and sdist SHA-256
`281174fc976070fa23d05bb3a7e08c4a1b63d3f3c0025667889fadb52a3ebff1`.
The build audit found all 459 Truss payload files byte-identical across source, wheel
and sdist. The separate `venv-final-3` installation preserves earlier diagnostic
environments. Candidate 3 includes the strict preparation routine
replacement/overload selection and exact declared ACL census corrections, plus
CLI handling for a typed contained refusal: one safe JSON refusal object and
exit status 1, with no attempt to read a refused installation's pending identity.
Only `truss/cli.py` differs from candidate 2; the other 458 package files and
native manifest are byte-identical, as recorded in
[`build/final-2-to-final-3-payload.json`](evidence/design-audit/managed-grants-20261022/build/final-2-to-final-3-payload.json).
The final HF-07 archive is
[`final-cli-migration-35fd.zip`](evidence/design-audit/managed-grants-20261022/hf61/final-cli-migration-35fd.zip),
SHA-256 `4be0ed4a0ad6f781cc160325caaf24f15d19fd365663a3e6f9ff7d920baf5ce6`.
Its profile SHA-256 is
`0945348e235fbcdd29cf499bd02457c4d618017582d34d83bf28d69d7854c859`;
all 61 case entries and limits remain unchanged. Only the current native digest
and five producer hashes differ from the retained HEAD profile. Three producers
now distinguish person-shim `P1403` from direct native `42501`; the other two
qualify CLI refusal handling and compare migration preservation over original
source-era columns while explicitly checking the new strict carrier. No
installation table is skipped and the HF case set is unchanged.

The final local gates pass on the exact candidate-3 wheel:

| Gate | Result | Original receipt |
| --- | --- | --- |
| Fresh selected managed/strict/host/protected-source/catalog/CLI regression | 19 modules, 116 tests, zero skips; worker baseline restored and stopped | [Selected regression](evidence/design-audit/managed-grants-20261022/attempt-4/selected-components/qualification.json) |
| HF-07 canonical corpus | 61 tests, zero skips/failures/errors | [HF corpus](evidence/design-audit/managed-grants-20261022/attempt-5/hf-corpus/qualification.json) |
| Existing strict protected regression | 9 tests, zero skips; does not qualify nonempty-policy protected activation | [Native output](evidence/design-audit/managed-grants-20261022/attempt-5/protected-regression.log) |
| Every admitted published lineage to latest | 80 tests, zero skips/failures/errors | [Migration gate](evidence/design-audit/managed-grants-20261022/attempt-5/migrations/qualification.json) |
| Original public small workload | 1,000 objects and 1,000 edges, 1,000 reads, 200 committed updates; reopened connection verified; 26,121 counted SQL submissions | [Workload](evidence/design-audit/managed-grants-20261022/attempt-5/public-workload/report.json) |

[The final remaining-gates receipt](evidence/design-audit/managed-grants-20261022/attempt-5/qualification.json)
records `passed=true` and `inputBasisUnchanged=true`; the selected regression
independently records unchanged inputs and exact installed/wheel/source payload.
These establish bounded local qualification on macOS ARM64, not a general
performance target or complete release acceptance. HF pin preflight from
attempt 4 remains a separate failed integrity observation. The reviewed canonical
profile was installed before attempt 5; that does not relabel the earlier
preflight as passed. Earlier
[`selected-regression-aggregate.json`](evidence/design-audit/managed-grants-20261022/selected-regression-aggregate.json)
retains candidate 2's 17-module/111-test observations as historical evidence;
the final 19-module run is fresh on candidate 3. Supplemental lifecycle evidence
was repeated on the exact final wheel with original candidate-2 evidence retained.

The first broad installed-suite diagnostic remains at
[`attempt-1/qualification.json`](evidence/design-audit/managed-grants-20261022/attempt-1/qualification.json)
for wheel `01c35175218f75809808bb756303a28ea04046b55b0ab944bfbfb57ece6bc606`.
The unchanged legacy full-discovery producer rejects historical opt-in skips and
obsolete proof fixtures requiring absent `truss.row_home_capacity` and
`truss.row_home_operation` homes (`test_edge_event_frame_native` and
`test_epoch_state_fence_native`). Failed cleanup stopped that worker's reuse.
Other excluded campaigns require older compiler/native bundles incompatible
with the selected tuple. Retain their original failures and unrun/unqualified
status; do not add obsolete schemas to make them pass. The final current
19-module selection establishes bounded regression only. It does not pass
all-module discovery or close the unresolved legacy complete-suite gate. The
exact HF-07 corpus and mandatory full lineage gate remain independent
requirements; historical or skipped required cases cannot close them.

Arras is the active consumer handoff name. The original Praxis request and
historical Hohfeld/Praxis snapshots and IDs remain provenance. Arras must forward
the exact typed tuple and named refusal, select its exact wheel/native tuple,
and qualify its actual Lakebase TLS/token/transaction behavior and required
protected features. Those external receipts remain open.

Concurrent HF changes were composed into the frozen candidate; the original
assessment anchors are historical context. Local qualification alone did not
authorize publication. The owner subsequently authorized the release; its exact
current public status is recorded in the release execution and closeout below.

## v0.0.49 release execution — 2026-10-22

The owner has now authorized finishing, committing, reviewing, testing and
releasing this change. This extends the earlier local-only execution authority;
it does not relabel any earlier artifact or failed diagnostic. The selected
managed-grants version is v0.0.49. Preserve v0.0.48's separate HF release notes,
source, immutable migration evidence and publication ownership.

The active [operator guide](../../../packages/python/README.md#runtime-migrations--v0049)
selects v0.0.49 in pip, example-tag and isolated `uvx`/constraints commands.
Its commands require the matching qualified public assets and tag. The historical
v0.0.48 follow-up section and migration link alias remain intact. Actual public
source48 admission is complete. The v0.0.49 release is published and its
exact tag/public verification is retained in [public release proof](evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json).

The integrated source retains the newer HF62 corpus, exact public Weft0.4.51
cohorts from source `557153731e9f5d0583193a1189a07c6ed485d3d3`, reproducible archive
generation and publisher compiler/source checks. At that integration checkpoint,
the native manifest was
`35fd797b5cf48dd888c68e53b9e599df20cffe00f8f3d33e1563820ea808d59f`;
the later qualified audit-accumulation target is native2888 below.
CONTRACT-008 RM-01 uses exact manifest identity; the shared native label
`truss-catalog-runtime/0.74-candidate` does not make the v0.0.48 `c4339ac7…`
installation current. The earlier 459-file candidate and HF61 archive remain
historical evidence after this integration. Final v0.0.49 package/recipe/archive
hashes must come from its own build and receipts.

Public Weft0.4.51 dependency integrity is now verified in the
[public dependency receipt](evidence/design-audit/managed-grants-release-049-20261022/dependencies/public-weft-051/verification.json).
All nine assets match their public API digests; the original checksum manifest
covers the three wheels. Wheel ZIP/RECORD/native checks and the public packaging
receipts bind the selected Mac ARM64 and Linux x86_64 cohorts to source557.
The public tag/workflow commit `d4b0b98507ae15bd98180a2ea2030ea92ce11d96`
is distinct from that compiler source freeze. Linux aarch64 received packaging
inspection only. This dependency audit executes no native qualification.

The source86 artifacts and earlier preliminary Truss results remain historical
evidence. In the 363-entry producer ledger, the merge changes only the reviewed
disclosure-cohort digest; all 62 cases and limits, the six
managed/portable producer overrides, v0.0.49 toolkit version, native35fd and
managed release gates are preserved. Final Truss qualification must use the
new public compiler bytes. The historical35fd installed macOS campaign below passes for its recorded
artifact. Current native2888 installed macOS ARM64 and hosted branch Linux
qualification pass below; this candidate checkpoint preceded the final tag
and public verification retained in [public release proof](evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json).

The [public v0.0.48 integrity receipt](evidence/design-audit/managed-grants-release-049-20261022/dependencies/public-truss-048/verification.json)
binds its published wheel SHA-256
`1aedf614ff3d3ff7a61bd4d91887ede650a7135d1239e8564c1c297c0ddc37c3`
to tag commit `8e89a068bcb68f1e631388ddc59bc97da748563d`, nativec433 and
original migration manifest7d165. The
[source48 admission receipt](evidence/design-audit/managed-grants-release-049-20261022/source48-admission/receipt.json)
records successful America/New_York and UTC captures, read-only comparison and
additive packaging. All 18 previously pinned current artifacts and all 15
published v0.0.48 migration artifacts retain their exact bytes. The added ACL
profile, managed-grants-only edge and archived original v0.0.48 manifest admit
the fourth source without changing native35fd. The resulting migration manifest
is `86bcf78541e316c7e5697fb91e09d4741ef3e3cb5600b9b76ac5c6cc2e836923`.
This closes public input integrity and route admission; it does not qualify the
final v0.0.49 wheel or its complete migration/recovery campaign.

### Historical source628 installed macOS qualification

The [final local receipt](evidence/design-audit/managed-grants-release-049-20261022/final-local/qualification.json)
accepts the exact macOS ARM64 scope on source
`6287e52a5ef8a0abce90341106e8e9389216cb80`, Python3.11.17, PostgreSQL18.6,
Weft0.4.51 source557/Mac native3469 and the independent UMF5ba/Bun1.4.3 oracle.
Its [payload audit](evidence/design-audit/managed-grants-release-049-20261022/final-local/payload-verification.json)
records these artifact identities:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `26cf1fd712930bc9e573682cc6b04b428756201cf619de902d2108769a90e5ff` |
| Native manifest | `35fd797b5cf48dd888c68e53b9e599df20cffe00f8f3d33e1563820ea808d59f` |
| HF62 corpus | `d5b89965ea9962049077fb1b813aed32341c9c8948c70b526a8baf21e5eeabfe` |
| HF archive | `c6b1eff58cf81beaf85bf0013f72156aca15654e2a61de49e5e43d440c1666c3` |

All eight local campaign steps exit zero: 20 boundary controls, 20 managed
modules/128 tests, 62 HF cases, nine strict protected tests, all 106 migration
and recovery tests over four actual published source wheels, lifecycle controls
and the original public workload. Test campaigns have zero skips, failures and
errors. Lifecycle evidence covers supported additive evolution, contained
unsupported-retirement refusal and later selected ACL changes with the immutable
carrier preserved. The workload verifies 1,000 objects, 1,000 edges, 1,000 reads,
200 committed updates and values after connection reopen; it counts 26,121 SQL
submissions. It does not establish a broader performance target.

The review verifies all 1,198 frozen input pins, 462 matching
source/wheel/sdist/installed runtime files, oracle/compiler identities, eight
outer log hashes and all 20 managed module log hashes. Worker cleanup and the
local producer's unchanged-input/payload/identity controls pass. The
[retained-file index](evidence/design-audit/managed-grants-release-049-20261022/final-local/retained-files.json)
binds the 56 original outputs retained losslessly. This is local acceptance of
the recorded artifact and platform. The later hosted tag Linux campaign and
public verification are retained in [public release proof](evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json).

The [first Linux failure](evidence/design-audit/managed-grants-release-049-20261022/linux-attempt-1/receipt.json)
preserves the two source48 rollback-test failures caused by fault injectors that
matched a statement absent from the short edge. The reviewed correction retains
all prior assertions and deadlines and adds exact injection checks across all
four routes. Only its HF producer digest changed. The
[second Linux failure](evidence/design-audit/managed-grants-release-049-20261022/linux-attempt-2/receipt.json)
preserves the corrected source628 run: all 106 migration tests passed, while one
HF case exceeded a native deadline with SQLSTATE57014. The same unchanged case
passed in the local campaign and public48 Linux evidence. Host speed is a possible
explanation, not an established cause. Sol recommended one unchanged failed-job
rerun of run39845177814 at that checkpoint. The repeated failure retained below
led to Linux timing/plan diagnosis; no assertion or limit was weakened.

The current release acceptance campaign is the finite installed-package campaign
in [`.github/workflows/release.yml`](../../../.github/workflows/release.yml),
executed on hosted Linux only. It already names supported embedding, native
authorization, preparation, query/disclosure, catalog, capacity, lifecycle,
migration and original public-workload regressions. The new mandatory managed
step invokes `scripts/qualify-managed-platform-grants.py` against the installed
wheel. Its 21 explicit modules include managed install/migration, preparation,
CLI, strict lifecycle/ACL/host and catalog regressions, including the complete
`test_catalog_key_backfill_native` module and two audit-accumulation semantic
controls. The selected set discovers 130 tests. It owns a native worker, requires
inventory restoration after each module, stops on failure, rejects skips and
retains raw logs and the final cleanup/input/payload receipt. The separate
local-runtime step also includes `test_local_install_cli_native`.
Every mandatory campaign step must pass.
Normal PR smoke checks and selected local component receipts alone cannot close
release acceptance.

The 21-module campaign also requires an independent strict protected test oracle:
set `UMF_OWNER_ROOT` to an unmodified UMF checkout at
`5ba77cff91a121a44c82f6bce32a78d8842161b5`, install its dependencies with
`bun install --frozen-lockfile`, and select Bun1.4.3 through
`TRUSS_BUN_EXECUTABLE`/PATH. The release workflow checks out that exact owner
revision separately; the runner verifies the revision, source/lock cleanliness,
package/lock hashes and unchanged oracle inputs before and after the campaign.
This test oracle supplies original UMF action preparation. It is not a deployment
sidecar or a change to Truss's embedded runtime dependencies. Use an isolated
checkout when the primary UMF workspace has concurrent changes. Earlier missing
oracle or platform-specific executable failures remain diagnostic evidence;
portable executable selection preserves the original behavioral assertions.

| Campaign source | Acceptance authority and scope |
| --- | --- |
| `.github/workflows/release.yml` package/native jobs and publish dependencies | Mandatory current Linux release campaign, including its original public workload on a tag and the explicit managed-grants step |
| `scripts/qualify-managed-platform-grants.py` | Installed/wheel/source correspondence and 21 explicit regression modules on an owned native worker; earlier 19/20-module receipts retain their original scopes |
| `scripts/qualify-runtime-migrations.py` and packaged `_migrations/manifest.json` | Every admitted source needs an exact real wheel fixture and a route; prior published manifests/immutable files remain in custody; skipped cases cannot pass |
| `scripts/run-hf-conformance.py` and `hohfeld-followup-0.1.json` | Exact current package/native/compiler cohort and all 62 authored corpus cases; changed producers or skipped cases cannot pass |
| `.github/workflows/python-runtime.yml` | PR/runtime smoke qualification; does not replace the release campaign |
| `scripts/check-python-installed-suite.py` and `scripts/run-python-installed-workers.py` | Historical all-discovery diagnostic over every `test_*.py`; not invoked by the release workflow and not evidence that all discovered components match the selected runtime |

The earlier all-discovery diagnostic is preserved as incomplete and unqualified.
Its historical proof fixtures depend on removed native homes, while some opt-in
campaigns require incompatible older compiler bundles. Those are outside the
supported current release campaign. This release disposition supersedes the
earlier wording that made a green unchanged all-discovery producer a separate
release prerequisite. It does not delete tests, grant a generic skip allowance,
or claim all-module discovery passed. Any failure in a mandatory current release
step still blocks release and requires diagnosis; failed native cleanup still
forbids worker reuse. Separate exact historical campaigns retain their own
unrun/unqualified status.

| Release slice | Required result | Current state |
| --- | --- | --- |
| Integrate and version | Preserve the HF baseline and select v0.0.49 with its own notes | Complete; [released notes](releases/v0.0.49.md) and the published artifact identities are retained in [public release proof](evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json) |
| Admit v0.0.48 | Use its actual public wheel/hash, retain its exact source profile and original migration manifest, append the `c4339ac7…` → current route | Complete: actual public wheel integrity and paired native initializer captures; [admission receipt](evidence/design-audit/managed-grants-release-049-20261022/source48-admission/receipt.json). Current2888 macOS and branch Linux 106-case campaigns pass below |
| Freeze and review | Build final wheel/sdist/archive; verify exact runtime payload, historical bytes, compiler cohort, source boundaries and final diff | Current2888 wheel57fd, archiveae57, migration96add and historical bytes reviewed; exact installed Mac and branch Linux campaigns pass |
| Qualify final artifacts | Installed managed controls, current HF62 corpus, all four native source manifests, prior receipts/recovery/restore, supported strict/protected routes and original public workload | Complete for published native manifest `288801f7…`: selected Mac ARM64 installed campaign and branch Linux campaign pass 21-module/130-test managed controls, HF62, 106 migration/recovery tests, lifecycle/protected controls and workload. See the [Mac receipt](evidence/design-audit/managed-grants-release-049-20261022/final-local-2888/qualification.json), [Linux receipt](evidence/design-audit/managed-grants-release-049-20261022/linux-2888-branch/receipt.json), and [public release proof](evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json) |
| Hosted release and public verification | Mandatory Linux package/native campaign passes, then tag/asset/source pins and public downloads agree | Complete: tag `v0.0.49` at `dd13e95804abc30202d449a756240c6a684ab942`, mandatory hosted Linux release workflow, public API asset digests/checksums and independent installed Mac ARM64 verifier agree; see [public release proof](evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json) |

Actual Arras/Lakebase TLS/token/workflow acceptance remains a separate deployment
qualification. The package may describe the explicit policy and locally proven
behavior without claiming that external deployment. Nonempty-policy protected
activation stays unsupported. Release closeout must keep those limits explicit
and link the final exact artifact receipts; it must not promote the old local
wheel hashes to the new release.

## Exit criteria

Planning, implementation, Truss release qualification and publication of
v0.0.49 are complete for the exact artifacts retained in the [public release proof](evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json). The tag
campaign and independent public verifier bind the published assets and source.
Truss has completed its MG-5 release slice; Arras consumer forwarding/adoption
and actual Lakebase TLS, token and transaction acceptance remain separate open
work. The selected Mac ARM64 and hosted Linux proofs do not establish full-engine
or all-discovery qualification.
The source628/native35fd macOS campaign remains historical. Actual public
v0.0.48 input integrity and additive route admission are complete. The historical all-discovery
diagnostic remains unqualified outside that supported release campaign. Actual
Lakebase/Arras deployment acceptance stays a separate gate with no support claim
until its exact consumer workflow is qualified.

### Audit deadline diagnosis and additive candidate supersession

The unchanged Linux rerun reproduced the whole-group audit deadline failure.
Same-host public48/current49 diagnostics both reached the original 10-second SQL
deadline in the shared collector. A representation-only appended collector
override is now a diagnostic candidate with native manifest
`288801f7177338328441b5d3ce9328af31740ebf513f04ea45e30ae316a9f3a4`.
The original35fd local pass remains historical evidence for source628. The new
candidate preserves validation, order, duplicates, nulls, owner reduction, bounds,
late authorization and both complete collector calls.

The [capture and packaging receipt](evidence/design-audit/managed-grants-release-049-20261022/audit-accumulation/receipt.json)
records passing actual America/New_York and UTC native source/target comparisons
and additive packaging through the reviewed
[producer](../../../scripts/build-audit-accumulation-migration.py). The exact
private source fixture is the earlier v0.0.49 wheel26cf; it is an intermediate
native fixture, not an admitted public source wheel. All 21 prior migration
artifact bytes and the four actual public source-wheel entries remain unchanged.
Four additions retain the old 86bc manifest and supply the new 2888 profile, exact
ACL census and 35fd→2888 SQL-only edge. The current migration manifest is
`96addcdb95523f478d8f50b0b47198e47a860680c7400dd359711930e837e535`.
The complete forward routes contain three edges for public 44/shared46 and two
for public47/public48, executed atomically by the latest tool.

The fresh-install [retained diagnostic](evidence/design-audit/managed-grants-release-049-20261022/audit-diagnostic-39852375031/receipt.json) ([run39852375031](https://github.com/DocumentDrivenDX/truss/actions/runs/39852375031))
passes both the unchanged public48 and new 2888 case on the same AMD EPYC9V45
host. Instrumented complete-page SQL takes 6.940221s versus 0.380100s; original
whole-test times are 12.764s versus 5.619s. Both default event-budget refusals remain
SQLSTATE54000, the 10-second SQL/30-second operation limits remain unchanged, and
all owned workers restore inventory and stop. These are bounded prototype
measurements with instrumentation overhead, not a release performance budget.
They do not replace the failed 9V74 diagnostics or establish full corpus success.

The managed campaign now selects 21 modules/130 tests, including the two new
semantic controls. HF keeps all 62 cases, limits and compiler cohorts; all 363
existing producer digests remain unchanged and the new test producer makes 364.
Native capture/packaging and one-case diagnosis are complete. New exact-artifact
Mac/Linux/corpus/lineage/lifecycle/workload qualification now passes below.
At this earlier candidate checkpoint, the final tag and public verification
were pending; the later completed status is retained in [public release proof](evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json).

### Hosted branch Linux qualification — native2888

The [full Linux branch receipt](evidence/design-audit/managed-grants-release-049-20261022/linux-2888-branch/receipt.json)
records run39854672450 at source
`4188141faf3e51a7a25711a6fc22751cb37c7ae4`. The package and complete mandatory
branch native jobs pass. The exact wheel is
`57fd9520a453dcafa52dabe6aa75a143c162593237e80177acaebdbd51202790`,
with native2888 and migration96add. All 467 source/wheel/sdist runtime files
agree; the HF archive has 411 exact manifest-bound source payloads and SHA-256
`ae5726d745e6ce52f1229ad1d1b46ca6a5ff55d8cb0bb0aa73751f2dd8fd0eb6`.
The current corpus remains 62 cases/364 producer bindings.

The hosted run passes 21 managed modules/130 tests with zero skips and confirmed
worker restoration/shutdown, unchanged inputs/payload and the pinned clean
UMF5ba/Bun1.4.3 oracle. HF62 and all 106 migration/recovery tests pass with zero
failures, errors or skips, using public Weft557's exact Linux cohort and all
four actual public source wheels. The formerly failing audit case passes both
in the independent corpus and the broader installed API regression step.
The original public workload verifies 1,000 objects, 1,000 edges, 1,000 reads,
200 committed updates and values after connection reopen, counting 26,122 SQL
submissions on this Linux run. Other mandatory branch native regressions pass.

The receipt retains 46 original logs/JSON outputs losslessly and identifies the
three original binary artifacts. This is complete branch Linux qualification
for the recorded source/artifacts, not publication: the publish job is skipped
on that branch run. The diagnostic-trigger-only follow-up does not change the
runtime/test/recipe basis. Current2888 full macOS qualification also passes below;
the later tag Linux campaign and public-download verification are retained in [public release proof](evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json). Earlier failed runs
and source628/native35fd local receipts keep their original scopes.

### Current installed macOS ARM64 qualification — native manifest `288801f7…`

The [complete local receipt](evidence/design-audit/managed-grants-release-049-20261022/final-local-2888/qualification.json)
passes at source `19d7bbe5793e61e4034769a18b1d9a03b5c7e959` on Python3.11.17,
PostgreSQL18.6, psycopg3.3.6 and public Weft0.4.51 compiler source `55715373…` with the exact Mac
native cohort `34691932…`. It uses the same wheel `57fd9520…`, native manifest `288801f7…` and migration manifest `96addcdb…`
and HF archive `ae5726d7…` as the passing commit `4188141f` Linux campaign above. All 467
source/wheel/installed runtime files agree. All 1,206 input hashes, the pinned
clean UMF commit `5ba77cff` / Bun1.4.3 oracle and compiler/worker identities remain unchanged.

All eight steps exit with status0: module boundaries and 20 allowed/forbidden controls;
21 managed modules/130 tests; lifecycle; HF62; nine strict protected tests;
106 migration/recovery tests over four actual public source wheels; and the
original public workload. Selected test campaigns have zero skips, failures or
errors. Lifecycle checks preserve the original carrier through supported r2
additive evolution, contained SQLSTATE `0A000` unsupported-retirement refusal and later
selected ACL variation. The workload verifies 1,000 objects, 1,000 edges,
1,000 reads, 200 committed updates and values after connection reopen, with
26,122 SQL submissions. The original 10s SQL/30s operation limits are unchanged.

The [retained-file index](evidence/design-audit/managed-grants-release-049-20261022/final-local-2888/retained-files.json)
binds 53 original outputs retained losslessly. [Scoped cleanup](evidence/design-audit/managed-grants-release-049-20261022/final-local-2888/final-local-audit2888-1-cleanup-owned.json)
confirms no campaign-owned or newly created PostgreSQL process remains;
unrelated pre-existing servers were outside custody and unchanged. The
[retention statement](evidence/design-audit/managed-grants-release-049-20261022/final-local-2888/retention.json)
records that the exact branch wheel/sdist/archive containers are private or held
in GitHub artifacts subject to retention limits. Their hashes and payload
identities remain durable, distinct from the published identities in [public release proof](evidence/design-audit/managed-grants-release-049-20261022/published-0.0.49/receipt.json).
This earlier branch record did not claim publication. The later tag Linux and
public-download verification are retained in the proof; these selected platform
results make no full-engine, broad discovery, general p95 or actual Lakebase/Arras
acceptance claim.
