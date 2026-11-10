# Test

Define test strategy, acceptance checks, and verification evidence linked
to the governing requirements and designs.

Status: test design is drafted; structural/source checks have scoped evidence. Native implementation acceptance remains unqualified.

Start with [TP-001](test-plan.md) for full-scope strategy and [STP-001–049](test-plans/) for primary story allocations. The allocation checker (`scripts/check-story-allocation.py`) counts 49 story pairs and 197 criteria, with 10 open allocation-row errors in baseline US-012-AC5/6 and US-045-AC6/7/8 (none in bulk UPDATE); older audits report 45 pairs and 167 criteria; those counts establish document structure, not executed acceptance. The [decision queue](../04-build/design-decision-queue.md) records unresolved semantic/profile choices, and the [implementation plan](../04-build/implementation-plan.md) sequences the public reference-host S01–S09 checkpoints without reducing release scope.

For current value/row integration, [STP-007](test-plans/STP-007-store-and-read-objects-and-edges-exactly.md) owns writer admission/replacement parity and [STP-020](test-plans/STP-020-read-an-object-by-identifier-or-key.md) owns direct/compiled readback, scalar/tree correlation, original field-identity bytes, occurrence custody and batch transport/resources. [Source evidence](../04-build/evidence/design-audit/) includes captured SQL/UMF/export artifacts and corruption-control receipts. Planned native cases, owner evidence inspected from another repository and Truss-executed tests must remain separately identified.

TP-001 and CONTRACT-011 govern complete case/manifest assessment. Missing, blocked or not-run required cases cannot produce qualified support; interrupted original work retains containment/recovery obligations. Exact native/driver/compiler/profile pins and independently authored expected observations are required before execution evidence can satisfy acceptance.
