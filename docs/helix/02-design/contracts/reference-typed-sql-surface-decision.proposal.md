# Typed SQL surface design boundary

PRD lists typed graph views for table-oriented tools as P2. CONTRACT-005 separately requires every deployment to enumerate its advertised direct SQL surfaces and forbids silently replacing those surfaces with a Truss API. These are distinct obligations: the core protected profile must have an explicit SQL exposure inventory, but optional typed views cannot be assumed installed or included in its capability claim.

## Meaning awaiting owner choice

The outstanding question is whether typed views promise complete logical values or explicitly documented physical projections. No answer is recorded yet. Preserve this as an unresolved design decision; neither a conventional SQL NULL nor a view name resolves it.

A logical projection must independently retain Item.note absence, present null and present empty string, exact numeric token meaning, whole required source/definition/presence correspondence and current qualified owner authority. A nullable text column alone is insufficient. Its result design needs explicit presence/provenance alongside value, and its execution must enforce every required integrity prerequisite before predicates can hide corrupt owners. Weft remains responsible for SQL compilation and its decoder/obligation semantics; Truss cannot invent a parallel compiler to create the view.

A physical projection must declare exact native columns and storage meaning, original qualified identity and current disclosure policy. It makes no whole-record decoding, absent/null reconstruction or compiler-host publication guarantee. It cannot be presented as an interchangeable implementation of a complete logical view. Exposing physical data still requires full indirect/base-table/role/policy review and cannot reveal private staging, guard, receipt or observer state.

## Execution handoff

After the owner selects meaning, enumerate each advertised relation/view/callable with exact selected result columns, parameterization and authority derivation. Define view lifecycle across accepted revision, same-ID reactivation, retirement and changed binding/profile generation. A generated SQL definition is an authored effect with original source identity and conversion disposition; it is not a new per-entity canonical storage table.

For logical views, first reconcile the required Weft representation and determine a realizable native validation/publication route for independent SQL consumers. Do not assume the optimizer runs a guard CTE, security barrier or volatile helper before all filters; that ordering needs a concrete design and independent native evidence. If the selected route cannot preserve obligations, report that capability unavailable rather than falling back to physical projection. Ordinary compiled execution through CONTRACT-007 remains separately qualified.

STP-045's declared-surface activation controls and STP-038 authority controls retain missing/broadened surfaces, indirect paths and rollback/recovery coverage. Add complete absent/null/empty, unsafe-number precision, hidden corrupt owner and revision/reactivation schedules after the result/route design is selected. The full existing product corpus remains required. No generated view, native grant or implementation is supplied by this decision record.
