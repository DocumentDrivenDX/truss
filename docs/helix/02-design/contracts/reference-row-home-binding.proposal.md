# Reference Account/Item row-home binding proposal

For M00–M07, propose the existing row_home_state/row_home_node/row_home_scalar realization for all four original fields in the [source inventory](reference-account-items-field-inventory.proposal.json). This makes the reference storage design concrete while retaining the original fixture and broader props/mixed-home/recursive release requirements. It is a source/profile proposal, not native adoption, a fallback policy or a change to UMF meanings.

The [scalar codec proposal](reference-scalar-codec.proposal.md) supplies exact string admission and the fixture-specific decimal token grammar. Original registered codec bytes, native bindings and qualification remain separate required outputs.

The [reference decoder procedure](reference-row-decoder.proposal.md) defines complete owner collection, state/tree/payload decisions and private whole-Record staging before publication. It consumes these same homes and existing public carriers; Weft retains compiled decoder ownership.

Resolve every property through its original document/module/Record/Field definition and allocated catalog identity. No storage IDs are assigned here. A state binds actual instance owner plus original property-owner type/property identity, root_node_id and complete definition/home/value/source bytes. The root binds the same state/node identities, original definition/source bytes and root slot/parent semantics. Full native/source/authority correspondence precedes decoding; matching a field name or value is insufficient.

| Original field / meaning | Required proposed native projection |
| --- | --- |
| Account.code and Item.code | One owned state and scalar root; one string scalar payload with exact text_value and original_source_bytes, codec_definition_bytes. Required null/absence refuses. Full source/definition/key coupling follows the [code/key proposal](reference-code-key-binding.proposal.md). |
| Item.amount | One owned state and scalar root; one decimal scalar payload with exact original numeric_token plus finite numeric_value equal to the independently admitted decimal(21,3) coefficient/1000. Full source/codec bytes and unused-slot NULL checks follow the [amount proposal](reference-amount-domain-binding.proposal.md). No narrowing numeric(21,3) cast can replace admission. |
| Item.note absent | No state for that original applicable owner/property. Complete authorized visibility establishes absence; a missing/filtered row alone does not. |
| Item.note present null | One owned state and explicit null root; no scalar row. The full admitted definition/source and [presence proposal](reference-note-presence-binding.proposal.md) establish null; a payload SQL NULL or missing scalar alone cannot. |
| Item.note present text | One owned state/string scalar root/payload, including text_value empty string; preserve original text/source/codec bytes. |

For each scalar, every unused boolean/numeric/text/binary/temporal/opaque slot is native NULL according to its selected dispatch. Null/container nodes cannot carry payload rows. Independently prove owner/property state uniqueness, root identity/reachability, complete node/payload membership, no extra child or payload, and exact original profile/source coupling. Empty scalar text is not an empty tree. Incompatible side facts cannot be hidden by a root-only SELECT or an eight-cell compiler projection.

The selected direct reader consumes the complete full-slot CONTRACT-010 source/manifest and protected owner enumeration. The compiled route consumes the exact original home descriptor and Weft-owned codec/presence registration, with owner-wide structural/payload prerequisites and same-affine-transaction prepublication rechecks. Weft's current null exclusion makes the complete note route unavailable until reviewed; it cannot redirect note to props, omit it, or make SQL NULL choose logical absence.

No shadow props copy is permitted to supply missing reference values. Key membership/reservations remain in their separate protected original homes under the UMF tuple/key profile; row-home code storage does not replace key enforcement. Catalog, graph, source and complete journal effects remain atomic under the existing operation/finalization procedures. Failed mutation or uncertain settlement retains original containment/recovery semantics.

Remaining exact outputs: original home/value/codec byte artifacts and hashes, native source/operator/type/security/dependency/resource bindings, protected writer/finalizer/collector realization, independent M03–M07/RD/K/FS observations and accepted Weft mapping. Full deployment selection and broader release/corpus admission stay separate. This proposed mapping alone does not qualify any runtime.
