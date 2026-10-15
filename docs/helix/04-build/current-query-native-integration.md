# Current-security query integration

Implementation handoff for the existing public Python compiled-query capability.
UMF owns policy, disclosure and route evaluation; Weft owns query interpretation
and SQL lowering. Truss owns the authenticated database operation, original
sources/facts, private materialization and final result release. This implements
the current security interface rather than enabling legacy query diagnostics.

## Original API references

UMF driver proposal: commit `0a893a79ba6596f6fa61a9543561af97524271e9`, TD-056-security-bindings dated private
computation-driver section. Weft current object: `a6168847c22717b012ee394e304bf536d5268645`.
The newer scalar candidate is frozen at
`/private/tmp/weft-current-scalar-frozen-20261015/source-manifest.json`, SHA-256
`6a901c4bdb5c9a5b1e6c2b2dd40c9a19df374584250e65c8d1290263722670d8`;
its unpublished wheel SHA-256 is
`5c3ec17bad0fb8ea12c66d0b027fef6ef4be1ca0b05343ed00df96b26f90bbcf`.
These are component inputs, not released Truss/Weft pairing or native permission.

## Native capture and lifetime

The entry remains an operation on the caller's adopted `PsycopgHost` transaction.
Use one synchronous `_run_operation` callback for capture through result release.
A private held context contains the actual host/transaction/cursor identity,
installation/release and source epoch, PostgreSQL backend/database identities,
original accepted source bytes, and authenticated Subject observation. It cannot
be imported from JSON or returned as a public credential. Its lifetime ends on
callback exit, transaction failure, cancellation or connection loss. The callback produces only a detached private candidate. Public release waits
for `_run_operation`'s final `Ok` after caller/context restoration, savepoint
release and cancellation checks. Any finalization error discards that candidate.
Native transaction locks can outlive the callback until host settlement; do not
claim callback exit released those locks.

Capture inputs are database originals, not a caller's replacement policy:

- Retain accepted `schema_doc.document` UTF-8 bytes, authored revision and digest;
  validate complete definition/report correspondence with the existing accepted
  catalog capture under its held catalog cut.
- Retain exact registered policy, ontology, protection catalog (or original null),
  association bindings, static Weft binding/profile and closure documents from
  the installed original-source archive. New current-source registrations need
  their own explicit source identity; do not relabel legacy graph/relationship
  source archives. Installation and source-epoch cuts precede capture.
- Observe `SESSION_USER` and its actual role OID on the same native connection;
  refuse SET ROLE/elevated caller substitution. Resolve the registered Subject
  through the installed helper and original UMF Key tuple codec, retaining the
  original qualified Subject type, ordered key and codec receipt. Never accept a
  supplied Subject key or actor string as authentication.
- Capture the complete typed facts/associations required by original UMF source
  inspection and every original Weft scan. Preserve original CoreLiteral tokens,
  qualified type and ordered Key tuples plus private object/edge identities and
  versions. No query predicate, FALSE or LIMIT may reduce this capture. Validate
  relation OIDs, definitions and complete columns under the native cuts. Refuse
  unsupported homes or an incomplete/bounded-overflow population, rather than
  publishing a truncated population as complete.

Existing `_security_catalog_assessment`, registered Subject and epoch/fact-cut
helpers supply components, not a current-security issuer. The implementation must
compose their actual native acquisitions/readbacks; a dataclass, hash or
`security_ready` flag cannot establish this lifetime. The current source storage
and issuer must be installed before this public branch becomes available.

## Private UMF child contract

Initial pipe realization is POSIX (macOS/Linux); Windows refuses before launch.
One trusted Bun child per native operation; private stdin/stdout pipes, one
in-flight call, no service endpoint. The Python host retains the actual native
context; it never serializes a native permission. Child inputs are immutable
copies of captured originals. Use the proposed private wrapper over UMF TD-056's original initialize,
inspect-routes and evaluate messages with these exact argument sources:

| Argument | Truss source |
| --- | --- |
| policy/catalog/closure/ontology/associationBindings | Exact installed source documents above, decoded without modifying tokens |
| extensionSelection | Explicit registered selection; child issues the original local opaque extension handle, never imports one |
| owner | Original registered storage/disclosure realization; `disclosure.readAction` must equal actual Weft `primary_action()` |
| cut | Original UMF cut carrier built from captured facts/graphs, original Subject and held source/policy generations |
| operations/routes | Derived from the actual typed `CurrentQueryPreparation.with_context` ledger and original UMF conditional source inspection |

The wrapper is being implemented, not an existing frozen transport. Closed
message members are:

| kind | Exact remaining members |
| --- | --- |
| initialize | requestId, sources (closed policy, catalog, closure, ontology, associationBindings, extensionSelection; explicit null when absent) |
| initialized | requestId, sourceReceipt |
| inspect-routes | requestId, sourceReceipt, owner, routes |
| routes-inspected | requestId, sourceReceipt, routeResults (ordered `{id,result}` original inspector results) |
| evaluate | requestId, sourceReceipt, owner, cut, operations, routes |
| evaluation | requestId, sourceReceipt, batch, routeResults (ordered `{id,result}` original route evaluation results) |
| refused | requestId, sourceReceipt, code (coarse private failure category) |

One initialize precedes inspection/evaluation. The child computes sourceReceipt
from the exact four-byte length header plus initialize body even if initialization refuses. Later calls must
match its retained receipt. The native host checks each expected response kind
and complete ordered result set; the pipe only checks framing and correlation.
Unknown members or phases refuse. Original source reading remains UMF-owned and
loss detecting, preserving integerToken/decimalToken wrappers and unknown source
content rather than converting numeric meaning through Python floats.

Wire envelope is UTF-8 JSON preceded by an unsigned four-byte big-endian byte
length. Reject duplicate JSON keys and non-UTF-8, oversized/truncated frames.
Each request has a unique operation-local ASCII requestId (1–64 characters);
responses echo it exactly and include `sourceReceipt`, the lowercase SHA-256 of
the exact original initialize request length header and frame body. Every later request carries
that same sourceReceipt; every response must match the host-retained value.
This is byte correlation only, never native authority. Route IDs are unique and returned in original order.
Reject unsolicited, duplicate, late, reordered or wrong-source responses. Preserve
untouched original UMF result objects, including refusals and `authority:false`.
No partial response may stage or release rows. Child failure refuses the query;
there is no automatic retry. The child has no database connection or credentials.

Use basic release limits: 4MiB per source/request, 16MiB complete response, at
most16 scans, 256 UMF operations, 4096 field occurrences/routes and 10000 captured
facts (or a smaller original owner limit). One native operation deadline bounds
all child calls and staging, not a fresh deadline per route. Keep original UMF
internal limits unchanged; exhaustion refuses. Retain plain configured logical
bounds and supported deadlines. The owner explicitly removed exact allocation,
rollback-resistant work accounting and custom tracing/metrics from release scope;
this handoff makes no aggregate heap/work guarantee and requires no new meter.
If original helpers cannot handle a supported query within their own limits,
refuse it without claiming successful partial evaluation.

## Weft materialization contract

Call the actual retained Python parent's `prepare_current_query()` and its typed
Rust consumer; never reconstruct it from designation JSON. `with_context` is a
Rust-only hook, not a Python callable. Weft must expose a source-bound Python
bridge deriving the original operation/route packet within that hook; this bridge
retains the same original parent and accepts no replacement plan/ledger/action.
Diagnostic designation JSON alone cannot supply that issuer provenance. Derive each scan,
projection and operand occurrence from that same object. Before SQL, require the
complete original read-rule/scan/action/route result set. Primary row eligibility,
public disclosure and hidden original-action permission stay separate. Pair scan
cells with the same batch's ordered permitted resources and exact original Keys;
unknown/prohibited/conflicting uses refuse the whole query, including empty work.

Build one private typed staging relation per original scan in the same native
operation. The initial installed staging profile requires READ COMMITTED,
read-write on the caller transaction so it can create/drop private temporary
relations and acquire its current-state cuts. A read-only caller receives a
profile refusal; Truss never changes the caller transaction mode. Read-only
current-query execution remains required later work, using a separately admitted
staging arrangement rather than silently promising it here. Truss chooses identifiers; no caller SQL/table names enter this path.
Use one boolean eligibility column and a separate column for every original
value occurrence, so a transformed public String and an authorized raw signed64
operand never share a cell. Populate only values admitted by original evaluation.
Include a unique nonnull TEXT row-key column per scan, issued by Truss for this
invocation. Retain private mapping from staged rows to original qualified resource identity,
version and route/action results; it does not leave the host.

Construct Weft's closed `weft.postgresql.current-values/0.1-candidate` binding
from those actual relations and original occurrence paths. Capture their real
OIDs, pg_attribute built-in types/typmods, collation and access rules, then verify
against the generated declaration before lowering. The first owner lowerer
supports required String and signed64 Integer; extend the original lowerer for
remaining specified domains rather than coercing Decimal/timestamps to fit.
Comparison scopes identify an actually verified equal runtime/domain realization,
not a caller-selected matching string. Refuse missing presence, nonuniform or
unsupported effective domain/scope. Null/withheld is not a scalar placeholder.

Execute conditional SQL only after all native checks above, with original typed
parameters and ordinary deadlines. Decode every result according to original
Weft output descriptors, preserving exact integers. The current frozen Weft candidate lacks row/contributor sidebands; its output
must not be released by matching public values or positions. Weft's next typed
lowerer increment must accept the private row-key column and emit hidden
per-output contributor keys (qualified by original scan) and output-cell/source
use associations, separately described from public result columns. Joins,
grouping, COUNT/DISTINCT and empty aggregates require their complete contributor
meaning, preserving the public bag and original result descriptors. Bound the
complete private sideband and refuse overflow, never truncate it. Aggregate
output is not admitted merely because SQL returned text. Revalidate original source/Subject/
authority and held native context before release. Dispose staging/child on every
exit. A normal semantic/child error with confirmed savepoint rollback may leave
the caller transaction usable. Unresolved native cleanup or cancellation join
must explicitly quarantine the original host custody and return
`transaction_unusable` under CONTRACT-007; an arbitrary cleanup exception alone
does not establish that disposition. Unconfirmed child termination discards all
private results and retains its process custody until containment succeeds.
Do not silently commit or roll back the host's outer transaction.

## Implementation order and basic witness

1. Install/register the original current-source bundle and compose native capture
   with the registered Subject, fact/epoch cuts and one held callback.
2. Implement the private original UMF child transport above and wire its actual
   outputs into Truss's per-use typed staging and the original Weft lowerer.
3. Expose through the existing assembly compiled capability only after complete
   capture → evaluate → stage → SQL → decode → guarded-release works.
4. One ordinary PG18 adopter test: authenticated Subject, masked public salary
   with separately permitted raw predicate, actual result plus denied raw action
   refusal. Include FALSE/LIMIT0 in that basic refusal workflow. Review plan and
   completed implementation with Astra Ultra; release matching wheels together.

Aurora/Lakebase qualification remains externally blocked. Local PG18 implementation
and broader owned-object support remain unblocked. This handoff is not installed
current-security support or a replacement for any original semantic API.

## Pipe implementation checkpoint

`_current_query_pipe.py` implements the private bounded framing, exact-byte
response retention, request correlation, shared operation deadline and terminal
no-retry child lifecycle. A basic real Bun two-call workflow passes. Its echo
fixture proves transport only; the original UMF driver and native issuer are
not implemented by that fixture. It is not exported from the public package.

Agreed Weft0.2 nonaggregate sideband: each private relation requires TEXT
`rowKeyColumn`. SQL appends one private TEXT column containing
`{version:"weft.stage-row-tuple/0.1-candidate",rows:[{scan,key}]}` in original scan
order. Separate `privateResultColumns` declares its position/name/purpose/encoding
and scans; `publicCellSources` declares each public position's original sourcePath,
scan and full Field identity. Exact descriptors stay owner-produced. Native code
must validate every closed carrier/member/key against its held private map.
Aggregates refuse until the original compiler supplies complete grouped bags;
no result value or output order substitutes for resource identity.
