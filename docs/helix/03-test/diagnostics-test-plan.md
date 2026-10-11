---
ddx:
  id: truss.diagnostics-test-plan
  type: test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.diagnostics
      kind: informed_by
    - id: CONTRACT-011
      kind: informed_by
---

# Basic diagnostic checks

Authority: [basic runtime diagnostics](../02-design/contracts/diagnostics.proposal.md).
The owner removed custom tracing/metrics on 2026-10-11. Retire OTLP receiver,
span/correlation/exporter/queue-loss and instrumentation qualification scenarios.
They are not implementation or release gates.

Verify only that ordinary failure diagnostics use safe stable codes/messages,
exclude credentials and application data, distinguish unknown transaction
outcomes, and do not alter success/refusal/rollback/retry behavior. Reuse the
relevant product-operation tests; do not create a separate instrumentation suite.
No implementation or pass is asserted by this plan.
