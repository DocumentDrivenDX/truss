# Python import contracts and local report consistency

`truss.imports` publishes draft import input, report and execution-result carriers.
It does not provide an import runner or callable capability. Inputs retain full
original record order, load identity, asserted origin, document-qualified object
keys, typed edge endpoints and opaque payload artifacts. Payload decoding remains
conditional on eligible creation; constructing an input neither decodes the
payload nor proves catalog/identity/authorization admission.

Import execution results have their own union rather than `Outcome[ImportReport]`:
`reported` contains progress, `resource_limited` retains an interrupted report,
`execution_failed` preserves the execution failure plus the original report or
explicit `None`, and `invalid` carries diagnostics with no report. A null report
is only permitted by the contract when no writer submission occurred; these
carriers cannot prove that fact. Every report preserves original indices, batch
identity, selected mutation configuration, all four record outcomes, all five
batch dispositions and all nine exact counters. Observed creation is distinct
from committed creation. A processed report can still contain unresolved effects;
it must not become a successful completed load.

Generic report types preserve engine versus supplied-scope execution and processed
versus interrupted status statically. Python erases generic specialization at
runtime. `check_import_execution_shape(..., expected_execution=...)` therefore
checks the expected execution family explicitly. Resource-limited construction
requires interrupted status and rejects attempted-unknown records and uncertain
batches. These are local shape restrictions, not confirmed containment. Trusted
native settlement and resource-profile evidence remain required before a producer
can publish resource-limited results. Failure reports retain pending/unknown
progress rather than converting it into rejection or resetting counters.

`check_import_report_consistency` checks a supplied immutable report against an
independently supplied expected input count. It returns only `consistent`,
`invalid` or `resource`. It checks canonical nonnegative decimal spelling,
original ordered unique outcomes, disjoint complete outcome/unprocessed coverage,
nonempty nonoverlapping batch membership, exact outcome-to-batch association,
unique batch IDs, execution-compatible dispositions and independently derived
nine counters. A processed report cannot contain unprocessed indices. Engine-owned
reports cannot use pending batches. The selected supplied-scope subset excludes
committed and commit-unknown batches because no host-confirmation protocol is
provided here. Confirmed rollback and transaction-unresolved progress remain
representable.

Explicit reduced limits cap record inventory at4096, decimal digits at20 and
aggregate Python string code points at1,048,576. Aggregate inventory lengths are
checked before the fixed carrier-tree walk; all text is charged before hashing
batch IDs or converting decimal strings. Exceeding a reduced digit budget returns
`resource`; malformed decimal spelling returns `invalid`. Expected count and
execution-family arguments must be exact strings before traversal/comparison. These bounds apply only to this local
check. Prior carrier allocation, original wire decoding, driver ingress, total
heap, native work and evidence/diagnostic authenticity remain outside its claim.
No payload or native evidence is decoded or interpreted. The checker does not
prove correspondence to original input values, greedy batch boundaries,
authorized disclosure, validated evidence digests, actual rollback/commit,
containment or full-load success. It leaves all original report data unchanged.

C01 still needs the callable import Protocol with complete transaction options
and cancellation contracts, plus the remaining capability families. C08 still
requires the installed protected catalog/mutation runtime and native batch
settlement. The next operational work is PA01 installed identity/owner/ACL and
dependency inventory with ordinary-role denial across all four admission families.
