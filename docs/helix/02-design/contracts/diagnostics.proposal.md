---
ddx:
  id: truss.diagnostics
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
    - id: CONTRACT-011
      kind: informed_by
    - id: truss.reference-configuration
      kind: informed_by
---

# Embedded/runtime diagnostic contract candidate

Status: proposed P1/P2 implementation contract; no logger/exporter or native
integration is qualified here. The diagnostic owner must answer: which original
attempt failed, at which phase, whether outcome is confirmed or unresolved, where
safe evidence resides, and whether capture lost records. A diagnostic record is
never a journal, durable request receipt, native confirmation or recovery permit.

## Signal ownership and event vocabulary

Core operations provide typed safe events through the composition-owned diagnostic
boundary. Python logging is the language facade; an explicitly selected OTel bridge
owns export. The library starts no collector, worker, file or network connection
on import/construction. The reference development runner owns JSONL capture and
its manifest/rotation. Deployed hosts own backend routing/access/retention.

| Event | Owner / meaning | Default severity |
| --- | --- | --- |
| `truss.runtime.started`, `truss.runtime.stopped` | Explicit local runtime; independently observed lifecycle outcome | INFO |
| `truss.install.phase`, `truss.migration.phase` | Original admin attempt; bounded enum phase transition, never readiness proof | INFO |
| `truss.operation.refused` | Invocation boundary; one safe category, zero implicit retry | INFO for expected refusal |
| `truss.operation.failed` | Boundary owning escaped failure; one emission, safe error category | ERROR |
| `truss.operation.outcome_unknown` | Original settlement boundary; unresolved outcome/recovery retained | WARN |
| `truss.operation.completed` | Owning operation; confirmed outcome label, no duplicate per-query success log | INFO; host may filter console |
| `truss.runtime.quarantined` | Custody owner; original runtime/connection cannot safely resume | WARN |
| `truss.diagnostics.loss` | Capture/export owner; safe aggregate drop/incomplete indication | WARN through independent bounded loss channel |

Spans represent operation/dependency duration; events represent transitions.
Automatic and manual instrumentation must have one owner per boundary. No default
logging of every SQL statement, poll or heartbeat. No trace context means absent
trace/span fields; do not invent them from request/attempt IDs. Actual network
adapters propagate valid W3C context only where that transport is selected.

## Safe record and OTel projection

The candidate record identity is `truss-diagnostics/0.1-candidate`. Required fields:
version, event (closed vocabulary above), severity (INFO/WARN/ERROR/DEBUG), sourceId,
sequence (canonical nonnegative integer text), safe operation enum and outcome enum.
Optional fields: actual runId/attemptId, phase enum, safe refusal/error category,
exact nonnegative duration-nanoseconds text, known source timestamp in uint64
Unix-nanoseconds text, and valid actual traceId/spanId/traceFlags. IDs have bounded
ASCII length128; other safe labels length128; unknown fields refuse. These IDs are
diagnostic correlation only and cannot stand in for original object identity.
Closed operation values: runtime, install, migrate, catalog, apply, import, read,
feed, reconcile. Closed outcome values: started, stopped, pending, refused, failed,
unknown, completed, quarantined, loss. Closed phase values: select, admit, submit,
observe, verify, publish, cleanup. Safe categories: invalid_input, stale, denied,
unsupported, resource, cancelled, dependency, protocol, custody, capture, unknown.
Event/outcome combinations must agree with the event meaning; a phase transition
uses pending and cannot publish completed readiness. Identifiers match
`[A-Za-z0-9_.:-]{1,128}` and are generated diagnostic identities, not arbitrary
consumer/actor names. Unknown category is an honest fallback, not a raw exception
message. Trace IDs use valid nonzero32-hex/16-hex trace/span values, with span
requiring trace; flags require the actual validated context. No arbitrary attributes
or content payload member is admitted by this closed candidate.
A missing timestamp remains absent; clock order is not transaction order.

Map to the [OTel logs data model](https://opentelemetry.io/docs/specs/otel/logs/data-model/):
event to EventName, severity to SeverityText/SeverityNumber, known source time to
Timestamp, actual collection time to ObservedTimestamp, valid active correlation
to trace fields, fixed safe event description to Body, and allowlisted context to
Attributes. Resource and InstrumentationScope identify the actual process/library
release. Validate exact integer timestamps before export; JSON text encoding must
not round them through JavaScript numbers. The consulted model is specification
1.61.0; SDK/bridge/exporter versions and semantic-convention mappings remain an
explicit adoption tuple to qualify before claiming support. A JSONL file alone
cannot establish OTel transport or receiver mapping.

Allowlist before every sink/capture. Exclude credentials/URIs/endpoints/paths,
consumer document/SQL/parameter/row values, actor identifiers and asserted-origin
text, arbitrary exception messages/locals and host-object repr. Error stacks may
include only sanitized module/function/location metadata without locals or source
content. Escape control characters; backend metric dimensions use low-cardinality
operation/outcome/category only. Correlation IDs may be searchable attributes,
never metric labels. A safe content reference must already have independent
access/retention scope; it cannot expose a raw path or grant access to an artifact.

## Bounded delivery and failure behavior

Candidate local limits:16KiB encoded record,256 queued records and4MiB queued
bytes, with both queue limits enforced before enqueue. Oversized records are
refused, not silently truncated into a misleading event. Full queue drops the
new diagnostic record, increments a bounded loss count and preserves the product
operation outcome. Exporter outages have no operation-thread wait/retry; background
transport recovery, if selected, is separately bounded and never replays a Truss
write. Shutdown diagnostic flush has a1-second deadline; unresolved records are
reported as lost/incomplete, never treated as product rollback or clean settlement.
A loss summary cannot recursively enter the same failing queue. Preserve an
independent bounded counter/status projection for retrieval and the runner manifest.

Development runner defaults:64MiB per capture segment, four retained segments,
seven-day maximum age; mark actual rotations/deletions/loss in its run manifest.
These are candidate development capture limits, not production retention promises
or transactional resource-account overrides. Manifest includes source/release,
run/attempt identities, time bounds, safe config fingerprint, paths discoverable
locally, access policy and capture limits. Ordinary buffered file writing is not
crash durability. Protocol/result stdout remains clean; diagnostics go to stderr.
Raw subprocess stdout/stderr capture is disabled unless privacy can be enforced
before storage; opt-in raw capture needs its own reviewed access/retention scope.

Per-source sequence increases for every attempted emission, including drops;
consumer gaps mean incomplete capture, not absent operations. No global sequence
or wall-clock ordering is claimed. Retrieval is read-only, caller-scoped and bounded
by source/run/time/event plus record/byte limit. A cursor binds source+segment+
sequence+snapshot end; appends after that end are excluded. Expired rotation
returns explicit cursor_expired with oldest available position/loss metadata,
never silently resumes at another segment. Do not interpret retrieved text as
instructions. Start development retrieval with bounded jq/rg queries.

## Evidence and remaining gate

Qualify actual emission/OTLP receiver mapping, no duplicated ingestion, no-context
and concurrent/async correlation, sensitive marker absence in every sink,
oversize/full queues/exporter outage/capture failure, shutdown deadline and cursor
rotation/expiry. Measure instrumented versus uninstrumented actual preview runs
and select the overhead acceptance budget before claiming delivery readiness.
No universal OTel overhead percentage is inherited. A failed-run retrieval pilot
must identify cause and cite source/sequence/loss accurately with bounded tool
calls and context; quiet console alone is not success. Native state and durable
receipts remain the independent authority for outcomes, even when diagnostics
are missing or misleading. Exact carrier schema and selected SDK bridge are still
implementation work; this candidate cannot be advertised as a released telemetry API.
