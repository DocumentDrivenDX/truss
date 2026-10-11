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

# Basic runtime diagnostics

Owner decision — 2026-10-11: remove custom tracing and metrics. The previous
custom event protocol, OpenTelemetry projection, span/context propagation,
exporter queues and diagnostic-loss machinery are withdrawn from the delivery
scope. No telemetry SDK, bridge, receiver or exporter is a Truss dependency.

Keep ordinary, minimal logging through the host application's logging setup.
Useful records identify the operation, outcome and stable failure category.
Report confirmed failure versus unknown transaction outcome accurately. Logging
must not change transaction results or introduce retry loops.

Do not log credentials, connection strings, SQL parameters, document/row values,
actor/origin contents, object representations or unsanitized exception locals.
Use stable error codes and safe messages. Callers continue to receive the typed
results needed for retry and idempotency; application receipts and journals are
product data, not metrics.

No per-statement tracing, phase spans, custom metric dimensions, trace-context
propagation, allocation/work counters, exporter lifecycle or dedicated diagnostic
record schema is required. Focus verification on safe failure information and
unchanged product behavior. Existing semantic integrity and transaction guards
remain required.
