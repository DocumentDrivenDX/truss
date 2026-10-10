# Local runtime, installation and migration execution plan

## Updated goal and selected direction — 2026-10-09

Complete Truss's remaining governed design and execution-ready implementation/test
planning for an embeddable toolkit plus reference implementation, synchronized
with UMF and Weft. Additionally deliver a Truss-maintained tested embeddable
Python implementation, document-qualified catalog identity, explicit pre-effect
stale refusal without automatic retry loops, and host-supplied PostgreSQL connection
embedding. Truss owns installation and migration profile selection and ships a
pgserver-based default runtime that starts easily for local development/testing.
Shipped migrations are explicit and infrequent; ordinary UMF model revisions are
DDL-free. Pool provisioning/operation is the host's responsibility. These criteria
extend, rather than replace, the original 45-story scope and conformance obligations.

## Accelerated capability queue — owner direction 2026-10-09

Prioritize usable Python operations over additional standalone declaration checks,
site refinement or broad profile exploration. This sequence supersedes the older
delivery ordering below where that ordering placed a complete populated migration
before usable application operations. It preserves the full design/corpus scope
and mandatory native security, atomicity, origin and settlement requirements.

The following are provisional engineering estimates in elapsed weeks of focused
implementation from this reprioritization, assuming sustained ownership and timely
UMF/Weft/security integration. They are not measured delivery commitments. Reforecast
after the first integrated admission/security checkpoint; an unresolved native
mechanism or incompatible default server invalidates the estimates rather than
authorizing weaker guarantees. Do not count component tests as milestone completion.

| Priority / planning target | Usable deliverable and exit evidence |
| --- | --- |
| P0 / next three focused working days | Resolve the concrete original issuer/native-admission mechanism, required security-owner interface, corrected pgserver candidate compatibility and reproducible default delivery. Produce a coherent implementation decision and an actual integrated control/admission experiment, or identify the precise unavailable prerequisite and revise the forecast. Do not spend this checkpoint producing another interface-only receipt. |
| P1 / weeks1–3 | Package a complete fresh-install bundle and Python explicit install/verify entrypoints. Install on a disposable pgserver runtime, verify original inventory, initialize and publish readiness atomically; inject late failure and prove no ready installation. Include the mandatory native guard/finalizer bodies and security composition. Server startup remains DDL-free. |
| P2 / weeks4–6 | Ship a Python preview supporting catalog acceptance/install, atomic apply with preconditions and same-plan dry-run, atomic/per-item provenance import, direct key/edge reads and the complete consumer R8 read-shape implementation path, together with its versioned executable preview corpus/runner. Exercise one installed consumer model through actual accepted IDs/report, persisted values/keys/edges, journal and exact read results. Include R4 per-person isolation, R5 authenticated-versus-asserted origin and document qualification in the same installed path. Test denial/revocation, failure/rollback and large integers/decimals/absence/null. Unsupported shapes explicitly refuse. Required R8 shapes include indexed equality, relationship predicates, capped alias expansion, business-key paging and one-property grouped counts with exact Weft/native plans and finite bounds. This is a preview integration milestone; unsupported required shapes prevent R8/consumer-ready acceptance. Complete corpus/stable-layout/managed-target release remains separate. |
| P3 / weeks6–8 | Add complete feed transaction delivery/acknowledgement and durable request receipts with retry/idempotency and reached-position semantics. Exercise commit, lost response, explicit caller retry, no-op groups, restart and isolation on the same installation. Expand the published preview corpus/runner with these installed cases; clearly identify remaining full-corpus cases. |
| P4 / weeks8–12 | Qualify the complete release corpus and Python/TypeScript interchange; freeze the admitted layout/support tuple, package explicit populated migration/reconciliation and prove preservation plus fresh-process recovery. Qualify Aurora/Lakebase independently before advertising them. Publish stable artifacts only after these exits; candidate0.16 and a preview cannot be relabeled stable. |

P1 and P2 are one integration workstream, not independent packages waiting for a
general design-completion vote. Implement R4/R5 against the existing security
owner's exact required subset; do not wait for every unrelated security case or
fork authorization. Bring the reference consumer and runnable failure cases into
the first installation work, rather than adding a corpus after the implementation.
UMF continues to own model/DDL generation and Weft owns logical compilation.
Direct key/edge reads need not wait for every Weft query shape, but still require
their complete native authority, decoding and disclosure checks.

Keep migration status/verification and recipe packaging alongside P1; populated
apply/reconcile depends on a real coherent source/target and remains P4. This
staging does not omit the shipped migration system. Defer microsite enhancements,
additional language/platform profiles and performance polish until after P2,
unless a concrete preview acceptance case requires them. No deferred work is
removed from the full goal.

The README must continue stating that mutation/query/installation APIs are not
released until the corresponding installed public exports and preview corpus
actually pass. Current sixteen-module/61-test component evidence provides no
calendar or capability-completion evidence for these estimates.

### P0 native caller checkpoint: corrected binary required

The [caller-reset experiment](../../../scripts/check-pgserver-caller-reset.py)
now executes18 independently expected role/session observations on a disposable
pgserver0.1.4 PostgreSQL16.2 server. Its
[receipt](evidence/design-audit/pgserver-caller-reset.json) records three mismatches:
full transaction rollback loses the previously selected role; savepoint rollback
also loses it; subsequent outer rollback restores current_user but leaves
current_setting('role') at none. These are real native observations, not an
installed RLS/origin test. The fixture authenticates administratively to exercise
session authorization; it does not qualify an ordinary actor or nested definer.

[PostgreSQL's16.5 release notes](https://www.postgresql.org/docs/16/release-16-5.html)
describe this rollback defect, and the
[advisory](https://www.postgresql.org/support/security/CVE-2024-10978/)
requires correction from16.5 onward in that major. CONTRACT-005 already excludes
known incorrect reset behavior. Therefore the existing16.2 binary cannot qualify
the selected R4/R5 profile. Do not reset the host role after each call, substitute
asserted origin for authenticated identity, or disable per-person isolation.

The immediate implementation queue now includes a reproducibly built corrected
PostgreSQL distribution inside the pgserver runtime packaging, with exact original
source/build/binary/dependency pins and platform loader evidence. The installed
pgserver0.1.4 candidate resolves commands from its packaged pginstall directory;
an ambient system binary or monkeypatched executable path is not a shipped fix.
Preserve existing16.2 evidence as historical component scope. Run the same reset
experiment plus the full prepared/unprepared, role/reset/rollback, non-superuser
definer, RLS and current-authority schedules on the corrected tuple before adoption.
Updating a patch number alone does not qualify the complete profile.

The provisional P1–P4 estimates are conditional on this corrected-binary work;
P0 has identified a concrete prerequisite, not completed native admission/security
integration. Corrected packaging is Truss-owned work and can proceed without a
new product decision or completion of every security-owner case.

The [corrected build inputs](evidence/design-audit/pgserver-corrected-build-inputs.json)
pin pgserver upstream3b227607 and the official PostgreSQL16.15 source archive,
including its independently fetched published SHA256. A disposable native build
has started using the upstream source-only postgres target, with explicit
--without-readline/--without-icu configuration. It does not include pgvector;
that is an explicit candidate distribution difference, not an inferred Truss
extension requirement or an identical upstream wheel. The planned local version
0.1.4+truss.pg16.15 distinguishes Truss's candidate package from published0.1.4.
These are build inputs, not build success or a shipped dependency change. Do not
alter the default package pin until installed wheel/native checks qualify it.

After that original native build completes, use
`scripts/package-corrected-pgserver.py SOURCE_CHECKOUT NEW_WHEEL_DIRECTORY` from
the pinned wheel-build environment. The packager verifies source/archive/recipe
pins and allowed tracked changes, emits the distinguished local version without
publishing it, and compares packaged pgserver payloads with the original build
directory. Its output receipt still declares installed/full-runtime qualification
false. Install into a separate environment, then run
`scripts/check-pgserver-caller-reset.py --receipt pgserver-corrected-caller-reset.json --require-matches`
so corrected observations cannot overwrite the historical16.2 failure receipt.
Only after this succeeds continue the full R4/R5 matrix and local lifecycle/loader
qualification; a packaging command or source parse is not those exits.

The first corrected build and private wheel now complete. The
[installed payload receipt](evidence/design-audit/pgserver-corrected-installed-wheel.json)
records0.1.4+truss.pg16.15, wheel SHA256
706ab843c9e8d8613a2a6cde6cf8156d8b83fa1921237e883c0aa878cfac88d9,
and1,620 installed/wheel/build-directory payload correspondences. The wheel is
cp311-cp311-macosx_27_0_arm64, so no older macOS, other Python or platform claim
follows. It is a local build artifact, not a published or adopted dependency.
The original build-input record's pending fields describe its earlier checkpoint.

The [corrected reset receipt](evidence/design-audit/pgserver-corrected-caller-reset.json)
now records actual PostgreSQL16.15 and all18 expected observations matching,
including the three rollback cases that failed on16.2. This resolves that
reproduced binary defect for this installed candidate. It does not qualify the
complete R4 isolation/R5 origin paths, native issuer, default LocalPostgres wrapper
or public application operations. Continue full security/role/prepared/lifecycle
qualification and deliberate packaging/profile adoption before changing the
default0.1.4/16.2 component pin.

The [corrected isolation experiment](../../../scripts/check-corrected-pgserver-isolation.py)
now passes the original historical0.2 storage/module-isolation/check sources on
that installed16.15 candidate. Five additional independent observations run a
SECURITY DEFINER function owned by the non-superuser shared-reader role: unprepared
writer-a/writer-b calls and one prepared statement reused under writer-a,
writer-b and an ungranted caller. Returned exact object-ID arrays match
[101,102,104], [103], [101,102,104], [103] and [], respectively, while the
effective function owner remains iso_ra. The
[receipt](evidence/design-audit/pgserver-corrected-isolation.json) retains full
fixture SQL, original source hashes and independent expected/actual rows. All
fixture DDL/data/roles roll back, and namespace absence is checked afterward.

This adds actual nested-definer/prepared policy observations to P0; it does not
install isolation on0.16, authenticate a public Python request, validate origin
capture/journal correspondence or qualify current revocation/publication. The
historical0.2 storage and grants cannot enter the new installation bundle as an
implicit substitute. Continue the current original security composition and
local runtime lifecycle/package integration rather than relabeling these passes
as R4/R5 completion.

LocalPostgres now recognizes exact package/server pairs0.1.4/16.2 and the explicit
candidate0.1.4+truss.pg16.15/16.15. RuntimeInfo records the actual package version;
unknown packages or mismatched native versions refuse. The
[corrected installed-suite receipt](evidence/design-audit/python-corrected-runtime-installed-suite.json)
passes all42 component tests with12 installed modules on macOS27 arm64/Python3.11,
including the four native lifecycle tests and synthetic constructor-fault control.
The same rebuilt Truss wheel also passes42 tests on the original published tuple
in the separately retained
[default component receipt](evidence/design-audit/python-current-installed-suite.json).
The environments were reused/prepared earlier; these are not new clean-resolution
claims. Corrected CLI signal checks remain outstanding. No default dependency,
complete Truss installer or R4/R5 readiness is published by this lifecycle change.

The [corrected CLI signal receipt](evidence/design-audit/python-corrected-runtime-cli-signals.json)
now verifies actual installed command startup, SIGTERM and SIGINT shutdown,
absent postmaster markers and retained-directory restart on16.15. Each signal
targets only the probe's original child PID. Reproduce with
`scripts/check-python-installed-cli-signals.py --corrected-pgserver` in the
installed candidate environment; its separate output preserves historical16.2
signal evidence. This closes the graceful corrected CLI component check, not
process-crash/forced-kill recovery or complete installation.

Read-only coordination observed the security workstream actively addressing
captured-versus-current native physical-profile correspondence for installer
admission. Keep that exact source/interface work with its existing owner; do not
copy its in-progress implementation or infer complete readiness. Truss's original
operation issuer/native-admission integration remains the next owned engineering
task after this corrected-runtime component work.

## Ownership and profile selection

Truss owns the Python package in this repository, installation bundles, migration
recipes, verification and recovery composition. UMF owns schema interpretation and
generic DDL generation; Weft owns logical SQL lowering; the existing security
workstream owns authorization and publication protocols. Source pins, finite driver
bounds and security admission remain explicit engineering outputs, not new product
votes. The source-epoch0.16 plus configuration/migration adjuncts are composition
inputs, not a claim of one complete installed bundle.

Select pgserver 0.1.4 as the first local runtime candidate with Python3.11. Pin
actual wheel/platform/dependency and bundled PostgreSQL version before support.
Its upstream README advertises PostgreSQL16.2; existing Truss17.9 evidence cannot
qualify that server. Audit SQL/catalog/xid/status dependencies against the actual
binary. Implement compatibility where possible and explicitly refuse an unsupported
complete installation; do not silently switch to Docker or system PostgreSQL.
An external PostgreSQL connection remains a supported embedding route under its
own qualified version/profile. Aurora and Lakebase retain independent obligations.

## Delivery sequence

The [local deadline handoff](local-deadline-installation-handoff.md) fixes
admission/cancellation/containment/COMMIT/recovery responsibilities. Its original
16.2 observations remain historical; that binary cannot qualify the selected
R4/R5 profile. Use the corrected 16.15 candidate for the next integrated experiment,
with its exact package/native tuple and independently admitted deadline mechanism.
The private corrected wheel is not yet a shipped default. Native transaction
termination and the host's deadline remain separate facts; original producer
qualification is required before complete readiness.

### Current integration priority

The security workstream's same-endpoint occurrence finding is independently
reproduced against original source-epoch0.16 on pgserver PostgreSQL16.2 in
[the native edge profile receipt](evidence/design-audit/pgserver-edge-occurrence-profile.json).
Unique `edge_out` rejects a second edge ID with the same source/relationship/target
tuple (SQLSTATE23505), preserving the first edge's properties. Other relationship
and target tuples remain distinct. The fixture satisfies native constraints but
does not establish admitted UMF/catalog/security semantics. Keep parallel-occurrence
support unavailable for this profile; do not deduplicate consumer records, drop
the index, or adopt unfinished security APIs to make the support report pass.
STP-040 PQ-01 retains its full gate with that limitation explicit. Complete
installer/profile verification must include this native uniqueness meaning.

The next deliverable is a complete installation composition, not another isolated
storage check. Existing native declaration, receipt boundary and lifecycle evidence
remain component evidence only. Work through these dependencies in order:

1. Correct all four operation-admission families against the original executor
   issuer. Savepoint rollback must never make an already consumed ordinal reusable.
   Bind issuer authority and uncertain driver outcomes through the existing
   [issuer handoff](operation-ordinal-issuer-handoff.md); caller-supplied ordinals
   cannot stand in for that authority.
2. Implement the five missing canonical trigger bodies and two scope validators
   against that issuer and the security owner's admitted authorization context.
   Exercise populated effects, savepoint rollback and failed finalization before
   treating their presence as installation readiness.
3. Compose generated storage with those routines, original grants, initialization,
   archive and complete inventory verification. Publish readiness only after the
   complete bundle verifies atomically on the selected PostgreSQL version.
4. In P1, package actual installation inputs and implement Python explicit fresh
   install, status/verify and bootstrap reconciliation against that composition.
   Apply the reference configuration and diagnostic contracts at this boundary;
   check Python module ownership and the specified settlement invariants. Native
   failure/unknown-outcome evidence remains required in addition to these checks.
5. Proceed to P2/P3 consumer operations and durable retry/feed qualification on the
   same installation. In P4, select the populated M1 route from coherent admitted
   source/target bundles, then implement migration apply/reconcile and M2–M5
   preservation/recovery. Full populated migration qualification is a release gate,
   not a prerequisite for fresh installation or the preview operations.

The security owner's grants and publication work is a composition dependency;
it does not require a second authorization implementation. Weft's PostgreSQL17.9
fixture qualification does not qualify the pgserver PostgreSQL16.2 default. Keep
that compiler/profile qualification explicit alongside installation integration.
These are engineering deliverables, not pending product votes or a reason to
pause independent Python and installation work.

1. Implement local server lifecycle: explicit start with caller-selected data
   directory, connection information, readiness, signal-safe stop and persistent
   restart. Fresh temporary fixtures are isolated. Server startup alone performs
   no Truss upgrade. No global process termination or unrelated data deletion.
2. Compose one complete UMF-generated installation bundle: storage, report/history,
   configuration/receipt homes, routines, grants, dependencies, initialization and
   verifier inputs. Choose exact symbolic definitions now; inspect actual native
   identifiers only after installation. Installer owns a dedicated administrative
   transaction and runs target/parity checks before publication. Existing ordinary
   or incompatible data is never mistaken for a fresh installation.
3. Implement Python host entrypoints against caller connections and transactions,
   shared protected PostgreSQL operations and Rust Weft. Expose exact carriers,
   whole atomic network batches, complete durable retry receipts and current-person
   authorization. No TypeScript service or second Python SQL compiler is required.
4. Select one complete populated migration source/target route using the same
   installation composition. Preserve object/key/edge IDs, values, reports, journal,
   retry receipts, epochs/feed positions and unresolved attempt custody. Implement
   M2–M5 from the existing migration handoff; administrative recovery does not
   repeat uncertain recipes. Startup reports incompatibility rather than migrating.
5. Qualify clean Python distribution and TypeScript/Python interchange, then each
   advertised managed target. Retain independent expected data and complete effects;
   a local server smoke or development wheel is not a complete Truss runtime.

## Independent acceptance scenarios

- Fresh local start needs no separately provisioned PostgreSQL or Docker; observe
  actual server version and successful native query. Stop and restart the same
  directory preserves committed data; concurrent isolated directories do not collide.
- Missing/incompatible local binaries refuse with actionable dependency/version
  information; no fallback changes the selected profile without disclosure.
- Fresh installation verifies complete original generated/native inventory; late
  failure leaves no published installation. Opening an existing installation is
  read-only until explicit deployment, and ordinary model acceptance adds no DDL.
- A host connection retains ownership: Truss neither closes it nor commits a caller
  transaction. Failed/unknown containment retains original custody; no pool manager
  or hidden connection substitution is introduced.
- Deterministic stale pre-effect admission returns the original refusal once, with
  no mutation/journal/report effects or automatic second submission. Caller retry
  is a new explicitly requested admission under existing request idempotency rules.
- Same module/element names in two documents remain distinct through acceptance,
  native grants, compiler binding, keys and output. Document identity is retained.
- Populated explicit migration passes independently expected preservation, late
  rollback, lost acknowledgement and fresh-process reconcile cases. Clean installed
  packages contain every registered recipe/profile/verification input.
- Complete required Python corpus and bidirectional committed interchange run on
  the exact local profile; known unsupported behavior never becomes a skipped pass.

## Traversal clarification

The earlier question concerned whether a separate multi-hop direct-read API returns
unique terminal entities or path records. The owner did not select either and asked
for its rationale. Review actual consumer uses before proposing that extra API;
compiled SQL relationship predicates keep Weft's original semantics. This isolated
read-surface question does not block local runtime, installation or Python delivery.

## Goal control

The user resumed the goal with the expanded criteria above; the next goal read
confirms status active. The stored original objective text remains unchanged
because the available tools cannot edit it; this plan retains the additional
criteria as governing user instructions. No old pending product decision or
control-plane limitation is a reason to stop installation/migration work.

## Initial runnable developer path

```sh
python3.11 -m venv .venv
.venv/bin/pip install './packages/python[local]'
.venv/bin/python scripts/local-postgres.py --data-dir .local/truss-postgres
```

The launcher emits local connection information and remains alive until SIGINT or
SIGTERM. `--probe` verifies readiness then stops; cleanup mode is `stop`, retaining
data. The launcher uses argv-based bundled psql execution with ON_ERROR_STOP and
an explicit readiness timeout. It neither installs Truss nor upgrades an existing
layout. This is the first executable development component; package-level public
runtime embedding and complete installation follow the delivery sequence above.

Actual initial macOS arm64/Python3.11 probe observed pgserver0.1.4 and PostgreSQL16.2.
Full Truss SQL compatibility and installer qualification remain required on that
exact server; retained17.9 evidence is separate.

## PostgreSQL16.2 installation frontier

The rollback-only [generated-layout probe](../../../scripts/check-pgserver-layout.py)
executes original source-epoch0.16 owner-export bytes without schema rewriting.
The [native component receipt](evidence/design-audit/pgserver-generated-layout-component.json)
confirms all 48 declared table names, including the partitioned journal, and
namespace removal after rollback. Native sha256, xid-status, current-xid and UUID
issuance functions resolve. This establishes DDL admission and a narrow native
prerequisite set, not complete constraints/grants/routines, initializer publication,
accepted catalog or migration qualification. Configuration and migration-receipt
adjuncts still require their complete generated/native composition.

Select a separate local16.2 session-observation profile instead of relabeling the
PostgreSQL17 reference profile. Capture transaction_timeout as unavailable; it
cannot be silently omitted or installed by a setting alias. Local operations use
finite Truss-controlled work/copy limits and bounded per-statement/lock admission;
statement_timeout and lock_timeout do not establish a whole-transaction lifetime
cap. Any capability requiring an unavoidable whole-native-transaction timeout
remains unsupported on this tuple until a separately qualified mechanism exists.
Original driver cancellation/termination and quarantine/recovery remain required;
a client deadline cannot certify stopped native work or safe connection reuse.
Do not downgrade the supplied-connection correctness or no-loss retry contract.

Next native installation work must compose the same48-table source with original
configuration/receipt adjuncts, routines and security-owned grants, then independently
compare complete objects/columns/FKs/constraints/defaults/functions/rights and
initializer effects. A CREATE success or equal table count cannot substitute for
that complete inventory. The first populated migration route uses those same
admitted inventories and preservation expectations, not these review version labels
as release versions. PostgreSQL17.9 and managed-service evidence remain separate.

## Exact local adjunct composition

The [composed probe](../../../scripts/check-pgserver-adjuncts.py) now runs original
base and both UMF-generated adjunct exports plus their immutable guard SQL in one
rollback-only PostgreSQL16.2 transaction. Its [receipt](evidence/design-audit/pgserver-composed-adjunct-component.json)
pins all five sources. All50 declared native table names are present; independent
adjunct expectations verify configuration16columns/2FKs/3generated hashes and
migration receipt11columns/1FK/3generated hashes. Each has two ALWAYS guards and
no PUBLIC INSERT privilege. Both TRUNCATE operations refuse with SQLSTATE55000
in origin and replica mode (four controls), and rollback removes the namespace.

This closes the isolated dependency-order and local native guard-admission question
for these exact components. It does not prove UPDATE/DELETE refusal on populated
original capsules, full column/constraint/routine/grant parity, protected insertion,
initializer/epoch publication or complete migration execution. Existing historical
component tests keep their original tuple; this new local result is not borrowed
managed-service or installed-engine evidence. The composed sources remain review
candidates; release versioning and one complete bundle still require the remaining
routines, original security procedures and independent full preservation profile.

## UMF core structural-to-native correspondence

The [structural checker](../../../scripts/check-pgserver-umf-structure.py) compares
actual local catalogs with the same core0.6 projection used by the schema browser,
not a manually repeated table/column list. Its [receipt](evidence/design-audit/pgserver-umf-structural-correspondence.json)
pins the complete model, generated sources and original guard bodies. On
PostgreSQL16.2, all50 Records and481 ordered column definitions match native
column names, built-in type identity, requiredness and declared array dimensions.
All67 ordered physical foreign-key tuples match with duplicate multiplicity
preserved; targets are in the original truss schema and types in pg_catalog.

The comparison consumes core Record/Field membership and the model's relationship
field correspondence. Seven xid8-related associations retain physical descriptors
rather than claiming portable core Key equality; native correspondence does not
promote them to a supported portable equality profile. Schema-browser visuals and
this native read retain that same meaning boundary.

Type modifiers, collations, defaults/check expressions, FK actions/deferrability,
complete indexes, routines and effective grants remain unverified by this checker.
Keep those as explicit next inventory outputs, rather than calling the whole
installation verified from structural agreement. The immutable adjunct controls
and rollback proof still run in the same actual transaction. No Truss installer
publication, initialized epoch or populated migration is claimed.

## FK action and deferral descriptor comparison

The structural checker now compares all67 native FK match/update/delete action
codes, deferrability, initial deferral and validation state against the retained
UMF native descriptors, in addition to ordered endpoint columns. The same local
rollback-only receipt has been refreshed at this extended scope. Original source
bytes are unchanged; no native fact is used to rewrite its expected descriptor.

One inline seed-artifact FK demonstrated why an individual Constraint node is
insufficient: the Field retains separate CONSTR_ATTR_DEFERRABLE and
CONSTR_ATTR_DEFERRED nodes following its original FK node. The scoped checker
requires exact node/pointer correspondence and includes those original attributes,
following PostgreSQL16 [transformConstraintAttrs](https://github.com/postgres/postgres/blob/REL_16_STABLE/src/backend/parser/parse_utilcmd.c).
It refuses ambiguous/misplaced correspondence rather than treating every omitted
flag as false. This inventory comparison is not a new portable UMF relationship
interpreter or generic SQL validator. The initial failed check exposed incomplete
probe interpretation, not lost source meaning or incompatible generated DDL.

Defaults/check expressions, type modifiers, collations, indexes and complete
routine/effective-grant inventory remain the next installation parity work. The
raw physical descriptor comparison cannot qualify logical lifecycle semantics,
protected producer authority or a populated migration route by itself.

## Column modifier and collation identity comparison

The same local structural probe now compares all481 column type modifiers and
qualified native collation identities, including86 explicit collation declarations
and four character(1) declarations. Expected modifiers come from retained native
AST literals under the selected bpchar profile; PostgreSQL16
[anychar_typmodin](https://github.com/postgres/postgres/blob/REL_16_STABLE/src/backend/utils/adt/varchar.c)
accounts for the varlena header. No expected value is copied from the installed
catalog. Other modifier profiles refuse until explicitly admitted.

For retained unqualified C declarations, this fresh-cluster probe admits only
pg_catalog.C. It does not provide arbitrary host-schema collation resolution or
allow same-name substitutions. Unspecified text/character collation is compared
with pg_catalog.default under this local tuple; noncollatable columns remain
uncollated. Provider implementation/version, locale behavior and complete host
lookup/session custody remain separately unverified. Qualifying names does not
prove all equality/order behavior or permit reusing this profile after database
collation configuration changes.

The refreshed receipt retains complete actual column observations and original
source pins. Remaining parity work is default/generated/check expression meaning,
index/sequence/routine/trigger inventory and effective ordinary-role grants, plus
complete initialization and published installation custody. Local native execution
continues to roll back all review DDL and establishes no installed release.

## Native declarations for remaining installation checks

The [declaration capture](../../../scripts/capture-pgserver-native-objects.ts) uses
UMF's existing PostgreSQL node API to retain original native definitions from all
three storage models. Its [artifact](evidence/design-audit/pgserver-native-object-declarations.json)
pins model bytes and the three imported UMF entrypoint files. It captures 25 explicit
index declarations and 12 sequence declarations, including exact integer option
tokens and original predicates. This is an input to the next native comparison,
not native verification, complete dependency pinning or inventory closure. Implicit
constraint indexes, defaults/check expressions, routine bodies, grants and
initializer publication remain separate required checks. UMF continues to own SQL
generation; this capture introduces no alternative SQL compiler.

## Local native sequence correspondence

The structural checker now consumes the captured original UMF sequence nodes and
refuses stale model hashes or options outside its admitted ascending-int8 subset.
It compares every truss sequence with actual pg_sequence metadata: type, increment,
minimum, maximum, start, cache and cycle. Native integers are transported as text;
original large Float AST tokens are parsed as exact Python integers, never binary
floats or JavaScript numbers. Defaults follow the
[PostgreSQL16 CREATE SEQUENCE contract](https://www.postgresql.org/docs/16/sql-createsequence.html).

All12 declarations match the fresh PostgreSQL16.2 composition, including the exact
9223372036854775807 maximum. The updated structural receipt retains actual native
values and the declaration-capture hash alongside the original source pins. The
same50-table/481-column/67-FK and four guard-refusal checks pass; rollback removes
the namespace. Sequence ownership dependencies, privileges, runtime allocation,
crash recovery and migration state preservation are not qualified by configuration
parity. Explicit/implicit indexes, defaults/check expressions and complete
routines/grants/initializer publication remain required installation work.

## Explicit native index structure

The structural checker additionally compares all25 original IndexStmt declarations
against installed pg_index/pg_class metadata. It verifies owning table, btree
method, uniqueness, null-distinctness, ordered key positions, included column order,
default ascending/null ordering, partial-index presence, validity and readiness.
It refuses unadmitted explicit operator classes, collations or ordering modifiers.
All25 match on the exact PostgreSQL16.2 composition. The receipt retains the full
native index inventory, including additional indexes it does not yet qualify.

For journal_request the expression occupies its expected key position, but a null
attribute number only establishes expression presence. This check does not establish
expression or predicate meaning. Implicit primary/unique constraint index
correspondence, index dependency identities, operator-class/collation semantics,
default/check expressions, routines, grants and initializer publication remain
required before full installation qualification.

## Primary and unique constraint correspondence

The capture now also retains original CreateStmt and AlterTableStmt nodes. The
checker derives final primary/unique key tuples from those original declarations,
including three added unique keys and the explicit replacement of
prop_def_type_id_element_key with its document/module-qualified field constraint.
It refuses an unrecognized key-constraint removal rather than guessing a final
layout. This is a scoped inventory projection, not a general DDL interpreter.

All64 final primary/unique constraints match native ordered columns, deferral
settings and null-distinctness, with unique, valid, ready backing indexes whose
ordered columns match the constraint. Duplicate multiplicity is preserved. The
first run deliberately failed on the unreconciled CREATE-only inventory; the
original ALTER declarations resolved the discrepancy without changing model or SQL.
Constraint names, backing-index operator classes/collations and dependency identities,
check/default and index expression meaning, complete routines/grants and initializer
publication remain unqualified. Complete migration preservation remains separate.

## Embeddable Python local lifecycle component

The experimental truss-toolkit package now exposes LocalPostgres and immutable
RuntimeInfo. Its context supplies a connection URI to the host driver, owns only
its local server, stops on normal/exception exit, retains committed data, and
requires a new context for restart. It installs no Truss objects and upgrades
nothing. The existing launcher consumes this same package API. Runtime requirements
are optional so external-connection consumers need not install bundled PostgreSQL.

Process-local plus nonblocking interprocess directory leases refuse overlapping
contexts once, with no automatic retry. Existing postmaster custody is refused
rather than taken over. Nonempty foreign directories and PostgreSQL major-version
mismatches remain unchanged on refusal. Qualification is scoped to macOS arm64,
Python3.11, pgserver0.1.4 and bundled PostgreSQL16.2. The full Python protected
engine and installation/migration APIs remain unfinished.

The [installed-wheel receipt](evidence/design-audit/python-local-runtime-wheel-component.json)
pins the built wheel and sources. Three native tests pass outside the checkout
using a separate wheel installation target, including cross-process refusal,
concurrent isolated servers, exact-text committed persistence and exception cleanup.
The installed-wheel launcher readiness/stop probe passes as well. Dependencies were
reused from the pinned qualification environment; clean dependency resolution and
other operating systems remain separate qualification work.

The [Python migration handoff](python-migration-installation-handoff.md) selects
package/API composition, original artifact custody, dedicated administrative
transaction rules, complete outcome mapping and implementation order under the
existing migration binding. It introduces no alternative ledger, SQL generator
or authorization resolver. It remains an implementation handoff; migration
status/verify/apply/reconcile and the complete populated M1 route are unfinished.

### Cleanup custody correction

LocalPostgres originally released its directory lease in a finally block even when
owned cleanup failed. It now invalidates connection information immediately and
retains the server handle plus both leases on raised cleanup failure or a remaining
postmaster marker. A later close is an explicit host recovery action; no automatic
retry loop is introduced. Failure injection against an actual running server
checks thrown cleanup, cleanup returning without stopping, continued overlapping
context refusal, and successful explicit cleanup/restart after removing the fault.
These controls qualify the wrapper's custody response, not every native shutdown
or startup-constructor failure. Complete driver/native outcome settlement and
process-crash recovery remain required for the installed engine/migration profile.

## Python exact-value component packaging

The existing numeric/timestamp candidate converters are now packaged as
truss.numeric and truss.timestamp, with the same independently authored shared
exact-value vectors. They require already admitted original text and a finite
caller-selected byte bound. Python int/Decimal construction retains original
spelling without float conversion or ambient Decimal rounding. Bool/float host
integers and nonfinite Decimal views refuse. Timestamp conversion retains the
token when precision, offset or Python's date range prevents a lossless datetime
view. It does not classify unavailable host conversion as invalid UMF content.

This packages host views, not UMF grammar/facet admission, a storage codec, key
normalization, decimal arithmetic or native-domain qualification. The committed
UMF JavaScript numeric owner API remains the source for TypeScript number/bigint/
decimalToken behavior; Python does not introduce a competing primitive. Original
candidate files and historical evidence remain unchanged.

The [exact-host-view wheel receipt](evidence/design-audit/python-exact-host-views-wheel-component.json)
pins the expanded distribution, unchanged original candidates, shared vectors and
committed owner numeric source review. All nine installed-wheel tests pass from
outside the checkout: five exact host-view checks plus four native local lifecycle
checks. Dependencies are reused; native exact-value round trips and complete
committed TypeScript/Python engine interchange remain separate obligations.

## Populated local immutable guards

The [populated checker](../../../scripts/check-pgserver-populated-guards.py) composes
the same five original generated/native inputs with an explicit administrative
fixture. It inserts the marker, source epoch and actual-xid operation dependencies
under origin-mode FK enforcement, then inserts configuration and migration-receipt
rows. These are test fixtures, not admitted original protected artifacts or a
ready installation. No constraint or trigger is disabled to prepare them.

All12 UPDATE/DELETE/TRUNCATE controls (two tables, two replication modes) refuse
with55000 and preserve the complete row after each refusal. Independently expected
original text and all six generated SHA-256 values match after those controls;
the migration row receives its expected sequence default. Rollback removes the
namespace. The [receipt](evidence/design-audit/pgserver-populated-guard-component.json)
pins every source and the producer. This extends the earlier empty-table TRUNCATE
evidence to populated native row guards and selected generated defaults.

Protected capsule/receipt production, ordinary-role authorization, complete
retention/cleanup lifecycle, semantic default/check/index correspondence, full
routine/grant inventory, initialization publication and migration execution remain
unqualified. This check must not publish or substitute for an installation marker.

The [updated installation gap matrix](../02-design/contracts/weft-review-installation-gap-matrix.proposal.md#current-local-installation-frontier--source-epoch016-plus-adjuncts)
now distinguishes verified local storage/immutable components from missing
canonical observers, ordinary scope validators, qualified authority and original
ready-publication composition. A current-model trigger scan confirms the five
missing handler bodies; it preserves the historical0.6 receipt rather than
relabeling that older source evidence. The next complete-bundle work follows
original operation dependencies → handlers/validators → independent full native
parity → initializer/publication, while retaining all other release obligations.

## Operation issuer dependency before canonical guards

The [issuer handoff](operation-ordinal-issuer-handoff.md) records a reproduced
OC01 conflict in the existing private admission allocator: savepoint rollback
reissues ordinal0 in the same native transaction. The other three admission
context families share the inspected MAX-over-surviving-rows source expression.
The original executor issuer must replace that derivation before these candidates
can support canonical observers or installer readiness. The native receipt marks
contractConformant=false; it does not relabel gap reproduction as qualification.
Correct all families against the same original issuer/driver/security port, retain
original context fields and verify nonreuse under actual rollback/unknown outcomes.

The original ordinal counter dependency now has private Python/TypeScript
components checked against the same six expected event sequences. Exact bounded
issuance never rewinds and closes on unknown/cancelled/ended custody. This is a
component implementation, not a native issuer permit or a correction of the four
old native allocators. Adapter transaction recognition, original account/control
reservations, savepoint proof and native issuer verification remain required.

The Python original control-frame seam now has fresh local16.2 evidence for five
fixed savepoint/transaction controls, reusing the existing pinned instance receiver.
All ten expected command/ready frames match; original issuer/account/unknown-outcome
qualification remains false. See the issuer handoff for the exact integration
boundary. This does not replace the full driver or native admission profile.

The Python driver failure seam now independently demonstrates that a handler
exception after SAVEPOINT CommandComplete leaves the backend pending. Quarantine
prevents a new send; explicit socket close is followed by separately observed
backend termination and rollback of the earlier pending fixture write. This closes
one concrete callback-failure behavior, not full control/COMMIT recovery or driver
account qualification. Preserve those separate outcomes in the original issuer
integration rather than classifying all client exceptions as rollback.

## Weft qualification for the default local engine

Source inspection at Weft commit
`f05f2df09e9c2494ac8c6d703dfe38413dbc4181` establishes a concrete integration
boundary. `crates/weft-postgresql/src/native_profile.rs` pins engineVersion17.9,
UTF8 client/server encodings, standard_conforming_strings=on, repeatable-read,
C locale/comparison and exact-or-error arithmetic. Its registered layout is
`weft-truss-fixtures/0.1`. `qualified_profile.rs` inherits these requirements in
`pg17.9-qualified-fixtures`; it changes qualification metadata, not the engine
or layout contract. That fixture evidence cannot qualify pgserver's observed16.2
or the composed Truss source-epoch0.16 layout.

The host must refuse an incompatible executing engine/profile before integrity
or user SQL. No fallback, profile relabeling or automatic retry is permitted.
This is a source-confirmed obligation mismatch, not a new executed compiler
refusal test. Existing local storage/control probes remain useful component
work; they do not satisfy compiler execution obligations.

The next integration packet must provide the Weft owner the exact local engine
and observed session settings, original versioned layout/model hashes, admitted
catalog/publication identity, document-qualified mappings and complete storage
home, value, key, presence/null, relationship and comparison semantics. Weft owns
registration and SQL lowering. Truss owns host verification, integrity and
authorization checks, decoder use and buffered publication in the same admitted
read context. Add a separately registered16.2 profile only with independent
native compiler/decoder qualification for its explicit domains. Keep17.9 and
managed-service evidence separate. A local16.2 registration alone would not
qualify the complete installation or the consumer's entire query corpus.

Upstream synchronization on2026-10-09 also found UMF commit
`8e76c74d14203225d1ef159c9132bb9e9b0cdffe` adding an explicit CSV Boolean
lexical source profile. Its JavaScript numeric adapter and schema-browser
JavaScript asset are unchanged from the preceding tracked commit. This does not
require adopting CSV ingestion into this installation slice. The security owner's
assertion-inventory composition remains in progress; use its finalized original
interfaces and evidence rather than substituting local security authority.

Fetched Weft now advances to `1a1c0ad2c26d0cdd7aa6fb7f415abbaa44ab2842`.
The [committed0.3 source review](evidence/design-audit/weft-v03-committed-source-review.json)
finds new explicit arithmetic/positional-output semantics but unchanged original
PostgreSQL native/qualified17.9 profile bytes. The local16.2 qualification task
above remains unchanged. Retain closed version/obligation admission and do not
adopt Databricks registrations as Lakebase/PostgreSQL execution evidence.

The subsequent [loader/native-null source review](evidence/design-audit/upstream-loader-null-source-review.json)
advances reviewed UMF to72996e58 and Weft to1a8a344. UMF's portable loader
contract primitives and Bun acquisition companion do not own Truss installation
or PostgreSQL migration. Acquisition retry/publication receipts cannot substitute
for Truss exact transaction retry receipts or native commit evidence. Its numeric
adapter is unchanged; current original browser assets match byte-for-byte and
Truss browser provenance now names that latest reviewed commit.

Weft's new0.3 native-null encoding is explicit Ashlar/Spark opt-in: present null
and present values have distinct tagged outputs, but source-valid absent optional
properties refuse that backend representation. Preserve Truss's complete logical
absence/null/empty/exact-value contract during later adoption; do not collapse
absence into null or reinterpret an ideal nonnullable descriptor as availability.
The PostgreSQL native/qualified17.9 source files remain unchanged. Current Python
and TypeScript compiler boundaries stay at the frozen f05f2df0.2 component; the
local16.2 and full installed-profile gates remain open.

## Native default declaration correspondence

The [default component receipt](evidence/design-audit/pgserver-default-declaration-component.json)
now compares all41 original CREATE/ALTER ADD ColumnDef defaults with fresh
PostgreSQL16.2 pg_attrdef/pg_get_expr observations on the same composed three-model
layout. Expected forms derive from the retained original native AST capture,
including exact literals, JSONB empty objects, original qualified sequence homes
and selected built-in clock/xid calls. Unsupported AST forms refuse. Native
stored-generated expressions share pg_attrdef but are explicitly excluded from
this ordinary-default inventory; they remain a separate verification obligation.

All41 declaration correspondences match, and outer rollback removes the namespace.
The script is a scoped installation assessor, not an alternative UMF DDL generator.
Source/model/capture/producer hashes and complete expected/observed inventories
are retained. This proves native declaration/deparse correspondence only. Actual
default execution, clock and sequence semantics, callable permissions/dependencies,
stored-generation meaning and full routines/grants/init/publication remain
unqualified. No installation-ready marker is issued.

The separate [stored-generated declaration receipt](evidence/design-audit/pgserver-generated-declaration-component.json)
now compares all29 digest columns with the original CREATE/ALTER ADD native AST:
exact source byte-column operand, sha256 expression and actual stored-generation
mode. Both originally qualified and unqualified builtin call forms are retained
in the source capture; observed native deparse/storage tuples match on fresh16.2.
The complete expected/observed inventory and source/capture/producer hashes are
retained, and rollback removes the namespace. This is declaration correspondence,
not populated generated-value evaluation, callable permission/dependency closure,
protected write-path enforcement or complete installer readiness. Hash routing
still requires full original byte equality; no digest becomes identity authority.

The generated-column assessor additionally verifies actual cached expression
function OIDs against the exact native `pg_catalog.sha256(bytea)` regprocedure.
All29 native expression trees contain exactly that one callable; source-qualified
and source-unqualified calls resolve to the same builtin on this16.2 composition.
The receipt retains the builtin OID and every original pg_node_tree observation.
This closes scoped callable-identity correspondence, not grants, argument dependency
closure or populated enforcement. The internal node-text extraction is explicitly
16.2-scoped and must be requalified for another server build rather than advertised
as a portable PostgreSQL AST API. All earlier generated-column limitations remain.

The [populated receipt digest receipt](evidence/design-audit/pgserver-receipt-digest-component.json)
now supplies five additional FK-valid administrative fixtures covering NUL/FF
bytes, all256 byte values, distinct composed/decomposed Unicode spellings and
exact-looking numeric JSON text with CRLF. All retained request/receipt/attempt
bytes and15 generated SHA-256 values match independently computed Python
expectations. Explicitly supplying a generated digest refuses with SQLSTATE428C9
and leaves the six fixture rows unchanged in count. Outer rollback removes the
namespace. These binary fixtures qualify storage behavior only; they are not
admitted migration request/receipt encodings or protected original producers.
Other generated homes, full byte collision processing, grants/current-person
authority and complete installer/migration execution remain unqualified.

The [migration receipt boundary receipt](evidence/design-audit/pgserver-receipt-boundary-component.json)
now verifies seven native CHECK refusals: empty/over1KiB attempt identity,
empty/over64KiB profile, empty request, empty receipt and combined payload one
byte over16MiB. Every refusal leaves the receipt row count unchanged. A single
positive row accepts exact1KiB attempt,64KiB profile and16MiB combined request/
receipt bytes; both generated payload digests match independent expectations.
The fixture transaction is rolled back and the namespace disappears.

These administrator binary fixtures test the declared storage bounds only; they
supply no admitted recipe/receipt semantics, shared resource-account containment
or protected migration service. Failed inserts may consume nontransactional
sequence values; unchanged row count is not evidence of zero allocator work or
rewound identity. Complete migration atomicity, artifact admission and recovery
remain the existing M1–M5 requirements.


## Development commit barrier replacement is an installation effect

The current `packages/postgresql/native/operation-commit-barrier.sql` declares
`runtime_operation_commit_barrier()` and its ALWAYS deferred constraint trigger
on row_home_operation. Its body unconditionally raises55000 because the complete
finalizer is absent. This is a deliberate development fail-closed component,
not a supported runtime finalizer or an installed-ready guard.

The complete installer composition must explicitly inventory its selected fate:
replace it with the original qualified full finalizer, or retire the development
routine/trigger through an admitted exact replacement whose unavoidable completion
coverage is independently established. Do not silently omit/drop/disable it or
mark readiness because its name, timing and signature match. Retain exact before/
after source identities, event/dependency/grant coverage and atomic replacement
order in generated source/inventory. Removing the development barrier without
complete substitute coverage is not a runtime-unblocking fix.

This requirement supplements the five missing canonical handler bodies and two
scope validators. The replacement must include full original row/non-row, journal,
feed and operation completion proof rather than accepting a phase flag. Independently
exercise a valid completed operation commit, unfinished and early-immediate refusal,
savepoint rollback, unrelated caller work and lost settlement on the same selected
installation/security/issuer tuple. The current artifact is not qualified by
storage projection checks or lifecycle startup tests.


## Remaining ownership and dependency scope

Do not wait for all132 UMF/Ashlar/Truss security cases before performing Truss-owned
integration work. The security workstream's26 registered passes are scoped evidence;
its unimplemented remainder is not automatically Truss's prerequisite set. Select
and trace only the complete authority/publication/resource contracts required by
the particular Truss installed capability, without promoting partial evidence.

| Deliverable | Owning work and required input |
| --- | --- |
| Original transaction ordinal/control issuer and correction of all four admission families | Truss driver/executor integration owns implementation, original custody and native verification. Security grants must protect the selected private entrypoint, but another security graph renderer cannot issue this proof. |
| Seven canonical orchestration bodies and development barrier replacement | Truss owns the complete algorithm/source/dependency composition. Their language/optimizer/null attributes and SECURITY DEFINER direction are already selected in the installation gap matrix; exact owners, trusted search paths and effective rights follow the selected security composition. |
| Actual caller/current-authority admission and publication drain | Consume the security owner's exact selected contract and qualified subset; do not fork a resolver, trust a role name or require unrelated Ashlar acceptance cases. |
| Structural/native model generation | UMF owns export/generation primitives; Truss owns complete model/source/inventory correspondence and installation behavior. No copied DDL generator. |
| Logical SQL lowering and executing-engine compatibility | Weft owns compiler/profile changes. Truss owns binding, exact result decoding, native execution and the actual16.2/managed-target qualification.17.9 fixtures do not confer16.2 support. |
| Bootstrap, populated route and migration/recovery distribution | Truss owns the installed Python tooling, original registered artifacts and failure/preservation corpus. M1 selection follows a complete coherent source/target bundle, not arbitrary version labels. |

The immediate Truss-owned task remains original issuer/native admission integration.
The runtime/CLI wheel is usable component infrastructure, not a substitute for that
work. Record a precise unavailable owner input when encountered; broad statements
that security must finish first cannot close, defer or reassign Truss's own work.

The current installed-wheel component check now covers all12 Python modules and
42 tests, including the six private admission-custody controls. The
[installed-suite receipt](evidence/design-audit/python-current-installed-suite.json)
verifies installed/wheel/source payload correspondence outside the checkout, with
warnings treated as errors. This reused environment contains the pinned local
dependencies; it is not a new clean dependency-resolution claim. The private
custody registry does not supply native transaction authority or correct the four
native ordinal admission families. Complete installation, migration execution and
whole-engine qualification remain open.


## HELIX0.15.4 adoption in the accelerated queue

The [concern selection](../01-frame/concerns.md) and
[Architecture module map](../02-design/architecture.md#module-boundaries) record
the newer committed source separately from installed HELIX0.15.0. Apply the
following work inside P0/P1/P2, not after public preview. Existing evidence stays
historical; none of these gates is satisfied by document edits.

- **Modularity / P0–P1:** implement the architecture boundary-check command and
  inventory exact existing violations with owners/remediation. Prove allowed-edge
  success and forbidden-edge rejection through the real checker; add the same
  command to local and CI checks. Baseline/checker adoption may proceed immediately;
  dependent source work needs this gate. Keep Python custody private, Weft/UMF
  translation adapter-owned, and security work with its current owner.
- **Configuration / P1:** define exact configuration ownership/validation in
  embedding/installation Contracts. Build one typed immutable object in the
  composition root before effects. Distinguish required host-injected connection,
  credentials and operational handles from reviewed non-secret defaults; no
  scattered environment reads or committed managed endpoints. Embedded callers
  inject objects directly; environment layering belongs to the reference runner.
  Migrations use the same release/configuration as install; startup stays DDL-free.
  Test invalid/unknown inputs, precedence and secret-safe fingerprints.
- **Observability / P1–P2:** contract safe lifecycle/admission/refusal/recovery
  event names and typed attributes, optional real trace context, per-source
  sequencing and bounded retrieval. Use Python logging through an adopted OTel
  bridge when export is enabled; require actual receiver/mapping evidence before
  claiming OTel support. Keep CLI result stdout clean and diagnostics on stderr;
  the development runner owns safe JSONL manifests/rotation/retention. Declare
  record/queue/flush limits, exporter-outage/drop behavior and measured overhead
  budget. Test sensitive-value absence in every sink, capture failure, oversized
  records and shutdown deadlines. Do not log SQL values, consumer documents or
  asserted origin text. Diagnostic failure cannot replace or authorize durable
  journal/receipt settlement; never add an internal write retry loop.
- **Formal analysis / P0–P2:** owning technical designs specify admission ticket
  lifecycle/non-rewinding ordinals, commit_unknown/reconciliation and atomic
  installed readiness as separate affected slices. Derive stable property IDs
  from existing requirements/Contracts. Name states, guards, actual lock/transaction
  boundaries, crash/retry transitions, safety versus liveness and environmental
  assumptions. Start at precise specification with explicit semantic review;
  select an established bounded analyzer for admission and recovery after the
  host/native trust assumption is resolved. Record exact model/config/tool/source
  revisions, bounds, reachable successful and recovery witnesses and deliberately
  broken-mechanism counterexamples. Map model elements to actual enforcing code
  and running-system tests. Timeout/unknown/model-green is not implementation
  proof. Recheck on mapped source/config/assumption changes; carry observable
  assumptions and recovery symptoms into the runbook. Unaffected slices record
  a reasoned non-applicability disposition rather than running empty analysis.

### Corrected-runtime origin checkpoint

[The independent origin probe](../../../scripts/check-corrected-pgserver-origin.py)
and [receipt](evidence/design-audit/pgserver-corrected-origin.json) pass two actual
non-superuser captures on the private PostgreSQL16.15 candidate: authenticated
login, then SET ROLE. Original admission captures independently checked session
and acting role identities/OIDs and exact asserted-origin/profile bytes. Each
operation is rolled back and no registry row survives; committed setup exists
only in the disposable fixture removed by runtime cleanup. Fixture grants are
not a production grant inventory. The probe does not qualify installed R5,
R4, native ordinal issuance, a public mutation path or admission-object authority.
The original SQL ordinal allocator remains incompatible. These observed cases
are useful implementation witnesses for the later model/code correspondence,
not formal analysis or proof of the unresolved embedding-host trust boundary.


### Python module-boundary gate — observed adoption

The actual AST checker passes the twelve Python source modules/51 imports with
no baseline exceptions. Nine real-checker controls include an allowed nested
import and rejection of a driver in pure code, private custody imports (relative
and absolute), package escape, direct dynamic loading, a cycle, unmapped source
and wildcard import. The [receipt](evidence/design-audit/python-module-boundaries.json)
records checker/producer/source hashes and Python version. Local commands and the
CI workflow are in Architecture; no remote CI pass is claimed. TypeScript and
native dependency enforcement plus reflection/runtime visibility review remain
open and are not qualified by this Python-only result. These are development
checks; they neither import the toolkit nor install/start a database.


### TypeScript module inventory and remediation handoff

The compiler-AST/resolver inventory observes70 source files and232 imports in
this worktree, using TypeScript5.9.3/Bun1.4.2. All local import targets resolve;
15 imports cross package boundaries and12 directly reach PostgreSQL implementation
files from the UMF adapter. Two computed dynamic imports in `umf-bun/src/index.ts`
require semantic review. This is an inventory, not a debt baseline, API adoption,
whole-program typecheck or dependency gate; it includes current peer candidates.
The [receipt](evidence/design-audit/typescript-module-inventory.json) binds source
and compiler/producer hashes. Its [three real-scanner controls](evidence/design-audit/typescript-module-inventory-controls.json)
verify public/private resolution, literal versus computed loading, ignoring import
text in comments/strings, and nonzero refusal for unresolved local imports.

Reproduce from the repo root with an explicitly supplied adopted compiler API:

```sh
TRUSS_TYPESCRIPT_API=/path/to/typescript5.9.3/lib/typescript.js bun scripts/inspect-typescript-boundaries.ts /tmp/truss-ts-inventory.json
TRUSS_TYPESCRIPT_API=/path/to/typescript5.9.3/lib/typescript.js python3 scripts/check-typescript-inventory-controls.py
```

The following exact edges need a shared ownership resolution before a TypeScript
boundary gate can qualify them. Integration ownership is Truss catalog/native
assembly, with the active catalog implementation owner responsible for applying
moves; this handoff does not edit or approve their unfinished APIs.

| UMF adapter source | Current PostgreSQL target | Remediation / removal trigger |
| --- | --- | --- |
| `packages/umf-bun/src/acceptance-input.ts` | `packages/postgresql/src/acceptance-json.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |
| `packages/umf-bun/src/canonical-report-handoff.ts` | `packages/postgresql/src/acceptance-json.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |
| `packages/umf-bun/src/canonical-report-handoff.ts` | `packages/postgresql/src/canonical-wire-tree.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |
| `packages/umf-bun/src/catalog-asserted-origin-basis.ts` | `packages/postgresql/src/asserted-origin-map.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |
| `packages/umf-bun/src/catalog-captured-origin-basis.ts` | `packages/postgresql/src/captured-origin-context.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |
| `packages/umf-bun/src/catalog-captured-origin-basis.ts` | `packages/postgresql/src/acceptance-json.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |
| `packages/umf-bun/src/catalog-epoch-context-basis.ts` | `packages/postgresql/src/captured-origin-context.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |
| `packages/umf-bun/src/catalog-epoch-context-basis.ts` | `packages/postgresql/src/acceptance-json.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |
| `packages/umf-bun/src/catalog-execution-report-candidate.ts` | `packages/postgresql/src/asserted-origin-map.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |
| `packages/umf-bun/src/catalog-input.ts` | `packages/postgresql/src/acceptance-json.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |
| `packages/umf-bun/src/catalog-original-execution-basis.ts` | `packages/postgresql/src/acceptance-json.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |
| `packages/umf-bun/src/catalog-report-correspondence.ts` | `packages/postgresql/src/acceptance-json.ts` | Extract pure shared translation into a core-owned module with a reviewed public contract; remove this edge before packaged preview qualification. |

Preserve the exact acceptance numeric/size refusal grammar, original byte/context
custody and asserted-versus-authenticated origin semantics during extraction;
CONTRACT-003, CONTRACT-007 and CONTRACT-010 govern those meanings. Do not simply
re-export every internal helper or add adapter-directory exceptions. Keep native
capture/enforcement in PostgreSQL and upstream assertion semantics with UMF.
Choose actual packaging/exports only after separating pure translation from native
authority; existing six-package declarations alone do not establish that split.
Retain original consumer and invalid-input tests across the move.

Then enforce the reviewed package graph through the real compiler resolver,
including portable `weft` rejecting native/host dependencies, native assembly
rejecting runtime/tooling/conformance imports, and adapters using reviewed public
interfaces. Prove allowed and forbidden/private edges plus cycles through actual
checker controls. Dynamic UMF loaders need exact integrity/containment review;
a compiler inventory cannot authenticate loaded code. Existing source hashes are
observations, not permission to baseline later changes. Remote CI enforcement
remains open until the actual check and measured controls exist.

### Upstream coordination checkpoint — 2026-10-09

Read-only origin queries now identify UMF `main` at
`6a2929d52d23b4587c9913aa87b3a265cf43ed1e` and Weft `main` at
`764d9fa1c4aef68358a5c77c85b051d6d7bf0495`. UMF's reviewed recent range includes
research-tool distribution and a default/deployment branch rename to `main`;
future alignment checks must use that actual branch. This checkpoint does not
replace the previously qualified Truss adoption pins or imply numeric/native
admission changes.

The two new Weft commits add explicitly selected Databricks required/optional
String COUNT DISTINCT, IN and narrow HAVING compositions in the0.3 candidate
family. Review of runtime registration, backend admission and its exact-arithmetic
contract shows distinct backend/profile identities with candidate fences. Keep
Truss's adopted `f05f2df` compiler/compile-sql0.2 tuple unchanged; no new feature
is silently inherited and no Truss SQL compiler fork is required. A future adoption
needs its own whole-vector source/artifact/native compatibility evidence.

The security owner's live task is still working on installation physical-profile
comparison and its pre-commit observation harness. Its latest snapshot reports a
harness lock/deadlock correction, not a completed admission profile. Native profile
comparison remains with that owner; this work neither duplicates it nor adopts
unfinished source. These snapshots are coordination evidence, not qualification.


### Formal specification checkpoint: ordinal/admission components

The owning Python design now specifies original identity/capacity/consumption,
lock boundaries and failure transitions with stable PY-ORD/PY-ADM property IDs.
The test plan maps those properties to the existing two ordinal/six admission
methods; [source-bound execution](evidence/design-audit/python-formal-correspondence.json)
passes all eight with warnings treated as errors. The component-level assurance
is author-reviewed precise specification plus implementation tests, not bounded
formal analysis or proof. At that historical checkpoint no analyzer/model/configuration had been selected.

The [later bounded model](evidence/design-audit/python-custody-bounded-model-controls.json)
now explores906 states/6224 transitions for one issuer, two ordinal values and two
confirmation tickets, with six detected broken variants and a retained unfenced
close/native-effect counterexample. Tool/configuration/source pins and exclusions
are in the owning Python design. This is author-reviewed abstract component
analysis, not implementation refinement, native authority, liveness or complete
protocol verification. Original driver/account/security integration and independent
review remain required; a failed initial harness expectation and exact initial
model source are preserved separately.

The review makes the post-verification close gate/native-dispatch gap explicit:
local closure cannot fence native effects by itself. PY-NATIVE-001 still needs
original native producer/account/arbitration/security integration under the accepted
ADR-008 embedding-host trust boundary. Preserve separate gate/dispatch/native-effect
transitions in the later bounded model, with rewind/restored-permission/copied-token
and unfenced-effect negative controls. This checkpoint does not substitute another
component receipt for the required P0 integrated native admission experiment.


### Configuration contract checkpoint

The reference-configuration candidate assigns ownership, typed embedding versus
launcher layering, exact refusal/effect boundaries and safe fingerprint rules.
It distinguishes process options from native original configuration/generation
admission, preserving the security owner's current-state comparison work.
CFG-01–12 cover typed original injection, absent/invalid/unsupported inputs,
precedence, secret-safe representations, inert construction, explicit local
custody, unchanged receipt meanings, account non-refund and native drift.
Implement these at the actual composition/launcher boundary during P1; do not
introduce a generic loader or configuration file merely to make these declarations
look implemented. No new config API or qualification is claimed.


### Observability contract checkpoint

The [diagnostic contract](../02-design/contracts/diagnostics.proposal.md) specifies
phase/refusal/failure/unknown/quarantine event ownership, OTel field projection,
privacy-before-sink, bounded queue/record/flush and development capture policy.
The [test plan](../03-test/diagnostics-test-plan.md) defines OBS-01–09 actual receiver,
privacy/failure/loss/cursor/overhead qualification. These are P1/P2 integration
requirements, not an implemented logger or telemetry adoption. Actual SDK/bridge
pins, carrier schema, overhead budget and receiver evidence remain open. Keep
receipt/journal settlement authoritative and independent of diagnostic delivery;
never ingest local CLI connection results wholesale as safe telemetry.


### Corrected current-layout compatibility checkpoint

The original structural and populated-guard probes now accept an explicit
`--corrected-pgserver` selection. They require the exact
`pgserver0.1.4+truss.pg16.15` / PostgreSQL16.15 pair before DDL, retain separate
corrected receipts and record actual postgres/psql binary hashes. The published
0.1.4/16.2 profile and its historical receipts are not overwritten or relabeled.

The [corrected structural receipt](evidence/design-audit/pgserver-corrected-umf-structural-correspondence.json)
compares the original0.16 source/adjunct/guard composition against UMF structural0.6:
50 tables,481 ordered columns,67 ordered physical FKs,12 sequence configurations,
25 explicit index structures and64 primary/unique constraints match. Four immutable
TRUNCATE attempts refuse in origin/replica modes. The
[corrected populated receipt](evidence/design-audit/pgserver-corrected-populated-guard-component.json)
passes12 UPDATE/DELETE/TRUNCATE refusals across both immutable homes and both modes,
independently comparing complete original rows, fixture bytes and generated hashes
after each attempt. Both disposable probes roll back all fixture DDL and confirm
the namespace is absent before stopping their owned server.

Reproduce in the installed corrected private-wheel environment:

```sh
python scripts/check-pgserver-umf-structure.py --corrected-pgserver
python scripts/check-pgserver-populated-guards.py --corrected-pgserver
```

This removes a specific current-layout compatibility uncertainty on the corrected
macOS/Python tuple. It is not full expression/collation/privilege qualification,
an ordinary authorized write path, a native issuer/account, complete guard/finalizer
installation, initialized readiness or populated migration. PostgreSQL16.15 still
lacks transaction_timeout: a profile requiring it must refuse or qualify its
separately admitted bounded alternative. The corrected binary remains a private
candidate, not a published default dependency. P0's actual original native admission
integration remains required, with no shortcut through these component probes.

### Native body / security-owner dependency checkpoint

The existing seven-routine manifest/matrix already selects PL/pgSQL attributes,
protected ownership and full-cohort validator composition. Its missing bodies
cannot be implemented honestly by trusting seal flags, caller ordinals or dummy
validators. The next dependency remains original operation attribution/account/
generation authority, followed by complete observer/validator/finalizer bodies and
atomic inventory/ready publication. No new product decision between handler
languages or invoker/definer is needed.

Read-only inspection previously reported scoped routine-definition guard success
and altered-definition/signature refusals; full acceptance at that checkpoint was
26/132. The historical security turn, `01a12379-c34d-7a43-b8fa-c568d229a726`,
failed with thread status systemError: the platform flagged possible
cybersecurity risk. This is a terminal turn observation, not an active process to
wait for or permission to restart/message the owner. Its last commentary reported
197 native bridge observations, but this handoff has not independently inspected
a corresponding receipt and makes no qualification claim from that count.

Keep native routine/profile comparison, unsupported-policy activation and report
weakening with that owner. Retain Truss's original issuer/account and seven-body
handoff separately. Complete installation needs the exact adopted security subset,
original producer/profile artifacts and independent native evidence; unavailable
owner outputs remain explicit dependencies. Independent Python/runtime/packaging
work can continue. Do not wait for unrelated security backends, fork authorization,
or interpret a routine lock or compiler-refusal bridge as policy activation or
complete R4/R5 qualification.


### Administrative ordering and bounded-recovery correction

The owning Python migration/install handoff now follows P0–P4 explicitly: fresh
install and bootstrap settlement precede preview operations, while actual populated
M1 selection/apply/reconcile follows a coherent admitted source/target. It no longer
selects defective16.2 or makes M1 a prerequisite for usable application operations.
The bounded-administration section names original forward/containment/observation
profile responsibilities, one explicit reconciliation invocation and timeout versus
pre-effect-refusal distinctions. Actual native contention/cancellation/lost-commit/
post-commit-cleanup schedules remain implementation gates; no stock driver or
secondary lock/recovery mechanism is silently adopted.


### Consumer-discovery scope reconciliation

The owning Python design now closes R1's stale pending-decision row against actual
accepted ADR-003/ADR-001, and explicitly keeps every R6/R8/R9 consumer shape on P2's
implementation path. Partial direct reads cannot satisfy R8. Parsed-input/compiler,
ready-index and native resource dependencies must be qualified or trigger a
reforecast, not silent shape removal. Preview corpus appears with installed cases;
full R2 interchange, R3 stable layout/Lakebase and R10 publication remain release
gates. P3 retains durable idempotent repeat/reached/feed qualification. The original
consumer discovery input remains unchanged, and all R1–R10 are required before
calling the result consumer-ready.


### Revised consumer input checkpoint

The original external consumer requirements changed on2026-10-09; a new frozen
snapshot preserves requirements/corpus/two models separately from the old archive.
The revised input accepts epoch/commit-aware receipt positions and distinguishes
Invalid from available false.35 authored core names remove the prior naming
prerequisite for the new source pins. The revision checker retains input-only
scope: compiler/native/corpus execution is not adopted from old proposal receipts.
Next PY-02/PY-05 work consumes these actual authored bytes and reruns original
compiler/name-resolution controls; P3 reached/replay cases preserve issuance and
no-op distinctions. The first release still needs all R1–R10, not just this input
alignment.


### Revised-source query frontend execution

The original consumer bytes now have fresh frozen-f05f2df frontend execution:
90 model/query observations,80 resolved and10 original directed-relationship
predicate refusals. Full backend/index/native/resource and parsed-input admission
remain unqualified. The local Weft iteration packet identifies the five exact
consumer steps and required key-membership/conjunction semantics; Weft remains
compiler owner. Do not substitute direct edge enumeration or rewrite consumer SQL
to close these R8 cases. A failed compiler fixture produces no new success receipt;
actual run metadata must correspond to its output/input/harness hashes.


### R7 refusal versus negative visibility handoff

The existing position/reached contract and RV schedule now explicitly map the
revised consumer Invalid cases without changing their wire. Available false
requires independently admitted issued/committed identity and negative same-cut
inclusion proof. Missing receipt evidence is unavailable, not false or proven
never-issued. Safe invalid_token projection remains security-owned; outer
execution uncertainty retains original recovery. Private locator decoding and
wire-shape tests cannot satisfy these native classifications. P3 implements the
extended RV controls under the original resolver, with no hidden connection/wait.


### Consumer dry-run/import native coverage

The revised corpus's seven action/import cases now have an explicit native
observation handoff. Supplement them in P2/shared corpus with actual caller rollback,
full deferred validation, private journal/request/receipt absence and distinct
atomic-versus-per-item import schedules. Existing action-batch success/refusal does
not prove atomic import; visible row counts cannot prove full native containment.
Retain ID/ordinal/resource non-refund and original uncertain recovery semantics.
The new test plan links exact original case IDs, without marking any as executed
Truss conformance or changing the consumer's source files.


## P1 installed-resource implementation handoff

Use the [Python installed-resource selection boundary](../02-design/python-integration.proposal.md#python-installed-resource-selection-boundary)
for packaging composition. Private index decoding, descriptor-relative directory
resolution and complete declared-byte capture now exist, with independently pinned
index bytes, closed unique membership, exact length/hash checks, original scalar
byte reservations and retained use-time bytes. The current installed wheel passes
58 tests; this remains component evidence. Complete precharged heap/work/deadline
accounting and independently registered real release membership still require
integration. Then package the complete admitted
CONTRACT-008 bundle and integrate IM01–IM05 with explicit install/verify and
unknown-outcome reconciliation. Do not publish installation readiness from a
resource-reader result, current candidate inventory or a recomputed local pin.
The [PKG schedules](../03-test/migration-inspection-contract-walkthrough.proposal.md#clean-installed-package-qualification--py-07)
retain actual wheel/sdist and native execution exits. The shipped pgserver default
and populated migration gates remain unchanged.


### Installed host byte-account prerequisite checkpoint

The [new installed-wheel receipt](evidence/design-audit/python-byte-account-installed-suite.json)
passes48 tests and matches all13 current module payloads against original wheel
and source bytes outside checkout. The private `BytePermitAccount` supplies
original identity permits/allocations, atomic reserve/drawdown, nonrefundable spent
allocation, qualified producer release/termination, retained unknown custody and
cumulative ledger-record bounds. It is available for host bookkeeping integration;
it is not a complete native account or proof of actual Python heap containment.
The reused environment remains corrected private pgserver0.1.4+truss.pg16.15 on
macOS arm64/Python3.11; no published default pin or managed-target claim changes.

The subsequent reader implements bounded byte capture, closed index membership
and original-root directory resolution against this account. Next qualify complete
precharged allocation/work bounds and trusted release/termination observations
across read/decode/hash/retain and native archive/use. Reader construction stays inert. A
reader failure closes ordinary account admission as applicable and preserves
original permit/allocation ownership until confirmed release; returning an error
or deleting a local reference cannot refund the unresolved charge. Use the existing
altered-package controls and installed-package gates. Still require full native
routine/security/grant/inventory composition before public installer readiness.


### P1 continuation after installed reader composition

The [full installed component run](evidence/design-audit/python-resource-reader-full-suite-diagnostic.json)
passes58 tests on15 original module payloads. Preserve the preceding180-second
timeout and unverified cleanup; the successful later run does not explain them.
All complete-release/native cases below remain unqualified.

| Remaining delivery | Original output required | Exit evidence |
| --- | --- | --- |
| Account composition | One selected original allocation/work/deadline profile and actual read/decode/hash/buffer/archive producers, retaining containment/recovery reserves. | Exact-at/one-over and cancellation/unknown ownership across the same account; scalar declared bytes cannot qualify heap/native work. |
| Release resource registration | Independently reviewed complete release index and original model/generated/native/grant/initialization/verifier/profile/recipe inventory, with bootstrap bundle/inventory pins. | PKG-01 clean wheel and sdist membership. Neither a test inventory nor recomputed package hash supplies expected release authority. |
| Installed package realization | Explicit trusted installed-directory root selection on an actually qualified platform, followed by the current composed reader. | Execute altered/missing/foreign package cases with original release registration and independent pre-effect native observations. Zip/Windows require separate support; no fallback realization. |
| Protected native composition | Original issuer/account and seven mandatory routine bodies, security-owner adopted subset, role/grant/initialization/complete inventory procedures. | Actual ordinary-role effects/refusals and rollback/finalization; exclude legacy executable ordinal allocators. No synthetic seals or no-op bodies. |
| Installer and verification | Explicit public install/status/verify/reconcile preserving host connection ownership and original attempt/recovery. | CONTRACT-008 IM01–IM05 and PKG-02/08 through actual native publication; late failure/unknown must retain original custody. |

These are dependencies for one complete installer, not five independently usable
installation APIs. Account and resource implementation remain Truss-owned;
UMF supplies original schema interpretation/generation, Weft its separately
admitted compiler realization, and the security owner authority semantics.
Populated migration PKG-07 and full Python/TypeScript interchange remain required
P4 exits; neither is silently removed to claim the P1 preview complete.


## Seven-body implementation packet: next native installation work

Read `reference-routine-design-v0.1.proposal.json` and its original trigger
references alongside current CONTRACT-001 OC/RF/EL, CONTRACT-005 privilege
boundaries and CONTRACT-006 FV algorithms. The frozen manifest chooses attributes/signatures, not executable
bodies. Its original governing hashes must retain their historical scope; compare
current contract changes semantically before producing a newly registered packet.
The16-selector security worklist is a known subset, not complete callable closure.

Bind the packet's exact counting meaning before implementing edge bodies. The
existing EL03 per-edge multiset is an occurrence cap; the
[distinct-neighbor candidate](../02-design/contracts/distinct-neighbor-participation.proposal.md)
instead groups proved typed endpoint pairs and derives representative markers.
An owning UMF participation claim requires the latter meaning and its complete
qualified mapping, not an old occurrence-cap body with a renamed profile.
The packet must freeze the original accepted definition/binding, counting
interpretation, marker algorithm and source/build/profile version together.
Absent or ambiguous interpretation refuses even with zero edge rows. Neither an
application count-mode flag nor a caller marker can select native semantics.

| Affected body/producer | Additional distinct-neighbor integration exit |
| --- | --- |
| Canonical edge writer and edge_limit_observe | Retain complete old/new occurrence membership, including representative deletion, FK cascade attribution, imported lower IDs and both endpoint directions. Observe all original effects; only the writer derives/replaces markers. |
| edge_limit_catalog_observe | Full populated degree and representative-marker derivation for definition tightening; zero-owner minimum checks use original complete owner roots. Preserve separate retirement/reactivation provenance. |
| edge_limit_verify_current_scope | Read-only complete pair grouping, canonical minimum representative and bidirectional marker correspondence under the selected interpretation. No repair, marker insertion or count-mode fallback. |
| effects_ready, row_touch_commit_check and feed validators | Complete edge/marker operation contributions and current generations after representative changes; occurrence IDs/history/feed bags remain unchanged by degree grouping. Existing finalized results remain immutable. |
| Installer/verify and explicit conversion | Independently compare the exact counting-profile/body/trigger/grant/configuration bundle. Convert the complete populated marker interpretation atomically under original administrative exclusion; a changed profile label or empty marker table does not establish conversion. |

The eight mathematical marker vectors are supplemental design inputs, not native
exit evidence. Independently run parallel/different-neighbor concurrency,
representative/nonrepresentative/last deletion, incoming/self-edge limits,
definition-only tightening, hidden siblings, bypass and early-check/savepoint
failure against actual enabled bodies and ordinary roles. Until those schedules
and complete release closure pass, owning UMF participation remains unavailable;
existing explicit occurrence-cap behavior and its qualified scope remain separate.

| Body | Required original inputs and behavior | Independent native exit |
| --- | --- | --- |
| row_touch_observe | Exact installed relation/event and complete OLD/NEW; actual transaction and unique admitted unfinished operation; original cascade/contribution and pre-reserved capacity. Retain complete contributing operations and advance dirty generation. | INSERT/UPDATE/DELETE each canonical home; multiple effects/operations retain all contributions; foreign event, absent/ambiguous attribution and overrun refuse without partial graph/touch effects. |
| edge_limit_observe | Exact edge event and both original/current typed endpoints; admitted operation and complete affected definition/owner scope under prescribed exclusion/account. | Add/remove/change both endpoint directions; repeated edges and changed definitions preserve full multiplicities; omitted affected owner or unsupported scope refuses. |
| edge_limit_catalog_observe | Original catalog event, admitted catalog operation and full old/new affected relationship definitions/owners, including populated existing edges. | Definition-only limit change with unchanged edge rows; invalid populated scope refuses whole catalog transition; no fabricated empty edge inventory. |
| row_touch_commit_check | Original native event plus all actual-transaction operation/touch/capacity records, complete coverage, generation equality and application finalization; invoke ordinary feed validator when selected. | Unsealed/missing contribution, unfinished operation, stale generation and unresolved reservation refuse early checking/commit; complete finalized scope validates without mutation or repair. |
| feed_current_union_check | Exact installed feed-store INSERT/UPDATE/DELETE and OLD/NEW attribution; retain original transaction/cut/account and dispatch ordinary validator. | Every event on all four stores; late delete/alter/omission and repeated deferred firing; scope includes independently required effects even when feed registration was omitted. |
| feed_union_validate_current_scope | Actual transaction and complete protected producer scope; execute FV01–FV07 under original authority/cut/account. No caller scope/xid/ordinal and no latest-row inference. | Full member/catalog/configuration prerequisite union, missing/extra/duplicate/mismatched facts, complete allowed no-op transaction; absence of registered feed rows cannot establish empty required effects. |
| edge_limit_verify_current_scope | Actual protected definition/edge/marker scope under original same-cut exclusions; derive/compare complete required multiset. | Valid and invalid full scope, marker omitted/altered, both endpoint directions and definition-only effects; return has no seal/finalization/publication authority. |

The body packet must include original source/model/generated statement identities,
exact argument/result/native attributes, role ownership, private call graph and
complete dependencies, original trigger parent/event/partition/enablement mapping,
plus selected operation/account/security/profile pins. Register real expected
scope/effects independently before execution. Preserve ordinary caller denial and
integrity observation independently of caller disclosure; administrative fixture
rights cannot qualify ordinary authorization. Actual installed OIDs and effect
receipts are observations, not authored fixture identities.

Implement protected attribution/account wiring before admitting positive body
execution. Observers consume earlier reservations and cannot acquire earlier
capacity locks after owner/key locks. Validators perform no sealing, repair,
registration, counter reset, commit or constraint-mode changes. Both trigger
handlers call the separately bound ordinary feed validator; never SELECT a
trigger-returning handler as a helper. Every repeated check charges actual work;
no cached completion flag supplies a bypass.

Run each exit against actual enabled installed triggers and the selected ordinary
roles, then exercise the complete combined transaction through savepoint rollback,
SET CONSTRAINTS early checking, failed finalization and actual commit. Keep all
original spent charges across rollback and quarantine unknown settlement. A body
source/count or individual guard refusal cannot pass combined installation.
Only after full call/trigger/privilege closure and independent complete inventory
verification may IM01–IM05 publish ready. The accepted security minimum handoff
remains required; it does not require unrelated security backends or authorize a
Truss-owned policy resolver. These schedules are not_run and confer no support.


## Security owner resumed: graph-stage compatibility review

The [read-only owner review](evidence/design-audit/security-resumed-graph-stage-review.json)
observes a new in-progress turn `01a123d9-78b3-7b52-a2bd-eb020c4c6847`, superseding
the earlier failed-turn status. No restart or cross-chat message was sent. The
retained graph-stage receipt has88 actual candidate observations but explicitly
sets nativeImplementationQualified=false and excludes ordinary identity enforcement,
committed catalog/current binding, authenticated namespace authority, source/cut
custody and backend acceptance. Original source fingerprints/current correspondence
are retained in the review; counts or current filenames cannot expand that scope.

Its source tuple includes qualified-property layout0.15 and legacy
operation-admission.sql with the retained rollback-only commit barrier. Truss's
current source-epoch0.16 and host-issued admission candidates are different inputs.
Do not install the legacy allocator alongside the issued-ordinal overload or
transplant old role/catalog/mapping evidence into the current profile. Require the
owner's exact adopted subset/interface, current original catalog/layout/principal
binding and protected publication/freshness packet, then independently qualify
native ordinary-role allowed/denied paths on the same complete installation.
Graph source/key/endpoint and supplied-dataset components remain reusable candidates
under their exact owner meaning; Truss owns composition and does not fork their
policy resolver. The seven-body/account/ready-publication gates remain open.

## Shared structural registry decoder evidence

The [Python/TypeScript replay](evidence/design-audit/python-typescript-operation-registry-parity.json)
passes 17 independently authored vectors through both original decoders. It covers
all four phase shapes, exact native integer maxima, duplicate/foreign ordinals,
noncanonical and overflowing integers, malformed byte carriers, and the exact byte
limit versus one byte over. Accepted rows retain the complete original cell values.
The fixture and checker are retained under tests/fixtures/operation-registry-decoder.json
and scripts/check-operation-registry-parity.py, with original source fingerprints.

This is private source-component parity, not installed-wheel qualification,
the full shared consumer corpus, native observation completeness, or transaction
authority. An assigned empty registry is structurally valid; its permission to
perform an operation still requires the native OC02/OC06 selection rules and the
complete original transaction observation. Continue with original driver/account
composition and the complete installation gates above.


## Integrated continuation after current component evidence — 2026-10-10

The [fresh offline resolver installation](evidence/design-audit/python-offline-resolved-local-install.json)
now closes the explicit private wheelhouse's normal dependency-resolution and
local lifecycle observation. PKG-01 still requires public resolvable artifact
availability, actual payload identity, advertised upgrade/platform paths and
complete consumer acceptance. The ordinary pgserver==0.1.4 constraint accepts
both public and corrected local versions; do not infer native bytes from that
requirement or claim adding the extra necessarily downgrades an installed build.

The [native timing witness](evidence/design-audit/python-dry-run-native-timing-restoration.json)
closes six named deferred-UNIQUE/savepoint observations only. Feed it into PY-04's
concrete R6 relationship-limit/caller-sentinel test after the actual installed
guards/executor exist. Do not add another generic PostgreSQL savepoint probe in
place of that integrated test. Preserve transaction_unusable until original local
rollback is confirmed, retain earlier caller work, and independently observe
explicit outer rollback. Complete journal/receipt/account/actor validation is
still required; administrative fixture evidence cannot waive it.

For P1, implement original protected operation attribution and account wiring,
then the seven actual bodies and complete native trigger/call/grant closure.
The [current routine semantic reconciliation](evidence/design-audit/routine-feed-disclosure-source-review.json)
and sixteen damaged-manifest controls keep source selection reproducible but
supply no executable guard or ready marker. Use the existing complete installer
observer and PKG-08 settlement schedules on the same candidate. No partial body
packet, synthetic seal or copied source hash opens public readiness.

For P2, attach the concrete R6 and [finite writer workload](../03-test/catalog-writer-workload-v0.1.proposal.json)
to actual public operations on that installation. The workload's observation
windows must be enforced by the original runner/executor, with full1024 planned
outcomes and unknown custody intact. The [acceptance scaling procedure](../03-test/acceptance-scaling-experiment.proposal.md)
measures fresh complete committed acceptance; its proposed ratio still requires
profile selection and native execution. These are existing criterion exits,
not additional milestone prerequisites detached from usable operations.

UMF remains the schema/DDL/semantics owner. Weft's committed f3208b2 private
path frontend is recorded in the [source review](evidence/design-audit/weft-f3208b2-path-foundation-review.json);
public0.4 lowering and the Truss result/authority/account tuple are not adopted.
Security's completed evaluated-fact checkpoint stays distinct from its active
native bridge iteration. Consume the minimum exact completed owner packet when
qualified; do not transplant its17.9 fixture or moving APIs into the16.15 default.
P3/P4 feed/reached, complete corpus/interchange, stable layout, populated migration
and managed qualification remain in the original queue. None of these component
observations changes the full45-story/167-criterion objective or marks P0/P1 done.


### Native operation resolver implementation split

Implement two private resolver paths within the existing protected body/account
composition; these are internal responsibilities, not new public APIs. The unique
unfinished-operation index proves only an upper bound. It supplies neither an
original operation/account nor authority to infer one from the newest row.

For observer dispatch, derive the actual assigned native writer transaction and
trusted installation/incarnation context from the admitted original producer.
Under its original exclusions enumerate the protected current transaction
registry, requiring exactly one unfinished operation with its exact admitted
phase, generation, producer/context and pre-reserved event capacity. Zero rows,
two candidates, foreign context, unavailable complete observation or finalized
operation refuse before canonical/touch/marker effects. Caller xid/ordinal,
custom session text, an RLS-filtered registry, MAX(ordinal), last-issued host
counter or constraint-name equality cannot select that operation. Bind each
actual trigger event's original relation and OLD/NEW contribution to this same
operation/account before consuming its existing reservation. No nested observer
opens a replacement account or changes phase to make attribution available.

For commit/final-state validators, enumerate every original surviving operation
and its complete contributions, including earlier finalized operations and
no-op operations with empty effect sets. Use the established OC/RF/FV/EL generation
and scope rules. Absence of an unfinished row cannot prove no required effects;
absence of feed registration cannot certify an empty transaction. An observer's
unique-current-operation result is not the validator's complete inventory.
Savepoint rollback removes native surviving contributions under its original
procedure but cannot reset host ordinal/cumulative work or erase unknown custody.

The first installed resolver controls independently cover zero current operation,
two unfinished candidates, stale phase/generation, finalized-only registry,
RLS-hidden sibling, foreign transaction/installation and exhausted earlier
reservation. Validate a transaction with finalized A followed by current B,
then B rollback with A surviving, and a genuine all-no-op admitted operation.
Check full original contribution/phase/account inventories and effects before
and after each failure. Both registry-index and genuine business-key violations
may emit23505; classify only through original admitted native failure provenance,
not a name/text heuristic. Actual protected resolver procedures, grants, account
producer and enabled body execution remain unimplemented qualification outputs.


### P0 original control/issuer composition implemented as a private candidate

The [original issuer handoff](operation-ordinal-issuer-handoff.md#original-connectioncontrol-producer-candidate--2026-10-10)
now has an actual pg8000/16.15 control producer rather than separate numeric
issuance and caller-labelled savepoint observations. Fifteen current native
controls preserve caller work, nonrewinding ordinals and explicit uncertain
attempt custody while independently observing that quarantine leaves a live
backend. Source, installed module and historical original pins are retained.

Continue P0/P1 by binding its original confirmations to one-use admission and
all four issued context families, then protected attribution/account and the
seven mandatory bodies. Current authority still comes from the security owner;
no unfinished capability/binding grammar is adopted. Actual recovery containment,
full resource composition and complete installed ready publication remain open.


### P0 native rejection recovery correction

The original control producer now distinguishes a fully captured native rejection
from unavailable completion. Its [recovery handoff](operation-ordinal-issuer-handoff.md#completed-native-rejection-versus-unavailable-completion)
retains the pre-fix six-observation counterexample, nine actual16.15 recovery
observations and fifteen current regression cases. Qualified rollback-to precedes
all inquiry/restoration/release SQL in an aborted transaction; confirmed restored
xid and readiness precede continuation. Caller work and spent ordinal survive.
This closes that concrete candidate defect, without making SQLSTATE a refusal/
retry authority or closing the full security/resource/installation gates.

Keep reserved cleanup capacity and complete savepoint handle invalidation in
CH-02/05's original control/account work. Four-family admission must test actual
native rejection through the corrected path, not catch an exception inside a
synthetic DO block that leaves the outer transaction apparently healthy.


### Shared savepoint lifetime and upstream adapter continuation

The [issuer lifetime handoff](operation-ordinal-issuer-handoff.md#shared-original-issuer-and-savepoint-lifetime)
now corrects per-facade issuer restart and ancestor/descendant lifetime before
four-family admission. Fourteen actual native lifetime observations pass; fifteen
control and nine error-recovery regressions pass under their separate scopes.
Compatible facades share original physical-connection issuer/account/control
custody and registered namespaces. Unknown work cannot reopen through a new
facade. Full reusable connection, cleanup capacity and installed authority remain
qualification outputs.

Fresh upstream observation keeps UMF main322b193 and advances Weft to e004b58.
The [Python owner-adapter handoff](../02-design/python-integration.proposal.md#official-umf-python-document-machinery-current-owner-source-handoff)
adds official tagged `umf-core` structural/preservation machinery to PY-01/A1/A2
without substituting its unchecked semantics for native acceptance. Its exact
wheel/resource/account controls are adapter implementation work, not another
product decision or a reason to wait for full Python parity before P1. The
explicit Weft path runtime is a distinct Rust candidate namespace; no Python
bridge or Truss backend adoption follows. Preserve the complete original tuple
when the security owner's eventual matching/lowering API is ready.


## Original four-family admission composition — 2026-10-10

The private original-driver admission candidate now connects confirmed native
savepoints to the installed one-use admission custody on the same physical
connection. All facades share the issuer, confirmation inventory and admission
custody; admission requires the latest live boundary. Payload reservation precedes
SQL encoding, and original native context cells remain authoritative.

[The native receipt](evidence/design-audit/pg8000-four-family-original-admission-native.json)
records 92 observations on PostgreSQL16.15 across base, asserted-origin,
source-epoch and configuration admission. Each family verifies complete original
context and registry cells, refuses confirmation reuse before further SQL,
rolls back admitted registry/configuration rows, and contains an actual SQLSTATE
22023 rejection by rolling back first from ReadyForQuery E. The next operation
uses ordinal2 after rolled-back ordinals0 and1; earlier caller data and the
original transaction ID survive. There is no automatic retry. The original
DatabaseError is retained; successful local containment does not classify a
business refusal or establish complete healthy-scope authority.

The shared locked rollback helper also passes the
[14-observation lifetime regression](evidence/design-audit/pg8000-savepoint-lifetime-after-admission-native.json)
and [nine-observation abort-recovery regression](evidence/design-audit/pg8000-aborted-control-after-admission-native.json).
The before-admission original control source is archived alongside the candidate
so prior receipts retain their exact producer bytes.

This is administrative local evidence using six synthetic artifact byte strings.
It does not qualify their meaning, ordinary-person isolation/origin, current
security, the complete allocator/native-work and pre-reserved cleanup profile,
seven native bodies, finalization, commit cohorts, journal/feed/receipts or ready
publication. Driver qualification and installer readiness remain false; no
acceptance criteria are promoted. The next implementation composition must add
original artifact/authority admission and the protected native guard inventory
before exposing an installed mutation API.


## Native capacity-ledger exclusion checkpoint — 2026-10-10

The [original-ledger native receipt](evidence/design-audit/capacity-ledger-native-exclusion.json)
passes six observations on corrected local PostgreSQL16.15. The checker executes
both original table and parameterized fresh-initialization sources, retaining the
complete layout-definition and resource-profile bytes and comparing every
returned ledger cell. Two actual connections demonstrate that a singleton
`FOR UPDATE` lock acquired before a child savepoint survives rollback of that
child. The contender receives native55P03 under a250ms local lock timeout,
restores its savepoint without automatic resubmission, and reads unchanged
counters. Only after explicit owner transaction rollback does a separately
submitted contender statement acquire the ledger. Complete original ledger
bytes and counters remain unchanged. A2s statement timeout bounds the fixture
statement; these fixture wait limits do not select release runtime defaults.

This confirms CONTRACT-009's documented serialization cost at the proposed
ledger: an operation-local rollback cannot release an earlier ledger lock.
The host controls the remaining transaction lifetime, so caller-owned idle time
cannot be advertised as bounded by an operation deadline. Writer scheduling must
allow the first admitted transaction to terminate before waiting writers can
acquire capacity; do not place a barrier requiring all writers to hold this
singleton concurrently. Refusal recovery must preserve prior caller work and
charge the original account, without internal retry.

The isolated administrative fixture does not prove fresh complete touch scope,
head-before-capacity ordering, private ownership/grants, native reservation
identity, operation attribution, exact consumption/settlement or whole-workload
performance. The original table explicitly lacks the reservation registry and
procedures. P1 must implement that registry and its original transaction/issued
ordinal/profile custody before observers can consume capacity. Native guards
cannot replace it with process-local counters, an unlocked COUNT, or acquisition
of the ledger after lower owner/key locks. Keep original capacity and operation
proof changes inside the same confirmed operation containment; preserve spent
host work across rollback. Installer readiness and native reservation
qualification remain false, with no promoted acceptance cases.

Reproduce with the corrected local environment and pg8000 dependency path used
by the original admission checker, running
`check_capacity_ledger_native.py <fresh-receipt-basename.json>` from the evidence
directory on an isolated server. The receipt pins every original source and the
checker; it introduces no installed schema/profile version or new public API.


## Reservation producer implementation packet — 2026-10-10

Use the existing installation singleton for the proposed serialized capacity
profile. The [six-column reservation extension](../02-design/contracts/row-home-capacity-reservation-v0.1.proposal.sql)
binds one active native transaction/issued operation to complete original context
and plan bytes plus immutable initial row/byte bounds. It extends the existing
ledger; it introduces neither another aggregate counter nor a process-local
capacity authority. This candidate is not in native0.16, core0.6, a release index
or an installed layout. Its ALTER source still requires owner UMF capture/export,
physical IDs, complete protected native composition and core browser projection.

The singleton's transaction-held exclusion permits one active reservation across
participating writers. A finalized operation clears its active slot before a
later operation in the same transaction reserves; prior retained operations and
touches remain counted. A foreign/orphan active slot is unavailable, not expired
or repaired by a new caller. No operation FK is required before insertion: the
producer reserves its own future registry storage before that registry row exists.
The observer subsequently proves exact current-operation/slot correspondence.

| Private phase | Concrete native implementation and independent check |
| --- | --- |
| Reserve | Under original head then singleton exclusion, compare complete installed layout/resource/epoch and original account/issuer authority. Derive actual assigned xid and issued ordinal; validate the complete bounded original plan. Require no existing active slot and exact complete retained-counter parity. Check proposed additions using subtraction from fixed caps before addition. Atomically set original binding/initial budgets and remaining counters, then insert the operation and consume its exact registry custody. Capture any duplicated slot bytes under the original account; reserve native slot/index/WAL overhead through the registered profile. |
| Consume | Before each registered original event, resolve the one unfinished operation and exact slot under the held exclusion. Compare full original context/plan, phase and generation; enumerate all OLD/NEW contributions. Compute actual new rows and positive custody growth, including repeated/duplicated carriers and result/generation updates. Precheck the entire event against remaining capacity and every per-row cap. Atomically transfer actual positive deltas from reserved to retained counters with canonical/touch/operation changes. Never allocate an earlier capacity lock from the observer. |
| Shrink | Independently prove exact removed byte membership before reducing retained bytes. Do not return spent growth to this operation's remaining budget; later regrowth spends remaining capacity again. Ordinary operations cannot delete retained operation/touch custody to obtain capacity. Administrative RT01–RT06 deletion remains separately governed. |
| Finalize | Verify complete original operation/contribution/result/generation scope and all required guards. Release only actual remaining reserved rows/bytes, clear all six active fields, and preserve actual retained totals. Do not subtract immutable initial budgets: consumed capacity is now retained. Finalization is pending until host commit and does not unlock the singleton. |
| Roll back | Confirm the original native operation boundary. Native rollback restores the slot, counters and every corresponding effect together; do not manually subtract again. The original host ordinal and cumulative work remain spent. Unknown containment preserves original unresolved custody and quarantines handles. |
| Check commit | Enumerate all surviving operations/touches and native capacity facts under original authority. Require no active reservation, zero remaining counters, exact independently recomputed retained totals, and complete generation/finalization/contribution coverage. An empty slot alone cannot prove a complete transaction. Never repair counters or clear a slot in a validator. |

An active slot with zero remaining rows/bytes is valid before finalization; a
cleared identity with nonzero counters or any partial identity is invalid. The
SQL uses `IS TRUE` so unknown CHECK truth cannot admit a partial binding.
Structural bounds do not prove actual xid, issuer, plan semantics or authority.
The original resource profile currently budgets operation/touch custody; adoption
must register the additional bounded slot custody/native overhead explicitly,
without silently treating duplicate bytes as free or enlarging existing caps.

Run native exact-bound/one-over and partial/null binding controls first, then
reserve before registry insertion; consume multiple rows and repeated growth;
shrink/regrow without refund; release only remaining capacity; finalize A then
reserve B; roll B back with A intact; refuse foreign/unfinished/hidden/oversized
scope; compare complete counters/bytes after every failure. Finally run enabled
observer/commit guards, early constraint checks and actual host commit/rollback
under ordinary roles and cross-connection exclusion. All producer/body schedules
remain not_run. Source schema checks alone cannot promote P1 or any acceptance
criterion; no competing UMF validator or security resolver is introduced.


## Reservation schema/source checkpoint — 2026-10-10

The reservation implementation packet now chooses an extension of the existing
singleton rather than another aggregate ledger: six nullable columns retain
actual writer/issued ordinal, complete original context/plan bytes and immutable
initial budgets. Cleared identity requires zero reserved counters; a complete
active binding may have zero remaining counters until finalization. Native
producer/observer procedures must establish authority and consume the original
remaining capacity; structural CHECKs cannot do so.

[UMF source capture](evidence/design-audit/capacity-reservation-source.json)
retains exact original ALTER source and archive/reload/export correspondence
through the owning PostgreSQL adapter. The adapter reports one declaration and
zero unhandled statements with complete=false. This is native extension custody,
not a core structural ER projection or an accepted installed model. The generated
owner export is the source executed by the native checker.

[Native size/shape evidence](evidence/design-audit/capacity-reservation-native-size-shape.json)
passes34 observations, including exact/one-over context and combined-slot byte
limits, complete/partial/null/negative bindings, zero-remaining active custody,
remaining budgets over initial limits and cleared identity with nonzero counters.
Each administrative corruption schedule rolls back and re-observes all six
original binding cells; the original two-connection ledger exclusion and complete
byte/counter initialization remain verified. The earlier26-observation receipt
and its exact before-size-controls producer remain archived.

This packet clarifies implementation: reserve future operation storage before
registry insertion; transfer actual positive deltas into retained totals; do not
refund spent growth after shrink; release only unused remaining budget; rollback
native effects/counters together without double subtraction; retain host ordinal
and cumulative work; require a complete empty-reservation and retained parity
check at commit. Additional bounded slot custody/native overhead needs original
resource registration before adoption. Actual procedures, ordinary-role guards,
physical IDs, complete generated/native inventory, source/core browser update,
security integration and installer readiness remain open. No criterion is
promoted by these structural observations.
