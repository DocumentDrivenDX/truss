---
ddx:
  id: CONTRACT-013
  type: contract
  activity: design
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
---

# Contract: Native source binding

**Type:** library/protocol. **Version:** isolated structural spike0.1-candidate.
**Status:** draft; not registered or native-admitted.

## Purpose

Retain exact original sources and describe native storage identities without
turning metadata into permission. The first spike freezes only the structural
identity envelope below. Authored Field/Record membership, ordered Key and edge
mapping, actual native capture and the operation-held authority witness remain
required extensions before binding admission. No full-binding or case pass may
be inferred from this envelope.

## Scope and Boundaries

Truss owns native observations; UMF owns semantics; Weft owns compilation.
This pure library accepts supplied original data. It opens no connection and
cannot issue a current-generation, permission or release witness. All original
Truss132/shared158 obligations remain unchanged.

## Normative Surface

`prepare_native_source_descriptor` accepts four exact immutable UTF-8 byte
objects, each1..4,000,000 bytes, with total at most16,000,000 bytes:
`accepted_request`, `accepted_assessment`, `runtime_release`, `native_inventory`.
All must be JSON objects with duplicate-key/Unicode/exact-number validation.
Original bytes MUST remain retrievable from the returned data object unchanged.
Unknown source content MUST NOT be normalized or passed through binary floats.

The inherited strict JSON capacity profile applies to every original object and
to each nested documentJson scan: numeric tokens at most512 characters; every
object at most4096 members; every array at most4096 items; root depth0 with
maximum depth128; at most1,000,000 traversed nodes including object keys.
These are logical parser limits, not native allocation or process guarantees.
The accepted request contains1..256 modules. Descriptor and inventory-specific
bounds below apply in addition. A source inside its byte budget may still refuse
these structural capacities; no prefix or normalized substitute is returned.

The native inventory has exactly:

| Member | Shape | Rule |
| --- | --- | --- |
| version | string | `truss.native-source.inventory/0.1-candidate` |
| installationId | string | Exact nonempty original identity, not an authentication claim |
| database | object | Exactly `systemIdentifier`, `oid`, `name`; positive canonical decimal strings for uint64 system identifier and uint32 OID |
| schema | object | Exactly `oid`, `name`; positive canonical uint32 OID, name `truss` |
| release | object | Exactly `id`, `sha256`; original runtime release identity and hash of the complete original release manifest bytes |
| relations | array | 1..256 closed relation objects |

Each relation has exactly `oid`, `name`, `ownerOid`, `columns`. OIDs are positive
canonical uint32 strings. Names are nonempty Unicode scalar text, no NUL, at
most63 UTF-8 bytes. Relation OIDs and names are unique in the selected schema.
Each columns array contains1..4096 objects, exactly `attnum`, `name`, `typeOid`,
`typmod`, `collationOid`, `notNull`, `dropped`, `generated`, `identity`.
`attnum` is an exact integer1..32767, unique within its relation; column names
are unique. `typeOid` is a positive canonical uint32 string; `collationOid` is
canonical uint32 including0. `typmod` is an exact signed32 integer. Flags are
exact booleans. `generated` is `''`, `s` or `v`; `identity` is `''`, `a` or `d`.
These are observed labels, not proof of native equivalence or comparator support.

Assessment version MUST be `truss.accepted-catalog-assessment/0.1`, with
`securityReady:false`. Its installation/release identity and release SHA MUST
match the inventory and original runtime manifest. Its `modelPins` MUST match
accepted-request module pins in original order. Pins have exactly documentId,
revision, umfVersion (nonempty scalar strings, at most4096 UTF-8 bytes each)
and a lowercase64-digit SHA256. Each module's exact
`documentJson` SHA MUST match its pin; duplicate document identities refuse.
The nested documentJson MUST itself pass strict JSON scanning as an object,
with exact id/umf correspondence to its pin. A matching recomputed hash does not
admit malformed, duplicate-key or non-finite nested source.
This is byte/identity correspondence, not a second UMF semantic validator.

The returned descriptor JSON contains exactly `version`, `scope`, `complete`,
`authority`, `securityReady`, `nativeAdmission`, `sources`, `unresolved`.
Version is `truss.native-source.descriptor/0.1-candidate`, scope is
`supplied-source-structural-correspondence`, complete/authority/securityReady are
false and nativeAdmission is `required`. `sources` contains four ordered
`{role,sha256,utf8Bytes}` references to all original bytes. It MUST NOT copy or
reinterpret source JSON values. No JSON constructor imports a native witness.

## Precedence and Compatibility

This protocol is not accepted by existing ABI2/presence registrations. There is
no automatic migration, new default cohort or current-authority implication.
OID/attnum reuse, same-named recreation, database restore/clone and copied
installation bytes can yield equal metadata; only verified source continuity
and actual held native DDL/source/authority custody can resolve that ambiguity.

## Error Semantics

Malformed/oversized/noncanonical/ambiguous inputs and mismatched sources refuse
with ValueError before returning a descriptor. No partial result, coercion,
semantic repair, truncation, registration or retry authority follows. Native
failure and witness lifetime semantics are not implemented by this pure spike.

## Examples

A native UUID column can be recorded with `typeOid:'2950'` and its actual
relation/attnum; a JSONB column can be recorded with `typeOid:'3802'`.
Neither label authorizes decoding a logical Field. A `home='row'` declaration
without installed stores remains unsupported by later binding admission.

## Non-Normative Notes

This intentionally incomplete first layer supports independently authored
structural controls. Freeze additional mapping/codec/current-witness schemas
and their actual native evidence separately; do not relabel this data envelope
as a completed native binding.
