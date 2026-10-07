---
ddx:
  id: TD-034
  type: technical-design
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: US-034
      kind: informed_by
    - id: SD-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
---

# TD-034: Import identity and durable reservations

## Technical Approach

Import is identity-based create-or-skip, never merge or overwrite. Resolve object identity from its type and authored primary key using shared canonicalization; resolve edge identity from relationship and ordered endpoint identifiers. Process objects before edges across the whole input. Live identity skips regardless of current payload; under forbid, reserved identities also skip. Under allow, an absent live identity may be recreated while preserving historical tombstones. This differs from request-id result replay: a new load id does not authorize changing existing records.

## Component Changes

| Planned files | Responsibility | Criteria |
| --- | --- | --- |
| `packages/core/src/import/identity.ts` | Typed primary-key/edge identity and no-key refusal | US-034-AC1, US-034-AC5 |
| `packages/postgresql/src/import/apply.ts` | Locked live/reserved check, create/skip outcomes and batch report | US-034-AC1, US-034-AC2, US-034-AC3, US-034-AC4, US-034-AC6 |
| `packages/postgresql/src/storage/reservations.ts` | Atomic delete/re-key reservation writes and reuse policy | US-034-AC3, US-034-AC4, US-034-AC6 |
| `tests/import/replay.test.ts` | Independent state, tombstone, journal and report expectations | All criteria |

## API, Storage and Concurrency

Imports bind the same selected key transport/native uniqueness profile as direct writes and lookups. The legacy full-`k` index cannot qualify codec-size keys beyond its evidenced native capacity. A selected large-key profile uses complete exact keys plus nonunique digest routing and native bucket generation admission from CONTRACT-001/009; digest collisions never turn distinct identities into skips. Full current/reserved-key comparison is complete and authoritative under the admitted snapshot or the entire attempt retries. Skip precedence cannot convert a truncated/stale bucket query into live/reserved identity evidence.

CONTRACT-004 owns import_batch; CONTRACT-007 separates engine-owned bounded commits from pending caller-owned effects and per-record savepoints. CONTRACT-001 owns tombstones and key identity. Reuse canonical key semantics from TD-009; no stringified floating-point keys. Lock catalog head and sorted business identity before live/reservation checks and revalidate afterward. Every delete/re-key reservation is transactional with canonical and journal effects. CONTRACT-004 now specifies original-order object/edge phases and first-created/later-skipped behavior, retaining submitted indices; unequal replacement payload never updates the live record.

CONTRACT-004 selects typed immutable storage endpoint identity for this draft edge reservation profile. Relationship, source/target order and original definition/encoding pins are preserved; business keys do not propagate reservations to recreated endpoints. Import and deletion share the same injective qualified tuple procedure. Native byte/storage qualification and reviewed profile migration remain required; this rule is not a claim that the current spike already implements it.

## Validation and Reporting

Use CONTRACT-004's closed report schema and deterministic admission order. Pure report validation consumes admitted attempt inventory and trusted batch evidence; it never reruns writers to repair malformed output. Indices are strictly below inputCount, coverage is disjoint/exhaustive, and counters derive independently. Report carrier shape is authored; request/batch/resource candidates are authored; selected decoder/producer/native reservation profiles remain gates.

Types without a primary key reject with a specific reason and no effects. Preserve counts and per-record identities/outcomes, actual durability and committed progress. Live/reserved skips produce no version bump, journal/source rewrite or correction loss. CONTRACT-004 rejects malformed/unauthorized identities before lookup, then skips existing identities without replacement payload/source validation. Request/batch bounds and settings-change semantics are authored; exact native reservation encoding/observation and physical producer qualification remain gates.

## Security and Testing

CONTRACT-009 admits an exact configuration generation under the existing catalog-head exclusion. Retain the selected reuse policy across the import attempt; every engine batch readmits it before writes and stops with unprocessed remainder on change. Adopted imports keep the host transaction's exclusion until the host ends it. Exact native observation/storage and report provenance must be selected before qualification; no per-record unlocked setting read may alter the policy mid-attempt.

Identity checks must not interpret RLS-hidden live rows as absent: use the qualified reservation/uniqueness protocol while respecting diagnostics exposure policy. Plain SQL without a qualified reservation trigger remains engine-only enforcement and must be reported. Test races between imports, deletion, direct create and re-key with independent connections. Ordinary writers cannot erase reservations to bypass forbid. STP-034 owns all criteria.

## Sequence and Rollback

Finalize shared identity/reservation/report semantics; write red create/repeat/correct/delete/allow/no-key tests; implement locking and atomic reservation writes; test interrupted engine batches and caller rollback separately. Failed records roll back all their effects; previously committed engine batches survive interruption. Switching to allow does not remove tombstones. Never delete reservations as rollback of an implementation deployment.

Bounded import candidate now selects complete pre-writer envelope/artifact limits and stable objects-then-edges greedy batches constrained by record count and exact canonical record bytes. Skipped records still bypass deferred payload semantics; transport integrity/byte admission remains mandatory. Preserve original indices and prior batch durability on exhaustion. Exact resource-interruption result/diagnostic wire and native accounting remain design outputs.

Import now has resource_limited with mandatory coherent interrupted progress and selected resource profile; unresolved application/commit/cleanup uses execution_failed instead. Pre-reserve complete bounded report storage before writers and preserve exact prior batch durability. Seven resource-result shape cases and strict consumers pass; schema-valid unresolved/false index inventories require semantic refusal. Native/report-memory/savepoint/cancellation qualification remains pending.

Import report reservation now has explicit context/outcome/batch/unprocessed slot bounds and checked whole-input worst-case formula. Preflight every producer branch before effects; no expected-skip or average-size assumption. Report failure capacity is reserved independently of candidate/driver buffers. Exact lossless producer/physical accounting profile remains open.


## Repeated input versus original uncertain-attempt recovery

Identity-based create-or-skip does not recover an earlier attempt's result. After lost commit acknowledgment, retain the original attempt/batch/index report and CONTRACT-007 recovery obligation unchanged. A later authorized invocation is a new attempt under its own current catalog/configuration/authority and executor admission; live/reserved lookup determines its own outcome only. It cannot rewrite the earlier attempt's unknown entries or release that attempt's quarantined native resource. Even exact input digest/load ID equality does not prove common execution identity, producing transaction or original result.

In particular, observing a live identity cannot establish that the uncertain attempt created it: it may predate the attempt or come from another writer. Observing absence cannot establish rollback: the original committed record may subsequently have been deleted. Recovery must use qualified original transaction/operation/termination evidence, preserving unknown status when that evidence is unavailable. Preserve the exact originally returned report bytes and their meaning at that observation boundary; later settlement is appended original recovery evidence, not an in-place rewrite of that report. A new attempt may proceed only on resources independently admitted by the executor; no reuse of a quarantined connection or automatic library retry follows create-or-skip semantics. Supplied-scope import never ends the host transaction to obtain recovery evidence.

Current ownership and reuse policy apply afresh to a new invocation, including current hidden-identity handling and original tombstone semantics. Keep its report and source/load provenance separate from retained original recovery custody. A new invocation's success does not resolve an earlier outcome; resolving the earlier outcome does not retroactively change the newer invocation's create/skip report. Original source and journal facts remain immutable and belong to their actual producing operations.


### Recovery evidence and derived report views

A settled recovery view, if exposed by the selected host tooling, must retain the original report reference plus separately admitted original obligation and appended observation references. It must distinguish what the original invocation reported from what later settlement establishes. No existing import facade method is implicitly extended by this design rule, and no new public report schema or callable is selected here. The original pending/unknown report remains valid historical evidence; later evidence cannot make its original observation retroactively claim committed durability.

Derive any later outcome only from complete original attempt/batch/index correspondence and qualified settlement evidence. Host transaction settlement alone does not establish that a particular interrupted savepoint's effects survived; native termination alone does not establish commit. When original membership or containment evidence is unavailable, keep the unresolved subset explicit. Original committed batch evidence may be retained without inferring settlement for another batch. Never rerun import, read current live state as historical proof or combine a newer attempt's outcomes to fill original unknown entries. Current report/recovery disclosure authority still applies before exposing either original or derived information.
