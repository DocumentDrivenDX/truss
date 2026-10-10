# Truss Python delivery

Truss owns the tested embeddable Python implementation. The complete engine
package is under implementation; current files provide the pinned local runtime
candidate, not released mutation/query/installation APIs.

The [accelerated capability queue](../../docs/helix/04-build/local-runtime-installation-migration-plan.md#accelerated-capability-queue--owner-direction-2026-10-09)
prioritizes complete installation, catalog acceptance, apply/import and direct
key/edge reads, with per-person isolation and origin capture included in the
first usable Python preview. The earlier week estimates are historical; there is
no verified delivery ETA yet. Reforecast follows a complete protected ordinary-
consumer transaction on one installed profile and measured fresh install/verify.
See the plan’s forecast checkpoint for exact prerequisites and current evidence.

For local PostgreSQL:

```sh
python3.11 -m venv .venv
.venv/bin/pip install './packages/python[local]'
.venv/bin/truss-local-postgres --data-dir .local/truss-postgres
```

The installation command uses the repository root; the installed `truss-local-postgres`
command runs without the checkout. Stop with Ctrl-C; data survives. `--probe` starts,
checks readiness and stops. This component uses pgserver0.1.4 with its actual
bundled PostgreSQL16.2 on the qualified macOS arm64 tuple. It performs no Truss
installation or migration. Use a host-supplied connection for external PostgreSQL;
pool configuration/operation belongs to the host.

The explicit corrected candidate `pgserver==0.1.4+truss.pg16.15` is now accepted
by LocalPostgres only when the native server reports16.15. RuntimeInfo and CLI
output retain that actual package version. The paired published0.1.4/16.2 check
remains separate; arbitrary package/server versions refuse. The corrected wheel
is a private macOS27 arm64/Python3.11 build, not a published dependency. For that
candidate, select the independently verified corrected wheel explicitly with the
base Truss package and lifecycle dependencies. The `[local]` requirement
`pgserver==0.1.4` also accepts `0.1.4+truss.pg16.15`; it does not select or exclude
the private candidate. Use an explicit artifact path and verify the installed
package and actual server versions:

```sh
.venv/bin/pip install ./packages/python fasteners==0.20 platformdirs==4.12.4 psutil==7.2.2 /path/to/admitted/pgserver-0.1.4+truss.pg16.15-cp311-cp311-macosx_27_0_arm64.whl
.venv/bin/python -c 'from importlib.metadata import version; assert version("pgserver") == "0.1.4+truss.pg16.15"'
.venv/bin/truss-local-postgres --data-dir .local/truss-postgres-corrected --probe
```

The wheel path is a placeholder for the separately admitted private artifact,
not a published download or a clean-install qualification claim. Verify its
original hash/platform before installation; the retained wheel receipt is linked
from the runtime plan. Check the actual CLI serverVersion16.15 as well as package
metadata. A fresh `[local]` installation with only the public index available
uses published0.1.4/16.2; an already installed matching local build also satisfies
that requirement. Do not infer replacement or candidate selection from the
public equality pin. The [installed matcher evidence](../../docs/helix/04-build/evidence/design-audit/python-local-runtime-dependency-selection.json)
checks these version matches only, not index resolution or installation.
Neither tuple installs Truss or qualifies complete R4/R5 enforcement.

For corrected-candidate development, use the explicit repository constraint:

```sh
.venv/bin/pip install --no-index --find-links /path/to/verified/wheels --constraint packages/python/constraints/local-corrected.txt './packages/python[local]'
```

The wheelhouse must contain the separately verified corrected pgserver and the
three pinned lifecycle dependency wheels. The exact local-version constraint
excludes public pgserver0.1.4; package version still does not prove original native
payload correspondence. The current rebuilt candidate has clean offline resolver,
payload and132-test evidence in the runtime plan. This optional development
constraint does not publish the private wheel or change the default public extra.


See the [installation and migration execution plan](../../docs/helix/04-build/local-runtime-installation-migration-plan.md)
for the complete delivery scope and independent acceptance scenarios.

Rollback-only native profile checks (same environment):

```sh
.venv/bin/python scripts/check-pgserver-layout.py
.venv/bin/python scripts/check-pgserver-adjuncts.py
.venv/bin/python scripts/check-pgserver-umf-structure.py
```

Each creates its own disposable server and rolls back all review DDL. The last
compares the UMF schema-browser model with actual columns and FK mappings; it
is not a complete installer or migration verifier.

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
bundled16.2 or the explicit corrected16.15 candidate; other platform/version
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
before SQL. Repeated BEGIN preserves its active epoch even at exhaustion. Atomic
original-generation adoption claims across separate executor objects remain a
required shared-arbitration integration gate.
