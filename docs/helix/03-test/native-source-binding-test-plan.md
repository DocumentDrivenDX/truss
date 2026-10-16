---
ddx:
  id: truss.native-source-binding.tests
  type: test-plan
  activity: test
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.native-source-binding.design
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-012
      kind: informed_by
    - id: truss.native-model-correspondence.design
      kind: informed_by
---

# Native source binding test plan

All cases below are required planned work, not passing evidence. A pure assembly
or schema test is not a native observation or permit. The original132 allocation
and shared158 requirements remain unchanged.

| Case | Required observation | Layer |
| --- | --- | --- |
| NSB-T01 Complete source | Descriptor references exactly retained accepted-request/assessment/model bytes and exact committed release; missing, duplicate, hash/size/identity drift refuses. | Pure and native |
| NSB-T02 Unknown content | Independently authored unknown object/array/Unicode/large integer/decimal extension content remains exactly retrievable; a float-rounding or replacement serializer mutant fails. Distinguish original UMF source from canonical native JSONB meaning. | Pure and native |
| NSB-T03 Relation identity | Drop/recreate a same-named source, recreate/restore/clone the database, deliberately reuse numeric OID/attnum values, change namespace/owner, add inheritance/partition/RLS, or substitute another installation: observation refuses without verified continuity despite identical names, locators or public values. | Native |
| NSB-T04 Column identity | Swap attnum/name/type OID/typmod/collation/default/generated/dropped state independently; names or matching type labels cannot repair correspondence. | Pure and native |
| NSB-T05 Field membership | Reuse a Field reference in two Record contexts; each maps to its actual native property membership. Equal property/type numbers from another namespace do not match. | Pure and native |
| NSB-T06 Ordered keys | Swap component order, selected Key, original codec/profile/namespace or native membership bytes; require original UMF encoding and exact native correspondence. | Pure and native |
| NSB-T07 Direction | Reverse edge source/target, replace a target type or key, or confuse relationship type with edge property-owner type; refuse before disclosure. | Pure and native |
| NSB-T08 Occurrences | Parallel native edges retain distinct occurrence/version identities; omission, duplicate or set-collapse refuses independently of equal endpoint/public values. | Native |
| NSB-T09 Home semantics | Actual native-column and JSON homes map explicitly. A `home='row'` tag with no realized stores refuses, including an empty object population. No observed value row is not absence proof. | Pure and native |
| NSB-T10 Bootstrap ordering | Source registration, Subject helper generation and ACL-changing activation have no self-hash cycle or silent snapshot replacement. Earlier source bytes stay immutable and independently inspectable. | Pure and native |
| NSB-T11 Current witness | JSON/hash import, foreign host/operation, different authenticated caller, stale generation and use after closing cannot issue or reuse a native witness. | Native |
| NSB-T12 Changed authority | Alter relevant grants, role membership, helper, source/configuration or writer path after capture; closing checks prevent data release. Do not substitute fixture booleans or one revoked view for complete authority closure. | Native |
| NSB-T13 Bounds | Independently cross each input/output/relation/column/cell/edge/byte/deadline limit, including long endpoint keys repeated across parallel occurrences. Refuse whole output and clean up; no truncation or unbounded prefix acceptance. | Pure and native |
| NSB-T14 Compatibility | Existing ABI2 and presence registrations reject the new binding/witness registration. Unknown codec/cohort/version refuses. Explicit migration preserves original bytes and cannot relabel an old native proof. | Pure and native |
| NSB-T15 Whole path | Actual authenticated caller/source, original UMF/Weft, actual SQL/driver/result, current witness and closing release compose on the same native cut; tampered header/cell/contributor and stale source refuse. | Native end to end |
| NSB-T16 Recovery | Failure/cancellation/uncertain cleanup never emits partial data or automatic retry authority; original host transaction ownership and qualified pending/unknown outcomes remain. Verify owned fixture cleanup independently. | Native end to end |

## Evidence requirements

Pin original source and test inputs, runtime/driver/compiler/owner versions and
artifacts, actual native observations, both positive and independently mutated
negative expectations, first failures, repairs and cleanup. Distinguish supplied
metadata, actual native capture, source endpoint correspondence and any stronger
custody proof. Actual authority/caller/source/generation must not be manufactured
from identical request values or fixture flags. No case receives a pass from a
neighboring case, metadata-only test or unchanged public result.

Use isolated owned PostgreSQL resources and serialized native timing windows.
Databricks needs its approved dedicated endpoint, two working authenticated
callers and the authorized isolated `client_dev` schema with cleanup. The shared
`data-gateway` warehouse remains off-limits. Local Spark/Delta or a serverless Job
cannot qualify Databricks SQL/Unity Catalog security. Native engine evidence is
kept separate from portable parser/type/schema tests.


## Structural spike capacity addendum

The inherited capacity profile is explicit in CONTRACT-013:1..256 modules,
512-character numeric tokens,4096 object members/array items, rootdepth0 through
128, and1,000,000 nodes including object keys. Individual source bytes remain
1..4,000,000, aggregate at most16,000,000. Test the largest admissible supplied
shape and the first failing shape independently, with matching recomputed hashes
so capacity failures cannot be confused with stale-source correspondence.
No capacity control establishes native allocation/CPU or authority guarantees.


## Issued model/native join component qualification

The actual-context candidate advances NSB-T01/T04/T05/T06/T09/T13/T14 component
prerequisites only. Independently expected complete qualified Record/Field/Key
identities, ordered native IDs, JSON keys and physical slots must survive; extra
native members, missing issued non-Key members, duplicate records and changed
source/column definitions must refuse. The stock host must preserve caller work
on refusal and owned fixture cleanup must be independently confirmed. Full
namespace/codec/graph/native continuity and guarded release remain required.

A separate issued-requirements decoder admits at most16,000,000 bytes while all
existing owner-evidence entry points retain8,388,608. Retain the actual large
compiler-context request/report proving this distinction, exact-limit and first
failing byte controls, and unchanged duplicate/number/Unicode/depth/container/
node checks. A pure capacity pass does not qualify the large report against an
actual native model, prove peak memory, or complete NSB-T13.

The model join returns immutable inspection data retaining the actual context
and parent. Supplied bytes, its publicly constructible data class, matching
hashes and restored physical metadata must never issue a current native witness.
The native component test has a dedicated TRUSS_NATIVE_MODEL_JOIN_QUALIFICATION
opt-in and TRUSS_NATIVE_MODEL_JOIN_EVIDENCE directory; the older paired test's
flag must not activate it. Default discovery with optional Weft unavailable must
skip before native setup. No existing ABI/default/cohort/dependency is repinned.
