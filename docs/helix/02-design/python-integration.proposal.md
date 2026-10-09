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

### Security-enabled compiler adoption gate

Read-only review of the security owner's uncommitted Weft CONTRACT-005 and
`compile-request-v0.3.schema.json` on 2026-10-09 observes a separate
`weft-compile/0.3.0` candidate: exact UMF 0.8 source pins plus policy/ontology
source bytes, retaining the 0.2 SQL grammar. Its documented activation gate
refuses security-enabled compilation before backend emission. This is an owner
review input, not a selected Truss interface, published package or supported
security profile; do not build a release from the dirty owner checkout.

PY-02/PY-03 must preserve that distinction when the owner publishes the actual
interface. Compile capability and native execution capability are admitted
separately. A source-shape-valid policy packet, ordinary compiler artifact or
successful Python import cannot establish protected lowering or authorization.
Consume the owner's complete emitted security/result/host-obligation contract
through original Truss execution custody once it is available; do not append a
local security flag to an ordinary artifact or implement policy lowering here.

The independent Python integration schedule must cover an unsupported protected
request, an unknown compiler version, malformed security source, and a protected
request whose selected backend lacks the required lowering. Each refuses before
native submission and publishes no partial SQL/result. Instrument the admitted
executor to independently observe zero submissions. No refusal may trigger a
retry through 0.1/0.2, drop policy/ontology members, change the selected backend,
or convert the request to an ordinary query. Faults after native submission keep
the original execution/settlement rules instead of being labeled compiler
refusal. Exact diagnostics and positive protected cases follow the owner's
published versioned contract; this handoff does not freeze its draft API.

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

A later [offset regression](../04-build/evidence/design-audit/python-timestamp-offset-regression.json)
shows that Python's `fromisoformat` accepts and normalizes minute overflow
(`+00:60` becomes `+01:00`). The convenience candidate now checks hour/minute
components before conversion: outside 00–23/00–59 there is no datetime view,
while original text stays unchanged. Independent cases cover both offset signs,
overflow and exact boundary offsets. This restricts conversion availability;
it neither rejects an original upstream-admitted token nor assigns that token
new temporal meaning. The earlier seventeen-test report-wire receipt retains
its historical source pins and scope.

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

The private `python_raw_json_candidate.py` now retains immutable original UTF-8
source bytes and produces a separate immutable convenience tree with explicit
number-token wrappers. Its parser never routes JSON numbers through float or
int conversion, and exact strings stay distinct from numeric tokens. Original
whitespace, escapes, unknown extension content and literal `$a` remain byte-exact;
the convenience tree grants no alias substitution or executable interpretation.
It refuses duplicate members, non-JSON numeric constants and nested
PostgreSQL-bound NUL/unpaired-surrogate content.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s docs/helix/04-build/evidence/design-audit -p 'test_python_*candidate.py'
```

Twelve tests pass on Python 3.11 across numeric, timestamp, tree and raw-JSON
candidates. The raw parser independently matches all five source/token/string
fixtures and presence expectations, including escaped pointer names; controlled
source mutation cannot change retained bytes. Explicit source-size and lexical
nesting-depth and value-node checks precede parsing. A lexical preflight counts
containers and scalar values while skipping quoted content/member names; the
JSON decoder still owns syntax validation. Controlled over-limit cases prove
the decoder is never called, and exact-at-bound arrays/objects still decode.
Immutable projection rechecks node count. These finite source/tree bounds do not
establish complete precharged heap/copy accounting, including decoded member names,
source/text copies and simultaneous trees. Original semantic/profile admission, public package ownership,
qualified native transport and integrated whole-operation resource accounting
remain required. No parser success claims native JSONB fidelity or UMF support.

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

### Psycopg candidate review — 2026-10-09

Source review targets the tagged
[Psycopg 3.2.12 ctypes wrapper](https://raw.githubusercontent.com/psycopg/psycopg/3.2.12/psycopg/psycopg/pq/pq_ctypes.py),
not an installed or qualified build. `PGresult.ftype()` and `fformat()` expose
ordered column metadata; `get_value()` copies the native cell using its length
and distinguishes SQL NULL from empty bytes. `consume_input()` delegates to
`PQconsumeInput`; `get_result()` delegates to `PQgetResult`. These wrapper paths
do not provide the shared port's pre-read reservation or complete-frame parser
entry. The [official module documentation](https://www.psycopg.org/psycopg3/docs/api/pq.html)
identifies libpq as the network/result owner and distinguishes Python, C and
binary implementations. That live development documentation is explanatory,
not a version pin for this candidate.

The result layer is a plausible exact-value adapter. Ingress qualification is
still incomplete; this review neither rules out a libpq-backed implementation
nor establishes that a native bridge is sufficient. PY-01 must first select
one actual implementation and libpq source/build, then inspect its receive,
TLS, parser and allocation paths against the shared producer port. A Python
wrapper around these two calls cannot infer the missing observations afterward.

The execution packet must supply:

1. An exact driver/libpq build and one supported execution mode, with original
   lease ownership and an identified producer for every shared-port operation.
2. A source-backed finite bound for retained receive/parser/capture capacity,
   including simultaneous native and Python cell copies; accounting must reserve
   before work and release only when the corresponding backing is released.
3. Independent oversized, partial-frame, malformed-field, parser/callback-fault
   and cancellation cases, proving refusal before publication and preserving
   possible effects until native termination is established.
4. Host-transaction adoption and reconnect refusal cases on the same physical
   connection. Result metadata and transaction status alone do not prove the
   original lease or safe reuse.

If these cannot be produced for the selected stock driver, identify the smallest
transport change that supplies them and qualify it independently. Keep Python
orchestration, Weft compilation and security-owned enforcement at their existing
boundaries. No package recommendation or supported-driver claim is adopted by
this source review; native execution remains not run.

Use Python `int` for admitted integral domains and `Decimal` constructed from exact text for decimals, with domain/arithmetic context explicit. Driver raw cells remain text until profile decoding. Decimal operations must not inherit an ambient low-precision context that rounds accepted values. Timestamp transport retains the original exact text and offset; expose an aware `datetime` only when its microsecond representation is lossless. Finer precision requires a lossless wrapper/text representation or explicit refusal of the convenience view. Preserve raw exact JSON bytes; a convenience parser uses an admitted numeric decoder, never the default float path. Python bool must be distinguished from int at validation boundaries.

Read shapes retain absent versus explicit null, ordered key components, exact large integral values and original selected decimal/token meaning. Known JSON-like values and retained unknown extensions cannot be normalized into different meanings. Exact wire grammar remains CONTRACT-010's responsibility; these mappings are Python implementation obligations, not new UMF types.

### PY-01 independent exact-value expectations

#### Python-owned framing candidate: pg8000 1.31.5

Source-only inspection of the
[published pg8000 1.31.5 wheel](https://pypi.org/project/pg8000/1.31.5/)
uses wheel SHA-256
`0af2c1926b153307639868d2ee5cef6cd3a7d07448e12736989b10e1d491e201`
and `pg8000/core.py` SHA-256
`cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26`.
The wheel was downloaded into an isolated temporary directory, not installed or
executed. This is an alternative prototype candidate, not a selected dependency.

Its Python `handle_messages` reads a five-byte header and then the declared body
before dispatch. `_read` builds a bytearray and returns a bytes copy; the connection
uses a socket file object. RowDescription retains type OID/format, while DataRow
slices and decodes cells before invoking type converters and accumulating rows.
The inspected dispatch path does not impose Truss's pre-body frame budget or
retain the required original raw-cell observation. A type-converter override is
too late to account for receive backing, body copies or malformed framing.

A prototype must reserve before body reads/copies, validate signed message/cell
lengths and exact complete consumption, admit every message kind for its cycle,
retain raw ordered metadata/cells before conversion, and account for buffered
socket/TLS read-ahead and accumulated rows/notices. Partial EOF, negative/oversized
lengths, trailing bytes, unexpected messages, decode faults and late callbacks
need independent containment cases. Python-owned source makes those modification
points inspectable; it does not prove allocation bounds, safe host adoption or
native termination. Compare an actual bounded prototype with the libpq candidate
before selecting PY-01's supported driver/build/mode; preserve the same shared
producer port and security/compiler ownership in either route.

The private [complete-frame decoder candidate](../04-build/evidence/design-audit/python_pg_frame_candidate.py)
now implements RowDescription/DataRow syntax from PostgreSQL 17's
[message format](https://www.postgresql.org/docs/17/protocol-message-formats.html).
Five independently authored tests preserve ordered metadata, unsigned OIDs,
signed size/modifier fields, duplicate names, raw binary/text cells, NULL versus
empty bytes and zero columns; malformed lengths/counts/formats/UTF-8 names,
trailing/partial frames and mutable input refuse. Its one-MiB/4,096-column limits
are candidate syntax bounds, not an adopted driver resource profile. Run with
`python3.11 -m unittest discover -s docs/helix/04-build/evidence/design-audit -p test_python_pg_frame_candidate.py`.
This decoder receives an already retained immutable frame and copies members.
It supplies no ingress reservation, socket/TLS behavior, command-cycle provenance,
statement-versus-portal descriptor qualification, native authority or publication.
All corresponding original producer obligations remain required before transport
activation; the candidate does not replace the selected shared driver port.

The [read-only native probe](../04-build/evidence/design-audit/check_python_pg_frame_native.py)
now passes against the confirmed owned PostgreSQL 17.9 container. Its
[receipt](../04-build/evidence/design-audit/python-pg-frame-native.json) retains
actual result/command/ready frames and decoder/checker source pins. Five raw
cells and their ordered descriptor facts match independent expectations, including
NULL, empty text, exact large decimal and Unicode. The administrative local-trust
session executes BEGIN READ ONLY/ROLLBACK without installed changes. This proves
native result syntax correspondence only; the receive harness is not the shared
original driver producer, qualified cancellation/TLS/account or public assembly.

The frame test command now runs six tests, adding offline verification of the
saved native frame sequence, original decoder/probe source hashes and independent
metadata/cell/command expectations. It performs no network access and never
rewrites the receipt. Passing this sixth test is saved-evidence correspondence,
not a fresh native run or driver qualification.

#### pg8000 candidate hook implementation map

Read-only inspection of the previously pinned pg8000 1.31.5 wheel identifies
separate receive loops in core.py: constructor startup at lines 389/391 and
`handle_messages` at lines 839/841. Both read a five-byte header and then dispatch
an already materialized body through `message_types`. The buffered socket is
created at line 339; module-level `_read` at lines 149–160 creates a bytearray,
extends it from further reads, then copies to bytes. These line references apply
only to the exact core.py digest already recorded above.

A private adapter experiment must establish its account/custody context before
constructor startup and instrument both loops, not override only the later
query handler. Qualify transport read-ahead at socket/TLS/buffer construction;
a body-size check after `makefile` has filled an unaccounted buffer is too late.
Route both loops through one instance-owned admitted receive procedure that checks
message eligibility, original header/length, body reservation and raw capture
before semantic dispatch. Do not globally monkey-patch `_read`: unrelated
connections must retain independent account and command custody. Preserve original
complete wire separately from scalar conversion and accumulated result rows.

Enumerate every query-loop caller (simple execution, prepare, execute, portal
continuation and statement close) against the pinned source before claiming
coverage. Map each dispatched notice, error, parameter, authentication and row
message to its original bounded handler/account or explicit unsupported route.
No unknown message may first allocate its body and then obtain admission by a
handler lookup. Startup authentication and backend-key material retain their
security/secret handling; this review authorizes no credential collection.

Controlled tests must inject exhaustion into startup and each selected query
entrypoint, observe zero forbidden subsequent reads/dispatches, and verify that a
second connection's budget cannot be charged or released. Include partial header,
partial body, read-ahead, notice floods, invalid signed lengths, handler errors
and cancellation with original backend outcome still unknown. All raw bytes,
lengths, decoded metadata and copy lifetimes must match their admitted account.
This maps an experiment, not a supported driver selection or a maintained fork:
exact source/build/mode, complete protocol behavior, native authority/settlement
and upstream maintenance strategy remain adoption requirements. Do not rerun the
already completed Weft wheel build to substitute for this driver work.

#### pg8000 pre-startup TLS admission boundary

The same pinned core.py source has an additional receive path before either
framed loop: `_make_socket` sends SSLRequest, reads one byte at line 232, and
wraps the socket at line 234. This negotiation is not a PostgreSQL five-byte
message and must have separate original transport admission/accounting. Source
inspection also finds that True/None ssl_context values create a context with
check_hostname=False and CERT_NONE (lines 222–225); with None, a non-S response
does not take the explicit refusal branch. These are static source observations,
not executed TLS behavior or a supported Truss transport policy.

For an advertised authenticated TLS tuple, select the exact original SSLContext,
certificate/hostname/endpoint and channel-binding profile under the security
owner's admission. Do not use the driver's Boolean/default configuration as proof
of authenticated transport. A profile requiring TLS refuses server N, EOF,
malformed negotiation and failed certificate/hostname admission before startup
credentials or application commands. An explicitly admitted local non-TLS tuple
remains separately scoped; no network fallback may silently switch between them.
Account handshake reads, backing buffers and failure cleanup before constructing
the framed startup receiver, while preserving original authentication custody.

PY-01b/PY-03 independently observe zero startup/authentication/application sends
after each failed negotiation or identity check, then qualify a correctly verified
endpoint and owner-approved channel-binding path. Test the complete selected
managed Aurora and Lakebase endpoints separately; the saved trust-authenticated
local PostgreSQL probe establishes none of these TLS outcomes. This is driver
integration work consuming the owner's transport/authentication contract, not a
new Truss certificate resolver or authorization model. No credentials or actual
TLS connections were accessed during this source review.

#### pg8000 connection-local transport and row-handler seams

The pinned 1.31.5 [source review](../04-build/evidence/design-audit/pg8000-instance-hook-source-review.json)
identifies a concrete experiment path: `CoreConnection` accepts a supplied
`sock`; the constructor creates its file only after `_make_socket` returns the
final transport. Its dispatch table binds instance row-description/data-row
handlers. An original adapter can investigate connection-local transport and
handler hooks without globally replacing `_read` or `PG_TYPES`. This is a
source-backed candidate path, not a driver choice or implemented raw producer.

Install original account/custody before constructor startup. The final file
producer must establish bounded read-ahead and pre-header/body admission for
both receive loops, including notice/error/authentication messages. Stock `_read`
still allocates/extends/copies buffers, and stock handlers still accumulate rows;
a supplied socket alone cannot account those allocations or establish release.
Original command/generation and cleanup/settlement custody remain mandatory.

TLS can replace the supplied socket before `makefile`. Instrument the final
security-owner-approved transport and preserve original endpoint/certificate and
channel-binding derivation; do not assume a raw socket proxy survives wrapping.
Passing an already TLS-wrapped socket with `ssl_context=False` skips this driver's
channel-binding derivation and cannot silently stand in for the selected secure
profile. Neither a global socket/SSL monkey patch nor turning TLS off supplies
the missing admission. Unsupported transport/security combinations remain unavailable.

The stock RowDescription metadata format uses signed 32-bit OIDs. The Truss raw
metadata path must preserve unsigned table/type OIDs, alongside signed attribute,
type-size and modifier fields; the existing independent frame vector with
4,294,967,295 OIDs demonstrates the distinction. Unknown OID/profile admission
is separate from unsigned transport. Raw DataRow capture must verify the complete
original count/length/body before conversion, preserve SQL NULL versus exact cell
bytes, and bind the same original descriptor/cycle. Reusing already converted
stock `context.rows` cannot reconstruct that raw port.

Qualify a connection-local experiment with independent sibling connections,
constructor/query/prepare/execute/close paths, unsigned metadata, exact numeric
and Unicode cells, malformed/trailing rows, fragmented/oversized reception,
handler failure and unknown termination. Keep authentication/backend-key material
out of evidence output. This source review does not install the driver, authorize
credential collection, qualify a native person or activate a Python package.

The subsequent [native instance-hook receipt](../04-build/evidence/design-audit/pg8000-instance-native.json)
now exercises that exact installed driver in an isolated Python 3.11 environment.
A supplied socket produces an instance-local file backed by the existing bounded
raw receiver, avoiding the stock buffered `makefile`; instance row handlers
consume the original completed header/body through the strict frame decoder.
The fixed BEGIN READ ONLY/SELECT/ROLLBACK query independently matches NULL,
empty text, the large exact decimal, Unicode, server version and ordered OIDs.
The experiment refuses authentication flows other than local AuthenticationOk;
it captures no authentication/backend-key body in its receipt. Exact dependency
versions, core/probe/receiver/decoder hashes and raw message-size counters are saved.

The private instance classes now reside in `pg8000_instance_candidate.py`,
with six offline controlled-transport tests. Fragmented header/body and zero-body
handling pass; malformed/partial input, wrong body requests, send-budget refusal
and unknown send failure permanently close the experiment file without budget
refund or sibling interference. A discovered pre-send budget refusal previously
left the file usable; it now closes before any send. Closure is only an adapter
state, not native termination, confirmed rollback or safe pool reuse. The native
probe was rerun after this refactoring and pins the extracted candidate source.

Constructor and query-loop exceptions now close the instance file as well.
Independent complete-frame controls exercise the original driver dispatch with
malformed row metadata and an unknown message kind: both raise, leave a following
ReadyForQuery unread, and prohibit subsequent reads or sends. The retained prior
transaction status is not a fresh outcome observation. This quarantine prevents
adapter reuse; it neither terminates the native transaction nor releases original
recovery custody. The caller still owes qualified outcome and cleanup handling.

A separate report-only driver experiment now closes the raw-capacity mismatch
at its private scope. `pg8000_report_instance_candidate.py` creates its initial
4,194,315-byte frame bound and eight-MiB outbound experiment allowance before
startup, requires one OID25/format0 descriptor and one original report row, and
uses the response-only frame decoder. The generic instance candidate stays at
one MiB. These constants are experimental raw limits, not a public resource
profile or reset of an active original operation account.

The [full-driver report receipt](../04-build/evidence/design-audit/pg8000-report-instance-native.json)
records actual local pg8000 execution with independently frozen four-MiB original
bytes, UTF8 startup observations, exact descriptor, BEGIN/SELECT/ROLLBACK tags
and all nineteen schema fields. Two report-path capacity controls add exact-frame
success and one-over refusal before any body ingress; eight total controlled
instance-file tests pass. Both driver receipts were refreshed against the current
shared candidate source.
The query remains a fixed read-only literal echo; no authentic report production,
persistence, full driver/parser/native copy accounting or protected publication
is qualified. Do not widen caller-input admission or adopt this experiment as the
original PY-01b port solely because the complete payload fits.

This is actual driver seam evidence, not the original protocol-port implementation.
Stock `_read` and row/helper allocations remain outside a qualified complete
account. The probe prefetches a whole admitted raw frame before returning its
header to the driver; its raw bounds do not establish all simultaneous driver
copies or callback backing. TLS/person identity, mode/lifetime/concurrency,
cancellation/unknown outcomes, native cleanup, report-size paths and public
packaging remain separate PY-01b/PY-03/PY-07 exits. Preserve the earlier source-only
review as historical; do not repeat that no driver experiment exists or claim
this read-only local result as a Lakebase/Aurora or protected mutation result.

#### Raw-wire probe versus pre-ingress accounting

Source inspection of `check_python_pg_frame_native.py` identifies two limits of
its retained read-only evidence. `receive` checks message count only after reading
and appending the complete next frame; the 101st body may therefore already be
materialized before refusal. `read_exact` retains each received fragment in a list
and joins them, with no independent fragment/work or simultaneous-copy account.
The fixed byte caps are harness bounds, not PY-01b pre-ingress guarantees. Preserve
the saved probe receipt and its source pins at that actual scope.

The original admitted driver must reserve eligibility for another message before
reading its header, then admit the length and reserve body/backing/copy capacity
before any body read. Include framing, transport buffering, fragmented reads,
retained raw observations and decoder views in the complete account; counting
only final joined bytes misses simultaneous lifetimes and per-fragment work.
If header/body reception stops with unknown backend work, original command-cycle
custody and settlement still apply. Resource refusal cannot manufacture an idle
connection or release a publication.

PY-01b's controlled transport tests must observe actual read requests: exhausting
the message budget causes zero reads for the next message; an oversized or
cumulatively unaffordable header causes zero body reads; and one-byte fragmentation
cannot exceed the registered allocation/work reservation. Include truncation,
EOF and cancellation after partial body reception, independently verify retained
original bytes and record actual cleanup/unknown outcomes. Compare exact-capacity
success with otherwise valid one-over refusals. These requirements apply to every
selected message kind, including notices and errors, not just DataRow. An admitted
bounded strategy may copy or buffer differently; Truss does not require the probe's
chunk-list implementation or choose a driver from this review. Native/TLS/driver
qualification and the full-report capacities below remain separate prerequisites.

#### Private controlled-transport receive candidate

`python_pg_receive_candidate.py` now implements an instance-local raw receiver
using recv_into: message/header eligibility precedes ingress; complete signed
length/frame/cumulative-byte admission precedes body allocation and reception;
a finite read-call budget precedes each fragmented read. Every receive failure,
including interruption, permanently closes that receiver and retains consumed
attempt/budget state. It neither closes nor settles the original backend and must
never justify returning a connection to a pool. It creates one immutable complete
frame after reception; decoder and semantic dispatch remain separate.

Run from the Truss repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s docs/helix/04-build/evidence/design-audit -p test_python_pg_receive_candidate.py
```

Six independent controlled-transport tests pass on Python 3.11. Literal frame
bytes and observed recv_into request inventories verify fragmented exact retention,
zero next-header reads on message exhaustion, zero body reads after invalid or
unaffordable lengths, read-work exhaustion before another fragment, partial EOF,
interruption, malformed returned counts and unaffected sibling state. These are
synthetic receive controls, not live driver/TLS startup or native command cycles.
The candidate bounds cover raw bytes/message attempts/read calls only; header and
whole-frame backing, immutable-copy lifetime, transport/TLS buffers, decoded values
and aggregate work still need the original complete account. No driver, resource
profile, custody issuer or public Python package is selected by this component.

The separate `check_python_pg_receive_native.py` now exercises that receiver over
the existing owned local PostgreSQL 17.9 raw socket with the earlier independently
specified read-only query and BEGIN READ ONLY/ROLLBACK. The saved
[receive receipt](../04-build/evidence/design-audit/python-pg-receive-native.json)
pins receiver, decoder and probe bytes, retaining exact ordered descriptors/cells
and remaining raw bounds. Startup and query frames share the same receiver instance.
No credentials or backend-key material are retained in the receipt. The seventh
receive test checks its source correspondence and independently expected null,
empty, large exact decimal, Unicode, server text and command sequence offline.
This adds actual local recv_into correspondence; it does not qualify authenticated
TLS, a pg8000 adapter, complete allocations, cancellation/settlement, installed
security or publication. The original frame receipt remains unchanged.

#### Native full-carrier size and decoder mismatch evidence

`check_python_pg_receive_full_carrier_native.py` now performs a separate local
read-only probe with bytea_output=hex and a four-MiB ASCII bytea value. The receiver
admits the exact 8,388,621-byte DataRow under explicitly larger harness bounds;
complete original cell bytes match the independently constructed hex literal.
The existing fixed-one-MiB frame decoder refuses that same complete frame. The
[separate receipt](../04-build/evidence/design-audit/python-pg-receive-full-carrier-native.json)
retains exact lengths, complete-byte comparison, cell digest, original source
pins and the decoder refusal, without storing the large cell as receipt hex.

The first attempted probe stopped at that decoder refusal and emitted no success
receipt. The completed read-only rerun records the refusal explicitly and compares
raw framing/cell content independently; it does not silently change the decoder's
admitted capacity. This demonstrates a concrete receiver/decoder profile mismatch,
not full report support. A1/PY-01b must admit compatible transport, decoder,
carrier and simultaneous-copy accounts before submitting a report-producing
operation; otherwise refuse before effects. The synthetic ASCII value establishes
wire size only, not a genuine nineteen-field report or its producer completeness.
TLS, driver command settlement, native authority and publication remain unqualified.

#### Preferred internal report transport experiment: canonical UTF-8 text

The current TypeScript raw ingress explicitly refuses binary result formats;
changing a Bind result format is not an admitted fallback. For the next internal
report experiment, prefer a text/OID25/format0 route carrying the producer's
already canonical UTF-8 report bytes, with UTF8 server/client encoding and exact
source-to-wire byte correspondence. This is a selected experiment direction,
not a public profile or permission to use the fixed-one-MiB decoder.

PostgreSQL's [protocol format rules](https://www.postgresql.org/docs/17/protocol-overview.html#PROTOCOL-FORMAT-CODES)
distinguish each type's text output from binary encoding. Its
[17.9 manual](https://www.postgresql.org/files/documentation/pdf/17/postgresql-17-US.pdf)
defines convert_from for original encoded bytes. A bounded conversion of admitted
canonical UTF-8 bytea to text can avoid bytea hex expansion; do not cast arbitrary
bytea to text or parse/reserialize through JSONB. Canonical member order, whitespace,
escapes, exact numeric token spelling and unknown content must remain byte-exact.
JSON control characters are already escaped; actual raw NUL or malformed UTF-8
refuses this route. Preserve original report bytes/digest as the equality basis.

A single four-MiB text cell requires 4,194,315 DataRow bytes, before separate
messages and simultaneous ownership. Independently test this exact boundary,
Unicode/escape content, malformed bytes and changed client encoding, comparing
complete native source and received bytes rather than character counts or digest
alone. Then run genuine full nineteen-field reports through both hosts under the
same original producer/wire/decoder/account tuple. Native conversion/detoast and
host UTF-8/backing/string/parser copies remain charged; reduced wire expansion
does not prove bounded allocations or settle driver/publication custody.

This experiment applies only to the complete canonical report route. Other raw
binary values and compiled query columns keep their original codec/type/format
profiles. Do not change Weft lowering or the security owner's working ingress
implementation to make this experiment pass. If correspondence or complete
capacity cannot be admitted, retain pre-effect refusal and the existing full
report requirement.

The selected text experiment now has a
[separate native receipt](../04-build/evidence/design-audit/python-pg-receive-canonical-text-native.json).
Its read-only probe admits original startup server/client UTF8 observations and
returns a complete four-MiB synthetic canonical JSON value through convert_to /
convert_from and text/OID25/format0. Every received byte equals the independently
constructed original literal; the DataRow is exactly 4,194,315 bytes. This confirms
that route's wire-size reduction without JSONB reserialization. The fixed-one-MiB
decoder still refuses, explicitly retained in the receipt. Therefore receiver/
decoder/account composition and genuine report production remain open; this
experiment is not a supported report capability or a new binary codec.

#### Internal response parser profile is distinct from request admission

Current source inspection identifies another A1/PY-01b composition gap:
`packages/postgresql/src/acceptance-json.ts` fixes source capacity at 1,048,576
bytes and logical work at 2,000,000; `ReportWireCandidate.prepare` likewise calls
Python's retained parser with a one-MiB source bound. A four-MiB canonical response
cannot be admitted through either current report path. Merely raising the
TypeScript byte ceiling also fails its work account, whose initial charge already
includes the entire source length. The saved codec/report receipts retain their
original input subsets; transport success does not expand them.

Author and admit a separate complete canonical-response parser/schema profile
for the selected report output ceiling. Keep original caller-input/source admission
limits unchanged. Its original registry tuple must bind parser grammar, full
nineteen-field schema closure, source/UTF-8/work/depth/node/member limits and all
simultaneous raw/string/schema/convenience-view allocations to the same operation
account. No caller parameter, response length or native success mints that profile.
Use the full original report bytes before schema projection; preserve numeric
node refusal and exact tagged numeric values, escaped NUL, duplicate-member and
unknown-content rules. Do not bypass schema admission with a parsed-looking object.

Freeze independent controls using genuine schema-valid report artifacts at the
selected response boundary and one over, then inject insufficient logical work
and simultaneous-copy capacity. Verify complete fields/bytes and honest resource
refusal separately from invalid-schema classification. Run unchanged caller-input
boundary controls alongside them so a response-profile change cannot silently
admit larger mutation/catalog requests. The four-MiB payload transport fixture is
valid JSON but not a full report; it cannot supply that positive semantic case.
Selected decoder/parser/account implementation and original admission remain open.

The [compact response boundary fixture](../03-test/report-response-boundary-v0.1.proposal.fixture.json)
now freezes complete nineteen-field synthetic report wires at 4,194,304 and
4,194,305 bytes. Eight independently encoded diagnostic artifacts keep each
base64 scalar below one MiB; exact complete wire hashes and original base-fixture
pin prevent the test from substituting a tiny or incomplete report. The checker
validates both against the pinned full schema closure, rejects omission of each
required field, verifies every diagnostic's complete bytes/digest, and observes
current codec resource refusal before schema admission. Synthetic diagnostic/
profile custody does not establish genuine producer authority or runtime effects.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 docs/helix/04-build/evidence/design-audit/check_report_response_boundary.py
```

Use jsonschema 4.23.0/referencing 0.35.1. The fixtures supply independent future
response-parser exact/one-over controls, not proof that either current codec
supports the four-MiB boundary. Original semantic/profile/account admission and
actual report-producing integration remain required.

A separate private `ReportResponseCandidate` now reuses the original pinned
schema closure while admitting response source bytes up to four MiB. The legacy
`ReportWireCandidate` and its one-MiB request/input behavior remain unchanged.
Four independent tests consume the frozen boundary fixtures: complete nineteen-
field response admission, one-over and legacy refusal, numeric/schema/duplicate/
Unicode negatives, mutable caller-buffer isolation and instance-free parser errors. Inherited native conversion
explicitly refuses because its carrier/account composition is not admitted.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s docs/helix/04-build/evidence/design-audit -p test_python_report_response_candidate.py
```

The malformed-wire regression originally observed JSONDecodeError.doc retaining
the complete response. Known parser failures now expose a short grammar/unicode/
resource category raised outside the original handler, with no doc/object or
instance-bearing cause/context. Independent malformed JSON and invalid UTF-8
controls verify those properties and preserve the categories. The complete native
echo was rerun after this source change; its current receipt pins the corrected
candidate. Protected original raw-source custody and public diagnostic/traceback
handling remain the original adapter's responsibilities.

This closes the private Python response source/schema subset gap only. The scope
is response_schema_bytes_only_without_account_admission: aggregate parser/schema
work and heap, simultaneous copies, TypeScript parity, original registration,
driver custody and genuine producer/native publication remain open. A structural
four-MiB positive does not mint the required original response profile or increase
caller request limits.

The separate private TypeScript response scanner now admits the same exact four-
MiB fixture under four-MiB source and 33,554,432 logical-work candidate limits;
the original request scanner remains unchanged. Three Bun tests/fourteen assertions
and strict TypeScript pass. Independently reconstructed wires match both frozen
Python hashes, preserve all nineteen fields, refuse one-over and legacy request
admission, preserve exact numeric strings/escaped NUL, and reject numeric nodes,
duplicates and invalid Unicode. Distinct long keys below source/member/depth bounds
also exhaust logical work with an honest resource refusal.

This is response grammar/structure evidence only. The response scanner records
its original request-scanner fork digest and retains existing duplicate/Unicode/
numeric refusal semantics. Its copied algorithm is private experimental code, not
an adopted shared parser or second UMF validator. Full schema integration and
original aggregate allocation/account/registration remain required; the 33,554,432-unit
logical work bound is not a host heap allowance or release profile. Neither host
candidate activates native conversion or report publication.

The TypeScript private response candidate now composes the scanner with the same
pinned eleven-schema closure as Python. Four tests/37 assertions and strict
TypeScript pass: exact frozen four-MiB wire/schema admission, one-over refusal,
every required-field omission, caller-buffer copying and the previous grammar/
work controls. `report-response-schema-candidate.ts` checks all original schema
bytes before compilation, returns response data only and exposes no native carrier
or operation issuer. Its short generic schema refusal does not expose the report
instance as a diagnostic.

The new candidates establish both hosts' structural response paths at the frozen
boundary. They still lack original aggregate account/registration and genuine
producer/driver/native/publication correspondence. The original one-MiB request
and report-to-native handoff components remain unchanged; their old source-pinned
receipts are not expanded by this response-only composition.

The [complete native echo receipt](../04-build/evidence/design-audit/python-report-response-native-echo.json)
now compares the entire independently frozen four-MiB, nineteen-field report over
local trust-authenticated PostgreSQL text/OID25/format0 and validates its actual
received bytes through `ReportResponseCandidate`. Original startup UTF8 admission,
exact 4,194,315-byte DataRow, complete response-only frame decoding, expected-byte
equality, nineteen schema fields and receiver/decoder/parser/probe source pins
are retained. The query is
an escaped read-only literal echo; its template/digest are stored instead of a
four-MiB SQL string. The old one-MiB frame decoder refusal remains explicit.

This exercises the actual received synthetic full wire and Python response
schema candidate, not genuine diagnostic/report production, a production-admitted
driver/frame/account profile, authoritative accepted IDs, committed report persistence, installed
security or publication. It uses independent fixture admission before native
submission and BEGIN READ ONLY/ROLLBACK. Original complete operation accounting,
qualified driver/settlement and public profile adoption remain required.

A separate private retained-frame candidate,
`python_report_frame_candidate.py`, now admits only a complete single nonnull
DataRow cell up to 4,194,304 bytes (4,194,315 frame bytes). Four independent
syntax tests cover exact/one-over capacity, malformed signed lengths, missing or
extra bytes, wrong message/column count, SQL NULL and mutable backing refusal.
The `described_report_cell` composition also parses the original retained
RowDescription and requires exactly one OID25/format0 column; bytea, JSON, JSONB,
binary format and malformed metadata refuse before response-cell parsing.
The response codec suite additionally composes the independently frozen full
nineteen-field report frame with original schema validation. The old decoder
and its original native receipts remain unchanged. The complete native echo receipt
now pins and exercises this response decoder against actual received bytes.
These metadata syntax checks do not establish original connection/cycle custody,
UTF8, ingress/account custody, command settlement or
native qualification; those require the original PY-01b composition. Arbitrary
cell bytes pass syntax alone and cannot authorize publication or commit claims.

#### PY-01b complete-report command-cycle qualification

For the selected single-text-report result procedure, freeze its complete result
shape and original command-cycle protocol before implementing host dispatch.
Require exactly the declared description and row count, original OID25/format0,
UTF8, complete cell/report validation and the original procedure's permitted
command completion and terminal transaction-state observations. Message bytes
must belong to the same admitted live connection, request and generation; a
saved matching descriptor from a previous command cannot supply that custody.
Multiple-result procedures need their separately declared complete shape rather
than truncation to the first acceptable report.

Independently author the following PY-01b fault schedules, using the same full
nineteen-field report as the success control and observing publication and
connection disposition separately from parsed bytes:

| Received sequence or failure | Required observation |
| --- | --- |
| Complete valid DataRow, then EOF/cancellation before command completion | Retain the provisional original bytes under their account; no completed operation result or safe pool reuse from successful report parsing |
| Complete report and command tag, then loss before terminal cycle observation | Command-cycle outcome remains unresolved under the original driver procedure; a command tag alone supplies neither native commit nor cleanup proof |
| Backend error after a complete report row | Original bounded error/transaction handling governs failure; the earlier report is not substituted for a successful result |
| Omitted, repeated or reordered description/row/completion; extra second report row | Refuse the complete result-shape mismatch; no first-row success or silent discarded result |
| Description or row from an earlier generation/interleaved command | Refuse custody mismatch before publishing protected data, even when metadata and report bytes independently match |
| Notices or error fields exhaust the selected account between report and completion | Preserve resource refusal and original outcome/cleanup custody; neither dropping messages nor refunding spent work can force success |
| Original transaction status differs from the expected procedure boundary | Original execution/settlement procedure classifies the mismatch; no invented commit, automatic retry or connection replacement |

The observer records actual submitted commands, complete permitted message
inventory, outstanding request/generation, retained report state, publication
attempts, native termination/settlement and whether the physical connection was
quarantined or safely returned. No-state-change expectations must be observed
independently; an absent delivered response does not prove absent backend work.
An idle ReadyForQuery status is a cycle observation, not proof that a particular
mutation or administrative attempt committed. Conversely, confirmed original
commit evidence remains committed when later report delivery fails. Adopted
execution preserves caller ownership and never issues an outer end command to
make these tests pass. These planned controls qualify the original adapter;
the read-only literal echo and retained-frame/schema candidates do not implement
the complete command lifecycle or settle a real acceptance attempt.

#### Full-report wire capacity before driver selection

The frame candidate's one-MiB limit cannot transport the existing four-MiB
canonical report ceiling. PY-01b must select its actual SQL result OID/format and
compute protocol capacity from the complete representation before acceptance
effects. A single-cell DataRow occupies eleven bytes plus the cell payload.
For a 4,194,304-byte canonical report returned as binary bytea, that is 4,194,315
frame bytes. With PostgreSQL
[bytea hex text output](https://www.postgresql.org/docs/17/datatype-binary.html),
two digits per byte plus the `\x` prefix produce 8,388,621 frame bytes. These
are representation arithmetic, not an adopted SQL route or native measurement.

Reserve the simultaneous native report, wire representation, receive backing,
complete frame, decoded bytes and host report views under the selected original
account. Bind text output settings or binary-format selection to actual metadata;
do not infer a hex bound if escape output is possible. Multiple cells/rows,
metadata, notices and other cycle messages need their own complete inventory.
Increasing a frame constant alone cannot qualify those lifetimes or introduce
support for a different result carrier. Refuse an incompatible producer/transport
tuple before application effects, rather than discover capacity failure after
commit or silently reduce the report guarantee to the small prototype.

The syntax suite now has seven tests. The new independent exact/one-over case
uses a complete otherwise valid single-cell frame at 1,048,576/1,048,577 bytes;
it confirms the prototype limit rather than attributing oversized refusal to
malformed input. The existing saved native receipt remains unchanged and scoped
to its small read-only result.

#### libpq receive-path qualification correction

Review of PostgreSQL
[REL_17_9 fe-misc.c](https://raw.githubusercontent.com/postgres/postgres/REL_17_9/src/interfaces/libpq/fe-misc.c)
shows `pqReadData` moving retained input bytes and warns that input-buffer
pointers/indexes may not survive the call. More importantly, `pqSendSome` can
call `pqReadData` while flushing output, including nonblocking operation and
write-failure handling. Therefore reserving ingress only around Python
`consume_input()` is insufficient for this source: sending/flushing may receive
before that wrapper is invoked. Socket readiness alone does not identify the
actual receive operation or retained buffer lifetime.

PY-01's source-backed producer inventory must include every send/flush/error
path that may receive, plus TLS and parser ownership. Its fault packet must
induce output backpressure with incoming responses/notices and a write failure,
then independently observe pre-read reservations and preserved original cycle
custody. No inferred refund follows input compaction or a wrapper return. This
is a concrete qualification obligation for the reviewed candidate, not proof
that the installed libpq has this exact build or that a bridge is implemented.

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


## Private PY-01a composed report schema checkpoint

The private [Python report candidate](../04-build/evidence/design-audit/python_report_wire_candidate.py)
consumes the same eleven pinned original schemas as the TypeScript composed
report codec. It uses Python 3.11 with jsonschema4.23.0 and an explicit local
referencing registry; it implements no substitute schema language or remote
reference fetching. Original numeric-free bytes pass through the bounded retained
JSON candidate before a temporary validation view. The returned original immutable
bytes/tree remain separate from that view. Missing any of the nineteen fields,
unknown versions, numeric nodes and invalid nested rebind/reactivation shapes refuse.

The [receipt](../04-build/evidence/design-audit/python-report-wire-candidate.json)
records seventeen passing tests across numeric/time/tree/raw-JSON/report candidates,
all source/schema pins, exact dependency versions and original test output.
Shape-valid forged source/effect examples explicitly retain codec-only scope;
artifact digest/meaning, complete actual effects, authority and commit are not
established by schema validation. The one-MiB/depth128/node100000 parser bounds
cover this controlled prototype; schema traversal and simultaneous retained/
validation allocations do not yet have the complete original precharged resource
profile. PY-01b transport and native acceptance remain unavailable.

Reproduce in a dedicated Python3.11 virtual environment using
`pip install -r docs/helix/04-build/evidence/design-audit/python-report-wire-candidate.requirements.txt`,
then `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s docs/helix/04-build/evidence/design-audit -p 'test_python_*candidate.py'`.
Earlier twelve-test standard-library-only checkpoints remain historical; this
seventeen-test run includes the explicit schema-validation dependencies. Dependency
selection here is experimental, not a package-ownership or release-route decision.
The validator API follows its [versioned documentation](https://python-jsonschema.readthedocs.io/en/v4.23.0/validate/)
and [local reference registry contract](https://python-jsonschema.readthedocs.io/en/v4.23.0/referencing/).


### Original report-byte interchange and NUL correction

The [shared wire checker](../04-build/evidence/design-audit/check_python_report_interchange.py)
now runs 39 independently expected positive/negative controls through Python and
TypeScript's explicit composed codec against identical original bytes and the
same eleven schema pins. The [receipt](../04-build/evidence/design-audit/python-report-interchange.json)
retains original source digests, both decisions and exact accepted-byte equality.
Controls include all nineteen missing fields, versions, nested key reactivation,
complete v0.2 rebind, numeric/boolean confusion, duplicate members, Unicode/escape
spellings, byte capacity and explicit shape-valid provenance forgery. Acceptance
of the latter remains visibly codec-only, not actual effect/provenance admission.

This comparison exposed Python's inappropriate application of its PostgreSQL-text
NUL restriction to an original byte document. The inspected native
`canonical-string-bytes.sql` deliberately escapes original NUL bytes into canonical
bytea without converting the original NUL to text. TypeScript's corresponding
positive scalar/member tests already preserve this meaning. Python report parsing
now explicitly selects byte-document NUL preservation; default PostgreSQL-text
convenience still refuses it, and unpaired surrogates still refuse. No native SQL
or TypeScript behavior was changed. Preserve opaque artifact bytes without
interpreting their content or inferring native-cell suitability.

The updated Python codec suite passes 18 tests; the TypeScript report/carrier suite
passes 16 tests/77 assertions, and the checker passes strict TypeScript. The older
17-test receipt retains its original source hashes as historical evidence. These
controls cover shared wire shape and original bytes within their exercised bounds;
they do not align the full host/native task/retained-allocation profiles, qualify
transport, or run PY-07's actual bidirectional database writers/readers.

Reproduce with the candidate's pinned Python environment:
`PYTHONDONTWRITEBYTECODE=1 python docs/helix/04-build/evidence/design-audit/check_python_report_interchange.py`.
The checker invokes the existing Bun codec with the selected local dependency
package; this is test orchestration, not a JavaScript runtime requirement for the
Python implementation. Public packaging/driver/security/resource adoption remains
separate.


### PY-01a/01b complete report resource composition

The shared wire checker now has 42 independently expected controls. Three added
rebind-value controls preserve original bytes for 61 nested sequences (actual
report container depth127), refuse 62 sequences (depth129 above cap128), and
refuse a wrong-type integer token at the deepest admitted leaf. Both hosts agree
under the pinned eleven-schema bundle. These are bounded parser/schema/byte
observations; they do not prove the history event's semantic rebind effects,
native value admission or complete allocation accounting. Earlier 39-control
checkpoints retain their historical scope.

The private Python report candidate now returns a fixed schema-refusal diagnostic
instead of propagating the validator's instance-bearing exception. A large
invalid original report remains refused without including its content in the
outward exception or chained cause. This bounds that diagnostic surface only;
the validator's internal traversal, errors and temporary allocations still need
the complete resource composition below. Detailed protected diagnostics require
their own explicitly bounded and authorized producer, rather than exposing a
third-party validation exception as the consumer contract.

The [resource-boundary probe](../04-build/evidence/design-audit/check_python_report_resource_boundaries.py)
retains [two observed distinctions](../04-build/evidence/design-audit/python-report-resource-boundaries.json),
separate from the 39 small shared wire controls. The original source-pinned probe observed Python accepting a shape-valid
4,097-member document array that TypeScript refused under its 4,096-member limit;
the subsequent container correction below addresses that one discrepancy. Both host codecs accept a 65,537-byte scalar while the inspected
private native canonical-string component declares a 65,536-byte source limit.
The probe does not invoke that native function or qualify its effects. Its synthetic
large report intentionally cannot establish complete accepted-input/report semantics.

| Phase | Inspected candidate bounds and adoption obligation |
| --- | --- |
| Original wire reception | Both prototypes use a one-MiB source cap; original driver ingress/backing/copy reservation must precede reads, not infer capacity from the resulting bytes |
| Parsing | Both select depth128 and nodes100000; TypeScript additionally caps each container at4096 and scanner work at2000000. Python's byte/depth/node preflight alone is not the same parser/work/collection profile |
| Schema validation | Both use the eleven exact original schemas. Reserve simultaneous retained source, parsed/frozen view, validation view and validator traversal/diagnostic capacity; a parser node count does not charge these copies |
| Native carrier preparation | TypeScript caps canonical-tree tasks at32768 and ASCII tagged carrier bytes at4194304. Python's schema-only result produces no equivalent native carrier or task admission; do not claim parity for that stage |
| Native scalar/output | The private native scalar input is capped at65536 bytes, with chunked output. A larger host-admitted scalar still needs an admitted complete native producer or refusal before effects. Chunk size is not a total source/output limit |

Select one coherent report/operation resource profile before PY-01b submission.
First derive complete worst-case report capacity from original admitted input,
profiles/artifacts and every possible producer branch; include exact base64/hex
expansion and simultaneous ownership. Then reconcile host collection/work/carrier
rules and native scalar/output admission with that same profile. Native string
and original artifact membership must be checked before any acceptance effect;
a late report-capacity failure cannot be repaired by omitting source bytes,
provisional/lifecycle entries or diagnostics.

The existing 64-KiB scalar component is not a complete producer for all larger
original artifacts. If the selected complete reference needs larger scalars,
author the bounded native streaming/chunk source through the authoritative UMF
physical/routine model and CH-01, retaining old component receipts at their actual
subset. Reserve complete source inspection, escaped output, chunk inventories and
final assembly/copies before execution. Do not just raise a SQL constant, mirror
host limits in an unregistered Python counter or shrink the required full report
into a passing projection. No selected release profile follows from this proposal.

Independent schedules vary each limit alone while keeping complete semantic input
fixed: at/above container membership, parser work, tree tasks, carrier bytes,
scalar UTF-8 bytes and complete escaped-output capacity. Include base64 original
artifact expansion, NUL/control escapes and late producer failure. A refused
original attempt leaves no accepted revision/report/head or durable data/history
effects; original unknown submission/commit retains recovery/quarantine separately.
Actual source/native/driver/resource and security-owner admission still precede
support. This is an execution-ready composition task, not a second UMF codec or
Weft compiler responsibility.


### Python report container preflight correction

The retained-JSON candidate now offers an explicitly selected per-container member
bound. The report candidate selects4096, matching the inspected TypeScript decoder.
Lexical preflight charges each array value and each object member before json.loads;
it keeps separate counters for nested containers and does not count quoted commas,
brackets or escaped quotes as structure. The generic candidate's prior default
remains unchanged when this additional bound is not selected.

Nineteen Python codec tests pass, including above-bound array/object/nested cases
with zero decoder calls, exact-bound nested containers and invalid bound types.
All 39 shared report controls pass again under updated source hashes. The
[new boundary receipt](../04-build/evidence/design-audit/python-report-resource-boundaries-container-aligned.json)
records both hosts refusing the 4,097-member report and retains the remaining
host/native scalar-capacity case. The earlier discrepancy receipt stays historical.

This closes the observed container-admission difference only. TypeScript's parser
work, canonical-tree tasks and carrier limits, Python validator/temporary-view
allocation, native scalar/output admission and complete shared precharging still
require the full composition above. A caller-selected counter is not an original
registered operation account or a public capability. No report field is omitted,
no native constant is raised and no acceptance effect is enabled by this correction.

### Full-report carrier and native encoding handoff

The later private PY-01a candidate implements original composed-schema → immutable
retained tree → preflighted numeric-free native carrier. Both hosts preflight exact
native cumulative tasks and compact ASCII length before tagged construction, and
verify the actual serialized length. Twenty-four Python candidate tests and
seventeen TypeScript carrier/report tests pass. The
[resource/encoding checkpoint](contracts/report-scalar-resource-v0.2.proposal.md)
records exact scope and the remaining allocation obligations.

The [cross-host native receipt](../04-build/evidence/design-audit/python-report-tree-native.json)
checks five complete nineteen-field synthetic reports using each host's separately
prepared carrier against complete independently expected native canonical bytes;
six additional malformed-tree controls refuse (16 observations, PostgreSQL 17.9).
Original integer-like member order deliberately produces different intermediate
carrier bytes while preserving original source bytes and equal canonical bytes.
This is neither a genuine acceptance report producer nor PY-07 interchange.
The older 39/42 wire inventories and scalar/container receipts remain historical
observations of their exact pinned implementations, not the current full profile.

Proceed through the existing implementation rows with these concrete exits:

| Existing work | Next required output | Evidence required before advancing |
| --- | --- | --- |
| PY-01a / A2 | Consume the complete original producer report, including all applicable lifecycle/assertion/rebind inventories, through the pinned schema/carrier path. | Independent full expected report and exact original source artifacts; synthetic shape-valid reports cannot prove producer completeness. |
| PY-01b / A1 | Integrate one admitted driver and operation account with original source, decoded/schema views, UTF-8 sizing, carrier, transport, native JSONB, scalar/sort/frame/sink and final-output ownership. | Exhaustion at each allocation/transition before effects, full account release or unknown-outcome custody; the numeric ceilings alone are insufficient. |
| PY-03 / A1 / A5 | Consume the existing security owner's admitted principal, graph-source and publication interfaces. | Original owner-qualified authority/cut/profile correspondence and installed ordinary-role evidence; no Python policy resolver or direct metadata authority is introduced. |
| PY-04 / A4–A7 | Wire complete report persistence and atomic catalog/head settlement into owned/adopted transaction handling. | Full rollback on late encoding/persistence failure; pending versus confirmed committed result, lost acknowledgment and original-attempt reconciliation. Codec success grants no finalization authority. |
| PY-07 | Execute TS writes/Python reads and Python writes/TS reads using the same qualified installed tuple and independently expected corpus. | Actual committed database contents, full exact values/history/receipts/feed outcomes and fresh authorization on retry. Native codec parity is only a prerequisite. |

Package ownership and registered release/driver/resource profiles remain explicit
unresolved selections. The carrier implementation can be reused once selected;
it does not activate public packaging or bypass those exits. Weft retains SQL
lowering and its Rust/Python packaging, UMF retains schema semantics and reusable
SQL generation, and the current security owner retains authorization meaning.

### R5 mismatched actor claim qualification

Re-reading the unchanged original consumer requirement confirms an additional
explicit negative expectation: a supplied actor differing from the authenticated
connecting person must refuse. Separating trusted execution origin from asserted
metadata does not, by itself, prove that negative outcome. PY-03/04 must consume
the security owner's exact original origin-admission profile and define which
public request field, if any, asserts execution actor. Do not manufacture that
field from an arbitrary `x-` extension or silently reinterpret every retained
assertion as an execution-identity claim.

Before a consumer-ready release, freeze an independently authored request through
the actual selected public surface with the mismatched actor claim. Compare the
native original connecting person, complete admitted claim and exact refusal;
observe no graph/journal/receipt effects. A host that merely discards the claim
and successfully writes fails this requested negative case. If the chosen public
surface has no execution-actor input, its closed-wire refusal must be demonstrated
rather than claiming that actor separation alone meets R5. Matching-actor handling
and generic asserted metadata keep their selected owner meanings.

Separately apply an authorized group with the consumer's action name in its
retained `x-` key. Independently inspect the complete original journal origin:
trusted actor equals the authenticated connecting person; the action extension
survives exact spelling; request-role and nested-definer owner cannot replace
actor. Compare the refused request with the allowed action-extension case so an
adapter cannot satisfy refusal by dropping all origin metadata. This is existing
consumer acceptance scope, not a new Truss-local ACL resolver or an adoption of
unqualified security source.

### R2/R7 journal assumptions and selected receipt contract

The unchanged consumer artifact describes replay "from the journal", assumes
last `(xid,seq)` for positions and asks for token reconstruction from repeated
journal rows. These assumptions require explicit integration reconciliation;
they are not the selected Truss receipt implementation. ADR-005 mandates complete
original results, including all-no-op batches, and those batches have no invented
journal row or last sequence. Preserve the original discovery artifact as evidence
rather than editing it to appear already agreed.

| Consumer assumption | Selected Truss handoff and acceptance obligation |
| --- | --- |
| Journal-only original replay | Original full input/results/configuration and position basis are retained in durable request receipts. Repeat returns those exact original results without current-state reconstruction. Changed/no-op mixtures and all-no-op groups are required corpus cases. |
| Last journal xid/seq token | The current proposed opaque locator binds original installation/epoch, receipt identity, full producing xid and comparison profile. It is not a consumer-readable sequence cursor; adoption and original native production remain open. |
| Rebuild every token from journal rows | Event-bearing groups may correlate journal witnesses to original receipt/transaction evidence under the selected resolver. All-no-op and locally trimmed history must resolve original retained receipt/position basis instead. Missing required original evidence is unavailable, never a guessed token or new mutation. |

PY-04/06 must expose this selected contract clearly in the consumer-facing release
and run independent authority/replica tests for both event-bearing and all-no-op
receipts after restart and local trimming. A replica's complete verified applied
coverage, not arrival count or an arbitrary same-numbered receipt row, governs
reached. Record any consumer requirement for a specifically journal-only token as
an unresolved incompatibility; do not advertise that representation merely because
it works for nonempty groups. Existing durable retry and no-loss requirements
remain selected, with the token/profile/native producer and consumer compatibility
handoff still explicit outputs.

### Authored Key selection and primary metadata correspondence

The security owner's current work identifies a Weft admission mismatch around
core `Key.primary` Boolean metadata. Treat that work as an upstream candidate,
not a published compiler version. PY-02/03 must consume the eventual original
owner profile and preserve the complete admitted Key; neither the Python adapter
nor Truss should strip `primary` to make an older compiler accept the document.
The current Weft application model separately resolves an explicit authored Key
ID and infers a Relationship source endpoint from one primary Key (or a sole
Key). These are distinct selection boundaries and must not be conflated.

Freeze independent cases before adopting the owner change: a Record with two
eligible Keys, one marked primary, and a request explicitly selecting the other;
the same request with primary true, false and absent on the selected Key; and
malformed non-Boolean primary metadata. The explicit selection must preserve its
original ordered fields, canonical key bytes and endpoint correspondence rather
than switching to the primary Key. Invalid metadata must fail original owner
admission before native submission. Relationship inference cases separately
exercise one primary, no primary with one Key, ambiguous multiple Keys and
multiple primary Keys against the owner's admitted rules; do not invent a
fallback in the adapter.

Compare original UMF metadata, compiler-selected identity and actual native
endpoint values using independent expected identities and bytes. Include equal
Key names in different Records and reordered composite fields so name-only or
unordered comparisons cannot pass. Unsupported compiler/security tuples remain
refused; a metadata-only compiler fix does not qualify authorization compilation,
installed graph-source authority or Python packaging. These cases are planned,
not executed, and remain within the existing UMF/Weft/security ownership split.


Read-only owner revision 15/source review now finds the Rust regression
`original_boolean_primary_metadata_preserves_explicit_key_selection_and_refusal_gate`.
Its alternate primary Key selects salary while the policy IR retains pk; malformed
metadata and duplicate primary definitions have authored refusal controls, and
public security compilation still refuses unsupported. The
[source review receipt](../04-build/evidence/design-audit/security-primary-key-source-review.json)
pins inspected working sources; Truss reran no owner tests. Consume the eventual
published owner suite for these logical controls instead of duplicating its
compiler oracle. Truss still supplies independent Python transport, zero-native-
submission and actual protected native endpoint/domain/ordered-byte comparisons.
Uncommitted source progress does not admit a release or resolve the package owner.
