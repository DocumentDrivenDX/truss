---
ddx:
  id: ADR-005
  type: adr
  activity: design
  status: accepted
  authoring:
    home: repo
  links:
    - id: ADR-002
      kind: informed_by
    - id: US-043
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
---

# ADR-005: Complete durable group request receipts

## Owner decisions — 2026-10-07

Accepted by the owner: request-enabled atomic batches use a fixed durable receipt home. Effects and the complete original ordered result, including all-no-op entries, commit together. Equal request identity and complete input replay the original result; unequal input conflicts. Lost network acknowledgment uses the same request identity for retry/lookup rather than blind reapplication. Expired identities never become reusable absence. Request-free groups remain receipt-free. Native bodies, exact selected wire/profile and qualification remain implementation gates; the old journal-only persistence alternative is superseded.


**Status:** accepted product decision; supersedes journal-only complete-result replay. **Date:** 2026-10-05.

## Problem and proposed decision

Property-change journal rows cannot recover every original ordered group result, especially mixed no-op operations. An all-no-op group creates no journal identity and cannot enforce a reuse conflict. Full request replay needs an immutable complete outcome rather than reconstruction from current records.

Propose one fixed `request_receipt` table, independent of journal partitions. It stores the verified request identity, versioned canonical input digest and full ordered semantic result in the same transaction as graph/journal effects. This remains a generic fixed layout addition, not a table per consumer or request. Request-free groups use no receipt. Request-enabled all-no-op groups persist a receipt and return it on repeat, replacing the current all-no-op reapplication exception after governing requirement reconciliation.

## Candidate logical fields

| Field | Proposed meaning |
| --- | --- |
| scope_id, request_id | Composite unique identity; scope is a host-authorized stable deployment/tenant namespace, never an unchecked caller privilege claim |
| protocol_version, digest_version | Exact request/result and canonicalization versions |
| input_sha256 | Server/library-verified hash of exact versioned semantic input; claimed caller hash must match |
| input, canonical_profile, semantic_domain | Complete exact semantic input and its pinned canonicalization/domain; digest equality alone cannot prove equality |
| catalog_rev, layout_profile | Qualified acceptance context used by original operation |
| original_execution_configuration | Selected configuration generation, reuse policy, journal mode, profile and producer inventory; retained original execution provenance, separate from caller canonical input |
| result | Complete ordered exact result envelope, including aliases, storage ids, versions and no-op values |
| origin | Original trusted journal origin; repeats cannot rewrite it |
| replay_authorization | Complete retained before/after declaring/endpoint owner context and definition pins; current grants govern disclosure |
| created_at, retain_until | Original database creation time and declared protection deadline; neither proves committed visibility or starts the minimum postcommit replay window |
| lifecycle protection | Separate trusted first confirmed committed observation and monotonic protection deadline; at least 24 hours from that observation plus all longer protections |
| expired identity | Compact scope/request/profile/input digest identity and expiry evidence retained after eligible payload purge; never inferred reusable absence |

Exact native columns/checks, resource bounds, result schema and scope authority require shared-contract review before DDL generation. Do not use JSON numeric decoding for exact result values. Result durability is response context: a stored semantic result does not permanently encode pending durability. A committed receipt replay reports committed effects; a first adopted call remains pending until host commit.

## Protocol

Acquire head, complete policy guards and trusted namespace lifecycle guards before request serialization, then business/root/row locks in the current CONTRACT-009 order. Verify identity scope/authorization and canonical input before lookup. Existing receipt with equal verified complete semantic input under compatible canonical/profile pins returns immutable original results after current replay authorization. A different verified digest or different complete input returns request_conflict without effects; matching digest cannot hide differing canonical bytes. A missing receipt plans/applies the group and inserts the receipt before releasing its savepoint. The selected native receipt profile must make full-identity uniqueness unavoidable; a digest-only unique constraint is not an equivalent identity rule or an excuse to skip shared lock ordering.

Winner rollback removes its receipt and effects; waiter can apply after observing absence. Winner commit permits waiter replay. Fixed-snapshot callers that cannot observe the committed winner restart at host discretion; no hidden host callback replay. Commit-unknown is resolved by qualified receipt lookup rather than blind mutation retry. Current input validation cannot invalidate old results by re-running the group against changed data; protocol/profile compatibility and replay authorization are checked explicitly.

## Canonical input and retention

### Proposed expiry and namespace lifecycle

To preserve US-043-AC4, full-payload purge is also ineligible while any original group journal event remains retained. Complete results stay self-contained: retaining a journal row is protection evidence, not a recipe to reconstruct missing result entries. Purge requires verified absence of all original event references under the shared retention arbitration profile, plus the minimum window and any longer declared protection. Inability to inspect protected evidence makes purge ineligible. Journal trimming itself may proceed under its own consumer/history rules because full receipts do not require journal payloads to replay.

The proposed `ReceiptPurgeAssessment` binding distinguishes protected, unavailable and eligible outcomes. Derive original event membership from the distinct union of every immutable operation result's event references; verify that union against original committed effects when admitting the receipt. Caller-provided lists and today's live records cannot establish completeness. Event-bearing eligibility records the full union and authoritative absence evidence; all-no-op eligibility records an empty union and the explicit replay-window profile. Missing or corrupt results make the inventory unavailable, not empty. The assessment is observation evidence only: revalidate the receipt identity, protection and event absence inside the serialized purge transaction. A previously eligible assessment cannot authorize purge after protection changes or replace shared retention arbitration.

All-no-op groups have no property-change journal rows; their explicit complete-result replay window is the declared request profile window, at least 24 hours after qualified committed observation. Do not manufacture mutation events merely to create a retention dependency. Review this no-op boundary together with the story's longer journal-dependent promise before accepting the profile. This proposal preserves that promise for event-bearing groups rather than shortening it to the minimum window.

After retainUntil and any longer published protection, an authorized retention operation may remove full input/result payloads, but preserve a compact expired identity record containing scope/request identity, canonical/profile digest pins and expiry evidence. A later lookup returns request_expired under current disclosure policy; it cannot treat the missing payload as permission to apply again. The minimum 24-hour complete-result guarantee is measured from confirmed committed receipt creation, not attempted dispatch time. Pending transactions cannot consume the advertised window before commit.

Within a namespace, a request id is never silently reused after payload expiry. Administrative namespace retirement/rotation establishes a new trusted scope identity and explicit new-request boundary; old workers cannot choose the new namespace merely by changing caller text. Retired namespace lookup remains expired/unavailable, never inferred absence. Compact identity retention and namespace metadata require a reviewed resource/administrative policy; they are part of this concrete proposal, not an unbounded-storage guarantee already accepted.

Expiry is administrative lifecycle evidence separate from the immutable original semantic receipt. Do not rewrite an old result as an empty successful result. Concurrent replay and payload expiry serialize on the same identity: either replay reads the complete protected result before expiration or returns explicit expired afterward. Failed expiry leaves protection unchanged. Journal trimming cannot shorten the complete-result window. Persisting original commit-relative expiry, compact identities and namespace authority requires exact schema/transaction review before DDL.

Review vectors: replay just before/after eligible expiry; payload purge preserving identity conflict/expiry outcome; same id unable to reapply; authorized namespace rotation with stale worker refusal; long host transaction committing after its initial wall-clock attempt; expiry/replay barrier race. This resolves the proposed lifecycle choice only; owner review and native proof remain gates.

Conservative implementation candidate: record a trusted firstConfirmedCommittedAt lifecycle observation after the receipt becomes visible on a fresh committed read; payload purge eligibility is no earlier than both declared retainUntil and that observation plus 24 hours. An unobserved/pending receipt is ineligible. This protects long adopted transactions without pretending a precommit timestamp is a commit timestamp. Lifecycle metadata may extend protection and cannot shorten it; its observation/persistence schema and clock validation remain review outputs. Extra retention is acceptable, early purge is not.

[Draft complete receipt binding](../contracts/bindings/truss-request-receipt-v0.1.d.ts) retains canonical input/result/profile pins, original execution role, scope/request identity and replay authorization context. The authorization context includes every required historical before/after declaring/endpoint owner and retained definition pin, not only the result entity's current owner. Current grants must authorize that complete context under CONTRACT-005; missing context blocks replay. A caller-supplied owner list cannot establish permission. Result durability is intentionally absent from persistence.

Input/result correspondence, verified canonical digest, source-scope authority and minimum replay-window timestamps require runtime/native validation. Proposed complete input retention permits direct integrity review but needs explicit sensitive-data retention/resource bounds and administrative access policy. Exact native columns, JSON wire validation and expiry/reuse/epoch handling remain reviewed profile decisions. This declaration is a concrete ADR candidate, not permission to create the table or claim journal-only replay now carries these members.

Hash operation order, typed aliases/references, exact values, expected versions, effect-relevant catalog/layout/profile and options. Propose including the complete asserted semantic origin (actor, reason and preserved extension members) in canonical input. Changed actor/reason/extension content therefore conflicts under one retained request identity. Retry-only transport metadata belongs outside origin and outside semantic input; it cannot rewrite original audit facts. Database-derived role and actual execution pins are recorded as original execution evidence, not caller-controlled digest fields. Authenticated scope remains bound to request identity and current replay authorization. Publish a versioned canonical schema and independent vectors before implementation; no caller hash alone proves equivalence.

Retention removes eligible expired full payloads under the lifecycle proposal above, retaining the compact identity within its namespace. Receipt expiry does not erase journal audit. A new trusted namespace is required for a new request identity after retirement; silent reuse inside the old namespace is forbidden. Journal retention cannot break a still-retained receipt because complete results are self-contained. Sensitive results need replay authorization and retention disclosure controls.

## Alternatives

A complete journal receipt record could also carry the outcome, but would expand journal operation semantics, include all-no-op events and require whole-receipt protection across partitions/feed/history. It is a viable separately reviewed alternative; property-change rows alone are insufficient. An in-memory cache cannot survive crash or supply native cross-process serialization. Recomputing results from current state violates original-result replay.

## Migration, tests and acceptance

Configuration change controls supplement receipt qualification: identical authorized replay after forbid/allow changes returns the original result and provenance without new mutation admission. An absent receipt uses current configuration before planning. Original configuration cannot be inferred from today's settings; missing required historical interpretation evidence refuses rather than reexecutes. CONTRACT-009 owns configuration exclusion and generation semantics; the proposed table must retain this provenance atomically with the original result.

Requires new explicit layout profile/model/inventory and ADR-002/CONTRACT-004/009/US-043 reconciliation. Existing journal-only deployments cannot be retroactively certified: historical results absent from the journal cannot be invented. Start a new qualified request profile/epoch with explicit migration boundary. Rollback cannot delete retained receipts while preserving a replay promise.

Independent expected cases: mixed changed/no-op original results after later edits; all-no-op conflict/replay; concurrent equal/different requests; caller rollback; uncertain commit lookup; unauthorized cross-scope lookup; 24-hour and journal-drop replay; corrupted/missing result member rejection. Proposal acceptance resolves persistence choice only; canonical wire schema and native evidence remain separate gates.

## Candidate fixed native realization

[Unapplied fixed-table fragment](../contracts/request-receipt-layout-v0.1.draft.sql) preserves original namespace/request bytes, complete immutable receipt bytes or a payload-free expired artifact, checked lifecycle generation and separate protection/evidence bytes. Positive storage sequence numbers are internal locators, never authored identity or authority. The bounded candidate admits each namespace/request UTF-8 identity up to 64 KiB, compact expiry/protection/evidence artifacts up to 1 MiB each, and complete receipts up to 64 MiB. These add explicit identity/administrative artifact bounds to the group reference resource candidate.

Nonunique fixed SHA-256 routes avoid indexing arbitrary full large values. Native serialized guard/complete-byte comparison and duplicate detection remain mandatory; no table constraint here proves logical request uniqueness. Complete-to-expired transition atomically preserves exact original compact provenance, clears full payload, increments checked generation and obeys current protection/event/clock admission. Expired cannot become complete again or be deleted for reuse. The protection row uses internal locator FK only; retained original identity/artifact admission still verifies correspondence and generation. Receipt insertion and graph/journal effects share one native transaction, including all-no-op receipts.

The fragment neither changes the baseline UMF model nor accepts this ADR. Before installation, reconcile ADR-002/layout requirements, allocate stable Truss-authored physical identities against the existing UMF capture, generate/compare full DDL through the selected existing owner APIs and Truss composition procedure, and author exact protected guard/insert/expiry/observation/privilege procedures. Missing complete Truss source/composition/native correspondence or native procedures blocks adoption; it is not permission to bypass model-backed generation or request new UMF features by default. No existing journal-only row can invent original result/input evidence.

Native original writer xid8 is deliberately not generalized as an UMF core integer. Current UMF native metadata retains this unresolved type's complete original content; synthetic projection evidence exists, while SQL/native/exporter round-trip remains unqualified. Include exact native type/profile/context in G03 generated layout adoption and G06 original observation. Missing known core family is not permission to omit the column or change its meaning to signed bigint.

The receipt layout/statement drafts now pass current UMF's pinned PostgreSQL parser/codec/export/reparse guard with original source archive preserved. Partial declarations still report complete:false and native xid8 unresolved; sequence/index/statement content is retained outside that incomplete declaration inventory. This strengthens candidate syntax preservation only, and does not accept this ADR or complete physical capture/exporter correspondence/native execution.
