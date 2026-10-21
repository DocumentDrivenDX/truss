# Embedder E2–E8 implementation review — 2026-10-20

This is a source/contract review receipt, not a GitHub approval, merge decision or
publication receipt. Review covers the original pasted feedback and its selected
R16–R22 requests, the adopted E2–E8 plan, relevant CONTRACT-002–009 supplements,
the changed Python/native adapters and the release qualification selection.
Generated UMF assets retain their original owner/provenance boundary; this review
does not independently redefine or certify UMF/Weft semantics.

The reviewed implementation commit is
`4a442f337c7f2508bd5a9064489f49d1b842cb79`; this receipt and the corrected statement
count wording are documentation-only follow-up. The inspected v0.0.44 runtime manifest SHA-256 is
`9f6aab31802e9bebcd886f735ba9fe0bb405e69d3501a32f36cee8827b544d00`.
The retained package receipt records exact source/wheel/sdist correspondence for 428
runtime files and 436 RECORD members. Review independently recomputed all 428
current source hashes with zero mismatches, verified all eleven retained receipt
checksums, and confirmed every pre-existing governing frontmatter is unchanged.
Linux CI and fresh
public-artifact verification remain release gates. Test-only additions after the
runtime freeze require their own receipts; earlier snapshots are not silently
relabeled as exact final-wheel evidence.

## Entire selected request disposition

| Original request | Delivered result or explicit adopted variant | Evidence and qualification boundary |
| --- | --- | --- |
| 1: per-record import and builder cost | Explicit batched builder and guarded native chunk route; per-record containment, original indices, objects before edges, source and full report authority remain intact | Eleven native batch controls and two legacy-parity/performance controls; 32/64/128 comparisons and 1,024 capacity. Fixed client submissions do not claim set-based native DML or tenfold latency improvement |
| 1/R19.4: document and increase import limits | Legacy 128-record route retained; new explicit 1,024-record profile, chunks 1–128, independent byte/deadline and transaction/host-handle budgets | Ceiling/refusal, small-chunk, rollback, containment and durability controls; native pending-work counters are transactional, host-handle submission budgets do not rewind on contained rollback |
| 2/R16.3: cheap reader validation and module revision | One conditional catalog function returns snapshot/unchanged, with fresh full visibility checks and document source acceptance revision per module | Conditional hit/miss, read-only and revocation controls. Validator is not reusable authority; unrelated catalog/global revision is distinct from module source revision |
| 3: 128-condition ceiling | Previously published E1 profile retains 3,072 conditions for 1,024 operations | v0.0.43 evidence plus current precondition regressions; count never waives input-byte, scope or deadline bounds |
| R16.4: nameless executable registration | Original rejection proposal superseded by working stable-ID registration/read/write support | Preserve existing native nameless controls; do not invent a UMF authored-name requirement |
| R17.2: relationship alias after `x.*` | Document selected appended columns, collisions, unused alias workaround and related-key cap | Projection redesign remains explicitly outside this delivery; original declared corpus limits remain |
| R18: typed operation and non-member refusals | Existing E1 operation code, typed catalog/object/group refusal families and original error preservation retained | Existing typing, native admission and strict native-wire regressions. Transport, retry and unknown transaction outcomes are not converted into semantic refusals |
| R18.19: collision ordinal | Existing native decision carries actual original collision ordinal, including tombstones and deterministic earliest conflicts | E1 first/middle/last/multiple/tombstone controls; index absent for unattributable finalization failures |
| R18.4: incident edges on delete | Explicit restrictive dependency refusal, plus separately selected existing owned cascade | Unconditional cascade and hidden dependency listing are declined variants; no hidden edge count/identity in refusal |
| R18: condition-only group | Separate advisory preview, one truth snapshot and independent fresh publication authorization | All five predicates, 153/3,072/3,073, concurrent update and actual mid-observation revocation. Actual adopted read-only execution is separately selected; preview has no mutation receipt or mutation locks/effects |
| R18.11/20: rolled-back basis and pending token | Observed preview basis remains separate from mutation receipt; existing pending/committed/rolled-back token lifecycle retained | Receipt visibility regressions and generated action opt-in run; pending or rolled-back work is never inferred committed |
| R19.1/7: imported values/source and graph invariants | Selected apply value/facet/source semantics and native graph finalization, preserving live/reserved skip precedence | Legacy parity includes source failure, duplicate/conflicting inputs, mixed edges and committed-deleted reservation. No arbitrary new key grammar or silent unknown-property loss |
| R19.2/6: reserved edge and tagged import result | Reserved identities remain documented skips; legacy tagged result retained; new wrapper preserves full partial/durability result and explicit empty-load disposition | Engine/caller rollback, malformed later response, cleanup and unknown/failed commit controls; no flattening into a lossy success/failure flag |
| R19.3: origin and zero-created load record | Same-transaction load rows retain asserted origin privately, native initiator, complete outcomes and actual chunk boundaries, including zero-created loads | Load-summary/rollback/fully-skipped origin controls; raw origin and input/key/property/source values are excluded from audit DTOs. Literal unscoped empty loads require the separately qualified administrative entitlement |
| R20: separate journal grant and group discovery | Independent qualified module auditor role; complete retained owner union; module/type/entity/key/person/`x-action`/time/group selectors and descending whole-group pages | Journal-only person without ordinary data read, unrelated-module prefilter, mixed-owner refusal, deleted/type and descending continuation controls; endpoint/owned-cascade collector control is separately selected |
| R20: companion load listing | One invocation summary with initiator, retained observation range and created/skipped/rejected counts over the frozen committed frontier | Complete/partial load summaries and typed continuations; per-chunk detail remains separate. Observation time is deliberately not advertised as commit time/order |
| R21: install refusal, exclusion and role recovery | Typed known preflight family, transaction-scoped exclusion, passive marker inspection and separate authorized recovery | Busy/rollback, existing/foreign/tampered marker, unauthorized/read-only installer and role recovery controls. No reset, overwrite or unknown-outcome retry |
| R21: per-module grants | Atomic indexed validation with per-input errors; independent audit grant remains admin controlled | Mixed-invalid batch leaves grants unchanged; existing protected configuration exclusion applies to audit regrant too |
| R22/R16.6: person status and head zero | Minimal installed/compatible/absent and empty/accepted/unknown catalog state, without installation ID or role names | Reader/writer/auditor enrollment and denial controls; administrative role recovery remains separate |
| 5/R16.5: extension-aware optional evolution | Pinned original UMF DDD validation and narrow paired optional core member/Field plus known `umf.ddd` addition | Original owner preparation and native acceptance/refusal controls; prior meaning, IDs/data and unknown extensions preserved. No blanket extension exclusion |
| 5/R16.1: registration expectation | Document-scoped CAS plus optional global expectation under original publication serialization | Unrelated document progress, stale expectation and exact replay controls; dedicated CAS state never absorbs native serialization/deadlock retry |
| 5/R16.2: registrar check | Cheap typed advisory registrar probe; acceptance still reauthorizes | Native/current-role controls and public documentation; no administrative inventory disclosure |
| Explicit read/write statement budget | Original consumer read/update/describe trace, plus separately stated conditional API wrapper | Three samples each, with execution, setup/adoption and settlement categories. A universal operation count and unmeasured TCP/managed latency are not claimed |

Identity-only replay redesign, broader query/fact projection, automatic migration,
unconditional cascade, reusable authority tokens and fabricated commit timestamps
are not silently claimed delivered. Existing installations retain their matching
runtime; a larger import is not a verified historical migration. The selected
requests do not encompass every adjacent R17/R18 item or full Hohfeld provider
conformance.

## Review findings resolved in source

- Native chunk output decoding/carrier construction remains inside containment;
  interrupted/cleanup paths retain original partial reports and empty-load
  settlement, including unknown commit.
- Conditional catalog publication rechecks complete policy/dependency authority;
  known CAS refusal is distinct from whole-transaction native retry.
- DDD acceptance consumes original UMF validation and a narrow correspondence
  guard, preserving incompatible prior/unknown meaning.
- Preview's public wrapper is VOLATILE; one private STABLE statement returns
  truth and its own revision/snapshot, followed by a separate fresh ordered
  authority pass and current basis/person checks. A weakened cross-statement
  revocation test does not replace the actual mid-observation control.
- Audit prefilters qualified module ownership before inspecting private key data,
  authorizes complete historical groups, rechecks even empty listing releases,
  conceals unknown versus foreign load existence and retains actor names/origin
  without disclosing private payloads. Malformed unscopable siblings cannot erase
  otherwise valid import progress merely to manufacture an audit inventory.
- Installer compatibility discovery rejects views, foreign tables, RLS/rules,
  partition/inheritance and generated/wrong-type columns before a plain
  `SELECT FROM ONLY` marker read. Audit regrant uses the existing protection
  configuration exclusion.

No remaining blocking source defect is identified in this reviewed runtime.
This statement is conditional on the final selected native controls and exact
qualification inputs; it does not assert that pending CI/publication succeeded.

## Observed qualification checkpoint and remaining gates

The retained [installed v0.0.44 API/wire selection](native.log) passed 74 tests
and the [broader regression selection](regressions.log) passed 70, with no skips.
The latter includes the generated action opt-in control. The [two final review
controls](review-controls.log) pass actual adopted read-only preview and the
cross-module edge/owned-cascade audit addition; these are separate targeted
receipts rather than being counted inside a run whose test inputs predate them.
The corrected complete [host guard/fault selection](host-guard.log) passes 44.

The original Python-only consumer sample workflows pass 21 tests. Corpus 13 at
consumer commit `fed2c116db5dcdf2ac3b12b71bbfdddc35d03f6c` reports 63 passed,
nine declared limits and seven replica-only exclusions. The original stale CAS
limit was removed only after the unchanged full business case demonstrated
success; the other limits remain explicit.

The corrected original consumer trace has three identical-count samples each:

| Warm original consumer operation | `Cursor.execute` calls | Connection rollback calls | Connection commit calls | Total traced driver submissions |
| --- | ---: | ---: | ---: | ---: |
| Read with facts | 29 | 2 | 0 | 31 |
| Single-object update | 31 | 1 | 1 | 33 |
| Describe/type enumeration | 27 | 3 | 0 | 30 |

The update's pre-commit subtotal is 32 when including its rollback, retaining the
original comparison convention. The consumer's wait-call metric is a psycopg
round-trip proxy, not network packet/protocol tracing. Setup/warmup/cleanup and
server-internal work are separately scoped. Five typing consumers produce the
expected diagnostics `0/10/0/10/0`; negative cases are expected failures, not
ignored errors.

- [x] Source/contract review and explicit original-request dispositions prepared.
- [x] Identified source findings corrected; governed frontmatter preserved.
- [x] Installed consumer workflows/corpus and read/write budget checkpoint recorded.
- [x] Final targeted read-only/owned-audit and corrected host-guard receipts retained; final CI repeats their committed module selection.
- [x] Independent review of implementation commit `4a442f33` identifies no blocking finding.
- [ ] Linux-only release CI passes on the qualified source.
- [ ] Fresh wheel/sdist/metadata/RECORD/release pins match the qualified release source.
- [ ] Publication and fresh public-download checks succeed, then pending release wording is closed.

Local native evidence selects macOS ARM64; hosted CI selects Linux x86_64 only.
This receipt does not qualify managed services, Windows, every stress profile,
all generated action handlers, the complete protected security profile or upgrades.
