# Original whole-entity query gap — 2026-10-13

The unchanged original `read.key-lookup-whole-entity` query runs against installed Truss0.32 / Weft0.4.5 rebuilt relationship frontend / PostgreSQL18.6 after original public registration, fixture mutation, commit, replay and reached. It returns the correct authored scalar values but fails the original expectation:

- Actual columns: code, name, practiceArea.
- Actual row: uc-1, Lease abstraction, real-estate.
- Missing original fields: addressedBy=['sol-1'], _version=1, _created_by=erik, _updated_by=erik, _original_author=null, _original_at=null.

Runtime retained at `/private/tmp/truss-original-whole-entity-r2-20261013`. This is a failed case, not whole-entity conformance evidence. Existing three passing authority cases remain valid; replicas remain unavailable.

Next work must expose original database facts: Weft owns versioned relationship and native metadata projection semantics; Truss owns authorized scoped object version, journal actor and import provenance observations. Do not populate missing fields from fixture assertions, caller actor strings or synthetic nulls. Relationship keys need exact bounds/truncation and direction-specific source meaning. Reserved metadata names require explicit Truss backend ownership and collision rules; UMF authored member semantics stay unchanged. Existing query_scope grants must not expand to unrestricted journal/import tables. The complete consumer expected shape remains required.
