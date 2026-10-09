# Python consumer integration design

This proposal implements the short-term consumer path in the [build plan](../04-build/implementation-plan.md#python-consumer-integration-priority--2026-10-09). ADR-001 remains accepted and ADR-003 remains proposed; the human requested a Python implementation promptly and asked for details before selecting the route. This document supplies those details without recording acceptance. CONTRACT-004/007/010/011/012 and the shared authorization design govern behavior. The [original consumer requirements](../04-build/evidence/consumer-python-requirements-2026-10-08.md) supply R1–R10.

## Implementation boundary

Recommend a separately packaged Python 3.11 implementation of the Truss contracts, using the same fixed PostgreSQL layout and protected SQL/PLpgSQL routines as the TypeScript reference. Python owns host integration and protocol orchestration. Weft's Rust core owns logical SQL compilation. PostgreSQL owns transactions, persistence and qualified native enforcement. Authorization policy/resolver semantics and their compiled/native handoff belong to the active security workstream.

This route needs no Rust port of Truss. It does require an independent Python adapter and exact codecs, shared callable database protocols, and a corpus that catches divergence from TypeScript. Shared native enforcement is intentional; language-neutral expected results remain independently authored. Performance evidence must determine whether any Python planning/resolution step needs a native implementation.

| Component | Python responsibility | Shared or owner-supplied dependency |
| --- | --- | --- |
| Catalog and installation | Invoke explicit installer/check procedures; expose admitted module revisions/layout version; refuse incompatible majors | UMF-authored original layout/DDL and Truss installer/admission; complete accepted catalog/report producer |
| Queries | Prepare admitted input, invoke compiler, preserve ordered parameters/obligations, submit through the original transaction, decode exact results | Weft compiler and admitted Truss physical mapping; direct key/page procedures for direct-read shapes |
| Mutation/import | Validate request shape; orchestrate group/precondition/import protocols; retain pending versus committed/unknown distinction | Shared protected native effects, journal, immutable receipt and finalization |
| Authorization | Supply the host-authenticated connection and consume the security workstream's admitted invocation boundary | Original database session person, current grants/policy, admitted subject/key/fact mappings and compiled enforcement |
| Exact values | Decode text/tagged values with exact integer/decimal/time/JSON handling and selected codecs | CONTRACT-010 and pinned shared value profiles; no float intermediates |
| Feed and reached | Consume complete manifests, apply atomically, retain original durable proof, compare opaque tokens through selected operation | CONTRACT-006 source epochs, complete feed/application/ACK and current authority |
| Conformance | Execute the same versioned fixtures and emit complete observations | CONTRACT-011 manifest/result/divergence/assessment grammar and STP-028 interchange |

Weft's committed source exposes `weft.compile_json(request: str) -> str` through the `weft-sql` PyO3/maturin package. Its `truss-postgresql-qualified` build feature is distinct from candidate/test configurations. Python packaging must pin the actual admitted feature/backend tuple, not infer it from an import or package version. Test-only configuration exports cannot serve as production registration. This source observation does not prove wheel availability or Python authorization/compiler qualification.

## Consumer count-summary integration

### PY-02 reproducible development wheel recipe

Use a clean source checkout of Weft commit
`5856c73db0342363e64802905a94abb96209d757`, not the security owner's dirty
checkout. Its committed `rust-toolchain.toml` selects Rust 1.90.0; its Python
pyproject pins maturin 1.9.6, and its Cargo feature forwards
`truss-postgresql-qualified` to the shared runtime. From that clean checkout:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install maturin==1.9.6
.venv/bin/maturin build --manifest-path crates/weft-python/Cargo.toml --features truss-postgresql-qualified --locked --release --interpreter .venv/bin/python --out dist
```

Install the exact emitted wheel into a separate clean Python 3.11 environment;
record its actual filename, SHA-256, platform/ABI tag, source commit, Cargo.lock
hash, toolchain and complete feature set. Do not guess a wheel filename or reuse
an unpinned ambient installation. Do not enable `test-original` or a candidate
backend as a substitute for the selected feature. The original extension exposes
`weft.compile_json(str) -> str`; the conformance-configuration entry point is
conditional on `test-original` and must be absent in this selected build.

First verify import, exact wheel identity and refusal of a closed invalid request;
then run independently authored supported-query/parameter/obligation expectations
through the original registered mapping. An import or a JSON error response is
only a packaging/ABI smoke check, not compilation or native Truss support. This
recipe has now run from an isolated committed-source archive using Rust 1.90.0,
maturin 1.9.6 hosted on Python 3.12.14, and locked/offline release dependencies.
The macOS arm64 cp39-abi3 wheel installed without dependencies into a clean
Python 3.11.17 environment. Import, version, absent test-original export and
actual WFT-INPUT blocked response for `{}` pass. The
[saved build/smoke receipt](../04-build/evidence/design-audit/weft-python-wheel-development-smoke.json)
pins archive, unchanged Cargo.lock and exact emitted wheel bytes. The ABI3 build
does not use a Python-3.11-specific binary ABI, despite the requested interpreter.
No supported query or Truss native operation ran. Wheel distribution and full
native security/transport/mapping qualification
remain PY-07 and PY-01b/03 dependencies. It supplies no new Weft registration or
Python ACL/compiler implementation.

Committed Weft `5856c73db0342363e64802905a94abb96209d757` defines COUNT(*)
in CONTRACT-004's application-read 0.2 dialect and resolves it in
`crates/weft-core/src/application_resolve.rs`. R8 should consume that owner
implementation rather than add a Truss aggregate compiler. The explicit
readProfile is version `weft-application-read/0.2.0`, subset `count-summary`;
omitting it does not supply bounded interactive-read semantics.

The clean Python 3.11 wheel now compiles the existing upstream-derived
`tests/weft/fixtures/qualified-count.request.json` through public
`weft.compile_json`, retaining the independently expected count text carrier and
qualified backend version. The same run refuses an unsupported target profile
without publishing SQL, rejects four wrong transport types and an invalid Unicode
surrogate, and confirms the test-only configuration export is absent. Run
`docs/helix/04-build/evidence/design-audit/check-weft-python-count.py` with the
clean pinned-wheel interpreter; the [saved component receipt](../04-build/evidence/design-audit/weft-python-count-component.json)
records fixture/checker/response hashes.
The checker first verifies the saved original wheel hash and compares the loaded
native extension byte-for-byte with its sole native wheel payload, retaining both
hashes in the receipt. A matching package version alone cannot pass this check;
missing original wheel custody refuses before compilation. This establishes
artifact correspondence only, not administrative or query authority.
The fixture has synthetic upstream
catalog identities and is not accepted Truss state. These checks do not qualify
native queries, complete obligation handling, actual catalog mapping or Python
runtime publication. The same checker now compiles an ordered grouped count
with LIMIT and verifies emitted grouping/order/limit clauses; removing LIMIT
refuses before SQL publication. These exercise the committed count-summary
profile rather than a local aggregate compiler. Native empty-input/bag/result
and finite scan-work evidence remain required.

The pinned wheel also passes complete parsed-response parity for all 1,216
Truss cases in the committed owner's qualified-registration artifact corpus.
The [saved parity receipt](../04-build/evidence/design-audit/weft-python-owner-corpus-parity.json)
retains original corpus, wheel, extension and checker hashes plus each response
hash. Run `check-weft-python-owner-corpus.py` from the same evidence directory
with the clean-wheel interpreter and the pinned owner gzip corpus path. It
refuses changed corpus bytes or missing/duplicate cases. The 965 Ashlar cases
are explicitly excluded from this Truss-only feature build. Owner compiler
outputs are the parity reference, not an independently authored Truss oracle;
no byte-order parity, native database execution or production mapping adoption
is claimed.

For this profile, grouped counts require complete grouping order and LIMIT;
global counts have one row and exclude ORDER BY/LIMIT. Cursor and relationship
predicates are excluded. Empty global input produces one zero-count row; empty
grouped input produces no rows. Joins retain bag multiplicity. Python preserves
the admitted exact integer carrier without float conversion, ordered parameters
and every original host obligation. Query LIMIT bounds returned groups, not
necessarily scanned input or native execution work.

PY-02/05 must independently test empty/global/grouped inputs, duplicate joined
rows, exact count decoding, parameter domains, omitted/partial grouping order,
missing grouped LIMIT and forbidden cursor/relationship constructs. Use actual
authorized native data and plans with finite selected scan/statement/transport
budgets. Compiler acceptance alone does not prove the Truss backend supports
the selected aggregate, security mapping or exact decoder; missing obligations
refuse the whole read. Parsed-query input remains a separate Weft-owned ABI
dependency: its availability cannot be inferred from SQL-text count support.

### R8 parsed-input compiler handoff

The original consumer requirement says the host parses its own statement and
wants parameterized SQL without a second textual parse. At the pinned committed
Weft baseline, `compile.rs` admits a closed request with required `sql: String`,
and the Python export forwards a JSON string to that compiler. Its internal Rust
logical plan is not a published language-neutral parsed-input ABI. Therefore the
current wheel satisfies neither parsed-input admission nor the complete R8 read
contract, even though supported SQL-text compilation and owner-corpus parity pass.

Weft owns the missing parsed representation and entrypoint. Truss supplies the
following consumer acceptance requirements for that upstream interface; it must
not create its own AST, serialize an AST back to SQL as a claimed solution, or
treat an arbitrary caller's pre-resolved plan as compiler authority.

- Admit an explicit versioned parsed representation with closed node variants,
  exact literals and parameter references. Preserve qualified entity/Field and
  alias references, projection order, relationship direction, grouping/order and
  paging bounds. Unknown or unsupported nodes refuse before database submission.
- Resolve the parsed input against the same original UMF modules and registered
  Truss backend mapping as SQL-text input. Host parsing does not bypass name,
  type, presence, key, security or supported-subset checks. The compiler owner
  defines which semantic stages remain shared and supplies their evidence.
- Return the existing admitted parameterized SQL, ordered typed parameter
  descriptors, complete result metadata and host obligations, or an explicitly
  versioned successor. Python must retain exact values and independently bind
  each parameter to its descriptor; a caller-provided SQL string or cursor is
  not an accepted compiled result.
- Define finite input/node/depth/output bounds and diagnostics for malformed
  parsed input. Truss's existing transport/resource account must include the
  original parsed carrier and compiler output; LIMIT alone cannot qualify
  indexed or bounded native work.

PY-02/05 qualification must pair independently authored parsed and text cases
for the same supported semantics and compare result/parameter/obligation meaning,
without requiring identical SQL formatting. Cover alias and qualified-name
collisions, large integer and decimal parameters, absent/null projections,
relationship direction, complete versus partial grouping order, keyset boundaries
and capped `alias.*` expansion. Mutate each parsed case to an unknown node,
unresolved reference, mistyped or missing parameter, unsupported relationship or
unbounded projection; require compiler refusal and zero native submissions.
Then execute admitted forms against the same authorized populated native data
with original plan/budget evidence for each advertised read shape.

The interim SQL-text route remains separately advertised at its actual scope.
Parsed-input availability is an upstream engineering dependency, not a new
consumer product choice. No release claim may mark R8 complete until its parsed
interface and all required direct/compiled read shapes have matching corpus and
native evidence. The exact ABI/profile bytes remain unselected until Weft
publishes them; Truss consumes that interface rather than inventing its wire.

### R8 read-shape delivery matrix

Use the existing direct lookup/page/traversal contracts and Weft-owned logical
query compiler. This matrix assigns implementation work; it does not advertise
any row as currently supported. Each row requires a selected original mapping,
ordinary-person read-only execution, full disclosure handling and actual native
plan/resource evidence in PY-05 and the shared corpus.

| Consumer shape | Intended route | Qualification required |
| --- | --- | --- |
| Exact authored business-key lookup | Direct authored-key lookup | Complete owner-local key definition/component order, admitted exact encoder and native indexed equality; one found record or independently established absence. No scan fallback when key semantics are unavailable |
| Equality over a key | Direct lookup for a complete unique key; Weft for logical projections, joins or partial key predicates | Partial-key predicates cannot borrow unique-lookup bounds. Qualify their original comparison/index route and result cap independently |
| Equality over an indexed property | Weft | Accepted declaration plus currently ready matching native index, exact comparator/presence mapping, statement/scan/result bounds and actual plan. A pending-index report is not a ready index |
| Relationship predicates | Weft for logical filtering; direct incident-edge enumeration/traversal for those explicit operations | Preserve direction, endpoint types, key/relationship ownership, disclosure and complete result semantics. Incident edges or terminal traversal are not substitutes for an arbitrary logical predicate; unsupported compiler semantics refuse |
| `alias.*` with capped relationship columns | Weft | Resolve expansion against the admitted catalog before submission, retain ordered result descriptors and the selected relationship-column cap. Extra fields cannot be silently dropped, and expansion cannot reinterpret absent/null/withheld values |
| Keyset page ordered by business key | Weft | Complete authored key comparator and tie-breaker, cursor/query/context correspondence, actual eligible lookahead and native ordered access. Direct storage-ID paging keeps its own ordering and cannot satisfy business-key ordering by renaming its cursor |
| `COUNT(*) GROUP BY` one property | Weft count-summary subset | Complete grouping order and LIMIT, exact count text, authorized input and native scan/statement budgets. Test empty groups, joined multiplicity and absent/null grouping under the original supported semantics; returned-group cap does not bound scanned rows |

For every advertised row retain the complete input, original accepted catalog
and compiler/direct mapping, ready index identities where applicable, native
EXPLAIN evidence, returned descriptor/value/cursor expectations and the selected
finite budgets. Test a populated success and independently injected unavailable
index, wrong definition/profile and exhausted budget. Refusal or unavailable
results carry no partial logical records. Native cancellation and cleanup retain
their original executor outcome, rather than becoming a false empty result.

The corpus must distinguish the direct and compiled routes even when both can
answer one fixture. A direct lookup success does not qualify projections, joins,
business-key paging or aggregate work; a compiler response does not qualify
native index use or disclosure. Release documentation lists each route's exact
supported subset and measured bounds. Numeric cap values and native access paths
remain profile-selection outputs, not defaults inferred from this matrix.

## Private PY-01a numeric convenience checkpoint

The private evidence-directory prototype `python_exact_numeric_candidate.py`
retains original admitted integer/decimal text and returns Python `int`/`Decimal`
views with an explicit caller-selected finite UTF-8 byte bound. It rejects bool
as integral host input and nonfinite decimals, preserves decimal signed zero
and spelling, and constructs large exact decimals without ambient precision
rounding. It performs no arithmetic or UMF grammar/facet/range admission.

From the Truss repository root, run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 docs/helix/04-build/evidence/design-audit/test_python_exact_numeric_candidate.py
```

Two tests pass on Python 3.11, covering all seven
numeric proposal vectors plus finite-value, host-type, UTF-8 and bound refusals.
At this numeric-only checkpoint, timestamp, recursive/presence/raw-JSON codecs, original upstream admission,
whole-operation resource accounting, native storage and public packaging were
separate PY-01a/PY-01b work. This candidate lives outside a public package while
package ownership is pending; its green results do not qualify the Python runtime.

The subsequent private `python_exact_timestamp_candidate.py` adds original-token
retention with an optional aware datetime view for its explicit offset/precision
subset. Nonzero submicrosecond digits refuse the convenience view; trailing zero
digits can have an exact microsecond representation while their original spelling
is retained. Unknown `-00:00` offset, leap seconds, offsetless forms and dates
Python cannot represent have no datetime view. This is conversion availability,
not source grammar/temporal-family validation. It grants no native instant,
comparison or ordering capability.

Run all numeric and timestamp candidates with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s docs/helix/04-build/evidence/design-audit -p 'test_python_exact_*_candidate.py'
```

Four tests pass on Python 3.11, including all three authored timestamp vectors,
same-instant/different-offset preservation, exact versus lossy finer precision,
unavailable views and capacity refusal. At that timestamp-only checkpoint,
recursive/presence/raw-JSON codecs and original source/native/resource admission
remained required.

The private `python_exact_tree_candidate.py` now projects the existing presence
and tagged-value carrier into immutable ordered Python values. It retains exact
numeric/timestamp wrappers, strings, binary text, boolean/null, sequence order,
exact map keys and record field identities/definition pins. Absent values remain
distinct from present null and empty collections. Duplicate map/field identities,
nested PostgreSQL-bound NUL/unpaired-surrogate text and changed opaque source
digests refuse; opaque format/source bytes remain uninterpreted.

The same discovery command now passes eight tests on Python 3.11, exercising all
fifteen original vectors, caller-mutation isolation, all tagged families, distinct
Unicode key spellings and explicit depth/node/entry bounds. Bounds are selected
arguments, with candidate depth limited to 128; this does not adopt draft release
defaults. Projection starts from already materialized admitted carriers. It
neither parses original bytes nor charges aggregate simultaneous allocation,
resolves definition ownership, validates binary/native domains or qualifies
opaque support. PY-01a must still integrate original byte parsing and upstream
semantic admission before this projection can serve an actual adapter.

## Host transaction adapter

Use the semantic Executor operations of CONTRACT-007 rather than a language-specific second transaction protocol. The adapter accepts the caller's actual live connection/transaction object, validates ownership/lifetime, and retains it internally. No transaction identifier is accepted as a substitute. Initial delivery selects one driver/transaction mode and qualifies it; sync and async modes cannot share a support claim without separate evidence. Driver selection remains explicit.

- Owned execution begins on one connection, commits after complete native finalization, and publishes durable results only after observed commit. Failed or unknown commit preserves recovery state.
- Adopted execution issues no outer BEGIN/COMMIT/ROLLBACK. Group-local savepoints contain failed effects while preserving prior caller work. Pending results settle only through the original adapter's outer-commit observation.
- Dry-run invokes the actual group path and its final-state/deferred validations, then the caller rolls back the outer transaction. The adapter must restore any operation-local constraint mode. No journal, request identity or receipt survives. A simulated success cannot rely on skipping commit-time validation.
- No automatic callback retry occurs. A connection loss may mean commit_unknown; exact request-ID recovery uses the same original semantic input and original ordered result. Retrying with a new request ID is a new action.
- Reads use the caller-person read-only transaction and current disclosure policy. A successful application-role lookup does not give access to private integrity observations.

## Security workstream handoff

Consume the security agent's model and implementation. Do not create an independent Python ACL policy parser, host role map, or alternative predicate compiler. Their current Truss predicate/key/namespace/transport/stored-key/query-use modules are component candidates, and their TypeScript interfaces are not yet a language-neutral public Python ABI.

The shared invocation design must specify: original authenticated subject/session binding; complete original policy/model/key identities; admitted compiler artifact and obligation inventory; native entrypoint, physical parameter/selector order and protected publication rules; current-authority refresh/invalidation; and exact denied/unavailable/error behavior. Artifact hashes identify bytes but do not grant authority. Python can orchestrate resolution through that boundary while native policies enforce the applicable rules.

R4's database reader/writer membership and any model-level ACLs are separately applicable rules. R5's authenticated connection actor and an asserted origin are separate facts. Internal definer ownership cannot replace either. The consumer's x- action extension must survive the same selected origin/journal path. Security qualification covers reads, group effects, imports, receipt replay disclosure, catalog enumeration, feed and reached.

A Python adapter must refuse an unavailable shared security profile; it cannot use the raw predicate fixture or a caller-supplied actor as a fallback. Exact registered policy/native context and privacy behavior are the security workstream's outputs. This proposal defines the consumer-facing dependency and its required tests without choosing their policy semantics.

### Current security-owner native observation handoff

The working-source CONTRACT-053 reviewed in
[the current boundary receipt](../04-build/evidence/design-audit/security-current-boundary-review-2026-10-09.json)
specifies a private principal observer returning native superuser, bypass and
encoding facts as TEXT. SESSION_USER and CURRENT_USER are selected outside the
definer as original/effective actor. That response is exactly one row with five
ordered fields, OIDs `[19,19,25,25,25]`, text format zero and non-null valid UTF-8.
The separate direct-principal option uses five TEXT fields: these are distinct
profiles, not decoder fallbacks. Inspection on 2026-10-09 still observes this
distinction; it does not adopt the uncommitted owner contract as a released ABI.

PY-01/03 must demonstrate original raw field metadata/byte custody before
decoded identity use. A driver-returned string tuple alone cannot prove the
selected OIDs, formats or original connection observation. Verify actual
session actor, admitted effective actor/reset state, false superuser/bypass and
UTF-8 through the owner's procedure. Missing/malformed facts close admission;
do not substitute catalog lookup or a host-supplied role map.

Subject-key results remain ordered TEXT OID25 even when a selected ordinary
subject preflight uses native name for its SESSION_USER argument. Argument
carrier selection does not change key-output semantics or authorize the caller.
Preserve owner-issued registration and original policy/key/context provenance;
serialized configuration cannot mint an issued resolver handle.

Independent Python cases must swap actor/key OIDs, reorder fields, return NULL
or malformed UTF-8, change the actual session/effective actor and lose the
original response. None may reach application effects or publish protected
facts. A host deadline does not prove native cancellation/rollback: retain
original unresolved execution and quarantine custody until qualified native
termination under CONTRACT-007. Security-owned routine/privilege closure and
actual Python driver evidence remain dependencies of this slice.

## Exact transport

### Initial Python driver qualification packet

PY-01 consumes the shared
[original driver producer port](contracts/reference-driver-producer-port.proposal.md).
The selected Python driver/mode must name its actual source/build and demonstrate
the original physical lease, ingress reservation before reads, retained backing
capacity/lifetime, frame reservation before capture/parser copies, complete-frame
consumption and callback/cycle correspondence. Metadata obtained from a completed
driver result cannot establish those earlier allocation or parser observations.

| Boundary | Required Python evidence |
| --- | --- |
| Admission | Original host transaction/connection and exclusive lease; supported exact producer hooks and finite conservative receive/parser/capture bounds before submission |
| Native response | Actual ordered field OIDs/formats and raw cell bytes under the same command cycle; malformed/oversized/partial frames refuse before protected publication |
| Containment | Callback/parser fault, cancellation and late response preserve original possible effects; independent native termination precedes safe reuse |
| Adoption | Host prior work survives operation-local failure; no outer BEGIN/COMMIT/ROLLBACK or replacement connection; original savepoint/constraint state is preserved |
| Ownership | Caller buffer mutation, shared backing views and asynchronous callbacks cannot change admitted bytes or refund performed work |

A driver exposing raw result metadata without qualifying ingress hooks remains
an incomplete adapter candidate, not a bounded supported implementation. A small
driver/native transport bridge may be needed even with Python host orchestration;
that is distinct from porting Truss to Rust. Choose it from actual source and
native evidence, rather than infer suitability from Python package popularity.
Reuse the shared port and original authority instead of creating a Python-only
transaction/identity protocol. Unsupported sync/async modes remain explicitly
unavailable until separately qualified.

Use Python `int` for admitted integral domains and `Decimal` constructed from exact text for decimals, with domain/arithmetic context explicit. Driver raw cells remain text until profile decoding. Decimal operations must not inherit an ambient low-precision context that rounds accepted values. Timestamp transport retains the original exact text and offset; expose an aware `datetime` only when its microsecond representation is lossless. Finer precision requires a lossless wrapper/text representation or explicit refusal of the convenience view. Preserve raw exact JSON bytes; a convenience parser uses an admitted numeric decoder, never the default float path. Python bool must be distinguished from int at validation boundaries.

Read shapes retain absent versus explicit null, ordered key components, exact large integral values and original selected decimal/token meaning. Known JSON-like values and retained unknown extensions cannot be normalized into different meanings. Exact wire grammar remains CONTRACT-010's responsibility; these mappings are Python implementation obligations, not new UMF types.

### PY-01 independent exact-value expectations

The [shared authored vectors](../03-test/python-exact-value-vectors.proposal.json)
now materialize fifteen CONTRACT-010 presence/value carriers plus a Python host
bool/integral refusal. Strict Ajv compilation validates each carrier and all
cross-vector references resolve. This is fixture shape evidence only; neither
Python/TypeScript decoding nor native storage has been run against them. The
signed-zero pair now independently preserves opposite signs and distinct wire
forms despite mathematical equality. The large decimal vector specifies ambient
precision 3; Python Decimal construction remains exact under that context in a
standard-library check. That check does not qualify adapter arithmetic or storage.
The
nested map vector checks typed token/string separation, not raw JSON parser
custody. The [raw JSON vectors](../03-test/python-raw-json-vectors.proposal.json)
separately author five exact UTF-8 sources, including nested large integers,
decimal/exponent/signed-zero spelling, unknown extensions, source escapes and
literal identity-looking strings. Python's standard JSON parser with explicit
token hooks initially checked twelve independently authored token/string expectations.
The saved checker `python3 docs/helix/04-build/evidence/design-audit/check-python-raw-json-vectors.py`
now compares complete numeric-token/string inventories and three presence checks,
for fifteen expectations across five fixtures. Missing/extra token expectations
cannot pass from partial pointer checks. Five negative controls refuse non-JSON
NaN/Infinity constants and duplicate root/nested fixture members; ambiguous
fixtures cannot silently lose entries through a dictionary overwrite. This is
the checker's admitted fixture subset, not a new universal native JSON policy.
This is not the production decoder and does not prove byte custody,
bounded parsing, unknown-content support or native JSON qualification. Both
adapters must retain the original source and run the complete fixture obligations
under their selected original parser/codec/resource profiles.

Materialize these pairs under explicitly admitted authored definitions and the
shared CONTRACT-010 carrier; the examples do not expand a selected native domain.
Retain the original wire alongside any Python convenience value. Compare both
original bytes/meaning and independently expected logical presence through
Python-write/TypeScript-read and the reverse.

| Input distinction | Required expectation |
| --- | --- |
| Adjacent integral values 9007199254740992 / 9007199254740993 | Distinct exact Python integers and readback; no float intermediary or equal rounded key |
| Decimal text 1.0 / 1.00 | Preserve each original lexical form where the selected value contract requires it; mathematical equality or Decimal equality cannot rewrite stored/original request bytes |
| Signed decimal zero / unsigned zero | Preserve selected lexical/sign semantics; key canonicalization is a separate admitted operation and cannot redefine value transport |
| Decimal exceeding the process's ambient precision | Construction/readback stays exact; arithmetic requires an explicit admitted context or refusal, never incidental rounding |
| Timestamp with nine fractional digits | Preserve all original digits and offset; a microsecond datetime is unavailable unless the actual value has an exact representation |
| Same instant with different authored offsets | Preserve original text/offset; UTC conversion as a convenience does not replace the retained authored value |
| Nested JSON numeric token and ordinary numeric-looking string | Preserve distinct families recursively; a number-token decoder cannot reinterpret the string or discard original unknown extension content |
| Absent, explicit null, empty string and empty collection | Four distinct admitted values/presence states; no defaulting or truthiness conversion merges them |
| Python True supplied for an integral field | Reject at the typed validation boundary despite bool being an int subclass; actual boolean fields retain boolean meaning |

Include native domain refusals separately from host precision refusals. A value
outside the selected database domain cannot become supported merely because
Python can represent it. Exercise both unprojected siblings and projected values
through the selected complete-value decoder, preserving whole-result refusal
when mandatory meaning cannot be decoded.

## Execution slices and independent test schedule

PY-01 remains the combined protocol/codec workstream; PY-01a and PY-01b below
split its implementation dependencies. References to PY-01 require both parts
where native transport is involved.

| Slice | Depends on | Deliverable and test gate |
| --- | --- | --- |
| PY-01a portable codecs and wire validation | CONTRACT-007/010 and independently authored exact vectors; no driver selection needed | Python 3.11 modules preserve original integer/decimal/time/JSON/presence meanings and original bytes; bool/int refusal and incompatible report/profile refusal. Pure codec passing does not qualify transport or database effects |
| PY-01b original protocol adapter | Selected driver, PY-01a and admitted raw producer port | Inert construction; original connection adoption; no outer transaction commands; original pre-ingress bounds and lossless metadata/cells; failure containment and outcome correlation. A driver which exposes only already-decoded results cannot satisfy the port |
| PY-02 compiler integration | Reproducibly built pinned Weft wheel and admitted mapping; public wheel distribution is a PY-07 release requirement | Clean Python 3.11 consumer compiles original supported queries; preserves parameters/obligations; rejects unsupported profiles before native submission. Development may build the wheel from exact committed owner source and features, retaining toolchain/build hashes. Do not use test-original configuration as production authority |
| PY-03 identity/security | Security workstream's complete handoff | Writer succeeds; reader write refuses; outsider read refuses; no identity refuses before application SQL; conflicting actor refuses; definer execution retains original person; denied queries publish no protected facts |
| PY-04 groups, dry-run and retries | Complete accepted catalog/install, PY-01/03, protected group/receipt procedures | Real group/preconditions; operation rollback preserves prior caller work; dry-run and apply violations agree; lost acknowledgment replays original ordered results; changed input conflicts; all-no-op receipt survives; commit_unknown remains unresolved |
| PY-05 reads/import/enumeration | PY-02/03/04 and native indexed/direct routes | Bounded key/equality/relationship/page/aggregate cases with actual plans; read-only enforcement; atomic/per-item imports/provenance; module revisions and incompatible layout refusal |
| PY-06 feed/visibility | Complete source manifest/application/ACK and receipt-token design | Whole transactions only; durable applied position; restart equality; reached false before apply only with admitted original token commitment and snapshot-exclusion evidence, otherwise unavailable; true only after complete durable inclusion proof; old snapshots, incomparable epochs and missing retention evidence explicit; no numeric xid-order shortcut |
| PY-07 publication/interchange | All applicable slices and versioned shared corpus | Clean wheel install; named layout/corpus/backend versions; Python-write/TypeScript-read and reverse on one real database; independent state/journal/receipt observations; unknown/newer required corpus and skipped cases prevent qualification |

Author setup/call/expected-result/error/journal fixtures before collecting observations. Reuse the existing conformance manifest's separate fixture/input/expected/identity-alias artifacts. Opaque identities are saved aliases, not fixed generated IDs. Complete selected accepted reports and original source epochs remain native outputs; no fixture accepted revision or invented epoch enables these slices. The combined reference uses the existing nineteen-field 0.3 lifecycle/history report, including lifecycleProfile/reactivations and 0.2 rebind events. A Python baseline 0.1 codec may preserve its separately qualified seventeen-field subset but cannot claim combined lifecycle compatibility by dropping fields or relabeling versions. Consume the same original selected schema/profile tuple as the TypeScript implementation; report version numbers alone are insufficient.

Start PY-01a and the reproducible PY-02 build/unsupported-input checks while
package ownership and driver qualification are being selected. These activities
need no fabricated installed identities or security authority. Author independent
exact-value and report-version vectors before either implementation emits results;
retain Python and TypeScript observations against the same expectations. Native
query submission remains gated on the original mapping, raw transport and security
composition even if a source-built compiler wheel runs successfully. This makes
the early development path executable without treating an unpublished wheel as
a released dependency or merging packaging and native qualification decisions.

## Validator diagnostic path correspondence

For the pinned UMF 0.7 source-validation candidate, preserve each original
`severity`, `code` and `path` unchanged. The committed UMF document validator
emits structural diagnostics using Ajv's original `instancePath`, and semantic
diagnostics using its escaped pointer helper. A missing-property structural
diagnostic may identify the containing object; do not append a guessed absent
property or convert its code to a semantic error. Preserve empty-string root
paths separately from `/`, which identifies an empty member name.

Keep the original source artifact/document identity and Truss diagnostic
classification separate from the upstream path. The existing rejection carrier
has `source`, `diagnosticProfile`, exact diagnostic artifact and `classification`;
reuse it rather than concatenating acceptance-wrapper/module names onto the
upstream pointer. Resolve sourcePointer under its original registered source
profile; a pointer inside the diagnostic's document is not automatically a pointer
inside the serialized acceptance request. Retain source bytes and complete raw
diagnostic artifacts before any convenience projection.

The semantic comparator must use severity/code/path as a multiset with
multiplicity under the same source/profile/classification. Message text and
ordering remain informative unless the selected profile declares otherwise.
Distinct source documents with equal paths stay distinct; upstream warnings on
accepted input cannot disappear or become Truss-support errors. Unsupported
Truss storage interpretation remains `truss_admission`, not UMF-invalid.

Independently author root-versus-empty-member, escaped slash/tilde member,
array-index-versus-numeric-member, duplicate diagnostic, warning-only and
missing-required-property-parent cases. Retain the pinned reference outputs and
review each against its authored invalid condition before adapter execution.
Byte parsing/duplicate-member behavior and the 0.8 transition remain separate
profiles; this 0.7 source observation does not select them. Original validator
registration, diagnostic artifact encoding and full Python/browser/native corpus
qualification remain open; no second UMF validator or normalization algorithm
is introduced here.

## Decisions still required

ADR-003 acceptance and Python package/repository ownership; initial driver and sync/async mode; published Weft wheel/feature tuple; admitted authorization ABI; stable install version and consumer-migration route; exact managed Lakebase version/extension/identity/transaction profile; native realization of CONTRACT-009's specified minimum 24-hour receipt protection; and receipt-token/reached ABI. Python adapter/codec/corpus work can start independently where these choices do not affect semantics. Complete public capability release still waits for the shared protected runtime and qualification.


## Consumer closure order and accountable outputs

R1–R10 are release outcomes, not ten additional votes on already selected
transaction, exact-value or receipt semantics. Close the route decision first;
author corpus cases alongside shared runtime work; qualify native identity
before consumer effects; then run the complete release conjunction.

| Requirement | Required output and implementation slice | Outstanding selection versus execution |
| --- | --- | --- |
| R1 Python route | ADR-003 owner decision, named package home and corresponding ADR-001 amendment | Owner decision pending; do not accept either ADR by inference |
| R2 shared corpus | Versioned data manifest, setup/calls/expected/error/journal/alias artifacts and native two-way interchange runner; PY-07/B-015 | Shared case/operation/identity grammar proposals are authored; exact admitted fixture/procedure/observer profiles and full corpus artifacts remain to author; actual TypeScript/Python runs then required |
| R3 installation | Stable compatible layout, exact DDL digest, installer/check plus explicit consumer deployment invocation; CH-01 and LM-01–06 | Stable release tuple and managed target selection open; native install/migration evidence not yet qualified |
| R4 membership | Security-owned person membership and enforced read/write boundary; PY-03 | Shared authorization ABI/profile belongs to security workstream; native writer/reader/outsider/no-identity cases required |
| R5 origin | Original session actor and separately retained asserted action extension; PY-03/04 | Security/native origin handoff, then actual journal correspondence; host cannot supply authority |
| R6 dry-run | Adopted original transaction with contained savepoints and actual final-state validation; PY-01/04 | Select one driver/mode; execute same-plan dry-run/apply and unchanged-after-rollback cases |
| R7 retry/reached | Immutable original result/token, current-snapshot comparison and complete applied coverage; PY-04/06 | Select token/resolver and native clock/protection profiles implementing the existing minimum 24-hour floor from first trusted confirmed commit observation; execute RV-01–14, including lost-ACK, no-op, snapshot, restart, exact expiry boundaries and epoch cases |
| R8 interactive reads | Direct versus Weft routes and finite indexed/work budgets; PY-02/05 | Parsed-input ABI is Weft-owned; aggregate/index resource profiles remain; actual native plans required |
| R9 exact values | Existing CONTRACT-010 wire plus Python int/Decimal/lossless time/JSON projections; PY-01 | Select owner codec tuple; independent boundary and round-trip vectors required without float intermediates |
| R10 publication | Release names Python/TypeScript, PostgreSQL/managed target, layout, corpus, UMF, Weft and authorization/profile versions; PY-07/B-014 | Exact artifacts and publication tuple open; clean package install and full matching receipts required |

The first consumer-ready release must satisfy every row; a working compiler or
adapter alone cannot replace it. Until R3/R10 close, describe source pins as
recorded experimental integration inputs rather than stable dependencies. No
managed Lakebase or Aurora support claim follows from isolated PostgreSQL 17.9
evidence. Qualification names the actual target version, extension availability,
authenticated connection semantics and transaction restrictions.

## Original configuration snapshot protocol

PY-01 can consume the [shared twelve-column native snapshot wire](contracts/installed-context-admission.proposal.md#original-snapshot-host-projection-and-shared-native-wire). PostgreSQL retains the pre-effect capsule and compares live current state before returning bytes. Python preserves canonical xid/ordinal/generation text, exact hex bytes and direct SHA-256; it keeps original adapter/transaction/cut/profile custody and rechecks at use. Current-only collection remains a different protocol. The TypeScript/native 171-check component establishes scoped correspondence; Python execution, qualified transport/security/installation and public report/finalization remain PY-01/03/04 evidence.
