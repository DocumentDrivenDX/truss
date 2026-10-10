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

# Diagnostic delivery qualification

Authority: [diagnostic candidate](../02-design/contracts/diagnostics.proposal.md).
No case is passed by this plan. Use actual installed Python instrumentation,
selected bridge/OTLP receiver and reference runner; do not substitute a test-only
logger or JSONL parser for transport evidence.

| Case | Required observation |
| --- | --- |
| OBS-01 lifecycle/refusal/failure | Correct event owner, category/severity, one emission and exact independent native/product outcome; no retry or duplicate query chatter. |
| OBS-02 mapping | Receiver observes Resource, scope, event/body, source/observed times, severity and exact safe attributes; timestamps above JS safe integer range retain precision. |
| OBS-03 correlation | Logs outside a span omit IDs; actual concurrent attempts and async propagation retain the correct context without cross-attempt contamination. |
| OBS-04 privacy | Synthetic secrets/content/SQL/origin/paths in every input and exception/repr fixture are absent in every actual sink/artifact; repr fixture is never invoked. |
| OBS-05 bounds/loss | Independently fill record/queue byte/count limits; oversized and dropped records produce bounded loss evidence without recursive flood or changed product outcomes. |
| OBS-06 outage/shutdown | Actual exporter/capture failure cannot wait/retry a product operation; flush stops within the selected deadline and reports incomplete capture. |
| OBS-07 rotation/retrieval | Concurrent appends respect snapshot end; expiry after actual rotation yields explicit recovery/loss metadata, with enforced access scope and byte/count limits. |
| OBS-08 ingestion | One chosen emission/export path produces one backend record; visibility changes preserve event meaning and unsampled lifecycle/final outcomes where capture remains available. |
| OBS-09 pilot/overhead | Run actual service/reference CLI failure and concurrent-attempt cases. Measure cause accuracy, cited evidence, retrieval calls/context and instrumented overhead against the declared baseline/budget. |

Record exact source/package/schema/SDK/bridge/receiver versions, commands, input
bounds, actual output/loss and mapping. Deployment routing/retention permissions
need their own target evidence. Product receipts and native observations are
separate references: neither missing logs nor a matching diagnostic digest proves
commit, authority or recovery. Current CLI output includes local connection data;
that is an explicit local result, not a safe diagnostic record to ingest wholesale.
