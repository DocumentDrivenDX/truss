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

## Uninstalled tree composition checkpoint

The [tree source](report-tree-bytes-v0.2.proposal.sql) derives from the existing
private `canonical-tree-bytes.sql` task/frame algorithm, with a distinct candidate
routine identity and calls to this scalar candidate. Its
[UMF capture](report-tree-bytes-v0.2.proposal.umf.json) preserves original source;
the [source receipt](../../04-build/evidence/design-audit/report-tree-source.json)
reports exact archive/reload/export and incomplete declaration extraction. The
existing native component files are unchanged.

Tree ceilings remain four MiB of native JSONB text and complete canonical output,
32,768 cumulative tasks, 16,384 pending tasks, native logical depth 256 and 4,096
members per container. Host original-wire depth 128 and one-MiB source admission
remain distinct checks; these numbers do not prove their full account composition.
String pieces now have up to four MiB of output and must remain charged while
copied into sink chunks. Pending frames, JSONB rendering/decoding, duplicate-key
inventory, byte-order sorting, array growth, suffix copies, aggregate workspace
and final contiguous output require actual original reservations. A bounded sink
does not establish bounded peak or linear total copying.

The [native tree receipt](../../04-build/evidence/design-audit/report-tree-native.json)
records four full nineteen-field synthetic report wires through the original
composed host schema/carrier preparation: baseline, control escape expansion,
large UTF-8 key, and byte-order/array-order/NUL content. Complete output bytes
equal an independently authored Unicode-string oracle. Six additional private
inert-tree controls refuse duplicate keys, invalid key/value UTF-8, unknown node
kinds, container overflow and aggregate output overflow. These fault carriers
are not advertised public report inputs. Native functions ran temporarily as the
administrative principal in one rolled-back session.

This supplies tree/scalar encoding correspondence, not genuine report production.
Original source/artifact digests, full lifecycle/assertion/UMF/index/rebind facts,
current authority, installed routine/grant inventory, pre-effect capacity and
atomic report/head settlement remain required before accepted publication.
