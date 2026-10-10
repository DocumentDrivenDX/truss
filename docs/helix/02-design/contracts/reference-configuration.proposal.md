---
ddx:
  id: truss.reference-configuration
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
    - id: truss.architecture
      kind: informed_by
---

# Reference composition configuration candidate

Status: proposed implementation contract. This closes process/configuration
ownership in the HELIX0.15.4 adoption plan; it does not add public engine APIs or
replace existing original assembly/executor/bootstrap/migration registrations.
Existing Contracts own their full signatures and authority requirements.

## Distinct meanings

The composition root captures one validated, immutable **process option view**
before effects. Its adapter/connection/service references remain the original
objects under their existing lifetime contracts; they are not serialized, copied
or turned into authority by being stored in this view. A frozen container does
not freeze or authenticate a host object. Embedded Python callers supply those
objects directly; the library does not read environment variables on their behalf.

Native installation/configuration artifacts, generation and original transaction
capsules are a separate meaning. They must be admitted and rechecked using
CONTRACT-007/008 and the installed-context protocol. A startup option view or safe
configuration fingerprint cannot mint native configuration, prove current state
or suppress per-operation admission. Refusal occurs once; no internal retry.

## Owners and admissible sources

| Input family | Owner | Source / validation and absent case |
| --- | --- | --- |
| Connection and exact registered native/compiler/security adapters | Embedding host | Required original references for the selected capability; existing exact registration/profile admission. No default connection, new pool, driver fallback or reconstructed issuer. |
| Connection credentials, managed endpoints, assigned ports | Operations | Injected only into the chosen host adapter/reference launcher. No committed per-environment values or defaults; do not expose them through public representations, errors or telemetry. The embedded toolkit need not receive a credential string when it already receives a connection. |
| Adopted release/bundle, layout/compiler/profile identities | Truss release plus host selection | Exact admitted original artifacts/profile tuple; no arbitrary version-derived SQL or best-effort substitute. Unknown/unavailable selection refuses before native effects. Metadata projection is not executable artifact admission. |
| Local runtime retained data directory | Local caller | Existing required `--data-dir` / LocalPostgres argument; path normalized by that runtime and actual directory custody checked on start. No hidden temporary default, implicit takeover or migration. Directory paths are operational data, excluded from shared telemetry by default. |
| Non-secret diagnostic verbosity | Development/release | Reviewed defaults and optional environment file in the reference launcher; host can inject an explicit incident override. Diagnostic visibility does not change event semantics, native policy or durable receipts. |
| Diagnostic exporter endpoint/authentication and operational retention | Operations/environment | Explicit supported transport/capture injection, no automatic backend discovery. Library has no mandatory exporter. Development runner owns file routing/rotation; deployed platform owns routing/retention. |
| Resource/account limits, timeouts and cancellation | Existing admitted profile plus host | Retain existing exact ownership and original precharged bounds; process options cannot create a caller override, independent allowance or an implicit retry budget. Unsupported combinations refuse. |

Each key has one owner. Reference launcher precedence is ops injection over
reviewed non-secret environment file over reviewed defaults. Environment selection
is one explicit launcher-owned selector, not inferred from hostname. Ops-required
handles have no committed default. A placeholder example may name keys but cannot
contain production/staging operational handles. There is no new config file or
loader implemented by this proposal; retain the minimal existing CLI until the
reference composition needs these inputs.

## Validation, effects and representation

Validate closed option shapes, exact types (no Boolean/integer confusion), supported
release/profile combinations and original reference registration before effectful
capability use. Unknown Truss-owned keys and duplicate declarations within one source layer refuse;
ignore unrelated process environment keys rather than treating the whole process
environment as Truss configuration. Environment coercion is reference-launcher
translation, with explicitly declared spellings in its eventual binding; the
embedded library accepts typed values. Do not invent universal environment names
or a second complete configuration schema ahead of those owned interfaces.

Configuration parsing/selection creates no connection, directory, SQL, worker,
transaction, installer attempt or telemetry network request. The local runtime's
explicit start owns its directory/server effects. Install/verify/apply/reconcile
use the same immutable release and captured host composition, with their original
per-call admission and explicit effect boundaries. Ordinary startup never runs a
migration. An incident option change requires a new validated composition; it
cannot mutate a live original transaction or refill its spent budgets.

Safe diagnostic fingerprints include only an allowlisted non-secret projection
of Truss release/profile labels and development-owned options. Credentials,
connection URIs, operational endpoints/paths, consumer content and actor/asserted
origin values are omitted before hashing. Hashing secret/low-entropy values is
not redaction. Do not stringify arbitrary host handles or invoke their repr
methods. Errors identify safe key/category and do not echo rejected values.

## Required qualification cases

CFG-01: typed embedded injection with no environment read or object cloning.
CFG-02: exact registered references remain original; copied/foreign registrations
cannot gain authority through options. CFG-03: absent required host connection
refuses before effects. CFG-04: unknown keys, duplicates and wrong exact types
refuse once with safe error context. CFG-05: launcher precedence selects the owned
value, while unrelated environment keys have no effect. CFG-06: credentials and
operational handles never occur in defaults/files, repr/errors/fingerprint or
any diagnostic sink. Inject synthetic markers and inspect actual outputs.
CFG-07: unsupported release/adapter/profile tuple refuses before native submission,
without fallback. CFG-08: same release/options drive explicit install/migration;
constructing/parsing does not start either. CFG-09: local retained directory custody
remains the runtime's explicit start check; no takeover. CFG-10: changing console
visibility does not change event meanings or product receipts. CFG-11: option
changes cannot modify/refund a live original transaction account. CFG-12: native
configuration/generation drift is independently refused by the original admission
protocol despite unchanged startup options/fingerprint.

No case is reported passed here. Existing runtime/component tests cover narrower
facts and cannot qualify a loader/reference composition that is not implemented.

Execution and evidence requirements are in the [configuration test plan](../../03-test/reference-configuration-test-plan.md).
