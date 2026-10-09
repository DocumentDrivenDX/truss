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
