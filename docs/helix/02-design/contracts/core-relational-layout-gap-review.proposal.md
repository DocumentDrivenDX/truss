# Core relational layout candidate and UMF gaps

The owner selected core Record/Field/Key/Relationship definitions as the ER source and UMF-owned reusable DDL generation. The first [candidate](../models/truss-layout-core-relational-0.1.proposal.umf.json) contains 46 Records, 442 Fields, 59 declared primary/unique Keys and 61 Relationships with ordered core Field correspondence. It retains the original native PostgreSQL archive and pinned source inventory. It is a new authored core 0.7.0 document, not an upgrade/adoption of original native identity.

The candidate is **blocked**, not a valid generator/diagram contract. [UMF validation](../../04-build/evidence/design-audit/core-relational-layout-validation.json) reports valid=false, complete=false: nine KEY_EQUALITY errors and five KEY_FIELD_REQUIRED errors. Required Fields follow explicit NOT NULL or primary-key semantics; nullable unique components remain unspecified instead of being falsely declared required. JSONB and xid8 retain unknown scalar families and native definitions. FK actions/match/deferral remain native correspondence; broad diagram multiplicities do not assert complete enforcement equivalence.

## Concrete reusable UMF work

1. Distinguish physical native key/equality correspondence from portable core tuple equality. The Truss journal, operation and feed keys include xid8, whose family/equality cannot be fabricated as integer or text. Determine an explicit supported native identity/comparator binding, or a core physical-key representation that preserves unknown portable equality. Do not change Truss key columns to pass validation.
2. Represent PostgreSQL nullable unique constraints without equating SQL NULL with missing core values. Existing core Keys require supplied components; five candidate components violate that requirement. Preserve native NULL-distinct/equality and constraint behavior, including any original compound/context semantics. Decide whether this belongs in a core Key capability or a physical binding linked to core Fields; no semantics are silently weakened.
3. Compose existing UMF Record/Field/Key/Relationship projection APIs into a whole-schema operation with native residuals and full original correspondence. Preserve composite field order, target key identity, namespace and unknown native refinements. SQL generation stays in UMF; Truss authors/consumes its layout model and installation policy.

ER rendering can consume core Records/Fields and relationship endpoints structurally, but must report the blocked key interpretation rather than claim fully understood relational metadata. Do not ship the candidate as a complete core model or generate replacement installation DDL from it before the gaps are resolved. Retain the existing qualified source-export path independently.

## Reproduction and boundaries

Run `python3 docs/helix/04-build/evidence/design-audit/build-core-relational-layout.py --check`, then `bun docs/helix/04-build/evidence/design-audit/check-core-relational-layout.ts` from Truss. The builder consumes the pinned declaration inventory derived from the original UMF source; it is a Truss layout-authoring experiment, not a general SQL parser/generator. The checker uses existing UMF validation and retains actual errors rather than converting them to success. Neither tool connects to a database or qualifies native behavior.

The prototype builder and validator currently reference the local pinned UMF checkout. Packaging, browser evidence, reusable native→core correspondence, original lifecycle IDs and whole-schema lowering remain unfinished. The portable model retains complete native content while admitting only the described core structural interpretation; no unsupported type or extension is dropped.
