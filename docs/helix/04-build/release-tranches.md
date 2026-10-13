# Complete release goal — owner direction, 2026-10-13

Deliver all currently specified Truss features, interfaces and required
verifications under accepted owner scope amendments. Features ship first in
tranches, interfaces follow in tranches, then required verification and fixes.
Commit/push completed work to main and review each plan/completed iteration with
Astra Ultra. Publish each completed tranche through release workflows. A blocked
stream requires an unblock notification and work on another unblocked stream;
do not pause the goal while useful work remains.

## Delivery order

| Tranche | Concrete remaining outcome | Governing scope |
| --- | --- | --- |
| Numeric release | v0.0.2 + matching Weft0.4.4 wheels; original0.7/0.8 acceptance/write/import/read/query precision | FEAT-002, existing numeric iteration |
| Typed business keys | Extend exact authored-key creation/update/lookup/import/preconditions beyond required strings using UMF-owned equality/encoding | FEAT-002 STO-04, FEAT-005 RD-01 |
| Value and graph completeness | Structured/collection/owned values, ownership/composition mutation and reads, retained-value rebinding, remaining catalog evolution | FEAT-001/002/003, CONTRACT-001/003 |
| Read and lifecycle completeness | Direct one-to-three-hop traversal; remaining query mapping; history retention/archive; import lifecycle | FEAT-004/005, CONTRACT-003/004 |
| Public interfaces | Every specified capability selector/provider and host-facing operation; complete documented parameter/result mapping and installation/migration paths | FEAT-008, CONTRACT-007 |
| Verification and fixes | Required basic and adversarial semantics, declared target qualification, enforcement reports and reproducible layout generation; release fixes as they land | FEAT-006/007, accepted scope amendments |

This list orders implementation; it does not certify any pending requirement or
replace the governing contracts. Existing object/edge groups, preconditions,
replay, feed, reads and compatible scalar evolution are already callable.
Avoid repeating historical unavailable-surface claims.

## Coordination and explicit constraints

Security-owner work remains a separate active stream. Consume its committed
boundary contracts; do not promote private components into protected deployment
claims. Weft owns logical SQL and UMF owns metadata, key equality and generation.
Truss owns their runtime composition and host execution.

UMF-valid unresolved external relationship declarations and timestamp key
semantics need owner support before those source profiles can be implemented;
continue other admitted key/value work. Actual Aurora/Lakebase environments
must be available before managed-service support can be claimed. Independent
second implementation/interchange remains deferred by accepted ADR-003; this
new goal does not revive superseded mandatory first-release gates.
