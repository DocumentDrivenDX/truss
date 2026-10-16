---
ddx:
  id: truss.native-source-binding.design
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.architecture
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
---

# Actual native source binding

Status: isolated design and spike scope, not an enrolled binding, native permit,
source migration or completed backend criterion. Baseline inspection uses Truss
`430b77b96373e05d20e513cbd048980d9e8031f1`. The separately reviewed current
presence consumer and its source/UMF pins remain frozen.

## Required behavior

The binding must replace the explicitly unadmitted reference fixture with exact
correspondence to the actual accepted catalog and realized storage. UMF owns
model, key, policy and disclosure meaning; Weft owns SQL resolution, typing,
lowering and result transport. Truss observes and validates its native source.
It must not add a Python policy, domain, key or SQL interpreter.

| Requirement | Obligation |
| --- | --- |
| NSB-01 Original source | Retain complete immutable accepted-request, assessment and authored model bytes, including unknown extension content. Hash references never replace those bytes. No numeric passage through binary floats or replacement of authored identities by names. |
| NSB-02 Installed realization | Bind the exact committed runtime release and original source hashes, installation identity, actual database/schema identities, owned native relations and columns. Refuse missing, foreign, duplicate, replaced or unobserved required sources. |
| NSB-03 Field membership | Bind a Field in its Record/property-membership context, not a global name or equal integer. Include accepted property identity and actual native property ID/home/codec correspondence. |
| NSB-04 Ordered keys | Preserve the selected original Key and component order, native namespace/definition/profile correspondence and original UMF codec. Equal numeric IDs do not establish equivalence. |
| NSB-05 Graph occurrences | Bind relationship identity, edge property-owner type, source/target direction, endpoint type/key correspondence and occurrence/version provenance independently. Include parallel occurrences; do not collapse them to a set. |
| NSB-06 Realized homes | Native-column bindings and JSON properties are distinct. A catalog `home='row'` tag without realized state/node/payload stores is unsupported, never an empty or JSON fallback. |
| NSB-07 Current native cut | Re-observe source and current authority under the actual authenticated host operation's required native cuts. A metadata snapshot/hash never issues permission, a current generation or a guarded-release token. |
| NSB-08 Compatibility | New protocol/registration/capability selection is explicit. Preserve current registrations and their computation assets; no implicit repin, migration or acceptance by an older registration. |
| NSB-09 Failure | Refuse the whole result before public data on incomplete correspondence, unsupported required homes/codecs, stale/current ambiguity, deadline or cleanup uncertainty. No partial population, guessed value, truncation or automatic retry. |
| NSB-10 Full scope | Original Truss132 and shared158 requirements remain required. A metadata descriptor, prototype or directed-opaque/JSON-only implementation does not complete or narrow them. |

Trace: UMF US-056 AC2/AC5/AC9/AC10 and the original security acceptance allocation.
These upstream obligations are not replaced by this local design.

## Separate persistent identity from current authority

The current bootstrap registers sources before Subject enrollment and protection
activation. Activation changes grants. The generated Subject helper also binds
the later source inventory digest. Naively putting both pre-activation ACL bytes
and that generated body into the persistent descriptor either makes a legitimate
activation stale or introduces a self-hash cycle.

Use two linked surfaces:

1. **Persistent source descriptor.** Bind immutable release/source/model inputs
   and their actual realized database/schema/relation/column, property, key and
   endpoint mappings. Include precise original codec and support references.
   The descriptor references the required authority-guard protocol, not a
   fabricated future ACL observation. It excludes the later opaque-source
   inventory digest and helper bodies that depend on that digest.
2. **Fresh held native witness.** Inside the original operation, bind the actual
   descriptor hash to the current native owner/role/ACL/helper/source/generation
   observations and their continuously held cuts. This witness belongs to the
   original host/operation/caller and cannot be reconstructed from JSON, copied
   to another operation or used after closing. Its inspection data is not an
   authority token. Closing guards remain necessary before any public release.

This separation is a design proposal to validate, not a claim that the existing
source-epoch issuer or every authority/DDL/configuration path is composed.
If an immutable ACL snapshot is required instead, a separately reviewed atomic
bootstrap/finalization protocol must solve the ordering; do not weaken the
existing bootstrap or declare changed ACLs equivalent.

## Native identities and original meaning

PostgreSQL column identity is `(relation OID, attnum)`, with actual name, type
OID, typmod, collation OID, nullability, dropped/generated/identity status and
original default-expression evidence. Do not invent a standalone column OID.
Qualified names are diagnostic locators; they do not authenticate identity.
Record owner, persistence, relation kind, RLS, inheritance/partition membership,
relevant constraints and actual ACL observations with their correct source.
A type OID or equal SQL spelling does not establish codec/comparator equivalence.
OID/attnum values are reusable locators, not standalone authenticated identities.
Drop/recreate, database recreation, restore/clone, installation replacement and
reused numeric identities must be distinguished by verified installation/source
correspondence and the actual continuously held DDL/source cut. Equal names,
OIDs, column positions or copied installation bytes alone never establish
continuity. An unqualified recreation or custody gap refuses the whole operation.

An authored Field may participate in different Record memberships. Mapping must
retain the containing Record/native type and property ID as well as the complete
Field reference. Likewise an edge's relationship type and property-owner type
are distinct domains. Endpoint direction and exact source/target definitions
must be explicit. Preserve original native/raw source content alongside any
known-field projection; an unknown extension is not permission to infer meaning.

## Actual row-home boundary

The inspected installed `prop_def` accepts `home IN ('json','row')`, but the
installed layout contains no value-row realization. `read.sql` freezes
`false AS row_home`; `barrier.sql` records the removal of
`truss.row_home_operation`. CONTRACT-001 explicitly calls the proposed fixed
presence/state/node/typed-payload stores unadopted. Therefore simply removing
`home!='json'` from the fact collector would invent a source and could turn
unobserved values into apparent absence.

A row-home mapping requires its separately accepted realization, exact
owner/state/node/payload inventory, complete authorized absence proof, original
value/domain codecs, migration parity and native enforcement evidence. Native
column/edge mappings can progress independently; neither is a substitute for
that work. Weft's broader non-JSON binding support remains part of the product.

## Isolated implementation sequence

1. Pin governing layout/source artifacts and specify CONTRACT-013's candidate
   descriptor and witness boundaries before registering a protocol.
2. Implement a pure deterministic descriptor assembly/closed-shape checker over
   captured immutable inputs. It must emit data only and preserve unknown raw
   input bytes. Test with independently authored correspondences/refusals.
3. Add a read-only trusted native capture path using original source assessment
   and actual held cuts; do not fabricate observations from fixture booleans.
4. Compose with the original UMF/Weft and the separately owned graph collector.
   Derive actual supported home/codec/endpoint subsets; refuse the remainder.
5. Qualify authenticated native mutation/drift/replacement/concurrency controls,
   cleanup and complete guarded release. Review the exact cohort before a new
   source registration or migration can be admitted.

## Open decisions and required evidence

- Include native metadata/statistics/diagnostic paths outside the Truss schema
  in authority/source closure. Denying table values alone does not close the
  retained ordinary-caller statistics counterexample; an equal public result
  cannot establish non-disclosure.
- Freeze exact descriptor schema, source-reference framing and native capture
  bounds without exceeding the complete compiler/source envelope budget.
- Define authority witness ownership/current-generation issuance and prove
  complete required native cuts. Existing source-epoch-empty assumptions are
  not a newly issued native generation.
- Distinguish cluster/database identity and original authenticated connection
  custody from copied names/OIDs or restored installation bytes.
- Preserve original assessment/native numeric extension content; audit any
  existing JSON decode/re-encode path before treating it as lossless source.
- Define explicit migration when release/layout/owner/collation/codec or current
  registered computation selection changes. An unknown new cohort must refuse.
- Full Record-backed edge and row-home realization, managed targets and all
  remaining original acceptance cases remain open after a metadata spike.
