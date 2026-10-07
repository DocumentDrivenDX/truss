---

ddx:
  id: EVIDENCE-UPSTREAM-INTERFACE-REFRESH
  type: status-report
  activity: build
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.design-coordination
      kind: informed_by
---

# Upstream interface refresh — 2026-10-05

## Remote Truss frame refresh — 2026-10-06

Fetched Truss origin without changing checkout files. Main remains d3dcddeec888cae4336b18af43a31fd19b93cf79; the newly observed frame-status branch is d30e72f332a4e6cbc30cfed0cca4001210e49bd1. Its ten-file documentation delta adds a parking lot, factual frame status and five open-question recommendations. It adds no runtime implementation and is not merged main or owner acceptance. Current sibling filesystem baselines remain UMF 16c35e8d943769ccfa7bb57d16785aa7159abe65 clean and Weft a95da1f82baf9148ec5235a0f2002d059a8ca3b5 with the existing PostgreSQL working changes.

Reconciliation: apply the two factual accepted-ADR references from “PRD not authored” to the existing draft PRD. Preserve their decisions/frontmatter. Do not replace this worktree's 45-story/56-requirement design with the branch's older 39-story/50-requirement status. Its recommendation for PostgreSQL 16/17/18 does not select versions or supersede CONTRACT-005's corrected-patch prerequisite. Proposed scale/latency recommendations remain owner choices, with measurements qualified at their original scope; the edge-limit tail remains a concrete future experimental task, not an owner preference.

The branch's deferred query-language/typed-view/optimization entries must be reconciled with the user's later toolkit/Weft direction and this worktree's B-012 bridge/P01–P06 handoffs before adopting its parking lot. Weft still owns compilation; no Truss compiler is introduced or existing bridge scope silently parked. UMF JSON-like/temporal/assertion gaps remain version/subset-specific, not permission to drop content or invent upstream semantics. No branch merge/cherry-pick or recommendation adoption was performed. This refresh identifies the overlapping framing delta and prevents blanket replacement of the governed design; complete owner decisions/shared reviews remain open.

## Converted-ingress scoped owner review — 2026-10-05

UMF chat `01a10926-e4f9-7842-914f-4fe4db9fc88b`, completed turn `01a10ea5-c28e-7613-af53-1cb529bc3e0c`, found no conflict in Truss's original-source/adapter/loss-report preservation proposal. Review is limited to that boundary: document revision tokens do not establish implemented package resolution; exact loss-report digests prove byte integrity, while meaning requires the pinned adapter validator. This is owner design feedback, not a new merged upstream capability or a native acceptance pass.

## Latest coordination observation

Read-only recheck: UMF main remains `16c35e8d943769ccfa7bb57d16785aa7159abe65` clean. Weft remains `a95da1f82baf9148ec5235a0f2002d059a8ca3b5`, with uncommitted PostgreSQL backend, TD/STP-003 and build-plan changes. Its live chat still reports waiting on environment approval; no native pass or new owner approval is inferred. The earlier baselines below are historical observations.

Sent the Weft owner the current CONTRACT-010 temporal fidelity/comparator distinction and CONTRACT-005 historical edge-authorization obligations, retaining its ownership of lowering and Truss's ownership of storage/policy. The message explicitly carries draft scope and no installed layout change. Delivery is coordination evidence, not agreement or implementation qualification. Review remains pending; Truss does not restart services to resolve the other chat's environment approval.

## Observed baseline

Read-only inspection of UMF main at `16c35e8d943769ccfa7bb57d16785aa7159abe65` and Weft at `48f9a9c66439e7b797adcf336506ecb5b86a6a4a`. Weft's application-read frontend is now merged; backend registration/emission is active uncommitted work. These are design/interface observations, not Truss integration tests or upstream approval of a Truss design.

| Source | SHA-256 at inspection |
| --- | --- |
| UMF CONTRACT-045 cross-document references | `4a81d8a0df1301b7a63d9dcbf934f187c6322b3e6411bcc78b4ffeff1a1e5521` |
| Weft CONTRACT-002 backend interface | `fb33dda4b9cfd822a9f31512c1fa0ff348bbb795145ce6be243998dbea2c7388` |
| Weft CONTRACT-004 application reads | `02274cde86dd042c47035200297f329316d807b49b606da8327734ef32c552cf` |

Sources remain owned in their sibling repositories. Digests identify the observed text and are not immutable release pins, particularly for uncommitted B-003.

## UMF identity dependency

CONTRACT-045 is a proposed successor envelope with document revision, exact dependencies and offline package resolution. It explicitly states that no core schema/public API/migration is implemented. Truss must consume this work instead of inventing an incompatible external-reference syntax or resolving bare local references across documents.

The proposed lineage identity is `(document.id,module.id,element.id)` and a definition adds `document.revision`. This directly informs D-04's storage reconciliation: document-qualified logical ownership and revision-qualified definitions must be mapped separately from generated integer storage IDs. Equal names cannot collapse identities. Unknown `revision`/`dependencies` members in older envelopes cannot acquire successor semantics merely because their names match.

Current relationship endpoint rules remain in-document until their future migration is published. Thus CONTRACT-045 alone does not make Truss cross-document relationship acceptance implementable. Package validation must precede relationship resolution when upstream support exists; an unresolved required target blocks, without network fetch or latest-revision fallback. The full PRD remains, with this dependency explicit.

## Weft merged frontend and developing backend

B-002A now supplies explicit 0.2 application-read plans. Public/native backend qualification is still incomplete. B-003 develops `weft-backend/0.2.0` alongside retained 0.1; no Truss profile should infer compatibility from a shared backend name.

Truss's future mapping must provide exact logical identity coverage, recognized property-home/type/presence representations, authored key selection and comparison, relationship access and obligations. Weft validates structural emitted columns, types, source identities, carriers and typed slots; independent native SQL/result equivalence remains Truss/backend qualification work. These checks do not inspect the actual stored data or establish database constraints.

Explicit native null requires a recognized binding capability (`value.nativeNull` in developing B-003), never optional availability alone. Structured numeric leaves use exact strings in the declared typed JSON carrier. Truss's JSONB source representation therefore needs a declared decoding transform and evidence; generic numeric JSON decoding cannot satisfy it.

The entity-page profiles require a complete authored key in ASC order and LIMIT through 1,000. Truss canonical key text is not automatically the logical ordering representation: decimal numeric equality/ordering and composite component ordering need qualified access paths, not naive lexical order of `object_key.k`. Timestamp authored-text identity also must not be replaced by instant identity. Use component mappings and independently test Unicode scalar ordering versus database collation.

Initial relationship reads are directed, one source/target, named target key, no association Record, with exact multiplicity retained. Truss's unique endpoint-pair storage cannot silently erase parallel association instances outside that subset. Broader Truss requirements remain separate future capability gates.

## Required follow-through

Update Truss mapping design against finalized B-003/B-004 before implementing lowering or publishing package ABI. Keep Rust registered backend distribution with Weft's owner review; Truss core remains TypeScript and does not implement a second frontend. Add independently expected numeric/composite key ordering, null/presence and related multiplicity cases to the Truss integration test allocation. D-04 and D-08 remain open; this refresh narrows their concrete dependency questions without declaring them solved.

## Follow-up observation: B-003 committed

Weft is clean at `2348b62573e08772429b35a66fa8b7b4615c7f25` (`Implement B-003 registered backend interface and conformance gate`). CONTRACT-002 now states the library boundary is implemented as `weft-backend/0.2.0`; ADR-002 accepts the structural boundary. Read `docs/helix/04-build/evidence/B-003-backend-interface.md`: evidence covers component tests, independent synthetic fixture SQL and real-browser parity. Its SQLite fixture is explicitly not a Truss backend qualification.

Truss can design its mapping against this committed library boundary rather than the earlier uncommitted observation. Public compile/Python/WASM wrappers and production native backends remain Weft B-004–B-007; distribution and exact host wrappers still require joint integration review. No Truss support claim follows from the upstream synthetic plugin. Preserve the earlier digests as the historical inspection; use new immutable commit/file pins in the eventual integration receipt.

The UMF coordination chat acknowledged Truss's local-reference/relationship boundary. It reports native regression verification blocked by unresponsive Docker and an OrbStack restart decision. This is an upstream evidence limitation, not permission to restart shared services or treat unrun native checks as passing. UMF main remains clean at the previously recorded commit.

## Follow-up observation: B-004 merged

Weft is clean at `a95da1f82baf9148ec5235a0f2002d059a8ca3b5` (merge of implementation `95da88e`). CONTRACT-003 and B-004 evidence now establish public `compile_json` transports: Python `weft.compile_json` and explicitly initialized browser WASM with a thin TypeScript wrapper. Both use the same Rust compiler; Truss must consume these transports rather than build a language-specific resolver. Default runtime registers no production adapters: Truss compilation still refuses `WFT-BACKEND-MISSING` until its backend is registered and qualified.

The upstream receipt reports 38 core tests and byte-identical public outcomes for 1,273 cases on CPython 3.12.14/macOS arm64 and Chromium 153.0.8010.12. These are upstream component claims, not independently rerun Truss evidence, PostgreSQL execution or broader wheel-platform support. Fixture SQLite execution cannot qualify Truss. The browser wrapper rejects unpaired surrogates and retires after a WASM trap; host integration must recreate its module context rather than retry a poisoned instance. Exact strings, ordered carriers, verified model/binding byte hashes and typed execution obligations remain the integration boundary.

D-08 now targets the implemented compile/backend 0.1/0.2 pairing and eventual production-backend composition. Package publication, Rust backend registration ownership, native PostgreSQL result parity and Truss executor obligation discharge remain open. Some upstream contract prose still says B-004 is in progress; the immutable implementation/evidence pin above distinguishes observed completion from that stale wording.

## Active B-005 observation

Weft HEAD remains a95da1f, but the working tree is no longer clean: PostgreSQL crate/native probes and TD/STP-003 changes are in progress. Read the active TD-003 storage-owner reconciliation. It correctly separates stale primary Truss checkout from active flat-layout draft, refuses unsupported home=row, uses typed authored key components rather than canonical key text ordering, and requires exact recursive/presence carriers plus owner profile approval. These are uncommitted proposals, not stable integration pins or native support evidence.

Sent targeted review requests to Weft for model/namespace/layout/exporter pins and D-04/05/08 ownership, and UMF for valid unresolved/package/cycle semantics. Awaiting replies is not recorded as owner approval. UMF HEAD remains clean at 16c35e8d; its native verification limitation persists, and no shared service restart was requested.

## UMF owner boundary review received

The UMF owner chat completed its requested review: current resolved local relationships support self-reference and mutual cycles; missing endpoints/target keys are invalid. Truss provisional/skip cannot change that validity. Proposed CONTRACT-045 would permit cross-document cycles in a verified package and preserve unresolved external references without a package as complete:false, blocking operations requiring their meaning. Cross-document relationship endpoints need a separate versioned contract/migration. D-04 remains gated; stubs/flattened identity have no current support. This is owner boundary confirmation, not approval of Truss storage changes or native qualification.

Also checked UMF CONTRACT-001's module namespace rule: naming scope is not a DDD bounded-context declaration. Corrected Truss CONTRACT-005's rationale to a local policy-unit choice rather than redefining UMF core semantics.

## Scoped catalog-view provenance review

UMF owner completed turn `01a10ed7-5d5a-7061-ad5e-4fc7ec6c6552`: no direct conflict found in unknown-extension preservation, projection qualification or separation of UMF validity from Truss provisional status. Requested explicit definitionPin resolution to exact accepted document revision/archive and key ownership by its Record. CONTRACT-003, catalog-view declaration/schema now carry acceptance revision/document ordinal/revision/digest, authored pointer and extraction profile; key type-local identity resolves the owning Record in the admitted closure. Retirement/reactivation remains a Truss product decision. This is scoped feedback and a Truss refinement, not universal owner approval or native qualification; confirmation of the revised provenance remains pending.

UMF confirmation turn `01a10ee0-a40a-7663-916d-b3f2e6506b72` closes both scoped catalog-view concerns: exact accepted document/definition provenance and key owning-Record/component ordering/ownership. The owner explicitly limits this to design alignment, without runtime support or broader approval. Weft mapping-basis review, Truss lifecycle selection and physical/native profile qualification remain open.

## Enforcement-report vocabulary inspection

UMF owner portable-key review completed turn `01a10efc-00e8-7343-a31d-b7d4fddaf508`: no conflict in the portable equality subset or stable-ID mapping. Corrects the earlier partial evidence inspection: `src/index.ts` publicly exports `encodeCoreKeyTuple`, and later implementation-plan evidence records public activation and Key gate admission. Dispatch supports core 0.6.0/0.7.0 but has no 0.8.0 path; pin an evidenced envelope until that compatibility gap closes. Truss's remaining dependency is version-pinned public package/API consumption and Bun/Chromium parity plus injective native transport/equality/collation. Decimal ordering stays separately qualified. This scoped review does not qualify Truss native key derivation or approve the separate compact-decimal profile.

Portable-key source inspection at UMF `16c35e8d943769ccfa7bb57d16785aa7159abe65`: CONTRACT-040 owns `umf-key-tuple-v1`, exact fixed-scale coefficient equality, nonportable/null/absence refusal and stable opaque key IDs. `src/model/key-tuple.ts` implements internal `encodeCoreKeyTuple` with receipt version 1.0.0/2.0.0; the implementation plan records scoped internal Bun/Chromium golden-vector evidence. Public API/native binding/migration qualification must be checked separately. Truss CONTRACT-001 and ADR-006 now require portable-profile reuse, preserving explicit stable-key-ID/local-number mapping and native byte carrier obligations. The proposed compact decimal profile is separate rather than a universal replacement. Weft was sent this correction/scope clarification for its pending review; source inspection is not a new owner approval.

Configuration refinement baseline check: UMF remains clean at `16c35e8d943769ccfa7bb57d16785aa7159abe65`; Weft remains at `a95da1f82baf9148ec5235a0f2002d059a8ca3b5` with its existing B-005 PostgreSQL backend/design/test work uncommitted. Truss configuration admission, immutable endpoint reservations and original replay provenance are Truss mutation/storage ownership. They introduce no UMF validity rule or Weft compiler behavior. No new sibling acceptance or native support is inferred from unchanged HEADs or this inspection; pending execution/catalog mapping review remains pending.

At UMF owner baseline `16c35e8d943769ccfa7bb57d16785aa7159abe65`, CONTRACT-040 separates authored ideals/refinements from native enforcement; CONTRACT-005's DDD invariant expressions remain opaque with DDD_INVARIANT_OPAQUE. `src/validation/facets.ts` retains unknown facet members/units with warnings rather than interpreting them. Truss CONTRACT-004 and STP-025 now preserve those meanings: explicit extraction profile, opaque none status, no document-supplied code, and separate Truss validator/native evidence. This is source inspection, not a new owner acceptance or runtime qualification.

## Scoped storage-key binding review

UMF owner completed turn `01a10f0a-ee90-76b3-b975-8c8d5cbb39f6`: no semantic conflict found in the separation of portable identity from sparse/timestamp storage uniqueness. Binding-derived provenance retains the exact binding artifact and owning Record separately. Component pins must resolve to exact fields owned by that Record, as required by CONTRACT-003 admission. Sparse rules cannot provide a total relationship target Key or complete import identity. This closes this scoped semantic review only; native enforcement, migrations, package/API consumer parity and Weft mapping review remain open.

## Acceptance diagnostic preservation review

UMF owner turn `01a10f24-7b42-7453-a7a2-4f45b2be8b66` found accepted reports lacked dedicated diagnostics despite valid documents carrying warnings/partial interpretation. Truss now retains AcceptanceDiagnostic entries on accepted reports and separate exact per-document interpretation evidence/completeness. Complete Truss assertion inventory does not imply complete UMF interpretation. Rejection boundary otherwise aligned in the scoped review. Revised preservation confirmation remains pending; no native/runtime qualification follows.

UMF confirmation turn `01a10f26-0cb3-7633-aba8-cf055a458f7f` closes the scoped accepted-diagnostics preservation correction: exact warning/producer evidence survives, interpretation completeness remains separate from assertion inventory and required unsupported meaning still refuses. This is scoped semantic alignment only; report schemas and native execution still require their own evidence.

## Bootstrap statement correspondence review — closed owner assessment, unresolved capability

UMF completed review `01a10f60-85b3-7373-82da-297a61a06324` against `16c35e8d943769ccfa7bb57d16785aa7159abe65`. Flat async `exportPostgresqlSql` and ordered native nodes do not qualify complete exact output/source correspondence. DDL declarations explicitly remain `complete:false`. Required UMF-owned capability: complete exact per-statement bytes, separators and source paths, independently verified to compose the full export. CONTRACT-008 now records this confirmed dependency and blocked candidate behavior; Truss physical inventory authoring can proceed independently. No parser/backend code or sibling files changed. Review closure does not mean capability implementation closure.

## Uncommitted Weft PostgreSQL boundary refresh

Weft HEAD remains `a95da1f82baf9148ec5235a0f2002d059a8ca3b5`; its working tree contains an untracked PostgreSQL primitive crate/native probe directory and modified TD/STP-003/build docs/Cargo files. UMF HEAD remains `16c35e8d943769ccfa7bb57d16785aa7159abe65` with clean primary working tree. Repository head alone therefore does not describe all active Weft work. The following exact original file hashes scope this observation.

| Working-tree file | SHA-256 |
| --- | --- |
| crates/weft-postgresql/src/lib.rs | `8ad0996c859ac8f518583d08dff2524eb7365096726639785983c1b468025f53` |
| docs/helix/02-design/technical-designs/TD-003-truss-postgresql.md | `fb855026c5e5a9069e5b98989d007ada2eec0e37019c15cb7aef93f4ed36782b` |
| tests/truss-postgresql/README.md | `6b5a1f3f3afc6eed06b427f99ebc1e0439860adeac436fd120333ba8320b1c80` |

Observed primitive source exposes separately quoted `Identifier` components, rejects empty/NUL/>63 UTF-8-byte identifiers, and assigns ordered exact lexical typed parameter slots with a 1,024-slot limit. Its tests are source observations here, not rerun native/compiler qualification. It performs no IO, has no storage registry entry and is not a Truss backend. Native probe README explicitly uses the Truss draft layout worktree, retains full mapping/context/value/relationship/Rust/Python/browser gates and makes no approved-table support claim.

Truss must independently admit the selected server identifier profile before using emitted qualified names; no truncation or merging namespace/object strings. A compiled operation exceeding Weft's selected parameter profile remains compiler/resource unavailable, not batched/split/reexecuted silently. Weft's 1,024 SQL slots and the Truss candidate's 1,024 submitted group operations are different units/profiles, with no cross-product support inference. Native receipt statement placeholders remain internal administrative statements, not a second public SQL compiler. UMF DDL/exporter ownership and Weft backend registry/mapping/obligation adoption remain unchanged. No final shared ABI approval or bucket/native mapping review follows from these primitive files.

Weft v0.2 compile-response inspection confirms modelPins hard-code UMF 0.7.0, backend identity/version/target/interface, bindingSha256 and generic id/parameters/owner/failureCode obligations. It supplies no dedicated top-level Truss native layout/epoch/bucket/snapshot fields. CONTRACT-007 now requires original binding custody and recognized exact obligation/target admission rather than fabricating schema fields. Exact shared Truss mapping/binding/obligation IDs remain an owner prerequisite; generic shape is not a reviewed native ABI.

## Receipt native xid8 representation review

Current UMF `src/adapters/postgresql/column-metadata.ts` and `declarations.ts` have no xid8 core scalar family mapping. Both preserve original native column content rather than inventing an integer family; declaration extraction remains complete:false and reports unresolved families. Truss's synthetic `check-receipt-native-type.ts` probe passes seven expectations: all three original columns/unknown content retained, xid8 core family absent, bytea binary and int8 integer known projections. This is synthetic metadata evidence only, not real PostgreSQL parsing/export/native type resolution or complete bundle correspondence.

Receipt layout adoption must retain qualified native xid8 identity and original context through the UMF native adapter/extension, without integer/bigint substitution, dropped unresolved column or core-family support claim. Exact AST/catalog/import/export round-trip/native lookup and complete generated statement correspondence remain owner/adoption prerequisites. The new draft storage provenance does not require a second Truss model parser or an UMF core scalar family change; it requires honest preserved-native representation and explicit versioned evidence.

## Receipt draft SQL owner round-trip evidence

`check-receipt-ddl-roundtrip.ts` imports both unapplied receipt layout/statement sources through current UMF's existing pinned `@libpg-query/parser@17.6.10` backend and exports them through its codec-loss and AST deparse/reparse guards. Both pass; original source archives remain byte-identical. `receipt-ddl-roundtrip.json` records input/output SHA-256, scoped diagnostics and generated owner exports. This is owner source/API probing, not packed public package qualification.

Partial declaration extraction is explicitly complete:false: layout yields three table declarations and two unhandled statements (sequence/index), while the statement fragment yields no declarations and seven retained unhandled statements. Original writer xid8 remains an unresolved native type without guessed core integer. This evidence establishes scoped syntax/codec/AST round-trip preservation, not native SQL execution, catalog resolution, privileges, complete emitted-statement/source correspondence, full UMF physical capture or installed layout support. The missing complete exporter correspondence API remains the named owner prerequisite; no local SQL splitting/parser replaces it.

## UMF receipt preservation owner response

UMF owner chat completed scoped review at cursor `c5df57a4-e14c-4b66-bd0e-5e514a291b10:19`: native xid8 type-node/source preservation requires no additional UMF capability. Portable type interpretation remains unresolved; decoding/equality/transaction use needs a separately qualified PostgreSQL binding. Complete exporter statement/source correspondence is still the same missing owner output; AST round-trip cannot establish its inventory. This closes the preservation-capability question only, not native semantics/layout adoption or exporter readiness.

## Remaining native draft owner round-trips

`check-native-draft-roundtrip.ts` passes seven additional current drafts through the existing pinned UMF PostgreSQL parser/codec/AST export/reparse plus exact source preservation and deterministic JSON reload. `native-draft-roundtrip.json` records source/export hashes and scoped partial declaration diagnostics. Bucket layout yields three declarations/three unhandled statements; bucket observation zero/seven; admission layout one/zero; admission statements zero/three; migration receipt layout one/two; receipt statements zero/two; head admission zero/two. Every declaration inventory remains complete:false, including the one-table fragment with no unhandled statements.

This syntax/archive evidence includes the head function statement but does not compile or execute its PL/pgSQL body. Native name/type/function/operator resolution, SQL parameter execution, privileges/current authority, concurrency, complete exporter source correspondence and target installation remain unqualified. Original SQL is retained rather than semicolon-split into guessed correspondence; no new parser/export implementation or schema installation was introduced.

## Current creation-alias ownership review

Weft chat `01a10d9e-a65f-73a3-a008-65f60d787b8b` completed the scoped update at cursor `43c2e7f2-f7be-411c-9847-f1a292139349:22`: no ownership conflict is apparent; Truss owns creation-alias allocation and mutation custody, and Weft consumes the resulting admitted storage mapping. No compiler ABI change follows. This is ownership alignment only, not production binding adoption, native allocator validation or completion of the broader interface gates. Current owner direction treats existing UMF capabilities as sufficient; historical missing-owner-output descriptions above do not authorize new UMF prerequisites.

STP-007 now supplies A01–A08 independently expected native alias schedules, including object/edge correspondence, invalid references, forged locators, rollback/nonreuse, owned deletion, complete bidirectional scope and later-invocation separation. These are planned runtime tests; the thirteen executed admission controls establish decoded shape only.

## Weft compiler-plan integration observation — 2026-10-06

A compact live thread observation reports active work connecting candidate mappings to resolved Weft plans and exercising both storage homes through the compiler. Cursor 68c1d315-f478-4884-b7f9-421ce10bc5d1:1 identifies that observation; no completed integration or accepted Truss binding is implied. Truss’s routine ACL/grant projection changes only installed-policy/bootstrap evidence, not Weft compiler ABI, parameters or value mappings. Existing source/profile adoption gates remain.

Weft’s next live observation at cursor 68c1d315-f478-4884-b7f9-421ce10bc5d1:2 reports B-005 work checking authored page key fields/order against the backend binding. No completed binding adoption or paging qualification is implied. Truss’s installed-policy/RLS carrier changes remain outside compiler ABI and page-key ownership; original Weft mapping and execution gates remain independent.

## Weft scalar-sequence integration observation — 2026-10-06

Compact live observation at cursor `68c1d315-f478-4884-b7f9-421ce10bc5d1:3` reports active B-005 work: scalar-item sequences compile for JSONB and complete row-tree storage; native ordered-duplicate/empty-array checks are next, and recursive items/maps/structured values remain in scope. This is owner-reported progress, not independently inspected code/native evidence or Truss binding adoption. The first complete PostgreSQL integration milestone consumes the selected accepted Weft binding and independently expected records without duplicating compiler logic. No new UMF work is requested.

## Weft optional-sequence observation — 2026-10-06

Live compact cursor `68c1d315-f478-4884-b7f9-421ce10bc5d1:4` reports active optional-sequence compilation with explicit presence envelopes and corrected JSONB wrong-container refusal; native tests, including explicit-null rejection, are in progress. The latest tool marker is failed, so no test-pass claim is recorded. This is owner-reported work, not accepted Truss binding/native qualification. Truss's external guard/rule queries do not alter compiler ABI or presence semantics.

## Weft whole-entity integration observation — 2026-10-06

Compact cursor `68c1d315-f478-4884-b7f9-421ce10bc5d1:5` reports active whole-entity queries passing on PostgreSQL across both homes, an added small-cursor positive case and pending exact nested numeric/corrupt structured-field observations. This is owner-reported progress with no independently inspected new hashes/results or Truss adoption claim. A scoped boundary message reports packed public reference-host parity, optional host-owned compiler and per-call original mapping/decoder/obligation checks; asks only for concrete existing-boundary conflicts. No ABI change, restart, upstream UMF feature or reduced structured-value scope was requested.

## Weft complete-tree observation — 2026-10-06

Live cursor `68c1d315-f478-4884-b7f9-421ce10bc5d1:6` reports active complete-tree reachability/orphan/scalar-child/duplicate-property checks with each node visited once and disconnected cycle reporting. This is owner-reported progress; no new source hashes/native results or accepted storage binding were independently inspected. Truss collector scheduling remains route-qualified original catalog closure, separate from Weft's stored-value decoder traversal. The earlier boundary review request remains delivered, not accepted.


## Weft recursive codec observation — 2026-10-06

Compact live cursor `68c1d315-f478-4884-b7f9-421ce10bc5d1:7` reports an active turn with descriptor-directed numeric/presence encoding connected to JSONB compound projections; equivalent recursive row-tree decoding remains required. The latest tool marker is completed, but the owner turn remains in progress. No independently inspected new source hashes/native receipts, full recursive support or accepted Truss binding follows. STP-020 now makes recursive direct/compiled and independently expected parity explicit for each selected home. UMF remains sufficient; no compiler implementation or upstream feature request is introduced here.


## Weft row-tree continuation — 2026-10-06

Compact cursor `68c1d315-f478-4884-b7f9-421ce10bc5d1:8` confirms an active B-005 turn adding recursive row-tree decoding using descriptor-driven encoding across both property homes. This is a specific live owner task, not a completed recursive/native support claim or independent source inspection. Truss's Q04 handoff now explicitly distinguishes prepared statement descriptor format from actual result format; no compiler decoder or ABI change is requested. STP-020's independently expected recursive home parity remains the acceptance boundary.


## Weft typed row codec observation — 2026-10-06

Compact live cursor `68c1d315-f478-4884-b7f9-421ce10bc5d1:9` reports the active owner row codec following exact member identities, sequence ordinals and map keys, reading native payload columns, validating the typed tree and feeding the shared descriptor encoder. Existing native-case checks and additional recursive fixtures remain in progress. This is owner-reported implementation progress, not independently inspected new code/hash/native receipts, complete recursive support or Truss binding adoption. Truss's direct/compiled independent parity requirements remain unchanged. Bootstrap catalog routes resolve native definitions and dependencies, separate from Weft's stored-value decoder; no new upstream feature or compiler ownership is introduced.


Weft compact observation (cursor 68c1d315-f478-4884-b7f9-421ce10bc5d1:10): chat remains active; owner reports extending native PostgreSQL execution to valid parameter-boundary cases with independently chosen fixture values and expected results. This is current owner progress commentary, not independently inspected native evidence, accepted Truss binding or completed recursive-value support. Truss's shared-role admission refinement does not alter compiler ownership or ABI.


Weft compact observation (cursor 68c1d315-f478-4884-b7f9-421ce10bc5d1:11): active owner reports duplicate state/root/payload corruption probes passing on PostgreSQL after independently removing fixture uniqueness constraints, with generated observations reporting both affected rows; 76 valid native cases reportedly still pass and embedding parity is being refreshed. This is owner-reported progress, not independently inspected artifacts, accepted Truss mapping or broad support qualification. Truss effective-right matrix work changes no Weft ABI.


Read-only Weft source review pins current README/prepared-check/parameter-native scripts at a95da1f82baf9148ec5235a0f2002d059a8ca3b5 in `design-audit/weft-preparation-source-review.json`. SQL PREPARE explicitly excludes host protocol binding; independently authored stored parameter values and Decimal expectations are separate from emitted compiler expressions. No local target/b005 receipt directory was available at this checkout, so no native pass was independently verified. Cursor :12 reports active work on a real driver test in a separate local test database, with connections/execution kept in the test host. Truss adapter/profile support remains independent of that compiler test-host evidence.


Weft cursor :13 reports active candidate preservation and identifies no published CONTRACT-007/bridge on Truss default branch or open PRs; owner qualification remains pending. Sent an authorized coordination correction: authoritative drafts are reviewable in `/private/tmp/claude-501/truss-spec-wt` on `spec/change-feed-and-groups`, remain uncommitted/unadopted, and this goal does not authorize publication. Clarified complete original query-route source coverage versus native qualification, dedicated installer ownership versus runtime caller ownership, and separate SQL PREPARE/test-host driver/Truss adapter evidence. Requested concrete parameter/decoder/obligation conflicts only, with exact draft source pins. Delivery is not owner adoption or interface acceptance.


Weft cursor :14 is terminal/idle: owner reports B-005 preserved in draft PR #7, goal blocked after three checks on adopted Truss binding/codec profiles plus qualified live host enforcement; B-006/B-007 pending. No PR source/native receipt or live Truss qualification was inspected in this observation. Truss has not adopted or published its current candidates, so this upstream gate remains genuine. No automatic goal resume/message/retesting follows from unchanged status. Next meaningful coordination requires concrete mapping/profile decision or new exact producer/evidence, while Truss-owned design work remains available.
