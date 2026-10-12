# Truss Python delivery

Truss owns the tested embeddable Python implementation. The complete engine
package is under implementation; current public components provide local runtime lifecycle, UMF acceptance-input
preparation, selected native host transaction controls, installation footprint inspection
and assembly construction. The selected catalog runtime additionally provides
transactional installation, status, fresh catalog registration, report retrieval
and durable registration retry. Runtime 0.4 provides module-authorized scalar-string object identity reads and
rootless string object creation through a selected group provider, including
caller rollback and durable request replay. Runtime 0.5 also provides ordinary-reader
catalog metadata and exact accepted-document retrieval. Runtime 0.8 provides public
business-key lookup, and runtime 0.9 reports exact-input unchanged registration.
Runtime 0.10 accepts additional documents while preserving existing definitions.
Runtime 0.11 adds exact integer, decimal, boolean, timestamp and binary properties.
Runtime 0.12 adds bounded live object pages.
Runtime 0.14 adds public scalar object updates/deletes and ordered mixed batches.
Compiled queries, imports, receipt visibility and feed operations remain unfinished.

The supported driver baseline is stock psycopg3.3.6 binary/libpq18.6 on PostgreSQL18.6. The initial
`adopt_psycopg_host(connection)` implementation selects psycopg/psycopg-binary
3.3.6, libpq18.6 and PostgreSQL18.6 on the selected local tuple. Install the
`[native]` extra. Other wheels, servers and Lakebase remain unqualified.

Supply a caller-owned synchronous connection with an already active transaction:

```python
from truss import Ok, adopt_psycopg_host

host = adopt_psycopg_host(connection)
adopted = host.adopt_transaction()
if not isinstance(adopted, Ok):
    raise RuntimeError(adopted.error.message)
transaction = adopted.value
# The caller continues to own outer commit/rollback and connection disposal.
host.detach()
```

Idle and failed transactions refuse adoption. Keep raw aliases unused during toolkit operations; the host may commit or
roll back between calls. Before every toolkit call, the host must configure
`statement_timeout` to 1..60000 milliseconds. The initial observer and failure
cleanup depend on this native bound; an observed zero or larger value refuses
adoption. The watchdog requests cancellation and checks monotonic elapsed time
before each SQL submission; it does not guarantee hard wall-clock termination. Toolkit operation containment preserves earlier host work and timeout
settings; unresolved cleanup quarantines the connection across detach/re-adoption.
This entry point provides host adoption, not installed graph capabilities,
compiled query execution or durable commit recovery.

The pg8000 entry points below are historical experimental components, available
through `[experimental-pg8000]`; their transport hooks do not gate the baseline.

For an existing idle `pg8000.native.Connection` from version 1.31.5 over a Unix socket, use
`adopt_pg8000_host(connection)`. It attaches without database I/O and never
creates, settles or closes your connection. The connection must have completed
an actual idle command; fresh startup status, active/failed transactions,
preexisting prepared resources and changed driver methods are refused.

After attaching, make a successful idle observation through
`host.connection.run_non_lifecycle("SELECT 1")`, then call
`host.session.observe_host_resource_baseline()`, `begin()` and
`adopt_transaction()`, checking each `Outcome`. Use that original handle for
Truss savepoints. The host session owns your explicit `commit()` or `rollback()`.
Keep raw connection aliases unused while attached.

`host.detach()` restores the original driver hooks only when the connection is
idle and native work is settled. It returns false while work is pending or
driver correspondence is lost. A hook-restoration exception is retained in
`detach_failure`; explicit `detach()` retry completes restoration without
native I/O and still refuses foreign replacements. Successful detachment invalidates the old
session and permits ordinary raw connection reuse. `dispose()` closes Truss
admission while leaving the host rollback route available; it does not detach.
Construction failures retain `BorrowedHostAttachmentFailure` with original
attachment custody and a `restored` flag. Unconfirmed restoration requires host
recovery before reuse. This API supplies transaction embedding; it grants no
catalog, read or mutation authority.

## Public catalog workflow

Select `CatalogRuntimeConfiguration()` with `create_reference_assembly(config,
host)`. The returned `Ok.value` provides `install_in_transaction`,
`status_in_transaction`, `prepare_catalog`, `accept_in_transaction` and
`report_in_transaction`. Installation requires a privileged caller with no existing
`truss` namespace; it creates private owner and registrar roles and returns their
names in `PendingCatalogInstallation`. Grant the registrar role to each eligible
ordinary login person. The toolkit never commits your outer transaction.

```python
from truss import CatalogRuntimeConfiguration, create_reference_assembly, Ok

assembly_result = create_reference_assembly(CatalogRuntimeConfiguration(), host)
if not isinstance(assembly_result, Ok):
    raise RuntimeError(assembly_result)
assembly = assembly_result.value
prepared = assembly.prepare_catalog(documents)  # tuple of CatalogDocument
registered = assembly.accept_in_transaction(
    transaction, prepared, request_key="register-orders-v1",
    origin_bytes=b'{"x-action":"register"}',
)
if not isinstance(registered, Ok):
    raise RuntimeError(registered.error.message)
# Result is pending_commit. The caller settles its transaction.
host.detach()
connection.commit()
```

The current release supports one fresh scalar-string catalog with authored keys
and relationships on PostgreSQL 18.6. Preparation uses the bundled UMF producer
through Bun. Original documents are retained; accepted identities come from
native catalog rows. Registration records the authenticated session person as
actor separately from asserted origin. Exact `SET ROLE` must be `none`.

Ordinary-person catalog calls require `READ COMMITTED`; higher isolation refuses
because membership authorization must observe committed revocations. Repeating
the same request key as the same person with identical original inputs and origin
returns the original report and `replayed=True`. Changing the request returns a
conflict. Retry still requires current authorization. There are no internal retry
loops. Catalog evolution remains unavailable. The selected runtime adds module-authorized object identity reads and the create-only group provider described below.
`dispose()` closes this assembly's admission without closing or settling the host.

The catalog runtime 0.2 candidate also provides
`catalog_view_in_transaction(transaction, assembly.catalog_view_request())`.
An `Ok` contains `CatalogViewAvailable(view=...)` or
`CatalogViewUnavailable(reason=...)`. The view exposes immutable definitions,
native IDs, exact original JSON definition bytes, archived document provenance,
and ordered dependencies. It includes fields declared in other modules and
document-qualified keys and relationships. `view.original_bytes` is the complete
shared catalog-view JSON wire representation.

This profile supports complete revision-1 views; genesis, unsupported history,
and owner projections return unavailable. Readers require current registrar
membership; they need not be the person who registered the catalog. Views hold a
catalog-head share lock with no wait and require a read-write READ COMMITTED
transaction. Define smaller output budgets with
`assembly.catalog_view_request(definition_count="100", encoded_bytes="1048576")`.
Count or full-output byte overflow returns unavailable without truncation. Failed
transaction cleanup remains an error requiring host recovery. The 0.2 candidate
does not migrate an existing 0.1 installation.

Trusted installation administrators can configure document-qualified policy rows
with `configure_module_access_in_transaction(transaction, grants)`, where `grants`
is a tuple of `ModuleAccessGrant(document_id, module_id, reader_role, writer_role)`.
Modules must exist in the original accepted archives. Permission roles must already
exist as safe, distinct non-login roles without paths into protected owners or raw
Truss privileges. Role names must fit 63 UTF-8 bytes and are compared as exact text.
The method creates no roles, memberships or privilege grants.

Configuration is an exact upsert of only the supplied addresses; omitted addresses
remain unchanged and identical rows are a no-op. A batch validates before writing,
verifies native effects, and returns `pending_commit`. The caller commits or rolls
back. Role names resolve live: administrators must quiesce role replacement,
renaming and membership changes and reconfigure policy deliberately. Removal is
not implicit in an omitted address. This administration API prepares policy
metadata; business authorization and mutation capabilities remain under implementation.

The package also retains a separately pinned original UMF key-tuple producer as
an internal dependency for grouped writes. It parses original source through UMF,
preserves ordered string components, and returns exact owner receipts and tuple
bytes in bounded batches. Equal tuple bytes can occur in different documents or
Keys: native uniqueness must bind the accepted qualified Key namespace separately.
This dependency does not enable mutation or uniqueness enforcement by itself.

The [accelerated capability queue](../../docs/helix/04-build/local-runtime-installation-migration-plan.md#accelerated-capability-queue--owner-direction-2026-10-09)
prioritizes complete installation, catalog acceptance, apply/import and direct
key/edge reads, with per-person isolation and origin capture included in the
first usable Python preview. The earlier week estimates are historical; there is
no verified delivery ETA yet. Reforecast follows a complete protected ordinary-
consumer transaction on one installed profile and measured fresh install/verify.
See the plan’s forecast checkpoint for exact prerequisites and current evidence.

`inspect_installation(host.connection)` reads PostgreSQL system catalogs through
an existing public `ConnectedHost` connection. It returns an `Outcome` containing
the observed `truss` namespace presence and relation kinds in the caller's current
snapshot. It always reports readiness as `unverified`: namespace/table presence
does not prove an installed runtime, layout version or accepted catalog. It does
not read Truss table/view bodies, begin or settle a transaction, or retry. Native
failures propagate without a new recovery reference; a failed query may abort the caller's transaction, whose rollback remains the host's responsibility.

For local PostgreSQL, install the reusable `pgserver-pg18==18.6.1` wheel from
[DocumentDrivenDX/pgserver](https://github.com/DocumentDrivenDX/pgserver). Imports
remain `pgserver`; install only one pgserver distribution in an environment.
The checked-in `_profiles/local-postgres-runtime.json` selects the exact tuple.
Ordinary installs and tests use binaries and never build PostgreSQL.

```sh
python3.11 -m venv .venv
.venv/bin/python scripts/install-local-runtime.py
.venv/bin/truss-local-postgres --data-dir .local/truss-postgres-18 --probe
```

Public release `pg18.6-pgv0.8.6-r2` is published. Packaging version18.6.1
fixes quoting/URI handling for short Unix socket paths containing spaces and
apostrophes. PostgreSQL remains18.6. The macOS arm64 CPython3.11 wheel SHA256 is
`fd42f07982693e16478ed42a297890d142d22250116e08887146e690f0dd2649`.
[Patch-release CI](https://github.com/DocumentDrivenDX/truss/actions/runs/38189066679)
passes all six focused groups, including short whitespace/apostrophe lifecycle
and CLI paths. Earlier .0 receipts retain their original wheel digests. The shared installer
verifies release checksums and requires binary wheels on every setup.
Do not install upstream `pgserver` alongside
`pgserver-pg18`, and do not upgrade retained PostgreSQL17 data in place.

Reproduce the focused consumer checks with both installed wheels:

```sh
.venv/bin/python scripts/check-local-runtime-smoke.py /path/to/pgserver_pg18.whl /path/to/truss_toolkit.whl --run-id FRESH_ID
```

`scripts/install-local-runtime.py` is the shared CI/development setup command.
It resolves only released binary runtime wheels, verifies their release checksums,
refuses conflicting pgserver distributions, and replaces preliminary same-version bytes
explicitly. Missing wheels or checksum failures stop installation; no PostgreSQL
source build is attempted. Truss's own pure Python wheel may still be built.
The `Released Python runtime` CI job uses the same installer and focused installed
smoke checks on Linux x64/Python3.11. PostgreSQL compilation belongs exclusively
to the reusable pgserver repository. The .1 runtime fixes short whitespace socket paths; lifecycle and CLI checks
exercise spaces and apostrophes on all platforms.

Ordinary psycopg and pg8000 native fixture classes reuse one owned Unix-socket
cluster per worker, with fresh databases/roles and verified cleanup. Worker
sockets have unique short paths and TCP is disabled; port5432 does not contend
across those directories. Lifecycle and destructive cluster tests remain isolated.
`TRUSS_INSTALLED_SUITE_WORKERS` defaults to2 (range1–8); the optional full suite
has a default1800-second bound. Workers disable background autovacuum for explicit
NOWAIT semantic probes; this does not qualify maintenance concurrency.
The comprehensive `scripts/qualify-pgserver.py` remains available separately.
Historical17.11 receipts retain their original subset and versions; they do not
establish18.6 corpus or Lakebase acceptance.

Embed the local runtime in Python3.11:

```python
from truss import LocalPostgres

with LocalPostgres('.local/truss-postgres') as runtime:
    uri = runtime.info.connection_uri
    # Open a connection with your PostgreSQL driver. Close it before context exit.
```

The context owns only its local server lifecycle. Callers own their connections
and transactions. Exit stops the server and retains its data, including after a
caller exception. Use a new context to restart. Same-directory contexts refuse
immediately through process-local and interprocess leases. Existing postmaster
custody, nonempty non-PostgreSQL directories and incompatible major versions
refuse without automatic retry, takeover or migration. The local candidate admits
bundled18.6 with its exact reusable package identity; retired16.x packages refuse
before startup. Other platform/version
tuples still require qualification.

The experimental truss-toolkit0.0.1.dev0 wheel exposes this lifecycle component;
it does not yet expose the complete Truss engine, catalog acceptance, mutation,
query or migration APIs. Test with `python -m unittest discover -s packages/python/tests -v`.

If cleanup raises or leaves a postmaster marker, close refuses and retains the
directory lease; connection information becomes unavailable. It does not retry
automatically. The host may explicitly call `close()` again after resolving the
failure. A successful close releases custody only after the owned cleanup returns
and its postmaster marker is absent. Startup failures inside pgserver's constructor,
crash recovery and other operating systems still need separate qualification.

Already admitted exact-value conveniences are available in `truss.numeric` and
`truss.timestamp`:

```python
from truss.numeric import decimal_from_admitted_text
from truss.timestamp import timestamp_from_admitted_text

amount = decimal_from_admitted_text('12345678901234567890.123456789', 128)
assert amount.original_text == '12345678901234567890.123456789'
time = timestamp_from_admitted_text('2026-10-09T12:34:56.123456789Z', 64)
assert time.datetime_view is None  # Python datetime cannot preserve nanoseconds.
```

The caller must first admit source grammar, UMF field meaning and native domain.
These functions retain original spelling and require a caller-selected finite byte
bound; they perform host conversion only. Decimal construction ignores ambient
precision, but subsequent Decimal arithmetic follows the caller's context and is
not qualified here. Integer host input rejects bool and float. Timestamp tokens
retain their original offset/precision even when a datetime view is unavailable.
These adapters do not normalize keys or define an alternative UMF grammar or codec.

For populated local guard qualification, run
`python scripts/check-pgserver-populated-guards.py` in the local runtime environment.
It checks12 immutable row/statement refusals using explicit FK-valid administrative
fixtures under rollback. It performs no protected engine or installer publication.

Declared migration metadata planning is available experimentally:

```python
from truss.migration_planning import plan_layout_migration

result = plan_layout_migration(manifest_bytes, observation_bytes, '2.0.0')
# Inspect result.outcome: plan, no_steps or refused.
```

Inputs are immutable original numeric-free JSON bytes and a bounded target version.
Only explicitly declared complete routes are selected; no route is synthesized
from intermediate steps. Results and nested artifact views are frozen. This
function performs no database I/O, retries, installation verification or migration
execution. Even `no_steps` requires independent full installation verification.
Keep original artifact bytes separately; decoded views provide no authority.

An experimental synchronous compiler boundary is available in `truss.weft`:

```python
import weft  # Separately delivered, verified original Rust/PyO3 extension.
from truss.weft import CompilerBoundary

compiler = CompilerBoundary(weft.compile_json)
compiled = compiler.compile_request(original_weft_request_bytes)
artifact = compiled.artifact
compiler.dispose()
```

The complete original request uses Weft's frozen compile0.2 / SQL0.2 grammar,
Truss PostgreSQL target and original owner model/binding bytes. Rust owns SQL
parsing and lowering. The boundary checks byte/hash and returned context
correspondence, retains immutable original request/response bytes, and freezes
nested artifact views. Parameter values remain exact text; decimal JSON metadata
is decoded as Decimal with original spelling retained in the response bytes.
Blocked input/compiler responses return a single CompileRefusal; callback errors
propagate without retry. Disposal prevents publication and new compilation.

The callback must come from the host's verified original source/build; supplying
a function cannot prove its compiler pin. No Weft wheel is currently published or
declared as a truss-toolkit dependency. The development wheel and compiler checks
are recorded in the Python implementation handoff. A compiled artifact is not a
native execution permit: this component has no database connection or execute
method. Host obligation admission, current-person read context, exact result
decoding and complete execution/profile qualification remain unfinished.

The current development wheel contains ten Python modules, including the private
`_query_execution` coordinator. All module payloads match the installed wheel and
source. In a fresh Python3.11 environment outside the checkout, the declared local
extra resolves and all34 existing component tests pass, including four actual
PostgreSQL16.2 lifecycle tests. The qualification tuple is macOS arm64 with the
pinned dependencies above; it does not qualify other platforms or a complete
Truss installation. See the [installed-wheel evidence](../../docs/helix/04-build/evidence/design-audit/python-current-wheel-local-extra.json).

The private coordinator orders original host obligations before read acquisition,
checks context through publication and waits for cleanup before returning immutable
exact-carrier results. Its eleven installed-wheel tests use synthetic callbacks,
including asynchronous callback refusal, disposal, reentrancy and failed cleanup.
It is not a public supported query API. Public query activation still requires
original native, decoder and security services and their complete qualification.

Installation and migration administration are designed but not implemented in
this wheel. The metadata planner above cannot substitute for them. The next
integration work is to bind the original nonrewinding operation issuer, finish
mandatory native guards and assemble a complete verified installation bundle,
then exercise a registered populated migration and fresh-process recovery. See
[the Python installation/migration handoff](../../docs/helix/04-build/python-migration-installation-handoff.md)
for entrypoint contracts, connection ownership and preservation/failure gates.


A subsequent source correction rejects asynchronous compiler functions/callable
objects at construction and closes unexecuted coroutine results from synchronous
wrappers before refusal, including disposal during the callback. Six compiler
boundary source tests pass with warnings treated as errors. This correction is
newer than the recorded ten-module wheel and34-test installed-suite evidence;
that wheel remains historical. The [rebuilt-wheel receipt](../../docs/helix/04-build/evidence/design-audit/python-async-fixed-wheel.json)
verifies all ten installed payloads against current source and passes the six
compiler plus eleven coordinator regression tests outside the checkout, in the
existing local-extra environment. Native lifecycle tests were not repeated for
this compiler-only correction. No asynchronous compiler execution
or automatic retry is introduced.


The subsequent source lifecycle fix retains directory custody when pgserver's
constructor fails without returning a handle but leaves a postmaster marker.
Connection information stays unavailable and a second context refuses. Truss
neither takes over nor terminates that unknown process; the host must establish
recovery before explicitly closing again. A synthetic constructor-fault test
checks this branch without starting a native process. Marker disappearance alone
is not general process-crash qualification. This source change is newer than the
recorded rebuilt wheel and requires a later package rebuild.


The [historical installed-suite receipt](../../docs/helix/04-build/evidence/design-audit/python-current-installed-suite.json)
covers a rebuilt wheel containing both subsequent fixes. All ten installed
module payloads match that wheel/source checkpoint, and all36 component tests pass with
warnings treated as errors outside the checkout. This reuses the previously
resolved local-extra environment; it is not a new dependency-resolution claim.
Four tests exercise native PostgreSQL16.2 lifecycle; constructor fault injection
and query/compiler host controls retain their synthetic scope. Reproduce with
`scripts/check-python-installed-suite.py TRUSS_WHEEL` using that wheel's installed
Python environment. Full installation, migration execution and protected engine
qualification remain unfinished.

The [latest installed component suite](../../docs/helix/04-build/evidence/design-audit/python-accounted-core-installed-suite.json)
verifies all17 current module payloads against the rebuilt wheel and installed
package, with70 tests passing outside the checkout. It uses the reused corrected
pgserver0.1.4+truss.pg16.15 environment; four tests exercise local native lifecycle.
The new private AccountedReceiver shares BytePermitAccount, reserves maximum
header/frame and optional header/body slice payload overlap before ingress, and retains charges after failure.
Its source-pinned core path additionally reserves and precharges two downstream
copies per part. These conservative charges do not prove the copies executed.
Its accounting/fault controls are synthetic. Transport, parser, object overhead
and containment integration remain required before this becomes a supported
database adapter. Public mutation/query/installation APIs remain unreleased.

The [local accounted-driver probe](../../docs/helix/04-build/evidence/design-audit/pg8000-core-accounted-control-native.json)
uses the installed receiver's header/body path through the frozen pg8000 seam.
Five fixed controls produce ten independently expected command/ready frames on
PostgreSQL16.15. This verifies that particular payload-account integration;
the full driver and its original authority/recovery protocol remain unqualified.


The [installed console-command receipt](../../docs/helix/04-build/evidence/design-audit/python-installed-local-cli.json)
verifies a subsequently rebuilt wheel's `truss-local-postgres --data-dir PATH --probe`
entrypoint outside the checkout: two actual PostgreSQL16.2 start/probe/stop runs
reuse retained data and leave no postmaster marker. The CLI delegates to the same
LocalPostgres lifecycle and restores prior signal handlers on exit. Signal-driven
termination itself remains separately unqualified by this probe. Startup performs
no Truss installation or migration; the repository script now delegates to this
packaged implementation rather than carrying a second launcher.


The later [installed signal receipt](../../docs/helix/04-build/evidence/design-audit/python-installed-cli-signals.json)
qualifies graceful SIGTERM and SIGINT for this installed CLI on the same macOS
arm64/PG16.2 tuple. The probe waits for actual readiness, signals only its own
recorded child PID, observes exit0 and an absent postmaster marker, and restarts
the retained directory between runs. Reproduce with
`scripts/check-python-installed-cli-signals.py` in the installed local-extra
environment. This supersedes the earlier probe-only signal limitation without
claiming crash, forced-kill or complete installation recovery.


The current installed-suite and Rust delivery receipts have been refreshed for
the eleven-module wheel, now including `truss.cli`. All36 component tests pass,
and the frozen original Rust extension's five compiler cases/five transport
refusals retain full CLI correspondence. Delivery evidence now observes the
installed local-extra dependencies rather than hardcoding their absence. The
coordinator receipt is refreshed against the new delivery hash. This uses the
existing qualified local environment; no fresh resolution or complete-engine
claim is added.


The latest installed wheel contains twelve modules and passes42 component tests
with warnings treated as errors; every installed payload matches wheel/source in
the [current installed-suite receipt](../../docs/helix/04-build/evidence/design-audit/python-current-installed-suite.json).
Six synthetic admission-custody tests include refusal of deferred generator work
without executing its body. This component is not exported as a supported writer
or native confirmation factory. The ten/eleven-module checks above are historical
delivery evidence. Original driver/control/issuer integration and native SQL
correction remain open;42 component tests do not qualify installed public operations.


Run `python3 scripts/check-module-boundaries.py` from the repository root for the
Python source import gate, and `python3 scripts/check-module-boundaries-controls.py`
for its real-checker allowed/forbidden controls. CI runs the same commands. New
modules/imports require a reviewed checker map change. This AST check is scoped
to Python imports; it does not qualify native behavior or runtime object privacy.

## Python execution contracts

`ExecutionFailure`, `Ok`, `Error` and `Outcome` are public Python result contracts.
`Outcome` carries execution success/failure; semantic application/replay and
pending/committed durability remain nested capability results, not synonyms for
`ok`. A retry failure requires `whole_transaction`; commit-unknown permits only
its explicitly qualified lookup scope. Result tags cannot be supplied by callers.

`truss._host_execution` is a private synchronous adoption candidate. It exercises
host ownership and savepoint lifetime without beginning, committing, ending or
closing the host transaction. Tests qualify trusted-port behavior only. It is
not a native driver adapter or protected transaction capability: E06 original
arbitration, host-command exclusion, generation and cross-assembly custody must
be integrated and qualified before publication. Unresolved original custody
blocks re-adoption and survives executor disposal. No public catalog/mutation/
feed/ACK or ReferenceAssembly is supplied by this iteration.

The private `_operation_arbitration` component supplies one registered operation
registry per exact executor, shared across assembly registrations. It retains
original attempts/leases, terminal decisions and uncertainty across admission
closure. Completion verification runs outside the transition lock and must
return correspondence to the immutable original registry/assembly/attempt/lease/
transaction context. Root state publishes atomically; completed verifier results
survive publication faults. Explicit reconciliation may restore a quarantined
slot without changing original evidence or admitting concurrent verification.
Confirmed transaction termination can close operation resources while retaining
commit-outcome recovery separately.

Its counters reserve encoded metadata/completion capacity and retain terminal
attempts. These checks do not qualify total Python heap or native resource usage.
The completion verifier is a required trusted host integration, not a supplied
native implementation; producer/ledger correspondence, native command exclusion
and driver generation recognition remain required before E06/native adoption
publication. No public capability or runtime support claim follows from these
component tests.

The private `_native_pg8000` slice wraps cooperative host calls on an original
pg8000 1.31.5 native connection after an explicit host idle probe. It captures
bounded original CommandComplete/ErrorResponse/ReadyForQuery evidence across
all cycles of a complete driver call, guards prepared run/close, and preserves
native completion when the driver raises the original native context error.
Transport failure after an earlier ready cycle quarantines the boundary.
Calls through retained raw/core aliases, cancellation, driver mutation and
arbitrary host concurrency are outside this profile; observed unowned responses
quarantine after effects and do not establish effect-free refusal. Capture limits
cover retained events only, not driver buffers or total resource usage. Operation
release here establishes exclusion only, not verified native cleanup. Typed
lifecycle/generation history, arbitration completion production and public host
adoption remain required; these components do not yet provide a consumer API.

The private `_native_transactions` component now supplies typed host lifecycle
controls, original issuer generations, native-ended retirement, exact quoted
savepoint custody and shadowing, and a port for the private HostExecutor. The
host must hold one original boundary operation token through the entire executor
call, including observation/control/post-observation and Python publication;
ports refuse use outside that scope. Ended ports cannot retarget a later
transaction. Host rollback/release/shadowing invalidates or hides executor
savepoints before their next control is submitted. Actual probes use pg_catalog
functions and nonallocating xid observation. Cached failed-state data supplies
original cleanup correspondence only, never fresh authority or role evidence.
Native controls and candidate custody survive post-native publication faults;
such faults quarantine rather than guess cleanup. This is native component
composition, not public adoption, protected capability admission or completed
arbitration/resource verification.
The original issuer now reserves monotone canonical positive uint64 epochs before
fresh BEGIN/chain submission, burns uncertain reservations, and refuses exhaustion
before SQL. Repeated BEGIN preserves its active epoch even at exhaustion. The private `_native_adoption` component now reserves original-generation claims
across separate executors before observation SQL. Exact probe and call revision
correspondence prevent unrelated observations from supplying adoption evidence.
Competing claims refuse before SQL; uncertainty retains original custody, while
known profile mismatch permits an exact refund. Already published outcomes
reconcile lost replies. Custody survives executor disposal and garbage collection.
Retention bounds cover claim counts, not total heap usage. Shared arbitration,
native resource-ledger verification and containment/recovery remain required
before exposing public host adoption.


The private `_native_arbitration` composition now binds the original admitted
lease/context, transaction generation and native operation guard to one retained
session. Every submitted call is registered before native invocation; original
completion survives later lifecycle/publication failure. Pending binding reserves the guard before registry acquisition, including
lost acquisition replies and session-allocation faults. A service lock preserves sessions across
concurrent connections. Disposal and exact call-count exhaustion refuse before
submission without changing existing resource state.

Prepared wrappers and resource records are retained before preparation SQL.
The selected driver supplies the exact statement-name argument before PARSE;
original ParseComplete and CloseComplete acknowledgements distinguish native
creation/closure from driver return and wrapper publication. A creation followed
by Describe failure and a closure followed by bookkeeping failure retain those
native facts. False acknowledgement flags mean unconfirmed, never proven absence.
Only supported prepared calls after attachment are tracked; pre-existing host
resources and driver buffers remain unqualified. The session locator identifies
custody and is not a completion artifact. A completion attempt freezes ordinary
submission while preserving in-flight calls and unresolved ownership.
All failed creation paths conservatively quarantine; there is no qualified
known-failed resource recovery yet. Retention limits count original records,
including closed records, and do not qualify heap or driver buffer usage.

Without a registered original completion producer, successful arbitration
release remains disabled. Observed prepared-resource closure alone cannot prove
buffer closure, caller-state restoration or containment.

Iteration 8 adds a private `_native_operation` producer for exactly
`SELECT :value::pg_catalog.text` on the pinned synchronous driver profile. It
preserves Unicode/NULL values, owns bounded response frames and original result
contexts, and reserves a separate cleanup lane. Explicit portal/statement close
acknowledgements and actual caller-state/savepoint restoration precede original
completion publication and atomic ownership handback. Native 22021 failures are
contained without committing or rolling back the host transaction. Lost completion
or handback replies reconcile original retained outcomes without replay.

This profile accepts no arbitrary SQL, DML, streams or custom codecs. Its native
tests use administrative connections; they provide no protected person/origin
qualification. Buffering/notices/notifications owned by the host connection are
preserved; counts and conservative payload charges are not a total heap bound.
Public adoption, ReferenceAssembly and the catalog-to-feed workflow remain open.
See [iteration 8 evidence](../../docs/helix/04-build/evidence/python-contracts-iteration8.json).

## Draft public group contracts

`truss.contracts` supplies immutable exact-value, profile and document-qualified
identity carriers. `truss.groups` supplies the grouped-operation input/result
carriers and synchronous `GroupCapability` Protocol, including request-free
return narrowing. The package includes `py.typed`; these modules provide types
and shape checks, not a callable mutation provider or an adoption factory. See
[the consumer mapping and limits](../../docs/helix/04-build/python-group-contracts.md).

## Draft import contracts

`truss.imports` preserves exact indexed partial progress, pending/unknown batch
durability and the full import result union. Its bounded local consistency check
rejects duplicate indices, incorrect batch membership, invented counters and
execution-incompatible dispositions. It does not execute imports or prove
commit/rollback. See [the import mapping and limits](../../docs/helix/04-build/python-import-contracts.md).

## Prepare original UMF for catalog registration

`from truss import CatalogDocument, prepare_acceptance, PreparationRejected`
exposes original UMF preparation. Supply a tuple of `CatalogDocument` values
(document ID, revision, exact UTF-8 JSON bytes) and `configuration` as UTF-8
AcceptanceInput JSON containing explicit layout, acceptance, validator, support,
binding, policy and transform selections, without `interfaceVersion` or
`documents`. The function returns `PreparedAcceptance.input_bytes` for subsequent
catalog admission, plus document-qualified declarations, original observations
and exact archived source carriers. `input()` returns a fresh dictionary.

The installed wheel bundles the original committed UMF producer and the existing
Truss preparation route. This release requires Bun 1.4.2 on PATH, or a trusted
host-configured `bun_executable` path. Missing runtime or altered producer assets
raise `PreparationRejected` with a finite reason. No database is opened. Selected
installation profiles are unverified, and preparation produces no accepted IDs,
catalog report, registration success or readiness. Catalog acceptance remains
unfinished. Exact source bytes are preserved; interpreted observations retain
the original UMF producer's supported semantics and diagnostics.

A preparation-only example with explicit, unverified selections:

```python
import json
from truss import CatalogDocument, prepare_acceptance

# Replace these selections with your deployment's registered profile pins
# before catalog admission. They are not installed by preparation.
def pin(name):
    return {"identity": name, "version": "example", "sha256": "0" * 64}

configuration = {
    "layoutProfile": pin("layout"),
    "acceptanceProfile": pin("acceptance"),
    "validatorProfile": pin("validator"),
    "supportProfile": pin("support"),
    "binding": {"state": "absent"},
    "policy": {"unknownEndpoint": "reject", "loss": "strict",
               "profile": pin("policy")},
    "transforms": [],
}
source = json.dumps({"umf": "0.7.0", "id": "inventory",
                     "vocabularies": {}, "extensions": {}, "modules": []}).encode()
prepared = prepare_acceptance(
    (CatalogDocument("inventory", "r1", source),),
    json.dumps(configuration).encode(),
)
assert prepared.provenance.installation_profiles_verified is False
# prepared.input_bytes is input for future catalog admission, not a receipt.
```

## Private native catalog staging

`truss._catalog_staging.stage_new_catalog` is an administrative component, not a
supported registration API. It consumes an original `prepare_acceptance` result
and an already admitted caller transaction on a trusted pg8000 native-style port.
It stages original documents, records, fields, keys and relationships using real
native allocations, then checks complete native/source correspondence and returns
an immutable provisional inventory. The selected absent-binding storage profile
uses the existing ADR-002 D4 JSON default; bindings and transforms require their
registered interpretation and currently refuse. Origin uses strict numeric-free
JSON and passes its original UTF-8 unchanged.

The host retains transaction ownership. A failed local operation rolls back its
savepoint; failed cleanup retains both failures with containment unconfirmed.
Ordinary-person admission, complete acceptance reports, finalization and public
installation remain unfinished. No accepted revision is published, and the
unconditional native commit barrier remains in place. Native tests load the
retained SQL explicitly; the Python wheel does not install or bundle that SQL.

## Private catalog report integration

The private `stage_catalog_report_basis` route composes original owner evidence
with actual native catalog allocations on the caller's savepoint. The selected
fresh-graph administrative profile requires Read Committed, takes native SHARE
locks without waiting, and includes the empty partitioned journal root. Existing
rows, uncovered topology, prior graph writes and competing writers refuse.
The basis retains exact owner bytes and full native source bytes, and currentness
checks reject changed effects even when a generation counter is reused.

This is report preparation, not accepted report publication. Missing report fields
and partial extension qualification are explicit. Successful public UMF preparation
remains usable when optional report evidence is unavailable. This legacy private
profile does not provide public registration or installation. The separate public
catalog runtime above provides those operations; apply/read remains unfinished.


## Selected host transaction entry point

Install `./packages/python[experimental-pg8000]` for the historical pg8000 1.31.5 Unix-socket
route. Base package import does not load pg8000. This factory opens a fresh
connection; adoption of an existing arbitrary driver connection remains unfinished.

```python
from truss import connect_pg8000_host, Ok

host = connect_pg8000_host(user="postgres", database="postgres",
                           unix_sock="/path/to/.s.PGSQL.5432")
try:
    assert isinstance(host.session.observe_host_resource_baseline(), Ok)
    assert isinstance(host.session.begin(), Ok)
    adopted = host.session.adopt_transaction()
    assert isinstance(adopted, Ok)
    # The host owns transaction settlement. No graph capability is granted.
    assert isinstance(host.session.rollback(), Ok)
finally:
    host.close()
```

Host lifecycle controls share one mediator; raw/dynamic lifecycle SQL violates
its cooperative contract. `run_non_lifecycle` is an explicit trusted host utility,
not the exact Truss query interface. Known idle/capacity/failed-state savepoint
refusals preserve rollback; actually submitted control errors may retain unresolved
custody. Do not treat cleanup closure as server rollback evidence.

With `ReferenceAssemblyConfiguration`, `create_reference_assembly` selects the
legacy `INERT_ASSEMBLY_PROFILE`. The catalog and inspection configurations select
their separate public providers.
It captures immutable configuration and original service registrations without
calling host services. Capability selectors return unavailable and configured
readiness remains unverified. Assembly disposal does not dispose the shared host
executor/session. Omitted configuration fields use `truss.contracts.ABSENT`.
This entry point is composition groundwork for install/register/apply/read, not
a usable graph implementation.

### Explicit PostgreSQL 18.6 host profile

The current integration target can be selected explicitly for a caller-owned
psycopg 3.3.6 binary connection using libpq 18.6:

```python
from truss import PsycopgProfile, adopt_psycopg_host

host = adopt_psycopg_host(connection, profile=PsycopgProfile(server=180006))
```

Only the exact selected tuple is accepted. There is no automatic version
fallback. The default profile selects PostgreSQL18.6. Retired16.15 packages are rejected
before embedded startup; earlier receipts retain their original historical scope.
Graph capabilities still require their separate scoped native qualification.
The host owns transaction start/end, connection lifecycle and pooling. Truss
does not change PostgreSQL 17's transaction_timeout; native timeout termination
retains the original failure, quarantines the connection and refuses reuse.

## Public object identity read

After registration, an installation administrator configures module access using
`configure_module_access_in_transaction`. This grants only schema usage and
execution of the protected reader to the selected module roles. The host grants
people membership in those roles; readers need no catalog registrar membership.

```python
from truss import Ok, ObjectFound

result = assembly.get_object_in_transaction(
    transaction, document_id="orders", module_id="sales",
    record_id="Order", object_id=123,
)
if isinstance(result, Ok) and isinstance(result.value, ObjectFound):
    order = result.value.object
    print(order.id, order.version, dict(order.values))
```

The `truss-python-scalar-object/0.1` result uses authored document/module/Record
addresses, native integer identities, versions/revisions and exact UTC microsecond
timestamps. `values` and `retained` are immutable tuples of name/value pairs:
strings are Python `str`, explicit null is `None`, and absent values have no pair.
This is an explicit scalar-string profile, not the draft historical `DirectRecord`
definition-pin carrier. It supports rootless JSON-home objects. Unsupported
ownership, row-home content, structured/numeric values or unknown properties
refuse rather than disappearing from the result. Keys and pages follow separately.

An `Ok` contains `ObjectFound`, `ObjectNotFound`, `ObjectReadInvalid`, or
`ObjectReadUnavailable`. Wrong-module and missing selections both return not-found.
Losing the sole role that grants facade execution returns an execution error;
unsafe caller contexts and unresolved transaction cleanup also remain errors.
Authorization uses current recursive native role membership before observing the
object and again before returning it. Calls require READ COMMITTED and the
caller-owned read-write transaction used by this installed profile; the toolkit
never commits, rolls back the outer transaction or retries. `maximum_bytes`
defaults to 1 MiB and can be selected from 1 byte through 16 MiB.

Runtime 0.3 requires a fresh installation; upgrading earlier candidates is not
implemented. Accepted catalog rows are protected from ordinary callers; trusted
administrative maintenance requires quiescence. Native reader fixtures seed rows
administratively and qualify reads only. Public grouped mutations remain the next
implementation milestone.

## Public create-only group provider: runtime 0.4

This candidate requires a fresh installation on the qualified PostgreSQL 18.6
profile. A caller supplies the original accepted UMF documents and selects
`assembly.groups(assembly.group_selection, documents=documents)`. The returned
`GroupCapabilityAvailable.capability` implements `GroupCapability`; its operation
is `apply_in_transaction(tx, input, request)`. The same operation is available on
the live assembly. This is the `CatalogRuntimeConfiguration` factory route.

Obtain the native profiles and request scope with
`assembly.group_context_in_transaction(tx)`, and obtain an accepted type pin with
`assembly.get_type_reference_in_transaction(tx, document_id=..., module_id=..., record_id=...)`.
Build `CreateObject` operations using logical `AuthoredValue` string/null values
and `RootlessOwnership`; use `context.input(operations, asserted_origin)` and
`context.request(your_idempotency_key)`. No public key codec calls are required.

A successful `GroupSuccess` contains `AppliedPending`: the host still owns commit.
Read the returned identity in the same transaction, or detach and commit the
connection, adopt a new transaction and retry the identical input/request. The
latter returns `CommittedReceiptReplay` with the original result and no new object
or journal event. A same-transaction retry returns `SameTransactionReplay`.
Changing the input under a request key refuses. `RequestNone()` creates without a
retry receipt. Dry-run follows this same path and rolls back the caller transaction.
The request fingerprint is the retained profile's duplicate-free input UTF-8 byte
hash, distinct from earlier proposed framed canonical fingerprints.

Current writer membership is required for every module, including on replay. The
authenticated PostgreSQL session person is recorded separately from asserted
origin, such as `x-action`. Roles reachable through SET/INHERIT/ADMIN paths must also lack
elevated or raw Truss access, including NOINHERIT/SET memberships. The supplied transaction remains READ COMMITTED and read-write.
There are no internal retries. Unsupported ownership, relationships, numeric or
structured values, and shapes requiring mandatory relationships refuse.

The create provider stores the complete native objects, exact key membership and
reservations, journal events and optional request receipt atomically. It does not
activate the full feed/history provider. Business-key lookup, updates/deletes,
preconditions, explicit unauthorized-person result carriers, receipt visibility,
imports, relationship reads, full Weft execution and Lakebase remain outstanding.

Current deployment dependencies: installation and module-access configuration
require a superuser and permission to create the private owner/registrar roles.
They are privileged provisioning operations, separate from ordinary application
registration and writes. This installer is not yet qualified for managed systems
without superuser access. Registration preparation currently needs Bun; the
create-only provider also runs the bundled UMF key producer through Bun.
Applications using those paths must include Bun today. A build-time preparation
route or Python-compatible producer is future work, not an existing deployment
claim. The checked driver/server tuple is psycopg3.3.6 binary/libpq18.6 with
PostgreSQL18.6; Lakebase requires an actual platform privilege, install, transaction
and public workflow qualification.

## Ordinary-reader catalog and accepted source: runtime 0.5

On the live assembly, `reader_catalog_in_transaction(tx)` returns a
`ReaderCatalog` containing only modules readable by the current person. Modules
are qualified by document ID and module ID, with accepted source revision/digest,
native types, properties, ordered key property IDs and relationships. This is an
authorized metadata projection, separate from the registrar's complete catalog
view. Dependencies on unreadable declaration modules are excluded; relationships
are included only with complete visible endpoint/key/association scope. Empty
authored modules participate in access checks and may appear with empty lists.

`accepted_document_in_transaction(tx, document_id=...)` returns an
`AcceptedDocument`: exact original `content` bytes, SHA256, source
`document_revision`, source `artifact_identity`, native `catalog_revision` and
`registration_id`. Source revision is caller-provided (`r1`, a content digest, or
another application version); artifact identity defaults to the document ID.
Registration ID is Truss's native UUID for the acceptance, not a source digest.
The full document is returned only when every declared module is readable. A
missing or unreadable document yields the same `CatalogRefused(code='unauthorized')`
without source bytes. Source is never silently redacted.

These calls return `CatalogInvalid` for invalid selections/limits and
`CatalogUnavailable` for unsupported profile, resource, observation or absent
installation. Native transaction retry/unusable errors remain `Error` outcomes.
This typed mapping currently covers the new reader calls; the older registration
and report calls still need their R13 result mapping.

Current module membership is rechecked before returning. Limits refuse rather
than truncate. Runtime 0.5 required read-write READ COMMITTED; runtime 0.6 adds the
read-only support described below.
Runtime 0.5 requires a fresh installation and does not upgrade 0.4 installations.

## Public reads on read-only transactions: runtime 0.6

`get_object_in_transaction`, `reader_catalog_in_transaction` and
`accepted_document_in_transaction` support an actual READ COMMITTED read-only
transaction. Supply the already active transaction with the matching adoption
mode:

```python
from truss import Ok, adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration

connection.execute("BEGIN READ ONLY")
host = adopt_psycopg_host(connection)
adopted = host.adopt_transaction(access_mode="read_only")
assert isinstance(adopted, Ok)
assembled = create_reference_assembly(CatalogRuntimeConfiguration(), host)
assert isinstance(assembled, Ok)
catalog = assembled.value.reader_catalog_in_transaction(adopted.value)
# The caller still settles the transaction.
host.detach()
connection.rollback()
```

The native transaction mode determines whether reads use row locks. Read-only
reads issue no writes and recheck current person/module/dependency authorization
before returning. Object lookup re-reads current policy role names, so replacing
a module policy while an object is buffered cannot authorize against old roles.
The outer transaction stays read-only after a contained refusal. Writers remain
read-write operations. READ COMMITTED and the current immutable revision-1
catalog restrictions remain; this does not add read-only support to the registrar
complete-view facade or group type-reference helper. Runtime 0.6 requires fresh
installation; candidate upgrades remain unfinished.

## Typed catalog failure codes: runtime 0.7

Registration, reports, complete catalog views and status retain their existing
`Error(ExecutionFailure(...))` result shape. Known catalog refusals additionally
set the optional `catalog_code` field, without changing `code`, `sql_state`,
`message` or `retry_scope`:

```python
from truss import Error

result = assembly.accept_in_transaction(tx, prepared, request_key="register-model")
if isinstance(result, Error):
    reason = result.error.catalog_code  # typed code; never parse message prose
    if reason == "unauthorized":
        print("Registration refused")
```

| Code | Meaning |
| --- | --- |
| `unauthorized` | Native permission/person check refused the call. |
| `invalid_input` | Known preparation, request, origin or revision validation failed. |
| `request_conflict` | The same registration request key was reused with different original input. |
| `unsupported_profile` | Unsupported preparation, transaction or installed-release profile, including the current fresh-catalog-only limitation. |
| `resource` | A supported native resource limit was exceeded. |
| `observation` | A required nonblocking lock could not be obtained. |
| `installation` | A required runtime schema, function or table is absent. |

`catalog_code=None` means no catalog classification was made. Coverage is
deliberately non-exhaustive: transaction admission, retry, cancellation, unknown
commit, decoder/integrity failures and a missing report for an otherwise valid
revision retain their original error fields. Inspect the ordinary execution code
for transaction recovery. Unrelated native uniqueness violations remain
unclassified; the request-conflict branch alone uses native state `P1001`.
The new reader methods retain their existing typed result carriers. This does
not yet add typed group authorization failures or invalid-input paths.

The native conflict-state change is pinned as runtime 0.7 and currently requires
a fresh installation. Earlier candidate upgrades remain open.

## Business-key lookup: runtime 0.8

`lookup_key_in_transaction` resolves an authored UMF key to the same complete
`ObjectFound.object` returned by identity lookup, including native `id` and current
`version`. Supply key components in the key's authored field order:

```python
result = assembly.lookup_key_in_transaction(
    tx, document_id="customer-model", module_id="customers",
    record_id="Customer", key_id="primary", values=("customer-123",),
)
```

The assembly obtains the accepted original document through the ordinary-reader
source API and uses the bundled UMF encoder internally. No public codec calls are
required. If the application already holds the exact accepted document, pass
`original_document=source_bytes`; native equality checks still bind it to the
accepted source. This also supports a reader of a subset of a multi-module
document when the application supplies its already-known source. Every key-field
declaration module must still be readable. Bun remains required for this path.

This string-key profile supports primary and alternate keys, composite authored
order, Unicode and empty string values. Unknown native key selections and missing
data return `ObjectNotFound`; wrong arity or source bytes are invalid. Owner
encoding failures never become `not_found`. Input/output limits and a bounded
indexed route query refuse excessive work; the route examines at most 10,001
candidates and refuses above 10,000 rows or 16 MiB of candidate bytes. Full
namespace and key bytes decide equality, and duplicate/inconsistent memberships
are integrity failures. The namespace includes the actual installation, source
epoch, native type/key and original definition pin. Reservations are not objects.

Lookup creates no route, guard or reservation. It supports adopted read-only and
read-write READ COMMITTED transactions; read-write lookup takes a nonblocking
object read lock. The returned record is verified against the requested key, with
current record and key-field permissions rechecked before publication. The
profile remains rootless/string-only and revision 1; pages, broader value types
and catalog evolution remain unfinished. Runtime 0.8 currently needs fresh install.
### Public object updates and deletes (runtime 0.14 candidate)

Use the same `assembly.apply_in_transaction` or selected `GroupCapability`
provider for `CreateObject`, `UpdateObject` and `Delete(operation="delete_object")`.
`StoredObjectReference` targets the exact `TypedIdentity` returned by a create;
`AliasObjectReference` targets a prior create in the same batch. Operations run
in order. `expected_version` checks that operation's current intermediate version.

```python
from truss.groups import UpdateObject, StoredObjectReference, AuthoredValue
from truss.contracts import TextValue, MapValue

context = assembly.group_context_in_transaction(tx).value
change = UpdateObject(
    target=StoredObjectReference(identity=created.identity),
    set=(AuthoredValue(name="title", value=TextValue(kind="string", text="Revised")),),
    unset=(), expected_version=created.version,
)
result = assembly.apply_in_transaction(
    tx, context.input((change,), MapValue(entries=())), context.request("edit-123"),
    documents=accepted_documents, bun_executable="bun",
)
# The caller commits or rolls back its connection.
```

Updates return `Changed` or exact `Unchanged`; deletes return `Deleted`.
One changed operation increments one version. No-ops preserve timestamps,
version and journal, and request-enabled no-ops remain replayable. Set/unset
preserves exact scalar spelling and absent-versus-null meaning, including
retained scalar values. Business-key changes use UMF's encoder; old reservations
remain, and unchanged keys remain owned by the same object.

The provider currently supports rootless scalar JSON-home objects. Deletes
refuse incident edges and owned dependents. Ownership changes and edge operations
remain unavailable. Stale versions, missing targets, dependent objects, invalid
values and key conflicts return `GroupFailed` with stable diagnostic codes.
Any failed operation rolls back the entire group within the caller's transaction.
Dry-run uses the same call followed by caller rollback. Retry with the original
request and input returns the original result after later updates or deletion;
current owner authorization is still required. Internal native progress handles
are private composition details and cannot be used to commit incomplete work.

Runtime 0.14 requires a fresh installation until migrations are implemented.

### Changed-document scalar refusal (runtime 0.13 candidate)

`accept_in_transaction` returns `Ok(CatalogAcceptanceRefused(...))` when an
incoming required scalar field is missing/null on existing objects, or existing
values fail its scalar-family rule. Each `CatalogCompatibilityViolation` names
the document, record module/ID, field module/ID, stable rule (`property.required`
or `property.scalar_type`) and exact integer `affected_object_count`. Counts are
per field/rule and may overlap. The refusal names the current revision and
publishes no registration, accepted report or catalog/data changes. The caller's
transaction remains usable. Exact original retry/unchanged handling runs first.

Counts require current read-or-write permission for the record and field modules;
a registrar without that permission receives `unauthorized`, without counts.
Other changed-document cases remain `unsupported_profile`: passing these scalar
checks does not yet enable compatible evolution, retirement or transforms.
Runtime 0.13 currently requires a fresh installation.

### Exact-input unchanged registration (runtime 0.9 candidate)

`accept_in_transaction` returns `CatalogRegistration` for a new accepted catalog
or its original request retry. A new request key for exactly the current accepted
input returns `CatalogUnchanged`, with `outcome="unchanged"`. Its `revision`,
`registration_id` and `report_bytes` identify the original accepted registration.
Its `request_key`, `actor` and `asserted_origin_bytes` describe the current request;
they do not replace the original report's actor or asserted origin.

Both calls remain inside the caller's transaction (`status="pending_commit"`).
An unchanged request stores a durable request alias when the caller commits,
without adding a catalog revision, report, archive or business journal event.
Repeating its exact input and origin returns `CatalogUnchanged(replayed=True)`;
reusing the key with different source/input or origin refuses with
`catalog_code="request_conflict"`. Current registrar authority is required on
retry and again at commit for a newly recorded alias. Rollback removes that alias.

The equality profile compares original input, archive, declarations and retained
source bytes. It does not claim semantic equivalence of rewritten documents.
Later documents and changed definitions still require the pending lifecycle
implementation. This candidate requires fresh installation.

### Additional documents (runtime 0.10 candidate)

Prepare the new documents and call `accept_in_transaction` on the caller's
transaction. New document IDs append at the next catalog revision; they do not
replace existing definitions. Multiple registrations may share one transaction.
Commit publishes them together, and rollback removes all their effects.

Existing type/property/key/relationship IDs and original definition pins remain
stable. Current views include all accepted documents; reports for earlier
registrations retain their original bytes. Exact repeats of an earlier accepted
input can return `CatalogUnchanged` even after another document was registered.

Old objects remain readable and old durable group receipts replay unchanged.
New creates and journal events use the current revision. `AcceptedDocument`
reports both `catalog_revision` (the observed current head) and
`source_catalog_revision` (the revision that accepted those exact bytes), plus
the original `registration_id`. A read-only observation whose head advances
during publication returns unavailable with reason `observation`.

The complete-view and mutation profiles are version 0.2. Obtain their current
pins through the assembly; old profile requests refuse. Preparing another
document does not discard the same assembly's previously accepted source cache.
Fresh assemblies should pass their caller-known original documents explicitly
to grouped writes; native code checks those sources against the accepted archives.

The cumulative catalog limits are 512 documents, 65,536 definitions and a 16MiB
native expected image, with ordinary operation deadlines. Changes to an existing
document still refuse as `unsupported_profile`; compatible evolution and exact
non-string values remain unfinished. This candidate requires fresh installation.

### Exact scalar properties (runtime 0.11 candidate)

Use the existing value contracts when constructing `AuthoredValue`:

```python
from truss.contracts import TextValue, BooleanValue

integer = TextValue(kind="integer", text="9007199254740993123456789")
decimal = TextValue(kind="decimal", text="1.2300e+1000")
flag = BooleanValue(value=True)
timestamp = TextValue(kind="timestamp", text="2024-02-29T23:59:59.123456789+05:30")
binary = TextValue(kind="binary", text="AP8=")  # bytes 00 ff, canonical base64
```

Scalar object reads return strings, `None`, booleans and `TextValue` instances
for the four exact textual families. Stored values and journals preserve the
original numeric tokens and timestamp offsets/fractions. Truss does not round
through float, database numeric or timestamp projections. Unknown retained scalar
values use the same representation. Business keys remain string-only in this
profile, and asserted origin remains a string/null map.

Integers accept JSON integer tokens; decimals accept JSON number tokens, including
exponents and original trailing zeros. Timestamp support accepts valid Gregorian
years 0001..9999, seconds 00..59, explicit offsets or Z, lowercase t/z, arbitrary
fractional digits and unknown offset -00:00. Leap seconds refuse. Binary requires
canonical padded base64; empty binary is valid. Family mismatches and malformed
values refuse before object/journal effects. Facets, structured values and broader
nullability/cardinality remain unfinished. Obtain the updated value/mutation pins
through the assembly. Fresh installation is required.

### Live object pages (runtime 0.12 candidate)

```python
result = assembly.page_objects_in_transaction(
    transaction, document_id="model", module_id="orders", record_id="Order",
    limit=100, cursor=previous_page.continuation if previous_page else None,
)
```

An `ObjectPage` contains complete `ScalarObject` values, the observed catalog
revision and `continuation` (`ObjectPageCursor` or `None`). Authorized empty
types return a terminal empty page. Records use ascending native ID order,
continuing after the last returned record. Read-only caller transactions work.

The cursor binds the qualified selection, installation, source epoch, release,
type/definition pin and catalog revision. A stale binding returns
`ObjectReadUnavailable(reason="context")`. Malformed/wrong-selection cursors
return `ObjectReadInvalid`. The cursor is unsigned routing data; editing a valid
position does not grant access. Current permissions are always checked. Role
revocation may return a native permission failure when function EXECUTE is also
removed. A page whose buffered observation loses authority is not published.

Limits are 1..1000 records and 1..16MiB for the complete encoded page, including
metadata and continuation; cursors are bounded to 64KiB. Oversized pages return
unavailable/resource, without truncating values or returning a partial page.
Reduce the page size explicitly to fit individual large records.

These are live reads. Separate pages do not share a frozen data snapshot, and
native ID order does not establish commit order or exactly-once enumeration.
Full DirectRecord/relationship/traversal and compiled-query profiles remain
unfinished. This candidate requires fresh installation.
