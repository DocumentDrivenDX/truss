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

For local PostgreSQL, use the verified private PostgreSQL17.11 wheel. This
checkout has a verified local wheelhouse at `.cache/pgserver/pg17.11/wheels`;
copy it or rebuild once if that ignored cache is absent:

```sh
python3.11 -m venv .venv
.venv/bin/pip install --no-index --find-links .cache/pgserver/pg17.11/wheels './packages/python[local]'
.venv/bin/truss-local-postgres --data-dir .local/truss-postgres-17 --probe
```

The wheelhouse must contain `pgserver0.1.4+truss.pg17.11`, fasteners0.20,
platformdirs4.12.4 and psutil7.2.2. The local extra, runtime requirements and
`constraints/local-corrected.txt` select the exact private distribution; the
public pgserver0.1.4 package cannot satisfy it. The wheel remains unpublished.
Build it once when PostgreSQL or its recipe changes, then reuse it for normal
tests. The [runtime checkpoint](../../docs/helix/04-build/local-runtime-installation-migration-plan.md#postgresql-1711-embedded-runtime--owner-direction-2026-10-11)
records the pinned source/build procedure, wheel hash, installed payload verification
and all15 passing component qualification groups on macOS27 arm64/Python3.11.

The [installed suite](../../docs/helix/04-build/evidence/design-audit/python-pg17.11-installed-suite.json)
passes132 tests; the [native timeout probe](../../docs/helix/04-build/evidence/design-audit/pgserver-pg17.11-transaction-timeout.json)
observes actual transaction_timeout connection termination. These component checks
retain the existing complete-engine, protected-installation and managed-service gates.
Earlier16.2/16.15 evidence below remains historical.

To reproduce the selected embedded qualification lane with an installed Truss wheel:

```sh
.venv/bin/python scripts/qualify-pgserver-pg17.py /path/to/truss_toolkit-0.0.1.dev0-py3-none-any.whl --run-id pg17-my-run --workers 2
```

This command requires the pinned pg8000/Weft test dependencies and a fresh run id.
It reuses installed binaries and performs no source build. Twelve native groups
share one cluster per worker with fresh databases and roles; default `--workers 1`
uses one suite cluster. The installed lifecycle suite, CLI signal/restart and
transaction-timeout observations use separate owned clusters.

Workers use unique short Unix socket directories and disable TCP listening.
The socket's port suffix is local to its directory; workers do not contend for a
TCP5432 listener. Fixtures refuse overlap, terminate leaked sessions only in their
owned database, remove fixture roles and compare original native inventory.
Failed setup/cleanup or leaked state invalidates the worker; confirmed shutdown
precedes directory removal. The [shared-worker checkpoint](../../docs/helix/04-build/local-runtime-installation-migration-plan.md#shared-native-test-workers--owner-direction-2026-10-11)
records all15 passing groups and21 native cleanup/collision controls.

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
bundled17.11 with its exact private package identity; historical16.x pairs remain
recognized explicitly for historical checks. Other platform/version
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
