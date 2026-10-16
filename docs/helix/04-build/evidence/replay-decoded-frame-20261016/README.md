# Invocation-local replay frame — 2026-10-16

Reuse original already-decoded operations/results and lazily reconstruct the
original catalog basis once per native replay invocation. All per-operation
current module/property/item authorization and final edge authorization remain.
The historical-reader wrapper is byte-for-byte unchanged. No persistent cache
or product instrumentation was introduced.

The original1024 create/changed-update/commit/replay/ordered-readback workload
passes under unchanged10s SQL/30s operation limits: baseline38.962s and candidate
30.804s. Stock PostgreSQL function statistics run only in this disposable fixture.
Old retained owner self-time7523.839ms/1024calls is replaced in replay by private
frame self-time23.943ms/1024calls. Concurrent SDK functional campaigns overlap;
these are diagnostic comparative observations, not isolated timing qualification
or a hosted CREATE-timeout fix. Both fixture runs clean up successfully.

Basic public controls:3PASS16.999s (cross-module property-reader revocation,
writer revocation, original receipt after compatible catalog evolution/history).
Published SDK37 upgrade/private-custody checks:2PASS5.979s. Runtime recipe223.
A separate main integration module-map failure for the security owner's new
module is assigned to that owner, with no waiver or competing map change.

Astra Ultra source review: SOURCE CLEAR after restoring the original wrapper.
It inspected3 basic passes and the complete1024-workflow pass, confirmed lazy
object-only basis/identity/STRICT-owner ordering and live authorization. Its
review preceded inspection of the completed upgrade log; the2 passing upgrade
checks are direct native evidence, not an expanded reviewer claim.
