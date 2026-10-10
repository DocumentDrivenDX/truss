# Distinct-neighbor participation — native engineering candidate

This candidate reconciles committed UMF relationship participation with Truss's
fixed generic marker strategy. It is not installed or qualified and does not
change US-011's explicit occurrence-cap contract. Governing inputs are
CONTRACT-001 EL/OC, CONTRACT-009 exclusions, TD/STP-011 and the
[committed upstream review](../../04-build/evidence/design-audit/weft-b8867c9-participation-review.json).
No new SQL compiler, security resolver or per-relationship index is introduced.

## Scope and representation

Choose a separately registered distinct-neighbor profile before accepting an
owning UMF participation assertion. Keep occurrence-cap selection explicit and
separate; neither profile can inherit the other's marker proof. A profile must
state which assertion it enforces and every stronger/residual constraint. Unknown
counting meaning refuses before effects. No implicit upgrade of existing markers
or compiler realization is allowed.

Use the existing edge_limit columns and fixed primary key as the candidate
maximum-one representation. For each complete canonical edge, first establish
the original relationship/revision and typed endpoint Record identity through
the admitted catalog/native mapping. Group edges by exact relationship, side,
owner Record and associated neighbor Record. IDs below are native representations
of those proved identities, never display keys or projected key tuples.

For target_max=1, group source-owned associations and derive one side-s marker
per distinct source/target pair. For source_max=1, group target-owned associations
and derive one side-t marker per distinct target/source pair. Each group's marker
uses the smallest exact native edge ID among its surviving occurrences as the
representative edge_id. Preserve the complete group membership separately in the
original proof; a marker cannot certify membership by itself. Self-edges need
both side markers when both ends are limited.

Two distinct neighbors of one limited owner derive two marker rows with the
same existing (rel_type_id,side,endpoint_id) primary key and therefore conflict.
Parallel occurrences of one neighbor derive one row. The representative edge
FK preserves existence; its endpoint/type/revision and canonical minimum must
still correspond to the complete independently derived group. No extra native
column/table is selected by this proposal. Actual type/collation/constraint and
source/model/generated-DDL correspondence must be verified for the chosen layout.

## Original mutation and final-state procedure

1. Admit exact installation, profile meaning, original actor/operation/account
   and complete old/new relationship/edge scope. Retain old representative and
   complete occurrence provenance before any deletion or FK cascade.
2. Plan both old/new owners, neighbor groups, incoming/outgoing invariants and
   catalog-change effects. Acquire the existing exclusion hierarchy, including
   shared targets; reserve complete collection/comparison/marker work first.
   Newly discovered earlier exclusions require the existing original refusal
   protocol, never an automatic retry loop.
3. Derive complete final canonical occurrences and distinct typed neighbors under
   one admitted cut. Larger maxima compare distinct-neighbor counts under the
   selected engine/serializable profile. Minimum checks enumerate complete owner
   roots, including zero-neighbor Records. Do not derive roots from edge rows.
4. Under held exclusions remove the complete affected old marker set, apply final
   canonical changes and insert all final derived representative markers. This
   uses EL04's final-state ordering and immediate fixed primary key. No ordinary
   caller can observe or exploit the unsealed gap through an unmediated writer.
5. Compare full final marker multiset bidirectionally with the independently
   derived groups and original effect membership. Extra, missing, wrong-side,
   wrong-neighbor, wrong representative or stale-profile markers refuse. Preserve
   all occurrence IDs/results; degree normalization is not result deduplication.
6. Complete original touch/generation/finalizer/feed and commit-dispatch coverage.
   Every edge and marker event contributes, including representative moves,
   unchanged-value writes, cascades and definition-only changes. No readiness flag
   bypasses complete current union validation. Failure rolls back only through
   confirmed original containment; unknown outcomes retain original custody.

Deleting a nonrepresentative parallel occurrence leaves the derived marker
unchanged but remains an actual accounted edge effect. Deleting the representative
while a sibling survives replaces its marker with the smallest surviving edge.
Deleting the last occurrence removes that pair's marker; a minimum may then fail.
Deleting a representative cannot rely on its FK cascade as evidence that the
owner has no neighbors. Parallel insertion may change the representative when an
admitted imported ID orders earlier; do not assume all incoming IDs are larger.

Both endpoint directions retain authored forward multiplicity orientation.
Definition tightening collects the complete populated relationship, not only
edges mentioned by the request. Revision/retirement/reactivation handling uses
the selected original definition provenance; no retirement filter drops live
occurrences. Public diagnostics remain under current disclosure while private
integrity includes hidden siblings.

## Qualification and conversion

The current occurrence-cap EL03 expected multiset is incompatible with this
group-derived multiset. Version the profile, verifier, observer/writer/trigger
dependencies and installation inventory together. Merely changing COUNT to
COUNT DISTINCT or retaining the old marker observer cannot activate support.
Canonical writers must be unavoidable under the admitted ordinary-role profile;
direct marker maintenance remains denied. Complete body/grant/dependency and
ordinary bypass evidence precede readiness.

Independent schedules cover parallel insertion, different-neighbor concurrency,
representative/nonrepresentative/last-occurrence deletion, lower imported edge
ID, self-edge/two-sided limits, incoming bounds, definition tightening, zero-root
minimum, hidden siblings, marker omission/substitution and finalizer/commit
failure. Repeat with early constraint checking and rollback preserving earlier
caller work. Related reads retain duplicate occurrence bags and exact lookahead.
These are native implementation exits, all not_run.

The [eight independently authored marker vectors](bindings/distinct-neighbor-marker-v0.1.vectors.json)
cover parallel/distinct neighbors, representative/last deletion, a lower imported
ID, self-edge, incoming conflict and independent owners. Their expected marker
multisets and primary-key conflict flags pass a separate mathematical grouping
check. They use synthetic already-proved Record stand-ins; no native identity,
type, context, authority or complete algorithm qualification is inferred.

An existing occurrence-cap installation needs an explicit complete conversion
route before adopting this meaning. Preserve all edges/history/receipts/feed and
recovery custody, rebuild the complete marker interpretation under administrative
exclusion and publish profile/inventory atomically. Existing occurrence-cap
validity does not prove minimum participation or current authority. A reverse
conversion refuses when retained parallel occurrences violate the destination
cap; it cannot delete or deduplicate them to make the route pass. Full populated
migration preservation remains required; no route is qualified here.
