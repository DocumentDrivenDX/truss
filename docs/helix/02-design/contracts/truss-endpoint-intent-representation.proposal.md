# Truss-owned endpoint-intent representation candidate

Design input for US-002/003 and CONTRACT-003. Status: representation experiment;
not an adopted extension, accepted catalog or change to UMF core relationships.
This uses UMF's existing extension registry, rather than requiring CONTRACT-045
or reinterpreting its future generic reference syntax.

## Existing-owner evidence

The [probe](../../04-build/evidence/design-audit/check-truss-endpoint-intent-extension.ts)
executes committed UMF `1f7b5f5d2a355c4b476e3a96b289b9048f03f567`
`Registry.register` and `validateDocument` on clean archived source. It checks the
complete 1,342-member src/spec tree digest before imports, and retains the
[receipt](../../04-build/evidence/design-audit/truss-endpoint-intent-extension-probe.json).
Five controls pass: a registered document-scoped pending external intent is
valid/complete in the probe's declared extension language; without registration
it is valid but incomplete retained content; an invalid local Record source and
duplicate intent refuse; an unresolved core relationship still refuses unchanged.
The checker passes strict TypeScript. No native execution or Truss acceptance ran.

The extension owns *catalog endpoint intent*. Its external coordinate is data
in that language, not a core reference, resolved Record or instance edge. The
probe's semantic callback establishes local source ownership and intent identity
only. It intentionally does not claim the target exists. Valid/complete extension
validation means that its declared pending-intent syntax and local checks passed;
it does not mean a relationship can execute or any database assertion is enforced.

This supplies concrete evidence that current UMF can represent a Truss-owned
pending intent without fabricated target stubs or invalid-core validation bypass.
It does not supply the complete endpoint/dependency semantics required to close
US-002/003. The small probe schema omits full relationship bounds, keys, lifecycle,
inverse and heterogeneous endpoint sets and must not become a release vocabulary.

## Remaining representation-to-policy handoff

| Stage | Required authored output and independent exit |
| --- | --- |
| E1 full extension meaning | Select a Truss-owned vocabulary/profile covering full relationship intent, exact declaring identity, endpoint sets, target keys, direction/bounds/lifecycle and original source pointers. Distinguish declared document dependencies from unresolved endpoint intent; never borrow the probe's minimal coordinate as a complete relation |
| E2 source and package custody | Capture exact original document/revision/bytes and complete supplied or previously accepted membership. A revision string is a selection claim, not authority. Validate core content unchanged and validate registered extension semantics; unregistered content remains retained-only and cannot drive required policy |
| E3 resolution and dependency graph | Resolve qualified definitions and keys through original owner producers and accepted catalog custody. Derive dependency edges only under E1's explicit semantics, then use the existing SCC/byte-order algorithm. Independently test mutual dependencies, permutation invariance, missing/wrong revisions and duplicate membership; do not flatten source documents or resolve bare names globally |
| E4 unknown policy | Apply reject/provisional/skip to valid admitted intents only. Provisional allocation requires complete qualified lineage and absent-definition provenance; skip records exact original source-qualified loss. Multiple equal unknowns share only their admitted identity, and unrelated owners remain distinct. Invalid core input refuses before every branch |
| E5 later definition and publication | Match the authoritative later definition to the original pending lineage, preserve stable type identity, validate/rebind retained data, and publish full lifecycle/report/history effects atomically. Independent occupied-home, changed owner/revision, failed rebind and rollback cases precede activation |

Truss owns the extension's catalog-policy semantics and registered producer.
UMF owns core validation, extension registration and original Record/Field/key
meaning. Weft must separately register any selected extension-derived relation
mapping before compiling it; valid pending content cannot expand its subset.
Security retains original administrative/read/publication admission. This proposal
adds no second compiler, dependency fetcher, authority registry or ACL resolver.

E1–E5 remain design/implementation work. Keep positive cross-document,
provisional/skip/promotion acceptance unavailable until complete original
representation, producer and policy correspondence is admitted. Existing core
relationship behavior and prior invalid-input refusals remain governing.

For reproduction, archive `src`, `spec` and `package.json` from that exact UMF
commit into a clean directory with its admitted dependencies, then run the probe
with the directory path. The checked tree digest refuses changed source members;
the receipt scopes library source correspondence only, not dependency installation
or native security/transport qualification.
