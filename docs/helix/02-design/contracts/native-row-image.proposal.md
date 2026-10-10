# Private native row-image correspondence profile

This candidate refines CONTRACT-001's complete native OLD/NEW image handling.
It is a PostgreSQL16.15 component profile, not portable logical UMF encoding,
protected event/prestate admission or a new public Truss API. Existing UMF APIs
retain the native routine source; no UMF numeric or compiler semantics are forked.

The private native codec emits UTF8 domain `truss.row-image.<kind>/0.1`, one NUL,
then the original PostgreSQL composite binary frame. Kind is state, node or scalar.
The frame has a big-endian signed four-byte field count, followed by each original
ordered field's unsigned four-byte native type OID, signed four-byte payload length
and complete payload. Length -1 means explicit NULL and contributes no payload;
zero means present empty payload. Other negative lengths, extra/truncated fields,
unknown kind/version/type profile and trailing bytes refuse. Complete input/output
is bounded to eight MiB; no partial image may stand in for a complete row.

State/scalar have thirteen fields; node has ten. The selected native column
validator binds complete names/order, native types/nullability/typmods/collation,
dropped/array membership and inheritance before encoding. The Python decoder
matches those ordered type OIDs and required/null slots, primitive integer/Boolean/
instant widths, strict scalar UTF8 native text and native Boolean representation.
Native text NUL refuses; opaque bytea retains arbitrary bytes including NUL.
Native numeric and temporal payload interpretation, finite domain/facets, lexical
correspondence and table CHECK/event/provenance proof remain separate obligations.
A valid binary frame does not authenticate an original PostgreSQL datum or event.

`_row_image.py` retains the exact immutable input bytes, immutable cell offsets and
lengths, and read-only memoryview payload spans. NULL returns None; present empty
bytes returns a zero-length view. Original numeric_token, temporal_text,
codec_definition_bytes and original_source_bytes remain separate original cells.
The native numeric datum and temporal instant are not converted to Python float,
JavaScript number, display strings or a reconstructed logical value. UTF8 validation
creates temporary text/copy work; span retention does not qualify whole heap/copy/
work/deadline accounting. Native image length preflight likewise does not qualify
complete native materialization/detoasting/numeric-send/resource admission.

The source suite replays ten retained native image vectors and independent framing,
OID/null/length/primitive/UTF8/boundary corruptions. These are source-decoder checks,
not installed-wheel or protected native observer qualification. Original complete
OLD/NEW/prestate/candidate/allocation source and current scope/subject/role evidence
must be independently bound before the observer compares these images or advances
operation/touch generation. Missing retained OLD association after cascade cannot
be repaired by a live parent lookup or by matching image hashes.

The private event-attribution component now consumes separately supplied immutable
prestate/candidate image collections under explicit count/byte bounds. It requires
complete byte equality for the actual event image, resolves node/scalar ownership
through retained state/node images, and refuses duplicate keys or conflicting
state associations for the native globally unique node identity. It retains OLD
and NEW images and associations separately, then deduplicates only the event-local
owner/property touch set. Owner/catalog IDs preserve their signed native domains;
edge property-owner type remains independent of relationship discriminator.

Original INSERT/UPDATE/DELETE side availability is explicit. Changed ownership or
reparenting projections do not grant support: the governing original operation
must independently permit the complete old/new scope and already hold all required
guards. Mapping completeness, native provenance, semantic codecs/tree grammar,
current authority and resource admission remain external. The component performs
no live lookup, native DML, generation advance or permission resolution.
