---
ddx:
  id: truss.weft-accepted-catalog-producer
  type: contract
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: CONTRACT-012
      kind: informed_by
    - id: CONTRACT-003
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: CONTRACT-008
      kind: informed_by
---

# Accepted catalog producer for Weft

This is the native producer handoff for the existing `serializeStorageBinding` API, not a second binding grammar or compiler. Consume Weft's `truss-postgresql-binding/0.1.0` grammar from the pinned compiler source. The serializer checks bytes and basic composition; a positive catalogRevision and matching hashes do not prove acceptance, authenticity or authority. Native producer implementation is pending.

## Original input and output custody

Input is the original admitted installation/executor context, selected accepted revision and exact qualified document/module selection. The producer obtains these through the issuer-owned context, never from arbitrary caller-supplied binding JSON or a connection selected by user data. Original authority/account/transaction admission precedes reads. Caller revision text is only a selector; native accepted revision and source correspondence must be observed.

Read schema_rev, schema_doc, immutable catalog_acceptance_report and the complete selected type/property/key/relationship definitions under one admitted catalog view. Preserve schema_doc ord, doc_id, doc_revision, umf_version, original document text, content_sha256 and validation. Preserve the original acceptance report bytes and its immutable producer/transition/check composition. Bind each definition to its qualified original source locator and actual accepted catalog ID. Do not allocate IDs, search by display name, replace an absent definition with a fixture mapping or reinterpret an incomplete report as complete. Retired/reactivated definitions follow the existing identity/history contract.

Compose the existing basis entries: modelBundle, catalogRevision, acceptedCatalog, layoutProfile, layoutInventory, layoutSql, exporterProfile, namespace, identityProfile, valueProfile, keyProfile, readContextProfile and readContextDefinition. Every original artifact carries its admitted identity, exact bytes and hash. Obtain installed layout/native correspondence from the verified installation inventory and original registration, not merely from a review SQL file or matching table count. Retain unknown source content in original documents; refuse affected unsupported meanings explicitly.

Produce complete entities, properties, keys, relationships and executionObligations. Entity typeId and property ownerTypeId/propertyId come from accepted native definitions; property home/value/presence profile definitions come from original admitted registrations. Never infer a JSONB home from physical props availability. Ordered key/relationship field correspondence and exact equality remain UMF-owned. Weft owns grammar validation, lowering, parameter domains, result representations and compiler obligations. Truss owns authenticated catalog/storage correspondence and actual execution/publication producers.

Pass the complete immutable composition and original model documents to the serializer. Its copied/hash-pinned BindingInput is reusable compilation input, not a portable authorization token. Keep native context custody private and distinct from serializable metadata. This proposal adds no public create-transaction/commit-by-ID API and no independently authoritative signature field.

## Execution and lifetime

Before integrity or user SQL, verify that the artifact's binding/model pins, selected installed layout/profile, original actor/disclosure and definition registrations match the executing affine context. A stale plan cannot silently recompile, remap IDs, migrate a profile or change parameter positions. Recheck current authority and disclosure before publication. A catalog transition may preserve identity while changing semantics; unchanged integer IDs cannot establish a compatible plan.

Owned network calls retain whole-transaction admission and buffered publication; embedded adopted transactions retain caller settlement ownership. Temporary catalog effects and provisional IDs cannot be exposed outside Truss before confirmed outer commit. A plan compiled privately against pending state is not publishable as an accepted durable binding. Disposal releases registration/cache admission and prevents publication; it does not commit or roll back the caller's transaction.

Cache by the complete binding/model/profile composition and original issuer registration, never revision alone. Cached metadata does not bypass per-execution context/authority checks. Do not persist an issuer capability alongside serializable binding bytes. Resource limits for extraction, artifacts, compiler, transport and buffered publication belong to the existing enclosing account; serializer limits do not prove native preallocation containment.

## Independent acceptance scenarios

All scenarios below are planned, not_run. Seed through the actual protected acceptance path and independently inspect stored reports/documents/definitions, not by copying compiler output or the producer's serialized binding. Use the current six query scenarios after obtaining real bindings; keep the existing synthetic corpus separately labeled.

| ID | Independent setup or fault | Required observation |
| --- | --- | --- |
| WCB-01 | Accept two documents with equal local element names in different qualified modules | Binding preserves distinct original IDs/locators and ordered original documents; logical query resolves only its selected qualified source. |
| WCB-02 | Replace accepted document bytes, report bytes or registered definition bytes while keeping claimed hashes | Extraction/admission refuses before compiler or SQL; no repaired hashes or reconstructed report. |
| WCB-03 | Catalog revision exists but report is missing/incomplete or requested definition is not accepted | No BindingInput publication and no fabricated IDs. Original invalid/incomplete diagnostics remain distinguishable. |
| WCB-04 | Compile at revision R, evolve or reactivate before execution | Context comparison either proves the exact pinned composition under the admitted view or refuses; no automatic remap/recompile. |
| WCB-05 | Install review0.13 while supplying the fixture-qualified layout identity | Refuse unregistered profile correspondence despite matching columns. Successful fixture execution does not admit installation. |
| WCB-06 | Change effective read authority after integrity checks but before publication | Withhold all buffered rows; hidden rows never become absent logical values. |
| WCB-07 | Roll back acceptance in an adopted transaction; separately lose network reply after outer commit | Rolled-back IDs/bindings are never public. Confirmed receipt recovery preserves original accepted IDs/report without reallocation. |
| WCB-08 | Unknown source assertion, unsupported note null mapping or unregistered home/codec | Refuse affected capability before SQL without inventing semantics; retain original source. |
| WCB-09 | Cross-engine/issuer plan reuse; dispose during extraction/compile/publication | Original custody mismatch or disposal refuses; no result and no implicit caller settlement. |
| WCB-10 | Exhaust extraction/artifact/frame/publication account independently | Refuse within the admitted producer/driver profile, release private reservations and preserve outer transaction ownership. Postallocation timeout alone fails qualification. |

## Remaining adoption gates

Implement the protected native acceptance reader and original installed registration producers. Admit a Weft profile whose actual storage-layout tuple corresponds to the installation; the current pg17.9-qualified-fixtures profile cannot be relabeled as Truss0.13. Adopt UMF source/transition/check profiles without duplicating metadata logic. Compiler-owner explicit-null interpretation remains required for complete Item.note projection. Exact native roles, OIDs, containment and fault outcomes are implementation evidence rather than guessed design values.
