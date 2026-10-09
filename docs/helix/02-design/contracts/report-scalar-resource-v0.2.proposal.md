# Uninstalled report scalar component resource profile

This candidate accompanies the [UMF-captured scalar source](report-scalar-bytes-v0.2.proposal.umf.json)
and its [original SQL](report-scalar-bytes-v0.2.proposal.sql). It preserves the old
65,536-byte component unchanged. It is not an adopted whole-report resource
profile, installation bundle or authority service.

| Controlled component dimension | Candidate ceiling / behavior |
| --- | --- |
| Original bytea input | 1,048,576 bytes; NULL refuses; actual input ownership and native detoast remain separately charged |
| Complete quoted output | 4,194,304 bytes including both quotes; exact widened length checked before emission |
| Sink chunk | At most 65,536 bytes; complete scalar/escape pieces move together; one opening/closing quote |
| Temporary piece | At most six bytes for a control escape, four for direct UTF-8 or two for quote/backslash |
| UTF-8 scan | One complete validation/length pass; invalid, overlong, surrogate, out-of-range or unfinished source refuses |
| Emission | One subsequent complete pass over the same immutable native argument; at most input-length scalar visits per pass |
| Consolidation | Ordered complete chunk aggregation followed by exact final length comparison; output is never a prefix |

The function consumes one complete native bytea, not externally supplied source
blocks or host stream handles. It can produce a scalar larger than the old
component limit while keeping output chunks bounded. It does not implement
full report-tree traversal, duplicate-key/UTF-8 ordering, schema admission,
base64, source-block custody or report/head publication.

Before invocation in A1–A5, the enclosing original profile must reserve actual
input/detoast, frame, piece, growing-chunk, bytea-array and aggregation ownership,
the simultaneous contiguous final output and any driver/storage copies. Each
append and chunk consolidation charges actual conservative copy/work costs;
bounded chunks do not establish linear work or native heap guarantees. This
prototype still concatenates within each bounded chunk. Native allocator,
array/aggregate internals and qualified original account observation remain
unselected; the constants above cannot substitute for their admission. The
complete nineteen-field report must fit its own total capacity independently.

The initial unadopted iteration limited scalar output to one MiB. Composition
review found that short JSON control escapes can fit the one-MiB original report
wire while expanding beyond that ceiling in canonical form. The current candidate
uses the tree encoder's four-MiB output ceiling; original input stays bounded at
one MiB. Earlier source/native receipts retain their exact original scope in Git.
No installed/released profile has changed. Full source/report/copy accounting
and aggregate tree admission remain required; this correction prevents an
accidental smaller value subset from becoming the complete report contract.

The [native receipt](../../04-build/evidence/design-audit/report-scalar-native.json)
records eighteen PostgreSQL 17.9 temporary-function observations: thirteen original
vectors, short-escape expansion beyond one MiB, exact/one-over four-MiB output
capacity and source/control-expanded-output refusals. Every valid output was compared
against complete independently authored bytes; digest agreement alone was not
the comparison. The session explicitly rolled back and changed no installed
Truss function. Tests ran as the native administrative principal; they establish
neither ordinary-role grants nor protected execution.

The [source receipt](../../04-build/evidence/design-audit/report-scalar-source.json)
records exact UMF source archive, JSON reload and stable export with zero
extracted declarations and `complete=false`. The loaded owner revision is
16c35e8d; its six listed source/dependency files match committed 1f7b5f5d bytes.
That subset comparison does not relabel the loaded owner or qualify a complete
current runtime bundle. Routine/body/grant/dependency inventory, resource
composition and actual report integration remain explicit A1/A2 outputs.
